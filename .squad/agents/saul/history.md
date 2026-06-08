# Saul — History

## Project context (seeded 2026-06-03)

- Python 3.12 race-analysis toolkit. Repo Steve-MS/Derby, commit 5a1770e.
- 227 pytest tests currently passing.
- Test pattern: each signal module has its own `tests/test_<signal>.py` with 18-22 tests.
- Reviewer authority on all scoring/signal/betting PRs.
- Key validation milestone: once Ladies Day (Fri 5 Jun) is run, backtest the model's Friday predictions against actual results before Derby Day picks are finalised.
- Boundary cases to always test: missing data → neutral 50, scratched horses, single-runner edge case.

## Learnings
### 2026-06-08 — Chunk 1 config gate
- Course/date decoupling gate should separately validate the pure resolver and the operator entry points: here `resolve_day()` fails loud on unknown configured dates, while legacy wrappers may intentionally keep older date defaults for backward compatibility.
- For shared dirty trees, record both `git diff --name-only` and untracked files; a GO can still require Scribe to stage only the reviewed chunk and leave unrelated inbox/test artifacts out.
- When a watchdog command writes a manifest during review, clean the generated output afterward so scope discipline evidence is not polluted by reviewer-created files.

### 2026-06-08 — T-60 watchdog re-gate after Linus-15
- Re-gate pattern: verify the exact rejected seams first, then run targeted tests, full suite, and idempotency; this caught both source correctness and operator behavior without re-litigating the whole artifact.
- Linus-15 did well by adding tests for every previous blind spot: pre-env ordering, independent stake arithmetic, render-header mismatch as a separate row, missing meta fallback, and race-scoped NR cases.
- Manual bad-env plus missing-artifact verification is valuable even when unit-covered: it proves the operator sees both failure classes in a single T-60 run.
- Lint/type-check evidence must distinguish "failed" from "not configured"; this repo currently exposes pytest only in pyproject, so record that explicitly instead of implying a skipped pass.
### 2026-06-05 — Ladies Day P/L Scoring (Stage 2a retro)

- **EW stake convention:** `bets-2026-06-05.json` records Wild Terrain as `stake_gbp: 2.44` (= TOTAL EW, £1.22 per side). Outsiders use `stake_gbp: 0.25` per side (£0.50 total). Inconsistent naming but confirmed by HTML total £11.61 arithmetic.
- **HTML is source of truth** for final picks. Race-day hand-edits by Linus added 7 per-race outsider EW rows not in the pre-race bets JSON. The bets JSON only shows 1 original outsider (Prizeland), superseded.
- **Trainer cross-reference trick:** Winner trainer in results JSON can confirm/deny WIN-side outcomes even when full finishing positions are absent. Respond, Wild Terrain, Hickory Lad, Liberty Lane, Rosie Frith WIN sides all confirmed lost this way.
- **Blocked bet scope:** Only EW PLACE portions blocked. WIN portions resolvable via trainer field in results. Doubles/treble all resolvable because at least one leg in each had a known confirmed-loss.
- **SP movement flags:** Stellar Sunrise (6/1 → Evens) and Dance In The Storm (16/1 → 15/8F) both massive market movers that lost as favourites. Key calibration input for Rusty.
- **Key output files:** `data/results/pl-2026-06-05.json` (P/L JSON), `.squad/decisions/inbox/saul-ladies-day-pl-2026-06-05.md` (decision note).
- **Mister Winston PASS:** Won at ~7/1 on 13% edge (below 15% gate). Gate question flagged for Danny — was 15% correct cutoff for 7/1 band?
- **Near-miss definition applied:** "4th or better at SP ≥ 10.0 decimal." ZERO picks qualify from confirmed results. Arctic Thunder (6th, SP 12.0) and Assaranca (5th, SP 34.0) fail on finish position only.

### 2026-06-08 — T-60 watchdog gate patterns

- **First-step means first executable side effect:** if a wrapper has module-level gates before `main()`, a later watchdog call is not truly first and may fail to write the manifest evidence coordinators need.
- **Watchdogs must be independent of renderers:** stake-total reconciliation should compute from betting JSON directly, then compare rendered header separately; importing the renderer as source of truth can inherit the bug being guarded against.
- **Live-runner checks need race scope:** global active/inactive horse-name sets can hide cross-entered runner problems. Future NR/VOID tests should include same-name or cross-entry fixtures.
- **Test-count drift is review evidence:** targeted watchdog tests passed 5/5, but full-suite count after ignoring the known failure was 453, not the requested 454; always record collected/pass counts exactly.

## Review Log

### Archive — pre-Derby reviews (2026-06-03 → 2026-06-05)

Detailed review log compressed by Scribe-19 on 2026-06-08 (file exceeded 15KB). Full history in git pre-2026-06-08.

- **2026-06-04 trial_form (Rusty v0.4)**: APPROVED. 19 tests, scoring formula matches Danny's spec, weight 0.0800. Coverage: tier compression, freshness flat-step decay, walkover cap.
- **2026-06-03 v0.5 source review GATE (Rusty)**: REJECTED initially — found None-guard gaps in market_move/trainer_14d/jt_combo. Re-review R2 (after Linus hardening): APPROVED. All None inputs route to neutral 50.
- **2026-06-03 v0.5 signal batch tests**: 27 new tests across the three modules. Edge cases covered: empty market files, missing horse keys, single-runner fields, name-normalisation collisions on jt_combo.
- **2026-06-03 v0.6 equipment signal**: Tests drafted (18), source review GATE APPROVED. Equipment data sourceable from RP `__NEXT_DATA__`. Wind ops paywalled → skipped (correct call by Livingston). Scoring curve verified: base 50 + first-time deltas + stacking, clamp [10,90].
- **2026-06-05 16:50 ESCALATION**: Stale-runner detection test coverage. Three Ladies Day NR cascade failures (Triple Double A, Blue Brother, Cameo) showed our tests lacked live-runner-presence assertions. Added regression tests in collaboration with Livingston's live-runner gate skill.
- **2026-06-05 12:59 Derby trifecta-box (Linus)**: Hand-assembled box reviewed (Item, Benvenuto Cellini, Maltese Cross, Causeway, £24/24-combo). Heads-up filed for future `trifecta_box(race_scores, n=4)` helper in `src/betting.py`.
- **2026-06-05 15:13 Prizeland NR replacement (Linus)**: Hand-edit reviewed. `render_replacement_row()` flag escalated to HARD-RULE (priority: ship before Royal Ascot).
- **2026-06-05 NR replacement helper review**: Caveat distinction validated — runner-validity caveat (red) must render separately from price-staleness caveat (amber). Existing merged caveat conflated the two failure modes.
- **2026-06-06 hand-edit on Derby card + render_trifecta_box() helper (Linus)**: Review of card injection; flagged the recurring header-staleness blocker (Saul Derby Day audit #3) that became Linus-14's render_header() refactor in wave-1.
- **2026-06-05 Ladies Day P/L (Stage 2a)**: Hickory Lad SP 100/30 WIN correction (Stage 2a initially blocked, Livingston re-scrape reversed). Final Friday P&L: −£10.07 confirmed. SP movement flags (Stellar Sunrise 6/1→Evens, Dance In The Storm 16/1→15/8F) calibration input for Rusty.

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

### 2026-06-08 — v0.4 wave-1 gate review (saul-3, re-attempt)

All four items cleared 🟢 GO. Re-ran 448 tests after a 14h gap following saul-2's CAPI crash — zero drift, 46/46 market_drift + 22/22 render_header + 14/14 check_env all pass, full suite 448/448. Key findings: (1) market_drift.py has Derby Day horse names in docstrings only — executable code is fully portable; the WEIGHT=0.0 gate-only design is correct and scoring.py weight sum remains 1.0000. (2) render_header's £12.50 arithmetic verified directly in the HTML and via parametric tests; EW double-stake, VOID/NR exclusion, and backward-compat (missing meta) all correct. (3) Danny's check_env wiring fires at module-level in both refresh_friday.py and morning_odds.py — no late-discovery risk. (4) Working tree holds ~30 orphan files from Derby Day race-day work that must be committed separately; coordinator should stage wave-1 (22 items) independently. (5) Pre-existing test_racecard_wave33 failure confirmed via git evidence — test was committed at HEAD before sprint, fixture lacks scenario field needed for GREEN SLIP banner assertion; assigned to Saul next sprint. Crash-resilience protocol (stub file on first tool call, section-by-section update) worked as designed — lesson for all agents: write state immediately before doing work, not after.


## 2026-06-08 — Cross-Agent Update (v0.4 wave-1 GREEN)

Wave-1 publish-readiness sprint shipped GREEN. All four work items GREEN GO. Full suite 448/448 PASS (minus pre-existing wave33 — confirmed pre-existing, not a wave-1 regression).

- **Rusty-7**: src/market_drift.py shipped (46/46) — gate-only modifier, weight 0.0, Lord Melbourne +53.8 percent earning event.
- **Linus-14**: render_header() JSON-driven refactor (22/22) — eliminates recurring pound-total mismatch publish blocker (Saul's Derby Day audit #3).
- **Danny-2**: .env.example + scripts/check_env.py validator (14/14) — Sporting Life creds fail-loud at startup, wired into refresh_friday.py + morning_odds.py.
- **Livingston-5**: RUNBOOK.md (565 lines) — two-source scrape pattern + manual fallback codified.
- **Saul-2** crashed mid-run 2026-06-07 ~19:11 BST (CAPI error after 1h41m, no output written). **Saul-3** re-attempt succeeded 2026-06-08 08:40 with crash-resilience protocol (incremental note-writing).
- Next-sprint open items: fix test_racecard_wave33 fixture (Saul); update morning_odds.py RACECARD_FILES for Royal Ascot 2026-06-16 (Danny); sanitise market_drift.py docstring of Derby Day examples (low-priority backlog); pre-sprint Derby Day orphan files need separate close-out commit (Coordinator).
