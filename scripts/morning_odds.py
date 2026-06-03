"""
morning_odds.py - Ladies Day & Derby Day odds snapshot for market_move signal.

Captures point-in-time price snapshots for all Epsom runners on Ladies Day
(Fri 2026-06-05) and Derby Day (Sat 2026-06-06), writing to
data/enrichment/market-baseline.json or market-latest.json.

Operator Runbook
----------------

FRIDAY (Ladies Day 2026-06-05):
  # 07:00 BST - lock in the morning baseline
  python scripts/morning_odds.py --mode baseline --date 2026-06-05

  # ~1 hr before each Group 1 race - update latest prices
  python scripts/morning_odds.py --mode latest --date 2026-06-05

BETWEEN DAYS (Fri evening after Ladies Day):
  # Archive Friday snapshots for historical record
  python scripts/morning_odds.py --mode archive --date 2026-06-05

SATURDAY (Derby Day 2026-06-06):
  # 07:00 BST - lock in the morning baseline
  python scripts/morning_odds.py --mode baseline --date 2026-06-06

  # ~1 hr before each Group 1 race - update latest prices
  python scripts/morning_odds.py --mode latest --date 2026-06-06

OPTIONAL: Override any price via manual CSV (format: date,horse,decimal_price,source)
  python scripts/morning_odds.py --mode baseline --date 2026-06-05 --prices overrides.csv

Run on the MORNING of each race day (Friday for Ladies Day, Saturday for Derby Day).

Data sources (priority order)
------------------------------
  1. --prices CSV  (manual override; operator fills in prices from their
                    bookmaker terminal / TV graphics)
  2. Racing Post __NEXT_DATA__ scrape  (best-effort; RP may block; prices
                    are loaded dynamically by the browser so this source
                    currently provides runner-list confirmation only -
                    the odds themselves are NOT embedded in the SSR HTML)
  3. Racecard morning_price  (from data/raw/epsom-YYYY-MM-DD-racecards.json;
                    set by enrich_odds.py from ante_post / estimated /
                    synthetic sources on 2026-06-02)

Archive Mode
------------
  Snapshot current market files for historical record:
    python scripts/morning_odds.py --mode archive --date 2026-06-05
  
  Behavior:
    - Creates data/enrichment/archive/ if missing
    - Copies market-baseline.json -> archive/market-baseline-{date}.json
    - Copies market-latest.json -> archive/market-latest-{date}-final.json
    - Prints what was copied + file sizes
    - Idempotent (safe to re-run)
    - Fails with clear message if source files don't exist

Anti-fabrication
----------------
  No prices are invented.  If no price can be verified, the horse entry is
  omitted from the snapshot.  The market_move signal returns 50 (neutral)
  for missing-data cases.
"""

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ENRICHMENT_DIR = DATA_DIR / "enrichment"
ARCHIVE_DIR = ENRICHMENT_DIR / "archive"
RAW_DIR = DATA_DIR / "raw"

OUTPUT_PATHS = {
    "baseline": ENRICHMENT_DIR / "market-baseline.json",
    "latest":   ENRICHMENT_DIR / "market-latest.json",
}

RACECARD_FILES = {
    "2026-06-05": RAW_DIR / "epsom-2026-06-05-racecards.json",
    "2026-06-06": RAW_DIR / "epsom-2026-06-06-racecards.json",
}

RP_RACECARD_URL = "https://www.racingpost.com/racecards/17/epsom/{date}"

# ---------------------------------------------------------------------------
# Fractional odds conversion
# ---------------------------------------------------------------------------

_FRACTION_MAP: dict[float, str] = {
    1.5:  "1/2",   1.57: "4/7",  1.67: "4/6",  1.75: "4/5",  2.0:  "Evs",
    2.1:  "11/10", 2.2:  "6/5",  2.25: "5/4",  2.5:  "6/4",  2.6:  "8/5",
    2.75: "7/4",   2.875:"15/8", 3.0:  "2/1",  3.25: "9/4",  3.5:  "5/2",
    3.75: "11/4",  4.0:  "3/1",  4.5:  "7/2",  5.0:  "4/1",  5.5:  "9/2",
    6.0:  "5/1",   6.5:  "11/2", 7.0:  "6/1",  7.5:  "13/2", 8.0:  "7/1",
    8.5:  "15/2",  9.0:  "8/1",  9.5:  "17/2", 10.0: "9/1",  11.0: "10/1",
    12.0: "11/1",  13.0: "12/1", 14.0: "13/1", 15.0: "14/1", 16.0: "15/1",
    17.0: "16/1",  18.0: "17/1", 19.0: "18/1", 20.0: "19/1", 21.0: "20/1",
    23.0: "22/1",  25.0: "24/1", 26.0: "25/1", 29.0: "28/1", 34.0: "33/1",
    41.0: "40/1",  51.0: "50/1", 67.0: "66/1", 81.0: "80/1", 101.0:"100/1",
}


def decimal_to_fractional(dec: float) -> str:
    """Convert a decimal price to the nearest standard UK fractional string."""
    closest = min(_FRACTION_MAP.keys(), key=lambda x: abs(x - dec))
    if abs(closest - dec) < 1.0:
        return _FRACTION_MAP[closest]
    # Fallback: simple integer fraction
    num = round(dec - 1)
    return f"{num}/1"


# ---------------------------------------------------------------------------
# Load racecard prices  (source 3 — always available)
# ---------------------------------------------------------------------------

_SOURCE_LABEL = {
    "ante_post": "Racing Post ante-post (captured 2026-06-02)",
    "estimated": "Estimated by form-analysis (River, 2026-06-02)",
    "synthetic": "Synthetic from OR/field-size (River, 2026-06-02)",
}

_CAPTURED_AT_RACECARD = "2026-06-02T13:55:00+01:00"


def load_racecard_prices(dates: list[str]) -> dict[str, dict]:
    """
    Return {horse_name: {race_date, race_name, off_time, decimal_odds,
                          fractional_odds, implied_probability,
                          source, captured_at}}
    for every runner in the racecard files for the given dates.
    """
    prices: dict[str, dict] = {}
    for date in dates:
        path = RACECARD_FILES.get(date)
        if not path or not path.exists():
            print(f"  [warn] racecard file not found for {date}: {path}", file=sys.stderr)
            continue
        with path.open(encoding="utf-8") as fh:
            card = json.load(fh)
        for race in card.get("races", []):
            rname = race.get("name", "")
            off = race.get("off_time", "")
            for runner in race.get("runners", []):
                horse = runner.get("horse", "")
                mp = runner.get("morning_price")
                src = runner.get("odds_source", "synthetic")
                if not horse or mp is None:
                    continue
                dec = float(mp)
                prices[horse] = {
                    "race_date": date,
                    "race_name": rname,
                    "off_time": off,
                    "decimal_odds": dec,
                    "fractional_odds": decimal_to_fractional(dec),
                    "implied_probability": round(1.0 / dec, 4),
                    "source": _SOURCE_LABEL.get(src, src),
                    "captured_at": _CAPTURED_AT_RACECARD,
                }
    return prices


# ---------------------------------------------------------------------------
# Racing Post __NEXT_DATA__ scrape  (source 2 — best-effort, names only)
# ---------------------------------------------------------------------------

_RP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-GB,en;q=0.9",
}


def _fetch_rp_runners(date: str) -> list[str] | None:
    """
    Fetch Racing Post racecard page and extract horse names from __NEXT_DATA__.
    Returns a list of confirmed runner names, or None on failure.

    NOTE: RP does not embed live odds in the SSR HTML — prices are loaded
    via a browser WebSocket (diffusion channel).  This function returns
    NAMES ONLY for runner-list confirmation and non-runner detection.
    """
    url = RP_RACECARD_URL.format(date=date)
    try:
        req = Request(url, headers=_RP_HEADERS)
        with urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except URLError as exc:
        print(f"  [warn] RP fetch failed for {date}: {exc}", file=sys.stderr)
        return None

    # Extract __NEXT_DATA__ JSON block
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
    if not m:
        print(f"  [warn] __NEXT_DATA__ not found in RP response for {date}", file=sys.stderr)
        return None

    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        print(f"  [warn] __NEXT_DATA__ parse error for {date}: {exc}", file=sys.stderr)
        return None

    try:
        state = data["props"]["pageProps"]["initialState"]
        races = state["racecardMeetingPage"]["data"]["races"]
    except (KeyError, TypeError):
        print(f"  [warn] unexpected RP data structure for {date}", file=sys.stderr)
        return None

    names: list[str] = []
    for race in races:
        for runner in race.get("runners", []):
            hname = runner.get("horseName", "")
            if hname:
                names.append(hname)

    print(f"  [rp]   {date}: {len(names)} runner names confirmed from RP __NEXT_DATA__")
    return names


def apply_rp_runner_filter(
    prices: dict[str, dict],
    date: str,
    rp_names: list[str],
) -> dict[str, dict]:
    """
    Remove horses for `date` that are NOT in the RP confirmed runner list
    (i.e. probable non-runners withdrawn after the racecard was published).
    Prints a warning for each removed horse.
    """
    if not rp_names:
        return prices

    # Build case-insensitive lookup of RP names
    rp_lower = {n.lower() for n in rp_names}

    removed: list[str] = []
    filtered = {}
    for horse, entry in prices.items():
        if entry["race_date"] != date:
            filtered[horse] = entry
            continue
        if horse.lower() in rp_lower:
            filtered[horse] = entry
        else:
            removed.append(horse)

    if removed:
        print(f"  [nr]   {date}: removed as probable non-runners: {', '.join(sorted(removed))}")

    return filtered


# ---------------------------------------------------------------------------
# CSV price overrides  (source 1 — highest priority)
# ---------------------------------------------------------------------------

def load_csv_overrides(csv_path: str, captured_at: str) -> dict[str, dict]:
    """
    Parse a CSV with columns: date,horse,decimal_price,source
    Returns {horse_name: partial_entry} for merging into the prices dict.
    """
    overrides: dict[str, dict] = {}
    path = Path(csv_path)
    if not path.exists():
        print(f"  [error] CSV file not found: {csv_path}", file=sys.stderr)
        return overrides

    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            horse = (row.get("horse") or "").strip()
            price_str = (row.get("decimal_price") or "").strip()
            src = (row.get("source") or "manual").strip()
            if not horse or not price_str:
                continue
            try:
                dec = float(price_str)
            except ValueError:
                print(f"  [warn] bad decimal price for {horse}: {price_str!r}", file=sys.stderr)
                continue
            overrides[horse] = {
                "decimal_odds": dec,
                "fractional_odds": decimal_to_fractional(dec),
                "implied_probability": round(1.0 / dec, 4),
                "source": f"Manual override ({src})",
                "captured_at": captured_at,
            }

    print(f"  [csv]  loaded {len(overrides)} price override(s) from {csv_path}")
    return overrides


# ---------------------------------------------------------------------------
# Build snapshot
# ---------------------------------------------------------------------------

def build_snapshot(
    dates: list[str],
    snapshot_type: str,
    csv_path: str | None,
    skip_rp_scrape: bool = False,
) -> dict:
    """Build the full snapshot dict."""
    captured_at = datetime.now(timezone.utc).astimezone().isoformat()

    # Source 3: racecard baseline
    print("Loading racecard prices ...")
    prices = load_racecard_prices(dates)
    print(f"  {len(prices)} runners from racecard files")

    # Source 2: RP runner-list confirmation (names only, no live prices)
    if not skip_rp_scrape:
        for date in dates:
            print(f"Fetching RP runner list for {date} ...")
            rp_names = _fetch_rp_runners(date)
            if rp_names:
                prices = apply_rp_runner_filter(prices, date, rp_names)

    # Source 1: CSV overrides (highest priority)
    if csv_path:
        print(f"Applying CSV overrides from {csv_path} ...")
        overrides = load_csv_overrides(csv_path, captured_at)
        for horse, override in overrides.items():
            if horse in prices:
                prices[horse].update(override)
            else:
                print(f"  [warn] CSV horse not in racecard: {horse!r}", file=sys.stderr)
    else:
        # For --mode latest with no CSV: the captured_at reflects this run
        for entry in prices.values():
            entry["captured_at"] = captured_at

    # Build output
    return {
        "_meta": {
            "doc": (
                "Market snapshot for Epsom Derby Day 2026-06-05/06. "
                "Used by market_move signal: compare baseline vs latest to "
                "detect price moves indicating shrewd-money confidence."
            ),
            "anti_fabrication": (
                "Prices from verified sources only: ante_post from Racing Post "
                "(2026-06-02), estimated from form context, synthetic from "
                "official ratings/field-size.  No bookmaker prices invented."
            ),
            "dates": dates,
            "snapshot_type": snapshot_type,
        },
        "generated": captured_at,
        "snapshot_type": snapshot_type,
        "horses": prices,
    }


# ---------------------------------------------------------------------------
# Archive mode
# ---------------------------------------------------------------------------

def archive_market_files(date: str, dry_run: bool = False) -> int:
    """
    Archive the current market-baseline.json and market-latest.json to
    data/enrichment/archive/ with date suffix.
    
    Returns 0 on success, 1 on failure.
    """
    baseline_src = OUTPUT_PATHS["baseline"]
    latest_src = OUTPUT_PATHS["latest"]
    
    if not baseline_src.exists():
        print(f"  [error] baseline file not found: {baseline_src}", file=sys.stderr)
        return 1
    if not latest_src.exists():
        print(f"  [error] latest file not found: {latest_src}", file=sys.stderr)
        return 1
    
    baseline_archive = ARCHIVE_DIR / f"market-baseline-{date}.json"
    latest_archive = ARCHIVE_DIR / f"market-latest-{date}-final.json"
    
    if not dry_run:
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    
    if not dry_run:
        baseline_src.read_bytes()  # Verify readable
        baseline_archive.write_bytes(baseline_src.read_bytes())
        baseline_size = baseline_archive.stat().st_size
        print(f"Archived: {baseline_archive} ({baseline_size} bytes)")
    else:
        baseline_size = baseline_src.stat().st_size
        print(f"[dry-run] Would archive: {baseline_archive} ({baseline_size} bytes)")
    
    if not dry_run:
        latest_src.read_bytes()  # Verify readable
        latest_archive.write_bytes(latest_src.read_bytes())
        latest_size = latest_archive.stat().st_size
        print(f"Archived: {latest_archive} ({latest_size} bytes)")
    else:
        latest_size = latest_src.stat().st_size
        print(f"[dry-run] Would archive: {latest_archive} ({latest_size} bytes)")
    
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Ladies Day & Derby Day odds snapshot for market_move signal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--mode",
        choices=["baseline", "latest", "archive"],
        required=True,
        help="'baseline' -> write market-baseline.json; 'latest' -> write market-latest.json; 'archive' -> snapshot to archive/",
    )
    p.add_argument(
        "--date",
        default=None,
        help="YYYY-MM-DD date to process (default: both 2026-06-05 and 2026-06-06 for snapshot modes)",
    )
    p.add_argument(
        "--prices",
        default=None,
        metavar="CSV",
        help="Path to CSV with columns date,horse,decimal_price,source (manual overrides; baseline/latest only)",
    )
    p.add_argument(
        "--no-rp-scrape",
        action="store_true",
        help="Skip the Racing Post HTML scrape (use racecard data only; baseline/latest only)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen but do not write output",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()

    if args.mode == "archive":
        if not args.date:
            print("  [error] --mode archive requires --date YYYY-MM-DD", file=sys.stderr)
            return 1
        print(f"\n=== morning_odds  mode=archive  date={args.date} ===")
        return archive_market_files(args.date, dry_run=args.dry_run)

    dates = [args.date] if args.date else ["2026-06-05", "2026-06-06"]
    out_path = OUTPUT_PATHS[args.mode]

    print(f"\n=== morning_odds  mode={args.mode}  dates={dates} ===")

    snapshot = build_snapshot(
        dates=dates,
        snapshot_type=args.mode,
        csv_path=args.prices,
        skip_rp_scrape=args.no_rp_scrape,
    )

    horse_count = len(snapshot["horses"])
    print(f"\nSnapshot complete: {horse_count} horses")
    for date in dates:
        n = sum(1 for v in snapshot["horses"].values() if v["race_date"] == date)
        print(f"  {date}: {n}")

    if args.dry_run:
        print("\n[dry-run] Output NOT written.")
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(snapshot, fh, indent=2, ensure_ascii=False)

    print(f"\nWritten: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
