# Decisions

Append-only ledger of team decisions. Scribe merges entries from `decisions/inbox/`.

---

### 2026-06-03: Team hired
**By:** Steve (via Copilot)
**What:** Cast a 5-agent crew (Danny, Livingston, Rusty, Linus, Saul) + Scribe + Ralph to take over race-analysis work for Epsom Derby weekend.
**Why:** Project had grown to 227 tests, v0.3 scoring weights, and a backlog of 5 new signals to ship before Saturday 6 Jun 2026. Squad enables parallel work and decision memory across sessions.

### 2026-06-03: Existing model state at squad hire (v0.3)
**By:** Steve (via Copilot)
**What:** Scoring weights sum to 1.0 with these contributions: class_rating 0.2568, recent_form 0.1468, trainer_form 0.0733, jockey 0.0733, course_distance 0.0733, going 0.0367, draw_bias 0.0571, class_move 0.0367, going_fit 0.1295, pace 0.0665, sire_stamina 0.0500. All 227 tests passing. Last shipped commit: 5a1770e (factors 3 & 4 — C&D form badges + sire stamina).
**Why:** Day-1 baseline for new agents — they need to know what's already in the model before adding signals.

### 2026-06-03: Anti-fabrication rule for new signals
**By:** Steve (via Copilot)
**What:** Any new signal must return a neutral value (50) when data is missing or unknown — never invent data to fill gaps. Sire stamina established the pattern: gated to 10f+, unknown horse → 50, unknown sire → 50.
**Why:** Steve's bets are real money. Fabricated data → bad predictions → losing money. Neutral 50 lets the signal sit quiet when it has nothing to say.

### 2026-06-03: Backlog — 5 signals to ship before Saturday
**By:** Steve (via Copilot)
**What:** Priority order: (1) Trial form (Dante/Chester Vase/Musidora/Cheshire Oaks results), (2) Market move signal (Saturday morning odds-refresh diff), (3) Trainer 14-day strike rate, (4) Jockey/trainer combo bonus, (5) Equipment changes & wind ops from RP notes.
**Why:** Trial form is the single highest-leverage Derby signal — winners of the Dante/Chester Vase have a documented edge. Market moves protect against backing a drifter. Others are incremental.
