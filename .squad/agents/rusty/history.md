# Rusty — History

## Project context (seeded 2026-06-03)

- Python 3.12 race-analysis toolkit. Repo Steve-MS/Derby, commit 5a1770e.
- Existing signal modules to mirror: `src/cd_form.py`, `src/sires.py`, `src/pace.py`, `src/going.py`.
- All return 0-100 normalised scores; missing data → 50.
- Sire stamina sets the gating pattern: only fires at 10f+ races.
- 227 tests passing — each new signal expected to add ~18-22 tests.
- Backlog: trial-form (first), market-move, trainer-strike, jt-combo, equipment.

## 2026-06-04 — trial_form signal

Implemented `src/trial_form.py` and updated `src/scoring.py` to v0.4.

**Outcome:** 246/246 tests passing (19 new from Saul's suite).

**Key calls made:**
- Normalised Livingston's signed `beaten_lengths` convention on JSON load (negative winner margin → 0.0 for pos=1, abs() for pos>1).
- Added walkover cap (field_size==1 → max 70.0) to pass `test_single_runner_field_no_overcredit`.
- Reconciled Danny's spec API with Saul's test API — both sets of function names implemented.
- `race_date` defaults to `"2026-06-06"` (Derby day) so Saul's 3-arg `score_trial_form` calls work.
- Tier 3 default for unlisted trial names; Leopardstown Derby Trial → Tier 2 per Steve Q3.
- All v0.3 weights × 0.92; trial_form = 0.0800; sum = 1.0000.

**Decision note:** `.squad/decisions/inbox/rusty-trial-form-implementation.md`

## 2026-06-03 — v0.5: market_move, trainer_14d, jt_combo signals

Implemented three new signal modules and updated `src/scoring.py` to v0.5.

**Outcome:** 246/246 tests passing. Saul's new test suites not yet present (in parallel).

**Key calls made:**
- `market_move`: read Livingston's 2-file schema (`market-baseline.json` + `market-latest.json`, each with `decimal_odds`) and combined in-memory — Danny's single-file spec was aspirational. Used Danny's Δip formula (not Livingston's `(b-l)/b` strawman). Empty latest stub → neutral 50 for all runners.
- `trainer_14d`: always recompute `wins_14d/runners_14d` — stored `strike_rate` is display-only.
- `jt_combo`: horse-keyed lookup avoids trainer/jockey name normalisation mismatches.
- All 15 v0.5 weights verified to sum to exactly 1.0000.
- Danny's score-curve anchors verified for all three pure scoring functions.

**Decision note:** `.squad/decisions/inbox/rusty-v05-implementation.md`
