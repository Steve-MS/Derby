from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scripts.morning_odds as morning_odds  # noqa: E402


def test_dry_run_without_credentials_does_not_fail(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fail_gate() -> None:
        raise AssertionError("dry-run must not require Sporting Life credentials")

    def fake_build_snapshot(**kwargs: object) -> dict[str, object]:
        dates = kwargs["dates"]
        assert dates == ["2026-06-16"]
        return {"horses": {"Northbank Verse": {"race_date": "2026-06-16"}}}

    monkeypatch.delenv("SPORTINGLIFE_USER", raising=False)
    monkeypatch.delenv("SPORTINGLIFE_PASS", raising=False)
    monkeypatch.setattr(morning_odds, "_gate_env", fail_gate)
    monkeypatch.setattr(morning_odds, "build_snapshot", fake_build_snapshot)
    monkeypatch.setattr(morning_odds, "market_output_path", lambda _mode, _course: tmp_path / "market.json")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "morning_odds.py",
            "--course=ascot",
            "--meeting=royal-ascot-2026",
            "--date=2026-06-16",
            "--dry-run",
        ],
    )

    assert morning_odds.main() == 0
    assert not (tmp_path / "market.json").exists()
