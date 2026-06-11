# race-analysis

Python 3.12 race-prediction toolkit for UK Flat racing. Course-agnostic; ships with Epsom 2026 and Royal Ascot 2026 worked examples.

Scoring model v0.5. 16 signals. Weights sum to 1.0.

## Quickstart (race-day operator)

Use this for a new race-day card in v0.5.0.

1. Open the Sporting Life racecard in your browser using your normal subscription view: `https://www.sportinglife.com/racing/racecards/{date}/{course}`
2. Click every race link on the meeting page so each full racecard is expanded before saving.
3. File, Save Page As, Webpage, complete. Save the page to your machine.
4. Run: `race-analysis fetch --from-file <saved.html> --course <slug> --meeting <slug> --date YYYY-MM-DD`
5. Run the rest of the pipeline: `score`, `predict`, `report`, and `card`.

```powershell
$course = "{course}"
$meeting = "{meeting}"
$date = "YYYY-MM-DD"
$saved = "C:\path\to\saved-racecard.html"

race-analysis fetch --from-file $saved --course $course --meeting $meeting --date $date
race-analysis score --course $course --meeting $meeting --date $date
race-analysis predict --course $course --meeting $meeting --date $date --bankroll 100
race-analysis report --course $course --meeting $meeting --date $date
race-analysis card --course $course --meeting $meeting --date $date
```

If the console script is not installed, use `python -m src.cli` in place of `race-analysis`.

## Why save-and-parse

Sporting Life's Terms of Service allow personal use but prohibit automated data capture, including screen scraping: https://www.sportinglife.com/terms-and-conditions. v0.5.0 does not automate HTTP scraping. The operator opens the page manually, saves their legitimate browser view, and the CLI parses that local HTML into the existing raw-card schema.

## Replay Epsom Derby Day 2026-06-06 offline

Use this for a zero-network demo or regression check. The Epsom 2026-06-06 archive is tracked in the repository, so the replay works without live racecards, Sporting Life credentials, or internet fetches. The `fetch` step verifies the archived raw racecard at `data\raw\epsom-2026-06-06-racecards.json`; it does not pull live data.

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

### Next live meeting: Royal Ascot 2026-06-16

Royal Ascot Day 1 remains the current non-Epsom rehearsal. In v0.5.0, expand every race in the browser, save the Sporting Life page, and import it with `fetch --from-file` instead of dropping hand-built JSON first. If the parser fails, the manual JSON fallback is unchanged: place the canonical raw file at `data\raw\ascot-2026-06-16-racecards.json`, then run `fetch`, `score`, `predict`, `report`, and `card`.

See `RUNBOOK.md` section 2.2 for the Ascot command sequence and section 5 for race-day operator gates.

## Required environment variables

The Epsom replay and `fetch --from-file` import do not need live credentials. For race-day work, copy `.env.example` to `.env`, fill in values you need for manual browser login and other operator scripts, and run `python scripts\check_env.py` if you plan to use scripts that require the environment. Never commit `.env`.

| Variable | Required | Purpose |
|---|---:|---|
| `SPORTINGLIFE_USER` | Browser login only | Used when manually logging into Sporting Life in your browser to view racecards before saving the page |
| `SPORTINGLIFE_PASS` | Browser login only | Password for the Sporting Life account above |
| `ATR_COOKIE_FILE` | No | Optional At The Races cookie export path; defaults to `.cookies\attheraces.txt` |
| `RACING_API_KEY` | No | Reserved for future live-price ingestion |

## Expected output artifacts

The replay produces the Epsom replay family shown above. Epsom 2026 historical artifacts intentionally keep their legacy names, for example `outputs\report-2026-06-06.html`.

For non-Epsom courses, generated artifacts are flat files with the course slug in the name, for example `outputs\report-ascot-2026-06-16.html`. See `docs\data-layout.md` for the full path decision.

Note: T-60 watchdog status (`outputs\t60-status-{date}.json`) is produced by the T-60 step in `RUNBOOK.md` section 5 for race-day operator workflows only. It is not part of the README Quickstart.

## Project layout

```text
race-analysis/
|-- src/              Python package: scoring, betting, reporting, signals
|-- scripts/          Race-day operator scripts and deprecated scraper references
|-- tests/            pytest test suite
|-- config/courses/   Course and meeting configuration
|-- data/
|   |-- raw/          Racecard JSON files, flat and course-prefixed
|   |-- enrichment/   Runner, going, source, and market snapshots
|   `-- results/      Post-race results JSON
|-- docs/             Data-layout and operator-facing design notes
`-- spec/             Model specs and scoring rationale
```

## CLI usage template

Always pass `--course`, `--meeting`, and `--date` for publish work. Add `--from-file` to `fetch` when importing a browser-saved racecard page; omit it only when validating an existing raw JSON file such as the Epsom archive.

```powershell
$course = "{course}"
$meeting = "{meeting}"
$date = "{date}"
$saved = "C:\path\to\saved-racecard.html"

race-analysis fetch --from-file $saved --course $course --meeting $meeting --date $date
race-analysis score --course $course --meeting $meeting --date $date
race-analysis predict --course $course --meeting $meeting --date $date --bankroll 100
race-analysis report --course $course --meeting $meeting --date $date
race-analysis card --course $course --meeting $meeting --date $date --outlay 100
python scripts\t60_watchdog.py --course=$course --meeting=$meeting --date=$date
```

## Running tests

```powershell
pytest -q
```

## Scoring model

Current version: v0.5. Weights sum exactly to 1.0000. The 16 signals cover class, form, going, pace, trainer/jockey, equipment, market move, and sire stamina. See `spec\scoring-model-v0.1.md` and `docs\` for consumer-facing design notes.

## Anti-fabrication rule

When data is missing for any signal, that signal returns 50 (neutral). It does not invent a score. The model abstains rather than fabricates.
