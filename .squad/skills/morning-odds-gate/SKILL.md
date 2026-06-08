# Skill: morning-odds-gate

## Purpose
Run the Friday/Saturday pre-race odds gate for the Epsom Derby weekend race-analysis project.  
Ensures market-baseline.json and market-latest.json are fresh, declarations are verified, and stake positions are sanity-checked before each Group 1.

## When to use
- On receiving a "run the Friday/Saturday AM gate" request
- After any delay to the 07:00 baseline window
- Before any ~1hr pre-race latest snapshot

---

## Step sequence

### 1. Read context
- `.squad/agents/livingston/history.md` — prior findings, known non-runners, data gaps
- `.squad/decisions.md` — entries containing "FRIDAY", "07:00", "morning_odds", "baseline"
- `scripts/morning_odds.py` docstring — operator runbook

### 2. Run baseline
```bash
python scripts/morning_odds.py --mode baseline --date YYYY-MM-DD
```
- Expect: `N runners from racecard files`, RP scrape, non-runner filter, final count
- Check `data/enrichment/market-baseline.json` → `generated` field updated

### 3. Run latest (with RP-scrape guard)
```bash
python scripts/morning_odds.py --mode latest --date YYYY-MM-DD --no-rp-scrape
```
**Known quirk:** RP `/racecards/17/epsom/{date}` returns HTTP 406 if called twice in quick succession (~<60s window). Always use `--no-rp-scrape` for latest, OR wait 90s after baseline. Baseline RP filter is canonical for non-runner detection.

### 4. Verify market files
```powershell
(Get-Content data/enrichment/market-baseline.json | ConvertFrom-Json).generated
(Get-Content data/enrichment/market-latest.json | ConvertFrom-Json).generated
```
Both should show today's date + current time.

### 5. Declarations check
- Web search: `"Epsom Oaks 2026 runners declarations June 5"` (or Derby equivalent)
- Compare declared runners vs racecard runners vs baseline runners
- Flag any horse in racecard but NOT in declarations (probable non-runner)
- Flag any horse in declarations but NOT in racecard (late entry / data gap)
- Check named stakes (Belinus, etc.) against declared field

### 6. Going check
```powershell
($rc = Get-Content data/raw/epsom-YYYY-MM-DD-racecards.json | ConvertFrom-Json).races | Where-Object { $_.name -like "*Oaks*" -or $_.name -like "*Derby*" } | Select-Object name, going
```
- Web search current going: `"Epsom going ground YYYY-MM-DD"`
- Flag if racecard assumed going != official current going

### 7. Stake position checks
For each named stake in `.squad/decisions.md`:
- Find horse in baseline: `$b.horses.PSObject.Properties | Where-Object { $_.Name -like "*HORSENAME*" }`
- Compare baseline price vs live market (web search for current odds)
- Flag if price outside stable window (e.g., `<20` or `>50` decimal for 33/1 starting price)

### 8. Report
Produce summary in the standard gate format:
```
Friday AM Gate completed at HH:MM BST
Market snapshots: baseline/latest refreshed
[Horse]: [IN / WITHDRAWN]
Going: [current vs assumed]
[Stake horse]: [stable / drifted]
Card freshness: [N runners verified, M non-runners]
Next gate: ~1hr before race off
```

### 9. Post-gate writes
- Append to `.squad/agents/livingston/history.md` under `## Learnings`
- Write decision to `.squad/decisions/inbox/livingston-{gate-name}.md`

---

## Known quirks / gotchas

| Issue | Notes |
|-------|-------|
| RP HTTP 406 on --mode latest | Use --no-rp-scrape for latest; baseline is the canonical RP-filtered source |
| Live odds NOT in RP SSR HTML | RP __NEXT_DATA__ gives runner names only; prices come from racecard (2026-06-02 snap) |
| Late declarations missing from racecard | Racecard built 2026-06-02; any horse declared after that date won't appear |
| market_move signal frozen | Both baseline and latest have identical racecard prices; signal always 50 unless CSV overrides provided |
| Belinus | WITHDRAWN from 2026-06-05 Oaks; Steve holds WIN £5 @ 3.5 awaiting bookmaker void |

---

## Files touched
- `data/enrichment/market-baseline.json`
- `data/enrichment/market-latest.json`
- `data/raw/epsom-YYYY-MM-DD-racecards.json` (read-only)
- `.squad/agents/livingston/history.md` (append)
- `.squad/decisions/inbox/livingston-{gate}.md` (create)
