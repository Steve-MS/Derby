"""
tests/test_render_header.py — unit tests for render_header() and _parse_stake_amount().

Covers the v0.4 refactor (JSON-driven header computation) that eliminates the
recurring "HTML header left at £5.50 per guardrails" staleness pattern identified
in Saul's 2026-06-06 Derby Day process audit.

Run:  pytest tests/test_render_header.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.report import _parse_stake_amount, render_header


# ---------------------------------------------------------------------------
# _parse_stake_amount helpers
# ---------------------------------------------------------------------------


def test_parse_stake_amount_gbp_win():
    assert _parse_stake_amount("£1.00 WIN") == 1.0


def test_parse_stake_amount_gbp_ew():
    assert _parse_stake_amount("£0.25 EW (min stake)") == 0.25


def test_parse_stake_amount_dollar_total():
    assert _parse_stake_amount("$6.00 total ($1.00 x 6 combos)") == 6.0


def test_parse_stake_amount_plain():
    assert _parse_stake_amount("£6.00") == 6.0


def test_parse_stake_amount_none():
    assert _parse_stake_amount(None) == 0.0


def test_parse_stake_amount_empty():
    assert _parse_stake_amount("") == 0.0


# ---------------------------------------------------------------------------
# Fixture: yesterday's actual Derby Day portfolio
# Eight WIN/EW picks + £6 trifecta → £12.50 total
# ---------------------------------------------------------------------------

BETS_DERBY_DAY = {
    "bets": [
        # 13:30 — no bet
        {
            "race_time": "13:30", "race_name": "Tattenham Corner Stakes",
            "pick": None, "status": "NO_BET", "stake_guidance": None,
        },
        # 14:05 — WIN £1.00
        {
            "race_time": "14:05", "race_name": "Princess Elizabeth Stakes G3",
            "pick": "Princess Child", "status": "WIN", "stake_guidance": "£1.00 WIN",
        },
        # 14:40 — no bet
        {
            "race_time": "14:40", "race_name": "Coronation Cup G1",
            "pick": None, "status": "NO_BET", "stake_guidance": None,
        },
        # 15:15 — WIN £0.25
        {
            "race_time": "15:15", "race_name": "Betfred Dash Heritage Handicap",
            "pick": "Another Baar", "status": "WIN",
            "stake_guidance": "£0.25 WIN (minimum stake — speculative)",
        },
        # 15:15 — EW £0.25 (unit) → £0.50 outlay
        {
            "race_time": "15:15", "race_name": "Betfred Dash Heritage Handicap",
            "pick": "Ziggy's Triton", "status": "EW", "stake_guidance": "£0.25 EW (min stake)",
        },
        # 16:00 — WIN £1.00
        {
            "race_time": "16:00", "race_name": "Betfred Derby G1",
            "pick": "Action", "status": "WIN", "stake_guidance": "£1.00 WIN",
        },
        # 16:40 — WIN £1.50
        {
            "race_time": "16:40", "race_name": "Lester Piggott Handicap",
            "pick": "Folk Pageant", "status": "WIN", "stake_guidance": "£1.50 WIN",
        },
        # 17:20 — WIN £0.75
        {
            "race_time": "17:20", "race_name": "Northern Dancer Handicap",
            "pick": "Lord Melbourne", "status": "WIN", "stake_guidance": "£0.75 WIN",
        },
        # 17:20 — EW £0.25 (unit) → £0.50 outlay
        {
            "race_time": "17:20", "race_name": "Northern Dancer Handicap",
            "pick": "Prydwen", "status": "EW", "stake_guidance": "£0.25 EW (min stake)",
        },
        # 17:55 — WIN £1.00
        {
            "race_time": "17:55", "race_name": "JRA Tokyo Trophy Handicap",
            "pick": "Apollo One", "status": "WIN", "stake_guidance": "£1.00 WIN",
        },
        # Derby trifecta box — £6.00 total
        {
            "race_time": "16:00", "race_name": "Epsom Derby",
            "pick": "TRIFECTA BOX: [Action, Benvenuto Cellini, Item]",
            "status": "TRIFECTA",
            "stake_guidance": "$6.00 total ($1.00 x 6 combos)",
            "total_stake": "£6.00",
            "horses": [
                {"horse": "Action", "role": "BANKER"},
                {"horse": "Benvenuto Cellini", "role": "Leg 2"},
                {"horse": "Item", "role": "Leg 3"},
            ],
        },
    ]
}


# ---------------------------------------------------------------------------
# Test 1: £12.50 total from 8 picks + £6 trifecta box
# ---------------------------------------------------------------------------

def test_total_outlay_12_50():
    """Yesterday's actual numbers: 8 WIN/EW picks (£6.50) + £6 trifecta = £12.50."""
    result = render_header(BETS_DERBY_DAY)
    assert result["winew_outlay"] == pytest.approx(6.50)
    assert result["trifecta_outlay"] == pytest.approx(6.00)
    assert result["total_outlay"] == pytest.approx(12.50)


def test_active_bet_count_8():
    """8 active WIN/EW bets; NO_BET entries excluded; trifecta counted separately."""
    result = render_header(BETS_DERBY_DAY)
    assert result["active_bet_count"] == 8


def test_trifecta_horses_captured():
    result = render_header(BETS_DERBY_DAY)
    assert result["trifecta_horses"] == ["Action", "Benvenuto Cellini", "Item"]


# ---------------------------------------------------------------------------
# Test 2: VOID + NR excluded from total but listed in NR line
# ---------------------------------------------------------------------------

BETS_WITH_NR = {
    "bets": [
        # VOID — Dance In The Storm NR at 17:55, bet was overridden
        {
            "race_time": "17:55", "pick": "Dance In The Storm",
            "status": "VOID", "stake_guidance": "£1.00 WIN",
            "rationale_short": "NR confirmed — replaced by Apollo One",
        },
        # NR — Horse A withdrawn
        {
            "race_time": "14:00", "pick": "Horse A",
            "status": "NR", "stake_guidance": "£0.50 EW",
            "rationale_short": "Withdrawn at declaration",
        },
        # NR — Horse B withdrawn
        {
            "race_time": "15:00", "pick": "Horse B",
            "status": "NR", "stake_guidance": "£1.00 WIN",
        },
        # Normal WIN — should count toward total
        {
            "race_time": "16:00", "pick": "Horse C",
            "status": "WIN", "stake_guidance": "£1.25 WIN",
        },
    ]
}


def test_nr_excluded_from_total():
    """VOID and NR entries must not contribute to stake totals."""
    result = render_header(BETS_WITH_NR)
    assert result["winew_outlay"] == pytest.approx(1.25)
    assert result["total_outlay"] == pytest.approx(1.25)


def test_nr_listed_in_nr_line():
    """VOID + 2 NR entries should all appear in nr_horses list."""
    result = render_header(BETS_WITH_NR)
    horses = [e["horse"] for e in result["nr_horses"]]
    assert "Dance In The Storm" in horses
    assert "Horse A" in horses
    assert "Horse B" in horses
    assert len(result["nr_horses"]) == 3


def test_nr_statuses_preserved():
    result = render_header(BETS_WITH_NR)
    by_horse = {e["horse"]: e["status"] for e in result["nr_horses"]}
    assert by_horse["Dance In The Storm"] == "VOID"
    assert by_horse["Horse A"] == "NR"
    assert by_horse["Horse B"] == "NR"


# ---------------------------------------------------------------------------
# Test 3: Missing `meta` field → graceful defaults (no crash)
# ---------------------------------------------------------------------------

BETS_NO_META = {
    # No "meta" key at all — old schema
    "generated": "2026-06-05T10:00:00+01:00",
    "bets": [
        {"race_time": "14:00", "pick": "Cameo", "status": "WIN", "stake_guidance": "£2.00 WIN"},
    ],
}


def test_no_meta_no_crash():
    """Old schema without meta block must not raise."""
    result = render_header(BETS_NO_META)
    assert result["total_outlay"] == pytest.approx(2.00)


def test_no_meta_course_defaults_to_epsom():
    result = render_header(BETS_NO_META)
    assert result["course"] == "Epsom"


def test_no_meta_validation_tag_is_none():
    result = render_header(BETS_NO_META)
    assert result["validation_tag"] is None


def test_no_meta_nr_horses_empty():
    result = render_header(BETS_NO_META)
    assert result["nr_horses"] == []


# ---------------------------------------------------------------------------
# Test 4: Validation tag passes through from meta when present
# ---------------------------------------------------------------------------

BETS_WITH_VALIDATION = {
    "meta": {
        "card_date": "2026-06-06",
        "course": "Epsom",
        "validation": "✅ Saul AMBER GO · Danny GO 12:13 BST · 17:55 override post-validation",
        "generated_at": "2026-06-06T11:52:00+01:00",
    },
    "bets": [
        {"race_time": "16:00", "pick": "Action", "status": "WIN", "stake_guidance": "£1.00 WIN"},
    ],
}


def test_validation_tag_present():
    result = render_header(BETS_WITH_VALIDATION)
    assert result["validation_tag"] == (
        "✅ Saul AMBER GO · Danny GO 12:13 BST · 17:55 override post-validation"
    )


def test_validation_tag_course_from_meta():
    result = render_header(BETS_WITH_VALIDATION)
    assert result["course"] == "Epsom"


# ---------------------------------------------------------------------------
# Test 5: Trifecta box stake shown separately; entries schema works
# ---------------------------------------------------------------------------

BETS_TRIFECTA_BOX_TYPE = {
    "entries": [  # new "entries" key instead of "bets"
        {
            "race_time": "16:00",
            "pick": "TRIFECTA: [Alpha, Beta, Gamma]",
            "bet_type": "trifecta_box",
            "status": "ACTIVE",
            "total_stake": "£12.00",
            "horses": [
                {"horse": "Alpha"},
                {"horse": "Beta"},
                {"horse": "Gamma"},
            ],
        },
        {
            "race_time": "14:00",
            "pick": "Delta",
            "status": "WIN",
            "stake_guidance": "£2.00 WIN",
        },
    ],
}


def test_trifecta_box_bet_type_detected():
    """bet_type == 'trifecta_box' should be detected and stake separated."""
    result = render_header(BETS_TRIFECTA_BOX_TYPE)
    assert result["trifecta_outlay"] == pytest.approx(12.00)
    assert result["winew_outlay"] == pytest.approx(2.00)
    assert result["total_outlay"] == pytest.approx(14.00)


def test_trifecta_box_horses_listed():
    result = render_header(BETS_TRIFECTA_BOX_TYPE)
    assert result["trifecta_horses"] == ["Alpha", "Beta", "Gamma"]


def test_trifecta_not_counted_in_active_bets():
    """Trifecta must not inflate the active_bet_count (shown separately)."""
    result = render_header(BETS_TRIFECTA_BOX_TYPE)
    assert result["active_bet_count"] == 1  # only Delta


def test_entries_key_schema():
    """'entries' key (new schema) works the same as 'bets' key (old schema)."""
    result = render_header(BETS_TRIFECTA_BOX_TYPE)
    assert result["total_outlay"] == pytest.approx(14.00)
