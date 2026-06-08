"""
market_move.py — Market-movement signal v0.5
=============================================

Scores a runner based on implied-probability shift between the baseline
price (race-morning) and latest price (T−30 min before post).

Returns neutral 50 when:
- Horse not found in either enrichment file
- Latest prices not yet populated (operator hasn't run --mode latest)
- Either price is invalid (not a decimal odd > 1.0)

Scoring uses Danny's Δip piecewise-linear formula (NOT Livingston's
(b−l)/b strawman).  Source of truth: danny-3-signals-design.md §2.

Data files
----------
``data/enrichment/market-baseline.json``  — 272 horses, pre-race baseline
``data/enrichment/market-latest.json``    — operator-populated T−30 min snapshot

Both files use Livingston's schema (per livingston-market-move-data.md):
  ``horses: { "Horse Name": { "decimal_odds": float, ... } }``

The loader reads both files and produces a combined in-memory dict:
  ``{ "Horse Name": { "baseline_price": float, "latest_price": float } }``

If a horse appears in baseline but not in latest (pre-race-day default),
market_move_signal returns 50 (neutral).

Weight in scoring.py: 0.0700 (v0.5 config)
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

# ---------------------------------------------------------------------------
# Score-curve constants (Danny's spec §2)
# ---------------------------------------------------------------------------

_STEAMER_CAP = 0.07
_DRIFTER_CAP = -0.06
_NOISE_LO = -0.01
_NOISE_HI = 0.01


def _find_data_file(name: str) -> str | None:
    for d in _DATA_DIR_CANDIDATES:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    return None


def _snake_to_title(s: str) -> str:
    """Convert snake_case horse key to display name: james_j_braddock → James J Braddock."""
    return " ".join(word.capitalize() for word in s.split("_"))


def _extract_odds(entry: dict) -> float | None:
    """Return the first valid decimal odds value from a horse entry dict."""
    for field in ("decimal_odds", "odds_decimal"):
        val = entry.get(field)
        if val is not None:
            try:
                f = float(val)
                return f if f > 1.0 else None
            except (ValueError, TypeError):
                pass
    return None


def _parse_horses(horses: dict) -> dict[str, float]:
    """Parse a horses dict into {display_name: decimal_odds}.

    Handles two schemas:
    - Flat:   {HorseName: {decimal_odds: float, ...}}
    - Nested: {race_day: {race_slug: {snake_name: {odds_decimal: float, ...}}}}
    """
    result: dict[str, float] = {}
    for name, entry in horses.items():
        if not isinstance(entry, dict):
            continue
        odds = _extract_odds(entry)
        if odds is not None:
            # Flat schema — name is already the horse display name
            result[name] = odds
        else:
            # Nested schema — entry is {race_slug: {snake_horse: {odds_decimal: ...}}}
            for race_slug, race_runners in entry.items():
                if not isinstance(race_runners, dict):
                    continue
                for horse_key, horse_data in race_runners.items():
                    if not isinstance(horse_data, dict):
                        continue
                    h_odds = _extract_odds(horse_data)
                    if h_odds is not None:
                        display_name = _snake_to_title(horse_key)
                        result[display_name] = h_odds
    return result


def _load_snapshot(filename: str) -> dict[str, float]:
    """Load one snapshot file; return {horse_name: decimal_odds} or {}.

    Supports both the flat baseline schema ({HorseName: {decimal_odds: ...}})
    and the nested latest schema ({race_day: {race: {snake_name: {odds_decimal: ...}}}}).
    """
    path = _find_data_file(filename)
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
    return _parse_horses(horses)


def load_market_move_data(
    baseline_path: str | None = None,
    latest_path: str | None = None,
) -> dict[str, dict]:
    """Load and combine baseline + latest snapshots.

    Returns a dict keyed by horse name:
        { "Horse Name": {"baseline_price": float, "latest_price": float} }

    Only horses with a valid baseline price are included.  ``latest_price``
    is None when the horse has no entry in the latest snapshot.

    This is the non-cached version used directly by tests (accepts explicit
    paths).  Production callers use ``load_market_data()`` (lru_cached).
    """
    if baseline_path is not None:
        # Inline path override for tests — read directly
        try:
            with open(baseline_path, encoding="utf-8") as fh:
                raw_b = json.load(fh)
            baseline_raw = raw_b.get("horses", {})
        except (OSError, json.JSONDecodeError):
            baseline_raw = {}
        baseline: dict[str, float] = {}
        for name, entry in baseline_raw.items():
            if isinstance(entry, dict):
                odds = entry.get("decimal_odds")
                if odds is not None:
                    try:
                        odds_f = float(odds)
                        if odds_f > 1.0:
                            baseline[name] = odds_f
                    except (ValueError, TypeError):
                        pass
    else:
        baseline = _load_snapshot("market-baseline.json")

    if latest_path is not None:
        try:
            with open(latest_path, encoding="utf-8") as fh:
                raw_l = json.load(fh)
            latest_raw = raw_l.get("horses", {})
        except (OSError, json.JSONDecodeError):
            latest_raw = {}
        latest: dict[str, float] = _parse_horses(latest_raw) if isinstance(latest_raw, dict) else {}
    else:
        latest = _load_snapshot("market-latest.json")

    combined: dict[str, dict] = {}
    for horse, b_price in baseline.items():
        combined[horse] = {
            "baseline_price": b_price,
            "latest_price": latest.get(horse),  # None if not in latest
        }
    return combined


@lru_cache(maxsize=1)
def load_market_data() -> dict[str, dict]:
    """Cached loader for production use inside market_move_signal."""
    return load_market_move_data()


# ---------------------------------------------------------------------------
# Scoring — pure functions (Danny's spec §2)
# ---------------------------------------------------------------------------

def _lerp(lo: float, hi: float, t: float) -> float:
    """Linear interpolation: lo + t * (hi - lo).  t clamped to [0, 1]."""
    t = max(0.0, min(1.0, t))
    return lo + t * (hi - lo)


def score_market_move(delta_ip: float) -> float:
    """Map Δip to a 0–100 signal using Danny's piecewise-linear curve.

    Parameters
    ----------
    delta_ip : float
        ip_latest − ip_baseline.  Positive = steamer, negative = drifter.

    Returns
    -------
    float
        Score clamped to [10, 90].

    Examples (Danny's spec §2 test anchors):
    >>> round(score_market_move(0.024), 1)  # 7/1→6/1 → Δip≈+0.024
    62.0
    >>> round(score_market_move(0.076), 1)  # 6/4→11/10 → Δip≈+0.076
    90.0
    >>> round(score_market_move(-0.075), 1)  # 4/1→7/1 → Δip≈-0.075
    10.0
    >>> score_market_move(0.0)
    50.0
    """
    d = delta_ip

    # Steamer cap
    if d >= _STEAMER_CAP:
        return 90.0

    # Strong steamer: +0.03 ≤ d < +0.07  →  lerp(70 → 90)
    if d >= 0.03:
        t = (d - 0.03) / (_STEAMER_CAP - 0.03)
        return round(_lerp(70.0, 90.0, t), 10)

    # Mild steamer: +0.01 ≤ d < +0.03  →  lerp(55 → 70)
    if d >= _NOISE_HI:
        t = (d - _NOISE_HI) / (0.03 - _NOISE_HI)
        return round(_lerp(55.0, 70.0, t), 10)

    # Noise band: −0.01 < d < +0.01
    if d > _NOISE_LO:
        return 50.0

    # Mild drifter: −0.04 < d ≤ −0.01  →  lerp(30 → 50) over [−0.04, −0.01]
    if d > -0.04:
        t = (d - (-0.04)) / (_NOISE_LO - (-0.04))
        return round(_lerp(30.0, 50.0, t), 10)

    # Moderate drifter: −0.06 < d ≤ −0.04  →  lerp(10 → 30) over [−0.06, −0.04]
    if d > _DRIFTER_CAP:
        t = (d - _DRIFTER_CAP) / (-0.04 - _DRIFTER_CAP)
        return round(_lerp(10.0, 30.0, t), 10)

    # Drifter cap
    return 10.0


# ---------------------------------------------------------------------------
# Public signal entry point (scoring.py integration)
# ---------------------------------------------------------------------------

def market_move_signal(runner: dict, race: dict) -> float:  # noqa: ARG001
    """Market-movement signal for ``score_runner`` in scoring.py.

    Returns neutral 50 when:
      - Horse name absent or not found in baseline data
      - Latest price not yet populated (pre-race-day operator hasn't run snapshot)
      - Either price is invalid

    Parameters
    ----------
    runner : dict
        Runner dict; ``horse`` or ``horse_name`` is the lookup key.
    race : dict
        Not used (market prices embed all conditions already).

    Returns
    -------
    float
        0–100 signal (clamped to [10, 90] for valid moves).
    """
    if not isinstance(runner, dict):
        return 50.0

    horse = runner.get("horse") or runner.get("horse_name")
    if not horse:
        return 50.0

    data = load_market_data()
    entry = data.get(horse)
    if entry is None:
        return 50.0

    baseline_price = entry.get("baseline_price")
    latest_price = entry.get("latest_price")

    # Latest not yet populated → neutral
    if latest_price is None:
        return 50.0

    # Validate both prices are decimal odds > 1.0
    try:
        b = float(baseline_price)
        l = float(latest_price)
    except (TypeError, ValueError):
        return 50.0

    if b <= 1.0 or l <= 1.0:
        return 50.0

    ip_baseline = 1.0 / b
    ip_latest = 1.0 / l
    delta_ip = ip_latest - ip_baseline

    raw = score_market_move(delta_ip)
    return float(max(10.0, min(90.0, raw)))


# ---------------------------------------------------------------------------
# Test helper
# ---------------------------------------------------------------------------

def _clear_caches() -> None:  # pragma: no cover
    """Reset lru_cache (mirrors sires.py / trial_form.py pattern)."""
    load_market_data.cache_clear()
