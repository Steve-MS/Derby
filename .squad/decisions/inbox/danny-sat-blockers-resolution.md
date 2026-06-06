### 2026-06-06T07:05+01:00: Saturday Blockers Resolution (Derby Day)
**By:** Danny (Lead)
**Requested by:** Steve (via race-day watchdog 07:00 gate)

---

## BLOCKER #2 — Derby Race Time: RESOLVED ✅

**Verdict: 16:00 BST is CORRECT. No patch required.**

Sources confirming 16:00:
1. The Jockey Club / Epsom Downs official — https://www.thejockeyclub.co.uk/epsom-derby/plan-your-day/when-and-what-time/
2. HorseRacing.net racecard — https://www.horseracing.net/epsom/06-06-26
3. IrishRacing.com racecard — https://www.irishracing.com/racecards/Sat-6th-Jun-2026/Epsom/1600

The coordinator brief stating "16:30" was in error. `bets-2026-06-06.json` race_id `epsom-2026-06-06-1600` and Saturday HTML extracted times are both correct. No file changes needed.

---

## BLOCKER #1 — Causeway NR: PATH C (Hybrid) ✅

**Chosen: (C) Annotate now, re-render only if more NRs surface from Livingston's 07:00 baseline.**

### Rationale (1 sentence)
Causeway is a £0.25 EW outsider that voids automatically at declarations — the financial risk is nil, re-rendering risks fresh bugs on Derby morning, and annotation takes 2 minutes with zero blast radius.

### What happens now
- NO re-render by Linus (unnecessary given £0.25 void-at-declarations + no visual confusion for Steve since he knows Causeway is out)
- Livingston's 07:00 baseline capture will confirm NR status from live RP scrape
- If Livingston's baseline surfaces ADDITIONAL NRs beyond Causeway → escalate to full re-render (Linus, Path A) before Steve's 10:00 GO/NO-GO
- If Causeway is the only NR → let it void naturally; it's already flagged in Livingston's report

### If escalation to Linus becomes necessary (scope brief)
> **Linus brief (conditional — only if ≥2 NRs total):**
> Re-generate `outputs/racecard-2026-06-06.html` + `outputs/bets-2026-06-06.json` with ALL confirmed NRs removed (Causeway + any from 07:00 baseline). Preserve: all other picks, trifecta block (adjust box if #4 model-ranked horse drops), going advisory, outsider rationale for remaining runners. Source of truth for NR list: Livingston's baseline capture + RP declarations page. Do NOT touch `data/results/*.json`.

---

## CHECKPOINT 4 — Saturday Operator Sequence & PROPOSED Rules

### Context
Two rules remain PROPOSED (not ratified by Steve):
1. No manual override of sub-50 model scores without 2-PM sign-off
2. Saturday morning ≥30% steam/drift gate

### My call (Danny, Lead):

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

---

## New Flags

None surfaced. Causeway is the only confirmed NR. Livingston's 07:00 baseline will be the authoritative check for any further NRs declared overnight.

---

## Summary

| Item | Outcome |
|------|---------|
| Derby time | **16:00 BST confirmed** (3 sources) — no patch |
| Causeway NR | **Path C** — let void naturally; re-render only if more NRs surface |
| Linus brief written | **Conditional only** — fires if ≥2 NRs from baseline |
| PROPOSED rules | Operate as soft guidance; Saul runs delta-check as planned |
| New flags | None |
