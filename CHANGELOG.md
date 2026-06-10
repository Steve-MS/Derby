# Changelog

All notable changes to race-analysis are documented here.
Format inspired by Keep a Changelog. Version numbers follow semver.

## [0.5.0] - 2026-06-10

Import-only racecard release. v0.5.0 replaces the v0.4.x manual JSON drop as the primary race-day path: operators save a Sporting Life racecard page from their browser, then parse that local HTML into the canonical raw-card JSON.

### Added
- `race-analysis fetch --from-file <saved.html>` imports browser-saved Sporting Life HTML and writes the canonical raw racecard file for the selected `--course`, `--meeting`, and `--date`.
- Going-fit `not_available` source flag. Explicitly missing going evidence now scores neutral at 0.5, while true insufficient-history cases keep the lower 0.35 prior.

### Changed
- `morning_price`, RPR, and TS can be null in raw/imported data. Scoring and market fallback paths tolerate those gaps instead of failing or fabricating values.
- Consumer docs now lead with the save-and-parse workflow and keep the manual JSON drop only as a fallback.

### Deprecated
- `scripts/scrape_sportinglife.py` and `scripts/scrape_racingpost.py` are renamed to `.deprecated.py` and exit immediately. They are retained only for historical reference and will be removed in v0.6.0.

### Fixed
- No additional consumer-facing side-fixes were flagged in the docs handoff.

### Notes for consumers
- Sporting Life's Terms of Service prohibit automated data capture including screen scraping. v0.5.0 therefore avoids live HTTP scraping and uses a browser save of the operator's legitimate personal-use view.
- Race-day command shape: save the page, run `race-analysis fetch --from-file <saved.html> --course <slug> --meeting <slug> --date YYYY-MM-DD`, then run `score`, `predict`, `report`, and `card`.
- Manual JSON drop fallback is unchanged: place the canonical raw card at `data\raw\{course}-{date}-racecards.json`, then run `race-analysis fetch` without `--from-file` to validate it before the rest of the pipeline.

[0.5.0]: https://github.com/Steve-MS/Derby/releases/tag/v0.5.0

## [0.4.1] - 2026-06-08

Patch release fixing publish blockers found in v0.4.0 consumer dress-rehearsal.

### Fixed
- **`pip install -e .` now works.** v0.4.0 shipped with an invalid
  `build-backend = "setuptools.backends.legacy:build"` in `pyproject.toml`;
  the `race-analysis` console script could not be installed. Fixed to use
  the standard `setuptools.build_meta`. (R-1)
- README Quickstart now uses the Epsom 2026-06-06 archive replay (works
  offline against committed data) instead of the Royal Ascot example
  (which required live fetch unavailable in v0.4.x). Royal Ascot moved
  to a "Live race-day workflow" section pointing at RUNBOOK.md. (R-2/R-3)
- README expected-artifacts list reconciled with what Quickstart actually
  produces; T-60 watchdog output is now noted as a RUNBOOK-only artifact. (R-4)
- README no longer points consumers at internal `.squad/` coordination
  files; weight-history and project-layout sections updated. (R-6)
- `python -m src.cli --help` description updated from
  "Race prediction toolkit - Epsom Classics 2026" to course-agnostic
  phrasing matching pyproject.toml. (R-7)
- Fixed the pre-existing `tests/test_racecard_wave33.py` failure so consumers
  can run `pytest -q` without surprises. (R-5)

### Notes for consumers
- Live data fetch from Sporting Life / Racing Post is NOT implemented in
  v0.4.x. To run the pipeline on a new race day, you must manually source
  racecards as JSON and place them at
  `data/raw/{course}-{date}-racecards.json`. See RUNBOOK.md.

[0.4.1]: https://github.com/Steve-MS/Derby/releases/tag/v0.4.1

## [0.4.0] - 2026-06-08

First publish-ready release. The CLI is now course-agnostic and ships with
two worked examples (Epsom 2026 and Royal Ascot 2026). See RUNBOOK.md for
the full operator workflow.

### Added
- Course/meeting/date CLI parameters (`--course`, `--meeting`, `--date`)
  threaded end-to-end through fetch / score / predict / report / card.
- `src/course_config.py` with `load_course_config()` and `path_for()` helpers;
  authoritative data-layout decision in `docs/data-layout.md` (keep flat
  course-prefixed; legacy Epsom paths preserved as archive).
- Royal Ascot 2026-06-16 course config (`config/courses/ascot.json`) and
  fixture set under `tests/fixtures/ascot/`.
- Course-aware scoring priors (chunk 4) and trial-form coupling that now
  requires an explicit course argument.
- Course-scoped market snapshots in report footer (no more cross-course
  leakage in race-day reports).
- T-60 watchdog with course-prefixed status output.
- Generic, Windows-first RUNBOOK.md with Epsom replay + Ascot Day 1 + template
  worked examples.
- `.squad/skills/*` rewritten as course-agnostic skill templates.
- `morning_odds.py --dry-run` skips credential gate so smoke tests work
  without Sporting Life secrets.

### Changed
- Root README rewritten as a consumer landing page (Quickstart + RUNBOOK
  pointer + env-var contract).
- `pyproject.toml` description is no longer Epsom-specific.
- `equipment_defaults` removed from course configs (was never consumed;
  re-wire if course-specific calibration becomes necessary).

### Known issues (ship-with-note, tracked in `.squad/followups.md`)
- FU-7: Cosmetic "Derby Weekend" CSS comment lingers in report template;
  non-user-facing.
- FU-8: T-60 PowerShell GBP-total line can wrap on narrow terminals;
  machine status remains correct.
- FU-9: Committed Epsom 2026-06-06 baseline outputs live under `outputs/`
  for now (intentional archive + regression baseline); future baselines
  belong under `tests/fixtures/regression/`.
- FU-10: T-60 status path is documented in RUNBOOK and `docs/data-layout.md`
  but is not yet a first-class `path_for()` "kind". Documentation gap only.

### Notes for consumers
- License: not yet attached. Treat this release as internal GitHub-only
  until a LICENSE file lands.
- Output baselines: the tracked Epsom 2026-06-06 artifacts under `outputs/`
  are intentional regression baselines, not example output. Generated
  Ascot artifacts should remain untracked locally.
- Credentials: `SPORTINGLIFE_USER` / `SPORTINGLIFE_PASS` only required for
  live odds fetch; `--dry-run` paths work without them. See `.env.example`.

[0.4.0]: https://github.com/Steve-MS/Derby/releases/tag/v0.4.0
