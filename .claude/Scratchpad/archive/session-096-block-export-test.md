# Session 096: Block Export Testing

**Date:** 2026-01-13
**Branch:** `feat/exotic-explorations`
**Status:** Complete - Export working with fixes

## Summary

Tested and fixed the BlockFormatExporter for round-trip xlsx export. Applied fixes based on Cowork review feedback.

---

## V1 Test Results

**Endpoint:** `GET /api/v1/admin/block-assignments/export-block-format?start_date=2026-03-12&end_date=2026-04-08`

```
HTTP Status: 200 OK
Found 1288 assignments
Filled 1288 cells
```

---

## V1 Fixes Applied

### 1. Path Fix
**File:** `backend/app/services/block_format_exporter.py:31`

```python
# Before (wrong - goes to root /)
DEFAULT_TEMPLATE_PATH = Path(__file__).parent.parent.parent.parent / "data" / "local" / ...

# After (correct - goes to /app)
DEFAULT_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "data" / "local" / ...
```

### 2. Name Format Matching
Added `normalize_db_name()` to convert "First Last" → "last, first"

### 3. Date Mapping Fix
Added day-offset calculation so template works with any year's block dates.

---

## V2 Fixes (Post-Cowork Review)

### Cowork Feedback Summary

| Issue | Severity | Status |
|-------|----------|--------|
| 4 blank residents | Critical | ✅ Fixed |
| Abbreviation mappings | High | ✅ Fixed |
| Mid-block transitions | Critical | ⚠️ Data issue |
| Intern Wed AM | High | ⚠️ Expansion issue |
| Faculty section sparse | Medium | Not investigated |

### Fixes Applied (V2)

**1. Name Matching - Last-name fallback**

Added `last_name_lookup` for cases where first names differ (nicknames):
- "Petrie, William*" ↔ "Clay Petrie" (William vs Clay)
- "Headid, Ronald" ↔ "James Headid" (Ronald vs James)
- "Maher, Nicholas" ↔ "Nick Maher" (Nicholas vs Nick)
- "Byrnes, Katherine" ↔ "Katie Byrnes" (Katherine vs Katie)

**2. Abbreviation Mappings**

Added/updated mappings:
```python
"LDNF": "L&D",       # L&D Night Float
"PNF": "PedNF",      # Pediatrics Night Float
"NEURO-NF": "NEURO", # Neuro + Night Float
"NF-ENDO": "NF",     # Night Float + Endo
"FMC": "C",          # Family Medicine Clinic → Clinic
```

### V2 Test Results

```
Found 1288 assignments
Filled 1288 cells

Previously blank → Now filled:
  Row 12 Petrie: FMIT/FMIT ✓
  Row 17 Headid: L&D/L&D ✓
  Row 18 Maher: SURG/SURG ✓
  Row 23 Byrnes: OFF/PedNF ✓

FMC → C mapping working:
  Mayell: C (not FMC) ✓
  Sawyer: C (not FMC) ✓
```

---

## Remaining Upstream Issues

### 1. Mid-Block Transitions (Data Issue)

`secondary_rotation_template_id` is NULL for all mid-block residents:
- Jae You: NEURO-NF (should switch to NF at day 14)
- Clara Wilhelm: PEDS-W (should switch to PNF at day 14)
- Katie Byrnes: PNF (should switch to PEDS-W at day 14)

**Root cause:** Import service didn't populate secondary rotations.
**Fix needed:** Update `block_assignment_import_service.py` to capture secondary rotations from xlsx.

### 2. Intern Wednesday AM (Expansion Issue)

PROC and IM interns show their rotation on Wed AM instead of 'C' (continuity clinic):
- Sloss (PROC): PR ❌ (should be C)
- Monsivais (IM): IM ❌ (should be C)

**Root cause:** Expansion service doesn't override Wed AM for certain rotations.
**Fix needed:** Update `block_assignment_expansion_service.py` to apply continuity clinic rule.

---

## Files Modified

| File | Changes |
|------|---------|
| `backend/app/services/block_format_exporter.py` | Path fix, name normalization, date mapping, last-name fallback, abbreviation mappings |

## Output Files

- V1: `Block10_EXPORTED_postprocessed.xlsx` (before cowork review fixes)
- V2: `Block10_EXPORTED_v2_postprocessed.xlsx` (after fixes)

Path: `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/`
