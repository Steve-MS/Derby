"""Tests for src.equipment — v0.6 equipment signal.

Rusty may be implementing src/equipment.py concurrently. These tests use
pytest.importorskip so collection skips cleanly until the module lands, then
exercise Danny's locked v0.6 contract.
"""
import math
from pathlib import Path

import pytest


equipment = pytest.importorskip("src.equipment")


REPO_ROOT = Path(__file__).resolve().parents[1]
EQUIPMENT_FILE = REPO_ROOT / "data" / "enrichment" / "equipment.json"
RACE = {"race_id": "equipment-contract"}


FIRST_TIME_DELTAS = {
    "blinkers": 8,
    "cheekpieces": 7,
    "tongue-tie": 6,
    "visor": 5,
    "hood": 3,
    "eyeshield": 2,
    "paddings": 2,
}


def _entry(equipment_items=None, first_time=None, changed=None, wind_surgery=None):
    return {
        "equipment": list(equipment_items or []),
        "first_time_use": list(first_time or []),
        "changed_vs_last_run": changed if changed is not None else [],
        "wind_surgery": wind_surgery,
    }


def _runner(name="Test Horse"):
    return {"horse": name, "trainer": "Trainer", "jockey": "Jockey"}


def _patch_equipment_data(monkeypatch, data):
    """Force score_equipment to see synthetic horse-keyed equipment data."""
    try:
        if hasattr(equipment.load_equipment_data, "cache_clear"):
            equipment.load_equipment_data.cache_clear()
        elif hasattr(equipment, "_clear_caches"):
            equipment._clear_caches()
    except AttributeError:
        pass
    monkeypatch.setattr(equipment, "load_equipment_data", lambda *args, **kwargs: data)


def _score(monkeypatch, horse_data, name="Test Horse"):
    _patch_equipment_data(monkeypatch, {name: horse_data})
    return equipment.score_equipment(_runner(name), RACE)


def test_loader_returns_dict_keyed_by_horse_name_from_real_file():
    data = equipment.load_equipment_data(str(EQUIPMENT_FILE))

    assert isinstance(data, dict)
    assert len(data) == 272
    assert "riley rocks" in data
    assert isinstance(data["riley rocks"], dict)


@pytest.mark.parametrize(
    "item, expected",
    [
        ("blinkers", 58.0),
        ("cheekpieces", 57.0),
        ("tongue-tie", 56.0),
        ("visor", 55.0),
        ("hood", 53.0),
        ("eyeshield", 52.0),
        ("paddings", 52.0),
    ],
)
def test_first_time_single_equipment_anchors(monkeypatch, item, expected):
    score = _score(monkeypatch, _entry([item], [item]))

    assert score == pytest.approx(expected)


def test_stacking_penalty_two_first_time_items(monkeypatch):
    score = _score(
        monkeypatch,
        _entry(["blinkers", "cheekpieces"], ["blinkers", "cheekpieces"]),
    )

    assert score == pytest.approx(62.0)  # 50 + 8 + 7 - 3


def test_stacking_penalty_three_first_time_items(monkeypatch):
    score = _score(
        monkeypatch,
        _entry(
            ["blinkers", "cheekpieces", "tongue-tie"],
            ["blinkers", "cheekpieces", "tongue-tie"],
        ),
    )

    assert score == pytest.approx(65.0)  # 50 + 8 + 7 + 6 - 6


def test_removal_bonus_one_piece_no_new_equipment(monkeypatch):
    score = _score(monkeypatch, _entry([], [], {"removed": ["hood"]}))

    assert score == pytest.approx(53.0)


def test_removal_bonus_combines_with_first_time_addition(monkeypatch):
    score = _score(
        monkeypatch,
        _entry(["blinkers"], ["blinkers"], {"removed": ["hood"]}),
    )

    assert score == pytest.approx(61.0)


def test_clamp_upper_at_90(monkeypatch):
    monkeypatch.setitem(equipment._ITEM_DELTAS, "blinkers", 100.0)

    score = _score(monkeypatch, _entry(["blinkers"], ["blinkers"]))

    assert score == pytest.approx(90.0)


def test_clamp_lower_at_10(monkeypatch):
    items = [f"unknown-piece-{i}" for i in range(25)]
    score = _score(monkeypatch, _entry(items, []))

    assert score == pytest.approx(10.0)


def test_missing_horse_returns_neutral(monkeypatch):
    _patch_equipment_data(monkeypatch, {"Other Horse": _entry(["blinkers"], ["blinkers"])})

    assert equipment.score_equipment(_runner("Missing Horse"), RACE) == pytest.approx(50.0)


def test_empty_equipment_returns_neutral(monkeypatch):
    score = _score(monkeypatch, _entry([], []))

    assert score == pytest.approx(50.0)


def test_none_runner_returns_neutral():
    assert equipment.score_equipment(None, {}) == pytest.approx(50.0)


def test_none_race_handled_gracefully(monkeypatch):
    _patch_equipment_data(monkeypatch, {"Test Horse": _entry(["blinkers"], ["blinkers"])})

    score = equipment.score_equipment(_runner(), None)

    assert isinstance(score, float)
    assert 10.0 <= score <= 90.0


def test_score_bounds_sweep_for_equipment_combos(monkeypatch):
    combos = [
        ["blinkers"],
        ["cheekpieces"],
        ["tongue-tie"],
        ["visor"],
        ["hood"],
        ["eyeshield"],
        ["paddings"],
        ["blinkers", "cheekpieces"],
        ["blinkers", "cheekpieces", "tongue-tie"],
        ["visor", "hood", "paddings"],
    ]

    for index, combo in enumerate(combos):
        score = _score(monkeypatch, _entry(combo, combo), name=f"Horse {index}")
        assert 10.0 <= score <= 90.0
        assert math.isfinite(score)


def test_output_type_is_float(monkeypatch):
    score = _score(monkeypatch, _entry(["blinkers"], ["blinkers"]))

    assert isinstance(score, float)


def test_two_horses_independent_no_state_mutation(monkeypatch):
    data = {
        "Blinker Horse": _entry(["blinkers"], ["blinkers"]),
        "Plain Horse": _entry([], []),
    }
    _patch_equipment_data(monkeypatch, data)

    first = equipment.score_equipment(_runner("Blinker Horse"), RACE)
    second = equipment.score_equipment(_runner("Plain Horse"), RACE)
    first_again = equipment.score_equipment(_runner("Blinker Horse"), RACE)

    assert first == pytest.approx(58.0)
    assert second == pytest.approx(50.0)
    assert first_again == pytest.approx(first)


def test_wind_surgery_null_does_not_crash(monkeypatch):
    score = _score(monkeypatch, _entry(["hood"], ["hood"], wind_surgery=None))

    assert score == pytest.approx(53.0)


def test_empty_changed_vs_last_run_means_no_removal_bonus(monkeypatch):
    score = _score(monkeypatch, _entry([], [], []))

    assert score == pytest.approx(50.0)


def test_empty_changed_vs_last_run_still_allows_first_time_use(monkeypatch):
    score = _score(monkeypatch, _entry(["visor"], ["visor"], []))

    assert score == pytest.approx(55.0)


def test_scoring_integration_includes_equipment_weight_and_signal(monkeypatch):
    scoring = pytest.importorskip("src.scoring")
    assert hasattr(scoring, "score_equipment"), "scoring.py must import score_equipment"

    cfg = scoring.load_default_config()
    assert cfg["weights"].get("equipment") == pytest.approx(0.0250)
    assert sum(cfg["weights"].values()) == pytest.approx(1.0)

    for signal_name in (
        "cd_form_signal",
        "sire_stamina_signal",
        "trial_form_signal",
        "market_move_signal",
        "trainer_14d_signal",
        "jt_combo_signal",
    ):
        if hasattr(scoring, signal_name):
            monkeypatch.setattr(scoring, signal_name, lambda runner, race: 50.0)
    monkeypatch.setattr(scoring, "score_equipment", lambda runner, race: 62.0)

    runner = {
        "horse": "Integration Horse",
        "rpr": 50.0,
        "ts": None,
        "or_rating": None,
        "runs": [],
        "trainer": "Unknown",
        "jockey": "Unknown",
        "draw": 1,
        "going_preference": None,
        "last_class": 1,
        "current_class": 1,
    }
    result = scoring.score_runner(runner, {"runners": [runner], "going": "good"}, cfg)

    assert result["raw_signals"]["equipment"] == pytest.approx(62.0)
    expected = sum(
        (result["raw_signals"].get(signal) if result["raw_signals"].get(signal) is not None else 50.0) * weight
        for signal, weight in cfg["weights"].items()
    )
    assert result["raw_score"] == pytest.approx(expected)
