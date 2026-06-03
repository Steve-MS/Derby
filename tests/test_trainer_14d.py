"""Tests for src/trainer_14d.py — trainer recent-form signal (v0.5).

Rusty's implementation (src/trainer_14d.py) is in place; these tests run
against it.

Score curve (Danny's spec §3 / Rusty's implementation):
    sr ≥ 0.30                → 90
    0.20 ≤ sr < 0.30        → lerp(75→90) over [0.20, 0.30]
    0.12 ≤ sr < 0.20        → lerp(55→75) over [0.12, 0.20]
    0.06 ≤ sr < 0.12        → lerp(40→55) over [0.06, 0.12]
    0.00 < sr < 0.06        → lerp(20→40) over [0.00, 0.06]
    sr == 0.00               → 15  (special case)

    where sr = wins_14d / runners_14d  (recomputed; stored strike_rate ignored)

Gating:
    runner["trainer"] absent or empty                → 50
    trainer not in enrichment data                   → 50
    runners_14d < 5                                  → 50 (small-sample guard)

Rusty's API:
    score_trainer_14d(strike_rate: float) -> float
        Pure scorer — takes sr directly, no I/O.
    trainer_14d_signal(runner, race) -> float
        Full pipeline — reads from cached load_trainer_14d().
        Inject test data via monkeypatch on trainer_14d.load_trainer_14d.

Data format returned by load_trainer_14d():
    { "Trainer Name": {"wins_14d": int, "runners_14d": int, ...} }
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

trainer_14d = pytest.importorskip("trainer_14d")
score_trainer_14d = trainer_14d.score_trainer_14d
trainer_14d_signal = trainer_14d.trainer_14d_signal


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _td_data(trainer, wins, runners, stored_sr=None):
    """Minimal trainer-14d data dict for one trainer.

    stored_sr defaults to wins/runners — lets tests deliberately inject a
    stale/wrong stored value to verify it is ignored by the signal.
    """
    if stored_sr is None:
        stored_sr = round(wins / runners, 4) if runners > 0 else 0.0
    return {
        trainer: {
            "wins_14d": wins,
            "runners_14d": runners,
            "strike_rate": stored_sr,
        }
    }


RUNNER = {"trainer": "A P O'Brien"}
RACE = {}   # race dict not used by this signal


# ===========================================================================
# § score_trainer_14d — pure scorer, takes strike rate directly
# ===========================================================================

@pytest.mark.parametrize("sr, expected, label", [
    (0.30, 90.0, "sr=0.30 cap"),
    (0.20, 75.0, "sr=0.20 band boundary"),
    (0.12, 55.0, "sr=0.12 band boundary"),
    (0.06, 40.0, "sr=0.06 band boundary"),
    (0.00, 15.0, "sr=0.00 zero wins"),
    # sr=0.10 → lerp(40→55) at t=0.6667 → 50.0 (Danny spec says ~48; formula gives 50)
    # TODO(Danny): spec anchor ~48 vs formula 50 — confirm which is authoritative.
    (0.10, 50.0, "sr=0.10 mid band"),
])
def test_score_curve_anchors(sr, expected, label):
    """Danny's score-curve anchors from spec §3."""
    score = score_trainer_14d(sr)
    assert score == pytest.approx(expected, abs=1.0), (
        f"{label}: score_trainer_14d({sr}) = {score:.2f}, expected ~{expected}"
    )


def test_score_is_monotone_increasing():
    """Higher strike rate must always yield higher (or equal) score."""
    srs = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40]
    scores = [score_trainer_14d(sr) for sr in srs]
    for i in range(len(scores) - 1):
        assert scores[i] <= scores[i + 1], (
            f"Non-monotone: sr={srs[i]} → {scores[i]:.2f} but "
            f"sr={srs[i+1]} → {scores[i+1]:.2f}"
        )


def test_output_type_pure_scorer():
    assert isinstance(score_trainer_14d(0.20), float)


# ===========================================================================
# § trainer_14d_signal — full pipeline, data injected via monkeypatch
# ===========================================================================

def test_hot_trainer_scores_above_neutral(monkeypatch):
    """sr=0.30 → 90, well above neutral 50."""
    monkeypatch.setattr(trainer_14d, "load_trainer_14d",
                        lambda: _td_data("A P O'Brien", 9, 30))
    assert trainer_14d_signal(RUNNER, RACE) == pytest.approx(90.0)


def test_cold_trainer_scores_below_neutral(monkeypatch):
    """sr=0.00 → 15, well below neutral 50."""
    monkeypatch.setattr(trainer_14d, "load_trainer_14d",
                        lambda: _td_data("A P O'Brien", 0, 10))
    assert trainer_14d_signal(RUNNER, RACE) < 50.0


# ===========================================================================
# Sample guard — runners_14d < 5 → return 50
# ===========================================================================

def test_sample_guard_four_runners_returns_neutral(monkeypatch):
    """runners_14d = 4 is below the guard of 5 → neutral 50."""
    monkeypatch.setattr(trainer_14d, "load_trainer_14d",
                        lambda: _td_data("A P O'Brien", 4, 4))
    assert trainer_14d_signal(RUNNER, RACE) == pytest.approx(50.0)


def test_sample_guard_five_runners_scores(monkeypatch):
    """runners_14d = 5 meets the guard — signal must be non-neutral."""
    monkeypatch.setattr(trainer_14d, "load_trainer_14d",
                        lambda: _td_data("A P O'Brien", 3, 5))
    score = trainer_14d_signal(RUNNER, RACE)
    assert score != 50.0


# ===========================================================================
# Anti-fabrication — missing / bad data always returns 50
# ===========================================================================

def test_trainer_14d_signal_returns_50_when_runner_is_none():
    assert trainer_14d_signal(None, {}) == 50.0


def test_trainer_not_in_data_returns_neutral(monkeypatch):
    """Trainer absent from enrichment file → neutral 50."""
    monkeypatch.setattr(trainer_14d, "load_trainer_14d", lambda: {})
    assert trainer_14d_signal(RUNNER, RACE) == pytest.approx(50.0)


def test_missing_trainer_key_in_runner_returns_neutral(monkeypatch):
    """Runner dict with no 'trainer' key → neutral."""
    monkeypatch.setattr(trainer_14d, "load_trainer_14d",
                        lambda: _td_data("A P O'Brien", 9, 30))
    assert trainer_14d_signal({}, RACE) == pytest.approx(50.0)


def test_empty_trainer_string_returns_neutral(monkeypatch):
    """runner['trainer'] = '' → neutral (blank string guard)."""
    monkeypatch.setattr(trainer_14d, "load_trainer_14d",
                        lambda: _td_data("A P O'Brien", 9, 30))
    assert trainer_14d_signal({"trainer": ""}, RACE) == pytest.approx(50.0)


def test_none_trainer_value_returns_neutral(monkeypatch):
    """runner['trainer'] = None → neutral."""
    monkeypatch.setattr(trainer_14d, "load_trainer_14d",
                        lambda: _td_data("A P O'Brien", 9, 30))
    assert trainer_14d_signal({"trainer": None}, RACE) == pytest.approx(50.0)


def test_missing_wins_14d_defaults_to_zero(monkeypatch):
    """Enrichment entry missing wins_14d defaults to 0 → sr=0.00 → 15 (floor score).

    Rusty's implementation uses entry.get("wins_14d", 0), treating absent
    wins as zero wins rather than missing data.
    """
    monkeypatch.setattr(trainer_14d, "load_trainer_14d",
                        lambda: {"A P O'Brien": {"runners_14d": 10}})
    assert trainer_14d_signal(RUNNER, RACE) == pytest.approx(15.0)


# ===========================================================================
# Stale strike_rate field is ignored — score recomputed from wins/runners
# ===========================================================================

def test_signal_ignores_stored_strike_rate(monkeypatch):
    """Danny's spec §3: scorer must use wins_14d/runners_14d, not stored sr.

    Inject a deliberately wrong stored strike_rate (0.50) but the computed
    sr = wins/runners = 4/20 = 0.20.  Signal must score for 0.20 → 75.
    """
    data = {"A P O'Brien": {
        "wins_14d": 4,
        "runners_14d": 20,
        "strike_rate": 0.50,   # stale/wrong — must be ignored
    }}
    monkeypatch.setattr(trainer_14d, "load_trainer_14d", lambda: data)
    score = trainer_14d_signal(RUNNER, RACE)
    assert score == pytest.approx(75.0, abs=1.0), (
        f"Expected ~75 (sr=0.20); stale sr=0.50 must not be used, got {score:.2f}"
    )


# ===========================================================================
# Full pipeline integration
# ===========================================================================

def test_full_pipeline_hot_trainer(monkeypatch):
    """End-to-end: hot trainer (sr=0.30) → 90 via full signal path."""
    data = {"Willie Mullins": {"wins_14d": 9, "runners_14d": 30, "strike_rate": 0.30}}
    monkeypatch.setattr(trainer_14d, "load_trainer_14d", lambda: data)
    runner = {"trainer": "Willie Mullins"}
    assert trainer_14d_signal(runner, RACE) == pytest.approx(90.0)


def test_full_pipeline_sample_guard_triggers(monkeypatch):
    """End-to-end: high sr but only 3 runners → sample guard → 50."""
    data = {"Hot Newcomer": {"wins_14d": 3, "runners_14d": 3, "strike_rate": 1.0}}
    monkeypatch.setattr(trainer_14d, "load_trainer_14d", lambda: data)
    runner = {"trainer": "Hot Newcomer"}
    assert trainer_14d_signal(runner, RACE) == pytest.approx(50.0)


# ===========================================================================
# Output contract
# ===========================================================================

def test_output_is_float(monkeypatch):
    """Return type must be float."""
    monkeypatch.setattr(trainer_14d, "load_trainer_14d",
                        lambda: _td_data("A P O'Brien", 9, 30))
    assert isinstance(trainer_14d_signal(RUNNER, RACE), float)


def test_output_in_valid_range(monkeypatch):
    """Score must lie in [15, 90] for valid enrichment data above sample guard."""
    cases = [
        ("A P O'Brien", 9, 30),   # sr=0.30 → 90
        ("A P O'Brien", 1, 10),   # sr=0.10 → 50
        ("A P O'Brien", 0, 10),   # sr=0.00 → 15
    ]
    for trainer, wins, runners in cases:
        monkeypatch.setattr(trainer_14d, "load_trainer_14d",
                            lambda w=wins, r=runners: _td_data("A P O'Brien", w, r))
        s = trainer_14d_signal(RUNNER, RACE)
        assert 15.0 <= s <= 90.0, f"Out-of-range {s:.2f} for wins={wins}, runners={runners}"


