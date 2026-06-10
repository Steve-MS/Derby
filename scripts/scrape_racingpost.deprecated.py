#!/usr/bin/env python3
"""
DEPRECATED in v0.5.0.

Racing Post automated scraping is deprecated for ToS hygiene. This repository
no longer ships automated Racing Post racecard capture because it follows the
same ToS risk pattern noted for Sporting Life.

Use `race-analysis fetch --from-file` instead: save the racecard page in your
browser from your legitimate personal-use view, then parse the saved HTML.

This script will be REMOVED in v0.6.0.
"""

from __future__ import annotations

import sys

sys.exit("scrape_racingpost.py is deprecated. See module docstring or CHANGELOG v0.5.0.")

# Original code below is retained for historical reference only and is unreachable.

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

RP_RACECARD_URL = "https://www.racingpost.com/racecards/{course_id}/{course_path}/{date}"
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


def build_plan(course_slug: str, meeting_slug: str, race_date: str) -> dict:
    cfg = load_course_config(course_slug)
    resolve_meeting(cfg, meeting_slug)
    rp_cfg = cfg.get("racingpost", {})
    course_id = rp_cfg.get("course_id")
    course_path = rp_cfg.get("course_path")
    if course_id is None or not course_path:
        raise CourseConfigError(f"Racing Post config incomplete for {course_slug!r}")
    output_path = _project_path_for(course_slug, race_date, "enrichment-racingpost")
    url = RP_RACECARD_URL.format(course_id=course_id, course_path=course_path, date=race_date)
    return {
        "course": course_slug,
        "meeting": meeting_slug,
        "date": race_date,
        "url": url,
        "output_path": _relative(output_path),
        "course_id": course_id,
        "course_path": course_path,
    }


def _extract_next_data(html: str) -> dict | None:
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
    if not match:
        return None
    return json.loads(match.group(1))


def _extract_runner_names(obj, names: list[str], depth: int = 0) -> None:
    if depth > 30:
        return
    if isinstance(obj, dict):
        horse = obj.get("horseName")
        if isinstance(horse, str) and horse.strip():
            names.append(horse.strip())
        for value in obj.values():
            _extract_runner_names(value, names, depth + 1)
    elif isinstance(obj, list):
        for item in obj:
            _extract_runner_names(item, names, depth + 1)


def scrape(plan: dict) -> dict:
    req = Request(plan["url"], headers=HEADERS)
    with urlopen(req, timeout=25) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    next_data = _extract_next_data(html)
    names: list[str] = []
    if next_data is not None:
        _extract_runner_names(next_data, names)
    return {
        **plan,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "html_bytes": len(html.encode("utf-8")),
        "runner_names": sorted(set(names)),
        "runner_count": len(set(names)),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape Racing Post racecard data for a configured course/date")
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
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"Racing Post scrape failed: {exc}", file=sys.stderr)
        return 1

    output_path = PROJECT_ROOT / plan["output_path"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": "ok", "output_path": plan["output_path"], "runner_count": payload["runner_count"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
