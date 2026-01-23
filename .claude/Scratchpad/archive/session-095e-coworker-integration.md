# Session 095e: Coworker Integration - TAMC Scheduling Context

**Date:** 2026-01-13
**Branch:** `feat/exotic-explorations`
**Status:** Complete - Parser, Constraints, Block Format Exporter

## Summary

Integrated Claude coworker's TAMC scheduling documentation and updated parser/import service to handle mid-block rotation transitions using combined templates.

---

## Completed Work

### 1. Migration: `20260113_add_secondary_rot.py`
Added `secondary_rotation_template_id` to `block_assignments` for mid-block transitions.

### 2. Model: `block_assignment.py`
- Added `secondary_rotation_template_id` column
- Added `secondary_rotation_template` relationship

### 3. Expansion Service: `block_assignment_expansion_service.py`

**Constants Added:**
```python
NIGHT_FLOAT_PATTERNS = {
    "NF": ("OFF-AM", "NF"),
    "NF-ENDO": ("OFF-AM", "NF"),
    "NEURO-NF": ("NEURO", "NF"),
    "PNF": ("OFF-AM", "PNF"),
    "LDNF": ("L&D", "L&D"),
    "KAPI-LD": ("KAP", "KAP"),
}

LEC_EXEMPT_ROTATIONS = frozenset([
    "NF", "NF-ENDO", "NEURO-NF", "PNF", "LDNF", "KAPI-LD", "HILO", "TDY",
])

WEDNESDAY_DOW = 3
MID_BLOCK_DAY = 14
```

**Helper Methods:**
- `_get_active_rotation()` - Handles mid-block transitions (day 14)
- `_is_wednesday()` - Wednesday check for LEC
- `_should_use_lec()` - LEC eligibility check
- `_get_night_float_template_abbrev()` - Night float AM/PM patterns

**Verified Results:**
- LEC-PM: 68 assignments (non-exempt residents on Wed PM)
- OFF-AM: 40 assignments (night float residents in AM)
- W-PM/W-AM: 368 assignments (weekends)

### 4. Parser: `block_schedule_parser.py`

**Updated ROTATION_MAPPINGS** to output DB abbreviations:
```python
ROTATION_MAPPINGS = {
    "Night Float": "NF-PM",
    "Sports Medicine": "SM-AM",
    "FMIT": "FMIT-R",
    "L&D Night Float": "LDNF",
    "GYN Clinic": "GYN-CLIN",
    "Kapiolani L&D": "KAPI-LD",
    "Internal Medicine": "IM-INT",
    "Procedures": "PR-AM",
    # ... etc
}
```

### 5. Import Service: `block_assignment_import_service.py`

**Problem:** xlsx gives "Night Float" + "Endocrinology" as separate columns, but DB uses combined templates like `NF-ENDO`.

**Solution:** Added `COMBINED_ROTATION_MAPPINGS` dict:
```python
COMBINED_ROTATION_MAPPINGS = {
    ("NIGHT FLOAT", "ENDOCRINOLOGY"): "NF-ENDO",
    ("ENDOCRINOLOGY", "NIGHT FLOAT"): "NF-ENDO",  # mirror
    ("NEUROLOGY", "NIGHT FLOAT"): "NEURO-NF",
    ("NIGHT FLOAT", "NEUROLOGY"): "NEURO-NF",  # mirror
    ("PEDIATRICS WARD", "PEDIATRICS NIGHT FLOAT"): "PEDS-W",
    ("PEDIATRICS NIGHT FLOAT", "PEDIATRICS WARD"): "PNF",
    # ... includes abbreviation variants
}
```

**New Method:** `_match_combined_rotation(primary, secondary)` - tries combined lookup first, falls back to individual matching.

**Updated `preview_block_sheet_import()`:**
- Processes xlsx directly (no CSV conversion)
- Tries combined rotation match when secondary_rotation present
- Preserves secondary_rotation_template_id in cache for execute_import

### 6. Schema: `block_assignment_import.py`

Added to `BlockAssignmentPreviewItem`:
```python
secondary_rotation_input: str | None
matched_secondary_rotation_id: UUID | None
matched_secondary_rotation_name: str | None
secondary_rotation_confidence: float = 0.0
```

---

## Verification Results

```
Block 10 Import Preview:
- Parsed: 17 rows
- Matched: 17 (all duplicates since Block 10 exists in DB)
- Unknown rotations: 0

Combined rotations working:
- Night Float + Endocrinology → NF-ENDO ✓
- Neurology + Night Float → NEURO-NF ✓
- Pediatrics Ward + Pediatrics Night Float → PEDS-W ✓
- Pediatrics Night Float + Pediatrics Ward → PNF ✓
```

---

## Pending Tasks

- [x] Add CP-SAT constraints for LEC, intern continuity (belt & suspenders)
- [x] Create BlockFormatExporter for round-trip xlsx
- [ ] **TEST**: Round-trip import → solve → export
- [ ] Document final workflow

## Next Session: Test Round-Trip

```bash
# 1. Export current Block 10 schedule
curl "http://localhost:8000/api/admin/block-assignments/export-block-format?start_date=2025-03-12&end_date=2025-04-08" \
  -H "Authorization: Bearer $TOKEN" -o Block10_EXPORTED.xlsx

# 2. Compare with original
# Open both xlsx files and verify assignments match
```

### Phase 2 Complete: CP-SAT Constraints

Created `backend/app/scheduling/constraints/fm_scheduling.py`:

| Constraint | Rule | Purpose |
|------------|------|---------|
| `WednesdayPMLecConstraint` | Wed PM = LEC-PM (non-exempt) | Validate lecture scheduling |
| `InternContinuityConstraint` | PGY-1 Wed AM = C | Validate intern continuity clinic |
| `NightFloatSlotConstraint` | NF AM = per-rotation pattern | Validate NF AM patterns (OFF-AM, NEURO, L&D, etc.) |

All constraints are **validation-focused** (belt & suspenders). The expansion service handles assignment; constraints validate correctness.

### Phase 3 Complete: Block Format Exporter

Created round-trip xlsx export capability:
- `BlockFormatExporter` service loads template xlsx, fills in assignments
- Uses `data/local/Block10_TEMPLATE.xlsx` (formatted, cleared assignments)
- Uses `data/local/block_template_mapping.json` (date→column mapping)
- API: `GET /api/admin/block-assignments/export-block-format?start_date=&end_date=`

---

## Key Design Decisions

1. **Combined Templates** (chosen over primary + secondary):
   - User decision: Use existing combined templates like `NF-ENDO`, `NEURO-NF`
   - Simpler: expansion service already handles these
   - Safer: many combined templates exist, avoids creating new ones

2. **Mirror Rotations**: Both orderings map to same template (A+B and B+A)

3. **Parser Outputs DB Abbreviations**: Easier cache matching in import service

---

## Files Modified (This Session)

| File | Changes |
|------|---------|
| `backend/app/schemas/block_assignment_import.py` | +4 secondary rotation fields |
| `backend/app/services/block_assignment_import_service.py` | +COMBINED_ROTATION_MAPPINGS, +_match_combined_rotation(), updated preview_block_sheet_import |
| `backend/app/services/block_schedule_parser.py` | Updated ROTATION_MAPPINGS to DB abbreviations |
| `backend/app/scheduling/constraints/fm_scheduling.py` | NEW - 3 validation constraints |
| `backend/app/scheduling/constraints/__init__.py` | +FM constraint exports |
| `backend/app/services/block_format_exporter.py` | NEW - Round-trip xlsx exporter |
| `backend/app/api/routes/admin_block_assignments.py` | +export-block-format endpoint |

---

## References

- Coworker docs: `docs/TAMC_SCHEDULING_CONTEXT.md`
- Plan: `.claude/plans/dynamic-giggling-sprout.md`
- Previous session: `.claude/Scratchpad/session-095-block-expansion-api.md`
- Skills: `skills/tamc-excel-scheduling/SKILL.md`, `skills/tamc-cpsat-constraints/SKILL.md`
