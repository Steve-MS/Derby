## SUMMARY (2026-06-06 Post-Derby)

**Key deliverables:**
- Live-runner verification gate shipped (mandatory for all race days)
- Ladies Day results captured: 27,850 bytes, 8 races complete
- Saturday baseline gate executed: 101 confirmed runners (41 NRs filtered)
- Identified 2 Saturday NRs (Dance In The Storm, See The Fire); Causeway confirmed
- Equipment/market-move data infrastructure built; prices remain SYNTHETIC (2026-06-02 source)

**Critical findings (Derby Saturday):**
- All core picks confirmed: Item (5.0), Kinswoman (24.0), Allegresse (9.0), Lord Melbourne (13.5)
- Going: "Good to Soft, good in places"; rain forecast possible (Soft by post)
- NRs impact: Dance In The Storm kills Kinswoman+DitS double (£0.50 at risk)

**Publish blockers:**
- Live price ingestion not implemented (RP 406 quirk on consecutive scrapes; Betfair API not enabled)
- Stale-data NR failures resolved by live-runner gate (prevents re-occurrence of Triple Double A pattern)
- RP scrape rate-limiting: 60s delay required between baseline→latest calls

**Operational data:**
- data/enrichment/archive/2026-06-05/: Friday archive complete (39981b baseline, 54055b latest)
- data/enrichment/live-runners-2026-06-06.json: pre-populated with Sporting Life + corroboration
- data/enrichment/equipment.json: 272 runners, 30 headgear codes, 31 no-equipment, 9 first-time flags

**Current state:**
- Live-runner gate operational and preventing stale-runner failures
- Equipment data available; wind ops paywalled (skipped for v0.6)
- Market data static (synthetic prices); market_move returns neutral
- Derby Saturday baseline captured at 07:00 BST; latest mode ready for pre-race gate

---

---

# Livingston — History

## Project context (seeded 2026-06-03)

- Python 3.12 race-analysis toolkit for Steve. Repo Steve-MS/Derby, commit 5a1770e.
- Existing enrichment files: `data/enrichment/horse-profiles.json` (29 horses with sires), going history, pace styles.
- Existing fetcher: `src/racecard.py`, refresh script `scripts/refresh_friday.py`.
- Open question: where do raw racecards live? `data/racecards/2026-06-06/*.json` returned empty when probed. Find this before equipment/wind signal can be built.
- Odds source: BetVictor + RP morning prices. `morning_price` field already on runner records.
- Target races: Ladies Day Fri 5 Jun + Derby Day Sat 6 Jun 2026 at Epsom.

- 2026-06-05 09:52: **Friday AM Gate completed (2h52m late vs 07:00 target).** Baseline refresh successful (106 runners, RP scrape OK, 38 non-runners filtered). Latest mode returned HTTP 406; wrote unfiltered 144 runners (Precise, Prizeland, Beautify confirmed non-runners now in latest but not baseline). **Belinus: definitively WITHDRAWN** — absent from final 9-runner Oaks field per web declaration check; Steve's WIN £5 @ 3.5 needs bookmaker refund. **On Message: DATA GAP** — Ralph Beckett trainer, Hector Crouch jockey, ~25/1 odds, declared in field but MISSING from racecard JSON (late entry or fetcher miss); will score nowhere. **Sugar Island: DRIFTED INWARD** — stake at 33/1 (34.0 dec), market now 16-22/1 (17-23 dec); moved well inside >20 threshold; EW locked at better price. **Going:** G/S stable, no going-based stake review. **RP 406 mitigation:** Next gate 15:00 BST will use --no-rp-scrape flag to avoid double-scrape 406 error. Oaks off 16:00 BST.



## Learnings (recent — Derby Day + wave-1)

- 2026-06-07 17:08: **v0.4 RUNBOOK.md SHIPPED.** Delivered comprehensive operator guide (`RUNBOOK.md` at repo root) taking strangers from install to printable race card. Encodes the **two-source scrape pattern** discovered yesterday (RP 406 quirks, Sporting Life 373-byte failures, post-race results as reliable fallback). Includes 8 required sections: prerequisites, scrape pattern with 5 sources + URL patterns + auth + failure modes, race-day timeline (T-24h to T+1d), manual live-odds entry procedure with exact JSON schema, sanity checks with command snippets, 6 failure-mode field guides, glossary (racing + signal terms for devs), and one-screen quick reference card. Audience: Python/CLI dev with zero horse racing knowledge. 565 lines, ~23KB. Tone: factual, self-sufficient, copypaste-ready. No .py/.json changes, no credentials leaked, dates use CURRENT_DATETIME. Decision note filed to `.squad/decisions/inbox/livingston-v04-runbook-shipped.md`. Ready for merge.

- 2026-06-06T07:08 BST: **SATURDAY 07:00 BASELINE GATE complete.** Ran `morning_odds.py --mode baseline --date 2026-06-06`. RP scrape returned 101 confirmed runners from 142 racecard entries (41 filtered as probable NRs). **CRITICAL FINDINGS:** (1) **Dance In The Storm PROBABLE NR** — absent from RP live racecard; WIN bet £1.33 @ 18.5 at risk; also kills Kinswoman+DitS double leg (£0.50 at risk). (2) **See The Fire PROBABLE NR** — absent from RP live racecard; Coronation Cup EW outsider £0.25 at risk; Coronation Cup now 6 runners. (3) **Causeway NR confirmed** — Derby still 14 runners (Constitution River, Endorsement, Proposition also absent — consistent with Friday check). (4) All remaining core picks confirmed: Item 16:00 at 5.0 synthetic (live was 3.25 in bets file — expected gap), Kinswoman 15:15 @ 24.0, Allegresse 16:40 @ 9.0, Lord Melbourne 17:20 @ 13.5. (5) Going: no update from RP at 07:08 — still "GTS, Good in places" from 2026-06-03. River forecast: Soft possible by Derby post-time. (6) market-baseline.json: 39,019 bytes; market-latest.json: 39,140 bytes (BASELINE_CAPTURE status). Filed decisions: `livingston-sat-baseline-NRs.md` + `livingston-sat-baseline-2026-06-06.md`. Race counts post-NR-filter: 13:30=8, 14:05=9, 14:40=6, 15:15=18, 16:00=14, 16:40=11, 17:20=17, 17:55=18. All prices remain SYNTHETIC (2026-06-02 source) — market_move delta will be flat; NR flags are the only actionable data.

## Archive — pre-Derby learnings (2026-06-03 → 2026-06-05)

Detailed entries compressed by Scribe-19 on 2026-06-08 (file exceeded 15KB). Full history in git pre-2026-06-08.

- **2026-06-03**: Built `data/enrichment/trial-form.json` (276 horses, 25 with verified trials). Built `trainer-14d.json` (28/93 trainers covered) and `jt-combo.json` (5 combos, 22 horses). Equipment discovery probe: equipment data sourceable from RP `__NEXT_DATA__`; wind ops paywalled. Built `equipment.json` (272 runners, 30 headgear codes, 11% coverage).
- **2026-06-03 morning_odds rename**: `saturday_morning_odds.py` → `morning_odds.py` (covers Ladies + Derby Day). Added `--mode archive` for snapshotting baseline/latest with date suffix.
- **2026-06-05 Friday gates**: 09:52 Friday AM gate (Belinus confirmed WITHDRAWN; Sugar Island drifted 33/1 → 16-22/1; RP 60s rate-limit identified). 11:59 midday refresh (prices stale synthetic 2026-06-02). 12:40 Betfair-key activation check (NOT FEASIBLE — no app key, no SSO session). 12:44 price-source survey (CSV override only feasible path). 12:59 odds-provenance correction (scraped, not transcribed).
- **2026-06-05 16:25 stale-data NR failure pattern**: Port Road then Triple Double A both not in live declared fields. Built `live-runners-2026-06-05.json`. Working URL pattern: `sportinglife.com/racing/racecards/{date}/epsom-downs/racecard/{race_id}/{slug}`. Race IDs 920732-920738.
- **2026-06-05 16:50 HARD-RULE ratified**: Livingston live-runner gate. Mandatory for all race days. Skill: `.squad/skills/live-runner-verification/SKILL.md`.
- **2026-06-05 19:10 post-race results capture**: Ladies Day results 27,850 bytes, 8 races. **Key finding: RP results pages work post-race even when racecard pages are blocked mid-day.** RP URL pattern: `/results/17/epsom/{date}/{race_id}/`. Sporting Life individual race result pages return JS component errors. ATR blocks results.
- **2026-06-05 21:00 Friday archive gate**: Archived baseline (39KB) + latest (54KB) to `data/enrichment/archive/2026-06-05/`. Saturday placeholders created. **Hickory Lad SP 100/30 WIN re-confirmed (Saul Stage 2a block reversed)** — Friday P&L revised −£11.61 → −£10.07. RP HTML confirmed: result pages list horses in finishing order, cloth numbers inline but NOT sort key. New RP IDs: 920049 (13:30 Dash), 920050 (14:05 Woodcote).

## 2026-06-08 — Cross-Agent Update (v0.4 wave-1 GREEN)

Wave-1 publish-readiness sprint shipped GREEN. Saul-3 gate review verdict 🟢 GO for all four items:
- **Livingston-5** (you): RUNBOOK.md shipped (this entry above) — 565 lines, 8 sections, two-source scrape pattern + manual fallback codified.
- **Rusty-7**: `src/market_drift.py` shipped. Lord Melbourne +53.8% drift (your Derby Day finding) was the earning event. Module prefers fractional string over decimal_odds — discovered synthetic-price artefact where `decimal_odds: 13.5` vs `fractional_odds: "12/1"` (=13.0) silently dropped the drift signal below the 50% threshold. **Action for you:** future `market-baseline.json` writes should add `baseline_price_type: "synthetic" | "ante_post" | "traded"` per Rusty's request — would let downstream signals distinguish price-discovery from genuine confidence moves automatically.
- **Linus-14**: render_header() refactor — when you ship `bets-{date}.json`, the new top-level `meta` block ({card_date, course, validation, generated_at}) drives header rendering. Backward compat preserved (missing meta defaults to Epsom).
- **Danny-2**: `.env.example` + `check_env.py` validator. Sporting Life creds (`SPORTINGLIFE_USER`, `SPORTINGLIFE_PASS`) now REQUIRED; fail-loud on missing.
- Royal Ascot 2026-06-16 live-test: `morning_odds.py` `RACECARD_FILES` hardcoded for Epsom dates — Danny owns the update. Your live-runner gate procedures will apply at Ascot unchanged.
- Pre-existing `test_racecard_wave33` failure: confirmed NOT a wave-1 regression. Saul will own the next-sprint fix.

---

## 2026-06-06T23:02:55+01:00 — Team Update (Cross-Agent Findings)

**From Saul's Derby Day Process Audit:**

3 hard publish blockers identified:
1. **T-1hr gate timing** — Derby check fired 39 minutes late (hourly watchdog ticks insufficient)
2. **Silent completion defence** — Livingston-3 output sat unread 7+ hours (platform silent success bug mitigation needed)
3. **HTML header staleness** — Manual patch class recurring (must compute header from JSON at render-time)

See .squad/orchestration-log/2026-06-07T00-36-45Z-saul.md for full audit details.

**From Rusty's Derby Day Signal Frame:**

v0.4 market_drift module proposed with 0 HIGH / 1 MEDIUM / 8 SPECULATIVE confidence signals. Benvenuto Cellini steam (9/4 → Evs) and Lord Melbourne drift (+53.8%) both correctly identified.

See .squad/orchestration-log/2026-06-07T00-36-45Z-rusty.md for full signal frame.

---

## 2026-06-08 — Livingston-6 Chunk 2 scraper parameterization

- Shipped v0.4 #6 Chunk 2 for scraper/odds/refresh wiring. Ascot Racing Post course id confirmed/configured as `1` with path `ascot`.
- Added dry-run `scripts/scrape_racingpost.py` and `scripts/scrape_sportinglife.py` entrypoints that default to Epsom, consume course/meeting config, and emit course-prefixed non-Epsom enrichment paths.
- `morning_odds.py` now keeps legacy Epsom market filenames but writes non-Epsom snapshots as `market-{baseline|latest}-{course}.json`; RP runner confirmation already consumes config ids/paths.
- `refresh_friday.py` preserves the old no-flag Epsom two-day wrapper, while `--course=ascot --meeting=royal-ascot-2026` resolves all configured meeting days when `--date` is omitted.
- Parameterized archived equipment RP URLs from course config without moving historical artifacts. Verification: `python -m pytest -x --ignore=tests/test_racecard_wave33.py` => 478 passed.

- 2026-06-08 12:45: **Livingston-7 Ascot synthetic E2E smoke COMPLETE.** Built `tests/fixtures/ascot/raw-ascot-2026-06-16-racecards.json` plus working raw copy for Royal Ascot 2026 Day 1 (6 synthetic races, 48 fake runners, Good to Firm). Stubbed course-prefixed live-runners/RP/SL/going enrichment, then ran fetch, score, predict, report, and card with `--course=ascot --meeting=royal-ascot-2026 --date=2026-06-16`. Core pipeline works and generated `outputs/report-ascot-2026-06-16.html` + `outputs/racecard-ascot-2026-06-16.html`; scores were non-trivial (5.0-95.0, 38 unique) while Ascot draw/CD/trial priors stayed neutral at 50.0. Rough edges found: report/card still read default Epsom market/going context in places, CLI predict schema does not satisfy T-60/render_header meta expectations, CLI card does not exercise bets_json_path/trifecta header path, no slip artifact is produced, and RUNBOOK remains Epsom/Derby-specific. Required suite passed: 484/484 with wave33 ignored. Verdict: PIPELINE-WORKS-WITH-ROUGH-EDGES. Full report in `.squad/decisions/inbox/livingston-7-ascot-e2e-smoke.md`.

- 2026-06-08 14:00: **Livingston-8 Ascot re-smoke COMPLETE.** Re-ran the Livingston-7 Royal Ascot 2026-06-16 synthetic E2E flow without regenerating fixtures. Linus-18 R-7/R-8/R-9 are closed: `bets-ascot-2026-06-16.json` now has `meta`/`entries`, CLI card renders real outlay GBP 11.70 from bets, `predict` writes `outputs\slip-ascot-2026-06-16.txt`, and T-60 no longer reports missing meta, computed GBP 0.00 mismatch, or missing slip. T-60 still exits 2 only for known env hygiene (`SPORTINGLIFE_USER`, `SPORTINGLIFE_PASS`). Suite sanity passed: `python -m pytest -x --ignore=tests/test_racecard_wave33.py` => 490 passed. Remaining old edges: stale 2026-06-06 odds snapshot leak, Derby CSS comment, racecard Going TBC. New low-severity operator edge: PowerShell T-60 detail wraps/splits GBP 11.70 across two lines. Verdict: R789-CLOSED-WITH-NEW-EDGE. Full report: `.squad/decisions/inbox/livingston-8-ascot-resmoke.md`.
- 2026-06-08 15:00: **Livingston-9 Chunk 5 + Chunk 6a + FU-1 COMPLETE.** Decided data layout should stay flat-with-course-prefix for non-Epsom while preserving historical Epsom archive paths; documented the path table and archive policy in `docs\data-layout.md` and added the design note to `src\course_config.py:path_for()`. Rewrote `RUNBOOK.md` as a Windows-first operator workflow for any `{course}/{meeting}/{date}`, with Epsom Derby, Royal Ascot Day 1, and generic examples; closed all 10 Livingston-7 gaps including Sporting Life credentials, PowerShell snippets, course-prefixed artifacts, T-60 meta/slip expectations, and raw `horse`/`horse_name` troubleshooting. Fixed FU-1 by moving `scripts\morning_odds.py` credential gate after the dry-run branch and adding `tests\test_morning_odds.py::test_dry_run_without_credentials_does_not_fail`. Validation: targeted morning_odds test passed, Ascot dry-run without credentials exited 0, live no-creds mode exited 1, full suite `python -m pytest -x --ignore=tests/test_racecard_wave33.py` passed with 500 tests. Verdict: all three deliverables READY-FOR-GATE.

- 2026-06-08 19:35: **Livingston-10 publish docs COMPLETE.** Closed Danny-6 publish-readiness docs punch list #1-#2: rewrote root README as the consumer landing page and updated all 7 flagged `.squad\skills\*\SKILL.md` files. README is now course-agnostic with a Royal Ascot 2026-06-16 quickstart, Sporting Life env-var setup, course-prefixed output artifacts, and an explicit RUNBOOK pointer. Full rewrites: live-runner-verification, morning-odds-gate, trifecta-box-from-scoring. Surgical publish-readiness rewrites/edits: bet-pass-rationale, midday-regen-preserving-context, per-race-outsiders, race-day-report-footnotes. All touched docs are ASCII and use `--course` / `--meeting` / `--date` examples plus current flat course-prefixed paths from `docs\data-layout.md` and `path_for()`. Validation: `pytest -q` needed `PYTHONPATH` in this shell; raw full suite still exposes known pre-existing `tests\test_racecard_wave33.py` failure, while accepted publish sanity `pytest -q --ignore=tests/test_racecard_wave33.py` passed 500/500. Handoff: READY-FOR-GATE for Saul-12 via Coordinator.

## 2026-06-08 - v0.4.0 consumer dress-rehearsal
- Ran a fresh v0.4.0 clone at C:\Users\stevenn\race-analysis-rehearsal as a first-time consumer.
- Found 3 blockers: editable/dev install fails, Ascot Quickstart cannot render without missing raw racecard/live ingest, and tests fail on wave33 after recovery.
- Dry-run URL discovery and env-var diagnostics worked well; recommend v0.4.1 docs/package/test fix before Royal Ascot operator use.

## 2026-06-08 - Livingston-12 v0.4.1 docs patch
- Rewrote README Quickstart from Royal Ascot live example to Epsom 2026-06-06 offline replay using committed raw, scores, bets, report, racecard, and slip artifacts.
- Added explicit v0.4.x live-fetch caveat for Royal Ascot 2026-06-16 and pointed operators to RUNBOOK sections 2.2 and 5 for the manual race-day path.
- Reconciled README expected artifacts: T-60 status is documented as RUNBOOK-only, not a Quickstart output.
- Removed consumer-facing README dependency on internal `.squad` files and kept `.squad/skills` unchanged after grep found only course-example tables, not an Ascot Quickstart contradiction.
- Added CHANGELOG v0.4.1 entry for R-1 through R-7 publish-blocker fixes.
- Verification: Epsom replay fetch, score, predict, report, and card all exited 0; restored regenerated Epsom archive outputs afterward to avoid unrelated artifact churn. Test sanity recovered from missing `src` import by setting PYTHONPATH to repo root; `pytest -q --ignore=tests/test_racecard_wave33.py` passed 500/500.

## 2026-06-10 - Livingston-13 v0.5.0 import-only docs
- Rewrote README around the v0.5.0 browser save plus `race-analysis fetch --from-file` workflow and kept the Epsom 2026-06-06 offline replay for demo/regression use.
- Prepended CHANGELOG v0.5.0 with import parser, not_available going-fit source flag, nullable price/RPR/TS tolerance, deprecated scrape scripts, and consumer ToS notes.
- Updated RUNBOOK, docs data-layout provenance, .env.example, and race-day skills for the save-and-parse workflow with manual JSON as fallback.
- Renamed Sporting Life and Racing Post scrape scripts to `.deprecated.py`, added exit banners, and retained original code as unreachable historical reference.
- Verification: installed editable package, then ran `race-analysis fetch --from-file tests\fixtures\Sportinglife\sample-meeting.html --course ascot --meeting royal-ascot-2026 --date 2026-06-16`, followed by score, predict, report, and card. All exited 0. Handoff: `.squad\decisions\inbox\livingston-13-v0-5-0-docs.md`. Verdict: READY-FOR-GATE.
