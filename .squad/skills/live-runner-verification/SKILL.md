# Skill: live-runner-verification

## Purpose

Verify live declared runners for all remaining races at a meeting, before Rusty scores or Linus renders, to prevent stale non-runners appearing on the printed card.

This skill exists because on 2026-06-05 Ladies Day at Epsom, `market-latest.json` (2026-06-02 vintage) was used as runner-identity source-of-truth. Two horses on the card — Port Road and Triple Double A — were confirmed non-runners, requiring manual emergency swaps. Blue Brother (17:50) was also not in live declarations and would have been backed without this verification pass.

## When to use

- Any time Rusty is about to re-score after a non-runner swap
- Any time Linus is about to render a race card or regenerate the betting slip
- Within 4 hours of race-time for the day's remaining races
- Whenever `market-latest.json` is older than midnight on race day

---

## Step sequence

### 1. Read context

- `data/enrichment/market-latest.json` — `generated` field to check staleness. If `generated` date < race day → STALE, must not trust for runner identity.
- `outputs/racecard-YYYY-MM-DD.html` — note every horse displayed, by race time.
- `.squad/agents/livingston/history.md` — any prior non-runner flags from the AM gate.

### 2. Identify races still to run

Current time (from CURRENT_DATETIME in prompt). Skip any race with `time < current_time_bst`.

### 3. Fetch live runners per race

Try sources in this order, stop at first success per race:

**Source A — Sporting Life (MOST RELIABLE — confirmed working 2026-06-05)**
```
https://www.sportinglife.com/racing/racecards/{YYYY-MM-DD}/epsom-downs/racecard/{race_id}/{race-slug}
```
Race IDs for Epsom 2026-06-05: 920732–920738 (13:30 through 17:50). Race list at:
```
https://www.sportinglife.com/racing/racecards
```
→ Find meeting "Epsom Downs" → copy individual race URLs.

**Source B — Sky Sports Racing**
```
https://www.skysports.com/racing/racecards/epsom-downs/{DD-MM-YYYY}/{race_id}/{race-slug}
```

**Source C — Racing Post**
```
https://www.racingpost.com/racecards/17/epsom/{YYYY-MM-DD}/{race_id}/compact-view/
```
Known quirk: RP returns HTTP 406 if fetched twice within ~60s. Fetch once.

**Source D — web_search fallback**
Query: `"Epsom HH:MM [race name] {date} confirmed runners list"`
Use when direct page fetch returns 403/404/JS-only response.

### 4. Extract confirmed runners

From the live racecard page, note:
- Total declared runner count (shown in header e.g. "18 Runners")
- Cloth numbers listed — any **gap** in cloth sequence = non-runner (withdrawn but cloth reserved)
- For each runner: number, name, jockey, trainer

**Non-runner detection:**
- Sporting Life: cloth numbers with no entry in the runner list = NR (e.g. cloth 3 and 4 absent → NR)
- Racing Post: struck-through horse names or explicit "Non-Runners" block
- Stale data field count vs live count discrepancy (e.g. 29 declared → 18 live = 11 NRs)

### 5. Cross-check against current card

For each remaining race:
- List every horse currently shown in `racecard-YYYY-MM-DD.html`
- Check each against the live runner list
- Flag as **must remove** if not in live field

### 6. Write output files

**Canonical runners file:**
```
data/enrichment/live-runners-YYYY-MM-DD.json
```
Schema:
```json
{
  "fetched_at": "YYYY-MM-DDTHH:MM:SS+01:00",
  "meeting": "Epsom — Ladies Day",
  "races": [
    {
      "time": "16:40",
      "name": "...",
      "source_url": "...",
      "source_name": "Sporting Life",
      "runners": [{"number": 1, "draw": 4, "name": "...", "jockey": "...", "trainer": "...", "price": null}],
      "non_runners_excluded": ["Horse A (reason)", "Horse B (reason)"],
      "status": "verified"
    },
    {
      "time": "17:15",
      "status": "blocked",
      "reason": "web_fetch returned 403 from all sources"
    }
  ]
}
```

**Mismatch report + hard-rule proposal:**
```
.squad/decisions/inbox/livingston-card-vs-live-YYYY-MM-DD.md
```
Include: per-race table (horse | card type | live status | action), source URLs, process post-mortem if this was triggered by a prior NR failure.

### 7. Hand off to Rusty and Linus

- Ping Rusty with: race times that need re-scoring + the `live-runners-YYYY-MM-DD.json` path
- Ping Linus with: horses to remove per race time + confirmed replacements (or `[VACANT — no bet]`)
- If `status: blocked` on any race: tell Steve the exact race time and ask for manual runner paste

---

## Constraints

- Do **NOT** use `market-latest.json` for runner identity — only for historical price estimates
- Do **NOT** guess at runners. If all sources fail → `status: blocked`, report to Steve
- Do **NOT** include races already past (race time < current time)
- Prices from any live source are preferred to stale estimates; if unavailable, set `"price": null`

---

## Known pitfalls

| Pitfall | Mitigation |
|---|---|
| RP 406 on second fetch | Use `--no-rp-scrape` or 90s gap; or use SL as primary |
| SL horse names hidden by JS | Use web_search with race name + date as fallback for names |
| Stale field sizes (29 declared → 18 live) | Always trust live page count, not stale JSON count |
| NR replacement horse also a NR | Re-run live verification on replacement before card update |
| Cloth-number gaps on SL page | Absent cloth numbers = NRs (withdrawn but cloth reserved) |

---

## Source reliability log (2026-06-05)

| Source | Result |
|---|---|
| Racing Post `/racecards/today` | ❌ 404 |
| Racing Post `/racecards/YYYY-MM-DD/epsom` | ❌ 404 |
| Sporting Life `/racing/racecards` (meeting list) | ✅ **WORKS** — returns race list with URLs |
| Sporting Life individual race pages | ✅ **WORKS** — cloth numbers + Timeform descriptions; horse names may need web_search |
| At The Races | ❌ JS-only (browser extension error) |
| web_search (Sky Sports / Timeform / RP via Bing) | ✅ **WORKS** — returns full runner + jockey + trainer lists |

**Recommended path for next run:** `web_search` for each race to get names+jockeys+trainers, then cross-validate count against Sporting Life individual racecard page.

---

## Output file example

See `data/enrichment/live-runners-2026-06-05.json` — first run of this skill.
See `.squad/decisions/inbox/livingston-card-vs-live-2026-06-05.md` — first mismatch report.
