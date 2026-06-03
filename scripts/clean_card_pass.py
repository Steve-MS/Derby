"""One-shot cleanup after 2026-06-03 card-filler agent.

- Updates card-level going to match RP-17 forecast.
- Adds per-race going overrides (5f course = Good, Derby course = Good to Soft).
- Renames Saturday races whose names were speculative.
- Re-saves both racecard files.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "raw"

GOING_CARD = "Good to Soft (Good in places); 5f course Good (Light rain) (Source: Racing Post 2026-06-03)"

# Saturday race-name corrections (off_time -> real name per RP-17)
SAT_RENAMES = {
    "15:15": "Betfred Dash Handicap (Heritage Handicap)",
    "16:40": "Cherryfield (Croydon) Lester Piggott Handicap",
    "17:20": "HKJC World Pool Northern Dancer Handicap",
    "17:55": "JRA Tokyo Trophy Handicap",
}


def per_race_going(distance_f: int | None) -> str:
    """5f sprints run on the 5f course (Good); everything else on Derby course (Good to Soft)."""
    if distance_f is not None and distance_f <= 5:
        return "Good"
    return "Good to Soft"


def clean(path: Path, renames: dict[str, str]) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["going"] = GOING_CARD
    data.setdefault("going_source", "racingpost.com course-id 17 fetched 2026-06-03")

    changes = []
    for race in data["races"]:
        ot = race.get("off_time", "")
        old_name = race.get("name", "")
        if ot in renames and renames[ot] != old_name:
            race["name"] = renames[ot]
            race["_name_note"] = (
                f"Renamed 2026-06-03: original speculative name '{old_name}' "
                f"replaced with verified RP-17 title."
            )
            changes.append(f"  {ot}: '{old_name}' -> '{renames[ot]}'")

        new_going = per_race_going(race.get("distance_f"))
        if race.get("going") != new_going:
            race["going"] = new_going

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated {path.name}")
    for c in changes:
        print(c)


if __name__ == "__main__":
    clean(RAW / "epsom-2026-06-05-racecards.json", {})
    clean(RAW / "epsom-2026-06-06-racecards.json", SAT_RENAMES)
    print("Done.")
