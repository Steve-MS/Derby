# Skill: per-race-outsiders

**Owner:** Linus (Reports)
**First used:** 2026-06-05 Ladies Day
**Status:** Active - use on every race day when Steve requests outsider picks per race

## Purpose

Add one outsider pick per race to both the printable racecard and long report. Each outsider is a horse priced roughly 10/1 or longer with at least one positive signal, usually staked at GBP 0.25 EW. The aim is place-market diversification without materially changing day exposure.

## When to apply

Use when Steve asks for outsider picks across a configured `{course}`, `{meeting}`, and `{date}` card. Apply to both artifacts in the same pass.

## Inputs

Read the course-scoped market file:

- Epsom legacy: `data\enrichment\market-latest.json`
- Non-Epsom: `data\enrichment\market-latest-{course}.json`

Also read:

- Epsom legacy report: `outputs\report-{date}.html`
- Non-Epsom report: `outputs\report-{course}-{date}.html`
- Epsom legacy racecard: `outputs\racecard-{date}.html`
- Non-Epsom racecard: `outputs\racecard-{course}-{date}.html`
- Bets JSON for current stake total.

## Step-by-step

### 1. Scan the market file by race

For each race, collect horses with `decimal_odds >= 10.0`. Sort ascending by price, shortest-priced outsider first.

If the market source predates race day or is synthetic, label prices as stale in both artifacts.

### 2. Pick the outsider

Default selection: shortest-priced qualifying horse, because the market has shown at least some support while the price still offers each-way coverage.

If no horse qualifies at roughly 10/1 or longer, write a no-outsider PASS note:

```text
No outsider: field priced [range]; no horse at roughly 10/1 or longer.
```

Borderline case: 9/1 is 10.0 decimal. Include it only if it is the sole horse above the rest of the field's price cluster, and call it borderline.

### 3. Write rationale

Printable racecard, compact:

```text
Outsider: shortest 10/1+ candidate; EW place cover in [N]-runner field.
```

Long report, two or three sentences:

1. Main bet or PASS context.
2. Why this horse is the outsider.
3. Price quality and stale/synthetic note.

### 4. Inject into printable racecard

Insert a single `row-outsider` row immediately after the main bet or pass-rationale row for the race.

```html
<!-- OUTSIDER PICK - injected YYYY-MM-DD by Linus -->
<tr class="row-outsider">
  <td class="col-time">HH:MM</td>
  <td class="col-race">Race Name - outsider</td>
  <td class="col-bet"><span class="bet-tag bet-ew">EW</span></td>
  <td class="col-horse"><strong>HORSE</strong> <span class="inline-price price-stale">~ODDS (stale)</span></td>
  <td class="col-num">DECIMAL</td>
  <td class="col-num">GBP 0.25 EW</td>
  <td class="col-num">-</td>
  <td class="col-note">Compact rationale.</td>
</tr>
```

For no-pick races, use a PASS row and a short reason.

### 5. Inject into long report

Insert a `<div class="outsider-pick">` block after the race's `<div class="race-bets">` block and inside the same race section.

```html
<!-- OUTSIDER PICK - injected YYYY-MM-DD by Linus -->
<div class="outsider-pick">
  <div class="outsider-pick-header">
    <span>Outsider Pick</span>
    <h4>HORSE_NAME</h4>
  </div>
  <div class="outsider-meta">
    <span><b>Price:</b> ~ODDS (DECIMAL decimal) <span class="odds-source-badge">stale</span></span>
    <span><b>Stake:</b> GBP 0.25 EW</span>
    <span><b>Source:</b> market-latest-{course}.json ([source])</span>
  </div>
  <p class="outsider-rationale">Rationale.</p>
</div>
```

For no-pick races, keep the same block shape but title it `No Outsider Pick` and explain why.

### 6. Update stake totals

- Printable racecard header: add GBP 0.50 for each new EW outsider pick.
- Long report portfolio card: update total stake and outsider count.
- Do not alter existing active bets unless Steve asked for a stake change.

### 7. Post-task writes

Append to `.squad\agents\linus\history.md` and write `.squad\decisions\inbox\linus-per-race-outsiders-{course}-{date}.md` with race-by-race picks, stake impact, source paths, and no-pick reasons.

## Notable historical example: Oaks and Derby requirement

On the Epsom 2026 card, the Oaks/Derby outsider requirement had its own active-bet treatment and used a two-row format for an existing special section. That was a historical card-specific rule. For new meetings, use the single-row format above unless the operator explicitly asks for a special active-bet section.

## Page-fit tactics

- Use single-row outsider entries in the printable racecard.
- Keep compact rationale around 40 to 60 characters.
- If the card is already dense, shorten text before changing stake logic.
