# Changelog

All notable changes to race-analysis are documented here.
Format inspired by Keep a Changelog. Version numbers follow semver.

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
