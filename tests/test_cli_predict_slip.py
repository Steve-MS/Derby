from __future__ import annotations

import json
import sys
import types
from argparse import Namespace
from pathlib import Path

from src import cli


def test_cli_predict_emits_plain_text_slip(tmp_path: Path, monkeypatch) -> None:
    scores = tmp_path / "scores.json"
    bets = tmp_path / "bets.json"
    slip = tmp_path / "slip.txt"
    scores.write_text(
        json.dumps({
            "venue": "Epsom",
            "races": [{"race_id": "epsom-2026-06-06-1515", "race_time": "15:15", "race_name": "Dash", "ranked_runners": []}],
        }),
        encoding="utf-8",
    )
    fake_betting = types.SimpleNamespace(
        default_config=lambda: {},
        build_bets=lambda _scores, _bankroll, _config: {
            "bankroll": 100.0,
            "singles": [{"race_id": "epsom-2026-06-06-1515", "horse": "Kinswoman", "bet_type": "WIN", "stake_gbp": 0.51, "odds_decimal": 24.0}],
            "doubles": [],
            "trebles": [],
            "accumulators": [],
            "lucky_15": None,
            "outsiders": [],
            "portfolio_summary": {"total_stake_gbp": 0.51, "active_singles": 1, "passed_singles": 0, "doubles_count": 0, "trebles_count": 0, "outsider_summary": {"count": 0}, "max_potential_return_gbp": 12.24},
        },
    )
    monkeypatch.setitem(sys.modules, "betting", fake_betting)
    monkeypatch.setattr(cli, "_artifact_path", lambda _args, kind: {"scores": scores, "bets": bets, "slip": slip}[kind])

    rc = cli.cmd_predict(Namespace(course="epsom", meeting="derby-2026", date="2026-06-06", bankroll=100.0))

    assert rc == 0
    text = slip.read_text(encoding="utf-8")
    assert "APEX RACING" in text
    assert "SINGLES" in text
    assert "Kinswoman" in text
    assert "SUMMARY" in text
    assert "Total stake:" in text
