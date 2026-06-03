# Livingston — History

## Learnings

- 2026-06-03: Built `data/enrichment/trial-form.json` — 276 horses across both days; 25 with verified trial data (Derby + Oaks circuits); 1 flag (Causeway withdrawal status unconfirmed); scores file may predate final declarations so Causeway entry needs pre-race sanity check against BHA/Epsom official declarations.

## Project context (seeded 2026-06-03)

- Python 3.12 race-analysis toolkit for Steve. Repo Steve-MS/Derby, commit 5a1770e.
- Existing enrichment files: `data/enrichment/horse-profiles.json` (29 horses with sires), going history, pace styles.
- Existing fetcher: `src/racecard.py`, refresh script `scripts/refresh_friday.py`.
- Open question: where do raw racecards live? `data/racecards/2026-06-06/*.json` returned empty when probed. Find this before equipment/wind signal can be built.
- Odds source: BetVictor + RP morning prices. `morning_price` field already on runner records.
- Target races: Ladies Day Fri 5 Jun + Derby Day Sat 6 Jun 2026 at Epsom.
