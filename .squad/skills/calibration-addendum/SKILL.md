# Calibration Addendum Pattern

Use this when tests expose a mismatch between a design note's prose anchor and the implemented scoring formula.

1. Treat the formula and stated intent as the source of truth before changing code.
2. If the formula is coherent and the rough anchor is wrong, ship a dated addendum that corrects the anchor and explicitly says no runtime change is required.
3. If the formula violates the betting rationale, require a fresh implementation agent to change code and keep the reviewer lockout intact.
4. For contradictory flags plus measured data, measured data wins unless the spec explicitly says the flag overrides it.

This keeps calibration stable near race day: correct examples cheaply, change weights or curves only when the money rationale demands it.
