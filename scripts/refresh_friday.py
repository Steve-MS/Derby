"""
refresh_friday.py — Friday-morning odds refresh wrapper.

Run this on Friday 5 June 2026 once bookmakers post morning prices to:
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
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
ENRICHMENT_DIR = PROJECT_ROOT / "data" / "enrichment"
DATES = ["2026-06-05", "2026-06-06"]
BANKROLL = 200
PY = sys.executable  # resolves to current interpreter — works around missing `python` on PATH


def run(cmd: list[str]) -> None:
    """Run a subprocess, streaming output, abort on non-zero exit."""
    print(f"\n$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        sys.exit(f"FAILED: {' '.join(cmd)} (exit {result.returncode})")


def load_manual_prices(csv_path: Path) -> dict[str, dict[str, tuple[float, str]]]:
    """Return {date: {horse: (decimal_price, source)}}."""
    out: dict[str, dict[str, tuple[float, str]]] = {d: {} for d in DATES}
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


def apply_manual_overrides(date: str, overrides: dict[str, tuple[float, str]]) -> None:
    """Patch morning_price on the racecard JSON for any horse in overrides."""
    if not overrides:
        return
    path = DATA_RAW / f"epsom-{date}-racecards.json"
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
    parser.add_argument("--skip-enrich", action="store_true",
                        help="Skip enrich_odds.py (use only the CSV overrides)")
    args = parser.parse_args()

    print(f"=== refresh_friday.py @ {datetime.now().isoformat(timespec='seconds')} ===")

    if not args.skip_enrich:
        print("\n[1/4] Running enrich_odds.py (hardcoded ante-post + synthetic fallback)")
        run([PY, str(PROJECT_ROOT / "enrich_odds.py")])
    else:
        print("\n[1/4] Skipping enrich_odds.py (--skip-enrich)")

    if args.prices:
        if not args.prices.exists():
            sys.exit(f"--prices file not found: {args.prices}")
        print(f"\n[2/4] Applying manual price overrides from {args.prices}")
        overrides = load_manual_prices(args.prices)
        for date in DATES:
            apply_manual_overrides(date, overrides.get(date, {}))
    else:
        print("\n[2/4] No --prices CSV supplied; skipping manual overrides")

    print("\n[3/4] Re-scoring both meetings")
    for date in DATES:
        run([PY, "-m", "src.cli", "score", "--date", date])

    print("\n[4/4] Re-predicting + reporting both meetings")
    for date in DATES:
        run([PY, "-m", "src.cli", "predict", "--date", date, "--bankroll", str(BANKROLL)])
        run([PY, "-m", "src.cli", "report", "--date", date])
        run([PY, "-m", "src.cli", "card", "--date", date])

    print("\n=== Done. Open outputs\\report-*.html (full HTML) and racecard-*.html (printable slip) ===")


if __name__ == "__main__":
    main()
