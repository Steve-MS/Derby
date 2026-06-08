from __future__ import annotations

import pytest

from src.bet_schema import computed_total, schema_entries
from src.report import render_header


def test_legacy_schema_totals_match_portfolio_during_transition() -> None:
    legacy = {
        "singles": [
            {"race_id": "epsom-2026-06-06-1515", "horse": "Win", "bet_type": "WIN", "stake_gbp": 1.0},
            {"race_id": "epsom-2026-06-06-1640", "horse": "Each Way", "bet_type": "EW", "stake_gbp": 2.0},
        ],
        "doubles": [{"legs": [{"horse": "Win"}, {"horse": "Each Way"}], "combined_stake_gbp": 0.5}],
        "outsiders": [{"race_id": "epsom-2026-06-06-1720", "horse": "Out", "outsider_pick": "Out", "stake_gbp": 0.25}],
        "portfolio_summary": {"total_stake_gbp": 4.0},
    }

    entries = schema_entries(legacy)

    assert computed_total(entries) == pytest.approx(4.0)
    assert render_header(legacy)["total_outlay"] == pytest.approx(4.0)
