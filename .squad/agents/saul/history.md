# Saul — History

## Project context (seeded 2026-06-03)

- Python 3.12 race-analysis toolkit. Repo Steve-MS/Derby, commit 5a1770e.
- 227 pytest tests currently passing.
- Test pattern: each signal module has its own `tests/test_<signal>.py` with 18-22 tests.
- Reviewer authority on all scoring/signal/betting PRs.
- Key validation milestone: once Ladies Day (Fri 5 Jun) is run, backtest the model's Friday predictions against actual results before Derby Day picks are finalised.
- Boundary cases to always test: missing data → neutral 50, scratched horses, single-runner edge case.

## Review Log

### 2026-06-04 — trial_form signal (Rusty)
- **Verdict: APPROVE**
- 19/19 test_trial_form.py, 246/246 full suite.
- Formula matches Danny's spec exactly (all 3 worked examples verified to the decimal).
- Weight math: 11 × 0.92 + 0.0800 = 1.0000 confirmed by Python.
- Causeway → 50 (empty trials, review flag safely ignored).
- No test assertion gaming detected.
- Noted issues (none blocking): (1) Rusty's decision note incorrectly describes freshness as `exp(-days/365)` — code is correct step-function; (2) `load_trial_data()` return type diverges from Danny's spec signature (nested dict vs list) — self-consistent; (3) No `_clear_caches` test — Saul's own omission.

### 2026-06-05 — v0.5 signal batch tests (market_move, trainer_14d, jt_combo)
- **77/77 tests passing.** 58 new tests written across 3 files.
- Initial stubs assumed wrong API (pre-implementation). All three files fully
  rewritten against Rusty's actual signatures once implementation was discovered.
- Monkeypatch pattern: `monkeypatch.setattr(module, "load_X", lambda: data)`.
- **API confirmed:** pure scorers take sr/delta directly (not wins/runners);
  signals read from cached loader (no `data` param).
- **3 TODOs flagged for Danny:** market_move 0.024 anchor (~62 vs 65.5);
  trainer_14d 0.10 anchor (~48 vs 50); first_time_pairing+runners>0 behaviour.
- **Notable divergences from spec:** jt_combo is horse-keyed not combo-keyed;
  trainer_14d defaults missing wins_14d to 0 (→ floor 15); no case normalisation
  in any of the three modules (correct — Livingston's responsibility).
- Full detail: `.squad/decisions/inbox/saul-v05-tests.md`

### 2026-06-06 — hand-edit on Derby card + render_trifecta_box() helper (Linus)

**Flag:** Linus hand-edited `outputs/racecard-2026-06-06.html` to insert trifecta box (not generator-based). Also added `render_trifecta_box(trifecta: dict)` helper to `src/report.py`. This hybrid route requires test coverage before next race-weekend cycle: (1) unit test for render_trifecta_box() function, (2) integration test for HTML structure (purple box, 4 horses, going contingency, stale-odds caveat). Before Royal Ascot, promote helper into template pipeline + full test suite.

### 2026-06-03 — v0.5 source review gate (Rusty)
- **Verdict: REJECT** — strict reviewer lockout applies; Rusty cannot revise this artifact.
- Weights sum PASS: 1.0000000000 exactly.
- Integration PASS: scoring.py imports/calls `market_move`, `trainer_14d`, `jt_combo` and uses v0.5 weights.
- Schema fidelity PASS: `market_move` uses Livingston's two-file baseline/latest schema.
- Score bounds PASS for all three new signals.
- Tests PASS: `pytest -x` collected 323 items, 323 passed in 8.26s.
- Blocking issue: all three new public signal functions raise `AttributeError` for `runner=None`; anti-fab gate requires neutral 50 for None inputs.
- Recommended reassignment: Linus, narrow hardening patch + one None-input test per module; Rusty locked out for this revision cycle.

### 2026-06-03 — v0.5 re-review R2 after Linus hardening
- **Verdict: APPROVE** — prior blocker resolved.
- Guard PRESENT in `market_move_signal`, `trainer_14d_signal`, and `jt_combo_signal`: non-dict/None runner returns 50.0 before field access.
- Regression test PRESENT in each owned test file for `runner=None` returning 50.0.
- Manual smoke CORRECT: all three `signal(None, {})` calls returned 50.0, no exception.
- Validation: `pytest -x` collected 326 items, 326 passed in 8.60s.
- Cleared to ship v0.5 to main.
### 2026-06-03 — v0.6 equipment signal tests drafted
- Wrote `tests/test_equipment.py` with 19 test functions / 25 pytest cases for Danny's v0.6 equipment contract.
- Scope: real loader, first-time equipment anchors, stacking penalty, removal bonus, clamp [10,90], anti-fab neutral fallbacks, None runner/race handling, bounds/type checks, no state mutation, null wind_surgery, empty changed_vs_last_run, and scoring.py integration weight 0.0250.
- Uses `pytest.importorskip("src.equipment")`; once Rusty's module landed, validation passed: `pytest tests/test_equipment.py -v` → 25 passed.
- Decision note: `.squad/decisions/inbox/saul-v06-equip-tests.md`.

### 2026-06-03 — v0.6 equipment source review gate (Rusty)
- **Verdict: APPROVE** — cleared to ship v0.6 to main.
- Weight sum PASS: 16 signals, total `1.0000000000`; equipment weight `0.0250`.
- Anti-fab PASS: `score_equipment(None, {})`, `score_equipment({}, None)`, and `score_equipment(None, None)` all returned `50.0`.
- Bounds PASS: equipment clamps to [10,90], no NaN in data sweep; real data min/max `47.0/60.0`.
- Integration PASS: scoring imports/calls equipment and includes it in weighted sum.
- Rebalance PASS: non-class v0.5 weights match ×0.9750 rounded; `class_rating` absorbs the residual.
- Validation PASS: `pytest -x` collected 352 items, 352 passed in 7.97s; equipment tests had 25 pass / 0 skips; smoke returned `50.0`.
- Data caveat: `changed_vs_last_run` empty across 272; wind_surgery is ignored safely. Audit found two numeric wind_surgery entries despite source note saying null, but this is non-blocking because wind ops are out of v0.6 scope.
- Decision note: `.squad/decisions/inbox/saul-v06-equip-review.md`.

### 2026-06-05 12:59 — Derby trifecta-box hand assembly (Linus, heads-up for future helper)

**Note:** Linus delivered a hand-assembled 4-horse trifecta-box recommendation (Item, Benvenuto Cellini, Maltese Cross, Causeway) for Derby. This was first-ever recommendation, built directly from scored data, **not** via a `trifecta_box()` helper in `src/betting.py`. **No test coverage** for this assembly — going contingency rule also hand-documented.

**For future:** When `src/betting.py` gains a `trifecta_box()` helper (v0.7+ backlog), recommend test cases:
- Box size selection (3/4/5 logic based on gap-to-#4, confidence, stdev)
- Stake matrix (£2.50/£1.00/£0.50 per combo)
- Going contingency (drop low-confidence horse if Soft declared)
- Edge case: single-horse removal → rebalance stake/combo
- Output format: ranked horses, combination count, total outlay

**Decision:** `.squad/decisions.md` 2026-06-05 entry "Derby trifecta box + stake convention established".

### 2026-06-05 15:13 — Prizeland NR Replacement (Linus hand-edit + render_replacement_row() flag)

**Flag:** Linus hand-edited `outputs/racecard-2026-06-05.html` to swap Prizeland row (16:00 Oaks, confirmed NR) with Cameo (£0.25 EW @ ~14/1, model #3 vs market #4, trial winner). This is the **second hand-edit in two days** (first: Derby trifecta box 2026-06-05 12:59). Pattern signals **reproducibility problem.**

**Before Royal Ascot:**
- Add `render_replacement_row(original_horse, replacement, bet, rationale, stale_price, conviction) -> str` to `src/report.py` alongside existing `render_trifecta_box()`.
- Wire into template pipeline (`.squad/` + Linus ownership).
- **Test coverage for render_replacement_row():**
  - NR badge rendered in `col-note` with correct amber inline style (background:#fff8dc; border-left:3pt solid #d99400)
  - Stale-odds caveat `<div>` present in `row-rationale`
  - Apostrophe/HTML-entity escaping (esp. trainer names: Aidan O'Brien)
  - Original horse name absent from rendered output
  - Decimal odds and stake × odds return column consistent
  - No regression in other race rows

**Reference:** `.squad/decisions/inbox/linus-prizeland-cameo-swap.md` (merged into decisions.md)

### 2026-06-05 — NR replacement helper (ender_replacement_row()) ELEVATED priority

**Context:** Second NR swap in 90 minutes on Ladies Day (Cameo for Prizeland at 16:00, Triple Double A for Port Road at 16:40). Pattern established. Linus hand-edits both cases with identical DOM structure + CSS styling. Two manual HTML surgeries on one race day = expected load for Group 1 / big-field cards.

**Flag:** ender_replacement_row() test coverage now **ELEVATED priority**. Bake into src/report.py test suite alongside ender_trifecta_box() tests (both helpers need promotion before Royal Ascot). Third NR swap today makes it a **hard rule**: ship helper to src/report.py before next race day. No more hand-edits after three swaps.

**Test coverage required when shipped:**
1. NR badge renders with correct text + inline style (ackground:#fff8dc; border-left:3pt solid #d99400)
2. Stale-odds caveat div is present in rationale row (same amber styling)
3. Apostrophes and special characters are HTML-escaped correctly
4. Original horse name does NOT appear in rendered HTML output (anti-regression)
5. ow-rationale row-rationale-outsider class is correctly applied

**Reviewer:** Saul (strict PRs for this helper; both Linus hand-edits verified before approval).
