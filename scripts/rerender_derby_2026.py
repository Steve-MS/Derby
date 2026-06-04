"""Re-render Epsom Derby Weekend 2026 HTML reports.

Usage (from repo root):
    python scripts/rerender_derby_2026.py

Outputs:
    outputs/report-2026-06-05.html        — Oaks Day (Friday)
    outputs/report-2026-06-06.html        — Derby Day (Saturday, dual GREEN/HOLD slip)
    outputs/racecard-2026-06-05.html      — Friday printable card
    outputs/racecard-2026-06-06.html      — Saturday GREEN printable card
    outputs/racecard-2026-06-06-hold.html — Saturday HOLD printable card
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running from repo root without installing the package.
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.report import render
from src.racecard import render_card

BASE = Path(__file__).parent.parent
DATA = BASE / "outputs"
GOING = BASE / "data" / "going-forecast.json"
RAW = BASE / "data" / "raw"
MARKET = BASE / "data" / "enrichment" / "market-latest.json"
RENDERED_AT_REPORT = "2026-06-04T17:11"
RENDERED_AT_CARD = "2026-06-04 17:11"


def _load(path: Path) -> dict | list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    # ── Friday 2026-06-05 (Oaks Day) ──────────────────────────────────
    scores_fri  = _load(DATA / "scores-2026-06-05.json")
    bets_fri    = _load(DATA / "bets-2026-06-05.json")

    # scores files wrap the race list under a top-level key in some versions
    if isinstance(scores_fri, dict):
        scores_fri = scores_fri.get("races", scores_fri.get("scores", []))

    render(
        date        = "2026-06-05",
        scores      = scores_fri,
        bets        = bets_fri,
        race_context= {"generated_at": RENDERED_AT_REPORT},
        output_path = str(DATA / "report-2026-06-05.html"),
        market_latest_path = str(MARKET),
    )
    render_card(
        date                = "2026-06-05",
        scores_path         = str(DATA / "scores-2026-06-05.json"),
        bets_path           = str(DATA / "bets-2026-06-05.json"),
        output_path         = str(DATA / "racecard-2026-06-05.html"),
        daily_outlay_gbp    = None,
        race_context        = {"generated_at": RENDERED_AT_CARD},
        going_forecast_path = str(GOING),
        raw_racecard_path   = str(RAW / "epsom-2026-06-05-racecards.json"),
        market_latest_path  = str(MARKET),
    )
    print("✅  Oaks Day report  →  outputs/report-2026-06-05.html")
    print("✅  Oaks Day card    →  outputs/racecard-2026-06-05.html")

    # ── Saturday 2026-06-06 (Derby Day) ───────────────────────────────
    scores_sat  = _load(DATA / "scores-2026-06-06.json")
    bets_sat    = _load(DATA / "bets-2026-06-06.json")          # GREEN slip
    bets_hold   = _load(DATA / "bets-2026-06-06-soft-contingency.json")  # HOLD slip

    if isinstance(scores_sat, dict):
        scores_sat = scores_sat.get("races", scores_sat.get("scores", []))

    render(
        date                 = "2026-06-06",
        scores               = scores_sat,
        bets                 = bets_sat,
        race_context         = {"generated_at": RENDERED_AT_REPORT},
        output_path          = str(DATA / "report-2026-06-06.html"),
        soft_contingency_bets= bets_hold,
        market_latest_path   = str(MARKET),
    )
    render_card(
        date                = "2026-06-06",
        scores_path         = str(DATA / "scores-2026-06-06.json"),
        bets_path           = str(DATA / "bets-2026-06-06.json"),
        output_path         = str(DATA / "racecard-2026-06-06.html"),
        daily_outlay_gbp    = None,
        race_context        = {"generated_at": RENDERED_AT_CARD},
        going_forecast_path = str(GOING),
        raw_racecard_path   = str(RAW / "epsom-2026-06-06-racecards.json"),
        market_latest_path  = str(MARKET),
    )
    render_card(
        date                = "2026-06-06",
        scores_path         = str(DATA / "scores-2026-06-06.json"),
        bets_path           = str(DATA / "bets-2026-06-06-soft-contingency.json"),
        output_path         = str(DATA / "racecard-2026-06-06-hold.html"),
        daily_outlay_gbp    = None,
        race_context        = {"generated_at": RENDERED_AT_CARD},
        going_forecast_path = str(GOING),
        raw_racecard_path   = str(RAW / "epsom-2026-06-06-racecards.json"),
        market_latest_path  = str(MARKET),
    )
    print("✅  Derby Day report →  outputs/report-2026-06-06.html")
    print("✅  Derby Day GREEN card → outputs/racecard-2026-06-06.html")
    print("✅  Derby Day HOLD card  → outputs/racecard-2026-06-06-hold.html")


if __name__ == "__main__":
    main()
