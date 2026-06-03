"""
equipment.py — Equipment-change signal v0.6
===========================================

Scores first-time race equipment for a runner.  The signal is deliberately
quiet when enrichment is absent: missing runner, missing horse, missing file,
malformed records, or no relevant equipment change all return neutral 50.0.

Data file
---------
``data/enrichment/equipment.json``

Expected shape::

    {
        "horses": {
            "Horse Name": {
                "equipment": ["tt", "cp"],
                "first_time_use": ["tt"],
                "changed_vs_last_run": []
            }
        }
    }

The loader returns a dict keyed by lower-cased horse name for safer lookup.
Common Racing Post equipment codes are normalised before scoring:
``b`` blinkers, ``cp`` cheekpieces, ``tt`` tongue-tie, ``v`` visor,
``h`` hood, ``es`` eyeshield, ``p`` paddings.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any

_DATA_DIR_CANDIDATES = (
    os.path.join(os.getcwd(), "data", "enrichment"),
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "enrichment",
    ),
)

_ITEM_DELTAS = {
    "blinkers": 8.0,
    "cheekpieces": 7.0,
    "tongue-tie": 6.0,
    "visor": 5.0,
    "hood": 3.0,
    "eyeshield": 2.0,
    "paddings": 2.0,
}

_ITEM_ALIASES = {
    "b": "blinkers",
    "blinker": "blinkers",
    "blinkers": "blinkers",
    "cp": "cheekpieces",
    "cheekpiece": "cheekpieces",
    "cheekpieces": "cheekpieces",
    "tt": "tongue-tie",
    "tongue tie": "tongue-tie",
    "tongue-tie": "tongue-tie",
    "tonguetie": "tongue-tie",
    "v": "visor",
    "visor": "visor",
    "h": "hood",
    "hood": "hood",
    "es": "eyeshield",
    "eye shield": "eyeshield",
    "eye-shield": "eyeshield",
    "eyeshield": "eyeshield",
    "p": "paddings",
    "pad": "paddings",
    "padding": "paddings",
    "paddings": "paddings",
}


def _find_data_file(name: str) -> str | None:
    for directory in _DATA_DIR_CANDIDATES:
        path = os.path.join(directory, name)
        if os.path.exists(path):
            return path
    return None


def _normalise_item(item: Any) -> str | None:
    if not isinstance(item, str):
        return None
    key = item.strip().lower().replace("_", "-")
    if not key:
        return None
    return _ITEM_ALIASES.get(key, key if key in _ITEM_DELTAS else None)


def _normalised_items(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    normalised: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = _normalise_item(item)
        if value and value not in seen:
            normalised.append(value)
            seen.add(value)
    return normalised


def _equipment_count(items: Any) -> int:
    if not isinstance(items, list):
        return 0
    return sum(1 for item in items if isinstance(item, str) and item.strip())


@lru_cache(maxsize=8)
def load_equipment_data(path: str = "data/enrichment/equipment.json") -> dict:
    """Load equipment enrichment, keyed by lower-cased horse name.

    Returns an empty dict if the file is missing or malformed.
    """
    resolved_path = path
    if not os.path.exists(resolved_path):
        candidate = _find_data_file(os.path.basename(path))
        if candidate is None:
            return {}
        resolved_path = candidate

    try:
        with open(resolved_path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}

    horses = raw.get("horses", {}) if isinstance(raw, dict) else {}
    if not isinstance(horses, dict):
        return {}

    result: dict[str, dict] = {}
    for horse, entry in horses.items():
        if isinstance(horse, str) and horse.strip() and isinstance(entry, dict):
            result[horse.strip().lower()] = entry
    return result


def _removed_count(changed_vs_last_run: Any) -> int:
    """Count removed equipment from likely Livingston/Danny schemas."""
    if isinstance(changed_vs_last_run, dict):
        for key in ("removed", "removals", "removed_items", "out"):
            value = changed_vs_last_run.get(key)
            if isinstance(value, list):
                return sum(1 for item in value if isinstance(item, str) and item.strip())
        return 0

    if not isinstance(changed_vs_last_run, list):
        return 0

    removed = 0
    for change in changed_vs_last_run:
        if isinstance(change, dict):
            direction = str(change.get("change") or change.get("direction") or change.get("type") or "").lower()
            item = change.get("item") or change.get("equipment") or change.get("code")
            if direction in {"removed", "removal", "out", "off"} and isinstance(item, str) and item.strip():
                removed += 1
        elif isinstance(change, str):
            text = change.strip().lower()
            if text.startswith(("-", "removed:", "removed ", "off:")):
                removed += 1
    return removed


def score_equipment(runner: dict, race: dict, equipment_data: dict = None) -> float:  # noqa: ARG001
    """Return the v0.6 equipment score for one runner.

    Base score is 50.0.  First-time equipment adds item-specific deltas,
    multiple first-time items incur a -3 penalty per extra item, and removed
    equipment adds +3 per item.  Valid non-neutral scores are clamped to
    Danny's [10, 90] range; missing data stays neutral at 50.0.
    """
    if not isinstance(runner, dict):
        return 50.0

    horse = runner.get("horse") or runner.get("horse_name")
    if not isinstance(horse, str) or not horse.strip():
        return 50.0

    data = equipment_data if equipment_data is not None else load_equipment_data()
    if not isinstance(data, dict) or not data:
        return 50.0

    entry = data.get(horse.strip().lower()) or data.get(horse.strip())
    if not isinstance(entry, dict):
        return 50.0

    first_time_items = _normalised_items(entry.get("first_time_use"))
    removed_count = _removed_count(entry.get("changed_vs_last_run"))
    equipment_count = _equipment_count(entry.get("equipment")) or len(first_time_items)

    if not first_time_items and not removed_count and equipment_count <= 1:
        return 50.0

    score = 50.0
    score += sum(_ITEM_DELTAS[item] for item in first_time_items)
    if equipment_count > 1:
        score -= 3.0 * (equipment_count - 1)
    score += 3.0 * removed_count

    return float(max(10.0, min(90.0, score)))


def _clear_caches() -> None:  # pragma: no cover
    """Reset loader cache for tests."""
    cache_clear = getattr(load_equipment_data, "cache_clear", None)
    if cache_clear is not None:
        cache_clear()
