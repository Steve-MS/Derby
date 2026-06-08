# Danny — History

## Project context (seeded 2026-06-03)

- Python 3.12 race-analysis toolkit for Steve (Steve-MS).
- Repo: github.com/Steve-MS/Derby on main, last commit 5a1770e.
- Python interpreter: `C:\Users\stevenn\AppData\Local\Programs\Python\Python312\python.exe`.
- 227 pytest tests passing.
- Scoring weights v0.3, sum 1.0. Sire stamina at 0.05.
- Backlog (impact order): trial form → market move → trainer 14-day → J/T combo → equipment/wind.
- Derby Saturday 6 Jun 2026. Ladies Day Friday 5 Jun. Both raced.
- Steve's daily outlay cap: £100. Wants accumulator suggestion per day.
- Current Derby top 5: Item, Maltese Cross, Causeway (outsider pick), Benvenuto Cellini, Christmas Day.

## Learnings

- 2026-06-08 (Danny-4 decouple scoping): Inventory found 5,236 target-venue/date/day-label hits. Most are historical DATA/OUTPUT/DOC, but the real coupling debt is concentrated in runtime path construction, report labels, scraper venue IDs, and scoring defaults. Ascot-safe reuse requires neutral unknown-track defaults plus config-driven venue/meeting/date identity before any new venue calibration.

- 2026-06-08 (Danny-3 orphan classification): Race-day drift is accumulating in three buckets: canonical data/output that deserves a close-out commit, local operational artifacts that need gitignore coverage, and hardcoded one-shot scripts/tests that need owner review before becoming product. Systemic fix: add a post-race close-out checklist that separates data commits, process-skill commits, gitignore candidates, and one-shot-script triage.

- 2026-06-03 (session 1): Designed trial_form signal (weight 0.08, gated 10f+, Tier 1/2/3 taxonomy, best-of-multiple-runs, neutral 50 on missing data); proposed v0.4 weights scaling all v0.3 by 0.92; spec written to `.squad/decisions/inbox/danny-trial-form-design.md` for Rusty to implement.
- 2026-06-03 (session 2): Designed 3 new signals for v0.5 (Derby Saturday T−2 days). Spec at `.squad/decisions/inbox/danny-3-signals-design.md`.
  - `market_move` (0.0700): implied-probability-shift scoring (Δip = ip_latest − ip_baseline); piecewise linear 10–90; Saturday 09:00 baseline vs T−30 min latest; both prices required else neutral 50; Livingston to extend Friday scraper. 8 open questions for Steve (timing, source, small-field treatment).
  - `trainer_14d` (0.0400): 14-day strike rate; sample guard < 5 runners → 50; piecewise linear calibrated to UK flat ~10–12% average at neutral; per-trainer JSON keyed by trainer name. Questions: surface scope (AW?), window length (14 vs 21d), ROI secondary metric.
  - `jt_combo` (0.0300): jockey/trainer interaction term; combo strike rate over trailing 365d; sample guard < 10 partnerships → 50; first-time pairing scores 60; pipe-delimited combo_key. Questions: time window, first-booking lean, double-count mitigation vs existing jockey + trainer_form signals.
  - v0.5 weight rebalance: existing 12 signals × 0.86; class_rating absorbs −0.0001 rounding residual (0.2032 → 0.2031); 15-signal total sums exactly to 1.0000.
- 2026-06-03 (session 3): Designed equipment signal for v0.6 (equipment-only; wind ops dropped — paywalled per Livingston's probe). Spec at `.squad/decisions/inbox/danny-equipment-design.md`.
  - `equipment` (0.0250): item-weighted delta score; base 50; first-time-use bonuses by item type (b=+8, cp=+7, tt=+6, v=+5, h=+3, e/p=+2); stacking penalty −3 per extra item beyond first; equipment removal +3 per item; clamp [10, 90]; neutral 50 on missing horse or empty lists. No distance/surface gate.
  - Data: `data/enrichment/equipment.json` (Livingston to rename from equipment-wind.json; source: Open Horse Racing Data free CSV).
  - v0.6 weight rebalance: existing 15 v0.5 signals × 0.9750; class_rating absorbs −0.0002 rounding overshoot (0.1980 → 0.1978); 16-signal total sums exactly to 1.0000.
  - 4 open questions for Steve (stacking penalty, removal direction, Livingston data reliability, scope Friday+Saturday).

- 2026-06-05 (session 5): Midday refresh round. Livingston (11:59 BST) executed market refresh: no material price moves, no new non-runners, prices remain synthetic 2026-06-02. Linus executed Option B regen (timestamp-only, preserving in-day manual work). Synthetic-price tag retained for Ladies Day + Derby Saturday. Market_move signal inert (0% deltas) until live-price ingestion implemented.

- 2026-06-05 16:50 — ESCALATION: Helper promotion `render_replacement_row()` elevated to HARD-RULE priority
  - **Context:** Three NR swaps on Ladies Day (Port Road → Triple Double A → Asmen Warrior, Blue Brother → Arctic Thunder) with two manual failures (Triple Double A also NR, caught 28min before race). Current merged stale-odds caveat conflates two distinct concerns: stale PRICE vs stale RUNNER.
  - **Problem:** `render_replacement_row()` currently in `src/report.py` is not generalized enough. Manual swap pattern (Linus hand-edits HTML + footnotes) is proving unsustainable. Three swaps in one afternoon = pattern.
  - **New requirement:** Promote helper to hardened public API with `runner_verified_source: str | None` parameter:
    - If `runner_verified_source='Sporting Life 2026-06-05T16:25 BST'` → render green ✅ caveat: "Runner live-verified [source]"
    - If None → render amber ⚠️ caveat: "Runner not live-verified — re-check at gate"
    - Stale-price caveat rendered SEPARATELY in amber: "Price ~20/1 from 2026-06-02 enrichment — verify at rail"
  - **Implementation priority:** HARD-RULE — helper ships BEFORE Royal Ascot (16–20 Jun 2026). No exceptions.
  - **Blockers:** None (existing HTML/CSS in src/report.py is stable; parameter is additive)
  - **Handoff:** Linus owns implementation; Saul owns test coverage (render_replacement_row() tests with both parameter values)
  - **Rationale:** Three manual hot-swaps in one afternoon proves the current manual workflow is error-prone. A hardened helper enables Saturday's Derby race-day pipeline to scale to multiple NR swaps without manual HTML surgery.

- 2026-06-03 (session 4): Resolved v0.5 spec-vs-implementation mismatches in `.squad/decisions/inbox/danny-v05-spec-addendum.md`.
  - `score_market_move(0.024)` stays at 65.5: the piecewise curve itself is coherent; the `~62` anchor was an arithmetic/example error.
  - `score_trainer_14d(0.10)` stays at 50.0: neutral at 10% is defensible and matches the stated 10–12% average-band intent.
  - `jt_combo` first-time override applies only when `combo_runners == 0`; if combo history exists, the sample guard/scoring curve wins and the flag is audit noise.
  - No runtime code change required; v0.5 can ship as-is with spec/documentation clarification only.

- 2026-06-05 (session 6): Race-confidence metric flag (Derby). Linus's 4-horse trifecta box referenced:
  - Derby model stdev: **25.23** (HIGH variance, low confidence in top cluster).
  - Gap from #3 (Causeway) → #4 (Christmas Day): **0.22σ** (very tight, suggests 3-horse box inappropriate).
  - **Decision tree consequence:** 4-horse box chosen (gap < 1σ, per established convention). This is correct, but **future weight tuning should consider whether a `race_confidence` signal belongs in the model** — stdev-based confidence flags could inform bet-sizing or box-width selection algorithmically rather than manually. Consider adding to v0.7+ backlog as an optional output dimension alongside score vectors (e.g., `score_and_confidence()` returning both score and race_confidence enum).

- **Decision:** `.squad/decisions.md` 2026-06-05 entry "Derby trifecta box + stake convention established"; `.squad/orchestration-log/2026-06-05T11-59-04-linus.md`.


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

## 2026-06-07T17:08:33+01:00 — v0.4 Env Validator (Danny, session 7)

**Blocker #2 resolved:** Undocumented credentials + .env exposure risk.

**Audit findings:** Zero `os.environ`/`os.getenv` calls existed anywhere in the codebase.
Sporting Life auth was entirely absent (hence the 373-byte SPA shell on Derby Day).
ATR cookie path was hardcoded in every probe script.

**Learnings:**
- When a scraper fails silently with a tiny response body, the first suspect is missing auth — not code logic.
- Required env vars must be validated at process start, not discovered mid-scrape.
- An `.env.example` with placeholder format `<…>` is the minimum viable credential contract for a shared toolkit.
- `check_env.py` as single source of truth means README, entry points, and tests all derive from the same dict — no drift.
- `_is_placeholder()` must check both exact match AND `<…>` pattern, because a stranger might copy the example and type their own token in `<>` style.

**Deliverables shipped:**
- `.env.example` — 4 vars, 3 credential families, placeholder-only
- `scripts/check_env.py` — startup validator (exit 0/1)
- `scripts/refresh_friday.py` — `_gate_env()` wired at top
- `scripts/morning_odds.py` — `_gate_env()` wired at top
- `scripts/playwright_atr_scraper.py` — loud-fail if cookie file missing
- `README.md` — created (first time), includes Credentials section
- `tests/test_check_env.py` — 14 tests, all passing
- `.squad/decisions/inbox/danny-v04-env-example-and-validator.md`

**Test run:** 14/14 passed. `check_env.py` correctly exits 1 naming both missing SPORTINGLIFE vars against Steve's current env.

---


## 2026-06-08 — Cross-Agent Update (v0.4 wave-1 GREEN)

Wave-1 publish-readiness sprint shipped GREEN. All four work items GREEN GO. Full suite 448/448 PASS (minus pre-existing wave33 — confirmed pre-existing, not a wave-1 regression).

- **Rusty-7**: src/market_drift.py shipped (46/46) — gate-only modifier, weight 0.0, Lord Melbourne +53.8 percent earning event.
- **Linus-14**: render_header() JSON-driven refactor (22/22) — eliminates recurring pound-total mismatch publish blocker (Saul's Derby Day audit #3).
- **Danny-2**: .env.example + scripts/check_env.py validator (14/14) — Sporting Life creds fail-loud at startup, wired into refresh_friday.py + morning_odds.py.
- **Livingston-5**: RUNBOOK.md (565 lines) — two-source scrape pattern + manual fallback codified.
- **Saul-2** crashed mid-run 2026-06-07 ~19:11 BST (CAPI error after 1h41m, no output written). **Saul-3** re-attempt succeeded 2026-06-08 08:40 with crash-resilience protocol (incremental note-writing).
- Next-sprint open items: fix test_racecard_wave33 fixture (Saul); update morning_odds.py RACECARD_FILES for Royal Ascot 2026-06-16 (Danny); sanitise market_drift.py docstring of Derby Day examples (low-priority backlog); pre-sprint Derby Day orphan files need separate close-out commit (Coordinator).
