# Skill: bet-pass-rationale

**Owner:** Linus (Reports)
**First used:** 2026-06-05 Ladies Day
**Status:** Active - use on every race day

## Purpose

Every race where the model outputs PASS needs a plain-English explanation on the card so Steve understands why we did not bet. The same rule applies to picks: add one line explaining which signal and threshold combination fired.

## When to apply

Use this when publishing or editing race-day HTML artifacts for a configured `{course}`, `{meeting}`, and `{date}`.

Typical paths:

- Epsom legacy report: `outputs\report-{date}.html`
- Non-Epsom report: `outputs\report-{course}-{date}.html`
- Epsom legacy racecard: `outputs\racecard-{date}.html`
- Non-Epsom racecard: `outputs\racecard-{course}-{date}.html`

Every race block must have either a `.pick-rationale` or `.pass-rationale` paragraph. The printable racecard must carry the same rationale in its table-row format.

## Step-by-step

### 1. Identify each race outcome

Read the rendered race header chips and the bet-list amounts. If the header and bet-list contradict, trust the bets JSON and the bet-list, because they reflect actual stake output.

### 2. Read the gate hit

Open `src\betting.py` and inspect `_build_single`.

| Gate | Trigger | Outcome |
|---|---|---|
| 1 | No parseable odds | PASS |
| 2 | confidence HIGH plus win_edge >= 15 percent | WIN |
| 3 | confidence HIGH/MED plus combined EW edge >= 20 percent | EW |
| 4 | fallthrough | PASS |

Also read the `bet["rationale"]` string from `build_bets()` output when available.

### 3. Write the rationale text

Pick template:

```text
Why we are on: Confidence [HIGH/MED], score [X]. [Top two signals]. [Threshold cleared]. Stake GBP [X] at [odds].
```

Pass template:

```text
Why we are passing: Confidence [level] - [required gate vs actual]. [Field context: N runners, short price, unscored runner, stale odds, etc.].
```

Keep it to one or two short sentences.

### 4. Inject into the long report

Insert after the description inside `.top-pick`, before the closing `</div>`:

```html
<p class="pick-rationale">Why we are on: ...</p>
```

Insert after `</ul>` inside `.race-bets`, before the closing `</div>`:

```html
<p class="pass-rationale">Why we are passing: ...</p>
```

### 5. Inject into the printable racecard

The 1-pager uses a `<table class="slip">` layout. Pass rationale goes in a `row-rationale` row immediately after the PASS row for that race.

```html
<tr class="row-rationale row-rationale-pass">
  <td colspan="8"><div class="bet-rationale">Why we are passing: ...</div></td>
</tr>
```

## Preserve existing footnotes

If the card was hand-touched before you edit it, check for race-day footnote blocks and do not overwrite them. Use surgical replacements; do not regenerate the full report just to add rationale.

## Examples

WIN:

```text
Why we are on: Confidence HIGH, score 95.0. Strong jockey and trainer signals in a 23-runner field. Model edge over 9/2 clears the 15 percent WIN threshold. Stake GBP 0.34.
```

PASS, low confidence:

```text
Why we are passing: Confidence LOW - WIN requires HIGH and EW requires HIGH or MED. Signal agreement is weak across 18 runners, so the model cannot separate the field with conviction.
```

PASS, no edge:

```text
Why we are passing: Confidence LOW. The top pick is a short-priced favourite and does not clear the 15 percent WIN edge threshold.
```

## Dual-artifact rule

Whenever pass rationale or pick rationale is applied to the long report, apply the same content to the printable racecard immediately after. They are independent HTML files at race-day edit time.

## Future automation

`src\report.py` already receives rationale strings from `build_bets()`. Once the template exposes them everywhere, this manual injection skill can retire.
