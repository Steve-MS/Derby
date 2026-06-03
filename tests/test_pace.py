"""Tests for the pace + extended draw-bias module."""

from src.pace import (
    EPSOM_DRAW_TABLE,
    extended_draw_signal,
    infer_run_style,
    pace_signal,
    project_race_pace,
)


class TestInferRunStyle:
    def test_explicit_override_wins(self):
        assert infer_run_style({"run_style": "led"}) == "LED"
        assert infer_run_style({"run_style": "HELD"}) == "HELD"

    def test_no_form_is_held(self):
        assert infer_run_style({}) == "HELD"
        assert infer_run_style({"form_string": ""}) == "HELD"

    def test_front_running_form_is_prom(self):
        # consistent 1-2 finishes => PROM
        assert infer_run_style({"form_string": "112211"}) == "PROM"

    def test_tail_form_is_held(self):
        # consistent 0s (unplaced) => HELD
        assert infer_run_style({"form_string": "000080"}) == "HELD"

    def test_mid_pack_form(self):
        assert infer_run_style({"form_string": "3454"}) == "MID"


class TestProjectRacePace:
    def test_no_pace_when_all_held(self):
        runners = [{"form_string": "0000"}, {"form_string": "0900"}]
        assert project_race_pace(runners) == "NO_PACE"

    def test_lone_leader(self):
        runners = [
            {"form_string": "11122"},  # PROM
            {"form_string": "0000"},
            {"form_string": "0000"},
            {"form_string": "5566"},
            {"form_string": "5566"},
            {"form_string": "5566"},
            {"form_string": "5566"},
        ]
        assert project_race_pace(runners) == "LONE_LEAD"

    def test_duel(self):
        runners = [
            {"form_string": "111"},
            {"form_string": "221"},
            {"form_string": "1212"},
            {"form_string": "55"},
        ]
        assert project_race_pace(runners) == "DUEL"

    def test_empty_field_does_not_crash(self):
        assert project_race_pace([]) == "NO_PACE"


class TestPaceSignal:
    def test_lone_leader_helps_front_runner(self):
        runner = {"form_string": "1122"}  # PROM
        assert pace_signal(runner, "LONE_LEAD") > pace_signal(runner, "DUEL")

    def test_duel_helps_closer(self):
        held = {"form_string": "0000"}
        assert pace_signal(held, "DUEL") > pace_signal(held, "LONE_LEAD")

    def test_signal_in_range(self):
        for pace in ("LONE_LEAD", "DUEL", "EVEN", "NO_PACE"):
            for style in ({"form_string": "1122"}, {"form_string": "0000"}, {}):
                s = pace_signal(style, pace)
                assert 0 <= s <= 100

    def test_unknown_pace_is_neutral(self):
        assert pace_signal({"form_string": "1"}, "UNKNOWN_PACE") == 50.0


class TestExtendedDrawSignal:
    def _race(self, **over):
        base = {
            "course": "Epsom",
            "distance_f": 5.0,
            "going": "good",
            "runners": [{}] * 10,
        }
        base.update(over)
        return base

    def test_non_epsom_returns_none(self):
        assert extended_draw_signal({"draw": 1}, {"course": "Ascot", "distance_f": 5.0}) is None

    def test_unknown_distance_returns_none(self):
        assert extended_draw_signal({"draw": 1}, self._race(distance_f=99.0)) is None

    def test_5f_quick_low_draw_favoured(self):
        low = extended_draw_signal({"draw": 1}, self._race())
        high = extended_draw_signal({"draw": 14}, self._race())
        assert low is not None and high is not None
        assert low > high
        assert low > 60  # strongly positive
        assert high < 40  # strongly negative

    def test_5f_soft_going_neutral(self):
        # going_filter excludes soft -> neutral 50
        s = extended_draw_signal({"draw": 1}, self._race(going="soft"))
        assert s == 50.0

    def test_derby_trip_minimal_bias(self):
        # 12f at Epsom -> low/high should be very close to 50
        low = extended_draw_signal({"draw": 1}, self._race(distance_f=12.0, runners=[{}]*14))
        high = extended_draw_signal({"draw": 18}, self._race(distance_f=12.0, runners=[{}]*14))
        assert abs(low - high) < 10  # minor difference only

    def test_no_draw_returns_neutral(self):
        assert extended_draw_signal({}, self._race()) == 50.0

    def test_small_field_dampens_bias(self):
        big = extended_draw_signal({"draw": 1}, self._race(runners=[{}]*12))
        small = extended_draw_signal({"draw": 1}, self._race(runners=[{}]*3))
        # small field should pull the signal closer to 50
        assert abs(small - 50) < abs(big - 50)


class TestEpsomDrawTableShape:
    def test_all_entries_have_required_keys(self):
        required = {"low", "mid", "high", "low_threshold", "high_threshold",
                    "field_size_pivot", "going_filter"}
        for key, val in EPSOM_DRAW_TABLE.items():
            assert required.issubset(val.keys()), f"{key} missing keys"
            assert 0 <= val["low"] <= 100
            assert 0 <= val["high"] <= 100
