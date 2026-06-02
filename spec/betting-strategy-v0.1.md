# Betting Strategy Module — v0.1 Specification

**Module:** `race-analysis/src/betting.py`  
**Author:** Badger (APEX Squad — Betting Strategist)  
**Date:** 2026-06-02  
**Status:** Accepted — APEX Squad review pending

---

## 1. Purpose

`betting.py` turns the scored, ranked race output from Kaylee's `score_race()` into
actionable bet recommendations. It answers three questions:

1. **Should I bet?** — WIN, EW, or PASS for each race
2. **How much?** — fractional Kelly stake sizing scaled to bankroll
3. **How do I combine?** — doubles, trebles, accumulators, Lucky 15

The module is a pure transformation layer: it does not fetch data, call external
services, or mutate scoring output. All inputs and outputs are plain Python dicts.

---

## 2. Scope

| In scope | Out of scope |
|---|---|
| Single bet type selection (WIN/EW/PASS) | Live prices / streaming feeds |
| Fractional Kelly stake sizing | Post-race settlement / P&L tracking |
| Multi-leg construction (doubles/trebles/accas) | Each-Way place terms negotiation |
| Lucky 15 builder | Tax / levy calculations |
| Bankroll-scaled GBP conversion | Exchange (lay) betting |
| Correlation guard (same-race dedup) | Rating system updates |

---

## 3. Integration Contract

### 3.1 Upstream — scoring.py (Kaylee)

`build_bets()` consumes a list of `score_race()` output dicts directly, with **one
required enrichment**: each `ranked_runner` entry must carry an `odds` or
`morning_price` key added by the integration layer before the call.

```python
# Integration layer (Wash's pipeline)
from scoring import score_race, load_default_config
from betting import build_bets, default_config

scored = score_race(racecard, load_default_config())

# Enrich rank-1 runner with current odds (source: Wash's odds feed)
scored["ranked_runners"][0]["odds"] = "3/1"

result = build_bets([scored], bankroll=100.0, config=default_config())
```

**Rationale:** `score_race()` does not preserve price data (Kaylee's §5.3 — her
module is model-only). Odds exist only in `notes` text in the current racecard
JSONs; Wash's integration layer is the correct place to extract and normalise them.
This is documented as **PROPOSED-CONTRACT-001** pending Wash's review.

### 3.2 Downstream — callers

```python
result = build_bets(scores: list[dict], bankroll: float, config: dict) -> dict
```

The returned dict has the following top-level keys:

| Key | Type | Description |
|---|---|---|
| `bankroll` | float | Bankroll passed in (£) |
| `singles` | list[dict] | One entry per race (WIN/EW/PASS) |
| `doubles` | list[dict] | All valid doubles from WIN singles |
| `trebles` | list[dict] | All valid trebles from WIN singles |
| `accumulators` | list[dict] | 4–6 leg accas (gated by count) |
| `lucky_15` | dict \| None | Lucky 15 (first 4 WIN singles; or None) |
| `portfolio_summary` | dict | Totals and counts |
| `disclaimer` | str | "For entertainment only. 18+. …" |

### 3.3 Required runner fields

`build_bets()` reads from each `ranked_runner`:

| Field | Required | Notes |
|---|---|---|
| `rank` | Yes | Used to identify rank-1 selection |
| `horse` | Yes | Used in all output and rationale strings |
| `score` | Yes | Used for model probability calculation |
| `odds` | Recommended | Decimal or fractional string; if absent → PASS |
| `morning_price` | Fallback | Checked if `odds` is absent |

Missing `odds`/`morning_price` results in `bet_type = "PASS"` with rationale
`"No odds available"`. No prices are fabricated.

---

## 4. Bet Type Decision Tree

```
For rank-1 runner in each race:

1. Parse odds → decimal price
   ├── No parseable odds → PASS ("No odds available")
   └── Decimal odds available:

2. Compute model_prob = score_top / Σ(all runner scores in race)
   Compute implied_prob = 1 / decimal_odds
   Compute win_edge_pct = (model_prob − implied_prob) / implied_prob × 100

3. If confidence == "HIGH" AND win_edge_pct ≥ win_threshold_pct (default 15%):
   └── BET TYPE = WIN  ← high-quality, clear favourite, priced up

4. Else if confidence in ("HIGH", "MED")
        AND (win_edge_pct + place_edge_pct) ≥ ew_combined_threshold_pct (default 20%):
   └── BET TYPE = EW   ← each-way value even if win price is short

5. Else:
   └── BET TYPE = PASS  (rationale includes computed edges for transparency)
```

### 4.1 Place probability estimate (EW)

```
places_paid = 3  if field_size > 7 else 2
place_prob  = min(0.95, model_win_prob × places_paid)
place_dec   = (win_decimal − 1) × place_fraction + 1
             where place_fraction = 0.20  (standard UK 1/5 odds)
place_edge_pct = (place_prob − 1/place_dec) / (1/place_dec) × 100
```

---

## 5. Stake Sizing — Fractional Kelly

### 5.1 Formula

```
b  = decimal_odds − 1         # net odds (profit per unit staked)
p  = model_prob
q  = 1 − p

full_kelly_fraction = (b × p − q) / b

fractional_kelly = full_kelly_fraction × kelly_fraction  (default 0.25)

stake_pts = clip(fractional_kelly × 100,
                 min_stake_pts,    # default 0.25 points
                 max_stake_pct)    # default 5.0 points
```

### 5.2 Unit definition

```
1 point = 1% of bankroll
stake_gbp = stake_pts × bankroll / 100
```

### 5.3 EW staking

EW is placed as two equal-unit bets (win + place). If `single_unit_pts` is the
fractional-Kelly output, the reported `stake_pts` = `2 × single_unit_pts` and
`stake_gbp` covers both legs.

### 5.4 Justification for quarter-Kelly

Full Kelly maximises the log of bankroll growth rate but produces extreme drawdowns
(40–60% bankroll risk) that are psychologically unsustainable. Quarter-Kelly reduces
stake by 75%, approximately halving the maximum drawdown relative to full Kelly while
retaining ~75% of the long-run growth rate improvement. This is a widely used
compromise in professional sports-betting contexts.

---

## 6. Multi-Leg Construction

Only **HIGH-confidence WIN singles** (not EW, not PASS) qualify as legs.

### 6.1 Qualification gates

| Product | Min qualifying WIN singles | Notes |
|---|---|---|
| Doubles | ≥ 2 | All valid pairings |
| Trebles | ≥ 3 | All valid triplets |
| Accumulators (4–6 legs) | ≥ 4 | `max(min_high_confidence_for_acca, 4)` |
| Lucky 15 | ≥ 4 | First 4 qualifying legs only |

### 6.2 Correlation guard

Before building multis, legs are deduplicated by `race_id`. Two selections from the
same race are never placed in the same multi. If two score entries share a `race_id`
(e.g., two different model runs for the same race), only the first qualifying single
is used as a multi-leg.

**Rationale:** Selections from the same race are perfectly negatively correlated —
at most one can win. Combining them in an accumulator would require both to win,
which is impossible. The guard prevents this logical error.

### 6.3 Lucky 15 structure

| Sub-bet | Count | Formula |
|---|---|---|
| Singles | 4 | Each of the 4 selections × unit_stake |
| Doubles | 6 | C(4,2) |
| Trebles | 4 | C(4,3) |
| Four-fold accumulator | 1 | All 4 |
| **Total bets** | **15** | |

Default unit stake: 0.10 points per bet = 1.50 points total (£1.50 at £100 bankroll).

### 6.4 Accumulator staking

All multi-leg bets use a **fixed unit stake** (configurable) rather than Kelly.
Applying Kelly to accumulators requires accurate joint probabilities under
independence assumptions that rarely hold in practice. Fixed-unit accas are
treated as speculative entertainment bets.

---

## 7. Configuration Reference

All parameters are exposed through `default_config()` and can be overridden
per-call without modifying source code.

```python
{
    "edge": {
        "win_threshold_pct": 15.0,        # Min edge % to trigger WIN
        "ew_combined_threshold_pct": 20.0, # Min combined edge % to trigger EW
    },
    "kelly": {
        "fraction": 0.25,                 # Quarter-Kelly
        "max_stake_pct_per_single": 5.0,  # Hard cap: 5% bankroll
        "min_stake_pts": 0.25,            # Minimum bet: ¼ point
    },
    "ew": {
        "place_fraction": 0.20,           # 1/5 place odds (standard UK)
        "large_field_threshold": 7,       # >7 runners → 3 places
        "places_paid_large": 3,
        "places_paid_small": 2,
    },
    "multis": {
        "min_high_confidence_for_acca": 3, # Quality gate
        "max_acca_legs": 6,
        "double_unit_pts": 0.50,
        "treble_unit_pts": 0.50,
        "acca_unit_pts": 0.50,
    },
    "lucky15": {
        "unit_pts": 0.10,                 # Per-bet unit (×15 = 1.5 pts total)
        "min_legs": 4,
    },
}
```

---

## 8. Worked Example

**Race:** Epsom Handicap (8 runners)  
**Bankroll:** £100  
**Confidence:** HIGH

| Runner | Score | Decimal odds |
|---|---|---|
| **Storming Home** | **80** | **4.0 (3/1)** |
| Second Fiddle | 60 | — |
| Trailing Cloud | 50 | — |
| Distant Hope | 40 | — |
| No Chance | 30 | — |

```
Σ scores = 260
model_prob = 80/260 = 0.3077
implied_prob = 1/4.0 = 0.25
win_edge = (0.3077 − 0.25)/0.25 × 100 = 23.1%   ← ≥ 15% threshold

full_kelly = (3.0 × 0.3077 − 0.6923) / 3.0 = 0.0769
quarter_kelly = 0.0769 × 0.25 = 0.01923
stake_pts = 0.01923 × 100 = 1.92 pts
stake_gbp = 1.92 × £100 / 100 = £1.92

Recommended bet: WIN £1.92 on Storming Home @ 3/1
Expected return: £1.92 × 0.3077 × 4.0 = £2.36
```

---

## 9. Proposed Module Contract — PROPOSED-CONTRACT-001

> **Status:** Proposed — awaiting Wash's review  
> **Context:** `module-contracts.md` does not yet exist; this is a draft entry.

**Contract name:** `scoring-to-betting-odds-enrichment`  
**Parties:** Kaylee (scoring.py) · Badger (betting.py) · Wash (integration/pipeline)

**Agreement:**
- Kaylee's `score_race()` output is consumed as-is; `betting.py` must not modify it.
- The `ranked_runners` list in `score_race()` output **does not** include odds.
- **Wash** is responsible for adding an `"odds"` (or `"morning_price"`) key to at
  minimum `ranked_runners[0]` before passing to `build_bets()`.
- `betting.py` gracefully handles missing odds by returning `bet_type = "PASS"`.
- Accepted odds formats: fractional strings `"3/1"`, decimal strings `"4.0"`,
  numeric values `4.0`, `"evs"`, `"evens"`. Unrecognised values → PASS.

---

## 10. Known Limitations (v0.1)

| Limitation | Future work |
|---|---|
| Only rank-1 runner is evaluated per race | Support multi-runner EW (e.g. 2nd-fav overlay) |
| EW place terms use flat 1/5 model | Adapt for courses/races that pay 1/4 or 1/3 |
| No track-condition sensitivity in edge calc | Integrate draw/going multipliers (Kaylee §4) |
| Independence assumption in multis | Correlation model (same trainer, going, etc.) |
| No rule-4 deductions | Post-scratching price adjustments |
| `morning_price` only; no in-play prices | Streaming price integration (Wash's scope) |

---

*DISCLAIMER: For entertainment only. 18+. Gamble responsibly. BeGambleAware.org.*
