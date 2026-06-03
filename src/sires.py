"""
sires.py — Sire stamina signal v0.1
====================================

Looks up the sire of a runner from a static enrichment file and
maps it to a stamina index (0-100) that informs the runner's
suitability for Classic / staying distances (10f+).

Data sources
------------
- ``data/enrichment/horse-profiles.json`` — per-horse static
  profile (currently only ``sire``). Manually curated from
  verified public sources (Racing Post, Horse Racing Nation,
  BloodHorse). Anti-fabrication: horses not in the file simply
  receive a neutral 50 — we never invent a sire.
- ``data/enrichment/sire-stamina.json`` — static stamina-index
  lookup for known flat sires. Sires not in the file also
  receive neutral 50.

Distance gating
---------------
The signal is irrelevant at sprint trips. It returns 50 for any
race below 10f. At 10f+ the signal scales by the sire stamina
index. The Derby (12f) and Oaks (12f) are the prime targets.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

_DATA_DIR_CANDIDATES = (
    # When code runs from project root (`python -m src.scoring …`)
    os.path.join(os.getcwd(), "data", "enrichment"),
    # When tests / scripts run with cwd elsewhere — relative to this file
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "enrichment"),
)

_MIN_DISTANCE_F = 10.0


def _find_data_file(name: str) -> str | None:
    for d in _DATA_DIR_CANDIDATES:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    return None


@lru_cache(maxsize=1)
def load_horse_profiles() -> dict[str, dict]:
    """Load horse profile enrichment (cached). Returns {} if file missing."""
    path = _find_data_file("horse-profiles.json")
    if not path:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("horses", {}) or {}
    except (OSError, json.JSONDecodeError):
        return {}


@lru_cache(maxsize=1)
def load_sire_stamina() -> dict[str, int]:
    """Load sire stamina lookup (cached). Returns {} if file missing."""
    path = _find_data_file("sire-stamina.json")
    if not path:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("sires", {}) or {}
    except (OSError, json.JSONDecodeError):
        return {}


def get_sire(runner: dict) -> str | None:
    """Return the sire name for a runner, or None if unknown.

    Looks first in the runner dict itself (``sire`` key — for tests
    and future-proofing), then falls back to the horse-profiles
    enrichment file keyed by exact horse name.
    """
    sire = runner.get("sire")
    if sire and isinstance(sire, str):
        return sire.strip()
    horse = runner.get("horse") or runner.get("horse_name")
    if not horse:
        return None
    profile = load_horse_profiles().get(horse)
    if not profile:
        return None
    sire = profile.get("sire")
    return sire.strip() if isinstance(sire, str) and sire else None


def sire_stamina_signal(runner: dict, race: dict) -> float:
    """Sire stamina signal (0-100).

    Returns neutral 50 in any of these cases:
      - Race distance < 10f (signal irrelevant for sprints/miles)
      - Sire unknown for this horse (anti-fabrication)
      - Sire not in the static stamina lookup

    Otherwise returns the sire's stamina index from
    ``data/enrichment/sire-stamina.json`` directly as the signal.

    Parameters
    ----------
    runner : dict
        Runner dict; ``horse`` or ``horse_name`` is the lookup key,
        or ``sire`` may be set directly.
    race : dict
        Race dict; ``distance_f`` (or ``distance_furlongs``) gates
        the signal.

    Returns
    -------
    float
        0-100 (clamped).
    """
    dist_f = float(race.get("distance_f") or race.get("distance_furlongs") or 0.0)
    if dist_f < _MIN_DISTANCE_F:
        return 50.0

    sire = get_sire(runner)
    if not sire:
        return 50.0

    stamina = load_sire_stamina().get(sire)
    if stamina is None:
        return 50.0

    return float(max(0.0, min(100.0, stamina)))


def _clear_caches() -> None:  # pragma: no cover - test helper
    """Reset cached enrichment files (used by tests after monkeypatching)."""
    load_horse_profiles.cache_clear()
    load_sire_stamina.cache_clear()
