"""Shared betting JSON schema helpers for CLI, renderers, and watchdog."""

from __future__ import annotations

import re
from typing import Any

MONEY_RE = re.compile(r"(?:£|\$|€|GBP\s*)?\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
VOID_STATUSES = {"NR", "VOID", "NO_BET", "REFUNDED", "NON_RUNNER", "NON-RUNNER", "WITHDRAWN", "SCRATCHED", "CANCELLED"}
MULTI_STATUSES = {"DOUBLE", "TREBLE", "ACCA", "ACCUMULATOR", "LUCKY15", "LUCKY_15"}
MULTI_TYPES = {"double", "treble", "acca", "accumulator", "lucky15", "lucky_15"}


def parse_money(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    match = MONEY_RE.search(str(value))
    return float(match.group(1)) if match else 0.0


def money(value: float) -> str:
    return f"£{float(value):.2f}"


def race_time_from_id(race_id: Any) -> str:
    tail = str(race_id or "").split("-")[-1]
    if re.fullmatch(r"\d{3,4}", tail):
        tail = tail.zfill(4)
        return f"{tail[:2]}:{tail[2:]}"
    return ""


def _race_meta(race_lookup: dict[str, dict[str, Any]], race_id: Any) -> dict[str, Any]:
    return race_lookup.get(str(race_id or ""), {})


def _entry_base(race_lookup: dict[str, dict[str, Any]], race_id: Any, course: str | None) -> dict[str, Any]:
    race = _race_meta(race_lookup, race_id)
    return {
        "race_id": str(race_id or ""),
        "race_time": race.get("race_time") or race_time_from_id(race_id),
        "race_name": race.get("race_name") or race.get("name") or "",
        "course": course or race.get("course") or race.get("venue") or "",
    }


def entries_from_legacy_bets(bets: dict[str, Any], scores: list[dict[str, Any]] | None = None, course: str | None = None) -> list[dict[str, Any]]:
    race_lookup = {str(r.get("race_id") or ""): r for r in (scores or [])}
    entries: list[dict[str, Any]] = []

    for single in bets.get("singles") or []:
        race_id = single.get("race_id")
        bet_type = str(single.get("bet_type") or "PASS").upper()
        stake = float(single.get("stake_gbp") or 0.0)
        unit_stake = stake / 2 if bet_type == "EW" else stake
        entry = {
            **_entry_base(race_lookup, race_id, course),
            "pick": single.get("horse"),
            "status": "NO_BET" if bet_type == "PASS" else bet_type,
            "bet_type": bet_type.lower(),
            "stake_guidance": None if bet_type == "PASS" else f"{money(unit_stake)} {bet_type}",
            "odds_decimal": single.get("odds_decimal"),
            "rationale_short": single.get("rationale", ""),
        }
        entries.append(entry)

    for outsider in bets.get("outsiders") or []:
        horse = outsider.get("outsider_pick") or outsider.get("horse")
        if not horse:
            continue
        stake = float(outsider.get("stake_gbp") or 0.0)
        entries.append({
            **_entry_base(race_lookup, outsider.get("race_id"), course),
            "pick": horse,
            "status": "EW",
            "bet_type": "outsider_ew",
            "stake_guidance": f"{money(stake)} EW",
            "odds_decimal": outsider.get("morning_price") or outsider.get("odds_decimal"),
            "rationale_short": outsider.get("rationale") or outsider.get("outsider_rationale") or "",
        })

    for key, status in (("doubles", "DOUBLE"), ("trebles", "TREBLE"), ("accumulators", "ACCA")):
        for bet in bets.get(key) or []:
            legs = bet.get("legs") or []
            stake = float(bet.get("combined_stake_gbp") or bet.get("stake_gbp") or bet.get("total_stake_gbp") or 0.0)
            entries.append({
                "race_id": "multi",
                "race_time": "Multi",
                "race_name": status.title(),
                "course": course or "",
                "pick": " × ".join(str(leg.get("horse") or "") for leg in legs if leg.get("horse")),
                "status": status,
                "bet_type": status.lower(),
                "stake_guidance": f"{money(stake)} {status}",
                "total_stake": money(stake),
                "legs": legs,
                "rationale_short": bet.get("rationale", ""),
            })

    lucky15 = bets.get("lucky_15")
    if isinstance(lucky15, dict):
        stake = float(lucky15.get("total_stake_gbp") or lucky15.get("combined_stake_gbp") or 0.0)
        if stake:
            entries.append({
                "race_id": "multi",
                "race_time": "Multi",
                "race_name": "Lucky 15",
                "course": course or "",
                "pick": "Lucky 15",
                "status": "LUCKY15",
                "bet_type": "lucky15",
                "stake_guidance": f"{money(stake)} LUCKY15",
                "total_stake": money(stake),
                "legs": lucky15.get("legs") or [],
                "rationale_short": lucky15.get("rationale", ""),
            })

    item = bets.get("item_special_bet")
    if isinstance(item, dict) and item.get("bet_type") == "WIN":
        stake = float(item.get("stake_gbp") or 0.0)
        entries.append({
            **_entry_base(race_lookup, item.get("race_id"), course),
            "pick": item.get("horse"),
            "status": "WIN",
            "bet_type": "special_win",
            "stake_guidance": f"{money(stake)} WIN",
            "odds_decimal": item.get("odds_decimal"),
            "rationale_short": item.get("rationale", ""),
        })

    return entries


def schema_entries(bets: dict[str, Any], scores: list[dict[str, Any]] | None = None, course: str | None = None) -> list[dict[str, Any]]:
    for key in ("bets", "entries"):
        value = bets.get(key)
        if isinstance(value, list):
            return value
    return entries_from_legacy_bets(bets, scores=scores, course=course)


def computed_total(entries: list[dict[str, Any]]) -> float:
    total = 0.0
    for entry in entries:
        status = str(entry.get("status") or "").upper()
        bet_type = str(entry.get("bet_type") or "").lower()
        if status in VOID_STATUSES:
            continue
        if status == "WIN":
            total += parse_money(entry.get("stake_guidance"))
        elif status == "EW":
            total += parse_money(entry.get("stake_guidance")) * 2
        elif status == "TRIFECTA" or bet_type == "trifecta_box":
            total += parse_money(entry.get("total_stake") or entry.get("stake_guidance"))
        elif status in MULTI_STATUSES or bet_type in MULTI_TYPES:
            total += parse_money(entry.get("total_stake") or entry.get("stake_guidance") or entry.get("combined_stake_gbp"))
    return round(total, 2)


def active_entry_count(entries: list[dict[str, Any]]) -> int:
    count = 0
    for entry in entries:
        status = str(entry.get("status") or "").upper()
        bet_type = str(entry.get("bet_type") or "").lower()
        if status in {"WIN", "EW"} or status in MULTI_STATUSES or bet_type in MULTI_TYPES:
            count += 1
    return count
