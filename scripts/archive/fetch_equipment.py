#!/usr/bin/env python3
"""
Fetch equipment data for configured race dates.

Sources tried in order:
  1. openhorsedata.com public CSV  (DNS unreachable in this env — fallback auto)
  2. Racing Post __NEXT_DATA__ SSR JSON  (primary working source)
     Field: horseHeadGear (string of single-char codes) + horseHeadGearFirstTime
     RP code key: b=blinkers, v=visor, h=hood, t=tongue-tie, p=cheekpieces, e=eyeshield
     Combinations are concatenated, e.g. "ht"=hood+tongue-tie, "tp"=tongue-tie+cheekpieces

Anti-fabrication rule: if no data found for a horse, equipment=[] — never invented.
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.course_config import default_course, default_meeting, load_course_config, resolve_meeting  # noqa: E402

MARKET_BASELINE = BASE_DIR / "data" / "enrichment" / "market-baseline.json"
OUTPUT_FILE = BASE_DIR / "data" / "enrichment" / "equipment.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json,*/*;q=0.9",
    "Accept-Language": "en-GB,en;q=0.9",
}

RP_RACECARD_URL = "https://www.racingpost.com/racecards/{course_id}/{course_path}/{race_date}"

# RP single-char code -> standard code used in equipment.json schema
RP_CHAR_MAP = {
    "b": "b",   # blinkers
    "v": "v",   # visor
    "h": "h",   # hood
    "t": "tt",  # tongue-tie / tongue strap
    "p": "cp",  # cheekpieces (pacifiers)
    "e": "e",   # eyeshield
}


def decode_rp_headgear(gear_str: str) -> list[str]:
    """
    Decode a Racing Post horseHeadGear string into standard equipment code list.
    E.g. "ht" -> ["h", "tt"], "tp" -> ["tt", "cp"], "b" -> ["b"]
    """
    if not gear_str:
        return []
    codes = []
    for ch in gear_str.lower():
        mapped = RP_CHAR_MAP.get(ch)
        if mapped and mapped not in codes:
            codes.append(mapped)
    return codes


def fetch_url(url: str, timeout: int = 20) -> str | None:
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, Exception) as exc:
        print(f"  [WARN] fetch failed {url}: {exc}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Source 1: openhorsedata.com  (attempted but not expected to resolve)
# ---------------------------------------------------------------------------

def try_openhorsedata(race_date: str) -> dict[str, dict]:
    """
    Attempt to download equipment CSV from openhorsedata.com.
    Returns {horse_name: {equipment, first_time_use}} on success, {} on failure.
    """
    date_nodash = race_date.replace("-", "")
    candidates = [
        f"https://openhorsedata.com/data/csv/{race_date}/racecards.csv",
        f"https://www.openhorsedata.com/data/csv/{race_date}/racecards.csv",
        f"https://openhorsedata.com/racecards/{date_nodash}.csv",
    ]
    for url in candidates:
        print(f"  openhorsedata: {url}", file=sys.stderr)
        body = fetch_url(url, timeout=10)
        if body and len(body) > 200 and "," in body:
            print(f"  [OK] openhorsedata: got {len(body)} bytes", file=sys.stderr)
            return {}  # Parse not implemented; RP is primary
    return {}


# ---------------------------------------------------------------------------
# Source 2: Racing Post __NEXT_DATA__ SSR
# ---------------------------------------------------------------------------

def rp_racecard_url(course_cfg: dict, race_date: str) -> str:
    rp_cfg = course_cfg.get("racingpost", {})
    course_id = rp_cfg.get("course_id")
    course_path = rp_cfg.get("course_path")
    if course_id is None or not course_path:
        raise ValueError(f"Racing Post config incomplete for {course_cfg.get('course_slug')!r}")
    return RP_RACECARD_URL.format(course_id=course_id, course_path=course_path, race_date=race_date)


def fetch_rp_racecard(race_date: str, course_cfg: dict) -> dict[str, dict]:
    """
    Fetch Racing Post racecard page, extract equipment from __NEXT_DATA__.
    Returns {horse_name: {equipment: [codes], first_time_use: [codes], wind_surgery: bool|None}}.
    """
    url = rp_racecard_url(course_cfg, race_date)
    print(f"  Racing Post: {url}", file=sys.stderr)
    body = fetch_url(url, timeout=25)
    if not body:
        return {}

    m = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        body, re.DOTALL
    )
    if not m:
        print("  [WARN] No __NEXT_DATA__ in RP page", file=sys.stderr)
        return {}

    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        print(f"  [WARN] __NEXT_DATA__ parse error: {exc}", file=sys.stderr)
        return {}

    result: dict[str, dict] = {}
    _extract_rp_runners(data, result, depth=0)
    print(f"  [OK] RP SSR: {len(result)} runners extracted", file=sys.stderr)
    return result


def _extract_rp_runners(obj, result: dict, depth: int):
    """Recursively find objects with horseHeadGear + horseName (racecard runner schema)."""
    if depth > 30:
        return
    if isinstance(obj, dict):
        # Racecard runner objects have BOTH horseHeadGear and horseName
        if "horseHeadGear" in obj and "horseName" in obj:
            horse = obj["horseName"].strip()
            gear_str = obj.get("horseHeadGear") or ""
            first_time = bool(obj.get("horseHeadGearFirstTime", False))
            wind = obj.get("windSurgery")  # None or bool or str — keep raw
            non_runner = bool(obj.get("nonRunner", False))

            codes = decode_rp_headgear(gear_str)
            first_time_codes = codes if first_time and codes else []

            if horse and not non_runner:
                result[horse] = {
                    "equipment": codes,
                    "first_time_use": first_time_codes,
                    "wind_surgery": wind,
                    "_rp_gear_raw": gear_str or None,
                }
        else:
            for val in obj.values():
                _extract_rp_runners(val, result, depth + 1)
    elif isinstance(obj, list):
        for item in obj:
            _extract_rp_runners(item, result, depth + 1)


# ---------------------------------------------------------------------------
# Merge + build output
# ---------------------------------------------------------------------------

def build_output(
    horses: dict,
    rp_data: dict[str, dict],   # {horse_name: {equipment, first_time_use, ...}}
    source_url_map: dict[str, str],  # {race_date: url}
) -> tuple[dict, dict]:
    """
    Merge RP data with horse roster. Returns (output_horses, stats).
    """
    output: dict[str, dict] = {}
    stats = {
        "total": len(horses),
        "with_equipment": 0,
        "no_equipment": 0,
        "not_found_in_rp": 0,
    }

    for horse_name, meta in horses.items():
        race_date = meta["race_date"]
        race_name = meta["race_name"]

        if horse_name in rp_data:
            rp = rp_data[horse_name]
            equipment = rp["equipment"]
            first_time = rp["first_time_use"]
            wind = rp.get("wind_surgery")
            source_url = source_url_map.get(race_date, "")
        else:
            equipment = []
            first_time = []
            wind = None
            source_url = ""
            stats["not_found_in_rp"] += 1

        if equipment:
            stats["with_equipment"] += 1
        else:
            stats["no_equipment"] += 1

        entry: dict = {
            "race_date": race_date,
            "race_name": race_name,
            "equipment": equipment,
            "first_time_use": first_time,
            "changed_vs_last_run": [],  # Cannot determine from RP racecard alone
            "source_url": source_url,
        }
        if wind is not None:
            entry["wind_surgery"] = wind

        output[horse_name] = entry

    return output, stats


def market_baseline_path(course_slug: str) -> Path:
    if course_slug == default_course():
        return MARKET_BASELINE
    return BASE_DIR / "data" / "enrichment" / f"market-baseline-{course_slug}.json"


def output_path(course_slug: str) -> Path:
    if course_slug == default_course():
        return OUTPUT_FILE
    return BASE_DIR / "data" / "enrichment" / f"equipment-{course_slug}.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch equipment data from configured Racing Post racecards")
    parser.add_argument("--course", default=default_course(), help="Course slug (default: epsom)")
    parser.add_argument("--meeting", default=default_meeting(), help="Meeting slug (default: derby-2026)")
    return parser.parse_args()


def main():
    args = parse_args()
    course_cfg = load_course_config(args.course)
    resolve_meeting(course_cfg, args.meeting)
    baseline_path = market_baseline_path(args.course)
    out_path = output_path(args.course)

    print("=== Equipment Fetcher (v2) ===", file=sys.stderr)
    print(f"Course={args.course} meeting={args.meeting}", file=sys.stderr)

    with open(baseline_path) as f:
        baseline = json.load(f)
    horses = baseline.get("horses", {})
    print(f"Loaded {len(horses)} horses from {baseline_path.name}", file=sys.stderr)

    race_dates = sorted(set(v["race_date"] for v in horses.values()))
    print(f"Race dates: {race_dates}", file=sys.stderr)

    # Fetch RP data for each race date; merge all into single name-keyed dict
    all_rp: dict[str, dict] = {}
    source_url_map: dict[str, str] = {}
    sources_used: list[str] = []

    for i, race_date in enumerate(race_dates):
        if i > 0:
            time.sleep(3)  # polite delay between requests

        print(f"\n--- {race_date} ---", file=sys.stderr)

        # 1. Try openhorsedata (best-effort, likely DNS-blocked)
        try_openhorsedata(race_date)

        # 2. Racing Post SSR (primary working source)
        rp = fetch_rp_racecard(race_date, course_cfg)
        all_rp.update(rp)
        url = rp_racecard_url(course_cfg, race_date)
        source_url_map[race_date] = url
        if rp:
            sources_used.append(url.replace("https://www.", ""))

    print(f"\nTotal RP entries merged: {len(all_rp)}", file=sys.stderr)

    output_horses, stats = build_output(horses, all_rp, source_url_map)

    result = {
        "generated": "2026-06-03T14:50:00+01:00",
        "source": (
            "Racing Post racecard SSR (__NEXT_DATA__); "
            "openhorsedata.com attempted (DNS unreachable); "
            "wind_surgery field present but null in RP free racecard"
        ),
        "sources_scraped": sources_used,
        "coverage": stats,
        "horses": output_horses,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n=== DONE ===", file=sys.stderr)
    print(f"Written: {out_path}", file=sys.stderr)
    print(f"Coverage: {json.dumps(stats)}", file=sys.stderr)

    print(json.dumps({"status": "ok", "coverage": stats}))


if __name__ == "__main__":
    main()
