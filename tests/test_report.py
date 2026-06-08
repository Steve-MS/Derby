"""
test_report.py — smoke tests for the HTML report renderer.

Run:  pytest tests/test_report.py -q
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import guard — skip whole module if jinja2 not installed
# ---------------------------------------------------------------------------
jinja2 = pytest.importorskip("jinja2", reason="jinja2 not installed")

# sys.path manipulation so tests can run from the repo root without install
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.report import render  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_RUNNER_1 = {
    "rank": 1,
    "horse": "City Of Troy",
    "trainer": "A P O'Brien",
    "jockey": "R Moore",
    "score": 82.5,
    "raw_signal_values": {
        "class_rating":    88.0,
        "recent_form":     75.0,
        "trainer_form":    100.0,
        "jockey":          100.0,
        "course_distance": 70.0,
        "going":           80.0,
        "going_fit":       72.0,
        "draw_bias":       50.0,
        "class_move":      50.0,
    },
    "score_breakdown": {
        "class_rating": 30.8, "recent_form": 15.0, "trainer_form": 10.0,
        "jockey": 10.0, "course_distance": 7.0, "going": 4.0,
        "going_fit": 10.8, "draw_bias": 2.5, "class_move": 2.5,
    },
    "missing_data_flags": [],
}

SAMPLE_RUNNER_2 = {
    "rank": 2,
    "horse": "Item",
    "trainer": "Andrew Balding",
    "jockey": "D Egan",
    "score": 68.3,
    "raw_signal_values": {
        "class_rating":    72.0,
        "recent_form":     80.0,
        "trainer_form":    80.0,
        "jockey":          0.0,
        "course_distance": 50.0,
        "going":           55.0,
        "going_fit":       35.0,
        "draw_bias":       50.0,
        "class_move":      50.0,
    },
    "score_breakdown": {},
    "missing_data_flags": [],
}

SAMPLE_RACE = {
    "race_id": "epsom-2026-06-06-1600",
    "race_meta": {
        "time": "16:00",
        "name": "Betfred Derby (Group 1)",
        "distance_f": 12,
        "going": "Good to Firm",
        "class": "Group 1",
        "prize_winner_gbp": 1000000,
        "runner_count": 17,
    },
    "ranked_runners": [SAMPLE_RUNNER_1, SAMPLE_RUNNER_2],
    "confidence": "HIGH",
    "bet_recommendation": "WIN",
    "race_stdev": 14.2,
    "race_competitiveness": "CLEAR FAVOURITE",
}

SAMPLE_BETS = {
    "singles": [
        {
            "race_id": "epsom-2026-06-06-1600",
            "horse": "City Of Troy",
            "bet_type": "WIN",
            "stake_gbp": 10.0,
            "price": "7/4",
            "est_return_gbp": 27.50,
        }
    ],
    "doubles": [
        {
            "label": "Dbl: City Of Troy / Benvenuto Cellini",
            "legs": [
                "epsom-2026-06-06-1600|City Of Troy",
                "epsom-2026-06-06-1430|Benvenuto Cellini",
            ],
            "stake_gbp": 3.00,
            "est_return_gbp": 45.00,
        }
    ],
    "trebles": [],
    "accas": [],
    "lucky15": None,
    "portfolio_summary": {
        "total_stake_gbp": 25.0,
        "est_total_return_gbp": 180.0,
        "edge_pct": 8.5,
        "bankroll_pct": 25.0,
        "bankroll_default_gbp": 100.0,
    },
}

SAMPLE_CONTEXT = {
    "going_saturday": "Good; good to firm in places",
    "narrative_saturday": (
        "Derby Day: fast ground expected. Benvenuto Cellini favourite at 9/4. "
        "O'Brien fields seven runners. Strong wind may affect younger 3yos."
    ),
    "backtest_verdict": None,
    "model_version": "v0.1",
    "generated_at": "2026-06-06T08:00",
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

_UNSET = object()


def _render_to_tmp(
    date: str = "2026-06-06",
    scores: list | None = _UNSET,
    bets: dict | None = _UNSET,
    context: dict | None = _UNSET,
) -> str:
    """Render into a temp file and return the HTML content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "report.html")
        render(
            date=date,
            scores=scores if scores is not _UNSET else [SAMPLE_RACE],
            bets=bets if bets is not _UNSET else SAMPLE_BETS,
            race_context=context if context is not _UNSET else SAMPLE_CONTEXT,
            output_path=out,
        )
        return Path(out).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRenderEmptyInputs:
    """render() must produce valid HTML even with fully empty inputs."""

    def test_empty_produces_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "empty.html")
            render("2026-06-05", [], {}, {}, out)
            assert os.path.exists(out)

    def test_empty_is_valid_html(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "empty.html")
            render("2026-06-05", [], {}, {}, out)
            content = Path(out).read_text(encoding="utf-8")
            assert content.strip().startswith("<!DOCTYPE html>")
            assert "<html" in content
            assert "</html>" in content

    def test_empty_has_required_sections(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "empty.html")
            render("2026-06-05", [], {}, {}, out)
            html = Path(out).read_text(encoding="utf-8")
            assert "hero" in html
            assert "disclaimer" in html or "entertainment" in html.lower()

    def test_empty_none_bets_and_context(self):
        """None inputs must not raise — treated as empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "none.html")
            render("2026-06-06", [], None, None, out)
            assert os.path.exists(out)


class TestRenderDateDisplay:
    """Date and day-name rendering."""

    def test_oaks_day_name(self):
        html = _render_to_tmp(date="2026-06-05", scores=[], bets={}, context={})
        assert "Oaks Day" in html

    def test_derby_day_name(self):
        html = _render_to_tmp(date="2026-06-06", scores=[], bets={}, context={})
        assert "Derby Day" in html

    def test_date_in_output(self):
        html = _render_to_tmp(date="2026-06-06", scores=[], bets={}, context={})
        assert "2026" in html
        assert "Epsom" in html


def test_report_renders_market_latest_price_in_runner_context():
    """Renderer pulls a best price from market-latest.json into runner output."""
    market = {
        "generated": "2026-06-04T16:41:23+01:00",
        "horses": {
            "2026_06_06": {
                "1600_derby": {
                    "city_of_troy": {
                        "horse": "City Of Troy",
                        "race_date": "2026-06-06",
                        "race_name": "Betfred Derby (Group 1)",
                        "off_time": "16:00",
                        "best_price_decimal": 5.0,
                        "best_price_fractional": "4/1",
                        "bookmaker": "Betfred",
                        "source": "JustBookies best-price comparison",
                        "retrieved_at": "2026-06-04T16:41:23+01:00",
                        "fresh": True,
                        "status": "priced",
                    }
                }
            }
        },
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        market_path = tmp / "market-latest.json"
        out = tmp / "report.html"
        market_path.write_text(json.dumps(market), encoding="utf-8")
        render(
            date="2026-06-06",
            scores=[SAMPLE_RACE],
            bets=SAMPLE_BETS,
            race_context=SAMPLE_CONTEXT,
            output_path=str(out),
            market_latest_path=str(market_path),
        )
        html = out.read_text(encoding="utf-8")
    assert "Best Price" in html
    assert "4/1" in html
    assert "Betfred" in html
    assert "Odds snapshot: 2026-06-04T16:41:23+01:00" in html


class TestRenderSections:
    """Key sections must appear when data is present."""

    def test_hero_section(self):
        html = _render_to_tmp()
        assert 'class="hero"' in html

    def test_race_block_present(self):
        html = _render_to_tmp()
        assert 'class="race-block"' in html

    def test_race_name_in_output(self):
        html = _render_to_tmp()
        assert "Betfred Derby" in html

    def test_runner_names_in_output(self):
        html = _render_to_tmp()
        assert "City Of Troy" in html
        assert "Item" in html

    def test_score_bar_present(self):
        html = _render_to_tmp()
        assert "score-bar" in html

    def test_confidence_chip_present(self):
        html = _render_to_tmp()
        assert "conf-HIGH" in html

    def test_recommendation_chip_present(self):
        html = _render_to_tmp()
        assert "rec-WIN" in html

    def test_signal_breakdown_present(self):
        html = _render_to_tmp()
        assert "signal-bar" in html
        assert "Class / Rating" in html

    def test_top_pick_panel_present(self):
        html = _render_to_tmp()
        assert "top-pick" in html
        assert "City Of Troy" in html

    def test_context_narrative_present(self):
        html = _render_to_tmp()
        assert "Derby Day" in html
        assert "Good; good to firm" in html

    def test_disclaimer_present(self):
        html = _render_to_tmp()
        assert "18+" in html
        assert "entertainment" in html.lower()


class TestRenderBets:
    """Betting sections appear when bets are provided."""

    def test_singles_table_present(self):
        html = _render_to_tmp()
        assert "Singles" in html

    def test_doubles_table_present(self):
        html = _render_to_tmp()
        assert "Doubles" in html

    def test_portfolio_summary_present(self):
        html = _render_to_tmp()
        assert "Day Portfolio" in html
        assert "£25.00" in html  # total stake

    def test_race_bet_in_race_block(self):
        html = _render_to_tmp()
        # The race-level bet section should appear inside the race block
        assert "Recommended Bets" in html

    def test_bets_omitted_when_empty(self):
        html = _render_to_tmp(bets={})
        assert "Day Portfolio" not in html
        assert "Singles" not in html

    def test_bets_omitted_when_none(self):
        html = _render_to_tmp(bets=None)
        assert "Day Portfolio" not in html


class TestRenderVerdictBadge:
    """Backtest verdict badge rendering."""

    def test_green_verdict(self):
        ctx = {**SAMPLE_CONTEXT, "backtest_verdict": "GREEN"}
        html = _render_to_tmp(context=ctx)
        assert "verdict-GREEN" in html
        assert "Trusted" in html

    def test_red_verdict(self):
        ctx = {**SAMPLE_CONTEXT, "backtest_verdict": "RED"}
        html = _render_to_tmp(context=ctx)
        assert "verdict-RED" in html

    def test_no_verdict_shows_not_validated(self):
        ctx = {**SAMPLE_CONTEXT, "backtest_verdict": None}
        html = _render_to_tmp(context=ctx)
        assert "Not yet validated" in html


class TestRenderSelfContained:
    """Output must be self-contained — no external file references."""

    def test_no_external_css_link(self):
        html = _render_to_tmp()
        # Should have inline <style> not a <link rel="stylesheet">
        assert '<link rel="stylesheet"' not in html
        assert "<style>" in html

    def test_css_inlined(self):
        html = _render_to_tmp()
        # CSS variables defined inline
        assert "--green:" in html

    def test_no_external_script_src(self):
        html = _render_to_tmp()
        assert re.search(r'<script[^>]+src=', html) is None


class TestRenderOutputPath:
    """Output path handling."""

    def test_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = os.path.join(tmpdir, "outputs", "reports", "report.html")
            render("2026-06-06", [], {}, {}, nested)
            assert os.path.exists(nested)

    def test_writes_utf8(self):
        html = _render_to_tmp()
        assert "O&#39;Brien" in html or "O'Brien" in html  # Jinja autoescape


class TestRenderMultipleRaces:
    """Multiple races in a card."""

    def test_two_races(self):
        race2 = {
            **SAMPLE_RACE,
            "race_id": "epsom-2026-06-06-1430",
            "race_meta": {
                **SAMPLE_RACE["race_meta"],
                "time": "14:30",
                "name": "Coronation Cup (Group 1)",
            },
        }
        html = _render_to_tmp(scores=[SAMPLE_RACE, race2])
        assert html.count('class="race-block"') == 2
        assert "Betfred Derby" in html
        assert "Coronation Cup" in html


# ---------------------------------------------------------------------------
# Outsider helper unit tests
# ---------------------------------------------------------------------------

class TestRaceOutsiderHelper:
    """Unit tests for _race_outsider_for()."""

    def setup_method(self):
        from src.report import _race_outsider_for
        self.fn = _race_outsider_for

    def _bets(self, outsiders):
        return {"outsiders": outsiders}

    def test_returns_outsider_for_matching_race(self):
        entry = {
            "race_id": "epsom-2026-06-06-1600",
            "outsider_pick": "Dark Horse",
            "horse": "Dark Horse",
            "stake_gbp": 0.25,
        }
        result = self.fn("epsom-2026-06-06-1600", self._bets([entry]))
        assert result is entry

    def test_returns_none_when_race_not_found(self):
        entry = {"race_id": "epsom-2026-06-06-1600", "outsider_pick": "X"}
        assert self.fn("epsom-2026-06-06-9999", self._bets([entry])) is None

    def test_returns_none_when_outsider_pick_null(self):
        entry = {"race_id": "epsom-2026-06-06-1600", "outsider_pick": None}
        assert self.fn("epsom-2026-06-06-1600", self._bets([entry])) is None

    def test_returns_none_when_bets_empty_dict(self):
        assert self.fn("epsom-2026-06-06-1600", {}) is None

    def test_returns_none_when_bets_none(self):
        assert self.fn("epsom-2026-06-06-1600", None) is None

    def test_returns_none_when_race_id_empty(self):
        entry = {"race_id": "epsom-2026-06-06-1600", "outsider_pick": "X"}
        assert self.fn("", self._bets([entry])) is None

    def test_returns_none_when_outsiders_key_absent(self):
        assert self.fn("epsom-2026-06-06-1600", {"singles": []}) is None

    def test_first_matching_entry_returned(self):
        """When two entries share race_id, the first qualifying one wins."""
        e1 = {"race_id": "epsom-2026-06-06-1600", "outsider_pick": "Alpha"}
        e2 = {"race_id": "epsom-2026-06-06-1600", "outsider_pick": "Beta"}
        result = self.fn("epsom-2026-06-06-1600", self._bets([e1, e2]))
        assert result is e1


# ---------------------------------------------------------------------------
# Outsider rendering tests
# ---------------------------------------------------------------------------

SAMPLE_OUTSIDER = {
    "race_id": "epsom-2026-06-06-1600",
    "race_name": "Betfred Derby (Group 1)",
    "race_time": "16:00",
    "horse": "Dark Horse",
    "trainer": "J Smith",
    "jockey": "R Dooley",
    "morning_price": 13.0,
    "odds_source": "estimated",
    "model_rank": 2,
    "market_rank": 6,
    "rank_delta": 4,
    "bet_type": "EW",
    "stake_pts": 0.25,
    "stake_gbp": 0.25,
    "ew_terms": "1/4 odds, 1-1-2-3",
    "potential_return_gbp_win": 3.25,
    "potential_return_gbp_place": 1.0,
    "rationale": "Model rates 2; market rates 6. Disagreement of 4 ranks — value play.",
    "outsider_pick": "Dark Horse",
}

SAMPLE_BETS_WITH_OUTSIDERS = {
    **SAMPLE_BETS,
    "outsiders": [SAMPLE_OUTSIDER],
    "portfolio_summary": {
        **SAMPLE_BETS["portfolio_summary"],
        "outsider_summary": {
            "count": 1,
            "total_stake_gbp": 0.5,
            "total_potential_return_gbp_win": 3.25,
            "total_potential_return_gbp_place": 1.0,
        },
    },
}

SAMPLE_BETS_NULL_OUTSIDER = {
    **SAMPLE_BETS,
    "outsiders": [
        {"race_id": "epsom-2026-06-06-1600", "outsider_pick": None,
         "outsider_rationale": "Top 3 in market also top 3 on model — no value outsider"},
    ],
    "portfolio_summary": {
        **SAMPLE_BETS["portfolio_summary"],
        "outsider_summary": {"count": 0, "total_stake_gbp": 0.0,
                              "total_potential_return_gbp_win": 0.0,
                              "total_potential_return_gbp_place": 0.0},
    },
}


class TestRenderOutsider:
    """Outsider block rendering."""

    def test_outsider_block_renders_when_present(self):
        html = _render_to_tmp(bets=SAMPLE_BETS_WITH_OUTSIDERS)
        assert 'class="outsider-pick"' in html
        assert "Dark Horse" in html

    def test_outsider_trainer_shown(self):
        html = _render_to_tmp(bets=SAMPLE_BETS_WITH_OUTSIDERS)
        assert "J Smith" in html

    def test_outsider_morning_price_shown(self):
        html = _render_to_tmp(bets=SAMPLE_BETS_WITH_OUTSIDERS)
        assert "13.0" in html

    def test_outsider_odds_source_badge_shown(self):
        html = _render_to_tmp(bets=SAMPLE_BETS_WITH_OUTSIDERS)
        assert "odds-source-badge" in html
        assert "estimated" in html

    def test_outsider_ew_terms_shown(self):
        html = _render_to_tmp(bets=SAMPLE_BETS_WITH_OUTSIDERS)
        assert "1/4 odds" in html

    def test_outsider_rank_delta_visualised(self):
        html = _render_to_tmp(bets=SAMPLE_BETS_WITH_OUTSIDERS)
        # Should show model rank, market rank, and delta
        assert "Model: 2" in html
        assert "Market: 6" in html
        assert "+4" in html

    def test_outsider_potential_return_shown(self):
        html = _render_to_tmp(bets=SAMPLE_BETS_WITH_OUTSIDERS)
        assert "£3.25" in html   # win return
        assert "£1.00" in html   # place return

    def test_outsider_rationale_shown(self):
        html = _render_to_tmp(bets=SAMPLE_BETS_WITH_OUTSIDERS)
        assert "Disagreement of 4 ranks" in html

    def test_outsider_block_absent_when_no_outsiders_key(self):
        html = _render_to_tmp(bets=SAMPLE_BETS)  # SAMPLE_BETS has no outsiders
        assert 'class="outsider-pick"' not in html

    def test_outsider_block_absent_when_outsiders_list_empty(self):
        bets = {**SAMPLE_BETS, "outsiders": []}
        html = _render_to_tmp(bets=bets)
        assert 'class="outsider-pick"' not in html

    def test_outsider_block_absent_when_null_pick(self):
        html = _render_to_tmp(bets=SAMPLE_BETS_NULL_OUTSIDER)
        assert 'class="outsider-pick"' not in html

    def test_outsider_block_absent_when_bets_empty(self):
        html = _render_to_tmp(bets={})
        assert 'class="outsider-pick"' not in html

    def test_outsider_block_absent_when_bets_none(self):
        html = _render_to_tmp(bets=None)
        assert 'class="outsider-pick"' not in html

    def test_portfolio_outsider_summary_rendered(self):
        html = _render_to_tmp(bets=SAMPLE_BETS_WITH_OUTSIDERS)
        assert "outsider-portfolio-card" in html
        assert "separate bankroll" in html
        assert "1 pick" in html

    def test_portfolio_outsider_summary_omitted_when_count_zero(self):
        html = _render_to_tmp(bets=SAMPLE_BETS_NULL_OUTSIDER)
        assert 'class="portfolio-card outsider-portfolio-card"' not in html

    def test_portfolio_outsider_summary_omitted_when_key_absent(self):
        # portfolio_summary without outsider_summary key
        bets = {**SAMPLE_BETS_WITH_OUTSIDERS,
                "portfolio_summary": {**SAMPLE_BETS["portfolio_summary"]}}
        html = _render_to_tmp(bets=bets)
        assert 'class="portfolio-card outsider-portfolio-card"' not in html

    def test_fallback_dash_when_model_rank_missing(self):
        """Missing model_rank/market_rank must not crash — renders '—'."""
        entry = {**SAMPLE_OUTSIDER}
        del entry["model_rank"]
        del entry["market_rank"]
        del entry["rank_delta"]
        bets = {**SAMPLE_BETS_WITH_OUTSIDERS, "outsiders": [entry]}
        html = _render_to_tmp(bets=bets)
        assert "outsider-pick" in html
        assert "—" in html

    def test_fallback_when_optional_fields_missing(self):
        """Outsider with only required fields must render without crashing."""
        minimal = {
            "race_id": "epsom-2026-06-06-1600",
            "outsider_pick": "Bare Minimum",
            "horse": "Bare Minimum",
        }
        bets = {**SAMPLE_BETS, "outsiders": [minimal]}
        html = _render_to_tmp(bets=bets)
        assert "Bare Minimum" in html
        assert "outsider-pick" in html

    def test_unknown_race_not_in_output(self):
        """Regression: 'Unknown Race' must not appear (shim from prior sprint)."""
        html = _render_to_tmp()
        assert "Unknown Race" not in html
