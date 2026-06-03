"""Pace / run-style and extended draw-bias scoring.

Adds two new signals to the model:

* ``pace`` — projected race pace x runner run-style fit. Run style is
  inferred heuristically from the runner's ``form_string`` and recent
  finishing positions (no RP Members pace icons available, so this is
  a best-effort signal — see ``infer_run_style``).
* Extended draw-bias logic (consumed by ``scoring._draw_signal`` when
  the runner-level ``draw_position`` and race-level ``distance_f`` /
  ``course`` are populated). Encodes documented Epsom course biases
  per trip / going.

Both signals are 0–100, neutral = 50.
"""

from __future__ import annotations


# --- Run-style inference --------------------------------------------------- #

# Order from most front-running to most held-up. Used by the pace map
# matcher; LED beats PROM beats MID beats HELD when projecting who'll
# be at the head of affairs.
RUN_STYLES = ("LED", "PROM", "MID", "HELD")


def infer_run_style(runner: dict) -> str:
    """Best-effort run-style inference from form data.

    Heuristic (in priority order):

    1. Explicit ``run_style`` field on the runner (manual override).
    2. Average finishing position from ``form_string`` — winners and
       runners who consistently place close to the front skew front-
       running; tail-of-field finishers skew held-up.
    3. ``HELD`` for first-time starters (no form), since debutants
       typically come from off the pace.

    Returns one of ``RUN_STYLES``.
    """
    explicit = (runner.get("run_style") or "").upper().strip()
    if explicit in RUN_STYLES:
        return explicit

    form = runner.get("form_string") or ""
    digits = [int(c) for c in form if c.isdigit()]
    if not digits:
        return "HELD"

    avg = sum(digits) / len(digits)
    # 0 in form-string typically means "unplaced (10+)"; bucket that
    # tail by treating 0s as 9 so heavy 0-loaders read as HELD.
    avg_adj = sum((d if d > 0 else 9) for d in digits) / len(digits)

    if avg_adj <= 2.5:
        return "PROM"  # consistently close to the pace
    if avg_adj <= 4.5:
        return "MID"
    if avg_adj <= 7.0:
        return "MID"
    return "HELD"


def project_race_pace(runners: list[dict]) -> str:
    """Classify projected pace based on the field's run-style mix.

    Returns one of:

    * ``LONE_LEAD`` — exactly one LED-or-PROM-leaning runner. Favours
      that horse and disadvantages held-up types (no closing kick if
      the leader dictates).
    * ``DUEL`` — multiple LED/PROM types. Front-runners burn each
      other out; favours held-up types.
    * ``EVEN`` — typical mix; no strong adjustment.
    * ``NO_PACE`` — entire field is MID/HELD. Tactical race; first to
      commit usually wins; small bump to PROM/MID over HELD.
    """
    led_or_prom = sum(
        1 for r in runners if infer_run_style(r) in ("LED", "PROM")
    )
    total = max(1, len(runners))

    if led_or_prom == 0:
        return "NO_PACE"
    if led_or_prom == 1:
        return "LONE_LEAD"
    if led_or_prom / total >= 0.30:
        return "DUEL"
    return "EVEN"


def pace_signal(runner: dict, race_pace: str) -> float:
    """Score this runner's pace fit (0–100).

    Combines the runner's run style with the projected race pace.
    """
    style = infer_run_style(runner)

    # Pace-map: race_pace -> {style: signal}
    table = {
        "LONE_LEAD": {"LED": 78, "PROM": 65, "MID": 45, "HELD": 32},
        "DUEL":      {"LED": 35, "PROM": 42, "MID": 58, "HELD": 70},
        "EVEN":      {"LED": 52, "PROM": 55, "MID": 50, "HELD": 48},
        "NO_PACE":   {"LED": 62, "PROM": 60, "MID": 52, "HELD": 40},
    }
    return float(table.get(race_pace, {}).get(style, 50.0))


# --- Extended draw bias ---------------------------------------------------- #

# Epsom is the most draw-sensitive flat track in the UK calendar.
# Tables encoded from documented public draw stats (RP / Timeform free
# articles, Epsom course guides). Signals are 0–100 where 50 = neutral.
#
# Schema:
#   {(course_lower, distance_f): {
#       "field_size_pivot": int,  # below this, draw matters less
#       "low":  signal,           # draws 1..low_threshold
#       "mid":  signal,
#       "high": signal,           # draws > high_threshold
#       "low_threshold":  int,
#       "high_threshold": int,
#       "going_filter": list[str] | None,  # apply only on these goings
#   }}
EPSOM_DRAW_TABLE = {
    # 5f Dash — strongly low-draw biased on quick ground
    ("epsom", 5.0): {
        "low": 78, "mid": 50, "high": 28,
        "low_threshold": 4, "high_threshold": 10,
        "field_size_pivot": 8,
        "going_filter": ["good", "good to firm", "firm"],
    },
    # 6f — moderate low-draw bias on quick ground
    ("epsom", 6.0): {
        "low": 65, "mid": 50, "high": 38,
        "low_threshold": 4, "high_threshold": 10,
        "field_size_pivot": 10,
        "going_filter": ["good", "good to firm", "firm"],
    },
    # 7f — slight low-draw bias
    ("epsom", 7.0): {
        "low": 58, "mid": 50, "high": 44,
        "low_threshold": 5, "high_threshold": 12,
        "field_size_pivot": 12,
        "going_filter": None,
    },
    # 1m114y (~8.5f) — minimal bias
    ("epsom", 8.5): {
        "low": 55, "mid": 50, "high": 47,
        "low_threshold": 5, "high_threshold": 12,
        "field_size_pivot": 14,
        "going_filter": None,
    },
    # 1m2f (~10f) Oaks/Coronation Cup trip — low-to-middle preferred
    ("epsom", 10.0): {
        "low": 60, "mid": 52, "high": 42,
        "low_threshold": 6, "high_threshold": 12,
        "field_size_pivot": 12,
        "going_filter": None,
    },
    # 1m4f (~12f) Derby trip — historically minimal bias; field size
    # and tactical luck dominate
    ("epsom", 12.0): {
        "low": 52, "mid": 50, "high": 48,
        "low_threshold": 6, "high_threshold": 14,
        "field_size_pivot": 14,
        "going_filter": None,
    },
}


def extended_draw_signal(runner: dict, race: dict) -> float | None:
    """Return an Epsom-tuned draw signal, or ``None`` if not applicable.

    ``None`` means "fall back to the legacy ``_draw_signal`` logic" —
    used when the course/distance isn't in our table so we don't
    overwrite the existing 5f-only handling silently.
    """
    course = (race.get("course") or "").lower().strip()
    if course != "epsom":
        return None

    dist = race.get("distance_f") or race.get("distance_furlongs")
    if dist is None:
        return None
    try:
        dist_f = float(dist)
    except (TypeError, ValueError):
        return None

    # Round to nearest 0.5f to match table keys
    key_dist = round(dist_f * 2) / 2
    table = EPSOM_DRAW_TABLE.get((course, key_dist))
    if table is None:
        return None

    going = (race.get("going") or "").lower().strip()
    if table["going_filter"] and going not in table["going_filter"]:
        return 50.0  # course matches but going doesn't — neutral

    draw = runner.get("draw")
    if draw is None:
        return 50.0
    try:
        draw_n = int(draw)
    except (TypeError, ValueError):
        return 50.0

    # Damp the bias when fields are small (less traffic, draw matters less)
    field_size = len(race.get("runners") or []) or 1
    damp = min(1.0, field_size / max(1, table["field_size_pivot"]))

    if draw_n <= table["low_threshold"]:
        raw = table["low"]
    elif draw_n > table["high_threshold"]:
        raw = table["high"]
    else:
        raw = table["mid"]

    # Pull toward 50 by (1-damp)
    return 50.0 + (raw - 50.0) * damp
