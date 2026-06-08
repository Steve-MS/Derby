# SKILL: Group 1 Trifecta Box from Scoring Model

**Author:** Linus (Reports)
**Created:** 2026-06-05
**First use:** Derby Day 2026-06-06 (Betfred Derby, Race 5, 16:00 BST)

---

## What this skill does

Takes a race's scored ranking (from `outputs/scores-YYYY-MM-DD.json`) and constructs a trifecta box recommendation: N horses, every permutation of them finishing 1-2-3 in any order.

**Cost formula:** N × (N-1) × (N-2) × stake_per_combo

| Box | Combos | @£1/combo |
|-----|--------|-----------|
| 3   | 6      | £6        |
| 4   | 24     | £24       |
| 5   | 60     | £60       |

---

## When to use

- Steve requests a trifecta box for a specific race.
- Race is a Group 1 or significant Group 2 with a deep, competitive field (≥10 runners).
- The race confidence may be LOW (as is common in the Derby/Oaks) — the trifecta box HEDGES against model uncertainty by covering multiple finish permutations.

---

## Inputs required

1. `outputs/scores-YYYY-MM-DD.json` — scored ranked runners for the race
2. `data/raw/epsom-YYYY-MM-DD-racecards.json` (or equivalent) — for jockey/trainer/draw/notes
3. `data/enrichment/market-latest.json` — for prices (flag as stale if not race-day morning)
4. `outputs/bets-YYYY-MM-DD.json` — to check existing Derby Day outlay and avoid double-counting

---

## Step-by-step procedure

### Step 1: Identify the race
- Find the target race in the racecard JSON by name (e.g. "Betfred Derby") — NOT by race number (numbering may shift from brief).
- Confirm distance, off time, class (Group 1 etc.).
- Note: the Derby at Epsom is 12f (1m4f), off ~16:00 BST.

### Step 2: Extract scored rankings
From `scores-YYYY-MM-DD.json`, for the target race extract:
- `race_name`, `race_time`, `confidence`, `race_stdev`, `race_competitiveness`
- For each runner: `rank`, `horse`, `trainer`, `jockey`, `score`, `raw_signal_values` (key signals: trial_form, market_move, going_fit, sire_stamina, recent_form, pace), `morning_price`

### Step 3: Determine box size

**Gap analysis:** Calculate score gaps between adjacent ranked runners.
- gap(N→N+1) = score[N] - score[N+1]

**Decision tree:**
- `3-horse box`: top-3 cluster AND gap(3→4) > 1 × race_stdev AND confidence HIGH/MED
- `4-horse box` (DEFAULT): gap(3→4) < 1 sigma OR confidence LOW. Use this for most Group 1 races.
- `5-horse box`: race_stdev very high AND race_competitiveness = "COMPETITIVE" AND no visible top-3 cluster. Flag as "wide net, low conviction".

For the Derby Day 2026 example:
- Stdev = 25.23, gap(3→4) = 5.5 pts = 0.22 sigma, confidence = LOW → 4-horse box ✓

### Step 4: Select horses

- Take the top N ranked runners by composite score.
- Check: does one of the box horses serve as the outsider (≥14/1 stale price, model rank notably higher than market rank)? If yes, note it satisfies the standing Derby outsider rule.
- Check `bets-YYYY-MM-DD.json` outsiders section to see if the long-shot is already an outsider pick.
- If a horse in top-4 has a special concern (e.g., 6-day turnaround from overseas trial, going_fit collapse risk), consider swapping for rank #5.

### Step 5: Size the stake

Target total outlay: **£15–35** for a trifecta box on a Group 1, sitting alongside the rest of the day's bets.

Standard stakes:
- 3-box: £2.50/combo → £15 total
- 4-box: £1.00/combo → £24 total ← Derby Day standard
- 5-box: £0.50/combo → £30 total

Check existing `portfolio_summary.total_stake_gbp` in bets JSON. The trifecta box is additive. Total day including the box must stay ≤ £100.

### Step 6: Write the rationale

For each horse, one line covering the strongest 2-3 signals. Priority signals for a 12f+ Classic:
- trial_form (Tier 1/2 win = key differentiator)
- market_move (steam = smart money)
- going_fit (Epsom round course is specific)
- sire_stamina (1m4f stamina depth)
- recent_form

For the outsider horse: note model rank vs market rank, and the discrepancy signal.

### Step 7: Add going contingency note

If going is forecast to change (e.g., Soft declared when GTS expected), note whether any box horse has a going_fit cliff. For the Derby:
- Item: going_fit 0.95 on GTS, ~0.55 on Soft — if Soft declared, reduce to 3-box.

### Step 8: Stale-odds caveat (always required)

> "These odds are [DATE] morning quotes. Tomorrow's SP could shift materially — especially if any of the box horses drift or shorten overnight. The selection rationale is FORM-driven and remains valid, but trifecta dividend calculation cannot be projected from these odds."

---

## Output format

```markdown
## [Race Name] Trifecta Box — [HH:MM] BST [Day] [Date]

**Box:** [N horses, list]
**Combinations:** [N × (N-1) × (N-2)]
**Stake per combo:** £[X]
**Total outlay:** £[Y]
**Conviction:** [High / Medium / Low] — [one-line why]

### Horses in the box
| # | Horse | Jockey | Trainer | Odds (stale) | Why included |
|---|-------|--------|---------|--------------|--------------|
...

### Notes
- {outsider commentary}
- {going contingency}
- ⚠️ Stale-odds caveat: ...
```

---

## Known limitations / future work

- `src/betting.py` has **no `trifecta_box()` helper** as of 2026-06-05. Boxes are hand-assembled from scored data. Future work: add `trifecta_box(ranked_runners, n=4, stake_per_combo=1.0)` to `src/betting.py`.
- **`src/report.py` now has `render_trifecta_box(trifecta: dict) -> str`** (added 2026-06-05). This returns a self-contained `<tr>` HTML snippet for insertion into a `.slip` table. It is **not yet wired** into the Jinja2 template (`src/templates/report.html.j2`) or the main `render()` pipeline — promotion needed before Royal Ascot. See `.squad/decisions/inbox/linus-trifecta-card-placement.md`.
- Trifecta dividend cannot be projected without live SP — stale odds caveat is mandatory.
- Box selection is form-driven, not payout-optimised. We are not trying to maximise expected dividend; we are trying to have the right horses in the box.

---

## First use: Derby 2026

- Race: Betfred Derby (Group 1), Race 5 in racecard JSON, off 16:00 BST 2026-06-06, 12f
- Box: 4-horse (Item, Benvenuto Cellini, Maltese Cross, Causeway), £1/combo, £24 total
- Conviction: Medium (LOW race confidence, stdev 25.23, gap #3→#4 only 5.5 pts)
- Outsider double-up: Causeway (model #4, market #11, ~28/1) satisfies standing Derby outsider rule
- Going contingency: If Soft declared, drop Item → 3-box at £6 total
