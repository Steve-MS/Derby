# Rusty — History

## Project context (seeded 2026-06-03)

- Python 3.12 race-analysis toolkit. Repo Steve-MS/Derby, commit 5a1770e.
- Existing signal modules to mirror: `src/cd_form.py`, `src/sires.py`, `src/pace.py`, `src/going.py`.
- All return 0-100 normalised scores; missing data → 50.
- Sire stamina sets the gating pattern: only fires at 10f+ races.
- 227 tests passing — each new signal expected to add ~18-22 tests.
- Backlog: trial-form (first), market-move, trainer-strike, jt-combo, equipment.
