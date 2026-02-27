# Annual Workbook Architecture: 14-Sheet Master Schedule

> **Status:** Planning (documentation only)
> **Created:** 2026-02-24
> **Depends on:** [Stateful Round-Trip Roadmap](excel-stateful-roundtrip-roadmap.md) Phases 1-2
> **Origin:** External architecture review — "Whole Academic Year upload is the architectural holy grail for residency scheduling"

---

## Overview

Elevate the Excel import/export from block-by-block to a single 14-sheet workbook representing an entire academic year. This turns Excel from a fragile monthly checklist into a relational, offline master-planning tool.

**Current state:** The pipeline is entirely block-scoped. `ImportBatch` targets one block, `CanonicalScheduleExportService.export_block_xlsx()` handles one block, import processing is synchronous, and no cross-block validation exists.

**Target state:** A single `.xlsx` file with 14 visible sheets (Blocks 0–13) plus hidden system sheets, processed asynchronously via Celery, with longitudinal ACGME validation across the entire year.

---

## 1. Calendar Math: The Fudge Factor is Industry Standard

The non-Gregorian academic year math is **correct and should not be changed**. This is the same approach used by enterprise GME scheduling engines (MedHub, Amion).

### The Problem

- A strict ACGME academic year is exactly **365 days** (366 in leap years), anchored July 1 – June 30.
- 13 blocks × 28 days = **364 days**.
- A strictly repeating 28-day cycle drifts backwards every year, eventually pushing Block 1 into early June, breaking military PCS dates and graduation requirements.

### The Solution: Shock Absorber Blocks

By pinning the start (July 1) and end (June 30) and using explicit `start_date`/`end_date` columns in `academic_blocks`, the system creates natural shock absorbers:

| Block | Duration | Purpose |
|-------|----------|---------|
| **Block 0** (Orientation) | 0–6 days | Absorbs the calendar shift between July 1 and the first Thursday |
| **Blocks 1–12** (Core Engine) | Exactly 28 days each | Stable Thursday→Wednesday cycles (optimized for Wednesday night inpatient call → Thursday morning clinic transitions) |
| **Block 13** (Cleanup) | 22–30 days | Absorbs remaining days through June 30 |

Because `academic_blocks` stores explicit dates rather than computing from a 28-day formula, the database natively handles leap years and variable-length edge blocks.

### Key Files

- `backend/app/models/academic_block.py` (lines 35–112) — `AcademicBlock` model with `start_date`, `end_date`, `is_variable_length`
- `backend/app/utils/academic_blocks.py` (lines 60–148) — Block date calculation: Block 0 = July 1 through day before first Thursday, Blocks 1–12 = 28 days Thursday-aligned, Block 13 = remainder through June 30
- `docs/architecture/BLOCK_ZERO_FUDGE.md` — Full history of Block 0/13 edge cases and regression tests

---

## 2. 14-Sheet Master Workbook Design

### 2a. Global Metadata Sheet

The `__SYS_META__` hidden sheet (from Phase 1 of the Stateful Round-Trip roadmap) expands from single-block metadata to a year-level manifest:

```json
{
  "academic_year": 2025,
  "export_timestamp": "2026-02-24T10:00:00Z",
  "export_version": 2,
  "block_map": {
    "Block 0":  "uuid-for-academic-block-0",
    "Block 1":  "uuid-for-academic-block-1",
    "Block 2":  "uuid-for-academic-block-2",
    "Block 12": "uuid-for-academic-block-12",
    "Block 13": "uuid-for-academic-block-13"
  }
}
```

**Backward compatibility:** Single-block files (no `block_map` key) continue to work. The presence of `block_map` signals a year-level workbook. Import logic gates on `if "block_map" in manifest:`.

### 2b. Dynamic Grid Sizing for Stub Blocks

Standard blocks get the full 28-day grid (56 AM/PM columns). But Block 0 might only be 3 days long and Block 13 might be 25. Giving coordinators blank columns for phantom days will cause scheduling errors.

**Solution:** The export backend uses `(block.end_date - block.start_date).days + 1` to determine actual block length, then:

- Draws the standard 28-day grid for all blocks
- For **stub blocks** (Block 0, Block 13), fills phantom columns beyond the actual block length with dark gray fill and locks them via `openpyxl` sheet protection

```python
from openpyxl.styles import PatternFill, Protection

PHANTOM_FILL = PatternFill(start_color="404040", end_color="404040", fill_type="solid")
LOCKED = Protection(locked=True)

actual_days = (block.end_date - block.start_date).days + 1
for day_index in range(actual_days, 28):
    for slot in range(2):  # AM, PM
        col = BT2_COL_SCHEDULE_START + (day_index * COLS_PER_DAY) + slot
        for row in range(DATA_START_ROW, last_row + 1):
            cell = ws.cell(row=row, column=col)
            cell.fill = PHANTOM_FILL
            cell.protection = LOCKED
            cell.value = None

ws.protection.sheet = True
ws.protection.password = None  # Visual lock, not security
```

This physically prevents coordinators from interacting with days that don't exist in that block.

### 2c. Shared vs. Per-Sheet Hidden Data

| Hidden Sheet | Scope | Notes |
|-------------|-------|-------|
| `__SYS_META__` | Workbook-level | One sheet, year-level manifest with `block_map` |
| `__REF__` | Workbook-level | One sheet — rotations and activities don't change mid-year. `ValidRotations` and `ValidActivities` Named Ranges shared across all block sheets |
| `__ANCHORS__{N}__` | Per-block | One hidden sheet per block sheet, containing person UUIDs and row hashes for that specific block. Row numbers match the corresponding visible sheet |

---

## 3. Celery Pipeline Architecture

### 3a. Year-Level Import Batch Model

The `ImportBatch` model (currently at `backend/app/models/import_staging.py`, lines 72–154) gains two fields:

```python
# New fields on ImportBatch
academic_year = Column(Integer, nullable=True)  # Set for year-level batches
parent_batch_id = Column(GUID, ForeignKey("import_batches.id"), nullable=True)  # Self-referential FK
```

**Hierarchy:**
- **Year-level batch** (parent): `academic_year=2025`, `parent_batch_id=NULL`, `target_block=NULL`
- **Block-level batches** (children): `parent_batch_id=parent.id`, `target_block=N`
- **Legacy single-block imports:** `parent_batch_id=NULL`, `target_block=N` (unchanged)

### 3b. Celery Task Chain

When a coordinator uploads the master workbook, the API endpoint hands off to a Celery task instead of processing synchronously:

```python
# backend/app/tasks/import_tasks.py (NEW)

@shared_task(bind=True)
def process_yearly_workbook(self, file_bytes: bytes, academic_year: int, user_id: str):
    """Parse a 14-sheet master workbook into staged assignments.

    ~44,000 cells (14 sheets × ~56 residents × 56 half-days) ≈ 3 seconds.
    """
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    manifest = json.loads(wb["__SYS_META__"]["A1"].value)

    # Validate manifest
    if manifest.get("academic_year") != academic_year:
        raise ValueError(f"Workbook is for AY {manifest['academic_year']}, expected {academic_year}")

    # Create parent batch
    parent_batch = create_import_batch(
        academic_year=academic_year,
        status="STAGED"
    )

    block_map = manifest.get("block_map", {})

    for sheet_name in wb.sheetnames:
        if sheet_name.startswith("__"):  # Skip hidden system sheets
            continue

        ws = wb[sheet_name]
        block_uuid = block_map.get(sheet_name)

        if not block_uuid:
            log.warning(f"Sheet '{sheet_name}' not in block_map, skipping")
            continue

        # Create child batch for this block
        child_batch = create_import_batch(
            parent_batch_id=parent_batch.id,
            target_block=extract_block_number(sheet_name),
        )

        # Reuse existing per-sheet parsing logic
        # Uses UUID anchors from __ANCHORS__{N}__ if present
        stage_assignments_for_sheet(ws, block_uuid, child_batch.id)

    # Run cross-block validation (Section 4)
    run_longitudinal_validation(parent_batch.id)

    return parent_batch.id
```

### 3c. Coordinated Rollback

| Scope | Mechanism |
|-------|-----------|
| **Full year rollback** | Rolling back parent batch cascades `DELETE` to all child batches via FK cascade. All staged assignments removed. |
| **Single block re-import** | Upload a single-block file targeting one block. Creates a new child batch under the same parent, replacing the old child. |
| **24-hour window** | Applies to the parent batch timestamp. After 24 hours, `rollback_available = False` propagates to all children. |

### 3d. Year-Level Export

A new method on `CanonicalScheduleExportService`:

```python
async def export_year_xlsx(self, academic_year: int) -> bytes:
    """Export all blocks for an academic year as a single 14-sheet workbook."""
    wb = Workbook()
    wb.remove(wb.active)  # Remove default sheet

    blocks = await self.db.execute(
        select(AcademicBlock)
        .filter_by(academic_year=academic_year)
        .order_by(AcademicBlock.block_number)
    )

    block_map = {}
    for block in blocks.scalars():
        # Reuse existing single-block export logic per sheet
        sheet_data = await self._export_block_data(block)
        ws = wb.create_sheet(title=f"Block {block.block_number}")
        self._write_block_to_sheet(ws, sheet_data, block)
        self._apply_phantom_columns(ws, block)  # Gray out non-existent days
        block_map[f"Block {block.block_number}"] = str(block.id)

    # Write shared system sheets
    write_sys_meta_sheet(wb, ExportMetadata(
        academic_year=academic_year,
        block_number=None,  # Year-level
        export_timestamp=datetime.now(UTC).isoformat(),
        block_map=block_map,
    ))
    write_ref_sheet(wb, rotations, activities)  # Shared across all blocks

    # Write per-block anchor sheets
    for block in blocks:
        write_anchor_sheet(wb, block, sheet_name=f"__ANCHORS_{block.block_number}__")

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
```

---

## 4. The Superpower: Longitudinal ACGME Validation

Parsing the whole workbook into `import_staged_assignments` simultaneously enables **cross-block constraint solving** that block-by-block imports cannot do:

### 4a. ACGME Night Float Caps

> *"Dr. Smith is scheduled for 5 blocks of Night Float this year (ACGME max is 4)."*

Query across all child batches: count blocks where any staged assignment has an NF activity code for a given person.

### 4b. Clinic Minimums

> *"Dr. Jones only has 32 half-days of FM Clinic scheduled across all 13 sheets (graduation requirement is 40)."*

Aggregate `COUNTIF activity IN ('CLI', 'FMC')` across all staged assignments for each person.

### 4c. Cross-Block Leave Continuity

If a resident takes leave from the last week of Block 2 into the first week of Block 3, a single-block parser breaks the continuity. The multi-sheet parser can:

1. Detect contiguous LV cells across sheet boundaries
2. Generate a single, clean date range in the `absences` table
3. Prevent double-counting in leave day calculations

### 4d. Cross-Boundary 1-in-7 Rule

If a resident is on Inpatient in Block 4 and Inpatient in Block 5, the system can verify they got their ACGME-mandated "1 day off in 7" crossing over the Wednesday/Thursday block boundary. Single-block validation has a blind spot at these seams.

### Validation Implementation

```python
# backend/app/services/longitudinal_validator.py (NEW)

async def run_longitudinal_validation(parent_batch_id: UUID) -> list[ValidationError]:
    """Cross-block validation for year-level imports."""
    errors = []

    # Get all staged assignments across child batches
    all_staged = await get_staged_for_parent(parent_batch_id)

    # Group by person
    by_person = group_by(all_staged, key=lambda s: s.matched_person_id)

    for person_id, assignments in by_person.items():
        # 4a: NF block count
        nf_blocks = count_nf_blocks(assignments)
        if nf_blocks > MAX_NF_BLOCKS_PER_YEAR:
            errors.append(ValidationError(
                person_id=person_id,
                rule="ACGME_NF_CAP",
                message=f"Night Float in {nf_blocks} blocks (max {MAX_NF_BLOCKS_PER_YEAR})"
            ))

        # 4b: Clinic minimums
        clinic_count = count_clinic_halves(assignments)
        if clinic_count < MIN_CLINIC_HALVES_PER_YEAR:
            errors.append(ValidationError(
                person_id=person_id,
                rule="CLINIC_MINIMUM",
                message=f"{clinic_count} clinic half-days (min {MIN_CLINIC_HALVES_PER_YEAR})"
            ))

        # 4c: Cross-block leave continuity
        leave_ranges = detect_cross_block_leave(assignments)
        # Returns consolidated date ranges spanning block boundaries

        # 4d: 1-in-7 across block boundaries
        violations = check_consecutive_days_across_blocks(assignments)
        errors.extend(violations)

    return errors
```

---

## Audit Warnings (Feb 26, 2026)

The full-codebase Perplexity audit (session #8) identified risks relevant to this architecture:

- **Finding 4.5 — Hardcoded column positions:** Any YTD_SUMMARY formulas that reference block sheet columns by position (e.g., col 62 for Clinic, col 69 for FMIT) will silently break if the block sheet template layout changes. Recommendation: either compute column positions dynamically from the template structure at export time, or use Excel named ranges that survive column insertions.
- **Finding 4.1 — PersonAcademicYear migration not applied (Alembic chain branching):** The migration `20260224_person_ay.py` exists and was never dropped — the Perplexity audit incorrectly claimed it was. The real issue is the Alembic chain has a branching divergence (two heads) after `20260219_add_gt_tables`, so the migration hasn't been applied to the running DB. Annual workbook features that depend on PGY-scoped queries (NF caps per PGY, clinic minimums by year) cannot work until the Alembic heads are merged and pending migrations applied.
- **Finding 1.1.1 — Schema drift:** 51 SQLAlchemy models lack migrations. Before building the Celery pipeline (Section 3), verify that `import_batches`, `import_staged_assignments`, and related tables actually exist in the database.

See `docs/perplexity-uploads/started/full-codebase/RESULTS.md` for full audit.

---

## 5. File Changes Summary

| File | Action | Details |
|------|--------|---------|
| `backend/app/models/import_staging.py` | Modify | Add `academic_year` and `parent_batch_id` (self-FK) to `ImportBatch` |
| `backend/app/services/import_staging_service.py` | Modify | Add year-level orchestration, parent/child batch creation |
| `backend/app/services/canonical_schedule_export_service.py` | Modify | Add `export_year_xlsx()` method, `_apply_phantom_columns()` |
| `backend/app/services/excel_metadata.py` | Modify | `ExportMetadata` gains `block_map` field; `write_sys_meta_sheet` handles year-level JSON |
| `backend/app/tasks/import_tasks.py` | **NEW** | Celery task `process_yearly_workbook()` |
| `backend/app/services/longitudinal_validator.py` | **NEW** | Cross-block ACGME validation (NF caps, clinic mins, leave continuity, 1-in-7) |
| `backend/app/api/routes/import_staging.py` | Modify | Add year-level upload endpoint, async task dispatch |
| `backend/alembic/versions/YYYYMMDD_annual_batch.py` | **NEW** | Add `academic_year` + `parent_batch_id` to `import_batches` |
| `backend/app/models/academic_block.py` | Read-only | No changes — already has `start_date`, `end_date`, `is_variable_length` |
| `backend/app/utils/academic_blocks.py` | Read-only | No changes — block date calculations reused as-is |

---

## 6. Dependencies and Sequencing

```
Phase 1 (Phantom Database)
    └─→ Phase 2 (UUID Anchoring)
            └─→ Annual Workbook (this document)
                    ├── Export: year-level workbook with 14 sheets + shared metadata
                    ├── Import: Celery task chain with parent/child batches
                    └── Validation: longitudinal cross-block ACGME checks
```

**Can be built incrementally:**
1. **Export-only first:** Generate the 14-sheet workbook with phantom column handling. Coordinators can review the full year in one file.
2. **Import second:** Add Celery pipeline, parent/child batch model, year-level upload endpoint.
3. **Validation last:** Longitudinal ACGME checks layered on top of the multi-block staged data.

---

## Related Documents

- [Stateful Round-Trip Roadmap](excel-stateful-roundtrip-roadmap.md) — Phases 1–4 (prerequisites)
- [Block Zero Fudge](BLOCK_ZERO_FUDGE.md) — Calendar math and shock absorber block design
- [Import-Export System](import-export-system.md) — Current single-block pipeline architecture
