# Skill: per-race-outsiders

**Owner:** Linus (Reports)
**First used:** 2026-06-05 Ladies Day
**Status:** Active — use on every race day when Steve requests outsider picks per race

---

## Purpose

Add one outsider pick per race to both the 1-pager and the long report. Each outsider is a horse priced roughly 10/1 or longer with at least one positive signal, staked at £0.25 EW. Provides place-market diversification alongside the model's main picks without materially affecting day outlay.

---

## When to apply

Any time Steve asks for "an outsider for each race" or "outsider picks across the card." Applies to both artifacts simultaneously (dual-artifact rule).

---

## Step-by-step

### 1. Scan market-latest.json for each race

For each race, collect all horses with `decimal_odds >= 10.0`. Sort ascending by price (shortest first among outsiders). That's your candidate list.

**Price note:** All synthetic / form-estimate prices must be marked `(stale)` if the `source` field contains a date prior to today's race date. Use `<span class="inline-price price-stale">~ODDS (stale)</span>` in both artifacts.

### 2. Pick the outsider

Select the **shortest-priced qualifying horse** (most market-backed among the outsiders). Rationale: the market has marginally endorsed it at a long price. One pick per race.

**If no horse qualifies at 10/1+:** Write a "no outsider" entry with a 1-line reason:
> "⛔ [Race type] field priced [range]; no horse at 10/1+."

**Borderline case (9/1 = 10.0 decimal):** Include if it is the sole horse clearly above the rest of the field's price cluster, and note it as borderline. The "roughly 10/1" wording gives this flexibility.

### 3. Write the rationale

**1-pager (compact, ~60 chars, in col-note column):**
- Picks: `⚡ [Why: market position + field-size EW maths]`
- No-pick: `⛔ [Field range + why nothing qualifies]`

**Long report (2-3 sentences):**
1. Context: who the main bet is (if any) and field size
2. Why this horse: market position, EW place-term maths for the field size
3. Note on price quality: "stale synthetic" / borderline threshold / etc.

**EW place-term reference:**
| Field size | Typical EW places | Place odds (1/4) |
|------------|-------------------|-----------------|
| 5–7 | 2 | price ÷ 4 |
| 8–11 | 3 | price ÷ 4 |
| 12–15 | 3 | price ÷ 4 |
| 16+ | 4 | price ÷ 4 |
| 20+ | 5 | price ÷ 4 |
| 25+ | 6 | price ÷ 4 |

### 4. Inject into the 1-pager (surgical, single-row)

Insert a `row-outsider` TR **immediately after** the main bet / pass rationale row for each race:

```html
<!-- ⚡ PER-RACE OUTSIDER — injected YYYY-MM-DD by Linus -->
<tr class="row-outsider">
  <td class="col-time">HH:MM</td>
  <td class="col-race">Race Name ⚡</td>
  <td class="col-bet"><span class="bet-tag bet-ew">EW</span></td>
  <td class="col-horse"><strong>HORSE</strong> <span class="inline-price price-stale">~ODDS (stale)</span></td>
  <td class="col-num">DECIMAL</td>
  <td class="col-num">£0.25 EW</td>
  <td class="col-num">—</td>
  <td class="col-note">⚡ COMPACT RATIONALE (~60 chars).</td>
</tr>
```

For a **no-pick** race, use `row-pass` class and `<span class="bet-tag bet-pass">PASS</span>`:
```html
<tr class="row-pass">
  <td class="col-time">HH:MM</td>
  <td class="col-race">Race Name</td>
  <td class="col-bet"><span class="bet-tag bet-pass">PASS</span></td>
  <td class="col-horse">— no outsider —</td>
  <td class="col-num">—</td><td class="col-num">—</td><td class="col-num">—</td>
  <td class="col-note">⛔ REASON.</td>
</tr>
```

**CSS:** `row-outsider` is already in the 1-pager stylesheet. No new CSS needed.

### 5. Inject into the long report (surgical, div block)

Insert a `<div class="outsider-pick">` block AFTER the closing `</div>` of `<div class="race-bets">`, INSIDE the `<section class="race-block">`:

```html
<!-- ⚡ OUTSIDER PICK — injected YYYY-MM-DD by Linus -->
<div class="outsider-pick">
  <div class="outsider-pick-header">
    <span>⚡</span>
    <h4>Outsider Pick: HORSE_NAME</h4>
  </div>
  <div class="outsider-meta">
    <span><b>Price:</b> ~ODDS (DECIMAL decimal) <span class="odds-source-badge">stale</span></span>
    <span><b>Stake:</b> £0.25 EW</span>
    <span><b>Source:</b> market-latest.json (YYYY-MM-DD synthetic)</span>
  </div>
  <p class="outsider-rationale">⚡ RATIONALE (2-3 sentences).</p>
</div>
```

For a **no-pick** race, use muted inline styles:
```html
<div class="outsider-pick" style="background:#f5f5f5; border-color:#bbb; border-left-color:#999;">
  <div class="outsider-pick-header">
    <span>⛔</span>
    <h4>No Outsider Pick — RACE_NAME</h4>
  </div>
  <p class="outsider-rationale">⛔ REASON (2-3 sentences, field pricing context).</p>
</div>
```

**CSS:** `.outsider-pick`, `.outsider-pick-header`, `.outsider-meta`, `.outsider-rationale` are already in the long report stylesheet. No new CSS needed.

### 6. Update stake totals

- **1-pager header:** `Total outlay` and `Bets` count
  - New total = old total + (N_new_picks × £0.50)
  - New bets = old bets + N_new_picks (each EW = 1 bet in this system)
- **Long report portfolio card:**
  - "Total Stake" card: update £ value
  - "Outsiders" card: update pick count and total stake line

### 7. Post-task writes

- Append to `.squad/agents/linus/history.md` under today's date
- Write `.squad/decisions/inbox/linus-per-race-outsiders.md` (race-by-race table, stake impact, sources, no-pick reasons)

---

## Page-fit tactics (1-pager)

- Use **single-row format** for all new outsider rows (rationale in col-note column, not a second TR)
- This adds 1 row per race vs 2 rows for the Prizeland-style 2-row format
- 8 new rows ≈ 35–40mm at print font size — well within A4 headroom
- If the card has unusually many bets already, consider shortening col-note rationale to 40 chars

## Existing outsider handling (Oaks / Derby requirement)

The Oaks outsider (required by charter: "Outsider pick required for the Derby itself") uses the 2-row Prizeland format in the active bets section. Do NOT convert it to the single-row format — it has its own section. For other races, use single-row.

---

## Example output (1-pager row)

```html
<tr class="row-outsider">
  <td class="col-time">13:30</td>
  <td class="col-race">3yo Dash Handicap ⚡</td>
  <td class="col-bet"><span class="bet-tag bet-ew">EW</span></td>
  <td class="col-horse"><strong>Rosie Frith</strong> <span class="inline-price price-stale">~11/1 (stale)</span></td>
  <td class="col-num">12.5</td>
  <td class="col-num">£0.25 EW</td>
  <td class="col-num">—</td>
  <td class="col-note">⚡ Shortest outsider in 18-runner sprint — EW place cover at 11/1.</td>
</tr>
```

## Example output (long report block)

```html
<div class="outsider-pick">
  <div class="outsider-pick-header">
    <span>⚡</span>
    <h4>Outsider Pick: Rosie Frith</h4>
  </div>
  <div class="outsider-meta">
    <span><b>Price:</b> ~11/1 (12.5 decimal) <span class="odds-source-badge">stale</span></span>
    <span><b>Stake:</b> £0.25 EW</span>
    <span><b>Source:</b> market-latest.json (2026-06-02 synthetic)</span>
  </div>
  <p class="outsider-rationale">⚡ 18-runner sprint handicap; main pick passed on LOW confidence.
  Rosie Frith at 11/1 is the market's shortest outsider, implying a degree of support.
  In a big-field sprint with 3-place EW terms, 11/1 provides worthwhile place coverage.</p>
</div>
```
