# Decisions Log

## 2026-06-05T15:02:08+01:00 — Rusty (Signal Engineer)

**Decision:** Prizeland (NR) Replacement — Oaks 16:00

**Status:** ✅ Pick delivered

### Context
Prizeland confirmed NOT RUNNING. Absent from `market-baseline.json` (09:52 BST). Verbal confirmation from Steve at 15:02 BST.

### Choice: Cameo £0.25 EW @ ~14/1 (stale)

| Field | Value |
|-------|-------|
| Horse | Cameo |
| Trainer | Aidan O'Brien |
| Model rank | #3 (score 88.4 / 100) |
| Market rank | #4 |
| Trial form | Won Lingfield Oaks Trial by 4.75L |
| Price | ~14/1 (15.0 decimal, 2026-06-02 estimate) |
| Confidence | MEDIUM |

**Rationale:** Aidan O'Brien trial winner (trial_form 80/100, trainer_form 100/100) at an outsider price with rank-price gap. Replaces Prizeland (model #3 → Cameo model #3) — scoring improves by +9.8 points.

**Stale-odds caveat:** Price is estimated from 2026-06-02 racecard. Verify current price at rail before staking.

**Why not Sugar Island?** Sugar Island scored 89.3 (model rank #2) but market has moved intra-day (34.0 → ~17–23). Stale 34.0 price is stale in wrong direction; current EW case is weaker. Steve already holds active Sugar Island EW at 34.0.

---

## 2026-06-05T15:13:00+01:00 — Linus (Reports Engineer)

**Decision:** Prizeland → Cameo Row Swap — Ladies Day Racecard

**Status:** ✅ Done

### What Was Done

Hand-edited `outputs/racecard-2026-06-05.html` to replace Prizeland selection (16:00 Oaks) with Cameo, per Rusty's signal.

### Changes

1. **Prizeland row removed** — `<tr class="row-outsider">` + `<tr class="row-rationale">` pair excised.
2. **Cameo row inserted** with matching structure:
   - Horse: Cameo · Trainer: Aidan O'Brien · Jockey: [TBC]
   - Price: ~14/1 (stale, 15.0 decimal, 2026-06-02 estimate)
   - Stake: £0.25 EW → win return col: £3.75
   - Note col: model rank 3 vs market 4 + amber NR badge `🚫 Replaces Prizeland (NR)`
   - Rationale: Lingfield Oaks Trial 4.75L win, trial_form 80/100, trainer_form 100/100
3. **Stale-odds caveat** — amber `<div>` in `row-rationale`: "Odds (~14/1, 15.0 decimal) are 2026-06-02 estimates. Verify current price at the rail or with your bookmaker before staking."
4. **Footnotes updated** — Added NR note to card-bottom race-day notes box.
5. **HTML comment audit trail** — `<!-- 🔄 CAMEO REPLACES PRIZELAND (NR) — hand-edit 2026-06-05 by Linus -->`

### Verification

- [x] Prizeland row removed from 16:00 race
- [x] Cameo row inserted with matching structure
- [x] Amber NR annotation visible in col-note
- [x] Stale-odds caveat present in rationale cell
- [x] Other races on Ladies Day card unchanged
- [x] Derby card untouched

### Cross-Agent Flag

**Task for Royal Ascot:** Add `render_replacement_row(original_horse, replacement, bet, rationale, stale_price, conviction)` to `src/report.py` alongside `render_trifecta_box()`.

This is the second hand-edit in two days. Helper would make row swap reproducible and testable rather than manual each time.

---

## 2026-06-05 — Linus (Reports Engineer)

**Decision:** Trifecta Box Placement on Race Day Cards

**Status:** ✅ Implemented

### Context

Derby Day 2026-06-06 card — first use of a trifecta box recommendation.

### Decision

**Trifecta boxes always render immediately below the parent race's outsider rationale row, not in a separate "Specials / Multiples" section.**

The box is inserted as a full-width spanning `<tr class="row-trifecta">` inside the main `.slip` table, directly after the `row-rationale-outsider` row for that race.

### Rationale

- Keeps all race content visually grouped together on the A4 card.
- Steve reads race-by-race in time order; avoids page-flip mid-race.
- Cross-reference is cleaner when trifecta is inline with race block.

### Implementation

- Visual distinction: purple left-border + shaded `#f6f3ff` background (`.trifecta-box` CSS class).
- `render_trifecta_box(trifecta: dict) -> str` helper added to `src/report.py` (2026-06-05).
- Helper exists but not yet wired into Jinja2 template.

### Handoff Note

⚠️ **Before Royal Ascot:** promote the helper into `src/templates/report.html.j2`, pass a `trifecta_boxes` dict via the `render()` call, and add companion CSS classes to `src/templates/style.css`.

---
