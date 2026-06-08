# Livingston-7 Ascot v0.4 #6 E2E Smoke

Status: COMPLETE
Verdict: PIPELINE-WORKS-WITH-ROUGH-EDGES
Started: 2026-06-08T12:45:00+01:00
Completed: 2026-06-08T12:45:00+01:00
Requested by: Steve via Coordinator
Scope: Synthetic Royal Ascot 2026 Day 1, Tuesday 2026-06-16

## Fixture paths

- Permanent test asset: `tests/fixtures/ascot/raw-ascot-2026-06-16-racecards.json`
- Working raw copy: `data/raw/ascot-2026-06-16-racecards.json`
- Shape: mirrors `data/raw/epsom-2026-06-06-racecards.json` top-level racecard shape.
- Contents: synthetic notice, Royal Ascot 2026, Ascot, Day 1, Good to Firm, 6 races, 48 fake runners.
- Distances exercised: 5f, 6f, 8f, 10f, 12f.

## Stub enrichment

No `scripts/enrich_*.py` consumer exists. I ran the configured scraper dry-runs and wrote synthetic enrichment stubs so downstream watchdog/artifact checks had data:

- `data/enrichment/live-runners-ascot-2026-06-16.json`
- `data/enrichment/racingpost-ascot-2026-06-16.json`
- `data/enrichment/sportinglife-ascot-2026-06-16.json`
- `data/enrichment/going-ascot-2026-06-16.json`

## Pipeline command transcript

```text
> python scripts\scrape_racingpost.py --course=ascot --meeting=royal-ascot-2026 --date=2026-06-16 --dry-run
planned URL: https://www.racingpost.com/racecards/1/ascot/2026-06-16
planned output: data\enrichment\racingpost-ascot-2026-06-16.json
exit 0

> python scripts\scrape_sportinglife.py --course=ascot --meeting=royal-ascot-2026 --date=2026-06-16 --dry-run
planned URL: https://www.sportinglife.com/racing/racecards/2026-06-16/ascot
planned output: data\enrichment\sportinglife-ascot-2026-06-16.json
exit 0

> python -m src.cli fetch --course=ascot --meeting=royal-ascot-2026 --date=2026-06-16
Racecard found: data\raw\ascot-2026-06-16-racecards.json
exit 0

> python -m src.cli score --course=ascot --meeting=royal-ascot-2026 --date=2026-06-16
Scored 6 races -> outputs\scores-ascot-2026-06-16.json
Top scores by race: Northbank Verse 95.0; Bright Borough 95.0; Rapid Lantern 95.0; Cobalt Monarch 95.0; Mersey Plan 95.0; Atlas Window 95.0
exit 0

> python -m src.cli predict --course=ascot --meeting=royal-ascot-2026 --date=2026-06-16 --bankroll 100
Bets written -> outputs\bets-ascot-2026-06-16.json
exit 0

> python -m src.cli report --course=ascot --meeting=royal-ascot-2026 --date=2026-06-16
Report written -> outputs\report-ascot-2026-06-16.html
exit 0

> python -m src.cli card --course=ascot --meeting=royal-ascot-2026 --date=2026-06-16
Race card written -> outputs\racecard-ascot-2026-06-16.html
exit 0
```

## Output dump / screenshot-equivalent

```json
{
  "report_html": {
    "title": "Race Analysis - Royal Ascot 2026 16 June 2026",
    "h1": "Royal Ascot 2026 - 16 June 2026",
    "subtitle": "Day 1",
    "first_3_race_headings_from_html": [
      "14:30 Synthetic Queen Anne Stakes (Group 1)",
      "15:05 Synthetic Coventry Stakes (Group 2)",
      "15:40 Synthetic King Charles III Stakes (Group 1)"
    ],
    "first_race_top3_with_scores": [
      {"horse": "Northbank Verse", "score": 95.0},
      {"horse": "Violet Cartographer", "score": 73.09},
      {"horse": "Glass Meridian", "score": 71.57}
    ],
    "top3_present_in_report_html": true
  },
  "racecard_html": {
    "title": "Royal Ascot 2026 Day 1 - Betting Slip - 16 June 2026",
    "h1": "Royal Ascot 2026 - Day 1",
    "subtitle": "16 June 2026, 6 races, Going: TBC",
    "first_3_betting_rows_from_html": [
      "14:30 Synthetic Queen Anne Stakes - EW Northbank Verse",
      "15:40 Synthetic King Charles III Stakes - EW Red Voltage",
      "16:20 Synthetic St James's Palace Stakes - WIN Cobalt Monarch"
    ],
    "first_race_top3_with_scores": [
      {"horse": "Northbank Verse", "score": 95.0},
      {"horse": "Violet Cartographer", "score": 73.09},
      {"horse": "Glass Meridian", "score": 71.57}
    ],
    "top3_present_in_racecard_html": false,
    "note": "Racecard is a betting slip, not a ranked-score table. It renders betting rows, not first-race top-3 scores."
  },
  "scoring_neutrality": {
    "score_min": 5.0,
    "score_max": 95.0,
    "unique_scores": 38,
    "draw_signals": [50.0],
    "course_distance_signals": [50.0],
    "trial_form_signals": [50.0]
  }
}
```

## Integration findings

1. Core pipeline works for non-Epsom: fetch, score, predict, report, and card all complete for `--course=ascot --meeting=royal-ascot-2026 --date=2026-06-16`.
2. Scores are non-trivial: 48 runners, score range 5.0 to 95.0, 38 unique scores. Ascot neutral priors are actually neutral for draw, course/distance, and trial form; all three signals are fixed at 50.0.
3. Scoring flows into report correctly: first-race top 3 and scores from `outputs\scores-ascot-2026-06-16.json` appear in `outputs\report-ascot-2026-06-16.html`.
4. Branding is mostly Ascot-aware: generated filenames are course-prefixed, title/h1 use Royal Ascot 2026, and Day 1 appears in the racecard title/h1. Report subtitle is Day 1.
5. Rough edge: report footer still picks up the default `data/enrichment/market-latest.json` odds snapshot from Epsom/2026-06-06 because `src.cli report` does not pass a course-prefixed market snapshot path.
6. Rough edge: report CSS contains a non-user-facing hardcoded comment `Derby Weekend 2026`.
7. Rough edge: `src.cli predict` writes the older betting schema (`singles`, `portfolio_summary`) without `meta` and without `bets`/`entries`; T-60 `render_header()` expects the Linus header schema, computes 0.00, and flags a mismatch.
8. Rough edge: `src.cli card` does not pass `bets_json_path`, so the JSON-driven header/trifecta path is not exercised by the actual CLI card command. The racecard shows WIN/EW betting rows, but no trifecta box was produced from the actual `predict` output.
9. Rough edge: no CLI step produced `outputs\slip-ascot-2026-06-16.txt`, so the T-60 watchdog fails even after the two HTML artifacts exist.
10. Rough edge: racecard subtitle shows `Going: TBC` even though the raw fixture and going stub say Good to Firm; `src.cli card` does not pass race_context/going into `render_card()`.

## T-60 watchdog result

```text
> python scripts\t60_watchdog.py --course=ascot --meeting=royal-ascot-2026 --date=2026-06-16
exit 2

OK: racecards, live-runners, sportinglife, racingpost, going, scores, report.
INCONSISTENT: bets - missing meta block; declared GBP 11.70 != computed GBP 0.00.
INCONSISTENT: racecard - header does not show bets total GBP 0.00.
MISSING: outputs\slip-ascot-2026-06-16.txt.
INCONSISTENT: consistency - check_env failed for SPORTINGLIFE_USER, SPORTINGLIFE_PASS in this shell.
```

## RUNBOOK gap list for future rewrite

1. Scope and header are explicitly Epsom/Ladies Day/Derby Day; should become course/meeting/date generic with examples for Royal Ascot.
2. Racing Post and Sporting Life URL patterns are hardcoded to Epsom course id 17 and `epsom-downs`; need config-driven examples for Ascot course id 1 and aliases.
3. Commands omit `--course` and `--meeting`; all operator commands should include or explain defaults.
4. Artifact paths use legacy Epsom names like `market-latest.json`, `live-runners-2026-06-06.json`, `outputs/race-card-2026-06-06.html`; non-Epsom course-prefixed paths need documenting.
5. Quick Reference is Derby Saturday 2026-06-06 only; needs a generic meeting-day checklist and an Ascot Day 1 example.
6. Credential section is stale: RUNBOOK mentions `RACING_API_USERNAME` and `RACING_API_PASSWORD`, while current env gate requires `SPORTINGLIFE_USER` and `SPORTINGLIFE_PASS`.
7. Several command snippets are POSIX-specific or invalid on Windows (`source .env`, `$(date +%F)`, `grep`, `tail`, `rm`, `/var/log/...`); rewrite should provide PowerShell-safe alternatives.
8. Manual odds schema is Epsom-flavoured and references Derby horses; rewrite should use neutral placeholders and course-prefixed market files.
9. T-60 section should document that watchdog currently expects bets meta/header schema and a slip artifact, while the generic CLI path does not create a slip.
10. Troubleshooting examples read raw runner key `horse_name`, but current raw racecard runners use `horse`; update snippets to support both.

## Verification

- `outputs\report-ascot-2026-06-16.html` exists and parses as HTML.
- `outputs\racecard-ascot-2026-06-16.html` exists and parses as HTML.
- Scores are not all 50.0; score range 5.0 to 95.0.
- Required pytest command passed: `python -m pytest -x --ignore=tests/test_racecard_wave33.py` => 484 passed in 19.87s.
- No source/config/script files modified.

## Verdict

PIPELINE-WORKS-WITH-ROUGH-EDGES. No ship-breaking traceback or empty HTML. The main seam bugs are betting-schema/header/watchdog alignment, missing slip generation, and report/card consumers still reading some Epsom/default enrichment context.
