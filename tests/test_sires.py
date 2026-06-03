"""Tests for src/sires.py — sire stamina signal."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import sires
from sires import get_sire, sire_stamina_signal


DERBY_RACE = {"course": "Epsom", "distance_f": 12.0}
OAKS_RACE = {"course": "Epsom", "distance_f": 12.0}
MID_RACE = {"course": "Epsom", "distance_f": 10.0}
SPRINT_RACE = {"course": "Epsom", "distance_f": 5.0}


# --- get_sire ---------------------------------------------------------------

def test_get_sire_from_runner_field():
    runner = {"horse": "Whatever", "sire": "Galileo"}
    assert get_sire(runner) == "Galileo"


def test_get_sire_from_enrichment_file():
    # These come from data/enrichment/horse-profiles.json
    assert get_sire({"horse": "Benvenuto Cellini"}) == "Frankel"
    assert get_sire({"horse": "Maltese Cross"}) == "Sea The Stars"
    assert get_sire({"horse": "Constitution River"}) == "Wootton Bassett"


def test_get_sire_unknown_horse():
    assert get_sire({"horse": "Made Up Horse Name 12345"}) is None


def test_get_sire_no_horse_name():
    assert get_sire({}) is None


def test_get_sire_runner_field_overrides_enrichment():
    runner = {"horse": "Benvenuto Cellini", "sire": "Override Sire"}
    assert get_sire(runner) == "Override Sire"


# --- sire_stamina_signal: distance gating -----------------------------------

def test_signal_neutral_for_sprint():
    runner = {"horse": "Benvenuto Cellini"}  # Frankel = 85
    assert sire_stamina_signal(runner, SPRINT_RACE) == 50.0


def test_signal_neutral_just_below_threshold():
    runner = {"horse": "Benvenuto Cellini"}
    race = {"course": "Epsom", "distance_f": 9.5}
    assert sire_stamina_signal(runner, race) == 50.0


def test_signal_active_at_10f():
    runner = {"horse": "Benvenuto Cellini"}  # Frankel = 85
    assert sire_stamina_signal(runner, MID_RACE) == 85.0


def test_signal_active_at_derby_trip():
    runner = {"horse": "Maltese Cross"}  # Sea The Stars = 90
    assert sire_stamina_signal(runner, DERBY_RACE) == 90.0


# --- sire_stamina_signal: anti-fabrication ----------------------------------

def test_signal_neutral_when_horse_unknown():
    runner = {"horse": "Some Horse Not In Profiles"}
    assert sire_stamina_signal(runner, DERBY_RACE) == 50.0


def test_signal_neutral_when_sire_not_in_lookup():
    runner = {"horse": "Mystery Horse", "sire": "Sire That Does Not Exist"}
    assert sire_stamina_signal(runner, DERBY_RACE) == 50.0


def test_signal_neutral_when_no_horse_name_no_sire():
    assert sire_stamina_signal({}, DERBY_RACE) == 50.0


# --- sire_stamina_signal: known mappings ------------------------------------

def test_signal_for_top_staying_sires():
    # Camelot is in lookup at 88
    assert sire_stamina_signal({"sire": "Camelot"}, DERBY_RACE) == 88.0
    # Galileo at 95
    assert sire_stamina_signal({"sire": "Galileo"}, DERBY_RACE) == 95.0


def test_signal_for_sprint_leaning_sires():
    # No Nay Never = 25, applied at 10f+
    assert sire_stamina_signal({"sire": "No Nay Never"}, DERBY_RACE) == 25.0


def test_signal_clamped_in_range():
    # Walk every Derby/Oaks runner profile
    for horse in [
        "Benvenuto Cellini", "Item", "Ancient Egypt", "Maltese Cross",
        "Christmas Day", "Pierre Bonnard", "Constitution River",
        "Amelia Earhart", "Precise", "Legacy Link", "Thundering On",
        "K Sarra", "Cameo", "Sugar Island",
    ]:
        s = sire_stamina_signal({"horse": horse}, DERBY_RACE)
        assert 0.0 <= s <= 100.0


# --- distance_furlongs alias --------------------------------------------------

def test_signal_accepts_distance_furlongs_alias():
    runner = {"horse": "Benvenuto Cellini"}
    race = {"course": "Epsom", "distance_furlongs": 12.0}
    assert sire_stamina_signal(runner, race) == 85.0


# --- cache loading ----------------------------------------------------------

def test_caches_populated():
    profiles = sires.load_horse_profiles()
    stamina = sires.load_sire_stamina()
    assert len(profiles) >= 29  # Derby (18) + Oaks (11)
    assert len(stamina) >= 30
    assert "Frankel" in stamina
    assert "Galileo" in stamina
