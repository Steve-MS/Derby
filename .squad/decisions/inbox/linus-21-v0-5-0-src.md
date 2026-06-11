# Linus 21 - v0.5.0 src handoff

Status: READY-FOR-GATE

## Files added / modified

- `src/sl_parser.py`: new stdlib Sporting Life saved-HTML parser, `__NEXT_DATA__` extractor, raw-schema mapper, import validator, and missing-field summarizer.
- `src/cli.py`: added `fetch --from-file PATH`, atomic same-dir temp write, score-smoke validation, failure fallback text, and ASCII fetch output.
- `src/going.py`, `src/scoring.py`: going-history source unavailable now scores true neutral and emits `going_data_source_unavailable`.
- `scripts/morning_odds.py`: skips null or unparseable raw `morning_price` values.
- `pyproject.toml`: bumped 0.4.1 to 0.5.0 and removed a non-ASCII comment marker.
- `tests/fixtures/sportinglife/sample-meeting.html`: moved lowercase and sanitized auth/account/email/token data while preserving racecard state.
- `tests/test_sl_parser.py`: parser and validation coverage.
- `tests/test_cli_fetch_from_file.py`: fetch import plus score smoke and atomic no-clobber failure coverage.
- `tests/test_scoring.py`: new going-source and null import scoring tests.
- `tests/test_chunk2_ascot_smoke.py`: updated stale live-scraper dry-run expectations to assert import-only deprecation state.
- `.squad/agents/livingston/history.md`, `.squad/decisions/inbox/livingston-13-v0-5-0-docs.md`: updated stale fixture path casing references.

## New CLI surface

Sample command:

```powershell
race-analysis fetch --course ascot --meeting royal-ascot-2026 --date 2026-06-16 --from-file tests\fixtures\sportinglife\sample-meeting.html
```

Sample output from the fixture shape:

```text
Source file: tests\fixtures\sportinglife\sample-meeting.html
Race count: 1
Runner count: 14 (13 active)
Fields missing: form_string=12, going_history=14, last_run_days=12, or=14, rpr=14, ts=14
Output path: data\raw\ascot-2026-06-16-racecards.json
Parse warnings: none
```

Without `--from-file`, `fetch` preserves validate-only behavior.

## Going-fit fix

`score_going_fit()` now accepts an optional source. Empty history with `going_history_source == "not_available"` returns 0.5 and `going_data == "source_unavailable"`; scoring adds `going_data_source_unavailable`. Empty history from any other source remains 0.35 plus `going_data_insufficient`.

Tests updated/added in `tests/test_scoring.py`:

- Existing insufficient-history test still asserts 0.35.
- New `not_available` test asserts true neutral 0.5 and the new flag.
- New null import test scores runners with null `morning_price`, `rpr`, and `ts`.

## Null tolerance

Checked consumers:

- `scripts/morning_odds.py`: skips null or unparseable `morning_price`.
- `src/betting.py`: already degrades through `parse_odds(None)` to PASS or no outsider odds.
- `src/racecard.py`: already renders missing prices as blank/zero potential through existing helpers.
- `src/scoring.py`: already falls back `rpr -> ts -> or_rating -> or`; null RPR/TS are safe when OR exists.

User-visible degradation: SL imports with no RPR/TS rely on OR-only class rating; no morning price yields neutral/no-odds betting behavior. Livingston should document if CHANGELOG needs more explicit operator wording.

## Pytest

Final command: `python -m pytest -q`

Result: `510 passed in 16.37s`

No ignore flags and no new skips.

## Parser warnings on fixture

Parser warnings observed: none.

Missing-field summary on fixture:

- `or=14`
- `rpr=14`
- `ts=14`
- `form_string=12`
- `last_run_days=12`
- `going_history=14`

## Rubber-duck concerns / judgment calls

- The supplied Sporting Life fixture is a single detailed racecard page with one detailed race and meeting-level summaries for the other races. The parser intentionally emits only detailed races with runner arrays and ignores summary-only races so it never writes zero-runner races.
- Fixture contained authenticated/account artifacts. I scrubbed the committed `sample-meeting.html` for email, auth/account, and token markers before using it in tests.
- I did not perform `git pull` because the mission also required no HTTP/network requests in the work. Branch was created from the local `main` at `v0.4.1`.
- I updated stale scraper smoke tests because v0.5.0 is import-only and those live scraper entrypoints are now deprecated/absent.

Status: READY-FOR-GATE
