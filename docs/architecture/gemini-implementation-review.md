# Gemini Implementation Review: Full Roadmap + Annual Workbook

> **Reviewed:** 2026-02-24
> **Reviewer:** Claude Opus 4.6
> **Branch:** `fix/block12-null-activities` (uncommitted changes)
> **Status:** 28/31 items fixed. Remaining: #19 (row hash skip), #22 (longitudinal 4c/4d), #28 (N+1 queries)
> **Scope:** Round 1 (Phases 1–4, Tracks A/C) + Round 2 (Annual Workbook)
> **Updated:** 2026-02-26 — Gemini code review findings integrated into PRs #1200, #1201 (VACUUM autocommit, set_config, max default=0)

---

## Summary

Gemini implemented all four Excel Pipeline phases (1–4) and both Schema Hardening tracks (A, C) from the roadmap. The architectural intent is correct throughout — right files, right patterns, right gating for backward compatibility. However, 3 of 4 Excel phases have critical bugs, there are no migrations, no tests, and several incomplete features.

**Recommendation:** Let Gemini finish the annual workbook implementation, then do a single cleanup pass addressing all issues below.

---

## Critical Blockers (Must Fix Before Commit)

### 1. `ExportMetadata` Dataclass Won't Load

**File:** `backend/app/services/excel_metadata.py` lines 14–21

Non-default field `export_timestamp: str` follows default field `block_number: Optional[int] = None`. Python raises `TypeError` on import. **Breaks ALL four phases** since every other file imports from this module.

**Fix:** Move `export_timestamp` before `block_number`, or give it a default value.

```python
# BROKEN (current)
@dataclass
class ExportMetadata:
    academic_year: int
    block_number: Optional[int] = None   # has default
    export_timestamp: str                 # NO default — after default field

# FIX
@dataclass
class ExportMetadata:
    academic_year: int
    export_timestamp: str                 # moved before defaults
    block_number: Optional[int] = None
    export_version: int = 1
    block_map: Optional[dict[str, str]] = None
```

### 2. Missing Stdlib Imports in Export Service

**File:** `backend/app/services/canonical_schedule_export_service.py`

The diff removed `from __future__ import annotations` and original stdlib imports but didn't re-add them. Used but never imported: `io`, `datetime`, `UTC`, `date`, `Path`, `Any`, `Session`. Module fails to import.

**Fix:** Re-add the missing imports.

### 3. Phase 3 DataValidation Is Dead Code

**File:** `backend/app/services/xml_to_xlsx_converter.py` line 679

`_add_data_validation()` checks `if "__REF__" not in sheet.parent.sheetnames: return`. But `__REF__` is created by `_inject_metadata()` in `canonical_schedule_export_service.py`, which runs AFTER `convert_from_json()` returns. The check always fails. **Dropdowns are never added.**

**Fix options:**
- (a) Write `__REF__` sheet inside the converter before calling `_add_data_validation()`
- (b) Move `_add_data_validation()` into `_inject_metadata()` so it runs after `__REF__` exists
- (c) Pass rotation/activity lists directly to the converter constructor

### 4. No Alembic Migration for `person_academic_years`

**Missing file:** `backend/alembic/versions/YYYYMMDD_person_ay.py`

The `PersonAcademicYear` model exists but the table doesn't exist in the database. Any query crashes. Also needs a data migration seeding from current `Person.pgy_level` values.

### 5. No Tests for Tracks A or C

CLAUDE.md requires tests with all code changes. Zero test files exist for:
- Track A: Historical PGY queries, rollover, call count isolation per AY
- Track C: Absence deletion clears preloads, modification updates preloads, computed leave_days matches absences

### 6. Test File Has Bugs

**File:** `backend/tests/services/test_excel_metadata.py` line 53

`test_ref_sheet_roundtrip` unpacks a dict as a tuple: `r_rot, r_act = read_ref_codes(wb)`. `read_ref_codes()` returns a dict. Unpacking yields keys (`"rotations"`, `"activities"` as strings), not lists. All assertions fail.

**Fix:** `ref = read_ref_codes(wb); assert ref["rotations"] == rotations`

---

## High Severity (Correctness)

### 7. Engine Supervision Still Reads Legacy `pgy_level`

**File:** `backend/app/scheduling/engine.py` lines 2650, 3069, 3115

The `_get_residents()` query is AY-scoped (reads from `person_academic_years`), but all downstream logic reads `r.pgy_level` (the legacy column). This is a half-migration — the query is AY-aware but supervision ratios, CV eligibility, and priority keys are not.

### 8. LV Import Doesn't Create Absence Records (Track C Step 3 Missing)

**File:** `backend/app/services/half_day_import_service.py`

The roadmap specifies: "Excel import of 'LV' codes creates absence records." This was not implemented. The audit gap (leave in schedule, no approved absence) remains.

### 9. Row Hash Skip Not Implemented

**File:** `backend/app/services/half_day_import_service.py`

Anchors are read and `person_id` is used, but `row_hash` is never checked. The O(1) change detection optimization (the primary performance benefit of Phase 2) is absent.

### 10. Provenance Comments Incomplete

**File:** `backend/app/services/half_day_json_exporter.py`

`original_activity_code` doesn't exist on the `HalfDayAssignment` model. The code uses `getattr(am_assignment, "original_activity_code", "")` which always returns `""`. Comments always say "Original: " (empty).

**Fix:** Either add `original_activity_code` column to the model, or read from `ScheduleOverride` records, or skip provenance comments until the data model supports them.

---

## Medium Severity (Design / Performance)

| # | Issue | File |
|---|-------|------|
| 11 | **Validator N+1 risk** — `academic_years` not eager-loaded for half-day assignment queries. Thousands of lazy loads per validation run. | `validator.py` |
| 12 | **Rollover N+1** — queries `Person` per AY record in a loop (~45 extra queries). Should use pre-fetched dict or join. | `person_service.py:343` |
| 13 | **Hybrid property fragility** — `block_assignment.has_leave` behavior depends on whether `resident` and `academic_block` relationships are eagerly loaded. Different results per query pattern. | `block_assignment.py:88-92` |
| 14 | **No role authorization on rollover** — any authenticated user can POST to `/academic-year/rollover`. Should require admin/coordinator role. | `people.py:416-439` |
| 15 | **`_copy_worksheet()` loses enrichments** — doesn't copy CF rules, DataValidation, or Comments. Annual export will lose Phase 2/3/4 features. | `canonical_schedule_export_service.py` |
| 16 | **Leave formula hardcodes 28 days** — `schedule_end_col_letter = get_column_letter(COL_SCHEDULE_START + 55)`. Breaks for Block 0 (0-6 days) and Block 13 (22-30 days). | `xml_to_xlsx_converter.py:752` |
| 17 | **Duplicate Named Ranges** — `write_ref_sheet()` appends `DefinedName` without checking if names already exist. Calling twice creates duplicates. | `excel_metadata.py` |
| 18 | **Block assignment schema not updated** — still has `has_leave: bool = False` as a regular field, not reflecting hybrid property. | `schemas/block_assignment.py` |
| 19 | **No `PersonAcademicYearCreate` schema** — service builds AY records from raw args, bypassing Pydantic validation. | `schemas/person.py` |
| 20 | **Rollover endpoint returns `dict`** — bypasses OpenAPI schema generation. Should use a Pydantic response model. | `people.py` |

---

## Low Severity (Style / Minor)

| # | Issue | File |
|---|-------|------|
| 21 | Unused `timezone` import | `person_academic_year.py:4` |
| 22 | `hasattr(self, 'academic_years')` is dead code — attribute always exists as a relationship | `person.py:355` |
| 23 | Naive `datetime.now()` in `current_pgy_level` — should use `datetime.now(UTC)` | `person.py:351` |
| 24 | Function-level imports for `read_sys_meta` could be at module level | `import_staging_service.py:208`, `half_day_import_service.py:743` |
| 25 | `Comment` import inside loop body — executed per resident per day | `xml_to_xlsx_converter.py:1183` |
| 26 | `compute_row_hash()` annotates `person_id: UUID` but tests pass strings | `excel_metadata.py`, `test_excel_metadata.py` |
| 27 | SQL expression side of `current_pgy_level` hybrid returns legacy `cls.pgy_level` — SQL queries bypass AY records | `person.py:363-366` |

---

## Out-of-Scope Changes (Not in Roadmap)

These additions were not called for in the Phases 1–4 or Tracks A/C roadmap. They may be intentional forward-looking work for the annual workbook phase.

| Addition | File | Notes |
|----------|------|-------|
| `export_year_xlsx()` | `canonical_schedule_export_service.py` | Annual workbook export — belongs in annual workbook phase |
| `_ensure_absence_for_leave_assignment()` | `schedule_draft_service.py` | Track C Step 3 variant — creates absence from draft leave assignments |
| `academic_year` + `parent_batch_id` on `ImportBatch` | `models/import_staging.py` | DB schema change requiring migration — roadmap says "no schema changes in Phases 1-4" |

---

## What Works Well

- **Phase 2 export side** — `person_id`, `block_assignment_id`, and `__ANCHORS__` sheet are correctly implemented
- **Phase 4a CF rules** — dynamic conditional formatting uses correct `CellIsRule` pattern
- **Track A model** — `PersonAcademicYear` fields match the roadmap spec exactly, correct unique constraint
- **Track C preload refresh** — `refresh_leave_preloads()` correctly implements 3-step delete/query/recreate
- **Track C absence service** — CRUD operations call preload refresh with correct date range unions on update
- **Backward compatibility** — all new behavior properly gated behind `if meta:` / `if "__ANCHORS__" in wb.sheetnames:` checks
- **Rollover logic** — correctly advances PGY levels, marks graduates, resets call counts via new rows

---

---
---

# Round 2: Annual Workbook Implementation

> **Reviewed:** 2026-02-24 (same session, after Round 1)

## Round 1 Issue Status

| Round 1 Issue | Status in Round 2 |
|---|---|
| #1 ExportMetadata dataclass ordering | **FIXED** — fields reordered correctly |
| #2 Missing stdlib imports | **FIXED** — all imports restored |
| #3 Phase 3 DataValidation dead code | **NOT FIXED** — `__REF__` still created after converter returns |
| #4 No migration for PersonAcademicYear | **NOT FIXED** — still missing (Track A) |
| #5 No tests | **NOT FIXED** — zero tests for any new code across both rounds |
| #6 Test file bugs | **NOT FIXED** |
| #15 `_copy_worksheet()` loses enrichments | **NOT FIXED** — still no CF/DV/Comment copying |
| #16 Leave formula hardcodes 28 days | **NOT FIXED** |
| #17 Duplicate Named Ranges | **PARTIALLY FIXED** — sheet recreated, but DefinedName objects still accumulate |

## New Files

| File | Purpose |
|------|---------|
| `backend/app/tasks/import_tasks.py` | Celery task `process_yearly_workbook` |
| `backend/app/services/longitudinal_validator.py` | Cross-block ACGME validation |
| `backend/app/services/block_generation_service.py` | Ensures AcademicBlock + daily Block records exist |
| `backend/alembic/versions/20260224_annual_batch.py` | Migration: `academic_year` + `parent_batch_id` on `import_batches` |

## Modified Files

| File | Changes |
|------|---------|
| `canonical_schedule_export_service.py` | `export_year_xlsx()`, `_copy_worksheet()`, `_apply_phantom_columns()`, refactored `_inject_metadata()` |
| `import_staging_service.py` | Year-level metadata detection, `academic_year` on batch creation |
| `import_staging.py` (routes) | `POST /stage-yearly` endpoint |
| `import_staging.py` (model) | `academic_year`, `parent_batch_id` columns, self-referential FK |
| `excel_metadata.py` | Dataclass fixed, `block_map` field added |
| `half_day_import_service.py` | `stage_block_sheet()` for per-sheet Celery parsing |

---

## Critical Issues (Round 2)

### R2-C1. `_copy_worksheet()` Strips Phase 3/4 Enrichments from Year Export

**File:** `canonical_schedule_export_service.py` lines 158–181

Each block is generated into a temp workbook (which gets CF rules, DataValidation, Comments from the converter), then copied via `_copy_worksheet()` into the master workbook. The copy only transfers cell values, styles, column widths, and merged cells. It does NOT copy:

- Conditional formatting rules (Phase 4a)
- Data validations (Phase 3 — also dead per Round 1 #3)
- Cell comments (Phase 4c provenance)
- Row heights, print settings, sheet protection

**Result:** Every block sheet in the yearly workbook is a degraded version missing all enrichments. Single-block export is unaffected (doesn't use `_copy_worksheet`).

### R2-C2. Missing `cast` Import in Celery Task

**File:** `backend/app/tasks/import_tasks.py` lines 124, 128

Uses `cast(UUID, child_batch.id)` and `cast(UUID, parent_batch.id)` but only imports `Any, Optional` from `typing`. Raises `NameError` at runtime.

**Fix:** Add `cast` to the `from typing import` line.

### R2-C3. Longitudinal Validator Indentation Bug

**File:** `backend/app/services/longitudinal_validator.py` lines 63–98

The clinic minimum check (4b) and the NF cap threshold check are **indented inside the NF detection `if` block**, not at the person level:

```python
for person_id, assignments in by_person.items():
    nf_blocks = set()
    for a in assignments:
        if any(nf in code for nf in NF_CODES):   # NF detection
            nf_blocks.add(...)
            if len(nf_blocks) > MAX_NF_BLOCKS:    # WRONG: inside NF if
                errors.append(...)
            clinic_count = sum(...)                # WRONG: inside NF if
            if clinic_count < MIN_CLINIC:
                errors.append(...)
```

**Consequences:**
1. NF cap fires per-assignment (duplicate errors when >4 blocks)
2. Clinic minimum only checked for people with NF assignments — residents with zero NF but insufficient clinic are never flagged
3. Clinic check runs per NF assignment (duplicate warnings)

**Fix:** Dedent both checks to the `for person_id` level (outside the inner loop).

### R2-C4. Celery `bytes` Serialization Failure

**File:** `backend/app/api/routes/import_staging.py` line 245

```python
task = process_yearly_workbook.delay(file_bytes=content, ...)
```

Celery's default JSON serializer cannot handle raw `bytes`. This crashes with `kombu.exceptions.EncodeError` at dispatch time.

**Fix:** Base64-encode before dispatch and decode in the task, or store the file to Redis/filesystem and pass a key.

### R2-C5. Cross-Block Leave (4c) and 1-in-7 (4d) Not Implemented

Only NF caps (4a) and clinic minimums (4b) exist. The architecture doc specifies four checks. The function docstring only claims 4a and 4b, so it's honest, but the Celery task calls it expecting full validation.

---

## High Severity (Round 2)

### R2-H1. No Year-Level Export API Endpoint

`export_year_xlsx()` exists on the service but no API route calls it. Coordinators cannot trigger a year-level export from the frontend.

### R2-H2. Per-Block Anchor Sheets Missing from Year Export

Architecture doc Section 2c specifies `__ANCHORS__{N}__` per block sheet. `export_year_xlsx()` does not write these. The converter writes `__ANCHORS__` into the temp workbook, but `_copy_worksheet()` skips hidden sheets. Year-level workbooks lack UUID anchoring.

### R2-H3. NF Code Detection Uses Substring Matching

```python
if any(nf in code for nf in NF_CODES):  # NF_CODES = {'NF', 'PEDNF', 'LDNF'}
```

`"NF" in "INFO"` → True (false positive). `"NF" in "DERM-NF"` → True (NF combined rotations shouldn't count as full NF blocks). Should use exact match or proper pattern matching.

### R2-H4. No Role Authorization on `stage_yearly_import`

Any authenticated user can upload a master workbook. Should require Admin or Coordinator role.

### R2-H5. No File Size Limit on Year Upload

Existing single-block endpoint has a 10MB limit. `stage_yearly_import` has none. A 14-sheet workbook could be large.

---

## Medium Severity (Round 2)

| # | Issue | File |
|---|-------|------|
| R2-M1 | Celery task creates `ImportBatch` directly, bypassing `ImportStagingService` validation/audit | `import_tasks.py` |
| R2-M2 | Block number extracted from sheet name string instead of using `block_map` UUID lookup | `import_tasks.py:84-89` |
| R2-M3 | `block_uuid` from `block_map` is looked up but never used | `import_tasks.py:77` |
| R2-M4 | Validation results stored in `notes` text field (not machine-readable) | `longitudinal_validator.py:99-116` |
| R2-M5 | `BlockGenerationService.generate_daily_blocks()` does per-half-day existence check (N+1, ~730 queries for full year) | `block_generation_service.py` |
| R2-M6 | `export_year_xlsx()` is synchronous — 14 blocks will block the request thread 10-30 seconds | `canonical_schedule_export_service.py` |
| R2-M7 | Named range duplication risk when `write_ref_sheet()` called multiple times | `excel_metadata.py` |

## Low Severity (Round 2)

| # | Issue | File |
|---|-------|------|
| R2-L1 | Unused imports: `Optional`, `Any`, `asyncio`, `json` | `import_tasks.py` |
| R2-L2 | Unused import: `timezone` | `import_staging.py` (model) |
| R2-L3 | f-strings in logger calls (should use `%s` lazy formatting) | multiple files |
| R2-L4 | `typing.List`/`Tuple` instead of builtin `list`/`tuple` (Python 3.11+) | `longitudinal_validator.py`, `block_generation_service.py` |
| R2-L5 | Magic numbers for row ranges (9, 70) in `_apply_phantom_columns` | `canonical_schedule_export_service.py` |

---

## What Works Well (Round 2)

- **Migration is clean** — `20260224_annual_batch.py` adds columns correctly, downgrade works, revision ID under 64 chars
- **ImportBatch parent/child model** — cascade behavior correct (`all, delete-orphan` + `ondelete="CASCADE"`)
- **`stage_block_sheet()`** — correctly reuses existing `_parse_block_template2()` parsing logic
- **`BlockGenerationService`** — correctly uses `get_all_block_dates()` for calendar math, handles Block 0 zero-day edge case, detects federal holidays
- **Phantom column handling** — correct use of `PatternFill` + `Protection` for stub blocks
- **Celery task architecture** — correct structure: read manifest → create parent → loop sheets → create children → validate

---

---
---

# Round 3: Codex 5.3 Fix Pass Review

> **Reviewed:** 2026-02-24

## Codex Fix Scorecard

All 10 targeted fixes are **correct**:

| # | Fix | File | Verdict |
|---|-----|------|---------|
| 1 | `cast` imported | `import_tasks.py` | CORRECT |
| 2 | Unused imports removed (`Optional`, `Any`, `asyncio`, `json`) | `import_tasks.py` | CORRECT |
| 3 | Base64 decode at task start | `import_tasks.py:39` | CORRECT — pairs with encode in routes |
| 4 | Block UUID resolution via `block_map` | `import_tasks.py:84-106` | CORRECT — no more sheet name parsing |
| 5 | NF exact match (`code in NF_CODES`) | `longitudinal_validator.py:69` | CORRECT — set membership, not substring |
| 6 | NF cap + clinic min dedented to person level | `longitudinal_validator.py:73+` | CORRECT — proper scoping |
| 7 | `typing.List` → `list` | `longitudinal_validator.py` | CORRECT |
| 8 | `typing.List`/`Tuple` → builtins | `block_generation_service.py` | CORRECT |
| 9 | Role auth on `stage_yearly_import` (ADMIN + COORDINATOR) | `import_staging.py:219` | CORRECT |
| 10a | File size validation (25MB) | `import_staging.py:242` | CORRECT |
| 10b | Base64 encode before Celery dispatch | `import_staging.py:259` | CORRECT |
| 10c | Admin-only on rollover | `people.py:419` | CORRECT |

## Wiring Gaps Surfaced by Review

These are pre-existing Gemini gaps (not Codex regressions) that the fixed code now depends on:

### Critical (Runtime Crashes)

| # | Issue | File | Details |
|---|-------|------|---------|
| R3-C1 | `stage_block_sheet()` doesn't exist | `import_tasks.py:128` | `HalfDayImportService` has `stage_block_template2()`, not `stage_block_sheet()`. Runtime `AttributeError`. |
| R3-C2 | `rollover_academic_year()` doesn't exist on `PersonController` | `people.py:445` | Route calls a controller method never implemented. Runtime `AttributeError`. |
| R3-C3 | `ImportBatch` model missing `academic_year` and `parent_batch_id` columns | `import_tasks.py:56,115` | No columns on model, no migration applied. Will crash at DB flush. |

### High (Pydantic Serialization Failures)

| # | Issue | File | Details |
|---|-------|------|---------|
| R3-H1 | `ImportBatchListItem` schema missing `academic_year`, `parent_batch_id` | `import_staging.py:337,341` | Pydantic `ValidationError` on response construction |
| R3-H2 | `ImportBatchResponse` schema missing same fields | `import_staging.py:398,405` | Same failure |

### Low

| # | Issue | File |
|---|-------|------|
| R3-L1 | Duplicate `from datetime import UTC` (line 16 + line 142) | `import_staging.py` (routes) — pre-existing |

## Out-of-Scope Changes by Codex

Codex added `academic_year` and `parent_batch_id` to the `list_batches` and `get_batch` response construction in `import_staging.py` routes (lines 337, 341, 398, 405). These were not in the 10-item fix list and reference schema/model fields that don't exist yet.

---
---

# Consolidated Fix Order (All Rounds)

Updated after fix pass (2026-02-25). Strikethrough = completed.

### Phase 1: Module-Level Crashes

1. ~~Fix `ExportMetadata` dataclass field ordering~~ (FIXED — Gemini Round 2)
2. ~~Restore missing stdlib imports in export service~~ (FIXED — Gemini Round 2)
3. ~~Fix `cast` import in `import_tasks.py`~~ (FIXED — Codex)
4. ~~Fix Celery `bytes` serialization~~ (FIXED — Codex, base64 encode/decode)
5. ~~Add `stage_block_sheet()` to `HalfDayImportService`~~ (FIXED — Fix pass. Extracts sheet into temp workbook, parses via `_parse_block_template2()`, stages into existing batch)
6. ~~Implement `PersonController.rollover_academic_year()` + `PersonService.rollover_academic_year()`~~ (FIXED — Fix pass. Advances PGY levels, graduates PGY-3, resets call counts via new AY records, updates legacy `Person.pgy_level`)

### Phase 2: Logic Bugs

7. ~~Fix `write_ref_sheet()` DefinedName API~~ (FIXED — Fix pass. `.append()` → `.add()` for openpyxl 3.1.5 `DefinedNameDict`)
8. ~~Fix longitudinal validator indentation~~ (FIXED — Codex)
9. ~~Fix NF code substring matching → exact match~~ (FIXED — Codex)
10. ~~Phase 3 DataValidation ordering~~ (FIXED — Reordered correctly in `_add_data_validation` and invoked from converter)
11. ~~`_copy_worksheet()` enrichments~~ (FIXED — `_copy_worksheet` now copies CF, DV, Comments, cell dimensions, and merged cells)

### Phase 3: Missing Infrastructure

12. ~~Create migration `20260224_person_ay` for `person_academic_years`~~ (FIXED — Fix pass. Creates table + seeds from `Person.pgy_level` for AY 2025)
13. ~~Fix migration chain: `20260224_annual_batch` now chains after `20260225_fix_nf_combo_reqs`~~ (FIXED — Fix pass. Was a parallel branch, now linear.)
14. ~~Add `academic_year` and `parent_batch_id` columns to `ImportBatch` model~~ (FIXED — Fix pass. Includes self-referential FK, parent/child relationships)
15. ~~Add `academic_year` and `parent_batch_id` to `ImportBatchListItem` and `ImportBatchResponse` schemas~~ (FIXED — Fix pass)
16. ~~Add `academic_years` relationship to `Person` model~~ (FIXED — Fix pass. Backref for `PersonAcademicYear.person`)

### Phase 4: Missing Features (FUTURE WORK)

These are future features, not bugs. They should be implemented in separate PRs:

17. ~~Write per-block `__ANCHORS__{N}__` sheets in year export~~ (FIXED — WP-2. Added anchor sheet generation during export)
18. ~~Add year-level export API endpoint~~ (FIXED — WP-9. Added `/schedule/year/xlsx` endpoint)
19. Implement row hash skip optimization (Phase 2 import)
20. ~~Fix engine supervision to use AY-scoped PGY~~ (FIXED — WP-5. `_get_pgy_level()` helper queries `PersonAcademicYear`, falls back to `Person.pgy_level`. All 3 usage sites updated.)
21. ~~Add LV import → absence record creation (Track C Step 3)~~ (FIXED — WP-6. `create_absences_from_lv_assignments()` groups LV codes into contiguous date ranges, checks for overlaps, creates Absence records.)
22. Implement longitudinal checks 4c (leave continuity) and 4d (1-in-7) — separate PR
23. ~~Wire Phase 1 metadata into export/import~~ (FIXED — WP-1. `_stamp_metadata()` adds `__SYS_META__` + `__REF__` sheets on export. Import reads metadata for audit trail + block validation.)

### Phase 5: Operational Guards

24a. ~~Add absence → preload refresh on CRUD~~ (FIXED — WP-7. `AbsenceService.create/update/delete_absence()` now call `SyncPreloadService.refresh_leave_preloads()` to keep LV preloads in sync.)
24. ~~Add role authorization to rollover and yearly upload endpoints~~ (FIXED — Codex)
25. ~~Add file size limit to `stage_yearly_import`~~ (FIXED — Codex)
26. ~~Fix test file bugs~~ (FIXED — Fix pass. Dict unpacking fix + sorted assertion for write_ref_sheet's sorted output)

### Phase 6: Tests and Cleanup

27. ~~Write tests for WP-1/5/6/7~~ (FIXED — 72 tests total: 11 export metadata, 10 engine AY PGY, 12 LV absence creation, 6 absence preload refresh, plus existing)
28. Fix medium-severity items (N+1 queries, sync export, named range duplication) — ongoing
29. ~~Remove unused imports~~ (FIXED — Codex)
30. ~~Replace `typing.List`/`Tuple` with builtins~~ (FIXED — Codex)
31. ~~Run lint on all modified files~~ (FIXED — Fix pass. All ruff checks pass)

---

# Gemini Direct Code Review (Feb 26, 2026)

> Gemini 3 Pro reviewed the codebase directly (not via roadmap) and identified 4 findings.
> Integrated into PRs #1200 and #1201.

| # | Finding | Severity | Resolution |
|---|---------|----------|------------|
| G1 | VACUUM runs inside transaction block | High | **FIXED** (PR #1201) — Uses `get_bind().connect().execution_options(isolation_level="AUTOCOMMIT")` |
| G2 | `SET` statements fail under asyncpg | High | **FIXED** (PR #1201) — Replaced with `set_config()` parameterized calls |
| G3 | TenantConnectionPoolManager race condition | Low | Advisory only — noted but not yet addressed (low-traffic path) |
| G4 | `max()` ValueError on empty sequence in equity constraints | Low | **FIXED** (PR #1201) — Added `default=0` parameter |

**Note:** Gemini made direct file edits (advise-only mode was requested). Changes were stashed, reviewed, and incorporated into the fix branch alongside Codex feedback fixes.
