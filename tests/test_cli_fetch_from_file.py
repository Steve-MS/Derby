import json
import re
from pathlib import Path

from src import cli
from src.sl_parser import extract_next_data

FIXTURE = Path(__file__).parent / "fixtures" / "sportinglife" / "sample-meeting.html"


def _replace_next_data(html: str, data: dict) -> str:
    next_json = json.dumps(data, separators=(",", ":"))
    return re.sub(
        r'(<script[^>]*\bid=["\']__NEXT_DATA__["\'][^>]*>)(.*?)(</script>)',
        lambda match: match.group(1) + next_json + match.group(3),
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )


def _single_complete_race_file(tmp_path: Path) -> Path:
    html = FIXTURE.read_text(encoding="utf-8")
    data = extract_next_data(html)
    page_props = data["props"]["pageProps"]
    page_props["meeting"][0]["races"] = [page_props["race"]["race_summary"]]
    complete = tmp_path / "single-complete-race.html"
    complete.write_text(_replace_next_data(html, data), encoding="utf-8")
    return complete


def test_fetch_from_file_rejects_partial_import_without_clobbering_raw(monkeypatch, tmp_path, capsys):
    raw_path = tmp_path / "ascot-2026-06-16-racecards.json"
    raw_path.write_text("sentinel", encoding="utf-8")

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
        "--from-file", str(FIXTURE),
    ])

    assert args.func(args) == 1
    stderr = capsys.readouterr().err
    assert "Partial import detected" in stderr
    assert "click each race to expand its full racecard" in stderr
    assert "re-save the page and retry" in stderr
    assert raw_path.read_text(encoding="utf-8") == "sentinel"
    assert not Path(f"{raw_path}.tmp").exists()


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
    complete_fixture = _single_complete_race_file(tmp_path)
    fetch_args = parser.parse_args([
        "fetch",
        "--course", "ascot",
        "--meeting", "royal-ascot-2026",
        "--date", "2026-06-16",
        "--from-file", str(complete_fixture),
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
