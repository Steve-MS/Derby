# Decisions

Append-only ledger of team decisions. Scribe merges entries from `decisions/inbox/`.

---

### 2026-06-03: Team hired
**By:** Steve (via Copilot)
**What:** Cast a 5-agent crew (Danny, Livingston, Rusty, Linus, Saul) + Scribe + Ralph to take over race-analysis work for Epsom Derby weekend.
**Why:** Project had grown to 227 tests, v0.3 scoring weights, and a backlog of 5 new signals to ship before Saturday 6 Jun 2026. Squad enables parallel work and decision memory across sessions.

### 2026-06-03: Existing model state at squad hire (v0.3)
**By:** Steve (via Copilot)
**What:** Scoring weights sum to 1.0 with these contributions: class_rating 0.2568, recent_form 0.1468, trainer_form 0.0733, jockey 0.0733, course_distance 0.0733, going 0.0367, draw_bias 0.0571, class_move 0.0367, going_fit 0.1295, pace 0.0665, sire_stamina 0.0500. All 227 tests passing. Last shipped commit: 5a1770e (factors 3 & 4 — C&D form badges + sire stamina).
**Why:** Day-1 baseline for new agents — they need to know what's already in the model before adding signals.

### 2026-06-03: Anti-fabrication rule for new signals
**By:** Steve (via Copilot)
**What:** Any new signal must return a neutral value (50) when data is missing or unknown — never invent data to fill gaps. Sire stamina established the pattern: gated to 10f+, unknown horse → 50, unknown sire → 50.
**Why:** Steve's bets are real money. Fabricated data → bad predictions → losing money. Neutral 50 lets the signal sit quiet when it has nothing to say.

### 2026-06-03: Backlog — 5 signals to ship before Saturday
**By:** Steve (via Copilot)
**What:** Priority order: (1) Trial form (Dante/Chester Vase/Musidora/Cheshire Oaks results), (2) Market move signal (Saturday morning odds-refresh diff), (3) Trainer 14-day strike rate, (4) Jockey/trainer combo bonus, (5) Equipment changes & wind ops from RP notes.
**Why:** Trial form is the single highest-leverage Derby signal — winners of the Dante/Chester Vase have a documented edge. Market moves protect against backing a drifter. Others are incremental.

---

## 2026-06-03 — trial_form signal v0.4 shipped
**Crew:** Danny (Design), Livingston (Data), Saul (Tests & Review), Rusty (Implementation)  
**Verdict:** ✅ APPROVED — ready for Epsom weekend

### Open Questions Resolved
1. **Derby vs Oaks:** Single signal covers both — gender-neutral trial taxonomy. Item's Musidora win counts toward Derby entry.
2. **Lingfield Polytrack:** No surface discount in v1. Tier 2 assignment (not downgraded to Tier 3).
3. **Irish/French trials:** Tetrarch (Curragh, listed, Tier 3) in scope; no French trials (scope creep risk).
4. **Weight 0.08 vs 0.06:** Approved 0.08 (not conservative retreat to 0.06).

### Design → Data → Tests → Implementation → Review Pipeline
- **Danny's spec** (221s) → Tier 1/2/3 taxonomy, scoring formula (position base + tier compression + freshness), weight 0.0800.
- **Livingston's data** (770s) → 25/276 horses with verified trials sourced from Racing Post. Dante, Chester Vase, Musidora, Cheshire Oaks, Lingfield trials, Leopardstown, 1000 Guineas, Irish 1000 Guineas, Newmarket Stakes, Blue Riband.
- **Saul's tests** (147s draft + 291s review) → 19 test cases, all pass. Full 246-test suite green.
- **Rusty's code** (519s) → `src/trial_form.py` module + `src/scoring.py` v0.4 integration. API: `load_trial_data()`, `score_trial_run()`, `best_trial_score()`, `trial_form_signal()`, `_clear_caches()`.

### Data Coverage
- **Total runners:** 276 (Derby + Oaks)
- **With verified trial:** 25 (Dante winner Item, Action 2nd, Christmas Day 3rd, Benvenuto Cellini Chester Vase winner, etc.)
- **No trial found:** 251 (return neutral 50)
- **Flagged:** Causeway (withdrawal status unconfirmed — BHA verification pending; signal returns 50 regardless)

### Weight Rebalance (v0.3 → v0.4)
- All existing weights × 0.92 + trial_form 0.0800
- Verification: (1.0000 − 0.0800) / 1.0000 = 0.9200; 0.9200 × 1.0000 + 0.0800 = 1.0000 ✓
- Example: class_rating 0.2568 → 0.2363; recent_form 0.1468 → 0.1351; sire_stamina 0.0500 → 0.0460

### Scoring Formula (Danny §4, verified by Saul)
- **Position base:** 1st=90, 2nd narrow=78, 2nd 0.5–2L=70, 2nd >2L=62, 3rd ≤2L=60, 3rd >2L=52, 4th=44, 5th+=35
- **Tier compression:** TIER_FACTORS {1: 1.00, 2: 0.75, 3: 0.55} → `50 + (base-50) × factor`
- **Freshness:** ≤28d=0, 29-42d=−2, 43-56d=−4, >56d=−7 (flat steps, not exponential)
- **Clamp:** [0, 100]
- **Worked examples:** Dante winner 21d → 90; Lingfield 2nd 1L → 65; Tier 3 5th → 42

### Anti-Fabrication Invariants (All Hold)
- Neutral 50 when: race < 10f, horse missing, empty trial_runs, malformed data
- beaten_lengths 0.0 for winner; abs(value) for placed; None for 2nd+ → 50
- Case-insensitive lookup
- Multi-trial: best result (max), not average

### Test Results
- **19/19 trial_form tests:** PASS
- **246/246 full suite:** PASS
- **Weight sum:** 1.0000 exactly (verified by Python interpreter)

### Files Shipped
- **NEW:** `src/trial_form.py`, `tests/test_trial_form.py`, `data/enrichment/trial-form.json`
- **MODIFIED:** `src/scoring.py` (v0.4: step 12 added, weights rebalanced, docstring updated)
- **Orchestration log:** `.squad/orchestration-log/2026-06-03-trial-form.md`

### Causeway Note
Causeway entry includes `"trials": []` + `"_review_flag"` (withdrawal unconfirmed). Signal returns neutral 50 regardless of withdrawal status — no special handling required. Flag is for human audit trail only.

---

## 2026-06-03 — Morning Odds Patch & Archive Mode

**Agent:** Livingston (Data Sourcer & Ops)  
**Date:** 2026-06-03T14:55+01:00  
**Status:** ✅ Shipped

Small ergonomic patch to the market-odds script. The original `saturday_morning_odds.py` is misnamed (it covers BOTH Ladies Day Fri 2026-06-05 AND Derby Day Sat 2026-06-06). Renamed to `morning_odds.py` with new `--archive` mode.

**Changes:**
- Script rename: `scripts/saturday_morning_odds.py` → `scripts/morning_odds.py`
- Added `--archive` mode to snapshot market files between race days
- Updated docstring + operator runbook for both-days workflow
- Archive function: idempotent, creates `data/enrichment/archive/` on demand

**Operator Runbook:**
- FRIDAY: 07:00 baseline → ~1hr before each Group 1 latest → ~21:00 archive
- SATURDAY: 07:00 baseline (reset) → ~1hr before each Group 1 latest → ~21:00 archive

**Schema preservation:** No changes to `market-baseline.json` + `market-latest.json` schema.

---

## 2026-06-03 — Equipment Signal Design (v0.6)

**Agent:** Danny (Architect & Lead)  
**Date:** 2026-06-03T14:50:08+01:00  
**Target:** v0.6 (equipment only; wind ops dropped — paywalled per Livingston)

Equipment changes are a low-noise proxy for trainer intent at race day.

**Signal Mechanics:**
- Base score = 50
- First-time-use bonuses: blinkers +8, cheekpieces +7, tongue-tie +6, visor +5, hood +3, eyeshield/paddings +2
- Stacking penalty: −3 per extra item beyond first
- Equipment removal bonus: +3 per item removed (trainer confident)
- Clamp [10, 90]

**Schema (data/enrichment/equipment.json):**
- `equipment` — all equipment worn today (full list)
- `first_time_use` — items never worn before by this horse
- `changed_vs_last_run` — items added or removed vs previous race

**Weight & Rebalance — v0.5 → v0.6:**
- Equipment weight: **0.0250** (2.5%)
- All 15 v0.5 weights × 0.9750; residual absorbed by `class_rating`
- Verification: sum = 1.0000 ✓

**Open questions for Steve:** (1) Stacking penalty — apply or not? (2) Equipment removal direction — +3 or neutral? (3) `first_time_use` vs `changed_vs_last_run` reliability from RP? (4) Derby only or both races?

---

## 2026-06-03 — Friday Oaks 48hr Declarations & Drift Check

**Agent:** Livingston (Data Sourcer)  
**Date:** 2026-06-03T15:37:52+01:00  
**Status:** ✅ Declarations LIVE

48-hour declarations for Friday 2026-06-05 published and live (Wed 14:00 BST).

**Standing Stakes:**
- **Belinus** (WIN £5 @ 3.5): 🚨 **WITHDRAWN or CANCELLED** — NOT in racecard. Verify status with bookmaker; request refund.
- **Sugar Island** (EW £0.25 @ 34.0): ✅ Stable, no drift.

**Oaks field (11 runners):** Amelia Earhart 3.5, Precise 5.0, Legacy Link 6.0, Venetian Lace 11.0, Cameo 15.0, A La Prochaine 17.0, Thundering On 21.0, K Sarra 26.0, Prizeland 34.0, Sugar Island 34.0, Beautify 101.0

**Drift analysis:** No horses flagged >20% drift. Belinus missing is data integrity issue, not price movement.

---

## 2026-06-03 — v0.5 Implementation (3 new signals)

**Agent:** Rusty (Signal Engineer)  
**Date:** 2026-06-03  
**Status:** Complete — awaiting review

Three new signal modules added:
- `src/market_move.py` (~210 LOC) — Implied-probability shift from 2-file market data
- `src/trainer_14d.py` (~165 LOC) — Trainer 14-day hot/cold form
- `src/jt_combo.py` (~185 LOC) — Jockey/trainer combo interaction term

**Test result:** 246/246 passing (all pre-existing tests green). Saul's new test files (58 tests) pending merge.

**Key deviations from Danny's spec:**
- **market_move:** 2-file schema (not single `market-move.json`)
  - `data/enrichment/market-baseline.json` — 272 horses
  - `data/enrichment/market-latest.json` — empty stub (populated on race day)
  - Returns 50 when latest is empty (pre-race-day, correct)
- **jt_combo:** horse-keyed lookup (not combo-key construction)
- **trainer_14d:** strike_rate always recomputed from `wins_14d / runners_14d`

**v0.5 weight table (15 signals, sum = 1.0000):**
- class_rating 0.2031, recent_form 0.1162, going_fit 0.1024, market_move 0.0700, trial_form 0.0688, trainer_form 0.0580, jockey 0.0580, course_distance 0.0580, pace 0.0526, draw_bias 0.0451, trainer_14d 0.0400, sire_stamina 0.0396, jt_combo 0.0300, going 0.0291, class_move 0.0291

---

## 2026-06-03 — Equipment Data — Epsom 2026-06-05/06

**Agent:** Livingston (Data Sourcer)  
**Date:** 2026-06-03  
**Status:** ✅ Shipped

Equipment enrichment delivered. 30 / 272 runners confirmed wearing headgear (11%). 31 horses not matched on RP; all get `equipment: []` per anti-fab rule.

**Data Sources:**
- openhorsedata.com CSV — ❌ DNS unreachable
- Racing Post `__NEXT_DATA__` SSR — ✅ Primary source (107 + 138 = 245 runners matched)
- Wind surgery — ⚠️ Present but null on free racecard (paywalled)

**Coverage:**
- Matched on RP: 241 / 272 (88.6%)
- With at least one equipment code: 30 (11.0%)
- First-time-use flags: 9 horses

**Equipment distribution:** tongue-tie 13, cheekpieces 11, hood 6, blinkers 3, visor 2

**Note:** `changed_vs_last_run` always empty — cannot determine without prior-run history (paywalled on RP).

---

## 2026-06-03 — v0.5 Signal Batch Tests

**Agent:** Saul (Reviewer & Test Lead)  
**Date:** 2026-06-03  
**Status:** ✅ All passing

Three new pytest test files:
- `tests/test_market_move.py` — 21 tests ✅ passing
- `tests/test_trainer_14d.py` — 18 tests ✅ passing
- `tests/test_jt_combo.py` — 19 tests ✅ passing
- **Total:** 58 tests, all passing
- Full suite: 77 collected (includes 21 pre-existing)

**API corrections:** All three files fully rewritten against Rusty's actual implementation (not initial spec).

**Non-blocking design TODOs for Danny:**
1. `score_market_move(0.024)`: Danny's spec says ~62; Rusty's formula gives ~65.5. Using `abs=5.0` tolerance.
2. `score_trainer_14d(0.10)`: Danny says ~48; formula gives 50.0. Using `abs=1.0` tolerance.
3. `first_time_pairing=True` with `combo_runners > 0`: spec only covers zero-history case; Rusty ignores flag when history exists.

---

## 2026-06-03 — v0.5 Source Review (REJECTED)

**Agent:** Saul (Tester / Reviewer)  
**Date:** 2026-06-03  
**Requested by:** Steve  
**Verdict:** ❌ REJECT

Blocking issue: All three new modules (`market_move`, `trainer_14d`, `jt_combo`) raise `AttributeError` when `runner is None`, violating the anti-fabrication gate. Must return neutral 50 on None inputs.

**Blocking details:**
- `market_move_signal(None, {})` → AttributeError
- `trainer_14d_signal(None, {})` → AttributeError
- `jt_combo_signal(None, {})` → AttributeError

**Reviewer lockout:** Rusty authored v0.5 and may not revise. Reassigned to Linus for narrow hardening patch.

**Other validations (all PASS):**
- Weights sum: 1.0000000000 ✓
- Score bounds: market_move [10,90], trainer_14d [15,90], jt_combo [15,90] ✓
- Integration: all imports + weights + calls correct ✓
- No regressions: only version/imports/weights/three-signal-calls changed ✓
- Schema fidelity: market_move handles 2-file schema correctly ✓
- Test result: 323/323 passing ✓

---

## 2026-06-03 — v0.5 Spec Addendum (3 Clarifications)

**Agent:** Danny (Architect & Lead)  
**Date:** 2026-06-03  
**What:** Resolved three v0.5 spec-vs-implementation mismatches

**Decisions:**
1. **`score_market_move(0.024)` → accept implementation 65.5.** Piecewise curve places +0.024 Δip at 65.5 (not ~62 as earlier example stated).
2. **`score_trainer_14d(0.10)` → accept implementation 50.0.** Design intent: 10–12% UK flat average band sits at neutral; formula already correct.
3. **`first_time_pairing=True` with `combo_runners > 0` → existing combo data wins.** 60-point first-time lean only applies to true zero-history pairings.

**Code-change routing:** No runtime code changes required — all are spec/documentation clarifications. v0.5 can ship as-is.

---

## 2026-06-03 — v0.5 Anti-Fab Hardening (None-guard patch)

**Agent:** Linus (Code Hardener)  
**Date:** 2026-06-03  
**What:** Patched the three v0.5 public signal entry points to return neutral 50.0 for non-dict runners

**Patched files:**
- `src/market_move.py` lines 262-263: market_move_signal returns 50.0 for non-dict runners
- `src/trainer_14d.py` lines 180-181: trainer_14d_signal returns 50.0 for non-dict runners
- `src/jt_combo.py` lines 189-190: jt_combo_signal returns 50.0 for non-dict runners

**Tests added:**
- `tests/test_market_move.py` lines 206-207: test_market_move_signal_returns_50_when_runner_is_none
- `tests/test_trainer_14d.py` lines 145-146: test_trainer_14d_signal_returns_50_when_runner_is_none
- `tests/test_jt_combo.py` lines 182-183: test_jt_combo_signal_returns_50_when_runner_is_none

**Validation:** `pytest -x` — 326 collected, 326 passed in 8.02s. Cleared for re-review.

---

## 2026-06-03 — v0.5 Re-review R2 (APPROVED)

**Agent:** Saul (Tester / Reviewer)  
**Date:** 2026-06-03  
**Requested by:** Steve  
**Verdict:** ✅ APPROVE

Narrow re-review: Linus's hardening patch resolves the prior blocker.

**Guard Status:**
| Module | Guard | Regression test | Behaviour |
|---|---|---|---|
| `market_move` | PRESENT — returns 50.0 when runner is not dict | PRESENT | CORRECT — smoke test 50.0 |
| `trainer_14d` | PRESENT — returns 50.0 when runner is not dict | PRESENT | CORRECT — smoke test 50.0 |
| `jt_combo` | PRESENT — returns 50.0 when runner is not dict | PRESENT | CORRECT — smoke test 50.0 |

**Validation:** `pytest -x` — 326 collected, 326 passed in 8.60s

**Manual smoke:**
```
market_move_signal(None, {}) → 50.0
trainer_14d_signal(None, {}) → 50.0
jt_combo_signal(None, {}) → 50.0
```

**Verdict:** Cleared to ship v0.5 to main.
