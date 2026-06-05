# Orchestration Log: Rusty — Port Road NR v2

**Agent:** Rusty (Signal Engineer)  
**Decision:** rusty-port-road-replacement-v2.md  
**Timestamp:** 2026-06-05T16:13:00+01:00  
**Background:** Re-picked after Triple Double A v1 failed NR verification  

## Decision Summary

| Field | Value |
|---|---|
| Context | Port Road NR, Triple Double A also confirmed NR by Livingston 16:25 live check |
| Pick | Asmen Warrior (cloth #15, draw 5, OR 88, RPR 112, TS 98) |
| Rationale | 5-star Timeform, 24pt RPR-OR gap, first-time blinkers, near-miss Windsor (11d), named jockey |
| Confidence | LOW/SPECULATIVE (standard EW outsider) |
| Stake | £0.25 EW @ ~20/1 (stale) |
| Live Verification | Sporting Life 2026-06-05T16:13 BST ✅ cloth #15, draw 5 confirmed |
| Status | ✅ PICK MADE — awaiting Linus hand-edit |

## Process Note

- v1 pick (Triple Double A) failed — relied on stale enrichment data for runner identity
- v2 enforces hard rule: runner must be confirmed in live declared-runners source (Racing Post / Sporting Life / At The Races) BEFORE pick is handed to Linus
- `market-latest.json` used ONLY for price cross-reference on confirmed runners
- `live-runners-2026-06-05.json` is canonical race-day artifact for runner identity

## Files Touched

- None (awaiting Linus racecard edit)
- Decision documented in .squad/decisions.md (merged from inbox)

## Downstream Actions

- Linus: Replace Triple Double A row with Asmen Warrior in outputs/racecard-2026-06-05.html
- Update footnote with both swap steps (Port Road NR → Triple Double A NR → Asmen Warrior ✅)
