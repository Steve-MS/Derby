"""
market_drift.py — Market-drift gate signal v0.4
================================================

Gate-only market-drift modifier.  Does NOT contribute additively to
model_score (weight = 0.0 in scoring.py).  Instead it multiplies
``final_signal`` and emits flags that callers merge into a runner's flag list.

v0.4 — gate-only market-drift modifier.  Earned from Lord Melbourne +53.8%
drift call on Derby Day 2026-06-06 (5th place, vindicated Saul's WARN).

Formula
-------
    drift_pct = (latest_decimal − baseline_decimal) / baseline_decimal × 100

Gate thresholds
---------------
* |drift_pct| < 30  (noise band)
    → multiplier = 1.0, no flag

* |drift_pct| ≥ 30 AND drift_pct > 0  (DRIFT — market moving against runner)
    → multiplier = 0.90, flag = "DRIFT_WARN"

* |drift_pct| ≥ 30 AND drift_pct < 0  (STEAM — market confidence)
    → multiplier = 1.0,  flag = "STEAM_NOTED"  (informational only, no penalty)

* |drift_pct| ≥ 50 AND drift_pct > 0  (severe drift)
    → multiplier = 0.80, flag = "DRIFT_CRITICAL",
       confidence_tier forced to "SPECULATIVE"

* Missing or invalid odds
    → multiplier = 1.0, flag = "MARKET_DATA_MISSING"

Portability
-----------
No hardcoded course names, race names, horse names or dates.
Pure odds arithmetic — works for any race on any date.

WEIGHT IN COMPOSITE: 0.0 (gate-only modifier).  Do NOT add to scoring.py
weights.  The sum of 1.0000 across all additive signals is preserved.

Integration example (report.py — do NOT modify report.py in this PR)
----------------------------------------------------------------------
    from market_drift import load_market_drift_data, market_drift_signal

    market_data = load_market_drift_data()            # {horse: {baseline_decimal, latest_decimal}}
    drift = market_drift_signal("Lord Melbourne", market_data)
    runner.setdefault("flags", []).extend(drift["flags"])
    runner["final_signal"] *= drift["adjusted_final_signal_multiplier"]
    if drift.get("confidence_tier_override"):
        runner["confidence_tier"] = drift["confidence_tier_override"]

Data files
----------
``data/enrichment/market-baseline.json``
    ``horses: { "Horse Name": { "fractional_odds": "12/1", "decimal_odds": float, ... } }``

``data/enrichment/market-latest.json``
    ``horses: { "Horse Name": { "fractional_odds": "19/1", "decimal_odds": float, ... } }``

Decimal odds are used when available; fractional strings are parsed and
preferred when the stored decimal differs (synthetic-price artefact observed
on Derby Day 2026-06-06 — Lord Melbourne baseline stored as 13.5 decimal but
fractional "12/1" = 13.0 is the correct ante-post figure).
"""
from __future__ import annotations

import json
import os
from typing import Any

# ---------------------------------------------------------------------------
# Data-directory candidates (mirrors market_move.py / trial_form.py pattern)
# ---------------------------------------------------------------------------

_DATA_DIR_CANDIDATES = (
    os.path.join(os.getcwd(), "data", "enrichment"),
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "enrichment",
    ),
)


def _find_data_file(name: str) -> str | None:
    for d in _DATA_DIR_CANDIDATES:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    return None


# ---------------------------------------------------------------------------
# Odds parsing — fractional string → decimal float
# ---------------------------------------------------------------------------

_EVS_ALIASES: frozenset[str] = frozenset({"evs", "evens", "ev", "1/1"})


def parse_fractional_odds(odds: Any) -> float | None:
    """Convert a fractional odds string to decimal odds.

    Parameters
    ----------
    odds : Any
        Fractional odds string such as ``"12/1"``, ``"9/4"``, ``"Evs"``,
        ``"EVS"``, or ``"Evens"``.

    Returns
    -------
    float | None
        Decimal odds (numerator / denominator + 1), or ``None`` when the
        input cannot be parsed or yields a value ≤ 1.0.

    Examples
    --------
    >>> parse_fractional_odds("12/1")
    13.0
    >>> parse_fractional_odds("9/4")
    3.25
    >>> parse_fractional_odds("Evs")
    2.0
    >>> parse_fractional_odds("EVS")
    2.0
    >>> parse_fractional_odds("Evens")
    2.0
    >>> parse_fractional_odds(None) is None
    True
    """
    if not isinstance(odds, str):
        return None
    s = odds.strip().lower()
    if not s:
        return None
    if s in _EVS_ALIASES:
        return 2.0
    if "/" in s:
        parts = s.split("/", 1)
        try:
            num = float(parts[0])
            den = float(parts[1])
            if den > 0.0:
                decimal = num / den + 1.0
                return decimal if decimal > 1.0 else None
        except (ValueError, ZeroDivisionError):
            pass
    return None


def _decimal_from_entry(entry: dict) -> float | None:
    """Extract a valid decimal odds value from a market-file horse entry.

    Prefers the ``fractional_odds`` string (avoids rounding artefacts in
    synthetic prices) and falls back to ``decimal_odds`` float.

    Returns ``None`` when neither yields a value > 1.0.
    """
    if not isinstance(entry, dict):
        return None

    frac = entry.get("fractional_odds")
    if frac is not None:
        parsed = parse_fractional_odds(frac)
        if parsed is not None and parsed > 1.0:
            return parsed

    dec = entry.get("decimal_odds")
    if dec is not None:
        try:
            f = float(dec)
            return f if f > 1.0 else None
        except (TypeError, ValueError):
            pass

    return None


# ---------------------------------------------------------------------------
# Core gate logic — pure function, no I/O
# ---------------------------------------------------------------------------

def assess_market_drift(
    baseline_decimal: float | None,
    latest_decimal: float | None,
) -> dict:
    """Apply the market-drift gate to a pair of decimal-odds values.

    This is the pure scoring heart of the module.  All data-loading and
    horse-lookup concerns live in the wrapper functions below.

    Parameters
    ----------
    baseline_decimal : float | None
        Baseline decimal odds (e.g. ``13.0`` for 12/1 ante-post).
    latest_decimal : float | None
        Latest decimal odds (e.g. ``20.0`` for 19/1 race-day price).

    Returns
    -------
    dict with keys:
        ``score``                        — always 0.0 (gate-only, not additive)
        ``flags``                        — list[str] of signal flags
        ``adjusted_final_signal_multiplier`` — float to multiply into final_signal
        ``confidence_tier_override``     — ``"SPECULATIVE"`` or ``None``
    """
    _missing: dict = {
        "score": 0.0,
        "flags": ["MARKET_DATA_MISSING"],
        "adjusted_final_signal_multiplier": 1.0,
        "confidence_tier_override": None,
    }

    if baseline_decimal is None or latest_decimal is None:
        return _missing

    try:
        b = float(baseline_decimal)
        l = float(latest_decimal)
    except (TypeError, ValueError):
        return _missing

    if b <= 1.0 or l <= 1.0:
        return _missing

    drift_pct = (l - b) / b * 100.0
    abs_drift = abs(drift_pct)

    # Severe positive drift — checked first (takes precedence over DRIFT_WARN)
    if abs_drift >= 50.0 and drift_pct > 0:
        return {
            "score": 0.0,
            "flags": ["DRIFT_CRITICAL"],
            "adjusted_final_signal_multiplier": 0.80,
            "confidence_tier_override": "SPECULATIVE",
        }

    # Moderate positive drift
    if abs_drift >= 30.0 and drift_pct > 0:
        return {
            "score": 0.0,
            "flags": ["DRIFT_WARN"],
            "adjusted_final_signal_multiplier": 0.90,
            "confidence_tier_override": None,
        }

    # Steam — informational only, no multiplier penalty
    if abs_drift >= 30.0 and drift_pct < 0:
        return {
            "score": 0.0,
            "flags": ["STEAM_NOTED"],
            "adjusted_final_signal_multiplier": 1.0,
            "confidence_tier_override": None,
        }

    # Noise band (|drift_pct| < 30) — no effect
    return {
        "score": 0.0,
        "flags": [],
        "adjusted_final_signal_multiplier": 1.0,
        "confidence_tier_override": None,
    }


# ---------------------------------------------------------------------------
# File I/O — loader
# ---------------------------------------------------------------------------

def _load_snapshot(
    filename: str,
    path_override: str | None = None,
) -> dict[str, dict]:
    """Load one market snapshot; return ``{horse_name: entry_dict}`` or ``{}``."""
    path = path_override if path_override is not None else _find_data_file(filename)
    if path is None or not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}
    horses = raw.get("horses", {})
    return horses if isinstance(horses, dict) else {}


def load_market_drift_data(
    baseline_path: str | None = None,
    latest_path: str | None = None,
) -> dict[str, dict]:
    """Load and combine baseline + latest market snapshots for drift assessment.

    Parameters
    ----------
    baseline_path : str | None
        Explicit path to ``market-baseline.json``; uses auto-discovery when
        ``None``.
    latest_path : str | None
        Explicit path to ``market-latest.json``; uses auto-discovery when
        ``None``.

    Returns
    -------
    dict
        ``{ horse_name: {"baseline_decimal": float | None,
                         "latest_decimal":   float | None} }``

        Only horses with a baseline entry are included.  ``latest_decimal``
        is ``None`` when the horse has no entry in the latest snapshot.
    """
    baseline = _load_snapshot("market-baseline.json", baseline_path)
    latest = _load_snapshot("market-latest.json", latest_path)

    combined: dict[str, dict] = {}
    for horse, b_entry in baseline.items():
        b_dec = _decimal_from_entry(b_entry)
        l_entry = latest.get(horse, {})
        l_dec = _decimal_from_entry(l_entry) if l_entry else None
        combined[horse] = {
            "baseline_decimal": b_dec,
            "latest_decimal": l_dec,
        }
    return combined


# ---------------------------------------------------------------------------
# Public signal entry point
# ---------------------------------------------------------------------------

def market_drift_signal(
    horse: str,
    market_data: dict | None = None,
    *,
    baseline_decimal: float | None = None,
    latest_decimal: float | None = None,
) -> dict:
    """Market-drift gate signal for one runner.

    Callers may either pass a pre-loaded ``market_data`` dict (as returned by
    :func:`load_market_drift_data`) **or** supply decimal odds directly via
    the ``baseline_decimal`` / ``latest_decimal`` keyword args.

    Parameters
    ----------
    horse : str
        Runner name (used to look up ``market_data``).
    market_data : dict | None
        Combined market dict from :func:`load_market_drift_data`.  When
        ``None`` and no direct decimal odds are supplied, the module
        auto-loads from the default data files.
    baseline_decimal : float | None
        Keyword override: baseline decimal odds.  Bypasses market_data lookup.
    latest_decimal : float | None
        Keyword override: latest decimal odds.  Bypasses market_data lookup.

    Returns
    -------
    dict
        ``score``, ``flags``, ``adjusted_final_signal_multiplier``,
        ``confidence_tier_override``.
    """
    # Direct decimal override — used by inline callers and some tests
    if baseline_decimal is not None or latest_decimal is not None:
        return assess_market_drift(baseline_decimal, latest_decimal)

    # Auto-load from files when no dict provided
    if market_data is None:
        market_data = load_market_drift_data()

    if not isinstance(horse, str) or not horse.strip():
        return assess_market_drift(None, None)

    if not isinstance(market_data, dict):
        return assess_market_drift(None, None)

    entry = market_data.get(horse.strip())
    if not isinstance(entry, dict):
        return assess_market_drift(None, None)

    return assess_market_drift(
        entry.get("baseline_decimal"),
        entry.get("latest_decimal"),
    )
