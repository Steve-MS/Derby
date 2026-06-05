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
