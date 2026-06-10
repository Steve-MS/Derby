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

### 2. Verify raw racecard import

For live race days, the raw card should come from `race-analysis fetch --from-file` against a browser-saved page, or from the documented manual JSON fallback.

```powershell
race-analysis fetch --course $course --meeting $meeting --date $date
```

This validation step should pass before market work starts.

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

If an internal Racing Post market check was just attempted, either wait 60 seconds or avoid a second RP call.

```powershell
Start-Sleep -Seconds 60
python scripts\morning_odds.py --mode latest --course=$course --meeting=$meeting --date=$date
```

or:

```powershell
python scripts\morning_odds.py --mode latest --course=$course --meeting=$meeting --date=$date --no-rp-scrape
```

### 6. Declaration and going checks

Compare raw racecard runners, baseline runners, latest runners, live declaration source, and current going. If going is explicitly unavailable from the imported page, ensure the source flag is `not_available` so scoring remains neutral rather than treating it as insufficient history.

### 7. Stake position checks

For each active stake in the bets file, verify the horse is live, compare baseline/latest price when available, flag material moves, flag stale source dates, and flag any probable non-runner.

## Known quirks

| Issue | Mitigation |
|---|---|
| Racing Post HTTP 406 on repeated market check | Wait 60 seconds or use `--no-rp-scrape` for latest |
| Live odds absent from RP static HTML | Treat RP as runner confirmation unless prices are explicitly present |
| Synthetic prices unchanged between baseline and latest | Record market_move as neutral and label prices stale |
| Missing credentials | Run `python scripts\check_env.py`; use browser login for the saved-page workflow |
| Late entries missing from raw card | Re-import a fresh browser save or escalate as data gap; do not score from guessed data |
