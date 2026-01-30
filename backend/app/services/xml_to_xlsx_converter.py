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

from datetime import date, datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from openpyxl import Workbook, load_workbook
from openpyxl.cell.cell import MergedCell
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
        """
        self.template_path = Path(template_path) if template_path else None
        self.apply_colors = apply_colors
        self.color_scheme = get_color_scheme() if apply_colors else None
        self.use_block_template2 = use_block_template2
        self.strict_row_mapping = strict_row_mapping

        # Load row mappings from structure XML if provided
        self.row_mappings: dict[str, int] = {}
        self.pgy_mappings: dict[str, int] = {}  # name → pgy level
        self.template_mappings: dict[str, str] = {}  # name → template code
        self.call_row: int = BT2_ROW_STAFF_CALL
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

        # Fill residents and faculty
        residents = data.get("residents", [])
        faculty = data.get("faculty", [])
        self._fill_residents(sheet, residents, block_start, is_faculty=False)
        self._fill_residents(sheet, faculty, block_start, is_faculty=True)

        # Fill call row (Row 4) - single cells for user to merge
        call_section = data.get("call", {})
        call_rows: list[dict[str, Any]] = []
        if isinstance(call_section, dict):
            call_rows = call_section.get("nights", []) or []
        elif isinstance(call_section, list):
            call_rows = call_section
        if call_rows:
            self._fill_call_row(sheet, call_rows, block_start, block_end)

            # Save to bytes
        buffer = BytesIO()
        wb.save(buffer)
        xlsx_bytes = buffer.getvalue()

        # Save to file if path provided
        if output_path:
            Path(output_path).write_bytes(xlsx_bytes)
            logger.info(f"Saved xlsx to {output_path}")

        return xlsx_bytes

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

    def _get_writable_cell(self, sheet, row: int, column: int):
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
                    if self.strict_row_mapping:
                        raise ValueError(
                            f"No row mapping for: {name}. "
                            "Update BlockTemplate2_Structure.xml."
                        )
                    logger.warning(f"No row mapping for: {name}")
                    continue
            else:
                row = i + 2  # Start at row 2 (row 1 is headers)

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
