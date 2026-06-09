# Squad Follow-ups (deferred work, no blocker)

## FU-1 — morning_odds.py --dry-run credential gate
Status: CLOSED 2026-06-08 by Scribe-27 (shipped in v0.4 #6 Chunk 5+6 batch).
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
## FU-2 — chunk4 edge-case tests
Status: CLOSED 2026-06-08 by Scribe-27 (shipped in v0.4 #6 Chunk 5+6 batch).
Created: 2026-06-08 by Danny-5 (Chunk 4 audit)
Owner: TBD (non-Rusty per reviewer-protocol)
Concern: tests/test_chunk4_priors.py covers main paths but not these edge cases:
  - partial scoring_priors (some keys present, others missing)
  - scoring_priors set to explicit non-object (e.g. null, string)
  - direct scoring_priors_for() with priors={} semantics
Impact: low — current Epsom + neutral Ascot work without these cases.
Add before enabling non-neutral priors for a new course.
Priority: low. Pick up alongside FU-3 if calibrating new course.

## FU-3 — trial_form.load_trial_form() default-course coupling
Status: CLOSED 2026-06-08 by Scribe-27 (shipped in v0.4 #6 Chunk 5+6 batch).
Created: 2026-06-08 by Danny-5 (Chunk 4 audit)
Owner: TBD (non-Rusty per reviewer-protocol)
Concern: trial_form.load_trial_form() normalizes raw enrichment using
default-course priors when called without an explicit course. Safe for
Epsom + disabled-neutral Ascot, but needs revisiting before enabling
trial-form priors for a non-Epsom course.
Impact: low for MVP, blocking for second-course trial-form calibration.
Priority: low-medium.

## FU-4 — equipment_defaults unused by score_equipment()
Status: CLOSED 2026-06-08 by Scribe-27 (shipped in v0.4 #6 Chunk 5+6 batch).
Created: 2026-06-08 by Danny-5 (Chunk 4 audit)
Owner: TBD (non-Rusty per reviewer-protocol)
Concern: config/courses/*.json carries equipment_defaults but
score_equipment() does not consume it. Empty default + no Epsom
calibration found means this is not a functional blocker today.
Wire it up if/when course-specific equipment calibration is added.
Priority: low.

## FU-5 - R-10 cli card going passthrough
Status: CLOSED 2026-06-08 by Scribe-27 (shipped in v0.4 #6 Chunk 5+6 batch).
Created: 2026-06-08 by Scribe-26 (from Livingston-8)
Owner: TBD
Concern: cli card still renders racecard subtitle Going: TBC even when Ascot report has Good to Firm.
Impact: low operator polish; non-blocking for R-7/R-8/R-9 ship.
Priority: defer to Chunk 5/6.

## FU-6 - R-5 report footer Epsom market-latest leak
Status: CLOSED 2026-06-08 by Scribe-27 (shipped in v0.4 #6 Chunk 5+6 batch).
Created: 2026-06-08 by Scribe-26 (from Livingston-7/8)
Owner: TBD
Concern: non-Epsom report/racecard paths can still surface stale Epsom odds snapshot context.
Impact: low-medium presentation provenance issue; not in Linus-18 blocker scope.
Priority: defer to Chunk 5/6.

## FU-7 - R-6 Derby Weekend CSS comment
Status: OPEN (ship-with-note in v0.4.0 CHANGELOG).
Created: 2026-06-08 by Scribe-26 (from Livingston-7/8)
Owner: TBD
Concern: generated report HTML still contains a Derby Weekend CSS comment.
Impact: cosmetic only; non-user-facing.
Priority: low, defer.

## FU-8 - R-11 PowerShell line-wrap on T-60 GBP total
Status: OPEN (ship-with-note in v0.4.0 CHANGELOG).
Created: 2026-06-08 by Scribe-26 (from Livingston-8)
Owner: TBD
Concern: T-60 operator table can wrap/split the GBP 11.70 header consistency detail in PowerShell transcripts.
Impact: cosmetic terminal rendering only; status remains correct.
Priority: low, defer.

## FU-9 - Audit stale committed outputs baselines
Status: OPEN (ship-with-note in v0.4.0 CHANGELOG).
Created: 2026-06-08 by Scribe-26 (Saul-10 stale-baseline lesson)
Owner: TBD
Concern: committed outputs/ files can be mistaken for current regression contracts after schema migrations.
Impact: process risk for future gates.
Fix: audit other stale committed outputs/ files; consider moving canonical baselines to tests/fixtures/regression/.
Priority: process improvement, defer.

## FU-10 — data-layout path_for ownership for T-60 status
Status: OPEN (ship-with-note in v0.4.0 CHANGELOG).
Created: 2026-06-08 by Saul-11 (Chunk 6 combined gate)
Owner: TBD
Concern: docs/data-layout.md says path_for() is the canonical resolver for course/date artifacts and says non-Epsom artifacts use course-prefixed filenames, but the T-60 status row is outputs\t60-status-2026-06-16.json and scripts/t60_watchdog.py writes that path directly rather than via path_for().
Impact: low documentation/API ownership ambiguity. Not a runtime regression; watchdog tests still pass.
Fix: Either add a path_for kind for t60-status and decide whether it becomes course-prefixed, or explicitly document T-60 status as watchdog-owned and intentionally not course-prefixed.
Priority: low-medium before the next non-Epsom operator docs pass.

## 2026-06-08 v0.4.1 follow-up check

Status: VERIFIED by Scribe-29. FU-7, FU-8, FU-9, and FU-10 remain OPEN; v0.4.1 closed Livingston-11 R-1 through R-7 only and does not supersede these deferred items.
