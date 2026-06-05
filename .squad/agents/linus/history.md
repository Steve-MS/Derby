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

## 2026-06-05 16:50 — ESCALATION: render_replacement_row() promotion to HARD-RULE priority

**Issue:** Three NR swaps on Ladies Day required manual HTML surgery (hand-editing racecard + report footnotes). Two swaps involved picking invalid replacements (Triple Double A, Blue Brother) that bypassed the stale-odds caveat — the caveat only warns about price, not runner validity.

**Current merged caveat:** "Stale odds — verify at rail" implies the runner is fine but price is uncertain. This is not always true.

**New requirement:** Promote `render_replacement_row()` to public, hardened helper in src/report.py with expanded parameter set:
- **New param:** `runner_verified_source: str | None`
  - If supplied (e.g., `"Sporting Life 2026-06-05T16:25 BST"`) → render GREEN ✅ caveat: "Runner live-verified [source]"
  - If None → render AMBER ⚠️ caveat: "Runner not live-verified — re-check at gate before staking"
- **Stale-price caveat:** Render SEPARATELY in amber (not merged): "Price ~20/1 from 2026-06-02 enrichment — verify at rail"

**Why:** Distinguishes two failure modes:
1. Stale price → expected, OK to hedge with stale-odds warning
2. Stale runner → unexpected, hard-stop risk (horse may not run)

**Implementation:** 
- Signature: `render_replacement_row(original_horse, replacement_horse, rationale, stale_price, runner_verified_source=None)`
- Render two separate `<div class="amber-caveat">` blocks if `runner_verified_source is None`, else one `<div class="green-verified">` + one `<div class="amber-caveat">`
- HTML templates in `src/report.py` ~line 200 (stale-odds caveat template)

**Priority:** HARD-RULE — ship BEFORE Royal Ascot (16–20 Jun 2026). No exceptions. Three manual swaps in one afternoon establishes pattern.

**Blockers:** None (additive parameter, existing CSS stable)

**Test coverage:** Saul owns render_replacement_row() tests (both parameter values + HTML output validation)

---

## 2026-06-05 16:45 — Live-verified reset: Card + Report rebuild complete

**What:** Full hand-edit of outputs/racecard-2026-06-05.html + outputs/report-2026-06-05.html with 2 NR swaps and verification stamps.

**NR swaps:**
1. 16:40 Triple Double A (NR) → Asmen Warrior (live-verified cloth #15)
2. 17:50 Blue Brother (NR) → Arctic Thunder (live-verified cloth #11)

**Rebuild approach (Option B):** Hand-edited outsider-pick recommendation blocks; retained field ranking tables as historical audit trail (model's original scoring preserved). Full verification sweep: all named horses on card cross-checked against live-runners-2026-06-05.json — CLEAN, no additional mismatches found.

**Verification stamp added to both outputs:**
> 🟢 Live-verified 2026-06-05 16:25 BST — All runners confirmed against Sporting Life + corroborating sources. Earlier card carried 3 non-runners (Port Road, Triple Double A, Blue Brother) — now replaced. Prices remain 2026-06-02 vintage; verify at the rail.

---

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

### Live-verified reset — 17:50 Arctic Thunder swap + full report regen (2026-06-05T16:45)

**Pipeline approach:** Option B (hand-edit). Option A (pipeline re-run) not viable on race day — stale enrichment data is the root cause, so re-running the pipeline would reproduce the same NR contamination. Surgical HTML edits to the outsider-pick blocks were the correct call. Gotcha: the report's field-ranking tables legitimately retain Port Road / Triple Double A / Blue Brother as historical model scoring rows — only the actionable recommendation blocks (`outsider-pick` divs) needed replacing.

**Verification stamp is now standard pattern:** Both racecard and report carry a 🟢 live-verified banner. This should be added to every race-day output going forward. Template:
```
🟢 Live-verified {DATE} {TIME} BST — All runners confirmed against Sporting Life + corroborating sources. Prices remain {DATE} vintage; verify at the rail.
```

**`render_replacement_row()` is a HARD RULE now — next race day starts with this work.** Four manual NR swap edits across two files in one afternoon (Cameo, Asmen Warrior, Arctic Thunder in racecard; Asmen Warrior + Arctic Thunder in report) is the definitive threshold. The helper ships before Royal Ascot (16–20 Jun 2026). It must cover: outsider-row swap, main-pick swap, separate stale-price vs runner-validity amber divs, always-emit rationale row, HTML entity escaping. No more hand-edits after this.

### Third NR swap today — `render_replacement_row()` HARD-RULE elevated (2026-06-05T16:32)

**What happened:** A third non-runner hot-swap in a single afternoon (Cameo ~15:13, Triple Double A ~15:58, Asmen Warrior ~16:32). Triple Double A was itself the v1 replacement for Port Road — it too was declared NR, caught by Steve at 16:12 BST. Asmen Warrior (James Owen / Silvestre De Sousa, draw 5, OR 88 / RPR 112, 5-star Timeform, ~20/1 stale) is the confirmed live-verified final pick for the 16:40 HKJC Handicap.

**HARD RULE — `render_replacement_row()` ships before Royal Ascot (16–20 Jun 2026):** Three hand-edits in one afternoon is the threshold. This is no longer a future-work flag — it is a hard delivery requirement. The helper must cover both outsider-row-only swaps and main-pick swaps (see history entry ~15:58 for required signature detail).

**Amber stale-odds caveat needs two-way split:** The current merged amber div ("stale odds — verify at rail") conflates price uncertainty with runner validity. Triple Double A proved these are separate concerns: the horse was invalid, not just the price. Propose splitting into: (1) stale-price caveat; (2) runner-validity caveat with `runner_verified_source` parameter — green div if live-verified, amber div if not. Full proposal in `.squad/decisions/inbox/linus-1640-asmen-warrior-swap.md`.




### Non-runner hot-swap pattern — when to hand-edit vs regenerate (2026-06-05)

**Trigger:** Prizeland confirmed NR (16:00 Oaks) at 15:02 BST on race day. Replacement pick (Cameo) delivered by Rusty. Card is already printed / at-rail; pipeline re-run not feasible (no live input pipeline on race day).

**Decision: hand-edit HTML directly.** Same call as the Derby trifecta box (2026-06-05 PM). Rule of thumb:
- **Hand-edit when:** race day, pipeline input data unavailable, single-row surgical change, output already in Steve's hands.
- **Regenerate when:** pre-race-day, full pipeline available, change touches scoring/weights/multi-row layout.

**Pattern used:**
1. Locate the `<tr class="row-outsider">` and its `<tr class="row-rationale">` pair for the NR horse.
2. Replace both rows wholesale — do not attempt in-place field edits (too error-prone for apostrophes, HTML entities, etc.).
3. In `col-note`: add an amber-highlighted NR badge using inline style matching `.stale-caveat` convention: `background:#fff8dc; border-left:3pt solid #d99400`.
4. In `row-rationale`: add a second amber `<div>` for the stale-odds caveat immediately below the bet-rationale text.
5. Update footnotes block at card bottom — add `🚫 Prizeland (NR) → Cameo` entry so it's visible even if the table is partially obscured.
6. Confirm Derby card (`racecard-2026-06-06.html`) mtime unchanged before declaring done.

**Helper-promotion flag — `render_replacement_row()` for Royal Ascot:**
No helper currently exists for NR row replacement. This is the second hand-edit in two days (trifecta box was the first). Recommend adding `render_replacement_row(original_horse, replacement, bet, rationale, stale_price, conviction)` to `src/report.py` alongside `render_trifecta_box()` before Royal Ascot — Group 1 cards reliably produce late NRs on race day. **Cross-agent flag for Saul:** if `render_replacement_row()` is added, it needs test coverage for: NR badge rendering, stale-caveat presence, apostrophe escaping, and that the original horse's row is absent from output.

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

### Second NR hand-edit in one afternoon — Cameo + Triple Double A (2026-06-05, ~15:58 BST)

**What happened:** Two NR swaps within 90 minutes on Ladies Day. Cameo at ~15:13 (Prizeland NR, 16:00 Oaks, main-outsider-row swap). Triple Double A at ~15:58 (Port Road NR, 16:40 HKJC Handicap, outsider-row swap). Both hand-edits to `outputs/racecard-2026-06-05.html`; both delivered from Rusty's decision files; both following the same amber-badge + amber-stale-caveat pattern. Derby Day card untouched in both cases.

**Pattern confirmed:** Two swaps of the same structural type (find `row-outsider`, replace wholesale, inject rationale row, update footnotes) in a single afternoon is now a confirmed pattern for high-attendance Group 1 + big-field handicap cards. This is not an edge case; it is the expected race-day workload.

**Per-race NR-check pass at gate time (~30 min before each race):** Would this catch these earlier? Yes — a 30-minute-before gate-time check of market data against the card would have surfaced both NRs before race day communication cut-off. Prizeland's absence from market-baseline.json was detectable at 09:52 BST; Port Road's absence was also in the baseline. The issue is not detection latency but process: there is no formalised gate-time NR-check step in the current race-day workflow. Recommend adding a named "gate-time check" step (30 min before each race) to the race-day runbook — scan market-baseline.json for any card horse with no entry; flag immediately to Rusty for replacement. This would convert reactive swaps into proactive ones and give more time for rationale construction.

**Structural difference: outsider-row swap (Triple Double A) vs main-pick swap (Cameo):**
- **Cameo (main-pick swap):** Replaced a `row-win`/`row-ew` row for a horse that had been the primary pick. The replacement row kept the same bet-tag type (EW) and full rationale row already existed as a sibling.
- **Triple Double A (outsider swap):** Replaced a bare `row-outsider` that had NO `row-rationale` sibling (the original Port Road row was a one-line col-note injection, not a full rationale pair). Had to add the rationale row from scratch — this is a structural addition, not just a content replacement.
- **Implication for `render_replacement_row()` helper signature:** The helper must accept a `has_existing_rationale_row: bool` parameter (or always produce the rationale row and let the caller decide whether to insert it). The outsider-swap path must always produce a rationale row even if the original had none. The main-pick-swap path must replace both rows. A single helper can cover both by always emitting the pair — the caller simply replaces 1 or 2 rows in the DOM accordingly.

**`render_replacement_row()` — ELEVATED PRIORITY (cross-flag in decision file):**
- Two hand-edits in 90 minutes confirms this is not a one-off. The helper should be in `src/report.py` before Royal Ascot (16–20 June 2026).
- If a third NR swap arrives today (or at any future single-day session), this becomes a hard rule: no more hand-edits, the helper ships immediately after that race day ends.
- Detailed signature and test requirements logged in `.squad/decisions/inbox/linus-port-road-triple-double-a-swap.md`.

---

**Early session work (2026-06-03–2026-06-05 12:05) archived to history-archive.md**

## 2026-06-05 PM — Port Road → Triple Double A swap (16:40 HKJC, second NR edit)

**What:** Hand-edited outputs/racecard-2026-06-05.html to swap Port Road (NR) for Triple Double A replacement.

**Edits:**
- Removed Port Road row-outsider (bare row, no rationale sibling)
- Inserted Triple Double A row-outsider + new row-rationale pair (matching Cameo pattern from earlier swap)
- Amber NR badge: ackground:#fff8dc; border-left:3pt solid #d99400
- Amber stale-odds caveat div (same style, 2026-06-02 vintage notice)
- Appended Port Road NR note to card-bottom footnotes (Cameo/Prizeland note already present)

**Verification:** All 10 pre-commit checks pass. Derby Day card untouched.

**Pattern flag:** This is swap #2 in 90 minutes (Cameo ~15:13, Triple Double A ~15:58). Manual HTML is the expected load for Group 1 big-field cards. **ender_replacement_row() promotion to src/report.py ELEVATED priority** — bake into test suite alongside ender_trifecta_box(). Third NR swap today triggers hard rule: ship helper before next race day.

**DRY violation:** Amber badge + stale-odds caveat CSS duplicated verbatim across Cameo and Triple Double A. When helper ships, consolidate to single render function with parameterized inline styles.
