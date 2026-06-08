import pytest

from src.cd_form import cd_form_signal
from src.course_config import CourseConfigError, load_course_config, scoring_priors_for
from src.pace import extended_draw_signal, pace_signal
from src.scoring import load_default_config, score_runner
from src.trial_form import score_trial_form


def test_epsom_draw_and_cd_use_extracted_json_priors():
    priors = load_course_config("epsom")["scoring_priors"]
    draw_cfg = priors["draw_bias"]["extended"]["5.0"]
    race = {"course": "Epsom", "course_slug": "epsom", "distance_f": 5.0, "going": "good", "runners": [{}] * draw_cfg["field_size_pivot"]}
    assert extended_draw_signal({"draw": 1}, race) == pytest.approx(float(draw_cfg["low"]))

    badge_scores = priors["cd_form_weights"]["badge_scores"]
    assert cd_form_signal({"notes": "badges CD; source RP"}, race) == pytest.approx(float(badge_scores["CD"]))
    assert cd_form_signal({"notes": "badges BF; source RP"}, race) == pytest.approx(float(badge_scores["BF"]))


def test_ascot_priors_are_neutral_for_draw_cd_pace_and_trial_form():
    cfg = load_default_config()
    runner = {
        "horse": "Neutral Runner",
        "rpr": 100,
        "form_string": "111",
        "draw": 1,
        "first_time_epsom": True,
        "notes": "badges CD; source RP",
    }
    race_low = {"race_id": "ascot-low", "course": "Ascot", "course_slug": "ascot", "distance_f": 5.0, "going": "good", "runners": [runner]}
    race_high = {"race_id": "ascot-high", "course": "Ascot", "course_slug": "ascot", "distance_f": 12.0, "going": "good", "runners": [{**runner, "draw": 20}]}

    low = score_runner(runner, race_low, cfg, course="ascot")
    high = score_runner({**runner, "draw": 20}, race_high, cfg, course="ascot")

    assert low["raw_signals"]["draw_bias"] == 50.0
    assert high["raw_signals"]["draw_bias"] == 50.0
    assert low["raw_signals"]["course_distance"] == 50.0
    assert high["raw_signals"]["course_distance"] == 50.0
    assert low["raw_signals"]["trial_form"] == 50.0
    assert high["raw_signals"]["trial_form"] == 50.0
    assert low["raw_score"] == pytest.approx(high["raw_score"])
    assert pace_signal({"run_style": "LED"}, "LONE_LEAD", course="ascot") == 50.0
    assert score_trial_form("Trial Horse", 12.0, {"Trial Horse": {"trials": [{"race": "Dante Stakes", "tier": 1, "date": "2026-05-14", "position": 1, "beaten_lengths": 0.0}] }}, course="ascot") == 50.0


def test_missing_course_raises_course_config_error():
    with pytest.raises(CourseConfigError):
        scoring_priors_for("missing-course")


def test_known_course_missing_scoring_priors_falls_back_to_neutral(monkeypatch):
    def fake_load(course_slug):
        return {"course_slug": course_slug}

    monkeypatch.setattr("src.course_config.load_course_config", fake_load)
    priors = scoring_priors_for("minimal")
    assert priors["draw_bias"]["extended"] == {}
    assert priors["pace_modifiers"]["default_signal"] == 50
    assert priors["cd_form_weights"]["badge_scores"]["CD"] == 50
    assert priors["trial_form_weights"]["enabled"] is False
