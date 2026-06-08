from __future__ import annotations

import sys
from datetime import date as date_cls
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from src import course_config  # noqa: E402
from src.course_config import (  # noqa: E402
    CourseConfigError,
    default_course,
    default_meeting,
    load_course_config,
    path_for,
    resolve_day,
)


def test_load_epsom_config_successfully() -> None:
    cfg = load_course_config("epsom")

    assert cfg["course_slug"] == "epsom"
    assert cfg["display_name"] == "Epsom"
    assert cfg["racingpost"]["course_id"] == 17
    assert "derby-2026" in cfg["meetings"]


def test_load_ascot_config_successfully() -> None:
    cfg = load_course_config("ascot")

    assert cfg["course_slug"] == "ascot"
    assert cfg["display_name"] == "Ascot"
    assert cfg["racingpost"]["course_id"] is None
    assert list(cfg["meetings"]["royal-ascot-2026"]["days"]) == [
        "2026-06-16",
        "2026-06-17",
        "2026-06-18",
        "2026-06-19",
        "2026-06-20",
    ]


def test_missing_course_raises_course_config_error() -> None:
    with pytest.raises(CourseConfigError, match="course config not found"):
        load_course_config("missing-course")


def test_missing_config_file_raises_course_config_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(course_config, "CONFIG_DIR", tmp_path)

    with pytest.raises(CourseConfigError, match="course config not found"):
        load_course_config("epsom")


def test_missing_required_field_raises_course_config_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg_dir = tmp_path / "courses"
    cfg_dir.mkdir()
    (cfg_dir / "broken.json").write_text('{"course_slug": "broken"}', encoding="utf-8")
    monkeypatch.setattr(course_config, "CONFIG_DIR", cfg_dir)

    with pytest.raises(CourseConfigError, match="missing required field"):
        load_course_config("broken")


def test_path_for_returns_epsom_legacy_paths() -> None:
    assert path_for("epsom", "2026-06-06", "raw-racecards") == REPO_ROOT / "data" / "raw" / "epsom-2026-06-06-racecards.json"
    assert path_for("epsom", "2026-06-06", "scores") == REPO_ROOT / "outputs" / "scores-2026-06-06.json"
    assert path_for("epsom", "2026-06-06", "bets") == REPO_ROOT / "outputs" / "bets-2026-06-06.json"
    assert path_for("epsom", "2026-06-06", "report") == REPO_ROOT / "outputs" / "report-2026-06-06.html"
    assert path_for("epsom", "2026-06-06", "racecard") == REPO_ROOT / "outputs" / "racecard-2026-06-06.html"
    assert path_for("epsom", "2026-06-06", "slip") == REPO_ROOT / "outputs" / "slip-2026-06-06.txt"
    assert path_for("epsom", "2026-06-06", "enrichment-going") == REPO_ROOT / "data" / "enrichment" / "going-2026-06-06.json"
    assert path_for("epsom", "2026-06-06", "results") == REPO_ROOT / "data" / "results" / "results-2026-06-06.json"


def test_path_for_returns_ascot_course_prefixed_paths() -> None:
    assert path_for("ascot", "2026-06-16", "raw-racecards") == REPO_ROOT / "data" / "raw" / "ascot-2026-06-16-racecards.json"
    assert path_for("ascot", "2026-06-16", "scores") == REPO_ROOT / "outputs" / "scores-ascot-2026-06-16.json"
    assert path_for("ascot", "2026-06-16", "bets") == REPO_ROOT / "outputs" / "bets-ascot-2026-06-16.json"
    assert path_for("ascot", "2026-06-16", "report") == REPO_ROOT / "outputs" / "report-ascot-2026-06-16.html"
    assert path_for("ascot", "2026-06-16", "racecard") == REPO_ROOT / "outputs" / "racecard-ascot-2026-06-16.html"
    assert path_for("ascot", "2026-06-16", "slip") == REPO_ROOT / "outputs" / "slip-ascot-2026-06-16.txt"
    assert path_for("ascot", "2026-06-16", "enrichment-going") == REPO_ROOT / "data" / "enrichment" / "going-ascot-2026-06-16.json"
    assert path_for("ascot", "2026-06-16", "results") == REPO_ROOT / "data" / "results" / "results-ascot-2026-06-16.json"


def test_resolve_day_returns_correct_metadata() -> None:
    cfg = load_course_config("epsom")

    assert resolve_day(cfg, "derby-2026", "2026-06-05") == {
        "label": "Ladies / Oaks Day",
        "going_key": "friday",
    }


def test_resolve_day_unknown_date_raises_course_config_error() -> None:
    cfg = load_course_config("epsom")

    with pytest.raises(CourseConfigError, match="unknown date"):
        resolve_day(cfg, "derby-2026", "2026-06-08")


def test_src_cli_course_defaults_use_epsom_derby_today() -> None:
    from src.cli import build_parser

    args = build_parser().parse_args(["score"])

    assert args.course == default_course()
    assert args.meeting == default_meeting()
    assert args.date == date_cls.today().isoformat()


def test_t60_cli_course_defaults_use_epsom_derby_today(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.t60_watchdog as t60_watchdog

    seen: dict[str, str] = {}

    def fake_run_watchdog(race_date: str, **kwargs: str) -> int:
        seen["date"] = race_date
        seen["course"] = kwargs["course_slug"]
        seen["meeting"] = kwargs["meeting_slug"]
        return 0

    monkeypatch.setattr(t60_watchdog, "run_watchdog", fake_run_watchdog)

    assert t60_watchdog.main([]) == 0
    assert seen == {
        "date": date_cls.today().isoformat(),
        "course": default_course(),
        "meeting": default_meeting(),
    }
