# Danny — History

## Project context (seeded 2026-06-03)

- Python 3.12 race-analysis toolkit for Steve (Steve-MS).
- Repo: github.com/Steve-MS/Derby on main, last commit 5a1770e.
- Python interpreter: `C:\Users\stevenn\AppData\Local\Programs\Python\Python312\python.exe`.
- 227 pytest tests passing.
- Scoring weights v0.3, sum 1.0. Sire stamina at 0.05.
- Backlog (impact order): trial form → market move → trainer 14-day → J/T combo → equipment/wind.
- Derby Saturday 6 Jun 2026. Ladies Day Friday 5 Jun. Both raced.
- Steve's daily outlay cap: £100. Wants accumulator suggestion per day.
- Current Derby top 5: Item, Maltese Cross, Causeway (outsider pick), Benvenuto Cellini, Christmas Day.

## Learnings

- 2026-06-03 (session 1): Designed trial_form signal (weight 0.08, gated 10f+, Tier 1/2/3 taxonomy, best-of-multiple-runs, neutral 50 on missing data); proposed v0.4 weights scaling all v0.3 by 0.92; spec written to `.squad/decisions/inbox/danny-trial-form-design.md` for Rusty to implement.
- 2026-06-03 (session 2): Designed 3 new signals for v0.5 (Derby Saturday T−2 days). Spec at `.squad/decisions/inbox/danny-3-signals-design.md`.
  - `market_move` (0.0700): implied-probability-shift scoring (Δip = ip_latest − ip_baseline); piecewise linear 10–90; Saturday 09:00 baseline vs T−30 min latest; both prices required else neutral 50; Livingston to extend Friday scraper. 8 open questions for Steve (timing, source, small-field treatment).
  - `trainer_14d` (0.0400): 14-day strike rate; sample guard < 5 runners → 50; piecewise linear calibrated to UK flat ~10–12% average at neutral; per-trainer JSON keyed by trainer name. Questions: surface scope (AW?), window length (14 vs 21d), ROI secondary metric.
  - `jt_combo` (0.0300): jockey/trainer interaction term; combo strike rate over trailing 365d; sample guard < 10 partnerships → 50; first-time pairing scores 60; pipe-delimited combo_key. Questions: time window, first-booking lean, double-count mitigation vs existing jockey + trainer_form signals.
  - v0.5 weight rebalance: existing 12 signals × 0.86; class_rating absorbs −0.0001 rounding residual (0.2032 → 0.2031); 15-signal total sums exactly to 1.0000.
- 2026-06-03 (session 3): Designed equipment signal for v0.6 (equipment-only; wind ops dropped — paywalled per Livingston's probe). Spec at `.squad/decisions/inbox/danny-equipment-design.md`.
  - `equipment` (0.0250): item-weighted delta score; base 50; first-time-use bonuses by item type (b=+8, cp=+7, tt=+6, v=+5, h=+3, e/p=+2); stacking penalty −3 per extra item beyond first; equipment removal +3 per item; clamp [10, 90]; neutral 50 on missing horse or empty lists. No distance/surface gate.
  - Data: `data/enrichment/equipment.json` (Livingston to rename from equipment-wind.json; source: Open Horse Racing Data free CSV).
  - v0.6 weight rebalance: existing 15 v0.5 signals × 0.9750; class_rating absorbs −0.0002 rounding overshoot (0.1980 → 0.1978); 16-signal total sums exactly to 1.0000.
  - 4 open questions for Steve (stacking penalty, removal direction, Livingston data reliability, scope Friday+Saturday).

- 2026-06-03 (session 4): Resolved v0.5 spec-vs-implementation mismatches in `.squad/decisions/inbox/danny-v05-spec-addendum.md`.
  - `score_market_move(0.024)` stays at 65.5: the piecewise curve itself is coherent; the `~62` anchor was an arithmetic/example error.
  - `score_trainer_14d(0.10)` stays at 50.0: neutral at 10% is defensible and matches the stated 10–12% average-band intent.
  - `jt_combo` first-time override applies only when `combo_runners == 0`; if combo history exists, the sample guard/scoring curve wins and the flag is audit noise.
  - No runtime code change required; v0.5 can ship as-is with spec/documentation clarification only.
