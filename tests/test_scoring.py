"""
test_scoring.py — Unit tests for Kaylee's scoring.py module.

API (v0.1, per Kaylee's implementation):
  - score_runner(runner: dict, race: dict, config: dict) -> dict
        Returns {"horse", "raw_signals", "raw_score", "missing_data_flags", "going_data"}
  - score_race(race: dict, config: dict) -> dict
        Returns {"race_id", "ranked_runners", "confidence",
                 "bet_recommendation", "race_stdev", "race_competitiveness",
                 "missing_data_flags"}
        ranked_runners is sorted by score desc; each entry has
        {"rank", "horse", "score", "score_breakdown", ...}
  - load_default_config() -> dict

Run with: pytest tests/test_scoring.py -v

Synthetic fixtures cover three canonical scenarios:
  1. Clear favourite    — one runner is obviously stronger on all signals
  2. Wide-open race     — runners are closely matched, scores should be close
  3. Missing-data race  — some runners have None/missing fields; model must not crash
"""

import math
import os
import sys

import pytest

# Add src/ to path so we can import scoring directly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scoring import load_default_config, score_race, score_runner  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def config():
    """Use the real default config so tests exercise the live weight set."""
    return load_default_config()


# Runner field names per scoring.py:
#   horse          — display name (horse_name is a legacy fallback)
#   or_rating      — official rating used by _best_rating() (rpr > ts > or_rating > or)
#   form_string    — raw form string, e.g. "111" = three consecutive wins (rightmost = most recent)
#   trainer        — trainer name looked up in internal bump table
#   jockey         — jockey name looked up in internal bump table
#   going_preference — runner's preferred going; matched against race going
#   course_winner  — bool, backward-compat fallback when cd_wins absent
#   distance_winner — bool, backward-compat fallback when cd_wins absent

CLEAR_FAVOURITE_RACE = {
    "race_id": "test-epsom-clear-favourite",
    "race_name": "Test Maiden Stakes",
    "race_time": "14:00",
    "course": "Epsom",
    "field_size": 8,
    "going": "Good to Firm",
    "distance_furlongs": 8,
    "runners": [
        {
            "horse": "Iron Duke",
            "age": 3,
            "weight_lbs": 126,
            "or_rating": 95,
            "form_string": "111",
            "trainer": "Aidan O'Brien",   # top-tier trainer bump = 10
            "jockey": "Ryan Moore",        # top-tier jockey bump = 10
            "days_since_last_run": 14,
            "course_winner": True,
            "distance_winner": True,
            "going_preference": "Good to Firm",
        },
        {
            "horse": "Plodder",
            "age": 3,
            "weight_lbs": 126,
            "or_rating": 72,
            "form_string": "456",
            "trainer": "Unknown Trainer",
            "jockey": "Unknown Jockey",
            "days_since_last_run": 45,
            "course_winner": False,
            "distance_winner": False,
            "going_preference": "soft",
        },
        # Fill field to 8 with anonymous average runners
        *[
            {
                "horse": f"Average Horse {i}",
                "age": 3,
                "weight_lbs": 126,
                "or_rating": 80,
                "form_string": "345",
                "trainer": "Unknown Trainer",
                "jockey": "Unknown Jockey",
                "days_since_last_run": 21,
                "course_winner": False,
                "distance_winner": False,
                "going_preference": "soft",
            }
            for i in range(1, 7)
        ],
    ],
}

WIDE_OPEN_RACE = {
    "race_id": "test-epsom-wide-open",
    "race_name": "Test Handicap",
    "race_time": "14:35",
    "course": "Epsom",
    "field_size": 6,
    "going": "Good",
    "distance_furlongs": 6,
    "runners": [
        {
            "horse": f"Runner {i}",
            "age": 4,
            "weight_lbs": 124 + i,
            "or_rating": 85,
            "form_string": "234",
            "trainer": "",
            "jockey": "",
            "days_since_last_run": 28,
            "course_winner": False,
            "distance_winner": False,
        }
        for i in range(6)
    ],
}

MISSING_DATA_RACE = {
    "race_id": "test-epsom-missing-data",
    "race_name": "Test Novice Chase",
    "race_time": "15:10",
    "course": "Epsom",
    "field_size": 5,
    "going": None,
    "distance_furlongs": None,
    "runners": [
        {
            # All fields absent — model must fall back to neutral defaults everywhere.
            "horse": "Ghost Runner",
            "age": None,
            "weight_lbs": None,
            "or_rating": None,
            "form_string": None,
            "trainer": None,
            "jockey": None,
            "days_since_last_run": None,
            "course_winner": None,
            "distance_winner": None,
        },
        {
            # Rating missing, some form present, known trainer, no jockey.
            "horse": "Partial Data",
            "age": 5,
            "weight_lbs": 128,
            "or_rating": None,
            "form_string": "12",
            "trainer": "Roger Varian",   # bump = 7; ensures trainer signal > 0
            "jockey": None,
            "days_since_last_run": 10,
            "course_winner": False,
            "distance_winner": True,
        },
        # Normal runners with good recent form so Ghost (neutral defaults) is not #1.
        *[
            {
                "horse": f"Normal Runner {i}",
                "age": 4,
                "weight_lbs": 126,
                "or_rating": 90,
                "form_string": "112",   # recent wins → form signal > neutral 50
                "trainer": "Unknown Trainer",
                "jockey": "Unknown Jockey",
                "days_since_last_run": 30,
                "course_winner": False,
                "distance_winner": False,
            }
            for i in range(3)
        ],
    ],
}


# ---------------------------------------------------------------------------
# Scenario 1: Clear favourite
# ---------------------------------------------------------------------------

class TestClearFavourite:
    """Iron Duke is clearly stronger on every signal — model should rank him #1."""

    def test_top_pick_is_clear_favourite(self, config):
        ranked = score_race(CLEAR_FAVOURITE_RACE, config)["ranked_runners"]
        assert ranked[0]["horse"] == "Iron Duke", (
            f"Expected Iron Duke as top pick, got {ranked[0]['horse']}"
        )

    def test_favourite_score_substantially_above_second(self, config):
        """Top pick's score should be meaningfully higher than #2 (not a fluke margin)."""
        ranked = score_race(CLEAR_FAVOURITE_RACE, config)["ranked_runners"]
        top_score = ranked[0]["score"]
        second_score = ranked[1]["score"]
        margin = (top_score - second_score) / top_score
        assert margin >= 0.10, (
            f"Expected ≥10% relative margin between #1 and #2, got {margin:.1%}"
        )

    def test_plodder_is_near_bottom(self, config):
        """The weakest runner (Plodder) should be ranked in the bottom half."""
        ranked = score_race(CLEAR_FAVOURITE_RACE, config)["ranked_runners"]
        names = [r["horse"] for r in ranked]
        plodder_rank = names.index("Plodder") + 1   # 1-based
        assert plodder_rank > len(ranked) // 2, (
            f"Plodder should be bottom half, ranked {plodder_rank}/{len(ranked)}"
        )

    def test_score_runner_returns_positive(self, config):
        runner = CLEAR_FAVOURITE_RACE["runners"][0]
        result = score_runner(runner, CLEAR_FAVOURITE_RACE, config)
        assert isinstance(result["raw_score"], float), (
            "score_runner must return a dict with a numeric raw_score"
        )
        assert result["raw_score"] >= 0, f"raw_score should be non-negative, got {result['raw_score']}"

    def test_all_runners_scored(self, config):
        ranked = score_race(CLEAR_FAVOURITE_RACE, config)["ranked_runners"]
        assert len(ranked) == len(CLEAR_FAVOURITE_RACE["runners"]), (
            "score_race must return a score for every runner"
        )

    def test_output_sorted_descending(self, config):
        ranked = score_race(CLEAR_FAVOURITE_RACE, config)["ranked_runners"]
        scores = [r["score"] for r in ranked]
        assert scores == sorted(scores, reverse=True), (
            "score_race must return runners sorted by score descending"
        )


# ---------------------------------------------------------------------------
# Scenario 2: Wide-open race
# ---------------------------------------------------------------------------

class TestWideOpenRace:
    """Six near-identical runners — scores should be close but model must not crash."""

    def test_returns_all_runners(self, config):
        ranked = score_race(WIDE_OPEN_RACE, config)["ranked_runners"]
        assert len(ranked) == 6

    def test_scores_are_finite(self, config):
        ranked = score_race(WIDE_OPEN_RACE, config)["ranked_runners"]
        for r in ranked:
            assert math.isfinite(r["score"]), f"Score must be finite, got {r['score']}"

    def test_scores_are_close(self, config):
        """In a wide-open race, score spread should be relatively small."""
        ranked = score_race(WIDE_OPEN_RACE, config)["ranked_runners"]
        scores = [r["score"] for r in ranked]
        spread = max(scores) - min(scores)
        top = max(scores)
        relative_spread = spread / top if top > 0 else 0
        # We allow up to 30% relative spread in a near-identical field
        assert relative_spread <= 0.30, (
            f"Scores too spread out for a wide-open race: {relative_spread:.1%} relative spread"
        )

    def test_output_has_rank_field(self, config):
        """Each output dict should have a 'rank' field (1-indexed)."""
        ranked = score_race(WIDE_OPEN_RACE, config)["ranked_runners"]
        for i, r in enumerate(ranked):
            assert "rank" in r, f"Missing 'rank' field on runner {r}"
            assert r["rank"] == i + 1, f"rank mismatch at position {i+1}: got {r['rank']}"


# ---------------------------------------------------------------------------
# Scenario 3: Missing data
# ---------------------------------------------------------------------------

class TestMissingDataRace:
    """Some runners have None/missing fields — model must degrade gracefully, not crash."""

    def test_does_not_crash_on_none_fields(self, config):
        """score_race must not raise an exception when data is None."""
        result = score_race(MISSING_DATA_RACE, config)
        assert result is not None
        assert len(result["ranked_runners"]) > 0

    def test_ghost_runner_not_top_pick(self, config):
        """A runner with all-None data should never be ranked #1."""
        ranked = score_race(MISSING_DATA_RACE, config)["ranked_runners"]
        assert ranked[0]["horse"] != "Ghost Runner", (
            "All-None runner should not be ranked #1"
        )

    def test_scores_are_not_nan(self, config):
        ranked = score_race(MISSING_DATA_RACE, config)["ranked_runners"]
        for r in ranked:
            assert not math.isnan(r["score"]), (
                f"NaN score for {r['horse']} — model must handle missing data"
            )

    def test_partial_data_runner_gets_scored(self, config):
        """Partial Data has some valid fields — should receive a meaningful (non-zero) score."""
        ranked = score_race(MISSING_DATA_RACE, config)["ranked_runners"]
        partial = next(r for r in ranked if r["horse"] == "Partial Data")
        assert partial["score"] > 0, (
            "Partial Data runner has valid fields and should score > 0"
        )


# ---------------------------------------------------------------------------
# Scenario 4: Going-fit
# ---------------------------------------------------------------------------

class TestGoingFit:
    """Historical going evidence is surfaced as a weighted model factor."""

    def test_going_fit_signal_and_breakdown_present(self, config):
        race = {
            "race_id": "test-going-fit",
            "course": "Epsom",
            "distance_furlongs": 8,
            "going": "Soft",
            "runners": [
                {
                    "horse": "Mud Lover",
                    "or_rating": 90,
                    "form_string": "1",
                    "runs": [
                        {"position": 1, "days_ago": 21, "going": "Good to Soft"},
                        {"position": 2, "days_ago": 75, "going": "Soft"},
                    ],
                },
                {
                    "horse": "Fast Ground Fan",
                    "or_rating": 90,
                    "form_string": "1",
                    "runs": [
                        {"position": 5, "days_ago": 21, "going": "Firm"},
                    ],
                },
            ],
        }
        ranked = score_race(race, config)["ranked_runners"]
        mud_lover = next(r for r in ranked if r["horse"] == "Mud Lover")
        assert mud_lover["raw_signal_values"]["going_fit"] > 50
        assert "going_fit" in mud_lover["score_breakdown"]
        assert mud_lover["going_data"] == "sufficient"

    def test_insufficient_going_history_is_flagged(self, config):
        result = score_runner(
            {"horse": "Unknown Ground", "or_rating": 80, "runs": []},
            {"race_id": "r1", "course": "Epsom", "distance_furlongs": 8, "going": "Good"},
            config,
        )
        assert result["going_data"] == "insufficient"
        assert result["raw_signals"]["going_fit"] == 35.0
        assert "going_data_insufficient" in result["missing_data_flags"]

    def test_explicit_none_going_is_neutral_not_flagged(self, config):
        result = score_runner(
            {"horse": "No Forecast", "or_rating": 80, "runs": []},
            {"race_id": "r1", "course": "Epsom", "distance_furlongs": 8, "going": None},
            config,
        )
        assert result["going_data"] == "not_applicable"
        assert result["raw_signals"]["going_fit"] == 50.0
        assert "going_data_insufficient" not in result["missing_data_flags"]

    def test_unavailable_going_history_is_true_neutral(self, config):
        result = score_runner(
            {
                "horse": "SL Import",
                "or_rating": 80,
                "going_history": [],
                "going_history_source": "not_available",
            },
            {"race_id": "r1", "course": "Epsom", "distance_furlongs": 8, "going": "Good"},
            config,
        )
        assert result["going_data"] == "source_unavailable"
        assert result["raw_signals"]["going_fit"] == 50.0
        assert "going_data_source_unavailable" in result["missing_data_flags"]
        assert "going_data_insufficient" not in result["missing_data_flags"]

    def test_null_import_ratings_and_prices_score_without_exception(self, config):
        race = {
            "race_id": "null-import",
            "course": "Ascot",
            "course_slug": "ascot",
            "distance_furlongs": 6,
            "going": "Good",
            "runners": [
                {
                    "horse": "Null One",
                    "rpr": None,
                    "ts": None,
                    "or": 85,
                    "morning_price": None,
                    "form_string": "1",
                    "going_history": [],
                    "going_history_source": "not_available",
                },
                {
                    "horse": "Null Two",
                    "rpr": None,
                    "ts": None,
                    "or": 80,
                    "morning_price": None,
                    "form_string": "2",
                    "going_history": [],
                    "going_history_source": "not_available",
                },
            ],
        }
        result = score_race(race, config, course="ascot")
        assert len(result["ranked_runners"]) == 2
        assert all(runner["morning_price"] is None for runner in result["ranked_runners"])


# ---------------------------------------------------------------------------
# Config sanity tests
# ---------------------------------------------------------------------------

class TestLoadDefaultConfig:

    def test_returns_dict(self):
        config = load_default_config()
        assert isinstance(config, dict), "load_default_config must return a dict"

    def test_has_required_keys(self):
        """Config must contain at minimum a weights section."""
        config = load_default_config()
        assert "weights" in config, "Config must have a 'weights' key"

    def test_weights_are_positive(self):
        config = load_default_config()
        for key, value in config.get("weights", {}).items():
            assert isinstance(value, (int, float)), f"Weight {key} must be numeric"
            assert value >= 0, f"Weight {key} must be non-negative"

    def test_going_fit_weight_present(self):
        config = load_default_config()
        # Rebalanced as new signals were added; kept near 0.10 to preserve
        # its role as a primary signal.
        assert config["weights"]["going_fit"] >= 0.099
        assert abs(sum(config["weights"].values()) - 1.0) < 0.001

    def test_equipment_weight_present(self):
        config = load_default_config()
        assert config["weights"]["equipment"] == pytest.approx(0.0250)
        assert abs(sum(config["weights"].values()) - 1.0) < 0.000001

    def test_pace_weight_present(self):
        config = load_default_config()
        assert "pace" in config["weights"]
        assert config["weights"]["pace"] > 0
