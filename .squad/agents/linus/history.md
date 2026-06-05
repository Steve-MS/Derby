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

## 2026-06-03 — v0.5 anti-fab hardening patch

- Took narrow reviewer-lockout escalation because Rusty was locked out of revising Saul's rejected v0.5 signal artifact.
- Added the same public-entry guard to `market_move_signal`, `trainer_14d_signal`, and `jt_combo_signal`: non-dict runners now return neutral 50.0.
- Added one explicit `runner=None` anti-fab regression test per module.
- Left signal maths, scoring weights, schemas, and Danny's spec TODOs untouched.
- Validation: `pytest -x` collected 326 tests and all 326 passed.

## 2026-06-05 — Friday AM Gate: On Message data gap alert

- **ALERT:** "On Message" (trainer Ralph Beckett, jockey Hector Crouch, ~25/1 odds) is declared in the Oaks field but MISSING from `data/raw/epsom-2026-06-05-racecards.json`.
- Data pull was 2026-06-02; On Message either declared late or missed by the fetcher.
- **Impact:** On Message will have NO score in the Ladies Day report (no entry in enrichment files).
- Action: Flag in report output. Steve should be made aware for transparency.

## 2026-06-05 — Ladies Day footnote injection (Oaks section)

**What:** Surgically edited `outputs/report-2026-06-05.html` — NO regeneration from source data.
Three footnotes injected into the Oaks (16:00) race block:

1. **⚠️ On Message warning** — amber box between race header and runners table.
   Text: "Field is 9, not 8. On Message (Ralph Beckett / Hector Crouch, ~25/1) is late-declared, absent from our data feed. No form, no signals, no score."
2. **🚫 Belinus withdrawal** — same amber box, second item.
   Text: "Belinus — WITHDRAWN. Refund due on WIN £5 @ 3.5 from bookmaker."
3. **📈 Sugar Island market-move badge** — small green badge inside the Sugar Island runner row.
   Text: "Market move: 34.0 → 17–23. Your stake locked at 34.0. Bet is live."

**Pattern established:** All three are raw HTML div/p blocks with inline styles matching existing CSS variables (`--amber-pale`, `--green-pale`, `--green`). No new CSS classes needed. No re-run of `src/report.py` required.

## Learnings

### Late-runner / withdrawal / market-move footnotes (2026-06-05)

**When this happens again** (Derby Day or any future race day):

1. **Late declaration (unscored runner):**
   - Edit the HTML directly — surgical injection only. Do NOT regenerate if Steve has reviewed picks.
   - Inject an amber (`background:#fef3e2; border:solid #d68910`) warning box between `.race-header` and `.runners-section`.
   - Text template: "Field is N+1, not N. '[Horse]' ([Trainer] / [Jockey], ~X/1) is a late entry declared for this race but absent from our data feed. No form, no signals, no score. Treat top pick with awareness that there is one unscored horse in the field."
   - Comment the HTML block: `<!-- ⚠️ RACE-DAY FOOTNOTES — injected YYYY-MM-DD by Linus -->`

2. **Withdrawal (refund due):**
   - Add to the same amber footnote box (second `<div>` item with 🚫 icon).
   - Text template: "[Horse] — WITHDRAWN. Refund due on [bet type] £X @ Y.Y from bookmaker."
   - Horse does NOT need to appear in the runners table if already absent.

3. **Market steam / stake locked at better price:**
   - Add a small green badge (`background:#d4edda; border:1px solid #9bcfab`) directly inside the horse's `<td>` in the runners table, below the trainer-jockey div.
   - Text template: "📈 Market move: OLD → NEW. Your stake locked at OLD. Bet is live."

4. **Never touch the scored data** — picks, scores, signals untouched. Footnotes are cosmetic-only.
5. **Derby Day**: same pattern applies. Check decisions.md for any last-minute Livingston gate notes before adding footnotes.

## 2026-06-05 — Pass-rationale injection (Ladies Day card)

**What:** Surgically edited outputs/report-2026-06-05.html — NO regeneration.
Added bet **pick rationale** (4 races: EW Wild Terrain, WIN Respond/Stellar Sunrise/Dance In The Storm) and
**pass rationale** (4 races: PASS Naana's Shadow / Linwood / Amelia Earhart / Mister Winston).

All 3 prior footnotes (On Message, Belinus, Sugar Island) preserved.

**Injection points:**
- Pick rationale: <p class="pick-rationale"> injected after the existing <p> inside .top-pick, before closing </div>.
- Pass rationale: <p class="pass-rationale"> injected after </ul> inside .race-bets, before closing </div>.

## Learnings

### Pass-rationale on cards (2026-06-05, generalises to Derby Day)

**Pattern:**
1. Every PASS race needs one plain-English sentence in the race-bets block explaining which gate was missed.
2. Gates in src/betting.py (v0.1): (a) No odds → "No odds available"; (b) confidence HIGH + win_edge ≥ 15% → WIN; (c) confidence HIGH/MED + combined EW edge ≥ 20% → EW; (d) anything else → PASS.
3. The rationale text always names the gate: confidence level, threshold, and why it wasn't cleared.
4. For PASS-on-a-favourite: also flag the short-price / overround problem explicitly.
5. For PASS with an unscored runner: cross-reference the On Message footnote in the Oaks rationale — Steve should see both together.

**Derby Day checklist:**
- Same pattern. Run through each PASS race and name the gate.
- Check decisions.md for any late Livingston gate notes before adding rationale.
- If a race was EW-header but PASS in bet-list (inconsistent data like Mister Winston 16:40), write the rationale from the bet-list outcome (PASS) since that's what Steve acted on.

### Dual-artifact update pattern (2026-06-05)

**Key learning:** The 1-pager (`outputs/racecard-YYYY-MM-DD.html`) and the long report (`outputs/report-YYYY-MM-DD.html`) are TWO SEPARATE artifacts. Any in-day event (withdrawal, late entry, market steam, pass-rationale addition) must be applied to BOTH files independently.

- This morning's pass-rationale + footnotes work was applied to the long report (commit fdbd840) but NOT to the 1-pager.
- The 1-pager was left stale until the afternoon surgical update on 2026-06-05.
- **Checklist for any future in-day injection:** (1) Edit long report, (2) immediately edit 1-pager with the same content adapted to the compact table format, (3) verify both files before finishing.
- The 1-pager uses `row-rationale row-rationale-pass` table rows (not `<p class="pass-rationale">`) because it is a table-based layout, not the card-based long report layout.

## 2026-06-05 — Per-race outsider picks injection

**What:** Steve requested one outsider pick per race across all 8 Ladies Day races.
Added 6 new outsider picks (EW £0.25 each) + 1 "no outsider" entry (Diomed G3) to both artifacts.

### Learnings

#### Per-race outsider picks pattern (2026-06-05, reusable every race day)

**Source:** market-latest.json prices. Mark as "(stale)" if source is "Synthetic from OR/field-size" dated before race day.

**Outsider definition used:**
- Horse priced ~10/1 or longer (10.0 decimal = 9/1 fractional is borderline — include if it's the longest in the field by a clear margin)
- Minimum ONE positive signal: market support at price, shortest longshot in field, field-size place-value maths, model rank discrepancy
- Stake: £0.25 EW standard
- If no horse qualifies at 10/1+: show a "no outsider" row with 1-line reason

**1-pager placement:**
- Outsider row goes IMMEDIATELY AFTER the main bet rationale row (same race pair)
- For PASS races: outsider row goes IMMEDIATELY AFTER the pass rationale row (same race pair)
- Use **single-row format** (data + rationale in the col-note column) to preserve page fit
- CSS: `row-outsider` class already handles background; `inline-price price-stale` for stale prices
- Prefix the col-note rationale with "⚡" for picks, "⛔" for no-pick rows
- Keep col-note rationale to ~60 chars (fits at print font size in the 63mm column)

**Long report placement:**
- `<div class="outsider-pick">` goes AFTER the closing `</div>` of `<div class="race-bets">`, INSIDE the `<section class="race-block">`
- Use existing CSS classes: `.outsider-pick`, `.outsider-pick-header`, `.outsider-meta`, `.outsider-rationale`
- For "no outsider" races: use inline style `background:#f5f5f5; border-color:#bbb; border-left-color:#999` to visually distinguish
- Rationale: 2-3 sentences covering: who the main bet is (if any), why this horse at this price, what the EW maths look like

**Stake accounting:**
- 6 new EW picks × £0.50 = £3.00 added to day total
- Update 1-pager header "Total outlay" and "Bets" count (each EW = 1 bet in this system)
- Update long report portfolio card "Total Stake" and outsider card ("N picks / £X stake")

**"No outsider" threshold cases:**
- Diomed G3 (14:40): entire 14-runner field priced 13/2–8/1. No pick; say so plainly.
- Surrey Listed (17:15): Assaranca at 9/1 is borderline — include with clear note that it's at the threshold.

**Dual-artifact checklist for future outsider runs:**
1. Check market-latest.json for each race — list horses ≥ 10/1+
2. Pick the market-shortest (most market-backed) outsider per race — most defensible single-signal rationale
3. If G1/G2/G3 field is tight (all ≤ 8/1): declare no pick with reason
4. 1-pager: insert single-row outsider immediately after each race's rationale row
5. Long report: insert outsider-pick div at end of each race section
6. Update stake totals in both files
7. Mark all synthetic/estimated prices as "(stale)"

## 2026-06-05 — Midday refresh regen (12:05 BST)

**What:** Livingston landed a refreshed market-latest.json at 11:59:32 BST (144 runners, 52.8KB).
Confirmation: no price moves >20%, no new non-runners, prices remain stale/synthetic (2026-06-02 basis).

**Decision:** Used **Option B** (surgical timestamp-only update). No data changed, so no re-render of picks, scores, signals, outsiders, accumulators, passes, or footnotes was needed or performed.

**Edits made:**
- `outputs/racecard-2026-06-05.html` line 512: updated disclaimer footer timestamp to "Generated 2026-06-05 12:05 BST — prices stale (2026-06-02 synthetic basis), no Betfair API"
- `outputs/report-2026-06-05.html` line 739 (page header disclaimer): same timestamp update
- `outputs/report-2026-06-05.html` line 7753 (page footer): same timestamp update; removed `<span class="odds-snapshot">` since that referred to a now-stale FanOdds snapshot

**Checklist verified post-edit:**
- 5 active bets present (Wild Terrain EW, Respond WIN, Prizeland EW outsider, Stellar Sunrise WIN, Dance In The Storm WIN)
- 7 outsider picks present (Rosie Frith, Hickory Lad, Liberty Lane, Prizeland, Port Road, Assaranca, Blue Brother)
- 4 passes present (Naana's Shadow, Linwood, Amelia Earhart, Mister Winston)
- 3 footnotes present (On Message, Belinus, Sugar Island)
- 3 doubles + 1 treble accumulators present
- Day total stake £11.61 unchanged
- All stale prices retain `(stale)` tag (9 occurrences on 1-pager, throughout report)
- Both footers now read "Generated 2026-06-05 12:05 BST — prices stale (2026-06-02 synthetic basis), no Betfair API"

## Learnings

### Midday regen without data change (2026-06-05)

**Rule:** If Livingston's midday refresh shows no material price moves and no new non-runners, use Option B (timestamp-only surgical edit). Do NOT regenerate from src/report.py — it would wipe all manual in-day annotations.

**Trigger test:** Use Option B when ALL of these hold:
  1. No price move >20% on any staked horse
  2. No new non-runners since morning gate
  3. No new declared runners since morning gate
  4. Prices remain stale/synthetic (no live API)

**Use Option A (surgical port of annotations into fresh regen) only when:** the underlying scored data changes materially (e.g. new signal shipped, weight change by Danny, new runners scored by Livingston).

**Timestamp format adopted (2026-06-05):**
- 1-pager: `Generated YYYY-MM-DD HH:MM BST — prices stale (YYYY-MM-DD synthetic basis), no Betfair API`
- Report header + footer: same format
- Remove `<span class="odds-snapshot">` from report footer when there is no live odds snapshot available


