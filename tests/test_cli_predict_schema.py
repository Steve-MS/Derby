from __future__ import annotations

import json
import sys
import types
from argparse import Namespace
from pathlib import Path

from src import cli


def _scores(path: Path) -> None:
    path.write_text(
        json.dumps({
            "venue": "Epsom",
            "races": [{
                "race_id": "epsom-2026-06-06-1515",
                "race_time": "15:15",
                "race_name": "Dash Handicap",
                "ranked_runners": [],
            }],
        }),
        encoding="utf-8",
    )


def test_cli_predict_writes_linus_schema_without_changing_legacy_keys(tmp_path: Path, monkeypatch) -> None:
    scores = tmp_path / "scores.json"
    bets = tmp_path / "bets.json"
    slip = tmp_path / "slip.txt"
    _scores(scores)

    legacy = {
        "bankroll": 100.0,
        "singles": [{
            "race_id": "epsom-2026-06-06-1515",
            "horse": "Kinswoman",
            "bet_type": "WIN",
            "stake_gbp": 0.51,
            "odds_decimal": 24.0,
            "rationale": "value",
        }],
        "doubles": [],
        "trebles": [],
        "accumulators": [],
        "lucky_15": None,
        "outsiders": [],
        "portfolio_summary": {"total_stake_gbp": 0.51, "active_singles": 1, "passed_singles": 0, "doubles_count": 0, "trebles_count": 0, "outsider_summary": {"count": 0}, "max_potential_return_gbp": 12.24},
    }

    fake_betting = types.SimpleNamespace(
        default_config=lambda: {},
        build_bets=lambda _scores, _bankroll, _config: json.loads(json.dumps(legacy)),
    )
    monkeypatch.setitem(sys.modules, "betting", fake_betting)
    monkeypatch.setattr(cli, "_artifact_path", lambda _args, kind: {"scores": scores, "bets": bets, "slip": slip}[kind])

    rc = cli.cmd_predict(Namespace(course="epsom", meeting="derby-2026", date="2026-06-06", bankroll=100.0))

    assert rc == 0
    data = json.loads(bets.read_text(encoding="utf-8"))
    assert data["singles"] == legacy["singles"]
    assert data["portfolio_summary"] == legacy["portfolio_summary"]
    assert data["meta"]["schema_version"] == "linus-cli-bets-v1"
    assert data["meta"]["course"] == "Epsom"
    assert data["meta"]["date"] == "2026-06-06"
    assert data["meta"]["bankroll"] == 100.0
    assert data["meta"]["total_stake"] == 0.51
    assert data["entries"][0]["pick"] == "Kinswoman"
    assert data["entries"][0]["status"] == "WIN"
