# race-analysis

Python 3.12 race-prediction toolkit for UK Flat racing. Course-agnostic; ships with Epsom 2026 and Royal Ascot 2026 worked examples.

Scoring model v0.4. 16 signals. Weights sum to 1.0.

## Quickstart: replay Epsom Derby Day 2026-06-06 offline

Use this first. The Epsom 2026-06-06 archive is tracked in the repository, so the replay works without live racecards, Sporting Life credentials, or internet fetches. The `fetch` step verifies the archived raw racecard at `data\raw\epsom-2026-06-06-racecards.json`; it does not pull live data.

```powershell
git clone https://github.com/Steve-MS/Derby.git race-analysis
Set-Location race-analysis

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e ".[dev]"

$course = "epsom"
$meeting = "derby-2026"
$date = "2026-06-06"

python -m src.cli fetch --course=$course --meeting=$meeting --date=$date
python -m src.cli score --course=$course --meeting=$meeting --date=$date
python -m src.cli predict --course=$course --meeting=$meeting --date=$date --bankroll 100
python -m src.cli report --course=$course --meeting=$meeting --date=$date
python -m src.cli card --course=$course --meeting=$meeting --date=$date

Start-Process .\outputs\report-2026-06-06.html
Start-Process .\outputs\racecard-2026-06-06.html
Get-Content .\outputs\slip-2026-06-06.txt
```

### What you should see

The replay writes or refreshes the committed Epsom archive artifacts below. Open the HTML files in a browser and inspect the slip in the terminal.

| Artifact | Epsom replay path |
|---|---|
| Raw racecards | `data\raw\epsom-2026-06-06-racecards.json` |
| Scores | `outputs\scores-2026-06-06.json` |
| Bets | `outputs\bets-2026-06-06.json` |
| Long report | `outputs\report-2026-06-06.html` |
| Printable racecard | `outputs\racecard-2026-06-06.html` |
| Plain-text slip | `outputs\slip-2026-06-06.txt` |

### Live race-day workflow: Royal Ascot 2026-06-16

Royal Ascot Day 1 is a live race-day workflow, not the default Quickstart in v0.4.x. Live fetch is not implemented in v0.4.x. For Royal Ascot 2026-06-16, you must source racecards manually, for example from a Racing Post export, and drop them into `data\raw\{course}-{date}-racecards.json` before running `race-analysis fetch` or `python -m src.cli fetch`. The Ascot path is `data\raw\ascot-2026-06-16-racecards.json`.

See `RUNBOOK.md` section 2.2 for the Ascot command sequence and section 5 for the race-day operator gates.

## Required environment variables

The Epsom replay above does not need live credentials. For live race-day work, copy `.env.example` to `.env`, fill in real values, and run `python scripts\check_env.py`. Never commit `.env`.

| Variable | Required | Purpose |
|---|---:|---|
| `SPORTINGLIFE_USER` | Yes for live odds | Sporting Life authenticated racecard and live-runner checks |
| `SPORTINGLIFE_PASS` | Yes for live odds | Password for the Sporting Life account above |
| `ATR_COOKIE_FILE` | No | Optional At The Races cookie export path; defaults to `.cookies\attheraces.txt` |
| `RACING_API_KEY` | No | Reserved for future live-price ingestion |

## Expected output artifacts

The Quickstart produces the Epsom replay family shown above. Epsom 2026 historical artifacts intentionally keep their legacy names, for example `outputs\report-2026-06-06.html`.

For non-Epsom courses, generated artifacts are flat files with the course slug in the name, for example `outputs\report-ascot-2026-06-16.html`. See `docs\data-layout.md` for the full path decision.

Note: T-60 watchdog status (`outputs\t60-status-{date}.json`) is produced by the T-60 step in `RUNBOOK.md` section 5 for race-day operator workflows only. It is not part of the README Quickstart.

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
`-- spec/             Model specs and scoring rationale
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

Current version: v0.4. Weights sum exactly to 1.0000. The 16 signals cover class, form, going, pace, trainer/jockey, equipment, market move, and sire stamina. See `spec\scoring-model-v0.1.md` and `docs\` for consumer-facing design notes.

## Anti-fabrication rule

When data is missing for any signal, that signal returns 50 (neutral). It does not invent a score. The model abstains rather than fabricates.
