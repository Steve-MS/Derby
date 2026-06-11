"""Sporting Life saved-HTML importer.

Parses a locally saved Sporting Life racecard page into the canonical raw
racecard JSON consumed by the CLI scoring pipeline. This module never performs
network requests.
"""

from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from typing import Any

NEXT_DATA_RE = re.compile(
    r"<script[^>]*\bid=[\"']__NEXT_DATA__[\"'][^>]*>(?P<body>.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)

MIN_HTML_BYTES = 10 * 1024


class SLParseError(ValueError):
    """Raised when saved Sporting Life HTML cannot be parsed."""


class SLValidationError(ValueError):
    """Raised when parsed raw JSON is unsafe to write."""


class SLPartialImportError(SLValidationError):
    """Raised when a saved meeting page was not fully expanded before save."""


def extract_next_data(html_text: str) -> dict[str, Any]:
    """Return decoded ``__NEXT_DATA__`` from a saved Sporting Life page."""
    match = NEXT_DATA_RE.search(html_text or "")
    if not match:
        raise SLParseError("__NEXT_DATA__ not found in HTML")
    body = html.unescape(match.group("body")).strip()
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise SLParseError(f"__NEXT_DATA__ is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SLParseError("__NEXT_DATA__ root is not a JSON object")
    return data


def parse_sl_html_to_raw(html_text: str, course: str, meeting: str, date: str) -> dict[str, Any]:
    """Parse saved Sporting Life HTML into the canonical raw racecard schema.

    Missing optional fields are represented as ``None`` or empty lists and noted
    in ``_parse_warnings``. Saved meeting pages must include detailed runner
    arrays for every advertised race; summary-only partial imports are refused.
    """
    warnings: list[str] = []
    retrieved_at = datetime.now(timezone.utc).isoformat()
    next_data = extract_next_data(html_text)
    page_props = _as_dict(_as_dict(next_data.get("props")).get("pageProps"))
    source_url = _source_url(next_data, course, date)

    meeting_summary = _find_meeting_summary(page_props)
    meeting_display = _dig(meeting_summary, "course", "name") or meeting or course
    going = _clean_text(meeting_summary.get("going")) or _clean_text(_dig(page_props, "race", "race_summary", "going")) or "Unknown"

    detailed_races = _detailed_races(page_props)
    races = [
        _map_race(race_payload, idx + 1, page_props, source_url, going, retrieved_at, warnings)
        for idx, race_payload in enumerate(detailed_races)
    ]
    advertised_count = _advertised_race_count(page_props, detailed_races)
    if advertised_count > len(races):
        raise SLPartialImportError(_partial_import_message(advertised_count, len(races)))

    raw = {
        "meeting": meeting_display,
        "course": meeting_display,
        "course_slug": course,
        "meeting_slug": meeting,
        "date": date,
        "going": going,
        "races": races,
        "retrieved_at": retrieved_at,
        "source": "sporting_life_html_import",
        "source_urls": [source_url],
        "going_source": "sporting_life",
        "_parse_warnings": warnings,
    }
    return raw


def validate_html_import(html_text: str, raw: dict[str, Any], *, require_next_data: bool = True) -> None:
    """Validate the import safety contract before writing raw JSON."""
    if len((html_text or "").encode("utf-8")) < MIN_HTML_BYTES:
        raise SLValidationError("HTML size is below 10 KB; this looks like an error page or partial save")
    if require_next_data and not NEXT_DATA_RE.search(html_text or ""):
        raise SLValidationError("__NEXT_DATA__ not found in HTML")
    races = raw.get("races") or []
    if not races:
        raise SLValidationError("parsed races are empty")
    for race_index, race in enumerate(races, 1):
        missing_race = [field for field in ("off_time", "name", "distance_f") if race.get(field) in (None, "")]
        if missing_race:
            raise SLValidationError(f"race {race_index} missing required field(s): {', '.join(missing_race)}")
        active_runners = [r for r in (race.get("runners") or []) if not r.get("withdrawn", False)]
        if not active_runners:
            raise SLValidationError(f"race {race_index} has zero non-withdrawn runners")
        for runner_index, runner in enumerate(active_runners, 1):
            if not runner.get("horse"):
                raise SLValidationError(f"race {race_index} runner {runner_index} missing horse")


def missing_field_summary(raw: dict[str, Any]) -> dict[str, int]:
    """Count missing nullable/import-gap fields for operator diagnostics."""
    fields = ("draw", "or", "rpr", "ts", "form_string", "last_run_days", "morning_price")
    summary = {field: 0 for field in fields}
    summary["going_history"] = 0
    for race in raw.get("races", []) or []:
        for runner in race.get("runners", []) or []:
            for field in fields:
                value = runner.get(field)
                if value is None or value == "":
                    summary[field] += 1
            if not runner.get("going_history"):
                summary["going_history"] += 1
    return {key: value for key, value in summary.items() if value}


def _detailed_races(page_props: dict[str, Any]) -> list[dict[str, Any]]:
    race = _as_dict(page_props.get("race"))
    if isinstance(race.get("rides"), list):
        return [race]
    races = []
    for payload in _walk(page_props):
        if isinstance(payload, dict) and isinstance(payload.get("rides"), list):
            races.append(payload)
    return races


def _advertised_race_count(page_props: dict[str, Any], detailed_races: list[dict[str, Any]]) -> int:
    return len(_advertised_race_summaries(page_props, detailed_races))


def _advertised_race_summaries(page_props: dict[str, Any], detailed_races: list[dict[str, Any]]) -> list[dict[str, Any]]:
    meeting = page_props.get("meeting")
    if isinstance(meeting, dict):
        meetings = [meeting]
    elif isinstance(meeting, list):
        meetings = meeting
    else:
        return []

    detailed_ids = {
        str(_dig(race, "race_summary", "race_summary_reference", "id") or "")
        for race in detailed_races
    }
    detailed_ids.discard("")

    all_races: list[dict[str, Any]] = []
    matched_races: list[dict[str, Any]] = []
    for meeting_payload in meetings:
        races = [race for race in (_as_dict(meeting_payload).get("races") or []) if isinstance(race, dict)]
        if not races:
            continue
        all_races.extend(races)
        if detailed_ids:
            advertised_ids = {str(_dig(race, "race_summary_reference", "id") or "") for race in races}
            if advertised_ids & detailed_ids:
                matched_races.extend(races)

    return _dedupe_race_summaries(matched_races or all_races)


def _dedupe_race_summaries(races: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[dict[str, Any]] = []
    for race in races:
        key = (
            str(_dig(race, "race_summary_reference", "id") or ""),
            str(race.get("time") or ""),
            str(race.get("name") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(race)
    return unique


def _partial_import_message(advertised_count: int, detailed_count: int) -> str:
    missing_count = advertised_count - detailed_count
    race_word = "race" if advertised_count == 1 else "races"
    detail_word = "was" if detailed_count == 1 else "were"
    other_word = "race is" if missing_count == 1 else "races are"
    return (
        "ERROR: Partial import detected -- saved meeting page contains "
        f"{advertised_count} {race_word} but only {detailed_count} {detail_word} parsed in detail.\n"
        f"The other {missing_count} {other_word} summary-only (race links were not expanded before save).\n"
        "Action: Open the meeting page in your browser, click each race to expand its full "
        "racecard, then re-save the page and retry."
    )


def _map_race(
    race_payload: dict[str, Any],
    race_number: int,
    page_props: dict[str, Any],
    source_url: str,
    going: str,
    retrieved_at: str,
    warnings: list[str],
) -> dict[str, Any]:
    summary = _as_dict(race_payload.get("race_summary"))
    race_id = _dig(summary, "race_summary_reference", "id")
    meeting_race_number = _meeting_race_number(page_props, race_id, summary.get("time"), summary.get("name"))
    race_label = f"race {meeting_race_number or race_number}"
    name = _clean_text(summary.get("name"))
    off_time = _clean_text(summary.get("time"))
    distance_f = _distance_to_furlongs(summary.get("distance"))
    race_class = _race_class(summary.get("race_class"))
    prize_winner = _winner_prize(race_payload.get("prizes"))

    _warn_missing(warnings, race_label, "name", name)
    _warn_missing(warnings, race_label, "off_time", off_time)
    _warn_missing(warnings, race_label, "distance_f", distance_f)

    runners = [
        _map_runner(ride, race_label, idx + 1, source_url, retrieved_at, warnings)
        for idx, ride in enumerate(race_payload.get("rides") or [])
        if isinstance(ride, dict)
    ]

    return {
        "race_number": meeting_race_number or race_number,
        "off_time": off_time,
        "name": name,
        "class": race_class,
        "distance_f": distance_f,
        "prize_winner_gbp": prize_winner,
        "runners": runners,
        "source_urls": [source_url],
        "going": going,
    }


def _map_runner(
    ride: dict[str, Any],
    race_label: str,
    runner_number: int,
    source_url: str,
    retrieved_at: str,
    warnings: list[str],
) -> dict[str, Any]:
    horse = _as_dict(ride.get("horse"))
    trainer = _as_dict(ride.get("trainer"))
    jockey = _as_dict(ride.get("jockey"))
    betting = _as_dict(ride.get("betting"))
    form_summary = _as_dict(horse.get("formsummary"))
    status = _clean_text(ride.get("ride_status")) or ""
    commentary = _clean_text(ride.get("commentary")) or ""
    current_odds = _clean_text(betting.get("current_odds"))
    horse_name = _clean_text(horse.get("name"))
    draw = _to_int(ride.get("draw_number"))
    form_string = _clean_text(form_summary.get("display_text")) or ""
    last_run_days = _last_run_days(commentary)
    withdrawn = _is_withdrawn(status, _clean_text(jockey.get("name")), commentary)

    label = f"{race_label} runner {runner_number}"
    _warn_missing(warnings, label, "horse", horse_name)
    if draw is None:
        warnings.append(f"{label} missing draw")

    notes_parts = []
    if commentary:
        notes_parts.append(commentary)
    if source_url:
        notes_parts.append(f"source {source_url}")

    return {
        "horse": horse_name,
        "age": _to_int(horse.get("age")),
        "trainer": _clean_text(trainer.get("name")),
        "jockey": _clean_text(jockey.get("name")),
        "draw": draw,
        "weight_st_lb": _clean_text(ride.get("handicap")),
        "or": _official_rating(ride),
        "rpr": None,
        "ts": None,
        "form_string": form_string,
        "last_run_days": last_run_days,
        "notes": "; ".join(notes_parts),
        "morning_price": _parse_decimal_odds(current_odds),
        "odds_source": "sporting_life" if current_odds else None,
        "odds_fetched_at": retrieved_at if current_odds else None,
        "going_history": [],
        "going_history_source": "not_available",
        "going_history_fetched_at": retrieved_at,
        "withdrawn": withdrawn,
    }


def _source_url(next_data: dict[str, Any], course: str, date: str) -> str:
    query = _as_dict(next_data.get("query"))
    page_date = _clean_text(query.get("date")) or date
    course_slug = _clean_text(query.get("courseNameSlug")) or course
    race_id = _clean_text(query.get("raceId"))
    slug = _clean_text(query.get("slug"))
    if race_id and slug:
        return f"https://www.sportinglife.com/racing/racecards/{page_date}/{course_slug}/racecard/{race_id}/{slug}"
    return f"https://www.sportinglife.com/racing/racecards/{page_date}/{course_slug}"


def _find_meeting_summary(page_props: dict[str, Any]) -> dict[str, Any]:
    meeting = page_props.get("meeting")
    if isinstance(meeting, list) and meeting:
        return _as_dict(_as_dict(meeting[0]).get("meeting_summary"))
    if isinstance(meeting, dict):
        return _as_dict(meeting.get("meeting_summary"))
    race_meeting = _dig(page_props, "race", "race_summary", "meeting_summary")
    return _as_dict(race_meeting)


def _meeting_race_number(page_props: dict[str, Any], race_id: Any, off_time: Any, name: Any) -> int | None:
    target_id = str(race_id or "")
    for meeting in page_props.get("meeting") or []:
        for idx, race in enumerate(_as_dict(meeting).get("races") or [], 1):
            race_ref = _dig(race, "race_summary_reference", "id")
            if target_id and str(race_ref or "") == target_id:
                return idx
            if off_time and name and race.get("time") == off_time and race.get("name") == name:
                return idx
    return None


def _race_class(value: Any) -> str | None:
    text = _clean_text(value)
    if not text:
        return None
    return f"Class {text}" if text.isdigit() else text


def _distance_to_furlongs(value: Any) -> float | None:
    text = _clean_text(value)
    if not text:
        return None
    miles = furlongs = yards = 0.0
    mile_match = re.search(r"(\d+(?:\.\d+)?)\s*m", text, re.IGNORECASE)
    furlong_match = re.search(r"(\d+(?:\.\d+)?)\s*f", text, re.IGNORECASE)
    yard_match = re.search(r"(\d+(?:\.\d+)?)\s*y", text, re.IGNORECASE)
    if mile_match:
        miles = float(mile_match.group(1))
    if furlong_match:
        furlongs = float(furlong_match.group(1))
    if yard_match:
        yards = float(yard_match.group(1))
    if miles == 0 and furlongs == 0 and yards == 0:
        return None
    result = miles * 8.0 + furlongs + yards / 220.0
    return int(result) if result.is_integer() else round(result, 2)


def _winner_prize(prizes: Any) -> int | None:
    prize_entries = _as_dict(prizes).get("prize") if isinstance(prizes, dict) else None
    for entry in prize_entries or []:
        if _to_int(_as_dict(entry).get("position")) == 1:
            return _money_to_int(_as_dict(entry).get("prize"))
    return None


def _official_rating(ride: dict[str, Any]) -> int | None:
    for key in ("official_rating", "officialRating", "or", "rating"):
        rating = _to_int(ride.get(key))
        if rating is not None:
            return rating
    handicap = ride.get("handicap")
    if isinstance(handicap, dict):
        for key in ("official_rating", "officialRating", "or", "rating"):
            rating = _to_int(handicap.get(key))
            if rating is not None:
                return rating
    return None


def _last_run_days(commentary: str) -> int | None:
    match = re.search(r"\b(\d+)\s+days?\s+ago\b", commentary or "", re.IGNORECASE)
    return int(match.group(1)) if match else None


def _is_withdrawn(status: str, jockey: str | None, commentary: str) -> bool:
    status_upper = (status or "").upper().replace("-", "_").replace(" ", "_")
    if status_upper and status_upper not in {"RUNNER", "ACTIVE", "DECLARED"}:
        return True
    if (jockey or "").strip().lower() in {"non runner", "non-runner", "nonrunner"}:
        return True
    return bool(re.search(r"\bNON\s+RUNNER\b", commentary or "", re.IGNORECASE))


def _parse_decimal_odds(value: Any) -> float | None:
    text = _clean_text(value)
    if not text or text.lower() in {"sp", "tbc", "n/a", "none", "-"}:
        return None
    if text.lower() in {"evs", "evens"}:
        return 2.0
    frac = re.fullmatch(r"(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)", text)
    if frac:
        num = float(frac.group(1))
        den = float(frac.group(2))
        return round(num / den + 1.0, 4) if den else None
    try:
        dec = float(text)
    except ValueError:
        return None
    return round(dec, 4) if dec >= 1.0 else None


def _money_to_int(value: Any) -> int | None:
    text = _clean_text(value)
    if not text:
        return None
    text = text.replace(",", "")
    match = re.search(r"\d+(?:\.\d+)?", text)
    return int(float(match.group(0))) if match else None


def _warn_missing(warnings: list[str], label: str, field: str, value: Any) -> None:
    if value is None or value == "":
        warnings.append(f"{label} missing {field}")


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return re.sub(r"\s+", " ", text) if text else None


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        match = re.search(r"-?\d+", str(value))
        return int(match.group(0)) if match else None


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _dig(value: Any, *keys: str) -> Any:
    current = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _walk(value: Any):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)
