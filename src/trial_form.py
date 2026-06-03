"""
trial_form.py — Trial-form signal v0.4
=======================================

Scores a runner's Classic-trial form and returns a normalised signal
(0–100) for races at 10f+.  Neutral 50 when:

- Race distance < 10f (gate, same convention as sire_stamina)
- Horse not found in the trial-form enrichment file
- Horse found but no trial runs recorded
- A trial entry is malformed / data missing

The signal is the *best single score* across all trial runs for a horse.
Blending / averaging is deliberately avoided so a standout Tier 1 win
(Dante, Chester Vase, Musidora) is not diluted by minor preps.

Scoring formula (Danny's spec, signed off 2026-06-03)
-----------------------------------------------------
1. Position base score
2. Tier compression  (Tier 1 = full; Tier 2 = 75%; Tier 3 = 55% towards neutral)
3. Freshness adjustment (−2 at 29–42 d, −4 at 43–56 d, −7 at >56 d)
4. Clamp [0, 100]

Data file
---------
``data/enrichment/trial-form.json``
Livingston uses a **signed beaten-lengths convention** (negative value = winner
won by that many lengths).  This module normalises on load:
  - finishing_position == 1  →  beaten_lengths = 0.0
  - finishing_position  > 1  →  beaten_lengths = abs(value)
  - beaten_lengths is None for 2nd+  →  treat as missing data → 50 for that trial

Tier taxonomy (v1 — UK + Leopardstown Derby Trial only)
-------------------------------------------------------
Tier 1: Dante Stakes, Chester Vase, Musidora Stakes, Cheshire Oaks
Tier 2: Lingfield Derby Trial, Dee Stakes, Lingfield Oaks Trial,
        Cashel Palace Hotel Derby Trial Stakes  (Leopardstown — Steve's Q3 answer)
        # TODO v2: consider Lingfield Polytrack discount (Steve's Q2 answer: not for v1)
Tier 3: Newmarket Stakes, Craven Stakes, Greenham Stakes, Tetrarch Stakes,
        Blue Riband Trial, 1000 Guineas, Irish 1000 Guineas
        (any unlisted trial name defaults to Tier 3)

Weight in scoring.py: 0.0800 (v0.4 config)
"""
from __future__ import annotations

import json
import os
from datetime import date
from functools import lru_cache

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MIN_DISTANCE_F = 10.0

_DEFAULT_RACE_DATE = "2026-06-06"  # Epsom Derby — used as fallback reference date

# Maps canonical trial names → tier.  Any unlisted name is treated as Tier 3.
_TIER_MAP: dict[str, int] = {
    # Tier 1 — Derby
    "Dante Stakes": 1,
    "Chester Vase": 1,
    # Tier 1 — Oaks
    "Musidora Stakes": 1,
    "Cheshire Oaks": 1,
    # Tier 2 — Derby
    "Lingfield Derby Trial": 2,
    "Dee Stakes": 2,
    # Tier 2 — Oaks
    "Lingfield Oaks Trial": 2,
    # Tier 2 — Irish (Leopardstown Derby Trial; Steve Q3)
    "Cashel Palace Hotel Derby Trial Stakes": 2,
    # Tier 3
    "Newmarket Stakes": 3,
    "Craven Stakes": 3,
    "Greenham Stakes": 3,
    "Tetrarch Stakes": 3,
    "Blue Riband Trial": 3,
    "1000 Guineas": 3,
    "Irish 1000 Guineas": 3,
}

_TIER_FACTORS: dict[int, float] = {1: 1.00, 2: 0.75, 3: 0.55}

_DATA_DIR_CANDIDATES = (
    # Running from project root
    os.path.join(os.getcwd(), "data", "enrichment"),
    # Running with cwd elsewhere — resolved relative to this file
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "enrichment",
    ),
)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _find_data_file(name: str) -> str | None:
    for d in _DATA_DIR_CANDIDATES:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    return None


def _normalise_trial(raw: dict) -> dict:
    """Convert a raw JSON trial entry to the normalised in-memory shape.

    Handles both Danny's spec field names (``race``, ``position``) and
    Livingston's actual names (``trial_name``, ``finishing_position``).
    Tier is looked up from ``_TIER_MAP`` when not present; defaults to 3.
    beaten_lengths convention is normalised here (Steve's resolution):
      - position == 1  → beaten_lengths = 0.0
      - position  > 1  → abs(beaten_lengths);  None → None (caller handles)
    """
    race_name = raw.get("race") or raw.get("trial_name") or ""
    tier = raw.get("tier")
    if tier is None:
        tier = _TIER_MAP.get(race_name, 3)

    position = raw.get("position") or raw.get("finishing_position")
    bl_raw = raw.get("beaten_lengths")

    if position is not None:
        pos_int = int(position)
        if pos_int == 1:
            beaten_lengths: float | None = 0.0
        elif bl_raw is None:
            beaten_lengths = None
        else:
            beaten_lengths = abs(float(bl_raw))
    else:
        beaten_lengths = bl_raw  # malformed — caller will detect None position

    return {
        "race": race_name,
        "tier": int(tier),
        "date": raw.get("date", ""),
        "position": int(position) if position is not None else None,
        "beaten_lengths": beaten_lengths,
        "field_size": raw.get("field_size"),
    }


def load_trial_form(path: str | None = None) -> dict:
    """Load and normalise trial-form enrichment from *path*.

    If *path* is None the file is auto-discovered via ``_DATA_DIR_CANDIDATES``.
    Returns an empty dict if the file is missing or malformed — callers must
    treat the result as "no data available" and return neutral 50.

    Keys in the returned dict are lower-cased horse names for case-insensitive
    lookup.  Each value is ``{"trials": [<normalised trial dicts>]}``.
    """
    if path is None:
        path = _find_data_file("trial-form.json")
    if path is None or not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}

    horses_raw = raw.get("horses", {})
    if not isinstance(horses_raw, dict):
        return {}

    result: dict = {}
    for name, entry in horses_raw.items():
        if not isinstance(entry, dict):
            continue
        # Accept both "trials" and "trial_runs" for forward-compat
        trials_raw = entry.get("trials") or entry.get("trial_runs") or []
        normalised = [_normalise_trial(t) for t in trials_raw if isinstance(t, dict)]
        result[name.lower()] = {"trials": normalised}

    return result


@lru_cache(maxsize=1)
def load_trial_data() -> dict:
    """Cached version of ``load_trial_form`` (no path arg).

    Use this inside ``trial_form_signal``; use ``load_trial_form(path)``
    in tests that need a specific file.
    """
    return load_trial_form()


# ---------------------------------------------------------------------------
# Scoring — pure functions
# ---------------------------------------------------------------------------

def score_trial_run(
    tier: int,
    position: int,
    beaten_lengths: float,
    days_since: int,
) -> float:
    """Score a single trial run → 0–100 float.

    Pure function; no I/O.  Implements Danny's four-step formula.

    Parameters
    ----------
    tier : int
        1, 2, or 3 from the taxonomy (unknown → treated as 3).
    position : int
        Finishing position (1 = winner).
    beaten_lengths : float
        0.0 for winners; lengths behind winner for placed horses.
    days_since : int
        Days between trial date and race day (clamped to ≥ 0).

    Returns
    -------
    float
        Clamped to [0.0, 100.0].
    """
    # Step 1 — Position base score
    if position == 1:
        base = 90.0
    elif position == 2:
        if beaten_lengths <= 0.5:
            base = 78.0
        elif beaten_lengths <= 2.0:
            base = 70.0
        else:
            base = 62.0
    elif position == 3:
        if beaten_lengths <= 2.0:
            base = 60.0
        else:
            base = 52.0
    elif position == 4:
        base = 44.0
    else:  # 5th+
        base = 35.0

    # Step 2 — Tier compression
    tier_factor = _TIER_FACTORS.get(tier, _TIER_FACTORS[3])
    tier_adjusted = 50.0 + (base - 50.0) * tier_factor

    # Step 3 — Freshness adjustment
    d = max(0, days_since)
    if d <= 28:
        freshness = 0
    elif d <= 42:
        freshness = -2
    elif d <= 56:
        freshness = -4
    else:
        freshness = -7

    # Step 4 — Clamp
    return float(max(0.0, min(100.0, tier_adjusted + freshness)))


def _score_single_trial(trial: dict, race_date: str) -> float | None:
    """Score one normalised trial dict.

    Returns *None* when the trial is malformed (missing tier/position/date),
    which the caller converts to a skipped entry.  Returns 50.0 when
    beaten_lengths is None for a placed finisher (treated as missing data,
    per Danny's spec).
    """
    tier = trial.get("tier")
    position = trial.get("position")
    date_str = trial.get("date") or ""
    beaten_lengths = trial.get("beaten_lengths")
    field_size = trial.get("field_size")

    # Guard: required fields
    if tier is None or position is None or not date_str:
        return None

    try:
        tier = int(tier)
        position = int(position)
    except (ValueError, TypeError):
        return None

    # Beaten lengths: winner is always 0.0; None for 2nd+ → missing → 50
    if position == 1:
        beaten_lengths = 0.0
    elif beaten_lengths is None:
        return 50.0
    else:
        try:
            beaten_lengths = abs(float(beaten_lengths))
        except (ValueError, TypeError):
            return None

    # Days since trial
    try:
        trial_dt = date.fromisoformat(date_str)
        ref_dt = date.fromisoformat(race_date)
        days_since = max(0, (ref_dt - trial_dt).days)
    except (ValueError, TypeError):
        days_since = 0

    raw_score = score_trial_run(tier, position, beaten_lengths, days_since)

    # Walkover discount: no real credit for a 1-horse field
    if field_size is not None:
        try:
            if int(field_size) == 1:
                raw_score = min(raw_score, 70.0)
        except (ValueError, TypeError):
            pass

    return raw_score


def best_trial_score(trial_runs: list[dict], race_date: str) -> float:
    """Score each run and return the maximum (best-result rule).

    Parameters
    ----------
    trial_runs : list[dict]
        Normalised trial dicts (from ``load_trial_data``).
    race_date : str
        ISO 8601 date string used to compute days_since.

    Returns
    -------
    float
        Maximum individual score, or 50.0 if trial_runs is empty /
        all entries are malformed.
    """
    if not trial_runs:
        return 50.0
    scores = []
    for t in trial_runs:
        if not isinstance(t, dict):
            continue
        s = _score_single_trial(t, race_date)
        if s is not None:
            scores.append(s)
    return float(max(scores)) if scores else 50.0


# ---------------------------------------------------------------------------
# Public composite function (Saul's API)
# ---------------------------------------------------------------------------

def score_trial_form(
    horse_name: str,
    distance_f: float,
    data: dict,
    race_date: str = _DEFAULT_RACE_DATE,
) -> float:
    """Score a horse's trial form given a pre-loaded data dict.

    This is the function imported by Saul's test suite.  It accepts a
    data dict directly so tests can inject fixture data without touching
    the filesystem.

    Parameters
    ----------
    horse_name : str
        Horse name (case-insensitive lookup).
    distance_f : float
        Race distance in furlongs; signal returns 50 for < 10f.
    data : dict
        Normalised trial data dict (from ``load_trial_form`` or inline).
        Shape: ``{horse_name_lower: {"trials": [...]}}``
    race_date : str
        ISO 8601 date for freshness calculation.  Defaults to Derby day
        (2026-06-06) so caller-omitted tests run correctly.

    Returns
    -------
    float
        0–100 signal score.  50 = neutral / no data.
    """
    if distance_f < _MIN_DISTANCE_F:
        return 50.0

    horse_lower = horse_name.lower()
    horse_entry: dict | None = None

    # Case-insensitive lookup (data may come from tests with mixed-case keys)
    for key, val in data.items():
        if key.lower() == horse_lower:
            horse_entry = val
            break

    if horse_entry is None:
        return 50.0

    trials = horse_entry.get("trials") or horse_entry.get("trial_runs") or []
    return best_trial_score(list(trials), race_date)


# ---------------------------------------------------------------------------
# Top-level signal entry point (scoring.py integration)
# ---------------------------------------------------------------------------

def trial_form_signal(runner: dict, race: dict) -> float:
    """Trial-form signal for ``score_runner`` in scoring.py.

    Returns neutral 50 when:
      - Race distance < 10f
      - Horse name absent from enrichment file
      - Horse has no trial runs in the file

    Parameters
    ----------
    runner : dict
        Runner dict; ``horse`` or ``horse_name`` is the lookup key.
    race : dict
        Race dict; ``distance_f`` (or ``distance_furlongs``) gates the
        signal; ``date`` used for freshness (falls back to Derby day).

    Returns
    -------
    float
        0–100 signal score.
    """
    dist_f = float(race.get("distance_f") or race.get("distance_furlongs") or 0.0)
    if dist_f < _MIN_DISTANCE_F:
        return 50.0

    horse = runner.get("horse") or runner.get("horse_name")
    if not horse:
        return 50.0

    data = load_trial_data()
    race_date = race.get("date") or _DEFAULT_RACE_DATE

    return score_trial_form(horse, dist_f, data, race_date)


# ---------------------------------------------------------------------------
# Test helper
# ---------------------------------------------------------------------------

def _clear_caches() -> None:  # pragma: no cover
    """Reset lru_cache (mirrors sires.py pattern; used by tests)."""
    load_trial_data.cache_clear()
