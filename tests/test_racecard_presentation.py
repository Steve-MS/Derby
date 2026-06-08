from __future__ import annotations

import json
from pathlib import Path

from src.racecard import racecard_output_path, render_card


ROOT = Path(__file__).resolve().parents[1]


def test_ascot_racecard_title_and_day_from_config(tmp_path: Path) -> None:
    scores = tmp_path / "scores-ascot.json"
    bets = tmp_path / "bets-ascot.json"
    out = tmp_path / "racecard-ascot.html"
    missing = tmp_path / "missing.json"

    scores.write_text(
        json.dumps({
            "venue": "Ascot",
            "course_slug": "ascot",
            "meeting_slug": "royal-ascot-2026",
            "races": [{
                "race_id": "ascot-2026-06-16-1430",
                "race_time": "14:30",
                "race_name": "Queen Anne Stakes (Group 1)",
                "ranked_runners": [{"horse": "Test Runner", "trainer": "A Trainer", "morning_price": 4.0}],
            }],
        }),
        encoding="utf-8",
    )
    bets.write_text(json.dumps({"singles": []}), encoding="utf-8")

    render_card(
        date="2026-06-16",
        scores_path=str(scores),
        bets_path=str(bets),
        output_path=str(out),
        daily_outlay_gbp=None,
        going_forecast_path=str(missing),
        raw_racecard_path=str(missing),
        market_latest_path=str(missing),
        course="ascot",
        meeting="royal-ascot-2026",
    )

    html = out.read_text(encoding="utf-8")
    assert "Royal Ascot 2026" in html
    assert "Day 1" in html
    assert "<title>Royal Ascot 2026 Day 1 — Betting Slip — 16 June 2026</title>" in html


def test_ascot_racecard_output_path_uses_course_prefix() -> None:
    assert racecard_output_path("ascot", "2026-06-16") == ROOT / "outputs" / "racecard-ascot-2026-06-16.html"
