"""Course config and canonical path helpers.

Chunk 1 of the course-decoupling work keeps Epsom as the compatibility
baseline while allowing new courses to use explicit course-prefixed artifacts.
Resolution rule: ``course_slug == "epsom"`` returns the legacy file names that
existing operators and historical outputs use (for example
``outputs/racecard-2026-06-06.html``). Any other course returns the new
course-prefixed names (for example ``outputs/racecard-ascot-2026-06-16.html``).
Raw racecards are already flat and course-prefixed for every course:
``data/raw/{course}-{date}-racecards.json``.

Unknown meeting/date resolution is a loud failure: ``resolve_meeting`` and
``resolve_day`` raise ``CourseConfigError`` instead of returning ``None`` so bad
operator input cannot silently render a nonsense card.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config" / "courses"

_DEFAULT_COURSE = "epsom"
_DEFAULT_MEETING = "derby-2026"

_REQUIRED_TOP_LEVEL = {
    "course_slug",
    "display_name",
    "racingpost",
    "aliases",
    "meetings",
    "draw_bias",
    "course_distance",
    "defaults",
}
_REQUIRED_RACINGPOST = {"course_id", "course_path"}
_OUTPUT_EXTENSIONS = {
    "scores": "json",
    "bets": "json",
    "report": "html",
    "racecard": "html",
    "slip": "txt",
}


class CourseConfigError(ValueError):
    """Raised when course configuration or operator selection is invalid."""


def _normalise_slug(course_slug: str) -> str:
    slug = str(course_slug or "").strip().lower()
    if not slug:
        raise CourseConfigError("course slug is required")
    if not re.fullmatch(r"[a-z0-9-]+", slug):
        raise CourseConfigError(f"invalid course slug {course_slug!r}; use lowercase letters, numbers, and hyphens")
    return slug


def load_course_config(course_slug: str) -> dict[str, Any]:
    """Load and validate ``config/courses/{course}.json``."""
    slug = _normalise_slug(course_slug)
    path = CONFIG_DIR / f"{slug}.json"
    if not path.exists():
        raise CourseConfigError(f"course config not found for {slug!r}: {path}")

    try:
        with path.open(encoding="utf-8") as fh:
            cfg = json.load(fh)
    except json.JSONDecodeError as exc:
        raise CourseConfigError(f"invalid JSON in course config {path}: {exc}") from exc

    if not isinstance(cfg, dict):
        raise CourseConfigError(f"course config {path} must be a JSON object")

    missing = sorted(_REQUIRED_TOP_LEVEL - cfg.keys())
    if missing:
        raise CourseConfigError(f"course config {path} missing required field(s): {', '.join(missing)}")

    if cfg.get("course_slug") != slug:
        raise CourseConfigError(f"course config {path} course_slug {cfg.get('course_slug')!r} does not match {slug!r}")

    racingpost = cfg.get("racingpost")
    if not isinstance(racingpost, dict):
        raise CourseConfigError(f"course config {path} field 'racingpost' must be an object")
    rp_missing = sorted(_REQUIRED_RACINGPOST - racingpost.keys())
    if rp_missing:
        raise CourseConfigError(f"course config {path} racingpost missing required field(s): {', '.join(rp_missing)}")

    if not isinstance(cfg.get("aliases"), list):
        raise CourseConfigError(f"course config {path} field 'aliases' must be a list")
    if not isinstance(cfg.get("meetings"), dict):
        raise CourseConfigError(f"course config {path} field 'meetings' must be an object")
    for meeting_slug, meeting in cfg["meetings"].items():
        if not isinstance(meeting, dict) or not isinstance(meeting.get("days"), dict):
            raise CourseConfigError(f"course config {path} meeting {meeting_slug!r} must contain a 'days' object")

    return cfg


def resolve_meeting(course_cfg: dict[str, Any], meeting_slug: str) -> dict[str, Any]:
    """Return a meeting sub-dict or raise ``CourseConfigError``."""
    meetings = course_cfg.get("meetings")
    if not isinstance(meetings, dict):
        raise CourseConfigError(f"course config {course_cfg.get('course_slug', '<unknown>')!r} has no meetings object")
    if meeting_slug not in meetings:
        raise CourseConfigError(f"unknown meeting {meeting_slug!r} for course {course_cfg.get('course_slug', '<unknown>')!r}")
    meeting = meetings[meeting_slug]
    if not isinstance(meeting, dict):
        raise CourseConfigError(f"meeting {meeting_slug!r} must be an object")
    return meeting


def resolve_day(course_cfg: dict[str, Any], meeting_slug: str, date_str: str) -> dict[str, Any]:
    """Return day metadata or raise ``CourseConfigError`` for unknown dates."""
    meeting = resolve_meeting(course_cfg, meeting_slug)
    days = meeting.get("days")
    if not isinstance(days, dict):
        raise CourseConfigError(f"meeting {meeting_slug!r} must contain a days object")
    if date_str not in days:
        raise CourseConfigError(f"unknown date {date_str!r} for meeting {meeting_slug!r}")
    day = days[date_str]
    if not isinstance(day, dict):
        raise CourseConfigError(f"day metadata for {date_str!r} must be an object")
    return day


def default_course() -> str:
    """Return the backward-compatible default course slug."""
    return _DEFAULT_COURSE


def default_meeting() -> str:
    """Return the backward-compatible default meeting slug."""
    return _DEFAULT_MEETING


def _output_path(course_slug: str, date_str: str, kind: str) -> Path:
    ext = _OUTPUT_EXTENSIONS[kind]
    filename = f"{kind}-{date_str}.{ext}" if course_slug == _DEFAULT_COURSE else f"{kind}-{course_slug}-{date_str}.{ext}"
    return PROJECT_ROOT / "outputs" / filename


def path_for(course_slug: str, date_str: str, kind: str) -> Path:
    """Return the canonical artifact path for a course/date/kind.

    Supported kinds: ``raw-racecards``, ``scores``, ``bets``, ``report``,
    ``racecard``, ``slip``, ``results``, and ``enrichment-{name}``.
    """
    slug = _normalise_slug(course_slug)
    if not date_str:
        raise CourseConfigError("date_str is required")

    if kind == "raw-racecards":
        return PROJECT_ROOT / "data" / "raw" / f"{slug}-{date_str}-racecards.json"
    if kind in _OUTPUT_EXTENSIONS:
        return _output_path(slug, date_str, kind)
    if kind == "results":
        filename = f"results-{date_str}.json" if slug == _DEFAULT_COURSE else f"results-{slug}-{date_str}.json"
        return PROJECT_ROOT / "data" / "results" / filename
    if kind.startswith("enrichment-"):
        name = kind.removeprefix("enrichment-")
        if not name:
            raise CourseConfigError("enrichment kind must include a name, e.g. enrichment-going")
        filename = f"{name}-{date_str}.json" if slug == _DEFAULT_COURSE else f"{name}-{slug}-{date_str}.json"
        return PROJECT_ROOT / "data" / "enrichment" / filename

    raise CourseConfigError(f"unknown path kind {kind!r}")


def race_id_for(course_slug: str, date_str: str, off_time: str) -> str:
    """Return a canonical race id: ``{course}-{date}-{HHMM}``."""
    slug = _normalise_slug(course_slug)
    time_slug = str(off_time or "").strip().replace(":", "")
    if not re.fullmatch(r"\d{3,4}", time_slug):
        raise CourseConfigError(f"invalid race off_time {off_time!r}")
    return f"{slug}-{date_str}-{time_slug.zfill(4)}"
