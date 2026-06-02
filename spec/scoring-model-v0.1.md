# Scoring Model v0.1 — Epsom Race Analysis

**Author:** Kaylee (Data Engineer)  
**Date:** 2026-06-02  
**Status:** Draft — designed for Epsom 5-6 June 2026  
**Version:** 0.1  
**Reproducibility note:** All weights are configurable via `load_default_config()`. Changes to weights must be re-run against the full racecard to recompute ranks.

---

## 1. Purpose

Transform a `Runner` dict (produced by River's ingestion pipeline) into a numeric `score` (0–100 scale, normalised within the race) plus a `score_breakdown` showing per-signal contributions. Rank all runners in a race; emit a bet recommendation and a race competitiveness rating.

This is v0.1 — an opinionated starting point. Jayne will backtest these weights against historical Epsom results; expect v0.2 to rebalance.

---

## 2. Input Data Shape

```python
Runner = {
    "horse":           str,          # Horse name
    "age":             int | None,
    "rpr":             float | None,  # Racing Post Rating
    "ts":              float | None,  # Topspeed rating
    "or_rating":       float | None,  # Official Rating
    "form_string":     str | None,    # e.g. "112-32"
    "runs": [                         # Last N runs, newest first
        {
            "position":     int | None,
            "days_ago":     int,
            "course":       str,
            "distance_f":   float,    # furlongs
            "going":        str,
        }
    ],
    "trainer":         str | None,
    "jockey":          str | None,
    "draw":            int | None,    # stall number
    "course_wins":     int,           # wins at this course
    "course_places":   int,           # places at this course
    "cd_wins":         int,           # course-and-distance wins
    "cd_places":       int,           # course-and-distance places
    "last_class":      int | None,    # class of last race (1=top)
    "current_class":   int | None,    # class of today's race
    "first_time_epsom": bool,
    "going_preference": str | None,   # "good", "soft", "firm", "any"
}

Race = {
    "race_id":      str,
    "course":       str,            # "Epsom"
    "distance_f":   float,          # e.g. 5.0, 14.0
    "going":        str,            # forecast going
    "runners":      list[Runner],
}
```

---

## 3. Signal Set and Weights

| # | Signal | Default Weight | Rationale |
|---|--------|---------------|-----------|
| 1 | Class/rating | **35%** | Rating is the single strongest predictor of flat race outcomes. RPR is the most comprehensive; fall back to TS, then OR, then a neutral default of 50. Z-score within the race ensures relative comparison, not absolute. |
| 2 | Recent form | **20%** | Recent finishing positions are the second strongest signal. Weighted by recency (last run counts most). Long absence penalised. |
| 3 | Trainer form | **10%** | Top yards run hot at big meetings. We proxy 14-day strike rate with a configurable bump table; real strike rates can replace this in v0.2. |
| 4 | Jockey suitability | **10%** | Top retained jockeys are booked on fancied runners; their presence is informational. |
| 5 | Course & distance | **10%** | C&D form is the strongest track-specific predictor, especially for Epsom's undulating camber. First-time visitors to 1m4f (Derby/Oaks) penalised. |
| 6 | Going suitability | **5%** | Smaller weight because going preference data is often incomplete; we only act when we have explicit evidence. |
| 7 | Draw bias | **5%** | Material only for the 5f Dash (low stall favoured on good ground). Neutral elsewhere. |
| 8 | Class move | **5%** | Dropping/rising in class is a secondary signal; small effect. |
| **Total** | | **100%** | |

---

## 4. Signal Computation Detail

### 4.1 Class/Rating Signal (35%)

```
best_rating = first non-null of [RPR, TS, OR, 50]
raw_signal  = z_score(best_rating, all runners in race)
```

- Z-score is clipped to [−3, +3] then linearly rescaled to [0, 100].
- If all runners lack ratings (all null), signal = 50 for everyone and confidence is forced to LOW.

### 4.2 Recent Form Signal (20%)

```
position_points = {1: 10, 2: 6, 3: 4, 4: 2, else: 0}
recency_weights = [1.0, 0.75, 0.5, 0.3, 0.15]  # last run → oldest of 5

form_score = sum(position_points[run.position] * recency_weight
                 for run, recency_weight in zip(runs[:5], recency_weights))

# Cap: max theoretical score = 10*(1.0+0.75+0.5+0.3+0.15) = 27.0
# Normalise to 0–100 within race.

# Long absence penalty (days since last run):
if days_since_last_run > 120:
    form_score -= 5
```

- Horses with zero runs get the race median form score.

### 4.3 Trainer Form Signal (10%)

```
trainer_bump = config["trainer_bumps"].get(trainer_name, 0)
# Returns value in [0, 10]; top trainers +10, good yards +7, smaller +0.
# Normalised to 0–100: trainer_bump / 10 * 100
```

Current default bumps (Epsom meeting context):

| Trainer | Bump |
|---------|------|
| Aidan O'Brien | +10 |
| John Gosden / Gosden & Gosden | +9 |
| Richard Hannon | +8 |
| Andrew Balding | +8 |
| William Haggas | +8 |
| Charlie Appleby | +9 |
| Roger Varian | +7 |
| Ralph Beckett | +7 |
| All others | 0 (neutral) |

### 4.4 Jockey Suitability Signal (10%)

```
jockey_bump = config["jockey_bumps"].get(jockey_name, 0)
# Returns value in [0, 10]
```

Current default bumps:

| Jockey | Bump |
|--------|------|
| Ryan Moore | +10 |
| William Buick | +9 |
| Oisin Murphy | +9 |
| James Doyle | +7 |
| Tom Marquand | +7 |
| Robert Havlin | +6 |
| All others | 0 |

> Frankie Dettori is retired from British flat racing as of 2024; remove if not active in 2026 fixtures.

### 4.5 Course & Distance Signal (10%)

```
cd_bonus = 0
if cd_wins > 0:     cd_bonus += 15
elif cd_places > 0: cd_bonus += 8
elif course_wins > 0: cd_bonus += 5
elif course_places > 0: cd_bonus += 3

# Epsom-specific first-timer penalty for 1m4f races:
if first_time_epsom and race.distance_f >= 12:
    cd_bonus -= 10

# Clip to [0, 20], then normalise to 0–100.
```

### 4.6 Going Suitability Signal (5%)

```
if going_preference is None:       signal = 50  # neutral
elif going_preference == forecast_going:  signal = 80  # match
elif going_preference == "any":    signal = 55
else:                              signal = 25  # mismatch
```

A "firm" preference on "good to soft" counts as a mismatch.

### 4.7 Draw Bias Signal (5%)

```
# Only material for 5f Dash (race.distance_f == 5.0, course == "Epsom")
if race.distance_f == 5.0 and race.course == "Epsom":
    # Low draws (1–4) favoured on good/good-to-firm ground
    if draw is not None and draw <= 4 and forecast_going in ("good", "good to firm"):
        signal = 80
    elif draw is not None and draw > 10:
        signal = 30
    else:
        signal = 50
else:
    signal = 50  # neutral for all other races
```

Configurable per race via `config["draw_bias"]`.

### 4.8 Class Move Signal (5%)

```
if last_class is None or current_class is None:
    signal = 50  # neutral
elif current_class < last_class:   # dropping in class (lower number = higher class)
    signal = 70  # bonus
elif current_class > last_class:   # rising in class
    signal = 30  # penalty
else:
    signal = 50  # same class
```

Note: class numbering convention is 1 (Group 1) → 7 (handicap). Lower number = better class.

---

## 5. Aggregation and Normalisation

### 5.1 Raw Score

```
raw_score = sum(signal_value * weight for signal_value, weight in zip(signals, weights))
```

Each signal is on a 0–100 scale before weighting.

### 5.2 Race Normalisation

After computing raw scores for all runners in the race:

```
min_s = min(raw_scores)
max_s = max(raw_scores)
if max_s - min_s < 1:
    # All equal — assign 50 each
    normalised = [50] * n
else:
    normalised = [(s - min_s) / (max_s - min_s) * 90 + 5
                  for s in raw_scores]
    # Floor at 5, ceiling at 95 (leaving headroom; favourite won't score 100 mechanically)
```

### 5.3 Confidence

```
gap = score_1st - score_2nd

if gap > 15:   confidence = "HIGH"
elif gap > 5:  confidence = "MED"
else:          confidence = "LOW"

# Override: LOW if any required signal is missing (all ratings null)
# Override: LOW if race_stdev < 8 (wide-open race)
```

### 5.4 Bet Recommendation

```
if confidence == "HIGH" and score_1st >= 40:  bet = "WIN"
elif confidence == "MED" and score_1st >= 40: bet = "EW"
else:                                          bet = "PASS"
```

### 5.5 Race Competitiveness

```
race_stdev = stdev(normalised_scores)
# < 8  → "WIDE OPEN" (lean PASS or saver)
# 8–15 → "COMPETITIVE"
# > 15 → "CLEAR FAVOURITE"
```

---

## 6. Output Shape

```python
RaceResult = {
    "race_id": str,
    "ranked_runners": [
        {
            "rank":            int,
            "horse":           str,
            "score":           float,         # 0–100
            "score_breakdown": {
                "class_rating":       float,
                "recent_form":        float,
                "trainer_form":       float,
                "jockey":             float,
                "course_distance":    float,
                "going":              float,
                "draw_bias":          float,
                "class_move":         float,
            },
            "raw_signal_values": dict,        # pre-weight signal values, for audit
        }
    ],
    "confidence":           str,              # "HIGH" | "MED" | "LOW"
    "bet_recommendation":   str,              # "WIN" | "EW" | "PASS"
    "race_stdev":           float,
    "race_competitiveness": str,              # "WIDE OPEN" | "COMPETITIVE" | "CLEAR FAVOURITE"
    "missing_data_flags":   list[str],        # e.g. ["no_ratings", "no_trainer_data"]
}
```

---

## 7. Tunable Knobs (for Jayne's Backtest)

The following are the primary tunable parameters exposed via `load_default_config()`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `weights.class_rating` | 0.35 | Weight for class/rating signal |
| `weights.recent_form` | 0.20 | Weight for recent form signal |
| `weights.trainer_form` | 0.10 | Weight for trainer form |
| `weights.jockey` | 0.10 | Weight for jockey suitability |
| `weights.course_distance` | 0.10 | Weight for C&D form |
| `weights.going` | 0.05 | Weight for going suitability |
| `weights.draw_bias` | 0.05 | Weight for draw bias |
| `weights.class_move` | 0.05 | Weight for class move |
| `form.position_points` | `{1:10, 2:6, 3:4, 4:2}` | Points per finishing position |
| `form.recency_weights` | `[1.0,0.75,0.5,0.3,0.15]` | Decay across last 5 runs |
| `form.absence_threshold_days` | 120 | Days before long-absence penalty |
| `form.absence_penalty` | 5 | Point penalty for long absence |
| `cd.cd_win_bonus` | 15 | Bonus for C&D win |
| `cd.cd_place_bonus` | 8 | Bonus for C&D place |
| `cd.course_win_bonus` | 5 | Bonus for course win (not C&D) |
| `cd.first_time_epsom_penalty` | 10 | Penalty: first time at Epsom, 1m4f+ |
| `confidence.high_gap` | 15 | Score gap for HIGH confidence |
| `confidence.med_gap` | 5 | Score gap for MED confidence |
| `confidence.min_score_for_bet` | 40 | Minimum score to recommend WIN/EW |
| `competitiveness.wide_open_stdev` | 8 | Stdev below which race is "WIDE OPEN" |
| `competitiveness.clear_fav_stdev` | 15 | Stdev above which race has "CLEAR FAVOURITE" |
| `trainer_bumps` | (table above) | Per-trainer raw bonus (0–10) |
| `jockey_bumps` | (table above) | Per-jockey raw bonus (0–10) |

All weights must sum to 1.0. The implementation validates this at config load.

---

## 8. Missing Data Policy

| Missing Data | Fallback |
|-------------|---------|
| All ratings (RPR, TS, OR) null | Class signal = 50 (neutral); flag `no_ratings`; force confidence LOW |
| No runs data | Form signal = race median; flag `no_form` |
| Trainer unknown | Trainer bump = 0 (neutral) |
| Jockey unknown / TBC | Jockey bump = 0 (neutral) |
| Draw missing | Draw signal = 50 (neutral) |
| Class info missing | Class move signal = 50 (neutral) |
| Going preference unknown | Going signal = 50 (neutral) |

---

## 9. Assumptions and Limitations

1. **Rating freshness:** RPR/TS/OR are used as-is from the data source. Stale ratings (e.g. a horse that ran once 2 years ago) will distort the class signal. River should annotate rating age; v0.2 can apply a staleness discount.
2. **Trainer/Jockey bumps are static:** Real 14-day strike rates would improve accuracy. This is the most important upgrade for v0.2.
3. **Going preference is binary:** We use a simple match/mismatch. A gradient (going preference vs. forecast distance, e.g. "good to firm" vs. "good") would be more accurate.
4. **Draw bias is Dash-only:** The model assigns neutral draw signal for all non-5f races. Evidence suggests some bias at 1m2f too; defer to backtest.
5. **No market signal:** Odds are intentionally excluded from v0.1 to keep the model predictive rather than reflexive. Market can be added as a separate signal in v0.2.
6. **Class numbering:** Assumes 1 = Group 1 / best class, 7 = lower handicap. River must normalise source class labels to this scale.

---

## 10. Change Log

| Version | Date | Author | Note |
|---------|------|--------|------|
| 0.1 | 2026-06-02 | Kaylee | Initial design |
