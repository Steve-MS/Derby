from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_script(script_name: str, *args: str) -> dict:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / script_name), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_racingpost_ascot_dry_run_uses_configured_course_id_and_path() -> None:
    plan = _run_script(
        "scrape_racingpost.py",
        "--course=ascot",
        "--meeting=royal-ascot-2026",
        "--date=2026-06-16",
        "--dry-run",
    )

    assert plan["url"] == "https://www.racingpost.com/racecards/1/ascot/2026-06-16"
    assert plan["output_path"] == str(Path("data") / "enrichment" / "racingpost-ascot-2026-06-16.json")
    assert plan["dry_run"] is True


def test_sportinglife_ascot_dry_run_uses_configured_aliases_and_path() -> None:
    plan = _run_script(
        "scrape_sportinglife.py",
        "--course=ascot",
        "--meeting=royal-ascot-2026",
        "--date=2026-06-16",
        "--dry-run",
    )

    assert plan["url"] == "https://www.sportinglife.com/racing/racecards/2026-06-16/ascot"
    assert "ascot" in plan["course_aliases"]
    assert plan["output_path"] == str(Path("data") / "enrichment" / "sportinglife-ascot-2026-06-16.json")
    assert plan["dry_run"] is True


def test_racingpost_no_course_flag_defaults_to_epsom_legacy_path() -> None:
    plan = _run_script("scrape_racingpost.py", "--date=2026-06-08", "--dry-run")

    assert plan["url"] == "https://www.racingpost.com/racecards/17/epsom/2026-06-08"
    assert plan["output_path"] == str(Path("data") / "enrichment" / "racingpost-2026-06-08.json")


def test_sportinglife_no_course_flag_defaults_to_epsom_alias_path() -> None:
    plan = _run_script("scrape_sportinglife.py", "--date=2026-06-08", "--dry-run")

    assert plan["url"] == "https://www.sportinglife.com/racing/racecards/2026-06-08/epsom-downs"
    assert "epsom downs" in plan["course_aliases"]
    assert plan["output_path"] == str(Path("data") / "enrichment" / "sportinglife-2026-06-08.json")


def test_morning_odds_non_epsom_market_path_is_course_prefixed() -> None:
    import scripts.morning_odds as morning_odds

    assert morning_odds.market_output_path("baseline", "epsom") == REPO_ROOT / "data" / "enrichment" / "market-baseline.json"
    assert morning_odds.market_output_path("latest", "ascot") == REPO_ROOT / "data" / "enrichment" / "market-latest-ascot.json"


def test_refresh_no_date_uses_meeting_days_for_non_default_course() -> None:
    import scripts.refresh_friday as refresh_friday

    assert refresh_friday.resolve_refresh_dates("epsom", "derby-2026", None) == ["2026-06-05", "2026-06-06"]
    assert refresh_friday.resolve_refresh_dates("ascot", "royal-ascot-2026", None) == [
        "2026-06-16",
        "2026-06-17",
        "2026-06-18",
        "2026-06-19",
        "2026-06-20",
    ]
