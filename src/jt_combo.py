"""
jt_combo.py — Jockey/Trainer combination signal v0.5
====================================================

Scores a runner based on the historical win strike rate of the specific
jockey/trainer partnership.  This is the **interaction term** — it
captures pairing-specific synergy beyond what the individual `jockey`
and `trainer_form` signals measure.

Returns neutral 50 when:
- ``runner["trainer"]`` or ``runner["jockey"]`` is absent or empty
- Horse not found in the enrichment file (lookup is horse-keyed)
- ``combo_runners < 10`` (small-sample guard)

Special case — first-time pairing:
- ``first_time_pairing == True`` and ``combo_runners == 0``  →  return 60
  (positive lean for a deliberate new booking; overrides sample-size guard)

Data file
---------
``data/enrichment/jt-combo.json``
Keyed by horse name (Danny's design §4 horse-keyed schema):
  ``horses: { "Horse Name": { "combo_wins": int, "combo_runners": int,
                               "first_time_pairing": bool, ... } }``

The enrichment file stores ``combo_key`` for audit; this module does NOT
construct the combo key from ``runner["trainer"]`` + ``runner["jockey"]``
to avoid mismatches with stored string normalisation.

Weight in scoring.py: 0.0300 (v0.5 config)
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

# ---------------------------------------------------------------------------
# Data-directory candidates (mirrors trial_form.py / sires.py pattern)
# ---------------------------------------------------------------------------

_DATA_DIR_CANDIDATES = (
    os.path.join(os.getcwd(), "data", "enrichment"),
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "enrichment",
    ),
)

_SAMPLE_GUARD = 10  # combo_runners < this → return 50 (unless first_time_pairing)
_FIRST_TIME_SCORE = 60.0


def _find_data_file(name: str) -> str | None:
    for d in _DATA_DIR_CANDIDATES:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    return None


def load_jt_combo_data(path: str | None = None) -> dict:
    """Load jockey/trainer combo enrichment from *path* (or auto-discover).

    Returns a dict keyed by horse name:
        { "Horse Name": {"combo_wins": int, "combo_runners": int,
                          "first_time_pairing": bool, ...} }

    Returns empty dict if file missing or malformed.
    """
    if path is None:
        path = _find_data_file("jt-combo.json")
    if path is None or not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}

    horses = raw.get("horses", {})
    if not isinstance(horses, dict):
        return {}
    return horses


@lru_cache(maxsize=1)
def load_jt_combo() -> dict:
    """Cached version of ``load_jt_combo_data`` (no path arg).

    Use inside ``jt_combo_signal``; use ``load_jt_combo_data(path)``
    in tests that need a specific file.
    """
    return load_jt_combo_data()


# ---------------------------------------------------------------------------
# Scoring — pure functions (Danny's spec §4)
# ---------------------------------------------------------------------------

def _lerp(lo: float, hi: float, t: float) -> float:
    """Linear interpolation: lo + t * (hi - lo).  t clamped to [0, 1]."""
    t = max(0.0, min(1.0, t))
    return lo + t * (hi - lo)


def score_jt_combo(combo_sr: float) -> float:
    """Map JT combo strike rate to 0–100 signal (Danny's spec §4).

    Parameters
    ----------
    combo_sr : float
        combo_wins / combo_runners.  Caller must validate combo_runners >= 10.

    Returns
    -------
    float
        Score in [15, 90].

    Test anchors (Danny's spec):
    >>> score_jt_combo(0.35)
    90.0
    >>> score_jt_combo(0.25)
    75.0
    >>> score_jt_combo(0.15)
    55.0
    >>> score_jt_combo(0.08)
    40.0
    >>> score_jt_combo(0.00)
    15.0
    """
    sr = combo_sr

    # sr ≥ 0.35 → 90
    if sr >= 0.35:
        return 90.0

    # 0.25 ≤ sr < 0.35 → lerp(75 → 90)
    if sr >= 0.25:
        t = (sr - 0.25) / (0.35 - 0.25)
        return round(_lerp(75.0, 90.0, t), 10)

    # 0.15 ≤ sr < 0.25 → lerp(55 → 75)
    if sr >= 0.15:
        t = (sr - 0.15) / (0.25 - 0.15)
        return round(_lerp(55.0, 75.0, t), 10)

    # 0.08 ≤ sr < 0.15 → lerp(40 → 55)
    if sr >= 0.08:
        t = (sr - 0.08) / (0.15 - 0.08)
        return round(_lerp(40.0, 55.0, t), 10)

    # 0.00 < sr < 0.08 → lerp(20 → 40)
    if sr > 0.00:
        t = sr / 0.08
        return round(_lerp(20.0, 40.0, t), 10)

    # sr == 0.00 → 15
    return 15.0


# ---------------------------------------------------------------------------
# Public signal entry point (scoring.py integration)
# ---------------------------------------------------------------------------

def jt_combo_signal(runner: dict, race: dict) -> float:  # noqa: ARG001
    """Jockey/trainer combo signal for ``score_runner`` in scoring.py.

    Returns neutral 50 when:
      - runner["trainer"] or runner["jockey"] absent or empty
      - Horse not found in enrichment file
      - combo_runners < 10 (and not first_time_pairing)

    Returns 60 for:
      - first_time_pairing == True AND combo_runners == 0

    Parameters
    ----------
    runner : dict
        Runner dict; ``horse`` (or ``horse_name``) is the lookup key.
    race : dict
        Not used.

    Returns
    -------
    float
        0–100 signal score.  50 = neutral / no data.
    """
    if not isinstance(runner, dict):
        return 50.0

    trainer = runner.get("trainer")
    jockey = runner.get("jockey")

    if (
        not trainer or not isinstance(trainer, str) or not trainer.strip()
        or not jockey or not isinstance(jockey, str) or not jockey.strip()
    ):
        return 50.0

    horse = runner.get("horse") or runner.get("horse_name")
    if not horse:
        return 50.0

    data = load_jt_combo()
    entry = data.get(horse)
    if entry is None:
        return 50.0

    try:
        combo_runners = int(entry.get("combo_runners", 0))
        combo_wins = int(entry.get("combo_wins", 0))
    except (TypeError, ValueError):
        return 50.0

    first_time = bool(entry.get("first_time_pairing", False))

    # First-time pairing override (combo_runners == 0 only)
    if first_time and combo_runners == 0:
        return _FIRST_TIME_SCORE

    # Sample-size guard
    if combo_runners < _SAMPLE_GUARD:
        return 50.0

    combo_sr = combo_wins / combo_runners
    return float(score_jt_combo(combo_sr))


# ---------------------------------------------------------------------------
# Test helper
# ---------------------------------------------------------------------------

def _clear_caches() -> None:  # pragma: no cover
    """Reset lru_cache (mirrors sires.py / trial_form.py pattern)."""
    load_jt_combo.cache_clear()
