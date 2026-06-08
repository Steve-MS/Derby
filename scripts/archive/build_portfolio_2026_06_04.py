"""Portfolio rebuild: Friday 2026-06-05 + Saturday 2026-06-06 (GREEN / HOLD branches).

Run from race-analysis/ root:
    python scripts/build_portfolio_2026_06_04.py
"""

from __future__ import annotations

import copy
import datetime
import json
import sys
from pathlib import Path

# ── path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from betting import build_bets  # noqa: E402

# ── constants ─────────────────────────────────────────────────────────────────
BANKROLL = 100.0          # £100 – 1 pt = £1.00
BUILT_AT = datetime.datetime.now(datetime.timezone.utc).isoformat()

SCORES_FRI = ROOT / "outputs" / "scores-2026-06-05.json"
SCORES_SAT = ROOT / "outputs" / "scores-2026-06-06.json"

OUT_FRI       = ROOT / "outputs" / "bets-2026-06-05.json"
OUT_SAT_GREEN = ROOT / "outputs" / "bets-2026-06-06.json"
OUT_SAT_HOLD  = ROOT / "outputs" / "bets-2026-06-06-soft-contingency.json"

SLIP_FRI  = ROOT / "outputs" / "slip-2026-06-05.txt"
SLIP_SAT  = ROOT / "outputs" / "slip-2026-06-06.txt"

# ── live-price overrides (market-latest.json snapshot 2026-06-04T12:15+01:00) ─
LIVE_PRICES: dict[str, float | None] = {
    # Friday – Oaks
    "Amelia Earhart": 2.25,
    "Legacy Link":    3.5,
    "Precise":        None,   # WITHDRAWN – filter from field

    # Saturday – Coronation Cup (drifters / turnarounds vs stale racecard)
    "Calandagan":     5.0,
    "Lambourn":       8.0,
    "Jan Brueghel":   4.5,

    # Saturday – Derby
    "Item":               3.25,
    "Benvenuto Cellini":  2.0,
    "James J Braddock":  10.0,
}

# ── going advisory blocks ──────────────────────────────────────────────────────
GOING_FRI = {
    "going":      "Good-to-Soft",
    "declared_at": "2026-06-04T09:00+01:00",
    "advisory":   (
        "Softened from Good (Tue call). No model re-run required; "
        "going_fit scores handle GTS adequately. Going stable, no further "
        "deterioration expected Friday."
    ),
}

GOING_SAT = {
    "going":       "Good-to-Soft → forecast Soft by Derby post-time",
    "forecast_by": "River (river-weather-agent)",
    "rain_mm":     5.2,
    "probability_soft": "60-80 % by 10:00 Derby morning",
    "advisory": (
        "5.2 mm overnight rain. River forecasts Soft on the round course "
        "by Derby post-time (16:00). Item going_fit = 0.95 on GTS; "
        "collapses to ~0.55 on Soft. Use GREEN slip until official "
        "declarations; switch to HOLD slip if Soft is declared."
    ),
    "item_trigger": {
        "going_fit_gts":  0.95,
        "going_fit_soft": 0.55,
        "action": "If Soft declared → cancel Item WIN, use soft-contingency slip.",
    },
}

# ── Item speculative bet (GREEN scenario only) ─────────────────────────────────
ITEM_SPECIAL_GREEN = {
    "race_id":    "epsom-2026-06-06-1600",
    "horse":      "Item",
    "scenario":   "GREEN – going GTS or firmer",
    "bet_type":   "WIN",
    "stake_pts":  1.0,
    "stake_gbp":  1.0,
    "odds_decimal": 3.25,
    "odds_fractional": "9/4",
    "model_score": 95.0,
    "going_fit_gts":  0.95,
    "going_fit_soft": 0.55,
    "edge_note": (
        "Race confidence = LOW. Live price 3.25 implies 30.8 % win prob; "
        "model_prob ~9.4 % on stale field scores → negative edge (-69 %). "
        "Included as GOING-CONDITIONAL SPECULATIVE PUNT only: "
        "score 95, going_fit 0.95, market steam 5.0 → 3.25 (−35 %)."
    ),
    "warning": (
        "NOT a model-recommended WIN/EW signal. 18+ entertainment allowance only. "
        "Stake 1 pt (£1.00). Do NOT place if going declared Soft – switch to HOLD slip."
    ),
    "cancel_if": "going declared Soft",
}

ITEM_ADVISORY_HOLD = {
    "race_id":  "epsom-2026-06-06-1600",
    "horse":    "Item",
    "scenario": "HOLD – going declared Soft",
    "bet_type": "PASS",
    "stake_pts": 0.0,
    "stake_gbp": 0.0,
    "rationale": (
        "Going declared Soft. Item going_fit collapses 0.95 → 0.55. "
        "Adjusted effective score ~55; combined with negative model edge "
        "at live price 3.25, no bet placed. 1 pt stake retained."
    ),
    "stake_freed_pts": 1.0,
}


# ═════════════════════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════════════════════

def load_scores(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def apply_overrides(scores_data: dict) -> dict:
    """Deep-copy scores and apply LIVE_PRICES overrides; filter WITHDRAWN runners."""
    data = copy.deepcopy(scores_data)
    for race in data["races"]:
        kept: list[dict] = []
        for runner in race["ranked_runners"]:
            horse = runner.get("horse", "")
            if horse in LIVE_PRICES:
                live_p = LIVE_PRICES[horse]
                if live_p is None:
                    continue   # WITHDRAWN – drop from field entirely
                runner["morning_price"] = live_p
            kept.append(runner)
        race["ranked_runners"] = kept
    return data


def _fmt_odds(dec: float) -> str:
    """Decimal → approximate fractional string for slip display."""
    frac = dec - 1.0
    # Simple lookup for common prices
    table = {
        2.0: "Evs", 2.25: "5/4", 2.5: "6/4", 3.0: "2/1", 3.25: "9/4",
        3.5: "5/2", 4.0: "3/1", 4.5: "7/2", 5.0: "4/1", 6.0: "5/1",
        7.0: "6/1", 8.0: "7/1", 9.0: "8/1", 10.0: "9/1", 11.0: "10/1",
        13.0: "12/1", 13.5: "25/2", 15.0: "14/1", 17.0: "16/1",
        18.5: "35/2", 19.0: "18/1", 21.0: "20/1", 24.0: "23/1",
        26.0: "25/1", 29.0: "28/1", 34.0: "33/1",
    }
    if dec in table:
        return table[dec]
    n = round(frac)
    return f"{n}/1" if abs(frac - n) < 0.1 else f"{frac:.2f}"


def build_bookmaker_slip(
    date_str: str,
    singles: list[dict],
    doubles: list[dict],
    trebles: list[dict],
    accumulators: list[dict],
    outsiders: list[dict],
    portfolio_summary: dict,
    item_special: dict | None = None,
    scenario_label: str = "",
) -> str:
    """Produce a plain-text bookmaker-ready slip."""
    lines: list[str] = []
    banner = f"APEX RACING – BADGER PORTFOLIO {'– ' + scenario_label if scenario_label else ''}"
    lines += [banner, f"Date: {date_str}", "=" * 60, ""]

    lines.append("── SINGLES ──────────────────────────────────────────────────")
    active = [s for s in singles if s.get("bet_type") not in ("PASS", None)]
    passed = [s for s in singles if s.get("bet_type") in ("PASS", None)]

    for s in active:
        btype  = s["bet_type"]
        horse  = s["horse"]
        odds   = s.get("odds_decimal", s.get("odds_raw", "?"))
        stake  = s["stake_gbp"]
        rid    = s["race_id"].split("-")[-1]  # e.g. "1515"
        conf   = s.get("rationale", "")[:60]
        lines.append(
            f"  {rid}  {horse:<28}  {btype:<3}  "
            f"{_fmt_odds(float(odds)) if isinstance(odds, (int,float)) else odds:<8}  "
            f"£{stake:.2f}"
        )

    if item_special and item_special.get("bet_type") == "WIN":
        item = item_special
        lines.append(
            f"  1600  {item['horse']:<28}  WIN* "
            f"{_fmt_odds(item['odds_decimal']):<8}  "
            f"£{item['stake_gbp']:.2f}  [SPECULATIVE – going-conditional]"
        )

    lines += ["", f"  ({len(passed)} races PASS)", ""]

    if doubles:
        lines.append("── DOUBLES ──────────────────────────────────────────────────")
        for d in doubles:
            legs  = " × ".join(leg["horse"] for leg in d["legs"])
            stake = d["combined_stake_gbp"]
            ret   = d["potential_return_gbp"]
            lines.append(f"  {legs:<52}  £{stake:.2f}  (→ £{ret:.2f})")
        lines.append("")

    if trebles:
        lines.append("── TREBLE ───────────────────────────────────────────────────")
        for t in trebles:
            legs  = " × ".join(leg["horse"] for leg in t["legs"])
            stake = t["combined_stake_gbp"]
            ret   = t["potential_return_gbp"]
            lines.append(f"  {legs}")
            lines.append(f"  Stake £{stake:.2f}  max return £{ret:.2f}")
        lines.append("")

    if accumulators:
        lines.append("── ACCUMULATORS ─────────────────────────────────────────────")
        for a in accumulators:
            legs  = " × ".join(leg["horse"] for leg in a["legs"])
            stake = a["combined_stake_gbp"]
            ret   = a["potential_return_gbp"]
            lines.append(f"  {legs}")
            lines.append(f"  Stake £{stake:.2f}  max return £{ret:.2f}")
        lines.append("")

    active_out = [o for o in outsiders if o.get("outsider_pick")]
    if active_out:
        lines.append("── OUTSIDERS (value EW) ─────────────────────────────────────")
        for o in active_out:
            horse  = o["horse"]
            odds   = o["morning_price"]
            stake  = o["stake_gbp"]
            terms  = o.get("ew_terms", "")
            rid    = o["race_id"].split("-")[-1]
            lines.append(
                f"  {rid}  {horse:<28}  EW  "
                f"{_fmt_odds(float(odds)) if isinstance(odds, (int,float)) else odds:<8}  "
                f"£{stake:.2f} EW  ({terms})"
            )
        lines.append("")

    ps = portfolio_summary
    item_stake = item_special["stake_gbp"] if item_special and item_special.get("bet_type") == "WIN" else 0.0
    total = ps["total_stake_gbp"] + item_stake
    lines += [
        "── SUMMARY ──────────────────────────────────────────────────",
        f"  Active singles:   {ps['active_singles']}",
        f"  Doubles:          {ps['doubles_count']}",
        f"  Trebles:          {ps['trebles_count']}",
        f"  Outsiders (EW):   {ps['outsider_summary']['count']}",
        f"  Total stake:      £{total:.2f}"
        + (f" (incl. £{item_stake:.2f} speculative Item bet)" if item_stake else ""),
        f"  Max win scenario: £{ps['max_potential_return_gbp']:.2f}",
        "",
        "  18+. Gamble responsibly. BeGambleAware.org.",
        "",
    ]
    return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════════
# Main build
# ═════════════════════════════════════════════════════════════════════════════

def main() -> None:
    # ── Load & override ──────────────────────────────────────────────────────
    fri_raw = load_scores(SCORES_FRI)
    sat_raw = load_scores(SCORES_SAT)

    fri_data  = apply_overrides(fri_raw)
    sat_data  = apply_overrides(sat_raw)   # Item GREEN (live 3.25)

    # Item HOLD: clone Saturday, set Item morning_price=None
    sat_hold_data = copy.deepcopy(sat_data)
    for race in sat_hold_data["races"]:
        if race["race_id"] == "epsom-2026-06-06-1600":
            for runner in race["ranked_runners"]:
                if runner.get("horse") == "Item":
                    runner["morning_price"] = None   # exclude from edge calc

    # ── Run build_bets() ─────────────────────────────────────────────────────
    print("Building Friday portfolio …")
    fri_result = build_bets(fri_data["races"], bankroll=BANKROLL)

    print("Building Saturday GREEN portfolio …")
    sat_green_result = build_bets(sat_data["races"], bankroll=BANKROLL)

    print("Building Saturday HOLD portfolio …")
    sat_hold_result = build_bets(sat_hold_data["races"], bankroll=BANKROLL)

    # ── Compose final JSON ───────────────────────────────────────────────────
    fri_out = {
        **fri_result,
        "built_at":       BUILT_AT,
        "bankroll_note":  "£100 bankroll. 1 pt = £1.00.",
        "going_advisory": GOING_FRI,
        "live_price_overrides_applied": {
            "Amelia Earhart": 2.25,
            "Legacy Link":    3.5,
            "Precise":        "WITHDRAWN – removed from field",
        },
    }

    sat_green_out = {
        **sat_green_result,
        "scenario":        "GREEN – going GTS or firmer",
        "built_at":        BUILT_AT,
        "bankroll_note":   "£100 bankroll. 1 pt = £1.00.",
        "going_advisory":  GOING_SAT,
        "live_price_overrides_applied": {
            k: v for k, v in LIVE_PRICES.items()
            if k not in ("Amelia Earhart", "Legacy Link", "Precise")
        },
        "item_special_bet": ITEM_SPECIAL_GREEN,
        "scenario_note": (
            "Use this slip ONLY if going remains GTS or firmer. "
            "Check official declarations by 10:00 Derby morning. "
            "If Soft declared, switch to soft-contingency slip and cancel Item WIN."
        ),
    }

    sat_hold_out = {
        **sat_hold_result,
        "scenario":       "HOLD – going declared Soft",
        "built_at":       BUILT_AT,
        "bankroll_note":  "£100 bankroll. 1 pt = £1.00.",
        "going_advisory": GOING_SAT,
        "live_price_overrides_applied": {
            k: v for k, v in LIVE_PRICES.items()
            if k not in ("Amelia Earhart", "Legacy Link", "Precise", "Item")
        },
        "item_advisory":  ITEM_ADVISORY_HOLD,
        "scenario_note": (
            "Activate this slip if going is officially declared Soft on Derby morning. "
            "Item bet is cancelled; 1 pt stake retained. All other bets unchanged."
        ),
    }

    # ── Write JSON outputs ───────────────────────────────────────────────────
    for path, obj in [
        (OUT_FRI,       fri_out),
        (OUT_SAT_GREEN, sat_green_out),
        (OUT_SAT_HOLD,  sat_hold_out),
    ]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)
        print(f"  ✓ {path.name}")

    # ── Write bookmaker slips ────────────────────────────────────────────────
    slip_fri_text = build_bookmaker_slip(
        "Friday 5 June 2026 – Epsom",
        fri_result["singles"],
        fri_result["doubles"],
        fri_result["trebles"],
        fri_result["accumulators"],
        fri_result["outsiders"],
        fri_result["portfolio_summary"],
    )
    with open(SLIP_FRI, "w", encoding="utf-8") as f:
        f.write(slip_fri_text)
    print(f"  ✓ {SLIP_FRI.name}")

    slip_sat_text = build_bookmaker_slip(
        "Saturday 6 June 2026 – Epsom (Derby Day)",
        sat_green_result["singles"],
        sat_green_result["doubles"],
        sat_green_result["trebles"],
        sat_green_result["accumulators"],
        sat_green_result["outsiders"],
        sat_green_result["portfolio_summary"],
        item_special=ITEM_SPECIAL_GREEN,
        scenario_label="GREEN (Item = BET if GTS) | HOLD file: bets-2026-06-06-soft-contingency.json",
    )
    with open(SLIP_SAT, "w", encoding="utf-8") as f:
        f.write(slip_sat_text)
    print(f"  ✓ {SLIP_SAT.name}")

    # ── Print summaries ──────────────────────────────────────────────────────
    def _summarise(label: str, result: dict, item_extra: float = 0.0) -> None:
        ps = result["portfolio_summary"]
        active = [s for s in result["singles"] if s.get("bet_type") not in ("PASS", None)]
        print(f"\n{'─'*60}")
        print(f"  {label}")
        print(f"{'─'*60}")
        for s in active:
            odds = s.get('odds_decimal', s.get('odds_raw', '?'))
            print(
                f"  {s['race_id'].split('-')[-1]}  {s['horse']:<28}"
                f"  {s['bet_type']:<4}  "
                f"@ {_fmt_odds(float(odds)) if isinstance(odds,(int,float)) else odds:<8}"
                f"  {s['stake_pts']:.2f}pt  £{s['stake_gbp']:.2f}"
            )
        out = [o for o in result["outsiders"] if o.get("outsider_pick")]
        for o in out:
            odds = o.get("morning_price", "?")
            print(
                f"  {o['race_id'].split('-')[-1]}  {o['horse']:<28}"
                f"  EW    @ {_fmt_odds(float(odds)) if isinstance(odds,(int,float)) else odds:<8}"
                f"  {o['stake_pts']:.2f}pt  £{o['stake_gbp']:.2f} EW"
            )
        if item_extra:
            print(f"  1600  {'Item':<28}  WIN*  @ 9/4      1.00pt  £{item_extra:.2f}  [SPECULATIVE]")
        print(f"\n  Doubles: {ps['doubles_count']}  Trebles: {ps['trebles_count']}"
              f"  Accas: {ps['accumulators_count']}")
        print(f"  Total stake:  £{ps['total_stake_gbp'] + item_extra:.2f}")
        print(f"  Max return:   £{ps['max_potential_return_gbp']:.2f}")

    _summarise("FRIDAY 5-Jun (bets-2026-06-05.json)", fri_result)
    _summarise(
        "SATURDAY 6-Jun GREEN (bets-2026-06-06.json)",
        sat_green_result,
        item_extra=1.0,
    )
    _summarise("SATURDAY 6-Jun HOLD (bets-2026-06-06-soft-contingency.json)", sat_hold_result)

    print(f"\n{'═'*60}")
    print("  All outputs written. Run tests: pytest tests/test_betting.py")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    main()
