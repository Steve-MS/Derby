#!/usr/bin/env python3
"""
backtest.py — Race-model validation harness for Epsom Ladies Day (Fri 6 June).

Usage:
    python tests/backtest.py \
        --predictions predictions/predictions-frozen-YYYY-MM-DD.json \
        --results results/results-frozen-YYYY-MM-DD.json

Exit codes:
    0 = GREEN  (trust Saturday)
    1 = AMBER  (trust high-confidence picks only)
    2 = RED    (model broken, don't bet Saturday)

See spec/backtest-protocol.md for threshold definitions and justification.
"""

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Thresholds (pre-registered — see backtest-protocol.md §2)
# ---------------------------------------------------------------------------

GREEN_TOP3_MIN = 0.50    # ≥ 50%
GREEN_PLACE_MIN = 0.30   # ≥ 30%
GREEN_ROI_MIN = -0.25    # > -25%
AMBER_TOP3_MIN = 0.35    # 35–49%
RED_TOP3_MAX = 0.35      # < 35%  → RED
RED_ROI_MAX = -0.50      # < -50% → RED


# ---------------------------------------------------------------------------
# EW terms by field size (see backtest-protocol.md §1.3)
# ---------------------------------------------------------------------------

def ew_places(field_size: int) -> int:
    """Return number of EW places for a given field size."""
    if field_size <= 4:
        return 1   # win only
    if field_size <= 7:
        return 2
    if field_size <= 15:
        return 3
    return 4


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_json(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(2)
    with p.open(encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Per-race metric computation
# ---------------------------------------------------------------------------

@dataclass
class RaceResult:
    race_id: str
    race_name: str
    race_time: str
    field_size: int
    top_pick: str            # model's #1 ranked horse
    top_pick_implied_prob: Optional[float]
    top_pick_score: Optional[float]
    winner: str              # actual winner
    winner_position_in_model_top3: bool   # was winner ranked 1/2/3 by model?
    top_pick_finish: int     # finishing position of model's #1 pick (0 = NR/DNF)
    win: bool
    place: bool              # top 3 regardless of field size
    ew: bool                 # within EW terms for this field size
    sp_of_top_pick: Optional[float]       # SP of model's top pick (for ROI)
    winner_sp: Optional[float]            # SP of actual winner
    brier_contribution: Optional[float]   # per-race Brier contribution (summed across runners)
    skipped: bool = False
    skip_reason: str = ""


def match_name(a: str, b: str) -> bool:
    """Case-insensitive, whitespace-normalised horse name comparison."""
    return a.strip().lower() == b.strip().lower()


def compute_race(pred_race: dict, result_race: dict) -> RaceResult:
    """Compute metrics for a single race."""
    race_id = pred_race.get("race_id", result_race.get("race_id", "unknown"))
    race_name = pred_race.get("race_name", result_race.get("race_name", ""))
    race_time = pred_race.get("race_time", result_race.get("race_time", ""))

    # Filter non-runners from results
    finishers = [f for f in result_race.get("finishers", []) if not f.get("non_runner", False)]
    actual_field_size = len(finishers)
    if actual_field_size == 0:
        return RaceResult(
            race_id=race_id, race_name=race_name, race_time=race_time,
            field_size=0, top_pick="", top_pick_implied_prob=None,
            top_pick_score=None, winner="", winner_position_in_model_top3=False,
            top_pick_finish=0, win=False, place=False, ew=False,
            sp_of_top_pick=None, winner_sp=None, brier_contribution=None,
            skipped=True, skip_reason="No finishers in results"
        )

    # Find winner
    winner_entry = next((f for f in finishers if f.get("position") == 1), None)
    if winner_entry is None:
        return RaceResult(
            race_id=race_id, race_name=race_name, race_time=race_time,
            field_size=actual_field_size, top_pick="", top_pick_implied_prob=None,
            top_pick_score=None, winner="", winner_position_in_model_top3=False,
            top_pick_finish=0, win=False, place=False, ew=False,
            sp_of_top_pick=None, winner_sp=None, brier_contribution=None,
            skipped=True, skip_reason="No winner (position=1) found in results"
        )

    winner_name = winner_entry["horse_name"]
    winner_sp = winner_entry.get("sp_decimal") or winner_entry.get("sp")

    # Get model rankings (sorted by rank already)
    rankings = sorted(pred_race.get("rankings", []), key=lambda r: r.get("rank", 999))
    if not rankings:
        return RaceResult(
            race_id=race_id, race_name=race_name, race_time=race_time,
            field_size=actual_field_size, top_pick="", top_pick_implied_prob=None,
            top_pick_score=None, winner=winner_name, winner_position_in_model_top3=False,
            top_pick_finish=0, win=False, place=False, ew=False,
            sp_of_top_pick=None, winner_sp=winner_sp, brier_contribution=None,
            skipped=True, skip_reason="No rankings in predictions"
        )

    top_pick_entry = rankings[0]
    top_pick_name = top_pick_entry["horse_name"]
    top_pick_implied_prob = top_pick_entry.get("implied_prob")
    top_pick_score = top_pick_entry.get("score")

    # Find top pick's finishing position
    top_pick_finish_entry = next(
        (f for f in finishers if match_name(f["horse_name"], top_pick_name)), None
    )
    top_pick_finish = top_pick_finish_entry.get("position", 0) if top_pick_finish_entry else 0
    sp_of_top_pick = (
        (top_pick_finish_entry.get("sp_decimal") or top_pick_finish_entry.get("sp"))
        if top_pick_finish_entry else None
    )

    # Was winner in model's top 3?
    top3_names = [r["horse_name"] for r in rankings[:3]]
    winner_in_top3 = any(match_name(winner_name, n) for n in top3_names)

    # Metrics
    win = top_pick_finish == 1
    place = top_pick_finish in (1, 2, 3) and top_pick_finish > 0
    ew_limit = ew_places(actual_field_size)
    ew = (top_pick_finish >= 1 and top_pick_finish <= ew_limit)

    # Brier score contribution (across all runners in this race)
    brier = None
    if top_pick_implied_prob is not None:
        # Try to compute Brier across all ranked runners
        brier = 0.0
        for r in rankings:
            prob = r.get("implied_prob")
            h_name = r.get("horse_name", "")
            outcome = 1.0 if match_name(h_name, winner_name) else 0.0
            if prob is not None:
                brier += (prob - outcome) ** 2

    return RaceResult(
        race_id=race_id, race_name=race_name, race_time=race_time,
        field_size=actual_field_size, top_pick=top_pick_name,
        top_pick_implied_prob=top_pick_implied_prob, top_pick_score=top_pick_score,
        winner=winner_name, winner_position_in_model_top3=winner_in_top3,
        top_pick_finish=top_pick_finish, win=win, place=place, ew=ew,
        sp_of_top_pick=sp_of_top_pick, winner_sp=winner_sp, brier_contribution=brier
    )


# ---------------------------------------------------------------------------
# Aggregate metrics
# ---------------------------------------------------------------------------

@dataclass
class AggregateMetrics:
    races_total: int
    races_run: int    # excludes skipped
    win_strike: float
    place_strike: float
    ew_strike: float
    top3_inclusion: float
    brier_score: Optional[float]
    roi: Optional[float]
    total_staked: float
    total_returned: float
    brier_races: int


def compute_aggregates(results: list[RaceResult]) -> AggregateMetrics:
    valid = [r for r in results if not r.skipped]
    n = len(valid)
    if n == 0:
        return AggregateMetrics(
            races_total=len(results), races_run=0,
            win_strike=0, place_strike=0, ew_strike=0, top3_inclusion=0,
            brier_score=None, roi=None, total_staked=0, total_returned=0, brier_races=0
        )

    wins = sum(1 for r in valid if r.win)
    places = sum(1 for r in valid if r.place)
    ews = sum(1 for r in valid if r.ew)
    top3 = sum(1 for r in valid if r.winner_position_in_model_top3)

    # ROI — only count races where we have SP
    roi_races = [r for r in valid if r.sp_of_top_pick is not None]
    total_staked = float(len(roi_races))
    total_returned = sum(r.sp_of_top_pick for r in roi_races if r.win and r.sp_of_top_pick)
    roi = ((total_returned - total_staked) / total_staked) if total_staked > 0 else None

    # Brier
    brier_races = [r for r in valid if r.brier_contribution is not None]
    brier_score = (
        sum(r.brier_contribution for r in brier_races) / len(brier_races)
        if brier_races else None
    )

    return AggregateMetrics(
        races_total=len(results), races_run=n,
        win_strike=wins / n, place_strike=places / n,
        ew_strike=ews / n, top3_inclusion=top3 / n,
        brier_score=brier_score, roi=roi,
        total_staked=total_staked, total_returned=total_returned,
        brier_races=len(brier_races)
    )


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------

def compute_verdict(m: AggregateMetrics) -> tuple[str, int, str]:
    """Returns (band, exit_code, explanation)."""
    # RED conditions first
    if m.top3_inclusion < RED_TOP3_MAX:
        return ("RED", 2,
                f"Top-3 inclusion {m.top3_inclusion:.0%} < {RED_TOP3_MAX:.0%} threshold")
    if m.roi is not None and m.roi < RED_ROI_MAX:
        return ("RED", 2,
                f"ROI {m.roi:.1%} < {RED_ROI_MAX:.0%} threshold")

    # GREEN: all three conditions must hold
    green_top3 = m.top3_inclusion >= GREEN_TOP3_MIN
    green_place = m.place_strike >= GREEN_PLACE_MIN
    green_roi = (m.roi is None) or (m.roi > GREEN_ROI_MIN)

    if green_top3 and green_place and green_roi:
        return ("GREEN", 0,
                "Top-3 inclusion, place strike and ROI all within GREEN band")

    # AMBER
    if m.top3_inclusion >= AMBER_TOP3_MIN:
        reasons = []
        if not green_top3:
            reasons.append(f"top-3 inclusion {m.top3_inclusion:.0%} < {GREEN_TOP3_MIN:.0%}")
        if not green_place:
            reasons.append(f"place strike {m.place_strike:.0%} < {GREEN_PLACE_MIN:.0%}")
        if not green_roi and m.roi is not None:
            reasons.append(f"ROI {m.roi:.1%} ≤ {GREEN_ROI_MIN:.0%}")
        return ("AMBER", 1, "Borderline: " + "; ".join(reasons) if reasons else "Borderline")

    # Fallback RED (shouldn't normally reach here given checks above)
    return ("RED", 2, "Top-3 inclusion below AMBER floor")


# ---------------------------------------------------------------------------
# Report printer
# ---------------------------------------------------------------------------

BAND_ICONS = {"GREEN": "🟢", "AMBER": "🟡", "RED": "🔴"}
BAND_ACTIONS = {
    "GREEN": "Trust Saturday predictions fully.",
    "AMBER": "Trust HIGH-confidence picks only (wide score gap to #2). Skip clustered races.",
    "RED":   "Do NOT bet Saturday. Model is broken or misconfigured. Investigate before use.",
}


def pct(v: float) -> str:
    return f"{v:.0%}"


def print_report(
    pred_meta: dict,
    results_meta: dict,
    race_results: list[RaceResult],
    metrics: AggregateMetrics,
    verdict: str,
    verdict_reason: str,
) -> None:
    icon = BAND_ICONS[verdict]
    width = 60
    border = "=" * width

    print()
    print(border)
    print(f"  RACE MODEL BACKTEST REPORT")
    print(f"  Card date : {pred_meta.get('card_date', 'unknown')}")
    print(f"  Venue     : {pred_meta.get('venue', 'unknown')}")
    print(f"  Frozen by : {pred_meta.get('frozen_by', 'unknown')} @ {pred_meta.get('frozen_at', '?')}")
    print(f"  Results by: {results_meta.get('fetched_by', 'unknown')} @ {results_meta.get('fetched_at', '?')}")
    print(border)
    print()
    print(f"  VERDICT: {icon} {verdict}")
    print(f"  {BAND_ACTIONS[verdict]}")
    print(f"  Reason  : {verdict_reason}")
    print()
    print(f"  METRICS ({metrics.races_run} races run, {metrics.races_total - metrics.races_run} skipped)")
    print(f"  {'Metric':<28}  {'Value':>8}  Threshold")
    print(f"  {'-'*52}")
    print(f"  {'Win strike rate':<28}  {pct(metrics.win_strike):>8}  (beat random ≥ 20%)")
    print(f"  {'Place strike rate':<28}  {pct(metrics.place_strike):>8}  GREEN ≥ 30%")
    print(f"  {'EW strike rate':<28}  {pct(metrics.ew_strike):>8}  (informational)")
    top3_flag = "✓" if metrics.top3_inclusion >= GREEN_TOP3_MIN else ("~" if metrics.top3_inclusion >= AMBER_TOP3_MIN else "✗")
    print(f"  {'Top-3 inclusion [PRIMARY]':<28}  {pct(metrics.top3_inclusion):>8}  GREEN ≥ 50% {top3_flag}")

    if metrics.brier_score is not None:
        print(f"  {'Brier score':<28}  {metrics.brier_score:>8.4f}  lower = better (rng≈0.109)")
    else:
        print(f"  {'Brier score':<28}  {'n/a':>8}  (implied_prob missing)")

    if metrics.roi is not None:
        roi_flag = "✓" if metrics.roi > GREEN_ROI_MIN else ("~" if metrics.roi > RED_ROI_MAX else "✗")
        print(f"  {'ROI (flat £1 win)':<28}  {metrics.roi:>7.1%}  GREEN > -25% {roi_flag}")
        print(f"  {'  staked/returned':<28}  £{metrics.total_staked:.0f} / £{metrics.total_returned:.2f}")
    else:
        print(f"  {'ROI (flat £1 win)':<28}  {'n/a':>8}  (SP data missing)")

    print()
    print(f"  PER-RACE BREAKDOWN")
    print(f"  {'Time':<7} {'Race':<30} {'Top Pick':<20} {'Fin':>4} {'W':>2} {'P':>2} {'T3':>2} {'SP':>6}")
    print(f"  {'-'*76}")
    for r in race_results:
        if r.skipped:
            print(f"  {r.race_time:<7} {r.race_name[:30]:<30} SKIPPED — {r.skip_reason}")
            continue
        w = "✓" if r.win else " "
        p = "✓" if r.place else " "
        t3 = "✓" if r.winner_position_in_model_top3 else " "
        fin = str(r.top_pick_finish) if r.top_pick_finish > 0 else "NR"
        sp_str = f"{r.sp_of_top_pick:.1f}" if r.sp_of_top_pick else "-"
        pick_disp = r.top_pick[:19] if r.top_pick else "?"
        print(f"  {r.race_time:<7} {r.race_name[:30]:<30} {pick_disp:<20} {fin:>4} {w:>2} {p:>2} {t3:>2} {sp_str:>6}")
        print(f"  {'':>7} {'  Winner: ' + r.winner:<50}")

    print()
    print(border)
    print()
    print("  ⚠️  SAMPLE SIZE WARNING: This is a ~7-race smoke test.")
    print("     Wide confidence intervals apply. See backtest-protocol.md §3.")
    print()
    print(border)
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Race model backtest harness. Exit 0=GREEN 1=AMBER 2=RED."
    )
    parser.add_argument(
        "--predictions", required=True,
        help="Path to frozen predictions JSON (produced by Kaylee's model pre-race)"
    )
    parser.add_argument(
        "--results", required=True,
        help="Path to actual results JSON (fetched by River on Friday evening)"
    )
    args = parser.parse_args()

    predictions = load_json(args.predictions)
    results = load_json(args.results)

    # Index results by race_id
    results_by_id: dict[str, dict] = {}
    for r in results.get("races", []):
        results_by_id[r["race_id"]] = r

    # Match each prediction race to its result
    race_results: list[RaceResult] = []
    for pred_race in predictions.get("races", []):
        rid = pred_race.get("race_id", "")
        result_race = results_by_id.get(rid)
        if result_race is None:
            # Try matching by race_time as fallback
            pred_time = pred_race.get("race_time", "")
            result_race = next(
                (r for r in results.get("races", []) if r.get("race_time") == pred_time), None
            )
        if result_race is None:
            race_results.append(RaceResult(
                race_id=pred_race.get("race_id", "unknown"),
                race_name=pred_race.get("race_name", ""),
                race_time=pred_race.get("race_time", ""),
                field_size=0, top_pick="", top_pick_implied_prob=None,
                top_pick_score=None, winner="", winner_position_in_model_top3=False,
                top_pick_finish=0, win=False, place=False, ew=False,
                sp_of_top_pick=None, winner_sp=None, brier_contribution=None,
                skipped=True, skip_reason=f"No matching result found for race_id={rid}"
            ))
        else:
            race_results.append(compute_race(pred_race, result_race))

    metrics = compute_aggregates(race_results)
    verdict, exit_code, verdict_reason = compute_verdict(metrics)

    print_report(predictions, results, race_results, metrics, verdict, verdict_reason)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
