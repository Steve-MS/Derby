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
