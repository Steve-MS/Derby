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

## 2026-06-03 — v0.5 anti-fab hardening patch

- Took narrow reviewer-lockout escalation because Rusty was locked out of revising Saul's rejected v0.5 signal artifact.
- Added the same public-entry guard to `market_move_signal`, `trainer_14d_signal`, and `jt_combo_signal`: non-dict runners now return neutral 50.0.
- Added one explicit `runner=None` anti-fab regression test per module.
- Left signal maths, scoring weights, schemas, and Danny's spec TODOs untouched.
- Validation: `pytest -x` collected 326 tests and all 326 passed.
