# Stateful Round-Trip and Schema Hardening Roadmap

> **Status:** Planning — Excel phases unstarted; Schema Track A partially implemented
> **Created:** 2026-02-24
> **Updated:** 2026-03-02 — Track A call equity done (PRs #1199, #1202, #1217). Excel phases 1-4 remain backlog.
> **Origin:** Architectural proposal from external review of Excel import/export pipeline and database schema

---

## Problem Statement

The current Excel export/import pipeline treats the `.xlsx` file as a **dumb visual grid**. Coordinators export a schedule, make edits in Excel, and re-import. The import side uses fuzzy name matching (`difflib.SequenceMatcher`, threshold 0.85), heuristic column discovery, and no way to detect stale or wrong-block files. This produces fragile round-trips with high error rates.

Additionally, an external architecture review identified structural database issues that compound the Excel pipeline problems: PGY levels lack academic-year scoping (breaking historical queries after graduation rollover), and leave data is stored in three places with no sync mechanism (causing orphaned preloads and audit gaps).

## Vision

Transform the exported Excel workbook into a **Stateful Offline Client** — a file that carries its own metadata, identity anchors, input validation, and provenance tracking. In parallel, harden the database schema to properly model time-series academic state and single-source-of-truth leave accounting. Each phase/track is independently shippable and adds cumulative value.

## Roadmap Structure

Two parallel tracks, plus two evaluated-and-deferred proposals:

| Track | Phases | Domain | Priority |
|-------|--------|--------|----------|
| **Excel Pipeline** | Phases 1–4 | Export/import `.xlsx` enrichment | Medium |
| **Schema Hardening** | Tracks A, C | Database model fixes | A=**High** (July 1 deadline), C=Medium |
| **Deferred** | B, D | Evaluated, not needed now | N/A |

## Current State

| Capability | Status |
|------------|--------|
| Hidden metadata sheets | Not implemented |
| UUID anchoring for person/row identity | Not implemented |
| Data validation dropdowns | Not implemented |
| Dynamic conditional formatting | Partial — `scripts/ops/stamp_template_cf.py` does static CF stamping |
| Leave-day formulas | Not implemented |
| Override provenance comments | Not implemented |

---

## Phase 1: Phantom Database (Hidden Metadata Sheets)

**Goal:** Import rejects wrong-block or stale files before parsing begins.

**Value:** Eliminates the most common coordinator error — importing a Block 8 file into Block 9.

### Design

Two `veryHidden` sheets injected at export time:

1. **`__SYS_META__`** — JSON blob in cell A1 containing:
   ```json
   {
     "academic_year": 2026,
     "block_number": 10,
     "export_timestamp": "2026-02-24T10:30:00Z",
     "export_version": 1
   }
   ```

2. **`__REF__`** — Reference data with Excel Named Ranges:
   - `ValidRotations` — all rotation abbreviations for the block
   - `ValidActivities` — all activity codes for the block
   - Used by Phase 3 (DataValidation dropdowns) and Phase 2 (hash computation)

### File Changes

| File | Action | Details |
|------|--------|---------|
| `backend/app/services/excel_metadata.py` | **NEW** | Shared utility: `write_sys_meta_sheet()`, `write_ref_sheet()`, `read_sys_meta()`, `read_ref_codes()`, `compute_row_hash()`, `ExportMetadata` dataclass |
| `backend/app/services/canonical_schedule_export_service.py` | Modify | In `export_block_xlsx()` (~line 31): query rotation/activity codes, load workbook from bytes, call metadata writers, re-save |
| `backend/app/services/half_day_import_service.py` | Modify | After `load_workbook`, before row iteration (~line 44): call `read_sys_meta()`, validate block/year match, reject with `ValueError` on mismatch, pass through if absent (legacy) |
| `backend/app/services/import_staging_service.py` | Modify | In `stage_import()`: read `__SYS_META__`, return `StageResult(success=False, error_code="BLOCK_MISMATCH")` on mismatch |
| `backend/tests/services/test_excel_metadata.py` | **NEW** | Roundtrip write/read, Named Range resolution, legacy file returns None, block mismatch rejection, matching block acceptance |

### Backward Compatibility

All new behavior is gated by `if "__SYS_META__" in wb.sheetnames:`. Legacy files (without metadata) fall through to the existing fuzzy parsing path unchanged.

---

## Phase 2: Spatial UUID Anchoring

**Goal:** Deterministic person mapping (bypass fuzzy name matching); O(1) diff detection on unchanged rows.

**Value:** Eliminates fuzzy matching errors and enables skip-unchanged-rows optimization during import.

**Depends on:** Phase 1 (`compute_row_hash()` from `excel_metadata.py`)

### Design

A third `veryHidden` sheet — **`__ANCHORS__`** — with row numbers matching the visible schedule sheet exactly:

| Column | Content |
|--------|---------|
| A | `person_id` (UUID from database) |
| B | `block_assignment_id` (UUID from database) |
| C | `row_hash` (MD5 of person_id + rotation1 + rotation2 + all day codes) |

Import reads anchors before processing:
- If `person_id` exists in anchor → use it directly (skip fuzzy matching)
- If `row_hash` matches current DB state → skip entire row (unchanged)
- If `row_hash` differs → process row (changed by coordinator)

### File Changes

| File | Action | Details |
|------|--------|---------|
| `backend/app/services/half_day_xml_exporter.py` | Modify | `_fetch_people()` (~line 327): add `"id": p.id`. `_fetch_rotations()` (~line 345): add `"id": ba.id` |
| `backend/app/services/half_day_json_exporter.py` | Modify | `_build_person()` (~line 138): add `person_id` and `block_assignment_id` to payload dict |
| `backend/app/services/xml_to_xlsx_converter.py` | Modify | New `_write_anchor_sheet()` method: creates `__ANCHORS__` veryHidden sheet, row numbers match visible sheet, calls `compute_row_hash()` |
| `backend/app/services/half_day_import_service.py` | Modify | Before fuzzy matching: read `__ANCHORS__`, build `anchor_map: dict[int, {person_id, block_assignment_id, row_hash}]`, use anchor person_id when available, skip unchanged rows |
| `backend/tests/services/test_excel_metadata.py` | Extend | Anchor roundtrip, import uses anchor person_id, unchanged row skipped, changed row processed, legacy fallback to fuzzy matching |

### Notes

- `ParsedSlot` already has `person_id: UUID | None` (line 62 of `half_day_import_service.py`) — populate it from anchor data
- Row hash uses MD5 (not cryptographic, just change detection)
- No database schema changes required

---

## Phase 3: Strict UI Contracts (Data Validation)

**Goal:** Coordinators can only enter valid rotation and activity codes via Excel dropdowns.

**Value:** Prevents typos at the source — invalid codes are rejected by Excel before the file is ever re-imported.

**Depends on:** Phase 1 (Named Ranges from `__REF__` sheet)

### Design

Excel `DataValidation` objects reference the Named Ranges created in Phase 1:

```python
from openpyxl.worksheet.datavalidation import DataValidation

# Rotation columns: dropdown from ValidRotations named range
rot_dv = DataValidation(type="list", formula1="ValidRotations", allow_blank=True)
ws.add_data_validation(rot_dv)
for row in range(DATA_START_ROW, last_row + 1):
    rot_dv.add(ws.cell(row=row, column=BT2_COL_ROTATION1))
    rot_dv.add(ws.cell(row=row, column=BT2_COL_ROTATION2))

# Activity columns: dropdown from ValidActivities named range
act_dv = DataValidation(type="list", formula1="ValidActivities", allow_blank=True)
ws.add_data_validation(act_dv)
for row in range(DATA_START_ROW, last_row + 1):
    for col in range(BT2_COL_SCHEDULE_START, COL_SCHEDULE_END + 1):
        act_dv.add(ws.cell(row=row, column=col))
```

### File Changes

| File | Action | Details |
|------|--------|---------|
| `backend/app/services/xml_to_xlsx_converter.py` | Modify | After writing schedule data: add `DataValidation` objects for rotation and activity columns, referencing `ValidRotations` and `ValidActivities` Named Ranges |
| `backend/tests/services/test_excel_metadata.py` | Extend | Verify DataValidation present on rotation columns, on schedule columns, Named Range references are valid |

### Notes

- Import-side changes are minimal — the import already validates codes. DataValidation just prevents typos at the Excel UI layer.
- Coordinators see a dropdown arrow when they click a cell. They can still type manually, but Excel warns on invalid input.

---

## Phase 4: Stateful Leave Overlays and Provenance

**Goal:** Leave codes auto-color, day counts auto-calculate, override provenance is preserved.

**Value:** Eliminates the need for the separate `stamp_template_cf.py` script. Adds audit trail for manual overrides.

**Depends on:** Phase 1 (reference data), Phase 2 (person identity for provenance)

### Design

Three capabilities added to the exported workbook:

#### 4a. Dynamic Conditional Formatting

Replaces the static `stamp_template_cf.py` run. CF rules are injected during export using the same color scheme:

```python
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import PatternFill, Font

# Reuse color scheme from tamc_color_scheme.py
scheme = get_color_scheme()
for code, colors in scheme.items():
    rule = CellIsRule(
        operator='equal',
        formula=[f'"{code}"'],
        fill=PatternFill(start_color=colors.bg, fill_type='solid'),
        font=Font(color=colors.fg)
    )
    ws.conditional_formatting.add("F9:BI45", rule)
```

#### 4b. Leave-Day Formula Column

A formula column after the schedule grid that auto-calculates leave days:

```python
leave_col = 71  # After schedule grid + summary columns
ws.cell(row=8, column=leave_col, value="Leave Days")
for row in range(9, last_row + 1):
    ws.cell(row=row, column=leave_col, value=f'=COUNTIF(F{row}:BI{row},"LV")/2')
```

#### 4c. Provenance Comments on Overridden Cells

When a cell value was manually overridden (vs. solver/template-assigned), the exported cell carries a Comment:

```python
from openpyxl.comments import Comment

if day.get("am_override"):
    cell.comment = Comment(f"Original: {day['am_original']}", "AAPM Export")
```

### File Changes

| File | Action | Details |
|------|--------|---------|
| `backend/app/services/half_day_json_exporter.py` | Modify | In `_build_person()`: add `is_override` and `override_source` to day dict when `hda.is_override` is True |
| `backend/app/services/xml_to_xlsx_converter.py` | Modify | Add dynamic CF rules (replace `stamp_template_cf.py`), leave-day formula column, provenance Comments on override cells |
| `backend/tests/services/test_excel_metadata.py` | Extend | CF rules present in exported workbook, leave formula calculates correctly, override cells have comments with original code |

---

# Parallel Track: Schema Hardening

These are database model changes independent of the Excel pipeline. They address structural issues identified in an external architecture review (Feb 2026) and validated against the actual codebase.

---

## Track A: Person Academic Years (PGY Graduation Rollover)

**Priority: HIGH — must ship before July 1 graduation rollover**

> **Audit Finding (Feb 26, 2026 — CORRECTED):** The Perplexity audit (Finding 4.1) incorrectly claimed the `PersonAcademicYear` migration was "created then dropped." Investigation shows migration `20260224_person_ay.py` exists and was NEVER dropped. The real issue: the Alembic chain has a branching divergence (two heads) after `20260219_add_gt_tables`, so migrations through `20260224_person_ay` haven't been applied to the running DB. The model at `backend/app/models/person_academic_year.py` is ready — just needs the Alembic heads merged and pending migrations applied. 67+ files reference `Person.pgy_level` directly and must be updated. July 1 deadline is ~16 weeks away; no rollover logic, PGY advancement automation, or call count reset mechanism exists. See `docs/perplexity-uploads/started/full-codebase/RESULTS.md`, Finding 4.1 (note: audit's "dropped" conclusion is incorrect).
>
> **Progress (Feb 26, 2026):** Alembic heads merged (PR #1196). `_sync_academic_year_call_counts()` implemented with idempotent recalculation from `call_assignments` source of truth (PR #1199). Uses CASE expression for FMIT weekend split (PR #1202). PersonAcademicYear migration exists; chain ready for `alembic upgrade head`. Gemini tiebreaker confirmed app-level service approach (Option A).

**Goal:** Separate immutable person identity from time-varying academic state so that historical schedules remain mathematically accurate after PGY advancement.

### Current Problem

`pgy_level` is a scalar field on the `Person` model with no academic year scoping:

```python
# backend/app/models/person.py (current)
pgy_level = Column(Integer, nullable=True)    # PGY 1-3, no AY context
clinic_min = Column(Integer)                   # Changes per PGY level
clinic_max = Column(Integer)                   # Changes per PGY level
sunday_call_count = Column(Integer, default=0) # "Reset annually" — but no reset code exists
weekday_call_count = Column(Integer, default=0)
fmit_weeks_count = Column(Integer, default=0)
```

**What breaks on July 1:** When an R1 becomes an R2, updating `person.pgy_level = 2` retroactively corrupts all historical queries. The ACGME validator, scheduling engine, compliance reports, and ML pipeline all read `Person.pgy_level` as eternal truth. There is no graduation logic, no PGY advancement automation, and no call count reset mechanism despite documentation saying counts "reset annually."

### Design

New table separating the *Biological Person* from their *Academic State*:

**`person_academic_years`**

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `person_id` | FK → `people` | |
| `academic_year` | Integer | e.g., 2025 for AY 2025-2026 |
| `pgy_level` | Integer 1-3 | PGY level for this specific AY |
| `clinic_min` | Integer | Clinic constraints for this AY |
| `clinic_max` | Integer | |
| `sunday_call_count` | Integer (default 0) | Resets naturally — new row per AY |
| `weekday_call_count` | Integer (default 0) | |
| `fmit_weeks_count` | Integer (default 0) | |
| `is_graduated` | Boolean (default False) | True when PGY-3 completes |
| `created_at` | DateTime | |
| `updated_at` | DateTime | |

**Unique constraint:** `(person_id, academic_year)`

The `Person` model keeps its `pgy_level` field for backward compatibility but derives it from the current AY's `PersonAcademicYear` record. Call counts are per-AY rows — no reset logic needed; each July 1 starts a fresh row.

### File Changes

| File | Action | Details |
|------|--------|---------|
| `backend/app/models/person_academic_year.py` | **NEW** | SQLAlchemy model with relationship to `Person` |
| `backend/app/models/person.py` | Modify | Add `academic_years` relationship; add `@hybrid_property` for `current_pgy_level` that reads from current AY record; deprecate direct `pgy_level` writes |
| `backend/alembic/versions/YYYYMMDD_person_ay.py` | **NEW** | Create table + data migration seeding from current `pgy_level` values |
| `backend/app/schemas/person.py` | Modify | Add `PersonAcademicYear` schema; update `PersonResponse` to include AY-scoped fields |
| `backend/app/repositories/person.py` | Modify | Scope PGY queries to academic year: `get_residents_by_pgy(pgy_level, academic_year)` |
| `backend/app/scheduling/engine.py` | Modify | Read PGY from `person_academic_years` for the target block's AY |
| `backend/app/scheduling/validator.py` | Modify | Same — use AY-scoped PGY level for ACGME validation |
| `backend/app/services/person_service.py` | Modify | CRUD for academic year records; rollover method for July 1 |
| `backend/app/api/routes/people.py` | Modify | Endpoints for AY progression, rollover trigger |
| `backend/tests/` | **NEW** | Test historical PGY queries, rollover, call count isolation per AY |

### Migration Strategy

1. Create `person_academic_years` table
2. Data migration: for each `Person` with `pgy_level IS NOT NULL`, insert a `PersonAcademicYear` row for the current AY (2025)
3. Keep `Person.pgy_level` column — deprecated but not dropped (too many consumers to update atomically)
4. Gradually migrate consumers to read from `person_academic_years`

---

## Track C: Leave Single-Source-of-Truth (Absence → Preload Sync)

**Priority: MEDIUM — prevents orphaned preloads and audit trail gaps**

> **Architectural Decision (Feb 26, 2026 — Gemini 3 Pro tiebreaker):** Two independent research sessions (annual-leap + full-codebase) produced conflicting designs for cross-block absence handling. Gemini Pro 3.1 adjudicated:
>
> - **Option A wins (single record, projected per-block).** Splitting a real-world leave event at block boundaries is an anti-pattern ("domain leakage"). A 10-day vacation crossing blocks is ONE Absence record; the solver clips dates in Python.
> - **Application-level service logic, NOT triggers.** PostgreSQL triggers are hostile to async SQLAlchemy 2.0 — trigger-created rows bypass the ORM identity map, causing stale reads. Use Unit of Work pattern with PG15 `MERGE` in Python instead.
> - **Triggers OK for audit only.** Append-only `absence_audit_log` can use triggers since audit data is rarely read back in the same request context.
> - **Migration path:** Add `absence_id` FK to `half_day_assignments` → backfill from existing LV preloads → add CHECK constraint → refactor import pipeline.
>
> Title changed from "Leave Event-Sourcing" to reflect that this is NOT event sourcing (per annual-leap Section 4: "hybrid stamped + audit log" model).

**Goal:** Make the `absences` table the single source of truth for leave. Eliminate stale derived state.

### Current Problem

Leave exists in three places with uni-directional, write-once data flow:

| Location | What's Stored | Updated When Absence Changes? |
|----------|--------------|-------------------------------|
| `absences` table | Date range, type, approval status | Source of truth |
| `block_assignments.has_leave` / `leave_days` | Summary flag + day count | **Never** (write-once at block scheduling time) |
| `half_day_assignments` (LV-AM/LV-PM activities) | Daily preloaded slots, locked as `source='preload'` | **Never** (write-once at preload time) |

**Three confirmed failure patterns:**

1. **Orphaned preloads:** Deleting or shortening an absence does NOT clear the corresponding LV-AM/LV-PM half-day assignments. The person appears "on leave" in the schedule after they've returned.
2. **Stale block summary:** `block_assignments.leave_days` is computed once and never updated. Modifying an absence leaves the count wrong — affects reporting/dashboards.
3. **Import audit gap:** Importing "LV" codes from Excel creates half-day assignments but does NOT create absence records. The audit trail has leave in the schedule but no corresponding approved absence.

### Design

**Step 1: Derive block-level leave dynamically**

Drop `has_leave` and `leave_days` from the `block_assignments` table. Replace with computed properties:

```python
# backend/app/models/block_assignment.py
@hybrid_property
def has_leave(self) -> bool:
    """Derived from absences table — no stale data possible."""
    return any(a.overlaps(self.block_start, self.block_end) for a in self.person.absences)

@hybrid_property
def leave_days(self) -> int:
    """Count of leave days within this block's date range."""
    return sum(a.overlap_days(self.block_start, self.block_end) for a in self.person.absences)
```

**Step 2: Absence CRUD propagates to preloads**

When an absence is created, updated, or deleted, the service layer refreshes LV-AM/LV-PM preloads for the affected date range:

```python
# backend/app/services/absence_service.py
async def create_absence(self, ...) -> Absence:
    absence = await self.repo.create(...)
    await self.preload_service.refresh_leave_preloads(
        person_id=absence.person_id,
        start_date=absence.start_date,
        end_date=absence.end_date
    )
    return absence

async def delete_absence(self, absence_id: UUID) -> None:
    absence = await self.repo.get(absence_id)
    await self.repo.delete(absence_id)
    await self.preload_service.refresh_leave_preloads(
        person_id=absence.person_id,
        start_date=absence.start_date,
        end_date=absence.end_date
    )
```

The `refresh_leave_preloads()` method:
1. Deletes all LV-AM/LV-PM preloads for the person in the date range
2. Re-queries blocking absences for that range
3. Re-creates preloads for dates still covered by an absence

**Step 3: Excel import of "LV" codes creates absence records**

When the import pipeline encounters LV codes that don't correspond to existing absences, it creates absence records to close the audit gap:

```python
# In half_day_import_service.py, after parsing LV slots:
for person_id, lv_dates in leave_dates_by_person.items():
    existing = await absence_repo.get_for_person_in_range(person_id, min(lv_dates), max(lv_dates))
    uncovered = lv_dates - covered_by(existing)
    if uncovered:
        await absence_service.create_absence(
            person_id=person_id,
            start_date=min(uncovered),
            end_date=max(uncovered),
            absence_type="vacation",
            source="excel_import"
        )
```

### File Changes

| File | Action | Details |
|------|--------|---------|
| `backend/app/models/block_assignment.py` | Modify | Replace `has_leave`/`leave_days` columns with `@hybrid_property` computed from absences |
| `backend/app/schemas/block_assignment.py` | Modify | Update schema to use `@computed_field` for leave fields |
| `backend/app/services/absence_service.py` | Modify | Add preload refresh calls on create/update/delete |
| `backend/app/services/preload/sync_preload_service.py` | Modify | Add `refresh_leave_preloads(person_id, start_date, end_date)` method |
| `backend/app/services/half_day_import_service.py` | Modify | Create absence records from imported LV codes |
| `backend/alembic/versions/YYYYMMDD_drop_leave_cols.py` | **NEW** | Drop `has_leave`/`leave_days` columns from `block_assignments` |
| `backend/tests/` | **NEW** | Absence deletion clears preloads, modification updates preloads, import creates absences, computed leave_days matches absences |

### Migration Strategy

**Phase 1 — Schema (Alembic):**
1. Add `absence_id` FK (nullable) and `preload_source` column to `half_day_assignments`
2. Add `@hybrid_property` methods on `block_assignment` that compute from absences (backward compatible)

**Phase 2 — Data backfill (Alembic data migration):**
1. Query all `HalfDayAssignment` rows where `activity_code IN ('LV-AM', 'LV-PM')` and `absence_id IS NULL`
2. Group contiguous dates per person into `(start_date, end_date)` ranges (reuse `_dates_to_ranges()` logic from `half_day_import_service.py:562`)
3. Bulk insert `Absence` records for collapsed ranges
4. Bulk update `half_day_assignments` to link `absence_id` to newly created `Absence.id`s

**Phase 3 — Enforce integrity:**
1. Add CHECK constraint: `activity_code NOT IN ('LV-AM', 'LV-PM') OR absence_id IS NOT NULL`
2. Migrate all consumers from column reads to property reads
3. Drop `has_leave`/`leave_days` columns in a separate migration once verified

**Context builder query (solver integration):**
```python
# Two date ranges overlap if: (Start_A <= End_B) AND (End_A >= Start_B)
stmt = select(Absence).where(
    and_(
        Absence.start_date <= block_end,
        Absence.end_date >= block_start,
        Absence.status.in_(["approved", "pending"])
    )
).order_by(Absence.person_id, Absence.start_date)
```

---

# Evaluated and Deferred

Two of the four proposals from the external review were evaluated against the codebase and deferred. Documenting the reasoning here for future reference.

## Deferred B: Rotation Spans Table (Normalizing Secondary Rotation)

**Proposal:** Replace `block_assignments.rotation_template_id` + `secondary_rotation_template_id` with a 1-to-many `block_rotation_spans` table.

**Why deferred:**

1. **2-column model maps 1:1 to the Excel template format** (2 rotation columns). Normalizing would break Excel import/export, which must remain the primary interface.
2. **NF combined rotations don't use `secondary_rotation_template_id`** — they're handled internally by the preload system via date-based activity code resolution in `rotation_codes.py`. The "DERM/NF" display issue comes from Excel parsing heuristics, not the database schema.
3. **No evidence of 3+ phase blocks** in 6 months of operation across all 6 NF combined rotation types.
4. **17 files** reference `secondary_rotation` — refactoring would be high cost for zero current benefit.

**Revisit trigger:** If requirements emerge for 3+ rotation phases within a single 28-day block.

## Deferred D: Actual Duty Hour Timestamps

**Proposal:** Add `actual_start_time` and `actual_end_time` (timestamp with time zone) to `half_day_assignments` or `activities` for precise ACGME duty-hour tracking.

**Why deferred:**

1. **The AM/PM model is conservatively ACGME-safe.** Each half-day slot = 6 hours (fixed constant). Maximum possible: 12 slots/day × 6 hours = 72 hours/week, well under the 80-hour limit. The approximation cannot produce false negatives.
2. **1-in-7 rule** is enforced via consecutive-day counting, which is sufficient.
3. **Night Float** is handled via activity code patterns and post-call mandatory activity assignments (PCAT/DO), not timestamps.
4. **This is standard** — every residency scheduling system reviewed uses slot-based modeling, not timestamp-based.

**What actual times would enable:** Precise fatigue modeling (FRMS integration), circadian-aware scheduling, exact 24+4 hour boundary enforcement. These are future optimization opportunities, not compliance gaps.

**Revisit trigger:** If ACGME changes reporting requirements to demand actual clock hours, or if the FRMS fatigue module needs real timestamps for risk scoring.

---

## File Change Summary

### Excel Pipeline (Phases 1–4)

| File | Phases | Action |
|------|--------|--------|
| `backend/app/services/excel_metadata.py` | 1 | **NEW** — metadata read/write + row hash |
| `backend/app/services/canonical_schedule_export_service.py` | 1 | Modify — query ref data, inject meta sheets |
| `backend/app/services/half_day_import_service.py` | 1, 2, C | Modify — read meta + anchors, validate, skip unchanged, create absences from LV |
| `backend/app/services/import_staging_service.py` | 1 | Modify — metadata validation before staging |
| `backend/app/services/half_day_xml_exporter.py` | 2 | Modify — include `id` in `_fetch_people`/`_fetch_rotations` |
| `backend/app/services/half_day_json_exporter.py` | 2, 4 | Modify — add UUIDs + override flags to person dict |
| `backend/app/services/xml_to_xlsx_converter.py` | 2, 3, 4 | Modify — anchors sheet, DataValidation, CF, comments |
| `backend/tests/services/test_excel_metadata.py` | 1, 2, 3, 4 | **NEW** — roundtrip, validation, backward compat tests |

### Schema Hardening (Tracks A, C)

| File | Track | Action |
|------|-------|--------|
| `backend/app/models/person_academic_year.py` | A | **NEW** — AY-scoped PGY level, clinic constraints, call counts |
| `backend/app/models/person.py` | A | Modify — add relationship, hybrid property for current PGY |
| `backend/app/models/block_assignment.py` | C | Modify — replace `has_leave`/`leave_days` with computed properties |
| `backend/app/schemas/person.py` | A | Modify — add PersonAcademicYear schema |
| `backend/app/schemas/block_assignment.py` | C | Modify — computed leave fields |
| `backend/app/repositories/person.py` | A | Modify — AY-scoped queries |
| `backend/app/scheduling/engine.py` | A | Modify — read PGY from AY record |
| `backend/app/scheduling/validator.py` | A | Modify — AY-scoped PGY for ACGME checks |
| `backend/app/services/person_service.py` | A | Modify — CRUD for AY records, rollover |
| `backend/app/services/absence_service.py` | C | Modify — preload refresh on CRUD |
| `backend/app/services/preload/sync_preload_service.py` | C | Modify — `refresh_leave_preloads()` method |
| `backend/app/api/routes/people.py` | A | Modify — AY progression endpoints |
| `backend/alembic/versions/YYYYMMDD_person_ay.py` | A | **NEW** — create table + data migration |
| `backend/alembic/versions/YYYYMMDD_drop_leave_cols.py` | C | **NEW** — drop stale leave columns |

## Implementation Notes

### Excel Pipeline (Phases 1–4)
- **Backward compatibility:** All new behavior gated by `if "__SYS_META__" in wb.sheetnames:`. Legacy files fall back to fuzzy matching.
- **No database schema changes** in Phases 1–4. No migrations required.
- **No frontend changes** — all backend export/import pipeline.
- **Each phase is independently shippable** and adds value on its own.
- **`veryHidden` sheets** (`ws.sheet_state = 'veryHidden'`) cannot be unhidden from the Excel UI — coordinators never see them.

### Schema Hardening (Tracks A, C)
- **Track A is time-critical:** Must ship before July 1 when PGY-1→PGY-2 and PGY-2→PGY-3 advancement occurs and PGY-3 residents graduate. After that date, updating `Person.pgy_level` corrupts historical ACGME validation.
- **Track C is incremental:** Can be done in 3 steps (computed properties → preload refresh → import audit fix), each independently shippable.
- **Both tracks require migrations** — follow Alembic safety rules (≤64 char revision IDs, test rollback).
- **Backward compatibility for Track A:** Keep `Person.pgy_level` column; derive from current AY's `PersonAcademicYear` record. Consumers migrate gradually.
- **Backward compatibility for Track C:** Add hybrid properties first (both column and property work), then drop columns in a later migration.

## Related Files

- `scripts/ops/stamp_template_cf.py` — existing static CF stamping (replaced by Phase 4a)
- `backend/app/services/tamc_color_scheme.py` — color scheme definitions
- `docs/architecture/import-export-system.md` — existing import/export architecture docs
- `backend/app/models/person.py` — current Person model with scalar `pgy_level`
- `backend/app/models/absence.py` — current absence model (source of truth for leave)
- `backend/app/models/block_assignment.py` — current model with `has_leave`/`leave_days` columns
- `backend/app/services/preload/sync_preload_service.py` — `_load_absences()` at line 161 (current leave preload logic)
