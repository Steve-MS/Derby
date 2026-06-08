# race-analysis

Python 3.12 race-prediction toolkit for Epsom 2026 — Ladies Day + Derby.

Scoring model v0.4 · 16 signals · sum 1.0.

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/Steve-MS/Derby.git
cd race-analysis

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt
pip install -e ".[dev]"         # dev extras (pytest)

# 4. Set up credentials — see section below
```

---

## Getting Started — Credentials

Several data sources require authentication.  The toolkit reads credentials
from environment variables so that no secrets are ever committed to the repo.

### Step 1 — Copy the template

```bash
copy .env.example .env          # Windows
# cp .env.example .env          # Mac/Linux
```

`.env` is in `.gitignore` and will never be committed.

### Step 2 — Fill in real values

Open `.env` in a text editor and replace every `<placeholder>` token:

| Variable | Required | Where to get it |
|---|---|---|
| `SPORTINGLIFE_USER` | ✅ Required | Free account at [sportinglife.com/racing](https://www.sportinglife.com/racing) |
| `SPORTINGLIFE_PASS` | ✅ Required | Same Sporting Life account |
| `ATR_COOKIE_FILE` | Optional | [attheraces.com](https://www.attheraces.com) — log in, export session cookies with [Cookie-Editor](https://cookie-editor.com/) browser extension. Defaults to `.cookies/attheraces.txt` |
| `RACING_API_KEY` | Optional (future) | [api.theracingapi.com](https://api.theracingapi.com) — reserved for v0.5+ live-price ingestion |

> **Why Sporting Life?**  
> The Sporting Life scraper silently returned a 373-byte JavaScript SPA shell on
> Derby Day 2026-06-06 because the credentials were not set.  That cost us live
> odds for the entire card.  `SPORTINGLIFE_USER` / `SPORTINGLIFE_PASS` are now
> validated at startup before any network call is made.

### Step 3 — Verify

```bash
python scripts/check_env.py
```

Expected output on success:

```
Checking race-analysis environment …
✅  Environment OK (2 required vars set, 1 optional)
```

If any required variable is missing or still a placeholder, the script exits
with code 1 and tells you exactly which variable to fix and where to get it.

### Step 4 — Run

```bash
# Friday morning odds refresh
python scripts/refresh_friday.py

# Manual odds snapshot
python scripts/morning_odds.py --mode baseline --date 2026-06-05
```

Both scripts call `check_env.py` automatically at startup.

---

## Project layout

```
race-analysis/
├── src/              Python package — scoring, betting, reporting, signals
├── scripts/          Race-day runner scripts (refresh_friday, morning_odds …)
├── tests/            pytest test suite (227+ tests)
├── data/
│   ├── raw/          Racecard JSON files (one per meeting date)
│   └── enrichment/   Enrichment data — equipment, market snapshots, results
├── outputs/          Generated HTML reports and betting slips
├── spec/             Architecture specs and scoring model docs
└── .squad/           Team agent config (squad leads, decisions ledger)
```

---

## Usage

```bash
# Check data is present for a date
python -m src.cli fetch --date 2026-06-05

# Score a meeting
python -m src.cli score --date 2026-06-05

# Generate predictions (default bankroll £200)
python -m src.cli predict --date 2026-06-05 --bankroll 200

# Generate HTML report
python -m src.cli report --date 2026-06-05

# Generate printable betting slip (£100 outlay cap)
python -m src.cli card --date 2026-06-05 --outlay 100
```

---

## Running tests

```bash
pytest tests/ -v
```

---

## Scoring model

Current version: **v0.4**.  Weights sum exactly to 1.0000.  16 signals
covering class, form, going, pace, trainer/jockey, equipment, market move,
and sire stamina.  See `spec/scoring-model-v0.1.md` and the decisions ledger
at `.squad/decisions.md` for weight history and design rationale.

---

## Anti-fabrication rule

When data is missing for any signal, that signal returns **50 (neutral)** —
it does not invent a score.  The model abstains rather than fabricates.
