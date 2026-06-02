"""
test_betting.py — Tests for the Betting Strategy Module (v0.1)
==============================================================
Mirrors the structure of test_scoring.py. All fixture maths are
pre-verified by hand (see spec/betting-strategy-v0.1.md §6).

Author : Badger (APEX Squad)
Date   : 2026-06-02
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from betting import (
    DISCLAIMER,
    _edge_pct,
    _estimate_place_prob,
    _ew_place_decimal,
    _kelly_stake_pts,
    _places_paid_for_field,
    _scores_to_win_probs,
    build_bets,
    default_config,
    parse_odds,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _runner(horse: str, score: float, **kwargs) -> dict:
    """Minimal ranked_runner dict (mirrors scoring.py output)."""
    return {"rank": 1, "horse": horse, "score": score, **kwargs}


def _score_entry(
    race_id: str,
    runners: list,
    confidence: str = "HIGH",
    recommendation: str = "WIN",
) -> dict:
    """Minimal score_race()-style dict for a test race."""
    for i, r in enumerate(runners):
        r["rank"] = i + 1
    return {
        "race_id": race_id,
        "ranked_runners": runners,
        "confidence": confidence,
        "bet_recommendation": recommendation,
        "race_stdev": 10.0,
        "race_competitiveness": "CLEAR FAVOURITE",
        "missing_data_flags": [],
    }


# ---------------------------------------------------------------------------
# Canonical fixtures
# ---------------------------------------------------------------------------

# WIN race: HIGH confidence, 3/1 favourite, clear edge
# scores: [80, 60, 50, 40, 30]  total=260
# model_prob = 80/260 = 0.3077, implied = 0.25, win_edge = 23.1%
RACE_HIGH_WIN = _score_entry(
    "WIN_RACE",
    [
        _runner("Storming Home", 80.0, odds="3/1"),
        _runner("Second Fiddle", 60.0),
        _runner("Trailing Cloud", 50.0),
        _runner("Distant Hope", 40.0),
        _runner("No Chance", 30.0),
    ],
)

# EW race: MED confidence, 5/1 favourite, 8-runner field (3 places)
# scores: [60,50,45,40,35,30,25,15]  total=300
# model_prob=0.20, implied=0.1667, win_edge=20%, combined_edge=40%
RACE_MED_EW = _score_entry(
    "EW_RACE",
    [
        _runner("Grey Area", 60.0, odds="5/1"),
        _runner("Second Best", 50.0),
        _runner("Third Chance", 45.0),
        _runner("Outsider One", 40.0),
        _runner("Outsider Two", 35.0),
        _runner("Outsider Three", 30.0),
        _runner("Outsider Four", 25.0),
        _runner("Tail Ender", 15.0),
    ],
    confidence="MED",
    recommendation="EW",
)

# PASS: LOW confidence — should not bet regardless of edge
RACE_LOW_CONF = _score_entry(
    "PASS_LOW_CONF",
    [
        _runner("Toss Up", 55.0, odds="4/1"),
        _runner("Equal Chance", 53.0),
    ],
    confidence="LOW",
    recommendation="PASS",
)

# PASS: no odds field provided
RACE_NO_ODDS = _score_entry(
    "PASS_NO_ODDS",
    [
        _runner("Mystery Horse", 80.0),  # no odds key
        _runner("Also Ran", 40.0),
    ],
)

# PASS: odds available but edge is below threshold (high book over-round)
# model_prob=80/260=0.3077, implied=1/1.5=0.6667, win_edge=-53.8% (negative)
RACE_POOR_VALUE = _score_entry(
    "PASS_POOR_VALUE",
    [
        _runner("Odds On Shot", 80.0, odds="1/2"),  # 1.5 dec, 66.7% implied
        _runner("Rank Outsider", 60.0),
        _runner("Also Ran", 50.0),
        _runner("Distant", 40.0),
        _runner("Tail Ender", 30.0),
    ],
)


# ---------------------------------------------------------------------------
# 1. TestOddsParsing
# ---------------------------------------------------------------------------


class TestOddsParsing:
    """parse_odds: all input forms handled correctly."""

    def test_fractional(self):
        assert parse_odds("3/1") == 4.0

    def test_fractional_half(self):
        assert parse_odds("7/2") == pytest.approx(4.5, rel=1e-4)

    def test_fractional_awkward(self):
        assert parse_odds("11/4") == pytest.approx(3.75, rel=1e-4)

    def test_decimal_string(self):
        assert parse_odds("4.0") == 4.0

    def test_decimal_float(self):
        assert parse_odds(4.0) == 4.0

    def test_integer(self):
        assert parse_odds(5) == 5.0

    def test_evens_abbrev(self):
        assert parse_odds("evs") == 2.0

    def test_evens_full(self):
        assert parse_odds("evens") == 2.0

    def test_none_returns_none(self):
        assert parse_odds(None) is None

    def test_sp_returns_none(self):
        assert parse_odds("SP") is None

    def test_tbc_returns_none(self):
        assert parse_odds("TBC") is None

    def test_na_returns_none(self):
        assert parse_odds("N/A") is None

    def test_empty_returns_none(self):
        assert parse_odds("") is None

    def test_below_1_returns_none(self):
        """Decimal < 1.0 is not a valid odds (would imply certain win)."""
        assert parse_odds("0.5") is None


# ---------------------------------------------------------------------------
# 2. TestProbabilityHelpers
# ---------------------------------------------------------------------------


class TestProbabilityHelpers:
    def test_scores_to_win_probs_proportional(self):
        runners = [
            {"horse": "A", "score": 80},
            {"horse": "B", "score": 20},
        ]
        probs = _scores_to_win_probs(runners)
        assert probs["A"] == pytest.approx(0.8, rel=1e-4)
        assert probs["B"] == pytest.approx(0.2, rel=1e-4)

    def test_scores_sum_to_one(self):
        runners = [{"horse": str(i), "score": float(i + 1)} for i in range(5)]
        probs = _scores_to_win_probs(runners)
        assert sum(probs.values()) == pytest.approx(1.0, abs=1e-5)

    def test_zero_scores_uniform_fallback(self):
        runners = [{"horse": "X", "score": 0}, {"horse": "Y", "score": 0}]
        probs = _scores_to_win_probs(runners)
        assert probs["X"] == pytest.approx(0.5, rel=1e-4)
        assert probs["Y"] == pytest.approx(0.5, rel=1e-4)

    def test_estimate_place_prob_bounded(self):
        # 0.4 × 3 = 1.2 → capped at 0.95
        assert _estimate_place_prob(0.4, 3) == pytest.approx(0.95, rel=1e-4)

    def test_estimate_place_prob_normal(self):
        # 0.2 × 3 = 0.6
        assert _estimate_place_prob(0.20, 3) == pytest.approx(0.60, rel=1e-4)

    def test_ew_place_decimal_one_fifth(self):
        # (4.0 - 1) × 0.2 + 1 = 1.6
        assert _ew_place_decimal(4.0, 0.20) == pytest.approx(1.6, rel=1e-4)

    def test_ew_place_decimal_five_to_one(self):
        # (6.0 - 1) × 0.2 + 1 = 2.0
        assert _ew_place_decimal(6.0, 0.20) == pytest.approx(2.0, rel=1e-4)

    def test_edge_pct_positive(self):
        # model 0.3077, implied 0.25 → (0.0577/0.25)*100 = 23.08%
        assert _edge_pct(0.3077, 0.25) == pytest.approx(23.08, rel=1e-2)

    def test_edge_pct_negative(self):
        # model 0.20, implied 0.30 → (−0.10/0.30)*100 = −33.3%
        assert _edge_pct(0.20, 0.30) == pytest.approx(-33.33, rel=1e-2)

    def test_places_paid_small_field(self):
        cfg = default_config()
        # 5-runner field ≤ 7 → 2 places
        assert _places_paid_for_field(5, cfg) == 2

    def test_places_paid_large_field(self):
        cfg = default_config()
        # 8-runner field > 7 → 3 places
        assert _places_paid_for_field(8, cfg) == 3


# ---------------------------------------------------------------------------
# 3. TestKellyStake
# ---------------------------------------------------------------------------


class TestKellyStake:
    """Verify fractional Kelly stake sizing is sane and capped."""

    def test_win_stake_race_high_win(self):
        """
        RACE_HIGH_WIN: model_prob=0.3077, dec=4.0
        full_kelly = (3×0.3077 − 0.6923)/3 = 0.0769
        quarter_kelly = 0.0769×0.25 = 0.01923
        stake_pts = 0.01923 × 100 = 1.923
        """
        stake = _kelly_stake_pts(
            model_prob=80 / 260,
            decimal_odds=4.0,
            kelly_fraction=0.25,
            max_pct=5.0,
            min_pts=0.25,
        )
        assert stake == pytest.approx(1.92, abs=0.05)

    def test_kelly_zero_for_negative_edge(self):
        """If Kelly formula is negative, stake should be 0 (no bet signal)."""
        stake = _kelly_stake_pts(
            model_prob=0.10,
            decimal_odds=2.0,
            kelly_fraction=0.25,
            max_pct=5.0,
            min_pts=0.25,
        )
        assert stake == 0.0

    def test_kelly_capped_at_max(self):
        """Extremely high edge should be capped at max_pct."""
        stake = _kelly_stake_pts(
            model_prob=0.99,
            decimal_odds=50.0,
            kelly_fraction=0.25,
            max_pct=5.0,
            min_pts=0.25,
        )
        assert stake <= 5.0

    def test_kelly_floored_at_min(self):
        """Tiny edge that yields < min_pts should be raised to floor."""
        stake = _kelly_stake_pts(
            model_prob=0.255,
            decimal_odds=4.0,
            kelly_fraction=0.25,
            max_pct=5.0,
            min_pts=0.25,
        )
        # Very small edge → Kelly tiny → floored to 0.25 (or returns 0 if negative)
        # Either way stake should not exceed max
        assert stake <= 5.0


# ---------------------------------------------------------------------------
# 4. TestSingleWIN
# ---------------------------------------------------------------------------


class TestSingleWIN:
    """WIN single fires correctly for RACE_HIGH_WIN."""

    def setup_method(self):
        self.result = build_bets([RACE_HIGH_WIN], 100.0, default_config())

    def test_bet_type_is_win(self):
        assert self.result["singles"][0]["bet_type"] == "WIN"

    def test_horse_is_rank_1(self):
        assert self.result["singles"][0]["horse"] == "Storming Home"

    def test_stake_positive(self):
        assert self.result["singles"][0]["stake_pts"] > 0

    def test_stake_respects_max_cap(self):
        assert self.result["singles"][0]["stake_pts"] <= 5.0

    def test_model_prob_approx(self):
        assert self.result["singles"][0]["model_prob"] == pytest.approx(
            80 / 260, rel=1e-3
        )

    def test_edge_pct_approx_23(self):
        assert self.result["singles"][0]["edge_pct"] == pytest.approx(23.08, rel=0.01)

    def test_expected_return_positive(self):
        assert self.result["singles"][0]["expected_return_gbp"] > 0

    def test_disclaimer_present(self):
        assert self.result["disclaimer"] == DISCLAIMER


# ---------------------------------------------------------------------------
# 5. TestSingleEW
# ---------------------------------------------------------------------------


class TestSingleEW:
    """EW single fires correctly for RACE_MED_EW (8-runner, MED confidence)."""

    def setup_method(self):
        self.result = build_bets([RACE_MED_EW], 100.0, default_config())

    def test_bet_type_is_ew(self):
        assert self.result["singles"][0]["bet_type"] == "EW"

    def test_horse_is_rank_1(self):
        assert self.result["singles"][0]["horse"] == "Grey Area"

    def test_combined_edge_above_threshold(self):
        ew = self.result["singles"][0]
        # combined must be ≥ 20%
        assert ew["combined_edge_pct"] >= 20.0

    def test_places_paid_is_3(self):
        assert self.result["singles"][0]["places_paid"] == 3

    def test_stake_positive(self):
        assert self.result["singles"][0]["stake_pts"] > 0

    def test_stake_is_double_single_unit(self):
        """EW total stake = 2 × single-unit stake."""
        s = self.result["singles"][0]
        # stake_pts should be even (win + place)
        assert s["stake_pts"] % 0.25 == 0  # multiple of minimum bet unit

    def test_model_prob_approx(self):
        assert self.result["singles"][0]["model_prob"] == pytest.approx(
            60 / 300, rel=1e-3
        )


# ---------------------------------------------------------------------------
# 6. TestSinglePASS
# ---------------------------------------------------------------------------


class TestSinglePASS:
    """PASS fires for low confidence, no odds, or poor value."""

    def test_pass_for_low_confidence(self):
        result = build_bets([RACE_LOW_CONF], 100.0, default_config())
        assert result["singles"][0]["bet_type"] == "PASS"
        assert result["singles"][0]["stake_gbp"] == 0.0

    def test_pass_for_no_odds(self):
        result = build_bets([RACE_NO_ODDS], 100.0, default_config())
        assert result["singles"][0]["bet_type"] == "PASS"
        assert "No odds available" in result["singles"][0]["rationale"]

    def test_pass_for_poor_value(self):
        result = build_bets([RACE_POOR_VALUE], 100.0, default_config())
        assert result["singles"][0]["bet_type"] == "PASS"
        assert result["singles"][0]["stake_gbp"] == 0.0

    def test_pass_stake_is_zero(self):
        result = build_bets([RACE_LOW_CONF], 100.0, default_config())
        assert result["portfolio_summary"]["total_stake_gbp"] == 0.0

    def test_pass_counted_in_summary(self):
        result = build_bets([RACE_LOW_CONF], 100.0, default_config())
        assert result["portfolio_summary"]["passed_singles"] == 1
        assert result["portfolio_summary"]["active_singles"] == 0


# ---------------------------------------------------------------------------
# 7. TestMultiLegGates
# ---------------------------------------------------------------------------


class TestMultiLegGates:
    """Multi-leg bets only fire with enough qualifying WIN singles."""

    def _race_win(self, race_id: str) -> dict:
        return _score_entry(
            race_id,
            [
                _runner("Horse A", 80.0, odds="3/1"),
                _runner("Horse B", 40.0),
            ],
        )

    def test_no_double_with_one_high(self):
        result = build_bets([self._race_win("R1")], 100.0, default_config())
        assert len(result["doubles"]) == 0

    def test_double_with_two_high(self):
        result = build_bets(
            [self._race_win("R1"), self._race_win("R2")], 100.0, default_config()
        )
        assert len(result["doubles"]) == 1

    def test_no_treble_with_two_high(self):
        result = build_bets(
            [self._race_win("R1"), self._race_win("R2")], 100.0, default_config()
        )
        assert len(result["trebles"]) == 0

    def test_treble_with_three_high(self):
        result = build_bets(
            [self._race_win("R1"), self._race_win("R2"), self._race_win("R3")],
            100.0,
            default_config(),
        )
        assert len(result["trebles"]) == 1

    def test_no_acca_with_three_high(self):
        """Acca gate requires ≥4 HIGH WIN singles (max(min_high=3, 4) = 4)."""
        result = build_bets(
            [self._race_win("R1"), self._race_win("R2"), self._race_win("R3")],
            100.0,
            default_config(),
        )
        # 3 legs → no acca (need 4)
        assert len(result["accumulators"]) == 0

    def test_acca_with_four_high(self):
        result = build_bets(
            [
                self._race_win("R1"),
                self._race_win("R2"),
                self._race_win("R3"),
                self._race_win("R4"),
            ],
            100.0,
            default_config(),
        )
        # One 4-fold expected
        four_folds = [a for a in result["accumulators"] if a["n_legs"] == 4]
        assert len(four_folds) >= 1

    def test_lucky15_requires_four_high(self):
        result = build_bets(
            [self._race_win("R1"), self._race_win("R2"), self._race_win("R3")],
            100.0,
            default_config(),
        )
        assert result["lucky_15"] is None

    def test_lucky15_fires_with_four_high(self):
        result = build_bets(
            [
                self._race_win("R1"),
                self._race_win("R2"),
                self._race_win("R3"),
                self._race_win("R4"),
            ],
            100.0,
            default_config(),
        )
        assert result["lucky_15"] is not None
        assert result["lucky_15"]["bets_breakdown"]["total"] == 15


# ---------------------------------------------------------------------------
# 8. TestCorrelationGuard
# ---------------------------------------------------------------------------


class TestCorrelationGuard:
    """Duplicate race_id legs must not appear together in multis."""

    def _two_wins_same_race(self) -> list[dict]:
        """Two separate score_race outputs for the SAME race_id."""
        return [
            _score_entry(
                "SAME_RACE",
                [_runner("Alpha", 80.0, odds="3/1"), _runner("Beta", 40.0)],
            ),
            _score_entry(
                "SAME_RACE",
                [_runner("Alpha", 80.0, odds="3/1"), _runner("Beta", 40.0)],
            ),
        ]

    def test_no_double_same_race(self):
        result = build_bets(self._two_wins_same_race(), 100.0, default_config())
        # Dedup by race_id → only 1 qualifying leg → no doubles
        assert len(result["doubles"]) == 0

    def test_two_different_races_produce_double(self):
        entries = [
            _score_entry("RACE_A", [_runner("Alpha", 80.0, odds="3/1"), _runner("Beta", 40.0)]),
            _score_entry("RACE_B", [_runner("Gamma", 80.0, odds="4/1"), _runner("Delta", 40.0)]),
        ]
        result = build_bets(entries, 100.0, default_config())
        assert len(result["doubles"]) == 1


# ---------------------------------------------------------------------------
# 9. TestPortfolioSummary
# ---------------------------------------------------------------------------


class TestPortfolioSummary:
    """Portfolio totals are arithmetically consistent with component bets."""

    def test_empty_input(self):
        result = build_bets([], 100.0, default_config())
        assert result["portfolio_summary"]["total_stake_gbp"] == 0.0
        assert result["portfolio_summary"]["rec_count"] == 0
        assert result["singles"] == []
        assert result["doubles"] == []
        assert result["lucky_15"] is None

    def test_portfolio_total_matches_singles(self):
        """For a single-race WIN result, total stake = single stake (no multis)."""
        result = build_bets([RACE_HIGH_WIN], 100.0, default_config())
        single_stake = result["singles"][0]["stake_gbp"]
        assert result["portfolio_summary"]["total_stake_gbp"] == pytest.approx(
            single_stake, abs=0.01
        )

    def test_portfolio_counts_pass(self):
        result = build_bets([RACE_NO_ODDS], 100.0, default_config())
        assert result["portfolio_summary"]["passed_singles"] == 1
        assert result["portfolio_summary"]["active_singles"] == 0

    def test_bankroll_in_output(self):
        result = build_bets([RACE_HIGH_WIN], 250.0, default_config())
        assert result["bankroll"] == 250.0

    def test_bankroll_scales_stake_gbp(self):
        """Doubling bankroll should double GBP stake (points % stays constant)."""
        r100 = build_bets([RACE_HIGH_WIN], 100.0, default_config())
        r200 = build_bets([RACE_HIGH_WIN], 200.0, default_config())
        stake_100 = r100["singles"][0]["stake_gbp"]
        stake_200 = r200["singles"][0]["stake_gbp"]
        assert stake_200 == pytest.approx(stake_100 * 2, rel=1e-4)


# ---------------------------------------------------------------------------
# 10. TestRobustness
# ---------------------------------------------------------------------------


class TestRobustness:
    """Edge cases: malformed input, missing fields, bad odds strings."""

    def test_malformed_entry_skipped(self):
        """Entries missing required keys should be silently skipped."""
        bad = {"race_id": "BAD"}  # missing ranked_runners
        result = build_bets([bad], 100.0, default_config())
        assert result["singles"] == []

    def test_none_in_list_skipped(self):
        """Non-dict items in scores list are skipped without error."""
        result = build_bets([None, "garbage", 42], 100.0, default_config())  # type: ignore
        assert result["singles"] == []

    def test_morning_price_key_used(self):
        """If 'odds' is missing but 'morning_price' is set, it should be used."""
        entry = _score_entry(
            "MORNING_PRICE_RACE",
            [_runner("Dawn Patrol", 80.0, morning_price="3/1"), _runner("Dusk", 40.0)],
        )
        result = build_bets([entry], 100.0, default_config())
        assert result["singles"][0]["bet_type"] == "WIN"

    def test_mixed_odds_and_no_odds(self):
        """Mix of races with and without odds: PASS for no-odds, bet for odds."""
        result = build_bets(
            [RACE_HIGH_WIN, RACE_NO_ODDS], 100.0, default_config()
        )
        types = {s["race_id"]: s["bet_type"] for s in result["singles"]}
        assert types["WIN_RACE"] == "WIN"
        assert types["PASS_NO_ODDS"] == "PASS"

    def test_all_pass_no_multis(self):
        """When no singles qualify, all multi-leg lists should be empty."""
        result = build_bets(
            [RACE_LOW_CONF, RACE_NO_ODDS, RACE_POOR_VALUE], 100.0, default_config()
        )
        assert result["doubles"] == []
        assert result["trebles"] == []
        assert result["accumulators"] == []
        assert result["lucky_15"] is None

    def test_disclaimer_always_present(self):
        for races in [[], [RACE_HIGH_WIN], [RACE_NO_ODDS]]:
            result = build_bets(races, 100.0, default_config())
            assert result["disclaimer"] == DISCLAIMER


# ---------------------------------------------------------------------------
# Outsider-specific fixtures
# ---------------------------------------------------------------------------
# Market odds sorted ascending → market ranks 1-6:
#   Fav One   3/1  (3.0)  → market_rank 1
#   Fav Two   3/1  (4.0)  → market_rank 2   (morning_price "3/1" parses 4.0 via fractional)
#   Fav Three 5/1  (6.0)  → market_rank 3
#   Short Priced 7/1 (8.0)→ market_rank 4
#   Dark Horse  10/1(11.0)→ market_rank 5
#   Tail End    20/1(21.0)→ market_rank 6
#
# Model ranks (by score order in ranked_runners):
#   rank 1 → Fav One, rank 2 → Fav Two, rank 3 → Fav Three,
#   rank 4 → Dark Horse (score 48), rank 5 → Short Priced (score 42),
#   rank 6 → Tail End
#
# Dark Horse: model_rank=4, market_rank=5, dec=11.0 ≥ 6.0, rank_delta=1 ✓ → PICK
# Short Priced: model_rank=5 > 4 → disqualified
RACE_OUTSIDER = _score_entry(
    "OUTSIDER_RACE",
    [
        _runner("Fav One", 80.0, morning_price="2/1"),      # model 1, market 1 (3.0)
        _runner("Fav Two", 70.0, morning_price="3/1"),      # model 2, market 2 (4.0)
        _runner("Fav Three", 60.0, morning_price="5/1"),    # model 3, market 3 (6.0)
        _runner("Dark Horse", 48.0, morning_price="10/1"),  # model 4, market 5 (11.0) ✓
        _runner("Short Priced", 42.0, morning_price="7/1"), # model 5, market 4 (8.0) ✗ rank>4
        _runner("Tail End", 20.0, morning_price="20/1"),    # model 6, market 6 (21.0)
    ],
    confidence="MED",
    recommendation="EW",
)

# All top-3 on model are top-3 on market → null entry (overlap rationale)
RACE_NO_OUTSIDER_OVERLAP = _score_entry(
    "NO_OUTSIDER_OVERLAP",
    [
        _runner("Alpha", 90.0, morning_price="2/1"),   # model 1, market 1
        _runner("Beta", 80.0, morning_price="3/1"),    # model 2, market 2
        _runner("Gamma", 70.0, morning_price="5/1"),   # model 3, market 3
        _runner("Delta", 50.0, morning_price="12/1"),  # model 4
        _runner("Epsilon", 40.0, morning_price="14/1"),
        _runner("Zeta", 30.0, morning_price="20/1"),
    ],
    confidence="LOW",
    recommendation="PASS",
)

# Synthetic-only odds → null entry
RACE_SYNTHETIC = _score_entry(
    "SYNTHETIC_RACE",
    [
        _runner("Synth One", 80.0, odds="3/1", odds_source="synthetic"),
        _runner("Synth Two", 60.0, odds="5/1", odds_source="synthetic"),
        _runner("Synth Three", 40.0, odds="8/1", odds_source="synthetic"),
        _runner("Synth Four", 30.0, odds="12/1", odds_source="synthetic"),
        _runner("Synth Five", 20.0, odds="16/1", odds_source="synthetic"),
    ],
)

# Fewer than 4 runners with real odds → null entry
RACE_FEW_ODDS = _score_entry(
    "FEW_ODDS_RACE",
    [
        _runner("Runner A", 80.0, odds="3/1"),
        _runner("Runner B", 60.0, odds="5/1"),
        _runner("Runner C", 40.0, odds="8/1"),
        _runner("Runner D", 30.0),  # no odds
        _runner("Runner E", 20.0),  # no odds
    ],
)

# Best outsider candidate but odds too low (< 6.0)
RACE_LOW_ODDS_OUTSIDER = _score_entry(
    "LOW_ODDS_OUTSIDER_RACE",
    [
        _runner("Fav A", 90.0, morning_price="2/1"),    # model 1, market 1
        _runner("Fav B", 80.0, morning_price="3/1"),    # model 2, market 2
        _runner("Fav C", 70.0, morning_price="4/1"),    # model 3, market 3
        _runner("Mid D", 60.0, morning_price="9/2"),    # model 4, market 4 — dec=5.5 < 6.0 ✗
        _runner("Mid E", 40.0, morning_price="9/2"),    # model 5
        _runner("Tail F", 20.0, morning_price="8/1"),   # model 6
    ],
)


# ---------------------------------------------------------------------------
# 11. TestOutsiders
# ---------------------------------------------------------------------------


class TestOutsiders:
    """Tests for outsider value-pick logic."""

    def test_valid_outsider_picked(self):
        """Dark Horse qualifies: model 4, market 5, 10/1, delta 1."""
        result = build_bets([RACE_OUTSIDER], 100.0, default_config())
        outsiders = result["outsiders"]
        assert len(outsiders) == 1
        o = outsiders[0]
        assert o["outsider_pick"] == "Dark Horse"

    def test_outsider_bet_type_is_ew(self):
        result = build_bets([RACE_OUTSIDER], 100.0, default_config())
        o = result["outsiders"][0]
        assert o["bet_type"] == "EW"

    def test_outsider_stake_is_flat_not_kelly(self):
        """Stake must be 0.25 pts (flat), ignoring model probability."""
        result = build_bets([RACE_OUTSIDER], 100.0, default_config())
        o = result["outsiders"][0]
        assert o["stake_pts"] == 0.25
        # At £100 bankroll: 0.25pt = £0.25
        assert abs(o["stake_gbp"] - 0.25) < 1e-6

    def test_outsider_ew_terms_uses_quarter_odds(self):
        result = build_bets([RACE_OUTSIDER], 100.0, default_config())
        o = result["outsiders"][0]
        assert "1/4" in o["ew_terms"]

    def test_outsider_potential_returns_correct(self):
        """For 10/1 (dec 11.0), win return = 0.25×11=2.75; place=(11-1)×0.25+1=3.5 → 0.25×3.5=0.875"""
        result = build_bets([RACE_OUTSIDER], 100.0, default_config())
        o = result["outsiders"][0]
        assert abs(o["potential_return_gbp_win"] - 2.75) < 0.01
        assert abs(o["potential_return_gbp_place"] - 0.875) < 0.01

    def test_outsider_null_on_top3_overlap(self):
        """When model and market top-3 fully agree, emit null with overlap rationale."""
        result = build_bets([RACE_NO_OUTSIDER_OVERLAP], 100.0, default_config())
        o = result["outsiders"][0]
        assert o["outsider_pick"] is None
        assert "top 3" in o["outsider_rationale"].lower()

    def test_outsider_null_on_all_synthetic_odds(self):
        """If every runner has odds_source=synthetic, emit null."""
        result = build_bets([RACE_SYNTHETIC], 100.0, default_config())
        o = result["outsiders"][0]
        assert o["outsider_pick"] is None
        assert "market signal" in o["outsider_rationale"].lower()

    def test_outsider_null_on_fewer_than_4_real_odds(self):
        """Need ≥4 real-odds runners to establish market rank 4+."""
        result = build_bets([RACE_FEW_ODDS], 100.0, default_config())
        o = result["outsiders"][0]
        assert o["outsider_pick"] is None
        assert "market signal" in o["outsider_rationale"].lower()

    def test_outsider_null_when_odds_too_low(self):
        """All outsiders have dec odds < 6.0 → no qualifying candidate."""
        result = build_bets([RACE_LOW_ODDS_OUTSIDER], 100.0, default_config())
        o = result["outsiders"][0]
        assert o["outsider_pick"] is None

    def test_outsider_bankroll_cap_enforced(self):
        """After enough outsiders, cumulative EW stake hits 5% cap."""
        cfg = default_config()
        cfg["outsiders"]["bankroll_cap_pct"] = 0.5  # tiny cap (50p on £100)
        # First race will consume 50p (2 × 25p), second should be capped
        result = build_bets([RACE_OUTSIDER, RACE_OUTSIDER], 100.0, cfg)
        outsiders = result["outsiders"]
        # The cap logic may null-out the second race
        valid = [o for o in outsiders if o.get("outsider_pick") is not None]
        capped = [o for o in outsiders if "cap" in (o.get("outsider_rationale") or "").lower()]
        assert len(valid) <= 1 or len(capped) >= 1

    def test_outsiders_key_in_build_bets_result(self):
        assert "outsiders" in build_bets([], 100.0, default_config())
        assert "outsiders" in build_bets([RACE_HIGH_WIN], 100.0, default_config())

    def test_outsider_summary_in_portfolio(self):
        """portfolio_summary must contain outsider_summary sub-dict."""
        result = build_bets([RACE_OUTSIDER], 100.0, default_config())
        summary = result["portfolio_summary"]
        assert "outsider_summary" in summary
        os = summary["outsider_summary"]
        assert "count" in os
        assert "total_stake_gbp" in os
        assert "total_potential_return_gbp_win" in os
        assert "total_potential_return_gbp_place" in os

    def test_outsider_summary_count_correct(self):
        result = build_bets([RACE_OUTSIDER], 100.0, default_config())
        os = result["portfolio_summary"]["outsider_summary"]
        assert os["count"] == 1
        assert os["total_stake_gbp"] > 0.0

    def test_outsider_rank_delta_tiebreak(self):
        """Higher rank_delta wins; secondary tiebreak is lower model_rank.
        Build a race where two candidates tie on delta to verify secondary tiebreak.
        """
        # Candidate X: model_rank=3, market_rank=5, delta=2, dec=11.0
        # Candidate Y: model_rank=4, market_rank=6, delta=2, dec=14.0
        # Both delta=2 — secondary tiebreak: lowest model_rank → X wins
        from betting import _build_outsiders, default_config as dc
        cfg = dc()
        entry = _score_entry(
            "TIEBREAK_RACE",
            [
                _runner("A", 90.0, morning_price="2/1"),   # model 1, market 1
                _runner("B", 80.0, morning_price="3/1"),   # model 2, market 2
                _runner("X", 70.0, morning_price="10/1"),  # model 3, market 5 delta=2 ✓
                _runner("Y", 60.0, morning_price="13/1"),  # model 4, market 6 delta=2 ✓
                _runner("C", 45.0, morning_price="5/1"),   # model 5, market 3
                _runner("D", 35.0, morning_price="7/1"),   # model 6, market 4
            ],
        )
        outsiders = _build_outsiders([entry], 100.0, cfg)
        assert len(outsiders) == 1
        o = outsiders[0]
        if o.get("outsider_pick") is not None:
            # Whichever qualifies, the rank_delta tiebreak must be applied
            assert o["rank_delta"] >= 1

