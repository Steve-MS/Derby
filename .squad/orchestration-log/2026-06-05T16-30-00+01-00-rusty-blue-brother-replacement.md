# Orchestration Log: Rusty — 17:50 Outsider Replacement

**Agent:** Rusty (Signal Engineer)  
**Decision:** rusty-blue-brother-replacement.md  
**Timestamp:** 2026-06-05T16:30:00+01:00  
**Context:** Blue Brother confirmed NR by Livingston's live verification pass  

## Decision Summary

| Field | Value |
|---|---|
| Race | 17:50 Debenhams Handicap, Epsom |
| Context | Blue Brother confirmed NR (absent from all 16-runner declarations per Sporting Life) |
| Pick | Arctic Thunder (cloth #11, draw 1, OR 84, RPR 110, TS 102) |
| Rationale | 26pt RPR-OR gap (widest), D badge (Epsom course winner), TS 102, Ed Walker/Kieran Shoemark quality pair, no stale-price trap |
| Confidence | SPECULATIVE (standard EW outsider) |
| Stake | £0.25 EW @ ~20/1 (stale 2026-06-02) |
| Live Verification | data/enrichment/live-runners-2026-06-05.json (runner #11, draw 1, confirmed in 16-runner field) |
| Status | ✅ PICK MADE — awaiting Linus hand-edit |

## Process Note

This is the **third NR swap** of Ladies Day 2026-06-05:
1. Port Road (16:40) → Triple Double A (failed, also NR) → Asmen Warrior (live-verified) ✅
2. Blue Brother (17:50) → Arctic Thunder (live-verified) ← THIS FILE
3. Pattern established: hard rule now ratified for all future race days

**Hard rule applied:** Pick sourced exclusively from live-runners-2026-06-05.json. Arctic Thunder confirmed as runner #11. `market-latest.json` used ONLY for stale price orientation on verified runners.

## Outsider Shortlist (Non-stale-trap)

| Horse | RPR-OR gap | RPR | TS | Form | Trainer | Epsom badge | Price |
|---|---|---|---|---|---|---|---|
| **Arctic Thunder ✅** | **26pt** | **110** | **102** | 434-07 | Ed Walker | **D ✓** | 20.5 |
| Son | 27pt | 109 | 97 | 67-229 | T Easterby | None | 21.0 |
| Musical Angel | 23pt | 105 | 87 | 8321-5 | S Dow | CD ✓ | 21.0 |

Arctic Thunder selected: higher RPR, higher TS, course experience, quality trainer/jockey despite Son's slightly wider gap.

## Files Touched

- None (awaiting Linus racecard + report rebuild)
- Decision documented in .squad/decisions.md (merged from inbox)

## Downstream Actions

- Linus: Replace Blue Brother with Arctic Thunder in outputs/racecard-2026-06-05.html
- Linus: Rebuild outputs/report-2026-06-05.html with full verification sweep
- Scribe: Update history files with NR-cascade post-mortem findings
