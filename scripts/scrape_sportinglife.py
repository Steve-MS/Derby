#!/usr/bin/env python3
"""Sporting Life racecard scrape planner/fetcher.

The course aliases come from config/courses/*.json so venue matching is not
hardcoded to Epsom Downs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date as date_cls
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.course_config import (  # noqa: E402
    CourseConfigError,
    PROJECT_ROOT as COURSE_CONFIG_ROOT,
    default_course,
    default_meeting,
    load_course_config,
    path_for,
    resolve_meeting,
)

SL_RACECARDS_URL = "https://www.sportinglife.com/racing/racecards/{date}/{course_path}"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json,*/*;q=0.9",
    "Accept-Language": "en-GB,en;q=0.9",
}


def _project_path_for(course_slug: str, date_str: str, kind: str) -> Path:
    canonical = path_for(course_slug, date_str, kind)
    try:
        return PROJECT_ROOT / canonical.relative_to(COURSE_CONFIG_ROOT)
    except ValueError:
        return canonical


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _slugify_alias(alias: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", alias.strip().lower()).strip("-")


def _sportinglife_course_path(course_slug: str, aliases: list[str]) -> str:
    if course_slug == default_course():
        downs_alias = next((alias for alias in aliases if "downs" in alias.casefold()), None)
        if downs_alias:
            return _slugify_alias(downs_alias)
    return _slugify_alias(aliases[0] if aliases else course_slug)


def matches_course_alias(venue_name: str, aliases: list[str]) -> bool:
    venue = venue_name.strip().casefold()
    return any(venue == alias.strip().casefold() for alias in aliases)


def build_plan(course_slug: str, meeting_slug: str, race_date: str) -> dict:
    cfg = load_course_config(course_slug)
    resolve_meeting(cfg, meeting_slug)
    aliases = [str(alias) for alias in cfg.get("aliases", [])]
    course_path = _sportinglife_course_path(course_slug, aliases)
    output_path = _project_path_for(course_slug, race_date, "enrichment-sportinglife")
    url = SL_RACECARDS_URL.format(date=race_date, course_path=course_path)
    return {
        "course": course_slug,
        "meeting": meeting_slug,
        "date": race_date,
        "url": url,
        "output_path": _relative(output_path),
        "course_path": course_path,
        "course_aliases": aliases,
    }


def scrape(plan: dict) -> dict:
    req = Request(plan["url"], headers=HEADERS)
    with urlopen(req, timeout=25) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    return {
        **plan,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "html_bytes": len(html.encode("utf-8")),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape Sporting Life racecard data for a configured course/date")
    parser.add_argument("--course", default=default_course(), help="Course slug (default: epsom)")
    parser.add_argument("--meeting", default=default_meeting(), help="Meeting slug (default: derby-2026)")
    parser.add_argument("--date", default=date_cls.today().isoformat(), metavar="YYYY-MM-DD", help="Race date (default: today)")
    parser.add_argument("--dry-run", action="store_true", help="Print URL/output plan without fetching or writing")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        plan = build_plan(args.course, args.meeting, args.date)
    except CourseConfigError as exc:
        print(f"Course config error: {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        print(json.dumps({**plan, "dry_run": True}, indent=2))
        return 0

    try:
        payload = scrape(plan)
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"Sporting Life scrape failed: {exc}", file=sys.stderr)
        return 1

    output_path = PROJECT_ROOT / plan["output_path"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": "ok", "output_path": plan["output_path"], "html_bytes": payload["html_bytes"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
