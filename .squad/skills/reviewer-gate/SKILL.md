# Reviewer Gate Checklist

Use this when reviewing signal/scoring changes before ship approval.

## Steps

1. Read the design note, implementation note, test note, changed signal modules, and scoring integration.
2. Verify weights numerically with the runtime config; require sum drift <= 1e-6.
3. Probe anti-fabrication behavior explicitly:
   - missing lookup data returns 50
   - empty runner/data returns 50
   - `runner=None` returns 50, not an exception
4. Probe score bounds for low/high/extreme valid data; require [0, 100] and no NaN.
5. Inspect `score_runner()` for imports, raw signal calls, config weights, and weighted-score use.
6. Run the required pytest command from repo root.
7. If rejecting, name a non-author revision owner and the exact lockout scope.

## Output

Record PASS/FAIL by gate, line references for integration, pytest summary, and explicit approve/reject wording.
