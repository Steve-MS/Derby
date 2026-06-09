## SUMMARY (2026-06-06 Post-Derby)

**Key deliverables:**
- Trifecta box for Derby (4-horse: Item, Benvenuto Cellini, Maltese Cross, Causeway) — £24 stake
- HTML header staleness recurring issue — manual patches required on Apollo One override (BLOCKER for publish)
- render_replacement_row() promoted to HARD-RULE (must ship before Royal Ascot)
- Live-verified NR swaps for Ladies Day (Triple Double A→Asmen Warrior, Blue Brother→Arctic Thunder)

**Publish blockers identified:**
- HTML header not updating on injection (must compute from JSON at render-time)
- render_replacement_row() must distinguish stale PRICE vs stale RUNNER (two separate caveats)
- Trifecta box vulnerable to single NR voiding entire ticket (consider 4-horse minimum or EW legs)

**Current state:**
- outputs/racecard-2026-06-06.html: 21,745 bytes (stale Causeway still in HTML pending Danny's decision)
- outputs/bets-2026-06-06.json: 9,508 bytes (valid, scenario GREEN, going GTS+)
- 
ender_replacement_row(): design approved, implementation pending (HIGH priority before Royal Ascot)


---

# Linus — History


# Linus — History

## Project context (seeded 2026-06-03)

- Python 3.12 race-analysis toolkit. Repo Steve-MS/Derby, commit 5a1770e.
- Owns `src/report.py` (HTML) + `src/betting.py` (betting maths + recommendations).
- Steve's standing rules:
  - £100 total outlay per day
  - One A4 race card per day (not per race)
  - Outsider bet required for the Derby itself
  - Accumulator suggestion per day
- `SIGNAL_LABELS` dict lives at lines ~44-56 of `src/report.py` — add new label whenever Rusty ships a signal.

## Archive — pre-Derby learnings (2026-06-03 → 2026-06-05)

Detailed entries compressed by Scribe-19 on 2026-06-08 (file exceeded 15KB). Full history in git pre-2026-06-08.

- **2026-06-03 v0.4–v0.6**: Added SIGNAL_LABELS for trial_form, market_move, trainer_14d, jt_combo, equipment in `src/report.py`. Updated betting outputs after each signal ship.
- **2026-06-05 16:50 ESCALATION**: `render_replacement_row()` promoted to HARD-RULE priority (ship before Royal Ascot). New parameter `runner_verified_source` distinguishes stale-price (amber) vs stale-runner (red) caveats. Three NR swaps in one afternoon established the pattern.
- **2026-06-05 16:45**: Full hand-edit of racecard + report for Ladies Day NR swaps (Triple Double A→Asmen Warrior, Blue Brother→Arctic Thunder). 🟢 Live-verified stamp added.
- **2026-06-05 PM Derby trifecta box** (race-day-eve): 4-horse hand-built box (Item, Benvenuto Cellini, Maltese Cross, Causeway) @ £1/combo = £24 total. No `trifecta_box()` helper exists — flagged for future `src/betting.py` addition.
- **2026-06-05 PM Port Road → Triple Double A swap (16:40 HKJC, second NR edit)**: rendered with stale-odds caveat; horse confirmed NR post-publish, triggering v2 swap to Asmen Warrior. Root cause: caveat warns price only, not runner validity.

## 2026-06-08 — Cross-Agent Update (v0.4 wave-1 GREEN)

Wave-1 publish-readiness sprint shipped GREEN. Saul-3 gate review verdict 🟢 GO for all four items:
- **Linus-14** (you): render_header() refactor (this entry below) — header staleness BLOCKER #3 eliminated. Authority docstring confirms in-scope without coordinator escalation.
- **Rusty-7**: `src/market_drift.py` shipped — gate-only modifier (weight 0.0, multipliers 0.80/0.90), Lord Melbourne +53.8% drift was the earning event. When you wire market_drift into reports, the flag values (DRIFT_WARN / DRIFT_CRITICAL / STEAM_NOTED / MARKET_DATA_MISSING) should land in the existing flag rendering.
- **Danny-2**: `.env.example` + `check_env.py` validator. Sporting Life creds now fail-loud at startup.
- **Livingston-5**: `RUNBOOK.md` shipped — section 2 (two-source scrape pattern) and section 4 (manual live-odds fallback with exact JSON schema) are operator-facing.
- `render_replacement_row()` HARD-RULE escalation from 2026-06-05 16:50 is STILL OPEN. Royal Ascot 2026-06-16 is the deadline. Coordinator and Lead need to schedule this in wave-2 or before.
- Pre-existing `test_racecard_wave33` test failure: confirmed NOT a wave-1 regression. Saul will own the next-sprint fix (update fixture to pass `bets_json_path` with `scenario` field).

---


## Learnings

### render_header() JSON-driven refactor — header staleness eliminated (2026-06-07)

**Root cause fixed:** Every race day, after Linus injected a trifecta or Apollo-One override into bets JSON, the racecard HTML header showed stale values (£5.50 instead of £12.50 on Derby Day 2026-06-06). The header was computed once at template render-time from separate context args; when the JSON changed the HTML wasn't refreshed. Coordinator had to manually patch header after every injection — a recurring class of avoidable toil.

**Fix:** `render_header(bets_data)` in `src/report.py` computes totals, active bet count, NR line, trifecta breakdown, and validation tag entirely from `outputs/bets-{date}.json` at render-time. `render_card()` in `src/racecard.py` accepts a new `bets_json_path` parameter; when set, all header ctx values come from `render_header()` — not from row summation.

**Authority docstring added:** `render_header()` docstring makes explicit that any change to header fields is in scope for Linus whenever bets JSON changes. No coordinator escalation required. This directly addresses the systemic guardrail issue Saul flagged in the Derby Day audit.

**Proof of correctness:** `outputs/racecard-2026-06-06-v04-verified.html` re-renders yesterday's card and shows £6.50 WIN/EW + £6.00 trifecta = £12.50 total. Original `racecard-2026-06-06.html` preserved as historical record.

**Test coverage:** 22/22 tests in `tests/test_render_header.py`. Covers: £12.50 total from 8 picks + trifecta; VOID + NR excluded from total + listed in NR line; missing meta graceful defaults; validation tag pass-through; trifecta_box bet_type detection; entries vs bets key schema.

**Schema extended:** bets-{date}.json gains optional top-level `meta` block (card_date, course, validation, generated_at). Back-compat: missing meta → defaults, no crash.

**EW stake convention confirmed:** "£0.25 EW" in stake_guidance = £0.25 unit stake per side = £0.50 total outlay. `_parse_stake_amount()` extracts the unit; `render_header()` doubles it for EW. Sum with this rule: 6.50 ✓.



**Pipeline approach:** Option B (hand-edit). Option A (pipeline re-run) not viable on race day — stale enrichment data is the root cause, so re-running the pipeline would reproduce the same NR contamination. Surgical HTML edits to the outsider-pick blocks were the correct call. Gotcha: the report's field-ranking tables legitimately retain Port Road / Triple Double A / Blue Brother as historical model scoring rows — only the actionable recommendation blocks (`outsider-pick` divs) needed replacing.

**Verification stamp is now standard pattern:** Both racecard and report carry a 🟢 live-verified banner. This should be added to every race-day output going forward. Template:
```
🟢 Live-verified {DATE} {TIME} BST — All runners confirmed against Sporting Life + corroborating sources. Prices remain {DATE} vintage; verify at the rail.
```

**`render_replacement_row()` is a HARD RULE now — next race day starts with this work.** Four manual NR swap edits across two files in one afternoon (Cameo, Asmen Warrior, Arctic Thunder in racecard; Asmen Warrior + Arctic Thunder in report) is the definitive threshold. The helper ships before Royal Ascot (16–20 Jun 2026). It must cover: outsider-row swap, main-pick swap, separate stale-price vs runner-validity amber divs, always-emit rationale row, HTML entity escaping. No more hand-edits after this.

### T-60 watchdog independence and race-scoped NR checks (2026-06-08)

**Independence pattern:** A watchdog must not reuse the renderer as the authoritative calculation for the value it is meant to audit. For bets totals, the watchdog now computes active WIN/EW/trifecta stakes locally, compares declarations against that independent sum, and treats `render_header()` as a separate header-consistency row.

**Race-scoping bug pattern:** Horse names are not globally unique enough for NR/VOID checks. The same horse name can be inactive in one race and active in another, so live-runner status must be keyed by race scope (time/course/name) and compared only against the bet's own race.

### Config-loader and Epsom compatibility strategy (2026-06-08)

**Config-loader pattern:** `src/course_config.py` is the Chunk 1 source for course identity. It fail-loud validates required JSON fields, meeting presence, and day metadata; unknown meeting/date raises `CourseConfigError` rather than returning a fallback. Tests monkeypatch `CONFIG_DIR` for bad-config cases instead of writing throwaway files into the real config tree.

**Legacy path strategy:** `path_for(course, date, kind)` keeps Epsom on historical artifact names (`outputs/racecard-{date}.html`, `outputs/bets-{date}.json`, etc.) while non-Epsom courses get course-prefixed names (`outputs/racecard-ascot-{date}.html`). Raw racecards stay flat for all courses: `data/raw/{course}-{date}-racecards.json`. This lets Ascot dry runs avoid Epsom output collisions without churning Derby artifacts.

**CLI defaulting sharp edge:** `--course` and `--meeting` default to `epsom` / `derby-2026`; `src.cli` and `t60_watchdog.py` default `--date` to today. `refresh_friday.py` remains the Epsom wrapper for one release, so no-date operation still uses the Derby meeting day list unless a non-default course/meeting is passed. Do not call `resolve_day()` in watchdog/default smoke paths because today can be outside the configured Derby days after the meeting.

### Chunk 3 presentation decoupling — config-backed report/racecard titles (2026-06-08)

**Pattern:** Keep renderer context backward-compatible (`venue`/`day_name`) but drive templates from `meeting.title` + `day.label` resolved via `src.render_helpers.presentation_context()`. For Epsom, the helper preserves legacy headings from config default display name; for non-default meetings it derives meeting brand from the configured meeting slug (e.g. `royal-ascot-2026` -> `Royal Ascot 2026`) without editing course JSON.

**Path rule:** Report/racecard renderers now expose `report_output_path()` / `racecard_output_path()` wrappers over `course_config.path_for()`. Epsom remains legacy (`outputs/report-YYYY-MM-DD.html`, `outputs/racecard-YYYY-MM-DD.html`); Ascot renders to course-prefixed outputs.

**Gotcha:** Current committed/untracked historical Epsom HTML artifacts are hand-edited race-day files, not clean renderer output; byte-diffing fresh CLI output against them is not meaningful for full-file equality. Header/title presentation stayed legacy-identical in fresh render smoke; document any historical diff as artifact drift rather than a presentation regression.

### Linus-18 CLI seam patch - schema drift lesson (2026-06-08)

CLI and script paths had drifted: Badger's legacy `singles`/`portfolio_summary` payload still powered report/racecard rows, while Linus header/T-60 consumers expected `meta` plus entry records. The safe migration pattern is additive: keep legacy keys byte/semantic-stable for Steve/report consumers, add `meta` and `entries`, and make watchdog/render-header derive equivalent entries from legacy payloads until every producer is upgraded. Slip validation must understand EW display conventions: entries store EW unit stake for computation, while operator slips may show either unit or total EW outlay. Future CLI seams should share schema adapters from `src/` instead of reimplementing totals in scripts.

### Linus-19 chunk6 src polish (2026-06-08)

- Going artifact pattern: CLI card should resolve `enrichment-going` through `path_for()` and pass the extracted string into `render_card(going=...)`. Let the template keep `Going: TBC` only as a missing-data fallback, not as CLI behavior.
- Market snapshot pattern: Epsom keeps legacy `data/enrichment/market-latest.json`; non-Epsom must use `market-latest-{course}.json` or render `Odds snapshot unavailable`. Never let report/card default to Epsom market context for another course.
- Priors edge-case pattern: `scoring_priors_for(..., priors={})` is the direct empty-object contract; null config means neutral; non-object config is a loud `CourseConfigError`; partial config deep-merges neutral defaults.
- Trial-form loader pattern: raw trial enrichment normalization now requires an explicit course. `trial_form_signal()` resolves the course once and the cache is keyed by course, preventing silent Epsom prior coupling when a second course later enables trial-form calibration.
- Equipment defaults decision: removed empty unused `equipment_defaults` from course configs and neutral priors as YAGNI. Reintroduce only when `score_equipment()` has a real course-specific calibration contract and regression coverage.
- Regression note: Epsom 2026-06-06 scores exact-match after changes; bets only changed in volatile `generated_at` during the smoke run. Full suite excluding `test_racecard_wave33.py` passed 500/500.

### Linus-20 v0.4.1 src patches (2026-06-08)

- R-1 packaging lesson: `setuptools.build_meta` fixes the import error, but this repo's package is literally named `src`; editable install also needs explicit setuptools package discovery (`packages = ["src"]`) or the console script cannot import `src.cli` outside the checkout CWD.
- R-5 wave33 disposition: Option A. The test was stale, not prod: committed `outputs/bets-2026-06-06.json` no longer has `item_special_bet`/`scenario`, so Item is correctly rendered as PASS with `edge -52.9%` and total outlay `GBP 6.40`; stale speculative assertions were removed.
- R-7 help guard: CLI help now uses course-agnostic copy and Ascot examples with `--course ascot --meeting royal-ascot-2026 --date 2026-06-16`; regression test asserts the old `Epsom Classics 2026` string stays gone.
- Validation: clean throwaway venv `pip install -e .` succeeded, `race-analysis` resolved on venv PATH and printed help, and full `python -m pytest -q` passed 503/503 with no ignores.
