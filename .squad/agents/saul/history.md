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

## Learnings

- 2026-06-03: Drafted `tests/test_trial_form.py` (19 tests) ahead of module — covers happy path, anti-fabrication fallbacks, distance gating, edge cases (case-insensitive lookup, None beaten_lengths, field-size-1 walkover, multi-trial best-result), and bounds. Key open questions for Danny: tier definitions, 10f gate confirmation, best-vs-most-recent multi-trial rule, exact JSON schema.

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
