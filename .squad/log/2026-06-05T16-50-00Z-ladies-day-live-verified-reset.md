# Session Log: Ladies Day Live-Verified Reset

**Date:** 2026-06-05  
**Session:** 16:00–16:50 BST  
**Trigger:** Steve's escalation at 16:12 BST — systemic stale-data risk after triple NR failures  
**Status:** ✅ COMPLETE — 3 NR swaps, all live-verified, card + report rebuilt  

---

## The Problem

**Cascading NR failures on Ladies Day 2026-06-05:**

1. **Port Road (16:40)** — Declared NR at start of day (Steve verbal 15:46 BST)
2. **Triple Double A (16:40 replacement)** — ALSO NR, caught by Steve at 16:12 BST (28 min before race)
3. **Blue Brother (17:50)** — Declared NR, caught by live verification sweep at 16:25 BST

All three horses were drawn from `market-latest.json` (2026-06-02 vintage) or stale racecard enrichment. The root cause was pipeline over-reliance on stale data for runner identity (not just price).

---

## The Reset

### Step 1: Live Verification (Livingston, 16:25 BST)

Livingston live-verified all remaining Ladies Day races vs Sporting Life:
- Pulled live racecard snapshot (Sporting Life + Sky Sports + Betfair corroboration)
- Cross-matched 16:40, 17:15, 17:50 race fields
- **Found 2 critical mismatches:** Triple Double A (16:40 NOT live), Blue Brother (17:50 NOT live)
- **Created artifact:** data/enrichment/live-runners-2026-06-05.json (canonical ground truth)
- **Proposed hard rule:** LIVINGSTON LIVE-RUNNER GATE — mandatory verification before any NR swap

### Step 2: Re-picks (Rusty, 16:13–16:30 BST)

Rusty re-picked both vacant outsider slots **using only live-runners-2026-06-05.json:**

**16:40 HKJC (v2 pick after Triple Double A failed):**
- **Asmen Warrior** (cloth #15, live-verified)
- Rationale: 5-star Timeform, RPR 112 vs OR 88 (24pt gap), first-time blinkers, near-miss Windsor form, named jockey
- Confidence: LOW/SPECULATIVE (standard EW outsider)
- Stake: £0.25 EW @ ~20/1 (stale)

**17:50 Debenhams (Blue Brother replacement):**
- **Arctic Thunder** (cloth #11, live-verified)
- Rationale: RPR 110 vs OR 84 (26pt gap, widest), D badge (Epsom course winner), TS 102, Ed Walker/Kieran Shoemark quality pair
- Confidence: SPECULATIVE (standard EW outsider)
- Stake: £0.25 EW @ ~20/1 (stale)

### Step 3: Card + Report Rebuild (Linus, 16:32–16:45 BST)

Linus hand-edited both outputs with verification stamps:

**Racecard (outputs/racecard-2026-06-05.html):**
- Removed Triple Double A (NR)
- Inserted Asmen Warrior (16:40)
- Removed Blue Brother (NR)
- Inserted Arctic Thunder (17:50)
- Updated footnotes with triple-NR sequence
- Added verification stamp: 🟢 Live-verified 2026-06-05 16:25 BST

**Report (outputs/report-2026-06-05.html):**
- Replaced Port Road / Triple Double A / Blue Brother outsider-pick blocks
- Inserted Asmen Warrior / Arctic Thunder blocks
- Retained field ranking tables (historical audit trail)
- Full verification sweep: all named horses cross-checked against live-runners-2026-06-05.json
- Added verification stamp

### Step 4: Cross-Agent Escalations

**Hard rules ratified:**

- **Livingston:** LIVE-RUNNER GATE — mandatory pre-render gate for all race days (not just when failures occur)
- **Rusty:** Market-latest.json NEVER trusted for runner identity — only for price orientation on confirmed runners
- **Linus:** `render_replacement_row()` helper elevated to HARD-RULE priority — ships before Royal Ascot (16–20 Jun 2026)
- **Saul:** Test coverage gap identified — need stale-runner detection tests (not just stale-price tests)
- **River:** NR swaps MUST verify replacement against live source BEFORE Linus hand-edits
- **Danny:** Three manual hot-swaps in one afternoon proves helper promotion is essential

---

## Hard Rules Established

### Rule 1: Live-Runner Verification (Livingston)

> Before Rusty scores or Linus renders for any race, verify all runners against a live source (Sporting Life, Sky Sports, Racing Post) within 4h of race-time. `market-latest.json` is NOT trusted for runner identity. Output: `live-runners-YYYY-MM-DD.json` as ground truth.

### Rule 2: NR-Swap Pre-Check (Rusty)

> Before any NR replacement is handed to Linus, the replacement horse MUST be confirmed present in a live declared-runners source on race day. Matching against enrichment files from before race day is NOT sufficient. If no live source can be fetched, the decision file must carry `status: blocked` and request Steve to paste the list.

### Rule 3: Runner-Validity Distinction (Linus)

> Separate stale-price caveat from runner-validity caveat in `render_replacement_row()`. Parameter: `runner_verified_source: str | None`. If supplied → green ✅ ("verified [source]"). If None → amber ⚠️ ("not live-verified — re-check at gate"). Do not merge into single merged caveat.

### Rule 4: Helper Promotion (Danny)

> `render_replacement_row()` helper in src/report.py ships before Royal Ascot (16–20 Jun 2026). No exceptions. Three manual swaps in one afternoon establishes pattern of unsustainability.

---

## Files Modified

- outputs/racecard-2026-06-05.html (2 NR swaps, verification stamp)
- outputs/report-2026-06-05.html (2 NR swaps, full rebuild, verification stamp)
- data/enrichment/live-runners-2026-06-05.json (created)
- .squad/decisions.md (merged 5 inbox decisions, marked v1 Triple Double A as superseded)
- .squad/log/ (this session log)
- .squad/orchestration-log/ (5 agent logs)
- .squad/agents/*/history.md (7 files updated with cross-agent escalations)

---

## Next Steps

1. **Royal Ascot (16–20 Jun 2026):** Ship `render_replacement_row()` helper (Danny + Linus)
2. **Next race day:** Incorporate LIVINGSTON LIVE-RUNNER GATE into standard pipeline (not just on failure)
3. **Saul (Tests):** Add stale-runner detection test fixtures from live-runners-2026-06-05.json
4. **River (Ops):** Document NR-swap verification protocol in race-day runbook

---

## Confidence Summary

**Asmen Warrior (16:40):** LOW/SPECULATIVE — standard EW outsider; live-verified; blinkers + RPR-OR gap + 5-star Timeform make credible case; stale price ~20/1

**Arctic Thunder (17:50):** SPECULATIVE — standard EW outsider; live-verified; RPR-OR gap + Epsom course winner make credible case; recent form (7th, unplaced) is slight concern; stale price ~20/1

**Overall race day outcome:** Pending. All bets now placed on live-verified runners with stale-data caveats clearly signaled.
