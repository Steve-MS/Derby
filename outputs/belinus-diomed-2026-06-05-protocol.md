# Belinus — Diomed Stakes Backtest Protocol
**Race:** Diomed Stakes, Epsom — Friday 6 June 2026 (Ladies Day)
**Date written:** 2026-06-04 (pre-race)
**Author:** Jayne (QA/Tester)
**Status:** PRE-RACE — protocol sealed before first race

---

## Purpose

This document records the pre-race prediction and result-recording procedure
for the Belinus bet in the Diomed Stakes.  Belinus is the model's expected
top pick for this race and is being used as the *primary single bet* to
evaluate model performance on Friday before Steve places full bets on Saturday
Derby Day.

Pre-registration rule (from backtest-protocol.md §2): **this file must be
committed to git before the Diomed Stakes goes off**. The commit SHA is the
tamper-evident seal.  Do not modify this file after that commit.

---

## Prediction (to be filled at time of racecard fetch)

| Field | Value |
|---|---|
| Horse | Belinus |
| Race | Diomed Stakes (14:25 approx) |
| Going at fetch | Good / Good to Soft |
| Model rank | 1 (expected) |
| Confidence | HIGH |
| Bet type | WIN single |
| Decimal odds | 3.5 (5/2) — indicative |
| Stake pts | ~1.92 pts (¼-Kelly at model_prob ≈ 0.3077) |
| Stake GBP (at £100 bankroll) | £1.92 |
| Expected value | +£1.125 (at model_prob = 0.35 matching market implied) |

**EV calculation:**
```
stake_gbp = £5.00   ← illustrative flat stake (replace with actual Kelly output)
dec_odds  = 3.5
model_prob = score_race() output: Belinus_score / sum(all_scores)

EV = (stake_gbp × dec_odds × model_prob) − stake_gbp
   = (£5 × 3.5 × 0.35) − £5
   = £6.125 − £5
   = +£1.125  ← positive EV if model_prob > implied_prob (0.286)
```

If `model_prob` from `score_race()` is below `1/dec_odds` (0.286 for 3.5),
the Kelly bet will be PASS.  Do not override PASS output.

---

## Running the prediction

```bash
# Step 1: Confirm racecard is present
python -m src.cli fetch --date 2026-06-05

# Step 2: Score all runners
python -m src.cli score --date 2026-06-05

# Step 3: Generate bets
python -m src.cli predict --date 2026-06-05 --bankroll 100.0

# Step 4: Freeze predictions (MUST happen before first race)
cp outputs/scores-2026-06-05.json outputs/scores-frozen-2026-06-05.json
cp outputs/bets-2026-06-05.json   outputs/bets-frozen-2026-06-05.json
git add outputs/scores-frozen-2026-06-05.json outputs/bets-frozen-2026-06-05.json
git add outputs/belinus-diomed-2026-06-05-protocol.md
git commit -m "freeze: Diomed Stakes predictions 2026-06-05 (pre-race)"
# Record commit SHA here after committing: SHA = _____________
```

---

## Result recording (to be filled Friday evening by River or Steve)

River: after the Diomed Stakes result is official, populate
`data/results/results-2026-06-05.json` in the format defined in
`spec/backtest-protocol.md §6`:

```json
{
  "date": "2026-06-05",
  "meeting": "Epsom",
  "races": [
    {
      "race_id": "epsom-2026-06-05-1425",
      "race_name": "Diomed Stakes",
      "finishers": [
        {
          "position": 1,
          "horse": "WINNER NAME",
          "sp_decimal": 3.50,
          "non_runner": false
        }
      ]
    }
  ]
}
```

Then run the backtest harness:

```bash
python tests/backtest.py \
  --predictions outputs/scores-frozen-2026-06-05.json \
  --results data/results/results-2026-06-05.json
```

**Expected output fields to record here:**

| Metric | Target | Actual |
|---|---|---|
| Win strike rate | — | ___ |
| Place strike rate | ≥ 30% (GREEN) | ___ |
| Top-3 inclusion | ≥ 50% (GREEN) | ___ |
| ROI | > −25% (GREEN) | ___ |
| Brier score | < 0.25 (GREEN) | ___ |
| Verdict | GREEN/AMBER/RED | ___ |

---

## Derby Day go/no-go gate

Per `spec/backtest-protocol.md` §4:

- **GREEN** → Full Saturday bet list: trust all HIGH-confidence singles, EW,
  Lucky 15, outsiders.  Maximum bankroll exposure.
- **AMBER** → HIGH-confidence WIN singles only.  No EW, no multis, no outsiders.
  Half-Kelly staking.
- **RED** → No bets Saturday.  Flag to Mal for model review.

---

## Known risks at time of writing (2026-06-04)

1. **Going change (Good → Soft):** If going changes overnight or on race
   morning, `score_race()` must be re-run with the updated going string.
   The CLI `cmd_score` reads going from the racecard JSON — confirm River
   updates `epsom-2026-06-05-racecards.json` if official going is declared
   after initial fetch.  See `test_regression_wave3.py::TestGoingNormalizationDerbyWeekend`.

2. **Non-runners:** `cli._normalize_race()` filters `withdrawn=True` runners
   before scoring.  If Belinus is declared a non-runner (injury, etc.) the
   model will not score it, and `build_bets()` will PASS on the race.
   Check BHA non-runner list at 10:00 on race day.

3. **Market data cache:** `market_move.py` uses `lru_cache` on
   `load_market_data()`.  If odds are refreshed after the initial load
   (common in morning/afternoon), the process must be restarted (not just
   re-run in the same Python process) to pick up the latest prices.
   River's `cmd_predict` launches a fresh process — this is safe in
   production.  Avoid calling `score_race()` twice in the same session
   with different market data.

4. **Synthetic odds fallback:** If River's market feed is unavailable,
   `market_move_signal()` returns neutral 50.  The model will still score
   but outsider picks will be suppressed (< 4 real-odds runners).
   Watch `"Insufficient market signal"` in the outsider rationale output.
