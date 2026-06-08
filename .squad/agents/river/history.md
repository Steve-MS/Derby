# River — History

## Project Context (seeded 2026-06-03)

- **Project:** Epsom Derby weekend race-analysis toolkit
- **User:** Steve
- **Repo:** Steve-MS/Derby (working tree: `C:\Users\stevenn\race-analysis`)
- **Stack:** Python 3.12 (`C:\Users\stevenn\AppData\Local\Programs\Python\Python312\python.exe`), pytest, plain HTML/CSS
- **Race weekend:** Ladies Day Fri 5 Jun 2026 + Derby Day Sat 6 Jun 2026
- **Today:** 2026-06-03 (Wed) — ~3 days to Derby

## Standing stakes (as of 2026-06-05)

- **Belinus** — WIN £5 @ decimal 3.5 (Friday Oaks) — **WITHDRAWN**, stake pending refund
- **Sugar Island** — EW £0.25 (Friday Oaks)
- **Asmen Warrior** — EW £0.25 @ ~20/1 (Ladies Day 16:40 — live-verified, stale price, verify at rail)
- **Arctic Thunder** — EW £0.25 @ ~20/1 (Ladies Day 17:50 — live-verified, stale price, verify at rail)

---

## 2026-06-05 16:50 — ESCALATION: NR-Swap Pre-Check Hard Rule (Ladies Day live-verified reset)

**HARD RULE RATIFIED:** NR swaps MUST verify replacement against live source (Racing Post / Sporting Life / At The Races) BEFORE Linus hand-edits.

**Failure chain today:**
1. Port Road (16:40) declared NR early (Steve 15:46 BST)
2. Rusty picked Triple Double A as replacement (from stale enrichment data)
3. Triple Double A ALSO NR by race-time (16:25 BST) — caught by Livingston's live check
4. Blue Brother (17:50) similar — not in live declarations, caught by Livingston sweep

**Root cause:** No verification step existed between Rusty's NR-replacement pick and Linus's hand-edit to racecard. Stale data (market-latest.json 2026-06-02) was trusted for runner identity.

**New protocol (effective 2026-06-05):**
1. **NR declared** → Rusty sources replacement from live-runners-YYYY-MM-DD.json ONLY (built by Livingston live-verification pass)
2. **Replacement candidate identified** → Rusty confirms horse is runner #N in live-runners file (double-check via source URL if needed)
3. **Pick handed to Linus** → Linus receives decision with `live_verified: true` flag + source URL + fetch timestamp
4. **Linus hand-edits** → racecard reflects live-verified pick; stale-price caveat rendered with runner_verified_source parameter (see Linus escalation)

**If Livingston verification is blocked** (live source unreachable):
- Status = `blocked`
- Request Steve to paste declared runners list manually OR accept no EW pick at that time slot
- NEVER fall back to stale data silently

**Impact:** live-runners-2026-06-05.json is the canonical race-day artifact going forward. Market-latest.json is forbidden for runner-identity purposes; price orientation only.

---

## Standing stakes (as of 2026-06-03)

- **Belinus** — WIN £5 @ decimal 3.5 (Friday Oaks)
- **Sugar Island** — EW £0.25 (Friday Oaks)

## Key files I touch

- `scripts/morning_odds.py` — Fri/Sat morning baseline + latest + archive (Livingston renamed from `saturday_morning_odds.py`; supports `--mode archive --date YYYY-MM-DD`)
- `scripts/refresh_friday.py` — full Friday pipeline runner
- `data/racecards-friday-*.json` / `data/racecards-saturday-*.json` — racecard outputs (Livingston's domain to schema, mine to refresh)
- `outputs/report-friday-*.html` / `outputs/report-saturday-*.html` — final reports (Linus's design, mine to regenerate)

## What I do NOT touch

- `src/*.py` — Rusty's signal modules + scoring code
- `data/enrichment/market-*.json` schema — Livingston's
- `.squad/agents/*/charter.md` — coordinator-owned

## Team context

- Danny — Lead (designs)
- Livingston — Data sourcing (racecards, raw odds, enrichment files)
- Rusty — Signal & scoring engineer (v0.5 mid-build right now: market_move + trainer_14d + jt_combo)
- Linus — Reports (HTML/A4)
- Saul — Reviewer/Tester (strict lockout)
- Scribe — Memory ledger

## Learnings

- **2026-06-08 — T-60 artifact dependency graph:** Race-day readiness is a chain, not a file list: course-specific raw racecards are discovered from `data/raw/*-{date}-racecards.json`; live-runner, Sporting Life, Racing Post, and going enrichment must be fresh before `outputs/scores-{date}.json`; reports depend on scores; racecards depend on bets and Linus's JSON-driven header total; slips must mirror active WIN/EW/trifecta entries. `data/enrichment/live-runners-{date}.json` is the runner-identity authority, and `data/enrichment/sportinglife-{date}.json` below 1KB is treated as a loud SPA-shell failure.

## Refresh #1 — Going Forecast (2026-06-03)

**Status:** ✓ Complete

**Execution:**
- Open-Meteo API pull: Wed 3 Jun 3.2mm, Thu 4 Jun 1.3mm, Fri 5 Jun 0.0mm, Sat 6 Jun 2.0mm
- Friday forecast: Good (4.5mm 48h rainfall, HIGH confidence)
- Saturday forecast: Good (2.0mm 48h rainfall, HIGH confidence — improved from previous Good-to-Soft)
- Commit SHA: 27c38501b40d21cc1f4a44a42600063b5f88602b

**Flags for Steve:**
- Saturday going improved (firmer than expected due to Fri dry window)
- Both days now HIGH confidence (up from medium) — suitable for 2-3 day race window

**No further action:** Forecasts stable, race-day readiness confirmed.

## 2026-06-05 12:59 — Derby trifecta box going contingency (Linus)

**Heads-up:** Linus published first-ever trifecta-box recommendation for Derby. **Going contingency rule:** If Soft going is declared pre-race (tomorrow, race morning), drop Item from the 4-horse box → 3-horse box (Benvenuto Cellini, Maltese Cross, Causeway) at stake £2.50/combo × 6 = £15 total. This is contingent on tomorrow's 07:00 BST going declaration.

**For race-morning runbook:** Check Official Going post (07:00 BST) against forecast. If Soft is declared → activate contingency flag, inform Steve before 16:00 race kickoff. **Print-card reminder:** Verify printed Derby card matches digital trifecta box (no mid-night re-edits post-print).

**Reference:** `.squad/decisions.md` 2026-06-05 PM entry "Derby Trifecta Box: Card Placement & Hybrid Delivery".

## 2026-06-05 15:18 — Ladies Day Racecard: Prizeland NR Swap (Linus)

**Heads-up:** Prizeland confirmed NR (absent from market-baseline.json 09:52 BST, verbal confirmation from Steve 15:02 BST). Linus hand-edited `outputs/racecard-2026-06-05.html` to replace Prizeland row (16:00 Oaks) with Cameo (£0.25 EW @ ~14/1, model #3 vs market #4, Aidan O'Brien trial winner).

**For race-morning runbook (Fri 5 Jun 07:00 BST):**
- **Print-card verification:** Check printed Ladies Day card shows **Cameo, not Prizeland** in the 16:00 Oaks race block.
- If printed card shows Prizeland → alert Steve immediately (mid-night re-edit occurred; disregard printed card, use digital racecard instead).
- Verify amber NR badge + stale-odds caveat visible on digital card for Cameo row.

**Reference:** `.squad/decisions/inbox/linus-prizeland-cameo-swap.md` (merged into decisions.md)


## 2026-06-05 — Race-morning verification (Ladies Day, NR swaps #1 & #2)

**Status:** Verification list + alert

**Context:** Two confirmed NR swaps on Ladies Day card. Both carry stale-odds caveats (2026-06-02 synthetic pricing). Steve heads to rail soon — must verify both runners still declared before placing bets.

**Race-morning verification list:**
1. **16:00 Oaks:** Cameo replaces Prizeland (confirmed NR by Steve ~15:13 BST). Stale price ~33/1, £0.25 EW. Verify Cameo still running.
2. **16:40 HKJC Handicap:** Triple Double A replaces Port Road (confirmed NR by Steve 15:46 BST; Port Road absent from market-baseline.json 09:52 BST). Stale price ~23/1, £0.25 EW. Verify Triple Double A still running.

**Action:** Both NR notes visible in card footnotes (outputs/racecard-2026-06-05.html). Print card; confirm both footnotes present. Before Steve heads to rail, read both notes aloud to verify runner status.
