# Excel Round-Trip Pipeline — Strategic Advice Brief

> **Purpose:** Self-contained prompt for AI-assisted strategic review of the Excel import/export round-trip pipeline for a military medical residency scheduler.
> **Target AI:** Gemini Pro 3.1 (Extended Thinking)
> **Project:** Military medical residency scheduler (ACGME-compliant, OPSEC-sensitive)
> **Created:** 2026-02-25
> **Master Priority List:** Item #35

---

## Section 1: Mission

### What We Need

Strategic advice on the Excel round-trip pipeline — the primary workflow where coordinators:

1. **Export** a block schedule from the app as `.xlsx`
2. **Edit** in Excel (reassign residents, add leave, change rotations)
3. **Re-import** the modified file, which computes diffs against the current DB state
4. **Review** diffs in a staging UI (filter by type, activity, person)
5. **Apply** selected changes as a schedule draft

This pipeline is partially implemented across 4 phases. We need guidance on:

1. **Bug triage** — A confirmed tuple comparison bug breaks block mismatch validation. What else is silently wrong?
2. **Wiring gaps** — Several Phase 1/2 features are implemented but not connected. What's the minimal wiring to make each phase functional?
3. **Round-trip test hardening** — The E2E golden test only mutates one cell. What mutation scenarios would catch real coordinator mistakes?
4. **Phase prioritization** — Given one developer, which phases/wiring deliver the most safety per hour invested?
5. **Visual QA strategy** — We have Chrome browser automation tools. What should we verify visually vs programmatically?

### Why This Matters

This is a scheduling application for a **military medical residency program** (Family Medicine, TAMC). Failures mean:

- **Wrong block import:** Coordinator imports Block 8 file into Block 9 → entire month's schedule silently corrupted
- **Fuzzy name mismatch:** "Smith, John" matched to wrong "Smith, James" → resident assigned to wrong rotation
- **Stale file re-import:** Coordinator re-imports an old export after someone else made changes → overwrites live edits
- **Silent diff miscalculation:** Import shows "0 changes" when changes exist → coordinator thinks nothing changed
- **ACGME violations undetected:** Work-hour or 1-in-7 violations introduced via Excel edit without validation

### Constraints

- **OPSEC:** No real names, schedules, or military data in test fixtures. All synthetic.
- **Native macOS:** Apple Silicon, local Postgres/Redis. No Docker.
- **Single developer:** Prioritize ROI over exhaustive coverage.
- **Pre-production:** No CI/CD pipeline yet. Tests run locally.

---

## Section 2: Architecture Overview

### Pipeline Flow

```
                    EXPORT CHAIN
                    ============
DB (half_day_assignments)
  ↓
HalfDayJSONExporter._build_person()       ← JSON with id, block_assignment_id, days
  ↓
JSONToXlsxConverter.convert_from_data()    ← inherits XMLToXlsxConverter
  ├── Fill schedule grid (rows 9-69)
  ├── _write_anchor_sheet()                ← Phase 2: __ANCHORS__ with UUIDs + row hashes
  ├── _add_data_validation()               ← Phase 3: Dropdowns from Named Ranges
  ├── _add_dynamic_cf()                    ← Phase 4: Conditional formatting
  └── _add_leave_formula_column()          ← Phase 4: COUNTIF leave formula
  ↓
CanonicalScheduleExportService._inject_metadata()
  ├── write_sys_meta_sheet()               ← Phase 1: __SYS_META__ (block_number, academic_year)
  └── write_ref_sheet()                    ← Phase 1: __REF__ (ValidRotations, ValidActivities Named Ranges)
  ↓
.xlsx file (downloaded by coordinator)


                    IMPORT CHAIN
                    ============
.xlsx file (uploaded by coordinator)
  ↓
HalfDayImportService.stage_block_template2()
  ↓
HalfDayImportService._parse_block_template2()
  ├── read_sys_meta()                      ← Phase 1: Read metadata
  ├── Block mismatch check (BUGGY)         ← BUG: tuple comparison always mismatches
  ├── Read __ANCHORS__ sheet               ← Phase 2: Build anchor_map
  ├── compute_row_hash() comparison        ← Phase 2: Skip unchanged rows
  └── Parse slots (rows 9-69, AM/PM)
  ↓
Diff computation (ADDED/MODIFIED/REMOVED)
  ↓
ImportStagedAssignment records (DB)
  ↓
preview_batch() → UI staging view
  ↓
create_draft_from_batch() → ScheduleDraft
```

### Block Template2 Format

```
Row 3:     Date headers (2026-03-12, 2026-03-13, ...)
Row 4:     Call row (on-call physician per night)
Row 8:     Column headers
Rows 9-30: Resident schedule data (up to 22 residents)
Rows 31-69: Faculty schedule data (up to 39 faculty)

Col A (1): Rotation 1 (first-half rotation code)
Col B (2): Rotation 2 (second-half rotation, if mid-block switch)
Col C (3): Template code (R1, R2, R3, C19, ADJ)
Col D (4): Role (PGY 1, PGY 2, PGY 3, FAC)
Col E (5): Name ("Last, First")
Col F+ (6+): Schedule data (AM/PM pairs per day, 2 columns per day)
             Activity codes: C, NF, FMIT-PG, LV-AM, LV-PM, ADMIN, DERM-PG, etc.

Hidden sheets:
  __SYS_META__ (veryHidden): Cell A1 = JSON metadata
  __REF__ (veryHidden): Col A = valid rotations, Col B = valid activities (Named Ranges)
  __ANCHORS__ (veryHidden): Row-aligned UUIDs and row hashes for change detection
```

### Key Backend Services

| Service | File | Role |
|---------|------|------|
| `CanonicalScheduleExportService` | `backend/app/services/canonical_schedule_export_service.py` | Orchestrates export: JSON → XLSX → metadata injection |
| `HalfDayJSONExporter` | `backend/app/services/half_day_json_exporter.py` | Reads DB, produces JSON with person IDs and day codes |
| `JSONToXlsxConverter` | `backend/app/services/json_to_xlsx_converter.py` | Thin wrapper over `XMLToXlsxConverter` for JSON input |
| `XMLToXlsxConverter` | `backend/app/services/xml_to_xlsx_converter.py` | Heavy lifter: template filling, anchors, DataValidation, CF |
| `HalfDayImportService` | `backend/app/services/half_day_import_service.py` | Import chain: parse, diff, stage, draft creation |
| `excel_metadata` | `backend/app/services/excel_metadata.py` | Shared: `ExportMetadata`, read/write meta, row hash |

---

## Section 3: Phase Status — What's Wired, What's Not

### Phase 1: Phantom Database (`__SYS_META__` + `__REF__`)

**Goal:** Import rejects wrong-block or stale files before parsing begins.

| Component | Status | Detail |
|-----------|--------|--------|
| `write_sys_meta_sheet()` | DONE | Creates veryHidden `__SYS_META__` with JSON metadata |
| `write_ref_sheet()` | DONE | Creates veryHidden `__REF__` with Named Ranges (ValidRotations, ValidActivities) |
| `read_sys_meta()` | DONE | Reads metadata from `__SYS_META__` |
| `read_ref_codes()` | DONE | Reads codes from `__REF__` |
| **Block mismatch validation** | **BUGGY** | `_parse_block_template2()` line 852: `get_block_number_for_date()` returns `tuple[int, int]` but is compared to `int`. Always mismatches. Also only warns, doesn't reject. |
| **Academic year validation** | **NOT WIRED** | Metadata has `academic_year` but import never validates it against the user-submitted form field |
| **Stale file detection** | **NOT WIRED** | Metadata has `export_timestamp` but import doesn't compare against DB last-modified |
| Named Range consumers | **NOT WIRED** | `__REF__` Named Ranges exist but Phase 3 DataValidation is the only consumer (see below) |

**Bug detail (line 852 of `half_day_import_service.py`):**
```python
# get_block_number_for_date returns tuple[int, int] (block_number, academic_year)
expected_block = get_block_number_for_date(start_date)  # ← tuple, not int!
if meta.block_number is not None and meta.block_number != expected_block:
    # Always true because int != tuple → warning fires on EVERY import with metadata
    warnings.append(...)
```

### Phase 2: Spatial UUID Anchoring (`__ANCHORS__`)

**Goal:** Deterministic person mapping (bypass fuzzy matching); skip unchanged rows.

| Component | Status | Detail |
|-----------|--------|--------|
| `_write_anchor_sheet()` | DONE | In `XMLToXlsxConverter` (line 633). Writes person_id, block_assignment_id, row_hash per row |
| `compute_row_hash()` | DONE | MD5 of `person_id|rotation1|rotation2|day_codes` |
| JSON exporter includes IDs | DONE | `_build_person()` includes `id` (person UUID) and `block_assignment_id` |
| XML exporter includes IDs | DONE | `_fetch_people()` returns `id`, `_fetch_rotations()` returns `id` |
| **Import reads anchors** | DONE | `_parse_block_template2()` lines 892-904: reads `__ANCHORS__`, builds `anchor_map` |
| **Import uses person_id from anchor** | DONE | Line 917: `person_id = UUID(person_id_str) if person_id_str else None` |
| **Import skips unchanged rows** | DONE | Lines 924-942: computes hash, compares to anchor hash, `continue` if match |
| **Hash alignment risk** | UNKNOWN | Export computes hash from JSON `day.get("am")`. Import computes from `_clean_cell_value()`. Subtle serialization differences could cause hash mismatch on unchanged rows. **Never been tested with real round-trip.** |

### Phase 3: Strict UI Contracts (Data Validation)

**Goal:** Excel dropdowns prevent invalid rotation/activity codes at the source.

| Component | Status | Detail |
|-----------|--------|--------|
| `_add_data_validation()` | DONE | In `XMLToXlsxConverter` (line 675). Creates `DataValidation` objects for rotation and activity columns |
| Named Range references | DONE | References `ValidRotations` and `ValidActivities` from `__REF__` |
| Applied to mapped rows | DONE | Iterates `self.row_mappings` to apply DV to correct rows |
| **Real-world validation** | UNKNOWN | Never tested whether dropdowns actually appear and constrain input in Excel. The Named Ranges are created by `_inject_metadata()` AFTER the converter runs, so the DV objects reference ranges that exist in the final workbook. Should work, but untested. |

### Phase 4: Stateful Leave Overlays + Provenance

**Goal:** Dynamic conditional formatting, leave-day formula, override provenance.

| Component | Status | Detail |
|-----------|--------|--------|
| `_add_dynamic_cf()` | DONE | Applies `CellIsRule` CF from `tamc_color_scheme.py` color scheme |
| `_add_leave_formula_column()` | DONE | Adds `COUNTIF(...,"LV")/2` formula column after schedule grid |
| Override provenance comments | NOT DONE | No `Comment` objects on overridden cells. Would require `is_override` flag in JSON exporter |
| **LV absence auto-creation** | DONE | `create_absences_from_lv_assignments()` at import time (Track C partial) |

### Summary Matrix

| Phase | Export Side | Import Side | E2E Tested? |
|-------|-----------|-------------|-------------|
| 1: `__SYS_META__` | DONE | BUGGY (tuple comparison) | Partial (verifySysMeta in round-trip test) |
| 1: `__REF__` | DONE | No consumer | No |
| 2: `__ANCHORS__` | DONE | DONE (but hash alignment untested) | No |
| 3: DataValidation | DONE | N/A (Excel-side only) | No |
| 4: Dynamic CF | DONE | N/A (Excel-side only) | No |
| 4: Leave formula | DONE | N/A (Excel-side only) | No |
| 4: Provenance | NOT DONE | N/A | No |

---

## Section 4: Code Excerpts

### 4a. `excel_metadata.py` — Core Metadata Utilities (Full File)

```python
"""Excel metadata utility for stateful round-trips."""

import json
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime, UTC
from typing import Any, Optional
from uuid import UUID

from openpyxl import Workbook
from openpyxl.workbook.defined_name import DefinedName


@dataclass
class ExportMetadata:
    """Metadata blob for exported Excel files."""

    academic_year: int
    export_timestamp: str
    block_number: int | None = None  # Optional for year-level
    export_version: int = 1
    block_map: dict[str, str] | None = None  # sheet_name -> block_uuid
    llm_rules_of_engagement: str | None = None  # AI agent instructions

    def to_json(self) -> str:
        d = asdict(self)
        return json.dumps({k: v for k, v in d.items() if v is not None})

    @classmethod
    def from_json(cls, data: str) -> "ExportMetadata":
        return cls(**json.loads(data))


def write_sys_meta_sheet(wb: Workbook, meta: ExportMetadata) -> None:
    """Create a veryHidden sheet __SYS_META__ with metadata JSON."""
    if "__SYS_META__" in wb.sheetnames:
        del wb["__SYS_META__"]
    ws = wb.create_sheet("__SYS_META__")
    ws.sheet_state = "veryHidden"
    ws.cell(row=1, column=1, value=meta.to_json())


def read_sys_meta(wb: Workbook) -> ExportMetadata | None:
    """Read metadata from __SYS_META__ sheet if present."""
    if "__SYS_META__" not in wb.sheetnames:
        return None
    ws = wb["__SYS_META__"]
    val = ws.cell(row=1, column=1).value
    if not val:
        return None
    try:
        return ExportMetadata.from_json(str(val))
    except Exception:
        return None


def write_ref_sheet(
    wb: Workbook, rotation_codes: list[str], activity_codes: list[str]
) -> None:
    """Create a veryHidden __REF__ sheet with Named Ranges."""
    if "__REF__" in wb.sheetnames:
        del wb["__REF__"]
    ws = wb.create_sheet("__REF__")
    ws.sheet_state = "veryHidden"

    ws.cell(row=1, column=1, value="ValidRotations")
    ws.cell(row=1, column=2, value="ValidActivities")

    sorted_rotations = sorted(set(code for code in rotation_codes if code))
    sorted_activities = sorted(set(code for code in activity_codes if code))

    for i, code in enumerate(sorted_rotations, start=2):
        ws.cell(row=i, column=1, value=code)
    for i, code in enumerate(sorted_activities, start=2):
        ws.cell(row=i, column=2, value=code)

    rot_range = f"'{ws.title}'!$A$2:$A${max(2, len(sorted_rotations) + 1)}"
    wb.defined_names.add(DefinedName("ValidRotations", attr_text=rot_range))

    act_range = f"'{ws.title}'!$B$2:$B${max(2, len(sorted_activities) + 1)}"
    wb.defined_names.add(DefinedName("ValidActivities", attr_text=act_range))


def compute_row_hash(
    person_id: UUID,
    rotation1: str | None,
    rotation2: str | None,
    days: list[str | None],
) -> str:
    """Compute MD5 hash of row content for change detection."""
    data = f"{person_id}|{rotation1 or ''}|{rotation2 or ''}|{'|'.join(d or '' for d in days)}"
    return hashlib.md5(data.encode()).hexdigest()  # nosec B324
```

### 4b. `half_day_import_service.py` — Metadata + Anchor Parsing (Lines 833-976)

```python
def _parse_block_template2(
    self, file_bytes: bytes, start_date: date, end_date: date
) -> tuple[list[ParsedSlot], list[str]]:
    """Parse Block Template2 Excel into slots."""
    warnings: list[str] = []
    wb = load_workbook(io.BytesIO(file_bytes), data_only=True)
    ws = wb.active

    # Read Phase 1 metadata if present (non-blocking: legacy files lack it)
    meta = read_sys_meta(wb)
    if meta:
        logger.info(
            "Import metadata: academic_year=%s, block_number=%s, "
            "export_version=%d, export_timestamp=%s",
            meta.academic_year, meta.block_number,
            meta.export_version, meta.export_timestamp,
        )
        # BUG: get_block_number_for_date returns tuple[int, int], not int!
        expected_block = get_block_number_for_date(start_date)
        if meta.block_number is not None and meta.block_number != expected_block:
            # This ALWAYS fires because int != tuple. Should be:
            #   expected_block, _expected_ay = get_block_number_for_date(start_date)
            warnings.append(
                f"Metadata block_number={meta.block_number} differs from "
                f"expected block {expected_block} (date {start_date})"
            )

    # Build date columns from row 3
    date_cols: list[tuple[int, date]] = []
    col = SCHEDULE_START_COL
    while True:
        cell = ws.cell(row=DATE_ROW, column=col)
        if isinstance(cell, MergedCell):
            col += 1
            continue
        val = cell.value
        if isinstance(val, datetime):
            date_cols.append((col, val.date()))
        elif isinstance(val, date):
            date_cols.append((col, val))
        else:
            if col >= SCHEDULE_START_COL + 56:
                break
        col += 2
        if col > 200:
            break

    if not date_cols:
        raise ValueError("Could not find date columns in row 3")

    # Read Phase 2 anchors if present
    anchor_map: dict[int, dict[str, str]] = {}
    if "__ANCHORS__" in wb.sheetnames:
        anchors_ws = wb["__ANCHORS__"]
        for row in range(2, anchors_ws.max_row + 1):
            p_id = anchors_ws.cell(row=row, column=1).value
            ba_id = anchors_ws.cell(row=row, column=2).value
            r_hash = anchors_ws.cell(row=row, column=3).value
            if p_id:
                anchor_map[row] = {
                    "person_id": str(p_id),
                    "block_assignment_id": str(ba_id) if ba_id else "",
                    "row_hash": str(r_hash) if r_hash else "",
                }

    slots: list[ParsedSlot] = []
    for row_idx in range(DATA_START_ROW, DATA_END_ROW + 1):
        name_cell = ws.cell(row=row_idx, column=NAME_COL)
        name_val = name_cell.value
        if not name_val:
            continue
        person_name = str(name_val).replace("*", "").strip()

        anchor = anchor_map.get(row_idx, {})
        person_id_str = anchor.get("person_id")
        try:
            person_id = UUID(person_id_str) if person_id_str else None
        except ValueError:
            person_id = None

        # Phase 2: compute hash to skip unchanged rows
        if person_id and anchor.get("row_hash"):
            rot1_val = self._clean_cell_value(ws.cell(row=row_idx, column=1).value)
            rot2_val = self._clean_cell_value(ws.cell(row=row_idx, column=2).value)
            days_codes = []
            for col, _ in date_cols:
                am = self._clean_cell_value(ws.cell(row=row_idx, column=col).value)
                pm = self._clean_cell_value(ws.cell(row=row_idx, column=col + 1).value)
                days_codes.extend([am, pm])

            current_hash = compute_row_hash(person_id, rot1_val, rot2_val, days_codes)
            if current_hash == anchor["row_hash"]:
                continue  # Unchanged row — skip

        for col, slot_date in date_cols:
            am_val = ws.cell(row=row_idx, column=col).value
            pm_val = ws.cell(row=row_idx, column=col + 1).value

            slots.append(ParsedSlot(
                person_name=person_name,
                person_id=person_id,
                assignment_date=slot_date,
                time_of_day="AM",
                raw_value=self._clean_cell_value(am_val),
                excel_code=None, warnings=[], errors=[],
                row_number=row_idx,
            ))
            slots.append(ParsedSlot(
                person_name=person_name,
                person_id=person_id,
                assignment_date=slot_date,
                time_of_day="PM",
                raw_value=self._clean_cell_value(pm_val),
                excel_code=None, warnings=[], errors=[],
                row_number=row_idx,
            ))

    wb.close()
    return slots, warnings
```

### 4c. `half_day_json_exporter.py` — `_build_person()` (Lines 138-180)

```python
def _build_person(
    self,
    person_info: dict[str, Any],
    rotation_info: dict[str, Any],
    assignments: list,
    block_start: date,
    block_end: date,
) -> dict[str, Any]:
    """Build person payload with daily schedule from DB assignments."""
    person = {
        "id": person_info.get("id"),                         # ← UUID for Phase 2 anchors
        "block_assignment_id": rotation_info.get("id"),       # ← BlockAssignment UUID
        "name": person_info.get("name", ""),
        "pgy": person_info.get("pgy"),
        "rotation1": rotation_info.get("rotation1", ""),
        "rotation2": rotation_info.get("rotation2", ""),
        "days": [],
    }

    assignment_index: dict[tuple[date, str], Any] = {}
    for a in assignments:
        assignment_index[(a.date, a.time_of_day)] = a

    current = block_start
    while current <= block_end:
        am_assignment = assignment_index.get((current, "AM"))
        pm_assignment = assignment_index.get((current, "PM"))

        am_code = self._get_activity_code(am_assignment)
        pm_code = self._get_activity_code(pm_assignment)

        person["days"].append({
            "date": current.isoformat(),
            "weekday": current.strftime("%a"),
            "am": am_code,
            "pm": pm_code,
        })

        current = current + timedelta(days=1)

    return person
```

### 4d. `xml_to_xlsx_converter.py` — `_write_anchor_sheet()` (Lines 633-673)

```python
def _write_anchor_sheet(self, wb: Workbook, data: dict[str, Any]) -> None:
    """Create a veryHidden sheet __ANCHORS__ with UUIDs and row hashes."""
    if "__ANCHORS__" in wb.sheetnames:
        del wb["__ANCHORS__"]
    ws = wb.create_sheet("__ANCHORS__")
    ws.sheet_state = "veryHidden"

    # Headers
    ws.cell(row=1, column=1, value="person_id")
    ws.cell(row=1, column=2, value="block_assignment_id")
    ws.cell(row=1, column=3, value="row_hash")

    from app.services.excel_metadata import compute_row_hash

    all_people = (data.get("residents", []) or []) + (data.get("faculty", []) or [])
    for person in all_people:
        name = person.get("name", "")
        person_id = person.get("id")
        if not person_id or not name:
            continue

        row = self.row_mappings.get(name.replace("*", "").strip())
        if not row:
            continue

        # Compute hash for Phase 2 O(1) change detection
        rotation1 = person.get("rotation1")
        rotation2 = person.get("rotation2")
        days_codes = []
        for day in person.get("days", []):
            days_codes.append(day.get("am"))
            days_codes.append(day.get("pm"))

        row_hash = compute_row_hash(UUID(person_id), rotation1, rotation2, days_codes)

        # Write to anchor sheet at matching row (Spatial Anchoring)
        ws.cell(row=row, column=1, value=str(person_id))
        ws.cell(row=row, column=2, value=str(person.get("block_assignment_id", "")))
        ws.cell(row=row, column=3, value=row_hash)
```

### 4e. `canonical_schedule_export_service.py` — `_inject_metadata()` (Lines 309-346)

```python
def _inject_metadata(
    self,
    xlsx_bytes: bytes,
    academic_year: int,
    block_number: int | None = None,
    output_path: Path | str | None = None,
    block_map: dict[str, str] | None = None,
) -> bytes:
    """Add __SYS_META__ and __REF__ sheets to exported workbook."""
    wb = load_workbook(io.BytesIO(xlsx_bytes))

    rotation_codes = [
        r[0] for r in self.db.query(RotationTemplate.abbreviation).distinct().all() if r[0]
    ]
    activity_codes = [
        a[0] for a in self.db.query(Activity.code).distinct().all() if a[0]
    ]

    meta = ExportMetadata(
        academic_year=academic_year,
        block_number=block_number,
        export_timestamp=datetime.now(UTC).isoformat(),
        block_map=block_map,
    )
    write_sys_meta_sheet(wb, meta)
    write_ref_sheet(wb, rotation_codes, activity_codes)

    buf = io.BytesIO()
    wb.save(buf)
    final_bytes = buf.getvalue()

    if output_path:
        with open(output_path, "wb") as f:
            f.write(final_bytes)

    return final_bytes
```

---

## Section 5: Existing E2E Test Inventory

### Import/Export Specs (4 files, ~23 tests)

| Spec | Tests | Status | What It Tests |
|------|-------|--------|---------------|
| `round-trip.spec.ts` | 3 | All skip (need seeded DB) | Export → mutate F9 → import → verify ≥1 Modified → apply → API verify |
| `import-stage-apply.spec.ts` | 8 | 4 skip | Upload form, file acceptance, staging with diff metrics, draft creation |
| `export-block.spec.ts` | 4 | 3 skip | Export panel formats, XLSX download, `__SYS_META__` verification |
| `acgme-violation-import.spec.ts` | 1 | Skip | Upload violation fixture, stage, verify violation count > 0 |

### Test Infrastructure

| File | Key Exports |
|------|-------------|
| `e2e/utils/xlsx-helpers.ts` | `parseExportedXlsx`, `mutateXlsxCell`, `verifySysMeta`, `streamToBuffer` |
| `e2e/fixtures/generate-test-xlsx.ts` | Creates `test-block10.xlsx` and `test-acgme-violation.xlsx` with `__SYS_META__` + `__REF__` |
| `e2e/fixtures/auth.fixture.ts` | `adminPage`, `coordinatorPage`, `facultyPage`, `residentPage` |
| `e2e/utils/selectors.ts` | `importExport.*` — 30+ selectors for upload, staging, diff, batch review |
| `e2e/global-setup.ts` | Calls `POST /api/v1/dev/seed?scenario=e2e_baseline` for deterministic DB seeding |

### Round-Trip Test (The Golden Test)

```typescript
// round-trip.spec.ts — abridged structure
test.describe('Round-Trip (Golden Test)', () => {
  test.skip(() => !process.env.E2E_HAS_SEEDED_DATA, 'Requires seeded database');

  let exportedBuffer: Buffer;
  let mutatedBuffer: Buffer;
  let tempFilePath: string;

  test('Step 1-3: Export, mutate, and write temp file', async ({ adminPage }) => {
    // Navigate to /hub/import-export
    // Select xlsx format, trigger download
    // Convert download stream to buffer
    // verifySysMeta(exportedBuffer, 10, 2025)
    // mutateXlsxCell(buffer, sheetName, 'F9', 'NF')
    // verifySysMeta(mutatedBuffer, 10, 2025)
    // Write to temp file
  });

  test('Step 4-6: Upload, stage, verify diff', async ({ adminPage }) => {
    // Navigate to /import/half-day
    // Upload mutated file, fill block_number=10, academic_year=2025
    // Stage and verify hdMetricChanged >= 1
  });

  test('Step 7-8: Apply and verify via API', async ({ adminPage }) => {
    // Select all diffs, create draft, apply
    // Verify status badge shows "applied"
    // Query API to confirm DB changed
  });
});
```

**Known weakness:** Uses `let` shared state across 3 separate `test()` blocks. If test 1 fails, tests 2-3 fail with confusing `undefined` errors. Should use `test.step()` pattern.

### Xlsx Helpers

```typescript
// xlsx-helpers.ts — full API surface
export async function parseExportedXlsx(buffer: Buffer): Promise<{
  meta: SysMetadata | null;     // Parsed __SYS_META__ JSON
  rows: ScheduleRow[];          // Rows 9-69 from visible sheet
  sheetName: string;            // Name of visible sheet
}>;

export async function mutateXlsxCell(
  buffer: Buffer, sheetName: string, cellRef: string, newValue: string
): Promise<Buffer>;             // Preserves veryHidden sheets

export async function verifySysMeta(
  buffer: Buffer, expectedBlock: number, expectedYear: number
): Promise<boolean>;

export async function streamToBuffer(stream: ReadableStream): Promise<Buffer>;
```

### Fixture Generator

```typescript
// generate-test-xlsx.ts — creates test fixtures
// test-block10.xlsx: 5 residents, 28 days, deterministic activity rotation
// test-acgme-violation.xlsx: Same but Resident 1 has 7 consecutive NF (1-in-7 violation)
// Both include __SYS_META__ (block=10, year=2025) and __REF__ (activity codes)
// Does NOT include __ANCHORS__ (no person UUIDs in fixture)
```

### Dev Seed Endpoint

```python
# POST /api/v1/dev/seed?scenario=e2e_baseline
# Env-gated: only when ENV=test or ALLOW_DEV_SEED=true
# Seeds:
#   - 17 residents (CPT Doe-01..17, PGY 1-3)
#   - 13 faculty (Dr. Faculty-A..M)
#   - 5 activities (C, NF, FMIT, LV, LEC)
#   - 28 days of half-day assignments
#   - Deterministic via random.Random(42)
```

### Selector Reference (Import/Export)

```typescript
selectors.importExport = {
  // Upload
  hdFileInput, hdBlockNumber, hdAcademicYear, hdStageBtn,
  // Staging/Preview
  hdFilterDiffType, hdFilterActivity, hdFilterErrors, hdFilterPerson,
  hdDiffTable, hdMetricTotal, hdMetricChanged, hdMetricAddedRemoved, hdMetricHours,
  hdPaginationInfo, hdSelectPageBtn,
  // Draft creation
  hdDraftNotes, hdCreateDraftBtn, hdDraftAdded, hdDraftModified, hdDraftRemoved, hdViewDraftBtn,
  // Batch review
  batchStatusBadge, batchApplyBtn, batchCancelBtn,
  batchStatNew, batchStatUpdates, batchStatViolations,
  // Export
  exportFormatCsv, exportFormatXlsx, exportFormatJson, exportSubmitBtn,
};
```

---

## Section 6: Chrome MCP Browser Automation

We have `mcp__claude-in-chrome__*` tools for live visual QA:

| Tool | Capability |
|------|-----------|
| `navigate` | Open URLs in Chrome |
| `read_page` | Get full DOM/text content |
| `form_input` | Fill form fields, click buttons |
| `computer` | Mouse/keyboard interaction |
| `gif_creator` | Record multi-step interactions as GIF |
| `upload_image` | Send screenshots for visual analysis |
| `get_page_text` | Extract visible text |

These can verify things Playwright cannot:
- Visual layout and styling (font colors, background fills, contrast)
- Conditional formatting rendering in the diff table
- That the staging UI is human-readable
- Error state UX (red badges, clear messages)

---

## Section 7: Questions for Gemini

Answer these in order. Be specific, cite code paths, and show implementation diffs where relevant.

### Bug Triage

1. **Tuple comparison bug (Phase 1):** Line 852 of `half_day_import_service.py` compares `meta.block_number` (int) against `get_block_number_for_date(start_date)` (tuple). This means block mismatch validation has NEVER worked. What's the correct fix? Should the validation:
   - (a) Stay in `_parse_block_template2()` using `start_date` to derive expected block?
   - (b) Move to `stage_block_template2()` where `block_number` and `academic_year` are explicit parameters?
   - (c) Both — validate against form parameters early, and cross-check against date range later?

   Also: should a metadata mismatch be a **hard rejection** (raise ValueError → HTTP 400) or a **soft warning** when `__SYS_META__` is present?

2. **Hash alignment risk (Phase 2):** The anchor hash is computed on export from `day.get("am")` (JSON string from `_get_activity_code()`). On import, it's computed from `_clean_cell_value(ws.cell(...).value)`. Are there serialization differences that would cause hash mismatch on unchanged rows? Consider:
   - Empty cells: export writes `""` (empty string), Excel stores as `None`, `_clean_cell_value(None)` returns `None`
   - `compute_row_hash` normalizes: `None` → `""` via `d or ''`. But `""` → `""` directly.
   - So `None` and `""` both hash the same. Is this correct?
   - What about numeric values? Can Excel convert a string "12" to number 12?

### Wiring Gaps

3. **Phase 1 import validation wiring:** What's the minimal change to make `__SYS_META__` validation actually work? Show the exact diff. Should we:
   - Fix the tuple bug and keep it as a warning?
   - Move validation earlier into `stage_block_template2()` and make it a hard rejection?
   - Add academic year validation alongside block number?

4. **Phase 2 `__ANCHORS__` preservation through openpyxl:** The export chain uses openpyxl (`_inject_metadata` at the end). Does the `load_workbook` → `wb.save` cycle in `_inject_metadata()` preserve veryHidden sheets created by xlsx-populate in the converter step? Or does openpyxl strip them? If this is broken, the anchors are being written by the converter but destroyed by the metadata injection step.

### Test Strategy

5. **Round-trip test hardening:** The golden test only mutates cell F9 to 'NF'. Design 5 additional mutation scenarios that would catch real coordinator mistakes:
   - Consider: rotation changes, leave on wrong day, duplicate assignments, bulk changes, empty cells
   - For each scenario, specify: what to mutate, expected diff type, expected diff count, and what failure would look like

6. **"0 diffs" test for Phase 2 validation:** The most critical untested path is: export a block → import the SAME file with no changes → verify the diff shows 0 changes. If the anchor hashing works, this should produce 0 diffs. If it doesn't, every "unchanged" row shows as modified. Write this test (Playwright + xlsx-helpers).

7. **"Wrong block" rejection test:** Export block 10 → attempt to import as block 9 → verify HTTP 400 and error message. Write this test. This validates the Phase 1 fix.

### Prioritization

8. **Phase ROI ranking:** Given one developer with limited time, rank these by ROI (safety improvement per hour invested):
   - (a) Fix tuple bug + wire Phase 1 hard rejection
   - (b) Validate Phase 2 anchor hash alignment (may require fixing hash computation)
   - (c) Refactor round-trip test to `test.step()` + add "0 diffs" and "wrong block" tests
   - (d) Validate Phase 3 DataValidation actually works in Excel
   - (e) Chrome MCP visual QA of the diff staging UI
   - (f) Wire academic year validation
   - (g) Wire stale-file detection (export_timestamp comparison)

### Architecture

9. **`_inject_metadata()` round-trip safety:** The canonical export does:
   1. `JSONToXlsxConverter.convert_from_json()` → writes schedule + `__ANCHORS__` + DataValidation + CF (via `openpyxl`)
   2. `_inject_metadata()` → `load_workbook()` the output → adds `__SYS_META__` + `__REF__` → `wb.save()`

   Does step 2's `load_workbook → save` cycle preserve everything from step 1? Specifically:
   - Does openpyxl preserve veryHidden sheet state on re-save?
   - Does it preserve DataValidation objects?
   - Does it preserve Conditional Formatting rules?
   - Does it preserve the row_hash values in `__ANCHORS__`?

   If any of these are lost, the inject-after-convert pattern is fundamentally broken and we need to inject metadata DURING conversion instead.

10. **Schema Track A interaction:** The `person_academic_years` migration (due before July 1) will change how PGY levels are stored. Currently `_fetch_people()` reads `p.pgy_level` directly. After Track A, it should read from the current AY's `PersonAcademicYear` record. Does this affect:
    - The exported workbook's "Role" column (PGY 1/2/3)?
    - The anchor hash computation (PGY isn't part of the hash, so probably no)?
    - The import side's person matching logic?

---

## Section 8: Key File Paths

### Backend Export Chain
```
backend/app/services/canonical_schedule_export_service.py  ← Orchestrator
backend/app/services/half_day_json_exporter.py             ← DB → JSON
backend/app/services/json_to_xlsx_converter.py             ← JSON → XLSX (thin wrapper)
backend/app/services/xml_to_xlsx_converter.py              ← Heavy lifter (anchors, DV, CF)
backend/app/services/excel_metadata.py                     ← Metadata read/write/hash
backend/app/services/tamc_color_scheme.py                  ← Color definitions for CF
backend/app/api/routes/export.py                           ← GET /api/v1/export/schedule/xlsx
backend/data/BlockTemplate2_Official.xlsx                  ← Formatted template file
backend/data/BlockTemplate2_Structure.xml                  ← Structure definition
```

### Backend Import Chain
```
backend/app/services/half_day_import_service.py            ← Parse, diff, stage, draft
backend/app/api/routes/half_day_imports.py                 ← POST /stage, GET /preview, POST /draft
backend/app/models/import_staging.py                       ← ImportBatch, ImportStagedAssignment
backend/app/schemas/half_day_import.py                     ← HalfDayDiffEntry, HalfDayDiffMetrics
backend/app/utils/academic_blocks.py                       ← get_block_dates, get_block_number_for_date
```

### Frontend Import/Export
```
frontend/src/hooks/useHalfDayImport.ts                     ← useStageHalfDayImport, useHalfDayImportPreview
frontend/src/hooks/useExportData.ts                        ← Export hooks
frontend/src/features/import-export/ExportPanel.tsx         ← Export UI
frontend/src/features/import-export/ImportPreview.tsx       ← Diff staging UI
frontend/src/features/import/components/BatchDiffViewer.tsx ← Diff table
```

### E2E Test Infrastructure
```
frontend/e2e/tests/import-export/round-trip.spec.ts
frontend/e2e/tests/import-export/import-stage-apply.spec.ts
frontend/e2e/tests/import-export/export-block.spec.ts
frontend/e2e/tests/import-export/acgme-violation-import.spec.ts
frontend/e2e/utils/xlsx-helpers.ts
frontend/e2e/utils/selectors.ts
frontend/e2e/fixtures/generate-test-xlsx.ts
frontend/e2e/fixtures/auth.fixture.ts
frontend/e2e/global-setup.ts
frontend/playwright.config.ci.ts
```

### Architecture Docs
```
docs/architecture/excel-stateful-roundtrip-roadmap.md      ← Phase 1-4 + Track A/C roadmap
docs/planning/E2E_GUI_TESTING_ROADMAP.md                   ← E2E testing roadmap (Phases 0-5)
docs/prompts/E2E_GUI_TESTING_REFINEMENT.md                 ← Prior Gemini prompt (E2E testing)
```

---

## Appendix A: `ExportMetadata` Dataclass

```python
@dataclass
class ExportMetadata:
    academic_year: int              # e.g., 2025 for AY 2025-2026
    export_timestamp: str           # ISO 8601
    block_number: int | None = None # 0-13 (None for year-level)
    export_version: int = 1
    block_map: dict[str, str] | None = None  # sheet_name -> block_uuid (year exports)
    llm_rules_of_engagement: str | None = None
```

## Appendix B: Auth Fixture Roles

```typescript
// e2e/fixtures/auth.fixture.ts
adminPage       — admin@test.mil / TestPassword123!
coordinatorPage — coordinator@test.mil / TestPassword123!
facultyPage     — faculty@test.mil / TestPassword123!
residentPage    — resident@test.mil / TestPassword123!
```

## Appendix C: API Endpoints (Import/Export)

```
GET  /api/v1/export/schedule/xlsx?block_number=10&academic_year=2025
POST /api/v1/import/half-day/stage       (multipart: file + block_number + academic_year)
GET  /api/v1/import/half-day/batches/{id}/preview?page=1&diff_type=MODIFIED
POST /api/v1/import/half-day/batches/{id}/draft
POST /api/v1/dev/seed?scenario=e2e_baseline  (env-gated)
```

## Appendix D: `half_day_import_service.py` — `stage_block_template2()` Method (Lines 199-390)

This is the top-level import method. Key flow:
1. Get block dates from `block_number` + `academic_year`
2. Call `_parse_block_template2()` (where the bug lives)
3. Load activity map and person map
4. Attach person IDs + normalize activity codes
5. Load current schedule from DB
6. Compute diffs (ADDED/MODIFIED/REMOVED)
7. Stage diffs as `ImportStagedAssignment` records
8. Create absence records from LV codes (Track C)
9. Return `(ImportBatch, HalfDayDiffMetrics, warnings)`

Note: `block_number` and `academic_year` are available as explicit parameters here (from the upload form), making this the ideal place for metadata validation — before `_parse_block_template2()` is called.
