# RUNBOOK: From Install to Race Card

**For:** Developers unfamiliar with horse racing or this codebase who need a printable race card by race day.

**Scope:** Epsom Group racing (specifically Ladies Day Fri & Derby Day Sat). Covers the common case, with fallbacks for observed failure modes.

**Last Updated:** 2026-06-08 | **Model Version:** v0.4 | **Venue:** Epsom

---

## 1. Prerequisites

### Required Credentials & Environment Variables

Refer to `.env` in the repository root. Your system must have these variables set:

| Variable | Purpose | Missing = ? |
|----------|---------|-------------|
| `RACING_API_USERNAME` | Public Racing API auth (live runner verification) | Script fails with 401; cannot fetch live declared fields |
| `RACING_API_PASSWORD` | Public Racing API auth (live runner verification) | Script fails with 401; cannot verify horses are actually in the race |

**File Location:** `.env` (git-ignored; you must create or populate this before running scripts)

**Minimum viable setup:**
```bash
# Check environment at session start
python -c "import os; print(f'API user: {os.getenv(\"RACING_API_USERNAME\", \"MISSING\")}'); print(f'API pass: {bool(os.getenv(\"RACING_API_PASSWORD\", \"\"))}')"
```

**Implicit Dependencies:**
- Python 3.12+
- `jinja2` (template rendering; see `requirements.txt`)
- Internet access (HTTP fetches from Racing Post, Sporting Life, BBC Sport)
- File write access to `data/enrichment/` and `outputs/`

---

## 2. The Two-Source Scrape Pattern

Yesterday's audit identified a critical finding: **Racing Post racecard pages return 404/406 intra-day, BUT results pages work post-race**. This runbook documents the pattern and fallbacks discovered.

### 2.1 Live Racecard Sources (T-2h to T+30min per race)

#### Source 1: Racing Post Live Racecard (Preferred)
- **URL pattern:** `https://www.racingpost.com/racecards/17/epsom/{YYYY-MM-DD}`
- **Auth required:** No (public)
- **Content:** SSR HTML with `__NEXT_DATA__` JSON blob; runner names + equipment + form snippets embedded
- **Typical success:** AM (07:00–12:00), may fail mid-day
- **Failure modes:**
  - HTTP 406 on repeated scrapes from same session within 60s
  - HTTP 404 if racecard is withdrawn/cancelled
  - Returns 200 but with 373-byte response (malformed; treat as failed)
- **How to detect silent failure:** Response < 1KB, no `horseName` keys in SSR blob, or parser throws on malformed JSON
- **Mitigation:** Add 60s sleep between baseline→latest calls; use `--no-rp-scrape` flag to skip on subsequent runs

#### Source 2: Sporting Life Racecard (Fallback)
- **URL pattern:** `https://www.sportinglife.com/racing/racecards/{YYYY-MM-DD}/epsom-downs/racecard/{race_id}/{slug}`
- **Auth required:** Yes (SPA shell; public URLs but may require session cookie)
- **Content:** Individual race racecard; runner list, weights, odds, form
- **Typical success:** Morning through race-time
- **Failure modes:**
  - Returns 200 but 373-byte HTML (empty skeleton; race not published yet)
  - Returns 403 (region/IP-based block)
  - JavaScript component errors (race details not populated)
- **How to detect silent failure:** Response < 1KB, no `<tr>` runner rows, no horse names in plain text
- **Mitigation:** Retry with user-agent string; check `data/enrichment/live-runners-YYYY-MM-DD.json` (pre-populated by manual web-search gate)

#### Source 3: Betdata.io (Historical; Often 404)
- **URL pattern:** `https://www.betdata.io/epsom/{YYYY-MM-DD}/{race_name}`
- **Auth required:** No
- **Content:** Odds + form data
- **Typical success:** Low (historically 404 for this venue)
- **Fallback:** Do not rely; skip if Racing Post + Sporting Life both succeed

#### Source 4: BBC Sport Racing (Fallback for verification)
- **URL pattern:** `https://www.bbc.co.uk/sport/horse-racing/epsom/{YYYY-MM-DD}`
- **Auth required:** No
- **Content:** Summary racecard; runner names only (no odds/equipment)
- **Use case:** Verify horse names exist in the race (sanity check)

#### Source 5: At The Races / Sky Sports (Low priority)
- **Auth required:** Yes (paywall/subscription)
- **Recommendation:** Skip for v0.4; documented for completeness

### 2.2 Post-Race Results Sources (T+5min onward)

**Critical Finding:** Results pages work even when racecard pages are blocked intra-day.

#### Source 1: Racing Post Results (Preferred)
- **URL pattern:** `https://www.racingpost.com/results/17/epsom/{YYYY-MM-DD}/{race_id}/`
- **Race ID lookup:** Use race ID from racecard URL (e.g., `920050` for 14:05 Woodcote)
- **Auth required:** No (public)
- **Content:** Finishing order, margins, SP odds, jockey/trainer confirmation
- **Typical success:** Immediate (within 1–2min post-race)
- **Failure modes:** HTTP 404 if race ID mismatch; very rare
- **How to detect silent failure:** Response contains no finish positions or horse names

#### Source 2: Sporting Life Results (Fallback)
- **URL pattern:** Individual race result pages (varies by race_id)
- **Auth required:** Yes
- **Content:** Finishing order, form updates
- **Typical success:** 5–10min post-race
- **Failure modes:** JavaScript component errors (results not parsed); treats 200 as success even if data is missing
- **Mitigation:** Cross-check against Racing Post results before publishing

### 2.3 Decision Tree: Which Source to Use?

```
[Fetch live racecard]
  ├─ Try Racing Post first (fastest)
  │  └─ If 406 or >60s elapsed since last RP call
  │     └─ Wait 60s, retry OR use --no-rp-scrape flag
  │
  ├─ If RP returns < 1KB or no horse names
  │  └─ Try Sporting Life (fallback)
  │     └─ If both fail
  │        └─ Stop; request manual intervention (see §4)
  │
  ├─ Cross-check against live-runners-YYYY-MM-DD.json
  │  └─ If live-runners file does not exist
  │     └─ Use web-search to build it (contact Steve for web access)
  │
  [After race runs]
  └─ Fetch post-race results from Racing Post (works reliably)
```

---

## 3. Race-Day Timeline

For exact copy-paste commands, keep the [Quick Reference Card](#8-quick-reference-card) open during the operator window.

### T-24h (Evening before race day)

- **Full overnight refresh**
  - Run `scripts/refresh_friday.py` (Ladies Day only) or equivalent for Saturday
  - Captures: declarations, runner list, trainer/jockey assignments, equipment flags
  - Output: `data/raw/epsom-YYYY-MM-DD-racecards.json` + enrichment files
  - If RP is blocked: use manual declarations list (contact Steve or Sporting Life)

### T-12h (Overnight / Early morning)

- **NR (non-runner) sweep**
  - Cross-check `live-runners-YYYY-MM-DD.json` against racecard to identify withdrawals
  - Flag any horse in racecard but NOT in live declared list as **probable NR**
  - Consequence: NR horses kill multi-race bets involving them (doubles, trebles)
  - Record: `.squad/decisions/inbox/livingston-*-baseline-NRs.md`

### T-2h (Morning: typically 07:00–09:00 BST)

- **Full odds refresh; baseline lock**
  - Run `scripts/morning_odds.py --mode baseline --date YYYY-MM-DD`
  - Captures all runner prices at this snapshot time
  - Output: `data/enrichment/market-baseline.json`
  - Use this as your reference for "yesterday's price" when comparing pre-race moves
  - **Critical:** If RP scrape fails (406), add 60s delay and retry, OR use `--no-rp-scrape` on next latest call

### T-60min before first race

- **T-60 watchdog gate**
  - Run `python scripts/t60_watchdog.py --date YYYY-MM-DD`
  - Confirms required racecards, live runners, Sporting Life/Racing Post/going enrichment, scores, bets, report, racecard, and slip are present and fresh
  - Cross-checks that bets/card horses are live, bets total matches the rendered header/slip, and `scripts/check_env.py` passes
  - **Exit handling:** `0` = clear; `1` = review stale artifacts before proceeding; `2` = **DO NOT RUN PIPELINE** until missing/inconsistent artifacts are fixed
  - `scripts/refresh_friday.py` invokes this as its first T-60 step and aborts on any non-zero result

### T-1h per Group 1 race (1h before race off)

- **Drift gate**
  - Run `scripts/morning_odds.py --mode latest --date YYYY-MM-DD`
  - Captures current prices; market_move signal compares to baseline
  - Look for **steam** (backed heavily → price shortens) or **drift** (uncertain → price lengthens)
  - **Note:** Yesterday's prices may be SYNTHETIC (v0.4 uses pre-race 2026-06-02 estimates if live odds unavailable)
  - **Consequence of skipping:** You miss live market signals; bets go to post on yesterday's price estimates

### T-30min per Group 1 race

- **NR final check**
  - Verify any horses marked NR earlier are still unavailable
  - Update `live-runners-YYYY-MM-DD.json` if new NRs declared post-baseline

### Post-race (+5min onward)

- **Results capture**
  - Fetch finishing order from Racing Post results page
  - Cross-check against Sporting Life if discrepancies
  - Record outcomes to settlement log (used for P&L audit)
  - Typical accuracy: 99.5% from RP; rare discrepancies on margins/weights

### Evening (~21:00 BST)

- **Archive snapshot**
  - Run `scripts/morning_odds.py --mode archive --date YYYY-MM-DD`
  - Snapshots `market-baseline.json` + `market-latest.json` to `data/enrichment/archive/`
  - Preserves day's data before next day overwrites files

---

## 4. Manual Live-Odds Fallback

When every automated source fails (Example: yesterday 15:39, RP blocked + Sporting Life returned 373-byte response), use this procedure.

If the scheduled `scripts/refresh_friday.py` did not run, invoke the T-60 gate directly before editing manual prices:

```bash
python scripts/t60_watchdog.py --date $(date +%F)
```

This writes `outputs/t60-status-YYYY-MM-DD.json` and fails loud on missing/stale artifacts before manual fallback work begins.

### Step 1: Capture Prices Manually

Open your bookmaker terminal or visit Sky Bet / Betfair / BetVictor web page. Write down the current decimal odds for each horse you are tracking. Example:

```
Item (Derby)          3.25
Kinswoman (Coronation) 24.0
Allegresse (Coronation) 9.0
```

### Step 2: Format as JSON

Create or edit `data/enrichment/market-latest.json` manually. It must match this schema:

```json
{
  "fetched_at": "2026-06-06T14:30:00+01:00",
  "source": "manual",
  "venue": "Epsom",
  "date": "2026-06-06",
  "races": [
    {
      "race_id": "16:00",
      "race_name": "Derby",
      "runners": [
        {
          "horse_name": "Item",
          "decimal_price": 3.25
        },
        {
          "horse_name": "Kinswoman",
          "decimal_price": 24.0
        }
      ]
    }
  ]
}
```

**Key fields:**
- `fetched_at`: ISO 8601 timestamp (your current time, with +01:00 for BST)
- `source`: Always "manual" for this workflow
- `horse_name`: Must exactly match the name in `market-baseline.json` (case-insensitive, but keep spelling consistent)
- `decimal_price`: Float (e.g., 3.25 for 13/5, not fractional odds)

### Step 3: Trigger Rescore (Market Move Only)

Don't re-run the full pipeline. Instead, re-run the market_move scoring step:

```bash
python -m src.scoring --mode latest --date 2026-06-06
```

This compares your manual prices in `market-latest.json` against the baseline from this morning, computing drift signals without fetching new data.

### Step 4: Verify Output

Check `outputs/race-card-YYYY-MM-DD.html` for the latest scores and drift indicators. The report should show:
- Horses with **steam** (price shorter than baseline) in green
- Horses with **drift** (price longer than baseline) in red
- Horses with no move (within ±1.5%) in neutral

**Do NOT publish if:**
- Any horse name failed to match (check the error log)
- More than 3 horses have missing prices (indicates incomplete manual capture)
- Any price seems far outside normal market range (e.g., 100.0 for a favorite)

---

## 5. Sanity Checks Before Betting

Run these checks on the race card before publishing it to Steve.

### Check 1: Drift vs Baseline

```bash
# Inspect market move signals
python -c "
import json
with open('data/enrichment/market-baseline.json') as f:
    baseline = json.load(f)
with open('data/enrichment/market-latest.json') as f:
    latest = json.load(f)
print(f'Baseline runners: {sum(len(r[\"runners\"]) for r in baseline[\"races\"])}')
print(f'Latest runners: {sum(len(r[\"runners\"]) for r in latest[\"races\"])}')
"
```

**Expected:** Same runner count (±10%). If latest is much smaller, RP may have blocked; revert to manual entry.

### Check 2: NR List Cross-Ref

```bash
# Verify all NRs from this morning are still accurate
python -c "
import json
with open('data/enrichment/live-runners-2026-06-06.json') as f:
    live = json.load(f)
print('Probable NRs:', [h for h in live.get('non_runners', [])])
"
```

**Expected:** NRs list should match what you saw at 07:00 baseline. If a new NR appears mid-day, update `live-runners-YYYY-MM-DD.json` and re-run scoring.

### Check 3: Header Total vs JSON Total

```bash
# Verify the HTML header shows the same number of runners as JSON
grep -o "Epsom .* [0-9]* runners" outputs/race-card-2026-06-06.html
python -c "
import json
with open('data/enrichment/market-latest.json') as f:
    races = json.load(f)['races']
total = sum(len(r['runners']) for r in races)
print(f'JSON total: {total} runners')
"
```

**Expected:** Header and JSON match within ±1. If mismatch >5, re-run rendering step.

### Check 4: Trifecta Box Leg Validation

If you're betting exotic multiples (trebles, trifecta boxes):

```bash
# Verify each leg is a valid runner in its race
for horse in "Item" "Kinswoman" "Allegresse"; do
  python -c "
import json
with open('data/enrichment/market-latest.json') as f:
    data = json.load(f)
for race in data['races']:
  if any(r['horse_name'] == '$horse' for r in race['runners']):
    print(f'✓ $horse in race {race[\"race_id\"]}')
  "
done
```

**Expected:** All horses in your multi-race bet appear in their respective races. If any is missing, the bet is invalid.

---

## 6. Common Failure Modes — Field Guide

### Symptom: "HTTP 406 from Racing Post"

**Diagnosis:**
```bash
# Check the error message
tail -20 /var/log/morning_odds.log  # or check script output directly
```

**Root Cause:** Consecutive calls to Racing Post within 60s trigger rate-limiting.

**Fix:**
1. Wait 60 seconds
2. Re-run with `--no-rp-scrape` flag: `python scripts/morning_odds.py --mode latest --date 2026-06-06 --no-rp-scrape`
3. If that fails, fall back to manual entry (see §4)

---

### Symptom: "373-byte response from Sporting Life"

**Diagnosis:**
```bash
# Check actual response size
curl -I https://www.sportinglife.com/racing/racecards/2026-06-06/epsom-downs/racecard/920050/woodcote
```

**Root Cause:** Race racecard not yet published or returning skeleton HTML only.

**Fix:**
1. Verify the date and race_id are correct
2. Wait 30min (race declaration may not yet be live)
3. Use manual web-search or BBC Sport (see §2.1, Source 4)
4. Fall back to manual entry if all else fails

---

### Symptom: "Environment variable not set; API auth fails"

**Diagnosis:**
```bash
echo "Username: $RACING_API_USERNAME"
echo "Password: $RACING_API_PASSWORD"
```

**Root Cause:** `.env` not loaded, or variables not exported.

**Fix:**
1. Verify `.env` exists in repo root with `RACING_API_USERNAME` and `RACING_API_PASSWORD` set
2. Source it: `source .env` (or set in your shell session)
3. Re-run the script
4. On Windows: use `.env` file in PowerShell; environment variables must be set in system or session scope

---

### Symptom: "Stale market-latest.json (>4 hrs old)"

**Diagnosis:**
```bash
ls -l data/enrichment/market-latest.json
```

**Root Cause:** Latest mode hasn't been run for >4 hours; prices are from yesterday.

**Fix:**
1. Immediately run `python scripts/morning_odds.py --mode latest --date YYYY-MM-DD`
2. Check the file timestamp and ensure `fetched_at` in JSON is recent (within last 60min)
3. If RP is blocked, use manual entry

---

### Symptom: "HTML header shows stale total"

**Diagnosis:**
```bash
grep "runners" outputs/race-card-2026-06-06.html | head -5
```

**Root Cause:** Header was computed before latest odds refresh. Template caches the value.

**Fix:**
1. Delete the HTML: `rm outputs/race-card-*.html`
2. Re-run rendering: `python src/racecard.py --date 2026-06-06`
3. This forces a fresh read of `market-latest.json`

---

### Symptom: "Horses appear in racecard but not in live-runners file"

**Diagnosis:**
```bash
python -c "
import json
with open('data/raw/epsom-2026-06-06-racecards.json') as f:
    racecard = json.load(f)
with open('data/enrichment/live-runners-2026-06-06.json') as f:
    live = json.load(f)
racecard_horses = set(h for r in racecard['races'] for h in [x['horse_name'] for x in r.get('runners', [])])
live_horses = set(live.get('runners', []))
print('In racecard but not live:', racecard_horses - live_horses)
"
```

**Root Cause:** Probable NR not yet confirmed; racecard may predate final declarations.

**Fix:**
1. Update `live-runners-YYYY-MM-DD.json` with current declarations (via RP or manual web-search)
2. Re-run scoring to apply NR filters
3. Confirm with Steve that these horses are indeed withdrawn

---

## 7. Glossary

**Betting Terms (for racing unfamiliar devs):**

- **WIN** — Bet that the horse finishes 1st. Fixed odds (e.g., 3.0 decimal = £3.00 payout per £1 staked if it wins).
- **EW** — "Each Way." Two separate bets: (1) WIN (horse finishes 1st), (2) PLACE (horse finishes 1st, 2nd, or 3rd). Typical place odds = 1/5 of win odds.
- **Place** — Horse finishes in the top 3 (varies by race type; Group 1 = top 3, handicaps = top 4–5).
- **Decimal odds** — 3.0 = £3.00 return per £1 staked (includes stake). Fractional equivalent: 2/1 (two-to-one).
- **SP** (Starting Price) — Official odds at race-start time. Used for settlement.
- **NR** (Non-runner) — Horse withdrawn from race before start. Bets on that horse lose; multi-race bets involving the NR are void.
- **VOID** — Bet cancelled (no payout, stake returned). Example: horse is NR or race is abandoned.

**Signal Terms:**

- **Drift** — Price lengthens (horse becomes less favored). Example: 5.0 → 8.0 = drift. Often indicates market uncertainty or late withdrawal.
- **Steam** — Price shortens (horse backed heavily). Example: 5.0 → 3.0 = steam. Often indicates informed backing or system success.
- **Baseline** — Reference price at 07:00 AM (locked in before most market movement).
- **Latest** — Current price snapshot (compared to baseline to detect drift/steam).
- **Market move** — Change from baseline to latest. Positive = price shortened (steam); negative = price lengthened (drift).

**Data Terms:**

- **Enrichment file** — JSON file in `data/enrichment/` containing horses, prices, form data, equipment changes, trainer stats. These augment the raw racecard.
- **Model score** — 0–100 confidence rating for each horse (0 = certain loser, 100 = certain winner). Combines 15+ signals (trial form, going fit, recent form, etc.).
- **Rank gap** — Difference between consecutive horse scores. Large gaps = model has high conviction; small gaps = model uncertain.
- **Confidence tier** — Grouping of horses by score range. High tier = model strong opinion; low tier = model uncertain.
- **Trifecta box** — Multi-race bet on 3 runners across 3 different races (all legs must be correct to win). Stake multiplied by number of possible combinations.
- **Exacta** — UK term sometimes used for 2-race double; other contexts (US) = 2-horse finish order bet.

---

## 8. Quick Reference Card

**Keep this on screen during race day:**

```
═══════════════════════════════════════════════════════════════
RACE-DAY QUICK START (Saturday Derby Day 2026-06-06)
═══════════════════════════════════════════════════════════════

PRE-RACE CHECKLIST (Start T-2h, ~07:00 BST)
───────────────────────────────────────────
☐ Check .env has RACING_API_USERNAME + RACING_API_PASSWORD set
☐ Run: python scripts/morning_odds.py --mode baseline --date 2026-06-06
☐ Inspect: data/enrichment/market-baseline.json (39KB ≈ right size)
☐ Check: data/enrichment/live-runners-2026-06-06.json for NRs
☐ T-60 manifest check: python scripts/t60_watchdog.py --date $(date +%F) — fail-loud on any missing/stale artifact

T-1H BEFORE EACH GROUP 1 RACE
─────────────────────────────
☐ Run: python scripts/morning_odds.py --mode latest --date 2026-06-06
☐ Check output for HTTP errors (406 → wait 60s, retry with --no-rp-scrape)
☐ Inspect: outputs/race-card-2026-06-06.html for drift signals (red = drift, green = steam)
☐ Verify NR status hasn't changed since 07:00

FAILURE: RP BLOCKED (HTTP 406)
──────────────────────────────
1. Wait 60 seconds
2. Retry: python scripts/morning_odds.py --mode latest --date 2026-06-06 --no-rp-scrape
3. Still failing? → Fall back to manual entry (see RUNBOOK §4)

FAILURE: ALL SOURCES DOWN
─────────────────────────
1. Open bookmaker app / Sky Bet / Betfair
2. Write down decimal odds for your horses
3. Edit data/enrichment/market-latest.json manually (see RUNBOOK §4, Step 2)
4. Re-run: python -m src.scoring --mode latest --date 2026-06-06

SANITY CHECKS BEFORE PUBLISHING
────────────────────────────────
✓ Baseline runner count ≈ Latest count (±10%)
✓ All NRs from 07:00 baseline still in live-runners file
✓ HTML header total matches JSON total (within ±1)
✓ All horses in multi-race bets appear in their respective races

AFTER EACH RACE FINISHES
────────────────────────
1. Results auto-fetch from Racing Post (happens in background)
2. Manual check: Verify finishing order matches settlement sheet
3. Update P&L log (for Steve's audit)

END OF RACE DAY (~21:00 BST)
───────────────────────────
Archive: python scripts/morning_odds.py --mode archive --date 2026-06-06

═══════════════════════════════════════════════════════════════
COMMON COMMANDS (Copypaste-ready)
═════════════════════════════════

# Check environment is loaded
python -c "import os; print('API ready:', bool(os.getenv('RACING_API_USERNAME')))"

# Baseline capture
python scripts/morning_odds.py --mode baseline --date 2026-06-06

# T-60 manifest check; fail-loud on any missing/stale artifact
python scripts/t60_watchdog.py --date $(date +%F)

# Latest prices (with auto-60s-retry for RP 406)
python scripts/morning_odds.py --mode latest --date 2026-06-06 --no-rp-scrape

# Manual CSV override (if using pre-filled prices)
python scripts/morning_odds.py --mode baseline --date 2026-06-06 --prices overrides.csv

# Render HTML race card
python src/racecard.py --date 2026-06-06

# Archive snapshot
python scripts/morning_odds.py --mode archive --date 2026-06-06

═══════════════════════════════════════════════════════════════
SUPPORT
═══════════════════════════════════════════════════════════════
Check full RUNBOOK.md for detailed troubleshooting.
Questions? See .squad/agents/livingston/charter.md (Livingston's role).
Historical context? See .squad/agents/livingston/history.md (Derby failures logged).
```

---

## Appendix: Troubleshooting Decision Tree

```
Does your race card look right?
├─ YES
│  └─ ✅ Proceed to betting
│
└─ NO (missing horses, wrong prices, or stale data)
   ├─ Are all horses from your portfolio present?
   │  ├─ NO (horse is missing)
   │  │  └─ Is it marked as NR in live-runners file?
   │  │     ├─ YES → Bet is void on that horse
   │  │     └─ NO → Probable data gap; manually verify on RP
   │  │
   │  └─ YES (all present)
   │     └─ Proceed to next check
   │
   ├─ Are the prices recent (<60min old)?
   │  ├─ NO (>60min old)
   │  │  └─ Run latest mode immediately
   │  │
   │  └─ YES (recent)
   │     └─ Proceed to next check
   │
   ├─ Does the header total match JSON total?
   │  ├─ NO (mismatch)
   │  │  └─ Delete outputs/race-card-*.html, re-render
   │  │
   │  └─ YES (match)
   │     └─ ✅ Proceed to betting
   │
   └─ Still broken? Check §6 Common Failure Modes for your specific error
```

---

**Version:** v0.4 | **Last audit:** 2026-06-07 | **Contact:** Steve (project lead)
