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
| Live runners | `data\enrichment\live-runners-2026-06-06.json` | `data\enrichment\live-runners-ascot-2026-06-16.json` |
| Market snapshot | `data\enrichment\market-latest.json` | `data\enrichment\market-latest-ascot.json` |
| Racecard HTML | `outputs\racecard-2026-06-06.html` | `outputs\racecard-ascot-2026-06-16.html` |

Do not use `market-latest*.json` as runner identity truth. It is price context only.

## Source order

Try these sources in order. Stop at the first source that yields a complete runner list for a race; use a second source only to resolve ambiguity.

### 1. Sporting Life

```text
https://www.sportinglife.com/racing/racecards/{date}/{sportinglife_path}/racecard/{race_id}/{race_slug}
```

Find `{sportinglife_path}`, `{race_id}`, and `{race_slug}` from the configured course page or the Sporting Life racecard list. Examples of paths are `epsom-downs` and `ascot`.

### 2. Racing Post

```text
https://www.racingpost.com/racecards/{course_id}/{course_path}/{date}/{race_id}/compact-view/
```

`{course_id}` and `{course_path}` come from `config\courses\{course}.json`. Racing Post can return HTTP 406 on repeated fetches; wait at least 60 seconds before retrying.

### 3. Other public racecard pages

Template the query from course/date/time rather than hardcoding a venue:

```text
{course_display} {date} {off_time} {race_name} confirmed runners
```

### 4. Search fallback

Use a web search only when direct pages are blocked or JavaScript-only:

```text
"{course_display}" "{race_name}" "{date}" confirmed runners jockey trainer
```

## Procedure

1. Set scope.

```powershell
$course = "{course}"
$meeting = "{meeting}"
$date = "{date}"
```

2. Read the raw racecard and current rendered card. List every race that has not yet run, using `CURRENT_DATETIME` from the task prompt.

3. For each remaining race, collect off time, race name, runner count, cloth numbers, horse name, jockey, trainer, and source URL.

4. Detect discrepancies:
   - horse appears in raw/card but not live source: remove or mark no bet
   - cloth number absent from source order: probable non-runner
   - horse appears live but not in raw: unscored late entry or data gap
   - source count differs from rendered field count: investigate before publish

5. Write or update the canonical live-runner file.

```json
{
  "fetched_at": "YYYY-MM-DDTHH:MM:SS+01:00",
  "course": "{course}",
  "meeting": "{meeting}",
  "date": "{date}",
  "races": [
    {
      "time": "HH:MM",
      "name": "Race name",
      "source_name": "Sporting Life",
      "source_url": "https://...",
      "status": "verified",
      "runners": [
        {"number": 1, "draw": 4, "name": "Horse", "jockey": "Jockey", "trainer": "Trainer", "price": null}
      ],
      "non_runners_excluded": []
    }
  ]
}
```

6. Write a mismatch note when any discrepancy exists:

```text
.squad\decisions\inbox\livingston-card-vs-live-{course}-{date}.md
```

Include `race_time`, `horse`, `card_status`, `live_status`, `action`, and `source_url`.

7. Hand off:
   - Rusty: races requiring re-score and the live-runner path.
   - Linus: horses to remove, replacements to render, or races that must become PASS.
   - Coordinator: blocked races needing manual runner paste.

## First use: Epsom Ladies Day 2026

On 2026-06-05 at Epsom, stale runner identity from a 2026-06-02 market file allowed Port Road and Triple Double A to remain on the card after they were non-runners. Blue Brother was also missing from live declarations. This skill generalizes that incident into a source-order verification gate for every course.

## Rules

- Do not guess runners.
- Do not trust stale market files for runner identity.
- Do not include races already past.
- If every source fails, mark the race `blocked` and escalate for manual runner paste.
- Prices are optional; runner identity is mandatory.
