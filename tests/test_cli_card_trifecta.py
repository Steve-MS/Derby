from __future__ import annotations

import json
import sys
import types
from argparse import Namespace
from pathlib import Path

from src import cli
from src.racecard import render_card


def _scores(path: Path) -> None:
    path.write_text(
        json.dumps({
            "venue": "Epsom",
            "course_slug": "epsom",
            "meeting_slug": "derby-2026",
            "races": [{
                "race_id": "epsom-2026-06-06-1600",
                "race_time": "16:00",
                "race_name": "Derby",
                "ranked_runners": [{"horse": "Action", "trainer": "Aidan O'Brien", "morning_price": 13.0}],
            }],
        }),
        encoding="utf-8",
    )


def test_cli_card_passes_bets_json_path_when_present(tmp_path: Path, monkeypatch) -> None:
    scores = tmp_path / "scores.json"
    bets = tmp_path / "bets.json"
    out = tmp_path / "card.html"
    raw = tmp_path / "raw.json"
    going = tmp_path / "going.json"
    market = tmp_path / "market.json"
    _scores(scores)
    bets.write_text(json.dumps({"entries": []}), encoding="utf-8")
    raw.write_text(json.dumps({"races": []}), encoding="utf-8")
    going.write_text(json.dumps({"going": "Good to Firm"}), encoding="utf-8")
    calls: dict = {}

    def fake_render_card(**kwargs):
        calls.update(kwargs)
        out.write_text("ok", encoding="utf-8")
        return out

    monkeypatch.setitem(sys.modules, "racecard", types.SimpleNamespace(render_card=fake_render_card))
    monkeypatch.setattr(cli, "_artifact_path", lambda _args, kind: {
        "scores": scores,
        "bets": bets,
        "racecard": out,
        "raw-racecards": raw,
        "enrichment-going": going,
        "market_snapshot": market,
    }[kind])

    rc = cli.cmd_card(Namespace(course="epsom", meeting="derby-2026", date="2026-06-06", outlay=None))

    assert rc == 0
    assert calls["bets_path"] == str(bets)
    assert calls["bets_json_path"] == str(bets)
    assert calls["going"] == "Good to Firm"
    assert calls["market_latest_path"] == str(market)


def test_render_card_with_bets_json_renders_trifecta_box(tmp_path: Path) -> None:
    scores = tmp_path / "scores.json"
    bets = tmp_path / "bets.json"
    out = tmp_path / "card.html"
    missing = tmp_path / "missing.json"
    _scores(scores)
    bets.write_text(
        json.dumps({
            "meta": {"course": "Epsom", "total_stake": 7.0},
            "singles": [],
            "entries": [{
                "race_time": "16:00",
                "race_name": "Derby",
                "pick": "TRIFECTA BOX: [Action, Benvenuto Cellini, Item]",
                "status": "TRIFECTA",
                "bet_type": "trifecta_box",
                "stake_guidance": "£6.00 total",
                "total_stake": "£6.00",
                "horses": [{"horse": "Action"}, {"horse": "Benvenuto Cellini"}, {"horse": "Item"}],
            }],
        }),
        encoding="utf-8",
    )

    render_card(
        date="2026-06-06",
        scores_path=str(scores),
        bets_path=str(bets),
        output_path=str(out),
        daily_outlay_gbp=None,
        raw_racecard_path=str(missing),
        bets_json_path=str(bets),
        course="epsom",
        meeting="derby-2026",
    )

    html = out.read_text(encoding="utf-8")
    assert "+ £6.00 trifecta = £6.00" in html
    assert "Trifecta box: Action / Benvenuto Cellini / Item" in html


def test_render_card_uses_explicit_going_label(tmp_path: Path) -> None:
    scores = tmp_path / "scores.json"
    out = tmp_path / "card.html"
    missing = tmp_path / "missing.json"
    _scores(scores)

    render_card(
        date="2026-06-06",
        scores_path=str(scores),
        bets_path=None,
        output_path=str(out),
        daily_outlay_gbp=None,
        raw_racecard_path=str(missing),
        market_latest_path=str(missing),
        going="Good to Firm",
        course="epsom",
        meeting="derby-2026",
    )

    html = out.read_text(encoding="utf-8")
    assert "Going: Good to Firm" in html
    assert "Going: TBC" not in html


def test_render_card_without_bets_json_skips_trifecta_gracefully(tmp_path: Path) -> None:
    scores = tmp_path / "scores.json"
    out = tmp_path / "card.html"
    missing = tmp_path / "missing.json"
    _scores(scores)

    render_card(
        date="2026-06-06",
        scores_path=str(scores),
        bets_path=None,
        output_path=str(out),
        daily_outlay_gbp=None,
        raw_racecard_path=str(missing),
        bets_json_path=str(missing),
        course="epsom",
        meeting="derby-2026",
    )

    html = out.read_text(encoding="utf-8")
    assert "Trifecta box:" not in html
