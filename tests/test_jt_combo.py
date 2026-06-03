"""Tests for src/jt_combo.py — jockey/trainer combination signal (v0.5).

Rusty's implementation (src/jt_combo.py) is in place; these tests run
against it.

Score curve (Danny's spec §4 / Rusty's implementation):
    sr ≥ 0.35                → 90
    0.25 ≤ sr < 0.35        → lerp(75→90) over [0.25, 0.35]
    0.15 ≤ sr < 0.25        → lerp(55→75) over [0.15, 0.25]
    0.08 ≤ sr < 0.15        → lerp(40→55) over [0.08, 0.15]
    0.00 < sr < 0.08        → lerp(20→40) over [0.00, 0.08]
    sr == 0.00               → 15  (special case)

    where sr = combo_wins / combo_runners

First-time pairing override:
    first_time_pairing=True AND combo_runners=0 → 60
    (overrides the sample guard; deliberate booking signal)

Gating:
    runner["trainer"] or runner["jockey"] absent/empty  → 50
    runner["horse"] / "horse_name" absent               → 50
    Horse not in enrichment data                        → 50
    combo_runners < 10 (and not first_time_pairing)    → 50

Rusty's API:
    score_jt_combo(combo_sr: float) -> float
        Pure scorer — takes sr directly, no I/O.
    jt_combo_signal(runner, race) -> float
        Full pipeline — reads from cached load_jt_combo().
        Inject test data via monkeypatch on jt_combo.load_jt_combo.

Data format returned by load_jt_combo():
    { "Horse Name": {"combo_wins": int, "combo_runners": int,
                     "first_time_pairing": bool, ...} }
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

jt_combo = pytest.importorskip("jt_combo")
score_jt_combo = jt_combo.score_jt_combo
jt_combo_signal = jt_combo.jt_combo_signal


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _jc_data(horse, combo_wins, combo_runners, first_time=False, trainer="A P O'Brien", jockey="Ryan Moore"):
    """Minimal jt-combo data dict for one horse (matches load_jt_combo() format)."""
    return {
        horse: {
            "combo_wins": combo_wins,
            "combo_runners": combo_runners,
            "first_time_pairing": first_time,
            "trainer": trainer,
            "jockey": jockey,
        }
    }


TRAINER = "A P O'Brien"
JOCKEY  = "Ryan Moore"
HORSE   = "Galileo's Pride"
RUNNER  = {"horse": HORSE, "trainer": TRAINER, "jockey": JOCKEY}
RACE    = {}   # race dict not used by this signal


# ===========================================================================
# § score_jt_combo — pure scorer, takes sr directly
# ===========================================================================

@pytest.mark.parametrize("sr, expected, label", [
    (0.35, 90.0, "sr=0.35 cap"),
    (0.25, 75.0, "sr=0.25 band boundary"),
    (0.20, 65.0, "sr=0.20 midpoint"),
    (0.15, 55.0, "sr=0.15 band boundary"),
    (0.08, 40.0, "sr=0.08 lower boundary"),
    (0.00, 15.0, "sr=0.00 no wins"),
])
def test_score_curve_anchors(sr, expected, label):
    """Danny's spec §4 anchors."""
    score = score_jt_combo(sr)
    assert score == pytest.approx(expected, abs=1.0), (
        f"{label}: score_jt_combo({sr}) = {score:.2f}, expected ~{expected}"
    )


def test_above_cap_still_returns_90():
    """sr > 0.35 must not exceed the 90 cap."""
    assert score_jt_combo(1.00) == pytest.approx(90.0)


def test_score_is_monotone_increasing():
    """Higher strike rate must always yield higher or equal score."""
    srs = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.50]
    scores = [score_jt_combo(sr) for sr in srs]
    for i in range(len(scores) - 1):
        assert scores[i] <= scores[i + 1], (
            f"Non-monotone: sr={srs[i]} → {scores[i]:.2f} but "
            f"sr={srs[i+1]} → {scores[i+1]:.2f}"
        )


def test_output_type_pure_scorer():
    assert isinstance(score_jt_combo(0.25), float)


# ===========================================================================
# § jt_combo_signal — full pipeline, data injected via monkeypatch
# ===========================================================================

def test_hot_combo_scores_at_cap(monkeypatch):
    """sr=0.35 → 90."""
    monkeypatch.setattr(jt_combo, "load_jt_combo",
                        lambda: _jc_data(HORSE, 35, 100))
    assert jt_combo_signal(RUNNER, RACE) == pytest.approx(90.0)


def test_cold_combo_scores_at_floor(monkeypatch):
    """sr=0.00 (0 wins, 15 runners) → 15."""
    monkeypatch.setattr(jt_combo, "load_jt_combo",
                        lambda: _jc_data(HORSE, 0, 15))
    assert jt_combo_signal(RUNNER, RACE) == pytest.approx(15.0)


# ===========================================================================
# Sample guard — combo_runners < 10 → 50
# ===========================================================================

def test_sample_guard_nine_runners_returns_neutral(monkeypatch):
    """9 runners < guard of 10 → 50."""
    monkeypatch.setattr(jt_combo, "load_jt_combo",
                        lambda: _jc_data(HORSE, 3, 9))
    assert jt_combo_signal(RUNNER, RACE) == pytest.approx(50.0)


def test_sample_guard_ten_runners_scores(monkeypatch):
    """10 runners meets the guard — signal must be non-neutral."""
    monkeypatch.setattr(jt_combo, "load_jt_combo",
                        lambda: _jc_data(HORSE, 3, 10))
    assert jt_combo_signal(RUNNER, RACE) != 50.0


# ===========================================================================
# First-time pairing override
# ===========================================================================

def test_first_time_pairing_zero_runners_returns_60(monkeypatch):
    """first_time_pairing=True AND combo_runners=0 → 60."""
    monkeypatch.setattr(jt_combo, "load_jt_combo",
                        lambda: _jc_data(HORSE, 0, 0, first_time=True))
    assert jt_combo_signal(RUNNER, RACE) == pytest.approx(60.0)


def test_first_time_false_zero_runners_returns_neutral(monkeypatch):
    """first_time_pairing=False AND combo_runners=0 → sample guard → 50."""
    monkeypatch.setattr(jt_combo, "load_jt_combo",
                        lambda: _jc_data(HORSE, 0, 0, first_time=False))
    assert jt_combo_signal(RUNNER, RACE) == pytest.approx(50.0)


def test_first_time_true_with_runners_does_not_return_60(monkeypatch):
    """first_time_pairing=True only overrides when combo_runners==0.

    With runners > 0 the flag is ignored and normal scoring applies.
    TODO(Danny): spec does not explicitly address first_time+runners>0 — test
    asserts it does NOT return the 60 override; normal curve scoring applies.
    """
    monkeypatch.setattr(jt_combo, "load_jt_combo",
                        lambda: _jc_data(HORSE, 3, 10, first_time=True))
    assert jt_combo_signal(RUNNER, RACE) != pytest.approx(60.0)


# ===========================================================================
# Anti-fabrication — missing / bad runner fields
# ===========================================================================

def test_jt_combo_signal_returns_50_when_runner_is_none():
    assert jt_combo_signal(None, {}) == 50.0


def test_missing_trainer_returns_neutral(monkeypatch):
    """Runner with no 'trainer' key → 50."""
    monkeypatch.setattr(jt_combo, "load_jt_combo",
                        lambda: _jc_data(HORSE, 14, 52))
    assert jt_combo_signal({"horse": HORSE, "jockey": JOCKEY}, RACE) == pytest.approx(50.0)


def test_missing_jockey_returns_neutral(monkeypatch):
    """Runner with no 'jockey' key → 50."""
    monkeypatch.setattr(jt_combo, "load_jt_combo",
                        lambda: _jc_data(HORSE, 14, 52))
    assert jt_combo_signal({"horse": HORSE, "trainer": TRAINER}, RACE) == pytest.approx(50.0)


def test_empty_trainer_returns_neutral(monkeypatch):
    """runner['trainer'] = '' → 50."""
    monkeypatch.setattr(jt_combo, "load_jt_combo",
                        lambda: _jc_data(HORSE, 14, 52))
    assert jt_combo_signal({"horse": HORSE, "trainer": "", "jockey": JOCKEY}, RACE) == pytest.approx(50.0)


def test_horse_not_in_data_returns_neutral(monkeypatch):
    """Horse absent from enrichment dict → 50."""
    monkeypatch.setattr(jt_combo, "load_jt_combo",
                        lambda: _jc_data(HORSE, 14, 52))
    runner = {"horse": "Unknown Horse", "trainer": TRAINER, "jockey": JOCKEY}
    assert jt_combo_signal(runner, RACE) == pytest.approx(50.0)


def test_empty_data_returns_neutral(monkeypatch):
    """Empty enrichment dict → 50."""
    monkeypatch.setattr(jt_combo, "load_jt_combo", lambda: {})
    assert jt_combo_signal(RUNNER, RACE) == pytest.approx(50.0)


# ===========================================================================
# Data is horse-keyed — two horses scored independently
# ===========================================================================

def test_two_horses_scored_independently(monkeypatch):
    """Hot combo on one horse does not bleed into a cold combo on another."""
    data = {
        "Hot Horse":  {"combo_wins": 35, "combo_runners": 100, "first_time_pairing": False},
        "Cold Horse": {"combo_wins": 0,  "combo_runners": 15,  "first_time_pairing": False},
    }
    monkeypatch.setattr(jt_combo, "load_jt_combo", lambda: data)
    hot  = jt_combo_signal({"horse": "Hot Horse",  "trainer": TRAINER, "jockey": JOCKEY}, RACE)
    cold = jt_combo_signal({"horse": "Cold Horse", "trainer": TRAINER, "jockey": JOCKEY}, RACE)
    assert hot  == pytest.approx(90.0), f"Hot horse: expected 90, got {hot:.2f}"
    assert cold == pytest.approx(15.0), f"Cold horse: expected 15, got {cold:.2f}"


# ===========================================================================
# Output contract
# ===========================================================================

def test_output_is_float(monkeypatch):
    """Return type must be float."""
    monkeypatch.setattr(jt_combo, "load_jt_combo",
                        lambda: _jc_data(HORSE, 14, 52))
    assert isinstance(jt_combo_signal(RUNNER, RACE), float)


def test_output_in_valid_range(monkeypatch):
    """Score must lie in [15, 90] for valid data above sample guard."""
    cases = [
        (35, 100),  # sr=0.35 → 90
        (5,   20),  # sr=0.25 → 75
        (0,   15),  # sr=0.00 → 15
    ]
    for wins, runners in cases:
        monkeypatch.setattr(jt_combo, "load_jt_combo",
                            lambda w=wins, r=runners: _jc_data(HORSE, w, r))
        s = jt_combo_signal(RUNNER, RACE)
        assert 15.0 <= s <= 90.0, f"Out-of-range {s:.2f} for wins={wins}, runners={runners}"
