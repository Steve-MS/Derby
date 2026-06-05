# River — History

## Project Context (seeded 2026-06-03)

- **Project:** Epsom Derby weekend race-analysis toolkit
- **User:** Steve
- **Repo:** Steve-MS/Derby (working tree: `C:\Users\stevenn\race-analysis`)
- **Stack:** Python 3.12 (`C:\Users\stevenn\AppData\Local\Programs\Python\Python312\python.exe`), pytest, plain HTML/CSS
- **Race weekend:** Ladies Day Fri 5 Jun 2026 + Derby Day Sat 6 Jun 2026
- **Today:** 2026-06-03 (Wed) — ~3 days to Derby

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

(none yet — River joined 2026-06-03)

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

