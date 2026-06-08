# Skill: morning-odds-gate

## Purpose

Run the morning and pre-race odds gate for a configured `{course}`, `{meeting}`, and `{date}`. The gate captures baseline/latest market snapshots, verifies declarations, records going context, and reports whether any stake or rendered card needs action before publish.

## When to use

- At the morning baseline window for a race day.
- About one hour before a target race or group-race sequence.
- After any manual price CSV is prepared.
- Before T-60 watchdog sign-off if market freshness is in doubt.

## Canonical files

Validate paths against `docs\data-layout.md` and `src.course_config.path_for()`. Current code writes market snapshots under `data\enrichment`, not nested output folders.

| Artifact | Epsom legacy path | Non-Epsom path |
|---|---|---|
| Baseline market | `data\enrichment\market-baseline.json` | `data\enrichment\market-baseline-{course}.json` |
| Latest market | `data\enrichment\market-latest.json` | `data\enrichment\market-latest-{course}.json` |
| Raw racecards | `data\raw\epsom-{date}-racecards.json` | `data\raw\{course}-{date}-racecards.json` |
| Archive baseline | `data\enrichment\archive\market-baseline-{date}.json` | `data\enrichment\archive\market-baseline-{course}-{date}.json` |
| Archive latest | `data\enrichment\archive\market-latest-{date}-final.json` | `data\enrichment\archive\market-latest-{course}-{date}-final.json` |

## Step sequence

### 1. Set context

```powershell
$course = "{course}"
$meeting = "{meeting}"
$date = "{date}"
```

Read `.squad\agents\livingston\history.md`, `.squad\decisions.md`, `RUNBOOK.md`, and `docs\data-layout.md`.

### 2. Verify environment

```powershell
python scripts\check_env.py
```

`SPORTINGLIFE_USER` and `SPORTINGLIFE_PASS` are required for live mode. Dry-run commands may be used before credentials are set.

### 3. Dry-run first

```powershell
python scripts\morning_odds.py --mode baseline --course=$course --meeting=$meeting --date=$date --dry-run
```

Confirm the command resolves the intended course, meeting, date, and raw racecard path.

### 4. Capture baseline

```powershell
python scripts\morning_odds.py --mode baseline --course=$course --meeting=$meeting --date=$date
```

Expected checks: exit code 0, plausible runner count, no surprising non-runner exclusions, and current baseline timestamp.

### 5. Capture latest

If Racing Post was just scraped, either wait 60 seconds or avoid a second RP scrape.

```powershell
Start-Sleep -Seconds 60
python scripts\morning_odds.py --mode latest --course=$course --meeting=$meeting --date=$date
```

or:

```powershell
python scripts\morning_odds.py --mode latest --course=$course --meeting=$meeting --date=$date --no-rp-scrape
```

### 6. Verify files

For Epsom:

```powershell
(Get-Content data\enrichment\market-baseline.json | ConvertFrom-Json).generated
(Get-Content data\enrichment\market-latest.json | ConvertFrom-Json).generated
```

For non-Epsom:

```powershell
(Get-Content data\enrichment\market-baseline-$course.json | ConvertFrom-Json).generated
(Get-Content data\enrichment\market-latest-$course.json | ConvertFrom-Json).generated
```

### 7. Declaration and going checks

Use course-specific search terms and configured course metadata. Do not hardcode Epsom, Oaks, or Derby.

```text
"{course_display}" "{date}" runners declarations
"{course_display}" "{date}" going ground
"{race_name}" "{date}" confirmed runners
```

Compare raw racecard runners, baseline runners, latest runners, live declaration source, and current going.

### 8. Stake position checks

For each active stake in the bets file, verify the horse is live, compare baseline/latest price when available, flag material moves, flag stale source dates, and flag any probable non-runner.

### 9. Report format

```text
Morning odds gate completed at HH:MM local
Scope: {course} / {meeting} / {date}
Snapshots: baseline=[path], latest=[path]
Runner freshness: [N verified, M possible non-runners, K data gaps]
Going: [current source] vs [raw/card value]
Stake checks: [stable / needs action]
Next gate: [time and command]
```

Write the decision note to:

```text
.squad\decisions\inbox\livingston-morning-odds-{course}-{date}.md
```

Append the learning to `.squad\agents\livingston\history.md` when new source behavior or market risk is discovered.

## Worked historical example: Epsom Derby weekend

The original 2026-06-05 and 2026-06-06 gates used Epsom legacy files: `market-baseline.json`, `market-latest.json`, and `data\raw\epsom-{date}-racecards.json`. The reusable lesson is not the venue; it is the sequence: dry-run, baseline, latest, declaration check, going check, stake check, then history/decision write.

## Known quirks

| Issue | Mitigation |
|---|---|
| Racing Post HTTP 406 on repeated fetch | Wait 60 seconds or use `--no-rp-scrape` for latest |
| Live odds absent from RP static HTML | Treat RP as runner confirmation unless prices are explicitly present |
| Synthetic prices unchanged between baseline and latest | Record market_move as neutral and label prices stale |
| Missing credentials | Run `python scripts\check_env.py`; set `SPORTINGLIFE_USER` and `SPORTINGLIFE_PASS` |
| Late entries missing from raw card | Escalate as data gap; do not score from guessed data |
