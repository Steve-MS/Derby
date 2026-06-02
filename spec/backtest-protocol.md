# Backtest Protocol v0.1 — Epsom Ladies Day (Fri 6 June 2025)

**Author:** Jayne (QA)  
**Date:** 2026-06-02  
**Status:** PRE-REGISTERED — thresholds locked before Friday runs  
**Purpose:** Define what "validated" means for Kaylee's race-scoring model so Steve can decide whether to trust Saturday (Derby Day) predictions.

---

## 1. What "Validated" Means

Validation is a *smoke test*: does the model perform better than a blind random guess on a single race card? We use six metrics to get a multi-dimensional picture.

### 1.1 Win Strike Rate
**Definition:** Percentage of races where the model's #1 ranked runner won.  
**Formula:** `wins / races_run * 100`  
**Baseline to beat:** Random guess in a typical field of 8 = 12.5%. We'd like ≥ 20%.

### 1.2 Place Strike Rate
**Definition:** Percentage of races where the model's #1 ranked runner finished in the top 3 (regardless of field size).  
**Formula:** `place_finishes / races_run * 100`  
**Baseline to beat:** Random guess in a field of 8 = 37.5%. We'd like ≥ 30% (allowing that our top pick may be a longer shot).

### 1.3 Each-Way (EW) Strike Rate
**Definition:** Percentage of races where the model's top pick finished within standard EW terms.  
**EW terms by field size:**
- Fields of 5–7: top 2
- Fields of 8–15: top 3
- Fields of 16+: top 4 (1/4 odds, standard EW)

**Formula:** `ew_finishes / races_run * 100`

### 1.4 Top-3 Inclusion Rate *(primary gate metric)*
**Definition:** Percentage of races where the race winner appeared somewhere in the model's top 3 ranked runners.  
**Formula:** `races_winner_in_top3 / races_run * 100`  
**Rationale:** This is the most forgiving of "does the model understand the race?" It doesn't require the model to nail #1; it just asks whether the model saw the winner as a contender.

### 1.5 Brier Score
**Definition:** Mean squared error between the model's implied probability for each runner and the binary outcome (1 = won, 0 = didn't win).  
**Formula:** `mean((prob_i - outcome_i)^2)` summed across all runners in all races.  
**Normalisation:** Kaylee's raw scores must be softmax-normalised to implied probabilities before computing. If scores are not available as probabilities, skip this metric and note it in the report.  
**Interpretation:** Lower = better. A perfect model scores 0; random guess in an 8-runner field ≈ 0.109. Anything below 0.100 is decent.

### 1.6 ROI (Return on Investment)
**Definition:** If we'd backed every model top pick at Starting Price (SP) with £1 win stake, what is the net return?  
**Formula:** `(sum_of_returns - total_staked) / total_staked * 100`  
Where `sum_of_returns` = SP of winner if our top pick won, else 0.  
**SP source:** River fetches SP from results file on Friday evening.  
**Note:** SP includes bookmaker margin. A break-even model in the long run would achieve ROI ≈ -5% to -8% (reflecting overround). ROI > 0% on a single day is extremely lucky; ROI > -25% is respectable.

---

## 2. Pass/Fail Thresholds

### Threshold Summary

| Band  | Condition | Action |
|-------|-----------|--------|
| 🟢 GREEN | Top-3 inclusion ≥ 50% **AND** Place strike ≥ 30% **AND** ROI > -25% | Trust Saturday predictions fully |
| 🟡 AMBER | Top-3 inclusion 35–49% (and not RED) | Trust HIGH-confidence picks only (top score significantly ahead of field); skip close-call races |
| 🔴 RED | Top-3 inclusion < 35% **OR** ROI < -50% | Model is broken or misconfigured — do not bet Saturday |

### Justification

**Why these numbers?**

Friday's card is ~7–8 races. At 7 races, a 95% confidence interval on a true 50% top-3 rate spans roughly ±38 percentage points (binomial, n=7). That means we *cannot* make a statistically reliable claim — we are doing a smoke test, not a proof.

The thresholds are calibrated against two anchors:

1. **Random baseline.** A model with no information that randomly ranks runners would include the winner in its top 3 at a rate of `3/N` per race. For average field size 8, that's 37.5%. Our GREEN threshold (50%) must comfortably beat this random baseline.

2. **Catastrophic failure detection.** A RED at < 35% means the model is performing *below* random expectation — a signal of a bug, wrong weights, or bad data. ROI < -50% on 7 races means we likely missed every winner by a wide margin.

**AMBER guidance:** In 35–49% top-3 territory, the model is borderline. Steve should look at the confidence spread: if the model's #1 pick has a score substantially higher than #2 (say, >15% relative margin), that pick may still be worth a small stake. If scores are clustered, skip.

---

## 3. Sample Size Caveat

**Friday is ~7 races. This is a small sample.**

| n races | Margin of error (95% CI, true rate 50%) |
|---------|----------------------------------------|
| 7       | ±38%                                   |
| 20      | ±22%                                   |
| 50      | ±14%                                   |
| 100     | ±10%                                   |

A single-day backtest has wide confidence intervals. A GREEN result on Friday does **not** prove the model is profitable long-term. It proves the model is not obviously broken on a real card under race-day conditions.

**Recommendation:** If time permits before Saturday morning, Steve should ask Kaylee to run the model against one additional historical Epsom card (e.g., last year's Derby card or any comparable flat card with published SP). Even one extra card halves the noise. However, this is optional for v0.1 validation — Friday is the minimum bar.

---

## 4. What We Are NOT Validating (v0.1 Scope Exclusions)

The following are explicitly out of scope for this backtest. Do not draw conclusions about them from Friday's results:

- **Long-term EV / profitability.** Seven races cannot establish a betting edge. A positive ROI on Friday is luck as much as skill.
- **Going-specific performance.** Epsom in June is typically Good to Firm. We have no data on how the model performs on Soft or Heavy.
- **Race-type specificity.** We are not separately validating Group races vs handicaps vs maidens. The model is scored across the whole card as a unit.
- **Distance profile.** Epsom has a mix of 5f to 14f races. We are not slicing by distance.
- **Market efficiency assumptions.** ROI calculations use SP, which is post-market. We are not validating whether the model beats the market at a fixed time pre-race.
- **Staking strategy.** We are only testing flat £1 win stakes. Kelly criterion, each-way staking, and lay betting are all out of scope.

---

## 5. Pre-Registration Procedure (Freeze Protocol)

The model picks for Friday **must be frozen before Friday's races begin** so we cannot retro-fit weights to match results.

### Step-by-step

1. **Run the model** against Friday's race card (Kaylee's `score_race()` or equivalent CLI command).
2. **Save output** to: `race-analysis/predictions/predictions-frozen-2025-06-06.json`  
   (The Friday card is 5 June 2025 per the race calendar. Note: file is dated by the race date, not today.)
3. **Commit the file** to the git repository:
   ```
   git add race-analysis/predictions/predictions-frozen-2025-06-06.json
   git commit -m "chore: freeze Friday Ladies Day predictions [pre-registered]"
   ```
4. **Record the commit SHA.** The backtest harness (`tests/backtest.py`) accepts `--predictions` pointing to this file. The SHA is the audit trail.
5. **Do not modify** the predictions file after the first race goes off. If any modification is made post-race, the backtest result is invalidated.

### Frozen predictions schema

```json
{
  "frozen_at": "2025-06-06T09:00:00Z",
  "frozen_by": "kaylee",
  "commit_sha": "<git SHA here>",
  "card_date": "2025-06-06",
  "venue": "Epsom",
  "races": [
    {
      "race_id": "epsom-2025-06-06-r1",
      "race_time": "14:00",
      "race_name": "string",
      "field_size": 8,
      "rankings": [
        {
          "rank": 1,
          "horse_name": "string",
          "score": 0.82,
          "implied_prob": 0.31,
          "confidence": "high"
        }
      ]
    }
  ]
}
```

---

## 6. Actual Results Schema

River fetches actual results on Friday evening. Results must be saved to:  
`race-analysis/results/results-frozen-2025-06-06.json`

```json
{
  "fetched_at": "2025-06-06T19:00:00Z",
  "fetched_by": "river",
  "card_date": "2025-06-06",
  "venue": "Epsom",
  "source": "racingpost|attheraces|bha",
  "races": [
    {
      "race_id": "epsom-2025-06-06-r1",
      "race_time": "14:00",
      "race_name": "string",
      "field_size": 8,
      "going": "Good to Firm",
      "finishers": [
        {
          "position": 1,
          "horse_name": "string",
          "sp": 4.5,
          "sp_decimal": 4.5,
          "bsp": null,
          "ran": true,
          "non_runner": false
        }
      ]
    }
  ]
}
```

**Field notes:**
- `sp_decimal`: Starting Price as a decimal (e.g. 4.5 = 7/2). Required for ROI calculation.
- `bsp`: Betfair SP — optional, include if River can fetch it (better for ROI accuracy).
- `non_runner`: If true, exclude this horse from all metric calculations and reduce `field_size` by 1 for EW terms.
- All finishers should be included (not just the top 4), ordered by finishing position.

---

## 7. Running the Backtest

```bash
cd race-analysis
python tests/backtest.py \
  --predictions predictions/predictions-frozen-2025-06-06.json \
  --results results/results-frozen-2025-06-06.json
```

Exit codes: `0` = GREEN, `1` = AMBER, `2` = RED.

---

*Protocol pre-registered and locked: 2026-06-02. Do not modify thresholds after Friday races begin.*
