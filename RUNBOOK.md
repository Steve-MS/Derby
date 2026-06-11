# RUNBOOK: Operator Workflow for Any Course, Meeting, and Date

For: operators and developers who need to import race data, score a card, generate bets, produce printable artifacts, and handle race-day failures.

Scope: Windows-first workflow for any configured course/meeting/date. Epsom Derby 2026 is preserved as the historical example. Royal Ascot Day 1 is the current non-Epsom example.

Last updated: 2026-06-10

## 0. Quick Reference: Generic Meeting-Day Checklist

Set these four values first in PowerShell. The saved HTML path is used only when importing a newly saved browser page.

```powershell
$course = "{course}"
$meeting = "{meeting}"
$date = "{date}"
$saved = "C:\path\to\saved-racecard.html"
```

1. Open the Sporting Life racecard in your browser, using your normal account view if needed. Click every race link on the meeting page so each full racecard is expanded, then save it with File, Save Page As, Webpage, complete.

```text
https://www.sportinglife.com/racing/racecards/{date}/{course}
```

2. Import or verify source racecards.

```powershell
race-analysis fetch --from-file $saved --course $course --meeting $meeting --date $date
```

If the console script is not installed, replace `race-analysis` with `python -m src.cli`.

3. Dry-run the morning odds command before any market write.

```powershell
python scripts\morning_odds.py --course=$course --meeting=$meeting --date=$date --dry-run
```

4. Score, predict, report, and card.

```powershell
race-analysis score --course $course --meeting $meeting --date $date
race-analysis predict --course $course --meeting $meeting --date $date --bankroll 100
race-analysis report --course $course --meeting $meeting --date $date
race-analysis card --course $course --meeting $meeting --date $date
```

5. Run the T-60 watchdog. Stop on exit code 2. Review stale artifacts on exit code 1.

```powershell
python scripts\t60_watchdog.py --course=$course --meeting=$meeting --date=$date
$LASTEXITCODE
```

6. Open the outputs listed by the commands. Expected core artifacts are scores JSON, bets JSON, report HTML, racecard HTML, plain-text slip, and T-60 status JSON.

## 1. Prerequisites

### 1.1 Environment

- Python 3.12+
- Dependencies from `requirements.txt`
- Browser access to the operator's racecard source view
- Write access to `data\raw`, `data\enrichment`, `data\results`, and `outputs`
- PowerShell as the primary shell

### 1.2 Credentials

The `fetch --from-file` import does not read Sporting Life credentials. The variables below are kept as operator documentation for manual browser login and for scripts that still check the environment.

| Variable | Purpose | Missing result |
|---|---|---|
| `SPORTINGLIFE_USER` | Used when manually logging into Sporting Life in your browser to view racecards before saving the page | Browser login must be handled outside the CLI |
| `SPORTINGLIFE_PASS` | Password for the Sporting Life account above | Browser login must be handled outside the CLI |

Do not paste credentials into logs, commits, runbook notes, or `.squad` files.

## 2. Worked Examples

### 2.1 Epsom Derby, Saturday 2026-06-06, historical replay

Use this to reproduce the historical Derby Day from archived raw data and legacy Epsom paths. No saved HTML is needed.

```powershell
$course = "epsom"
$meeting = "derby-2026"
$date = "2026-06-06"

python -m src.cli fetch --course=$course --meeting=$meeting --date=$date
python -m src.cli score --course=$course --meeting=$meeting --date=$date
python -m src.cli predict --course=$course --meeting=$meeting --date=$date --bankroll 100
python -m src.cli report --course=$course --meeting=$meeting --date=$date
python -m src.cli card --course=$course --meeting=$meeting --date=$date
python scripts\t60_watchdog.py --course=$course --meeting=$meeting --date=$date
```

### 2.2 Royal Ascot Day 1, Tuesday 2026-06-16

Use this for the current Ascot smoke and operator rehearsal.

```powershell
$course = "ascot"
$meeting = "royal-ascot-2026"
$date = "2026-06-16"
$saved = "C:\path\to\sportinglife-ascot-2026-06-16.html"

race-analysis fetch --from-file $saved --course $course --meeting $meeting --date $date
python scripts\morning_odds.py --course=$course --meeting=$meeting --date=$date --dry-run

race-analysis score --course $course --meeting $meeting --date $date
race-analysis predict --course $course --meeting $meeting --date $date --bankroll 100
race-analysis report --course $course --meeting $meeting --date $date
race-analysis card --course $course --meeting $meeting --date $date
python scripts\t60_watchdog.py --course=$course --meeting=$meeting --date=$date
```

Expected course-prefixed output names include `data\raw\ascot-2026-06-16-racecards.json`, `outputs\scores-ascot-2026-06-16.json`, `outputs\bets-ascot-2026-06-16.json`, `outputs\report-ascot-2026-06-16.html`, `outputs\racecard-ascot-2026-06-16.html`, `outputs\slip-ascot-2026-06-16.txt`, and `outputs\t60-status-2026-06-16.json`.

### 2.3 Generic template

Replace the placeholders and keep course, meeting, and date on every command.

```powershell
$course = "{course}"
$meeting = "{meeting}"
$date = "{date}"
$saved = "C:\path\to\saved-racecard.html"

race-analysis fetch --from-file $saved --course $course --meeting $meeting --date $date
python scripts\morning_odds.py --course=$course --meeting=$meeting --date=$date --dry-run
race-analysis score --course $course --meeting $meeting --date $date
race-analysis predict --course $course --meeting $meeting --date $date --bankroll 100
race-analysis report --course $course --meeting $meeting --date $date
race-analysis card --course $course --meeting $meeting --date $date
python scripts\t60_watchdog.py --course=$course --meeting=$meeting --date=$date
```

## 3. Source Pattern and Fallbacks

### 3.1 Browser-saved Sporting Life racecards

Open manually in the browser:

```text
https://www.sportinglife.com/racing/racecards/{date}/{course}
```

Before saving, click every race link on the meeting page so all full racecards are expanded in the saved HTML.

Import command:

```powershell
race-analysis fetch --from-file $saved --course $course --meeting $meeting --date $date
```

Why: Sporting Life's Terms of Service prohibit automated data capture including screen scraping. The v0.5.0 workflow parses a local browser save that the operator created from their legitimate personal-use view.

Failure modes: saved file is the wrong page, page is an error shell, racecard app state is absent, the parser reports missing mandatory fields, or the parser reports a partial import. Do not publish partial imports.

#### If fetch reports partial import

A partial import means the saved meeting page advertised more races than the parser found in full detail. The raw JSON is not written.

Recovery:

1. Reopen the meeting page in your browser.
2. Click every race link so each full racecard expands.
3. Save the page again with File, Save Page As, Webpage, complete.
4. Retry `race-analysis fetch --from-file $saved --course $course --meeting $meeting --date $date`.
5. Continue only after fetch exits 0 and reports the expected race count.

### 3.2 Manual JSON fallback

Use this if `fetch --from-file` cannot parse the saved page before a race-day deadline.

1. Manually source or export racecard JSON in the documented schema.
2. Save it to the canonical raw path, for example `data\raw\ascot-2026-06-16-racecards.json`.
3. Validate it.

```powershell
race-analysis fetch --course $course --meeting $meeting --date $date
```

4. Continue with `score`, `predict`, `report`, `card`, and `scripts\t60_watchdog.py`.

The deprecated `scripts\scrape_sportinglife.deprecated.py` and `scripts\scrape_racingpost.deprecated.py` files are historical references only and must not be used for race-day data capture.

### 3.3 Post-race results

Use manually verified result pages only after the race is complete. Record settlement and P&L separately from model artifacts.

## 4. Artifact Layout and Archive Rules

The current decision is flat with course-prefixed filenames for non-Epsom. `path_for()` is the source of truth. See `docs\data-layout.md` for the full decision table.

## 5. Race-Day Timeline

### T-24h: declarations and raw racecards

Goal: make sure the racecard exists and can be loaded.

```powershell
race-analysis fetch --from-file $saved --course $course --meeting $meeting --date $date
```

If import fails, use the manual JSON fallback in section 3.2. The fallback path for Ascot is `data\raw\ascot-2026-06-16-racecards.json`; replace the course/date for other meetings.

### T-12h: non-runner and declaration sweep

```powershell
python scripts\t60_watchdog.py --course=$course --meeting=$meeting --date=$date
```

If live-runner data is missing, create or refresh `data\enrichment\live-runners-{course}-{date}.json` for non-Epsom or `data\enrichment\live-runners-{date}.json` for Epsom from manually verified declarations.

### T-2h: baseline price snapshot

```powershell
python scripts\morning_odds.py --mode baseline --course=$course --meeting=$meeting --date=$date
```

If Racing Post rate-limits a market check, wait 60 seconds. If you already have enough verified runner data, retry with `--no-rp-scrape`.

### T-60min: watchdog gate

```powershell
python scripts\t60_watchdog.py --course=$course --meeting=$meeting --date=$date
$LASTEXITCODE
```

Exit handling:

- `0`: proceed.
- `1`: stale artifact; review and refresh before betting.
- `2`: stop. Missing or inconsistent artifacts must be fixed first.

If the gate fails because raw racecards are missing or malformed, re-run `fetch --from-file` from a fresh browser save. If the parser still fails, place manual JSON at the canonical raw path and validate with `race-analysis fetch --course $course --meeting $meeting --date $date`.

### Race morning: rerender after any raw-card repair

```powershell
race-analysis score --course $course --meeting $meeting --date $date
race-analysis predict --course $course --meeting $meeting --date $date --bankroll 100
race-analysis report --course $course --meeting $meeting --date $date
race-analysis card --course $course --meeting $meeting --date $date
python scripts\t60_watchdog.py --course=$course --meeting=$meeting --date=$date
```

### T-1h before target races: latest prices

```powershell
python scripts\morning_odds.py --mode latest --course=$course --meeting=$meeting --date=$date
```

### T-30min: final NR check

Run the watchdog again and inspect live-runner consistency. If a selected horse is now NR or VOID, treat affected singles and multiples as void or invalid according to bookmaker rules.

## 6. Manual Live-Odds Fallback

Use this only when automated market sources fail or the operator has a verified bookmaker terminal.

Example `overrides.csv`:

```csv
date,horse,decimal_price,source
2026-06-16,Northbank Verse,4.5,manual-bookmaker
2026-06-16,Mersey Plan,6.0,manual-bookmaker
```

Run latest mode with the CSV:

```powershell
python scripts\morning_odds.py --mode latest --course=$course --meeting=$meeting --date=$date --prices overrides.csv --no-rp-scrape
```

Regenerate model artifacts with the Race morning commands in section 5.

## 7. T-60 Watchdog Requirements

The watchdog validates presence, freshness, and consistency. It writes `outputs\t60-status-{date}.json`.

Required artifact families:

- Raw racecard
- Live-runners enrichment
- Sporting Life enrichment or explicit not_available source flag
- Racing Post enrichment or explicit not_available source flag
- Going enrichment
- Scores JSON
- Bets JSON
- Report HTML
- Racecard HTML
- Plain-text slip
- Environment check when required by the selected scripts

Bets schema requirements remain unchanged from v0.4.1: top-level `meta`, current `entries`, matching stake totals, and a generated slip must exist before publishing.

## 8. Sanity Checks Before Publishing

Runner count:

```powershell
$raw = "data\raw\ascot-2026-06-16-racecards.json"
python -c "import json, sys; data=json.load(open(sys.argv[1], encoding='utf-8')); print(sum(len(r.get('runners', [])) for r in data.get('races', [])))" $raw
```

Bets total:

```powershell
python -c "import json; from pathlib import Path; p=Path('outputs') / 'bets-ascot-2026-06-16.json'; bets=json.loads(p.read_text()); print('meta GBP', bets.get('meta', {}).get('total_stake_gbp')); print('summary GBP', bets.get('portfolio_summary', {}).get('total_stake_gbp'))"
```

Open generated HTML:

```powershell
Start-Process .\outputs\report-ascot-2026-06-16.html
Start-Process .\outputs\racecard-ascot-2026-06-16.html
```

## 9. Troubleshooting

### `fetch --from-file` rejects the saved page

Cause: wrong file, browser saved an error shell, parser schema drift, missing mandatory race/runner fields, or partial import because not every race was expanded before save.

Fix:

```powershell
race-analysis fetch --from-file $saved --course $course --meeting $meeting --date $date
```

If stderr says `Partial import detected`, reopen the meeting page, click every race link to expand every full racecard, re-save the page, and retry fetch. If it still fails near deadline, use the manual JSON fallback in section 3.2. The fetch command must not delete an existing raw file on failure.

### Raw card exists but fetch still fails

```powershell
Get-Item .\data\raw\*-$date-racecards.json | Select-Object FullName, Length, LastWriteTime
race-analysis fetch --course $course --meeting $meeting --date $date
```

### HTTP 406 from Racing Post market checks

```powershell
Start-Sleep -Seconds 60
python scripts\morning_odds.py --mode latest --course=$course --meeting=$meeting --date=$date --no-rp-scrape
```

### Credential gate fails

`fetch --from-file` does not read Sporting Life credentials. If another selected script requires them, set `SPORTINGLIFE_USER` and `SPORTINGLIFE_PASS` in the operator environment, then rerun that script.

## 10. Glossary

- WIN: bet that the horse finishes first.
- EW: each-way bet; separate win and place legs.
- Place: horse finishes in the paid places for that race.
- Decimal odds: 3.0 means GBP 3.00 return per GBP 1.00 staked, including stake.
- SP: official starting price.
- NR: non-runner.
- VOID: bet cancelled; stake returned under bookmaker rules.
- Baseline: reference price snapshot, usually morning.
- Latest: current price snapshot.
- Enrichment file: JSON data that augments the raw racecard.
- Model score: 0 to 100 confidence rating.
- Slip: plain-text bookmaker-ready bet list emitted by `predict`.
