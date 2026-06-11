### 2026-06-11: Hard-fail partial Sporting Life imports
**By:** Marty-1
**What:** Implemented the user-confirmed hard-fail path for saved Sporting Life meeting pages that advertise more races than are parsed in detail.
**Why:** Saul-14 rejected v0.5.0 because summary-only races were silently dropped, creating a risk of publishing partial cards.

## Changed files and line counts

- `src\sl_parser.py`: +73 / -2. Added `SLPartialImportError`, advertised race counting from `pageProps.meeting`, and the operator-facing partial import message.
- `src\cli.py`: +20 / -6. Added the partial-import failure path before any raw JSON write, with temp cleanup and raw-file unchanged reporting.
- `tests\test_cli_fetch_from_file.py`: +51 / -1. Added fetch-level partial import rejection coverage and changed the success path to use a one-advertised/one-detailed HTML fixture variant.
- `tests\test_sl_parser.py`: +28 / -9. Added parser-level partial fixture rejection and complete fixture mutation helpers.
- `README.md`: +5 / -4. Added Quickstart instructions to expand every race before saving.
- `RUNBOOK.md`: +18 / -4. Added partial import recovery instructions and troubleshooting guidance.

## Test count delta

- Before: 510 passed per Saul-14 gate.
- Now: 512 passed with `python -m pytest -q`.

## Exact partial import error message

```text
ERROR: Partial import detected -- saved meeting page contains 6 races but only 1 was parsed in detail.
The other 5 races are summary-only (race links were not expanded before save).
Action: Open the meeting page in your browser, click each race to expand its full racecard, then re-save the page and retry.
```

The race counts are dynamic; the text above is the sample fixture result.

## Re-check notes for Saul

- Re-check a real fully expanded saved meeting with multiple detailed races, not just the one-race complete fixture mutation.
- Re-check that failure leaves `data\raw\ascot-2026-06-16-racecards.json` unchanged; Marty verified the sample fixture exits 1 and the SHA256 hash is unchanged.
- The advertised count is derived from the `pageProps.meeting` race summaries matched to detailed race IDs when available.
