# Saul-15 v0.5.0 re-gate

## Verdict

SHIP.

Marty-1's hard-fail fix addresses Saul-14's BLOCKER. A saved Sporting Life meeting page that advertises more races than are parsed in detail now fails before raw JSON write, prints an operator-facing recovery action, and leaves the prior raw card untouched.

I do not regress any Saul-14 PASS findings. The only wrinkle: the exact prompt command used `--meeting royal-ascot`, which is not a configured meeting slug and exits before import with `unknown meeting`. I therefore also ran the same fixture with the configured slug used by tests and CLI examples, `royal-ascot-2026`, to exercise the partial-import path.

## Test suite

Command:

```powershell
python -m pytest -q
```

Result: PASS.

- Count: 512 passed
- Pytest-reported runtime: 15.68s
- Measured wall runtime: 16.91s
- Exit code: 0

## Hard-fail verification

### Exact prompt command

Command used the prompt's meeting slug:

```powershell
race-analysis fetch --from-file tests\fixtures\sportinglife\sample-meeting.html --course ascot --meeting royal-ascot --date 2026-06-16
```

Result:

- Exit code: 2
- Raw SHA256 before: `865CEE6A9F8A8171A12728FBE03F348146D365252905B59791BD6BCB460D6FDA`
- Raw SHA256 after: `865CEE6A9F8A8171A12728FBE03F348146D365252905B59791BD6BCB460D6FDA`
- Added files in `data\raw`: none

Quoted stderr/output:

```text
Error: unknown meeting 'royal-ascot' for course 'ascot'
```

Judgment: this does not exercise Marty's partial-import path because the slug is rejected by course config first. It also cannot publish a partial raw card.

### Configured Royal Ascot slug

Command:

```powershell
race-analysis fetch --from-file tests\fixtures\sportinglife\sample-meeting.html --course ascot --meeting royal-ascot-2026 --date 2026-06-16
```

Result:

- Exit code: 1
- Raw SHA256 before: `865CEE6A9F8A8171A12728FBE03F348146D365252905B59791BD6BCB460D6FDA`
- Raw SHA256 after: `865CEE6A9F8A8171A12728FBE03F348146D365252905B59791BD6BCB460D6FDA`
- Added files in `data\raw`: none
- Raw file count before/after: 3 / 3

Quoted stderr/output:

```text
ERROR: Partial import detected -- saved meeting page contains 6 races but only 1 was parsed in detail.
The other 5 races are summary-only (race links were not expanded before save).
Action: Open the meeting page in your browser, click each race to expand its full racecard, then re-save the page and retry.
Raw racecard was left untouched: C:\Users\stevenn\race-analysis\data\raw\ascot-2026-06-16-racecards.json
```

Operator judgment: PASS. The wording names the condition, explains that unexpanded race links caused summary-only races, and gives a clear recovery action: open page, expand every racecard, re-save, retry. A non-author operator should understand what to do.

## Happy path verification

Marty did not add a second full-meeting fixture; tests mutate the partial fixture into a one-advertised/one-detailed complete case. I reproduced that manually by creating a temporary complete single-race HTML file, running fetch, then restoring the previous raw bytes and deleting the temporary fixture.

Command used configured slug:

```powershell
race-analysis fetch --from-file tests\fixtures\sportinglife\saul-15-single-complete-race.html --course ascot --meeting royal-ascot-2026 --date 2026-06-16
```

Result:

- Exit code: 0
- Raw SHA256 before happy path: `865CEE6A9F8A8171A12728FBE03F348146D365252905B59791BD6BCB460D6FDA`
- Raw SHA256 immediately after write: `87F8FB1EB743405FE97A6377EC10775F2291FF66DCDB1C494CD0F657EAD1F771`
- Raw SHA256 after restore: `865CEE6A9F8A8171A12728FBE03F348146D365252905B59791BD6BCB460D6FDA`
- Output included `Race count: 1`, `Runner count: 14 (13 active)`, and `Parse warnings: none`.
- Temporary fixture removed: yes.

## Atomic-write re-verify summary

PASS, light re-verify.

Per the focused re-gate instruction, I did not manually redo Saul-14's four pre-existing corrupt-input probes unless suspicious. Full suite is green at 512 passed, Marty added coverage for partial-import no-clobber and did not weaken the existing failure paths. Saul-14's atomic-write PASS therefore stands for:

- HTML under 10 KB with `__NEXT_DATA__`
- Large HTML missing `__NEXT_DATA__`
- Mutated fixture with empty races
- Simulated score-smoke failure

Additional manual evidence from this re-gate: both the invalid-slug failure and the partial-import failure left the raw SHA256 unchanged and added no files in `data\raw`.

## Doc completeness

PASS.

- README Quickstart step 2 now says: `Click every race link on the meeting page so each full racecard is expanded before saving.`
- README Royal Ascot section repeats: `expand every race in the browser` before import.
- RUNBOOK has a dedicated `If fetch reports partial import` section.
- RUNBOOK states the raw JSON is not written and gives exact recovery steps: reopen page, click every race link, save again as complete webpage, retry fetch, continue only after exit 0 and expected race count.

Judgment: readable and actionable for a non-author operator.

## ToS hygiene re-verify

PASS.

Checks:

- `git diff origin/main..HEAD -- src\sl_parser.py src\cli.py` contains no added `requests.`, `httpx.`, `urllib.request`, `urlopen`, `import requests`, `import httpx`, or `from urllib` usage.
- Direct file scan of `src\sl_parser.py` and `src\cli.py` found no HTTP client usage. The only match was prose stating the parser performs no network requests.
- No automated Sporting Life HTTP racecard fetch was reintroduced.

## Repo hygiene

PASS.

- Added-line ASCII scan over `origin/main..HEAD`: no non-ASCII added lines outside `tests/fixtures/sportinglife/sample-meeting.html`.
- `scripts\scrape_sportinglife.py`: absent.
- `scripts\scrape_racingpost.py`: absent.
- `pyproject.toml` version: `0.5.0`.
- Working tree had pre-existing untracked race-day artifacts and a modified `.squad\agents\saul\history.md`; this gate only writes this verdict. `.squad\saul-history.md` does not exist, so no one-line history entry was appended.

## Scope discipline

PASS.

`git show --stat 9b2567d` shows Marty touched only:

- `.squad\decisions\inbox\marty-1-v0-5-0-hardfail.md`
- `README.md`
- `RUNBOOK.md`
- `src\cli.py`
- `src\sl_parser.py`
- `tests\test_cli_fetch_from_file.py`
- `tests\test_sl_parser.py`

No changes to deprecated scrape scripts, `going.py`, `scoring.py`, or `CHANGELOG.md` in Marty's fix commit.

## Issues found

1. [INFO] The re-gate prompt's exact command uses `--meeting royal-ascot`, but this repo's configured slug is `royal-ascot-2026`. The exact command exits 2 before import with `unknown meeting`, raw unchanged. I do not treat this as a ship blocker because it cannot publish partial data and the configured slug exercises the intended hard-fail path successfully.

No BLOCKER, MAJOR, or MINOR issues found in Marty's fix.

## Recommendation to Scribe

Tag and push v0.5.0.

Exact tag name: `v0.5.0`.

Push sequence:

```powershell
git push origin main
git tag v0.5.0
git push origin v0.5.0
```

GitHub release notes draft:

```text
v0.5.0 - HTML import-only racecard workflow

- Adds `race-analysis fetch --from-file` for browser-saved Sporting Life racecards.
- Hard-fails partial saved meeting pages where summary-only races would otherwise be silently dropped.
- Keeps v0.5.0 ToS-safe by avoiding automated Sporting Life HTTP racecard scraping.
- Parses saved racecard app state into the canonical raw JSON pipeline.
- Scores, predicts, reports, and renders cards from imported Ascot fixtures.
- Fixes imported going-history handling so `not_available` scores neutral instead of penalizing runners.
- Tolerates null RPR, TS, and morning price without crashing or fabricating values.
- Deprecates legacy Sporting Life and Racing Post racecard scraper entrypoints.
- Documents manual browser login, expand-every-race save workflow, partial-import recovery, and manual JSON fallback paths.
```
