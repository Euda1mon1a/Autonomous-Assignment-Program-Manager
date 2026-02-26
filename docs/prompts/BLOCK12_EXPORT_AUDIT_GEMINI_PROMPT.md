# Block 12 Export Pipeline Audit — Unblock Real Data Export

> **Purpose:** Self-contained prompt for AI-assisted diagnosis and unblocking of the Block 12 Excel export pipeline for a military medical residency scheduler.
> **Target AI:** Gemini Pro 3.1 (Extended Thinking)
> **Project:** Military medical residency scheduler (ACGME-compliant, local-only deployment)
> **Created:** 2026-02-26
> **Master Priority List:** Item #36

---

## Section 1: Mission

### What We Need

Make `export_block_xlsx(block_number=12, academic_year=2025)` produce a **functional Block Template2 XLSX** containing:

1. **All residents** assigned to Block 12 — grouped by PGY level (3→2→1), with correct rotation codes and daily AM/PM activity codes for all 28 days
2. **All faculty** — with half-day assignments (clinic, admin, teaching, leave, etc.)
3. **Faculty call** — nightly on-call assignments placed in the call row

**"Functional" defined:** A coordinator can open the file in Excel and see the same information they'd see on the hand-jam spreadsheet. Names in column E, rotations in columns A-B, AM/PM codes in columns F+ (2 columns per day, 56 schedule columns for 28 days). Call assignments in row 4.

### Constraints

- **Local-only deployment** — real personnel data is acceptable (no synthetic names needed)
- **Block Template2 format only** — ROSETTA (legacy validation format) is deprecated
- **Single developer** — solutions must be pragmatic, not over-engineered
- **No Docker required** — native macOS with PostgreSQL
- **Block 12 AY 2025** = May 7, 2026 (Thursday) to June 3, 2026 (Wednesday) — standard 28-day block

### Current State: Three Hard Blockers

The export pipeline **cannot run at all** for Block 12 (or any block). Three `FileNotFoundError` / `ValueError` exceptions fire before any data is written:

| # | Blocker | What Happens |
|---|---------|-------------|
| 1 | No template XLSX exists at `backend/data/BlockTemplate2_Official.xlsx` | `_template_path()` raises `FileNotFoundError` |
| 2 | Structure XML at wrong path (`docs/scheduling/` not `backend/data/`) | `_structure_path()` raises `FileNotFoundError` |
| 3 | Structure XML has placeholder names (`R3-A, Resident`) instead of real DB names | `_fill_residents()` raises `ValueError` with `strict_row_mapping=True` |

---

## Section 2: Export Pipeline Architecture

### Service Chain

```
DB (half_day_assignments, block_assignments, persons, call_assignments)
  ↓
CanonicalScheduleExportService.export_block_xlsx()
  ↓
HalfDayJSONExporter.export()  →  JSON dict  {residents: [...], faculty: [...], call: {...}}
  ↓
JSONToXlsxConverter.convert_from_json()  →  passes through to XMLToXlsxConverter
  ↓
XMLToXlsxConverter.convert_from_data()  →  loads template XLSX + structure XML → fills rows → bytes
  ↓
Phase 1 metadata (__SYS_META__, __REF__) written in same save cycle
  ↓
bytes returned to caller
```

### Key Method: `export_block_xlsx()` (canonical_schedule_export_service.py:47-104)

```python
def export_block_xlsx(
    self,
    block_number: int,
    academic_year: int,
    include_faculty: bool = True,
    include_overrides: bool = True,
    include_qa_sheet: bool = True,
    preserve_template_identity_fields: bool = True,
    presentation_profile: str = "tamc_handjam_v2",
    output_path: Path | str | None = None,
) -> bytes:
    """Export a block schedule to XLSX using the canonical template."""
    block_dates = get_block_dates(block_number, academic_year)

    data = self._export_json_data(
        block_dates.start_date,
        block_dates.end_date,
        include_faculty=include_faculty,
        include_overrides=include_overrides,
    )

    # Query ref codes for Phase 1 __REF__ sheet (single-save pattern)
    rotation_codes = [
        r[0]
        for r in self.db.query(RotationTemplate.abbreviation).distinct().all()
        if r[0]
    ]
    activity_codes = [
        a[0] for a in self.db.query(Activity.code).distinct().all() if a[0]
    ]

    meta = ExportMetadata(
        academic_year=academic_year,
        block_number=block_number,
        export_timestamp=datetime.now(UTC).isoformat(),
    )

    converter = JSONToXlsxConverter(
        template_path=self._template_path(),        # ← BLOCKER 1: FileNotFoundError
        structure_xml_path=self._structure_path(),   # ← BLOCKER 2: FileNotFoundError
        use_block_template2=True,
        apply_colors=True,
        strict_row_mapping=True,                     # ← BLOCKER 3: ValueError
        include_qa_sheet=include_qa_sheet,
        preserve_template_identity_fields=preserve_template_identity_fields,
        presentation_profile=presentation_profile,
    )
    xlsx_bytes = converter.convert_from_json(
        data,
        export_metadata=meta,
        rotation_codes=rotation_codes,
        activity_codes=activity_codes,
    )

    if output_path:
        Path(output_path).write_bytes(xlsx_bytes)

    return xlsx_bytes
```

### Path Resolution (canonical_schedule_export_service.py:380-400)

```python
def _data_dir(self) -> Path:
    # backend/app/services -> backend
    return Path(__file__).resolve().parents[2] / "data"

def _template_path(self) -> Path:
    template = self._data_dir() / "BlockTemplate2_Official.xlsx"
    if not template.exists():
        raise FileNotFoundError(
            f"Canonical template missing: {template}. "
            "Place the formatted Block Template2 XLSX in backend/data."
        )
    return template

def _structure_path(self) -> Path:
    structure = self._data_dir() / "BlockTemplate2_Structure.xml"
    if not structure.exists():
        raise FileNotFoundError(
            f"Structure XML missing: {structure}. "
            "Expected BlockTemplate2_Structure.xml in backend/data."
        )
    return structure
```

**Filesystem reality:**
- `backend/data/` contains only `csv_files/` — no XLSX, no XML
- Structure XML exists at `docs/scheduling/BlockTemplate2_Structure.xml` (wrong directory)
- Template XLSX does not exist anywhere in the repository

---

## Section 3: Three Blockers — Detailed Analysis

### Blocker 1: No Template XLSX

The converter checks `if self.template_path and self.template_path.exists()` at line 231. If a template exists, it loads it and writes into the "Block Template2" sheet. If not, it falls back to `_create_new_workbook()` which creates a ROSETTA-format sheet.

Since `_template_path()` raises `FileNotFoundError` before the converter is even instantiated, the code never reaches the ROSETTA fallback. But even if it did, ROSETTA is the wrong format — it uses different column positions (Name in col 1 vs col 5) and sequential rows instead of PGY-grouped mapped rows.

**What the template provides:**
- Pre-formatted sheet named "Block Template2" with merged header cells, color fills, row/column dimensions
- Row structure: rows 9-25 for residents (grouped by PGY), rows 31-43 for faculty, row 4 for staff call, row 5 for resident call
- Column structure: A=Rotation1, B=Rotation2, C=Template, D=Role, E=Name, F+=Schedule (2 cols/day)
- Summary formula columns at the end (BJ-BR for clinic counts, etc.)

**Without the template:** openpyxl generates a blank workbook with no formatting, no pre-existing row structure, and no summary formulas.

### Blocker 2: Structure XML in Wrong Directory

Trivial to fix (copy or symlink), but raises a deeper question: should the XML be static at all, or generated dynamically from DB data?

The XML provides name→row mappings that the converter uses at line 1072:
```python
if self.row_mappings:
    row = self.row_mappings.get(lookup_name)
```

Without the XML, `self.row_mappings` is empty and the converter falls back to sequential rows starting at row 2 — which conflicts with the BT2 row layout (residents start at row 9).

### Blocker 3: Placeholder Names Don't Match DB

The structure XML has entries like:
```xml
<resident row="9" name="R3-A, Resident" pgy="3" rotation1="Hilo"/>
<person row="31" name="F-A, Faculty" template="C19"/>
```

The converter tries 3-tier name matching (xml_to_xlsx_converter.py:1072-1103):

```python
# Tier 1: Exact match
row = self.row_mappings.get(lookup_name)

# Tier 2: Comma-swap ("Last, First" → "First Last")
if lookup_name not in self.row_mappings and "," in lookup_name:
    last, first = [part.strip() for part in lookup_name.split(",", 1)]
    swapped = f"{first} {last}".strip()
    if swapped in self.row_mappings:
        lookup_name = swapped

# Tier 3: First-name fuzzy match
if not row:
    first_name = lookup_name.split()[0] if lookup_name else ""
    for mapping_name, mapping_row in self.row_mappings.items():
        if mapping_name.startswith(first_name):
            row = mapping_row
            break

if not row:
    if self.strict_row_mapping:
        raise ValueError(
            f"No row mapping for: {name}. "
            "Update BlockTemplate2_Structure.xml."
        )
```

With placeholder names like "R3-A, Resident" and DB names like "Smith, John", none of the 3 tiers match. With `strict_row_mapping=True`, this raises `ValueError` for every person.

---

## Section 4: Current Structure XML

Full contents of `docs/scheduling/BlockTemplate2_Structure.xml`:

```xml
<?xml version="1.0" ?>
<block_template name="Block Template2" source="Block_Template2.xlsx">
  <layout>
    <call_row row="4"/>
    <resident_call_row row="5"/>
    <schedule_col_start>6</schedule_col_start>
    <cols_per_day>2</cols_per_day>
  </layout>
  <residents>
    <!-- PGY-3 Residents (Rows 9-13) -->
    <resident row="9" name="R3-A, Resident" pgy="3" rotation1="Hilo"/>
    <resident row="10" name="R3-B, Resident" pgy="3" rotation1="NF" rotation2="Elective"/>
    <resident row="11" name="R3-C, Resident" pgy="3" rotation1="FMC"/>
    <resident row="12" name="R3-D, Resident" pgy="3" rotation1="FMIT 2"/>
    <resident row="13" name="R3-E, Resident" pgy="3" rotation1="NEURO" rotation2="NF"/>
    <!-- PGY-2 Residents (Rows 14-19) -->
    <resident row="14" name="R2-A, Resident" pgy="2" rotation1="FMIT 2"/>
    <resident row="15" name="R2-B, Resident" pgy="2" rotation1="SM"/>
    <resident row="16" name="R2-C, Resident" pgy="2" rotation1="POCUS"/>
    <resident row="17" name="R2-D, Resident" pgy="2" rotation1="L and D night float"/>
    <resident row="18" name="R2-E, Resident" pgy="2" rotation1="Surg Exp"/>
    <resident row="19" name="R2-F, Resident" pgy="2" rotation1="Gyn Clinic"/>
    <!-- PGY-1 Residents (Rows 20-25) -->
    <resident row="20" name="R1-A, Resident" pgy="1" rotation1="FMC"/>
    <resident row="21" name="R1-B, Resident" pgy="1" rotation1="Peds Ward" rotation2="Peds NF"/>
    <resident row="22" name="R1-C, Resident" pgy="1" rotation1="Kapiolani L and D"/>
    <resident row="23" name="R1-D, Resident" pgy="1" rotation1="Peds NF" rotation2="Peds Ward"/>
    <resident row="24" name="R1-E, Resident" pgy="1" rotation1="PROC"/>
    <resident row="25" name="R1-F, Resident" pgy="1" rotation1="IM"/>
  </residents>
  <faculty>
    <!-- Core Faculty (Rows 31-40) -->
    <person row="31" name="F-A, Faculty" template="C19"/>
    <person row="32" name="F-B, Faculty" template="C19"/>
    <person row="33" name="F-C, Faculty" template="C19"/>
    <person row="34" name="F-D, Faculty" template="C19"/>
    <person row="35" name="F-E, Faculty" template="C19"/>
    <person row="36" name="F-F, Faculty" template="C19"/>
    <person row="37" name="F-G, Faculty" template="C19"/>
    <person row="38" name="F-H, Faculty" template="C19"/>
    <person row="39" name="F-I, Faculty" template="C19"/>
    <person row="40" name="F-J, Faculty" template="C19"/>
    <!-- Adjunct Faculty (Rows 41-42) -->
    <person row="41" name="F-K, Faculty" template="ADJ"/>
    <person row="42" name="F-L, Faculty" template="ADJ"/>
    <!-- Specialist (Row 43) -->
    <person row="43" name="F-M, Faculty" template="SPEC"/>
  </faculty>
</block_template>
```

**Row Layout:**
- Rows 9-13: PGY-3 residents (5 slots)
- Rows 14-19: PGY-2 residents (6 slots)
- Rows 20-25: PGY-1 residents (6 slots)
- Rows 26-30: Blank separator / unused
- Rows 31-40: Core faculty (10 slots, template C19)
- Rows 41-42: Adjunct faculty (2 slots, template ADJ)
- Rows 43: Specialist (1 slot, template SPEC)

**Problem:** Real Block 12 may have different counts per PGY class. If there are 7 PGY-2s and 5 PGY-1s, the fixed 6-slot bands don't fit.

---

## Section 5: Data Flow — What the JSON Exporter Produces

### `_build_person()` (half_day_json_exporter.py:138-180)

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
        "id": person_info.get("id"),                    # person UUID (str)
        "block_assignment_id": rotation_info.get("id"),  # block_assignment UUID (str)
        "name": person_info.get("name", ""),             # "First Last" from DB
        "pgy": person_info.get("pgy"),                   # int or None (faculty)
        "rotation1": rotation_info.get("rotation1", ""), # e.g., "FMIT 2"
        "rotation2": rotation_info.get("rotation2", ""), # e.g., "NF" or ""
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

**Good news:** Both `id` (person UUID) and `block_assignment_id` are already included. This data is available for Phase 2 UUID anchoring.

### `_fetch_people()` (half_day_xml_exporter.py:326-343)

```python
def _fetch_people(self, person_ids: list[UUID]) -> dict[UUID, dict[str, Any]]:
    """Fetch person details by ID."""
    stmt = select(Person).where(Person.id.in_(person_ids))
    result = self.db.execute(stmt)
    people = result.scalars().all()

    return {
        p.id: {
            "id": str(p.id),
            "name": p.name,                                    # "First Last" format
            "pgy": p.pgy_level if p.type == "resident" else None,
            "type": p.type,                                    # "resident" or "faculty"
        }
        for p in people
    }
```

**Note:** `p.name` is stored as "First Last" in the DB. The converter's `_to_last_first()` converts it to "Last, First" for display in column E.

### `_fetch_rotations()` (half_day_xml_exporter.py:345-406)

```python
def _fetch_rotations(
    self,
    person_ids: list[UUID],
    block_start: date,
    block_end: date,
) -> dict[UUID, dict[str, Any]]:
    """Fetch rotation info from block_assignments for the date range."""
    from app.utils.academic_blocks import get_block_number_for_date
    block_num, acad_year = get_block_number_for_date(block_start)

    stmt = (
        select(BlockAssignment)
        .options(
            selectinload(BlockAssignment.rotation_template),
            selectinload(BlockAssignment.secondary_rotation_template),
        )
        .where(
            BlockAssignment.resident_id.in_(person_ids),
            BlockAssignment.block_number == block_num,
            BlockAssignment.academic_year == acad_year,
        )
    )

    result = self.db.execute(stmt)
    block_assignments = result.scalars().all()

    rotation_map: dict[UUID, dict[str, Any]] = {}
    for ba in block_assignments:
        rotation1 = ""
        rotation2 = ""
        if ba.rotation_template:
            rotation1 = (
                ba.rotation_template.display_abbreviation
                or ba.rotation_template.abbreviation or ""
            )
        if ba.secondary_rotation_template:
            rotation2 = (
                ba.secondary_rotation_template.display_abbreviation
                or ba.secondary_rotation_template.abbreviation or ""
            )
        rotation_map[ba.resident_id] = {
            "id": str(ba.id),
            "rotation1": rotation1,
            "rotation2": rotation2,
        }

    return rotation_map
```

**Potential gap:** The column is `BlockAssignment.resident_id` — does this work for faculty too? Faculty are also stored in `block_assignments` with the same `resident_id` FK? If faculty don't have `block_assignments` rows, `rotation_info` will be empty for them — meaning no rotation1/rotation2 (which may be correct for faculty).

### `_fetch_call_assignments()` (half_day_xml_exporter.py:456-486)

```python
def _fetch_call_assignments(
    self,
    block_start: date,
    block_end: date,
) -> list[dict[str, Any]]:
    """Fetch call assignments for date range."""
    stmt = (
        select(CallAssignment)
        .join(Person, CallAssignment.person_id == Person.id)
        .where(
            CallAssignment.date >= block_start,
            CallAssignment.date <= block_end,
        )
        .options(selectinload(CallAssignment.person))
    )
    result = self.db.execute(stmt)
    calls = result.scalars().all()

    call_rows: list[dict[str, Any]] = []
    for ca in calls:
        name = ca.person.name if ca.person else ""
        last_name = name.split(",")[0] if "," in name else name
        call_rows.append({
            "date": ca.date,
            "staff": last_name,
        })

    return call_rows
```

**Potential gap:** `last_name` extraction assumes "Last, First" format (`name.split(",")[0]`). But `_fetch_people` shows `p.name` is "First Last" — no comma. So `last_name` would be the full "First Last" string, not just the last name. This means the call row would show full names instead of last names.

---

## Section 6: Row Filling Logic

### Converter Initialization (xml_to_xlsx_converter.py:96-143)

```python
def __init__(
    self,
    template_path: Path | str | None = None,
    apply_colors: bool = True,
    structure_xml_path: Path | str | None = None,
    use_block_template2: bool = True,
    strict_row_mapping: bool = False,
    include_qa_sheet: bool = True,
    preserve_template_identity_fields: bool = True,
    presentation_profile: str = "tamc_handjam_v2",
) -> None:
    self.template_path = Path(template_path) if template_path else None
    self.apply_colors = apply_colors
    self.use_block_template2 = use_block_template2
    self.strict_row_mapping = strict_row_mapping
    # ...

    # Load row mappings from structure XML if provided
    self.row_mappings: dict[str, int] = {}         # name → row number
    self.pgy_mappings: dict[str, int] = {}         # name → pgy level
    self.template_mappings: dict[str, str] = {}    # name → template code
    self.call_row: int = BT2_ROW_STAFF_CALL        # default 4
    if structure_xml_path:
        self._load_structure_xml(Path(structure_xml_path))
```

### `_load_structure_xml()` (xml_to_xlsx_converter.py:145-185)

```python
def _load_structure_xml(self, xml_path: Path) -> None:
    """Load row mappings from BlockTemplate2_Structure.xml."""
    if not xml_path.exists():
        logger.warning(f"Structure XML not found: {xml_path}")
        return

    tree = ElementTree.parse(xml_path)
    root = tree.getroot()

    layout = root.find("layout")
    if layout is not None:
        call_row_elem = layout.find("call_row")
        if call_row_elem is not None:
            self.call_row = int(call_row_elem.get("row", "4"))

    for resident in root.findall(".//resident"):
        name = resident.get("name", "")
        row = resident.get("row", "")
        pgy = resident.get("pgy", "")
        if name and row:
            normalized = name.replace("*", "").strip()
            self.row_mappings[normalized] = int(row)
            if pgy:
                self.pgy_mappings[normalized] = int(pgy)
                self.template_mappings[normalized] = f"R{pgy}"

    for person in root.findall(".//faculty/person"):
        name = person.get("name", "")
        row = person.get("row", "")
        template = person.get("template", "C19")
        if name and row:
            normalized = name.replace("*", "").strip()
            self.row_mappings[normalized] = int(row)
            self.template_mappings[normalized] = template
```

### Template vs No-Template Branching (xml_to_xlsx_converter.py:230-242)

```python
# Load template or create new workbook
if self.template_path and self.template_path.exists():
    wb = load_workbook(self.template_path)
    if "Block Template2" in wb.sheetnames:
        sheet = wb["Block Template2"]
    else:
        sheet = wb.active
else:
    # Create new workbook (ROSETTA validation format)
    wb = self._create_new_workbook(block_start, block_end)
    sheet = wb.active
```

### `_fill_call_row()` (xml_to_xlsx_converter.py:1212-1247)

```python
def _fill_call_row(
    self,
    sheet,
    call_rows: list[dict[str, Any]],
    block_start: date,
    block_end: date,
) -> None:
    """Fill call row with staff names (single cells, user merges manually).

    Writes staff name to AM column only (even columns 6, 8, 10, ...).
    Row position comes from self.call_row (default 4, from structure XML).
    """
    call_lookup: dict[date, str] = {}
    for night in call_rows:
        night_date = self._coerce_date(night.get("date"))
        if not night_date:
            continue
        staff_name = night.get("staff", "")
        if staff_name:
            call_lookup[night_date] = staff_name

    current = block_start
    col = COL_SCHEDULE_START  # Column 6
    while current <= block_end:
        staff = call_lookup.get(current, "")
        if staff:
            cell = self._get_writable_cell(sheet, row=self.call_row, column=col)
            cell.value = staff
        current += timedelta(days=1)
        col += 2  # Skip PM column (write to AM only)
```

### `_to_last_first()` (xml_to_xlsx_converter.py:1030-1037)

```python
def _to_last_first(self, name: str) -> str:
    """Convert 'First Last' to 'Last, First' format."""
    if not name or "," in name:
        return name  # Already in Last, First format or empty
    parts = name.strip().split()
    if len(parts) >= 2:
        return f"{parts[-1]}, {' '.join(parts[:-1])}"
    return name
```

### Column Constants (xml_to_xlsx_converter.py:50-69)

```python
# BLOCK TEMPLATE2 FORMAT (production, full TAMC layout)
# Column Layout: Rotation1, Rotation2, Template, Role, Name, Schedule...
BT2_COL_ROTATION1 = 1    # col A
BT2_COL_ROTATION2 = 2    # col B
BT2_COL_TEMPLATE = 3     # col C
BT2_COL_ROLE = 4         # col D
BT2_COL_NAME = 5         # col E
BT2_COL_SCHEDULE_START = 6  # col F

# Special rows in Block Template2
BT2_ROW_STAFF_CALL = 4
BT2_ROW_RESIDENT_CALL = 5

# Date-to-column calculation
COLS_PER_DAY = 2   # AM (even col), PM (odd col+1)
TOTAL_DAYS = 28
```

---

## Section 7: Questions for Gemini

### Question 1: Fastest Path to Unblock

Given the three blockers, what's the fastest path to a working Block 12 export? Consider these options and recommend **one**:

**(a) Generate Structure XML dynamically from DB:** Query `Person` + `BlockAssignment` for Block 12, group by PGY, assign rows following the BT2 layout convention (PGY3 start at 9, PGY2 after, PGY1 after, gap, faculty start at 31). Write XML string and pass to converter.

**(b) Manually create Structure XML with real names:** Hand-edit the XML file with actual names from the DB. Low-tech but fast.

**(c) One-time Python script:** Query DB, generate XML, save to `backend/data/BlockTemplate2_Structure.xml`. Run before export. Manual step but automated content.

**(d) Skip structure XML entirely:** Modify `_fill_residents()` to assign rows programmatically when `row_mappings` is empty AND `use_block_template2=True`. Use PGY-based grouping without an XML file.

For each option, comment on: maintenance burden, what happens when the roster changes next block, and whether it handles variable PGY class sizes.

### Question 2: Template XLSX Strategy

We need `BlockTemplate2_Official.xlsx` with formatted headers, merged cells, colors, row dimensions, and summary formula columns (BJ-BR). Options:

**(a) Create manually in Excel:** Open Excel, build the template by hand with all formatting, save as the official template. Pros: exact control. Cons: hard to version, must rebuild if layout changes.

**(b) Generate programmatically with openpyxl:** Write a `generate_template()` function that creates the formatted workbook. Pros: reproducible, version-controlled. Cons: lots of formatting code.

**(c) Make converter create formatting on the fly:** When no template exists, have `convert_from_data()` create a BT2-formatted workbook instead of falling back to ROSETTA. Pros: no separate template file. Cons: mixes data logic and formatting logic.

Which approach for a solo developer who needs this working quickly but also needs it maintainable?

### Question 3: Dynamic Structure XML Generation

If we go with option (a) from Question 1, design the method. It should:

1. Query all active residents assigned to Block 12 (via `BlockAssignment` where `block_number=12, academic_year=2025`)
2. Query all active faculty who have `HalfDayAssignment` records in the Block 12 date range
3. Group residents by PGY level (3→2→1)
4. Assign row numbers following BT2 convention: PGY-3 starts at row 9, PGY-2 immediately after PGY-3 ends, PGY-1 after PGY-2, faculty starts at row 31 (or dynamically after a gap)
5. Assign faculty template codes — how do we determine C19 vs ADJ vs SPEC from the DB?
6. Return either an XML string or directly populate `row_mappings`/`template_mappings` dicts

Show pseudocode. Consider: what if a resident has no `BlockAssignment` for Block 12 but does have `HalfDayAssignment` records? (Orphaned assignments.)

### Question 4: Person Count Flexibility

The current XML has fixed PGY bands: 5 PGY-3, 6 PGY-2, 6 PGY-1, 13 faculty. Real data varies by block.

If Block 12 has 4 PGY-3s and 7 PGY-2s, what should happen? Options:

**(a) Fixed bands with overflow:** Keep 5/6/6 structure, skip unused rows, raise error if overflow.

**(b) Dynamic bands:** Compute row assignments based on actual counts. PGY-3 starts at 9, PGY-2 at 9+count(PGY3), etc.

**(c) Hybrid:** Fixed starting rows with empty-row filling, but allow bands to grow into the gap (rows 26-30) if needed.

The template XLSX (if we create one) needs to accommodate the maximum expected count. What's the right design?

### Question 5: Faculty Call Completeness

The call data flow is:

1. `export_block_xlsx()` calls `_export_json_data()` with `include_call=True`
2. `HalfDayJSONExporter.export()` calls `_fetch_call_assignments(block_start, block_end)`
3. Returns `{"call": {"nights": [{"date": "2026-05-07", "staff": "Smith"}]}}`
4. Converter receives `data["call"]["nights"]` and calls `_fill_call_row()`
5. Writes staff name to row 4, AM column for each date

**Potential bugs I see:**
- `_fetch_call_assignments()` extracts `last_name = name.split(",")[0]` but DB stores "First Last" (no comma) — so it returns the full name, not last name
- The call row shows **staff** call (row 4) — is there also a **resident** call row (row 5)? The structure XML defines `resident_call_row row="5"` but I see no code that fills it
- Are call assignments present in the DB for Block 12? The `call_assignments` table needs to be populated

Review this flow and identify any wiring gaps.

### Question 6: Name Format Alignment

The current name format pipeline:

| Stage | Format | Source |
|-------|--------|--------|
| DB `Person.name` | "First Last" | PostgreSQL |
| JSON export | "First Last" | `_fetch_people()` returns `p.name` |
| Structure XML | "Last, First" | Manually written |
| Converter display | "Last, First" | `_to_last_first()` converts before writing col E |
| Structure XML lookup | "Last, First" matching against "Last, First" | XML entry names |

The problem: JSON data has "First Last", XML mappings have "Last, First". The converter's lookup at line 1074 does:
```python
normalized = name.replace("*", "").strip()  # "First Last"
lookup_name = normalized                     # "First Last"
```
Then checks `self.row_mappings` which has keys like "Last, First". No match.

The comma-swap fallback at line 1077 triggers only if `"," in lookup_name` — but "First Last" has no comma. So it never fires.

The first-name fuzzy match at line 1086 might work if first names are unique, but it's fragile.

**If we generate the Structure XML from DB data, should we:**
(a) Store names in the XML as "First Last" (matching DB), or
(b) Store as "Last, First" (matching display convention), or
(c) Use person UUID as the XML key instead of name?

### Question 7: Verification Plan

After fixing the blockers, how do we verify the output is correct?

**(a) pytest against real DB:**
```python
def test_export_block_12_real_data():
    service = CanonicalScheduleExportService(db)
    xlsx_bytes = service.export_block_xlsx(12, 2025)
    wb = load_workbook(io.BytesIO(xlsx_bytes))
    # Assert sheet name, row count, cell values...
```
Pro: automated, repeatable. Con: DB state dependency.

**(b) Manual Excel inspection:**
Open the XLSX in Excel, visually confirm: all names present, rotations correct, call row populated, AM/PM codes match expected schedule.

**(c) Round-trip test:**
Export → immediately re-import → verify 0 diffs. This proves symmetry but not correctness (could be symmetrically wrong).

**(d) Side-by-side with existing hand-jam:**
Compare the export output cell-by-cell against the coordinator's manually-created Block 12 spreadsheet (if one exists).

Recommend a verification strategy that gives confidence with minimal effort.

---

## Section 8: Key File Paths

### Backend Services (Export Chain)
- `backend/app/services/canonical_schedule_export_service.py` — orchestrator
- `backend/app/services/half_day_json_exporter.py` — DB → JSON
- `backend/app/services/half_day_xml_exporter.py` — parent class with `_fetch_*` methods
- `backend/app/services/json_to_xlsx_converter.py` — thin wrapper, delegates to XMLToXlsxConverter
- `backend/app/services/xml_to_xlsx_converter.py` — core converter (1260 lines)
- `backend/app/services/excel_metadata.py` — Phase 1 metadata utilities
- `backend/app/services/tamc_color_scheme.py` — activity code → color mapping

### Models
- `backend/app/models/person.py` — `Person` (name, type, pgy_level)
- `backend/app/models/block_assignment.py` — `BlockAssignment` (resident_id, rotation_template, block_number)
- `backend/app/models/half_day_assignment.py` — `HalfDayAssignment` (person_id, date, time_of_day, activity)
- `backend/app/models/call_assignment.py` — `CallAssignment` (person_id, date)
- `backend/app/models/activity.py` — `Activity` (code, name)
- `backend/app/models/rotation_template.py` — `RotationTemplate` (abbreviation, display_abbreviation)

### Utilities
- `backend/app/utils/academic_blocks.py` — `get_block_dates()`, `get_block_number_for_date()`

### Data Files
- `docs/scheduling/BlockTemplate2_Structure.xml` — current location (wrong path)
- `backend/data/` — expected location (only contains `csv_files/`)

### Tests
- `backend/tests/services/test_canonical_schedule_export.py`
- `backend/tests/services/test_excel_metadata.py`
- `backend/tests/services/test_half_day_import_service.py`

### API Route
- `backend/app/api/routes/half_day_exports.py` — `GET /api/v1/half-day/export/block`

---

## Appendix A: Block 12 Date Calculation

From `backend/app/utils/academic_blocks.py`:

```
AY 2025 starts July 1, 2025
First Thursday of July 2025 = July 3, 2025

Block 12 start = first_thursday + (12-1) * 28 = July 3 + 308 days = May 7, 2026 (Thursday)
Block 12 end = start + 27 = June 3, 2026 (Wednesday)
Duration: 28 days (standard block)
```

This is the last standard block before Block 13 (variable length, June 4 - June 30).

## Appendix B: ExportMetadata Dataclass

From `backend/app/services/excel_metadata.py`:

```python
@dataclass
class ExportMetadata:
    """Metadata blob for exported Excel files."""
    academic_year: int
    export_timestamp: str
    block_number: int | None = None       # Optional for year-level
    export_version: int = 1
    block_map: dict[str, str] | None = None  # sheet_name -> block_uuid (year export)
    llm_rules_of_engagement: str | None = None  # AI agent instructions
```

Written to `__SYS_META__` veryHidden sheet as JSON. Read back by `read_sys_meta()` for import validation (block mismatch rejection).

## Appendix C: BT2 Column and Row Constants

```
COLUMNS:
  A (col 1) = Rotation1 (first-half rotation abbreviation)
  B (col 2) = Rotation2 (second-half rotation, if mid-block switch)
  C (col 3) = Template code (R1, R2, R3, C19, ADJ, SPEC)
  D (col 4) = Role (PGY 1, PGY 2, PGY 3, FAC)
  E (col 5) = Name ("Last, First" format)
  F-BI (cols 6-61) = Schedule (2 cols/day × 28 days: AM, PM, AM, PM, ...)
  BJ-BR (cols 62-70) = Summary formulas (clinic counts, leave totals, etc.)

ROWS:
  1-3   = Headers (dates, day names, AM/PM labels)
  4     = Staff Call (faculty on-call name per night)
  5     = Resident Call (resident on-call per night)
  6-8   = Blank / section headers
  9-25  = Residents (grouped by PGY: 3, 2, 1)
  26-30 = Blank separator
  31-43 = Faculty (core C19, adjunct ADJ, specialist SPEC)
  44+   = Overflow / unused
```
