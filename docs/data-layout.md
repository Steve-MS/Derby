# Data Layout Decision

Date: 2026-06-08
Owner: Livingston-9
Status: KEEP flat-with-course-prefix

## Current layout

`src.course_config.path_for()` is the canonical resolver for course/date artifacts. Epsom keeps its legacy archive names for generated outputs. Non-Epsom courses use flat filenames with the course slug embedded.

| Artifact kind | Epsom path for 2026-06-06 | Ascot path for 2026-06-16 |
|---|---|---|
| Raw racecards | `data\raw\epsom-2026-06-06-racecards.json` | `data\raw\ascot-2026-06-16-racecards.json` |
| Enrichment: live runners | `data\enrichment\live-runners-2026-06-06.json` | `data\enrichment\live-runners-ascot-2026-06-16.json` |
| Enrichment: Racing Post | `data\enrichment\racingpost-2026-06-06.json` | `data\enrichment\racingpost-ascot-2026-06-16.json` |
| Enrichment: Sporting Life | `data\enrichment\sportinglife-2026-06-06.json` | `data\enrichment\sportinglife-ascot-2026-06-16.json` |
| Enrichment: going | `data\enrichment\going-2026-06-06.json` | `data\enrichment\going-ascot-2026-06-16.json` |
| Scores | `outputs\scores-2026-06-06.json` | `outputs\scores-ascot-2026-06-16.json` |
| Bets | `outputs\bets-2026-06-06.json` | `outputs\bets-ascot-2026-06-16.json` |
| Racecard | `outputs\racecard-2026-06-06.html` | `outputs\racecard-ascot-2026-06-16.html` |
| Report | `outputs\report-2026-06-06.html` | `outputs\report-ascot-2026-06-16.html` |
| Slip | `outputs\slip-2026-06-06.txt` | `outputs\slip-ascot-2026-06-16.txt` |
| T-60 status | `outputs\t60-status-2026-06-06.json` | `outputs\t60-status-2026-06-16.json` |
| Results | `data\results\results-2026-06-06.json` | `data\results\results-ascot-2026-06-16.json` |

## Decision

Keep the flat layout with course-prefixed filenames for non-Epsom artifacts. Do not move to `data\raw\{course}\{date}\racecards.json` in v0.4.

## Rationale

- It works today for Epsom and Ascot without directory migration.
- It preserves historical Epsom artifacts exactly where existing operators and tests expect them.
- Operators can glob by course prefix, for example `*-ascot-2026-06-16.*`, without walking nested directories.
- The current `path_for()` resolver already centralizes path decisions, so callers do not need to know the naming convention.
- A nested tree would create churn across scrapers, watchdogs, reports, fixtures, tests, and archive procedures for little operational gain.

## Migration plan

No migration is planned. If a future release needs meeting-level archive bundles, add a new chunk to design copy/export tooling rather than rewriting canonical paths in place.

## Archive policy

Historical Epsom artifacts are archives. Leave them at legacy paths and never re-emit them under new prefixed or nested paths. New non-Epsom outputs should use `path_for()` and the course-prefixed flat filenames above.
