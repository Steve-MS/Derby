# Saul — History

## Project context (seeded 2026-06-03)

- Python 3.12 race-analysis toolkit. Repo Steve-MS/Derby, commit 5a1770e.
- 227 pytest tests currently passing.
- Test pattern: each signal module has its own `tests/test_<signal>.py` with 18-22 tests.
- Reviewer authority on all scoring/signal/betting PRs.
- Key validation milestone: once Ladies Day (Fri 5 Jun) is run, backtest the model's Friday predictions against actual results before Derby Day picks are finalised.
- Boundary cases to always test: missing data → neutral 50, scratched horses, single-runner edge case.
