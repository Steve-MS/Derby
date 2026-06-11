# Saul-14 v0.5.0 gate

## Verdict
NO-SHIP

Status: NEEDS-REWORK. Owner: Coordinator must assign a non-Linus/non-Livingston revision agent per reviewer lockout. The release artifact is rejected until the summary-only race risk is fixed and re-gated.

## Test suite
Command: `python -m pytest -q`

Result: PASS. Actual count: 510 passed, 0 skipped, 0 xfailed, 0 ignored. Runtime: 17.37s.

## E2E Quickstart
Fixture: `tests\fixtures\sportinglife\sample-meeting.html`

| Step | Exit code |
|---|---:|
| fetch --from-file | 0 |
| score | 0 |
| predict --bankroll 100 | 0 |
| report | 0 |
| card | 0 |

Artifacts:

| Artifact | Size |
|---|---:|
| `outputs\report-ascot-2026-06-16.html` | 45414 bytes |
| `outputs\racecard-ascot-2026-06-16.html` | 9282 bytes |

Raw backup was restored after the E2E run. Pre-run hash and restored hash matched.

## Atomic-write check
Raw file unchanged on corrupt input: Y.

Checks run against `data\raw\ascot-2026-06-16-racecards.json`:

| Case | Exit | Unchanged | Evidence |
|---|---:|---|---|
| HTML under 10 KB with `__NEXT_DATA__` | 1 | Y | Rejected as below 10 KB |
| Large HTML missing `__NEXT_DATA__` | 1 | Y | Rejected as `__NEXT_DATA__ not found` |
| Mutated fixture with empty races | 1 | Y | Rejected as parsed races are empty |
| Simulated score-smoke failure | 1 | Y | Rejected as score smoke failed |

## ToS hygiene
PASS for v0.5.0 import path.

- `scripts\scrape_sportinglife.py` does not exist.
- `scripts\scrape_racingpost.py` does not exist.
- `scripts\scrape_sportinglife.deprecated.py` exits 1 and stderr contains `deprecated`.
- `scripts\scrape_racingpost.deprecated.py` exits 1 and stderr contains `deprecated`.
- `src\sl_parser.py` states it performs no network requests and contains no HTTP client import.
- Grep found existing non-import utilities with HTTP behavior, especially `scripts\morning_odds.py` Racing Post best-effort scrape and archived/probe scripts. I did not classify these as new v0.5.0 racecard fetch bypasses, but Scribe should avoid staging unrelated scrape-probe changes.

## Going-fit blocker check
PASS.

`src\going.py` returns `score: 0.5` and `going_data: source_unavailable` when no runs are present and `going_history_source == "not_available"`. `tests\test_scoring.py` covers this in `test_unavailable_going_history_is_true_neutral`, including the 50.0 raw signal and `going_data_source_unavailable` flag.

## Null-tolerance blocker check
PASS.

`tests\test_scoring.py` includes `test_null_import_ratings_and_prices_score_without_exception`, covering null `rpr`, `ts`, and `morning_price` on imported runners. The full suite and E2E score path both passed.

## Summary-only races judgment
BLOCKER. Parser must warn or fail before ship.

Current behavior is truly silent: `src\sl_parser.py` emits only detailed races with `rides` arrays and ignores summary-only meeting races; the fixture imports as 1 race, 14 runners, with `Parse warnings: none`. README and RUNBOOK explain save-and-parse, but neither clearly tells the operator to expand all races before saving, and neither warns that a partial save can silently omit races.

For Royal Ascot, silently missing 4 of 7 races is catastrophic. A generic RUNBOOK line saying `Do not publish partial imports` is not sufficient because the operator is not told how to detect this class. Fix should be one of:

1. Preferred: fetch hard-fails when meeting summaries imply more races than detailed parsed races.
2. Acceptable for re-gate: fetch prints a prominent parse warning and docs explicitly instruct the operator to expand/open every race before browser save and verify expected race count.

## Doc completeness
MOSTLY PASS, with the summary-only blocker exception.

- README has v0.5.0 Quickstart with `--from-file`.
- README has a `Why save-and-parse` ToS note.
- README labels `SPORTINGLIFE_USER` and `SPORTINGLIFE_PASS` as browser-login-only.
- CHANGELOG has a v0.5.0 entry covering parser/import, going-fit neutral fix, null tolerance, and scraper deprecation.
- RUNBOOK reflects the import workflow and manual JSON fallback.
- `.env.example` says import does not read credentials and marks Sporting Life values as browser login only.
- Missing: explicit operator-facing instruction/warning for summary-only races.

## Repo hygiene
- Branch: `main`, 4 commits ahead of `origin/main` before Saul gate files.
- `pyproject.toml` version is `0.5.0`.
- Added-line ASCII scan over `origin/main..HEAD` found no non-ASCII additions, excluding the sanitized HTML fixture.
- Working tree had pre-existing untracked Ascot race-day data/output carry-overs before this verdict, matching the handoff scope. Saul adds this verdict and history entry.

## Issues found
1. [BLOCKER] Summary-only races are silently dropped. The parser imports one detailed race from the fixture, emits `Parse warnings: none`, and docs do not clearly instruct the operator to expand all races before saving. This can publish a partial Royal Ascot card.
2. [NICE-TO-HAVE] ToS grep still surfaces older HTTP-capable utilities outside the v0.5 import path, notably `scripts\morning_odds.py` and archived/probe scripts. Not a v0.5.0 blocker if Scribe stages only the reviewed commits, but the repo should eventually label or isolate these more clearly.

## Recommendation to Scribe
Do not tag or push v0.5.0 yet.

Required before re-gate: assign a non-Linus/non-Livingston revision agent to add summary-only race detection or a loud warning plus explicit operator docs, then rerun Saul gate.

Exact tag name after SHIP re-gate: `v0.5.0`.

Push command after SHIP re-gate:

```powershell
git push origin main
git tag v0.5.0
git push origin v0.5.0
```

GitHub release notes draft after SHIP re-gate:

```text
v0.5.0 - HTML import-only racecard workflow

- Adds `race-analysis fetch --from-file` for browser-saved Sporting Life racecards.
- Keeps v0.5.0 ToS-safe by avoiding automated Sporting Life HTTP racecard scraping.
- Parses saved racecard app state into the canonical raw JSON pipeline.
- Scores, predicts, reports, and renders cards from imported Ascot fixtures.
- Fixes imported going-history handling so `not_available` scores neutral instead of penalizing runners.
- Tolerates null RPR, TS, and morning price without crashing or fabricating values.
- Deprecates legacy Sporting Life and Racing Post racecard scraper entrypoints.
- Documents manual browser login and manual JSON fallback paths.
```
