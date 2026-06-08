from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

DATE = "2026-06-08"
REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "t60_watchdog.py"


def _write(path: Path, content: str, mtime: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    os.utime(path, (mtime, mtime))


def _write_json(path: Path, data: dict, mtime: float, pad_to: int | None = None) -> None:
    text = json.dumps(data, indent=2)
    if pad_to and len(text.encode("utf-8")) < pad_to:
        data = {**data, "padding": "x" * (pad_to - len(text.encode("utf-8")))}
        text = json.dumps(data, indent=2)
    _write(path, text, mtime)


def _base_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "SPORTINGLIFE_USER": "race-day-user",
            "SPORTINGLIFE_PASS": "race-day-pass",
            "ATR_COOKIE_FILE": "race-day-cookie-file",
            "RACING_API_KEY": "race-day-api-key",
            "PYTHONIOENCODING": "utf-8",
        }
    )
    return env


def _build_fixture(root: Path) -> None:
    now = time.time()
    raw_time = now - 60 * 60
    enrich_time = now - 45 * 60
    scores_time = now - 30 * 60
    bets_time = now - 20 * 60
    report_time = now - 10 * 60
    racecard_time = now - 5 * 60
    slip_time = now - 4 * 60

    raw = {
        "meeting": "Epsom",
        "date": DATE,
        "races": [
            {
                "off_time": "13:30",
                "name": "Fixture Stakes",
                "runners": [
                    {"horse": "Fast Horse"},
                    {"horse": "Place Horse"},
                    {"horse": "Box One"},
                    {"horse": "Box Two"},
                    {"horse": "Box Three"},
                ],
            }
        ],
    }
    _write_json(root / "data" / "raw" / f"epsom-{DATE}-racecards.json", raw, raw_time)

    live = {
        "fetched_at": f"{DATE}T09:00:00+01:00",
        "races": [
            {
                "time": "13:30",
                "status": "verified",
                "runners": [
                    {"name": "Fast Horse"},
                    {"name": "Place Horse"},
                    {"name": "Box One"},
                    {"name": "Box Two"},
                    {"name": "Box Three"},
                ],
                "non_runners_excluded": ["Scratched Horse (NR)"],
            }
        ],
    }
    _write_json(root / "data" / "enrichment" / f"live-runners-{DATE}.json", live, enrich_time)
    _write_json(root / "data" / "enrichment" / f"sportinglife-{DATE}.json", {"success": True}, enrich_time, pad_to=1400)
    _write_json(root / "data" / "enrichment" / f"racingpost-{DATE}.json", {"success": True}, enrich_time)
    _write_json(root / "data" / "enrichment" / f"going-{DATE}.json", {"going": "Good"}, enrich_time)
    _write_json(root / "outputs" / f"scores-{DATE}.json", {"races": []}, scores_time)

    bets = {
        "meta": {"card_date": DATE, "course": "Epsom", "validation": "GO"},
        "total_outlay_gbp": 7.5,
        "bets": [
            {
                "race_time": "13:30",
                "race_name": "Fixture Stakes",
                "pick": "Fast Horse",
                "status": "WIN",
                "stake_guidance": "£1.00 WIN",
            },
            {
                "race_time": "13:30",
                "race_name": "Fixture Stakes",
                "pick": "Place Horse",
                "status": "EW",
                "stake_guidance": "£0.25 EW",
            },
            {
                "race_time": "13:30",
                "race_name": "Fixture Stakes",
                "pick": "TRIFECTA BOX: [Box One, Box Two, Box Three]",
                "status": "TRIFECTA",
                "total_stake": "£6.00",
                "horses": [
                    {"horse": "Box One"},
                    {"horse": "Box Two"},
                    {"horse": "Box Three"},
                ],
            },
        ],
    }
    _write_json(root / "outputs" / f"bets-{DATE}.json", bets, bets_time)
    _write(root / "outputs" / f"report-{DATE}.html", "<html>report</html>", report_time)
    _write(
        root / "outputs" / f"racecard-{DATE}.html",
        "<html><header>WIN/EW outlay: £1.50 (+ £6.00 trifecta = £7.50)</header>"
        "<body>Fast Horse Place Horse Box One Box Two Box Three</body></html>",
        racecard_time,
    )
    _write(
        root / "outputs" / f"slip-{DATE}.txt",
        "Fast Horse £1.00\nPlace Horse £0.25\nBox One\nBox Two\nBox Three\nTrifecta £6.00\n",
        slip_time,
    )


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--date", DATE],
        cwd=root,
        env=_base_env(),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )


def _touch_minutes_ago(path: Path, minutes: int) -> None:
    stamp = time.time() - minutes * 60
    os.utime(path, (stamp, stamp))


def _write_json_fixture(path: Path, data: dict, minutes_ago: int) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    _touch_minutes_ago(path, minutes_ago)


def _add_same_horse_two_races(root: Path) -> None:
    raw_path = root / "data" / "raw" / f"epsom-{DATE}-racecards.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    raw["races"][0]["runners"].append({"horse": "Shared Horse"})
    raw["races"].append(
        {
            "off_time": "14:00",
            "name": "Second Fixture Stakes",
            "runners": [{"horse": "Shared Horse"}, {"horse": "Second Rival"}],
        }
    )
    _write_json_fixture(raw_path, raw, 60)

    live_path = root / "data" / "enrichment" / f"live-runners-{DATE}.json"
    live = json.loads(live_path.read_text(encoding="utf-8"))
    live["races"][0]["non_runners_excluded"].append("Shared Horse (NR in Fixture Stakes)")
    live["races"].append(
        {
            "time": "14:00",
            "name": "Second Fixture Stakes",
            "status": "verified",
            "runners": [{"name": "Shared Horse"}, {"name": "Second Rival"}],
            "non_runners_excluded": [],
        }
    )
    _write_json_fixture(live_path, live, 45)


def _set_first_bet(root: Path, horse: str, race_time: str, race_name: str) -> None:
    bets_path = root / "outputs" / f"bets-{DATE}.json"
    bets = json.loads(bets_path.read_text(encoding="utf-8"))
    bets["bets"][0]["pick"] = horse
    bets["bets"][0]["race_time"] = race_time
    bets["bets"][0]["race_name"] = race_name
    _write_json_fixture(bets_path, bets, 20)

    racecard_path = root / "outputs" / f"racecard-{DATE}.html"
    racecard_path.write_text(
        "<html><header>WIN/EW outlay: £1.50 (+ £6.00 trifecta = £7.50)</header>"
        f"<body>{horse} Place Horse Box One Box Two Box Three</body></html>",
        encoding="utf-8",
    )
    _touch_minutes_ago(racecard_path, 5)

    slip_path = root / "outputs" / f"slip-{DATE}.txt"
    slip_path.write_text(
        f"{horse} £1.00\nPlace Horse £0.25\nBox One\nBox Two\nBox Three\nTrifecta £6.00\n",
        encoding="utf-8",
    )
    _touch_minutes_ago(slip_path, 4)


def test_missing_artifact_exits_2(tmp_path: Path) -> None:
    _build_fixture(tmp_path)
    (tmp_path / "data" / "enrichment" / f"going-{DATE}.json").unlink()

    result = _run(tmp_path)

    assert result.returncode == 2
    assert "MISSING" in result.stdout
    assert "DO NOT RUN PIPELINE" in result.stdout


def test_stale_artifact_exits_1(tmp_path: Path) -> None:
    _build_fixture(tmp_path)
    stale = time.time() - 25 * 60 * 60
    raw_path = tmp_path / "data" / "raw" / f"epsom-{DATE}-racecards.json"
    os.utime(raw_path, (stale, stale))

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "STALE" in result.stdout
    assert "REVIEW BEFORE PROCEEDING" in result.stdout


def test_all_present_and_consistent_exits_0(tmp_path: Path) -> None:
    _build_fixture(tmp_path)

    result = _run(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "T-60 CLEAR" in result.stdout
    manifest = json.loads((tmp_path / "outputs" / f"t60-status-{DATE}.json").read_text(encoding="utf-8"))
    assert manifest["courses"] == ["epsom"]
    assert manifest["exit_code"] == 0


def test_bets_total_mismatch_exits_2_with_inconsistent_marker(tmp_path: Path) -> None:
    _build_fixture(tmp_path)
    bets_path = tmp_path / "outputs" / f"bets-{DATE}.json"
    bets = json.loads(bets_path.read_text(encoding="utf-8"))
    bets["total_outlay_gbp"] = 99.0
    bets_path.write_text(json.dumps(bets), encoding="utf-8")

    result = _run(tmp_path)

    assert result.returncode == 2
    assert "INCONSISTENT" in result.stdout
    assert "declared GBP 99.00 != computed GBP 7.50" in result.stdout


def test_sportinglife_spa_shell_detection_exits_2(tmp_path: Path) -> None:
    _build_fixture(tmp_path)
    sport = tmp_path / "data" / "enrichment" / f"sportinglife-{DATE}.json"
    sport.write_text("{" + "x" * 371 + "}", encoding="utf-8")

    result = _run(tmp_path)

    assert result.returncode == 2
    assert "INCONSISTENT" in result.stdout
    assert "SPA-shell" in result.stdout


def test_race_scoped_nr_in_bet_race_exits_2_when_active_elsewhere(tmp_path: Path) -> None:
    _build_fixture(tmp_path)
    _add_same_horse_two_races(tmp_path)
    _set_first_bet(tmp_path, "Shared Horse", "13:30", "Fixture Stakes")

    result = _run(tmp_path)

    assert result.returncode == 2
    assert "bet horse marked NR/VOID in live-runners for race 13:30: Shared Horse" in result.stdout


def test_race_scoped_active_in_bet_race_stays_ok_when_nr_elsewhere(tmp_path: Path) -> None:
    _build_fixture(tmp_path)
    _add_same_horse_two_races(tmp_path)
    _set_first_bet(tmp_path, "Shared Horse", "14:00", "Second Fixture Stakes")

    result = _run(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "bet horse marked NR/VOID" not in result.stdout


def test_race_scoped_nr_in_same_race_exits_2(tmp_path: Path) -> None:
    _build_fixture(tmp_path)
    live_path = tmp_path / "data" / "enrichment" / f"live-runners-{DATE}.json"
    live = json.loads(live_path.read_text(encoding="utf-8"))
    live["races"][0]["runners"] = [r for r in live["races"][0]["runners"] if r["name"] != "Fast Horse"]
    live["races"][0]["non_runners_excluded"].append("Fast Horse (NR)")
    _write_json_fixture(live_path, live, 45)

    result = _run(tmp_path)

    assert result.returncode == 2
    assert "bet horse marked NR/VOID in live-runners for race 13:30: Fast Horse" in result.stdout


def test_render_header_mismatch_exits_2_with_header_marker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.t60_watchdog as t60_watchdog
    import src.report as report

    _build_fixture(tmp_path)
    for key, value in _base_env().items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(report, "render_header", lambda _bets: {"total_outlay": 99.0})

    code = t60_watchdog.run_watchdog(DATE, root=tmp_path)

    assert code == 2
    manifest = json.loads((tmp_path / "outputs" / f"t60-status-{DATE}.json").read_text(encoding="utf-8"))
    rows = {row["artifact"]: row for row in manifest["artifacts"]}
    assert rows["bets"]["severity"] == 0
    assert rows["header consistency"]["severity"] == 2
    assert "render_header total GBP 99.00 != computed GBP 7.50" in rows["header consistency"]["detail"]


def test_missing_bets_meta_degrades_without_crashing(tmp_path: Path) -> None:
    _build_fixture(tmp_path)
    bets_path = tmp_path / "outputs" / f"bets-{DATE}.json"
    bets = json.loads(bets_path.read_text(encoding="utf-8"))
    bets.pop("meta")
    bets_path.write_text(json.dumps(bets), encoding="utf-8")
    bets_time = time.time() - 20 * 60
    os.utime(bets_path, (bets_time, bets_time))

    result = _run(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "missing meta block" in result.stdout


def test_refresh_friday_watchdog_surfaces_env_and_missing_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    import scripts.refresh_friday as refresh_friday

    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir(parents=True)
    (scripts_dir / "t60_watchdog.py").write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
    (scripts_dir / "check_env.py").write_text((REPO_ROOT / "scripts" / "check_env.py").read_text(encoding="utf-8"), encoding="utf-8")

    monkeypatch.setattr(refresh_friday, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(refresh_friday, "DATES", [DATE])
    monkeypatch.setattr(refresh_friday, "PY", sys.executable)
    monkeypatch.setattr(sys, "argv", ["refresh_friday.py", "--skip-enrich"])
    for key in ("SPORTINGLIFE_USER", "SPORTINGLIFE_PASS"):
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(SystemExit):
        refresh_friday.main()

    out = capfd.readouterr().out
    assert "[T-60] Running artifact watchdog" in out
    assert "racecards" in out
    assert "MISSING" in out
    assert "check_env failed" in out
    assert "SPORTINGLIFE_USER" in out
