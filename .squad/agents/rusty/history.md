## SUMMARY (2026-06-06 Post-Derby)

**Key deliverables:**
- Implemented 4 signal modules: trial_form (v0.4), market_move/trainer_14d/jt_combo (v0.5), equipment (v0.6)
- All test suites passing (352/352 for v0.6)
- market_drift module proposed for v0.4 (0 HIGH, 1 MEDIUM, 8 SPECULATIVE)
- Live-verify-first protocol established for NR replacements (via Livingston's live-runners-YYYY-MM-DD.json)

**Signal deliverables:**
- trial_form (0.0800 weight): Handles beaten_lengths normalization, walkover cap, Tier 3 taxonomy
- market_move (0.0700): Δip scoring; signal inert (0%) due to synthetic prices until live feed
- trainer_14d (0.0400): 28/93 trainers covered; sample guard <5 runners → 50
- jt_combo (0.0300): 5 verified combos; first-time pairings score 60
- equipment (0.0250): 30/272 runners with headgear (11%); stacking penalty applied

**Publish blockers:**
- market_move signal returns neutral (50) for all runners — live price ingestion blocked (RP 406 quirk, Betfair API not implemented)
- Synthetic price tag retained in outputs until live feed available

**Current state:**
- v0.6 weights: all 15 signals scale to exactly 1.0000
- Signal implementation stable and tested
- Live-verify protocol active and preventing stale-runner failures

---


---

# Rusty — History


## Project context (seeded 2026-06-03)

- Python 3.12 race-analysis toolkit. Repo Steve-MS/Derby, commit 5a1770e.
- Existing signal modules to mirror: `src/cd_form.py`, `src/sires.py`, `src/pace.py`, `src/going.py`.
- All return 0-100 normalised scores; missing data → 50.
- Sire stamina sets the gating pattern: only fires at 10f+ races.
- 227 tests passing — each new signal expected to add ~18-22 tests.
- Backlog: trial-form (first), market-move, trainer-strike, jt-combo, equipment.


## Archive — pre-Derby learnings (2026-06-03 → 2026-06-05)

Detailed entries compressed by Scribe-19 on 2026-06-08 (file exceeded 15KB). Full history in git pre-2026-06-08.

- **2026-06-04**: Implemented `src/trial_form.py` + scoring.py v0.4 (weight 0.0800, 19 tests, 246/246 suite green)
- **2026-06-03 v0.5**: Shipped market_move, trainer_14d, jt_combo signals (combined weight 0.1400). Used Danny's Δip formula, horse-keyed jt_combo lookup. 246/246 tests.
- **2026-06-03 v0.6**: Shipped equipment signal (weight 0.0250). Score curve: base 50 + first-time deltas + stacking penalties, clamp [10,90]. 352/352 tests.
- **2026-06-05 Ladies Day NR cascade**: TWO replacement failures using stale data — Triple Double A (16:40 HKJC), Blue Brother (17:50 Debenhams) both not in live declared fields. v2 picks (Asmen Warrior, Arctic Thunder) sourced via Sporting Life live racecard. Hard rule: live-verify-first for ALL NR replacements.
- **2026-06-05 midday**: Synthetic-price tag retained — RP scrape bypasses JS-rendered odds; market_move returns neutral 50 until live ingestion. Sugar Island drift detected manually (33/1 → 16-22/1) but signal cannot see it.

## 2026-06-08 — Cross-Agent Update (v0.4 wave-1 GREEN)

Wave-1 publish-readiness sprint shipped GREEN. Saul-3 gate review verdict 🟢 GO for all four items:
- **Rusty-7** (you): market_drift.py shipped (this entry below)
- **Linus-14**: render_header() JSON-driven refactor — header staleness eliminated. `render_card(bets_json_path=…)` now triggers automatic header recomputation. Your future signal-injection work no longer needs to coordinate manual header patches with Linus.
- **Danny-2**: `.env.example` + `scripts/check_env.py` validator wired into `refresh_friday.py` + `morning_odds.py`. Sporting Life credentials now fail-loud at startup.
- **Livingston-5**: `RUNBOOK.md` (565 lines) — encodes two-source scrape pattern + manual live-odds fallback. Reference for race-day operator procedures.
- Pre-existing `test_racecard_wave33` failure confirmed NOT a wave-1 regression (Saul provided git evidence). Next-sprint fix: update test fixture to pass bets_json_path with scenario field.

Royal Ascot 2026-06-16 live-test approaching. `morning_odds.py` `RACECARD_FILES` still hardcoded for Epsom dates — Danny owns the update.

---

## 2026-06-06 — Derby Day HOLD Card Rescore (rusty-rescored-2026-06-06.json)

**Trigger:** Steve requested full Saturday rescore from Livingston's 11:26 BST refresh (100 active runners, RP forecast odds, GTS confirmed going).

**Key outputs:**
- **7 WIN candidates across 8 races** (13:30 and 14:40 NO_BET; 17:55 VOID)
- **2 EW outsider candidates:** Prydwen 17/1 (17:20), Ziggy's Triton 32/1 (15:15 — COMPRESSED_RANGE_CAUTION)
- **2 Linus-v1 picks invalidated:** Illinois (14:40, model rank 6/6, NO_OVERRIDE) and Christmas Day (16:00, rank_gap +0.5 < +2)

**Critical findings:**
1. Benvenuto Cellini (Derby): 9/4 → Evs = only genuine steam signal (38.5% from real ante-post baseline). MARKET_STEAM_MAJOR + EDGE_ERODED.
2. Lord Melbourne (17:20): model rank 1/17, rank_gap +13, going_fit 78. Strongest overlay signal on card. Upgraded from bets-file EW outsider to WIN candidate.
3. GTS going REJECT flags: Ancient Egypt, Balzac, A Taste Of Glory, Poker (all good-to-firm specialists in 16:00 Derby). HOLD card confirmed correct.
4. 15:15 Dash scoring caveat: RPM field range = only 5 points (102–107). Compressed range amplifies tiny differences into large rank gaps. Both 15:15 picks (Another Baar 39/1, Ziggy's Triton 32/1) flagged COMPRESSED_RANGE_CAUTION.
5. Synthetic baseline caveat: For 6/8 races, baseline prices were synthetic (not real). EDGE_ERODED flags in those races reflect price revelation, not genuine steam. Only Benvenuto Cellini and Coronation Cup runners had real ante-post baselines.

**Scoring methodology established for future reference:**
- composite = RPM×0.45 + OR×0.30 + TS×0.25, normalised 5-95 within active field
- final_signal adjustments: headgear×0.90 (fields ≥14), EDGE_ERODED×0.85 (steam≥30% + market_rank≤3)
- going_fit <40 → REJECT; model_score <50 → NO_OVERRIDE flag
- LATE_ENTRY_NEUTRAL = 50 for runners not in score DB (Star Chorus, Stormy Impact in 15:15)

**Files written:**
- `data/enrichment/rusty-rescored-2026-06-06.json` (full ranked tables + per-race recommendations)
- `.squad/decisions/inbox/rusty-sat-rescore-2026-06-06.md` (decision summary)

## Learnings

### 2026-06-06 — Synthetic Baseline Steam Problem

**Pattern observed:** When the market-baseline.json contains synthetic prices (OR/field-size estimates) and market-latest.json contains real traded/forecast prices, ALL horses in synthetic-base races will show high steam_drift_pct values — even horses that have actually DRIFTED vs real traded prices. This renders the EDGE_ERODED steam filter largely useless for synthetic-base races. 

**Key finding:** In a 20-runner handicap with synthetic baseline ~25/1 across the board, the top-3 market prices (real 5/1, 6/1, 7/1) will all show 60-80% "steam" and all get EDGE_ERODED flagged — eliminating the three most likely winners from the WIN candidates list.

**Mitigation applied:** Added SYNTHETIC_BASE_CAVEAT flag to differentiate synthetic→real transitions from genuine steam. Only Benvenuto Cellini (real 9/4 baseline → real Evs) and Calandagan (real 6/4 baseline → real -1/11) carry genuine steam signals.

**Recommendation for next race day:** Livingston should flag `baseline_price_type: "synthetic" | "ante_post" | "traded"` in market-baseline.json for each horse. This would allow the market_move signal and EDGE_ERODED rule to distinguish price discovery from genuine confidence moves automatically, without manual caveats.

### 2026-06-06 — Compressed-Range Handicap Scoring Anomaly

**Pattern:** In big handicap fields with very narrow RPM ranges (e.g., 15:15 Dash: 102–107, range = 5), the 5-95 normalisation amplifies small absolute differences into large perceived gaps. A horse with RPM 107 scores 95.0 while one with RPM 106 scores 77.0 — only 1 point of actual difference.

**Effect:** In the 15:15 Dash, the model top-picks (Ziggy's Triton 95.0, King Of Light 88.6) had OR and TS ratings that also happened to be high, compounding the effect. The market (which uses many more signals) priced them at 33/1 and 13/1 respectively. The 33/1 vs model rank 1 gap looks like a massive overlay but is mostly a normalisation artefact.

**Lesson:** For handicaps with field RPM range ≤8 points, add a COMPRESSED_RANGE_CAUTION flag and reduce confidence in WIN candidate designation. Rank gaps >10 in these races should be treated as speculative outsider signals only, not model-grade WIN picks.

**Future signal improvement:** Consider using raw RPM percentile rank within a broader population (e.g., all handicappers rated 83-99 in the current season) rather than within-field normalisation for compressed-range handicaps.


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

## 2026-06-07T17:08:33+01:00 — v0.4 market_drift module shipped

**Deliverables:** `src/market_drift.py` + `tests/test_market_drift.py`

**Outcome:** 46/46 tests passing. scoring.py weights untouched (sum remains 1.0000).

**Key calls made:**

- Gate-only design (weight = 0.0): multiplies `final_signal` and emits flags; does not add to model_score. Preserves Danny's gate-beats-averaging principle.
- Pure public API: `parse_fractional_odds`, `assess_market_drift`, `load_market_drift_data`, `market_drift_signal` — all independently testable.
- Preferred fractional string parsing over stored decimal_odds. Reason: Derby Day data artefact — Lord Melbourne `decimal_odds: 13.5` vs `fractional_odds: "12/1"` (= 13.0). Using decimal would give 48.1% drift (misses ≥50 gate); fractional gives 53.8% (correct DRIFT_CRITICAL). Fractional preferred, decimal as fallback.
- Threshold semantics confirmed: ≥ 30 fires (not >30); ≥ 50 fires DRIFT_CRITICAL and takes precedence over DRIFT_WARN. All four boundaries covered in tests.
- Portability maintained: zero hardcoded horse names, course names, dates.

**Decision note:** `.squad/decisions/inbox/rusty-v04-market-drift-shipped.md`

---

## Learnings

### 2026-06-07 — Synthetic-Price Decimal vs Fractional Artefact

**Pattern confirmed:** When Livingston builds market-baseline.json from synthetic OR/field-size estimates, the `decimal_odds` field may not match the `fractional_odds` string. Observed: Lord Melbourne `decimal_odds: 13.5`, `fractional_odds: "12/1"` (= 13.0). The 0.5-point discrepancy is enough to move the drift calculation from 48.1% (misses DRIFT_CRITICAL at ≥50) to 53.8% (correctly triggers DRIFT_CRITICAL).

**Rule for all future market-parsing modules:** Prefer fractional string parsing when available. Fall back to decimal_odds. Do not assume decimal_odds is authoritative when fractional string is present.

**Why this matters operationally:** The whole point of the drift gate is to penalise significant market-against moves. Lord Melbourne drifting to 19/1 from a 12/1 baseline is a 53.8% move — exactly the profile the gate was designed to flag. An off-by-half-point baseline from a synthetic price should not silently drop the signal below the DRIFT_CRITICAL threshold.

## 2026-06-08 — Chunk 4 Course Priors Extraction

**Deliverables:** extracted scoring priors into `config/courses/epsom.json`, added neutral Ascot priors, and refactored pace/draw, C/D form, trial form, and scoring integration to read course config.

**Regression:** pre-edit Epsom 2026-06-06 baseline saved at `tests/fixtures/regression/chunk4-epsom-2026-06-06-baseline.json`; post-edit byte compare returned `REGRESSION_DIFF=EMPTY` across 8 races / 149 runners.

**Tests:** `python -m pytest -x --ignore=tests/test_racecard_wave33.py` -> 484 passed.

**Learning:** keep old two-arg signal monkeypatch compatibility when adding course/prior keyword parameters; `score_runner` now uses a small compatibility shim for C/D and trial signals.

**Learning:** known-course missing `scoring_priors` should be neutral, not Epsom fallback. Unknown course remains loud via `CourseConfigError`.
