# Scribe-28 v0.4.0 ship

Status: COMPLETE
Started: 2026-06-08T19:40:00+01:00
Completed: 2026-06-08T19:40:00+01:00

Checklist:
- [x] Stage 1: Read gate/context docs and validate working tree
- [x] Stage 2: Create atomic commits for docs, metadata, and squad state
- [x] Stage 3: Push main, tag v0.4.0, and create GitHub release
- [x] Stage 4: Verify release, test suite, and final clean disposition

Commit batch:
- Commit 1: 4816929 - publish-ready docs
- Commit 2: 0c661a2 - release metadata
- Commit 3: a6fd7c2 - squad state merge
- Commit 4: this commit - Scribe-28 ceremony log

Tag:
- v0.4.0 - Course-agnostic publish-ready release

Release:
- https://github.com/Steve-MS/Derby/releases/tag/v0.4.0

Untracked disposition:
- Do not stage Ascot generated outputs under data/enrichment, data/raw, or outputs.
- Do not stage tests/fixtures/ascot; no tracked tests reference it.
- Do not stage tests/test_regression_wave3.py.
