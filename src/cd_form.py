"""
cd_form.py — Course & Distance form signal v0.1
================================================

Derives Course/Distance/CD/BF (Beaten Favourite) status from the
Racing Post badge tokens captured in the runner ``notes`` field
(format: ``... badges X, Y, Z; ...``), and emits a 0-100 signal.

Why this exists
---------------
The original ``_cd_signal`` in ``scoring.py`` reads structured fields
(``cd_wins``, ``course_wins``, ``first_time_epsom``) that are never
populated by the racecard scraper — so it always returned a neutral
50. RP shows the same information in the form of coloured badges
next to each horse on the racecard, which the scraper preserves as
text inside ``notes``. This module extracts them and produces a
useful signal.

Anti-fabrication
----------------
- If ``notes`` is missing or contains no recognisable ``badges …``
  segment, the signal returns 50 (neutral, NOT a penalty).
- The first-time-Epsom-at-Derby-trip penalty is only applied when
  there is positive evidence (the runner has no C/CD badge AND the
  race is at Epsom AND distance >= 12f). For mature handicappers
  with no badges, neutral 50 is returned (we can't tell if they've
  never tried Epsom or simply haven't won there).
"""
from __future__ import annotations

import re
from typing import Iterable

# Tokens RP uses on the racecard
_BADGE_TOKENS = {"CD", "C", "D", "BF"}

_BADGES_RE = re.compile(
    r"badges\s+([A-Za-z, ]+?)(?:\s*;|\s*source\b|$)",
    flags=re.IGNORECASE,
)


def extract_badges(runner: dict) -> set[str]:
    """Extract the set of RP badges for a runner.

    Returns
    -------
    set[str]
        Subset of {"CD", "C", "D", "BF"}. Empty set if no badges
        could be parsed.
    """
    notes = runner.get("notes")
    if not notes or not isinstance(notes, str):
        return set()

    match = _BADGES_RE.search(notes)
    if not match:
        return set()

    raw = match.group(1)
    tokens = {tok.strip().upper() for tok in re.split(r"[, ]+", raw) if tok.strip()}
    return tokens & _BADGE_TOKENS


def cd_form_signal(runner: dict, race: dict) -> float:
    """Course & Distance form signal derived from RP badges (0-100).

    Mapping
    -------
    - CD (course+distance winner)       -> 80
    - D  (distance winner)              -> 70
    - C  (course winner)                -> 62
    - BF (beaten favourite last time)   -> 55  (modest positive)
    - No badge, no penalty trigger      -> 50  (neutral)
    - First-time Epsom at 12f+ (no C/CD/D):
        -> 40 penalty applied to the neutral baseline

    If a horse holds multiple badges, the strongest one wins
    (CD > D > C > BF). BF is treated additively only when no
    course-form badge is present.

    Parameters
    ----------
    runner : dict
        Runner dict; ``notes`` field is consulted.
    race : dict
        Race dict; ``course`` and ``distance_f`` consulted for the
        first-time-Epsom-long-trip rule.

    Returns
    -------
    float
        0-100 (clamped).
    """
    badges = extract_badges(runner)

    # Strongest badge wins
    if "CD" in badges:
        return 80.0
    if "D" in badges:
        return 70.0
    if "C" in badges:
        return 62.0
    if "BF" in badges:
        return 55.0

    # No badges — apply first-time Epsom long-trip penalty if
    # explicitly flagged on the runner. Otherwise neutral.
    course = (race.get("course") or "").strip().lower()
    dist_f = float(race.get("distance_f") or race.get("distance_furlongs") or 0.0)
    first_epsom = bool(runner.get("first_time_epsom", False))
    if first_epsom and course == "epsom" and dist_f >= 12.0:
        return 40.0
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
