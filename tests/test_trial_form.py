"""Tests for src/trial_form.py — trial form signal.

Module does not exist yet; this file defines the target contract for Rusty.
Tests are skipped automatically until src/trial_form.py is present.
"""
import os
import sys
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

trial_form = pytest.importorskip("trial_form")
load_trial_form = trial_form.load_trial_form
score_trial_form = trial_form.score_trial_form


# ---------------------------------------------------------------------------
# Shared fixture data
# The assumed JSON schema:
#   { "Horse Name": { "trials": [ { "race": str, "tier": int (1|2|3),
#                                    "date": "YYYY-MM-DD", "position": int,
#                                    "beaten_lengths": float | None,
#                                    "field_size": int } ] } }
# ---------------------------------------------------------------------------

TIER1_WIN = {
    "race": "Dante Stakes",
    "tier": 1,
    "date": "2026-05-14",
    "position": 1,
    "beaten_lengths": 0.0,
    "field_size": 8,
}

TIER1_SECOND_NARROW = {
    "race": "Dante Stakes",
    "tier": 1,
    "date": "2026-05-14",
    "position": 2,
    "beaten_lengths": 0.75,
    "field_size": 8,
}

TIER2_WIN = {
    "race": "Chester Vase",
    "tier": 2,
    "date": "2026-05-06",
    "position": 1,
    "beaten_lengths": 0.0,
    "field_size": 7,
}

TIER1_UNPLACED = {
    "race": "Dante Stakes",
    "tier": 1,
    "date": "2026-05-14",
    "position": 4,
    "beaten_lengths": 6.0,
    "field_size": 8,
}

RECENT_WIN = {
    "race": "Chester Vase",
    "tier": 2,
    "date": "2026-05-20",   # ~14 days before race
    "position": 1,
    "beaten_lengths": 0.0,
    "field_size": 6,
}

OLD_WIN = {
    "race": "Chester Vase",
    "tier": 2,
    "date": "2026-03-15",   # ~80 days before race
    "position": 1,
    "beaten_lengths": 0.0,
    "field_size": 6,
}

DERBY_DIST = 12.0
OAKS_DIST = 12.0
MID_DIST = 10.0
BELOW_GATE_DIST = 9.5
SPRINT_DIST = 5.0


# ===========================================================================
# Happy path
# ===========================================================================

def test_winner_tier1_scores_high():
    """Winner of a Tier 1 trial (Dante) should score >= 80."""
    data = {"Galileo's Glory": {"trials": [TIER1_WIN]}}
    score = score_trial_form("Galileo's Glory", DERBY_DIST, data)
    assert score >= 80.0


def test_second_tier1_narrow_beaten_scores_good():
    """2nd in Tier 1 beaten < 1 length should still score >= 65."""
    data = {"Riviera Rose": {"trials": [TIER1_SECOND_NARROW]}}
    score = score_trial_form("Riviera Rose", DERBY_DIST, data)
    assert score >= 65.0


def test_winner_tier2_trial_in_range():
    """Winner of a Tier 2 trial (Chester Vase) should score 60-80."""
    data = {"Chester Champ": {"trials": [TIER2_WIN]}}
    score = score_trial_form("Chester Champ", DERBY_DIST, data)
    assert 60.0 <= score <= 80.0


def test_unplaced_major_trial_scores_moderate():
    """4th+ in a Tier 1 trial should score in the 40-55 range."""
    data = {"Also Ran": {"trials": [TIER1_UNPLACED]}}
    score = score_trial_form("Also Ran", DERBY_DIST, data)
    assert 40.0 <= score <= 55.0


def test_recent_trial_scores_higher_than_old():
    """Same finishing position in a recent trial (<=21 days) should outscore
    an old trial (60+ days) for the same horse."""
    recent_data = {"Time Sensitive": {"trials": [RECENT_WIN]}}
    old_data = {"Time Sensitive": {"trials": [OLD_WIN]}}
    recent_score = score_trial_form("Time Sensitive", DERBY_DIST, recent_data)
    old_score = score_trial_form("Time Sensitive", DERBY_DIST, old_data)
    assert recent_score > old_score


# ===========================================================================
# Anti-fabrication / neutral fallbacks
# ===========================================================================

def test_horse_not_in_data_returns_50():
    """Unknown horse → neutral 50."""
    data = {"Known Horse": {"trials": [TIER1_WIN]}}
    assert score_trial_form("Completely Unknown Horse", DERBY_DIST, data) == 50.0


def test_horse_with_empty_trials_returns_50():
    """Horse in file but with empty trials list → neutral 50."""
    data = {"Empty Entry": {"trials": []}}
    assert score_trial_form("Empty Entry", DERBY_DIST, data) == 50.0


def test_malformed_trial_entry_returns_50():
    """Malformed trial dict (missing keys) → returns 50, does not crash."""
    data = {"Bad Data Horse": {"trials": [{"race": "Dante Stakes"}]}}  # missing position/tier/date
    result = score_trial_form("Bad Data Horse", DERBY_DIST, data)
    assert result == 50.0


def test_missing_file_returns_50(tmp_path):
    """load_trial_form with a nonexistent path returns empty/neutral, and
    score_trial_form on that result returns 50."""
    nonexistent = str(tmp_path / "does_not_exist.json")
    data = load_trial_form(nonexistent)
    assert score_trial_form("Any Horse", DERBY_DIST, data) == 50.0


# ===========================================================================
# Distance gating
# ===========================================================================

def test_sprint_returns_50():
    """5f sprint → signal should not fire → 50."""
    data = {"Sprint Flyer": {"trials": [TIER1_WIN]}}
    assert score_trial_form("Sprint Flyer", SPRINT_DIST, data) == 50.0


def test_below_distance_threshold_returns_50():
    """9.5f is below the 10f gate → neutral 50."""
    data = {"Close But No": {"trials": [TIER1_WIN]}}
    assert score_trial_form("Close But No", BELOW_GATE_DIST, data) == 50.0


def test_derby_trip_12f_signal_active():
    """Derby trip (12f) → signal is active for a horse with trial data."""
    data = {"Derby Hope": {"trials": [TIER1_WIN]}}
    score = score_trial_form("Derby Hope", DERBY_DIST, data)
    assert score != 50.0


def test_oaks_trip_12f_signal_active():
    """Oaks trip (12f fillies race) → signal fires the same way as Derby."""
    data = {"Oaks Fancy": {"trials": [TIER2_WIN]}}
    score = score_trial_form("Oaks Fancy", OAKS_DIST, data)
    assert score != 50.0


# ===========================================================================
# Edge cases
# ===========================================================================

def test_multiple_trials_uses_best_result():
    """When a horse has multiple trial entries, the BEST result should
    determine the score.
    # TODO: Confirm with Danny whether 'best' means highest position (win > 2nd)
    #       or most-recent trial. Tests assume best-result rule for now.
    """
    mediocre = {
        "race": "Lingfield Derby Trial",
        "tier": 3,
        "date": "2026-05-09",
        "position": 3,
        "beaten_lengths": 4.0,
        "field_size": 6,
    }
    data = {"Two Trials": {"trials": [mediocre, TIER1_WIN]}}
    # With best-result rule, should score as a Tier 1 winner (>= 80)
    score = score_trial_form("Two Trials", DERBY_DIST, data)
    assert score >= 80.0


def test_horse_name_case_insensitive():
    """Lookup should be case-insensitive; 'constitution river' matches
    'Constitution River' in the data."""
    data = {"Constitution River": {"trials": [TIER1_WIN]}}
    lower_score = score_trial_form("constitution river", DERBY_DIST, data)
    upper_score = score_trial_form("Constitution River", DERBY_DIST, data)
    assert lower_score == upper_score
    assert lower_score != 50.0


def test_beaten_lengths_none_no_crash():
    """beaten_lengths of None should not crash; treated as a moderate signal."""
    trial = {
        "race": "Dante Stakes",
        "tier": 1,
        "date": "2026-05-14",
        "position": 2,
        "beaten_lengths": None,
        "field_size": 8,
    }
    data = {"Unknown Margin": {"trials": [trial]}}
    result = score_trial_form("Unknown Margin", DERBY_DIST, data)
    assert isinstance(result, float)
    assert 0.0 <= result <= 100.0


def test_single_runner_field_no_overcredit():
    """Win in a 1-horse field should not produce an elite score (>= 80).
    Walking over gets no real credit."""
    trial = {
        "race": "Walkover Trial",
        "tier": 1,
        "date": "2026-05-14",
        "position": 1,
        "beaten_lengths": 0.0,
        "field_size": 1,
    }
    data = {"Walkover Winner": {"trials": [trial]}}
    score = score_trial_form("Walkover Winner", DERBY_DIST, data)
    assert score < 80.0


# ===========================================================================
# Bounds
# ===========================================================================

def test_output_always_in_0_100_range():
    """All valid inputs must produce a score in [0, 100]."""
    cases = [
        ("Winner", [TIER1_WIN]),
        ("Second", [TIER1_SECOND_NARROW]),
        ("Tier2 Win", [TIER2_WIN]),
        ("Unplaced", [TIER1_UNPLACED]),
        ("Empty", []),
        ("Unknown Horse Entirely", None),
    ]
    for name, trials in cases:
        if trials is None:
            data = {}
        else:
            data = {name: {"trials": trials}}
        s = score_trial_form(name, DERBY_DIST, data)
        assert 0.0 <= s <= 100.0, f"Out-of-range score {s} for case '{name}'"


def test_output_is_float():
    """Return value must be a float (not int, not None)."""
    data = {"Float Check": {"trials": [TIER1_WIN]}}
    result = score_trial_form("Float Check", DERBY_DIST, data)
    assert isinstance(result, float)
