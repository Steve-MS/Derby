# Linus — History

## Project context (seeded 2026-06-03)

- Python 3.12 race-analysis toolkit. Repo Steve-MS/Derby, commit 5a1770e.
- Owns `src/report.py` (HTML) + `src/betting.py` (betting maths + recommendations).
- Steve's standing rules:
  - £100 total outlay per day
  - One A4 race card per day (not per race)
  - Outsider bet required for the Derby itself
  - Accumulator suggestion per day
- `SIGNAL_LABELS` dict lives at lines ~44-56 of `src/report.py` — add new label whenever Rusty ships a signal.

## 2026-06-05 PM — Derby Trifecta Box (race-day-eve)

**What:** Produced a hand-assembled Derby trifecta box recommendation on race-day eve for Steve. No `trifecta_box()` helper exists in `src/betting.py` — this was a one-off manual construction from the scoring model. **Flag for future work:** add a `trifecta_box(race_scores, n=4)` helper to `src/betting.py`.

**Race identified:** Betfred Derby (Group 1) — Race 5, off 16:00 BST 2026-06-06, 12f. NOTE: the task brief said 16:30 but the racecard JSON and bets file both show 16:00. Used 16:00 (data-authoritative).

**Box selected:** 4-horse box (24 combinations) — Item, Benvenuto Cellini, Maltese Cross, Causeway.
- Item: score 95.0 (Dante winner, trial=90, market_move=90, going_fit=95)
- Benvenuto Cellini: score 93.6 (Chester Vase winner, trial=88, market_move=90; live 2.0)
- Maltese Cross: score 85.6 (Lingfield Trial winner, sire=90, recent=90)
- Causeway: score 80.1 (model #4 vs market #11 at 28/1; going_fit=95, recent=96)

**Conviction: Medium.**
Rationale: Top-3 cluster is clear (scores 95.0/93.6/85.6), gap to #4 is 5.5 points, but race confidence is LOW (stdev 25.23). The 5.5pt gap is only ~0.22 sigma — insufficient to justify a 3-horse box given the race volatility and competitiveness of a deep 18-runner Group 1 field. 4-horse box is the correct default.

**Stake convention used:** £1.00 per combination = £24.00 total. Fits within Steve's £15-35 trifecta budget and leaves headroom in the £100 daily outlay.

**Outsider:** Causeway IS the outsider (28/1 stale, model rank 4 vs market rank 11). Already in the box — satisfies the standing outsider rule for the Derby. Also already picked as EW outsider in the main bets slip.

**Constitution River (score 71.0, 9/1) deliberately left out:** French Derby winner 6 days before; 6-day Chantilly→Epsom turnaround is a risk the model cannot fully score; no market_move signal (=50). Causeway's model discrepancy is a cleaner value argument.

**Going contingency noted:** If Soft declared Sat morning, Item going_fit collapses 0.95→0.55. In that case, switch to 3-horse box (Benvenuto Cellini, Maltese Cross, Causeway) at £6 total.

## Learnings

### Trifecta box added to Derby Day card (2026-06-05 PM)

**Route taken:** Hybrid — hand-edited `outputs/racecard-2026-06-06.html` to insert the trifecta section (generator re-run not feasible without full input pipeline); simultaneously added `render_trifecta_box()` helper to `src/report.py` for future reproducibility.

**Placement:** Immediately below the Derby outsider rationale row (Causeway EW row + rationale), inside the main `.slip` table as a full-width `<tr class="row-trifecta">` with `colspan=8`. Layout option (a) per the task brief — keeps Derby content grouped.

**Promotion task flagged:** `render_trifecta_box()` in `src/report.py` must be wired into the Jinja2 template and `render()` pipeline before Royal Ascot. Decision logged at `.squad/decisions/inbox/linus-trifecta-card-placement.md`.

**Verification:** All 11 content checks passed (box content, stale caveat, 4 horses, going contingency, conviction, total outlay). Ladies Day card (`racecard-2026-06-05.html`) untouched. Downstream races (16:40 Allegresse etc.) intact.

### Trifecta box construction from scoring model (2026-06-05, reusable for any Group 1)

1. **No `trifecta_box()` in betting.py as at 2026-06-05.** Future work: add a helper function.
2. **Box size decision tree:**
   - 3-box (6 combos): top-3 cluster with gap >1 sigma from #4, AND confidence HIGH/MED
   - 4-box (24 combos): default; use when gap to #4 is <1 sigma OR confidence LOW
   - 5-box (60 combos): use when race_stdev very high + race is very competitive + no clear top-3
3. **Stake convention:** Target £15-35 total for a Group 1 trifecta alongside other day bets. £1/combo for 4-box = £24 (sweet spot). £2.50/combo for 3-box = £15. £0.50/combo for 5-box = £30.
4. **Outsider double-up:** If the model's top-4 includes a long-shot (14/1+), it is both a box pick AND satisfies the standing Derby outsider rule. Document this to avoid double-counting stake against the £100 budget.
5. **Going contingency:** Always note a going-triggered box reduction (e.g., if GTS→Soft, drop the going_fit-sensitive horse and reduce to 3-box). This is especially relevant for Epsom round course.
6. **Odds column:** Always label "(stale)" and include a caveat. Never project trifecta dividend from stale odds.

---

**Early session work (2026-06-03–2026-06-05 12:05) archived to history-archive.md**
