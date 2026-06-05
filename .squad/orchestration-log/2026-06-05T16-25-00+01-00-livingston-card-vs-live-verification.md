# Orchestration Log: Livingston — Live Verification Pass

**Agent:** Livingston (Data Eng)  
**Decision:** livingston-card-vs-live-2026-06-05.md  
**Timestamp:** 2026-06-05T16:25:00+01:00  

## Verification Summary

| Scope | Status |
|---|---|
| Method | Sporting Life live racecards (corroborated: Sky Sports, Timeform, Racing Post, Betfair) |
| Races checked | 3 (16:40 HKJC, 17:15 Surrey Stakes, 17:50 Debenhams) |
| Mismatches found | 2 critical (Triple Double A 16:40, Blue Brother 17:50) |
| Result | ⚠️ FAILURES IDENTIFIED — systemic stale-data risk confirmed |

## Mismatches Found

### 16:40 HKJC World Pool Handicap

| Horse | Card type | Live status | Action |
|---|---|---|---|
| Mister Winston | PASS (model fancied) | ✅ cloth 3, live confirmed | No action |
| Triple Double A | ⚡ EW outsider | ❌ **NOT IN LIVE FIELD** | **REMOVE** |
| Port Road | (already NR) | ❌ Not in live | Already handled |

**Live field size:** 18 runners (vs stale declaration: 29 — **11 NRs since 02 June**)

### 17:15 Cygames Surrey Stakes

| Horse | Card type | Live status | Action |
|---|---|---|---|
| Stellar Sunrise | WIN bet | ✅ cloth 5, live confirmed | No action |
| Assaranca (IRE) | ⚡ EW outsider | ✅ cloth 7, live confirmed | No action |

**Status:** ✅ CLEAN — both confirmed runners

### 17:50 Debenhams Handicap

| Horse | Card type | Live status | Action |
|---|---|---|---|
| Dance In The Storm | WIN bet | ✅ cloth 1, live confirmed | No action |
| Blue Brother | ⚡ EW outsider | ❌ **NOT IN LIVE FIELD** | **REMOVE** |

**Live field size:** 16 runners (all confirmed)

## Root Cause Analysis

### Failure Chain

1. Port Road declared NR → Rusty replaced with Triple Double A (from stale 2026-06-02 data)
2. Triple Double A also a NR by 16:25 BST → caught by Livingston's live check (would have been missed by pipeline)
3. Blue Brother (17:50) similar fate → not yet caught before verification pass
4. ~11 horses in stale HKJC declaration not present in live field → model has been scoring non-existent runners

### Process Failure

`market-latest.json` is 2026-06-02 vintage. Used as source-of-truth for:
- Runner identity (which horses to score / display)
- NR replacement workflow (Port Road → Triple Double A)

**Root cause:** Runner-list verification relied on stale enrichment data. Final declarations window (typically T-48h to T-24h) had already passed. No mechanism to verify replacement runners against live declarations before Linus hand-edits.

## Proposed Hard Rule (LIVINGSTON LIVE-RUNNER GATE)

> **Before Rusty scores or Linus renders for any race, Livingston MUST run live-runner verification using a public racecard source (Sporting Life, Sky Sports, or Racing Post) within 4 hours of race-time.**
>
> `market-latest.json` is **NOT trusted for runner identity.** It may be used for historical price estimates only.
>
> Any horse in the model output that is absent from the live racecard is a non-runner and must be excluded before printing.
>
> **Trigger:** Any time Linus is about to render a race card OR Rusty is about to re-score post-NR.
>
> **Output:** `data/enrichment/live-runners-YYYY-MM-DD.json` as ground truth, with `non_runners_excluded` audit trail per race.
>
> **Failure mode:** If live source is unreachable, status = `blocked` and Steve is informed to paste the runner list manually. Do NOT fall back to stale data silently.

## Files Created/Modified

- **Created:** data/enrichment/live-runners-2026-06-05.json (canonical artifact for race day)
- **Modified:** .squad/decisions.md (merged from inbox)

## Skill Documentation

This verification protocol has been documented at `.squad/skills/live-runner-verification/SKILL.md`. Incorporate as mandatory pre-render gate in Saturday Derby Day pipeline.

## Downstream Actions

- Rusty: Re-pick 16:40 outsider from live-runners-2026-06-05.json (Asmen Warrior) ✅
- Rusty: Re-pick 17:50 outsider from live-runners-2026-06-05.json (Arctic Thunder) ✅
- Linus: Hand-edit racecard + report with both live-verified picks ✅
- Scribe: Document reset + update cross-agent histories ← THIS SESSION
