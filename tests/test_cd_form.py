"""Tests for src/cd_form.py — RP badge extraction + C&D form signal."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cd_form import badge_summary, cd_form_signal, extract_badges


# --- extract_badges ---------------------------------------------------------

def test_extract_badges_cd_only():
    runner = {"notes": "badges CD; source RP"}
    assert extract_badges(runner) == {"CD"}


def test_extract_badges_multiple_tokens():
    runner = {"notes": "badges C, D, BF; source RP"}
    assert extract_badges(runner) == {"C", "D", "BF"}


def test_extract_badges_with_cd_and_others():
    runner = {"notes": "badges CD, BF; rest of notes"}
    assert extract_badges(runner) == {"CD", "BF"}


def test_extract_badges_case_insensitive():
    runner = {"notes": "BADGES cd, bf; source"}
    assert extract_badges(runner) == {"CD", "BF"}


def test_extract_badges_no_notes_field():
    assert extract_badges({}) == set()


def test_extract_badges_none_notes():
    assert extract_badges({"notes": None}) == set()


def test_extract_badges_no_badges_segment():
    runner = {"notes": "trainer comment about going preference"}
    assert extract_badges(runner) == set()


def test_extract_badges_ignores_unknown_tokens():
    runner = {"notes": "badges CD, XX, ZZ; source RP"}
    assert extract_badges(runner) == {"CD"}


def test_extract_badges_trailing_no_separator():
    runner = {"notes": "badges D"}
    assert extract_badges(runner) == {"D"}


def test_extract_badges_with_source_separator():
    runner = {"notes": "badges CD source RP"}
    assert extract_badges(runner) == {"CD"}


# --- cd_form_signal: badge mapping ------------------------------------------

DERBY_RACE = {"course": "Epsom", "distance_f": 12.0, "going": "good"}
SPRINT_RACE = {"course": "Epsom", "distance_f": 5.0, "going": "good"}


def test_signal_cd_badge_dominant():
    runner = {"notes": "badges CD, D, C, BF; source RP"}
    assert cd_form_signal(runner, DERBY_RACE) == 80.0


def test_signal_d_when_no_cd():
    runner = {"notes": "badges D, BF; source RP"}
    assert cd_form_signal(runner, DERBY_RACE) == 70.0


def test_signal_c_when_no_cd_or_d():
    runner = {"notes": "badges C; source RP"}
    assert cd_form_signal(runner, DERBY_RACE) == 62.0


def test_signal_bf_alone():
    runner = {"notes": "badges BF; source RP"}
    assert cd_form_signal(runner, DERBY_RACE) == 55.0


def test_signal_neutral_when_no_badges():
    runner = {"notes": "no badges here"}
    assert cd_form_signal(runner, DERBY_RACE) == 50.0


def test_signal_neutral_when_no_notes():
    assert cd_form_signal({}, DERBY_RACE) == 50.0


def test_signal_neutral_for_sprint_no_badge_no_penalty():
    runner = {"notes": "badges; nothing", "first_time_epsom": True}
    assert cd_form_signal(runner, SPRINT_RACE) == 50.0


# --- First-time Epsom long-trip penalty -------------------------------------

def test_first_time_epsom_penalty_applies_at_derby_trip():
    runner = {"first_time_epsom": True, "notes": "no badges"}
    assert cd_form_signal(runner, DERBY_RACE) == 40.0


def test_first_time_epsom_penalty_does_not_apply_under_12f():
    runner = {"first_time_epsom": True, "notes": "no badges"}
    race = {"course": "Epsom", "distance_f": 10.0}
    assert cd_form_signal(runner, race) == 50.0


def test_first_time_epsom_penalty_does_not_apply_at_other_courses():
    runner = {"first_time_epsom": True, "notes": "no badges"}
    race = {"course": "Ascot", "distance_f": 12.0}
    assert cd_form_signal(runner, race) == 50.0


def test_first_time_epsom_overridden_by_badge():
    # If horse has CD/D/C, the badge wins (it has Epsom form)
    runner = {"first_time_epsom": True, "notes": "badges D; source"}
    assert cd_form_signal(runner, DERBY_RACE) == 70.0


# --- badge_summary helper ---------------------------------------------------

def test_badge_summary_counts():
    runners = [
        {"notes": "badges CD; source"},
        {"notes": "badges D; source"},
        {"notes": "badges D, BF; source"},
        {"notes": "no badges"},
        {},
    ]
    summary = badge_summary(runners)
    assert summary == {"CD": 1, "D": 2, "C": 0, "BF": 1, "none": 2}


def test_signal_clamped_to_0_100_range():
    # Sanity — any valid output must be in [0, 100]
    runners = [
        {"notes": "badges CD; source"},
        {"notes": "badges D; source"},
        {"notes": "badges C; source"},
        {"notes": "badges BF; source"},
        {"notes": "no badges"},
        {"first_time_epsom": True, "notes": "no badges"},
    ]
    for r in runners:
        s = cd_form_signal(r, DERBY_RACE)
        assert 0.0 <= s <= 100.0
