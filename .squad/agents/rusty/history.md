# Rusty — History

## Project context (seeded 2026-06-03)

- Python 3.12 race-analysis toolkit. Repo Steve-MS/Derby, commit 5a1770e.
- Existing signal modules to mirror: `src/cd_form.py`, `src/sires.py`, `src/pace.py`, `src/going.py`.
- All return 0-100 normalised scores; missing data → 50.
- Sire stamina sets the gating pattern: only fires at 10f+ races.
- 227 tests passing — each new signal expected to add ~18-22 tests.
- Backlog: trial-form (first), market-move, trainer-strike, jt-combo, equipment.

## 2026-06-04 — trial_form signal

Implemented `src/trial_form.py` and updated `src/scoring.py` to v0.4.

**Outcome:** 246/246 tests passing (19 new from Saul's suite).

**Key calls made:**
- Normalised Livingston's signed `beaten_lengths` convention on JSON load (negative winner margin → 0.0 for pos=1, abs() for pos>1).
- Added walkover cap (field_size==1 → max 70.0) to pass `test_single_runner_field_no_overcredit`.
- Reconciled Danny's spec API with Saul's test API — both sets of function names implemented.
- `race_date` defaults to `"2026-06-06"` (Derby day) so Saul's 3-arg `score_trial_form` calls work.
- Tier 3 default for unlisted trial names; Leopardstown Derby Trial → Tier 2 per Steve Q3.
- All v0.3 weights × 0.92; trial_form = 0.0800; sum = 1.0000.

**Decision note:** `.squad/decisions/inbox/rusty-trial-form-implementation.md`

## 2026-06-03 — v0.5: market_move, trainer_14d, jt_combo signals

Implemented three new signal modules and updated `src/scoring.py` to v0.5.

**Outcome:** 246/246 tests passing. Saul's new test suites not yet present (in parallel).

**Key calls made:**
- `market_move`: read Livingston's 2-file schema (`market-baseline.json` + `market-latest.json`, each with `decimal_odds`) and combined in-memory — Danny's single-file spec was aspirational. Used Danny's Δip formula (not Livingston's `(b-l)/b` strawman). Empty latest stub → neutral 50 for all runners.
- `trainer_14d`: always recompute `wins_14d/runners_14d` — stored `strike_rate` is display-only.
- `jt_combo`: horse-keyed lookup avoids trainer/jockey name normalisation mismatches.
- All 15 v0.5 weights verified to sum to exactly 1.0000.
- Danny's score-curve anchors verified for all three pure scoring functions.

**Decision note:** `.squad/decisions/inbox/rusty-v05-implementation.md`

## 2026-06-03 — v0.6: equipment signal

Implemented `src/equipment.py` and updated `src/scoring.py` to v0.6.

**Outcome:** 352/352 tests passing.

**Key calls made:**
- Added mandatory top-level non-dict runner guard: `score_equipment(None, {}) -> 50.0` confirmed.
- Loader returns equipment enrichment keyed by lower-cased horse name for safer lookup.
- Equipment scoring follows Danny's locked spec: base 50, first-time item deltas, -3 stacking penalty per extra current item, +3 per removed item, clamp [10, 90].
- All 15 v0.5 weights scaled ×0.9750; `class_rating` absorbed rounding residual; equipment = 0.0250; sum = 1.0000.
- Added/updated tests for equipment scoring, None guard, loader shape, scoring integration, and weight sanity.

**Decision note:** `.squad/decisions/inbox/rusty-v06-equip.md`

## 2026-06-05 — Friday AM Gate: Sugar Island market_move signal limitation

- **Finding:** Sugar Island (EW £0.25 @ 34.0) drifted inward from 33/1 → 16-22/1 today (decimal 17-23).
- **Signal impact:** market_move returns neutral 50 (both baseline and latest have price 34.0 from racecard — no live odds feed).
- **Real move:** Market shows genuine confidence (50–100% inward move), but market_move signal cannot detect it without live mid-race odds.
- **Note:** This is a data-feed limitation, not a signal bug. Recommend manual note in report: "Sugar Island has moved in overnight market but signal shows no change due to no live odds feed."
- **Mitigation for future:** Racing Post WebSocket odds would be needed for real-time market_move signal updates (currently blocked).

## 2026-06-05 — Midday Refresh Round: Synthetic-price tag retained

Livingston (11:59 BST): midday market refresh executed. No material price moves (<20% threshold), no new non-runners. **Critical finding:** prices still synthetic, dated 2026-06-02 (no live Betfair API implemented). RP scrape bypasses JS-rendered odds, falls back to enrichment DB.

**Impact on v0.5 signals:** market_move signal returns neutral 50 for all runners (0% Δip detected). This is expected behavior given synthetic prices. Signal will remain inert until live-price ingestion is implemented.

**Synthetic-price tag:** Retained in both racecard and report footers for Ladies Day + Derby Saturday.

## Learnings

### 2026-06-05 — Two NRs in 90 Minutes: Batch-Check Pattern

**Trigger:** Two non-runner swaps in the same afternoon session — Prizeland (16:00 Oaks) confirmed ~15:02 BST, Port Road (16:40 HKJC Handicap) confirmed ~15:46 BST. Both were outsider-slot horses in separate races. Handled as two sequential single-NR interruptions.

**Observation:** A batch NR-check pass at ~14:30-15:00 BST (i.e., ~90 minutes before the first afternoon race) would have caught both simultaneously rather than processing them as separate context-switches. The check is trivially cheap: iterate `market-baseline.json` keys against racecard horses and flag absences in one pass.

**Workflow improvement for future race days:**
1. **Batch NR pass at T-90min** (e.g., 14:30 for a 16:00 first race): compare all remaining racecard horses against `market-baseline.json` in a single pass; produce a single "NR found" list rather than relying on Steve to catch each one separately.
2. **Handle all NRs as a batch**: if multiple NRs are found in step 1, execute all replacements in one agent session rather than one at a time. Reduces Steve's interruptions from N to 1.
3. **Ladies Day risk higher than Derby Day**: big-field handicaps (HKJC 29 runners, Nifty 50 25 runners) tend to have more late scratches than Group 1 Classics — operator runbook should note an elevated NR probability for the Friday card specifically.
4. **Outsider-slot horses are highest-risk for late NRs**: Port Road (TBC jockey, Simon Dow smaller yard, OR 79) and Prizeland (34/1) are exactly the profile that gets scratched late. Prioritise checking low-profile outsider-slot horses in the batch scan.

**Stale-price trap awareness in big-field handicaps:** This NR highlighted how many runners in a 29-runner field have "stale-price trap" profiles (Zarathos: two recent wins; Jimmy Speaking: two wins + 2nd). In future, a pre-race stale-price audit of outsider candidates (checking recent form for price-compressions) should be standard before nominating any outsider pick in a multi-runner handicap.

**Port Road replacement decision note:** `.squad/decisions/inbox/rusty-port-road-replacement.md`  
**Replacement pick: Triple Double A** (Hugo Palmer / Saffie Osborne, OR 80 / RPR 109, ~23/1 stale, £0.25 EW)  
**Action owner:** Linus (racecard HTML update)

---

### 2026-06-05 — Non-Runner Replacement Workflow (Race-Day-Eve Hot-Swap)

**Trigger:** Steve confirmed Prizeland (16:00 Oaks) is not running ~1 hour before the race. Data files (market-latest.json, market-baseline.json) already reflected the NR via absence from baseline — verbal confirmation was authoritative but the data corroborated it independently.

**Workflow pattern established:**

1. **Confirm NR source.** Check market-baseline.json absence first (fastest); treat Steve's verbal as authoritative if data lags. Do not regenerate the full pipeline — surgical pick only.
2. **Re-run score_race on the adjusted field** (exclude all confirmed NRs). Field-size normalisation shifts rankings non-trivially — a horse that was model #4 in the full 11-runner field can become model #2 in the 8-runner adjusted field. Always re-score; never assume ranks carry over.
3. **Market rank also shifts.** When NRs are removed, market ranks compress. Recalculate from the remaining horses' decimal_odds to get the true rank-price gap for the replacement pick.
4. **Watch for stale-price traps.** If a horse's intra-day market move is already documented in decisions.md footnotes (e.g., Sugar Island 34.0 → 17–23), the stale odds are specifically unreliable for that horse. Prefer alternatives where stale price is likely still indicative.
5. **Check for existing bets before doubling up.** If the highest-scored alternative already has a live stake from a footnote/pre-existing pick, flag this and consider the next-ranked scorer to avoid unintended position doubling.

**Scoring shortcuts for race-day-eve hot-swaps:**
- Score the adjusted field (NRs removed) against the full enrichment stack — no need to rebuild enrichment files.
- Market rank recalculation: `sorted([(name, odds) for name in active_field], key=lambda x: x[1])` gives immediate market order.
- The `score_race()` function handles field-size normalisation automatically — pass only the active runners.
- Jockey TBC (= 0/100 in jockey signal) suppresses both candidates equally when comparing two TBC horses; don't use jockey signal as a tiebreaker under those conditions.

**Prizeland scoring re-check:**
- Prizeland's adjusted-field score was 78.6 (rank #3 in the 8-runner field).
- Original racecard said "model rank #2 vs market #8" — this was computed on the card-generation field (Precise already a NR at that run), giving a slightly different normalisation. Both representations are consistent with a genuine rank-price gap pick.
- The original selection logic holds up: Prizeland had strong rank-price gap value at 33/1 vs a model ranking well above its market position. The replacement (Cameo) scores 88.4 vs Prizeland's 78.6 — the replacement is a genuine improvement, not a like-for-like downgrade.

**Replacement pick: Cameo (Aidan O'Brien, £0.25 EW ~14/1 stale)**
- Decision note: `.squad/decisions/inbox/rusty-prizeland-replacement.md`
- Action owner: Linus (racecard HTML update)

## 2026-06-05 PM — Port Road NR replacement (16:40 HKJC, second swap)

**What:** Picked Triple Double A as 16:40 outsider replacement for Port Road (confirmed NR).

**Key inputs:**
- Race: 16:40 HKJC World Pool Handicap, Epsom Ladies Day, 29 runners
- NR signal: Steve verbal 15:46 BST + corroborated by Port Road absence in market-baseline.json
- Constraint: Outsider tier (£0.25 EW, ~24/1 price band), stale-price avoidance

**Analysis:**
- Screened 29-runner field for outsiders with poor recent form (5+ days since last run)
- Triple Double A emerges: OR 80 vs RPR 109 (29-pt gap — outlier width), distance winner (D badge), Hugo Palmer trainer, Saffie Osborne jockey
- Scoring delta vs Port Road: TS +20, RPR +2, OR +1, jockey/trainer both upgraded
- Runners discarded: Zarathos, Jimmy Speaking, Footwork (all recent-form stale-price traps — likely much shorter today)

**Confidence:** LOW/SPECULATIVE (standard EW outsider)

**Stale-price caveat:** ~23/1 (24.0 decimal) is 2026-06-02 synthetic; verify at rail before staking.

**Handoff:** Decision passed to Linus for HTML edits (Port Road row removed, Triple Double A row inserted with rationale + amber NR badge + stale-odds caveat).
