"""
scoring.py — Race analysis scoring model v0.4
=============================================

Turns a Runner dict into a score (0-100) and score_breakdown.

Author:  Kaylee (Data Engineer)
Date:    2026-06-02
Version: 0.4  (trial_form signal added; all v0.3 weights × 0.92)

Usage (CLI):
    python -m scoring path/to/racecard.json

Racecard JSON shape::

    {
        "races": [
            {
                "race_id": "epsom_1",
                "course": "Epsom",
                "distance_f": 5.0,
                "going": "good",
                "runners": [ { ...runner fields... } ]
            }
        ]
    }
"""

from __future__ import annotations

import json
import math
import sys
from typing import Any

try:  # supports both `python -m src...` and direct `sys.path` test imports
    from going import normalise_going, score_going_fit
    from pace import extended_draw_signal, infer_run_style, pace_signal, project_race_pace
    from cd_form import cd_form_signal
    from sires import sire_stamina_signal
    from trial_form import trial_form_signal
except ImportError:  # pragma: no cover
    from .going import normalise_going, score_going_fit
    from .pace import extended_draw_signal, infer_run_style, pace_signal, project_race_pace
    from .cd_form import cd_form_signal
    from .sires import sire_stamina_signal
    from .trial_form import trial_form_signal


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_default_config() -> dict:
    """Return the default model configuration.

    All weights must sum to 1.0 (validated at runtime).

    Returns
    -------
    dict
        Nested configuration dict with keys:
        ``weights``, ``form``, ``cd``, ``draw``, ``class_move``,
        ``going_fit``, ``confidence``, ``competitiveness``,
        ``trainer_bumps``, ``jockey_bumps``.

    Example
    -------
    >>> cfg = load_default_config()
    >>> round(sum(cfg["weights"].values()), 10)
    1.0
    >>> cfg["weights"]["going_fit"]
    0.15
    """
    return {
        "weights": {
            # v0.4 weights — adds `trial_form` (0.0800) as highest-leverage
            # Derby/Oaks signal.  All v0.3 weights scaled × 0.9200 to make
            # room.  Total sums to exactly 1.0000.
            # `course_distance` powered by RP badge extraction (cd_form.py).
            "class_rating":    0.2363,
            "recent_form":     0.1351,
            "trainer_form":    0.0674,
            "jockey":          0.0674,
            "course_distance": 0.0674,
            "going":           0.0338,
            "draw_bias":       0.0525,
            "class_move":      0.0338,
            "going_fit":       0.1191,
            "pace":            0.0612,
            "sire_stamina":    0.0460,
            "trial_form":      0.0800,
        },
        "form": {
            "position_points":        {1: 10, 2: 6, 3: 4, 4: 2},
            "recency_weights":        [1.0, 0.75, 0.5, 0.3, 0.15],
            "absence_threshold_days": 120,
            "absence_penalty":        5,
        },
        "cd": {
            "cd_win_bonus":            15,
            "cd_place_bonus":           8,
            "course_win_bonus":         5,
            "course_place_bonus":       3,
            "first_time_epsom_penalty": 10,
            "epsom_long_dist_furlongs": 12,  # 1m4f threshold for penalty
        },
        "draw": {
            # Only applied for 5f Dash at Epsom
            "material_distances": [5.0],
            "material_courses":   ["Epsom"],
            "good_goings":        ["good", "good to firm"],
            "low_draw_threshold": 4,
            "high_draw_threshold": 10,
            "low_draw_signal":    80,
            "mid_draw_signal":    50,
            "high_draw_signal":   30,
        },
        "class_move": {
            "drop_signal":  70,
            "same_signal":  50,
            "rise_signal":  30,
        },
        "going": {
            "match_signal":   80,
            "any_signal":     55,
            "neutral_signal": 50,
            "mismatch_signal": 25,
        },
        "confidence": {
            "high_gap":          15.0,
            "med_gap":            5.0,
            "min_score_for_bet": 40.0,
        },
        "competitiveness": {
            "wide_open_stdev":   8.0,
            "clear_fav_stdev":  15.0,
        },
        # Raw bump values 0–10; will be normalised to 0–100 signal
        "trainer_bumps": {
            "Aidan O'Brien":        10,
            "John Gosden":           9,
            "Gosden & Gosden":       9,
            "Charlie Appleby":       9,
            "Richard Hannon":        8,
            "Andrew Balding":        8,
            "William Haggas":        8,
            "Roger Varian":          7,
            "Ralph Beckett":         7,
        },
        "jockey_bumps": {
            "Ryan Moore":      10,
            "William Buick":    9,
            "Oisin Murphy":     9,
            "James Doyle":      7,
            "Tom Marquand":     7,
            "Robert Havlin":    6,
        },
    }


def score_runner(runner: dict, race: dict, config: dict) -> dict:
    """Compute signal values for a single runner.

    Does NOT normalise scores to the race — call ``score_race`` for
    normalised, ranked output.

    Parameters
    ----------
    runner : dict
        Runner fields; see spec for full shape.
    race : dict
        Race-level context (course, distance_f, going).
    config : dict
        Config dict (from ``load_default_config`` or overrides).

    Returns
    -------
    dict
        ``{"raw_signals": {...}, "raw_score": float,
           "missing_data_flags": list[str]}``
        where ``raw_signals`` has one key per signal (each 0–100)
        and ``raw_score`` is the weighted sum (also 0–100 pre-normalise).

    Example
    -------
    >>> cfg = load_default_config()
    >>> race = {"race_id": "r1", "course": "Epsom",
    ...         "distance_f": 5.0, "going": "good", "runners": []}
    >>> runner = {
    ...     "horse": "Test Horse", "rpr": 105.0, "ts": None,
    ...     "or_rating": None, "runs": [], "trainer": "Ryan Moore",
    ...     "jockey": "Ryan Moore", "draw": 2, "cd_wins": 1,
    ...     "cd_places": 0, "course_wins": 0, "course_places": 0,
    ...     "first_time_epsom": False, "going_preference": "good",
    ...     "last_class": 2, "current_class": 2,
    ... }
    >>> result = score_runner(runner, race, cfg)
    >>> "raw_signals" in result
    True
    >>> 0 <= result["raw_score"] <= 100
    True
    """
    _validate_weights(config["weights"])
    flags: list[str] = []

    raw_signals: dict[str, float] = {}

    # 1. Class / Rating signal (pre-zscore; z-score applied in score_race)
    best_rating = _best_rating(runner)
    if best_rating is None:
        raw_signals["class_rating"] = None  # type: ignore[assignment]
        flags.append("no_ratings")
    else:
        raw_signals["class_rating"] = float(best_rating)

    # 2. Recent form
    raw_signals["recent_form"] = _form_signal(runner, config["form"])

    # 3. Trainer form
    raw_signals["trainer_form"] = _trainer_signal(runner, config["trainer_bumps"])

    # 4. Jockey suitability
    raw_signals["jockey"] = _jockey_signal(runner, config["jockey_bumps"])

    # 5. Course & distance (RP badges via cd_form module; legacy
    # _cd_signal kept as fallback if module unavailable).
    raw_signals["course_distance"] = cd_form_signal(runner, race)

    # 6. Going suitability
    raw_signals["going"] = _going_signal(runner, race, config["going"])

    # 7. Going-fit from historical runs. Explicit None means no race-day going
    # context yet, so the helper returns a neutral non-ranking signal.
    going_fit = score_going_fit(runner.get("going_history") or runner.get("runs") or [], _race_target_going(race))
    raw_signals["going_fit"] = float(going_fit["score"]) * 100.0
    if going_fit.get("going_data") == "insufficient":
        flags.append("going_data_insufficient")

    # 8. Draw bias (Epsom course table first; falls back to legacy 5f rule)
    ext_draw = extended_draw_signal(runner, race)
    if ext_draw is not None:
        raw_signals["draw_bias"] = ext_draw
    else:
        raw_signals["draw_bias"] = _draw_signal(runner, race, config["draw"])

    # 9. Class move
    raw_signals["class_move"] = _class_move_signal(runner, config["class_move"])

    # 10. Pace / run-style fit
    race_pace = race.get("_projected_pace") or project_race_pace(race.get("runners") or [])
    raw_signals["pace"] = pace_signal(runner, race_pace)

    # 11. Sire stamina (gated to 10f+; neutral 50 when sire unknown)
    raw_signals["sire_stamina"] = sire_stamina_signal(runner, race)

    # 12. Trial form (gated to 10f+; neutral 50 when no trial data)
    raw_signals["trial_form"] = trial_form_signal(runner, race)

    # Raw score (class_rating placeholder is 50 until z-score in score_race)
    class_val = raw_signals["class_rating"] if raw_signals["class_rating"] is not None else 50.0
    signals_for_score = {**raw_signals, "class_rating": class_val}
    raw_score = _weighted_sum(signals_for_score, config["weights"])

    return {
        "horse":             runner.get("horse") or runner.get("horse_name", "Unknown"),
        "raw_signals":       raw_signals,
        "raw_score":         raw_score,
        "missing_data_flags": flags,
        "going_data":         going_fit.get("going_data", "not_applicable"),
        "going_fit":          going_fit,
    }


def score_race(race: dict, config: dict) -> dict:
    """Score all runners in a race, normalise, rank, and emit a recommendation.

    Parameters
    ----------
    race : dict
        Race dict with a ``runners`` list.
    config : dict
        Config dict (from ``load_default_config``).

    Returns
    -------
    dict
        ``{"race_id", "ranked_runners", "confidence",
           "bet_recommendation", "race_stdev",
           "race_competitiveness", "missing_data_flags"}``

    Example
    -------
    >>> cfg = load_default_config()
    >>> race = {
    ...     "race_id": "test_race",
    ...     "course": "Epsom",
    ...     "distance_f": 10.0,
    ...     "going": "good",
    ...     "runners": [
    ...         {"horse": "A", "rpr": 110, "ts": None, "or_rating": None,
    ...          "runs": [{"position": 1, "days_ago": 14, "course": "Epsom",
    ...                    "distance_f": 10.0, "going": "good"}],
    ...          "trainer": "Aidan O'Brien", "jockey": "Ryan Moore",
    ...          "draw": 3, "cd_wins": 1, "cd_places": 0,
    ...          "course_wins": 2, "course_places": 1,
    ...          "first_time_epsom": False, "going_preference": "good",
    ...          "last_class": 1, "current_class": 1},
    ...         {"horse": "B", "rpr": 95, "ts": None, "or_rating": None,
    ...          "runs": [{"position": 4, "days_ago": 30, "course": "Other",
    ...                    "distance_f": 10.0, "going": "soft"}],
    ...          "trainer": "Unknown", "jockey": "Unknown",
    ...          "draw": 12, "cd_wins": 0, "cd_places": 0,
    ...          "course_wins": 0, "course_places": 0,
    ...          "first_time_epsom": True, "going_preference": "soft",
    ...          "last_class": 3, "current_class": 1},
    ...     ],
    ... }
    >>> result = score_race(race, cfg)
    >>> result["ranked_runners"][0]["horse"]
    'A'
    >>> result["ranked_runners"][0]["rank"]
    1
    >>> result["bet_recommendation"] in ("WIN", "EW", "PASS")
    True
    """
    _validate_weights(config["weights"])
    runners = race.get("runners", [])
    if not runners:
        return _empty_race_result(race)

    # Precompute projected race pace once per race so `score_runner`
    # doesn't recompute it for every runner.
    race["_projected_pace"] = project_race_pace(runners)

    # Step 1: raw per-runner signals
    runner_results = [score_runner(r, race, config) for r in runners]

    # Step 2: z-score the class/rating signal across the field
    ratings = [
        r["raw_signals"]["class_rating"]
        for r in runner_results
        if r["raw_signals"]["class_rating"] is not None
    ]
    for rr in runner_results:
        val = rr["raw_signals"]["class_rating"]
        if val is None or len(ratings) < 2:
            rr["raw_signals"]["class_rating"] = 50.0
        else:
            rr["raw_signals"]["class_rating"] = _zscore_to_signal(
                val, ratings
            )

    # Step 3: recompute raw scores with z-scored class signal
    for rr in runner_results:
        rr["raw_score"] = _weighted_sum(rr["raw_signals"], config["weights"])

    # Step 4: normalise to 0-100 within race
    raw_scores = [rr["raw_score"] for rr in runner_results]
    norm_scores = _normalise_scores(raw_scores)

    for rr, norm in zip(runner_results, norm_scores):
        rr["score"] = round(norm, 2)

    # Step 5: compute score_breakdown (weighted contribution per signal)
    weights = config["weights"]
    for rr in runner_results:
        rr["score_breakdown"] = {
            sig: round(rr["raw_signals"].get(sig, 50.0) * w, 3)
            for sig, w in weights.items()
        }

    # Step 6: rank
    runner_results.sort(key=lambda x: x["score"], reverse=True)
    for i, rr in enumerate(runner_results):
        rr["rank"] = i + 1

    # Step 7: confidence + recommendation
    sorted_scores = [rr["score"] for rr in runner_results]
    gap = (sorted_scores[0] - sorted_scores[1]) if len(sorted_scores) > 1 else 100.0
    conf_cfg = config["confidence"]

    all_flags = [f for rr in runner_results for f in rr["missing_data_flags"]]
    force_low = "no_ratings" in all_flags and len(ratings) == 0

    if force_low:
        confidence = "LOW"
    elif gap > conf_cfg["high_gap"]:
        confidence = "HIGH"
    elif gap > conf_cfg["med_gap"]:
        confidence = "MED"
    else:
        confidence = "LOW"

    # Step 8: race competitiveness
    race_stdev = _stdev(sorted_scores)
    comp_cfg = config["competitiveness"]
    if race_stdev < comp_cfg["wide_open_stdev"]:
        race_comp = "WIDE OPEN"
        if confidence != "LOW":
            confidence = "LOW"   # override — wide-open race overrides confidence
    elif race_stdev > comp_cfg["clear_fav_stdev"]:
        race_comp = "CLEAR FAVOURITE"
    else:
        race_comp = "COMPETITIVE"

    # Step 9: bet recommendation
    top_score = sorted_scores[0]
    if confidence == "HIGH" and top_score >= conf_cfg["min_score_for_bet"]:
        bet = "WIN"
    elif confidence == "MED" and top_score >= conf_cfg["min_score_for_bet"]:
        bet = "EW"
    else:
        bet = "PASS"

    # Build odds lookup from original runner dicts (keyed by horse name)
    odds_lookup: dict[str, dict] = {}
    for r in runners:
        name = r.get("horse") or r.get("horse_name", "")
        if name:
            odds_lookup[name] = {
                "morning_price":  r.get("morning_price"),
                "odds_source":    r.get("odds_source"),
                "odds_fetched_at": r.get("odds_fetched_at"),
                "trainer":        r.get("trainer", ""),
                "jockey":         r.get("jockey", ""),
            }

    # Clean output — remove internal keys; pass through odds + display fields for template/Badger
    ranked = []
    for rr in runner_results:
        odds = odds_lookup.get(rr["horse"], {})
        ranked.append({
            "rank":              rr["rank"],
            "horse":             rr["horse"],
            "trainer":           odds.get("trainer", ""),
            "jockey":            odds.get("jockey", ""),
            "score":             rr["score"],
            "score_breakdown":   rr["score_breakdown"],
            "raw_signal_values": rr["raw_signals"],
            "missing_data_flags": rr["missing_data_flags"],
            "going_data":        rr.get("going_data", "not_applicable"),
            "going_fit":         rr.get("going_fit", {}),
            "morning_price":     odds.get("morning_price"),
            "odds_source":       odds.get("odds_source"),
            "odds_fetched_at":   odds.get("odds_fetched_at"),
        })

    return {
        "race_id":            race.get("race_id", "unknown"),
        "going":              _race_target_going(race),
        "ranked_runners":     ranked,
        "confidence":         confidence,
        "bet_recommendation": bet,
        "race_stdev":         round(race_stdev, 2),
        "race_competitiveness": race_comp,
        "missing_data_flags": list(set(all_flags)),
    }


# ---------------------------------------------------------------------------
# Signal helpers
# ---------------------------------------------------------------------------


def _best_rating(runner: dict) -> float | None:
    """Return best available rating: RPR > TS > OR > None.

    Accepts both ``or_rating`` (spec shape) and ``or`` (River racecard shape).
    """
    for key in ("rpr", "ts", "or_rating", "or"):
        val = runner.get(key)
        if val is not None:
            return float(val)
    return None


def _parse_form_string(form_string: str, last_run_days: int | None = None) -> list[dict]:
    """Parse River's text form string into a minimal runs list (newest first).

    Extracts digit characters 1-9 and 0 (treated as unplaced), strips
    hyphens, letters, and whitespace.  Assigns ``days_ago`` to the first
    run only (from ``last_run_days``); remaining runs get 0.

    Example
    -------
    >>> _parse_form_string("7221-8", 14)
    [{'position': 8, 'days_ago': 14}, {'position': 2, 'days_ago': 0}, {'position': 2, 'days_ago': 0}, {'position': 1, 'days_ago': 0}, {'position': 7, 'days_ago': 0}]
    """
    if not form_string:
        return []
    # Extract only digit chars; reverse so newest (rightmost) is first
    digits = [ch for ch in form_string if ch.isdigit()]
    digits = list(reversed(digits))[:5]
    runs = []
    for i, d in enumerate(digits):
        pos: int | None = int(d) if d != "0" else None  # 0 = unplaced
        days = (last_run_days or 0) if i == 0 else 0
        runs.append({"position": pos, "days_ago": days})
    return runs


def _form_signal(runner: dict, form_cfg: dict) -> float:
    """Compute form signal (0–100) from last 5 runs.

    Accepts a ``runs`` list (spec shape) OR River's ``form_string`` text
    (e.g. ``"7221-8"``). When ``form_string`` is present and ``runs`` is
    absent, positions are parsed from right to left (newest first); hyphens
    and letters are ignored.
    """
    runs = runner.get("runs") or []
    if not runs:
        # Attempt to parse River-format form_string
        form_str = runner.get("form_string") or ""
        last_run_days = runner.get("last_run_days") or runner.get("days_since_last_run")
        runs = _parse_form_string(form_str, last_run_days)

    runs = runs[:5]
    if not runs:
        return 50.0  # neutral; replaced by race median in score_race

    pts = form_cfg["position_points"]
    decay = form_cfg["recency_weights"]
    total = 0.0
    for i, run in enumerate(runs):
        pos = run.get("position")
        weight = decay[i] if i < len(decay) else 0.0
        points = pts.get(pos, 0) if pos is not None else 0
        total += points * weight

    # Max theoretical = 10 * sum([1.0,0.75,0.5,0.3,0.15]) = 27.0
    max_form = 10.0 * sum(form_cfg["recency_weights"])
    signal = (total / max_form) * 100.0 if max_form > 0 else 50.0

    # Long-absence penalty
    if runs:
        days_ago = runs[0].get("days_ago") or runs[0].get("days_since_last_run") or 0
        if days_ago > form_cfg["absence_threshold_days"]:
            signal -= form_cfg["absence_penalty"]

    return max(0.0, min(100.0, signal))


def _trainer_signal(runner: dict, trainer_bumps: dict) -> float:
    """Trainer form signal: bump table → 0–100."""
    trainer = runner.get("trainer") or ""
    bump = trainer_bumps.get(trainer, 0)
    # bump is 0–10; scale to 0–100
    return float(bump) / 10.0 * 100.0


def _jockey_signal(runner: dict, jockey_bumps: dict) -> float:
    """Jockey suitability signal: bump table → 0–100."""
    jockey = runner.get("jockey") or ""
    bump = jockey_bumps.get(jockey, 0)
    return float(bump) / 10.0 * 100.0


def _cd_signal(runner: dict, race: dict, cd_cfg: dict) -> float:
    """Course & distance signal (0–100)."""
    cd_wins    = int(runner.get("cd_wins", 0) or 0)
    cd_places  = int(runner.get("cd_places", 0) or 0)
    c_wins     = int(runner.get("course_wins", 0) or 0)
    c_places   = int(runner.get("course_places", 0) or 0)
    # Also handle River's boolean-style fields from test fixtures
    if runner.get("cd_wins") is None and runner.get("course_winner"):
        c_wins = max(c_wins, 1)
    if runner.get("cd_wins") is None and runner.get("distance_winner"):
        cd_wins = max(cd_wins, 1)

    first_epsom = bool(runner.get("first_time_epsom", False))

    bonus = 0.0
    if cd_wins > 0:
        bonus += cd_cfg["cd_win_bonus"]
    elif cd_places > 0:
        bonus += cd_cfg["cd_place_bonus"]
    elif c_wins > 0:
        bonus += cd_cfg["course_win_bonus"]
    elif c_places > 0:
        bonus += cd_cfg["course_place_bonus"]

    dist_f = float(race.get("distance_f") or race.get("distance_furlongs") or 0)
    if (
        first_epsom
        and race.get("course", "").lower() == "epsom"
        and dist_f >= cd_cfg["epsom_long_dist_furlongs"]
    ):
        bonus -= cd_cfg["first_time_epsom_penalty"]

    # Scale: 0 neutral is bonus=0; max realistic bonus ~15; map linearly
    # Use 0 as 50 (neutral), max bonus (+15) → 80, min penalty → 20
    signal = 50.0 + bonus * 2.0
    return max(0.0, min(100.0, signal))


def _going_signal(runner: dict, race: dict, going_cfg: dict) -> float:
    """Going suitability signal (0–100)."""
    pref = (runner.get("going_preference") or "").lower().strip()
    forecast = (normalise_going(_race_target_going(race)) or "").lower().strip()

    if not pref:
        return float(going_cfg["neutral_signal"])
    if pref == "any":
        return float(going_cfg["any_signal"])
    if forecast and pref == forecast:
        return float(going_cfg["match_signal"])
    return float(going_cfg["mismatch_signal"])


def _race_target_going(race: dict) -> str | None:
    """Return target going; missing metadata defaults to Good, explicit None does not."""
    if "going" in race:
        return race.get("going")
    race_meta = race.get("race_meta")
    if isinstance(race_meta, dict) and "going" in race_meta:
        return race_meta.get("going")
    return "Good"


def _draw_signal(runner: dict, race: dict, draw_cfg: dict) -> float:
    """Draw bias signal (0–100)."""
    dist_f  = float(race.get("distance_f") or race.get("distance_furlongs") or 0)
    course  = (race.get("course") or "").strip()
    going   = (race.get("going") or "").lower().strip()
    draw    = runner.get("draw")

    material = (
        dist_f in draw_cfg["material_distances"]
        and course in draw_cfg["material_courses"]
    )
    if not material:
        return 50.0

    if draw is None:
        return 50.0

    draw = int(draw)
    if going in draw_cfg["good_goings"]:
        if draw <= draw_cfg["low_draw_threshold"]:
            return float(draw_cfg["low_draw_signal"])
        if draw > draw_cfg["high_draw_threshold"]:
            return float(draw_cfg["high_draw_signal"])
    return float(draw_cfg["mid_draw_signal"])


def _class_move_signal(runner: dict, class_cfg: dict) -> float:
    """Class move signal (0–100)."""
    last    = runner.get("last_class")
    current = runner.get("current_class")
    if last is None or current is None:
        return float(class_cfg["same_signal"])
    last, current = int(last), int(current)
    # Lower number = higher class (1 = Group 1)
    if current < last:   # dropping down in class = positive
        return float(class_cfg["drop_signal"])
    if current > last:   # stepping up in class = negative
        return float(class_cfg["rise_signal"])
    return float(class_cfg["same_signal"])


# ---------------------------------------------------------------------------
# Maths helpers
# ---------------------------------------------------------------------------


def _zscore_to_signal(value: float, population: list[float]) -> float:
    """Convert a value to a 0-100 signal via z-score within the population.

    Clips z-score to [-3, 3] then maps linearly: -3 → 0, +3 → 100.

    Example
    -------
    >>> round(_zscore_to_signal(100, [90, 95, 100, 105, 110]), 1)
    50.0
    """
    n = len(population)
    if n < 2:
        return 50.0
    mean = sum(population) / n
    variance = sum((x - mean) ** 2 for x in population) / n
    std = math.sqrt(variance) if variance > 0 else 1.0
    z = (value - mean) / std
    z = max(-3.0, min(3.0, z))
    return (z + 3.0) / 6.0 * 100.0


def _weighted_sum(signals: dict[str, Any], weights: dict[str, float]) -> float:
    """Return weighted sum of signal values (each 0–100).

    Missing signal keys default to 50 (neutral).
    """
    total = 0.0
    for key, w in weights.items():
        val = signals.get(key)
        total += float(val if val is not None else 50.0) * w
    return total


def _normalise_scores(raw: list[float]) -> list[float]:
    """Linearly normalise a list of scores to [5, 95].

    If all scores are equal, returns 50 for each.

    Example
    -------
    >>> _normalise_scores([10, 20, 30])
    [5.0, 50.0, 95.0]
    """
    min_s = min(raw)
    max_s = max(raw)
    if max_s - min_s < 1e-9:
        return [50.0] * len(raw)
    return [(s - min_s) / (max_s - min_s) * 90.0 + 5.0 for s in raw]


def _stdev(values: list[float]) -> float:
    """Population standard deviation."""
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    return math.sqrt(sum((v - mean) ** 2 for v in values) / n)


def _validate_weights(weights: dict) -> None:
    """Raise ValueError if weights do not sum to 1.0 (±0.001)."""
    total = sum(weights.values())
    if abs(total - 1.0) > 0.001:
        raise ValueError(
            f"config weights must sum to 1.0; got {total:.4f}"
        )


def _empty_race_result(race: dict) -> dict:
    return {
        "race_id":              race.get("race_id", "unknown"),
        "going":                _race_target_going(race),
        "ranked_runners":       [],
        "confidence":           "LOW",
        "bet_recommendation":   "PASS",
        "race_stdev":           0.0,
        "race_competitiveness": "WIDE OPEN",
        "missing_data_flags":   ["no_runners"],
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _print_ranked_table(result: dict) -> None:
    """Print a formatted race result table to stdout."""
    print(f"\n{'='*70}")
    print(f"Race: {result['race_id']}")
    print(
        f"Confidence: {result['confidence']}  |  "
        f"Bet: {result['bet_recommendation']}  |  "
        f"Competitiveness: {result['race_competitiveness']}  "
        f"(stdev={result['race_stdev']})"
    )
    if result["missing_data_flags"]:
        print(f"⚠ Missing data: {', '.join(result['missing_data_flags'])}")
    print(f"\n{'Rank':<5} {'Horse':<30} {'Score':>6}  Breakdown (top signals)")
    print("-" * 70)
    for r in result["ranked_runners"]:
        bd = r["score_breakdown"]
        top_signals = sorted(bd.items(), key=lambda x: x[1], reverse=True)[:3]
        top_str = "  ".join(f"{k}={v:.1f}" for k, v in top_signals)
        print(f"{r['rank']:<5} {r['horse']:<30} {r['score']:>6.1f}  {top_str}")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scoring <racecard.json>")
        sys.exit(1)

    path = sys.argv[1]
    with open(path, encoding="utf-8") as fh:
        racecard = json.load(fh)

    config = load_default_config()
    races = racecard.get("races", [racecard])  # support single-race or multi-race
    for race_data in races:
        result = score_race(race_data, config)
        _print_ranked_table(result)
