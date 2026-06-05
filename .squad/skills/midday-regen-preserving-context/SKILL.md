# Skill: midday-regen-preserving-context

**Owner:** Linus (Reports)  
**First used:** 2026-06-05 Ladies Day (12:05 BST midday refresh)  
**Status:** Active — use on every race day when Livingston delivers a midday market refresh after manual annotations have been added to the HTML artifacts

---

## Purpose

Regenerate the "freshness" claim of both HTML artifacts (updated timestamp, refreshed market data) without losing the in-day manual annotations — footnotes, pass rationale, outsider picks, bets placed, footnotes about withdrawals and non-runners — that Steve and the team built up during the morning.

There are two options depending on how much the data changed. This skill governs which to choose and how to execute each.

---

## When to apply

Any midday or afternoon call from Livingston that says: "I've refreshed the market data — please regenerate the report." Before touching anything, run the Option B / Option A triage below.

---

## Step 1: Triage — Option B vs Option A

Read Livingston's refresh report (typically in the task prompt or in `.squad/log/`). Answer these four questions:

| Question | Option B (timestamp-only) | Option A (full regen + port) |
|---|---|---|
| Any price move >20% on a staked horse? | No | Yes |
| Any new non-runners since morning gate? | No | Yes |
| Any new runners scored since morning gate? | No | Yes |
| Prices remain stale/synthetic? | Yes | No (live prices available) |

**Use Option B if ALL four answers are in the Option B column.** This is the common case for synthetic-price race days (no Betfair API).

**Use Option A if ANY answer is in the Option A column** — i.e. data changed materially.

---

## Option B — Surgical timestamp-only edit

### When: no material data change

1. Read current timestamps in both files:
   ```powershell
   Get-Content outputs\racecard-YYYY-MM-DD.html | Select-String -Pattern "Generated"
   Get-Content outputs\report-YYYY-MM-DD.html   | Select-String -Pattern "Generated"
   ```

2. Edit the footer disclaimer in the 1-pager:
   - Old: `Generated YYYY-MM-DDT<old-time> · Model v0.1 · Odds snapshot: ... · For personal use.`
   - New: `Generated YYYY-MM-DD HH:MM BST — prices stale (YYYY-MM-DD synthetic basis), no Betfair API · Model v0.1 · For personal use. Please gamble responsibly.`

3. Edit the header disclaimer in the long report (search for `Generated` near line 740):
   - Old: `Generated YYYY-MM-DDT<old-time> · Race-Analysis Plugin v0.1`
   - New: `Generated YYYY-MM-DD HH:MM BST — prices stale (YYYY-MM-DD synthetic basis), no Betfair API · Race-Analysis Plugin v0.1`

4. Edit the footer block in the long report (search for `Generated` near end of file):
   - Old: `Race Analysis Plugin v0.1 · Generated YYYY-MM-DDT<old-time><br><span class="odds-snapshot">...</span><br>`
   - New: `Race Analysis Plugin v0.1 · Generated YYYY-MM-DD HH:MM BST — prices stale (YYYY-MM-DD synthetic basis), no Betfair API<br>`
   - Note: remove `<span class="odds-snapshot">` when there is no live snapshot.

5. Verify with grep:
   ```powershell
   Get-Content outputs\racecard-YYYY-MM-DD.html | Select-String "Generated"
   Get-Content outputs\report-YYYY-MM-DD.html   | Select-String "Generated"
   ```

### Timestamp format

```
Generated YYYY-MM-DD HH:MM BST — prices stale (YYYY-MM-DD synthetic basis), no Betfair API
```

Where the second date is the synthetic-price source date (from Livingston's `source` field in market-latest.json — typically "Synthetic from OR/field-size (YYYY-MM-DD)").

---

## Option A — Full regen + annotation port

### When: data changed materially (new scores, new prices, non-runner confirmed)

**Do NOT run this without a complete list of all annotations to preserve.**

1. Collect the current annotation inventory from both files:
   ```powershell
   $rp = Get-Content outputs\report-YYYY-MM-DD.html
   # Footnote blocks
   $rp | Select-String "injected \d{4}-\d{2}-\d{2} by Linus" | ForEach-Object { "$($_.LineNumber): $($_.Line)" }
   # Outsider picks
   $rp | Select-String "class=""outsider-pick""" | Measure-Object
   # Pass rationale
   $rp | Select-String "class=""pass-rationale""" | Measure-Object
   ```

2. Run the regeneration:
   ```powershell
   python -m src.report --date YYYY-MM-DD > outputs\report-YYYY-MM-DD-new.html
   python -m src.report --date YYYY-MM-DD --card > outputs\racecard-YYYY-MM-DD-new.html
   ```

3. Port each annotation block from the old file to the new, following the injection patterns in:
   - `.squad/skills/race-day-report-footnotes/SKILL.md` — for footnotes
   - `.squad/skills/per-race-outsiders/SKILL.md` — for outsider picks
   - `.squad/skills/bet-pass-rationale/SKILL.md` — for pass rationale

4. Once ported, replace old with new:
   ```powershell
   Move-Item outputs\report-YYYY-MM-DD-new.html  outputs\report-YYYY-MM-DD.html  -Force
   Move-Item outputs\racecard-YYYY-MM-DD-new.html outputs\racecard-YYYY-MM-DD.html -Force
   ```

5. Run the full verification checklist (see below).

---

## Verification checklist (both options)

After any regen, confirm in both files:

- [ ] Both timestamps read `Generated YYYY-MM-DD HH:MM BST — prices stale (...), no Betfair API`
- [ ] All 5 active bets present (horse names match bets-YYYY-MM-DD.json)
- [ ] All outsider picks present (count matches per-race-outsiders run)
- [ ] All pass rationale rows present
- [ ] All footnotes present (On Message / Belinus / Sugar Island pattern or equivalent)
- [ ] Accumulators present (3 doubles + 1 treble is the Ladies Day standard)
- [ ] Day total stake unchanged (check `£XX.XX` in 1-pager header and report portfolio card)
- [ ] All stale prices retain `(stale)` tag — do NOT drop it

---

## Page-fit note (1-pager)

Option B makes no layout change — no fit check needed.

Option A may change row counts. After a full regen, estimate mm by counting table rows × ~6mm per row (print font ~8pt) and check against ~216mm A4 printable. If the card overflows, shorten col-note rationale strings to ~40 chars.

---

## Post-task writes

1. Append to `.squad/agents/linus/history.md` under today's date
2. Write `.squad/decisions/inbox/linus-midday-regen-YYYY-MM-DD.md` with: option chosen, reason, files changed, checklist outcome
