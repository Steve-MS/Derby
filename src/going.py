"""Ground-condition (going) fit helpers for the scoring model."""

from __future__ import annotations

from typing import Any

CANONICAL_GOINGS: tuple[str, ...] = (
    "Heavy",
    "Soft",
    "Good to Soft",
    "Good",
    "Good to Firm",
    "Firm",
)

_GOING_INDEX = {going.lower(): i for i, going in enumerate(CANONICAL_GOINGS)}
_ALIASES = {
    "good to soft in places": "Good to Soft",
    "good; good to firm in places": "Good",
    "good, good to firm in places": "Good",
    "good to firm in places": "Good to Firm",
    "good to soft": "Good to Soft",
    "good-to-soft": "Good to Soft",
    "good to firm": "Good to Firm",
    "good-to-firm": "Good to Firm",
}


def normalise_going(value: Any) -> str | None:
    """Return a canonical going string, or None when the value is blank."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    key = text.lower()
    if key in _ALIASES:
        return _ALIASES[key]
    if "good to soft" in key:
        return "Good to Soft"
    if "good to firm" in key:
        return "Good to Firm"
    for canonical in CANONICAL_GOINGS:
        if key == canonical.lower():
            return canonical
    for canonical in CANONICAL_GOINGS:
        if canonical.lower() in key:
            return canonical
    return None


def going_similarity(target: Any, observed: Any) -> float:
    """Similarity between two going values on a simple going-family ladder."""
    target_norm = normalise_going(target)
    observed_norm = normalise_going(observed)
    if target_norm is None or observed_norm is None:
        return 0.0
    distance = abs(_GOING_INDEX[target_norm.lower()] - _GOING_INDEX[observed_norm.lower()])
    if distance <= 1:
        return 1.0
    if distance == 2:
        return 0.5
    if distance == 3:
        return 0.25
    return 0.0


def score_going_fit(runs: list[dict] | None, target_going: Any) -> dict[str, Any]:
    """Score historical fit to target going on a 0.0-1.0 scale.

    Uses going-family similarity, weighted win rate, effective sample size,
    and recency. Returns ``going_data='insufficient'`` when no historical run
    contains usable adjacent/matching going evidence.
    """
    target_norm = normalise_going(target_going)
    if target_norm is None:
        return {"score": 0.5, "going_data": "not_applicable", "target_going": None}

    weighted_runs = 0.0
    weighted_wins = 0.0
    for index, run in enumerate((runs or [])[:10]):
        similarity = going_similarity(target_norm, run.get("going"))
        if similarity <= 0:
            continue
        recency = _recency_weight(run, index)
        weight = similarity * recency
        weighted_runs += weight
        if _is_win(run.get("position")):
            weighted_wins += weight

    if weighted_runs <= 0:
        return {"score": 0.35, "going_data": "insufficient", "target_going": target_norm}

    win_rate = weighted_wins / weighted_runs
    confidence = min(1.0, weighted_runs / 3.0)
    score = 0.35 + (0.50 * win_rate) + (0.15 * confidence)
    return {
        "score": max(0.0, min(1.0, score)),
        "going_data": "sufficient",
        "target_going": target_norm,
        "effective_runs": round(weighted_runs, 3),
        "weighted_win_rate": round(win_rate, 3),
    }


def _recency_weight(run: dict, index: int) -> float:
    days = run.get("days_ago") or run.get("days_since_last_run")
    if days is None:
        fallback = [1.0, 0.8, 0.6, 0.4, 0.25]
        return fallback[index] if index < len(fallback) else 0.15
    try:
        days_float = float(days)
    except (TypeError, ValueError):
        return 0.5
    if days_float <= 60:
        return 1.0
    if days_float <= 180:
        return 0.75
    if days_float <= 365:
        return 0.5
    return 0.25


def _is_win(position: Any) -> bool:
    try:
        return int(position) == 1
    except (TypeError, ValueError):
        return False
