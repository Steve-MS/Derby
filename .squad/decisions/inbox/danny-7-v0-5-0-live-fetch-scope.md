# Danny-7: v0.5.0 live racecard fetch scope

Date: 2026-06-08
Agent: Danny
Repo: C:\Users\stevenn\race-analysis
Branch/tag audited: main at v0.4.1
Mode: read-only scoping audit. No network requests. No credential values read.

## 1. Current state inventory

### Raw racecard file path

Canonical path is resolved by `src.course_config.path_for(course, date, "raw-racecards")`:

- `data\raw\{course}-{date}-racecards.json`
- Epsom examples: `data\raw\epsom-2026-06-05-racecards.json`, `data\raw\epsom-2026-06-06-racecards.json`
- Ascot example: `data\raw\ascot-2026-06-16-racecards.json`

### Top-level JSON schema observed

Files read: Epsom 2026-06-05, Epsom 2026-06-06, Ascot 2026-06-16, plus Ascot test fixture.

Required by all observed files:

| Field | Type | Notes |
|---|---|---|
| `meeting` | string | Display venue/meeting name, for example `Epsom` or `Royal Ascot`. |
| `date` | string | ISO date, for example `2026-06-16`. |
| `going` | string | Card-level going. Used as fallback when race going missing. |
| `races` | array of race objects | Required. Pipeline iterates this. |
| `retrieved_at` | string | ISO-ish source timestamp. Operational/audit field. |
| `going_source` | string | Human source label for going. |

Optional in observed files:

| Field | Type | Notes |
|---|---|---|
| `course` | string | Present in Ascot fixture. |
| `course_slug` | string | Present in Ascot fixture. |
| `meeting_slug` | string | Present in Ascot fixture. |
| `day_label` | string | Present in Ascot fixture. |
| `source` | string | Present in synthetic Ascot fixture. |
| `synthetic_notice` | string | Present only in synthetic Ascot fixture. |

### Race object schema observed

Required by all observed races:

| Field | Type | Notes |
|---|---|---|
| `race_number` | int | Display/order only. |
| `off_time` | string | `HH:MM`. Critical. Used to form race ids and live-runner matching. |
| `name` | string | Race display name. |
| `class` | string | Human class label, not currently the main class-move input. |
| `distance_f` | int or float | Distance in furlongs. Critical for scoring. |
| `prize_winner_gbp` | int or null | Display/audit. Can be null. |
| `runners` | array of runner objects | Critical. Empty races are skipped. |
| `source_urls` | array of strings | Audit/source trace. |
| `going` | string | Race-level override. Falls back from top-level `going`. |

Optional in observed races:

| Field | Type | Notes |
|---|---|---|
| `_name_note` | string | Present in some Epsom races after manual rename cleanup. |

### Runner object schema observed

Required by all observed runners, though several can be null:

| Field | Type | Notes |
|---|---|---|
| `horse` | string | Critical. Main runner key. |
| `age` | int | Display/enrichment. |
| `trainer` | string | Used by trainer bump, trainer 14d, and J/T combo. |
| `jockey` | string | Used by jockey bump and J/T combo. |
| `draw` | int or null | Used by draw and pace. Null is tolerated. |
| `weight_st_lb` | string or null | Display/enrichment. |
| `or` | int or null | Official rating. Scoring fallback after RPR and TS. |
| `rpr` | int or null | Racing Post Rating. Preferred class rating if present. |
| `ts` | int or null | Topspeed. Second class rating fallback. |
| `form_string` | string | Parsed right-to-left for recent form and inferred pace. |
| `last_run_days` | int or null | Used with `form_string` for absence penalty. |
| `notes` | string | Display/audit and CD badge heuristics. |
| `morning_price` | float | Used by market fallback and reports. |
| `odds_source` | string | Audit/source label. |
| `odds_fetched_at` | string | Audit/source timestamp. |
| `going_history` | array | Used by going-fit signal. Empty array gives neutral. |
| `going_history_source` | string | Audit/source label. |
| `going_history_fetched_at` | string | Audit/source timestamp. |

Optional in observed runners:

| Field | Type | Notes |
|---|---|---|
| `withdrawn` | bool | Present in Ascot fixture. `src.cli._normalize_race()` filters runners with `withdrawn == true`. Missing means active. |

### `going_history` item schema observed

Required by most observed history entries:

| Field | Type | Notes |
|---|---|---|
| `date` | string | Past run date. |
| `going` | string or null | Used by going-fit. Null tolerated. |
| `position` | int or null | Used by going-fit. Null tolerated. |
| `field_size` | int | Used by going-fit sample weighting. |

Optional rare fields:

| Field | Type | Notes |
|---|---|---|
| `course` | string | Present on one observed entry. |
| `race` | string | Present on one observed entry. |

### Downstream readers of raw racecard file

Mapped by path/glob search in `src`, `scripts`, and `tests`:

- `src\course_config.py`
  - Defines canonical path kind `raw-racecards`.
- `src\cli.py`
  - `fetch`: currently only validates existence.
  - `score`: loads raw JSON, normalizes races, filters `withdrawn`, calls `score_race()`.
  - `card`: passes raw path into `render_card()` for withdrawn banners.
- `src\racecard.py`
  - `_withdrawn_horses_from_raw()` reads raw JSON and marks `withdrawn` horses on printable card.
- `scripts\morning_odds.py`
  - `load_racecard_prices()` reads raw JSON and uses runner `morning_price` as fallback market data.
- `scripts\refresh_friday.py`
  - Reads raw racecard path for refresh flow.
- `scripts\t60_watchdog.py`
  - Checks raw file freshness and size, loads raw cards, cross-checks bet horses against raw runners.
- Legacy/one-shot scripts:
  - `scripts\clean_card_pass.py`, `scripts\rerender_derby_2026.py`, `scripts\show_race.py` hardcode Epsom raw files.
- Tests:
  - `tests\test_course_config.py` asserts raw path resolution.
  - `tests\test_cli_card_trifecta.py` monkeypatches `raw-racecards` path.
  - `tests\test_racecard_wave33.py` reads Epsom raw path.
  - `tests\test_t60_watchdog.py` creates and mutates raw racecards.
  - `tests\fixtures\ascot\raw-ascot-2026-06-16-racecards.json` is the Ascot fixture.

### Other input artifacts the pipeline expects

Strictly speaking these are enrichment/results inputs, not raw racecards, but the race-day pipeline expects them:

| Artifact | Path pattern | Consumer | Purpose |
|---|---|---|---|
| Live runners / non-runners | `data\enrichment\live-runners-{course}-{date}.json` for non-Epsom, legacy no-course for Epsom | `scripts\t60_watchdog.py` | Detect NR/VOID runners against bets. Shape: top-level `races`; race has `time`, `name`, `course`, `runners`, `non_runners`; runner has `name`, `status`. |
| Sporting Life scrape artifact | `data\enrichment\sportinglife-{course}-{date}.json` | `scripts\t60_watchdog.py` | Fresh source proof and live-runner hygiene. T-60 enforces over 1 KB to reject SPA shell. |
| Racing Post scrape artifact | `data\enrichment\racingpost-{course}-{date}.json` | `scripts\t60_watchdog.py`, `scripts\morning_odds.py` | Runner-name confirmation and source trace. |
| Going artifact | `data\enrichment\going-{course}-{date}.json` | `src\cli.py card`, `scripts\t60_watchdog.py` | Official going subtitle and freshness gate. |
| Market baseline/latest | `data\enrichment\market-baseline[-course].json`, `market-latest[-course].json` | `scripts\morning_odds.py`, `src\racecard.py`, report/rendering | Market move, stale price display, latest price overlay. |
| Legacy going forecast | `data\going-forecast.json` | `src\racecard.py`, legacy Epsom render scripts | Epsom scenario/going banner. |
| Results | `data\results\results[-course]-{date}.json` | `backtest` | Post-race evaluation. |
| ATR going history | `data\enrichment\atr-going-playwright.json` | archived/enrichment scripts | Historical going runs; optional. |

## 2. Source survey

No HTTP requests were made. This survey is based on repo code, cached fixtures, and public product knowledge.

### Sporting Life, preferred

Credential contract:

- Runtime expects `SPORTINGLIFE_USER` and `SPORTINGLIFE_PASS` via `os.environ`.
- This audit did not read or print their values.
- Existing `scripts\check_env.py` validates presence and placeholder status.

Repo findings:

- No `api.sportinglife` or `sportinglife.com/api` references found.
- Existing planner URL in `scripts\scrape_sportinglife.py`:
  - `https://www.sportinglife.com/racing/racecards/{date}/{course_path}`
  - Ascot course path resolves to `ascot`.
  - Epsom special-cases alias `epsom-downs`.
- Current scraper only fetches HTML metadata. It does not log in and does not map raw racecards.
- Existing operational notes say missing auth can return a tiny SPA shell, observed as 373 bytes during Derby work. T-60 now treats Sporting Life artifact below 1 KB as inconsistent.
- Cached Ascot Sporting Life fixture contains only race names, runner names, active status, and non-runners. It is synthetic and not enough to prove full schema mapping.

Public/API posture:

- Public documented Sporting Life racing API is not evident from repo.
- The racecard page is a browser app. The MVP should first inspect server-rendered HTML or embedded app state in controlled cassettes, then only use network calls that the page itself makes and that are allowed by site policy.
- Avoid private or unstable endpoints if they require bypassing normal browser behavior.

Login requirement:

- Racecard pages are generally public, but the repo's own Derby failure notes say auth is needed for authenticated form and live-odds scraping to avoid empty SPA shell behavior.
- MVP should support env-based login/session if required, but the first implementation should try the public racecard page, then authenticated page, then fail loud.

Robots and ToS considerations:

- Robots/ToS were not fetched in this audit by instruction.
- Builders must check robots.txt and terms before coding live requests.
- Do not bypass paywalls, bot controls, or account restrictions.
- Use the operator's legitimate account only for normal page access.
- Cache responses in tests and do not run automated broad crawling.

Polite request rate:

- One meeting/date fetch should need only 1 to 6 requests.
- Recommended MVP limit: serial requests only, at least 1 second between requests, exponential backoff on 429/403/5xx, max 2 retries, and clear stop after failure.
- Never run parallel scraping against Sporting Life.

### Racing Post, fallback

Repo findings:

- Existing planner URL in `scripts\scrape_racingpost.py` and RUNBOOK:
  - `https://www.racingpost.com/racecards/{course_id}/{course_path}/{date}`
  - Ascot example: `https://www.racingpost.com/racecards/1/ascot/2026-06-16`
  - Epsom example: `https://www.racingpost.com/racecards/17/epsom/2026-06-06`
- Existing code extracts `__NEXT_DATA__` and recursively finds `horseName`, but only writes runner names/count.
- RUNBOOK notes failure modes: HTTP 406 on repeated scrapes, HTTP 404 on wrong date/id, malformed small HTML. Wait 60 seconds before retrying.
- Cached Ascot Racing Post fixture is synthetic and contains runner names only.

Public/paywall posture:

- Racing Post full cards, ratings, comments, and some data can be paywalled or bot-protected.
- Free meeting summaries/declared runner lists may be sufficient for names and declarations but are unlikely to be a reliable full-schema source by T-1.
- Use as fallback cross-check, not primary MVP source, unless Sporting Life cannot provide ratings/form fields.

Rate-limit posture:

- More fragile than Sporting Life in this repo's current runbook.
- Keep to 1 request per minute on retry after a block. Do not loop.

### Other, note only

- Betfair Exchange API: viable for declared runners, market identifiers, runner selection ids, and live prices if the operator has an app key and session token. It will not provide full racecard form, RPR, TS, trainer form, or going history. Good v0.5.2+ enrichment, not v0.5.0 raw-card source.
- At The Races: repo already has authenticated cookie-based Playwright work for going history. Could enrich form/going history later, but cookie and browser automation make it too heavy for this MVP.
- GB Racing / BHA / Racing Admin: worth checking for official declarations and non-runner feeds. Likely useful for runner status, not complete model schema.
- The Racing API: `.env.example` reserves `RACING_API_KEY`, but repo says it is not integrated and commercial. Not v0.5.0.

## 3. Schema-match analysis

Recommended source: Sporting Life, because Steve already has account credentials, the repo already gates those env vars, and Sporting Life is already part of the operator workflow.

Expected Sporting Life coverage, based on public racecard pages and current repo assumptions:

| Required raw field | Likely source coverage | MVP action |
|---|---|---|
| Card `meeting`, `course`, `date` | Yes via CLI/config/page | Fill from config and page. |
| Card/race `going` | Usually yes, but may be page-level only | Fill from page if present; else from `data\enrichment\going-*`; else `Unknown` with source note. |
| Race `off_time`, `name`, `class`, `distance_f` | Yes | Parse and normalize. |
| Race `prize_winner_gbp` | Maybe | Parse if available; else null. |
| Runner `horse`, `age`, `trainer`, `jockey`, `draw`, `weight_st_lb`, `form_string` | Likely yes | Parse as primary schema. |
| Runner `or` | Likely yes for handicap/official cards | Parse if present; else null. |
| Runner `rpr`, `ts` | Uncertain. Sporting Life may not publish Racing Post specific ratings consistently | If absent, set null and rely on `or`. Document lower-confidence class signal. Do not scrape Racing Post only for these in MVP. |
| Runner `last_run_days` | Likely yes or computable from last-run date | Parse if present; compute from last-run date when available; else null. |
| Runner `morning_price` | Maybe, odds can be dynamic | Parse if visible; else null would break observed schema but scoring tolerates missing market via neutral later. MVP should set null only if consumers are updated/tested, or set from existing market snapshot when available. Recommended: parse if present, else use no-price neutral plus audit note. |
| Runner `going_history` | No, not on basic racecard | Set empty array, source `not_available`. Later enrich from ATR/Racing Post. Going-fit becomes neutral. |
| Runner `notes` | Not structured | Compose audit note from source fields, including source URL and unavailable gaps. |
| Runner `withdrawn` | Yes via runner status/non-runner list if page indicates | Default false; true for NR/VOID statuses. |
| `source_urls`, source timestamps | Yes | Fill from requested URL and current UTC time. |

Important scoring impact of gaps:

- Class rating uses `rpr`, then `ts`, then `or`. OR-only cards still score, but with less predictive richness.
- Recent form can work from `form_string` and `last_run_days`.
- Going-fit will be neutral without `going_history`.
- Course/distance and trial/sire/equipment/trainer14d/JT enrichment already use side data or neutral defaults; raw fetch does not need to solve them.
- Morning price is operationally important for market fallback. If Sporting Life does not expose stable prices server-side, do not invent prices. Prefer null plus a clear warning, or keep existing `morning_odds.py` enrichment path.

Recommended gap decisions:

| Gap | Decision |
|---|---|
| RPR/TS absent | Skip and document `not_available`; rely on OR. Later Racing Post enrichment can fill. |
| Going history absent | Skip and document `not_available`; neutral going-fit. Later ATR/Racing Post enrichment. |
| Morning odds absent | Do not fabricate. Use visible odds if present; otherwise null plus command warning. If current code requires float in tests, update tests/consumers to tolerate null before release. |
| Prize money absent | Set null. |
| Course/distance badges absent | Compute only if explicit badges present; otherwise leave inferred fields absent and rely on neutral. |
| Draw absent before final declarations | Set null and warn; T-60 should force refresh once declarations include draw. |

## 4. Recommended MVP scope, 5 to 7 build days

### MVP recommendation

Build v0.5.0 as a tight, single-source Sporting Life live racecard fetcher.

Command:

```powershell
race-analysis fetch --course ascot --meeting royal-ascot-2026 --date 2026-06-16
```

Behavior:

1. Resolve course/meeting/date with `src.course_config`.
2. Build Sporting Life URL `https://www.sportinglife.com/racing/racecards/{date}/{course_path}`.
3. Read `SPORTINGLIFE_USER` and `SPORTINGLIFE_PASS` from `os.environ` only when live network mode needs auth. Never print values.
4. Fetch one meeting page politely.
5. Parse card into canonical raw schema.
6. Write `data\raw\ascot-2026-06-16-racecards.json` atomically.
7. Print source URL, race count, runner count, fields missing count, and output path.
8. If fetch fails, leave any existing raw file untouched and print manual fallback instructions.

Testing:

- Fixture/cassette based tests only. Dress rehearsal must pass without network.
- Store sanitized HTML or JSON fixtures under `tests\fixtures\sportinglife\` or equivalent.
- Do not store credentials, cookies, account identifiers, or personal data in fixtures.
- Parser tests should run from fixture to raw JSON and then through `score` smoke path.

What is not in MVP:

- Racing Post enrichment for RPR/TS.
- Results scraping.
- Live odds scraping beyond whatever appears on the racecard page.
- Betfair integration.
- Jockey changes after initial fetch beyond a full re-fetch.
- Automated non-runner polling loops.
- Browser automation/Playwright.
- Keyring/config-file credential storage.
- Multi-source merge/conflict resolution.
- Automatic T-60 repair.

### Full scope sketch after MVP

- v0.5.1: Racing Post enrichment to backfill RPR/TS and cross-check runner names.
- v0.5.2: Betfair runner/price enrichment and market id mapping.
- v0.5.3: Non-runner/jockey-change refresh command with diff output.
- v0.6.0: Multi-source racecard merge with provenance and confidence per field.

## 5. Risks and mitigations

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Sporting Life auth flow is harder than expected | HIGH | MED | Keep MVP parser decoupled from HTTP. Ship fixture parser first. If auth blocks, allow manual HTML fixture import or fall back to manual JSON. |
| Sporting Life page lacks RPR/TS or going history | MED | HIGH | Treat as not available, rely on OR and neutral going-fit. Document field gaps in output metadata. |
| Sporting Life page lacks stable odds | MED | MED | Do not invent. Use `morning_odds.py` path for prices. Score market-move neutral when absent. |
| Schema drift in page/app state | HIGH | MED | Contract tests against fixtures plus parser diagnostics that list missing selectors/keys. Keep parser small and fail loud. |
| Robots/ToS disallow scraping | HIGH | UNKNOWN | Builder must check before live code. If disallowed, do not scrape; pivot to manual JSON plus official/export source. |
| Rate-limit or block | HIGH | MED | One serial request, 1 second minimum delay, backoff, max 2 retries, cached tests, no parallelism. |
| Network flakiness on race morning | HIGH | MED | Fetch at T-24 and T-12. Keep last good raw file. Fetch command must not delete/overwrite on failure. |
| Race morning T-60 failure leaves operator stuck | HIGH | MED | Document fallback: if fetch fails, manually place JSON at `data\raw\ascot-2026-06-16-racecards.json`, then re-run `race-analysis fetch`, `score`, `predict`, `card`, and T-60 watchdog. |
| Bad parse silently writes partial card | HIGH | MED | Enforce minimums: non-empty races, non-empty runners, off_time/name/horse present, output runner count visible, optional `--force` only later not in MVP. |
| Existing consumers assume `morning_price` is float | MED | MED | Test raw output through score, morning_odds fallback, card, and T-60. If needed, parser sets missing price to null and consumers tolerate it, or command fails with actionable warning. |
| Credentials leak to `.squad` or fixtures | HIGH | LOW | Do not read or print values. Redact headers/cookies from fixtures. Add fixture scan for env names and secret-like patterns. |
| Ascot declarations/draw not available until later | MED | MED | Allow re-run to refresh same path. T-60 checks freshness. Missing draw warns but does not block scoring unless no runners. |

Race morning failure mode spec:

- Fetch command failure must print exactly where manual JSON belongs.
- It must say existing file was left untouched if present.
- Operator fallback:
  1. Manually source/export racecard JSON in the documented schema.
  2. Save it to `data\raw\ascot-2026-06-16-racecards.json`.
  3. Run `race-analysis fetch --course ascot --meeting royal-ascot-2026 --date 2026-06-16` to validate existence/schema.
  4. Run score, predict, report, card, and `scripts\t60_watchdog.py`.
- This fallback must be in README/RUNBOOK before v0.5.0 tag.

## 6. Integration plan

Recommended integration:

- Slot fetch as a pre-pipeline standalone command, replacing current existence-only `cmd_fetch` behavior.
- Keep command name `fetch`; no new top-level command needed.
- Add optional flags only if necessary:
  - `--source sportinglife` default, future-proofed but no multi-source MVP.
  - `--offline-fixture PATH` or test-only parser entry point if needed for tests.
  - Avoid `--username` or credential flags.
- Existing pipeline remains:
  - `fetch` writes/verifies raw card.
  - `score` consumes raw card.
  - `predict`, `report`, `card` consume generated outputs.
  - T-60 watchdog verifies raw plus enrichment freshness.

CLI restructuring:

- No broad CLI restructure required. `src.cli` already has subcommands.
- `fetch` help text must change from "Validate that a racecard JSON exists" to "Fetch or validate raw racecard JSON".
- Keep course/meeting/date args exactly as v0.4.1.

Docs/skills updates:

- README Quickstart live section: replace manual-only note with `race-analysis fetch` live command and fallback.
- RUNBOOK: update sections 0, 2.2, 3.2, and 5 T-24/T-60 fallback.
- `docs\data-layout.md`: no path change, but add source/provenance note if desired.
- `.squad\skills\`: update operator/race-day skill templates that currently instruct manual raw JSON sourcing.
- CHANGELOG: v0.5.0 Added/Notes for consumers.

## 7. Chunked build plan

### Chunk 1: Fetch contract and fixtures

Owner: Saul for tests plus Danny consult on schema.

Deliverable:

- Canonical raw schema fixture test from sanitized Sporting Life sample.
- Tests that fetch command never needs network in normal test suite.
- Acceptance: fixture parser target shape documented; failing missing fields are explicit.

### Chunk 2: Sporting Life HTTP/auth client

Owner: Linus for source code.

Deliverable:

- Small stdlib or requests-based client, depending on dependency decision.
- Env var auth reads only from `os.environ`.
- Polite request/backoff behavior.
- Atomic write discipline: no clobber on failure.
- Acceptance: mocked HTTP tests for success, auth missing, 403/429, tiny SPA shell.

### Chunk 3: Parser and schema mapper

Owner: Linus for parser, Kaylee/Rusty review scoring implications.

Deliverable:

- Sporting Life HTML/app-state parser to canonical raw JSON.
- Field provenance/missing-field summary.
- Minimum schema validation.
- Acceptance: fixture maps to raw file, then `score` can process it offline.

### Chunk 4: CLI wiring and end-to-end offline smoke

Owner: Linus with Saul tests.

Deliverable:

- `race-analysis fetch` writes `data\raw\ascot-2026-06-16-racecards.json`.
- Existing existence-only behavior becomes validation after fetch or when offline/manual file exists.
- Acceptance: pytest covers fetch, score smoke, and no-network dress rehearsal.

### Chunk 5: Operator docs and rehearsal

Owner: Livingston for docs, Danny for final scope check, Steve/operator for manual rehearsal.

Deliverable:

- README/RUNBOOK updated.
- Race morning fallback documented.
- Changelog v0.5.0 drafted.
- Acceptance: run Royal Ascot 2026-06-16 rehearsal from a clean checkout using fixture/no network, then with live fetch if allowed.

## 8. Verdict and recommendation

Verdict: GO for v0.5.0 MVP, with strict scope control.

Recommended version: v0.5.0.

Reason:

- The current consumer blocker is exactly `fetch` being validate-only.
- The repo already has course/date pathing, env-var gate, source URL patterns, T-60 freshness checks, and Ascot fixtures.
- A single-source Sporting Life MVP can fit in 5 to 7 build days if it accepts neutral gaps for RPR/TS/going history instead of building multi-source enrichment.

Kickoff recommendation:

- Launch chunks 1, 2, and 3 in parallel only after a 30 minute rubber-duck on the raw schema contract.
- Chunk 4 depends on chunks 1 to 3.
- Chunk 5 can start docs skeleton immediately, then finalize after CLI behavior lands.

Go/no-go gate for builders:

- If Sporting Life robots/ToS or auth flow blocks automated page fetch, stop live implementation and ship v0.5.0 as `fetch --from-file/--validate` plus a stronger manual fallback only. Do not spend T-7 on multi-source scraping.
