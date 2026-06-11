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


def _run_deprecated_script(script_name: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / script_name)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        env=env,
    )


def test_racingpost_scraper_is_deprecated_for_import_only_release() -> None:
    result = _run_deprecated_script("scrape_racingpost.deprecated.py")

    assert result.returncode != 0
    assert "deprecated" in result.stderr.lower()


def test_sportinglife_scraper_is_deprecated_for_import_only_release() -> None:
    result = _run_deprecated_script("scrape_sportinglife.deprecated.py")

    assert result.returncode != 0
    assert "deprecated" in result.stderr.lower()


def test_live_scraper_entrypoints_are_not_present() -> None:
    assert not (REPO_ROOT / "scripts" / "scrape_racingpost.py").exists()
    assert not (REPO_ROOT / "scripts" / "scrape_sportinglife.py").exists()


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
