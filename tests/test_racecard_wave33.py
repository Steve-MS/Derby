import json
from pathlib import Path

from src.racecard import render_card


ROOT = Path(__file__).resolve().parents[1]


def test_racecard_wave33_params_render_going_scenario_and_item():
    """Printable card accepts Wave 3.3 context and renders compact slip rows."""
    out = ROOT / "outputs" / ".test-racecard-wave33.html"
    try:
        render_card(
            date="2026-06-06",
            scores_path=str(ROOT / "outputs" / "scores-2026-06-06.json"),
            bets_path=str(ROOT / "outputs" / "bets-2026-06-06.json"),
            output_path=str(out),
            daily_outlay_gbp=None,
            going_forecast_path=str(ROOT / "data" / "going-forecast.json"),
            raw_racecard_path=str(ROOT / "data" / "raw" / "epsom-2026-06-06-racecards.json"),
        )
        html = out.read_text(encoding="utf-8")
        assert "Going: Soft (5.2mm rain forecast, 60-80% prob)" in html
        assert "🟢 GREEN SLIP — assumes Going holds at Good-to-Soft or better" in html
        assert "⚠️ SPECULATIVE — NOT A MODEL PICK" in html
        assert "edge <span class=\"edge-negative\">-69.4%</span>" in html
        assert "Cancel if going declared Soft Saturday AM → use HOLD card." in html
        assert "Total outlay:</span> <strong>£7.40</strong>" in html
    finally:
        out.unlink(missing_ok=True)


def test_racecard_renders_bet_rationale_from_bet_object():
    """Printable card carries Badger's bet rationale into the template."""
    scores = ROOT / "outputs" / ".test-rationale-scores.json"
    bets = ROOT / "outputs" / ".test-rationale-bets.json"
    out = ROOT / "outputs" / ".test-rationale-card.html"
    missing = ROOT / "outputs" / ".test-rationale-missing.json"
    try:
        scores.write_text(
            json.dumps({
                "venue": "Epsom",
                "races": [{
                    "race_id": "r1",
                    "race_time": "14:00",
                    "race_name": "Test Stakes (Group 3)",
                    "ranked_runners": [{"horse": "Rationale Runner", "trainer": "A Trainer", "morning_price": 4.0}],
                }],
            }),
            encoding="utf-8",
        )
        bets.write_text(
            json.dumps({
                "singles": [{
                    "race_id": "r1",
                    "horse": "Rationale Runner",
                    "bet_type": "WIN",
                    "odds_decimal": 4.0,
                    "stake_gbp": 2.0,
                    "expected_return_gbp": 8.0,
                    "rationale": "Crisp model edge on proven Epsom form.",
                }]
            }),
            encoding="utf-8",
        )

        render_card(
            date="2026-06-05",
            scores_path=str(scores),
            bets_path=str(bets),
            output_path=str(out),
            daily_outlay_gbp=None,
            going_forecast_path=str(missing),
            raw_racecard_path=str(missing),
            market_latest_path=str(missing),
        )
        html = out.read_text(encoding="utf-8")
        assert "class=\"row-rationale row-rationale-win\"" in html
        assert "▸ Crisp model edge on proven Epsom form." in html
    finally:
        scores.unlink(missing_ok=True)
        bets.unlink(missing_ok=True)
        out.unlink(missing_ok=True)
