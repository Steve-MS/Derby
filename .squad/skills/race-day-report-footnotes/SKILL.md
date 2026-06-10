# Skill: race-day-report-footnotes

## Purpose

Add late-runner warnings, withdrawal notices, and market-move badges to generated race-day HTML artifacts without regenerating the full report from source data.

## When to use

- A live gate identifies a horse declared after the data pull.
- A named stake horse is withdrawn and a refund is due.
- A horse's odds have moved significantly since the stake was placed.
- Steve already reviewed the card and you need factual updates without touching picks.

## Scope and paths

Set scope first.

```powershell
$course = "{course}"
$meeting = "{meeting}"
$date = "{date}"
```

Target files:

- Epsom legacy report: `outputs\report-{date}.html`
- Non-Epsom report: `outputs\report-{course}-{date}.html`
- Epsom legacy racecard: `outputs\racecard-{date}.html`
- Non-Epsom racecard: `outputs\racecard-{course}-{date}.html`

## Step sequence

### 1. Read context

- `.squad\agents\linus\history.md` for prior footnotes.
- `.squad\decisions.md` for today's date, `WITHDRAWN`, `declared`, `market move`, `steam`, `drift`, `non-runner`, and `unscored`.
- `.squad\log\` or inbox gate notes from Livingston.

### 2. Locate target HTML files

```powershell
Get-ChildItem .\outputs\ | Where-Object { $_.Name -like "*${course}*${date}*" -or $_.Name -like "*${date}*" } | Select-Object Name, Length, LastWriteTime
```

Confirm you have the intended course and date before editing.

### 3. Find the target race section

Use generic anchors: time, exact race name, horse name, or runner name. Do not rely on course-specific race names.

Source note: if the warning traces to `fetch --from-file`, cite the browser-saved page or import timestamp. Do not cite deprecated scrape scripts as evidence.

```powershell
Select-String -Path outputs\report-{course}-{date}.html -Pattern "HH:MM|Race Name|Horse Name" | Select-Object LineNumber, Line
```

For Epsom legacy files, drop `{course}-` from the filename.

### 4. Inject race-level warning box

Anchor on the race time plus race name. Insert immediately after the race header and before the runners section.

```html
<!-- RACE-DAY FOOTNOTES - injected YYYY-MM-DD by Linus -->
<div style="margin:0;padding:12px 20px 10px;background:#fef3e2;border-bottom:2px solid #d68910;">
  <div style="display:flex;align-items:flex-start;gap:9px;margin-bottom:10px;">
    <span style="font-size:1.05rem;flex-shrink:0;">Note</span>
    <div>
      <strong style="font-size:.83rem;color:#7d4e00;display:block;margin-bottom:3px;">Field is [N+1], not [N].</strong>
      <p style="font-size:.80rem;color:#5a3a00;line-height:1.55;margin:0;">[Horse] ([Trainer] / [Jockey], around [price]) is declared for this race but absent from our data feed. Treat model picks with awareness that one horse is unscored.</p>
    </div>
  </div>
  <div style="display:flex;align-items:flex-start;gap:9px;">
    <span style="font-size:1.05rem;flex-shrink:0;">Void</span>
    <p style="font-size:.80rem;color:#5a3a00;line-height:1.55;margin:0;"><strong>[Horse] - WITHDRAWN.</strong> Refund due on [BET_TYPE] GBP [STAKE] at [ODDS] from bookmaker.</p>
  </div>
</div>
```

Remove blocks that do not apply. Keep one warning box per race.

### 5. Inject per-runner market-move badge

Find the horse row by exact horse name. Insert the badge inside that runner's table cell after trainer/jockey context.

Steam badge:

```html
<div style="font-size:.69rem;color:#1a4a2e;background:#d4edda;border:1px solid #9bcfab;border-radius:3px;padding:2px 7px;margin-top:4px;display:inline-block;line-height:1.4;">Market move: [OLD] -> [NEW_RANGE]. Stake locked at [OLD]. Bet is live.</div>
```

Drift badge:

```html
<div style="font-size:.69rem;color:#7d1a1a;background:#fde8e8;border:1px solid #f5a0a0;border-radius:3px;padding:2px 7px;margin-top:4px;display:inline-block;line-height:1.4;">Market drift: [OLD] -> [NEW_RANGE]. Review risk before adding stake.</div>
```

### 6. Verify injections

```powershell
Select-String -Path outputs\report-{course}-{date}.html -Pattern "RACE-DAY FOOTNOTES|WITHDRAWN|Market move|Market drift|unscored" | Select-Object LineNumber, Line
```

For the printable racecard, run the same check against `outputs\racecard-{course}-{date}.html` when you touched it.

### 7. Post-task writes

Append to `.squad\agents\linus\history.md` and write or update `.squad\decisions\inbox\linus-late-runner-footnotes-{course}-{date}.md` if the schema or placement changed.

## Rules

| Rule | Detail |
|---|---|
| Never regenerate | Only surgical HTML edits; preserve reviewed picks |
| Never touch scored data | Scores, signals, and recommendations are read-only |
| One warning box per race | Stack late-runner and withdrawal notes inside it |
| Runner badge stays local | Market-move note goes inside the runner cell |
| Inline styles only | No new CSS dependency for a race-day injection |
| Mark every injection | Use `<!-- RACE-DAY FOOTNOTES - injected YYYY-MM-DD by Linus -->` |

## Known gotchas

| Issue | Fix |
|---|---|
| Replacement string is not unique | Anchor on race time plus exact race name |
| Horse row is absent due to withdrawal | Add only a race-level note |
| Odds appear as fractions in one place and decimal elsewhere | Include both if needed, for example `34.0 (33/1)` |
| Multiple withdrawals in one race | Stack one line per horse in the same warning box |

## Files typically touched

- `outputs\report-{course}-{date}.html` or Epsom legacy equivalent.
- `outputs\racecard-{course}-{date}.html` or Epsom legacy equivalent, if the printable artifact needs the same note.
- `.squad\agents\linus\history.md`.
- `.squad\decisions\inbox\linus-late-runner-footnotes-{course}-{date}.md` when schema or placement changes.
