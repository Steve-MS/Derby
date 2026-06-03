# Team

## Project Context

- **Project:** Epsom Derby weekend race-analysis toolkit
- **User:** Steve
- **Repo:** Steve-MS/Derby
- **Stack:** Python 3.12, pytest, plain HTML/CSS for reports
- **Purpose:** Predictive scoring model for 2026 Epsom Ladies Day (5 Jun) + Derby Day (6 Jun). Outputs ranked picks, betting recommendations, A4 race cards, and accumulator suggestions for a £100 daily outlay.
- **Key files:** `src/scoring.py` (v0.3 weights, sum=1.0), `src/cd_form.py`, `src/sires.py`, `src/pace.py`, `src/going.py`, `src/report.py`, `src/betting.py`, `data/enrichment/*.json`, `outputs/*.html`, `scripts/refresh_friday.py`

## Members

| Name | Role | Model | Badge |
|------|------|-------|-------|
| Danny | Lead — scoring model owner, scope, architecture, weight tuning | auto | 🏗️ Lead |
| Livingston | Data Engineer — racecard fetching, scraping, enrichment files, odds capture | claude-sonnet-4.6 | 📊 Data |
| Rusty | Signal Engineer — builds new signal modules (trial form, market moves, trainer strike rate, equipment, J/T combos) | claude-sonnet-4.6 | 🔧 Signals |
| Linus | Reports — HTML report, printable A4 betting slip, race cards, narrative copy | claude-sonnet-4.6 | ⚛️ Reports |
| Saul | Tester — pytest suite, signal validation, Ladies Day backtest against Derby Day | claude-sonnet-4.6 | 🧪 Tester (Reviewer) |
| River | Race Day Ops — scheduled jobs, end-to-end pipeline runs, drift checks vs standing stakes, race-morning runbook execution | claude-haiku-4.5 | 🔄 Ops |
| Scribe | Memory & decision ledger | claude-haiku-4.5 | 📋 Scribe |
| Ralph | Work Monitor | — | 🔄 Monitor |
