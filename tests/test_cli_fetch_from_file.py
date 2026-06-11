import json
from pathlib import Path

from src import cli

FIXTURE = Path(__file__).parent / "fixtures" / "sportinglife" / "sample-meeting.html"


def test_fetch_from_file_writes_raw_and_scores(monkeypatch, tmp_path):
    raw_path = tmp_path / "ascot-2026-06-16-racecards.json"
    scores_path = tmp_path / "scores-ascot-2026-06-16.json"

    def fake_artifact_path(args, kind):
        if kind == "raw-racecards":
            return raw_path
        if kind == "scores":
            return scores_path
        return tmp_path / f"{kind}.json"

    monkeypatch.setattr(cli, "_artifact_path", fake_artifact_path)
    parser = cli.build_parser()
    fetch_args = parser.parse_args([
        "fetch",
        "--course", "ascot",
        "--meeting", "royal-ascot-2026",
        "--date", "2026-06-16",
        "--from-file", str(FIXTURE),
    ])
    assert fetch_args.func(fetch_args) == 0
    assert raw_path.exists()

    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    assert raw["races"]

    score_args = parser.parse_args([
        "score",
        "--course", "ascot",
        "--meeting", "royal-ascot-2026",
        "--date", "2026-06-16",
    ])
    assert score_args.func(score_args) == 0
    scores = json.loads(scores_path.read_text(encoding="utf-8"))
    assert scores["races"]
    assert scores["races"][0]["ranked_runners"]


def test_fetch_from_file_failure_does_not_clobber_existing_raw(monkeypatch, tmp_path):
    raw_path = tmp_path / "ascot-2026-06-16-racecards.json"
    raw_path.write_text("sentinel", encoding="utf-8")
    bad_html = tmp_path / "bad.html"
    bad_html.write_text("<html>no next data</html>", encoding="utf-8")

    def fake_artifact_path(args, kind):
        if kind == "raw-racecards":
            return raw_path
        return tmp_path / f"{kind}.json"

    monkeypatch.setattr(cli, "_artifact_path", fake_artifact_path)
    args = cli.build_parser().parse_args([
        "fetch",
        "--course", "ascot",
        "--meeting", "royal-ascot-2026",
        "--date", "2026-06-16",
        "--from-file", str(bad_html),
    ])

    assert args.func(args) == 1
    assert raw_path.read_text(encoding="utf-8") == "sentinel"
    assert not Path(f"{raw_path}.tmp").exists()
