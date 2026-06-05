# Decision: Trifecta Box Placement on Race Day Cards

**Author:** Linus (Reports)
**Date:** 2026-06-05
**Context:** Derby Day 2026-06-06 card — first use of a trifecta box recommendation.

---

## Decision

**Trifecta boxes always render immediately below the parent race's outsider rationale row, not in a separate "Specials / Multiples" section.**

Specifically: the box is inserted as a full-width spanning `<tr class="row-trifecta">` inside the main `.slip` table, directly after the `row-rationale-outsider` row for that race. This keeps all Derby/race content visually grouped together on the A4 card.

## Rationale

- Steve reads the card race-by-race in time order. Grouping the trifecta box with the parent race avoids a page-flip to a "Specials" section mid-race-day.
- The outsider row is always the last Derby row (since the outsider is the model's #4 or similar rank). The trifecta box slots naturally after it.
- A "Specials / Multiples" section at the bottom would require Steve to cross-reference back to the Derby block for going contingency decisions. Inlining it with the race block is cleaner for race-day use.

## Implementation

- The section is visually distinguished by a purple left-border + shaded `#f6f3ff` background (`.trifecta-box` CSS class), matching the `row-multi` purple but as a box rather than a table row.
- `render_trifecta_box(trifecta: dict) -> str` helper added to `src/report.py` (2026-06-05) for future reproducibility. The helper returns a self-contained `<tr>` HTML snippet.

## Handoff note

**⚠️ The Derby Day 2026-06-06 trifecta box was hand-inserted into `outputs/racecard-2026-06-06.html` on 2026-06-05 PM.** The `render_trifecta_box()` helper exists in `src/report.py` but is not yet wired into the Jinja2 template or the main `render()` pipeline. **Before Royal Ascot:** promote the helper into `src/templates/report.html.j2`, pass a `trifecta_boxes` dict via the `render()` call, and add the companion CSS classes to `src/templates/style.css`.
