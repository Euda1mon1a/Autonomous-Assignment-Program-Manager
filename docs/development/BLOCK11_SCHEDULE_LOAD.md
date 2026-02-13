# Block 11 Schedule Load — Import Log

> **Date:** 2026-02-12
> **Block:** 11 (Apr 9 – May 6, 2026), AY 2025
> **Source:** Excel handjam (authoritative human-maintained schedule)
> **Branch:** `feat/block11-schedule-load`

---

## Summary

Block 11 schedule data was loaded from the Excel handjam into the database across multiple sessions. This involved parsing the Excel, creating missing activity codes, syncing half-day assignments (HDAs), fixing structural linkages, populating faculty weekly templates, and syncing absence records.

### Final State

| Table | Count | Status |
|-------|-------|--------|
| `half_day_assignments` | 1,496 | Synced from updated Excel |
| `assignments` | 896 | Rebuilt from BlockAssignments (16 residents x 56 slots) |
| `block_assignments` | 16 | Pre-existing (resident → rotation mappings) |
| `faculty_weekly_templates` | 140 | Populated from Excel patterns (10 faculty x 14 slots) |
| `absences` (Block 11) | 8 | Synced from Excel leave/TDY/deployment data |

---

## What Was Done

### 1. Excel Parsing & HDA Sync

- Parsed Excel handjam (rows 9-25 residents, 31-45 faculty)
- Columns F-BI map to 56 half-day slots (28 days x AM/PM)
- Created missing activity codes: `CC`, `OB`, `TAMC-LD`
- Mapped Excel display codes to DB activity codes (e.g., `C` → `fm_clinic`, `SM` → `sm_clinic`)
- Loaded 1,496 HDAs (118 updated, 162 created from first pass; 43 updated from revised Excel)
- 100% match verified between Excel and DB

### 2. Assignments Table Fix

- Deleted 995 stale solver-generated assignments with incorrect rotation templates
- Rebuilt 896 correct assignments from `block_assignments` table
- Each of 16 residents mapped to their correct rotation template across 56 block slots

### 3. HDA Block Assignment Linkage

- Backfilled `block_assignment_id` on 891 resident HDAs
- Links each daily HDA back to the governing `BlockAssignment` for provenance
- Faculty HDAs (605) correctly remain NULL (no BlockAssignment for faculty)

### 4. Faculty Weekly Templates

- Analyzed 4 weeks of Excel data per faculty member
- Extracted default weekly patterns using most-common-activity logic
- Filtered out rotating activities (CALL, PCAT, DO) — handled by preload system
- Updated 100 existing weekday template rows, created 40 weekend slots
- Final: 140 template slots, all with `activity_id` populated

### 5. Absence Sync

Synced absence records from Excel leave-type activities (LV, TDY, DEP, SLV):

| Person | Type | Dates | Notes |
|--------|------|-------|-------|
| Resident A | deployment | Feb 21 – Jun 30 | Pre-existing, spans multiple blocks |
| Resident B | vacation | Apr 20–22 | Supervisory leave |
| Resident C | vacation | May 1–5 | |
| Resident D | vacation | Apr 13–19 | |
| Resident E | vacation | Apr 20–26 | |
| Resident F | vacation | Apr 13–19 | |
| Resident F | tdy | Apr 20 – May 1 | TDY to away rotation |
| Resident G | vacation | Apr 12 – May 5 | Extended leave |

### 6. Activity Code Distinction: TAMC-LD vs KAP-LD

- Created `TAMC-LD` activity code for TAMC Labor & Delivery rotation
- Distinguished from existing `KAP-LD` (Kapiolani L&D)
- Updated resident HDAs to use correct site-specific code based on rotation assignment

### 7. Bug Fix: `is_gap` AttributeError

- `HalfDayAssignmentRead` schema declared `is_gap: bool = False` but the SQLAlchemy model lacked this attribute
- Fixed with `getattr(a, "is_gap", False)` in the route handler
- This was blocking the entire HDA API endpoint

### 8. Codex Review Fixes (PR #1117)

After the initial data load, Codex automated review on PR #1117 identified 7 rounds of issues. All P1/P2 findings were addressed across commits `a4d6fbe8` through `74fe704f`.

#### Split-Block Rotation Support (engine + solver)

- **`engine.py` `_get_residents()`**: Added union query to check both `rotation_template_id` and `secondary_rotation_template_id` for outpatient rotation filtering. Previously only checked primary, causing split-block residents to be miscategorized.
- **`engine.py` `_load_resident_template_map()`**: Changed return type from `dict[UUID, UUID]` to `dict[UUID, set[UUID]]` so residents with mid-block rotation changes get both template IDs.
- **`solvers.py`**: Updated variable creation to use set-based lookup with intersection against active templates. Guards against archived templates causing residents to get zero solver variables.
- **`constraints/base.py`**: Updated `SchedulingContext.resident_template_map` type annotation to `dict[UUID, set[UUID]]`.

#### Faculty Assignment Expansion Fixes

- **Process-global cache**: Moved `_activity_cache` from class-level to instance variable in `FacultyAssignmentExpansionService`, matching the pattern used by `BlockAssignmentExpansionService` and `SyncPreloadService`. Class-level cache persisted stale SQLAlchemy objects across requests.
- **Holiday/weekend priority**: Swapped evaluation order so federal holidays (`HOL`) are checked before weekends (`W`). Previously a Sunday federal holiday would be marked `W` instead of `HOL`.

#### Template Script Fixes

- **`block_import_template.py`**: Changed HDA source from `excel_import` (invalid check constraint) to `manual`. Added date range filter to absence DELETE to prevent cross-year collisions.
- **`fix_assignments_template.py`**: Added `secondary_rotation_template_id` to SELECT, split-block logic with `block_half_day = 14`, and fixed 4-column unpack in backfill loop.

#### Test Fix

- **`test_faculty_pipeline.py`**: Corrected `get_block_dates` mock patch target from `app.utils.academic_blocks` to `app.services.faculty_assignment_expansion_service`.

#### Engine Guard

- **No-block-context guard**: Added `if block_number is not None and academic_year is not None` check before calling `_load_resident_template_map()`. Prevents crash when engine runs without block context (e.g., daily preload).

#### False Positive: ResidentWeeklyClinic

Codex flagged `ResidentWeeklyClinic` as "not registered" twice. This is a **false positive** — the constraint IS registered at `manager.py:404`, disabled by default at line 406, and conditionally enabled at `engine.py:983`.

---

## Scripts Used (all in `/tmp/`, not committed)

| Script | Purpose |
|--------|---------|
| `parse_excel_handjam.py` | Excel parser + DB comparison tool |
| `load_excel_to_db.py` | Initial HDA sync from Excel |
| `fix_block11_assignments.py` | Fix assignments + backfill block_assignment_id |
| `populate_faculty_templates.py` | Analyze Excel + populate faculty templates |
| `sync_block11_absences.py` | Sync absences from Excel leave data |
| `sync_updated_excel.py` | Apply changes from revised Excel |

## DB Backups

| Backup | Location |
|--------|----------|
| Pre-Excel load | `/tmp/block11_pre_excel_backup.dump` |
| Pre-assignments fix | `/tmp/block11_pre_assignments_fix.dump` |
| Pre-absence sync | `/tmp/block11_pre_absence_fix.dump` |
| Pre-updated Excel | `/tmp/block11_pre_updated_excel_fix.dump` |

---

## Lessons Learned

1. **Excel is authoritative** — The human-maintained handjam is the source of truth for Block 11. DB records from solver runs were stale.
2. **Multiple Excel revisions** — The Excel was updated mid-import. Always confirm you have the latest version before syncing.
3. **Activity code granularity matters** — `L&D` in Excel maps to different DB codes depending on rotation site (TAMC vs Kapiolani).
4. **Absence table has no half-day support** — Half-day leave (e.g., AM-only) requires a note; the table only tracks full-day date ranges.
5. **`is_gap` schema/model mismatch** — Schema fields without model backing cause runtime errors. Use `getattr()` defensively for optional fields.

---

## Verification Checklist

- [x] HDA count matches Excel (1,496)
- [x] 100% activity code match between Excel and DB
- [x] Assignments table has correct rotation templates (896 records)
- [x] HDA block_assignment_id populated for residents (891)
- [x] Faculty weekly templates all have activity_id (140 slots)
- [x] Absences match Excel leave/TDY/deployment data (8 records)
- [x] TAMC-LD vs KAP-LD correctly assigned per resident rotation
- [x] HDA API endpoint returns data (is_gap bug fixed)
- [x] GUI renders Block 11 schedule correctly
- [x] Split-block residents get both rotation templates in solver (Codex P1)
- [x] Faculty expansion uses instance-level cache (Codex P2)
- [x] HOL prioritized over W in faculty expansion (Codex P2)
- [x] Import/fix templates sanitized for DB constraints (Codex P1)
- [x] Absence cleanup scoped to block date range (Codex P1)
- [x] 169 relevant tests pass, 0 regressions
