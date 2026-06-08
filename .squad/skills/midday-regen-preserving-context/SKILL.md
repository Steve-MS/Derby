# Skill: midday-regen-preserving-context

**Owner:** Linus (Reports)
**First used:** 2026-06-05 Ladies Day, 12:05 BST midday refresh
**Status:** Active - use on every race day when market refresh happens after manual annotations were added

## Purpose

Refresh both HTML artifacts after a midday or afternoon market update without losing in-day manual annotations. Annotations can include footnotes, pass rationale, outsider picks, placed-bet notes, withdrawal notes, non-runner warnings, and manual stake context.

## When to apply

Use when Livingston reports a refreshed market or live-runner update and asks for regenerated artifacts for a configured `{course}`, `{meeting}`, and `{date}`.

## Paths

Use `docs\data-layout.md` and `path_for()` for exact paths.

| Artifact | Epsom legacy path | Non-Epsom path |
|---|---|---|
| Long report | `outputs\report-{date}.html` | `outputs\report-{course}-{date}.html` |
| Printable racecard | `outputs\racecard-{date}.html` | `outputs\racecard-{course}-{date}.html` |
| Bets | `outputs\bets-{date}.json` | `outputs\bets-{course}-{date}.json` |
| Latest market | `data\enrichment\market-latest.json` | `data\enrichment\market-latest-{course}.json` |

## Step 1: triage Option B vs Option A

Read Livingston's refresh report and answer these questions.

| Question | Option B: timestamp/context edit | Option A: full regen plus port |
|---|---|---|
| Any price move over 20 percent on a staked horse? | No | Yes |
| Any new non-runners since the morning gate? | No | Yes |
| Any new runners or late entries? | No | Yes |
| Prices remain stale/synthetic? | Yes | No |

Use Option B if all answers are in the Option B column. Use Option A if any answer lands in the Option A column.

## Option B: surgical timestamp/context edit

1. Read current timestamps.

```powershell
Get-Content outputs\racecard-{course}-{date}.html | Select-String -Pattern "Generated"
Get-Content outputs\report-{course}-{date}.html | Select-String -Pattern "Generated"
```

For Epsom legacy files, drop `{course}-` from the output filename.

2. Update generated text only. Use this ASCII format:

```text
Generated YYYY-MM-DD HH:MM BST - prices stale ([source]), no live-price API - Model v0.4 - For personal use. Please gamble responsibly.
```

3. Verify that only timestamp/context lines changed.

```powershell
Get-Content outputs\racecard-{course}-{date}.html | Select-String "Generated"
Get-Content outputs\report-{course}-{date}.html | Select-String "Generated"
```

## Option A: full regen plus annotation port

Do not run this without a complete annotation inventory.

### 1. Build a generic annotation inventory

Search both artifacts and record line numbers plus snippets for each category.

```powershell
$report = "outputs\report-{course}-{date}.html"
$card = "outputs\racecard-{course}-{date}.html"

Get-Content $report | Select-String "RACE-DAY FOOTNOTES|footnote|WITHDRAWN|non-runner|unscored|market move" | Select-Object LineNumber, Line
Get-Content $report | Select-String 'class="outsider-pick"|Outsider Pick|No Outsider' | Select-Object LineNumber, Line
Get-Content $report | Select-String 'class="pass-rationale"|class="pick-rationale"' | Select-Object LineNumber, Line
Get-Content $card | Select-String "row-outsider|row-rationale|RACE-DAY FOOTNOTES|WITHDRAWN|non-runner|market move" | Select-Object LineNumber, Line
```

Record the inventory in the task response or decision note before regeneration.

### 2. Regenerate with current CLI commands

```powershell
python -m src.cli score --course=$course --meeting=$meeting --date=$date
python -m src.cli predict --course=$course --meeting=$meeting --date=$date --bankroll 100
python -m src.cli report --course=$course --meeting=$meeting --date=$date
python -m src.cli card --course=$course --meeting=$meeting --date=$date
```

### 3. Port annotations

Use these skills as the insertion guides:

- `.squad\skills\race-day-report-footnotes\SKILL.md`
- `.squad\skills\per-race-outsiders\SKILL.md`
- `.squad\skills\bet-pass-rationale\SKILL.md`

Port every inventory item. If an annotation no longer applies because the horse is a non-runner or the race moved to PASS, state that in the decision note.

## Verification checklist

After either option:

- [ ] Both artifacts have current generated text.
- [ ] Active bets match the bets JSON.
- [ ] Pass and pick rationale are present for every race.
- [ ] Outsider picks are present where requested.
- [ ] Race-day footnotes and non-runner notes are preserved or explicitly retired.
- [ ] Stale prices keep a stale label.
- [ ] Day total stake is unchanged unless the operator approved a change.
- [ ] T-60 watchdog result is reviewed before publish.

## Historical note: Ladies Day first use

The first use on 2026-06-05 preserved Ladies Day manual annotations, including accumulator context. That accumulator count was specific to that historical card. For future meetings, preserve whatever accumulator or manual-bet inventory exists; do not assume the Ladies Day structure.

## Post-task writes

Append the outcome to `.squad\agents\linus\history.md` and write `.squad\decisions\inbox\linus-midday-regen-{course}-{date}.md` with option chosen, reason, files changed, and checklist outcome.
