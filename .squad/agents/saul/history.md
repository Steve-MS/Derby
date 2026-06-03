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

## Learnings

- 2026-06-03: Drafted `tests/test_trial_form.py` (19 tests) ahead of module — covers happy path, anti-fabrication fallbacks, distance gating, edge cases (case-insensitive lookup, None beaten_lengths, field-size-1 walkover, multi-trial best-result), and bounds. Key open questions for Danny: tier definitions, 10f gate confirmation, best-vs-most-recent multi-trial rule, exact JSON schema.
