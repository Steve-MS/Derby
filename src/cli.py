#!/usr/bin/env python3
"""
cli.py — Race-analysis plugin CLI entry point.

Usage:
    python -m src.cli <subcommand> [options]

Subcommands:
    fetch    --date YYYY-MM-DD
    score    --date YYYY-MM-DD
    predict  --date YYYY-MM-DD [--bankroll FLOAT]
    backtest --date YYYY-MM-DD --results PATH
    report   --date YYYY-MM-DD [--format html]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

_HERE = Path(__file__).parent   # src/
_ROOT = _HERE.parent            # race-analysis/

# Add src/ to sys.path so we can import scoring (and future betting/report)
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

# Ensure stdout/stderr handle Unicode on Windows consoles (cp1252 → utf-8)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# fetch
# ---------------------------------------------------------------------------

def cmd_fetch(args: argparse.Namespace) -> int:
    """Validate that a racecard JSON exists for the given date.

    Live HTTP fetching is River's domain.  This subcommand lets Steve confirm
    data is present before running score.
    """
    date: str = args.date
    racecard_path = _ROOT / "data" / "raw" / f"epsom-{date}-racecards.json"
    if racecard_path.exists():
        print(f"✓  Racecard found: {racecard_path}")
        return 0

    print(f"✗  Racecard not found: {racecard_path}", file=sys.stderr)
    print(
        "   Live fetch is River's domain — drop JSON into data/raw/ manually "
        "or wait for River's ingest module.",
        file=sys.stderr,
    )
    return 1


# ---------------------------------------------------------------------------
# score
# ---------------------------------------------------------------------------

def _normalize_race(raw_race: dict, meeting: str, date: str, card_going: str) -> dict:
    """Map a raw racecard race dict to the shape expected by score_race()."""
    off_time: str = raw_race.get("off_time", "")
    time_slug: str = off_time.replace(":", "")
    race_id: str = f"{meeting.lower()}-{date}-{time_slug}"
    # Per-race going overrides card-level going when present
    going: str = raw_race.get("going") or card_going

    runners = [
        r for r in raw_race.get("runners", [])
        if not r.get("withdrawn", False)
    ]

    return {
        "race_id":    race_id,
        "race_name":  raw_race.get("name", ""),
        "race_time":  off_time,
        "course":     meeting,
        "distance_f": raw_race.get("distance_f"),
        "going":      going,
        "runners":    runners,
    }


def cmd_score(args: argparse.Namespace) -> int:
    """Load racecard, score all runners via Kaylee's scoring API, write outputs/scores-{date}.json."""
    date: str = args.date

    try:
        from scoring import load_default_config, score_race  # noqa: PLC0415
    except ImportError as exc:
        print(f"Error: cannot import scoring module: {exc}", file=sys.stderr)
        return 1

    racecard_path = _ROOT / "data" / "raw" / f"epsom-{date}-racecards.json"
    if not racecard_path.exists():
        print(f"Error: racecard not found: {racecard_path}", file=sys.stderr)
        print(f"  Run `fetch --date {date}` first or drop JSON into data/raw/.", file=sys.stderr)
        return 1

    with racecard_path.open(encoding="utf-8") as fh:
        racecard: dict = json.load(fh)

    config: dict = load_default_config()
    meeting: str = racecard.get("meeting", "Epsom")
    card_going: str = racecard.get("going") or "Good"

    scored_races: list[dict] = []
    for raw_race in racecard.get("races", []):
        race_dict = _normalize_race(raw_race, meeting, date, card_going)
        if not race_dict["runners"]:
            print(f"  ⚠  {race_dict['race_time']} {race_dict['race_name'][:40]} — no runners, skipped")
            continue
        result: dict = score_race(race_dict, config)
        # Attach display fields not returned by score_race()
        result["race_name"] = race_dict["race_name"]
        result["race_time"] = race_dict["race_time"]
        scored_races.append(result)

    output: dict[str, Any] = {
        "card_date":  date,
        "venue":      meeting,
        "frozen_by":  "wash-cli",
        "frozen_at":  datetime.now(timezone.utc).isoformat(),
        "races":      scored_races,
    }

    outputs_dir = _ROOT / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    out_path = outputs_dir / f"scores-{date}.json"
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2)

    print(f"✓  Scored {len(scored_races)} races → {out_path}\n")
    for r in scored_races:
        top = r["ranked_runners"][0] if r["ranked_runners"] else None
        horse = (top["horse"][:20] if top else "n/a").ljust(20)
        score_str = f"{top['score']:5.1f}" if top else "  n/a"
        print(
            f"   {r['race_time']}  {r.get('race_name', '')[:36].ljust(36)}"
            f"  top: {horse}  score={score_str}  "
            f"{r['confidence']:3}  {r['bet_recommendation']}"
        )
    return 0


# ---------------------------------------------------------------------------
# predict
# ---------------------------------------------------------------------------

def cmd_predict(args: argparse.Namespace) -> int:
    """Call Badger's betting.build_bets() and write outputs/bets-{date}.json.

    Gracefully stubs if betting.py has not shipped yet.
    """
    date: str = args.date
    bankroll: float = args.bankroll

    try:
        from betting import build_bets, default_config as betting_default_config  # noqa: PLC0415
    except ImportError:
        print("ℹ  Module 'betting' is not yet available — Badger is still building it.")
        print("   Once src/betting.py ships, re-run: predict --date", date)
        return 0

    scores_path = _ROOT / "outputs" / f"scores-{date}.json"
    if not scores_path.exists():
        print(f"Error: scores not found: {scores_path}", file=sys.stderr)
        print(f"  Run `score --date {date}` first.", file=sys.stderr)
        return 1

    with scores_path.open(encoding="utf-8") as fh:
        scores_data: dict = json.load(fh)

    scores_list: list[dict] = scores_data.get("races", [])
    config: dict = betting_default_config()

    bets: dict = build_bets(scores_list, bankroll, config)

    outputs_dir = _ROOT / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    out_path = outputs_dir / f"bets-{date}.json"
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(bets, fh, indent=2)

    print(f"✓  Bets written → {out_path}")
    return 0


# ---------------------------------------------------------------------------
# backtest
# ---------------------------------------------------------------------------

def _to_backtest_predictions(scores_data: dict) -> dict:
    """Translate scores JSON to the format expected by tests/backtest.py.

    backtest.py expects:
        predictions.races[].rankings[].horse_name  (not .horse)
        predictions.races[].rankings[].rank
        predictions.races[].rankings[].score
        predictions.races[].rankings[].implied_prob  (optional)
    """
    races_out: list[dict] = []
    for race in scores_data.get("races", []):
        rankings: list[dict] = [
            {
                "rank":       r["rank"],
                "horse_name": r["horse"],
                "score":      r["score"],
                # implied_prob deliberately omitted — not computed yet.
                # backtest.py treats absent implied_prob as n/a for Brier.
            }
            for r in race.get("ranked_runners", [])
        ]
        races_out.append({
            "race_id":   race.get("race_id", ""),
            "race_name": race.get("race_name", ""),
            "race_time": race.get("race_time", ""),
            "rankings":  rankings,
        })

    return {
        "card_date": scores_data.get("card_date", ""),
        "venue":     scores_data.get("venue", ""),
        "frozen_by": scores_data.get("frozen_by", "wash-cli"),
        "frozen_at": scores_data.get("frozen_at", ""),
        "races":     races_out,
    }


def cmd_backtest(args: argparse.Namespace) -> int:
    """Invoke Jayne's tests/backtest.py and propagate its exit code.

    Exit codes mirror backtest.py:
        0 = GREEN  (trust Saturday)
        1 = AMBER  (trust high-confidence picks only)
        2 = RED    (model broken)
    """
    date: str = args.date
    results_path: str = args.results

    scores_path = _ROOT / "outputs" / f"scores-{date}.json"
    if not scores_path.exists():
        print(f"Error: scores not found: {scores_path}", file=sys.stderr)
        print(f"  Run `score --date {date}` first.", file=sys.stderr)
        return 1

    with scores_path.open(encoding="utf-8") as fh:
        scores_data: dict = json.load(fh)

    # Write backtest-compatible predictions alongside scores
    predictions_data = _to_backtest_predictions(scores_data)
    predictions_path = _ROOT / "outputs" / f"predictions-{date}.json"
    with predictions_path.open("w", encoding="utf-8") as fh:
        json.dump(predictions_data, fh, indent=2)

    backtest_script = _ROOT / "tests" / "backtest.py"
    if not backtest_script.exists():
        print(f"Error: backtest script not found: {backtest_script}", file=sys.stderr)
        return 1

    proc = subprocess.run(
        [
            sys.executable,
            str(backtest_script),
            "--predictions", str(predictions_path),
            "--results",     results_path,
        ],
        check=False,
    )
    return proc.returncode


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

def cmd_report(args: argparse.Namespace) -> int:
    """Call Mr. Universe's report.render() and write outputs/report-{date}.html.

    Gracefully stubs if report.py has not shipped yet.
    """
    date: str = args.date
    fmt: str = args.format

    try:
        from report import render  # noqa: PLC0415
    except ImportError:
        print("ℹ  Module 'report' is not yet available — Mr. Universe is still building it.")
        print("   Once src/report.py ships, re-run: report --date", date)
        return 0

    scores_path = _ROOT / "outputs" / f"scores-{date}.json"
    if not scores_path.exists():
        print(f"Error: scores not found: {scores_path}", file=sys.stderr)
        print(f"  Run `score --date {date}` first.", file=sys.stderr)
        return 1

    with scores_path.open(encoding="utf-8") as fh:
        scores_data: dict = json.load(fh)

    # Load bets if available (optional)
    bets: dict = {}
    bets_path = _ROOT / "outputs" / f"bets-{date}.json"
    if bets_path.exists():
        with bets_path.open(encoding="utf-8") as fh:
            bets = json.load(fh)

    outputs_dir = _ROOT / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    output_path = str(outputs_dir / f"report-{date}.{fmt}")

    race_context: dict = {
        "venue":     scores_data.get("venue", ""),
        "card_date": date,
    }

    render(
        date=date,
        scores=scores_data.get("races", []),
        bets=bets,
        race_context=race_context,
        output_path=output_path,
    )

    print(f"✓  Report written → {output_path}")
    return 0


# ---------------------------------------------------------------------------
# card
# ---------------------------------------------------------------------------

def cmd_card(args: argparse.Namespace) -> int:
    """Render the printable race card (A4, one race per page)."""
    date: str = args.date

    try:
        from racecard import render_card  # noqa: PLC0415
    except ImportError as exc:
        print(f"Error: cannot import racecard module: {exc}", file=sys.stderr)
        return 1

    scores_path = _ROOT / "outputs" / f"scores-{date}.json"
    if not scores_path.exists():
        print(f"Error: scores not found: {scores_path}", file=sys.stderr)
        print(f"  Run `score --date {date}` first.", file=sys.stderr)
        return 1

    bets_path = _ROOT / "outputs" / f"bets-{date}.json"
    output_path = _ROOT / "outputs" / f"racecard-{date}.html"

    render_card(
        date=date,
        scores_path=str(scores_path),
        bets_path=str(bets_path) if bets_path.exists() else None,
        output_path=str(output_path),
        daily_outlay_gbp=args.outlay,
    )

    print(f"✓  Race card written → {output_path}")
    print(f"   Open in browser and Ctrl+P → Save as PDF for print.")
    return 0


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="race-analysis",
        description="Race prediction toolkit — Epsom Classics 2026.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m src.cli fetch    --date 2026-06-05\n"
            "  python -m src.cli score    --date 2026-06-05\n"
            "  python -m src.cli predict  --date 2026-06-05 --bankroll 200\n"
            "  python -m src.cli backtest --date 2026-06-05 --results data/results/results-2026-06-05.json\n"
            "  python -m src.cli report   --date 2026-06-05 --format html\n"
            "  python -m src.cli card     --date 2026-06-06\n"
        ),
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    p = sub.add_parser("fetch", help="Validate that a racecard JSON exists for a date")
    p.add_argument("--date", required=True, metavar="YYYY-MM-DD")
    p.set_defaults(func=cmd_fetch)

    p = sub.add_parser("score", help="Score all runners for a date → outputs/scores-{date}.json")
    p.add_argument("--date", required=True, metavar="YYYY-MM-DD")
    p.set_defaults(func=cmd_score)

    p = sub.add_parser(
        "predict",
        help="Generate betting predictions via Badger's betting.py → outputs/bets-{date}.json",
    )
    p.add_argument("--date", required=True, metavar="YYYY-MM-DD")
    p.add_argument(
        "--bankroll", type=float, default=100.0, metavar="FLOAT",
        help="Total bankroll in GBP (default: 100.0)",
    )
    p.set_defaults(func=cmd_predict)

    p = sub.add_parser(
        "backtest",
        help="Run Jayne's backtest harness against actual results; propagates exit code",
    )
    p.add_argument("--date", required=True, metavar="YYYY-MM-DD")
    p.add_argument("--results", required=True, metavar="PATH",
                   help="Path to actual results JSON")
    p.set_defaults(func=cmd_backtest)

    p = sub.add_parser(
        "report",
        help="Generate HTML report via Mr. Universe's report.py → outputs/report-{date}.html",
    )
    p.add_argument("--date", required=True, metavar="YYYY-MM-DD")
    p.add_argument("--format", default="html", choices=["html"],
                   help="Output format (default: html)")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser(
        "card",
        help="Generate printable race card → outputs/racecard-{date}.html (A4, one race per page)",
    )
    p.add_argument("--date", required=True, metavar="YYYY-MM-DD")
    p.add_argument(
        "--outlay",
        type=float,
        default=100.0,
        help="Total daily outlay cap in GBP (stakes scaled proportionally). Default: 100",
    )
    p.set_defaults(func=cmd_card)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
