"""Presentation helpers shared by report and racecard renderers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

try:  # package import in tests
    from .course_config import default_course, default_meeting, load_course_config, path_for, resolve_day, resolve_meeting
except ImportError:  # direct import via src/ on sys.path in cli.py
    from course_config import default_course, default_meeting, load_course_config, path_for, resolve_day, resolve_meeting


def _title_from_slug(slug: str) -> str:
    parts = [p for p in str(slug or "").split("-") if p]
    if not parts:
        return ""
    year = parts[-1] if parts[-1].isdigit() and len(parts[-1]) == 4 else ""
    words = parts[:-1] if year else parts
    title = " ".join(word.upper() if word.isupper() else word.capitalize() for word in words)
    return f"{title} {year}".strip()


def _meeting_title(course_cfg: dict[str, Any], meeting_slug: str, meeting: dict[str, Any]) -> str:
    for key in ("display_name", "title", "label", "name"):
        value = meeting.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    course_display = str(course_cfg.get("display_name") or course_cfg.get("course_slug") or "").strip()
    derived = _title_from_slug(meeting_slug)
    if not derived:
        return course_display

    # Preserve Epsom legacy headings while allowing non-Epsom meetings such as
    # royal-ascot-2026 to surface their meeting brand from the config slug.
    if course_cfg.get("course_slug") == default_course():
        return course_display

    if course_display and course_display.lower() in derived.lower().split():
        return derived
    return f"{course_display} {derived}".strip()


def presentation_context(
    *,
    date: str,
    course_slug: str | None = None,
    meeting_slug: str | None = None,
    venue_override: str | None = None,
    day_label_override: str | None = None,
) -> dict[str, Any]:
    """Resolve course/meeting/day display metadata for renderers."""
    course_slug = course_slug or default_course()
    meeting_slug = meeting_slug or default_meeting()
    course_cfg = load_course_config(course_slug)
    meeting = resolve_meeting(course_cfg, meeting_slug)
    day = dict(resolve_day(course_cfg, meeting_slug, date))
    if day_label_override:
        day["label"] = day_label_override

    try:
        weekday = datetime.strptime(date, "%Y-%m-%d").strftime("%A")
    except ValueError:
        weekday = ""
    if weekday:
        day.setdefault("weekday", weekday)

    course_display = str(course_cfg.get("display_name") or course_slug).strip()
    venue = (venue_override or course_display).strip()
    title = _meeting_title(course_cfg, meeting_slug, meeting)

    return {
        "course": {"slug": course_slug, "display_name": course_display, "config": course_cfg},
        "meeting": {"slug": meeting_slug, "title": title, "config": meeting},
        "day": day,
        "venue": venue,
        "title": title or venue,
    }


def default_course_display() -> str:
    """Return the configured display name for the default course."""
    cfg = load_course_config(default_course())
    return str(cfg.get("display_name") or default_course()).strip()


def output_path_for(kind: str, *, course_slug: str | None = None, date: str) -> Path:
    """Return the configured output path for report/racecard helpers."""
    return path_for(course_slug or default_course(), date, kind)
