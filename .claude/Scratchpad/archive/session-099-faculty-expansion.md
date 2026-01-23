# Session 099: Faculty Expansion Service (Context Recovery)

**Date:** 2026-01-13
**Branch:** `feat/session-091`
**Status:** 🔧 In progress - recovering from context loss

## What Was Accomplished (Pre-Compact)

### 1. DB State Queried
- Call assignments: 20 nights properly distributed
- Faculty assignments: Had `FMIT-R` (wrong - resident code)
- `faculty_weekly_templates`: 0 rows (empty)

### 2. Strategy Decision
User chose: Generate faculty from rules (not export existing DB data)

### 3. Faculty Constraints Captured (User-Confirmed)

| Role | Name | C min-max | GME min-max | DFM min-max | AT min-max |
|------|------|-----------|-------------|-------------|------------|
| Core | Kinkennon, LaBounty, McRae, Colgan, Chu | 2-4 | 2-3 | - | 1-3 |
| APD | Montgomery | 1-2 | 3-4 | - | 1-3 |
| OIC | Dahl | 1-2 | 1-2 | 1-2 (split) | 1-3 |
| Chief | McGuire | 1-1 | - | fills rest | 1-1 |
| PD | Bevis | 0-0 | fills rest | - | 1-1 |
| SM | Tagawa | 0-0 | - | - | 1-3 |
| Adjunct | Van Brunt, Lamoureux, Napierala | Skip (filled by hand) |

### 4. FacultyAssignmentExpansionService Extended
- Added `FACULTY_CONSTRAINTS` dict
- Added `ADJUNCT_FACULTY` set
- Added `_preload_call_assignments()`
- Added `_preload_fmit_dates()`
- Added `_is_post_call()` (checks FMIT exclusion)
- Added `_fill_slot_v2()` with priority order:
  1. Existing → skip
  2. Weekend → W
  3. Absent → LV
  4. Holiday → HOL
  5. Post-call → PCAT (AM) / DO (PM)
  6. Wed PM → LEC
  7. C up to weekly cap
  8. Admin (GME/DFM/SM)

### 5. Blocker Found
`HOL-AM`, `HOL-PM` templates don't exist in DB.

## What Needs to Happen Next

1. **Fix HOL template issue** - Create templates or use OFF fallback
2. **Run faculty expansion** - Populate DB with generated assignments
3. **Extend XML exporter** - Add faculty section
4. **Update xlsx converter** - Add faculty rows (31-43)
5. **Visual validation** - Export and inspect

## Key Files
- `backend/app/services/faculty_assignment_expansion_service.py` - Extended
- `backend/app/services/schedule_xml_exporter.py` - Needs faculty support
- `backend/app/services/xml_to_xlsx_converter.py` - Needs faculty rows

## User Corrections Applied
- FMIT call doesn't get PCAT/DO (they continue FMIT coverage)
- Tagawa gets SM independently (not just when residents have SM)
- Dahl gets GME/DFM split (not all GME)
- Adjunct faculty skipped (filled by hand)
