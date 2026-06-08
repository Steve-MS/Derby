"""
cd_form.py — Course & Distance form signal v0.1
===============================================

Derives Course/Distance/CD/BF status from Racing Post badge tokens and emits a
0-100 signal. Course-specific badge and first-time-course priors come from
``config/courses/{course}.json``.
"""
from __future__ import annotations

import re
from typing import Iterable

try:
    from course_config import default_course, scoring_priors_for
except ImportError:  # pragma: no cover
    from .course_config import default_course, scoring_priors_for

_BADGE_TOKENS = {"CD", "C", "D", "BF"}

_BADGES_RE = re.compile(
    r"badges\s+([A-Za-z, ]+?)(?:\s*;|\s*source\b|$)",
    flags=re.IGNORECASE,
)


def _course_slug(course: str | None = None, race: dict | None = None) -> str:
    explicit = course or (race or {}).get("course_slug") or (race or {}).get("course") or default_course()
    return str(explicit).strip().lower().replace(" ", "-")


def extract_badges(runner: dict) -> set[str]:
    """Extract the set of RP badges for a runner."""
    notes = runner.get("notes")
    if not notes or not isinstance(notes, str):
        return set()

    match = _BADGES_RE.search(notes)
    if not match:
        return set()

    raw = match.group(1)
    tokens = {tok.strip().upper() for tok in re.split(r"[, ]+", raw) if tok.strip()}
    return tokens & _BADGE_TOKENS


def cd_form_signal(
    runner: dict,
    race: dict,
    course: str | None = None,
    priors: dict | None = None,
) -> float:
    """Course & Distance form signal derived from RP badges (0-100)."""
    cd_priors = priors or scoring_priors_for(_course_slug(course, race)).get("cd_form_weights", {})
    badge_scores = cd_priors.get("badge_scores", {})
    badges = extract_badges(runner)

    for token in ("CD", "D", "C", "BF"):
        if token in badges:
            return float(badge_scores.get(token, 50.0))

    first_time = cd_priors.get("first_time_long_trip") or {}
    flag = first_time.get("runner_flag", "first_time_epsom")
    dist_f = float(race.get("distance_f") or race.get("distance_furlongs") or 0.0)
    if (
        first_time.get("enabled", False)
        and bool(runner.get(flag, False))
        and dist_f >= float(first_time.get("min_distance_f", 999.0))
    ):
        return float(first_time.get("score", 50.0))
    return 50.0


def badge_summary(runners: Iterable[dict]) -> dict[str, int]:
    """Count badge frequencies across a list of runners (diagnostic helper)."""
    counts: dict[str, int] = {"CD": 0, "C": 0, "D": 0, "BF": 0, "none": 0}
    for r in runners:
        b = extract_badges(r)
        if not b:
            counts["none"] += 1
            continue
        for tok in b:
            counts[tok] += 1
    return counts
