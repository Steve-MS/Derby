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

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .bet_schema import MULTI_STATUSES, MULTI_TYPES, parse_money, schema_entries
    from .course_config import CourseConfigError, path_for
    from .render_helpers import default_course_display, output_path_for, presentation_context
except ImportError:  # direct import via src/ on sys.path in cli.py
    from bet_schema import MULTI_STATUSES, MULTI_TYPES, parse_money, schema_entries
    from course_config import CourseConfigError, path_for
    from render_helpers import default_course_display, output_path_for, presentation_context

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
BASE_DIR = Path(__file__).parent.parent

# Human-readable signal labels in display order.
SIGNAL_LABELS: dict[str, str] = {
    "class_rating":    "Class / Rating",
    "recent_form":     "Recent Form",
    "trainer_form":    "Trainer",
    "jockey":          "Jockey",
    "course_distance": "Course & Distance",
    "going":           "Going",
    "going_fit":       "Going Fit",
    "draw_bias":       "Draw",
    "class_move":      "Class Move",
    "pace":            "Pace Fit",
    "sire_stamina":    "Sire Stamina",
}

VENUE = default_course_display()

MODEL_VERSION = "v0.1"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render(
    date: str,
    scores: list[dict],
    bets: dict | None,
    race_context: dict | None,
    output_path: str | None = None,
    soft_contingency_bets: dict | None = None,
    market_latest_path: str | None = None,
    course: str | None = None,
    meeting: str | None = None,
) -> Path:
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
    soft_contingency_bets:
        Optional HOLD-slip portfolio (Saturday only).  When provided the
        report renders a second "HOLD – Soft Contingency" slip section
        below the main GREEN portfolio.  May be ``None``.

    Returns
    -------
    Path
        The output file path written.

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
    out_path = Path(output_path) if output_path else report_output_path(course=course, date=date)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Build template context.
    ctx = _build_context(date, scores, bets, race_context, soft_contingency_bets, market_latest_path, course, meeting)

    # Render via Jinja2.
    html = _render_template(ctx)

    out_path.write_text(html, encoding="utf-8")
    return out_path


def report_output_path(course: str | None, date: str) -> Path:
    """Return the configured report output path for *course* and *date*."""
    return output_path_for("report", course_slug=course, date=date)


# ---------------------------------------------------------------------------
# Template context builder
# ---------------------------------------------------------------------------


def _build_context(
    date: str,
    scores: list[dict],
    bets: dict,
    race_context: dict,
    soft_contingency_bets: dict | None = None,
    market_latest_path: str | None = None,
    course: str | None = None,
    meeting: str | None = None,
) -> dict:
    """Assemble the Jinja2 template context dict."""

    # Parse date for display
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
        date_display = dt.strftime("%-d %B %Y") if os.name != "nt" else dt.strftime("%#d %B %Y")
    except ValueError:
        date_display = date

    bets_meta = bets.get("meta") if isinstance(bets.get("meta"), dict) else {}
    presentation = presentation_context(
        date=date,
        course_slug=course or race_context.get("course") or bets_meta.get("course_slug"),
        meeting_slug=meeting or race_context.get("meeting") or bets_meta.get("meeting_slug"),
        venue_override=race_context.get("venue") or bets_meta.get("course"),
        day_label_override=race_context.get("day_label") or bets_meta.get("day_label"),
    )
    day_name = presentation["day"].get("label", "")

    # Going / narrative from race_context using meeting-day metadata when present.
    config_going_key = presentation["day"].get("going_key")
    if config_going_key:
        going_key = f"going_{config_going_key}"
        narr_key = f"narrative_{config_going_key}"
    else:
        is_friday = date.endswith("-05") or "friday" in date.lower()
        going_key = "going_friday" if is_friday else "going_saturday"
        narr_key = "narrative_friday" if is_friday else "narrative_saturday"

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

    market_snapshot = _load_market_latest(market_latest_path, course=presentation["course"]["slug"], date=date)
    market_index = _build_market_index(date, market_snapshot)
    scores_with_prices = _attach_market_prices(date, scores, market_index, presentation["course"]["display_name"])
    market_summary = _market_summary(date, market_snapshot, market_index)

    # Non-runners: horses listed as WITHDRAWN in live price overrides.
    live_overrides = bets.get("live_price_overrides_applied", {})
    non_runners = [
        horse for horse, val in live_overrides.items()
        if isinstance(val, str) and "WITHDRAWN" in val.upper()
    ]

    # Going advisory detail from bets (richer than race_context going_label).
    going_advisory = bets.get("going_advisory", {})

    # Item speculative punt (Saturday only — not a model-generated signal).
    item_special_bet = _with_market_price(bets.get("item_special_bet"), market_index)

    # GREEN / HOLD scenario metadata.
    scenario      = bets.get("scenario", "")
    scenario_note = bets.get("scenario_note", "")

    return {
        "date":             date,
        "date_display":     date_display,
        "day_name":         day_name,
        "venue":            presentation["title"],
        "course":           presentation["course"],
        "meeting":          presentation["meeting"],
        "day":              presentation["day"],
        "race_count":       len(scores),
        "going_label":      going_label,
        "going_detail":     going_detail,
        "wind":             wind,
        "temp":             temp,
        "narrative":        narrative,
        "backtest_verdict": backtest_verdict,
        "model_version":    model_version,
        "generated_at":     generated_at,
        "scores":           scores_with_prices,
        "bets":             bets,
        "signal_labels":    SIGNAL_LABELS,
        # Going / field-change context
        "non_runners":      non_runners,
        "going_advisory":   going_advisory,
        # Item speculative punt
        "item_special_bet": item_special_bet,
        # Scenario (GREEN / HOLD) for Saturday dual-slip display
        "scenario":         scenario,
        "scenario_note":    scenario_note,
        "soft_contingency": soft_contingency_bets or {},
        "market_snapshot_iso": market_summary.get("snapshot_iso", ""),
        "market_odds_label": market_summary.get("odds_label", ""),
        # Callable helpers exposed to the template
        "top_pick_rationale":  _top_pick_rationale,
        "race_bets_for":       _race_bets_for,
        "race_outsider_for":   _race_outsider_for,
    }


# ---------------------------------------------------------------------------
# Market odds snapshot helpers
# ---------------------------------------------------------------------------


def _load_market_latest(path: str | None = None, course: str | None = None, date: str | None = None) -> dict:
    if path:
        p = Path(path)
    else:
        try:
            p = path_for(course or "epsom", date or "0000-00-00", "market_snapshot")
        except CourseConfigError:
            return {}
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _day_key(date: str) -> str:
    return date.replace("-", "_")


def _norm_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")


def _price_context(raw: dict) -> dict:
    bookmaker = raw.get("bookmaker")
    source = raw.get("source") or raw.get("odds_source") or ""
    fresh = raw.get("fresh") is not False
    fractional = raw.get("best_price_fractional") or raw.get("fractional_odds") or raw.get("odds_fraction")
    decimal = raw.get("best_price_decimal") or raw.get("decimal_odds") or raw.get("odds_decimal")
    status = str(raw.get("status") or "").upper()
    if status == "WITHDRAWN":
        fractional = None
        decimal = None
    return {
        "horse": raw.get("horse", ""),
        "fractional": fractional,
        "decimal": decimal,
        "bookmaker": bookmaker,
        "source": source,
        "source_display": _short_price_source(bookmaker, source, fresh),
        "fetched_at": raw.get("retrieved_at") or raw.get("odds_fetched_at"),
        "fresh": fresh,
        "stale": not fresh,
        "status": status,
        "prefix": "~" if not fresh and fractional else "",
    }


def _short_price_source(bookmaker: str | None, source: str, fresh: bool) -> str:
    if not fresh:
        return "stale fallback"
    if bookmaker:
        first = bookmaker.split(",", 1)[0].strip()
        return "FanOdds" if first.startswith("FanOdds") else first
    if "fanodds" in source.lower():
        return "FanOdds"
    if "justbookies" in source.lower():
        return "JustBookies"
    return source


def _build_market_index(date: str, snapshot: dict) -> dict:
    prices = []
    by_triplet: dict[tuple[str, str, str], dict] = {}
    by_time_horse: dict[tuple[str, str], dict] = {}
    by_race_horse: dict[tuple[str, str], dict] = {}
    by_horse_multi: dict[str, list[dict]] = {}

    day = (snapshot.get("horses") or {}).get(_day_key(date), {})
    for race_prices in day.values():
        for raw in (race_prices or {}).values():
            price = _price_context(raw)
            prices.append(price)
            time_key = _norm_key(raw.get("off_time"))
            race_key = _norm_key(raw.get("race_name"))
            horse_key = _norm_key(raw.get("horse"))
            by_triplet[(time_key, race_key, horse_key)] = price
            by_time_horse[(time_key, horse_key)] = price
            by_race_horse[(race_key, horse_key)] = price
            by_horse_multi.setdefault(horse_key, []).append(price)

    by_horse = {k: v[0] for k, v in by_horse_multi.items() if len(v) == 1}
    return {
        "prices": prices,
        "by_triplet": by_triplet,
        "by_time_horse": by_time_horse,
        "by_race_horse": by_race_horse,
        "by_horse": by_horse,
    }


def _market_price_for(index: dict, race: dict, horse: str | None) -> dict | None:
    if not horse:
        return None
    meta = race.get("race_meta") or {}
    time_key = _norm_key(meta.get("time") or race.get("race_time"))
    race_key = _norm_key(meta.get("name") or race.get("race_name"))
    horse_key = _norm_key(horse)
    return (
        index.get("by_triplet", {}).get((time_key, race_key, horse_key))
        or index.get("by_time_horse", {}).get((time_key, horse_key))
        or index.get("by_race_horse", {}).get((race_key, horse_key))
        or index.get("by_horse", {}).get(horse_key)
    )


def _attach_market_prices(date: str, scores: list[dict], market_index: dict, course_display: str = VENUE) -> list[dict]:
    priced_scores = []
    for race in scores:
        normalized = _normalize_race_meta(race, course_display)
        runners = []
        for runner in normalized.get("ranked_runners", []) or []:
            runner_copy = dict(runner)
            price = _market_price_for(market_index, normalized, runner_copy.get("horse"))
            if price:
                runner_copy["market_price"] = price
            runners.append(runner_copy)
        priced_scores.append({**normalized, "ranked_runners": runners})
    return priced_scores


def _with_market_price(item: dict | None, market_index: dict) -> dict | None:
    if not item:
        return item
    race = {"race_id": item.get("race_id"), "race_time": item.get("race_time"), "race_name": item.get("race_name")}
    price = _market_price_for(market_index, race, item.get("horse")) or market_index.get("by_horse", {}).get(_norm_key(item.get("horse")))
    if not price:
        return item
    updated = dict(item)
    updated["market_price"] = price
    if price.get("fractional"):
        updated["odds_fractional"] = price["fractional"]
    if price.get("decimal"):
        updated["odds_decimal"] = price["decimal"]
    return updated


def _market_summary(date: str, snapshot: dict, market_index: dict) -> dict:
    snapshot_iso = snapshot.get("generated") or (snapshot.get("_meta") or {}).get("generated_at") or ""
    if not snapshot_iso:
        return {"snapshot_iso": "", "odds_label": ""}
    time_label = _snapshot_time_label(snapshot_iso)
    source_mix = _source_mix_label(market_index.get("prices", []))
    return {
        "snapshot_iso": snapshot_iso,
        "odds_label": f"Odds as of {time_label}, source: {source_mix}" if source_mix else f"Odds as of {time_label}",
    }


def _snapshot_time_label(snapshot_iso: str) -> str:
    try:
        dt = datetime.fromisoformat(snapshot_iso)
    except ValueError:
        return snapshot_iso
    suffix = " BST" if dt.utcoffset() and dt.utcoffset().total_seconds() == 3600 else ""
    return dt.strftime("%H:%M") + suffix


def _source_mix_label(prices: list[dict]) -> str:
    names: list[str] = []
    for price in prices:
        if not price.get("fresh") or not price.get("fractional"):
            continue
        bookmaker = price.get("bookmaker") or ""
        source = price.get("source") or ""
        if "FanOdds" in bookmaker or "fanodds" in source.lower():
            names.append("FanOdds")
        for part in bookmaker.split(","):
            part = part.strip()
            if part and not part.startswith("FanOdds"):
                names.append(part)
    unique = sorted(dict.fromkeys(names))
    if len(unique) > 3:
        return f"{', '.join(unique[:3])} +{len(unique) - 3}"
    return ", ".join(unique)


# ---------------------------------------------------------------------------
# Race-dict normalisation
# ---------------------------------------------------------------------------


def _normalize_race_meta(race: dict, course_display: str = VENUE) -> dict:
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
        "course":   race.get("course", course_display),
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


def render_trifecta_box(trifecta: dict) -> str:
    """Return an HTML snippet for a trifecta box section.

    Parameters
    ----------
    trifecta:
        Dict with keys:
          race_name    : str  e.g. "Betfred Derby"
          race_time    : str  e.g. "16:00 BST Sat 6 Jun 2026"
          horses       : list of dicts, each: {rank, horse, trainer, odds_stale, why}
          combinations : int  e.g. 24
          stake_per_combo : float e.g. 1.0
          total_outlay : float e.g. 24.0
          conviction   : str  e.g. "Medium"
          conviction_note : str  one-line rationale
          going_contingency : str  optional — note for going-triggered reduction
          outsider_note     : str  optional — note about EW double-up
          odds_vintage      : str  e.g. "2026-06-02"

    Returns
    -------
    str
        Self-contained HTML ``<tr>`` row (colspan=8) for insertion into a
        ``.slip`` table.  The caller is responsible for including the companion
        CSS classes (``trifecta-box``, ``trifecta-horses``, etc.) in the
        stylesheet — these are defined in ``src/templates/style.css``.
    """
    if not trifecta:
        return ""

    race_name    = trifecta.get("race_name", "")
    race_time    = trifecta.get("race_time", "")
    horses       = trifecta.get("horses", [])
    combinations = trifecta.get("combinations", 0)
    stake        = trifecta.get("stake_per_combo", 1.0)
    total        = trifecta.get("total_outlay", 0.0)
    conviction   = trifecta.get("conviction", "")
    conv_note    = trifecta.get("conviction_note", "")
    going_note   = trifecta.get("going_contingency", "")
    outsider_note = trifecta.get("outsider_note", "")
    odds_vintage = trifecta.get("odds_vintage", "")

    horse_rows = ""
    for h in horses:
        rank    = h.get("rank", "")
        name    = h.get("horse", "")
        trainer = h.get("trainer", "—")
        odds    = h.get("odds_stale") or "—"
        why     = h.get("why", "")
        outsider_flag = " ⚡" if h.get("is_outsider") else ""
        horse_rows += (
            f"<tr>"
            f"<td>{rank}</td>"
            f"<td><strong>{name}</strong>{outsider_flag}</td>"
            f"<td>{trainer}</td>"
            f"<td>~{odds}</td>"
            f"<td>{why}</td>"
            f"</tr>\n"
        )

    going_html = ""
    if going_note:
        going_html = f'<div class="tnote">🌧 <strong>Going contingency:</strong> {going_note}</div>'

    outsider_html = ""
    if outsider_note:
        outsider_html = f'<div class="tnote">⚡ {outsider_note}</div>'

    stale_html = ""
    if odds_vintage:
        stale_html = (
            f'<div class="stale-caveat">⚠️ <strong>Stale-odds caveat:</strong> '
            f"All odds are {odds_vintage} morning quotes. Saturday SP could shift materially. "
            f"Selection is FORM-driven and valid; trifecta dividend cannot be projected from these quotes.</div>"
        )

    conviction_upper = conviction.upper() if conviction else "MEDIUM"

    return (
        f'<!-- ═══ TRIFECTA BOX: {race_name} ═══ -->\n'
        f'<tr class="row-trifecta">\n'
        f'  <td colspan="8">\n'
        f'    <div class="trifecta-box">\n'
        f'      <h3>🎰 {race_name} Trifecta Box — {race_time}</h3>\n'
        f'      <div class="trifecta-summary">\n'
        f'        <div class="ts-item"><span class="ts-label">Box: </span>'
        f'<span class="ts-value">'
        + " · ".join(h.get("horse", "") for h in horses)
        + f' ({len(horses)} horses)</span></div>\n'
        f'        <div class="ts-item">'
        f'<span class="ts-label">Combos: </span><span class="ts-value">{combinations}</span>&nbsp;·&nbsp;'
        f'<span class="ts-label">Stake/combo: </span><span class="ts-value">£{stake:.2f}</span>&nbsp;·&nbsp;'
        f'<span class="ts-label">Total outlay: </span><span class="ts-outlay">£{total:.2f}</span>'
        f'</div>\n'
        f'        <div class="ts-item"><span class="trifecta-conviction">{conviction_upper}</span>'
        f'<span style="font-size:7.6pt;color:#555">{conv_note}</span></div>\n'
        f'      </div>\n'
        f'      <table class="trifecta-horses">\n'
        f'        <thead><tr><th>#</th><th>Horse</th><th>Trainer</th>'
        f'<th>Odds (stale)</th><th>Why included</th></tr></thead>\n'
        f'        <tbody>\n{horse_rows}'
        f'        </tbody>\n'
        f'      </table>\n'
        f'      <div class="trifecta-notes">\n'
        f'{outsider_html}\n{going_html}\n{stale_html}\n'
        f'      </div>\n'
        f'    </div>\n'
        f'  </td>\n'
        f'</tr>\n'
        f'<!-- ═══ END TRIFECTA BOX ═══ -->\n'
    )


def _parse_stake_amount(s: str | None) -> float:
    """Extract the leading £/$/€ amount from a stake_guidance or total_stake string.

    Examples::

        "£1.00 WIN"                        → 1.0
        "£0.25 EW (min stake)"             → 0.25
        "$6.00 total ($1.00 x 6 combos)"  → 6.0
        "£6.00"                            → 6.0
        None / ""                          → 0.0
    """
    return parse_money(s)


def render_header(bets_data: dict) -> dict:
    """Compute all header display values from a ``bets-{date}.json`` dict.

    AUTHORIZED: any change to header fields — totals, NR line, validation tag,
    bet count — is in scope for Linus whenever bets JSON changes.
    No coordinator escalation required.

    Handles Linus schema (``"meta": {...}, "entries": [...]`` or ``"bets": [...]``)
    and derives equivalent entries from legacy Badger ``singles``/``portfolio_summary``
    payloads during the migration.  If ``meta`` is absent the renderer falls back
    gracefully: course defaults to the configured default course, validation to ``None``.

    Parameters
    ----------
    bets_data:
        Parsed contents of ``outputs/bets-{date}.json``.

    Returns
    -------
    dict with keys:
        ``winew_outlay``      – float: SUM of WIN/EW stakes (EW doubled).
        ``trifecta_outlay``   – float | None: trifecta total stake, or None.
        ``total_outlay``      – float: winew_outlay + (trifecta_outlay or 0).
        ``active_bet_count``  – int: count of WIN + EW entries.
        ``nr_horses``         – list[dict]: entries with status NR or VOID.
        ``validation_tag``    – str | None: from meta.validation or root field.
        ``trifecta_horses``   – list[str]: horse names in the trifecta box.
        ``course``            – str: from meta.course, default course display name.

    Notes
    -----
    - Entries with status ``NO_BET`` or ``REFUNDED`` are silently ignored.
    - Entries with status ``NR`` or ``VOID`` appear in ``nr_horses`` and are
      excluded from stake totals.
    - EW unit stake is doubled (win side + place side = 2× the quoted amount).
    - Trifecta stake is read from ``entry["total_stake"]``; falls back to
      ``entry["stake_guidance"]``.
    """
    entries = schema_entries(bets_data)
    meta = bets_data.get("meta") or {}

    course = meta.get("course") or VENUE

    # Validation tag: prefer meta.validation, then saul_validation_status if
    # it looks like an approval (contains "GO" or "PASS").
    validation_tag: str | None = meta.get("validation")
    if not validation_tag:
        svs = str(bets_data.get("saul_validation_status") or "")
        if "GO" in svs.upper() or "PASS" in svs.upper():
            validation_tag = svs

    winew_total = 0.0
    trifecta_total = 0.0
    active_bets = 0
    nr_horses: list[dict] = []
    trifecta_horses: list[str] = []

    for entry in entries:
        status = str(entry.get("status") or "").upper()
        pick = entry.get("pick")
        bet_type = str(entry.get("bet_type") or "").lower()

        # NR / VOID entries → list them, exclude from totals.
        if status in ("NR", "VOID") and pick:
            nr_horses.append({
                "horse": pick,
                "status": status,
                "race_time": entry.get("race_time") or "",
                "rationale": entry.get("rationale_short") or "",
            })
            continue

        # Skip no-bet / refunded / un-picked entries.
        if status in ("VOID", "REFUNDED", "NO_BET") or not pick:
            continue

        # Trifecta box entries.
        if status == "TRIFECTA" or bet_type == "trifecta_box":
            stake_str = entry.get("total_stake") or entry.get("stake_guidance") or ""
            trifecta_total += _parse_stake_amount(stake_str)
            trifecta_horses = [
                h.get("horse", "") for h in (entry.get("horses") or [])
            ]
            continue

        if status in MULTI_STATUSES or bet_type in MULTI_TYPES:
            winew_total += _parse_stake_amount(entry.get("total_stake") or entry.get("stake_guidance") or entry.get("combined_stake_gbp"))
            active_bets += 1
            continue

        # Regular WIN / EW bets.
        if status in ("WIN", "EW"):
            unit = _parse_stake_amount(entry.get("stake_guidance") or "")
            # EW = two sides (win + place) at the quoted unit stake each.
            winew_total += unit * 2 if status == "EW" else unit
            active_bets += 1

    trifecta_outlay: float | None = round(trifecta_total, 2) if trifecta_total else None
    total_outlay = round(winew_total + trifecta_total, 2)

    return {
        "winew_outlay": round(winew_total, 2),
        "trifecta_outlay": trifecta_outlay,
        "total_outlay": total_outlay,
        "active_bet_count": active_bets,
        "nr_horses": nr_horses,
        "validation_tag": validation_tag,
        "trifecta_horses": trifecta_horses,
        "course": course,
    }


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
