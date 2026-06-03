# Orchestration Log: trial_form Signal Ship (2026-06-03)

**Scribe:** Committed by Copilot (Historian & Janitor)  
**Date:** 2026-06-03  
**Outcome:** ✅ Shipped v0.4 (trial_form weight 0.0800)

---

## Spawn Sequence & Timings

### 1. Danny (Design Lead) — 221s
- **Task:** Write design spec for trial_form signal (§1–8).
- **Deliverable:** `danny-trial-form-design.md` — Trial taxonomy (Tier 1/2/3), scoring formula (position base scores + tier compression + freshness adjustment), weight allocation (0.0800), hand-off API.
- **Open questions:** Derby vs Oaks split, Lingfield Polytrack caveat, Irish/French trials scope, weight 0.08 vs 0.06.
- **Duration:** 221s

### 2. Livingston (Data Engineer) — 770s
- **Task:** Populate `data/enrichment/trial-form.json` — source trial runs for all Derby/Oaks runners from Racing Post and allied sources.
- **Deliverable:** 276 horses (both days); 25 with verified trials; 251 with empty trial_runs []. Covered 12 canonical races (Dante, Chester Vase, Musidora, Cheshire Oaks, Lingfield trials, etc.).
- **Flagged:** Causeway (withdrawal status unconfirmed — BHA verification pending).
- **Duration:** 770s

### 3. Saul (Tester) — 147s
- **Task:** Draft 19 test cases for `src/trial_form.py` before module exists.
- **Deliverable:** `tests/test_trial_form.py` — 5 test groups (happy path, anti-fabrication, distance gating, edge cases, bounds). Made 8 assumptions documented in the note.
- **Duration:** 147s

### 4. Rusty (Signal Engineer) — 519s
- **Task:** Implement `src/trial_form.py` + integrate into `src/scoring.py` v0.4.
- **Deliverable:** 
  - `src/trial_form.py` — API: `load_trial_data()`, `score_trial_run()`, `best_trial_score()`, `trial_form_signal()`, `_clear_caches()`.
  - `src/scoring.py` — Step 12 added (after sire_stamina), weights rebalanced (all v0.3 × 0.92 + trial_form 0.0800).
  - Reconciled schema differences (Danny `race_name` ↔ Livingston `trial_name`; tier mapping; beaten_lengths normalisation).
- **Duration:** 519s

### 5. Saul (Reviewer) — 291s
- **Task:** Review Rusty's implementation against Danny's spec + validate Livingston's data + green all tests.
- **Deliverable:** `saul-trial-form-review.md` — ✅ APPROVE. 19/19 tests pass. Full 246-test suite green. Weight math verified (1.0000 exactly). All worked examples match spec. Anti-fabrication invariants hold.
- **Duration:** 291s

---

## Total Elapsed Time

- **Spawn-to-review:** 221 + 770 + 147 + 519 + 291 = **1948s ≈ 32.5 minutes**
- **Parallel phases:** Danny (221s) → Livingston (770s parallel to Danny tail) → Saul test draft (147s parallel) → Rusty impl (519s) → Saul review (291s)

---

## Decisions Ratified by Steve

1. **Weight:** 0.0800 (Danny Q4 resolved — no 0.06 conservative retreat).
2. **Derby vs Oaks:** Single signal fires on both — gender-neutral trial taxonomy (Danny Q1 resolved).
3. **Lingfield Polytrack:** No discount in v1 (Danny Q2 resolved).
4. **Irish trials:** Tetrarch (Curragh, Tier 3) included; no French trials in v1 scope (Danny Q3 resolved).
5. **Leopardstown Derby Trial:** Tier 2 assignment approved.
6. **Causeway:** Flagged for BHA withdrawal verification; signal gracefully returns 50.0 regardless.

---

## Green-Light Checkpoint

- **Design** → ✅ Signed
- **Data** → ✅ Sourced (25/276 horses with verified trials)
- **Tests** → ✅ 19/19 passing + 246/246 full suite
- **Code** → ✅ All spec requirements met + anti-fabrication invariants held
- **Review** → ✅ APPROVE by Saul
- **Weight math** → ✅ Sum = 1.0000 exactly

**Status:** Ready to commit and push.
