import json
import re
from pathlib import Path

import pytest

from src.sl_parser import (
    SLParseError,
    SLValidationError,
    extract_next_data,
    parse_sl_html_to_raw,
    validate_html_import,
)

FIXTURE = Path(__file__).parent / "fixtures" / "sportinglife" / "sample-meeting.html"


def _fixture_html() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def test_parse_fixture_to_canonical_raw_shape():
    raw = parse_sl_html_to_raw(_fixture_html(), "ascot", "royal-ascot-2026", "2026-06-16")

    assert len(raw["races"]) > 0
    runner_count = sum(len(race["runners"]) for race in raw["races"])
    assert runner_count > 0
    assert raw["going_source"] == "sporting_life"
    assert raw["source_urls"]

    for race in raw["races"]:
        assert race["off_time"]
        assert race["name"]
        assert race["distance_f"]
        for runner in race["runners"]:
            if not runner.get("withdrawn", False):
                assert runner["horse"]
            assert runner["rpr"] is None
            assert runner["ts"] is None
            assert runner["going_history"] == []
            assert runner["going_history_source"] == "not_available"

    validate_html_import(_fixture_html(), raw)


def test_validation_rejects_empty_html():
    with pytest.raises(SLValidationError, match="below 10 KB"):
        validate_html_import("", {"races": []})


def test_parse_rejects_html_without_next_data():
    html = "<html><body>" + ("x" * 12000) + "</body></html>"
    with pytest.raises(SLParseError, match="__NEXT_DATA__ not found"):
        parse_sl_html_to_raw(html, "ascot", "royal-ascot-2026", "2026-06-16")


def test_validation_rejects_empty_races_from_mutated_fixture():
    html = _fixture_html()
    data = extract_next_data(html)
    data["props"]["pageProps"]["race"] = {}
    data["props"]["pageProps"]["meeting"][0]["races"] = []
    mutated_json = json.dumps(data, separators=(",", ":"))
    mutated = re.sub(
        r'(<script[^>]*\bid=["\']__NEXT_DATA__["\'][^>]*>)(.*?)(</script>)',
        lambda match: match.group(1) + mutated_json + match.group(3),
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    raw = parse_sl_html_to_raw(mutated, "ascot", "royal-ascot-2026", "2026-06-16")

    with pytest.raises(SLValidationError, match="parsed races are empty"):
        validate_html_import(mutated, raw)
