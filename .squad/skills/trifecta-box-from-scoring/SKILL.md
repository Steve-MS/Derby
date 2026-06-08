# Skill: trifecta-box-from-scoring

## Purpose

Build a manual trifecta-box recommendation for a specific Group 1 or significant Group 2 race from the scored runner ranking. The box covers every ordered 1-2-3 finish permutation among N selected horses.

Cost formula:

```text
N * (N - 1) * (N - 2) * stake_per_combo
```

| Box size | Combinations | Cost at GBP 1 per combo |
|---:|---:|---:|
| 3 | 6 | GBP 6 |
| 4 | 24 | GBP 24 |
| 5 | 60 | GBP 60 |

## When to use

- Steve requests a trifecta box for a named race.
- The race is Group 1 or a significant Group 2.
- The field is deep or competitive, usually 10 or more runners.
- Standard win/EW confidence is low or medium but the model ranking still gives a useful cluster.

## Inputs

Use canonical course-aware paths.

| Input | Epsom legacy example | Non-Epsom example |
|---|---|---|
| Scores | `outputs\scores-2026-06-06.json` | `outputs\scores-ascot-2026-06-16.json` |
| Raw racecards | `data\raw\epsom-2026-06-06-racecards.json` | `data\raw\ascot-2026-06-16-racecards.json` |
| Latest market | `data\enrichment\market-latest.json` | `data\enrichment\market-latest-ascot.json` |
| Bets | `outputs\bets-2026-06-06.json` | `outputs\bets-ascot-2026-06-16.json` |

Set context first:

```powershell
$course = "{course}"
$meeting = "{meeting}"
$date = "{date}"
$race = "{race name or off time}"
```

## Procedure

### 1. Identify the target race

Find the race by name and off time, not by race number. Race numbering can change when data sources omit or add races. Confirm race name, off time, class/group status, distance, field size, and current going.

### 2. Extract scored rankings

From the scores file, collect `race_name`, `race_time`, `confidence`, `race_stdev`, `race_competitiveness`, and for each runner: rank, horse, trainer, jockey, score, key signals, and morning price.

### 3. Choose box size

Calculate score gaps between adjacent ranks.

```text
gap(N -> N+1) = score[N] - score[N+1]
```

Decision tree:

- 3-horse box: top-3 cluster is clear, gap from rank 3 to 4 is greater than one race stdev, and confidence is high or medium.
- 4-horse box: default for most Group 1 races; use when confidence is low or the rank 3 to 4 gap is inside one stdev.
- 5-horse box: use only for very high stdev, competitive field, and no visible top cluster. Label as wide net, low conviction.

### 4. Select horses

Start with the top N ranked runners. Then check whether rank N+1 has a strong reason to replace a selected horse: severe going cliff, known non-runner risk, unscored late entry, short turnaround concern, or stale odds making market context unreliable. If you swap, state the reason explicitly.

### 5. Size the stake

Target total outlay: GBP 15 to GBP 35 for a Group 1/Group 2 box, unless Steve specifies otherwise.

- 3-box: GBP 2.50 per combo = GBP 15 total
- 4-box: GBP 1.00 per combo = GBP 24 total
- 5-box: GBP 0.50 per combo = GBP 30 total

Check the bets file before recommending the box. The box is additive, so include it in total day exposure.

### 6. Write the rationale

For each horse, write one short line using the strongest two or three signals: trial or prep form, market move, going fit, sire stamina, recent form, pace setup, or trainer/jockey combination. If one horse is an outsider relative to model rank, state the model-rank versus market-rank discrepancy.

### 7. Add stale-odds and going notes

Always include a stale-odds caveat if the market source predates race day or was synthetic.

```text
These odds are from [source date/source type]. Starting price can shift materially. The box is form-driven; dividend cannot be projected from stale odds.
```

If going could change before post time, list which box horses improve or weaken on the alternate going.

## Output format

```markdown
## [Race Name] Trifecta Box - [HH:MM] [Date]

Scope: {course} / {meeting} / {date}
Box: [N horses]
Combinations: [N * (N - 1) * (N - 2)]
Stake per combo: GBP [X]
Total outlay: GBP [Y]
Conviction: [High / Medium / Low] - [one-line reason]

### Horses in the box
| Rank | Horse | Jockey | Trainer | Odds source | Why included |
|---:|---|---|---|---|---|
| 1 | ... | ... | ... | ... | ... |

### Notes
- Outsider/model-rank note: ...
- Going contingency: ...
- Stale-odds caveat: ...
```

## Worked historical example: Derby 2026

- Course/meeting/date: `epsom` / `derby-2026` / `2026-06-06`.
- Race: Betfred Derby, Group 1, 16:00 BST, 12f.
- Decision: 4-horse box because confidence was LOW and the rank 3 to 4 gap was inside one stdev.
- Stake: GBP 1 per combo, GBP 24 total.
- Lesson: the Derby was a good first use because model uncertainty was high, but the top-scored cluster was still informative. Treat it as a historical example, not the default course.

## Limitations

- There is no automated `trifecta_box()` staking helper in the betting pipeline.
- Box selection is form-driven, not payout-optimized.
- Dividend cannot be projected without live SP and pool data.
- Do not add a trifecta box to generated artifacts unless the operator explicitly asks for it.
