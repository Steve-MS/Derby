"""Pace / run-style and course-configured draw-bias scoring.

Signals are 0-100, neutral = 50. Course-specific values are loaded from
``config/courses/{course}.json`` via ``scoring_priors``.
"""

from __future__ import annotations

try:  # supports direct `sys.path` imports and package imports
    from course_config import default_course, scoring_priors_for
except ImportError:  # pragma: no cover
    from .course_config import default_course, scoring_priors_for


# --- Run-style inference --------------------------------------------------- #

RUN_STYLES = ("LED", "PROM", "MID", "HELD")


def _course_slug(course: str | None = None, race: dict | None = None) -> str:
    explicit = course or (race or {}).get("course_slug") or (race or {}).get("course") or default_course()
    return str(explicit).strip().lower().replace(" ", "-")


def _epsom_draw_table() -> dict[tuple[str, float], dict]:
    extended = scoring_priors_for("epsom").get("draw_bias", {}).get("extended", {})
    return {("epsom", float(dist)): dict(values) for dist, values in extended.items()}


EPSOM_DRAW_TABLE = _epsom_draw_table()


def infer_run_style(runner: dict) -> str:
    """Best-effort run-style inference from form data."""
    explicit = (runner.get("run_style") or "").upper().strip()
    if explicit in RUN_STYLES:
        return explicit

    form = runner.get("form_string") or ""
    digits = [int(c) for c in form if c.isdigit()]
    if not digits:
        return "HELD"

    avg_adj = sum((d if d > 0 else 9) for d in digits) / len(digits)

    if avg_adj <= 2.5:
        return "PROM"
    if avg_adj <= 4.5:
        return "MID"
    if avg_adj <= 7.0:
        return "MID"
    return "HELD"


def project_race_pace(runners: list[dict]) -> str:
    """Classify projected pace based on the field's run-style mix."""
    led_or_prom = sum(
        1 for r in runners if infer_run_style(r) in ("LED", "PROM")
    )
    total = max(1, len(runners))

    if led_or_prom == 0:
        return "NO_PACE"
    if led_or_prom == 1:
        return "LONE_LEAD"
    if led_or_prom / total >= 0.30:
        return "DUEL"
    return "EVEN"


def pace_signal(
    runner: dict,
    race_pace: str,
    course: str | None = None,
    priors: dict | None = None,
) -> float:
    """Score this runner's pace fit (0-100) using course priors."""
    style = infer_run_style(runner)
    pace_priors = priors or scoring_priors_for(_course_slug(course)).get("pace_modifiers", {})
    default_signal = float(pace_priors.get("default_signal", 50.0))
    table = pace_priors.get("fit_table") or {}
    return float(table.get(race_pace, {}).get(style, default_signal))


# --- Extended draw bias ---------------------------------------------------- #


def extended_draw_signal(
    runner: dict,
    race: dict,
    course: str | None = None,
    priors: dict | None = None,
) -> float | None:
    """Return configured draw signal, or ``None`` when no table applies."""
    course_slug = _course_slug(course, race)
    draw_priors = priors or scoring_priors_for(course_slug).get("draw_bias", {})
    extended = draw_priors.get("extended") or {}
    if not extended:
        return None

    dist = race.get("distance_f") or race.get("distance_furlongs")
    if dist is None:
        return None
    try:
        dist_f = float(dist)
    except (TypeError, ValueError):
        return None

    key_dist = round(dist_f * 2) / 2
    table = extended.get(f"{key_dist:.1f}") or extended.get(str(key_dist))
    if table is None:
        return None

    going = (race.get("going") or "").lower().strip()
    going_filter = table.get("going_filter")
    if going_filter and going not in going_filter:
        return 50.0

    draw = runner.get("draw")
    if draw is None:
        return 50.0
    try:
        draw_n = int(draw)
    except (TypeError, ValueError):
        return 50.0

    field_size = len(race.get("runners") or []) or 1
    damp = min(1.0, field_size / max(1, int(table.get("field_size_pivot", 1))))

    if draw_n <= int(table.get("low_threshold", 0)):
        raw = float(table.get("low", 50.0))
    elif draw_n > int(table.get("high_threshold", 0)):
        raw = float(table.get("high", 50.0))
    else:
        raw = float(table.get("mid", 50.0))

    return 50.0 + (raw - 50.0) * damp
