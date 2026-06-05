# Orchestration: Linus — Derby Trifecta Card Placement

**Dispatch:** 2026-06-05 13:40 BST (12:40 UTC)  
**Duration:** 258 seconds  
**Route:** Hybrid (hand-edit + helper promotion)  
**Status:** ✅ Complete — racecard ready for print

---

## Scope

**Objective:** Add first-ever trifecta box recommendation to Derby Day A4 card.

**Decision:** Trifecta box renders immediately below parent race's outsider rationale row, inside main bet-slip table (layout option a — keeps all Derby content grouped).

---

## Deliverables

### 1. Hand-edited Racecard

**File:** `outputs/racecard-2026-06-06.html`

- Full-width `<tr class="row-trifecta">` inserted with purple-left-border + `#f6f3ff` shaded background
- 4-horse box: Item, Benvenuto Cellini, Maltese Cross, Causeway
- £24 total stake, conviction tag (Medium), going contingency note, stale-odds caveat (amber), double-count warning for Causeway
- **Verification:** 11/11 content checks pass; Ladies Day card untouched; downstream races (16:40 Allegresse, 17:15 Ribblesdale) intact
- Ready for Steve to open and print

### 2. Reusable Helper Function

**File:** `src/report.py`

- **Function:** `render_trifecta_box(trifecta: dict) -> str`
- Returns: self-contained `<tr>` HTML snippet
- **Purpose:** Reproducibility for Royal Ascot and future race cards
- **Status:** Added but NOT wired to Jinja2 template or render() pipeline
- **Promotion path:** Royal Ascot v0.7 task — integrate into template, add to render() context, update CSS

---

## Cross-Agent Notes

### Saul (Test Lead)

Hand-edit on published racecard + new render_trifecta_box() helper require test coverage before next race-weekend cycle:
1. Unit test for render_trifecta_box() function
2. Integration test for HTML structure (purple box, 4 horses, going contingency, stale-odds caveat)
3. Before Royal Ascot: promote helper into template pipeline + full test suite

### River (Ops & Runbook)

**Going contingency rule:** If Soft going declared Sat 07:00 BST, drop Item from 4-horse box → 3-horse box (Benvenuto Cellini, Maltese Cross, Causeway) at £2.50/combo × 6 = £15 total.

**Race-morning runbook:** Check Official Going post (07:00 BST). If Soft → activate contingency flag, inform Steve before 16:00. **Print verification:** No mid-night re-edits post-print (digital card already printed by race morning).

---

## File Changes Summary

| File | Change | Status |
|---|---|---|
| `outputs/racecard-2026-06-06.html` | Trifecta `<tr>` inserted (hand-edit) | ✅ Complete |
| `src/report.py` | `render_trifecta_box()` helper added | ✅ Complete (not wired to template) |
| `.squad/agents/linus/history.md` | Entry appended (already done) | ✅ Complete |
| `.squad/decisions/inbox/linus-trifecta-card-placement.md` | Decision document created | ✅ Complete |
| `.squad/skills/trifecta-box-from-scoring/SKILL.md` | Referenced for future promotion | ✅ Ready |

---

## Verification Checklist

- [x] 4 horses present and correct (Item, Benvenuto Cellini, Maltese Cross, Causeway)
- [x] Scores & market ranks align to model state
- [x] Conviction tag present (Medium)
- [x] Going contingency noted (Item drop rule)
- [x] Stale odds caveat with amber highlight
- [x] Double-count warning for Causeway
- [x] Stake £24 within £15-35 Group 1 budget
- [x] Ladies Day card untouched
- [x] Downstream races intact
- [x] CSS classes applied + rendering correct
- [x] Purple border + background visible

---

## Next Steps

**Royal Ascot promotion (v0.7):**
1. Wire `render_trifecta_box()` into `src/templates/report.html.j2`
2. Pass `trifecta_boxes` dict in `render()` via `_build_context()`
3. Update CSS in `src/templates/style.css` (class already defined)
4. Add full test coverage before race weekend
5. Reference: `.squad/skills/trifecta-box-from-scoring/SKILL.md`

---

**Orchestration log entry recorded by:** Scribe  
**Merge to main:** Ready (post-ceremony commit)
