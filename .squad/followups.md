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
## FU-2 — chunk4 edge-case tests
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
Created: 2026-06-08 by Danny-5 (Chunk 4 audit)
Owner: TBD (non-Rusty per reviewer-protocol)
Concern: trial_form.load_trial_form() normalizes raw enrichment using
default-course priors when called without an explicit course. Safe for
Epsom + disabled-neutral Ascot, but needs revisiting before enabling
trial-form priors for a non-Epsom course.
Impact: low for MVP, blocking for second-course trial-form calibration.
Priority: low-medium.

## FU-4 — equipment_defaults unused by score_equipment()
Created: 2026-06-08 by Danny-5 (Chunk 4 audit)
Owner: TBD (non-Rusty per reviewer-protocol)
Concern: config/courses/*.json carries equipment_defaults but
score_equipment() does not consume it. Empty default + no Epsom
calibration found means this is not a functional blocker today.
Wire it up if/when course-specific equipment calibration is added.
Priority: low.
