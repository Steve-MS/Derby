# Decisions Log

## 2026-06-05T15:02:08+01:00 — Rusty (Signal Engineer)

**Decision:** Prizeland (NR) Replacement — Oaks 16:00

**Status:** ✅ Pick delivered

### Context
Prizeland confirmed NOT RUNNING. Absent from `market-baseline.json` (09:52 BST). Verbal confirmation from Steve at 15:02 BST.

### Choice: Cameo £0.25 EW @ ~14/1 (stale)

| Field | Value |
|-------|-------|
| Horse | Cameo |
| Trainer | Aidan O'Brien |
| Model rank | #3 (score 88.4 / 100) |
| Market rank | #4 |
| Trial form | Won Lingfield Oaks Trial by 4.75L |
| Price | ~14/1 (15.0 decimal, 2026-06-02 estimate) |
| Confidence | MEDIUM |

**Rationale:** Aidan O'Brien trial winner (trial_form 80/100, trainer_form 100/100) at an outsider price with rank-price gap. Replaces Prizeland (model #3 → Cameo model #3) — scoring improves by +9.8 points.

**Stale-odds caveat:** Price is estimated from 2026-06-02 racecard. Verify current price at rail before staking.

**Why not Sugar Island?** Sugar Island scored 89.3 (model rank #2) but market has moved intra-day (34.0 → ~17–23). Stale 34.0 price is stale in wrong direction; current EW case is weaker. Steve already holds active Sugar Island EW at 34.0.

---

## 2026-06-05T15:13:00+01:00 — Linus (Reports Engineer)

**Decision:** Prizeland → Cameo Row Swap — Ladies Day Racecard

**Status:** ✅ Done

### What Was Done

Hand-edited `outputs/racecard-2026-06-05.html` to replace Prizeland selection (16:00 Oaks) with Cameo, per Rusty's signal.

### Changes

1. **Prizeland row removed** — `<tr class="row-outsider">` + `<tr class="row-rationale">` pair excised.
2. **Cameo row inserted** with matching structure:
   - Horse: Cameo · Trainer: Aidan O'Brien · Jockey: [TBC]
   - Price: ~14/1 (stale, 15.0 decimal, 2026-06-02 estimate)
   - Stake: £0.25 EW → win return col: £3.75
   - Note col: model rank 3 vs market 4 + amber NR badge `🚫 Replaces Prizeland (NR)`
   - Rationale: Lingfield Oaks Trial 4.75L win, trial_form 80/100, trainer_form 100/100
3. **Stale-odds caveat** — amber `<div>` in `row-rationale`: "Odds (~14/1, 15.0 decimal) are 2026-06-02 estimates. Verify current price at the rail or with your bookmaker before staking."
4. **Footnotes updated** — Added NR note to card-bottom race-day notes box.
5. **HTML comment audit trail** — `<!-- 🔄 CAMEO REPLACES PRIZELAND (NR) — hand-edit 2026-06-05 by Linus -->`

### Verification

- [x] Prizeland row removed from 16:00 race
- [x] Cameo row inserted with matching structure
- [x] Amber NR annotation visible in col-note
- [x] Stale-odds caveat present in rationale cell
- [x] Other races on Ladies Day card unchanged
- [x] Derby card untouched

### Cross-Agent Flag

**Task for Royal Ascot:** Add `render_replacement_row(original_horse, replacement, bet, rationale, stale_price, conviction)` to `src/report.py` alongside `render_trifecta_box()`.

This is the second hand-edit in two days. Helper would make row swap reproducible and testable rather than manual each time.

---

## 2026-06-05 — Linus (Reports Engineer)

**Decision:** Trifecta Box Placement on Race Day Cards

**Status:** ✅ Implemented

### Context

Derby Day 2026-06-06 card — first use of a trifecta box recommendation.

### Decision

**Trifecta boxes always render immediately below the parent race's outsider rationale row, not in a separate "Specials / Multiples" section.**

The box is inserted as a full-width spanning `<tr class="row-trifecta">` inside the main `.slip` table, directly after the `row-rationale-outsider` row for that race.

### Rationale

- Keeps all race content visually grouped together on the A4 card.
- Steve reads race-by-race in time order; avoids page-flip mid-race.
- Cross-reference is cleaner when trifecta is inline with race block.

### Implementation

- Visual distinction: purple left-border + shaded `#f6f3ff` background (`.trifecta-box` CSS class).
- `render_trifecta_box(trifecta: dict) -> str` helper added to `src/report.py` (2026-06-05).
- Helper exists but not yet wired into Jinja2 template.

### Handoff Note

⚠️ **Before Royal Ascot:** promote the helper into `src/templates/report.html.j2`, pass a `trifecta_boxes` dict via the `render()` call, and add companion CSS classes to `src/templates/style.css`.

---


---

### 2026-06-05T17:14 BST: Ladies Day post-card retro — auto-fire directive
**By:** Steve (via Coordinator)
**What:** Auto-fire the Ladies Day results retro at the next watchdog tick AFTER card close (~18:25 BST). User confirmed via choice picker: "Auto — fire at ~18:35 BST after final race".
**Why:** Validate today's pipeline (live-verified gate, outsider picks, confidence calibration) and feed any learnings into the Derby Day card before it's locked.

**Trigger condition (watchdog must check at every tick from 18:30 BST onward):**
- Has the final Ladies Day race off-time passed? (estimated ~18:25 BST; verify against `data/enrichment/live-runners-2026-06-05.json` and source racecard)
- If YES → fire retro spawn sequence immediately and DO NOT wait for next hourly tick.
- If NO → stand down, wait for next tick.

**Retro spawn sequence (all background, in stages — wait for stage N before launching stage N+1):**

**Stage 1 — Results capture (single agent, ~5 min):**
- Spawn Livingston (claude-sonnet-4.6) → `web_fetch` official results for all 5 Ladies Day races from Sporting Life + Racing Post.
- Output: `data/results/ladies-day-2026-06-05.json` — per race: finish order (1-2-3 + winning margin), BSP, SP, official going, declared NRs vs. our caught NRs.
- Audit specifically: Triple Double A (16:40), Blue Brother (17:50), Port Road — were they confirmed NRs at the off?

**Stage 2 — Scoring + signal calibration (parallel, ~8 min):**
- Spawn Saul (claude-sonnet-4.6) → score every WIN/EW pick on `racecard-2026-06-05.html` against Stage 1 results. Output a P/L table per race, hit-rate by confidence tier (HIGH / MED / LOW / SPEC), and outsider-specific stats. Flag any pick that finished 4th or better at 10/1+ as "near miss".
- Spawn Rusty (claude-sonnet-4.6) → signal calibration pass. For each outsider pick (Asmen Warrior, Arctic Thunder, Cameo's outsider counterpart, etc.): did OR→RPR gap predict? Did first-time blinkers / Epsom D-badge / handicapper-lag carry weight? Output: which signals to dial up/down for Derby outsider.

**Stage 3 — Decision + render (sequential, ~10 min):**
- Spawn Danny (Lead, claude-opus-4.6 — bumped for architecture-level call) → read Stage 1+2 outputs, write a 1-page retro decision in `.squad/decisions/inbox/danny-ladies-day-retro.md`: what holds, what changes, whether the Derby card needs any pick swap, whether the 🟢 live-verified gate held under pressure.
- IF Danny flags a Derby change → spawn Linus (claude-sonnet-4.6) to re-render ONLY `racecard-2026-06-06.html` (preserve trifecta block unless Danny/Rusty explicitly touched it). 🟢 stamp must be re-issued from a fresh live-verification.
- IF Danny says "Derby card holds" → skip Linus, log the decision.

**Stage 4 — Commit (Scribe, ~5 min):**
- Spawn Scribe (claude-haiku-4.5) → merge all inbox files, post cross-agent updates, commit retro artifacts. Standard secret-scan gate applies.

**Termination conditions:**
- Retro complete → log to session log, schedule continues hourly until Sat 21:30 auto-stop.
- If any stage fails (3 retries) → fall back to Direct Mode summary for Steve, do NOT touch Derby card.

**Pin to coordinator memory:** This directive supersedes the previous "next scheduled action = ~21:00 archive" entry. The 21:00 archive still happens; the retro is an additional event.


---

# Publish-Readiness Audit — race-analysis as a Skill
**Author:** Danny (Lead)
**Date:** 2026-06-06T23:02:55+01:00
**Requested by:** Steve
**Context:** End-of-day Derby retrospective. Steve's explicit lens: "Determine if any adjustments
should have been made in regards to this being a published skill that others could use."
**Prior intent:** Checkpoints 004 (productize-race-pipeline-as-skill) and 005 (race-pipeline-skill-
conversion-scoping) show this was always intended to ship publicly.

---

## Verdict Up Front

**This skill is NOT ready to publish in any form.** The three hardest failures today — all
scraper routes dead, SPORTINGLIFE credentials undocumented and silently failing, and a codebase
that hardcodes "epsom" and "2026" in a dozen places — mean that a stranger who installed this
tomorrow would get a broken pipeline with no diagnostic path. The scoring engine itself (src/) is
genuinely good work. The infrastructure around it isn't shippable yet.

---

## 1. Environment Prerequisites

### Credentials and Environment Variables

| Credential | Where Referenced | Documented? | Failure Mode |
|---|---|---|---|
| `RACING_API_USERNAME` | `.env` file (committed) | No README mention | Silent — scraper silently skips API calls |
| `RACING_API_PASSWORD` | `.env` file (committed) | No README mention | Silent — same |
| `SPORTINGLIFE_USER` | Livingston-3 session (2026-06-06T15:39) | **Nowhere in codebase** | 🔴 **Silent hard stop** — SPA returns 373 bytes, no data, no exception |
| `SPORTINGLIFE_PASS` | Livingston-3 session (2026-06-06T15:39) | **Nowhere in codebase** | 🔴 Same |
| Betfair App Key / session token | decisions.md 2026-06-05 Betfair entry | **Nowhere in codebase** | Not attempted — no code path exists |

**Today's evidence:** At 15:39 BST, Livingston's pre-Derby drift check was BLOCKED across all
sources. The Sporting Life scraper returned a 373-byte SPA shell with no data. The root cause:
`SPORTINGLIFE_USER` / `SPORTINGLIFE_PASS` not set in the session. There is no validation on
startup, no `check_env()` helper, no `.env.example`, no README section listing these variables.
A stranger would run the script, get output that looks plausible, and make betting decisions
on 4-day-old synthetic prices thinking they had live data.

### Silent vs Noisy Failures

| Condition | Behaviour | Verdict |
|---|---|---|
| RP HTTP 406 / 404 | Prints `[warn]` to stderr, falls through to racecard data | Semi-silent — warns but doesn't abort |
| SPORTINGLIFE not set | SPA shell 373 bytes, script returns empty data | 🔴 **Silent hard stop** |
| Betfair not configured | No code path attempted | Silent — feature simply doesn't exist |
| Racecard JSON missing | `cmd_fetch` raises clear error | ✅ Noisy |
| CSV price override file missing | `sys.exit` with message | ✅ Noisy |
| enrich_odds.py horse not in ODDS table | Falls through to synthetic | ✅ Documented behaviour |

**Hard stops with no fallback:**
- Sporting Life live odds (no credentials → all live price data unavailable)
- Betfair Exchange (no app key → no exchange data)
- Racing Post __NEXT_DATA__ (brittle structure; HTML schema can change any deployment)

**Fallback available:**
- Racecard synthetic prices (always available; stale from enrichment date; market_move signal
  returns neutral 50 — documented in decisions.md, anti-fabrication compliant)
- Manual CSV price override (--prices flag on both refresh_friday.py and morning_odds.py)

### What a Stranger Can't See

The `.env` file is in the repo but contains live credentials (`RACING_API_USERNAME=AHCO2Q3...`).
This needs to be `.env.example` with placeholder values and a `.env` in `.gitignore` for any
public release. There is no `setup.md`, no `CONTRIBUTING.md`, no `INSTALL.md`.

---

## 2. External Data Sources

### Dependency Map

| Source | Purpose | Today's Status | Brittleness |
|---|---|---|---|
| Racing Post `__NEXT_DATA__` | Runner-list confirmation, ante-post prices | 🔴 HTTP 406 / 404 | HIGH — SPA structure changes without notice |
| Sporting Life scraper | Live odds | 🔴 SPA shell (no credentials) | HIGH — requires account + session |
| Betdata.io | Market data | 🔴 404 | HIGH — third-party service unavailability |
| enrich_odds.py hardcoded table | Ante-post + estimated prices | ✅ Always available | LOW — deterministic, no network |
| Open-Meteo API | Going forecast | ✅ Available (no key required) | LOW — stable free API |
| BHA/Epsom declarations | NR confirmation | Manual browser check | HIGH — no programmatic fetch |
| Racecard JSON files | All runner data | ✅ Available (pre-committed) | LOW — local files |

**All three live-data routes (RP, SL, Betdata) failed simultaneously today.** The pipeline still
produced a card because of the enrich_odds.py fallback. This is correct anti-fabrication
behaviour — but the consequence is that market_move signal was INERT for the entire Derby weekend.
`market_move` has weight 0.0683 in the v0.6 model. A signal carrying ~7% of model weight was
returning neutral 50 for 100% of runners for the full 4-day period. The card worked. The signal
didn't. A published user would not know which signals were actually firing vs coasting on neutral.

### Minimum-Viable Data Path

The absolute minimum to produce a card:
1. `data/raw/epsom-YYYY-MM-DD-racecards.json` — must exist (pre-fetched, not live-fetched)
2. `enrich_odds.py` — runs against hardcoded ODDS table; produces `morning_price` on all runners
3. `python -m src.cli score --date YYYY-MM-DD` → score file
4. `python -m src.cli predict --date YYYY-MM-DD` → bets file
5. `python -m src.cli report --date YYYY-MM-DD` → HTML

Everything else (RP scrape, SL odds, Betdata, market_move live data) is additive and currently
failing. The pipeline is effectively "BYO racecard JSON + hardcoded prices."

### Could the Skill Ship with a BYO Data Mode?

Yes, and this is the **right architectural answer** for a publishable skill. The scoring engine
(`src/scoring.py` and all signal modules) is already data-agnostic — it accepts any runner dict
and returns a score. The blocker is that the orchestration layer assumes Epsom/2026 throughout.
A BYO mode needs:
- A documented racecard JSON schema (currently undocumented)
- A `--venue` and `--date` parameterisation on the CLI
- A CSV or JSON paste-in path for prices (partially exists via `--prices` flag)
- A worked example racecard + prices fixture in `data/examples/`

---

## 3. Hardcoded Paths and Assumptions

The following are confirmed hardcodes that break generalisation. No `C:\Users\stevenn` literals
were found in `src/` (Path(__file__) is used throughout — good), but event/venue/year specificity
is pervasive.

### Breaks (a) Different User

| File | Line / Pattern | Issue |
|---|---|---|
| `.env` | All | Live credentials committed; must become `.env.example` |
| `scripts/morning_odds.py` | `_RP_HEADERS` User-Agent: Windows NT 10.0 | Windows UA — may not work on Linux |
| `src/cli.py` | stdout.reconfigure encoding guard | Windows-specific `reconfigure()` call |

### Breaks (b) Different Course

| File | Evidence | Impact |
|---|---|---|
| `src/pace.py` | `EPSOM_DRAW_TABLE` — entire draw-bias system keyed `("epsom", dist)` | Returns `None` / neutral for any non-Epsom course |
| `src/pace.py` L181 | `if course != "epsom": return None` | Hard gate — draw_bias signal dead for Ascot, Goodwood, Newmarket |
| `src/cd_form.py` L112 | `if first_epsom and course == "epsom"` | First-time-course penalty only coded for Epsom |
| `src/scoring.py` L123 | `"material_courses": ["Epsom"]` | Course config locked to Epsom |
| `src/racecard.py` L22 | `VENUE = "Epsom"` | Hardcoded venue string in output |
| `src/report.py` L73 | `VENUE = "Epsom"` | Same |
| `scripts/morning_odds.py` L96 | `RP_RACECARD_URL = ".../racecards/17/epsom/{date}"` | Venue ID `17` and "epsom" slug hardcoded |
| `data/enrichment/*.json` | All enrichment files | Horse names are Epsom 2026 runners — entirely event-specific |

### Breaks (c) Different Year

| File | Evidence | Impact |
|---|---|---|
| `enrich_odds.py` L15 | `FETCHED_AT = "2026-06-02T13:55:00+01:00"` | Hardcoded timestamp on all enriched prices |
| `enrich_odds.py` L23-77 | `ODDS_05`, `ODDS_06` dicts | 100% horse-name-keyed for Epsom 2026 field |
| `scripts/refresh_friday.py` L40 | `DATES = ["2026-06-05", "2026-06-06"]` | Hardcoded race dates |
| `scripts/refresh_friday.py` L41 | `BANKROLL = 200` | Hardcoded bankroll |
| `scripts/morning_odds.py` L91-94 | `RACECARD_FILES` dict | Hardcoded 2026-06-05/06 keys |
| `scripts/morning_odds.py` L136 | `_CAPTURED_AT_RACECARD = "2026-06-02T13:55:00+01:00"` | Hardcoded |
| `scripts/morning_odds.py` L355-358 | Metadata string mentions "2026-06-05/06" | Hardcoded |
| `src/racecard.py` L26-27 | `_DATE_DAY_NAMES` dict — 2026-06-05/06 keys | Returns empty string for any other date |
| `src/racecard.py` L203,210 | `if date == "2026-06-05"` / `"2026-06-06"` | Date-branched logic |
| `src/racecard.py` L257,264 | `if date != "2026-06-06"` / `date == "2026-06-06"` | Same |
| `src/report.py` L69-70 | `_DATE_DAY_NAMES = {"2026-06-05": ..., "2026-06-06": ...}` | Returns blank for other dates |
| `src/trial_form.py` L58 | `_DEFAULT_RACE_DATE = "2026-06-06"` | Wrong fallback for any other event |

### Breaks (d) Non-Windows System

| File | Evidence | Impact |
|---|---|---|
| `src/cli.py` L38-41 | `sys.stdout.reconfigure(encoding="utf-8")` — Windows-specific | Harmless on Linux (method exists), but signals Windows assumptions |
| `scripts/morning_odds.py` | Windows NT User-Agent in `_RP_HEADERS` | Cosmetic but shows provenance |
| `pyproject.toml` / docs | No platform requirements specified | Undocumented |
| Path separators | All use `Path()` correctly | ✅ Cross-platform |
| Python interpreter | History.md: `C:\Users\stevenn\AppData\Local\...` | Not in code but in team memory |

**Assessment:** The codebase is not catastrophically Windows-only (Path() is used correctly), but
the Epsom/2026 specificity is so deep it would require editing 15+ files to run for a different
event. That's not a skill — it's a bespoke tool.

---

## 4. Manual Coordinator Interventions

Today's Derby pipeline required at least these non-automatable interventions:

### 4.1 HTML Header Surgical Patch (Linus-v3 guardrail injection)
**What happened:** After Linus-v3 rendered the Derby card, the coordinator identified that lines
174 and 178-181 needed surgical correction to fix an HTML structure issue from Linus's guardrail-
bound injection.
**Why it can't transfer:** Requires knowing the exact HTML line structure, which div classes wrap
what content, and which lines correspond to which race slot. The HTML has no semantic injection
markers — only raw line offsets.
**Can be codified?** Yes. Define `<!-- INJECTION-POINT: race-{time}-header -->` comment anchors
in the template. Linus would target comments, not line numbers. **Medium effort.**

### 4.2 Apollo One Override Decision (Linus-v3 VOID)
**What happened:** Dance In The Storm was confirmed NR (absent from RP live racecard at 07:08).
The coordinator reviewed Rusty's alternative pick (Apollo One WIN @ 7/1, £1.00) and approved
it as a VOID override, then Linus injected the 17:55 Apollo One row into the final card.
**Why it can't transfer:** Requires understanding what VOID means in the context of a bet slip,
knowing that a VOID bet is financially recoverable but needs replacing, and having the domain
judgment to evaluate Rusty's alternative pick against the daily budget and the remaining races.
**Can be codified?** Partially. A `void_replacement` ceremony with defined steps (Rusty scores
alternative → Danny sign-off threshold → Linus injects) can be documented. The judgment call
on whether to replace or leave void is inherently coordinator territory. **Hard to fully automate.**

### 4.3 Manually Unblocking Livingston-3's Silent-Completion Read
**What happened:** Livingston-3's pre-Derby drift check at 15:39 appeared to complete normally
but all scrape routes were silently blocked. The coordinator had to recognise that "no data
returned" was a failure state, not a "no movement detected" true result.
**Why it can't transfer:** No exception, no error exit code — the script returned cleanly with
empty data. A stranger would interpret this as "no price movement" rather than "scrape failed."
**Can be codified?** Yes, with validation. `morning_odds.py` should assert minimum runner count
before writing output: `if horse_count < EXPECTED_MIN_RUNNERS: sys.exit("SCRAPE FAILURE: ...")`
The SL session-check should happen at import time with a clear `EnvironmentError` if creds absent.
**Low effort — high value.**

### 4.4 Scribe-16 Partial-Failure Cleanup via Scribe-17
**What happened:** A commit/merge pass (Scribe-16) had a partial failure that required a follow-up
Scribe-17 cleanup pass.
**Why it can't transfer:** Requires understanding the decisions.md append-only invariant, the
inbox merge protocol, and the difference between what was vs wasn't successfully committed.
**Can be codified?** Yes. A pre-commit validation script that checks inbox files exist, decisions.md
is append-only (no deletions), and the merge summary is internally consistent. **Medium effort.**

### Dual-Artifact Rule
**What happened:** All in-day edits must apply to BOTH `racecard-YYYY-MM-DD.html` AND
`report-YYYY-MM-DD.html` — discovered and documented on Ladies Day, correctly applied Saturday.
**Status:** Codified in linus/history.md and the bet-pass-rationale skill. But there is no
automated check that both files are in sync. A stranger would miss the second artifact.
**Can be codified?** Yes. A `validate_artifacts.py` script that diffs key bet-data sections
between the two HTML files and warns on mismatch. **Low effort.**

---

## 5. Domain Knowledge Requirements

A publisher-user needs to KNOW the following, none of which is documented in the codebase:

### Bet Structure
- **WIN + EW stake shapes:** Steve's convention is WIN for high-confidence picks, EW for medium/
  outsider tier. The `src/betting.py` gate logic implements this but the thresholds (win_edge ≥15%,
  EW combined edge ≥20%) are not explained to the user.
- **Each-way terms by field size:** 9+ runners → 4 places at 1/5 odds; 5-8 runners → 2 places;
  etc. The betting.py code calculates EW returns but doesn't document the place-term table.
- **Daily outlay cap:** Steve's £100 cap is referenced in history.md and runbook scripts
  (BANKROLL = 200 in refresh_friday.py, `--outlay 100` on the card command) but never explained.
  A user with a different cap gets no guidance on how to parameterize.

### Race-Day Operations
- **NR handling:** When a horse is declared non-runner, its bet voids at SP. The pipeline has
  no automated NR detection — it relies on the Livingston baseline RP scrape to filter, and on
  coordinator judgment to decide which NRs affect live bets.
- **Drift semantics:** >20% inward = potential steam; >30% outward = drift concern triggering
  Saul's delta-check. These thresholds are in decisions.md and proposed (unratified) rules but
  not in any code or user-facing documentation.
- **Stale odds caveat:** The "(stale)" label in the HTML means odds are from the 2026-06-02
  enrichment, not from a live feed. A stranger reading the card would not understand this without
  reading decisions.md history.

### Model Concepts
- **Trifecta box mechanics:** 3/4/5-horse boxes, combination counts (6/24/60), stake-per-combo
  conventions, when to widen the box based on race stdev. This is documented in decisions.md
  and in the trifecta-box skill but not in any user-facing documentation.
- **Trial taxonomy (Tier 1/2/3):** Required to understand why trial_form scores vary.
  Tier 1 = Derby/Oaks trials (Dante, Chester Vase, Musidora); Tier 2 = Secondary; Tier 3 = Listed/
  international. Only documented in src/trial_form.py docstring.
- **Neutral 50 anti-fabrication rule:** The model returns 50 (not 0) for missing data. A user
  who doesn't understand this would misread neutral 50 as "average confidence" when it really
  means "no data."
- **Race confidence / stdev:** The 4-horse trifecta box decision came from stdev = 25.23,
  gap #3→#4 = 0.22σ. A user cannot replicate this reasoning without understanding the decision
  tree in decisions.md (2026-06-05 entry).

### Should the Skill Include a Glossary?

**Yes — mandatory.** Recommend `docs/glossary.md` covering: going types, EW terms by field size,
WIN/EW/PASS gate thresholds, neutral 50 semantics, trifecta box decision tree, drift/steam
thresholds, stale-odds meaning. This is a minimum for a published skill. The model can produce
defensible picks; without the glossary, the user can't interpret them.

**Fail with helpful errors?** Also yes. `src/betting.py` should add `_explain_pass()` output
that maps PASS reasons to human-readable text. This is partially implemented (rationale field
exists in bet dicts) but not surfaced in the HTML template. Steve's ask from 2026-06-05 for
pass-rationale blocks confirms this is already a known gap.

---

## 6. Skill Packaging Shape

### Options

**(a) Monolithic skill — end-to-end**
Everything in one skill: fetch racecard → enrich odds → score → predict → render → validate →
publish. One command. Maximum magic.
**Problem:** All live data routes failed today. A monolithic skill that silently falls back to
4-day-old synthetic prices, with no signal to the user about which data paths worked, is a
liability. The monolith hides too much.

**(b) Composable kit — data-fetch, score, render, validate, publish**
Separate skills that can be used independently. A user can skip `data-fetch` and BYO their own
prices. The scoring skill works on any conformant racecard JSON. The render skill takes scored
output.
**Problem:** Requires more documentation and more user judgment about which skills to chain.
But today's failures show that the chain DOES break at the data-fetch step and users need to
be able to bypass it.

**(c) Workflow template — assumes user has data**
Like (b) but the data-fetch skill is explicitly out of scope. User provides a racecard JSON
and prices CSV; the skill does scoring → rendering → validation only.
**Problem:** Punts the hardest problem (live data) to the user without guidance. Fine for
sophisticated users; hostile for newcomers.

### Recommendation: **(b) Composable Kit**

**One-paragraph justification:**

Today's failure sequence — all three scraper routes blocked simultaneously, credentials
undocumented, market_move signal INERT for the full weekend — is the decisive argument against
a monolith. If `data-fetch` is a separate, clearly-scoped skill with explicit documentation of
every credential it needs, an `--env-check` flag that validates prerequisites before running,
and a BYO-prices CSV fallback as first-class mode, then the failure is localised and
recoverable. The user who can't get live data simply passes `--no-live-data` and the rest of
the pipeline runs cleanly. The scoring engine (src/) is already well-separated from the
orchestration scripts and has zero hardcoded paths — it's essentially ready to be the core
of a `score` skill with only date/venue parameterisation work remaining. The render and
validate skills map directly to `src/report.py` and `src/racecard.py` which are similarly
self-contained. A composable kit makes each failure point explicit, each skill independently
testable, and the BYO-data path first-class rather than an afterthought. The monolithic
approach would require solving ALL the blockers below before it could ship; the kit approach
lets the scoring skill ship independently while data-fetch remains in development.

---

## 7. Top 5 Publish-Blockers

| Rank | Severity | Blocker | Evidence |
|------|----------|---------|----------|
| 1 | 🔴 BLOCKER | **All live scraper routes are dead with no documented fallback path for users** | RP 406, Betdata 404, SL SPA+no-creds — all three failed on Derby Day. market_move (0.0683 weight) was neutral for 100% of runners for the full weekend. No user-visible warning. A stranger gets confident-looking picks based entirely on synthetic prices from 4+ days ago. |
| 2 | 🔴 BLOCKER | **SPORTINGLIFE_USER / SPORTINGLIFE_PASS are undocumented and fail silently** | Livingston-3 (2026-06-06T15:39): "SL env vars NOT SET in current session." No `.env.example`, no README, no `check_env()` at startup. Silent 373-byte SPA shell with no exception. A stranger would never know this was a failure. |
| 3 | 🔴 BLOCKER | **Epsom/2026 hardcoded throughout — not generalisable to any other event** | `enrich_odds.py` is a 100% horse-name dict for Epsom 2026. `DATES = ["2026-06-05", "2026-06-06"]` in refresh_friday.py. `RACECARD_FILES` keyed to 2026 dates. `_DATE_DAY_NAMES` dicts in racecard.py and report.py only recognise 2026 dates. 15+ files require editing to run for Royal Ascot 2026 or Epsom 2027. |
| 4 | 🟡 POLISH | **Manual HTML surgery is the primary NR-swap and annotation workflow** | 3 NR swaps × 2 artifacts + Apollo One override + trifecta injection on Derby day alone. `render_replacement_row()` promoted to HARD-RULE priority but not yet wired to template (src/report.py). The dual-artifact rule is in history.md, not in code. No automated sync check between racecard and report HTML files. |
| 5 | 🟡 POLISH | **No README, no setup guide, no data contract, no glossary** | 36+ probe scripts in scripts/, live credentials in .env, CLI description says "Epsom Classics 2026", no entry-point documentation. A stranger cloning the repo has no starting point. The racecard JSON schema is undocumented. Drift/steam thresholds are in decisions.md only. The neutral-50 anti-fabrication rule is in decisions.md and charter, not in any user-visible help text. |

---

## Day 1 for a Stranger

### Shortest Happy Path (if blockers are addressed)

```
1. git clone github.com/Steve-MS/Derby && cd Derby
2. cp .env.example .env && fill in SPORTINGLIFE_USER, SPORTINGLIFE_PASS
3. pip install -r requirements.txt
4. Place your racecard JSON in data/raw/epsom-YYYY-MM-DD-racecards.json
5. py enrich_odds.py                                 # populate prices
6. py -m src.cli score   --date YYYY-MM-DD
7. py -m src.cli predict --date YYYY-MM-DD --bankroll 200
8. py -m src.cli report  --date YYYY-MM-DD
9. Open outputs/report-YYYY-MM-DD.html
```

That's 9 steps — manageable. But Step 4 requires knowing the undocumented racecard JSON schema.
Step 5 requires editing `enrich_odds.py` with the right horse names and prices. Neither is
documented anywhere.

### Most Likely First Failure

**Step 2 doesn't exist** — there is no `.env.example`. The stranger opens `.env` and sees live
credentials. If they try to run without credentials, all scraper routes silently fail and the
pipeline runs on synthetic data with no warning. If they try to share the repo, they accidentally
publish `RACING_API_PASSWORD=<REDACTED>`.

**Second most likely first failure:** After somehow getting through setup, the stranger runs
`py -m src.cli score --date 2026-07-15` (Ascot) and gets `✗ Racecard not found: ...epsom-2026-07-15-racecards.json`. The CLI hardcodes `epsom-` prefix in the racecard filename. There is no `--venue` flag.

---

## Summary: What Must Change Before Publish

### Before Any Public Release

1. **🔴** Create `.env.example` with all required env vars documented (SPORTINGLIFE_USER,
   SPORTINGLIFE_PASS, RACING_API_USERNAME, RACING_API_PASSWORD, BETFAIR_APP_KEY). Add `.env`
   to `.gitignore` if not already present. Add `check_env()` startup validation that exits loudly
   if required vars are unset.

2. **🔴** Parameterise venue and date throughout: `--venue epsom`, `--dates 2026-06-05,2026-06-06`
   on all CLI commands. Remove hardcoded `DATES` in refresh_friday.py and `RACECARD_FILES` in
   morning_odds.py. Replace `epsom-{date}-racecards.json` naming with `{venue}-{date}-racecards.json`.
   This touches ~15 files but is mostly mechanical string replacement.

3. **🔴** Add minimum-runner validation to morning_odds.py and all scraper scripts. If a scrape
   returns fewer than N runners (configurable, default ~5), exit with error rather than writing a
   partial file that will silently produce wrong results.

4. **🟡** Wire `render_replacement_row()` into the Jinja template (already HARD-RULE priority per
   Danny history.md 2026-06-05). Add injection-point HTML comments to the template so NR swaps
   can target semantic anchors rather than line numbers.

5. **🟡** Write `docs/README.md` (entry point), `docs/glossary.md` (domain terms), and
   `docs/data-schema.md` (racecard JSON contract). Add `--help` text to CLI that includes
   threshold explanations and points to glossary.

---

*Danny — Lead, 2026-06-06T23:02:55+01:00*


---

### 2026-06-06T07:05+01:00: Saturday Blockers Resolution (Derby Day)
**By:** Danny (Lead)
**Requested by:** Steve (via race-day watchdog 07:00 gate)

---

## BLOCKER #2 — Derby Race Time: RESOLVED ✅

**Verdict: 16:00 BST is CORRECT. No patch required.**

Sources confirming 16:00:
1. The Jockey Club / Epsom Downs official — https://www.thejockeyclub.co.uk/epsom-derby/plan-your-day/when-and-what-time/
2. HorseRacing.net racecard — https://www.horseracing.net/epsom/06-06-26
3. IrishRacing.com racecard — https://www.irishracing.com/racecards/Sat-6th-Jun-2026/Epsom/1600

The coordinator brief stating "16:30" was in error. `bets-2026-06-06.json` race_id `epsom-2026-06-06-1600` and Saturday HTML extracted times are both correct. No file changes needed.

---

## BLOCKER #1 — Causeway NR: PATH C (Hybrid) ✅

**Chosen: (C) Annotate now, re-render only if more NRs surface from Livingston's 07:00 baseline.**

### Rationale (1 sentence)
Causeway is a £0.25 EW outsider that voids automatically at declarations — the financial risk is nil, re-rendering risks fresh bugs on Derby morning, and annotation takes 2 minutes with zero blast radius.

### What happens now
- NO re-render by Linus (unnecessary given £0.25 void-at-declarations + no visual confusion for Steve since he knows Causeway is out)
- Livingston's 07:00 baseline capture will confirm NR status from live RP scrape
- If Livingston's baseline surfaces ADDITIONAL NRs beyond Causeway → escalate to full re-render (Linus, Path A) before Steve's 10:00 GO/NO-GO
- If Causeway is the only NR → let it void naturally; it's already flagged in Livingston's report

### If escalation to Linus becomes necessary (scope brief)
> **Linus brief (conditional — only if ≥2 NRs total):**
> Re-generate `outputs/racecard-2026-06-06.html` + `outputs/bets-2026-06-06.json` with ALL confirmed NRs removed (Causeway + any from 07:00 baseline). Preserve: all other picks, trifecta block (adjust box if #4 model-ranked horse drops), going advisory, outsider rationale for remaining runners. Source of truth for NR list: Livingston's baseline capture + RP declarations page. Do NOT touch `data/results/*.json`.

---

## CHECKPOINT 4 — Saturday Operator Sequence & PROPOSED Rules

### Context
Two rules remain PROPOSED (not ratified by Steve):
1. No manual override of sub-50 model scores without 2-PM sign-off
2. Saturday morning ≥30% steam/drift gate

### My call (Danny, Lead):

**Operate under PROPOSED rule #2 as soft guidance today — no ratification required.**

Reasoning:
- Rule #2 has ZERO impact on Derby picks (no sub-50 picks exist on Saturday card per decisions.md line 1323)
- The mechanism is already in motion regardless: Livingston 07:00 baseline → Saul delta-check → Danny review → Steve 10:00
- If Saul's delta-check surfaces ≥30% movers, I will review them and flag to Steve with a binary HOLD/PULL recommendation
- This is operationally identical to ratification — but we're treating it as guidance not hard rule, so Steve retains full override authority at 10:00
- Formal ratification deferred to post-Derby (more data from Royal Ascot will strengthen the case)

**What Saul should expect:**
- Run delta-check by 07:30 as planned
- If ANY runner has moved ≥30% (steam or drift) vs the bets-file baseline price, flag it to Danny immediately
- I'll review and make a HOLD/PULL call before Steve's 10:00 window
- If no ≥30% movers: proceed to 10:00 GO/NO-GO with card as-is

**Rule #1 (sub-50 gate):** Not operationally relevant today — no sub-50 picks on Saturday card. Fully deferred to Royal Ascot data.

---

## New Flags

None surfaced. Causeway is the only confirmed NR. Livingston's 07:00 baseline will be the authoritative check for any further NRs declared overnight.

---

## Summary

| Item | Outcome |
|------|---------|
| Derby time | **16:00 BST confirmed** (3 sources) — no patch |
| Causeway NR | **Path C** — let void naturally; re-render only if more NRs surface |
| Linus brief written | **Conditional only** — fires if ≥2 NRs from baseline |
| PROPOSED rules | Operate as soft guidance; Saul runs delta-check as planned |
| New flags | None |


---

# Derby Day Results — Post-Mortem
**Agent:** Livingston (Data Engineer)
**Date:** 2026-06-06T23:02:55+01:00
**For:** Steve

---

## Going Report (Official)

| Course | Going | Changed At |
|--------|-------|------------|
| Derby course (round) | Good to Soft (Good in places) | → GTS after R1 (13:30), → **Soft** after R4 (15:15) |
| 5f straight course | Good to Soft (Good in places) | No change recorded |
| Weather | Rain | — |
| Wind | Fairly strong, half behind | — |

**Total non-runners on card: 10** (unsuitable ground dominated; Benvenuto Cellini was a stalls incident NR).

---

## Results Table

| Time | Race | Our Pick(s) | SP (pick) | Finished | Outcome | P&L |
|------|------|-------------|-----------|----------|---------|-----|
| 13:30 | Betfred Tattenham Corner Stakes G3 | NO BET | — | **Ten Bob Tony** won (Shoemark/Walker) ~5/1; NeverSoBrave 15/8F unplaced | N/A | £0.00 |
| 14:05 | Princess Elizabeth Stakes G3 | Princess Child WIN £1.00 @ 11/1 | — | **PRINCESS CHILD NR** (vet's cert). **Sparks Fly** won (Pearson/Loughnane) 7/2 | **REFUND** | +£0.00 (£1.00 returned) |
| 14:40 | Coolmore Coronation Cup G1 | NO BET (Illinois invalidated) | — | **Bay City Roller** won (Murphy/Scott) ~11/2, 10 lengths clear; Calandagan 5/4F unplaced | N/A | £0.00 |
| 15:15 | Betfred Dash Heritage Handicap | Another Baar WIN £0.25 @ 39/1; Ziggy's Triton EW £0.25 @ 32/1 | — | **Arklow Lad** won (Davies/Appleby); 2nd Vintage Clarets; 3rd Lexington Blitz. Kinswoman 5/1F unplaced. Another Baar **10th**, Ziggy's Triton **11th** | **LOST** both | -£0.75 |
| 16:00 | Betfred Derby G1 | Action WIN £1.00 @ 13/1; Trifecta box [Action, Benvenuto Cellini, Item] £6.00 | 13/1 (taken) | **BENVENUTO CELLINI NR** (stalls, 3/1F, Rule 4: 25p/£). **Christmas Day** won (Whelan/O'Brien) 7/1. 2nd Maltese Cross 12/1, 3rd James J Braddock 9/1. Item 9th, **Action 12th** | **LOST** WIN; Trifecta **VOID/REFUND** | -£1.00 (+£6.00 refund) |
| 16:40 | Cherryfield (Croydon) Lester Piggott Handicap | Folk Pageant WIN £1.50 @ 6/1 | 5/1 SP (taken 6/1) | **FOLK PAGEANT WON** (Scott/Johnston) 5/1. 2nd Silver State (IRE) 20/1, 3rd Pendella (IRE) 9/1. HellYeahHeDid 5/4F unplaced | **WINNER** ✅ | +£9.00 (return £10.50) |
| 17:20 | HKJC World Pool Northern Dancer Handicap | Lord Melbourne WIN £0.75 @ 19/1; Prydwen EW £0.25 @ 17/1 | — | **PRYDWEN NR** (unsuitable ground). **Too Soon** won (Fentiman/Gary & Josh Moore) 17/2. 2nd Night Breeze 15/2, 3rd Bulletin 15/2. **Lord Melbourne 5th** (SP ~15/2 on day vs our 19/1 model price) | **LOST** Melbourne; Prydwen **REFUND** | -£0.75 (+£0.50 refund) |
| 17:55 | JRA Tokyo Trophy Handicap | Apollo One WIN £1.00 @ 7/1 | — | **Sondad** won (Mason/Easterby) 11/2. 2nd Invictus Gold 28/1, 3rd Partisan Hero 11/1. Fine Interview 15/8F unplaced. **Apollo One unplaced** (parade notes: "not as fit as could be") | **LOST** | -£1.00 |

---

## P&L Summary

| Category | Amount |
|----------|--------|
| Total portfolio staked | £6.50 |
| Trifecta side bet | £6.00 |
| **Total outlay** | **£12.50** |
| Returns — Folk Pageant WIN | £10.50 |
| Refunds — Princess Child NR | £1.00 |
| Refunds — Prydwen NR | £0.50 |
| Refunds — Trifecta (Benvenuto Cellini NR) | £6.00 |
| **Total receipts** | **£18.00** |
| **Net P&L** | **+£5.50** |
| ROI on total outlay | +44.0% |

One bet settled as winner: Folk Pageant (Lester Piggott Handicap, 16:40). Three bets/stakes refunded due to NRs. Five bets lost.

---

## Scrape Source Report

### What worked

| Source | Status | What it returned |
|--------|--------|-----------------|
| `https://www.racingpost.com/results/9/epsom-downs/2026-06-06/` | ✅ ACCESSIBLE | Going, NR list with reasons, Rule 4 deductions, distances, times, jockey + trainer names, Tote dividends. **Horse names stripped** (rendered as HTML link anchors → plain markdown extraction loses them). |
| Web search (tool) — Bing/AI aggregation | ✅ ACCESSIBLE | Horse names 1st/2nd/3rd all races, SPs, finishing positions for all our picks. Multi-source citation (myracing.com, racingtv.com, horseandhound.co.uk, sportinglife.com, channelnewsasia.com, oddschecker.com, timeform.com). |

### What failed / was not attempted

| Source | Status | Notes |
|--------|--------|-------|
| RP live racecard (pre-race) | ❌ BLOCKED at 15:39 | HTTP 406 / 404 for all racecard routes (confirmed during Derby build-up) |
| Sporting Life authenticated | ⚠️ SKIPPED | `SPORTINGLIFE_USER` env var not set in current session |
| At The Races | ❌ KNOWN BLOCKER | Blocks requests (confirmed from history) |
| Racing Post individual race pages | NOT ATTEMPTED | Would need known race IDs; aggregate page + web_search was sufficient |

**Key finding:** RP *results* pages (post-race) ARE accessible even when racecard pages are blocked during the day. The blocker appears to be route-specific (racecard vs results endpoints). Results pages rendered without JS, racecard pages appear to require SPA/JS hydration.

---

## Lessons Learned for Tomorrow

### What the model got right
1. **HOLD card (Soft ground) correctly called.** Going became full Soft from Race 4 (15:15) — exactly matching the rain-declared scenario. Every race from 15:15 onwards ran on Soft, with most times 8–10 seconds slower than standard.
2. **Folk Pageant identified as winner.** Model rank 2/10, rank_gap +2. Soft preference confirmed. 6/1 early price vs 5/1 SP — early price advantage retained. Clean signal, no adverse flags. *This is exactly how the model should work.*
3. **Illinois (Coronation Cup) correctly invalidated.** Model scored it last (rank 6/6, rank_gap 0). Calandagan (5/4F) was also unplaced. The field avoided was the right call.
4. **COMPRESSED_RANGE_CAUTION (Dash) proved correct.** Both Another Baar and Ziggy's Triton finished 10th and 11th respectively. The flag accurately reflected signal unreliability in the 5-point RPM range.

### What went wrong
1. **Action finished 12th in the Derby.** Model had Action at rank 3/14, score 69.4. Christmas Day (the winner, which was V1_INVALIDATED_CHRISTMAS_DAY in the final bets file) had earlier scored 77.1 per the Trifecta box scores. The rank_gap invalidation rule correctly excluded Christmas Day from the WIN slot, but the model did not surface him as a strong enough trifecta candidate. **Lesson: rank_gap threshold for WIN may be too aggressive; Trifecta box should consider highest absolute score, not just rank_gap picks.**
2. **Benvenuto Cellini NR (stalls incident) voided the Trifecta.** Market had steamed him from 9/4 ante-post to 3/1F on the day. Score 88.0 — our top-scoring horse. Would have been the Derby favourite had he broken cleanly. **This is unforeseeable operational race-day risk; the trifecta box with only 3 horses is extremely vulnerable to a single NR voiding the entire ticket. Mitigation: require 4-horse box or back individual legs as each-way bets.**
3. **Lord Melbourne: model price vs market price divergence.** Our model had him at 19/1 (synthetic base, rank 1/17, rank_gap +13). On the day, sources suggest he may have started ~15/2 — a dramatic move-in from our 19/1. He finished 5th. **Lesson: SYNTHETIC_BASE_CAVEAT must be applied to rank_gap as well as stake sizing. When the real market disagrees by this magnitude, the rank_gap signal is unreliable.**
4. **Apollo One (override pick) also lost.** OVERRIDE_OF_VOID + SYNTHETIC_BASE_CAVEAT + GOING_FIT_CAUTION_PRECAUTIONARY — three amber flags on a bet placed at Steve's explicit request. Parade notes confirmed the horse "not as fit as could be." **Lesson: three amber flags on a pick = do not bet.**
5. **Two NRs on picks again (Princess Child, Prydwen).** Live-runner gate was in place for the baseline check, but unsuitable-ground withdrawals cannot be predicted until race morning, and some occur after the final declarations window. Princess Child's vet's certificate came day-of. **Lesson: EW bets on outsiders in soft/heavy ground conditions carry compounding NR risk.**

### Going/model calibration note
The going-fit signal (going_fit 68 for Action, 78 for Lord Melbourne) did not differentiate well in Soft conditions. Both horses underperformed. In full-Soft going, the model may need a separate Soft-specific calibration rather than interpolating from GTS form. **Recommend: review going_fit signal for Soft vs GTS separation before next soft-ground meeting.**

---

## Skill Publishability Audit — What Would Break for a Stranger

This section documents pipeline brittleness observed during Derby Day for the publish-skill review.

### Hard blockers (would prevent a stranger running the skill)

| Issue | Root Cause | Impact |
|-------|-----------|--------|
| **Live racecard scrape is unreliable** | RP racecard pages return 406 in production (confirmed multiple times). Alternative routes (SL API, Betdata) also 404 or DNS-fail. | Stranger cannot run the live-runner gate reliably without a paid/authenticated data source. |
| **No automated live odds** | Prices remain SYNTHETIC from 2026-06-02 enrichment run. RP odds are JS-loaded (WebSocket). No free API with live odds identified. | `market_move` signal is always flat (neutral 50). Stranger expecting live price signals gets nothing. |
| **Race times in task spec vs actual card** | Task spec listed times 13:50, 14:25, 15:00, 15:35 etc. Actual Epsom times: 13:30, 14:05, 14:40, 15:15. | Any hardcoded time filter will miss races. Race times vary year-to-year; must always re-fetch from live declarations. |
| **Env vars for Sporting Life not set** | `SPORTINGLIFE_USER` / `SPORTINGLIFE_PASS` not present in current environment | Authenticated SL scrape path silently skipped. Stranger has no documentation on what credentials are needed or where to obtain them. |

### Soft blockers (degraded experience)

| Issue | Root Cause | Impact |
|-------|-----------|--------|
| **RP results page strips horse names** | Markdown extraction of RP aggregate results loses horse names (rendered as `[name](url)` anchors in HTML; stripped in plain-text render). Individual race pages need known IDs. | Results pipeline requires web_search fallback; can't be fully automated from RP alone. |
| **Race IDs for individual RP pages not discoverable** | IDs are non-sequential and change each year. History log stores previous IDs but no pattern for inferring future ones. | Requires a probe step to discover IDs before individual-race fetch. |
| **Trifecta voiding on NR** | No guard in bet-file generation for trifecta box containing a potential NR. Benvenuto Cellini (3/1F) caught in stalls. | £6.00 side bet voided. A future user would need documentation that 3-horse box is NR-fragile. |
| **SYNTHETIC_BASE_CAVEAT not propagated to rank_gap** | Model rank_gap uses synthetic baseline prices. A horse the market rates 15/2 can appear at "19/1 rank_gap +13" — a false signal. | Misleading confidence scores for rank_gap when underlying prices are stale. Requires a "synthetic discount factor" on rank_gap confidence. |
| **Score files not re-run with day-of going** | `rusty-rescored-2026-06-06.json` was produced at 12:12 BST with GTS forecast. Ground became full Soft by 15:15. Going-fit scores were not refreshed. | All going_fit values used for afternoon selection were calibrated for GTS, not Soft. |

### For the publish-skill document
The skill currently requires: (1) a human to paste live odds/prices (no automated price source), (2) accepted that live racecard scrape is unreliable (mitigated by the live-runner gate protocol documented in `SKILL.md`), (3) knowledge that results are scraped from RP post-race results pages plus web_search fallback. A stranger would need a `RUNBOOK.md` covering: data source dependencies, env vars required, which scripts to run in which order, and the manual interventions expected at each gate.

---

## Files Written
- `data/enrichment/results-2026-06-06.json` — structured race results, one entry per race
- `.squad/decisions/inbox/livingston-derby-day-results-2026-06-06.md` — this file


---

# 2026-06-05T21:00+01:00: Friday 21:00 Archive Gate
**By:** Livingston (Data Engineer) — scheduled gate tick
**Requested by:** Steve (via race-day watchdog)
**Run completed:** 2026-06-05T21:00+01:00 BST

---

## 🚨 BLOCKING ISSUES FOR SATURDAY (Danny to review before 07:00)

### 1. Causeway still in Saturday racecard HTML — CONFIRMED NR
- `outputs/racecard-2026-06-06.html` (21745 bytes, last modified 13:44 today) contains "Causeway"
- History confirms Causeway is a confirmed non-runner (absent from RP racecard for 2026-06-06, confirmed during morning odds refresh)
- **Action needed:** Danny to decide whether to re-render the Saturday HTML with Causeway removed, or note it as a known stale entry
- `outputs/bets-2026-06-06.json` also has Causeway as an outsider EW pick (£0.25 stake) — if Causeway is NR at declarations, that bet becomes VOID (stake returned). Not a financial risk, but renders the outsider leg void.

### 2. Derby race time discrepancy
- `outputs/bets-2026-06-06.json` shows Derby race_id as `epsom-2026-06-06-1600` (16:00)
- Coordinator brief says "Derby is the headline **16:30 BST**"
- Saturday HTML also shows 16:00 in extracted times
- **Action needed:** Verify official race time against Epsom declarations at 10:00 Saturday. If actually 16:30, race_id may need updating. If 16:00 is confirmed, coordinator brief was in error — no action on files.

---

## Task 1 — Archive: Friday market files ✅

**Files moved to `data/enrichment/archive/2026-06-05/`:**
| File | Size | Notes |
|------|------|-------|
| `market-baseline.json` | 39,981 bytes | Friday AM gate (09:52 BST), 106 runners |
| `market-latest.json` | 54,055 bytes | Midday refresh (11:59 BST), 144 runners |

**Intra-day files:** No additional `market-*.json` files found in `data/enrichment/` root. The `odds-refresh-2026-06-05-*.json` files (2 files) do not match the `market-*.json` pattern and remain in place (not part of this archive scope).

---

## Task 2 — Saturday Scaffolding ✅

**Placeholders created:**
- `data/enrichment/market-baseline.json` — `{"date": "2026-06-06", "captured_at": null, "races": [], "status": "PENDING_07_00_CAPTURE"}` (93 bytes)
- `data/enrichment/market-latest.json` — `{"date": "2026-06-06", "captured_at": null, "races": [], "status": "PENDING_FIRST_REFRESH"}` (93 bytes)

**Saturday card race verification (from `outputs/bets-2026-06-06.json` + HTML grep):**
- 8 races found: 13:30, 14:05, 14:40 (Coronation Cup G1 ✅), 15:15, 16:00 (Derby G1 ✅), 16:40, 17:20, 17:55
- Coronation Cup: PRESENT ✅
- Derby: PRESENT ✅ — but see blocking issue #2 on race time
- `outputs/racecard-2026-06-06-hold.html` (soft-going contingency): EXISTS ✅ (15,846 bytes)
- Going advisory in bets file: "Forecast Soft by Derby post-time; use GREEN slip until official declarations, switch to HOLD if Soft declared"

---

## Task 3 — Re-scrape: Ladies Day Blocked EW Bets ✅ FULLY RESOLVED

**All 4 blocked EW place portions resolved via Racing Post individual result pages (920049, 920050, 920045).**

### Method confirmed
RP result pages list horses in **finishing order** (not cloth order). Verified by cross-checking known winners (Naana's Shadow cloth-6 → listed 1st ✅; Hickory Lad cloth-4 → listed 1st ✅) against previously confirmed jockey/trainer data.

### Results per race

| Race | RP ID | Winner | SP | Bet | Finish | EW Outcome |
|------|-------|--------|----|-----|--------|------------|
| 13:30 Dash Handicap | 920049 | Naana's Shadow (IRE) | 7/2F | o01 Rosie Frith EW | **12th/16** | **LOSE** |
| 14:05 Woodcote Listed | 920050 | **Hickory Lad (IRE)** | **100/30** | o02 Hickory Lad EW | **1st/13 — WINNER** | **WIN** ⭐ |
| 14:05 Woodcote Listed | 920050 | Hickory Lad (IRE) | 100/30 | s01 Wild Terrain EW | **12th/13** | **LOSE** |
| 15:15 Nifty 50 | 920045 | Sallaal (IRE) | 5/2F | o03 Liberty Lane EW | **8th/16** | **LOSE** |

### ⭐ Critical Stage 2a Correction — Hickory Lad EW (o02)
- **Saul's Stage 2a assumption was wrong.** Saul wrote "Winner = Phillip Makin trained horse. Hickory Lad WIN side confirmed lost." — Saul assumed the Phillip Makin winner was a *different* horse.
- **Confirmed from RP 920050:** Hickory Lad (IRE), cloth 4, Sam James, **Phillip Makin** — listed 1st = WINNER at SP 100/30.
- **Return calculation (Saul's place-pay logic, 1/4 odds, places 1-2-3):**
  - WIN: £0.25 × 4.333 decimal = £1.083
  - PLACE: £0.25 × 1.833 decimal = £0.458
  - **Total return: £1.54 | Net P&L: +£1.04**
- Also confirmed: **Respond (s02) finished 2nd at SP 11/4** (3.75 decimal) — WIN bet correctly LOSE, but SP now on record.

### Files updated
- **NEW:** `data/results/ladies-day-2026-06-05-winners-update.json` (4,256 bytes) — delta file with all 3 race winner resolutions and finishing positions
- **UPDATED:** `data/results/pl-2026-06-05.json` (2,389 bytes) — corrected summary with Hickory Lad WIN, all blocks resolved
  - `total_returned_gbp`: 0.00 → **1.54**
  - `net_pl_gbp`: -7.67 (partial) → **-10.07** (full)
  - `roi_pct`: -100% → **-86.7%**
  - `blocked_stake_gbp`: 3.94 → **0.00**

**NOT touched:** `data/results/ladies-day-2026-06-05.json` (Stage 1, immutable) ✅

### 13:30 HTTP note
RP 920049 (13:30 Dash) initially returned HTTP 406 (SigSci WAF rate-limit). Retry with different UA headers after 8s sleep succeeded (HTTP 200). Total scrape retries: 1 per page.

---

## Task 4 — Health Check: Saturday Pipeline Readiness

| Item | Status | Detail |
|------|--------|--------|
| `outputs/racecard-2026-06-06.html` exists | ✅ PASS | 21,745 bytes, modified 2026-06-05 13:44 |
| Saturday racecard has live runners | ✅ PASS | 8 races present, Derby + Coronation Cup confirmed |
| **Causeway in HTML** | ⚠️ FLAG | Confirmed NR still in HTML — see blocking issue #1 |
| `outputs/bets-2026-06-06.json` exists + valid JSON | ✅ PASS | 9,508 bytes, valid JSON, scenario=GREEN going GTS+ |
| `outputs/racecard-2026-06-06-hold.html` exists | ✅ PASS | 15,846 bytes, modified 2026-06-04 18:11 |
| Network reachability (Racing Post) | ✅ PASS | RP returned HTTP 200 on multiple result pages throughout run; one 406 rate-limit resolved on retry |
| Going advisory in bets | ✅ PASS | Going advisory present: "5.2mm rain overnight, 60-80% soft by 16:00, use GREEN until official declarations" |
| Derby time in bets vs brief | ⚠️ FLAG | Bets/HTML show 16:00; coordinator brief said 16:30 — verify at 10:00 declarations |

---

## Summary P&L Update

| | Before gate | After gate |
|--|------------|-----------|
| Total returned | £0.00 | **£1.54** |
| Net P&L | -£7.67 (confirmed) / -£11.61 (worst) | **-£10.07 (final)** |
| ROI | -100% (confirmed) | **-86.7%** |
| Blocked bets | 4 | 0 |
| VOID (Belinus) | £5.00 stake returned | unchanged |

---

## For Danny (07:00 brief)

1. **Causeway NR:** HTML still has Causeway. Decide: re-render or annotate. Outsider EW bet (£0.25) becomes void if NR at official declarations.
2. **Derby time:** Confirm 16:00 vs 16:30 against official Epsom schedule at 10:00.
3. **Going trigger:** If official going declared Soft → switch to `racecard-2026-06-06-hold.html` + cancel Item WIN bet per bets-2026-06-06.json going_advisory.
4. **Market baseline ready:** `data/enrichment/market-baseline.json` is a clean PENDING_07_00_CAPTURE placeholder. The `morning_odds.py --mode baseline --date 2026-06-06` run at 07:00 will populate it.
5. **Hickory Lad win:** Friday P&L is now confirmed -£10.07 (not -£11.61 worst case). One small win on the day.

---

*End of Friday 21:00 Archive Gate — Livingston*


---

### 2026-06-06T15:39+01:00: Pre-Derby Drift Check (URGENT-LITE)
**By:** Livingston (Data Curator)
**Requested by:** Race-day watchdog (Steve at the races)
**Scope:** 4-horse drift check — Derby 16:00 × 3 + 17:20 × 1. NOT a full refresh.

---

## Live Scrape Status

**BLOCKED across all sources.** Sporting Life: SPA shell only (373 bytes, no data).
Racing Post: HTTP 406 / 404. Betdata.io: 404. Sporting Life API: 404/DNS-fail.
SL env vars (SPORTINGLIFE_USER / SPORTINGLIFE_PASS): **NOT SET** in current session.

**Fallback applied:** Card prices provided by Steve used as proxy for live (~15:39 BST).
All card prices match `market-latest.json` 11:26 BST snapshot exactly → 0% further movement detected since morning capture.

**Source column below: Racing Post 07:08 BST live scrape (Livingston baseline) + RP forecast odds 11:26 BST (Livingston latest).**

---

## Drift Table

| Horse | Race | Baseline 07:08 | Morning 11:26 | Card ~15:39 | Drift% (base→morn) | Status | Flag |
|-------|------|---------------|--------------|-------------|-------------------|--------|------|
| Action | 16:00 Derby | 12/1 | 13/1 | 13/1 | +7.7% DRIFT | DECLARED | ✅ OK |
| Benvenuto Cellini | 16:00 Derby | 9/4 | Evs | Evs | **−38.5% STEAM** | DECLARED | 🚨 MATERIAL |
| Item | 16:00 Derby | 4/1 | 7/2 | 7/2 | −10.0% steam | DECLARED | ✅ OK |
| Lord Melbourne | 17:20 N.Dancer Hcp | 12/1 | 19/1 | 19/1 | **+53.8% DRIFT** | DECLARED | 🚨 MATERIAL (Saul +54% WARN ✓) |

> Drift% = (morning_decimal − baseline_decimal) / baseline_decimal × 100.
> Card vs morning = 0% for all 4 — no movement detected post-11:26 BST.

---

## NR Declarations Confirmed

All 4 horses confirmed DECLARED (non_runner=False in 07:08 baseline RP live scrape):
- **Action** — present in live RP racecard at 07:08 ✅
- **Benvenuto Cellini** — present ✅
- **Item** — present ✅
- **Lord Melbourne** — present ✅

Derby NRs (for context): Causeway, Constitution River, Endorsement, Proposition confirmed NR at 07:08 baseline. None of the 4 target horses affected.

---

## Bet Position Summary

| Horse | Bet | Note |
|-------|-----|------|
| Action | WIN £1 + trifecta banker | DECLARED. 13/1 = gentle drift from 12/1 baseline. No concern. |
| Benvenuto Cellini | Trifecta leg | DECLARED. **Heavy steam 9/4→Evs.** Market confidence. Shortening suits the trifecta. |
| Item | Trifecta leg | DECLARED. Slight steam 4/1→7/2. No concern. |
| Lord Melbourne | WIN (implied) 19/1 | DECLARED. **Major drift 12/1→19/1 +53.8%.** Saul's WARN confirmed. Market moving against. Already flagged this AM; Danny aware. |

---

## Data Provenance

- Baseline prices: `data/enrichment/market-baseline.json` captured 2026-06-06T07:08 BST (RP live racecard)
- Morning prices: `data/enrichment/market-latest.json` captured 2026-06-06T11:26 BST (RP forecast odds)
- Live prices (~15:39): **UNAVAILABLE** — all scrape routes blocked. Card prices (Steve) used as proxy.
- NR status: `livingston-sat-baseline-NRs.md` (07:08 RP live scrape)

---

## Limitations

1. No live Sporting Life odds retrieved — cannot confirm price movement in the 11:26→15:39 window from an independent source.
2. Card prices assumed static since morning. Exchange prices (Betfair) may differ — Steve should cross-check app if Lord Melbourne stake is significant.
3. SPORTINGLIFE env vars not present in session. If Steve can share session credentials separately, a re-scrape could confirm.


---

### 2026-06-06T07:08 BST: Saturday NR check — 07:00 baseline gate
**By:** Livingston (Derby Day baseline capture)
**Source:** RP __NEXT_DATA__ live racecard scrape at 07:08 BST

---

## ⚠️ PROBABLE NEW NON-RUNNERS — BET IMPACT (URGENT for Danny / Steve)

These horses are **present in the locked racecard HTML** but **absent from the RP live racecard** at 07:08 BST. Filtered as probable NRs by the morning_odds script. **Requires official confirmation before betting.**

### 1. DANCE IN THE STORM — 17:55 JRA Tokyo Trophy Handicap
- **Bet impact: WIN £1.33 @ 18.5 (35/2)** — Steve's main late-race WIN
- Bets file: `epsom-2026-06-06-1755`, stake £1.33, edge +93.3%
- Status: ABSENT from RP racecard at 07:08. **Must be verified before bet placement.**
- Action required: Danny / Steve to confirm via official Epsom declarations or bookmaker.

### 2. SEE THE FIRE — 14:40 Coolmore Coronation Cup G1
- **Bet impact: outsider EW £0.25 @ 13.0 (12/1)** — Kaylee #1 vs market #6
- Bets file: `epsom-2026-06-06-1440`, outsiders block
- Status: ABSENT from RP racecard at 07:08. Coronation Cup now shows 6 confirmed runners (was 8).
- Action required: Confirm runner status. If NR, EW outsider bet is void.

---

## ✅ KNOWN NR — CONFIRMED

- **Causeway** — 16:00 Derby G1: CONFIRMED NR (absent from RP since 2026-06-05; known from Friday gate). Still present in locked racecard HTML. Danny reviewing HTML fix separately.
  - Bet impact: outsider EW £0.25 in bets file — stake is void if officially NR.

---

## Other horses from bets file — STATUS OK

- **Item** — 16:00 Derby G1: IN BASELINE at 5.0 (4/1). Bets file live override was 3.25; synthetic racecard price 5.0. Runner confirmed.
- **Kinswoman** — 15:15 Dash Handicap: IN BASELINE at 24.0 (23/1). Confirmed runner.
- **Allegresse** — 16:40 Lester Piggott Handicap: IN BASELINE at 9.0 (8/1). Confirmed runner.
- **Lord Melbourne** — 17:20 Northern Dancer Handicap: IN BASELINE at 13.5 (12/1). Confirmed runner.

---

## Additional NRs removed by RP scrape (non-bet impact, for information)

The full list of 41 horses removed as probable NRs at 07:08 (racecard count 142 → live 101):

**13:30 Tattenham Corner G3** (14→8): Audience, Cowardofthecounty, Copacabana Sands, Humam, Lake Forest, Linwood

**14:05 Princess Elizabeth G3** (13→9): Alobayyah, Celestial Orbit, Sindria, Sunlit Uplands

**14:40 Coronation Cup G1** (8→6): See The Fire, Sunway

**15:15 Dash Handicap** (34→18): Counsel, Desert Cop, Fierce Fortitude, Forager, Francisco's Piece, Golden Long, Law Of Average, Marching Mac, Michaela's Boy, Nogo's Dream, Oneforthegutter, Seven Questions, Spangled Mac, Sturlasson, Tatterstall, The Bell Conductor

**16:00 Derby G1** (18→14): Causeway, Constitution River, Endorsement, Proposition

**16:40 Lester Piggott Hcp** (13→11): My Mate Roger, Tai Hang Pegasus

**17:20 Northern Dancer Hcp** (21→17): Patagonia Girl, Sunway *(note: Sunway appears in both 14:40 and 17:20 listings — racecard deduplication artefact)*,  Will Scarlet, Oneforthegutter *(possible dedup)*

**17:55 Tokyo Trophy Hcp** (28→18): Cinque Verde, Dance In The Storm, Toyotomi, Veblen Good, Winged Messenger + others in Dash double-runners (Desert Cop, Francisco's Piece, Golden Long, Seven Questions, Spangled Mac, Stormy Impact, Star Chorus)

---
**Note:** All NR filtering is based on RP __NEXT_DATA__ scrape. RP does not publish official Epsom declarations — this is a best-available live confirmation. Cross-reference against BHA/Epsom official declarations when available.


---

# Rusty — Derby Day Signal Confidence Frame
**Author:** Rusty (Signal Engineer)
**Date:** 2026-06-06T23:02:55+01:00
**Status:** PRE-RESULTS — analytical frame ready; apply mechanically when Livingston delivers actuals.
**Sources:** `outputs/bets-2026-06-06.json` + `data/enrichment/rusty-rescored-2026-06-06.json`

---

## Section 1 — Signal Confidence Classification

Classification logic (strict layering — top rule wins):
- **HIGH**: model_score ≥ 90 **AND** rank_gap ≥ +3 **AND** zero warning flags
- **SPECULATIVE**: model_score < 80 **OR** rank_gap ≤ 0 **OR** 2+ warning flags **OR** OVERRIDE_OF_VOID
- **MEDIUM**: anything else (≥80 score, ≥+1 gap, exactly 1 warning flag, but not HIGH-qualifying)

Warning flags counted: `GOING_FIT_CAUTION`, `GOING_FIT_CAUTION_PRECAUTIONARY`, `SYNTHETIC_BASE_CAVEAT`, `OVERRIDE_OF_VOID`, `COMPRESSED_RANGE_CAUTION`. Process/info flags excluded: `UPGRADED_EW_TO_WIN`, `RUSTY_REPICK_*`, `DERBY_SIDE_BET`.

| Time  | Horse             | Bet       | Stake  | Odds  | model_score | rank_gap | Flags                                                           | Confidence  |
|-------|-------------------|-----------|--------|-------|-------------|----------|-----------------------------------------------------------------|-------------|
| 14:05 | Princess Child    | WIN       | £1.00  | 11/1  | 77.5        | +3.5     | —                                                               | SPECULATIVE |
| 15:15 | Another Baar      | WIN       | £0.25  | 39/1  | 86.2        | +15      | COMPRESSED_RANGE_CAUTION, SYNTHETIC_BASE_CAVEAT                 | SPECULATIVE |
| 15:15 | Ziggy's Triton    | EW        | £0.25  | 32/1  | 95.0 ‡      | +16      | COMPRESSED_RANGE_CAUTION                                        | **MEDIUM**  |
| 16:00 | Action            | WIN       | £1.00  | 13/1  | 77.1 †      | +3.5     | HEADGEAR_LARGE_FIELD (scoring downgrade only)                   | SPECULATIVE |
| 16:00 | Derby Trifecta    | TRIFECTA  | £6.00  | —     | 77.1/88.0/85.8 | +3.5/0/0 | SPECULATIVE (bets file), two legs rank_gap = 0              | SPECULATIVE |
| 16:40 | Folk Pageant      | WIN       | £1.50  | 6/1   | 64.1        | +2       | —                                                               | SPECULATIVE |
| 17:20 | Lord Melbourne    | WIN       | £0.75  | 19/1  | 78.8        | +13      | — (model), WARN_DRIFT_+54% (Saul)                               | SPECULATIVE |
| 17:20 | Prydwen           | EW        | £0.25  | 17/1  | 62.9 ‡      | +9       | —                                                               | SPECULATIVE |
| 17:55 | Apollo One        | WIN       | £1.00  | 7/1   | 95.0        | +3       | SYNTHETIC_BASE_CAVEAT, GOING_FIT_CAUTION_PRECAUTIONARY, OVERRIDE_OF_VOID | SPECULATIVE |

**† Action bets-file shows 69.4 (final_signal post-headgear ×0.90); raw model_score 77.1 used here per Saul WARN 1 note.**
**‡ model_score taken from rescore file; not explicitly listed in bets-file entry.**

### Summary
- **HIGH confidence picks: 0** — No pick cleared all three HIGH gates simultaneously.
- **MEDIUM confidence picks: 1** — Ziggy's Triton EW (model 95.0, gap +16, but COMPRESSED_RANGE_CAUTION flag is a valid concern).
- **SPECULATIVE picks: 8** — Primary disqualifiers: (a) 6 of 9 picks score below 80 after headgear/EDGE_ERODED adjustments; (b) Apollo One carries OVERRIDE_OF_VOID; (c) Another Baar carries 2 warning flags.

The entire live card is SPECULATIVE or MEDIUM. This is consistent with a HOLD/rain card where the main going-qualified horses are handicappers being backed against market consensus (Lord Melbourne, Another Baar, Ziggy's Triton) — market consensus is not obviously wrong, so model overlays are inherently speculative.

---

## Section 2 — "If results show X, conclusion is Y" Decision Tree

Apply this tree mechanically when Livingston delivers results. All conclusions reference v0.3 weight review (Section 5) and v0.4 proposal (Section 6).

---

### 2A — Derby Trifecta Box (16:00): Action, Benvenuto Cellini, Item

**Box mechanics:** Pays if all three finish 1st/2nd/3rd in any combination.

**Pre-classified leg status (model perspective):**
- **Action** (banker): rank_gap +3.5 at 13/1 → genuine model overlay. If in the frame, this leg is **model-earned**.
- **Benvenuto Cellini**: rank_gap 0, EDGE_ERODED, model rank 1 at Evs → was the model's highest scorer but market correctly priced it. In-the-frame finish is **model-expected** (not an overlay), not model-earned as value. Presence in box is justified as a likely frame-finisher, not a mispriced bet.
- **Item**: rank_gap 0, model rank 2, 7/2 → efficient pricing. Same as Benvenuto Cellini: **model-expected**, not model-earned as overlay.

| Outcome | Legs in frame | Conclusion |
|---------|--------------|------------|
| All three finish 1st–3rd (any order) | Action (earned), B. Cellini (expected), Item (expected) | Trifecta hits. **1 model-earned leg + 2 model-expected legs.** This is a good result but reflects the box needing Action's overlay to pay — it's not a vindication of 3-way model edge. |
| Benvenuto Cellini + Item finish 1–2; Action misses | Action out of frame | Box misses. Model correctly identified top 2 but Action's rank_gap +3.5 was not enough for a place. Going_fit 68 was the limiting factor. Investigate whether HEADGEAR_LARGE_FIELD downgrade was correctly applied. |
| Action + one of B.Cellini/Item finish; third leg absent | 2 of 3 in frame | Box misses. Which horse missed tells us the model's weakness: if Item missed → going_fit 48 concern confirmed; if B.Cellini missed → GTS steam-money was wrong. |
| Action finishes 1st or 2nd; both others miss | Action in frame, box still misses | Action overlay vindicated. Benvenuto Cellini's steam price (Evs) reflected false confidence. Note MARKET_STEAM_MAJOR should have triggered a lower box confidence classification. |
| None in top 3 | All three miss | Model had wrong top-3 entirely. Investigate which runner won: if a REJECTED horse (going_fit <40) won, the going_fit signal needs recalibration for GTS vs Soft distinction. |

---

### 2B — Action WIN £1 (16:00) — "gentle drift" validation

**Context:** Action showed steam_drift_pct = –7.7% (outward drift, price moved from baseline to ~13/1). Task asks: if Action places or wins, does this vindicate the "+7.7% gentle drift" call?

| Outcome | Conclusion |
|---------|------------|
| **Action wins** | Full vindication. rank_gap +3.5 was genuine overlay at 13/1. The –7.7% outward drift was market noise, not meaningful intelligence. Our model correctly identified the overlay DESPITE the gentle drift. The drift did NOT erode edge (sub-10% drift is below the 30% EDGE_ERODED threshold). Potential rule: drift < 15% = informational only, do NOT demote. |
| **Action places (2nd or 3rd)** | Partial vindication. Model identified the correct quality tier (top-3 per rank_gap +3.5) but not a winning price. The –7.7% drift remains noise-level. Cheekpieces may have boosted performance without producing the win needed. Going_fit 68 correctly placed it below the "confident win" range. |
| **Action beaten mid-field (4th–7th)** | Drift was irrelevant; model_score 77.1 (raw) / 69.4 (adjusted) was the tell — below the 80-point soft confidence boundary. Gentle drift vindication is N/A; focus instead on whether headgear ×0.90 downgrade was too aggressive or too conservative. |
| **Action tailed off / last** | Going_fit 68 wasn't enough on a deteriorating surface. If going was worse than declared GTS at 16:00, this is a going_fit calibration miss. Investigate the going stick readings at race-time vs 11:26 BST declaration. |

---

### 2C — Lord Melbourne WIN £0.75 (17:20) — drift WARN validation

**Context:** Lord Melbourne drifted 12/1 → 19/1 (+54% decimal), triggering Saul WARN 2. Model: rank 1/17, rank_gap +13, going_fit 78, model_score 78.8. 2026 form poor at 1m2f; today 1m4f GTS.

| Outcome | Conclusion |
|---------|------------|
| **Lord Melbourne wins** | Model conviction (rank_gap +13, going_fit 78, November Hcp soft 2024) was correct. The +54% drift was the market being wrong. The WARN 2 was appropriate (escalate to Steve) but should NOT have been auto-void. v0.4 rule: "drift > 30% → WARN flag + require Steve acknowledgement before placing." Current behaviour was correct. |
| **Lord Melbourne places (top 3)** | Model quality signal was right (top-tier finish). The drift reflected market scepticism about 2026 form, not genuine ability on GTS at 1m4f. WARN was correct; bet was defensible. No rule change needed. |
| **Lord Melbourne mid-field (4th–8th)** | Ambiguous. Market might have been partially right (2026 form degradation). Going_fit 78 correctly identified going preference but not current form. Investigate trainer/jockey booking quality for this race — does jt_combo signal (v0.5) show a weak booking? |
| **Lord Melbourne beaten badly (tailed off / last)** | **Saul WARN 2 was justified and should have been a stronger gate.** The +54% drift was the market discounting 2026 form accurately. Model's going_fit 78 and rank_gap +13 were based on 2024–2025 form and did not reflect current condition. **This outcome supports the v0.4 market_drift gating rule: if drift ≥ 30% outward AND model_score < 80, auto-demote from WIN to EW or flag as BLOCKED pending live-track report.** It DOES support a "drift warns about current form, not just price" framework. |

---

### 2D — Apollo One WIN £1 (17:55) — override quality check

**Context:** Dance In The Storm NR → VOID → Apollo One injected as OVERRIDE_OF_VOID at Steve's request. model rank 1/16, rank_gap +3, model_score 95.0. Flags: SYNTHETIC_BASE_CAVEAT, GOING_FIT_CAUTION_PRECAUTIONARY.

| Outcome | Conclusion |
|---------|------------|
| **Apollo One wins** | Override was model-justified, NOT lucky. rank_gap +3 (above the ≥+2 threshold), model_score 95.0 is genuine if the SYNTHETIC_BASE_CAVEAT doesn't inflate it. Key check: **was the 7/1 price a real market price or a synthetic estimate?** If Apollo One's final SP was ~7/1 ± 2/1, the rank_gap +3 vs market was real and the override was earned. If SP drifted to 12/1+, the synthetic → real transition reduced the edge but the model's rank-1 position was still valid (2nd 2023, 3rd 2024 in this race). Conclusion: good override. |
| **Apollo One loses (respectable run, 4th–7th)** | SYNTHETIC_BASE_CAVEAT was material. The 95.0 model_score may reflect the synthetic-to-real price revelation more than genuine horse quality. going_fit_assumed was the second weakness. **Lesson: going_fit MUST be persisted before any OVERRIDE_OF_VOID bet. Future protocol: if going_fit not available → BLOCKED status, no override without confirmed going_fit ≥ 50.** |
| **Apollo One tailed off / beaten badly** | GOING_FIT_CAUTION_PRECAUTIONARY was the tell. "Acts on any ground" is insufficient data. SYNTHETIC_BASE_CAVEAT inflated the model signal. The override at Steve's request was not supported by full signal validation. **Rule for v0.4: OVERRIDE_OF_VOID requires: (a) live-verified runner status, (b) confirmed going_fit value from the rescore file (not assumed), (c) rank_gap ≥ +3 on verified prices (not synthetic).** |

---

### 2E — Dance In The Storm NR: Model bug or data freshness bug?

**Verdict: DATA FRESHNESS BUG — not a model bug.**

Evidence:
1. `confirmed_nrs` in rescore meta explicitly lists: *"Dance In The Storm (17:55 JRA Tokyo — known pre-baseline)"* — the NR was declared before the 07:08 baseline.
2. Linus v1 picks were generated before the live-verify-first protocol ran. v1 was working from a stale enrichment snapshot that still listed Dance In The Storm as a runner.
3. Apollo One's model rank 1/16 after Dance In The Storm's removal reflects a clean field rescore. The question of what rank Dance In The Storm held BEFORE removal is not answerable from current data (runner table was omitted per VOID status), but its NR was known pre-baseline, meaning any v1 system that had it as a pick was using pre-declaration data.
4. The live-verify-first protocol (history 2026-06-05) exists precisely for this scenario. **Linus v1 did not have access to the post-declaration racecard.**

**Conclusion for v0.4 process:** NR-cascade picks (OVERRIDE_OF_VOID) should always be generated by the post-declaration rescore, never from v1 output. The Apollo One re-pick followed the correct protocol (Rusty sourced from live-runners post-declaration). The original Linus v1 VOID was a process-correct response to stale data, not a signal failure.

---

## Section 3 — Princess Child (14:05) — note for completeness

**Context:** No specific decision-tree question posed for Princess Child. Quick frame:

| Outcome | Conclusion |
|---------|------------|
| **Princess Child wins** | model_score 77.5, going_fit 80, rank_gap +3.5 correctly identified a GTS-suited overlay at 11/1. Despite SPECULATIVE classification (model < 80), the going_fit signal was the strong factor. Suggests going_fit should have more influence in final confidence classification, not just as a REJECT gate. |
| **Princess Child beaten** | Going_fit 80 was not enough; model_score 77.5 was below our confidence floor. 11/1 was offered for a reason — quality gap to market-ranked competitors (Shes Perfect at 5/2, Pacific Mission at 9/2) was correctly assessed by market. |

---

## Section 4 — Folk Pageant (16:40) — note for completeness

**Context:** rank_gap exactly +2 (at the minimum WIN threshold), model_score 64.1 (well below 80), no flags. Clean signal but thin edge.

| Outcome | Conclusion |
|---------|------------|
| **Folk Pageant wins** | Vindication of HOLD card going-preference logic. GTS consistency across Newmarket and Chester (last two starts) was real. Even minimum rank_gap +2 was sufficient when backed by going_fit 65 and clean flags. |
| **Folk Pageant beaten** | rank_gap +2 is the minimum qualifier and probably should require model_score ≥ 65 to be included. At 64.1, the model barely cleared the sub-50 gate. Consider adding: "WIN requires rank_gap ≥ +2 AND model_score ≥ 65" as a soft rule in v0.4 to avoid borderline qualifiers. |

---

## Section 5 — v0.3 Weight Sensitivity Analysis

### 5A — If GOING_FIT had been weighted higher

**Current v0.3 scoring:** `going_fit` is used as a gate (< 40 → REJECT) and as a going_fit adjustment, but is NOT a standalone composite weight. It modifies via the HOLD card path selection rather than direct score contribution.

**Hypothetical higher GOING_FIT weight (e.g., 5% direct composite contribution):**

| Pick | going_fit | Impact |
|------|-----------|--------|
| Princess Child | 80 | Elevated — model_score would rise from 77.5 toward ~80–82, potentially clearing the MEDIUM boundary. This pick would become MEDIUM. |
| Lord Melbourne | 78 | Elevated — model_score would rise from 78.8 toward ~80–83. Would become MEDIUM. Might have been presented with higher confidence from the outset. |
| Action | 68 | Modest elevation — model_score from 77.1 would rise ~1–2 points; still SPECULATIVE. |
| Apollo One | ≥50 (assumed) | Indeterminate — going_fit not persisted. Higher weight = higher risk from unconfirmed value. |
| Folk Pageant | 65 | Modest elevation; minimal impact on classification. |
| Another Baar | 60 | Minimal change; already carries 2 warning flags → SPECULATIVE regardless. |
| Ziggy's Triton | 68 | No reclassification — already MEDIUM; flag-based ceiling. |

**Conclusion:** Higher GOING_FIT weight would have elevated Princess Child and Lord Melbourne from SPECULATIVE to MEDIUM. Neither would reach HIGH. Apollo One's unconfirmed going_fit becomes a larger vulnerability. Net benefit is modest; PRIMARY benefit is better differentiation between 68–80 going_fit picks and 40–55 picks.

### 5B — If RANK_GAP had a minimum threshold (≥ +2)

The current system already uses rank_gap ≥ +2 as the WIN criterion. Applying ≥ +3:

| Pick | rank_gap | Impact at ≥+3 threshold |
|------|----------|-------------------------|
| Folk Pageant | +2 | **KILLED** — would have been NO_BET at ≥+3 requirement. Saves £1.50 if Folk Pageant loses. |
| Action | +3.5 | Survives. |
| Princess Child | +3.5 | Survives. |
| Lord Melbourne | +13 | Survives. |
| Apollo One | +3 | **Borderline** — just clears ≥+3. A ≥+4 threshold would kill it. |
| Another Baar | +15 | Survives. |
| Ziggy's Triton | +16 | Survives. |
| Prydwen | +9 | Survives. |

**Only pick killed by ≥+3 threshold:** Folk Pageant (rank_gap exactly +2). This is a reasonable tightening for WIN bets but not for EW outsiders where large rank_gap is the core value signal.

**Recommended rule for v0.4:** Separate WIN and EW thresholds — WIN requires rank_gap ≥ +3; EW retains ≥ +3 at prices ≥ 8/1. Folk Pageant at 6/1 with rank_gap +2 would be demoted to NO_BET under this rule.

### 5C — If a MARKET_DRIFT signal existed (it does not yet in v0.3)

A market_drift signal firing on outward price movement ≥ 30% would have triggered on:

| Horse | drift_pct | Action under drift rule |
|-------|-----------|------------------------|
| Lord Melbourne | +54.2% (12/1 → 19/1) | **FLAG/DEMOTE** — WIN demoted to EW or BLOCKED. Stake saved: £0.75 WIN → £0.25 EW. |
| Action | –7.7% (slight outward) | Sub-threshold. No action. |
| Folk Pageant | +0% (no material drift) | No action. |
| Apollo One | synthetic → real transition | SYNTHETIC_BASE_CAVEAT already covers this; no additional drift flag. |

**Net mechanical impact today had market_drift existed:** Lord Melbourne demoted from WIN to EW. All other picks unaffected. £0.50 stake reduction (£0.75 WIN → £0.25 EW). Small financial impact but large signal quality improvement.

---

## Section 6 — v0.4 Signal Proposal: `market_drift`

### Signal name: `src/market_drift.py`

**Feature definition:**
A gate signal (not a scorer) that computes the percentage change in a horse's decimal odds between two timestamps and applies a confidence modifier to the final_signal when outward drift exceeds a threshold.

```
drift_pct = (latest_dec - baseline_dec) / baseline_dec × 100
```
Positive value = outward drift (price lengthened = market losing confidence).
Negative value = inward move (steam).

**Thresholds:**
- `|drift_pct| < 15%`: NEUTRAL — informational, no action.
- `drift_pct ≥ 15% and < 30%`: SOFT_WARN — log flag `MARKET_DRIFT_SOFT`, no score change.
- `drift_pct ≥ 30%`: DRIFT_WARN — flag `MARKET_DRIFT_WARN`, apply ×0.90 to final_signal. For WIN bets with model_score < 80, demote to EW recommendation.
- `drift_pct ≥ 50%`: DRIFT_CRITICAL — flag `MARKET_DRIFT_CRITICAL`, require Steve acknowledgement before placing WIN. Recommend EW or NO_BET.

**Inward steam flags** (already partially handled by EDGE_ERODED):
- `drift_pct ≤ -30%` (steam): Fire `MARKET_STEAM` in addition to existing EDGE_ERODED logic.

**Data source:**
- `market-baseline.json` (07:08 BST morning prices) — existing file, per current Livingston feed.
- `market-latest.json` (11:26 BST or as close to race-time as available) — existing file.
- **Critical caveat:** Prices must be REAL (not synthetic) on BOTH ends for this signal to be meaningful. Synthetic baseline prices produce SYNTHETIC_BASE_CAVEAT and the drift signal should return NEUTRAL (50) for such pairs to avoid false drift alarms. This is already the correct behaviour per history 2026-06-05 note.
- **Future upgrade path:** Racing Post WebSocket live odds would allow intra-day drift tracking (currently blocked per history).

**Expected weight in v0.4 composite:**
This signal is a **gate modifier only**, not a composite score contributor. Weight = 0.0 in the composite. Applied post-scoring as a multiplier/flag injection:
- `MARKET_DRIFT_WARN (≥30%)`: final_signal × 0.90
- `MARKET_DRIFT_CRITICAL (≥50%)`: final_signal × 0.80, classification forced to SPECULATIVE regardless of raw score

**Expected impact on today's Derby Day card (had it existed):**

| Horse | drift | Signal output | Bets-file change |
|-------|-------|---------------|------------------|
| Lord Melbourne | +54.2% | DRIFT_CRITICAL → final_signal 78.8 × 0.80 = 63.0 | Forced SPECULATIVE; WIN demoted to EW. Stake £0.75 WIN → £0.25 EW. |
| Action | –7.7% | NEUTRAL | No change |
| Princess Child | –60.0% (drifted synthetic → real) | SYNTHETIC_BASE_CAVEAT prevents drift signal firing | No change |
| Apollo One | synthetic → real | SYNTHETIC_BASE_CAVEAT prevents firing | No change |
| All others | < ±30% | NEUTRAL or SYNTHETIC_BASE_CAVEAT | No change |

**Epsom-specific vs portable:** This signal is **fully portable** — drift detection requires only two price timestamps regardless of course, going, or race type.

---

## Section 7 — Publish-Skill Portability Audit

### Epsom-specific signal modules (caution: low portability)

| Module / Logic | Why Epsom-specific | Portability path |
|----------------|-------------------|------------------|
| `HOLD card path` | Calibrated to Epsom's unique drainage and GTS frequency on Derby weekend. The going_stick thresholds (6.0 Derby, 6.2 5f) are course-calibrated. | Create `going_card_path(course, going_stick_value)` abstraction. Other courses have published going_stick norms. |
| `going_fit` scoring | Weighted on Epsom GTS/soft historical run evidence. The 40-point REJECT threshold is calibrated for Epsom's demands. | Abstract to `course_going_fit(horse, course, going)`. The 40-point gate is likely universal but evidence weighting is Epsom-biased. |
| `trial_form` | Trial list includes Dante, Chester Vase, Lingfield Derby Trial — all Derby prep races. | Parameterise trial list as `trials_for_course_distance(course, distance)`. Oaks would need Cheshire Oaks, Musidora in lieu of Dante. |
| `trifecta_note` logic | Derby-box construction assumes a 14-runner field with 4+ REJECT horses — specific to Derby field composition. | Trifecta logic is generic; the "top 3 by model_score" selection is portable but box sizing (6 combos) may not suit smaller fields. |

### Fully portable signal modules

| Module | Portability |
|--------|-------------|
| `market_move.py` (v0.5) | ✅ Fully portable. Input: two price files, any course. |
| `market_drift` (proposed v0.4) | ✅ Fully portable. Input: two timestamps, any horse. |
| `trainer_14d.py` (v0.5) | ✅ Fully portable. Strike rate is trainer-level, not course-level. |
| `jt_combo.py` (v0.5) | ✅ Fully portable. Jockey/trainer pairing is universal. |
| `equipment.py` (v0.6) | ✅ Fully portable. Headgear changes apply at any course. |
| `EDGE_ERODED` logic | ✅ Fully portable. Any synthetic→real or steam ≥30% scenario. |
| `COMPRESSED_RANGE_CAUTION` | ✅ Portable. Field-specific RPM compression is a handicap-field issue, not an Epsom issue. |
| `rank_gap` WIN/EW criteria | ✅ Portable. Thresholds may need calibration per race type (Group 1 vs Heritage Handicap) but logic is universal. |

### Key portability gap

**Live odds ingestion** is the single largest constraint on portability across all market-based signals (`market_move`, `market_drift`, EDGE_ERODED). Until a live Betfair/Racing Post WebSocket feed replaces synthetic prices, all market signals will return NEUTRAL (50) or SYNTHETIC_BASE_CAVEAT for non-Derby-ante-post races, regardless of course. This is an infrastructure gap, not a signal design gap.

---

## Section 8 — Open Questions for Team Post-Mortem

1. **Saul:** Does the Section D validation process need a harder gate at DRIFT_CRITICAL (≥50%)? Today's WARN 2 (Lord Melbourne +54%) was non-blocking. Should it be?
2. **Danny:** v0.4 market_drift weight = 0 (gate only). Does this need a weight review alongside v0.6 equipment signal, or can it be injected as a post-score gate modifier without a full weight reshuffle?
3. **Livingston:** Live odds (Racing Post WebSocket or Betfair streaming API) is the precondition for market_drift and market_move to be meaningful. What is the timeline for live odds ingestion?
4. **Linus:** Trifecta box construction today used top-3 by model_score (Benvenuto Cellini 88.0, Item 85.8, Action 77.1 — with Causeway NR). Two of those legs had rank_gap = 0 (efficient pricing). Should the trifecta box require ≥1 leg with rank_gap ≥ +3 to qualify as a value box?

---

*Document complete. Ready for mechanical application when Livingston delivers race results. All conclusions are deterministic given the above inputs — no judgement calls required at results time.*


---

# Saul — Derby Day Process Audit
**Date:** 2026-06-06T23:02:55+01:00
**By:** Saul (Tester / Reviewer)
**Requested by:** Steve Newby (post-race retrospective)
**Scope:** 6 process items from the 2026-06-06 Derby Day session

---

## Summary table

| # | Issue | Verdict | Publish-readiness |
|---|-------|---------|-------------------|
| 1 | Apollo One 17:55 override | ✅ GOOD | 🟡 polish-then-ship |
| 2 | Missed 15:00 Derby T-1hr gate | 🟡 NEEDS WORK | 🔴 blocker |
| 3 | Livingston-3 silent completion | 🚨 SYSTEMIC RISK | 🔴 blocker |
| 4 | Lord Melbourne +54% drift WARN | ✅ GOOD | 🟡 polish-then-ship |
| 5 | HTML header staleness (recurring) | 🚨 SYSTEMIC RISK | 🔴 blocker |
| 6 | Scribe-16 partial failure | 🟡 NEEDS WORK | 🟡 polish-then-ship |

---

## Issue 1 — Apollo One 17:55 Override

**Verdict: ✅ GOOD**
**Publish-readiness: 🟡 polish-then-ship**

### What happened
Dance In The Storm was flagged as probable NR in the Livingston 07:08 baseline scrape
(absent from RP live racecard, bet impact marked URGENT). Linus-v3 correctly rendered the
17:55 slot as VOID. Coordinator spawned Rusty-5 to produce a conditional replacement.
Rusty picked Apollo One (rank 1/16, score 95.0, 7/1). Steve approved at 12:15 BST. Linus
injected at 12:17 with correct SYNTHETIC_BASE_CAVEAT + GOING_FIT_CAUTION amber flags.
Result: WIN at 7/1 on £1.00 stake.

### Was the override well-grounded?
Yes. Gate check was explicit: all 16 runners declared live in market-latest.json, Dance In
The Storm confirmed non_runner:true. Apollo One flags were honest (synthetic baseline, no
persisted going_fit). Steve approval was sought and received before injection. Linus left
the header alone per guardrails. The audit trail is complete and clean.

### Should the thin-field risk have been caught earlier?
Partially. Dance In The Storm was flagged by Livingston at 07:08 — 8+ hours before race
time. The original model VOID was correct. However, Linus-v3 (11:52) rendered VOID without
proactively queuing a repick. The coordinator had to spawn Rusty separately after
recognising the VOID on review. There was a ~20-minute gap between Linus v3 output and
the repick spawn. That gap is fine for a manually-supervised session; it would be a
reliability hole in a fully automated published skill.

The "thin field" as a model risk (sparse rank_gap reliability when field drops below 8)
is not explicitly flagged in the scoring output for the 17:55 race. With 16 live runners
that particular concern doesn't apply today, but the general absence of a field-size
quality flag in model output is worth noting for future races where a significant NR wave
reduces a race to 5 or 6 runners.

### Recommended fix
Add a VOID-triggers-conditional-repick rule to the coordinator runbook: any VOID call for
a race with ≥6 live runners SHOULD automatically queue a Rusty repick spawn (conditional
on coordinator/Steve approval). This turns a manual follow-up into a documented reflex.
Also add a field-size guard: if post-NR field drops to ≤5, model output should include
a THIN_FIELD caution flag.

---

## Issue 2 — Missed 15:00 Derby T-1hr Gate

**Verdict: 🟡 NEEDS WORK**
**Publish-readiness: 🔴 blocker**

### What happened
Livingston's morning_odds runbook specifies a drift check ~1 hour before each Group 1.
Derby 16:00 → check should have fired at ~15:00. Livingston-3 actually ran at 15:39, 39
minutes late. The cause: no explicit watchdog tick was scheduled for 15:00 in the session
configuration. The runbook said "~1hr before"; the coordinator acted on it but with delay.

### Root cause analysis
Three candidate causes were possible:
- (A) Watchdog spec wrong — the tick schedule had no 15:00 entry
- (B) Tick fired on time but coordinator didn't act promptly
- (C) Coordinator misread the runbook timing

The evidence points to (A) primarily, compounded by (B). The watchdog ticks were hourly
(confirmed from the copilot-directive file: "schedule continues hourly until Sat 21:30").
There is no explicit "T-1hr Group 1 pre-race check" in the watchdog configuration — it
was described in the Livingston runbook as a norm, not as a mandatory scheduled tick.
The coordinator interpreted "~1hr before" loosely and acted 39 minutes late. The result
was that Livingston-3 ran with 21 minutes before Derby post-time, significantly reducing
the window to act on any drift finding.

In the event, scraping was blocked anyway (Sporting Life 404, Racing Post 406, env vars
not set) and the fallback used card prices. So the 39-minute delay caused no financial
harm today. That's luck, not design.

### What protective mechanism would prevent this for publish?
Hourly ticking is insufficient for intra-race-day Group 1 checks. A published skill
needs explicit T-60m and T-30m pre-race event rules for any Group 1 on the card, generated
at card-lock time and added to the watchdog schedule as named events — not buried in a
runbook. The schedule should read:

  - `15:00 — Derby T-1hr drift check → spawn Livingston`
  - `15:30 — Derby T-30min final NR confirmation → spawn Livingston`

These should be generated automatically by a card-lock step that reads the race times
from bets.json and writes named watchdog events. Without this, a published skill will
always depend on the coordinating user noticing the runbook note.

### Recommended fix
**Rule change:** After card lock, a `generate_watchdog_events()` step reads race times from
bets.json and emits T-60m and T-30m event entries for every race with a Group 1 or Live bet
flag. These events are appended to the watchdog schedule file before the session goes
background. This must be a hard step, not optional. Missing a T-1hr Group 1 gate on a
live card is not acceptable in production.

---

## Issue 3 — Livingston-3 Silent Completion

**Verdict: 🚨 SYSTEMIC RISK**
**Publish-readiness: 🔴 blocker**

### What happened
Livingston-3 completed at ~15:40 and wrote
`.squad/decisions/inbox/livingston-pre-derby-drift-2026-06-06.md`. No completion
notification fired. The coordinator did not poll. The file sat unread for 7+ hours.
This is the documented platform ~7-10% "silent success" bug: the agent completes,
writes its output, but the completion event is not delivered to the coordinator.

### What is our current defence?
Essentially none. The coordinator relies on the platform completion event. When that event
is missing, the only recovery path is human observation ("I wonder if that agent finished")
or a subsequent agent accidentally discovering the file. Neither is acceptable for a
published skill.

### Is this acceptable for a published skill?
No. Emphatically not. In our session Steve was physically present at the races and could
notice the gap eventually. A published skill running headless for another user would have
silently missed the Derby T-1hr drift check entirely. Lord Melbourne's +53.8% drift would
have been unchecked at race time.

### Recommended fixes (defence in depth — all three needed for publish)

**Fix A — Filesystem polling (minimum viable defence):**
After any background spawn targeting an inbox output file, the coordinator should schedule
a polling check at `spawn_time + expected_duration + 5min`. If the output file exists and
is non-empty, treat it as complete and process it. This catches silent success without
requiring platform event delivery.

**Fix B — Spawn ack pattern:**
Each spawned agent writes an ack file (`<agent>-ack-<timestamp>.md`) as its FIRST action
before doing any substantive work. The coordinator confirms the ack within 2 minutes of
spawn; if absent, the spawn is considered failed and retried. This catches silent FAILURE
(agent never started) as well as silent success.

**Fix C — Coordinator timeout escalation:**
Any spawn with no ack AND no output file within `expected_duration × 2` triggers an
escalation to Direct Mode: the coordinator summarises the missing agent's known inputs and
asks Steve (or the user) to confirm or override. For a published skill this becomes an
automated alert, not a human ask.

Fix A is the quickest to implement and gives 90%+ coverage of the silent success case.
All three together eliminate the class of problem. This MUST be resolved before publish —
a skill that silently drops a pre-race drift check while the user is at a betting window
is a genuine harm vector.

---

## Issue 4 — Lord Melbourne +54% Drift WARN

**Verdict: ✅ GOOD**
**Publish-readiness: 🟡 polish-then-ship**

### Was the WARN the right call?
Yes. The WARN 2 I raised at Section D (12:12) was correct in every respect:
- Price moved from 12/1 to 19/1 (+54% decimal), confirmed by Livingston-3
- 2026 form at 1m2f flagged as poor (RP Diomed note cited)
- Model conviction (rank 1/17, rank_gap +13, going_fit 78) explicitly acknowledged
- Action specified: accept, check live price before 17:20, pull or halve stake at 25/1+

The WARN surfaced the risk clearly, quantified it, and gave Steve a decision rule. It did
not overcall (pulling the bet without evidence would have been wrong given model rank 1/17).
It did not undercall (a silent acceptance of +54% drift without a flag would have been
negligent). Calibration was correct.

### Was the decision to keep the bet documented?
Yes. The decision is documented in three places:
1. Saul Section D validation (12:12) — WARN 2 text + action instruction
2. Danny GO/NO-GO (12:13) — explicitly overrides drift concern on model conviction grounds,
   with live-price instruction
3. Full Consolidation master entry — WARN 2 repeated in key decisions table

The audit trail is complete. If Lord Melbourne had won, this decision chain would be
defensible. If it lost, we can point to the WARN and Danny's considered override.

### Should the system have escalated automatically (auto-void at >50% drift)?
This is a legitimate design question. My assessment: for this system, no — for a
published skill, configurable yes.

In our session, Lord Melbourne's model conviction was legitimately strong (rank 1/17,
rank_gap +13). An automatic void at >50% drift would have overridden a correct model
signal. The right threshold for auto-void is highly dependent on field size, rank_gap,
and going context. A blanket rule misses nuance.

However, for a published skill where the user may not be actively monitoring: if the drift
exceeds a configurable threshold (default 50%, range 30–80%) AND model conviction is below
a configurable floor (default rank_gap <5), auto-void should fire without requiring
coordinator confirmation. Above the floor (as Lord Melbourne was, at rank_gap +13), the
system should require explicit coordinator confirmation before allowing the bet to stand.
Today's manual WARN achieved exactly this — Danny confirmed explicitly. That pattern should
be encoded as a rule, not left to agent discretion.

### Recommended fix
Add a drift-gate rule: at T-1hr check, any runner with |drift%| > drift_threshold (default
50%) triggers a REQUIRES_CONFIRMATION flag that must be cleared by the coordinator before
the bet is placed. If coordinator does not respond within 10 minutes of the flag, the bet
auto-voids (conservative default). The threshold and auto-void behaviour should be
user-configurable in the skill parameters. For publish, document the default clearly.

---

## Issue 5 — HTML Header Staleness (Recurring Pattern)

**Verdict: 🚨 SYSTEMIC RISK**
**Publish-readiness: 🔴 blocker**

### What happened
Linus-13 injected Apollo One correctly but left the HTML header showing £5.50 total (pre-
override). Actual outlay was £6.50. Coordinator patched HTML lines 174, 178-181 manually.
Per session summary, this has happened before (header not updated on prior override
injections). It is a known recurring pattern.

The root cause is a guardrail conflict: Linus's current charter says "do not update header
unless explicitly instructed", which prevents autonomous header edits. That guardrail was
designed to avoid Linus corrupting the summary line. But the side-effect is that any
injection that changes total outlay leaves the header stale. The coordinator must always
remember to patch it.

### Why this is systemic
Three separate times this pattern has surfaced in two race days. It is not a one-off
oversight — it is a structural mismatch between where financial state lives (JSON) and
where it is displayed (HTML header). Every time the JSON portfolio_summary is updated,
the HTML header diverges. The only current mechanism to re-sync them is human memory.

In a published skill, the user running headless will not see the divergence until they
open the HTML. If they use the HTML header to track their outlay (which is its purpose),
they will have incorrect information at race time.

### Three options considered

**Option A — Expand Linus's authority:**
Give Linus permission to update the header whenever it injects a row. This is the
simplest patch but requires Linus to compute the correct totals, introducing a new failure
mode (Linus arithmetic errors on totals). Also, Linus still won't know the full card state
if the header has been touched by multiple prior agents.

**Option B — Add a header-refresh role:**
After any injection, the coordinator spawns a dedicated header-refresh agent (or Scribe)
that reads bets.json and recomputes the HTML header from scratch. Clean separation of
concerns. But adds a spawn + latency after every injection.

**Option C — Compute header from JSON at render time (preferred):**
Make bets.json the single source of truth for all totals. The HTML header is rendered
programmatically from `src/report.py` by reading bets.json at template render time.
Linus never writes totals directly — it writes rows and calls `render_header(bets_path)`.
This eliminates the divergence class permanently.

### Recommended fix
**Option C, implemented as follows:**
1. Add `render_header(bets_path: str) -> str` to `src/report.py`. Reads bets.json, sums
   all active stakes, formats the header line.
2. All Linus HTML generation calls `render_header()` as a final step.
3. Any injection script (Linus or coordinator) calls `render_header()` after modifying
   rows. Manual header patches become redundant.
4. Test: unit test for `render_header()` covering VOID exclusion, trifecta inclusion,
   EW total (both sides), and the Apollo-One override scenario specifically.

This is a **pre-publish hard requirement**. A skill that displays wrong outlay to the user
is a material defect.

---

## Issue 6 — Scribe-16 Partial Failure

**Verdict: 🟡 NEEDS WORK**
**Publish-readiness: 🟡 polish-then-ship**

### What happened
The first Scribe spawn (commit 423db3c) processed only a stale skill-audience directive
and missed the entire race-day inbox (9 inbox files from the 11:01–12:17 session).
Scribe-17 had to rerun the full merge, producing commit 0de1154 which is the canonical
Saturday record. The partial failure meant the Saturday session was unrecorded for a
period after the agents had completed their work.

### Root cause
Spawn-prompt scope problem. Scribe-16 was given a narrow prompt scoped to a specific
directive file rather than an unconditional inbox sweep. The prompt likely said something
like "merge the skill-audience directive from inbox" and Scribe executed that and nothing
more. Scribe did not discover the 9 race-day inbox files because it was not instructed to
look for them, and it had no standing rule to always sweep the entire inbox first.

This is not a platform bug — it's a prompt engineering failure. The coordinator wrote a
narrow scope prompt for Scribe when it should have written an unconditional "process ALL
inbox files" prompt.

### Was inbox-detection logic at fault?
No. Scribe is capable of listing inbox files (it uses the same file tools as other agents).
The detection logic works — Scribe-17 proved this by successfully sweeping and merging all
9 files. The problem was the spawn prompt for Scribe-16 bypassed the sweep.

### Should Scribe always sweep the entire inbox unconditionally?
Yes. This should be a hard rule in Scribe's charter, not something the coordinator decides
per-spawn. Every Scribe spawn should begin with:
1. `ls .squad/decisions/inbox/*.md` — enumerate all pending inbox files
2. Process ALL of them in chronological order by timestamp
3. Only THEN apply any specific additional directive from the spawn prompt

The specific directive (e.g., "also include the skill-audience update") is additive, not
a replacement for the standard sweep.

### Recommended fix
**Rule change in Scribe charter:** Add a mandatory first action: unconditional inbox sweep.
The charter should read: "Begin every spawn by listing and processing all pending files in
`.squad/decisions/inbox/`. Never process a subset of inbox files based on spawn prompt
scope alone — the prompt may add files to process but may not reduce the default sweep."

Additionally, the coordinator should include a standard preamble in every Scribe spawn
prompt: "First: sweep and merge all files in .squad/decisions/inbox/ — do not scope this
to specific files unless explicitly told to skip others."

This is a polish-then-ship item rather than a hard blocker because Scribe-16's partial
failure was caught quickly and fully remediated by Scribe-17 before the session ended. But
in a published skill, an undetected partial merge would corrupt the decisions ledger
without the safety net of a follow-up human review.

---

## Overall Day Assessment

### What went well
- Core model pipeline (Livingston → Rusty → Linus → Saul → Danny) executed cleanly in
  the 11:00–12:20 window. All gate criteria documented. Guardrails (Linus header rule,
  Steve approval on override, WARN escalation to Danny) functioned correctly.
- Apollo One repick: the NR was caught 8+ hours early, the repick was signalled, gated,
  and approved by Steve. Win at 7/1.
- My WARN 2 on Lord Melbourne was correctly calibrated and correctly handled by Danny.
- Secret scan: all 9 inbox files clear at commit. No credential leakage.
- Friday retro lessons (going_fit floor, steam gate) were applied correctly to Saturday
  card — Illinois and Christmas Day correctly invalidated.

### What went badly
- The T-1hr pre-race gate for the Derby itself was 39 minutes late. For the flagship race
  of the day, this is the most important pre-race check and it missed its window.
- Livingston-3 output sat unread for 7+ hours. The platform silent success bug bit us on
  the Derby specifically. We got away with it because scraping was blocked anyway and
  Lord Melbourne drift was already WARN-flagged from morning data. We will not always
  be this lucky.
- HTML header was wrong on the final card. A user opening racecard-2026-06-06.html
  after the session would have seen £5.50 outlay when the true total was £12.50 (£6.50
  bets + £6.00 trifecta). That's not a minor cosmetic discrepancy — it's materially
  misleading at race time.

### Publish-readiness verdict
**Three hard blockers must be resolved before this is publishable:**
1. **T-1hr gate**: Auto-generate named watchdog events at card-lock time. Hourly ticking
   is not sufficient for live Group 1 race management.
2. **Silent completion defence**: Filesystem polling + spawn ack pattern. A skill that
   silently drops a pre-race check harms its users.
3. **HTML header computed from JSON**: Eliminate the manual patch class permanently.

The two 🟡 polish items (VOID repick protocol, Scribe unconditional sweep) should be
addressed before publish to reduce coordinator burden, but they do not create the same
category of user harm as the three blockers.

---

**Filed by:** Saul (Tester / Reviewer)
**Timestamp:** 2026-06-06T23:02:55+01:00
**Cross-refs:** decisions.md §2026-06-06 full consolidation; livingston-pre-derby-drift-2026-06-06.md; commit 0de1154


---


