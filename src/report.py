"""
report.py — HTML report renderer for the race-analysis plugin.

Generates a single self-contained HTML file per race day that Steve can open
in a browser with no external dependencies.

Usage
-----
    from src.report import render

    render(
        date="2026-06-05",
        scores=[...],          # list of scored-race dicts
        bets={},               # Badger's portfolio; may be empty
        race_context={},       # from race-day-context.md
        output_path="outputs/reports/epsom-2026-06-05.html",
    )

See spec/module-contracts.md for full input schemas.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from jinja2 import Environment, FileSystemLoader, pass_eval_context
    from markupsafe import Markup
    _JINJA2_AVAILABLE = True
except ImportError:  # pragma: no cover
    _JINJA2_AVAILABLE = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TEMPLATE_DIR = Path(__file__).parent / "templates"

# Human-readable signal labels in display order.
SIGNAL_LABELS: dict[str, str] = {
    "class_rating":    "Class / Rating",
    "recent_form":     "Recent Form",
    "trainer_form":    "Trainer",
    "jockey":          "Jockey",
    "course_distance": "Course & Distance",
    "going":           "Going",
    "draw_bias":       "Draw",
    "class_move":      "Class Move",
}

# Race-day names keyed by ISO weekday (Monday=0)
_DAY_NAMES: dict[int, str] = {
    3: "Derby Day",    # Saturday Derby Day is Sat 6 June 2026
    4: "Oaks Day",     # Friday Oaks Day is Fri 5 June 2026
}

# Explicit overrides by date string (takes precedence over weekday)
_DATE_DAY_NAMES: dict[str, str] = {
    "2026-06-05": "Oaks Day",
    "2026-06-06": "Derby Day",
}

VENUE = "Epsom"

MODEL_VERSION = "v0.1"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render(
    date: str,
    scores: list[dict],
    bets: dict | None,
    race_context: dict | None,
    output_path: str,
) -> None:
    """Render a single race-day HTML report and write it to *output_path*.

    Parameters
    ----------
    date:
        ISO date string e.g. ``"2026-06-05"`` or ``"2026-06-06"``.
    scores:
        List of scored-race dicts.  Each item: ``{race_id, race_meta,
        ranked_runners, confidence, bet_recommendation, race_stdev,
        race_competitiveness}``.  May be empty — renders a minimal page.
    bets:
        Badger's bet portfolio dict ``{singles, doubles, trebles, accas,
        lucky15, portfolio_summary}``.  May be ``None`` or ``{}`` — all
        betting sections are omitted gracefully.
    race_context:
        Race-day context dict (going forecast, narratives, backtest verdict).
        May be ``None`` or ``{}``.
    output_path:
        Filesystem path for the output HTML file.  Parent directory is
        created if it does not exist.

    Returns
    -------
    None
        Writes the HTML file as a side effect.

    Raises
    ------
    ImportError
        If Jinja2 is not installed.

    Examples
    --------
    >>> import tempfile, os
    >>> with tempfile.TemporaryDirectory() as d:
    ...     out = os.path.join(d, "test.html")
    ...     render("2026-06-05", [], {}, {}, out)
    ...     assert os.path.exists(out)
    ...     content = open(out).read()
    ...     assert "<!DOCTYPE html>" in content
    """
    if not _JINJA2_AVAILABLE:
        raise ImportError(
            "Jinja2 is required for report rendering. "
            "Install it with: pip install jinja2"
        )

    scores = scores or []
    bets = bets or {}
    race_context = race_context or {}

    # Ensure output directory exists.
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Build template context.
    ctx = _build_context(date, scores, bets, race_context)

    # Render via Jinja2.
    html = _render_template(ctx)

    out_path.write_text(html, encoding="utf-8")


# ---------------------------------------------------------------------------
# Template context builder
# ---------------------------------------------------------------------------


def _build_context(
    date: str,
    scores: list[dict],
    bets: dict,
    race_context: dict,
) -> dict:
    """Assemble the Jinja2 template context dict."""

    # Parse date for display
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
        date_display = dt.strftime("%-d %B %Y") if os.name != "nt" else dt.strftime("%#d %B %Y")
    except ValueError:
        date_display = date

    # Day name
    day_name = _DATE_DAY_NAMES.get(date, "")
    if not day_name:
        try:
            day_name = _DAY_NAMES.get(dt.weekday(), "")  # type: ignore[possibly-undefined]
        except Exception:
            day_name = ""

    # Going / narrative from race_context (try both Friday and Saturday keys)
    is_friday = date.endswith("-05") or "friday" in date.lower()
    going_key   = "going_friday"   if is_friday else "going_saturday"
    narr_key    = "narrative_friday" if is_friday else "narrative_saturday"

    going_label  = race_context.get(going_key) or race_context.get("going", "")
    going_detail = going_label
    narrative    = race_context.get(narr_key) or race_context.get("narrative", "")
    wind         = race_context.get("wind", "")
    temp         = race_context.get("temp", "")

    backtest_verdict = race_context.get("backtest_verdict")
    model_version    = race_context.get("model_version", MODEL_VERSION)
    generated_at     = race_context.get(
        "generated_at",
        datetime.now().strftime("%Y-%m-%dT%H:%M"),
    )

    return {
        "date":             date,
        "date_display":     date_display,
        "day_name":         day_name,
        "venue":            VENUE,
        "race_count":       len(scores),
        "going_label":      going_label,
        "going_detail":     going_detail,
        "wind":             wind,
        "temp":             temp,
        "narrative":        narrative,
        "backtest_verdict": backtest_verdict,
        "model_version":    model_version,
        "generated_at":     generated_at,
        "scores":           [_normalize_race_meta(r) for r in scores],
        "bets":             bets,
        "signal_labels":    SIGNAL_LABELS,
        # Callable helpers exposed to the template
        "top_pick_rationale":  _top_pick_rationale,
        "race_bets_for":       _race_bets_for,
        "race_outsider_for":   _race_outsider_for,
    }


# ---------------------------------------------------------------------------
# Race-dict normalisation
# ---------------------------------------------------------------------------


def _normalize_race_meta(race: dict) -> dict:
    """Ensure every race dict has a populated ``race_meta`` sub-dict.

    Kaylee's scoring module writes display fields (``race_name``,
    ``race_time``) as flat top-level keys.  The Jinja template reads
    them via ``race_meta``.  When ``race_meta`` is absent or ``None``
    we synthesise it from the flat fields so existing callers that
    already provide a fully-formed ``race_meta`` are unaffected.
    """
    if race.get("race_meta"):
        return race
    meta = {
        "name":     race.get("race_name", "Unknown Race"),
        "time":     race.get("race_time", "?"),
        "course":   race.get("course", "Epsom"),
        "distance": race.get("distance", ""),
        "going":    race.get("going", ""),
    }
    return {**race, "race_meta": meta}


# ---------------------------------------------------------------------------
# Template helpers (called from Jinja2)
# ---------------------------------------------------------------------------


def _top_pick_rationale(runner: dict, race: dict) -> str:
    """Generate a one-sentence rationale for the top-ranked runner.

    Looks at ``raw_signal_values`` and calls out the two strongest signals
    by name.
    """
    sigs: dict[str, float] = runner.get("raw_signal_values") or {}
    horse = runner.get("horse", "This runner")
    conf  = race.get("confidence", "LOW")
    rec   = race.get("bet_recommendation", "PASS")
    score = runner.get("score", 0)

    # Identify top 2 signals by value (exclude any None values)
    valid_sigs = {k: v for k, v in sigs.items() if v is not None and v > 0}
    top_sigs = sorted(valid_sigs.items(), key=lambda x: x[1], reverse=True)[:2]
    sig_names = [SIGNAL_LABELS.get(k, k) for k, _ in top_sigs]

    if sig_names:
        strength_str = " and ".join(sig_names)
        rationale = (
            f"{horse} leads the field with a model score of {score:.1f}/100, "
            f"driven by strong {strength_str}. "
        )
    else:
        rationale = (
            f"{horse} leads the field with a model score of {score:.1f}/100. "
        )

    if conf == "HIGH" and rec == "WIN":
        rationale += "High confidence — WIN recommended."
    elif conf == "MED" and rec == "EW":
        rationale += "Moderate confidence — Each-Way suggested."
    elif rec == "PASS":
        rationale += "Low confidence — model recommends passing this race."
    else:
        rationale += f"Confidence: {conf}."

    return rationale


def _race_bets_for(race_id: str, bets: dict) -> list[dict]:
    """Return singles from *bets* that match the given race_id."""
    if not bets or not race_id:
        return []
    return [b for b in bets.get("singles", []) if b.get("race_id") == race_id]


def _race_outsider_for(race_id: str, bets: dict) -> dict | None:
    """Return the qualifying outsider entry for the given race_id.

    Returns ``None`` if *bets* is empty, *race_id* is unset, no matching
    entry is found, or the entry has ``outsider_pick=None`` (no qualifying
    outsider for that race).
    """
    if not bets or not race_id:
        return None
    for o in bets.get("outsiders", []):
        if o.get("race_id") == race_id and o.get("outsider_pick") is not None:
            return o
    return None


# ---------------------------------------------------------------------------
# Jinja2 rendering
# ---------------------------------------------------------------------------


def _render_template(ctx: dict) -> str:
    """Load template + CSS and return rendered HTML string."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Add custom filters
    env.filters["format"] = lambda val, fmt: val % fmt

    template = env.get_template("report.html.j2")

    # Inline the CSS
    css_path = TEMPLATE_DIR / "style.css"
    css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""

    return template.render(**ctx, css=css)
