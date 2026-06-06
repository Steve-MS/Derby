### 2026-06-06T07:08 BST: Saturday 07:00 baseline gate — capture complete
**By:** Livingston (scheduled watchdog tick, Derby Day)
**Requested by:** Steve

---

## Baseline Capture Summary

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

---

## Race-level runner counts (post-NR filter)

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

---

## Going

Official going declared in racecard (from Racing Post 2026-06-03):
> **"Good to Soft (Good in places); 5f course Good (Light rain)"**

As of 07:08 BST: **no updated official going available from RP scrape** — the racecard `going` field remains the 2026-06-03 source. Based on the bets file weather advisory (River forecast: 5.2mm overnight rain, 60-80% probability of Soft by Derby post-time):
- Expected going: **Good to Soft → Soft possible by 16:00**
- Going advisory in bets file: use GREEN slip until official declarations; switch to HOLD slip if Soft declared
- Steve GO/NO-GO call at 10:00 should include going check

---

## Key Pick Status

| Horse | Race | Baseline status | Price (synthetic) | Bets file price | Note |
|---|---|---|---|---|---|
| Item | 16:00 Derby G1 | ✅ CONFIRMED | 5.0 (4/1) | 3.25 (live override) | Synthetic price is 5.0; bets file live override was 3.25. Price gap expected — synthetic baseline. |
| Kinswoman | 15:15 Dash | ✅ CONFIRMED | 24.0 (23/1) | 24.0 | Stable |
| Allegresse | 16:40 Lester Piggott | ✅ CONFIRMED | 9.0 (8/1) | 9.0 | Stable |
| Lord Melbourne | 17:20 Northern Dancer | ✅ CONFIRMED | 13.5 (12/1) | 13.5 | Stable |
| **Dance In The Storm** | 17:55 Tokyo Trophy | ⚠️ **PROBABLE NR** | N/A | 18.5 (WIN £1.33) | **URGENT — WIN bet. Absent from RP live racecard 07:08. Verify before betting.** |
| **See The Fire** | 14:40 Coronation Cup G1 | ⚠️ **PROBABLE NR** | N/A | 13.0 (EW outsider £0.25) | Absent from RP live racecard 07:08. Coronation Cup now 6 runners. |
| Causeway | 16:00 Derby G1 | ❌ ABSENT | N/A | 29.0 (EW outsider £0.25) | Known NR since Friday gate. Confirmed. Danny reviewing HTML. |

---

## Anomalies for Saul's Attention

### ⚠️ HIGH PRIORITY — New probable NRs on bet horses
1. **Dance In The Storm**: WIN bet £1.33 at 17:55 — probable NR per RP scrape. **If confirmed, this eliminates the main late WIN from the portfolio and removes one leg of the Kinswoman+Dance In The Storm double (£0.50).** Total stake at risk: £1.33 WIN + £0.50 double = £1.83.

2. **See The Fire**: EW outsider £0.25 at 14:40 Coronation Cup — probable NR per RP scrape. Stake at risk: £0.25.

### ℹ️ MEDIUM — Field compression
- **Coronation Cup G1 14:40** now 6 runners (was 8). Place terms may change (bookmaker by bookmaker). Affects any remaining EW bets on this race.
- **Dash Handicap 15:15** down to 18 from 34 — expected ballot reduction for this heritage race. Kinswoman confirmed.
- **Derby 16:00** confirmed at 14 runners — consistent with 2026-06-05 RP check (4 NRs: Causeway, Constitution River, Endorsement, Proposition all absent).

### ℹ️ LOW — Price source note
All baseline prices are **synthetic (from racecard 2026-06-02)** or **ante_post (RP 2026-06-02)**. No live market prices are available (RP odds are JS/WebSocket, not in SSR HTML). Saul's delta-check vs Friday closing prices will show ~0% movement everywhere — this is expected behaviour. Only the NR filter (reduced field) is meaningful data from this scrape. Live price comparison requires manual override CSV (see runbook).

### ℹ️ NOTE — Item price discrepancy
Item shows **5.0 (4/1)** in baseline (synthetic, 2026-06-02 source). Bets file used **live override 3.25 (9/4)**. The 3.25 was a manually confirmed live price (applied when the bet slip was built). The synthetic baseline correctly anchors at 5.0 — this is expected and is NOT a market move signal. The actual live Derby market should be checked at 09:00–10:00 gate.

---

## Next steps (per operator sequence)

- **~07:30** → Saul: delta-check vs Friday close prices (note: prices are synthetic/flat, delta will be neutral; NR flags are the actionable findings)
- **If ≥30% steam/drift on any pick**: spawn Danny for review (PROPOSED rule)
- **By 10:00** → Steve: GO/NO-GO call on Derby Day bets. **Verify Dance In The Storm and See The Fire NR status before this call.**
- **Going check**: Official going update expected by ~09:00 from Epsom Racecourse. Key trigger: if Soft declared → cancel Item WIN, switch to HOLD slip.

---

**Files written:**
- `data/enrichment/market-baseline.json` — 39,019 bytes, 101 runners, status: baseline
- `data/enrichment/market-latest.json` — 39,140 bytes, 101 runners, status: BASELINE_CAPTURE
- `.squad/decisions/inbox/livingston-sat-baseline-NRs.md` — full NR list with bet impact
