# Routing

## By Signal

| User says / signal | Route to |
|---|---|
| "what should we do next", architecture choices, weight tuning, scope decisions | Danny |
| "fetch", "scrape", "racecard data", "odds", "BetVictor", enrichment JSON, new horse profiles | Livingston |
| "add signal X", "build trial form", "market move signal", scoring-module work | Rusty |
| "HTML report", "race card", "betting slip", "narrative", anything user-facing | Linus |
| "write tests", "validate", "backtest", "did Ladies Day predictions actually work" | Saul |
| "refresh the racecard", "morning odds run", "regenerate report", "push it", race-day pipeline execution, scheduled prompts, drift vs my standing stakes | River |
| Any new bet/scoring artifact before committing | Saul reviews |

## By File

| File pattern | Owner |
|---|---|
| `src/scoring.py` (weights, score_runner) | Danny |
| `src/cd_form.py`, `src/sires.py`, `src/pace.py`, `src/going.py`, new `src/*_signal.py` | Rusty |
| `src/racecard.py`, `scripts/refresh_friday.py`, `data/enrichment/*.json` | Livingston |
| `src/report.py`, `src/betting.py`, `outputs/*.html` | Linus |
| `scripts/morning_odds.py` (execution), pipeline orchestration, race-day refresh jobs | River |
| `tests/*` | Saul |

## Rules

- Multi-domain work → fan out in parallel (e.g. Rusty builds signal + Saul writes tests + Linus updates report copy)
- Reviewer rejection lockout applies normally: Saul rejects → original author cannot self-revise
- New horse races / fresh racecards → Livingston first, then signal/report work fans out
