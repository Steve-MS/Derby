# Skill: artifact-watchdog

## Purpose

Build or operate a pre-pipeline artifact watchdog that fails loud when race-day inputs, derived outputs, or stake totals are missing, stale, or inconsistent.

## When to use

- Before a race-day scoring/rendering pipeline starts at a fixed deadline gate
- When silent scraper failures need to become explicit operator blockers
- When generated reports/cards/slips must be checked against source-of-truth JSON

## Pattern

1. **Discover source artifacts instead of hardcoding courses.** Use filename patterns such as `data/raw/*-{date}-racecards.json` and parse the course prefix.
2. **Apply artifact-specific freshness windows.** Raw declarations can be older than live-runner checks; live identity and bookmaker enrichments need tighter windows.
3. **Check dependency ordering.** Enrichment precedes scores; scores precede reports; bets precede rendered cards; slips mirror bets.
4. **Promote suspicious small files to hard failures.** Known SPA-shell or auth-failure outputs should be size-gated, not merely parsed.
5. **Cross-check domain invariants.** Active bets must exist in the raw racecard for the same race; no active bet/card horse can be NR/VOID in live-runner data; rendered totals must match computed stake totals.
6. **Emit both human and machine output.** Console table for operators, JSON manifest for downstream automation.

## Exit-code contract

- `0` — all checks green; proceed
- `1` — stale/warning only; operator review required
- `2` — missing or inconsistent artifact; do not run pipeline

## Implementation notes

- Keep the script idempotent: checking should not mutate source artifacts.
- Reuse existing validators such as `scripts/check_env.py` rather than duplicating credential rules.
- Tests should run against isolated fixture roots so live race data is never touched.
