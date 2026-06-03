"""Tests for src/market_move.py — market price movement signal (v0.5).

Rusty's implementation (src/market_move.py) is in place; these tests run
against it.

Score curve (Danny's spec §2 / Rusty's implementation):
    Δip ≥ +0.07             → 90  (steamer cap)
    +0.03 ≤ Δip < +0.07    → lerp(70→90) over [+0.03, +0.07]
    +0.01 ≤ Δip < +0.03    → lerp(55→70) over [+0.01, +0.03]
    −0.01 < Δip < +0.01    → 50  (noise band)
    −0.04 < Δip ≤ −0.01    → lerp(30→50) over [−0.04, −0.01]
    −0.06 < Δip ≤ −0.04    → lerp(10→30) over [−0.06, −0.04]
    Δip ≤ −0.06             → 10  (drifter floor)
    Final score clamped to [10, 90].

Rusty's API:
    score_market_move(delta_ip: float) -> float
        Pure scorer — takes Δip = ip_latest − ip_baseline directly.
    market_move_signal(runner, race) -> float
        Full pipeline — reads from cached load_market_data().
        Inject test data via monkeypatch on market_move.load_market_data.

Data format returned by load_market_data():
    { "Horse Name": {"baseline_price": float, "latest_price": float | None} }
    latest_price is None when the latest snapshot hasn't been populated yet.
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

market_move = pytest.importorskip("market_move")
score_market_move = market_move.score_market_move
market_move_signal = market_move.market_move_signal


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _mm_data(**entries):
    """Build a fake load_market_data() return dict.

    Usage: _mm_data(Altior=(7.0, 6.0), Sprinter=(5.0, None))
    Each value is (baseline_price, latest_price) where latest_price=None
    means the latest snapshot hasn't been populated yet.
    """
    return {
        name: {"baseline_price": bp, "latest_price": lp}
        for name, (bp, lp) in entries.items()
    }


RUNNER = {"horse": "Altior", "trainer": "N Henderson", "jockey": "A P McCoy"}
RACE = {}   # no distance/going gate on this signal


# ===========================================================================
# § score_market_move — pure scorer, takes Δip directly
# ===========================================================================

@pytest.mark.parametrize("delta_ip, lo, hi, label", [
    # 6/4 → 11/10 (2.5 → 2.1): Δip ≈ +0.076 → steamer cap → 90
    (1/2.1 - 1/2.5,   90.0, 90.0, "6/4→11/10 steamer cap"),
    # 4/1 → 7/1  (5.0 → 8.0): Δip ≈ -0.075 → drifter floor → 10
    (1/8.0 - 1/5.0,   10.0, 10.0, "4/1→7/1 drifter floor"),
    # 100/1 → 80/1 (101→81):  Δip ≈ +0.0025 → noise band → 50 (anti-trap)
    (1/81 - 1/101,    50.0, 50.0, "100/1→80/1 anti-trap noise band"),
    # 6/1 → 5/1  (7.0 → 6.0): Δip ≈ +0.024 → lerp(55→70) ≈ 65.5
    # NOTE: Steve's brief quotes ~62; formula gives ~65.5.
    # TODO(Danny): confirm authoritative anchor — brief ~62 vs formula ~65.5.
    (1/6.0 - 1/7.0,   60.0, 70.0, "6/1→5/1 mid steamer band"),
    # 3/1 → 5/2  (4.0 → 3.5): Δip ≈ +0.036 → lerp(70→90), score ≈ 73
    (1/3.5 - 1/4.0,   70.0, 80.0, "3/1→5/2 upper steamer band"),
])
def test_score_curve_danny_worked_examples(delta_ip, lo, hi, label):
    """Danny's example price pairs map to their expected score band."""
    score = score_market_move(delta_ip)
    assert lo <= score <= hi, (
        f"{label}: score_market_move({delta_ip:.4f}) = {score:.2f}, "
        f"expected [{lo}, {hi}]"
    )


def test_score_exact_6to1_to_5to1():
    """6/1→5/1: formula gives exactly 65.5 (Rusty's docstring '62.0' is a typo)."""
    # TODO(Danny): docstring in market_move.py claims 62.0 but formula → 65.5
    score = score_market_move(1/6.0 - 1/7.0)
    assert score == pytest.approx(65.5, abs=0.5)


def test_steamer_cap_clamps_at_90():
    """Δip well above 0.07 must clamp at 90."""
    assert score_market_move(0.20) == 90.0


def test_drifter_floor_clamps_at_10():
    """Δip well below −0.06 must clamp at 10."""
    assert score_market_move(-0.30) == 10.0


def test_noise_band_returns_50():
    """Δip = 0.0 is dead centre → neutral 50."""
    assert score_market_move(0.00) == 50.0


@pytest.mark.parametrize("delta_ip, label", [
    (0.005,  "tiny positive drift"),
    (-0.005, "tiny negative drift"),
    (0.009,  "just below noise HI"),
    (-0.009, "just above noise LO"),
])
def test_noise_band_variants(delta_ip, label):
    """Edge values still inside ±0.01 noise band → 50."""
    assert score_market_move(delta_ip) == 50.0, f"{label} should be 50"


def test_score_is_monotone_steamer():
    """Larger steamer Δip → higher score."""
    assert score_market_move(0.04) > score_market_move(0.02)


def test_score_is_monotone_drifter():
    """Larger drift (more negative Δip) → lower score."""
    assert score_market_move(-0.04) < score_market_move(-0.02)


def test_output_type_pure_scorer():
    assert isinstance(score_market_move(0.0), float)


# ===========================================================================
# § market_move_signal — full pipeline, data injected via monkeypatch
# ===========================================================================

def test_steamer_scores_above_neutral(monkeypatch):
    """Valid steamer (6/1→5/1) → score above 50."""
    monkeypatch.setattr(market_move, "load_market_data",
                        lambda: _mm_data(Altior=(7.0, 6.0)))
    assert market_move_signal(RUNNER, RACE) > 50.0


def test_drifter_scores_below_neutral(monkeypatch):
    """Valid drifter (4/1→7/1) → score below 50."""
    monkeypatch.setattr(market_move, "load_market_data",
                        lambda: _mm_data(Altior=(5.0, 8.0)))
    assert market_move_signal(RUNNER, RACE) < 50.0


def test_heavy_steamer_hits_cap(monkeypatch):
    """6/4→11/10 is above cap — signal returns 90."""
    monkeypatch.setattr(market_move, "load_market_data",
                        lambda: _mm_data(Altior=(2.5, 2.1)))
    assert market_move_signal(RUNNER, RACE) == pytest.approx(90.0)


def test_drifter_hits_floor(monkeypatch):
    """4/1→7/1 is below floor — signal returns 10."""
    monkeypatch.setattr(market_move, "load_market_data",
                        lambda: _mm_data(Altior=(5.0, 8.0)))
    assert market_move_signal(RUNNER, RACE) == pytest.approx(10.0)


def test_anti_trap_100to1_to_80to1_noise_band(monkeypatch):
    """100/1→80/1 is huge in raw terms but tiny Δip — must stay at 50."""
    monkeypatch.setattr(market_move, "load_market_data",
                        lambda: _mm_data(Altior=(101.0, 81.0)))
    assert market_move_signal(RUNNER, RACE) == pytest.approx(50.0)


def test_missing_latest_price_returns_neutral(monkeypatch):
    """latest_price=None (snapshot not yet populated) → neutral 50."""
    monkeypatch.setattr(market_move, "load_market_data",
                        lambda: _mm_data(Altior=(7.0, None)))
    assert market_move_signal(RUNNER, RACE) == pytest.approx(50.0)


def test_horse_not_in_market_data_returns_neutral(monkeypatch):
    """Horse absent from combined data (no baseline) → neutral 50."""
    monkeypatch.setattr(market_move, "load_market_data", lambda: {})
    assert market_move_signal(RUNNER, RACE) == pytest.approx(50.0)


def test_baseline_odds_le_one_returns_neutral(monkeypatch):
    """Baseline price ≤ 1.0 is invalid → neutral."""
    monkeypatch.setattr(market_move, "load_market_data",
                        lambda: {"Altior": {"baseline_price": 1.0, "latest_price": 6.0}})
    assert market_move_signal(RUNNER, RACE) == pytest.approx(50.0)


def test_latest_odds_le_one_returns_neutral(monkeypatch):
    """Latest price ≤ 1.0 is corrupt → neutral."""
    monkeypatch.setattr(market_move, "load_market_data",
                        lambda: {"Altior": {"baseline_price": 7.0, "latest_price": 0.9}})
    assert market_move_signal(RUNNER, RACE) == pytest.approx(50.0)


def test_non_numeric_baseline_returns_neutral(monkeypatch):
    """Non-numeric baseline (e.g. 'SP') must not crash → neutral 50."""
    monkeypatch.setattr(market_move, "load_market_data",
                        lambda: {"Altior": {"baseline_price": "SP", "latest_price": 6.0}})
    assert market_move_signal(RUNNER, RACE) == pytest.approx(50.0)


def test_market_move_signal_returns_50_when_runner_is_none():
    assert market_move_signal(None, {}) == 50.0


def test_missing_horse_key_in_runner_returns_neutral(monkeypatch):
    """Runner dict missing 'horse' and 'horse_name' keys → neutral."""
    monkeypatch.setattr(market_move, "load_market_data",
                        lambda: _mm_data(Altior=(7.0, 6.0)))
    assert market_move_signal({}, RACE) == pytest.approx(50.0)


# ===========================================================================
# No distance or going gate — signal must fire for any race conditions
# ===========================================================================

def test_signal_active_for_sprint_race(monkeypatch):
    """No distance gate: 5f sprint must still produce non-neutral score."""
    monkeypatch.setattr(market_move, "load_market_data",
                        lambda: _mm_data(Altior=(9.0, 6.0)))
    assert market_move_signal(RUNNER, {"distance_f": 5, "going": "Firm"}) != 50.0


def test_signal_active_for_heavy_going(monkeypatch):
    """No going gate: heavy ground must not neutralise market data."""
    monkeypatch.setattr(market_move, "load_market_data",
                        lambda: _mm_data(Altior=(9.0, 6.0)))
    assert market_move_signal(RUNNER, {"distance_f": 12, "going": "Heavy"}) != 50.0


# ===========================================================================
# Output contract
# ===========================================================================

def test_output_is_float(monkeypatch):
    """Return type must be float."""
    monkeypatch.setattr(market_move, "load_market_data",
                        lambda: _mm_data(Altior=(7.0, 6.0)))
    assert isinstance(market_move_signal(RUNNER, RACE), float)


def test_output_always_in_10_to_90_range(monkeypatch):
    """Clamping contract: every valid case stays in [10, 90]."""
    cases = [
        (2.5,   2.1,   "heavy steamer"),
        (7.0,   6.0,   "mid steamer"),
        (5.0,   8.0,   "drifter"),
        (101.0, 81.0,  "anti-trap long shot"),
        (5.0,   5.0,   "no movement"),
        (3.5,   21.0,  "extreme drift"),
        (21.0,  3.5,   "extreme steam"),
    ]
    for bp, lp, label in cases:
        monkeypatch.setattr(market_move, "load_market_data",
                            lambda bp=bp, lp=lp: _mm_data(Altior=(bp, lp)))
        s = market_move_signal(RUNNER, RACE)
        assert 10.0 <= s <= 90.0, f"Out-of-range {s:.2f} for '{label}'"
