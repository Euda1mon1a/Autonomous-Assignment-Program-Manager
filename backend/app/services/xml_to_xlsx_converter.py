"""
XML to XLSX Converter (legacy/validation).

Converts schedule XML to Excel format.
Canonical export now uses JSON → JSONToXlsxConverter, but XML remains
for validation and legacy tooling.

Supports two formats:
1. ROSETTA format (validation): Simple layout for testing
2. Block Template2 format (production): Full TAMC layout with all rows/columns

Legacy pipeline:
    DB → HalfDayXMLExporter → XML → XMLToXlsxConverter → xlsx
"""

from __future__ import annotations

from collections import Counter
from copy import copy
from datetime import date, datetime, timedelta, UTC
from io import BytesIO
from pathlib import Path
from typing import Any
from defusedxml import ElementTree

from openpyxl import Workbook, load_workbook
from openpyxl.cell.cell import Cell, MergedCell
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from app.core.logging import get_logger
from app.services.tamc_color_scheme import get_color_scheme
from app.utils.academic_blocks import get_block_number_for_date

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# ROSETTA FORMAT (validation-focused, simple layout)
# ═══════════════════════════════════════════════════════════════════════════════
# Column Layout: Name, PGY, Rotation1, Rotation2, Notes, Schedule...
ROSETTA_COL_NAME = 1
ROSETTA_COL_PGY = 2
ROSETTA_COL_ROTATION1 = 3
ROSETTA_COL_ROTATION2 = 4
ROSETTA_COL_NOTES = 5
ROSETTA_COL_SCHEDULE_START = 6

# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK TEMPLATE2 FORMAT (production, full TAMC layout)
# ═══════════════════════════════════════════════════════════════════════════════
# Column Layout: Rotation1, Rotation2, Template, Role, Name, Schedule...
BT2_COL_ROTATION1 = 1  # First-half rotation (e.g., "Hilo", "FMC")
BT2_COL_ROTATION2 = 2  # Second-half rotation (if mid-block switch)
BT2_COL_TEMPLATE = 3  # Template code (R1, R2, R3, C19, ADJ)
BT2_COL_ROLE = 4  # Role (PGY 1, PGY 2, PGY 3, FAC)
BT2_COL_NAME = 5  # Name ("Last, First")
BT2_COL_SCHEDULE_START = 6  # First schedule column

# Special rows in Block Template2
BT2_ROW_STAFF_CALL = 4
BT2_ROW_RESIDENT_CALL = 5

# Date-to-column calculation (same for both formats)
# Each date uses 2 columns: AM (even col), PM (odd col+1)
# Block 10: Mar 12-Apr 8 = 28 days = 56 columns (6-61)
COLS_PER_DAY = 2
TOTAL_DAYS = 28

# Legacy aliases for backward compatibility
ROW_HEADERS = 1
COL_RESIDENT_NAME = ROSETTA_COL_NAME
COL_PGY = ROSETTA_COL_PGY
COL_ROTATION1 = ROSETTA_COL_ROTATION1
COL_ROTATION2 = ROSETTA_COL_ROTATION2
COL_NOTES = ROSETTA_COL_NOTES
COL_SCHEDULE_START = ROSETTA_COL_SCHEDULE_START
COL_SCHEDULE_END = COL_SCHEDULE_START + (TOTAL_DAYS * COLS_PER_DAY) - 1  # 61


class XMLToXlsxConverter:
    """
    Convert HalfDayXMLExporter XML to Excel xlsx format.

    Supports two formats:
    1. ROSETTA format (validation): Simple layout - Name, PGY, Rotation, Schedule
    2. Block Template2 format (production): Full TAMC layout with correct columns

    Block Template2 format uses:
    - Column layout: Rotation1, Rotation2, Template, Role, Name, Schedule...
    - Row mappings from structure XML for exact positioning
    - Name format: "Last, First"
    """

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
        """
        Initialize converter with optional template.

        Args:
            template_path: Path to Excel template (e.g., Block_Template2.xlsx).
                          If not provided, creates new workbook.
            apply_colors: Whether to apply TAMC color scheme to cells.
            structure_xml_path: Path to BlockTemplate2_Structure.xml for row mappings.
                               If provided, uses name → row lookup instead of sequential.
            use_block_template2: If True, use Block Template2 column layout (production).
                                If False, use ROSETTA layout (validation).
            strict_row_mapping: If True, fail export when a person name has no row mapping.
            include_qa_sheet: If True, add an Export_QA worksheet with explicit
                code totals and per-faculty clinic counts.
            preserve_template_identity_fields: If True, keeps template values in
                columns A-E (rotations/template/role/name) and only writes schedule
                cells. This preserves full handjam labels/names.
            presentation_profile: Post-processing profile for summary formulas and
                freeze panes. "tamc_handjam_v2" aligns output with manual Block 10.
        """
        self.template_path = Path(template_path) if template_path else None
        self.apply_colors = apply_colors
        self.color_scheme = get_color_scheme() if apply_colors else None
        self.use_block_template2 = use_block_template2
        self.strict_row_mapping = strict_row_mapping
        self.include_qa_sheet = include_qa_sheet
        self.preserve_template_identity_fields = preserve_template_identity_fields
        self.presentation_profile = presentation_profile

        # Load row mappings from structure XML if provided
        self.row_mappings: dict[str, int] = {}
        self.pgy_mappings: dict[str, int] = {}  # name → pgy level
        self.template_mappings: dict[str, str] = {}  # name → template code
        self.call_row: int = BT2_ROW_STAFF_CALL
        self.last_conversion_stats: dict[str, Any] = {}
        if structure_xml_path:
            self._load_structure_xml(Path(structure_xml_path))

    def _load_structure_xml(self, xml_path: Path) -> None:
        """Load row mappings from BlockTemplate2_Structure.xml."""
        if not xml_path.exists():
            logger.warning(f"Structure XML not found: {xml_path}")
            return

        tree = ElementTree.parse(xml_path)
        root = tree.getroot()

        # Load layout settings
        layout = root.find("layout")
        if layout is not None:
            call_row_elem = layout.find("call_row")
            if call_row_elem is not None:
                self.call_row = int(call_row_elem.get("row", "4"))

                # Load resident row mappings (name → row, pgy, template)
        for resident in root.findall(".//resident"):
            name = resident.get("name", "")
            row = resident.get("row", "")
            pgy = resident.get("pgy", "")
            if name and row:
                # Normalize name (remove asterisks, extra spaces)
                normalized = name.replace("*", "").strip()
                self.row_mappings[normalized] = int(row)
                if pgy:
                    self.pgy_mappings[normalized] = int(pgy)
                    # Template code from PGY: R1, R2, R3
                    self.template_mappings[normalized] = f"R{pgy}"

                    # Load faculty row mappings
        for person in root.findall(".//faculty/person"):
            name = person.get("name", "")
            row = person.get("row", "")
            template = person.get("template", "C19")
            if name and row:
                normalized = name.replace("*", "").strip()
                self.row_mappings[normalized] = int(row)
                self.template_mappings[normalized] = template

        logger.info(f"Loaded {len(self.row_mappings)} row mappings from {xml_path}")

    def convert_from_string(
        self,
        xml_string: str,
        output_path: Path | str | None = None,
    ) -> bytes:
        """
        Convert XML schedule string to xlsx.

        Args:
            xml_string: XML from ScheduleXMLExporter
            output_path: Optional path to save xlsx

        Returns:
            xlsx bytes (openpyxl workbook)
        """
        root = ElementTree.fromstring(xml_string)
        data = self._parse_xml_to_data(root)
        return self.convert_from_data(data, output_path=output_path)

    def convert_from_data(
        self,
        data: dict[str, Any],
        output_path: Path | str | None = None,
    ) -> bytes:
        """Convert schedule data dict to xlsx."""
        block_start = self._coerce_date(data.get("block_start"))
        block_end = self._coerce_date(data.get("block_end"))
        if not block_start or not block_end:
            raise ValueError("Missing block_start/block_end in schedule data")

        logger.info(f"Converting schedule data to xlsx: {block_start} to {block_end}")

        # Load template or create new workbook
        if self.template_path and self.template_path.exists():
            wb = load_workbook(self.template_path)
            # Use "Block Template2" sheet if available, else active
            if "Block Template2" in wb.sheetnames:
                sheet = wb["Block Template2"]
            else:
                sheet = wb.active
            logger.info(f"Loaded template from {self.template_path}")
        else:
            # Create new workbook (ROSETTA validation format)
            wb = self._create_new_workbook(block_start, block_end)
            sheet = wb.active

        # Fill header row (always - helps with readability)
        self._fill_header_row(sheet, block_start, block_end)
        unmerged_cells = self._prepare_schedule_grid(sheet, block_start, block_end)

        # Fill residents and faculty
        residents = data.get("residents", [])
        faculty = data.get("faculty", [])
        stats: dict[str, Any] = {
            "block_start": block_start.isoformat(),
            "block_end": block_end.isoformat(),
            "residents": {
                "people_input": len(residents),
                "people_written": 0,
                "unmapped_names": [],
                "codes_written": {},
            },
            "faculty": {
                "people_input": len(faculty),
                "people_written": 0,
                "unmapped_names": [],
                "codes_written": {},
            },
        }
        stats["schedule_cells_unmerged"] = unmerged_cells
        self._fill_residents(
            sheet,
            residents,
            block_start,
            is_faculty=False,
            stats=stats["residents"],
        )
        self._fill_residents(
            sheet,
            faculty,
            block_start,
            is_faculty=True,
            stats=stats["faculty"],
        )

        # Fill call row (Row 4) - single cells for user to merge
        call_section = data.get("call", {})
        call_rows: list[dict[str, Any]] = []
        if isinstance(call_section, dict):
            call_rows = call_section.get("nights", []) or []
        elif isinstance(call_section, list):
            call_rows = call_section
        if call_rows:
            self._fill_call_row(sheet, call_rows, block_start, block_end)
        stats["call_nights_input"] = len(call_rows)
        self._apply_presentation_profile(sheet, block_start, block_end)
        self.last_conversion_stats = stats

        # Spatial UUID Anchoring (Phase 2)
        if self.use_block_template2:
            self._write_anchor_sheet(wb, data)

        # Strict UI Contracts (Phase 3)
        if self.use_block_template2:
            self._add_data_validation(sheet, block_start, block_end)

        # Stateful Overlays (Phase 4)
        if self.use_block_template2:
            self._add_dynamic_cf(sheet, block_start, block_end)
            self._add_leave_formula_column(sheet, block_start, block_end)

        if self.include_qa_sheet and self.use_block_template2:
            self._write_export_qa_sheet(wb, data, stats)
        if self.use_block_template2:
            self._prune_empty_sheets(wb, keep={"Block Template2", "Export_QA"})

        # Save to bytes
        buffer = BytesIO()
        wb.save(buffer)
        xlsx_bytes = buffer.getvalue()

        # Save to file if path provided
        if output_path:
            Path(output_path).write_bytes(xlsx_bytes)
            logger.info(f"Saved xlsx to {output_path}")

        return xlsx_bytes

    def _prepare_schedule_grid(self, sheet, block_start: date, block_end: date) -> int:
        """Unmerge schedule-grid cells in mapped rows so AM/PM can be written independently."""
        if not self.use_block_template2 or not self.row_mappings:
            return 0

        schedule_start_col = COL_SCHEDULE_START
        total_days = (block_end - block_start).days + 1
        schedule_end_col = schedule_start_col + (total_days * COLS_PER_DAY) - 1

        target_rows = set(self.row_mappings.values())
        if not target_rows:
            return 0

        merged_ranges = list(sheet.merged_cells.ranges)
        unmerged = 0

        for merged_range in merged_ranges:
            if merged_range.max_col < schedule_start_col:
                continue
            if merged_range.min_col > schedule_end_col:
                continue
            if merged_range.max_row < min(target_rows):
                continue
            if merged_range.min_row > max(target_rows):
                continue

            overlaps_target_row = any(
                merged_range.min_row <= row <= merged_range.max_row
                for row in target_rows
            )
            if not overlaps_target_row:
                continue

            top_left = sheet.cell(row=merged_range.min_row, column=merged_range.min_col)

            # Preserve style/format from top-left before unmerge.
            for row in range(merged_range.min_row, merged_range.max_row + 1):
                for col in range(merged_range.min_col, merged_range.max_col + 1):
                    if row == merged_range.min_row and col == merged_range.min_col:
                        continue
                    cell = sheet.cell(row=row, column=col)
                    cell._style = copy(top_left._style)
                    cell.number_format = top_left.number_format
                    cell.protection = copy(top_left.protection)
                    cell.alignment = copy(top_left.alignment)

            sheet.unmerge_cells(str(merged_range))
            unmerged += 1

        if unmerged:
            logger.info(f"Unmerged {unmerged} schedule cell ranges for AM/PM fidelity")
        return unmerged

    def _normalize_code(self, value: Any) -> str:
        if value is None:
            return ""
        code = str(value).strip().upper()
        return code

    def _collect_people_code_counts(
        self, people: list[dict[str, Any]]
    ) -> list[tuple[str, Counter[str]]]:
        rows: list[tuple[str, Counter[str]]] = []
        for person in sorted(people, key=lambda p: str(p.get("name", ""))):
            name = str(person.get("name", "") or "").strip()
            if not name:
                continue
            counter: Counter[str] = Counter()
            for day in person.get("days", []) or []:
                am = self._normalize_code(day.get("am", ""))
                pm = self._normalize_code(day.get("pm", ""))
                if am:
                    counter[am] += 1
                if pm:
                    counter[pm] += 1
            rows.append((name, counter))
        return rows

    def _apply_presentation_profile(
        self, sheet, block_start: date, block_end: date
    ) -> None:
        """Apply output formatting profile overlays for Block Template2."""
        if not self.use_block_template2:
            return
        if self.presentation_profile != "tamc_handjam_v2":
            return
        self._apply_tamc_handjam_summary_layout(sheet, block_start, block_end)

    def _apply_tamc_handjam_summary_layout(
        self, sheet, block_start: date, block_end: date
    ) -> None:
        """Align summary headers/formulas/freeze panes with handjam Block 10."""
        # Keep navigation locked to schedule start while exposing summary rows.
        sheet.freeze_panes = "F50"

        summary_headers = [
            "C",
            "CC",
            "CV",
            "(C+CC+CV)",
            "NF",
            "CC",
            "PC/OFF",
            "LV",
            "FMIT",
        ]
        for idx, header in enumerate(summary_headers):
            sheet.cell(row=8, column=62 + idx).value = header

        for row in range(9, 29):
            c_terms = '{"C","C-I","SM"}' if row == 9 else '{"C","CV","C-I","SM"}'
            sheet.cell(
                row=row, column=62
            ).value = f"=SUMPRODUCT(COUNTIF(F{row}:BI{row}, {c_terms}))"
            sheet.cell(row=row, column=63).value = f'=COUNTIF(F{row}:BI{row}, "CC")'
            sheet.cell(row=row, column=64).value = f'=COUNTIF(F{row}:BI{row}, "CV")'
            sheet.cell(row=row, column=65).value = f"=BJ{row}+BK{row}+BL{row}"
            sheet.cell(row=row, column=66).value = f'=COUNTIF(F{row}:BI{row}, "NF")'
            sheet.cell(row=row, column=67).value = f'=COUNTIF(F{row}:BI{row}, "CC")'
            sheet.cell(
                row=row, column=68
            ).value = f'=SUMPRODUCT(COUNTIF(F{row}:BI{row}, {{"PC","OFF","W"}}))'
            sheet.cell(row=row, column=69).value = f'=COUNTIF(F{row}:BI{row}, "LV")'
            sheet.cell(row=row, column=70).value = f'=COUNTIF(F{row}:BI{row}, "FMIT")'

        sheet.cell(row=29, column=62).value = "=SUM(BJ9:BJ26)"
        sheet.cell(row=29, column=63).value = "=SUM(BK9:BK26)"
        sheet.cell(row=29, column=64).value = "=SUM(BL9:BL26)"
        sheet.cell(row=29, column=65).value = "=SUM(BM9:BM26)"
        sheet.cell(row=29, column=66).value = "=SUM(BN9:BN28)"
        sheet.cell(row=29, column=67).value = "=SUM(BP9:BP28)"
        sheet.cell(row=29, column=68).value = "=SUM(BQ9:BQ28)"
        sheet.cell(row=29, column=69).value = "=SUM(BR9:BR28)"
        sheet.cell(row=29, column=70).value = None

        row30_headers = [
            "C",
            "CC",
            "CV",
            "(C+CC+CV)",
            "AT",
            "ADM",
            "LV",
            "FMIT",
            "CALL",
        ]
        for idx, header in enumerate(row30_headers):
            sheet.cell(row=30, column=62 + idx).value = header

        for row in range(31, 43):
            sheet.cell(
                row=row, column=62
            ).value = f'=SUMPRODUCT(COUNTIF(F{row}:BI{row}, {{"C","SM"}}))'
            sheet.cell(row=row, column=63).value = f'=COUNTIF(F{row}:BI{row}, "CC")'
            sheet.cell(row=row, column=64).value = f'=COUNTIF(F{row}:BI{row}, "CV")'
            sheet.cell(row=row, column=65).value = f"=BJ{row}+BK{row}+BL{row}"
            sheet.cell(
                row=row, column=66
            ).value = f'=SUMPRODUCT(COUNTIF(F{row}:BI{row}, {{"AT","PCAT","DO"}}))'
            sheet.cell(
                row=row, column=67
            ).value = f'=SUMPRODUCT(COUNTIF(F{row}:BI{row}, {{"GME","DFM","DOFM"}}))'
            sheet.cell(row=row, column=68).value = f'=COUNTIF(F{row}:BI{row}, "LV")'
            sheet.cell(row=row, column=69).value = f'=COUNTIF(F{row}:BI{row}, "FMIT")'
            call_name = self._call_last_name_token(sheet.cell(row=row, column=5).value)
            sheet.cell(row=row, column=70).value = (
                f'=COUNTIF(F4:BI4, "{call_name}")' if call_name else None
            )

        sheet.cell(row=43, column=62).value = "=SUM(BJ31:BJ42)"
        sheet.cell(row=43, column=63).value = "=SUM(BK31:BK42)"
        sheet.cell(row=43, column=64).value = "=SUM(BL31:BL42)"
        sheet.cell(row=43, column=65).value = "=SUM(BM31:BM42)"
        sheet.cell(row=43, column=66).value = "=SUM(BN31:BN42)"
        sheet.cell(row=43, column=67).value = "=SUM(BO31:BO42)"
        sheet.cell(row=43, column=68).value = "=SUM(BP31:BP42)"
        sheet.cell(row=43, column=69).value = "=SUM(BQ31:BQ42)"
        sheet.cell(row=43, column=70).value = "=SUM(BR31:BR42)"
        sheet.cell(row=44, column=62).value = "%CVf"
        sheet.cell(row=44, column=64).value = "=BL43/(BJ43+BK43+BL43)*100"

    def _call_last_name_token(self, raw_name: Any) -> str:
        if not raw_name:
            return ""
        text = str(raw_name).replace("*", "").strip()
        if not text:
            return ""
        if "," in text:
            last = text.split(",", 1)[0]
        else:
            last = text.split()[-1]
        return " ".join(last.split()).upper()

    def _write_export_qa_sheet(
        self, wb: Workbook, data: dict[str, Any], stats: dict[str, Any]
    ) -> None:
        """Write a human-readable QA sheet with explicit code breakdowns."""
        if "Export_QA" in wb.sheetnames:
            del wb["Export_QA"]
        qa = wb.create_sheet("Export_QA")

        bold = Font(bold=True)
        qa["A1"] = "Export QA Summary"
        qa["A1"].font = bold
        qa["A2"] = "Generated UTC"
        qa["B2"] = f"{datetime.now(UTC).isoformat(timespec='seconds')}Z"
        qa["A3"] = "Block Start"
        qa["B3"] = str(stats.get("block_start", ""))
        qa["A4"] = "Block End"
        qa["B4"] = str(stats.get("block_end", ""))
        qa["A5"] = "Source"
        qa["B5"] = str(data.get("source", "unknown"))
        qa["A6"] = "Unmerged Schedule Ranges"
        qa["B6"] = int(stats.get("schedule_cells_unmerged", 0))
        qa["A7"] = "Presentation Profile"
        qa["B7"] = self.presentation_profile
        qa["C7"] = "Identity Fields"
        qa["D7"] = (
            "template-preserved"
            if self.preserve_template_identity_fields
            else "db-written"
        )

        qa["A9"] = "Section"
        qa["B9"] = "People Input"
        qa["C9"] = "People Written"
        qa["D9"] = "Unmapped Names"
        qa["E9"] = "Non-empty Cells"
        for cell in ("A9", "B9", "C9", "D9", "E9"):
            qa[cell].font = bold

        for idx, section in enumerate(("residents", "faculty"), start=10):
            section_stats = stats.get(section, {})
            qa.cell(row=idx, column=1, value=section.title())
            qa.cell(row=idx, column=2, value=int(section_stats.get("people_input", 0)))
            qa.cell(
                row=idx, column=3, value=int(section_stats.get("people_written", 0))
            )
            unmapped = section_stats.get("unmapped_names", []) or []
            qa.cell(row=idx, column=4, value=", ".join(str(n) for n in unmapped))
            codes_written = section_stats.get("codes_written", {}) or {}
            qa.cell(
                row=idx, column=5, value=sum(int(v) for v in codes_written.values())
            )

        resident_codes = Counter(
            {
                k: int(v)
                for k, v in (
                    stats.get("residents", {}).get("codes_written", {}) or {}
                ).items()
            }
        )
        faculty_codes = Counter(
            {
                k: int(v)
                for k, v in (
                    stats.get("faculty", {}).get("codes_written", {}) or {}
                ).items()
            }
        )
        combined_codes = resident_codes + faculty_codes

        qa["A14"] = "Code"
        qa["B14"] = "Residents"
        qa["C14"] = "Faculty"
        qa["D14"] = "Combined"
        for cell in ("A14", "B14", "C14", "D14"):
            qa[cell].font = bold

        code_row = 15
        for code in sorted(combined_codes):
            qa.cell(row=code_row, column=1, value=code)
            qa.cell(row=code_row, column=2, value=int(resident_codes.get(code, 0)))
            qa.cell(row=code_row, column=3, value=int(faculty_codes.get(code, 0)))
            qa.cell(row=code_row, column=4, value=int(combined_codes.get(code, 0)))
            code_row += 1

        qa["F9"] = "Note"
        qa["F9"].font = bold
        qa["F10"] = (
            "Template summary columns on Block Template2 are composite in places "
            "(e.g. BJ may include C with SM/C-I). Use this sheet for explicit counts."
        )

        qa["F14"] = "Faculty Clinic Detail"
        qa["F14"].font = bold
        qa["F15"] = "Name"
        qa["G15"] = "C"
        qa["H15"] = "SM"
        qa["I15"] = "C+SM"
        for cell in ("F15", "G15", "H15", "I15"):
            qa[cell].font = bold

        faculty_people = self._collect_people_code_counts(data.get("faculty", []) or [])
        faculty_row = 16
        for name, counter in faculty_people:
            c_count = int(counter.get("C", 0))
            sm_count = int(counter.get("SM", 0))
            qa.cell(row=faculty_row, column=6, value=name)
            qa.cell(row=faculty_row, column=7, value=c_count)
            qa.cell(row=faculty_row, column=8, value=sm_count)
            qa.cell(row=faculty_row, column=9, value=c_count + sm_count)
            faculty_row += 1

        for col, width in (
            ("A", 28),
            ("B", 16),
            ("C", 16),
            ("D", 40),
            ("E", 16),
            ("F", 42),
            ("G", 10),
            ("H", 10),
            ("I", 10),
        ):
            qa.column_dimensions[col].width = width

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

            row_hash = compute_row_hash(
                UUID(person_id), rotation1, rotation2, days_codes
            )

            # Write to anchor sheet at matching row (Spatial Anchoring)
            ws.cell(row=row, column=1, value=str(person_id))
            ws.cell(row=row, column=2, value=str(person.get("block_assignment_id", "")))
            ws.cell(row=row, column=3, value=row_hash)

    def _add_data_validation(self, sheet, block_start: date, block_end: date) -> None:
        """Add Excel DataValidation dropdowns referencing __REF__ Named Ranges.

        Note: The Named Ranges (ValidRotations, ValidActivities) are created globally
        in canonical_schedule_export_service.py. The dropdowns are applied here.
        """
        from openpyxl.worksheet.datavalidation import DataValidation

        # Rotation columns: dropdown from ValidRotations named range
        rot_dv = DataValidation(
            type="list", formula1="ValidRotations", allow_blank=True
        )
        sheet.add_data_validation(rot_dv)

        # Activity columns: dropdown from ValidActivities named range
        act_dv = DataValidation(
            type="list", formula1="ValidActivities", allow_blank=True
        )
        sheet.add_data_validation(act_dv)

        schedule_start_col = COL_SCHEDULE_START
        total_days = (block_end - block_start).days + 1
        schedule_end_col = schedule_start_col + (total_days * COLS_PER_DAY) - 1

        # Apply to all mapped resident/faculty rows
        target_rows = sorted(set(self.row_mappings.values()))
        if not target_rows:
            return

        for row in target_rows:
            # Rotation columns (A and B)
            rot_dv.add(sheet.cell(row=row, column=BT2_COL_ROTATION1))
            rot_dv.add(sheet.cell(row=row, column=BT2_COL_ROTATION2))

            # Schedule columns (F through schedule end)
            for col in range(schedule_start_col, schedule_end_col + 1):
                act_dv.add(sheet.cell(row=row, column=col))

    def _add_dynamic_cf(self, sheet, block_start: date, block_end: date) -> None:
        """Add dynamic conditional formatting rules based on tamc_color_scheme."""
        from openpyxl.formatting.rule import CellIsRule
        from openpyxl.styles import Font, PatternFill

        if not self.color_scheme:
            return

        schedule_start_col = COL_SCHEDULE_START
        total_days = (block_end - block_start).days + 1
        schedule_end_col = schedule_start_col + (total_days * COLS_PER_DAY) - 1

        # Standard grid range for Block Template 2
        min_row = 9
        max_row = 69
        grid_range = f"{get_column_letter(schedule_start_col)}{min_row}:{get_column_letter(schedule_end_col)}{max_row}"

        # Add rules for each code in scheme
        for code, bg_color in self.color_scheme._code_colors.items():
            fg_color = self.color_scheme._font_colors.get(code, "000000")

            rule = CellIsRule(
                operator="equal",
                formula=[f'"{code}"'],
                fill=PatternFill(start_color=bg_color, fill_type="solid"),
                font=Font(color=fg_color),
            )
            sheet.conditional_formatting.add(grid_range, rule)

    def _add_leave_formula_column(
        self, sheet, block_start: date, block_end: date
    ) -> None:
        """Add a column that auto-calculates leave days from the grid."""
        # Standard summary position: Column BS (71)
        leave_col = 71
        sheet.cell(row=8, column=leave_col, value="LV Days")

        schedule_start_col_letter = get_column_letter(COL_SCHEDULE_START)

        # Calculate end column dynamically based on block length
        actual_days = (block_end - block_start).days + 1
        schedule_end_col_letter = get_column_letter(
            COL_SCHEDULE_START + (actual_days * COLS_PER_DAY) - 1
        )

        for row in range(9, 70):
            # Formula: count LV codes and divide by 2 (AM/PM slots)
            sheet.cell(
                row=row,
                column=leave_col,
                value=f'=COUNTIF({schedule_start_col_letter}{row}:{schedule_end_col_letter}{row}, "LV")/2',
            )

    def _prune_empty_sheets(self, wb: Workbook, keep: set[str]) -> None:
        """Remove placeholder sheets that contain no data."""
        for name in list(wb.sheetnames):
            if name in keep:
                continue
            ws = wb[name]
            if ws.max_row == 1 and ws.max_column == 1 and ws["A1"].value in (None, ""):
                del wb[name]

    def _parse_xml_to_data(self, root: ElementTree.Element) -> dict[str, Any]:
        """Parse XML schedule into a JSON-like dict."""
        block_start = root.get("block_start", "")
        block_end = root.get("block_end", "")

        def _parse_people(elements: list[ElementTree.Element]) -> list[dict[str, Any]]:
            people: list[dict[str, Any]] = []
            for elem in elements:
                person = {
                    "name": elem.get("name", ""),
                    "pgy": elem.get("pgy", ""),
                    "rotation1": elem.get("rotation1", ""),
                    "rotation2": elem.get("rotation2", ""),
                    "days": [],
                }
                for day in elem.findall("day"):
                    person["days"].append(
                        {
                            "date": day.get("date", ""),
                            "am": day.get("am", ""),
                            "pm": day.get("pm", ""),
                        }
                    )
                people.append(person)
            return people

        residents = _parse_people(root.findall(".//resident"))
        faculty = _parse_people(root.findall(".//faculty"))

        call_rows: list[dict[str, Any]] = []
        call_section = root.find(".//call")
        if call_section is not None:
            for night in call_section.findall("night"):
                call_rows.append(
                    {
                        "date": night.get("date", ""),
                        "staff": night.get("staff", ""),
                    }
                )

        return {
            "block_start": block_start,
            "block_end": block_end,
            "source": root.get("source", "xml"),
            "residents": residents,
            "faculty": faculty,
            "call": {"nights": call_rows},
        }

    def _coerce_date(self, value: Any) -> date | None:
        """Coerce ISO date string or datetime/date into date."""
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str) and value:
            return date.fromisoformat(value)
        return None

    def _apply_cell_color(self, cell, code: str) -> None:
        """Apply background and font color to cell based on schedule code.

        Font colors have semantic meaning:
        - Red: procedures needing supervision (PR adds +1 AT), or high-visibility roles
        - Light gray: Night Float (NF, Peds NF)
        - White: Contrast on dark backgrounds
        """
        if not self.apply_colors or not self.color_scheme:
            return

            # Apply fill color
        hex_color = self.color_scheme.get_code_color(code)
        if hex_color:
            cell.fill = PatternFill(start_color=hex_color, fill_type="solid")

            # Apply font color (priority: explicit mapping > contrast fallback)
        font_color = self.color_scheme.get_font_color(code)
        if font_color:
            cell.font = Font(color=font_color)
        elif hex_color in ("000000", "FF0000"):
            # Fallback: white text on dark backgrounds
            cell.font = Font(color="FFFFFF")

    def _apply_header_color(self, cell, day_of_week: int) -> None:
        """Apply header background color based on day of week."""
        if not self.apply_colors or not self.color_scheme:
            return

        hex_color = self.color_scheme.get_header_color(day_of_week)
        if hex_color and hex_color != "FFFFFF":  # Skip white (default)
            cell.fill = PatternFill(start_color=hex_color, fill_type="solid")

    def _apply_rotation_color(self, cell, rotation: str) -> None:
        """Apply color to rotation column cell."""
        if not self.apply_colors or not self.color_scheme:
            return

        hex_color = self.color_scheme.get_rotation_color(rotation)
        if hex_color:
            cell.fill = PatternFill(start_color=hex_color, fill_type="solid")
            # Use white text for dark backgrounds
            if hex_color in ("000000", "FF0000"):
                cell.font = Font(color="FFFFFF")

    def _create_new_workbook(
        self,
        block_start: date,
        block_end: date,
    ) -> Workbook:
        """Create new workbook matching ROSETTA validation format."""
        wb = Workbook()
        sheet = wb.active

        # Calculate block number
        block_number = self._calculate_block_number(block_start)
        sheet.title = f"Block{block_number}_GENERATED"

        # Set column widths
        sheet.column_dimensions["A"].width = 20  # Resident name
        sheet.column_dimensions["B"].width = 5  # PGY
        sheet.column_dimensions["C"].width = 12  # Rotation1
        sheet.column_dimensions["D"].width = 12  # Rotation2
        sheet.column_dimensions["E"].width = 30  # Notes
        for col in range(COL_SCHEDULE_START, COL_SCHEDULE_END + 1):
            sheet.column_dimensions[get_column_letter(col)].width = 6

        return wb

    def _get_writable_cell(self, sheet, row: int, column: int) -> Cell:
        """Return a writable cell, resolving merged ranges to their top-left cell."""
        cell = sheet.cell(row=row, column=column)
        if isinstance(cell, MergedCell):
            coord = f"{get_column_letter(column)}{row}"
            for merged_range in sheet.merged_cells.ranges:
                if coord in merged_range:
                    return sheet.cell(
                        row=merged_range.min_row, column=merged_range.min_col
                    )
        return cell

    def _fill_block_template2_headers(
        self,
        sheet,
        block_start: date,
        block_end: date,
    ) -> None:
        """Update day-of-week and date headers for Block Template2."""
        day_full = {
            0: "MON",
            1: "TUE",
            2: "WED",
            3: "THURS",
            4: "FRI",
            5: "SAT",
            6: "SUN",
        }
        day_abbrev = {
            0: "MON",
            1: "TUE",
            2: "WED",
            3: "THU",
            4: "FRI",
            5: "SAT",
            6: "SUN",
        }

        block_number = self._calculate_block_number(block_start)
        if block_number:
            block_cell = self._get_writable_cell(sheet, row=1, column=BT2_COL_TEMPLATE)
            block_cell.value = block_number

        current = block_start
        col = BT2_COL_SCHEDULE_START
        while current <= block_end:
            weekday = current.weekday()
            day_cell = self._get_writable_cell(sheet, row=1, column=col)
            abbrev_cell = self._get_writable_cell(sheet, row=2, column=col)
            date_cell = self._get_writable_cell(sheet, row=3, column=col)

            day_cell.value = day_full.get(weekday, "")
            abbrev_cell.value = day_abbrev.get(weekday, "")
            date_cell.value = datetime(current.year, current.month, current.day)

            current += timedelta(days=1)
            col += 2

    def _fill_header_row(
        self,
        sheet,
        block_start: date,
        block_end: date,
    ) -> None:
        """Fill header row based on format (Block Template2 or ROSETTA)."""
        if self.use_block_template2:
            # Use the template's own layout; only update day/date headers.
            self._fill_block_template2_headers(sheet, block_start, block_end)
            return
        else:
            # ROSETTA format headers
            sheet.cell(row=ROW_HEADERS, column=ROSETTA_COL_NAME).value = "Resident"
            sheet.cell(row=ROW_HEADERS, column=ROSETTA_COL_PGY).value = "PGY"
            sheet.cell(
                row=ROW_HEADERS, column=ROSETTA_COL_ROTATION1
            ).value = "Rotation 1"
            sheet.cell(
                row=ROW_HEADERS, column=ROSETTA_COL_ROTATION2
            ).value = "Rotation 2"
            sheet.cell(row=ROW_HEADERS, column=ROSETTA_COL_NOTES).value = "Notes"
            col_schedule_start = ROSETTA_COL_SCHEDULE_START

            # Schedule column headers (e.g., "Thu Mar 12 AM", "Thu Mar 12 PM")
        current = block_start
        col = col_schedule_start
        while current <= block_end:
            day_str = current.strftime("%a %b %d").replace(" 0", " ")  # "Thu Mar 12"

            am_cell = self._get_writable_cell(sheet, row=ROW_HEADERS, column=col)
            pm_cell = self._get_writable_cell(sheet, row=ROW_HEADERS, column=col + 1)

            am_cell.value = f"{day_str} AM"
            pm_cell.value = f"{day_str} PM"

            # Apply header colors based on day of week
            self._apply_header_color(am_cell, current.weekday())
            self._apply_header_color(pm_cell, current.weekday())

            current += timedelta(days=1)
            col += 2

    def _to_last_first(self, name: str) -> str:
        """Convert 'First Last' to 'Last, First' format."""
        if not name or "," in name:
            return name  # Already in Last, First format or empty
        parts = name.strip().split()
        if len(parts) >= 2:
            return f"{parts[-1]}, {' '.join(parts[:-1])}"
        return name

    def _get_role(self, pgy: str, is_faculty: bool) -> str:
        """Get role string for Block Template2 format."""
        if is_faculty:
            return "FAC"
        if pgy:
            return f"PGY {pgy}"
        return ""

    def _fill_residents(
        self,
        sheet,
        residents: list[dict[str, Any]],
        block_start: date,
        is_faculty: bool,
        stats: dict[str, Any] | None = None,
    ) -> None:
        """Fill resident/faculty rows from schedule dicts.

        If row_mappings loaded from structure XML, uses name → row lookup.
        Otherwise, uses sequential rows starting at row 2 (ROSETTA format).

        Column layout depends on use_block_template2 flag:
        - Block Template2: Rotation1, Rotation2, Template, Role, Name, Schedule...
        - ROSETTA: Name, PGY, Rotation1, Rotation2, Notes, Schedule...
        """
        # Sort by name when no mappings (ROSETTA order)
        sorted_residents = sorted(residents, key=lambda r: r.get("name", ""))

        for i, resident in enumerate(sorted_residents):
            name = resident.get("name", "")
            name = str(name) if name is not None else ""

            # Use row mapping if available, else sequential
            if self.row_mappings:
                # Normalize name for lookup
                normalized = name.replace("*", "").strip()
                lookup_name = normalized

                if lookup_name not in self.row_mappings and "," in lookup_name:
                    last, first = [part.strip() for part in lookup_name.split(",", 1)]
                    swapped = f"{first} {last}".strip()
                    if swapped in self.row_mappings:
                        lookup_name = swapped

                row = self.row_mappings.get(lookup_name)

                # Try fuzzy match by first name (DB uses "First Last")
                if not row:
                    first_name = lookup_name.split()[0] if lookup_name else ""
                    for mapping_name, mapping_row in self.row_mappings.items():
                        # Check if first name matches start of mapping
                        if mapping_name.startswith(first_name):
                            row = mapping_row
                            break

                if not row:
                    if stats is not None:
                        stats["unmapped_names"].append(name)
                    if self.strict_row_mapping:
                        raise ValueError(
                            f"No row mapping for: {name}. "
                            "Update BlockTemplate2_Structure.xml."
                        )
                    logger.warning(f"No row mapping for: {name}")
                    continue
            else:
                row = i + 2  # Start at row 2 (row 1 is headers)

            if stats is not None:
                stats["people_written"] += 1

            pgy = resident.get("pgy", "")
            rotation1 = resident.get("rotation1", "") or ""
            rotation2 = resident.get("rotation2", "") or ""

            if self.use_block_template2:
                # Block Template2 format: Rotation1, Rotation2, Template, Role, Name
                normalized = name.replace("*", "").strip()
                lookup_name = normalized
                if lookup_name not in self.template_mappings and "," in lookup_name:
                    last, first = [part.strip() for part in lookup_name.split(",", 1)]
                    swapped = f"{first} {last}".strip()
                    if swapped in self.template_mappings:
                        lookup_name = swapped

                template_code = self.template_mappings.get(lookup_name, "")
                if not template_code and pgy:
                    template_code = f"R{pgy}"
                elif not template_code and is_faculty:
                    template_code = "C19"

                role = self._get_role(pgy, is_faculty)
                display_name = self._to_last_first(name)

                if not self.preserve_template_identity_fields:
                    rot1_cell = self._get_writable_cell(
                        sheet, row=row, column=BT2_COL_ROTATION1
                    )
                    rot1_cell.value = rotation1
                    self._apply_rotation_color(rot1_cell, rotation1)

                    rot2_cell = self._get_writable_cell(
                        sheet, row=row, column=BT2_COL_ROTATION2
                    )
                    rot2_cell.value = rotation2 or ""
                    if rotation2:
                        self._apply_rotation_color(rot2_cell, rotation2)

                    self._get_writable_cell(
                        sheet, row=row, column=BT2_COL_TEMPLATE
                    ).value = template_code
                    self._get_writable_cell(
                        sheet, row=row, column=BT2_COL_ROLE
                    ).value = role
                    self._get_writable_cell(
                        sheet, row=row, column=BT2_COL_NAME
                    ).value = display_name
            else:
                # ROSETTA format: Name, PGY, Rotation1, Rotation2, Notes
                self._get_writable_cell(
                    sheet, row=row, column=ROSETTA_COL_NAME
                ).value = name
                self._get_writable_cell(
                    sheet, row=row, column=ROSETTA_COL_PGY
                ).value = pgy

                rot1_cell = self._get_writable_cell(
                    sheet, row=row, column=ROSETTA_COL_ROTATION1
                )
                rot1_cell.value = rotation1
                self._apply_rotation_color(rot1_cell, rotation1)

                rot2_cell = self._get_writable_cell(
                    sheet, row=row, column=ROSETTA_COL_ROTATION2
                )
                rot2_cell.value = rotation2 or ""
                if rotation2:
                    self._apply_rotation_color(rot2_cell, rotation2)

                    # Fill schedule columns from day elements
            days = resident.get("days", []) or []
            sorted_days = sorted(days, key=lambda d: str(d.get("date", "")))
            for day in sorted_days:
                day_date = self._coerce_date(day.get("date"))
                if not day_date:
                    continue
                am_code = day.get("am", "") or ""
                pm_code = day.get("pm", "") or ""

                # Calculate column from date
                day_offset = (day_date - block_start).days
                am_col = COL_SCHEDULE_START + (day_offset * 2)
                pm_col = am_col + 1

                am_cell = self._get_writable_cell(sheet, row=row, column=am_col)
                pm_cell = self._get_writable_cell(sheet, row=row, column=pm_col)

                am_cell.value = am_code
                pm_cell.value = pm_code

                if stats is not None and am_code:
                    codes_written = stats["codes_written"]
                    codes_written[am_code] = codes_written.get(am_code, 0) + 1
                if stats is not None and pm_code:
                    codes_written = stats["codes_written"]
                    codes_written[pm_code] = codes_written.get(pm_code, 0) + 1

                # Apply colors based on schedule code
                if am_code:
                    self._apply_cell_color(am_cell, am_code)
                if pm_code:
                    self._apply_cell_color(pm_cell, pm_code)

    def _fill_call_row(
        self,
        sheet,
        call_rows: list[dict[str, Any]],
        block_start: date,
        block_end: date,
    ) -> None:
        """Fill call row with staff names (single cells, user merges manually).

        Writes staff name to AM column only (even columns 6, 8, 10, ...).
        User can manually merge AM/PM cells in Excel if desired.

        Row position comes from self.call_row (default 4, from structure XML).
        """

        # Build date -> staff lookup
        call_lookup: dict[date, str] = {}
        for night in call_rows:
            night_date_val = night.get("date")
            night_date = self._coerce_date(night_date_val)
            if not night_date:
                continue
            staff_name = night.get("staff", "")
            if staff_name:
                call_lookup[night_date] = staff_name

                # Write to call row, AM column only (col 6, 8, 10, ...)
        current = block_start
        col = COL_SCHEDULE_START  # Column 6
        while current <= block_end:
            staff = call_lookup.get(current, "")
            if staff:
                cell = self._get_writable_cell(sheet, row=self.call_row, column=col)
                cell.value = staff
            current += timedelta(days=1)
            col += 2  # Skip PM column (write to AM only)

    def _calculate_block_number(self, block_start: date) -> int:
        """Calculate block number from start date."""
        block_number, _ = get_block_number_for_date(block_start)
        return block_number


def convert_xml_to_xlsx(
    xml_string: str,
    output_path: Path | str | None = None,
    template_path: Path | str | None = None,
    apply_colors: bool = True,
) -> bytes:
    """
    Convenience function to convert XML to xlsx.

    Args:
        xml_string: XML from ScheduleXMLExporter
        output_path: Optional path to save xlsx
        template_path: Optional template xlsx
        apply_colors: Whether to apply TAMC color scheme (default: True)

    Returns:
        xlsx bytes
    """
    converter = XMLToXlsxConverter(template_path, apply_colors=apply_colors)
    return converter.convert_from_string(xml_string, output_path)
