"""betting.py — Betting Strategy Module v0.1
==========================================
Turns Kaylee's score_race() outputs into actionable bet recommendations
with stake sizing (fractional Kelly), bet-type selection (WIN/EW/PASS),
and multi-leg construction (doubles, trebles, accumulators, Lucky 15).

DISCLAIMER: For entertainment only. 18+. Gamble responsibly. BeGambleAware.org.

Author:  Badger (Betting Strategist — APEX Squad)
Date:    2026-06-02
Version: 0.1

Methodology
-----------
- Singles WIN  : model rank #1 AND confidence HIGH AND edge ≥ win_threshold_pct
- Singles EW   : model rank #1 AND confidence HIGH/MED AND (win_edge + place_edge) ≥ ew_combined_threshold_pct
- Doubles      : 2+ HIGH-confidence WIN singles from different races
- Trebles      : 3+ HIGH-confidence WIN singles from different races
- Accumulators : 4+ HIGH-confidence WIN singles, only when ≥ min_high_confidence_for_acca exist
- Lucky 15     : exactly the first 4 qualifying WIN singles; 15 bets (4S+6D+4T+1F)
- Stake        : fractional Kelly (default 0.25), capped at 5% bankroll per single
- Unit         : 1 point = 1% of bankroll
"""

from __future__ import annotations

import re
from itertools import combinations
from typing import Any

DISCLAIMER = (
    "For entertainment only. 18+. Gamble responsibly. BeGambleAware.org."
)

_REQUIRED_SCORE_KEYS: frozenset[str] = frozenset({"ranked_runners", "confidence"})
_REQUIRED_RUNNER_KEYS: frozenset[str] = frozenset({"rank", "horse", "score"})


# ---------------------------------------------------------------------------
# Public: configuration
# ---------------------------------------------------------------------------


def default_config() -> dict:
    """Return all tunable betting-strategy parameters.

    All thresholds are intentionally conservative defaults.
    Override per-run by passing a mutated copy to build_bets().

    Returns
    -------
    dict
        Nested configuration with sections:
        ``edge``, ``kelly``, ``ew``, ``multis``, ``lucky15``.

    Examples
    --------
    >>> cfg = default_config()
    >>> cfg["edge"]["win_threshold_pct"]
    15.0
    >>> cfg["kelly"]["fraction"]
    0.25
    """
    return {
        "edge": {
            # Minimum model edge over implied probability to recommend WIN
            "win_threshold_pct": 15.0,
            # Minimum (win_edge_pct + place_edge_pct) to recommend EW
            "ew_combined_threshold_pct": 20.0,
        },
        "kelly": {
            "fraction": 0.25,                 # quarter-Kelly (conservative)
            "max_stake_pct_per_single": 5.0,  # hard cap: 5 pts = 5% of bankroll
            "min_stake_pts": 0.25,            # floor: ¼ point minimum
        },
        "ew": {
            "place_fraction": 0.20,           # 1/5 odds for place payment
            "large_field_threshold": 7,       # fields > 7 runners pay 3 places
            "places_paid_large": 3,
            "places_paid_small": 2,
        },
        "multis": {
            # Need at least this many HIGH-confidence picks to unlock accas
            "min_high_confidence_for_acca": 3,
            "max_acca_legs": 6,
            "double_unit_pts": 0.50,  # stake per double bet (in points)
            "treble_unit_pts": 0.50,
            "acca_unit_pts": 0.50,
        },
        "lucky15": {
            "unit_pts": 0.10,  # per individual bet (×15 = 1.5 pts total)
            "min_legs": 4,
        },
        "outsiders": {
            # Minimum decimal odds to qualify as a value outsider
            "min_odds": 6.0,
            # Minimum rank disagreement (market_rank - model_rank) required
            "min_rank_delta": 1,
            # Flat EW unit stake in points (1 pt = 1% of bankroll); NEVER Kelly
            "stake_pts": 0.25,
            # Hard cap: one outsider pick per race
            "max_per_race": 1,
            # Max % of bankroll committed across ALL outsider EW stakes combined
            "bankroll_cap_pct": 5.0,
            # EW place fraction for outsiders: 1/4 odds (0.25)
            "ew_place_fraction": 0.25,
        },
    }


# ---------------------------------------------------------------------------
# Public: odds parsing
# ---------------------------------------------------------------------------


def parse_odds(odds_raw: Any) -> float | None:
    """Parse bookmaker odds into a decimal price.

    Handles:
    - Fractional strings : "3/1" → 4.0, "7/2" → 4.5, "11/4" → 3.75
    - Decimal strings    : "4.0" → 4.0, "2.5" → 2.5
    - Decimal floats/int : 4.0 → 4.0, 4 → 4.0
    - Evens shorthand    : "evs" / "evens" → 2.0
    - Missing/invalid    : None, "SP", "TBC", "N/A" → None (bet marked PASS)

    Parameters
    ----------
    odds_raw : Any
        Raw odds value from racecard data.

    Returns
    -------
    float | None
        Decimal odds (e.g. 4.0 for 3/1) or None if not parseable.

    Examples
    --------
    >>> parse_odds("3/1")
    4.0
    >>> parse_odds("7/2")
    4.5
    >>> parse_odds("4.0")
    4.0
    >>> parse_odds(5)
    5.0
    >>> parse_odds("evs")
    2.0
    >>> parse_odds(None) is None
    True
    >>> parse_odds("SP") is None
    True
    """
    if odds_raw is None:
        return None
    s = str(odds_raw).strip().lower()
    if not s or s in ("sp", "n/a", "tbc", "none", "-", ""):
        return None
    if s in ("evs", "evens"):
        return 2.0
    # Fractional: "3/1", "7/2", "11/4", "100/30"
    m = re.match(r"^(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)$", s)
    if m:
        num, den = float(m.group(1)), float(m.group(2))
        if den == 0:
            return None
        return round(num / den + 1.0, 4)
    # Decimal (float or integer string)
    try:
        dec = float(s)
        return round(dec, 4) if dec >= 1.0 else None
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Internal: probability helpers
# ---------------------------------------------------------------------------


def _implied_prob(decimal_odds: float) -> float:
    """1 / decimal_odds → bookmaker-implied win probability."""
    return round(1.0 / decimal_odds, 6)


def _scores_to_win_probs(ranked_runners: list[dict]) -> dict[str, float]:
    """Score-proportional win probability per horse.

    model_prob_i = score_i / Σ(all scores in race)

    Uses max(score, 0) so a zero-scored horse doesn't cause problems.
    If all scores are zero, falls back to uniform distribution.
    """
    scores = {
        r.get("horse", f"runner_{i}"): max(0.0, float(r.get("score", 0)))
        for i, r in enumerate(ranked_runners)
    }
    total = sum(scores.values())
    if total <= 0:
        n = max(1, len(ranked_runners))
        return {h: round(1.0 / n, 6) for h in scores}
    return {h: round(s / total, 6) for h, s in scores.items()}


def _estimate_place_prob(win_prob: float, places_paid: int) -> float:
    """Estimate probability of finishing in the top *places_paid* positions.

    Approximation: place_prob ≈ min(0.95, win_prob × places_paid)

    Rationale: the expected number of top-k finishes for a horse with
    win probability p is k × p (linearity of expectation). Bounded at
    0.95 to prevent absurd implied prices on short-priced favourites.

    Show your maths example: p=0.25, k=3 → place_prob=0.75
    """
    return round(min(0.95, win_prob * places_paid), 6)


def _ew_place_decimal(win_decimal: float, place_fraction: float) -> float:
    """EW place decimal odds from win decimal odds.

    EW place pays (win_decimal - 1) × place_fraction + 1.
    Example: win 4.0 at 1/5 odds → place = (4.0-1) × 0.2 + 1 = 1.6
    """
    return round((win_decimal - 1.0) * place_fraction + 1.0, 4)


def _edge_pct(model_prob: float, implied_prob: float) -> float:
    """Percentage edge over the bookmaker-implied probability.

    edge_pct = (model_prob - implied_prob) / implied_prob × 100

    Positive = our model thinks the horse is more likely to win than the
    price implies. Negative = book has shorter price than our model justifies.
    """
    if implied_prob <= 0:
        return 0.0
    return round((model_prob - implied_prob) / implied_prob * 100.0, 2)


# ---------------------------------------------------------------------------
# Internal: stake sizing
# ---------------------------------------------------------------------------


def _kelly_stake_pts(
    model_prob: float,
    decimal_odds: float,
    kelly_fraction: float,
    max_pct: float,
    min_pts: float,
) -> float:
    """Fractional Kelly stake in points (1 pt = 1% of bankroll).

    Kelly formula:
        f* = (b × p − q) / b
    where:
        b = decimal_odds − 1   (net odds: profit per unit staked)
        p = model_prob
        q = 1 − p (probability of loss)

    Fractional Kelly: f = kelly_fraction × f*
    Stake in points : min(max_pct, max(min_pts, f × 100))

    Returns 0.0 when Kelly is zero or negative (no modelled edge).
    """
    b = decimal_odds - 1.0
    q = 1.0 - model_prob
    if b <= 0 or model_prob <= 0:
        return min_pts
    full_kelly = (b * model_prob - q) / b
    if full_kelly <= 0:
        return 0.0  # model says don't bet
    frac = full_kelly * kelly_fraction
    pts = frac * 100.0
    pts = min(pts, max_pct)
    pts = max(pts, min_pts)
    return round(pts, 2)


def _pts_to_gbp(pts: float, bankroll: float) -> float:
    """Convert stake points to GBP.  1 pt = 1% of bankroll."""
    return round(pts * bankroll / 100.0, 2)


def _places_paid_for_field(field_size: int, cfg: dict) -> int:
    ew = cfg["ew"]
    if field_size > ew["large_field_threshold"]:
        return ew["places_paid_large"]
    return ew["places_paid_small"]


# ---------------------------------------------------------------------------
# Internal: single bet construction
# ---------------------------------------------------------------------------


def _build_single(
    race_entry: dict,
    top_runner: dict,
    model_prob: float,
    all_runners: list[dict],
    bankroll: float,
    cfg: dict,
) -> dict:
    """Build the single-bet dict for rank-1 runner in a race.

    Decision path (in order):
    1. No parseable odds               → bet_type "PASS", rationale "No odds available"
    2. confidence HIGH, win_edge ≥ thr → bet_type "WIN"
    3. confidence HIGH/MED, combined
       EW edge ≥ thr                   → bet_type "EW"
    4. Otherwise                       → bet_type "PASS" with reason

    All decisions show the underlying maths in the ``rationale`` field.
    """
    race_id = race_entry.get("race_id", "unknown")
    horse = top_runner.get("horse", "Unknown")
    score = float(top_runner.get("score", 0))
    confidence = race_entry.get("confidence", "LOW")
    field_size = max(1, len(all_runners))

    # PASS stub — overwritten if a bet condition is met
    stub: dict[str, Any] = {
        "race_id": race_id,
        "horse": horse,
        "bet_type": "PASS",
        "stake_pts": 0.0,
        "stake_gbp": 0.0,
        "model_prob": round(model_prob, 4),
        "implied_prob": None,
        "edge_pct": None,
        "expected_return_gbp": 0.0,
        "rationale": "Below confidence/edge threshold",
    }

    # --- Odds ---
    raw_odds = top_runner.get("odds") or top_runner.get("morning_price")
    dec_odds = parse_odds(raw_odds)
    if dec_odds is None:
        stub["rationale"] = "No odds available"
        return stub

    impl_prob = _implied_prob(dec_odds)
    win_edge = _edge_pct(model_prob, impl_prob)
    stub["implied_prob"] = round(impl_prob, 4)
    stub["edge_pct"] = win_edge

    kcfg = cfg["kelly"]
    edge_cfg = cfg["edge"]

    # --- WIN path ---
    if confidence == "HIGH" and win_edge >= edge_cfg["win_threshold_pct"]:
        stake_pts = _kelly_stake_pts(
            model_prob,
            dec_odds,
            kcfg["fraction"],
            kcfg["max_stake_pct_per_single"],
            kcfg["min_stake_pts"],
        )
        stake_gbp = _pts_to_gbp(stake_pts, bankroll)
        expected_return = round(stake_gbp * model_prob * dec_odds, 2)
        return {
            "race_id": race_id,
            "horse": horse,
            "bet_type": "WIN",
            "stake_pts": stake_pts,
            "stake_gbp": stake_gbp,
            "model_prob": round(model_prob, 4),
            "implied_prob": round(impl_prob, 4),
            "edge_pct": win_edge,
            "odds_decimal": dec_odds,
            "odds_raw": str(raw_odds),
            "expected_return_gbp": expected_return,
            "rationale": (
                f"Rank #1 (score {score:.1f}), confidence HIGH, "
                f"model_prob {model_prob:.4f} vs implied {impl_prob:.4f} "
                f"→ edge {win_edge:.1f}% ≥ {edge_cfg['win_threshold_pct']:.0f}% threshold. "
                f"Quarter-Kelly stake: {stake_pts:.2f}pts (£{stake_gbp:.2f}) @ {raw_odds}."
            ),
        }

    # --- EW path ---
    places = _places_paid_for_field(field_size, cfg)
    place_prob = _estimate_place_prob(model_prob, places)
    place_dec = _ew_place_decimal(dec_odds, cfg["ew"]["place_fraction"])
    implied_place_prob = _implied_prob(place_dec) if place_dec > 1.0 else 1.0
    place_edge = _edge_pct(place_prob, implied_place_prob)
    combined_edge = win_edge + place_edge

    if confidence in ("HIGH", "MED") and combined_edge >= edge_cfg["ew_combined_threshold_pct"]:
        stake_pts = _kelly_stake_pts(
            model_prob,
            dec_odds,
            kcfg["fraction"],
            kcfg["max_stake_pct_per_single"],
            kcfg["min_stake_pts"],
        )
        # EW = one stake on win + one stake on place (equal units)
        total_stake_pts = round(stake_pts * 2, 2)
        total_stake_gbp = _pts_to_gbp(total_stake_pts, bankroll)
        win_stake_gbp = _pts_to_gbp(stake_pts, bankroll)
        exp_win = model_prob * dec_odds * win_stake_gbp
        exp_place = place_prob * place_dec * win_stake_gbp
        expected_return = round(exp_win + exp_place, 2)
        return {
            "race_id": race_id,
            "horse": horse,
            "bet_type": "EW",
            "stake_pts": total_stake_pts,
            "stake_gbp": total_stake_gbp,
            "model_prob": round(model_prob, 4),
            "implied_prob": round(impl_prob, 4),
            "edge_pct": win_edge,
            "place_edge_pct": round(place_edge, 2),
            "combined_edge_pct": round(combined_edge, 2),
            "odds_decimal": dec_odds,
            "odds_raw": str(raw_odds),
            "places_paid": places,
            "model_place_prob": round(place_prob, 4),
            "place_odds_decimal": place_dec,
            "expected_return_gbp": expected_return,
            "rationale": (
                f"Rank #1 (score {score:.1f}), confidence {confidence}. "
                f"Win edge {win_edge:.1f}% + place edge {place_edge:.1f}% "
                f"= {combined_edge:.1f}% combined ≥ {edge_cfg['ew_combined_threshold_pct']:.0f}% EW threshold. "
                f"EW: {stake_pts:.2f}pts WIN + {stake_pts:.2f}pts PLACE "
                f"= {total_stake_pts:.2f}pts total (£{total_stake_gbp:.2f}) @ {raw_odds} "
                f"({places} places, 1/{int(1/cfg['ew']['place_fraction'])} odds)."
            ),
        }

    # --- PASS (fell through) ---
    stub["edge_pct"] = win_edge
    stub["rationale"] = (
        f"Confidence {confidence}, win edge {win_edge:.1f}%, "
        f"combined EW edge {combined_edge:.1f}% — below thresholds "
        f"({edge_cfg['win_threshold_pct']:.0f}% WIN / "
        f"{edge_cfg['ew_combined_threshold_pct']:.0f}% EW combined)."
    )
    return stub


# ---------------------------------------------------------------------------
# Internal: multi-leg helpers
# ---------------------------------------------------------------------------


def _multi_leg_entry(single: dict) -> dict:
    """Extract the compact leg descriptor used inside multi-leg dicts."""
    return {
        "race_id": single["race_id"],
        "horse": single["horse"],
        "odds_decimal": single.get("odds_decimal", 0.0),
        "model_prob": single["model_prob"],
    }


def _build_doubles(
    legs: list[dict],
    unit_pts: float,
    bankroll: float,
) -> list[dict]:
    """Build all valid doubles from qualifying WIN singles.

    Correlation guard: legs from the same race_id are never combined.
    """
    doubles = []
    for a, b in combinations(legs, 2):
        if a["race_id"] == b["race_id"]:
            continue  # same-race correlation forbidden
        combined_prob = round(a["model_prob"] * b["model_prob"], 6)
        combined_dec = a.get("odds_decimal", 0.0) * b.get("odds_decimal", 0.0)
        stake_gbp = _pts_to_gbp(unit_pts, bankroll)
        pot_return = round(stake_gbp * combined_dec, 2)
        ev_gbp = round(combined_prob * pot_return - stake_gbp, 2)
        doubles.append(
            {
                "legs": [_multi_leg_entry(a), _multi_leg_entry(b)],
                "combined_stake_gbp": stake_gbp,
                "potential_return_gbp": pot_return,
                "combined_prob": combined_prob,
                "expected_value_gbp": ev_gbp,
                "rationale": (
                    f"Double: {a['horse']} × {b['horse']}. "
                    f"Model probs: {a['model_prob']:.4f} × {b['model_prob']:.4f} "
                    f"= {combined_prob:.5f}. Dec odds product: {combined_dec:.2f}. "
                    f"EV: £{ev_gbp:.2f}."
                ),
            }
        )
    return doubles


def _build_trebles(
    legs: list[dict],
    unit_pts: float,
    bankroll: float,
) -> list[dict]:
    """Build all valid trebles from qualifying WIN singles.

    Correlation guard: all three race_ids must be distinct.
    """
    trebles = []
    for combo in combinations(legs, 3):
        race_ids = [leg["race_id"] for leg in combo]
        if len(set(race_ids)) < 3:
            continue
        combined_prob = round(
            combo[0]["model_prob"] * combo[1]["model_prob"] * combo[2]["model_prob"], 6
        )
        combined_dec = (
            combo[0].get("odds_decimal", 0.0)
            * combo[1].get("odds_decimal", 0.0)
            * combo[2].get("odds_decimal", 0.0)
        )
        stake_gbp = _pts_to_gbp(unit_pts, bankroll)
        pot_return = round(stake_gbp * combined_dec, 2)
        ev_gbp = round(combined_prob * pot_return - stake_gbp, 2)
        trebles.append(
            {
                "legs": [_multi_leg_entry(leg) for leg in combo],
                "combined_stake_gbp": stake_gbp,
                "potential_return_gbp": pot_return,
                "combined_prob": combined_prob,
                "expected_value_gbp": ev_gbp,
                "rationale": (
                    f"Treble: {' × '.join(leg['horse'] for leg in combo)}. "
                    f"Combined prob {combined_prob:.5f}. "
                    f"Dec odds product: {combined_dec:.2f}. EV: £{ev_gbp:.2f}."
                ),
            }
        )
    return trebles


def _build_accumulators(
    legs: list[dict],
    unit_pts: float,
    bankroll: float,
    max_legs: int,
) -> list[dict]:
    """Build all valid accumulators (4+ legs) from qualifying WIN singles.

    Gated by caller: only called when n_high ≥ min_high_confidence_for_acca.
    Correlation guard: all leg race_ids must be distinct within each acca.
    """
    accas = []
    n = len(legs)
    for k in range(4, min(n, max_legs) + 1):
        for combo in combinations(legs, k):
            race_ids = [leg["race_id"] for leg in combo]
            if len(set(race_ids)) < k:
                continue
            combined_prob = 1.0
            combined_dec = 1.0
            for leg in combo:
                combined_prob *= leg["model_prob"]
                combined_dec *= leg.get("odds_decimal", 0.0)
            combined_prob = round(combined_prob, 6)
            stake_gbp = _pts_to_gbp(unit_pts, bankroll)
            pot_return = round(stake_gbp * combined_dec, 2)
            ev_gbp = round(combined_prob * pot_return - stake_gbp, 2)
            accas.append(
                {
                    "legs": [_multi_leg_entry(leg) for leg in combo],
                    "n_legs": k,
                    "combined_stake_gbp": stake_gbp,
                    "potential_return_gbp": pot_return,
                    "combined_prob": combined_prob,
                    "expected_value_gbp": ev_gbp,
                    "correlation_warning": (
                        f"All {k} races assumed independent. "
                        "Do not combine horses from the same race in any multi."
                    ),
                    "rationale": (
                        f"{k}-fold accumulator: "
                        f"{' × '.join(leg['horse'] for leg in combo)}. "
                        f"Combined prob {combined_prob:.6f}. "
                        f"Dec odds product: {combined_dec:.2f}. "
                        f"Potential return: £{pot_return:.2f}. EV: £{ev_gbp:.2f}."
                    ),
                }
            )
    return accas


# ---------------------------------------------------------------------------
# Internal: Lucky 15
# ---------------------------------------------------------------------------


def _build_lucky15(
    legs: list[dict],
    unit_pts: float,
    bankroll: float,
) -> dict | None:
    """Build a Lucky 15 from the first 4 qualifying WIN singles.

    Lucky 15 structure (4 selections = 15 bets):
        4 singles + 6 doubles + 4 trebles + 1 four-fold = 15 total

    Returns None if fewer than 4 qualifying legs, or if correlation
    guard would be violated (duplicate race_ids in first 4).
    """
    if len(legs) < 4:
        return None
    sel = legs[:4]
    race_ids = [leg["race_id"] for leg in sel]
    if len(set(race_ids)) < 4:
        return None  # correlation guard

    total_stake_pts = round(15 * unit_pts, 2)
    total_stake_gbp = _pts_to_gbp(total_stake_pts, bankroll)

    unit_gbp = _pts_to_gbp(unit_pts, bankroll)

    # Best-case return: all 4 legs win
    # Singles returns
    single_returns = [unit_gbp * sel[i]["odds_decimal"] for i in range(4)]
    # Doubles returns
    double_returns = [
        unit_gbp * sel[i]["odds_decimal"] * sel[j]["odds_decimal"]
        for i, j in combinations(range(4), 2)
    ]
    # Trebles returns
    treble_returns = [
        unit_gbp
        * sel[i]["odds_decimal"]
        * sel[j]["odds_decimal"]
        * sel[k]["odds_decimal"]
        for i, j, k in combinations(range(4), 3)
    ]
    # Four-fold return
    fourfold_return = (
        unit_gbp
        * sel[0]["odds_decimal"]
        * sel[1]["odds_decimal"]
        * sel[2]["odds_decimal"]
        * sel[3]["odds_decimal"]
    )

    best_case = round(
        sum(single_returns)
        + sum(double_returns)
        + sum(treble_returns)
        + fourfold_return,
        2,
    )

    # Expected return: weight each sub-bet by its combined probability
    # Singles
    exp_singles = sum(
        sel[i]["model_prob"] * unit_gbp * sel[i]["odds_decimal"] for i in range(4)
    )
    # Doubles
    exp_doubles = sum(
        sel[i]["model_prob"] * sel[j]["model_prob"]
        * unit_gbp * sel[i]["odds_decimal"] * sel[j]["odds_decimal"]
        for i, j in combinations(range(4), 2)
    )
    # Trebles
    exp_trebles = sum(
        sel[i]["model_prob"] * sel[j]["model_prob"] * sel[k]["model_prob"]
        * unit_gbp * sel[i]["odds_decimal"] * sel[j]["odds_decimal"] * sel[k]["odds_decimal"]
        for i, j, k in combinations(range(4), 3)
    )
    # Four-fold
    exp_fourfold = (
        sel[0]["model_prob"] * sel[1]["model_prob"]
        * sel[2]["model_prob"] * sel[3]["model_prob"]
        * unit_gbp
        * sel[0]["odds_decimal"] * sel[1]["odds_decimal"]
        * sel[2]["odds_decimal"] * sel[3]["odds_decimal"]
    )
    expected_return = round(
        exp_singles + exp_doubles + exp_trebles + exp_fourfold, 2
    )

    return {
        "legs": [_multi_leg_entry(leg) for leg in sel],
        "bets_breakdown": {
            "singles": 4,
            "doubles": 6,
            "trebles": 4,
            "fourfold": 1,
            "total": 15,
        },
        "unit_stake_pts": unit_pts,
        "unit_stake_gbp": round(unit_gbp, 2),
        "total_stake_pts": total_stake_pts,
        "total_stake_gbp": total_stake_gbp,
        "best_case_return_gbp": best_case,
        "expected_return_gbp": expected_return,
        "rationale": (
            f"Lucky 15: {', '.join(leg['horse'] for leg in sel)}. "
            f"15 bets × {unit_pts:.2f}pts = {total_stake_pts:.2f}pts "
            f"(£{total_stake_gbp:.2f}). "
            f"Best case (all 4 win): £{best_case:.2f}. "
            "Covering bets insure against 1–2 losing legs."
        ),
    }


# ---------------------------------------------------------------------------
# Internal: outsider picks
# ---------------------------------------------------------------------------


def _build_outsiders(
    scores: list[dict],
    bankroll: float,
    cfg: dict,
) -> list[dict]:
    """Build outsider value picks — one per race (or null where none qualifies).

    Qualifying criteria (all must hold):
    - ``market_rank`` ≥ 4  (not in bookmakers' top 3)
    - ``model_rank``  ≤ 4  (Kaylee's model rates the horse highly)
    - decimal odds    ≥ ``cfg["outsiders"]["min_odds"]`` (genuine long-shot)
    - ``rank_delta``  ≥ ``cfg["outsiders"]["min_rank_delta"]``
      where rank_delta = market_rank − model_rank (bigger = more disagreement)

    Tie-break: highest rank_delta; secondary: lowest model_rank.

    Stake: flat ``stake_pts`` (never Kelly); each-way (1/4 odds, standard
    place terms).  Total EW outlay = 2 × stake_gbp_per_leg.

    A 5% bankroll cap applies across ALL outsider EW stakes combined.

    Null signals are emitted (with a plain-English ``outsider_rationale``) when:
    - Fewer than 4 runners have real (non-synthetic) odds — can't rank the market.
    - All odds are ``odds_source == "synthetic"`` — insufficient signal.
    - No runner survives the qualifying filter.
    - Bankroll cap already reached.
    """
    out_cfg = cfg["outsiders"]
    min_odds: float = out_cfg["min_odds"]
    min_rank_delta: int = out_cfg["min_rank_delta"]
    stake_pts: float = out_cfg["stake_pts"]
    bankroll_cap_pct: float = out_cfg["bankroll_cap_pct"]
    ew_place_fraction: float = out_cfg["ew_place_fraction"]

    # Total outsider EW budget (win leg + place leg per race)
    max_total_outsider_gbp: float = bankroll * bankroll_cap_pct / 100.0
    cumulative_ew_stake: float = 0.0

    outsiders: list[dict] = []

    for entry in scores:
        if not _validate_entry(entry):
            continue

        race_id = entry.get("race_id", "unknown")
        race_name: str = (
            entry.get("race_name")
            or entry.get("race_meta", {}).get("name", "")
        )
        race_time: str = (
            entry.get("race_time")
            or entry.get("race_meta", {}).get("time", "")
        )
        runners: list[dict] = entry["ranked_runners"]

        # --- Classify odds availability ---
        runners_with_real_odds: list[dict] = []
        has_any_odds = False

        for r in runners:
            raw_odds = r.get("morning_price") or r.get("odds")
            dec = parse_odds(raw_odds)
            if dec is None:
                continue
            has_any_odds = True
            odds_source: str = r.get("odds_source", "")
            if odds_source == "synthetic":
                continue  # skip synthetic-only signal
            runners_with_real_odds.append(
                {
                    "runner": r,
                    "dec_odds": dec,
                    "raw_odds": raw_odds,
                    "odds_source": odds_source,
                    "horse": r.get("horse", ""),
                }
            )

        # Fallback: no real odds at all
        if not has_any_odds or not runners_with_real_odds:
            outsiders.append(
                {
                    "race_id": race_id,
                    "outsider_pick": None,
                    "outsider_rationale": "Insufficient market signal",
                }
            )
            continue

        # Need ≥4 runners with real odds to establish market rank 4+
        if len(runners_with_real_odds) < 4:
            outsiders.append(
                {
                    "race_id": race_id,
                    "outsider_pick": None,
                    "outsider_rationale": "Insufficient market signal",
                }
            )
            continue

        # Assign market ranks: 1 = shortest price (favourite)
        runners_with_real_odds.sort(key=lambda x: x["dec_odds"])
        market_rank_map: dict[str, dict] = {}
        for i, r_info in enumerate(runners_with_real_odds):
            r_info["market_rank"] = i + 1
            market_rank_map[r_info["horse"]] = r_info

        # --- Find qualifying candidates ---
        candidates: list[dict] = []
        for r in runners:
            horse = r.get("horse", "")
            model_rank = int(r.get("rank", 99))

            if horse not in market_rank_map:
                continue  # no real odds for this runner

            r_info = market_rank_map[horse]
            market_rank: int = r_info["market_rank"]
            dec_odds: float = r_info["dec_odds"]

            if market_rank < 4:
                continue  # bookmakers' top 3 — not a value outsider
            if model_rank > 4:
                continue  # model doesn't rate highly enough
            if dec_odds < min_odds:
                continue  # not a genuine long-shot price
            rank_delta = market_rank - model_rank
            if rank_delta < min_rank_delta:
                continue  # no meaningful disagreement

            candidates.append(
                {
                    "runner": r,
                    "horse": horse,
                    "model_rank": model_rank,
                    "market_rank": market_rank,
                    "rank_delta": rank_delta,
                    "dec_odds": dec_odds,
                    "raw_odds": r_info["raw_odds"],
                    "odds_source": r_info["odds_source"],
                }
            )

        if not candidates:
            # Explain why: check for top-3 model / market overlap
            top3_model = [r.get("horse", "") for r in runners[:3]]
            top3_market = [
                r_info["horse"]
                for r_info in sorted(
                    market_rank_map.values(), key=lambda x: x["market_rank"]
                )[:3]
            ]
            if set(top3_model) == set(top3_market):
                rationale = (
                    "Top 3 in market also top 3 on model — no value outsider"
                )
            else:
                rationale = (
                    f"No runner meets outsider criteria "
                    f"(market rank ≥4, model rank ≤4, odds ≥{min_odds:.1f}, "
                    f"rank delta ≥{min_rank_delta})"
                )
            outsiders.append(
                {
                    "race_id": race_id,
                    "outsider_pick": None,
                    "outsider_rationale": rationale,
                }
            )
            continue

        # Best candidate: highest rank_delta; tie-break: lowest model_rank
        candidates.sort(key=lambda c: (-c["rank_delta"], c["model_rank"]))
        best = candidates[0]

        # --- Stake sizing: flat, never Kelly ---
        # 0.25pt or 1% of bankroll, whichever is lower
        stake_gbp_per_leg: float = min(
            _pts_to_gbp(stake_pts, bankroll),
            bankroll / 100.0,
        )
        ew_total_gbp: float = round(stake_gbp_per_leg * 2, 2)

        # Apply bankroll cap
        if cumulative_ew_stake + ew_total_gbp > max_total_outsider_gbp + 1e-9:
            outsiders.append(
                {
                    "race_id": race_id,
                    "outsider_pick": None,
                    "outsider_rationale": "Outsider bankroll cap reached",
                }
            )
            continue

        cumulative_ew_stake += ew_total_gbp

        # EW terms and potential returns
        field_size = len(runners)
        places = _places_paid_for_field(field_size, cfg)
        place_term_str = "-".join(str(i + 1) for i in range(places))
        ew_terms = f"1/4 odds, 1-{place_term_str}"

        win_return_gbp: float = round(stake_gbp_per_leg * best["dec_odds"], 2)
        place_dec: float = _ew_place_decimal(best["dec_odds"], ew_place_fraction)
        place_return_gbp: float = round(stake_gbp_per_leg * place_dec, 2)

        runner = best["runner"]

        outsiders.append(
            {
                "race_id": race_id,
                "race_name": race_name,
                "race_time": race_time,
                "horse": best["horse"],
                "trainer": runner.get("trainer", ""),
                "jockey": runner.get("jockey", ""),
                "morning_price": best["dec_odds"],
                "odds_source": best["odds_source"],
                "model_rank": best["model_rank"],
                "market_rank": best["market_rank"],
                "rank_delta": best["rank_delta"],
                "bet_type": "EW",
                "stake_pts": stake_pts,
                "stake_gbp": round(stake_gbp_per_leg, 2),
                "ew_terms": ew_terms,
                "potential_return_gbp_win": win_return_gbp,
                "potential_return_gbp_place": place_return_gbp,
                "rationale": (
                    f"Model rates {best['model_rank']}; "
                    f"market rates {best['market_rank']}. "
                    f"Disagreement of {best['rank_delta']} ranks — value play."
                ),
                "outsider_pick": best["horse"],
            }
        )

    return outsiders


# ---------------------------------------------------------------------------
# Internal: validation
# ---------------------------------------------------------------------------


def _validate_entry(entry: Any) -> bool:
    """Return True if a score dict has minimum required structure.

    Defends against malformed scoring.py output or schema changes.
    """
    if not isinstance(entry, dict):
        return False
    if not _REQUIRED_SCORE_KEYS.issubset(entry.keys()):
        return False
    runners = entry.get("ranked_runners")
    if not isinstance(runners, list) or len(runners) == 0:
        return False
    top = runners[0]
    if not isinstance(top, dict):
        return False
    return _REQUIRED_RUNNER_KEYS.issubset(top.keys())


# ---------------------------------------------------------------------------
# Internal: portfolio summary
# ---------------------------------------------------------------------------


def _portfolio_summary(
    singles: list[dict],
    doubles: list[dict],
    trebles: list[dict],
    accumulators: list[dict],
    lucky15: dict | None,
    outsiders: list[dict],
) -> dict:
    """Roll up total stake, max potential, expected value, counts, and outsider tally."""
    active = [s for s in singles if s["bet_type"] != "PASS"]

    total_stake = sum(s["stake_gbp"] for s in active)
    total_stake += sum(d["combined_stake_gbp"] for d in doubles)
    total_stake += sum(t["combined_stake_gbp"] for t in trebles)
    total_stake += sum(a["combined_stake_gbp"] for a in accumulators)
    if lucky15:
        total_stake += lucky15["total_stake_gbp"]

    max_potential = sum(s["expected_return_gbp"] for s in active)
    max_potential += sum(d["potential_return_gbp"] for d in doubles)
    max_potential += sum(t["potential_return_gbp"] for t in trebles)
    max_potential += sum(a["potential_return_gbp"] for a in accumulators)
    if lucky15:
        max_potential += lucky15["best_case_return_gbp"]

    # Expected value = Σ(expected_return - stake) for each bet
    ev = sum(s["expected_return_gbp"] - s["stake_gbp"] for s in active)
    ev += sum(d.get("expected_value_gbp", 0.0) for d in doubles)
    ev += sum(t.get("expected_value_gbp", 0.0) for t in trebles)
    ev += sum(a.get("expected_value_gbp", 0.0) for a in accumulators)
    if lucky15:
        ev += lucky15.get("expected_return_gbp", 0.0) - lucky15["total_stake_gbp"]

    # --- Outsider summary (separate budget, separate tally) ---
    valid_outsiders = [o for o in outsiders if o.get("outsider_pick") is not None]
    outsider_total_ew_stake = sum(
        o.get("stake_gbp", 0.0) * 2 for o in valid_outsiders
    )
    outsider_total_win_return = sum(
        o.get("potential_return_gbp_win", 0.0) for o in valid_outsiders
    )
    outsider_total_place_return = sum(
        o.get("potential_return_gbp_place", 0.0) for o in valid_outsiders
    )
    # Outsider EW stakes ARE included in the overall total for full exposure view
    total_stake += outsider_total_ew_stake

    rec_count = (
        len(active)
        + len(doubles)
        + len(trebles)
        + len(accumulators)
        + (1 if lucky15 else 0)
        + len(valid_outsiders)
    )

    return {
        "total_stake_gbp": round(total_stake, 2),
        "max_potential_return_gbp": round(max_potential, 2),
        "expected_value_gbp": round(ev, 2),
        "rec_count": rec_count,
        "active_singles": len(active),
        "passed_singles": len([s for s in singles if s["bet_type"] == "PASS"]),
        "doubles_count": len(doubles),
        "trebles_count": len(trebles),
        "accumulators_count": len(accumulators),
        "outsider_summary": {
            "count": len(valid_outsiders),
            "total_stake_gbp": round(outsider_total_ew_stake, 2),
            "total_potential_return_gbp_win": round(outsider_total_win_return, 2),
            "total_potential_return_gbp_place": round(outsider_total_place_return, 2),
        },
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_bets(
    scores: list[dict],
    bankroll: float = 100.0,
    config: dict | None = None,
) -> dict:
    """Turn scored race results into actionable bet recommendations.

    Parameters
    ----------
    scores : list[dict]
        List of score_race() outputs, each optionally enriched with odds.
        Each dict must have ``ranked_runners`` (list) and ``confidence`` (str).
        Each ranked runner may carry an ``odds`` or ``morning_price`` key
        (set by the integration layer before calling build_bets).
        If no odds key is present the runner is marked PASS; no prices
        are invented.

    bankroll : float
        Current bankroll in GBP.  1 point = 1% of bankroll.

    config : dict | None
        Betting config dict from default_config().  Defaults are used if None.

    Returns
    -------
    dict
        ``{"bankroll", "singles", "doubles", "trebles",
           "accumulators", "lucky_15", "portfolio_summary",
           "disclaimer"}``

        ``singles`` includes both actionable bets (WIN/EW) and PASS entries
        so the caller can audit every race considered.

    Examples
    --------
    >>> result = build_bets([], 100.0, default_config())
    >>> result["singles"]
    []
    >>> result["disclaimer"]
    'For entertainment only. 18+. Gamble responsibly. BeGambleAware.org.'
    >>> result["portfolio_summary"]["total_stake_gbp"]
    0.0
    """
    cfg = config if config is not None else default_config()
    bankroll = float(bankroll)

    empty_summary: dict[str, Any] = {
        "total_stake_gbp": 0.0,
        "max_potential_return_gbp": 0.0,
        "expected_value_gbp": 0.0,
        "rec_count": 0,
        "active_singles": 0,
        "passed_singles": 0,
        "doubles_count": 0,
        "trebles_count": 0,
        "accumulators_count": 0,
        "outsider_summary": {
            "count": 0,
            "total_stake_gbp": 0.0,
            "total_potential_return_gbp_win": 0.0,
            "total_potential_return_gbp_place": 0.0,
        },
    }

    if not scores:
        return {
            "bankroll": bankroll,
            "singles": [],
            "doubles": [],
            "trebles": [],
            "accumulators": [],
            "lucky_15": None,
            "outsiders": [],
            "portfolio_summary": empty_summary,
            "disclaimer": DISCLAIMER,
        }

    # --- 1. Build singles (one per race entry) ---
    singles: list[dict] = []
    for entry in scores:
        if not _validate_entry(entry):
            continue  # skip malformed entries gracefully
        runners = entry["ranked_runners"]
        top = runners[0]
        probs = _scores_to_win_probs(runners)
        horse_name = top.get("horse", "")
        model_prob = probs.get(horse_name, 1.0 / max(1, len(runners)))
        single = _build_single(entry, top, model_prob, runners, bankroll, cfg)
        singles.append(single)

    # --- 2. Qualifying legs for multi-leg bets ---
    # Only HIGH-confidence WIN singles with valid odds qualify.
    qualifying_raw: list[dict] = [s for s in singles if s.get("bet_type") == "WIN"]

    # Correlation / dedup guard: one leg per race_id
    seen: set[str] = set()
    qualifying: list[dict] = []
    for s in qualifying_raw:
        rid = s["race_id"]
        if rid not in seen:
            seen.add(rid)
            qualifying.append(s)

    n_high = len(qualifying)
    mcfg = cfg["multis"]

    # --- 3. Doubles (need ≥2 qualifying legs) ---
    doubles: list[dict] = []
    if n_high >= 2:
        doubles = _build_doubles(qualifying, mcfg["double_unit_pts"], bankroll)

    # --- 4. Trebles (need ≥3 qualifying legs) ---
    trebles: list[dict] = []
    if n_high >= 3:
        trebles = _build_trebles(qualifying, mcfg["treble_unit_pts"], bankroll)

    # --- 5. Accumulators (4+ legs; gated by min_high_confidence_for_acca) ---
    accumulators: list[dict] = []
    # Acca needs ≥4 legs AND n_high must meet the quality gate
    acca_min = max(mcfg["min_high_confidence_for_acca"], 4)
    if n_high >= acca_min:
        accumulators = _build_accumulators(
            qualifying, mcfg["acca_unit_pts"], bankroll, mcfg["max_acca_legs"]
        )

    # --- 6. Lucky 15 (need ≥4 qualifying legs) ---
    lucky15: dict | None = None
    l15_cfg = cfg["lucky15"]
    if n_high >= l15_cfg["min_legs"]:
        lucky15 = _build_lucky15(qualifying, l15_cfg["unit_pts"], bankroll)

    # --- 7. Outsider value picks (one per race) ---
    outsiders = _build_outsiders(scores, bankroll, cfg)

    # --- 8. Portfolio summary ---
    summary = _portfolio_summary(singles, doubles, trebles, accumulators, lucky15, outsiders)

    return {
        "bankroll": bankroll,
        "singles": singles,
        "doubles": doubles,
        "trebles": trebles,
        "accumulators": accumulators,
        "lucky_15": lucky15,
        "outsiders": outsiders,
        "portfolio_summary": summary,
        "disclaimer": DISCLAIMER,
    }
