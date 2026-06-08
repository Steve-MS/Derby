# Skill: bet-pass-rationale

**Owner:** Linus (Reports)
**First used:** 2026-06-05 Ladies Day
**Status:** Active — use on every race day

---

## Purpose

Every race where the model outputs PASS needs a plain-English explanation on the card
so Steve understands *why* we didn't bet — not just that we didn't.
Same applies to picks: one line explaining which signal + threshold combination fired.

---

## When to apply

Any time you are publishing or editing a race-day HTML report (outputs/report-YYYY-MM-DD.html).
Every race block must have either a .pick-rationale or .pass-rationale paragraph.

---

## Step-by-step

### 1. Identify each race's outcome

From the race header chips (ec-WIN, ec-EW, ec-PASS) and the bet-list amounts.
If header and bet-list contradict, trust the bet-list (it reflects actual stake output).

### 2. Read the gate hit

Open src/betting.py, function _build_single. The gates in order:

| Gate | Trigger | Outcome |
|------|---------|---------|
| 1 | No parseable odds | PASS |
| 2 | confidence HIGH + win_edge ≥ 15% | WIN |
| 3 | confidence HIGH/MED + combined EW edge ≥ 20% | EW |
| 4 | fallthrough | PASS |

Also read the et["rationale"] string from uild_bets() output — it contains the exact numbers.

### 3. Write the rationale text

**Pick template:**
> ✅ Why we're on: Confidence [HIGH/MED], score [X]. [Top 2 signals from top-pick text]. [Which threshold cleared]. Stake £[X] @ [odds].

**Pass template:**
> ⛔ Why we're passing: Confidence [level] — [which gate was required vs what we have]. [Field context: N runners, short price, unscored runner, etc.].

Keep it to 1–2 sentences. No jargon. Steve reads on a train.

### 4. Inject into the HTML (surgical)

**Pick rationale:** After the <p> description inside .top-pick, before </div>.
`html
<p class="pick-rationale">✅ Why we're on: ...</p>
`

**Pass rationale:** After </ul> inside .race-bets, before </div>.
`html
<p class="pass-rationale">⛔ Why we're passing: ...</p>
`

### 5. Ensure CSS is present

Add to the report stylesheet (once per report, after .outsider-rationale):

`css
.pick-rationale {
  font-size: .79rem;
  color: var(--green-light);
  font-style: italic;
  margin-top: 6px;
  padding-top: 5px;
  border-top: 1px solid var(--border);
}
.pass-rationale {
  font-size: .79rem;
  color: var(--muted);
  font-style: italic;
  margin-top: 6px;
  padding: 5px 0 0;
}
`

---

## Preserve existing footnotes

If the card was hand-touched before you edit it (race-day injections by Linus),
check for <!-- ⚠️ RACE-DAY FOOTNOTES --> blocks and DO NOT overwrite them.
Use surgical dit replacements; do not regenerate the full report.

---

## Example output

**Pick (WIN):**
> ✅ Why we're on: Confidence HIGH, score 95.0. Model edge over 9/2 implied probability clears the 15% WIN threshold. Quarter-Kelly stake £0.34. Strong Jockey and Trainer signals in a 23-runner field — top score stands clear.

**Pass (LOW confidence):**
> ⛔ Why we're passing: Confidence LOW — WIN gate requires HIGH, EW gate requires HIGH or MED. Signal agreement is weak across 18 runners. High score for the top pick, but the model can't separate the field with conviction.

**Pass (favourite, no edge):**
> ⛔ Why we're passing: Confidence LOW. Top pick goes off at 9/4 — short-priced favourite with no model edge above the 15% WIN minimum at that price.

---

## Future automation

src/report.py already has the et["rationale"] string from uild_bets().
When the jinja template is updated to expose it, these <p> blocks can be
generated automatically and this surgical injection step disappears.


---

## 1-pager variant (table-based layout)

The 1-pager (`outputs/racecard-YYYY-MM-DD.html`) is a `<table class="slip">` layout,
not the card-div layout of the long report. Pass rationale goes in a `row-rationale` row:

```html
<tr class="row-rationale row-rationale-pass">
  <td colspan="8"><div class="bet-rationale">⛔ [rationale text]</div></td>
</tr>
```

**Where to inject:** Immediately after the closing `</tr>` of the PASS row for that race.

**CSS:** Already covered by `.row-rationale td` in the 1-pager stylesheet. No new classes needed.

**Content:** Same rationale text as the long report — stripped to a single compact sentence.
Keep ⛔ prefix. Max ~120 characters to stay on one line at 8pt print.

**Dual-artifact rule:** Whenever pass-rationale (or footnotes) are applied to the long report,
apply the same content to the 1-pager immediately after. Both are independent HTML files —
they do not share a template at race-day injection time.
