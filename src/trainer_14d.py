"""
trainer_14d.py — Trainer 14-day form signal v0.5
================================================

Scores a runner based on their trainer's win strike rate in the trailing
14 calendar days.  Captures trainer "temperature" (hot/cold yard) rather
than long-term quality, which is handled by the separate `trainer_form`
signal (v0.4).

Returns neutral 50 when:
- ``runner["trainer"]`` is absent or empty
- Trainer not found in the enrichment file
- ``runners_14d < 5`` (small-sample guard)

Strike rate is always recomputed from ``wins_14d / runners_14d`` —
the stored ``strike_rate`` field is for readability only and is not used.

Scoring formula: Danny's spec §3 piecewise-linear curve.

Data file
---------
``data/enrichment/trainer-14d.json``
Keyed by trainer name (exact string, Livingston normalises case):
  ``trainers: { "Trainer Name": { "wins_14d": int, "runners_14d": int, ... } }``

Weight in scoring.py: 0.0400 (v0.5 config)
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

_SAMPLE_GUARD = 5  # runners_14d < this → return 50


def _find_data_file(name: str) -> str | None:
    for d in _DATA_DIR_CANDIDATES:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    return None


def load_trainer_14d_data(path: str | None = None) -> dict:
    """Load trainer 14-day enrichment from *path* (or auto-discover).

    Returns a dict keyed by trainer name:
        { "Trainer Name": {"wins_14d": int, "runners_14d": int, ...} }

    Returns empty dict if file missing or malformed.
    """
    if path is None:
        path = _find_data_file("trainer-14d.json")
    if path is None or not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}

    trainers = raw.get("trainers", {})
    if not isinstance(trainers, dict):
        return {}
    return trainers


@lru_cache(maxsize=1)
def load_trainer_14d() -> dict:
    """Cached version of ``load_trainer_14d_data`` (no path arg).

    Use inside ``trainer_14d_signal``; use ``load_trainer_14d_data(path)``
    in tests that need a specific file.
    """
    return load_trainer_14d_data()


# ---------------------------------------------------------------------------
# Scoring — pure functions (Danny's spec §3)
# ---------------------------------------------------------------------------

def _lerp(lo: float, hi: float, t: float) -> float:
    """Linear interpolation: lo + t * (hi - lo).  t clamped to [0, 1]."""
    t = max(0.0, min(1.0, t))
    return lo + t * (hi - lo)


def score_trainer_14d(strike_rate: float) -> float:
    """Map trainer 14d strike rate to 0–100 signal (Danny's spec §3).

    Parameters
    ----------
    strike_rate : float
        wins_14d / runners_14d.  Caller must validate runners_14d >= 5.

    Returns
    -------
    float
        Score in [15, 90].

    Test anchors (Danny's spec):
    >>> score_trainer_14d(0.30)
    90.0
    >>> score_trainer_14d(0.20)
    75.0
    >>> score_trainer_14d(0.12)
    55.0
    >>> score_trainer_14d(0.06)
    40.0
    >>> score_trainer_14d(0.00)
    15.0
    """
    sr = strike_rate

    # sr ≥ 0.30 → 90
    if sr >= 0.30:
        return 90.0

    # 0.20 ≤ sr < 0.30 → lerp(75 → 90)
    if sr >= 0.20:
        t = (sr - 0.20) / (0.30 - 0.20)
        return round(_lerp(75.0, 90.0, t), 10)

    # 0.12 ≤ sr < 0.20 → lerp(55 → 75)
    if sr >= 0.12:
        t = (sr - 0.12) / (0.20 - 0.12)
        return round(_lerp(55.0, 75.0, t), 10)

    # 0.06 ≤ sr < 0.12 → lerp(40 → 55)
    if sr >= 0.06:
        t = (sr - 0.06) / (0.12 - 0.06)
        return round(_lerp(40.0, 55.0, t), 10)

    # 0.00 < sr < 0.06 → lerp(20 → 40)
    if sr > 0.00:
        t = sr / 0.06
        return round(_lerp(20.0, 40.0, t), 10)

    # sr == 0.00 → 15
    return 15.0


# ---------------------------------------------------------------------------
# Public signal entry point (scoring.py integration)
# ---------------------------------------------------------------------------

def trainer_14d_signal(runner: dict, race: dict) -> float:  # noqa: ARG001
    """Trainer 14-day signal for ``score_runner`` in scoring.py.

    Returns neutral 50 when:
      - runner["trainer"] absent or empty
      - Trainer not found in enrichment file
      - runners_14d < 5 (small-sample guard)

    Parameters
    ----------
    runner : dict
        Runner dict; ``trainer`` key is the lookup.
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
    if not trainer or not isinstance(trainer, str) or not trainer.strip():
        return 50.0

    data = load_trainer_14d()
    entry = data.get(trainer)
    if entry is None:
        return 50.0

    try:
        runners_14d = int(entry.get("runners_14d", 0))
        wins_14d = int(entry.get("wins_14d", 0))
    except (TypeError, ValueError):
        return 50.0

    if runners_14d < _SAMPLE_GUARD:
        return 50.0

    strike_rate = wins_14d / runners_14d
    return float(score_trainer_14d(strike_rate))


# ---------------------------------------------------------------------------
# Test helper
# ---------------------------------------------------------------------------

def _clear_caches() -> None:  # pragma: no cover
    """Reset lru_cache (mirrors sires.py / trial_form.py pattern)."""
    load_trainer_14d.cache_clear()
