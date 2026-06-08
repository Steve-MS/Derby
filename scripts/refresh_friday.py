"""
refresh_friday.py — Friday-morning odds refresh wrapper.

Run this on Friday 5 June 2026 once bookmakers post morning prices to:
  0. Run the T-60 artifact watchdog and abort on any stale/inconsistent gate
  1. (Optionally) merge fresh prices from a CSV you paste in
  2. Re-run enrich_odds.py (restores hardcoded ante-post + synthetic fallback)
  3. Re-score both meetings
  4. Re-predict both meetings (£200 bankroll)
  5. Re-generate HTML reports

USAGE
-----
Default (use existing hardcoded odds table in enrich_odds.py):
    py scripts\\refresh_friday.py

With a fresh prices CSV (recommended Friday AM):
    py scripts\\refresh_friday.py --prices data\\enrichment\\friday-prices.csv

CSV format (header required):
    date,horse,decimal_price,source
    2026-06-05,Amelia Earhart,3.0,sportinglife
    2026-06-06,Item,4.5,skysports

Any horse NOT in the CSV keeps the hardcoded enrich_odds.py value.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SOURCE_ROOT
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))
from src.course_config import (  # noqa: E402
    CourseConfigError,
    PROJECT_ROOT as COURSE_CONFIG_ROOT,
    default_course,
    default_meeting,
    load_course_config,
    path_for,
    resolve_meeting,
)

DATA_RAW = PROJECT_ROOT / "data" / "raw"
ENRICHMENT_DIR = PROJECT_ROOT / "data" / "enrichment"
DATES = ["2026-06-05", "2026-06-06"]
BANKROLL = 200
PY = sys.executable  # resolves to current interpreter — works around missing `python` on PATH


def _project_path_for(course_slug: str, date_str: str, kind: str) -> Path:
    canonical = path_for(course_slug, date_str, kind)
    try:
        return PROJECT_ROOT / canonical.relative_to(COURSE_CONFIG_ROOT)
    except ValueError:
        return canonical


def _meeting_dates(course_slug: str, meeting_slug: str) -> list[str]:
    cfg = load_course_config(course_slug)
    meeting = resolve_meeting(cfg, meeting_slug)
    days = meeting.get("days", {})
    return sorted(days)


def resolve_refresh_dates(course_slug: str, meeting_slug: str, date_arg: str | None) -> list[str]:
    """Resolve dates for refresh, keeping the old no-flag Epsom two-day wrapper."""
    if date_arg:
        return [date_arg]
    if course_slug == default_course() and meeting_slug == default_meeting():
        return DATES
    return _meeting_dates(course_slug, meeting_slug)


def run(cmd: list[str]) -> None:
    """Run a subprocess, streaming output, abort on non-zero exit."""
    print(f"\n$ {' '.join(cmd)}")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SOURCE_ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, env=env)
    if result.returncode != 0:
        sys.exit(f"FAILED: {' '.join(cmd)} (exit {result.returncode})")


def load_manual_prices(csv_path: Path, dates: list[str]) -> dict[str, dict[str, tuple[float, str]]]:
    """Return {date: {horse: (decimal_price, source)}}."""
    out: dict[str, dict[str, tuple[float, str]]] = {d: {} for d in dates}
    with csv_path.open(encoding="utf-8") as fh:
        non_comment = (line for line in fh if not line.lstrip().startswith("#"))
        for row in csv.DictReader(non_comment):
            date = row["date"].strip()
            horse = row["horse"].strip()
            price = float(row["decimal_price"])
            source = row.get("source", "manual").strip() or "manual"
            if date not in out:
                print(f"  WARN: unknown date {date} in CSV, skipping {horse}")
                continue
            out[date][horse] = (price, source)
    total = sum(len(v) for v in out.values())
    print(f"Loaded {total} manual prices from {csv_path.name}")
    return out


def apply_manual_overrides(date: str, overrides: dict[str, tuple[float, str]], course_slug: str) -> None:
    """Patch morning_price on the racecard JSON for any horse in overrides."""
    if not overrides:
        return
    path = _project_path_for(course_slug, date, "raw-racecards")
    with path.open(encoding="utf-8") as fh:
        card = json.load(fh)

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    matched: list[str] = []
    unmatched = set(overrides.keys())

    for race in card.get("races", []):
        for runner in race.get("runners", []):
            horse = runner.get("horse", "")
            if horse in overrides:
                price, source = overrides[horse]
                runner["morning_price"] = price
                runner["odds_source"] = source
                runner["odds_fetched_at"] = now
                matched.append(horse)
                unmatched.discard(horse)

    with path.open("w", encoding="utf-8") as fh:
        json.dump(card, fh, indent=2, ensure_ascii=False)

    print(f"  {date}: overrode {len(matched)} horses; {len(unmatched)} CSV rows unmatched")
    if unmatched:
        for h in sorted(unmatched):
            print(f"    UNMATCHED: {h}")

    audit_path = ENRICHMENT_DIR / f"odds-refresh-{date}-{now[:19].replace(':', '')}.json"
    ENRICHMENT_DIR.mkdir(parents=True, exist_ok=True)
    with audit_path.open("w", encoding="utf-8") as fh:
        json.dump(
            {
                "date": date,
                "fetched_at": now,
                "matched": sorted(matched),
                "unmatched_csv_rows": sorted(unmatched),
            },
            fh,
            indent=2,
        )
    print(f"  audit -> {audit_path.relative_to(PROJECT_ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Friday-morning odds refresh wrapper")
    parser.add_argument("--prices", type=Path, help="Optional CSV of fresh prices to override")
    parser.add_argument("--course", default=default_course(), help="Course slug (default: epsom)")
    parser.add_argument("--meeting", default=default_meeting(), help="Meeting slug (default: derby-2026)")
    parser.add_argument("--date", default=None, metavar="YYYY-MM-DD", help="Optional single race date; default preserves Epsom wrapper dates")
    parser.add_argument("--skip-enrich", action="store_true",
                        help="Skip enrich_odds.py (use only the CSV overrides)")
    args = parser.parse_args()

    try:
        load_course_config(args.course)
        resolve_meeting(load_course_config(args.course), args.meeting)
    except CourseConfigError as exc:
        sys.exit(f"Course config error: {exc}")

    dates = resolve_refresh_dates(args.course, args.meeting, args.date)

    print(f"=== refresh_friday.py @ {datetime.now().isoformat(timespec='seconds')} ===")
    print(f"Course={args.course} meeting={args.meeting} dates={', '.join(dates)}")

    print("\n[T-60] Running artifact watchdog")
    run([PY, str(PROJECT_ROOT / "scripts" / "t60_watchdog.py"), "--course", args.course, "--meeting", args.meeting, "--date", dates[0]])

    if not args.skip_enrich and args.course == default_course() and args.meeting == default_meeting():
        print("\n[1/4] Running enrich_odds.py (Epsom compatibility ante-post + synthetic fallback)")
        run([PY, str(PROJECT_ROOT / "enrich_odds.py")])
    elif not args.skip_enrich:
        print("\n[1/4] Skipping enrich_odds.py for non-Epsom config-driven refresh")
    else:
        print("\n[1/4] Skipping enrich_odds.py (--skip-enrich)")

    if args.prices:
        if not args.prices.exists():
            sys.exit(f"--prices file not found: {args.prices}")
        print(f"\n[2/4] Applying manual price overrides from {args.prices}")
        overrides = load_manual_prices(args.prices, dates)
        for date in dates:
            apply_manual_overrides(date, overrides.get(date, {}), args.course)
    else:
        print("\n[2/4] No --prices CSV supplied; skipping manual overrides")

    print("\n[3/4] Re-scoring configured meeting dates")
    for date in dates:
        run([PY, "-m", "src.cli", "score", "--course", args.course, "--meeting", args.meeting, "--date", date])

    print("\n[4/4] Re-predicting + reporting configured meeting dates")
    for date in dates:
        run([PY, "-m", "src.cli", "predict", "--course", args.course, "--meeting", args.meeting, "--date", date, "--bankroll", str(BANKROLL)])
        run([PY, "-m", "src.cli", "report", "--course", args.course, "--meeting", args.meeting, "--date", date])
        run([PY, "-m", "src.cli", "card", "--course", args.course, "--meeting", args.meeting, "--date", date, "--outlay", "100"])

    print("\n=== Done. Open outputs\\report-*.html (full HTML) and racecard-*.html (printable slip) ===")


if __name__ == "__main__":
    main()
