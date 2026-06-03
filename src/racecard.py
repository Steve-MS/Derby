"""
racecard.py — Printable one-page-per-day betting slip.

Generates a single A4 HTML page per race day showing only the betting
recommendations (WIN, EW, outsider EW) in a flat table — designed to be
printed and taken to the bookmaker.

Usage
-----
    from src.racecard import render_card

    render_card(
        date="2026-06-06",
        scores_path="outputs/scores-2026-06-06.json",
        bets_path="outputs/bets-2026-06-06.json",
        output_path="outputs/racecard-2026-06-06.html",
    )
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


TEMPLATE_DIR = Path(__file__).parent / "templates"
VENUE = "Epsom"
MODEL_VERSION = "v0.1"

_DATE_DAY_NAMES = {
    "2026-06-05": "Ladies / Oaks Day",
    "2026-06-06": "Derby Day",
}

ACCA_STAKE_GBP = 5.0


def _short_race_name(name: str) -> str:
    """Trim 'Group X', sponsor noise, and parentheticals for slip display."""
    if not name:
        return ""
    short = name
    for marker in (" (Group ", " (Listed", " (Handicap", " (Class"):
        idx = short.find(marker)
        if idx > 0:
            short = short[:idx]
    return short.strip()


def _build_rows(scores: list[dict], bets: dict) -> tuple[list[dict], list[dict]]:
    """Return (slip_rows, pass_rows) — flat lists ready for template."""
    singles_by_race = {s.get("race_id"): s for s in bets.get("singles", [])}
    outsiders_by_race = {
        o.get("race_id"): o
        for o in bets.get("outsiders", [])
        if o.get("outsider_pick")
    }

    slip_rows: list[dict] = []
    pass_rows: list[dict] = []

    for race in scores:
        rid = race.get("race_id")
        time = race.get("race_time", "?")
        race_short = _short_race_name(race.get("race_name", ""))

        primary = singles_by_race.get(rid)
        outsider = outsiders_by_race.get(rid)

        # Primary recommendation (WIN/EW) — skip if PASS
        if primary and primary.get("bet_type") not in (None, "PASS"):
            stake = primary.get("stake_gbp", 0) or 0
            odds = None
            for r in race.get("ranked_runners", []):
                if r.get("horse") == primary.get("horse"):
                    odds = r.get("morning_price")
                    break
            potential = primary.get("expected_return_gbp", 0) or 0
            slip_rows.append({
                "kind": primary["bet_type"].lower(),
                "time": time,
                "race_short": race_short,
                "bet_type": primary["bet_type"],
                "horse": primary["horse"],
                "trainer": _trainer_for(race, primary["horse"]),
                "odds": odds,
                "stake": stake,
                "potential": potential,
                "note": f"edge {primary.get('edge_pct', 0):+.1f}%",
            })
        elif primary:
            pass_rows.append({
                "time": time,
                "race_short": race_short,
                "horse": primary.get("horse", "—"),
                "odds": _odds_for(race, primary.get("horse")),
                "note": f"edge {primary.get('edge_pct', 0):+.1f}% — below threshold",
            })

        # Outsider EW (separate row if present)
        if outsider:
            slip_rows.append({
                "kind": "outsider",
                "time": time,
                "race_short": race_short + " ⚡",
                "bet_type": "EW",
                "horse": outsider["horse"],
                "trainer": outsider.get("trainer", ""),
                "odds": outsider.get("morning_price"),
                "stake": outsider.get("stake_gbp", 0) or 0,
                "potential": outsider.get("potential_return_gbp_win", 0) or 0,
                "note": f"value: model rank {outsider.get('model_rank')} vs market {outsider.get('market_rank')}",
            })

    # Sort slip rows by race time
    slip_rows.sort(key=lambda r: r["time"])
    pass_rows.sort(key=lambda r: r["time"])
    return slip_rows, pass_rows


def _odds_for(race: dict, horse: str | None) -> float | None:
    if not horse:
        return None
    for r in race.get("ranked_runners", []):
        if r.get("horse") == horse:
            return r.get("morning_price")
    return None


def _trainer_for(race: dict, horse: str) -> str:
    for r in race.get("ranked_runners", []):
        if r.get("horse") == horse:
            return r.get("trainer", "") or ""
    return ""


def _pick_best_acca(bets: dict, races: list[dict], stake_gbp: float) -> dict | None:
    """Pick the day's recommended accumulator.

    Preference order: largest accumulator (4+ legs) → treble → best double.
    Within each tier the highest-EV entry wins. Returns a slip-ready dict
    with the supplied flat stake applied, or ``None`` if no multi-leg bet
    was generated.
    """
    candidates: list[dict] = []
    for key in ("accumulators", "trebles", "doubles"):
        bucket = bets.get(key) or []
        if bucket:
            candidates = bucket
            break
    if not candidates:
        return None

    pick = max(candidates, key=lambda a: a.get("expected_value_gbp", 0) or 0)
    legs = pick.get("legs", []) or []
    if not legs:
        return None

    combined_dec = 1.0
    for leg in legs:
        combined_dec *= float(leg.get("odds_decimal") or 1.0)
    combined_prob = pick.get("combined_prob") or 0.0
    potential = round(stake_gbp * combined_dec, 2)

    race_by_id = {r.get("race_id"): r for r in races}
    leg_lines = []
    for leg in legs:
        race = race_by_id.get(leg.get("race_id")) or {}
        time = race.get("race_time", "?")
        leg_lines.append({
            "time": time,
            "horse": leg.get("horse", "—"),
            "odds": leg.get("odds_decimal"),
        })

    n = len(legs)
    label = {1: "Single", 2: "Double", 3: "Treble"}.get(n, f"{n}-fold acca")

    return {
        "label": label,
        "leg_count": n,
        "legs": leg_lines,
        "combined_dec": round(combined_dec, 2),
        "combined_prob": combined_prob,
        "stake": round(stake_gbp, 2),
        "potential": potential,
        "expected_value_gbp": pick.get("expected_value_gbp", 0) or 0,
    }


def render_card(
    date: str,
    scores_path: str,
    bets_path: str | None,
    output_path: str,
    race_context: dict | None = None,
    daily_outlay_gbp: float = 100.0,
) -> None:
    """Render the printable one-page betting slip.

    Stakes from bets.json are scaled proportionally so the day's total
    outlay equals ``daily_outlay_gbp`` (default £100). The shape of the
    portfolio (relative sizing across WIN / EW / outsider bets) is
    preserved — only the scale changes.
    """
    scores_data = json.loads(Path(scores_path).read_text(encoding="utf-8"))

    bets = {}
    if bets_path and Path(bets_path).exists():
        bets = json.loads(Path(bets_path).read_text(encoding="utf-8"))

    races = scores_data.get("races", [])
    slip_rows, pass_rows = _build_rows(races, bets)

    acca = _pick_best_acca(bets, races, ACCA_STAKE_GBP)
    singles_budget = daily_outlay_gbp
    if acca:
        singles_budget = max(daily_outlay_gbp - acca["stake"], 0.0)

    raw_total_stakes = sum(r.get("stake", 0) for r in slip_rows)
    if raw_total_stakes > 0 and singles_budget > 0:
        scale = singles_budget / raw_total_stakes
        for r in slip_rows:
            r["stake"] = round(r["stake"] * scale, 2)
            r["potential"] = round(r["potential"] * scale, 2)

    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
        date_display = dt.strftime("%#d %B %Y") if os.name == "nt" else dt.strftime("%-d %B %Y")
    except ValueError:
        date_display = date

    day_name = _DATE_DAY_NAMES.get(date, "")

    total_stakes = sum(r.get("stake", 0) for r in slip_rows)
    total_potential = sum(r.get("potential", 0) for r in slip_rows)
    if acca:
        total_stakes += acca["stake"]
        total_potential += acca["potential"]

    ctx = {
        "venue": scores_data.get("venue", VENUE),
        "day_name": day_name,
        "date": date,
        "date_display": date_display,
        "race_count": len(races),
        "going_label": (race_context or {}).get("going", ""),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "model_version": MODEL_VERSION,
        "slip_rows": slip_rows,
        "pass_rows": pass_rows,
        "acca": acca,
        "active_bet_count": len(slip_rows) + (1 if acca else 0),
        "total_stakes_gbp": total_stakes,
        "total_potential_gbp": total_potential,
        "daily_outlay_target_gbp": daily_outlay_gbp,
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

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")

