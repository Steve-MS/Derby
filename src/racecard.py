"""
racecard.py — Printable one-page-per-day betting slip.

Generates a compact A4 HTML betting slip showing Steve's actual portfolio
(WIN, EW, outsider EW, doubles/trebles) for a race day.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

try:
    from .render_helpers import default_course_display, output_path_for, presentation_context
except ImportError:  # direct import via src/ on sys.path in cli.py
    from render_helpers import default_course_display, output_path_for, presentation_context


TEMPLATE_DIR = Path(__file__).parent / "templates"
BASE_DIR = Path(__file__).parent.parent
VENUE = default_course_display()
MODEL_VERSION = "v0.1"


# ---------------------------------------------------------------------------
# Small formatters / lookups
# ---------------------------------------------------------------------------


def _short_race_name(name: str) -> str:
    """Trim sponsor/class noise where the slip needs a compact label."""
    if not name:
        return ""
    short = name
    for marker in (" (Group ", " (Listed", " (Handicap", " (Heritage", " (Class"):
        idx = short.find(marker)
        if idx > 0:
            short = short[:idx]
    return short.strip()


def _money(value: float | int | None) -> str:
    return f"£{float(value or 0):.2f}"


def _odds_for(race: dict, horse: str | None) -> float | None:
    if not horse:
        return None
    for runner in race.get("ranked_runners", []):
        if runner.get("horse") == horse:
            return runner.get("morning_price")
    return None


def _price_decimal(price: dict | None) -> float | None:
    return price.get("decimal") if price else None


def _price_inline(price: dict | None) -> str:
    if not price or not price.get("fractional"):
        return ""
    source = price.get("source_display")
    text = f"{price.get('prefix', '')}{price['fractional']}"
    return f"{text} ({source})" if source else text


def _rationale_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _trainer_for(race: dict, horse: str | None) -> str:
    if not horse:
        return ""
    for runner in race.get("ranked_runners", []):
        if runner.get("horse") == horse:
            return runner.get("trainer", "") or ""
    return ""


def _race_maps(races: list[dict]) -> tuple[dict[str, dict], dict[str, tuple[str, str]]]:
    by_id = {r.get("race_id"): r for r in races if r.get("race_id")}
    label_by_id = {
        rid: (race.get("race_time", "?"), _short_race_name(race.get("race_name", "")))
        for rid, race in by_id.items()
    }
    return by_id, label_by_id


def _edge_for(bets: dict, race_id: str | None, horse: str | None) -> float | None:
    if not race_id or not horse:
        return None
    for single in bets.get("singles", []) or []:
        if single.get("race_id") == race_id and single.get("horse") == horse:
            return single.get("edge_pct")
    return None


# ---------------------------------------------------------------------------
# Wave 3.3 context: going, non-runners, scenarios
# ---------------------------------------------------------------------------


def _load_json(path: Path | str | None) -> dict:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _load_market_latest(path: Path | str | None = None) -> dict:
    return _load_json(path or BASE_DIR / "data" / "enrichment" / "market-latest.json")


def _day_key(date: str) -> str:
    return date.replace("-", "_")


def _norm_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")


def _short_price_source(bookmaker: str | None, source: str, fresh: bool) -> str:
    if not fresh:
        return "stale"
    if bookmaker:
        first = bookmaker.split(",", 1)[0].strip()
        return "FanOdds" if first.startswith("FanOdds") else first
    if "fanodds" in source.lower():
        return "FanOdds"
    if "justbookies" in source.lower():
        return "JustBookies"
    return source


def _price_context(raw: dict) -> dict:
    bookmaker = raw.get("bookmaker")
    source = raw.get("source") or raw.get("odds_source") or ""
    fresh = raw.get("fresh") is not False
    status = str(raw.get("status") or "").upper()
    fractional = raw.get("best_price_fractional") or raw.get("fractional_odds") or raw.get("odds_fraction")
    decimal = raw.get("best_price_decimal") or raw.get("decimal_odds") or raw.get("odds_decimal")
    if status == "WITHDRAWN":
        fractional = None
        decimal = None
    return {
        "fractional": fractional,
        "decimal": decimal,
        "source_display": _short_price_source(bookmaker, source, fresh),
        "fresh": fresh,
        "stale": not fresh,
        "status": status,
        "prefix": "~" if not fresh and fractional else "",
    }


def _build_market_index(date: str, snapshot: dict) -> dict:
    by_time_horse: dict[tuple[str, str], dict] = {}
    by_race_horse: dict[tuple[str, str], dict] = {}
    by_horse_multi: dict[str, list[dict]] = {}
    day = (snapshot.get("horses") or {}).get(_day_key(date), {})
    for race_prices in day.values():
        for raw in (race_prices or {}).values():
            price = _price_context(raw)
            time_key = _norm_key(raw.get("off_time"))
            race_key = _norm_key(raw.get("race_name"))
            horse_key = _norm_key(raw.get("horse"))
            by_time_horse[(time_key, horse_key)] = price
            by_race_horse[(race_key, horse_key)] = price
            by_horse_multi.setdefault(horse_key, []).append(price)
    by_horse = {k: v[0] for k, v in by_horse_multi.items() if len(v) == 1}
    return {"by_time_horse": by_time_horse, "by_race_horse": by_race_horse, "by_horse": by_horse}


def _market_price_for(index: dict, race: dict, horse: str | None) -> dict | None:
    if not horse:
        return None
    time_key = _norm_key(race.get("race_time"))
    race_key = _norm_key(race.get("race_name"))
    horse_key = _norm_key(horse)
    return (
        index.get("by_time_horse", {}).get((time_key, horse_key))
        or index.get("by_race_horse", {}).get((race_key, horse_key))
        or index.get("by_horse", {}).get(horse_key)
    )


def _market_snapshot_iso(snapshot: dict) -> str:
    return snapshot.get("generated") or (snapshot.get("_meta") or {}).get("generated_at") or ""


def _going_label_from_forecast(date: str, going_forecast_path: str | None = None) -> str:
    """Return the one-line print subtitle going from data/going-forecast.json."""
    forecast_path = Path(going_forecast_path) if going_forecast_path else BASE_DIR / "data" / "going-forecast.json"
    data = _load_json(forecast_path)
    if date == "2026-06-05":
        friday = data.get("friday_2026_06_05", {})
        rain = friday.get("rainfall_mm_48h")
        if rain is not None:
            return f"Good-to-Soft (overnight rain ~{rain:g}mm)"
        if friday.get("going"):
            return friday["going"].replace("Good to Soft", "Good-to-Soft")
    if date == "2026-06-06":
        saturday = data.get("saturday_2026_06_06", {})
        rain = saturday.get("rainfall_mm_48h")
        probability = _soft_probability(saturday)
        if rain is not None and probability:
            return f"Soft ({rain:g}mm rain forecast, {probability} prob)"
        if rain is not None:
            return f"Soft ({rain:g}mm rain forecast)"
        if saturday.get("going"):
            return saturday["going"]
    return ""


def _soft_probability(saturday_forecast: dict) -> str:
    text = " ".join(
        str(saturday_forecast.get(k, ""))
        for k in ("rationale", "weather_notes", "official_going")
    )
    match = re.search(r"(\d{2}\s*[–-]\s*\d{2})\s*%", text)
    if not match:
        return ""
    return match.group(1).replace(" ", "").replace("–", "-") + "%"


def _withdrawn_horses_from_raw(date: str, raw_racecard_path: str | None = None, course: str | None = None) -> list[str]:
    path = Path(raw_racecard_path) if raw_racecard_path else output_path_for("raw-racecards", course_slug=course, date=date)
    data = _load_json(path)
    names: set[str] = set()
    for race in data.get("races", []) or []:
        for runner in race.get("runners", []) or []:
            if runner.get("withdrawn") is True:
                name = runner.get("horse") or runner.get("name")
                if name:
                    names.add(name)
    return sorted(names)


def _non_runners_from_bets(bets: dict) -> list[str]:
    overrides = bets.get("live_price_overrides_applied", {}) or {}
    return sorted(
        horse for horse, value in overrides.items()
        if isinstance(value, str) and "WITHDRAWN" in value.upper()
    )


def _scenario_banner_for(date: str, bets: dict, course: str | None = None) -> dict[str, str] | None:
    scenario = str(bets.get("scenario", ""))
    if course not in (None, "epsom") and not scenario:
        return None
    if date != "2026-06-06" and not scenario:
        return None
    if "HOLD" in scenario.upper():
        return {
            "class": "scenario-hold",
            "text": "🟡 HOLD SLIP — assumes Going downgraded to Soft. Item bet CANCELLED.",
        }
    if "GREEN" in scenario.upper() or date == "2026-06-06":
        base = output_path_for("racecard", course_slug=course, date=date)
        hold_file = f"{base.stem}-hold{base.suffix}"
        return {
            "class": "scenario-green",
            "text": f"🟢 GREEN SLIP — assumes Going holds at Good-to-Soft or better. HOLD slip file: {hold_file}",
        }
    return None


# ---------------------------------------------------------------------------
# Row builders
# ---------------------------------------------------------------------------


def _base_row(
    *,
    kind: str,
    time: str,
    race_short: str,
    bet_type: str,
    horse: str,
    trainer: str = "",
    odds: float | None = None,
    stake: float = 0.0,
    potential: float = 0.0,
    note: str = "",
    stake_display: str | None = None,
    withdrawn: bool = False,
    legs: list[dict] | None = None,
    edge_pct: float | None = None,
    cancel_note: str = "",
    market_price: dict | None = None,
    rationale: str = "",
) -> dict:
    return {
        "kind": kind,
        "time": time,
        "race_short": race_short,
        "bet_type": bet_type,
        "horse": horse,
        "trainer": trainer,
        "odds": odds,
        "stake": round(float(stake or 0), 2),
        "stake_display": stake_display or _money(stake),
        "potential": round(float(potential or 0), 2),
        "potential_display": _money(potential) if potential else "—",
        "note": note,
        "withdrawn": withdrawn,
        "legs": legs or [],
        "edge_pct": edge_pct,
        "cancel_note": cancel_note,
        "market_price": market_price,
        "price_inline": _price_inline(market_price),
        "price_stale": bool(market_price and market_price.get("stale")),
        "rationale": _rationale_text(rationale),
    }


def _primary_row(race: dict, primary: dict, withdrawn: set[str], market_index: dict) -> dict:
    horse = primary.get("horse", "—")
    bet_type = primary.get("bet_type", "BET")
    price = _market_price_for(market_index, race, horse)
    odds = _price_decimal(price) or primary.get("odds_decimal") or _odds_for(race, horse)
    stake = primary.get("stake_gbp", 0) or 0
    potential = primary.get("expected_return_gbp") or primary.get("est_return_gbp") or 0
    edge = primary.get("edge_pct")
    return _base_row(
        kind=bet_type.lower(),
        time=race.get("race_time", "?"),
        race_short=_short_race_name(race.get("race_name", "")),
        bet_type=bet_type,
        horse=horse,
        trainer=_trainer_for(race, horse),
        odds=odds,
        stake=stake,
        potential=potential,
        note=f"edge {edge:+.1f}%" if edge is not None else "",
        stake_display=f"{_money(stake)} EW" if bet_type == "EW" else _money(stake),
        withdrawn=horse in withdrawn,
        edge_pct=edge,
        market_price=price,
        rationale=primary.get("rationale", ""),
    )


def _pass_row(race: dict, primary: dict, withdrawn: set[str], market_index: dict) -> dict:
    horse = primary.get("horse", "—")
    price = _market_price_for(market_index, race, horse)
    edge = primary.get("edge_pct")
    note = "below threshold" if edge is None else f"edge {edge:+.1f}% — below threshold"
    return _base_row(
        kind="pass",
        time=race.get("race_time", "?"),
        race_short=_short_race_name(race.get("race_name", "")),
        bet_type="PASS",
        horse=horse,
        odds=_price_decimal(price) or _odds_for(race, horse),
        note=note,
        withdrawn=horse in withdrawn,
        edge_pct=edge,
        market_price=price,
        rationale=primary.get("rationale", ""),
    )


def _outsider_row(outsider: dict, withdrawn: set[str], market_index: dict, race: dict | None = None) -> dict:
    horse = outsider.get("horse", "—")
    price = _market_price_for(market_index, race or outsider, horse)
    stake_each_way = float(outsider.get("stake_gbp", 0) or 0)
    stake_total = stake_each_way * 2 if outsider.get("bet_type") == "EW" else stake_each_way
    return _base_row(
        kind="outsider",
        time=outsider.get("race_time", "?"),
        race_short=f"{_short_race_name(outsider.get('race_name', ''))} ⚡",
        bet_type=outsider.get("bet_type", "EW"),
        horse=horse,
        trainer=outsider.get("trainer", "") or "",
        odds=_price_decimal(price) or outsider.get("morning_price"),
        stake=stake_total,
        potential=outsider.get("potential_return_gbp_win", 0) or 0,
        stake_display=f"{_money(stake_each_way)} EW",
        note=f"value: model rank {outsider.get('model_rank')} vs market {outsider.get('market_rank')}",
        withdrawn=horse in withdrawn,
        market_price=price,
        rationale=outsider.get("rationale", ""),
    )


def _item_special_row(item: dict, race: dict, edge_pct: float | None, market_index: dict) -> dict:
    stake = item.get("stake_gbp", 0) or 0
    price = _market_price_for(market_index, race, item.get("horse"))
    odds = _price_decimal(price) or item.get("odds_decimal") or _odds_for(race, item.get("horse"))
    potential = round(float(stake) * float(odds or 0), 2)
    edge = edge_pct if edge_pct is not None else -69.4
    return _base_row(
        kind="speculative",
        time=race.get("race_time", "?"),
        race_short=_short_race_name(race.get("race_name", "")),
        bet_type=item.get("bet_type", "WIN"),
        horse=item.get("horse", "Item"),
        trainer=_trainer_for(race, item.get("horse")),
        odds=odds,
        stake=stake,
        potential=potential,
        stake_display=_money(stake),
        note="SPECULATIVE — NOT A MODEL PICK",
        edge_pct=edge,
        cancel_note="Cancel if going declared Soft Saturday AM → use HOLD card.",
        market_price=price,
        rationale=item.get("rationale", ""),
    )


def _item_cancelled_row(item_advisory: dict, race: dict, market_index: dict) -> dict:
    return _base_row(
        kind="cancelled",
        time=race.get("race_time", "?"),
        race_short=_short_race_name(race.get("race_name", "")),
        bet_type="CXL",
        horse=item_advisory.get("horse", "Item"),
        trainer=_trainer_for(race, item_advisory.get("horse")),
        odds=_price_decimal(_market_price_for(market_index, race, item_advisory.get("horse"))) or _odds_for(race, item_advisory.get("horse")),
        stake=0.0,
        potential=0.0,
        stake_display="—",
        note="❌ CANCELLED — going downgrade; 1pt retained.",
        rationale=item_advisory.get("rationale", ""),
    )


def _build_rows(scores: list[dict], bets: dict, non_runners: list[str] | None = None, market_index: dict | None = None) -> tuple[list[dict], list[dict], list[dict]]:
    """Return (slip_rows, pass_rows, multi_rows) ready for the template."""
    withdrawn = set(non_runners or [])
    market_index = market_index or {}
    singles_by_race = {s.get("race_id"): s for s in bets.get("singles", []) or []}
    outsiders_by_race = {
        o.get("race_id"): o
        for o in bets.get("outsiders", []) or []
        if o.get("outsider_pick")
    }
    item_special = bets.get("item_special_bet") or {}
    item_advisory = bets.get("item_advisory") or {}

    slip_rows: list[dict] = []
    pass_rows: list[dict] = []

    for race in scores:
        rid = race.get("race_id")
        primary = singles_by_race.get(rid)
        outsider = outsiders_by_race.get(rid)

        if primary and primary.get("bet_type") not in (None, "PASS"):
            slip_rows.append(_primary_row(race, primary, withdrawn, market_index))
        elif primary:
            same_as_item = primary.get("horse") == item_special.get("horse") and rid == item_special.get("race_id")
            same_as_cancelled = primary.get("horse") == item_advisory.get("horse") and rid == item_advisory.get("race_id")
            if not same_as_item and not same_as_cancelled:
                pass_rows.append(_pass_row(race, primary, withdrawn, market_index))

        if item_special and rid == item_special.get("race_id"):
            slip_rows.append(_item_special_row(item_special, race, _edge_for(bets, rid, item_special.get("horse")), market_index))
        if item_advisory and rid == item_advisory.get("race_id"):
            slip_rows.append(_item_cancelled_row(item_advisory, race, market_index))

        if outsider:
            slip_rows.append(_outsider_row(outsider, withdrawn, market_index, race))

    multi_rows = _build_multi_rows(bets, scores, market_index)
    slip_rows.sort(key=lambda r: r["time"])
    pass_rows.sort(key=lambda r: r["time"])
    return slip_rows, pass_rows, multi_rows


def _build_multi_rows(bets: dict, races: list[dict], market_index: dict | None = None) -> list[dict]:
    by_id, label_by_id = _race_maps(races)
    market_index = market_index or {}
    rows: list[dict] = []
    groups = (("doubles", "DBL", "Double"), ("trebles", "TBL", "Treble"), ("accumulators", "ACCA", "Accumulator"))
    for key, bet_type, label in groups:
        for bet in bets.get(key, []) or []:
            legs = []
            combined_dec = 1.0
            for leg in bet.get("legs", []) or []:
                race = by_id.get(leg.get("race_id"), {})
                time, race_short = label_by_id.get(leg.get("race_id"), ("?", ""))
                price = _market_price_for(market_index, race, leg.get("horse"))
                odds = _price_decimal(price) or leg.get("odds_decimal") or 1.0
                combined_dec *= float(odds)
                legs.append({
                    "time": time,
                    "race_short": race_short,
                    "horse": leg.get("horse", "—"),
                    "odds": odds,
                    "price_inline": _price_inline(price),
                    "price_stale": bool(price and price.get("stale")),
                })
            if not legs:
                continue
            stake = bet.get("combined_stake_gbp", bet.get("stake_gbp", bet.get("total_stake_gbp", 0))) or 0
            potential = bet.get("potential_return_gbp", bet.get("est_return_gbp", 0)) or 0
            ev = bet.get("expected_value_gbp")
            rows.append(_base_row(
                kind="multi",
                time="Multi",
                race_short=label,
                bet_type=bet_type,
                horse=" × ".join(leg["horse"] for leg in legs),
                odds=round(combined_dec, 2),
                stake=stake,
                potential=potential,
                stake_display=_money(stake),
                note=f"EV {_money(ev)}" if ev is not None else "",
                legs=legs,
                rationale=bet.get("rationale", ""),
            ))
    return rows


def _rescale_rows(rows: list[dict], target_total: float) -> None:
    source_total = sum(float(r.get("stake", 0) or 0) for r in rows)
    if source_total <= 0 or target_total <= 0:
        return
    scale = target_total / source_total
    for row in rows:
        if not row.get("stake"):
            continue
        row["stake"] = round(row["stake"] * scale, 2)
        row["potential"] = round(row.get("potential", 0) * scale, 2)
        row["potential_display"] = _money(row["potential"]) if row["potential"] else "—"
        if row["kind"] == "outsider" and " EW" in row.get("stake_display", ""):
            each_way = row["stake"] / 2
            row["stake_display"] = f"{_money(each_way)} EW"
        elif row["bet_type"] == "EW":
            row["stake_display"] = f"{_money(row['stake'])} EW"
        else:
            row["stake_display"] = _money(row["stake"])


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_card(
    date: str,
    scores_path: str,
    bets_path: str | None,
    output_path: str | None = None,
    race_context: dict | None = None,
    daily_outlay_gbp: float | None = 100.0,
    going_forecast_path: str | None = None,
    raw_racecard_path: str | None = None,
    scenario_banner: dict[str, str] | None = None,
    market_latest_path: str | None = None,
    bets_json_path: str | None = None,
    course: str | None = None,
    meeting: str | None = None,
) -> Path:
    """Render the printable one-page betting slip.

    ``daily_outlay_gbp=None`` preserves the exact stakes from Badger's portfolio.
    Passing a number keeps the older CLI behaviour of scaling all active rows to
    that total. Wave 3.3 callers may also pass/derive going, non-runner, and
    scenario context; all parameters are backward-compatible.

    Parameters
    ----------
    bets_json_path:
        Optional path to ``outputs/bets-{date}.json`` (Linus format).  When
        supplied, ``render_header()`` computes the WIN/EW outlay, trifecta
        outlay, active bet count, NR line and validation tag directly from the
        JSON source — eliminating header staleness when the JSON changes after
        a scoring injection.  This is the v0.4 fix for the recurring
        "header left at £5.50 per guardrails" pattern (Saul audit 2026-06-06).
    """
    scores_data = json.loads(Path(scores_path).read_text(encoding="utf-8"))

    presentation = presentation_context(
        date=date,
        course_slug=course or scores_data.get("course_slug"),
        meeting_slug=meeting or scores_data.get("meeting_slug"),
        venue_override=scores_data.get("venue"),
    )

    bets = {}
    if bets_path and Path(bets_path).exists():
        bets = json.loads(Path(bets_path).read_text(encoding="utf-8"))

    races = scores_data.get("races", [])
    market_snapshot = _load_market_latest(market_latest_path)
    market_index = _build_market_index(date, market_snapshot)
    non_runners = sorted(set(_withdrawn_horses_from_raw(date, raw_racecard_path, presentation["course"]["slug"])) | set(_non_runners_from_bets(bets)))
    slip_rows, pass_rows, multi_rows = _build_rows(races, bets, non_runners, market_index)
    active_rows = slip_rows + multi_rows

    if daily_outlay_gbp is not None:
        _rescale_rows(active_rows, daily_outlay_gbp)

    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
        date_display = dt.strftime("%#d %B %Y") if os.name == "nt" else dt.strftime("%-d %B %Y")
    except ValueError:
        date_display = date

    day_name = presentation["day"].get("label", "")
    going_label = (race_context or {}).get("going") or _going_label_from_forecast(date, going_forecast_path)

    total_stakes = round(sum(float(r.get("stake", 0) or 0) for r in active_rows), 2)
    total_potential = round(sum(float(r.get("potential", 0) or 0) for r in active_rows), 2)
    active_bet_count = sum(1 for r in active_rows if float(r.get("stake", 0) or 0) > 0)

    # JSON-driven header: when bets_json_path is provided, override header
    # values with those computed by render_header() from the source JSON.
    # This is the fix for the recurring header-staleness publish blocker.
    trifecta_outlay: float | None = None
    total_outlay_gbp: float = total_stakes
    validation_tag: str | None = None
    header_nr_horses: list[dict] = []
    trifecta_horses: list[str] = []

    if bets_json_path and Path(bets_json_path).exists():
        from src.report import render_header  # lazy import — avoids circular at module load
        bets_json = _load_json(bets_json_path)
        hdr = render_header(bets_json)
        total_stakes = hdr["winew_outlay"]
        trifecta_outlay = hdr["trifecta_outlay"]
        total_outlay_gbp = hdr["total_outlay"]
        active_bet_count = hdr["active_bet_count"]
        validation_tag = hdr["validation_tag"]
        header_nr_horses = hdr["nr_horses"]
        trifecta_horses = hdr["trifecta_horses"]

    ctx = {
        "venue": presentation["title"],
        "course": presentation["course"],
        "meeting": presentation["meeting"],
        "day": presentation["day"],
        "day_name": day_name,
        "date": date,
        "date_display": date_display,
        "race_count": len(races),
        "going_label": going_label,
        "generated_at": (race_context or {}).get("generated_at") or datetime.now().strftime("%Y-%m-%d %H:%M"),
        "model_version": MODEL_VERSION,
        "slip_rows": slip_rows,
        "pass_rows": pass_rows,
        "multi_rows": multi_rows,
        "scenario_banner": scenario_banner or _scenario_banner_for(date, bets, presentation["course"]["slug"]),
        "non_runners": non_runners,
        "active_bet_count": active_bet_count,
        "total_stakes_gbp": total_stakes,
        "total_potential_gbp": total_potential,
        "total_outlay_gbp": total_outlay_gbp,
        "trifecta_outlay": trifecta_outlay,
        "validation_tag": validation_tag,
        "header_nr_horses": header_nr_horses,
        "trifecta_horses": trifecta_horses,
        "daily_outlay_target_gbp": daily_outlay_gbp,
        "market_snapshot_iso": _market_snapshot_iso(market_snapshot),
    }

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    tpl = env.get_template("racecard.html.j2")

    css = (TEMPLATE_DIR / "racecard.css").read_text(encoding="utf-8")
    html = tpl.render(**ctx, css=css)

    out = Path(output_path) if output_path else racecard_output_path(course=presentation["course"]["slug"], date=date)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


def racecard_output_path(course: str | None, date: str) -> Path:
    """Return the configured racecard output path for *course* and *date*."""
    return output_path_for("racecard", course_slug=course, date=date)
