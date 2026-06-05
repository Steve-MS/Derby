# Skill: race-day-report-footnotes

## Purpose
Add late-runner warnings, withdrawal notices, and market-move badges to a generated race card HTML file on race day — without regenerating the full report from source data.

## When to use
- On race day when Livingston's AM gate identifies a horse declared AFTER our data pull (unscored runner)
- When a named stake horse is withdrawn and a refund is due
- When a horse's odds have moved significantly since Steve's stake was placed
- Any time Steve has already reviewed the card and you need to append factual updates without touching the picks

---

## Step sequence

### 1. Read context
- `.squad/agents/linus/history.md` — check for any prior footnotes already applied
- `.squad/decisions.md` — search for today's date, "WITHDRAWN", "declared", "market move", "steam"
- `.squad/log/` — any gate log from Livingston with today's date

### 2. Locate the target HTML file
```powershell
Get-ChildItem C:\Users\stevenn\race-analysis\outputs\ | Where-Object { $_.Name -like "*$(Get-Date -Format yyyy-MM-dd)*" }
```
Typical names: `report-YYYY-MM-DD.html`, `racecard-YYYY-MM-DD.html`

### 3. Find the target race section
Use grep to locate the race by time:
```
Select-String -Path outputs/report-YYYY-MM-DD.html -Pattern "16:00|Oaks|Derby" | Select-Object LineNumber, Line
```

### 4. Inject race-level warning box (late runner + withdrawals)

Find the unique closing `</div>` of the race's `.race-header` block (anchored by race time + race name).

**Insert immediately after the race-header closing `</div>`, before `<div class="runners-section">`:**

```html
<!-- ⚠️ RACE-DAY FOOTNOTES — injected YYYY-MM-DD by Linus -->
<div style="margin:0;padding:12px 20px 10px;background:#fef3e2;border-bottom:2px solid #d68910;">

  <!-- Late runner -->
  <div style="display:flex;align-items:flex-start;gap:9px;margin-bottom:10px;">
    <span style="font-size:1.05rem;flex-shrink:0;">⚠️</span>
    <div>
      <strong style="font-size:.83rem;color:#7d4e00;display:block;margin-bottom:3px;">Field is [N+1], not [N].</strong>
      <p style="font-size:.80rem;color:#5a3a00;line-height:1.55;margin:0;">"[Horse]" ([Trainer] / [Jockey], ~[X]/1 in the market) is a late entry declared for this race but absent from our data feed. We have no form, no signals, and no score for this runner. Treat any "top pick" with awareness that there is one unscored horse in the field.</p>
    </div>
  </div>

  <!-- Withdrawal -->
  <div style="display:flex;align-items:flex-start;gap:9px;">
    <span style="font-size:1.05rem;flex-shrink:0;">🚫</span>
    <p style="font-size:.80rem;color:#5a3a00;line-height:1.55;margin:0;"><strong>[Horse] — WITHDRAWN.</strong> Refund due on [BET_TYPE] £[STAKE] @ [DECIMAL_ODDS] from bookmaker.</p>
  </div>

</div>
```

Remove items that don't apply. If only one type is present, omit the `margin-bottom:10px` on the last item.

### 5. Inject per-runner market-move badge

Find the target horse's row. The anchor is:
```html
<div class="horse-name">[Horse Name]</div>
<div class="trainer-jockey hide-xs">
```

**Insert a badge div after the trainer-jockey div, before `</td>`:**

```html
<div style="font-size:.69rem;color:#1a4a2e;background:#d4edda;border:1px solid #9bcfab;border-radius:3px;padding:2px 7px;margin-top:4px;display:inline-block;line-height:1.4;">📈 Market move: [OLD] → [NEW_RANGE]. Your stake locked at <strong>[OLD]</strong>. Bet is live.</div>
```

Use 📉 and `background:#fde8e8; border-color:#f5a0a0; color:#7d1a1a` for a drift instead.

### 6. Verify injections
```powershell
Select-String -Path outputs/report-YYYY-MM-DD.html -Pattern "RACE-DAY FOOTNOTES|WITHDRAWN|Market move" | Select-Object LineNumber, Line
```
Confirm all expected lines appear at the right line numbers.

### 7. Post-task writes
- Append to `.squad/agents/linus/history.md` under today's date
- Write schema/decision to `.squad/decisions/inbox/linus-late-runner-footnotes.md` (if schema changed)

---

## Rules

| Rule | Detail |
|------|--------|
| Never regenerate | Only surgical HTML edit — preserve reviewed picks |
| Never touch scored data | Scores, signals, recommendations are read-only |
| One amber box per race | Stack late-runner + withdrawals in the same box |
| Badge at runner level | Market-move note goes inside the runner's `<td>` |
| Inline styles only | No new CSS classes — stays forward-compatible |
| Use HTML comment | Mark every injection with `<!-- ⚠️ RACE-DAY FOOTNOTES -->` |

---

## Known gotchas

| Issue | Fix |
|-------|-----|
| `old_str` not unique if multiple races share same structure | Anchor on race time + race name (both are in the race-header span elements) |
| Horse not in runners table (already absent due to withdrawal) | Add footnote to race-level box only; no runner row needed |
| Odds shown as fractions in table but decimal in footnote | Use both in note: "34.0 (33/1)" for clarity |
| Multiple withdrawals same race | Stack inside the same amber box, one `<div>` per horse |

---

## Files typically touched
- `outputs/report-YYYY-MM-DD.html` (surgical edit)
- `.squad/agents/linus/history.md` (append)
- `.squad/decisions/inbox/linus-late-runner-footnotes.md` (create/update if schema changes)
