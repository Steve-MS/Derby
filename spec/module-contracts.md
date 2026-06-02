# Module Contracts — race-analysis v0.1

**Author:** Mr. Universe (report contract); Wash (betting contract + CLI integration)  
**Date:** 2026-06-02  
**Status:** CONFIRMED — Badger and Mr. Universe build against these shapes  

---

## `report.render()` — HTML Report Generator

**Location:** `src/report.py`  
**Called by:** Wash's CLI (`python -m race_analysis report --date YYYY-MM-DD`)

### Signature

```python
def render(
    date: str,               # ISO date string: "2026-06-05" or "2026-06-06"
    scores: list[dict],      # list of scored-race dicts (see §scores shape)
    bets: dict,              # Badger's bet portfolio (see §bets shape); may be {} or None
    race_context: dict,      # race-day context/narrative (see §race_context shape)
    output_path: str,        # filesystem path to write the HTML file
) -> None
```

Writes a single self-contained HTML file to `output_path`. Raises no exceptions on empty inputs — renders a minimal valid HTML page if `scores=[]`, `bets={}`, `race_context={}`.

---

### §scores shape — one item per race

```json
{
  "race_id": "epsom-2026-06-05-1330",
  "race_meta": {
    "time": "13:30",
    "name": "Win With Zyn 3yo Dash Handicap",
    "distance_f": 5,
    "going": "Good to soft",
    "prize_winner_gbp": 38655,
    "class": "Handicap",
    "runner_count": 10
  },
  "ranked_runners": [
    {
      "rank": 1,
      "horse": "Cato (IRE)",
      "trainer": "Unknown",
      "jockey": "TBC",
      "score": 72.5,
      "raw_signal_values": {
        "class_rating": 75.0,
        "recent_form": 60.0,
        "trainer_form": 0.0,
        "jockey": 0.0,
        "course_distance": 50.0,
        "going": 55.0,
        "going_fit": 35.0,
        "draw_bias": 80.0,
        "class_move": 50.0
      },
      "score_breakdown": {
        "class_rating": 26.25,
        "recent_form": 12.0,
        "trainer_form": 0.0,
        "jockey": 0.0,
        "course_distance": 5.0,
        "going": 2.75,
        "going_fit": 5.25,
        "draw_bias": 4.0,
        "class_move": 2.5
      },
      "missing_data_flags": [],
      "going_data": "insufficient"
    }
  ],
  "confidence": "MED",
  "bet_recommendation": "EW",
  "race_stdev": 12.5,
  "race_competitiveness": "COMPETITIVE"
}
```

**Notes:**
- `ranked_runners` items are sorted rank=1 first (best to worst).
- `trainer` and `jockey` fields on each runner are optional — render shows "—" if absent.
- `raw_signal_values` signals: `class_rating`, `recent_form`, `trainer_form`, `jockey`, `course_distance`, `going`, `going_fit`, `draw_bias`, `class_move`.  Each is 0–100.
- `race_meta.going` / racecard `going` supplies the target race-day going. If omitted, scoring defaults to `"Good"`; if explicitly `null`, `going_fit` is neutral/non-ranking.
- `going_fit` is Kaylee's historical ground-fit factor (15% model weight): weighted win rate on matching/adjacent going families, effective sample confidence, and recency. When no usable historical going evidence exists, per-runner `going_data` is `"insufficient"` and `going_fit` is emitted as a low-confidence 35/100 signal.
- `confidence`: `"HIGH"` | `"MED"` | `"LOW"` — one value per race (from `score_race()`).
- `bet_recommendation`: `"WIN"` | `"EW"` | `"PASS"` — one value per race.

**Assembly (Wash's responsibility):**  
Call `score_race(race, config)` for each race, then enrich `ranked_runners` items with `trainer` and `jockey` from the original racecard `runners[]` array (keyed by `horse` name). Add `race_meta` from the racecard header.

---

### §bets shape — Badger's portfolio output

```json
{
  "singles": [
    {
      "race_id": "epsom-2026-06-05-1330",
      "horse": "Cato (IRE)",
      "bet_type": "WIN",
      "stake_gbp": 5.00,
      "price": "7/2",
      "est_return_gbp": 22.50
    }
  ],
  "doubles": [
    {
      "legs": ["epsom-2026-06-05-1330|Cato (IRE)", "epsom-2026-06-05-1440|Horse B"],
      "stake_gbp": 2.00,
      "est_return_gbp": 30.00,
      "label": "Dbl: Cato / Horse B"
    }
  ],
  "trebles": [ /* same shape as doubles, 3 legs */ ],
  "accas": [ /* 4+ leg accumulators */ ],
  "lucky15": null,
  "portfolio_summary": {
    "total_stake_gbp": 25.00,
    "est_total_return_gbp": 150.00,
    "edge_pct": 12.5,
    "bankroll_pct": 25.0,
    "bankroll_default_gbp": 100.0
  }
}
```

**Graceful degradation:** If `bets` is `None`, `{}`, or any sub-list is missing/empty, the render omits that section silently. The "Day Portfolio" section is hidden entirely if `bets` is empty.

---

### §race_context shape

```json
{
  "going_friday": "Good to soft in places",
  "going_saturday": "Good; good to firm in places",
  "narrative_friday": "Light rain expected. Ballydoyle dominant. O'Brien has 12 runners...",
  "narrative_saturday": "Fast ground likely. Derby: Benvenuto Cellini favourite...",
  "backtest_verdict": null,
  "model_version": "v0.1",
  "generated_at": "2026-06-02T11:49:20+01:00"
}
```

All fields optional. `backtest_verdict`: `"GREEN"` | `"AMBER"` | `"RED"` | `null` — controls the verdict badge. `null` renders "Not yet validated".

---

### Return value

`None`. Side effect: writes HTML to `output_path`.

---

## CLI integration (Wash)

```bash
# Wash calls report.render() after score step:
python -m race_analysis report --date 2026-06-05
# -> writes outputs/reports/epsom-2026-06-05.html
```

Expected CLI call in `__main__.py`:

```python
from src.report import render
render(
    date=args.date,
    scores=scored_races,      # list of dicts from score_race()
    bets=bet_portfolio,       # from Badger; {} if not yet available
    race_context=ctx,         # from parsed race-day-context or {}
    output_path=f"outputs/reports/epsom-{args.date}.html",
)
```

---

## `betting.build_bets()` — Staking Engine (Badger)

**Location:** `src/betting.py`  
**Called by:** Wash's CLI (`python -m src.cli predict --date YYYY-MM-DD [--bankroll FLOAT]`)

### Signature

```python
def build_bets(
    scores: list[dict],   # .races array from outputs/scores-{date}.json
    bankroll: float,      # total available bank in GBP (e.g. 100.0)
    config: dict,         # staking config — Badger defines keys; CLI passes {} for now
) -> dict:
    ...
```

### `scores` element shape

Same as the `§scores shape` above — the full `score_race()` output enriched with `race_name`/`race_time` by the CLI.

Key fields for staking decisions:

| Field | Description |
|-------|-------------|
| `ranked_runners[0].horse` | Top pick horse name |
| `ranked_runners[0].score` | Model score 0–100 |
| `confidence` | `"HIGH"` \| `"MED"` \| `"LOW"` |
| `bet_recommendation` | `"WIN"` \| `"EW"` \| `"PASS"` (Badger may override) |
| `race_competitiveness` | `"CLEAR FAVOURITE"` \| `"COMPETITIVE"` \| `"WIDE OPEN"` |

### Return value

```json
{
  "date": "2026-06-05",
  "venue": "Epsom",
  "bankroll": 100.0,
  "total_staked": 35.0,
  "bets": [
    {
      "race_id":   "epsom-2026-06-05-1330",
      "race_name": "Win With Zyn 3yo Dash Handicap",
      "race_time": "13:30",
      "horse":     "Iron Duke",
      "bet_type":  "WIN",
      "stake":     10.0,
      "rationale": "HIGH confidence, score gap > 15pts"
    }
  ]
}
```

**Field rules:**
- `bet_type`: `"WIN"` | `"EW"` (each-way). Omit races with `"PASS"`.
- `stake`: GBP. Must satisfy `sum(bets[].stake) <= bankroll`.
- `bets`: include only races where a stake is placed.
- `rationale`: 1-sentence plain-English reason (used by report renderer).

---

## Deferred Signals — reserved for v0.2

| Field | Location | Notes |
|-------|----------|-------|
| `implied_prob` | `ranked_runners[].implied_prob` | Model probability; enables Brier scoring in backtest |
| `morning_price` | `runner.morning_price` | Raw racecard price e.g. `"5/2"` |
| `sp_decimal` | `runner.sp_decimal` | SP as decimal; needed for ROI calculation |

Once Kaylee adds these, `_to_backtest_predictions()` in `src/cli.py` can include `implied_prob` without any other CLI changes.

---

## §7 — `outsiders` list shape (new — added 2026-06-05)

`build_bets()` now returns an `"outsiders"` key: one entry per validated race.

**When an outsider is found:**

```json
{
  "race_id":                  "string",
  "race_name":                "string",
  "race_time":                "string",
  "horse":                    "string",
  "trainer":                  "string",
  "jockey":                   "string",
  "morning_price":            11.0,
  "odds_source":              "string",
  "model_rank":               4,
  "market_rank":              5,
  "rank_delta":               1,
  "bet_type":                 "EW",
  "stake_pts":                0.25,
  "stake_gbp":                0.25,
  "ew_terms":                 "1/4 odds, 1-1-2-3",
  "potential_return_gbp_win": 2.75,
  "potential_return_gbp_place": 0.875,
  "rationale":                "Model rates 4; market rates 5. Disagreement of 1 ranks — value play.",
  "outsider_pick":            "Dark Horse"
}
```

**When no outsider qualifies (null signal):**

```json
{
  "race_id":           "string",
  "outsider_pick":     null,
  "outsider_rationale": "Top 3 in market also top 3 on model — no value outsider"
}
```

Possible `outsider_rationale` values:
- `"Insufficient market signal"` — fewer than 4 runners with real odds, or all synthetic
- `"Top 3 in market also top 3 on model — no value outsider"` — full top-3 agreement
- `"No runner meets outsider criteria (market rank ≥4, model rank ≤4, odds ≥6.0, rank delta ≥1)"`
- `"Outsider bankroll cap reached"` — 5% bankroll cap exhausted

---

## §8 — `outsider_summary` in `portfolio_summary`

`portfolio_summary` now includes an `"outsider_summary"` sub-dict:

```json
"outsider_summary": {
  "count":                           1,
  "total_stake_gbp":                 0.50,
  "total_potential_return_gbp_win":  2.75,
  "total_potential_return_gbp_place": 0.875
}
```

`total_stake_gbp` = 2 × `stake_gbp` per valid outsider (EW = two legs). This amount is **also** included in `portfolio_summary.total_stake_gbp` for full-exposure visibility.

---

*End of contracts.*
