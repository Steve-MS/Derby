### 2026-06-10: v0.5.0 import-only docs and ToS hygiene
**By:** Livingston

## Files added / renamed / modified

Modified:
- README.md
- CHANGELOG.md
- RUNBOOK.md
- docs\data-layout.md
- .env.example
- .squad\skills\artifact-watchdog\SKILL.md
- .squad\skills\live-runner-verification\SKILL.md
- .squad\skills\morning-odds-gate\SKILL.md
- .squad\skills\race-day-report-footnotes\SKILL.md

Renamed/deprecated:
- scripts\scrape_sportinglife.py -> scripts\scrape_sportinglife.deprecated.py
- scripts\scrape_racingpost.py -> scripts\scrape_racingpost.deprecated.py

Added:
- .squad\decisions\inbox\livingston-13-v0-5-0-docs.md

## README Quickstart verification

Verified end-to-end against the shipped fixture with the actual v0.5.0 CLI surface:

```powershell
python -m pip install -e . --quiet
$course='ascot'; $meeting='royal-ascot-2026'; $date='2026-06-16'
$saved='tests\fixtures\Sportinglife\sample-meeting.html'
race-analysis fetch --from-file $saved --course $course --meeting $meeting --date $date
race-analysis score --course $course --meeting $meeting --date $date
race-analysis predict --course $course --meeting $meeting --date $date --bankroll 100
race-analysis report --course $course --meeting $meeting --date $date
race-analysis card --course $course --meeting $meeting --date $date
```

Result: all commands exited 0. Fetch reported 1 race, 14 runners, 13 active, and wrote `data\raw\ascot-2026-06-16-racecards.json`. Score, bets, slip, report, and racecard were generated.

Linus handoff note `.squad\decisions\inbox\linus-21-v0-5-0-src.md` was not present when this handoff was written. CLI behavior was verified directly from `race-analysis fetch --help`, which exposes `--from-file PATH`.

## CHANGELOG v0.5.0 entry shipped

Yes. Prepended v0.5.0 with Added, Changed, Deprecated, Fixed, and Notes for consumers.

## Scrape scripts

Renamed/deprecated as planned using `git mv`. Each `.deprecated.py` file exits immediately with a v0.5.0 deprecation message and retains original code below as unreachable historical reference.

## Imports broken by deprecation

No Python imports found for `scrape_sportinglife` or `scrape_racingpost`. Grep did find old test smoke references to the script filenames, but tests are Linus-owned and were not modified by this docs pass.

## Skill files updated

- artifact-watchdog
- live-runner-verification
- morning-odds-gate
- race-day-report-footnotes

Other skill files were audited by grep and did not require source-workflow edits.

## .env.example audit

`SPORTINGLIFE_USER` and `SPORTINGLIFE_PASS` remain listed. Comments now state they are used when manually logging into Sporting Life in the browser before saving the page.

## Status

READY-FOR-GATE
