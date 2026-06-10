# Skill: live-runner-verification

## Purpose

Verify source-order live declared runners for a configured `{course}`, `{meeting}`, and `{date}` before scoring, betting, report generation, or printing. The goal is to stop stale raw data or stale market files from putting non-runners on a consumer-facing card.

## When to use

- Before any T-60 watchdog gate.
- Before Rusty re-scores after a non-runner or replacement.
- Before Linus renders or edits `outputs\racecard-{course}-{date}.html` or `outputs\report-{course}-{date}.html`.
- Whenever the current market snapshot is older than race-day midnight.
- Whenever the operator has manually swapped a horse.

## Inputs

Resolve paths with `src.course_config.path_for()` or `docs\data-layout.md`.

| Artifact | Epsom legacy example | Non-Epsom example |
|---|---|---|
| Raw racecards | `data\raw\epsom-2026-06-06-racecards.json` | `data\raw\ascot-2026-06-16-racecards.json` |
| Browser-saved source | `C:\path\to\epsom-2026-06-06.html` | `C:\path\to\ascot-2026-06-16.html` |
| Live runners | `data\enrichment\live-runners-2026-06-06.json` | `data\enrichment\live-runners-ascot-2026-06-16.json` |
| Market snapshot | `data\enrichment\market-latest.json` | `data\enrichment\market-latest-ascot.json` |
| Racecard HTML | `outputs\racecard-2026-06-06.html` | `outputs\racecard-ascot-2026-06-16.html` |

Do not use `market-latest*.json` as runner identity truth. It is price context only.

## Source order

Try these sources in order. Stop at the first source that yields a complete runner list for a race; use a second source only to resolve ambiguity.

### 1. Imported raw racecard

Use `race-analysis fetch --from-file` output first. If the operator has a fresher browser save, re-import it before comparing.

```powershell
race-analysis fetch --from-file $saved --course $course --meeting $meeting --date $date
```

### 2. Manual browser verification

Open the relevant racecard page in the browser and verify runner identity from the visible page. Save the page and re-run `fetch --from-file` if the raw card is stale. Do not use deprecated scrape scripts or automated page capture.

### 3. Other public racecard pages

Use manually opened pages or operator-provided exports. Template the query from course/date/time rather than hardcoding a venue.

### 4. Search fallback

Use a web search only when direct pages are blocked or JavaScript-only:

```text
"{course_display}" "{race_name}" "{date}" confirmed runners jockey trainer
```

## Procedure

1. Set scope with `$course`, `$meeting`, and `$date`.
2. Read the raw racecard and current rendered card. List every race that has not yet run.
3. For each remaining race, collect off time, race name, runner count, cloth numbers, horse name, jockey, trainer, and source URL or saved-page evidence.
4. Detect discrepancies: card-only runners, source-only runners, count mismatches, and probable non-runners.
5. Write or update the canonical live-runner file using `source_name` such as `Sporting Life browser save` and the source URL or saved-page reference.
6. Write mismatch notes to `.squad\decisions\inbox\livingston-card-vs-live-{course}-{date}.md`.
7. Hand off re-score, render, or blocked-race action to the relevant owner.

## Rules

- Do not guess runners.
- Do not trust stale market files for runner identity.
- Do not use deprecated `scripts\scrape_*.deprecated.py` files for live capture.
- Do not include races already past.
- If every source fails, mark the race `blocked` and escalate for manual runner paste.
- Prices are optional; runner identity is mandatory.
