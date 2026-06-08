# RUNBOOK: Operator Workflow for Any Course, Meeting, and Date

For: operators and developers who need to fetch race data, score a card, generate bets, produce printable artifacts, and handle race-day failures.

Scope: Windows-first workflow for any configured course/meeting/date. Epsom Derby 2026 is preserved as the historical example. Royal Ascot Day 1 is the current non-Epsom example.

Last updated: 2026-06-08

## 0. Quick Reference: Generic Meeting-Day Checklist

Set these three values first in PowerShell:

```powershell
$course = "{course}"
$meeting = "{meeting}"
$date = "{date}"
```

1. Confirm credentials are present for live odds work.

```powershell
python scripts\check_env.py
```

2. Dry-run the morning odds command before any write.

```powershell
python scripts\morning_odds.py --course=$course --meeting=$meeting --date=$date --dry-run
```

3. Capture or verify source racecards and enrichment.

```powershell
python scripts\scrape_racingpost.py --course=$course --meeting=$meeting --date=$date --dry-run
python scripts\scrape_sportinglife.py --course=$course --meeting=$meeting --date=$date --dry-run
python -m src.cli fetch --course=$course --meeting=$meeting --date=$date
```

4. Score, predict, report, and card.

```powershell
python -m src.cli score --course=$course --meeting=$meeting --date=$date
python -m src.cli predict --course=$course --meeting=$meeting --date=$date --bankroll 100
python -m src.cli report --course=$course --meeting=$meeting --date=$date
python -m src.cli card --course=$course --meeting=$meeting --date=$date
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
- Internet access for Racing Post and Sporting Life checks
- Write access to `data\raw`, `data\enrichment`, `data\results`, and `outputs`
- PowerShell as the primary shell

### 1.2 Credentials

The current credential gate checks Sporting Life credentials, not retired API variable names.

| Variable | Purpose | Missing result |
|---|---|---|
| `SPORTINGLIFE_USER` | Sporting Life authenticated fallback and live-runner hygiene | Live odds mode fails before write |
| `SPORTINGLIFE_PASS` | Sporting Life authenticated fallback and live-runner hygiene | Live odds mode fails before write |

Check them without printing secrets:

```powershell
python -c "import os; print('SPORTINGLIFE_USER set:', bool(os.getenv('SPORTINGLIFE_USER'))); print('SPORTINGLIFE_PASS set:', bool(os.getenv('SPORTINGLIFE_PASS')))"
```

Do not paste credentials into logs, commits, runbook notes, or `.squad` files.

## 2. Worked Examples

### 2.1 Epsom Derby, Saturday 2026-06-06, historical replay

Use this to reproduce the historical Derby Day from archived raw data and legacy Epsom paths.

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

Expected legacy output names include:

- `data\raw\epsom-2026-06-06-racecards.json`
- `outputs\scores-2026-06-06.json`
- `outputs\bets-2026-06-06.json`
- `outputs\report-2026-06-06.html`
- `outputs\racecard-2026-06-06.html`
- `outputs\slip-2026-06-06.txt`
- `outputs\t60-status-2026-06-06.json`

Historical artifacts remain archives. Do not move them into new paths.

### 2.2 Royal Ascot Day 1, Tuesday 2026-06-16

Use this for the current Ascot smoke and operator rehearsal.

```powershell
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
python scripts\t60_watchdog.py --course=$course --meeting=$meeting --date=$date
```

Expected course-prefixed output names include:

- `data\raw\ascot-2026-06-16-racecards.json`
- `data\enrichment\live-runners-ascot-2026-06-16.json`
- `data\enrichment\racingpost-ascot-2026-06-16.json`
- `data\enrichment\sportinglife-ascot-2026-06-16.json`
- `data\enrichment\going-ascot-2026-06-16.json`
- `outputs\scores-ascot-2026-06-16.json`
- `outputs\bets-ascot-2026-06-16.json`
- `outputs\report-ascot-2026-06-16.html`
- `outputs\racecard-ascot-2026-06-16.html`
- `outputs\slip-ascot-2026-06-16.txt`
- `outputs\t60-status-2026-06-16.json`

### 2.3 Generic template

Replace the three placeholders and keep them on every command.

```powershell
$course = "{course}"
$meeting = "{meeting}"
$date = "{date}"

python scripts\morning_odds.py --course=$course --meeting=$meeting --date=$date --dry-run
python -m src.cli fetch --course=$course --meeting=$meeting --date=$date
python -m src.cli score --course=$course --meeting=$meeting --date=$date
python -m src.cli predict --course=$course --meeting=$meeting --date=$date --bankroll 100
python -m src.cli report --course=$course --meeting=$meeting --date=$date
python -m src.cli card --course=$course --meeting=$meeting --date=$date
python scripts\t60_watchdog.py --course=$course --meeting=$meeting --date=$date
```

## 3. Source Pattern and URLs

The code resolves course IDs, course paths, aliases, and meeting days from `config\courses\*.json`. Prefer config-driven commands over hardcoded URLs.

### 3.1 Racing Post racecards

Template:

```text
https://www.racingpost.com/racecards/{course_id}/{course_path}/{date}
```

Examples:

- Epsom: `https://www.racingpost.com/racecards/17/epsom/2026-06-06`
- Ascot: `https://www.racingpost.com/racecards/1/ascot/2026-06-16`

Operator command:

```powershell
python scripts\scrape_racingpost.py --course=$course --meeting=$meeting --date=$date --dry-run
```

Failure modes: HTTP 406 on repeated scrapes, HTTP 404 on wrong date or race ID, or small malformed HTML. Wait 60 seconds before retrying a Racing Post scrape.

### 3.2 Sporting Life racecards

Template:

```text
https://www.sportinglife.com/racing/racecards/{date}/{sportinglife_path}
```

Examples:

- Epsom uses the `epsom-downs` path.
- Ascot uses the `ascot` path.

Operator command:

```powershell
python scripts\scrape_sportinglife.py --course=$course --meeting=$meeting --date=$date --dry-run
```

Failure modes: 373-byte SPA shell, 403, or JavaScript component errors. Treat a small response as a failed data fetch even if HTTP status is 200.

### 3.3 Post-race results

Racing Post result pages are the preferred post-race check when racecard pages are blocked intra-day.

Template:

```text
https://www.racingpost.com/results/{course_id}/{course_path}/{date}/{race_id}/
```

Use results only after the race is complete. Cross-check against Sporting Life if settlement details disagree.

## 4. Artifact Layout and Archive Rules

The current decision is flat with course-prefixed filenames for non-Epsom. `path_for()` is the source of truth.

- Epsom keeps legacy archive names for generated outputs, for example `outputs\report-2026-06-06.html`.
- Non-Epsom uses course-prefixed names, for example `outputs\report-ascot-2026-06-16.html`.
- Raw racecards are flat and course-prefixed, for example `data\raw\epsom-2026-06-06-racecards.json` and `data\raw\ascot-2026-06-16-racecards.json`.
- Historical Epsom artifacts are archives. Never re-emit them under nested or newly prefixed paths.

See `docs\data-layout.md` for the full decision table.

## 5. Race-Day Timeline

### T-24h: declarations and raw racecards

Goal: make sure the racecard exists and can be loaded.

```powershell
python -m src.cli fetch --course=$course --meeting=$meeting --date=$date
```

If the raw file is missing, restore the expected raw artifact or run the scraper workflow for that configured course.

### T-12h: non-runner and declaration sweep

Goal: identify horses present in stale raw data but absent from current declarations.

```powershell
python scripts\t60_watchdog.py --course=$course --meeting=$meeting --date=$date
```

If live-runner data is missing, create or refresh `data\enrichment\live-runners-{course}-{date}.json` for non-Epsom or `data\enrichment\live-runners-{date}.json` for Epsom.

### T-2h: baseline price snapshot

Goal: lock the reference market.

```powershell
python scripts\morning_odds.py --mode baseline --course=$course --meeting=$meeting --date=$date
```

If Racing Post rate-limits you, wait 60 seconds. If you already have enough verified runner data, retry with `--no-rp-scrape`.

### T-60min: watchdog gate

Goal: do not proceed with missing or inconsistent artifacts.

```powershell
python scripts\t60_watchdog.py --course=$course --meeting=$meeting --date=$date
$LASTEXITCODE
```

Exit handling:

- `0`: proceed.
- `1`: stale artifact; review and refresh before betting.
- `2`: stop. Missing or inconsistent artifacts must be fixed first.

### T-1h before target races: latest prices

Goal: capture live moves from baseline to latest.

```powershell
python scripts\morning_odds.py --mode latest --course=$course --meeting=$meeting --date=$date
```

### T-30min: final NR check

Run the watchdog again and inspect live-runner consistency. If a selected horse is now NR or VOID, treat affected singles and multiples as void or invalid according to bookmaker rules.

### Post-race: results capture and settlement

Use Racing Post results first, then cross-check with Sporting Life if needed. Record settlement and P&L separately from model artifacts.

### End of day: archive market files

```powershell
python scripts\morning_odds.py --mode archive --course=$course --meeting=$meeting --date=$date
```

## 6. Manual Live-Odds Fallback

Use this only when automated sources fail or the operator has a verified bookmaker terminal.

### Step 1: create a CSV override

Example `overrides.csv`:

```csv
date,horse,decimal_price,source
2026-06-16,Northbank Verse,4.5,manual-bookmaker
2026-06-16,Mersey Plan,6.0,manual-bookmaker
```

### Step 2: run latest mode with the CSV

```powershell
python scripts\morning_odds.py --mode latest --course=$course --meeting=$meeting --date=$date --prices overrides.csv --no-rp-scrape
```

### Step 3: regenerate model artifacts

```powershell
python -m src.cli score --course=$course --meeting=$meeting --date=$date
python -m src.cli predict --course=$course --meeting=$meeting --date=$date --bankroll 100
python -m src.cli report --course=$course --meeting=$meeting --date=$date
python -m src.cli card --course=$course --meeting=$meeting --date=$date
python scripts\t60_watchdog.py --course=$course --meeting=$meeting --date=$date
```

Do not publish if horse names failed to match, prices are incomplete, or a selected horse is not live.

## 7. T-60 Watchdog Requirements

The watchdog validates presence, freshness, and consistency. It writes `outputs\t60-status-{date}.json`.

Required artifact families:

- Raw racecard
- Live-runners enrichment
- Sporting Life enrichment
- Racing Post enrichment
- Going enrichment
- Scores JSON
- Bets JSON
- Report HTML
- Racecard HTML
- Plain-text slip
- Environment check

Bets schema requirements:

- Top-level `meta` object is required for current render-header consistency.
- `meta` should include `schema_version`, `course`, `course_slug`, `meeting`, `meeting_slug`, `date`, `card_date`, `generated_at`, `bankroll`, `total_stake`, and `total_stake_gbp`.
- Top-level `entries` should include one row per rendered recommendation or pass, with `race_id`, `race_time`, `race_name`, `course`, `pick`, `status`, `bet_type`, `stake_guidance`, `odds_decimal`, and `rationale_short` where available.
- `portfolio_summary.total_stake_gbp` and `meta.total_stake_gbp` must match the computed active stake.
- `outputs\slip-{course}-{date}.txt` for non-Epsom, or `outputs\slip-{date}.txt` for Epsom, must exist and include active bet horses and stakes.
- The racecard header must show the same GBP total as the computed bets total.

If the watchdog says `missing meta block`, regenerate bets with current `python -m src.cli predict ...`. If it says `missing slip`, regenerate with the same predict command. If it says header total mismatch, regenerate the card after regenerating bets.

## 8. Sanity Checks Before Publishing

### 8.1 Runner counts

```powershell
$raw = "data\raw\ascot-2026-06-16-racecards.json"
python -c "import json, sys; data=json.load(open(sys.argv[1], encoding='utf-8')); print(sum(len(r.get('runners', [])) for r in data.get('races', [])))" $raw
```

For reusable checks, prefer a short script over shell pipes. Do not use POSIX-only shell snippets on Windows; use PowerShell commands or Python snippets like the examples above.

### 8.2 Raw runner names support both keys

Raw fixtures may use either `horse` or `horse_name`. Use this PowerShell-safe Python snippet:

```powershell
python -c "import json; from pathlib import Path; p=Path('data/raw') / 'ascot-2026-06-16-racecards.json'; card=json.loads(p.read_text()); names=[runner.get('horse') or runner.get('horse_name') for race in card.get('races', []) for runner in race.get('runners', [])]; print([n for n in names if n][:10])"
```

### 8.3 Bets total

```powershell
python -c "import json; from pathlib import Path; p=Path('outputs') / 'bets-ascot-2026-06-16.json'; bets=json.loads(p.read_text()); print('meta GBP', bets.get('meta', {}).get('total_stake_gbp')); print('summary GBP', bets.get('portfolio_summary', {}).get('total_stake_gbp'))"
```

### 8.4 Open generated HTML

```powershell
Start-Process .\outputs\report-ascot-2026-06-16.html
Start-Process .\outputs\racecard-ascot-2026-06-16.html
```

## 9. Troubleshooting

### HTTP 406 from Racing Post

Cause: repeated Racing Post calls too close together.

Fix:

```powershell
Start-Sleep -Seconds 60
python scripts\morning_odds.py --mode latest --course=$course --meeting=$meeting --date=$date --no-rp-scrape
```

### Sporting Life response is around 373 bytes

Cause: SPA shell or blocked content, not usable runner data.

Fix: verify course/date, retry later, use Racing Post if available, or use the manual CSV fallback.

### Credential gate fails

Diagnosis:

```powershell
python scripts\check_env.py
```

Fix: set `SPORTINGLIFE_USER` and `SPORTINGLIFE_PASS` in the operator environment, then rerun live mode. `--dry-run` is allowed to run without those credentials.

### Stale market file

Diagnosis:

```powershell
Get-Item .\data\enrichment\market-latest.json | Select-Object FullName, LastWriteTime, Length
```

Fix:

```powershell
python scripts\morning_odds.py --mode latest --course=$course --meeting=$meeting --date=$date
```

For non-Epsom, the files are course-prefixed, for example `market-latest-ascot.json`.

### Racecard shows wrong total or stale header

Fix:

```powershell
python -m src.cli predict --course=$course --meeting=$meeting --date=$date --bankroll 100
python -m src.cli card --course=$course --meeting=$meeting --date=$date
python scripts\t60_watchdog.py --course=$course --meeting=$meeting --date=$date
```

### Horse appears in raw racecard but not live-runners

Use a snippet that supports both raw keys:

```powershell
python -c "import json; raw=json.load(open('data/raw/ascot-2026-06-16-racecards.json', encoding='utf-8')); live=json.load(open('data/enrichment/live-runners-ascot-2026-06-16.json', encoding='utf-8')); raw_names={x.get('horse') or x.get('horse_name') for r in raw.get('races', []) for x in r.get('runners', [])}; live_names=set(live.get('runners', [])); print(sorted(n for n in raw_names - live_names if n))"
```

If a bet horse is missing from live-runners, verify manually before placing any related bet.

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
- Drift: price lengthens.
- Steam: price shortens.
- Enrichment file: JSON data that augments the raw racecard.
- Model score: 0 to 100 confidence rating.
- Slip: plain-text bookmaker-ready bet list emitted by `predict`.
