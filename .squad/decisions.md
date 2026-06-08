# Decisions

Append-only ledger of team decisions. Scribe merges entries from `decisions/inbox/`.

> **Archive note:** Entries from 2026-06-03 through 2026-06-05 PM have been archived to
> `.squad/decisions/archive/2026-06.md` by Scribe-19 on 2026-06-08 (publish-readiness
> sprint, decisions.md exceeded 51KB threshold). 2026-06-06 Derby Day content onwards
> remains live below.

---
**→ Ralph:** Hourly watchdog #1 continues through Sat ~21:30. Schedule #2 stopped earlier. No new monitor work needed.

---

## 2026-06-06 — Derby Day Morning Gate

### 2026-06-06T07:05+01:00: Saturday Blockers Resolution (Derby Day)
**By:** Danny (Lead)
**Requested by:** Steve (via race-day watchdog 07:00 gate)

#### BLOCKER #2 — Derby Race Time: RESOLVED ✅

**Verdict: 16:00 BST is CORRECT. No patch required.**

Sources confirming 16:00:
1. The Jockey Club / Epsom Downs official — https://www.thejockeyclub.co.uk/epsom-derby/plan-your-day/when-and-what-time/
2. HorseRacing.net racecard — https://www.horseracing.net/epsom/06-06-26
3. IrishRacing.com racecard — https://www.irishracing.com/racecards/Sat-6th-Jun-2026/Epsom/1600

The coordinator brief stating "16:30" was in error. `bets-2026-06-06.json` race_id `epsom-2026-06-06-1600` and Saturday HTML extracted times are both correct. No file changes needed.

#### BLOCKER #1 — Causeway NR: PATH C (Hybrid) ✅

**Chosen: (C) Annotate now, re-render only if more NRs surface from Livingston's 07:00 baseline.**

**Rationale (1 sentence):** Causeway is a £0.25 EW outsider that voids automatically at declarations — the financial risk is nil, re-rendering risks fresh bugs on Derby morning, and annotation takes 2 minutes with zero blast radius.

**What happens now:**
- NO re-render by Linus (unnecessary given £0.25 void-at-declarations + no visual confusion for Steve since he knows Causeway is out)
- Livingston's 07:00 baseline capture will confirm NR status from live RP scrape
- If Livingston's baseline surfaces ADDITIONAL NRs beyond Causeway → escalate to full re-render (Linus, Path A) before Steve's 10:00 GO/NO-GO
- If Causeway is the only NR → let it void naturally; it's already flagged in Livingston's report

**If escalation to Linus becomes necessary (scope brief):**
> **Linus brief (conditional — only if ≥2 NRs total):**
> Re-generate `outputs/racecard-2026-06-06.html` + `outputs/bets-2026-06-06.json` with ALL confirmed NRs removed (Causeway + any from 07:00 baseline). Preserve: all other picks, trifecta block (adjust box if #4 model-ranked horse drops), going advisory, outsider rationale for remaining runners. Source of truth for NR list: Livingston's baseline capture + RP declarations page. Do NOT touch `data/results/*.json`.

#### CHECKPOINT 4 — Saturday Operator Sequence & PROPOSED Rules

**Context:** Two rules remain PROPOSED (not ratified by Steve):
1. No manual override of sub-50 model scores without 2-PM sign-off
2. Saturday morning ≥30% steam/drift gate

**My call (Danny, Lead):**

**Operate under PROPOSED rule #2 as soft guidance today — no ratification required.**

Reasoning:
- Rule #2 has ZERO impact on Derby picks (no sub-50 picks exist on Saturday card per decisions.md line 1323)
- The mechanism is already in motion regardless: Livingston 07:00 baseline → Saul delta-check → Danny review → Steve 10:00
- If Saul's delta-check surfaces ≥30% movers, I will review them and flag to Steve with a binary HOLD/PULL recommendation
- This is operationally identical to ratification — but we're treating it as guidance not hard rule, so Steve retains full override authority at 10:00
- Formal ratification deferred to post-Derby (more data from Royal Ascot will strengthen the case)

**What Saul should expect:**
- Run delta-check by 07:30 as planned
- If ANY runner has moved ≥30% (steam or drift) vs the bets-file baseline price, flag it to Danny immediately
- I'll review and make a HOLD/PULL call before Steve's 10:00 window
- If no ≥30% movers: proceed to 10:00 GO/NO-GO with card as-is

**Rule #1 (sub-50 gate):** Not operationally relevant today — no sub-50 picks on Saturday card. Fully deferred to Royal Ascot data.

#### New Flags

None surfaced. Causeway is the only confirmed NR. Livingston's 07:00 baseline will be the authoritative check for any further NRs declared overnight.

#### Summary

| Item | Outcome |
|------|---------|
| Derby time | **16:00 BST confirmed** (3 sources) — no patch |
| Causeway NR | **Path C** — let void naturally; re-render only if more NRs surface |
| Linus brief written | **Conditional only** — fires if ≥2 NRs from baseline |
| PROPOSED rules | Operate as soft guidance; Saul runs delta-check as planned |
| New flags | None |

---

### 2026-06-06T07:08 BST: Saturday 07:00 baseline gate — capture complete
**By:** Livingston (scheduled watchdog tick, Derby Day)
**Requested by:** Steve

#### Baseline Capture Summary

| Field | Value |
|---|---|
| **Capture timestamp** | 2026-06-06T07:08:00.227074+01:00 BST |
| **Mode** | baseline (07:00 Saturday gate) |
| **Date** | 2026-06-06 |
| **Race count** | 8 races (all Epsom) |
| **Runner count (baseline)** | 101 confirmed runners |
| **Runner count (racecard input)** | 142 (pre-NR-filter) |
| **Probable NRs filtered** | 41 |
| **market-baseline.json size** | 39,019 bytes |
| **market-latest.json size** | 39,140 bytes (BASELINE_CAPTURE status) |

#### Race-level runner counts (post-NR filter)

| Off time | Race | Racecard | Baseline | Delta |
|---|---|---|---|---|
| 13:30 | Betfred Tattenham Corner Stakes G3 | 14 | 8 | −6 |
| 14:05 | Princess Elizabeth Stakes G3 | 13 | 9 | −4 |
| 14:40 | Coolmore Coronation Cup G1 | 8 | 6 | −2 |
| 15:15 | Betfred Dash Handicap (Heritage) | 34 | 18 | −16 (expected ballot) |
| 16:00 | Betfred Derby G1 | 18 | 14 | −4 (Causeway + 3) |
| 16:40 | Cherryfield Lester Piggott Hcp | 13 | 11 | −2 |
| 17:20 | HKJC Northern Dancer Hcp | 21 | 17 | −4 |
| 17:55 | JRA Tokyo Trophy Hcp | 28 | 18 | −10 (ballot + NRs) |
| **Total** | | **149*** | **101** | **−48*** |

*\*149 unique horses across card; ~142 after deduplication of cross-race entries (Desert Cop, Partisan Hero etc. entered in 2 races each).*

#### Going

Official going declared in racecard (from Racing Post 2026-06-03):
> **"Good to Soft (Good in places); 5f course Good (Light rain)"**

As of 07:08 BST: **no updated official going available from RP scrape** — the racecard `going` field remains the 2026-06-03 source. Based on the bets file weather advisory (River forecast: 5.2mm overnight rain, 60-80% probability of Soft by Derby post-time):
- Expected going: **Good to Soft → Soft possible by 16:00**
- Going advisory in bets file: use GREEN slip until official declarations; switch to HOLD slip if Soft declared
- Steve GO/NO-GO call at 10:00 should include going check

#### Key Pick Status

| Horse | Race | Baseline status | Price (synthetic) | Bets file price | Note |
|---|---|---|---|---|---|
| Item | 16:00 Derby G1 | ✅ CONFIRMED | 5.0 (4/1) | 3.25 (live override) | Synthetic price is 5.0; bets file live override was 3.25. Price gap expected — synthetic baseline. |
| Kinswoman | 15:15 Dash | ✅ CONFIRMED | 24.0 (23/1) | 24.0 | Stable |
| Allegresse | 16:40 Lester Piggott | ✅ CONFIRMED | 9.0 (8/1) | 9.0 | Stable |
| Lord Melbourne | 17:20 Northern Dancer | ✅ CONFIRMED | 13.5 (12/1) | 13.5 | Stable |
| **Dance In The Storm** | 17:55 Tokyo Trophy | ⚠️ **PROBABLE NR** | N/A | 18.5 (WIN £1.33) | **URGENT — WIN bet. Absent from RP live racecard 07:08. Verify before betting.** |
| **See The Fire** | 14:40 Coronation Cup G1 | ⚠️ **PROBABLE NR** | N/A | 13.0 (EW outsider £0.25) | Absent from RP live racecard 07:08. Coronation Cup now 6 runners. |
| Causeway | 16:00 Derby G1 | ❌ ABSENT | N/A | 29.0 (EW outsider £0.25) | Known NR since Friday gate. Confirmed. Danny reviewing HTML. |

#### Anomalies for Saul's Attention

##### ⚠️ HIGH PRIORITY — New probable NRs on bet horses
1. **Dance In The Storm**: WIN bet £1.33 at 17:55 — probable NR per RP scrape. **If confirmed, this eliminates the main late WIN from the portfolio and removes one leg of the Kinswoman+Dance In The Storm double (£0.50).** Total stake at risk: £1.33 WIN + £0.50 double = £1.83.

2. **See The Fire**: EW outsider £0.25 at 14:40 Coronation Cup — probable NR per RP scrape. Stake at risk: £0.25.

##### ℹ️ MEDIUM — Field compression
- **Coronation Cup G1 14:40** now 6 runners (was 8). Place terms may change (bookmaker by bookmaker). Affects any remaining EW bets on this race.
- **Dash Handicap 15:15** down to 18 from 34 — expected ballot reduction for this heritage race. Kinswoman confirmed.
- **Derby 16:00** confirmed at 14 runners — consistent with 2026-06-05 RP check (4 NRs: Causeway, Constitution River, Endorsement, Proposition all absent).

##### ℹ️ LOW — Price source note
All baseline prices are **synthetic (from racecard 2026-06-02)** or **ante_post (RP 2026-06-02)**. No live market prices are available (RP odds are JS/WebSocket, not in SSR HTML). Saul's delta-check vs Friday closing prices will show ~0% movement everywhere — this is expected behaviour. Only the NR filter (reduced field) is meaningful data from this scrape. Live price comparison requires manual override CSV (see runbook).

##### ℹ️ NOTE — Item price discrepancy
Item shows **5.0 (4/1)** in baseline (synthetic, 2026-06-02 source). Bets file used **live override 3.25 (9/4)**. The 3.25 was a manually confirmed live price (applied when the bet slip was built). The synthetic baseline correctly anchors at 5.0 — this is expected and is NOT a market move signal. The actual live Derby market should be checked at 09:00–10:00 gate.

#### Next steps (per operator sequence)

- **~07:30** → Saul: delta-check vs Friday close prices (note: prices are synthetic/flat, delta will be neutral; NR flags are the actionable findings)
- **If ≥30% steam/drift on any pick**: spawn Danny for review (PROPOSED rule)
- **By 10:00** → Steve: GO/NO-GO call on Derby Day bets. **Verify Dance In The Storm and See The Fire NR status before this call.**
- **Going check**: Official going update expected by ~09:00 from Epsom Racecourse. Key trigger: if Soft declared → cancel Item WIN, switch to HOLD slip.

**Files written:**
- `data/enrichment/market-baseline.json` — 39,019 bytes, 101 runners, status: baseline
- `data/enrichment/market-latest.json` — 39,140 bytes, 101 runners, status: BASELINE_CAPTURE
- `.squad/decisions/inbox/livingston-sat-baseline-NRs.md` — full NR list with bet impact

---

### 2026-06-06T07:08 BST: Saturday NR check — 07:00 baseline gate
**By:** Livingston (Derby Day baseline capture)
**Source:** RP __NEXT_DATA__ live racecard scrape at 07:08 BST

#### ⚠️ PROBABLE NEW NON-RUNNERS — BET IMPACT (URGENT for Danny / Steve)

These horses are **present in the locked racecard HTML** but **absent from the RP live racecard** at 07:08 BST. Filtered as probable NRs by the morning_odds script. **Requires official confirmation before betting.**

##### 1. DANCE IN THE STORM — 17:55 JRA Tokyo Trophy Handicap
- **Bet impact: WIN £1.33 @ 18.5 (35/2)** — Steve's main late-race WIN
- Bets file: `epsom-2026-06-06-1755`, stake £1.33, edge +93.3%
- Status: ABSENT from RP racecard at 07:08. **Must be verified before bet placement.**
- Action required: Danny / Steve to confirm via official Epsom declarations or bookmaker.

##### 2. SEE THE FIRE — 14:40 Coolmore Coronation Cup G1
- **Bet impact: outsider EW £0.25 @ 13.0 (12/1)** — Kaylee #1 vs market #6
- Bets file: `epsom-2026-06-06-1440`, outsiders block
- Status: ABSENT from RP racecard at 07:08. Coronation Cup now shows 6 confirmed runners (was 8).
- Action required: Confirm runner status. If NR, EW outsider bet is void.

#### ✅ KNOWN NR — CONFIRMED

- **Causeway** — 16:00 Derby G1: CONFIRMED NR (absent from RP since 2026-06-05; known from Friday gate). Still present in locked racecard HTML. Danny reviewing HTML fix separately.
  - Bet impact: outsider EW £0.25 in bets file — stake is void if officially NR.

#### Other horses from bets file — STATUS OK

- **Item** — 16:00 Derby G1: IN BASELINE at 5.0 (4/1). Bets file live override was 3.25; synthetic racecard price 5.0. Runner confirmed.
- **Kinswoman** — 15:15 Dash Handicap: IN BASELINE at 24.0 (23/1). Confirmed runner.
- **Allegresse** — 16:40 Lester Piggott Handicap: IN BASELINE at 9.0 (8/1). Confirmed runner.
- **Lord Melbourne** — 17:20 Northern Dancer Handicap: IN BASELINE at 13.5 (12/1). Confirmed runner.

#### Additional NRs removed by RP scrape (non-bet impact, for information)

The full list of 41 horses removed as probable NRs at 07:08 (racecard count 142 → live 101):

**13:30 Tattenham Corner G3** (14→8): Audience, Cowardofthecounty, Copacabana Sands, Humam, Lake Forest, Linwood

**14:05 Princess Elizabeth G3** (13→9): Alobayyah, Celestial Orbit, Sindria, Sunlit Uplands

**14:40 Coronation Cup G1** (8→6): See The Fire, Sunway

**15:15 Dash Handicap** (34→18): Counsel, Desert Cop, Fierce Fortitude, Forager, Francisco's Piece, Golden Long, Law Of Average, Marching Mac, Michaela's Boy, Nogo's Dream, Oneforthegutter, Seven Questions, Spangled Mac, Sturlasson, Tatterstall, The Bell Conductor

**16:00 Derby G1** (18→14): Causeway, Constitution River, Endorsement, Proposition

**16:40 Lester Piggott Hcp** (13→11): My Mate Roger, Tai Hang Pegasus

**17:20 Northern Dancer Hcp** (21→17): Patagonia Girl, Sunway *(note: Sunway appears in both 14:40 and 17:20 listings — racecard deduplication artefact)*, Will Scarlet, Oneforthegutter *(possible dedup)*

**17:55 Tokyo Trophy Hcp** (28→18): Cinque Verde, Dance In The Storm, Toyotomi, Veblen Good, Winged Messenger + others in Dash double-runners (Desert Cop, Francisco's Piece, Golden Long, Seven Questions, Spangled Mac, Stormy Impact, Star Chorus)

**Note:** All NR filtering is based on RP __NEXT_DATA__ scrape. RP does not publish official Epsom declarations — this is a best-available live confirmation. Cross-reference against BHA/Epsom official declarations when available.


---

## 2026-06-06 — Saturday Rescore & Card Refresh Complete (Rusty-4 → Linus-11 → Saul → Linus-12 → Danny)

**Date:** 2026-06-06T12:13:00+01:00  
**Crew:** Rusty (Signal Engineer), Linus (Reports Engineer), Saul (Tester), Danny (Lead)  
**Requested by:** Steve Newby  
**Verdict:** ✅ GO — Card ready to place

### Pipeline Summary

1. **Rusty full-rescore (11:30)** — Against market-latest.json (11:26 BST, 100 active runners). HOLD card confirmed GTS with ongoing rain. Two v1 picks invalidated (Illinois: rank 6/6, rank_gap 0; Christmas Day: rank_gap +0.5 <threshold). Lord Melbourne UPGRADED to WIN (model rank 1/17, rank_gap +13, going_fit 78). New winners: Action (13/1), Princess Child (11/1), Folk Pageant (6/1), Another Baar (39/1 speculative), Lord Melbourne (19/1).

2. **Linus re-render v3 (11:52)** — Regenerated outputs/racecard-2026-06-06.html + outputs/bets-2026-06-06.json reflecting Rusty slate. Compliance check: all picks sourced from market-latest, no NR swaps introduced, all prices fractional + exact match vs market.

3. **Saul Section D validation (12:12)** — 5 PASS / 2 WARN / 0 FAIL. Gates: live-runner ✅, NR-swap pre-check ✅, sub-50 score ✅, going_fit ≥40 ✅, price sanity ✅. WARN 1 (Action model_score label cosmetic only); WARN 2 (Lord Melbourne market drift 12/1→19/1, requires live-price check before placing). Verdict: AMBER — ready to ship once Steve acknowledges WARN 2.

4. **Linus trifecta inject (12:07)** — 3-horse box (Action banker, Benvenuto Cellini, Item) × 6 combos × £1 = £6.00. Conservative sizing post-Friday -£10.07. All WIN bets unchanged.

5. **Danny final GO/NO-GO (12:13)** — Card ready to bet. Bets JSON well-formed, all picks defensible, one operational risk: Lord Melbourne drift — Steve to check live price 17:15 before placing. Total outlay £11.50 (£5.50 picks + £6.00 trifecta). MAX potential ~£74 + trifecta upside.

### Files Produced

- data/enrichment/rusty-rescored-2026-06-06.json — Full rescore with all races + flags
- outputs/racecard-2026-06-06.html (v3) — HOLD card template, Rusty pick slate, Saul handoff embedded
- outputs/bets-2026-06-06.json (v3 + trifecta) — 10 pick entries + 1 trifecta, total £11.50

### Key Decisions

1. **HOLD card is correct.** Going GTS with ongoing rain. Soft-preference upgrades (Lord Melbourne, Princess Child) definitively outperform standard card.
2. **No picks invalidated on Saul validation.** Both WARN items are Steve-awareness, not card edits. Action label cosmetic; Lord Melbourne drift warrants live-price check but model conviction stands.
3. **Trifecta is speculative add-on.** Conservative sizing £6 vs Friday loss. Skip if cashflow tight — entirely optional.

### Card Status

✅ **READY** — Steve may place at posted stakes once WARN 2 live-price check completed pre-17:20.

---

### 2026-06-06T11:30:00+01:00: Saturday Rescore — Rusty Signal Output (HOLD Card)
**By:** Rusty (Signal Engineer)
**Requested by:** Steve Newby
**Input:** market-latest.json (11:26 BST, 100 active runners), market-baseline.json (07:08 BST), Livingston full-refresh + NR delta, Saul validation checklist
**Output:** data/enrichment/rusty-rescored-2026-06-06.json

**5-Line Summary: Biggest Shifts vs Baseline**

1. **Benvenuto Cellini (Derby 16:00): 9/4 ante-post → Evs** — The only genuine steam signal on the card (38.5% from a real baseline). MARKET_STEAM_MAJOR + EDGE_ERODED flags applied. Ground concern persists.
2. **Lord Melbourne (Northern Dancer 17:20) UPGRADED to WIN candidate** — Model rank 1/17, rank_gap +13, going_fit 78. Strongest signal on the full card. Upgrades from bets-file EW outsider to WIN candidate.
3. **Both Linus-v1 picks invalidated**: Illinois (14:40) scores model_score 12.1 → NO_OVERRIDE, rank_gap 0; Christmas Day (16:00) rank_gap only +0.5, fails ≥+2 WIN threshold.
4. **Kinswoman (Dash 15:15) price-eroded**: Synthetic 23/1 → real 4/1 triggered EDGE_ERODED flag per rule.
5. **Going confirmed GTS with ongoing rain: HOLD card correct.** Four Derby runners REJECTED on going_fit <40.

**HOLD Card vs Standard Card Confidence: HIGH**

HOLD card is definitively correct. Proceeding with HOLD card path recommended.

---

### 2026-06-06T11:52:00+01:00: Saturday Re-render v3 — Linus Output Summary
**By:** Linus (Reports Engineer)
**Requested by:** Steve Newby
**Trigger:** Rusty rescore complete (11:30 BST). Two v1 picks invalidated; Lord Melbourne upgraded to WIN. Dance In The Storm confirmed NR. HOLD card is live target.
**Files written:** outputs/racecard-2026-06-06.html (v3), outputs/bets-2026-06-06.json (v3)

**5-Line Summary: Pick Changes from v1**

1. **14:40 Illinois REMOVED → NO_BET**: Rusty rescore: model_score 12.1, rank last in 6-runner field (rank 6/6), rank_gap 0. Market at 39/1 (drifted +90.5%).
2. **16:00 Christmas Day REMOVED → Action (13/1) WIN**: Christmas Day rank_gap +0.5 fails the ≥+2 WIN criterion. Replaced by Action: model rank 3/14, rank_gap +3.5.
3. **17:20 Lord Melbourne UPGRADED: EW outsider → WIN candidate (19/1)**: Model rank 1/17, rank_gap +13, score 78.8, going_fit 78.
4. **14:05 Princess Child (11/1) WIN added**: Model rank 3/9, rank_gap +3.5, score 77.5.
5. **15:15 Another Baar (39/1) WIN + Ziggy's Triton (32/1) EW added**: Both carry COMPRESSED_RANGE_CAUTION.

**HOLD Card vs Standard Card Status**

HOLD card is the live target. outputs/racecard-2026-06-06.html — REGENERATED as v3 using HOLD card template structure with Rusty's full pick slate.

---

### 2026-06-06T12:12:00+01:00: Section D Validation — Saturday Card
**By:** Saul (Tester)
**Requested by:** Steve Newby
**Artefacts validated:** outputs/racecard-2026-06-06.html (v3, 11:58 BST), outputs/bets-2026-06-06.json (v3, 11:58 BST)

**AGGREGATE VERDICT: AMBER — SHIP AFTER STEVE ACKNOWLEDGES 2 WARNS**

Two WARNs present. Neither requires a card or bets-file edit. Both are Steve-awareness items before placement. No pick should be pulled. Danny: clear to GO once Steve confirms he has seen the two WARN notes below.

**Section D Gate Summary (All 5 gates PASS)**

- D1 — Live-runner gate (all 7 picks declared) ✅ ALL CLEAR
- D2 — NR-swap pre-check ✅ ALL CLEAR
- D3 — Sub-50 score gate (min: Folk Pageant 64.1) ✅ ALL CLEAR
- D4 — going_fit ≥ 40 floor (min: Another Baar 60) ✅ ALL CLEAR
- D5 — Price sanity (±0% card vs market-latest) ✅ ALL CLEAR

**WARNs Summary (for Danny / Steve)**

**WARN 1 — Action (16:00) model_score label:** Bets JSON and HTML card show 69.4; this is actually final_signal after headgear ×0.90 downgrade. Sub-50 gate passes. No functional failure, cosmetic label only. Action: Accept, do not pull.

**WARN 2 — Lord Melbourne (17:20) market drift:** Price drifted 12/1 → 19/1 (+54% decimal). 2026 form poor. Model rank 1/17 and rank_gap +13 remain valid on GTS. Action: Accept. Steve to check live market price before placing 17:20 bet.

---

### 2026-06-06T12:07:00+01:00: Derby trifecta box injection
**By:** Linus (Reports Engineer) — requested by Steve Newby
**Task:** Additive trifecta side-bet injection into AMBER GO card. WIN rows NOT modified.

**Chosen horses (3-horse trifecta box):**
- ★ BANKER — Action (score 77.1 · going_fit 68 · 13/1)
- Leg 2 — Benvenuto Cellini (score 88.0 · going_fit 50 · Evs)
- Leg 3 — Item (score 85.8 · going_fit 48 · 7/2)

**Rationale:** Top 3 by Rusty model_score in 14-runner Derby field. Score gap from rank-3 to rank-4 is 7.0 points — sufficient separation.

**Stake:** £1.00 per combo × 6 combos = £6.00 total.

**All active WIN bets unchanged** — Action is also trifecta banker but WIN entry unmodified.

---

### 2026-06-06T12:13:30+01:00: Saturday Card — Final GO/NO-GO
**By:** Danny (Lead)
**Requested by:** Steve Newby
**Inputs reviewed:** Saul AMBER GO, bets-2026-06-06.json (v3 + trifecta), Linus v3 + trifecta inject, Rusty rescore

**VERDICT: ✅ GO**

### 1. Is the card ready to bet?
**Yes.** Bets JSON well-formed, 10 pick entries + 1 trifecta, all statuses correct, all prices fractional and match market-latest. One minor JSON cosmetic: total_outlay still reads £5.50 (pre-trifecta); true outlay £11.50.

### 2. Are the picks defensible if Steve loses?
**Yes, all 7 picks + trifecta.** Another Baar (39/1) explicitly speculative. Lord Melbourne (19/1): rank 1/17, rank_gap +13, going_fit 78, GTS Epsom winner — model conviction overrides drift. Derby trifecta (£6.00): top-3 by model_score with 7pt gap to rank-4.

### 3. The one thing Steve must remember 12:15→17:20?
**Live-price check before placing each bet — especially Lord Melbourne at 17:20.** If LM has drifted to 25/1+ at the off, halve stake or pull.

**Carve-outs: NONE.** All 7 picks + trifecta clear to place at posted stakes.

**Message to Steve**

Card is GO. Place exactly as written in bets-2026-06-06.json — total outlay £11.50 (£5.50 picks + £6.00 trifecta), max potential ~£74 + trifecta upside. Trifecta is optional cash-flow cover — skip if you'd rather hold the £6 back. Good luck.



---

## 2026-06-06 Saturday Derby Day — Full Consolidation

**Master entry combining:**
- 11:26 Livingston fullrefresh (prices, going, NR delta)  
- 11:01 Saul validation-checklist (4 hard rules, lessons, trifecta logic)
- 11:30 Rusty rescore (major signals, pick changes, invalidations)
- 11:52 Linus rerender-v3 (4 hard rules compliance, pick slate)
- 12:12 Saul Section D validation (AMBER GO, 2 WARNs)
- 12:07 Linus trifecta injection (3-horse box, £6.00)
- 12:13 Danny go-no-go (✅ GO verdict)
- 12:12 Rusty 17-55 alternative (Apollo One WIN @ 7/1)
- 12:17 Linus 17-55 injection (override VOID → Apollo One)

---

### EXECUTIVE SUMMARY

**FINAL VERDICT: ✅ GO** — Saul AMBER GO (2 WARNs, both handled), Danny green-lit, all 8 picks + trifecta ready. Total outlay: £12.50 (£6.50 bets + £6.00 trifecta).

**Card state:** 8 picks live (Princess Child 11/1, Another Baar 39/1, Ziggy's Triton 32/1 EW, Action 13/1, Folk Pageant 6/1, Lord Melbourne 19/1, Prydwen 17/1 EW, Apollo One 7/1), Derby trifecta (Action banker, Benvenuto Cellini, Item; £6 box).

**Key decisions:**
1. **HOLD card confirmed** — Going Good To Soft with ongoing rain; soft-weighting elevation for Lord Melbourne, Princess Child, Folk Pageant. Standard card NOT used.
2. **Two v1 picks invalidated** — Illinois (14:40 score 12.1, rank last), Christmas Day (16:00 rank_gap +0.5 below ≥+2 threshold).
3. **Lord Melbourne upgraded to WIN** — model rank 1/17, rank_gap +13, score 78.8; November Handicap soft 2024, GTS Epsom Sept '25 winner. **WARN 2: Drifted 12/1 → 19/1. Steve to check live price before 17:20 placement; if 25/1+, reduce stake or EW only.**
4. **Action replaces Christmas Day in Derby** — model rank 3/14, rank_gap +3.5, score 69.4 (final_signal post-headgear). **WARN 1: JSON/card show 69.4 as label; actually final_signal, not raw. No functional failure.**
5. **Dance In The Storm VOID applied** — 17:55 Tokyo Trophy NR, original £1.33 WIN voids. **Rusty's conditional pick: if Steve approves, Apollo One (rank 1/16, score 95.0, 7/1) replaces as WIN @ £1.00.** Steve approved at 12:15 BST. Apollo One injected.
6. **Trifecta: 3-horse box** — Action (banker, 13/1), Benvenuto Cellini (rank 1, Evs, EDGE_ERODED flag), Item (rank 2, 7/2); gap Action-3 to Maltese Cross-4 is 7.0pts. £1.00/combo × 6 = £6.00. Causeway (confirmed NR) excluded; box unaffected (still 3 horses).

---

### DECISIONS DETAILED

**1. Livingston (11:26 BST) — Full Refresh, Data Layer**
- RP primary scrape: SUCCESS — 101 runners, all 8 races declared, forecast odds captured
- Sporting Life fallback: FAILED — 404 on all 6 strategies (no Playwright for JS-only site)
- Going declared: GOOD TO SOFT (Derby), GOOD (5f), GoingStick 6.0/6.2, rain ongoing
- **→ HOLD path active** — going deterioration risk material with continued rain through afternoon
- NR delta: Be The Standard 16:40 (new since 07:08), 3 pre-baseline NRs confirmed
- Price sample: Benvenuto Cellini 9/4 → Evs (steam signal flagged), Item 4/1 → 7/2, Kinswoman 23/1→4/1 (synthetic→real, not steam)
- **Decision: HOLD card soft-weighting is definitively correct. Market prices all updated to RP forecast (11:26).**

**2. Saul (11:01 BST) — Validation Checklist (Input to Linus)**
- 4 Hard Rules ratified (commit e7061d3, Friday retro Stage 3): Live-runner gate, NR-swap pre-check, runner-validity distinction, anti-fabrication
- Selection rigor lessons from Friday -86.7% ROI: 
  - Market steam ≥30% inward = edge-erosion flag (both steamed-favs failed)
  - RPR-OR gap demoted to CORROBORATING (not PRIMARY for outsiders)
  - going_fit <40 = reject outsider (Arctic Thunder case: 35.0, 6th/16)
  - Sub-50 score override = PROPOSED NOT RATIFIED (zero Saturday impact — no sub-50 picks)
- Outsider rules: if no 10/1+ runner in race → NO_BET, don't force. If going_fit <40 → reject candidate.
- Trifecta: Causeway confirmed NR; box drops to 3 horses effective (Causeway EW voids, trifecta still runs with 3).
- **Decision: 4 hard rules are non-negotiable gates. Apply rigorously to Saturday picks.**

**3. Rusty (11:30 BST) — Rescore Narrative**
- Biggest shifts vs baseline:
  - Benvenuto Cellini: 9/4 → Evs (38.5% steam, MARKET_STEAM_MAJOR flag, ground concern persists)
  - Lord Melbourne UPGRADED to WIN: rank 1/17, gap +13, going_fit 78, no flags
  - Illinois invalidated: score 12.1, rank 6/6, gap 0 (NO_OVERRIDE)
  - Christmas Day invalidated: score 66.0, rank_gap +0.5 (below ≥+2 WIN threshold)
  - Action new WIN: rank 3/14, gap +3.5, score 69.4, cheekpieces first-time
  - Another Baar WIN: 39/1, gap +15, SYNTHETIC_BASE_CAVEAT + COMPRESSED_RANGE_CAUTION
  - Kinswoman EDGE_ERODED: synthetic 23/1 → real 4/1 (price revelation, no longer overlaid)
- HOLD card soft-weighting confirmed HIGH confidence. Going deterioration risk non-trivial.
- **Decision: Replace Illinois + Christmas Day. Upgrade Lord Melbourne EW→WIN. Inject Another Baar + Ziggy's Triton at speculative stakes.**

**4. Linus v3 (11:52 BST) — Rererender**
- v1 picks removed: Illinois (14:40), Christmas Day (16:00)
- v1 picks upgraded: Lord Melbourne (EW→WIN)
- New picks added: Princess Child (14:05), Action (16:00), Another Baar + Ziggy's Triton (15:15)
- HOLD card path confirmed live target
- Saul Rule 3 compliance: runner-validity distinction as separate amber indicators (price-stale vs runner-status)
- **Decision: outputs/racecard-2026-06-06.html v3, outputs/bets-2026-06-06.json v3 generated with Rusty's full slate. Handoff to Saul Section D validation.**

**5. Saul Section D (12:12 BST) — Card Validation**
- All 5 gate criteria passed cleanly:
  - D1 (live-runner): all 7 picks declared, non_runner: false
  - D2 (NR-swap): only new NR is Be The Standard (16:40, not in scoring)
  - D3 (sub-50): min score Folk Pageant 64.1, all ≥50
  - D4 (going_fit ≥40): min Another Baar 60, all ≥40
  - D5 (price sanity ±10%): all 7 picks exact match card-to-market-latest
- **2 WARNs identified (non-blocking):**
  - WARN 1 — Action (16:00): model_score label 69.4 is actually final_signal post-headgear (raw 77.1). Sub-50 gate passes either way. **Action: Accept, cosmetic label only, do not pull.**
  - WARN 2 — Lord Melbourne (17:20): drifted 12/1 → 19/1 (+54%), RP diomed says "market check needed", 2026 form poor at 1m2f. Model rank 1/17 and rank_gap +13 on GTS 1m4f remain strongest signals. **Action: Accept upgrade. Steve to check live price before 17:20; if 25/1+, reduce stake or EW only. Do not pull.**
- **Decision: AMBER GO — ship after Steve acknowledges WARN 2. Both WARNs are Steve-awareness items, no card/bets-file edits required.**

**6. Linus trifecta (12:07 BST) — Derby 3-Horse Box**
- Top 3 by model_score: Action (banker, 77.1), Benvenuto Cellini (88.0), Item (85.8)
- Gap Action-3 to Maltese Cross-4: 7.0pts — clean separation justifying 3-horse box not wider cover
- Causeway confirmed NR — excluded (EW voids, trifecta still runs with 3 effective)
- Stake: £1.00/combo × 6 combos = £6.00 total (conservative sizing after Friday -£10.07)
- **Decision: Trifecta injected as additive side-bet, £11.50 → £12.50 total outlay. Optional — skip if cashflow tight.**

**7. Danny go/no-go (12:13 BST) — Final Verdict**
- Card is GO. Bets JSON well-formed, 8 picks + trifecta, all statuses correct, prices match market-latest.
- All picks defensible if loss (Another Baar 39/1 SYNTHETIC_BASE_CAVEAT + min stake, Lord Melbourne rank 1/17 + going_fit 78, trifecta 3-horse box clean).
- Operational reminder to Steve: live-price check before placing each bet, especially Lord Melbourne at 17:20.
- **Decision: ✅ GO. Place exactly as written in bets-2026-06-06.json, total outlay £12.50 (£6.50 picks + £6.00 trifecta), max potential ~£82 + trifecta upside.**

**8. Rusty 17-55 alternative (12:12 BST) — Apollo One Conditional Pick**
- Context: Dance In The Storm confirmed NR; original VOID called. Rusty flagged Apollo One (rank 1/16, score 95.0, 7/1) as conditional replacement if Steve approves.
- Gate check: all 16 live-runner declared, Dance In The Storm confirmed NR in market-latest. Apollo One live, non_runner: false.
- Model signals: rank 1/16, rank_gap +3, score 95.0, going_fit ≥50 (assumed — "acts on any ground", placed 2nd 2023 + 3rd 2024 in same race under GTS conditions at Epsom)
- Flags: SYNTHETIC_BASE_CAVEAT (baseline 17/1 synthetic → 7/1 real via OR-model repricing, not steam), GOING_FIT_CAUTION (precautionary — going_fit not persisted in VOID data, but course form implies ≥50)
- Stake: £1.00 WIN @ 7/1 (step-down from voided £1.33 @ 35/2; reflects end-of-card position and precautionary flag)
- **Decision: Apollo One injected as WIN @ 7/1, £1.00, replacing voided Dance In The Storm. Steve approved at 12:15 BST.**

**9. Linus 17-55 injection (12:17 BST) — Override Execution**
- Replaced 17:55 VOID block with Apollo One WIN panel (7/1, rank 1/16, gap +3, score 95.0)
- Two separate amber indicators (Saul Rule 3): SYNTHETIC_BASE_CAVEAT + GOING_FIT_CAUTION (precautionary)
- Updated bets JSON: status VOID→WIN, price null→7/1, stake null→£1.00, flags updated
- Metadata updated: total_outlay £5.50→£6.50, win_bets_count 5→6, void_races 1→0, max_potential £74.25→£82.25
- HTML header NOT updated per guardrails (cosmetic only — card shows £5.50, actual £6.50 live in JSON portfolio_summary)
- **Decision: 17:55 row finalized. 8 picks + trifecta ready for placement. No further handoffs needed.**

---

### FILES WRITTEN / TOUCHED (for commit)

- outputs/racecard-2026-06-06.html (v3 → v4 after 17-55 injection)
- outputs/bets-2026-06-06.json (v3 → v4 after 17-55 injection)
- data/enrichment/market-latest.json (RP prices 11:26 BST, 100 active runners)
- data/enrichment/racingpost-2026-06-06.json (RP scrape, 101 runners, all prices)
- data/enrichment/going-2026-06-06.json (going declaration, GoingStick, HOLD flag)
- data/enrichment/rusty-rescored-2026-06-06.json (rescored artifacts)

---

**FINAL CARD STATE (8 picks + 1 trifecta):**

| Time | Pick | Type | Price | Stake | Model Signal | Flags |
|------|------|------|-------|-------|--------------|-------|
| 13:30 | NO_BET | — | — | — | — | — |
| 14:05 | Princess Child | WIN | 11/1 | £1.00 | rank 3/9, gap +3.5, score 77.5 | — |
| 14:40 | NO_BET | — | — | — | — | — |
| 15:15 | Another Baar | WIN | 39/1 | £0.25 | rank 3/20, gap +15, score 86.2 | SYNTHETIC_BASE_CAVEAT, COMPRESSED_RANGE_CAUTION |
| 15:15 | Ziggy's Triton | EW | 32/1 | £0.25 | final_signal 85.5, going_fit 68 | COMPRESSED_RANGE_CAUTION |
| 16:00 | Action | WIN | 13/1 | £1.00 | rank 3/14, gap +3.5, score 69.4 | — |
| 16:40 | Folk Pageant | WIN | 6/1 | £1.50 | rank 2/10, gap +2, score 64.1 | — |
| 17:20 | Lord Melbourne | WIN | 19/1 | £0.75 | rank 1/17, gap +13, score 78.8 | UPGRADED_EW_TO_WIN, **WARN 2: market drift 12/1→19/1** |
| 17:20 | Prydwen | EW | 17/1 | £0.25 | score 62.9, going_fit 68 | — |
| 17:55 | Apollo One | WIN | 7/1 | £1.00 | rank 1/16, gap +3, score 95.0 | SYNTHETIC_BASE_CAVEAT, GOING_FIT_CAUTION (precautionary), **OVERRIDE of VOID** |

**Derby Trifecta (3-horse box):** Action (banker), Benvenuto Cellini, Item | £6.00 stake | 6 combos

**Header:** ✅ Saul AMBER GO · Danny GO · £12.50 combined (£6.50 bets + £6.00 trifecta) | Max potential ~£82 + trifecta upside

---

**DECISIONS RECORDED BY:** Scribe (merger + consolidation) on 2026-06-06 12:18 BST
**AGENTS INVOLVED:** Livingston, Saul (×2 entries), Rusty (×2 entries), Linus (×3 entries), Danny
**ARCHIVE STATUS:** decisions.md size post-merge will exceed 51KB; 7-day archive gate active (trigger: entries >7 days old)


---

## 2026-06-07 — v0.4 wave-1 publish-readiness sprint (GREEN)

Parallel 5-agent sprint to land the systemic fixes earned from Derby Day. All four work items shipped GREEN, gate-reviewed 🟢 GO by Saul on 2026-06-08.

### 2026-06-07T17:08+01:00: market_drift.py shipped (Rusty-7)

**By:** Rusty (Signal Engineer)
**Requested by:** Steve
**What:** New `src/market_drift.py` — gate-only modifier earned from Lord Melbourne's +53.8% drift call on Derby Day (5th place, vindicated Saul's WARN 2). Weight = 0.0 in scoring composite (does not disturb 1.0000 weight sum). Pure odds arithmetic, zero hardcoded names/dates/courses.

**Gate thresholds:**

| Condition | Multiplier | Flag | Tier override |
|---|---|---|---|
| `|drift_pct| < 30` | 1.0 | — | — |
| `≥ 30, drift > 0` | 0.90 | DRIFT_WARN | — |
| `≥ 30, drift < 0` | 1.0 | STEAM_NOTED | — |
| `≥ 50, drift > 0` | 0.80 | DRIFT_CRITICAL | SPECULATIVE |
| missing data | 1.0 | MARKET_DATA_MISSING | — |

**Public API:** `parse_fractional_odds`, `assess_market_drift`, `load_market_drift_data`, `market_drift_signal`. Module returns flat dict `{score, flags, adjusted_final_signal_multiplier, confidence_tier_override}`.

**Why fractional-over-decimal preference:** Derby Day surfaced a synthetic-price artefact — Lord Melbourne's baseline stored `decimal_odds: 13.5` but `fractional_odds: "12/1"` (= 13.0). Decimal would give drift = 48.1% (misses ≥50 gate); fractional gives 53.8% (correct DRIFT_CRITICAL).

**Why weight = 0.0:** This is a gate, not a score component. Adding to weighted sum would double-count drift already implicit in class/form signals (Danny gate-vs-average principle).

**Tests:** `tests/test_market_drift.py` — 46/46 PASS. Coverage: Derby Day actuals (Action +7.7%, Lord Melbourne +53.8%, Benvenuto Cellini −38.5%), Evs parsing (5 variants), boundary tests (30/50/29.99/−30), output schema, missing-data edges.

**Integration hook:** Module docstring example shows how to wire into report.py / scoring.py — deferred to follow-up. `src/scoring.py` not touched.

### 2026-06-07T17:08+01:00: render_header() JSON-driven refactor (Linus-14)

**By:** Linus (Reports Engineer)
**Requested by:** Steve
**What:** Refactored racecard HTML header to compute entirely from `outputs/bets-{date}.json` via new `render_header()` in `src/report.py`. Added `bets_json_path` param to `render_card()` in `src/racecard.py`. Templates updated for WIN/EW + trifecta split, validation tag, richer NR line. `outputs/bets-2026-06-06.json` extended with top-level `meta` block.

**Why:** Recurring publish blocker (Saul Derby Day audit, blocker #3) — after every scoring injection the HTML header showed stale values (£5.50 vs correct £12.50) because totals were hardcoded in template, not recomputed from source JSON. Coordinator was manually patching after each Linus injection.

**Linus authority clarified (docstring):** Any change to header fields (totals, NR line, validation tag, bet count) is in Linus's scope whenever bets JSON changes. No coordinator escalation required. This is the systemic fix.

**Schema extension** — bets-{date}.json now supports optional `meta`:

```json
{
  "meta": {
    "card_date": "YYYY-MM-DD",
    "course": "Epsom",
    "validation": "string or null",
    "generated_at": "ISO datetime"
  },
  "bets": [...]
}
```

Renderer handles missing `meta` gracefully (defaults: course=Epsom, validation=null, no crash). Backward compat verified: `test_no_meta_no_crash` PASS.

**EW math:** `winew_total += unit * 2 if status == "EW" else unit` — double-stake applied correctly (BETS_DERBY_DAY fixture has 2 EW entries, both double-counted). VOID/NR routed to nr_horses list and excluded from totals.

**Proof:** `outputs/racecard-2026-06-06-v04-verified.html` line 191: `WIN/EW outlay: £6.50 (+ £6.00 trifecta = £12.50)` — confirmed.

**Files:** MODIFIED report.py (added `_parse_stake_amount`, `render_header`), racecard.py (`bets_json_path` param, lazy import), templates/racecard.html.j2, templates/racecard.css (`.subtotal-note`, `.validation-tag`, `.nr-reason`), outputs/bets-2026-06-06.json (meta block). CREATED tests/test_render_header.py (22 tests), outputs/racecard-2026-06-06-v04-verified.html (proof).

**Tests:** 22/22 PASS.

### 2026-06-07T17:08+01:00: .env.example + check_env.py validator (Danny-2)

**By:** Danny (Lead)
**Requested by:** Steve
**What:** Resolution of Blocker #2 from publish-skill audit — undocumented credentials + .env exposure risk. Derby Day discovered `SPORTINGLIFE_USER` / `SPORTINGLIFE_PASS` were not set anywhere and no startup check caught the gap, causing Sporting Life scraper to silently return a 373-byte SPA shell.

**Env-var audit:** `Select-String` across `src/`, `scripts/`, `tests/` found ZERO existing `os.environ` / `os.getenv` calls. All credential use was either hardcoded paths (ATR cookie) or entirely absent (SL auth).

**Decisions:**

| # | Decision |
|---|---|
| 1 | `SPORTINGLIFE_USER` + `SPORTINGLIFE_PASS` are REQUIRED env vars |
| 2 | `ATR_COOKIE_FILE` is OPTIONAL, default `.cookies/attheraces.txt` |
| 3 | `RACING_API_KEY` reserved as OPTIONAL (future, v0.5+ live-price) |
| 4 | `.env.example` = single source of truth for placeholder format (`<…>` tokens) |
| 5 | `scripts/check_env.py` = runtime source of truth for required/optional classification (matches .env.example 1:1) |
| 6 | `check_env` wired at TOP of `refresh_friday.py` and `morning_odds.py` — before any I/O — so failures surface immediately |
| 7 | `playwright_atr_scraper.py` gets loud-fail guard: if cookie file missing, exits 1 with path + instructions |

**Anti-fab compliance:** .env file NEVER read. All var names derived from grep + audit. No real credential values anywhere. Placeholder format uses `<…>` throughout. `check_env.py` never prints values — only var names.

**Files:** CREATED .env.example, scripts/check_env.py, README.md (with Credentials section), tests/test_check_env.py (14 tests). MODIFIED refresh_friday.py, morning_odds.py, playwright_atr_scraper.py. .gitignore verified — `.env` and `.env.*` already covered.

**Tests:** 14/14 PASS.

**Steve's next action:**
```bash
copy .env.example .env
# Edit .env — add SPORTINGLIFE_USER and SPORTINGLIFE_PASS
python scripts/check_env.py   # should exit 0
```

### 2026-06-07T17:08+01:00: RUNBOOK.md shipped (Livingston-5)

**By:** Livingston (Data Engineer)
**Requested by:** Steve
**What:** `RUNBOOK.md` at repo root — 565 lines, 8 sections, single operator guide taking a stranger from "I just installed this" to "I have a printable race card by race time." Encodes the two-source scrape pattern earned during Derby Day audit + named fallbacks for all observed failure modes.

**Audience:** Developer with Python + CLI knowledge, ZERO horse racing knowledge, ZERO pre-existing codebase knowledge.

**Structure:**

1. Prerequisites (env vars + consequences of each missing)
2. **The Two-Source Scrape Pattern** (most important) — 5 sources documented with URLs, auth, typical failure modes, detection logic
3. Race-Day Timeline (T-24h overnight → T-2h baseline → T-1h drift gate → T-30 NR check → post-race results → evening archive)
4. Manual Live-Odds Fallback (step-by-step + exact JSON schema)
5. Sanity Checks Before Betting (4 pre-publication checks)
6. Common Failure Modes (6 observed: RP 406, SL 373-byte, missing env vars, stale market, HTML staleness, orphaned horses — each with diagnosis, root cause, fix)
7. Glossary (15 racing + signal terms)
8. Quick Reference Card (one-screen summary)

**Key finding documented:** Racing Post results pages work post-race even when racecard pages are blocked mid-day. This was yesterday's breakthrough finding.

**Compliance:** Zero real API keys, passwords, tenant IDs. Used CURRENT_DATETIME (2026-06-07T17:08:33+01:00); no hardcoded future dates beyond instructional timeline examples.

### 2026-06-08T08:40+01:00: v0.4 wave-1 gate review — 🟢 GO (Saul-3)

**By:** Saul (Reviewer; re-attempt after saul-2 crashed 2026-06-07 ~19:11 BST with CAPI error after 1h41m, no output written — see orchestration log)
**Requested by:** Steve

**Overall verdict:** 🟢 GO — all four wave-1 items cleared for merge. No conditions required.

**Per-item:**

| Item | Verdict | Tests |
|---|---|---|
| market_drift.py (Rusty-7) | 🟢 GO | 46/46 |
| render_header + racecard (Linus-14) | 🟢 GO | 22/22 |
| env-validator + check_env (Danny-2) | 🟢 GO | 14/14 |
| RUNBOOK.md (Livingston-5) | 🟢 GO | n/a (docs) |

**Full suite:** 448/448 PASS (excluding pre-existing wave33 failure — confirmed pre-existing by git evidence, NOT a wave-1 regression).

**Verified:**
- No drift in 14+ hours since yesterday's passes
- market_drift: weight=0.0 not in scoring weights dict (sum still 1.0000); no circular imports; portable code (docstring-only Derby Day mentions are non-blocking)
- render_header: £12.50 correct in proof file; EW double-stake correct; VOID/NR exclusion correct; backward compat for missing meta
- check_env: secret-handling clean (no real creds, `<…>` placeholders, gitignore coverage verified); both refresh_friday.py + morning_odds.py wire `_gate_env()` BEFORE network calls (refresh_friday.py:53, morning_odds.py:94)
- RUNBOOK: credential skim ZERO matches for password/credential/token/api.key/Bearer/Authorization/https.*@; all scraping URLs public; var names only, no values

**Working-tree classification (Section H):** Saul produced authoritative wave-1 vs orphan classification for the 27 unexpected M files. Scribe-19 used this as the staging contract.

**Non-blocking actions logged for next sprint:**

1. Fix `test_racecard_wave33`: update fixture to pass `bets_json_path` with scenario field — assign to Saul
2. Update `morning_odds.py` `RACECARD_FILES` for Royal Ascot 2026-06-16 dates — assign to Danny before live-test
3. Sanitise `market_drift.py` docstring of Derby Day horse name examples (low priority backlog)
4. Pre-sprint Derby Day orphan files (4 deleted inbox entries + `outputs/racecard-2026-06-06.html` hand-edit + race-day data drift) remain unstaged — separate "Derby Day close-out" commit review needed

**Report path:** archived from inbox to `.squad/decisions/inbox/` (merged into this entry; raw report deleted with other inbox files per normal flow).

### 2026-06-08: v0.4 wave-2 T-60 watchdog shipped (River-1 / Linus-15 / Saul-5)
**Verdict:** SHIPPED in commit f684ed9 after Saul-5 re-gated GO.
**Summary:** River-1 built the pre-pipeline `scripts/t60_watchdog.py`, tests, `refresh_friday.py` wiring, RUNBOOK coverage, and reusable artifact-watchdog skill. Saul-4 gave a CONDITIONAL gate on four material issues: watchdog ordering, independent bets-total reconciliation, race-scoped NR/VOID handling, and Quick Reference docs. Linus-15 applied the non-River fix pass: watchdog now runs first, bets total is independently computed, render-header consistency is separate, NR/VOID checks are race-scoped, and RUNBOOK fallback docs include the direct T-60 command. Saul-5 verified 11/11 targeted tests and 459/459 full-suite pass with `tests/test_racecard_wave33.py` ignored, plus idempotency and bad-env/missing-artifact behavior. The bundle writes `outputs/t60-status-{date}.json` and exits 0 OK / 1 STALE / 2 MISSING or INCONSISTENT.

### 2026-06-08: Orphan cleanup close-out recorded (Scribe-21 / Danny-3)
**Verdict:** COMPLETE - Scribe-21 pushed four atomic cleanup commits to `origin/main` after Danny-3 classified the orphan set.
**Commits:** `7c1c7a0` race-day artifacts; `83092f4` report/market compatibility code and tests; `2a33a54` process assets and inbox cleanup; `2845e84` local-only gitignore plus one-shot script archive.
**Notes:** Scribe-21 left River T-60 work, Danny-4 scoping, Saul notes, and `tests/test_regression_wave3.py` untouched for the next owners. `decisions.md` was 45,744 bytes after that pass, below the 51KB archive gate.

### 2026-06-08: v0.4 wave-2 #6 Epsom/2026 decouple scoping (Danny-4)
**Verdict:** JSON config approach, 14-26h MVP, Ascot fit YES with neutral priors.
**6 chunks:** 1+3 Linus, 2+5 Livingston, 4 Rusty/Danny/Saul, 6 Saul/Linus/Danny.
**Full scoping at:** `.squad/decisions/inbox/danny-4-decouple-scoping.md` (1.3MB inventory - leave in inbox, do not archive yet).
**Steve approved defaults:** JSON, neutral Ascot priors, flat data layout, --course/--meeting/--date CLI, refresh_friday.py stays as Epsom wrapper one release, don't churn historical outputs.

### 2026-06-08: v0.4 #6 Chunk 1 config loader delivered (Linus-16)
**Verdict:** COMPLETE - ready for gate; source summary at `.squad/decisions/inbox/linus-16-chunk1-config.md`.
**Summary:** Linus-16 added JSON course configs for Epsom and Ascot, `src/course_config.py`, and 11 config-loader tests.
**CLI impact:** `refresh_friday.py`, `t60_watchdog.py`, `src/cli.py`, and `morning_odds.py` now accept `--course`, `--meeting`, and `--date` while preserving Epsom defaults.
**Compatibility:** Epsom keeps legacy output paths; non-Epsom courses use course-prefixed paths to avoid collisions.
**Validation claimed:** targeted config/watchdog tests 22/22 and full suite 470/470 with wave33 ignored.

### 2026-06-08: v0.4 #6 Chunk 1 gate GO (Saul-6)
**Verdict:** 🟢 GO - standalone config/path/CLI-default slice approved; source summary at `.squad/decisions/inbox/saul-6-chunk1-gate.md`.
**Evidence:** Saul-6 verified `tests/test_course_config.py` 11/11 and full suite 470/470 with `tests/test_racecard_wave33.py` ignored.
**Scope:** Gate confirmed required config shape, Ascot five-day calendar with neutral priors, fail-loud resolver behavior, and CLI help/default wiring.
**Discipline:** No Chunk 3/4 scoring or presentation files changed; Scribe must stage only the reviewed eight code files.
**Compatibility:** T-60 missing-artifact behavior and old-style `src.cli fetch --date 2026-06-06` remained intact.

### 2026-06-08: Danny-4 remains canonical v0.4 #6 6-chunk plan
**Decision:** Keep `.squad/decisions/inbox/danny-4-decouple-scoping.md` in inbox as the canonical 1.3MB scoping inventory.
**Reason:** decisions.md carries only the summary; the full plan remains referenced for future chunks and must not be deleted in this cleanup.

### 2026-06-08: v0.4 #6 Chunk 2 scraper/odds/refresh delivery (Livingston-6)
**Verdict:** COMPLETE - ready for gate; source summary at `.squad/decisions/inbox/livingston-6-chunk2-scraper.md`.
**Summary:** Livingston-6 set Ascot RP course_id 1 and added config-driven Racing Post + Sporting Life dry-run scrapers.
**Compatibility:** Epsom legacy paths/defaults preserved while non-Epsom enrichment and market snapshots become course-prefixed.
**Validation:** Targeted Chunk 2/course-config tests passed; Saul-7 later verified 480/480 full-suite pass with wave33 ignored.

### 2026-06-08: v0.4 #6 Chunk 2 gate AMBER + FU-1 (Saul-7)
**Verdict:** 🟡 AMBER ship-with-followup; source review at `.squad/decisions/inbox/saul-7-chunk2-gate.md`.
**Evidence:** Saul-7 verified scraper dry-runs, Ascot RP course id, refresh-date behavior, Epsom legacy filenames, and 480/480 tests.
**Concern:** `scripts/morning_odds.py --dry-run` exits 1 without `SPORTINGLIFE_USER/PASS` because `_gate_env()` runs before dry-run handling.
**Disposition:** Accepted as pre-existing fail-loud live-scrape protection, not a Chunk 2 regression. FU-1 tracked, see followups.md.

### 2026-06-08: v0.4 #6 Chunk 3 course-aware presentation delivery (Linus-17)
**Verdict:** COMPLETE - ready for gate; source summary at `.squad/decisions/inbox/linus-17-chunk3-presentation.md`.
**Summary:** Linus-17 added `src/render_helpers.py` and made report/racecard titles, headings, and output paths flow from course_config.
**Compatibility:** Epsom report/racecard wording and legacy paths preserved; Ascot synthetic renders use Royal Ascot titles and course-prefixed paths.
**Validation:** 76 targeted presentation/config tests and 480/480 full-suite pass with wave33 ignored.

### 2026-06-08: v0.4 #6 Chunk 3 gate GO (Saul-8)
**Verdict:** 🟢 GO; source review at `.squad/decisions/inbox/saul-8-chunk3-gate.md`.
**Evidence:** Saul-8 verified templates have no hardcoded Epsom/Derby tokens, renderers delegate paths through config, and CLI changes are pass-through only.
**Compatibility:** HEAD-baseline synthetic Epsom render was byte-equivalent; historical output diffs were explained as race-day hand-edits, not regressions.
**Scope:** CSS, trifecta box, portfolio rendering, and Chunk 4 scoring code remained untouched.
### 2026-06-08: v0.4 #6 Chunk 4 course-aware scoring priors delivered (Rusty)
**Verdict:** COMPLETE - ready for state merge; source summary at `.squad/decisions/inbox/rusty-chunk4-priors.md`.
**Summary:** Rusty extracted 9 hardcoded Epsom scoring priors from pace, C/D form, trial form, and scoring into course config.
**Compatibility:** Epsom 2026-06-06 regression stayed byte-equivalent across 8 races / 149 runners; Derby top 3 unchanged.
**Ascot:** Ascot scoring priors are deliberately neutral for MVP: no draw table, no pace fit table, neutral CD badges, disabled trial form, and empty equipment defaults.
**Validation claimed:** targeted Chunk 4 tests passed and full suite was 484/484 with wave33 ignored.

### 2026-06-08: v0.4 #6 Chunk 4 calibration audit GREEN (Danny-5)
**Verdict:** GREEN with non-blocking follow-ups; source audit at `.squad/decisions/inbox/danny-5-chunk4-audit.md`.
**Evidence:** Danny-5 spot-checked extracted draw, pace, CD, and trial-form values against git history and confirmed Epsom regression faithfulness.
**Ascot:** Audit confirmed Ascot has neutral priors and no Epsom scoring leakage through score-runner integration.
**Follow-ups:** FU-2 edge-case tests, FU-3 `trial_form.load_trial_form()` default-course coupling, and FU-4 unused `equipment_defaults` were created in followups.md.
**Disposition:** All three follow-ups are non-blocking for v0.4 MVP and should be handled before non-neutral non-Epsom calibration.

### 2026-06-08: v0.4 #6 Chunk 4 final gate GO (Saul-9)
**Verdict:** 🟢 GO; source gate at `.squad/decisions/inbox/saul-9-chunk4-gate.md`.
**Evidence:** Saul-9 independently verified `tests/test_chunk4_priors.py` 4/4 and full suite 484/484 with wave33 ignored.
**Regression:** Independent canonical recompute confirmed Epsom byte-equivalence: 8 races, 149 runners, 149 score fields, Derby top 3 unchanged.
**Scope:** Gate confirmed allowed Chunk 4 files only, Ascot neutrality, centralized `scoring_priors_for()`, and no forbidden output/template/report churn.

## 2026-06-08T14:30 v0.4 #6 polish: CLI seam blockers + stale-baseline lesson

Livingston-7 Ascot E2E smoke surfaced 10 rough edges. Linus-18 patched 3 publish-blockers (R-7 predict schema, R-8 card->bets wiring, R-9 slip generation). Saul-10 returned CONDITIONAL on R-7 because comparison against HEAD outputs/bets-2026-06-06.json failed; investigation revealed HEAD was a pre-wave-1 stale artifact from "Linus Reports Engineer v3", not a true CLI baseline. Steve approved refreshing baseline (option A). Linus-18 shipped: 490 pass, Ascot T-60 clean. Livingston-8 independently confirmed R-7/R-8/R-9 closed via re-smoke. New low edge R-11 (PowerShell line-wrap on T-60 GBP total) logged.

LESSON: gate prompts that say "compare against HEAD" need to verify HEAD is the current contract, not a stale committed artifact. Future regression baselines belong in tests/fixtures/regression/, not in outputs/.


### 2026-06-08: v0.4 #6 fully shipped - Chunk 5 + Chunk 6 complete
**Verdict:** SHIPPED. Combined Livingston-9, Linus-19, and Saul-11 batch closed the course-agnostic publish-ready skill work.
**Chunk 5:** Livingston-9 kept the flat course-prefixed data layout, added `docs/data-layout.md`, and documented `path_for()` layout intent. Saul-11 verdict: AMBER CONDITIONAL with FU-10 for the T-60/path_for ownership wording gap.
**Chunk 6a:** Livingston-9 rewrote RUNBOOK as Windows-first, course-agnostic operator docs and fixed FU-1 by moving `morning_odds.py` credential gating after dry-run handling. Saul-11 verdicts: GREEN SHIP for RUNBOOK and FU-1.
**Chunk 6b/6c:** Linus-19 closed FU-2 through FU-6: priors edge tests, explicit trial_form course parameter, equipment_defaults YAGNI delete, card going passthrough, and course-scoped market snapshots. Saul-11 verdicts: GREEN SHIP for FU-2/FU-3/FU-4/FU-5 and AMBER CONDITIONAL for FU-6 because the remaining broad Derby grep hit is the existing FU-7 CSS comment.
**Test count:** Saul-11 verified 500/500 with `python -m pytest --ignore=tests/test_racecard_wave33.py`; Scribe final rerun used `python -m pytest -x --ignore=tests/test_racecard_wave33.py`.
**Lessons:** Stale-baseline trap confirmed by Saul-10 and Saul-11: verify the baseline is the current contract before regression-comparing. Parallel-agent file boundaries worked: Livingston owned docs/scripts while Linus owned source/tests, with only compatible `src/course_config.py` overlap.
**Followups:** CLOSED in this batch: FU-1, FU-2, FU-3, FU-4, FU-5, FU-6. OPEN after ship: FU-7, FU-8, FU-9, FU-10.

### 2026-06-08: v0.4.0 SHIPPED - publish-readiness wave
**Verdict:** SHIPPED. Danny-6's publish-readiness audit moved from ALMOST to all blockers closed for an internal GitHub release.
**Docs:** Livingston-10 delivered 8/8 publish-facing docs: README plus seven course-agnostic `.squad\skills\*\SKILL.md` updates. Epsom, Ladies Day, and Derby wording is now historical/example-only where it remains.
**Gate:** Saul-12 returned 10/10 GREEN SHIP across the eight Livingston docs plus Coordinator metadata (`pyproject.toml` and `CHANGELOG.md`). Validation used baseline `6ee87d2` correctly, reran 500/500 tests with `tests/test_racecard_wave33.py` ignored, and confirmed no tracked output drift.
**Metadata:** `pyproject.toml` is stamped `0.4.0` with course-agnostic description; `CHANGELOG.md` carries v0.4.0 release notes and FU-7..FU-10 ship-with-note known issues.
**Process lesson:** Single-Saul-gate pattern worked again: one focused final reviewer gate after producer docs/metadata avoided split-brain signoff while preserving speed.
**Stale-baseline lesson:** Saul-12 explicitly anchored review to `6ee87d2`, continuing the Saul-10/Saul-11 lesson that a committed output must be proven current before it is treated as a regression baseline.
