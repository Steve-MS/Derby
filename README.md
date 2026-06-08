# race-analysis

Python 3.12 race-prediction toolkit for UK Flat racing. Course-agnostic; ships with Epsom 2026 and Royal Ascot 2026 worked examples.

Scoring model v0.4. 16 signals. Weights sum to 1.0.

## Quickstart: render Royal Ascot Day 1 in about 10 minutes

This path takes a new consumer from clone to a rendered racecard using the current Ascot worked example: `ascot`, `royal-ascot-2026`, `2026-06-16`.

```powershell
git clone https://github.com/Steve-MS/Derby.git race-analysis
Set-Location race-analysis

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e ".[dev]"

Copy-Item .env.example .env
# Edit .env and set SPORTINGLIFE_USER and SPORTINGLIFE_PASS.
python scripts\check_env.py

$course = "ascot"
$meeting = "royal-ascot-2026"
$date = "2026-06-16"

python scripts\scrape_racingpost.py --course=$course --meeting=$meeting --date=$date --dry-run
python scripts\scrape_sportinglife.py --course=$course --meeting=$meeting --date=$date --dry-run
python scripts\morning_odds.py --course=$course --meeting=$meeting --date=$date --dry-run

python -m src.cli fetch --course=$course --meeting=$meeting --date=$date
python -m src.cli score --course=$course --meeting=$meeting --date=$date
python -m src.cli predict --course=$course --meeting=$meeting --date=$date --bankroll 100
python -m src.cli report --course=$course --meeting=$meeting --date=$date
python -m src.cli card --course=$course --meeting=$meeting --date=$date

Start-Process .\outputs\racecard-ascot-2026-06-16.html
```

For the full operator workflow, including the T-60 watchdog, see `RUNBOOK.md`.

## Required environment variables

Copy `.env.example` to `.env`, fill in real values, and run `python scripts\check_env.py`. Never commit `.env`.

| Variable | Required | Purpose |
|---|---:|---|
| `SPORTINGLIFE_USER` | Yes | Sporting Life authenticated racecard and live-runner checks |
| `SPORTINGLIFE_PASS` | Yes | Password for the Sporting Life account above |
| `ATR_COOKIE_FILE` | No | Optional At The Races cookie export path; defaults to `.cookies\attheraces.txt` |
| `RACING_API_KEY` | No | Reserved for future live-price ingestion |

## Expected output artifacts

For non-Epsom courses, generated artifacts are flat files with the course slug in the name. The Ascot quickstart above should produce this core family:

| Artifact | Example path |
|---|---|
| Raw racecards | `data\raw\ascot-2026-06-16-racecards.json` |
| Scores | `outputs\scores-ascot-2026-06-16.json` |
| Bets | `outputs\bets-ascot-2026-06-16.json` |
| Long report | `outputs\report-ascot-2026-06-16.html` |
| Printable racecard | `outputs\racecard-ascot-2026-06-16.html` |
| Plain-text slip | `outputs\slip-ascot-2026-06-16.txt` |
| T-60 status | `outputs\t60-status-2026-06-16.json` |

Epsom 2026 historical artifacts intentionally keep their legacy names, for example `outputs\report-2026-06-06.html`. See `docs\data-layout.md` for the full path decision.

## Project layout

```text
race-analysis/
|-- src/              Python package: scoring, betting, reporting, signals
|-- scripts/          Race-day operator scripts and scrapers
|-- tests/            pytest test suite
|-- config/courses/   Course and meeting configuration
|-- data/
|   |-- raw/          Racecard JSON files, flat and course-prefixed
|   |-- enrichment/   Runner, going, source, and market snapshots
|   `-- results/      Post-race results JSON
|-- outputs/          Generated scores, bets, reports, racecards, slips
|-- docs/             Data-layout and operator-facing design notes
|-- spec/             Model specs and scoring rationale
`-- .squad/           Team agent config, skills, and decisions ledger
```

## CLI usage template

Always pass `--course`, `--meeting`, and `--date` for publish work.

```powershell
$course = "{course}"
$meeting = "{meeting}"
$date = "{date}"

python -m src.cli fetch --course=$course --meeting=$meeting --date=$date
python -m src.cli score --course=$course --meeting=$meeting --date=$date
python -m src.cli predict --course=$course --meeting=$meeting --date=$date --bankroll 100
python -m src.cli report --course=$course --meeting=$meeting --date=$date
python -m src.cli card --course=$course --meeting=$meeting --date=$date --outlay 100
python scripts\t60_watchdog.py --course=$course --meeting=$meeting --date=$date
```

## Running tests

```powershell
pytest -q
```

## Scoring model

Current version: v0.4. Weights sum exactly to 1.0000. The 16 signals cover class, form, going, pace, trainer/jockey, equipment, market move, and sire stamina. See `spec\scoring-model-v0.1.md` and `.squad\decisions.md` for weight history and design rationale.

## Anti-fabrication rule

When data is missing for any signal, that signal returns 50 (neutral). It does not invent a score. The model abstains rather than fabricates.
