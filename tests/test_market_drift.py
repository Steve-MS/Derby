"""tests/test_market_drift.py — v0.4 market-drift gate signal.

Covered:
    §1  Derby Day actuals (2026-06-06)
        - Action 12/1 → 13/1 (+7.7%)     → no flag, multiplier 1.0
        - Lord Melbourne 12/1 → 19/1 (+53.8%) → DRIFT_CRITICAL, 0.80, SPECULATIVE forced
        - Benvenuto Cellini 9/4 → Evs (−38.5%) → STEAM_NOTED, 1.0

    §2  Missing-data edge cases
        - Missing baseline          → MARKET_DATA_MISSING, multiplier 1.0
        - Missing latest            → MARKET_DATA_MISSING, multiplier 1.0
        - Both None                 → MARKET_DATA_MISSING
        - Decimal odds ≤ 1.0        → MARKET_DATA_MISSING
        - Horse absent from data dict → MARKET_DATA_MISSING

    §3  Evs/EVS/Evens parsing (all spellings round-trip to 2.0)

    §4  Threshold boundaries (deliberate ≥ vs > semantics)
        - exactly 30% drift  → DRIFT_WARN (≥ 30 fires)
        - exactly 50% drift  → DRIFT_CRITICAL (≥ 50 fires, overrides DRIFT_WARN)
        - 29.99% drift       → no flag (< 30 is noise band)
        - exactly -30% steam → STEAM_NOTED

    §5  Output schema invariants
        - score always 0.0
        - adjusted_final_signal_multiplier always in {0.80, 0.90, 1.0}
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

market_drift = pytest.importorskip("market_drift")

assess_market_drift = market_drift.assess_market_drift
parse_fractional_odds = market_drift.parse_fractional_odds
market_drift_signal = market_drift.market_drift_signal
load_market_drift_data = market_drift.load_market_drift_data


# ===========================================================================
# §1  Derby Day actuals (2026-06-06)
# ===========================================================================

class TestDerbyDayActuals:
    """Real price moves from Derby Day card — the signals that earned this module."""

    def test_action_small_drift_no_flag(self):
        """Action: 12/1 → 13/1 today. drift_pct ≈ +7.7% — noise band, no flag."""
        b = parse_fractional_odds("12/1")   # 13.0
        l = parse_fractional_odds("13/1")   # 14.0
        # drift = (14 − 13) / 13 × 100 = 7.69 %
        result = assess_market_drift(b, l)

        assert result["flags"] == []
        assert result["adjusted_final_signal_multiplier"] == 1.0
        assert result["score"] == 0.0
        assert result["confidence_tier_override"] is None

    def test_lord_melbourne_drift_critical(self):
        """Lord Melbourne: 12/1 → 19/1 today. drift_pct ≈ +53.8% → DRIFT_CRITICAL."""
        b = parse_fractional_odds("12/1")   # 13.0
        l = parse_fractional_odds("19/1")   # 20.0
        # drift = (20 − 13) / 13 × 100 = 53.85 %
        result = assess_market_drift(b, l)

        assert "DRIFT_CRITICAL" in result["flags"]
        assert "DRIFT_WARN" not in result["flags"]
        assert result["adjusted_final_signal_multiplier"] == pytest.approx(0.80)
        assert result["confidence_tier_override"] == "SPECULATIVE"
        assert result["score"] == 0.0

    def test_benvenuto_cellini_steam_noted(self):
        """Benvenuto Cellini: 9/4 → Evs today. drift_pct ≈ −38.5% → STEAM_NOTED."""
        b = parse_fractional_odds("9/4")    # 3.25
        l = parse_fractional_odds("Evs")    # 2.0
        # drift = (2.0 − 3.25) / 3.25 × 100 = −38.46 %
        result = assess_market_drift(b, l)

        assert "STEAM_NOTED" in result["flags"]
        assert "DRIFT_WARN" not in result["flags"]
        assert "DRIFT_CRITICAL" not in result["flags"]
        assert result["adjusted_final_signal_multiplier"] == 1.0
        assert result["confidence_tier_override"] is None
        assert result["score"] == 0.0


# ===========================================================================
# §2  Missing-data edge cases
# ===========================================================================

class TestMissingData:

    def test_missing_baseline_gives_market_data_missing(self):
        result = assess_market_drift(None, 14.0)
        assert "MARKET_DATA_MISSING" in result["flags"]
        assert result["adjusted_final_signal_multiplier"] == 1.0
        assert result["score"] == 0.0

    def test_missing_latest_gives_market_data_missing(self):
        result = assess_market_drift(13.0, None)
        assert "MARKET_DATA_MISSING" in result["flags"]
        assert result["adjusted_final_signal_multiplier"] == 1.0

    def test_both_none_gives_market_data_missing(self):
        result = assess_market_drift(None, None)
        assert "MARKET_DATA_MISSING" in result["flags"]

    def test_baseline_decimal_below_one_is_invalid(self):
        """Decimal odds ≤ 1.0 are nonsensical — treated as missing."""
        result = assess_market_drift(0.5, 14.0)
        assert "MARKET_DATA_MISSING" in result["flags"]

    def test_latest_decimal_equal_to_one_is_invalid(self):
        result = assess_market_drift(13.0, 1.0)
        assert "MARKET_DATA_MISSING" in result["flags"]

    def test_market_drift_signal_horse_absent_from_data(self):
        """Horse not present in market_data dict → MARKET_DATA_MISSING."""
        result = market_drift_signal("Unknown Horse", market_data={})
        assert "MARKET_DATA_MISSING" in result["flags"]
        assert result["adjusted_final_signal_multiplier"] == 1.0

    def test_market_drift_signal_none_data_dict(self):
        """market_data entry is not a dict → MARKET_DATA_MISSING."""
        data = {"Test Horse": "not-a-dict"}
        result = market_drift_signal("Test Horse", market_data=data)
        assert "MARKET_DATA_MISSING" in result["flags"]

    def test_market_drift_signal_entry_missing_latest_decimal(self):
        """latest_decimal is None in the entry → MARKET_DATA_MISSING."""
        data = {"Test Horse": {"baseline_decimal": 13.0, "latest_decimal": None}}
        result = market_drift_signal("Test Horse", market_data=data)
        assert "MARKET_DATA_MISSING" in result["flags"]


# ===========================================================================
# §3  Evs / EVS / Evens parsing
# ===========================================================================

class TestEvsParsing:

    def test_evs_lowercase(self):
        assert parse_fractional_odds("evs") == pytest.approx(2.0)

    def test_evs_mixed_case(self):
        assert parse_fractional_odds("Evs") == pytest.approx(2.0)

    def test_EVS_uppercase(self):
        assert parse_fractional_odds("EVS") == pytest.approx(2.0)

    def test_evens_word(self):
        assert parse_fractional_odds("Evens") == pytest.approx(2.0)

    def test_evens_lowercase(self):
        assert parse_fractional_odds("evens") == pytest.approx(2.0)

    def test_none_input_returns_none(self):
        assert parse_fractional_odds(None) is None

    def test_integer_input_returns_none(self):
        assert parse_fractional_odds(13) is None

    def test_evs_in_gate_is_not_missing_data(self):
        """Evs as latest odds should parse correctly and not raise MARKET_DATA_MISSING."""
        result = assess_market_drift(
            parse_fractional_odds("9/4"),   # 3.25
            parse_fractional_odds("Evs"),   # 2.0
        )
        assert "MARKET_DATA_MISSING" not in result["flags"]

    def test_standard_fractional_parsing(self):
        assert parse_fractional_odds("12/1") == pytest.approx(13.0)
        assert parse_fractional_odds("9/4") == pytest.approx(3.25)
        assert parse_fractional_odds("13/1") == pytest.approx(14.0)
        assert parse_fractional_odds("19/1") == pytest.approx(20.0)
        assert parse_fractional_odds("2/1") == pytest.approx(3.0)


# ===========================================================================
# §4  Threshold boundaries — deliberate ≥ vs > semantics
# ===========================================================================

class TestThresholdBoundaries:

    def test_exactly_30pct_drift_fires_drift_warn_not_critical(self):
        """drift_pct == 30.0: |drift| ≥ 30, drift > 0 → DRIFT_WARN (not DRIFT_CRITICAL)."""
        # baseline=10.0, latest=13.0 → drift = (13−10)/10 × 100 = 30.0%
        result = assess_market_drift(10.0, 13.0)

        assert "DRIFT_WARN" in result["flags"]
        assert "DRIFT_CRITICAL" not in result["flags"]
        assert result["adjusted_final_signal_multiplier"] == pytest.approx(0.90)
        assert result["confidence_tier_override"] is None

    def test_exactly_50pct_drift_fires_drift_critical_not_warn(self):
        """drift_pct == 50.0: |drift| ≥ 50, drift > 0 → DRIFT_CRITICAL (not DRIFT_WARN)."""
        # baseline=10.0, latest=15.0 → drift = (15−10)/10 × 100 = 50.0%
        result = assess_market_drift(10.0, 15.0)

        assert "DRIFT_CRITICAL" in result["flags"]
        assert "DRIFT_WARN" not in result["flags"]
        assert result["adjusted_final_signal_multiplier"] == pytest.approx(0.80)
        assert result["confidence_tier_override"] == "SPECULATIVE"

    def test_just_below_30pct_is_noise_no_flag(self):
        """drift_pct ≈ 29.99%: strictly below threshold → no flag, multiplier 1.0."""
        # baseline=10.0, latest=12.999 → drift ≈ 29.99%
        result = assess_market_drift(10.0, 12.999)

        assert result["flags"] == []
        assert result["adjusted_final_signal_multiplier"] == 1.0

    def test_exactly_30pct_steam_fires_steam_noted(self):
        """drift_pct == −30.0: |drift| ≥ 30, drift < 0 → STEAM_NOTED, multiplier 1.0."""
        # baseline=10.0, latest=7.0 → drift = (7−10)/10 × 100 = −30.0%
        result = assess_market_drift(10.0, 7.0)

        assert "STEAM_NOTED" in result["flags"]
        assert result["adjusted_final_signal_multiplier"] == 1.0
        assert result["confidence_tier_override"] is None


# ===========================================================================
# §5  Output schema invariants
# ===========================================================================

class TestOutputSchema:

    @pytest.mark.parametrize("b,l", [
        (13.0, 14.0),    # noise band → no flag
        (13.0, 20.0),    # DRIFT_CRITICAL
        (3.25, 2.0),     # STEAM_NOTED
        (10.0, 13.0),    # DRIFT_WARN (exactly 30%)
        (None, 14.0),    # missing baseline
        (13.0, None),    # missing latest
    ])
    def test_score_always_zero(self, b, l):
        """score must be 0.0 for every possible gate outcome — not additive."""
        result = assess_market_drift(b, l)
        assert result["score"] == 0.0

    @pytest.mark.parametrize("b,l,expected_mult", [
        (13.0, 14.0, 1.0),   # noise band
        (13.0, 20.0, 0.80),  # DRIFT_CRITICAL
        (3.25, 2.0,  1.0),   # STEAM_NOTED
        (10.0, 13.0, 0.90),  # DRIFT_WARN (30%)
        (None, 14.0, 1.0),   # missing data
    ])
    def test_multiplier_correct_per_gate(self, b, l, expected_mult):
        result = assess_market_drift(b, l)
        assert result["adjusted_final_signal_multiplier"] == pytest.approx(expected_mult)

    @pytest.mark.parametrize("b,l", [
        (13.0, 14.0),
        (13.0, 20.0),
        (3.25, 2.0),
        (10.0, 13.0),
        (None, 14.0),
    ])
    def test_flags_is_list(self, b, l):
        result = assess_market_drift(b, l)
        assert isinstance(result["flags"], list)

    @pytest.mark.parametrize("b,l", [
        (13.0, 14.0),
        (13.0, 20.0),
        (3.25, 2.0),
        (10.0, 13.0),
        (None, 14.0),
    ])
    def test_confidence_tier_override_is_str_or_none(self, b, l):
        result = assess_market_drift(b, l)
        assert result["confidence_tier_override"] is None or isinstance(
            result["confidence_tier_override"], str
        )

    def test_required_keys_present(self):
        result = assess_market_drift(13.0, 14.0)
        assert "score" in result
        assert "flags" in result
        assert "adjusted_final_signal_multiplier" in result
        assert "confidence_tier_override" in result
