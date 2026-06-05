# Linus — History Archive (2026-06-03–2026-06-05 early)

## Archived Summary (2026-06-03–12:05 2026-06-05)

**v0.5 anti-fab hardening patch (2026-06-03):** Added None-input guard to `market_move_signal`, `trainer_14d_signal`, `jt_combo_signal` after Saul's review rejection. All 326 pytest passed post-hardening.

**Friday Oaks data gap (2026-06-05 09:50):** On Message (Ralph Beckett trainer, ~25/1) declared but absent from racecard JSON feed — no score possible. Flagged in HTML injection.

**Ladies Day footnote injection (2026-06-05 09:50–12:05):**
- Amber warnings: On Message late-entry, Belinus withdrawal (refund due on WIN £5 @ 3.5), Sugar Island market steam (34.0 → 17–23).
- Established surgical injection pattern: HTML edits only, no regeneration if Steve has reviewed picks.
- Pattern reusable: race-day warnings live in amber boxes between .race-header and .runners-section.

**Pass-rationale injection (2026-06-05 early):**
- Added 4-race pass explanations (Naana's Shadow, Linwood, Amelia Earhart, Mister Winston).
- Pattern: name the gate (confidence threshold, edge %, why missed).
- Applied to both 1-pager (table rows with `row-rationale row-rationale-pass`) and long report (`<p class="pass-rationale">`).

**Per-race outsider picks (2026-06-05 early):**
- Added 6 EW outsiders × £0.25 + 1 "no outsider" (Diomed G3 field tight).
- Criteria: ≥10/1 with ≥1 positive signal (market support, shortest long-shot, model rank discrepancy).
- Injection sites: 1-pager rows immediately after rationale rows; long report `<div class="outsider-pick">` after `<div class="race-bets">`.
- Stake accounting: £3.00 added, day total £11.61.

**Midday refresh Option B (2026-06-05 12:05):**
- No material price moves (0% on all staked horses), no new non-runners.
- Used surgical timestamp-only edit (no data regeneration), preserving all in-day annotations.
- Timestamps updated on both 1-pager and report (9 stale-price tags retained).

**Learnings archived:**
1. Dual-artifact update pattern: every in-day change must apply to BOTH 1-pager (table) and long report (card layout) independently.
2. Midday regen decision tree: Option B (timestamp-only) if no price moves >20%, no new runners, prices remain stale; Option A (surgical port) only if underlying scored data changes materially.
3. Late-entry, withdrawal, market-steam footnotes are cosmetic-only surgical HTML edits — never touch scored data.
4. Outsider picks always justify their price tier with a clear single-signal rationale (market-backed, model-rank discrepancy, field context).

---

## Early project context (2026-06-03 seeded)

- Python 3.12 race toolkit, repo Steve-MS/Derby, commit 5a1770e.
- Owns `src/report.py` (HTML generation) and `src/betting.py` (betting recommendations).
- Steve's standing rules: £100/day outlay, one A4 card/day, outsider required for Derby, accumulator suggestion/day.
- `SIGNAL_LABELS` dict at `src/report.py` lines ~44-56 (update when Rusty ships signals).
