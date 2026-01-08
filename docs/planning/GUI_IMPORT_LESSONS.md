# GUI Import Lessons Learned

From Session 073-074: Full Year Block Assignment Import

## Summary

Successfully imported 221 block assignments (17 residents × 13 blocks) for AY 2025-2026 using CLI script. Lessons documented for GUI implementation.

---

## 1. Data Format Challenges

### CSV Requirements
- **Header row required**: `block_number,rotation_abbrev,resident_name`
- **No comment lines**: Lines starting with `#` break CSV parser
- **UTF-8 encoding**: Special characters in names need proper encoding

### Resident Name Matching
- **Fuzzy matching by last name works well**: "Sawyer" matches "Tessa Sawyer"
- **Gotcha**: Multiple residents with same last name would conflict
- **GUI should**: Show matched full name for user verification

### Rotation Abbreviation Matching
- **Case-insensitive matching**: "cardio" matches "CARDIO"
- **Multiple keys per template**: abbreviation, display_abbreviation, name
- **Variations tried**: `- → space`, `space → -`, `/ → -`, `_ → -`

---

## 2. Missing Template Detection

### Templates That Were Missing (17 total)

| Abbreviation | Name | Activity Type |
|--------------|------|---------------|
| CARDIO | Cardiology | outpatient |
| DERM | Dermatology | outpatient |
| ELEC | Elective | outpatient |
| EM | Emergency Medicine | inpatient |
| FAC-DEV | Faculty Development | education |
| GERI | Geriatrics | outpatient |
| IM | Internal Medicine Ward | inpatient |
| JAPAN | Japan Off-Site Rotation | off |
| MILITARY | Military Duty | off |
| MSK-SEL | Musculoskeletal Selective | outpatient |
| PEDS-CLIN | Pediatrics Clinic | outpatient |
| PEDS-EM | Pediatric Emergency Medicine | inpatient |
| PEDS-SUB | Pediatrics Subspecialty | outpatient |
| PROC | Procedures | procedures |
| PSYCH | Psychiatry | inpatient |
| SEL-MED | Medical Selective | outpatient |
| TAMC-LD | TAMC Labor & Delivery | inpatient |

### GUI Recommendation
- **Preview mode**: Show all unmatched rotations BEFORE import
- **Quick-create option**: "Create template for 'CARDIO'?" with type dropdown
- **Bulk create**: "Create all 17 missing templates with default types?"

---

## 3. Duplicate Detection

### Block 10 Was Pre-imported
- 17 rows skipped as duplicates (resident already has Block 10 assignment)
- GUI should: Offer "Update existing" vs "Skip" option

### Duplicate Key: (block_number, academic_year, resident_id)
- Unique constraint prevents double-booking resident in same block

---

## 4. GUI Implementation Recommendations

### Import Workflow

```
1. UPLOAD/PASTE → Parse CSV/spreadsheet
2. PREVIEW → Show:
   - Matched rows (green)
   - Unmatched rotations (yellow) with "Create Template" button
   - Unmatched residents (red) - require manual mapping
   - Duplicates (gray) with "Skip/Update" toggle
3. RESOLVE → User fixes mismatches
4. CONFIRM → Show final count
5. IMPORT → Commit with progress bar
6. RESULT → Show success/failure summary with downloadable log
```

### API Endpoint Design

```typescript
// POST /api/v1/admin/block-assignments/preview
{
  csv_content: string,
  academic_year: number
}
// Returns: { matched: [], unmatched_rotations: [], unmatched_residents: [], duplicates: [] }

// POST /api/v1/admin/block-assignments/import
{
  csv_content: string,
  academic_year: number,
  create_missing_templates: boolean,
  update_duplicates: boolean
}
// Returns: { imported: number, skipped: number, errors: [] }
```

### Paste Parser
- **Excel paste**: Tab-separated, needs column detection
- **Google Sheets**: Tab-separated
- **CSV**: Comma-separated
- **Auto-detect**: First row analysis for delimiter

---

## 5. Error Handling Patterns

### Errors Encountered & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `ValueError: invalid literal for int()` | Comment lines (`#`) in CSV | Strip comment lines before parsing |
| `Unknown rotation 'X'` | Missing template | Create template OR manual mapping |
| `Unknown resident 'X'` | Name mismatch | Fuzzy matching OR manual mapping |
| `Skip duplicate` | Already exists | Expected behavior, log and continue |

### GUI Error Display
- **Per-row errors**: Inline indicators with hover details
- **Batch errors**: Summary panel with "Fix All" suggestions
- **Rollback**: On critical error, rollback transaction

---

## 6. Performance Considerations

### Current CLI Performance
- 221 rows: ~2 seconds
- Pre-load caches: Rotation templates, residents

### GUI Optimization
- **Server-side validation**: Preview endpoint should validate all rows
- **Batch insert**: Use bulk insert instead of row-by-row
- **Progress streaming**: For large imports, use WebSocket progress updates

---

## 7. Testing Recommendations

### Test Cases for GUI Import

1. **Happy path**: Valid CSV, all matches
2. **Missing templates**: Some rotations don't exist
3. **Missing residents**: Some names don't match
4. **Duplicates**: Re-import same data
5. **Partial overlap**: Some new, some duplicate
6. **Empty file**: Handle gracefully
7. **Invalid format**: Wrong columns, bad encoding
8. **Large file**: 500+ rows performance test

---

## 8. Files Created

| File | Purpose |
|------|---------|
| `backend/scripts/import_block_assignments.py` | CLI import script |
| `full_year_assignments.csv` | Sample data (221 rows) |
| `docs/admin-manual/rotation-templates.md` | Template reference |
| `docs/planning/GUI_IMPORT_LESSONS.md` | This document |

---

## 9. Database State After Import

```
block_assignments: 221 rows (17 residents × 13 blocks)
rotation_templates: 84 templates (67 + 17 new)
```

### Verification Query
```sql
SELECT block_number, COUNT(*)
FROM block_assignments
WHERE academic_year = 2026
GROUP BY block_number
ORDER BY block_number;
-- All blocks should have 17 assignments
```
