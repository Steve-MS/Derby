# Squad Follow-ups (deferred work, no blocker)

## FU-1 — morning_odds.py --dry-run credential gate
Created: 2026-06-08 by Saul-7 (Chunk 2 gate)
Owner: TBD (non-Livingston per reviewer-protocol)
Concern: scripts/morning_odds.py:525-527 calls _gate_env() before the dry-run
check at line 556-558, so --dry-run exits 1 without SPORTINGLIFE_USER/PASS
in the environment. Pre-existing fail-loud live-scrape protection.
Impact: Steve's local env has creds so this doesn't bite ops. Matters for
v0.4 publish-as-skill goal — downstream skill users won't have these env vars.
Fix: Move _gate_env() call AFTER the dry-run branch. ~5 lines.
Tests: add a tests/test_morning_odds.py case for dry-run-without-credentials.
Priority: low-medium. Pick up after wave-2 #6 chunks 4 land.