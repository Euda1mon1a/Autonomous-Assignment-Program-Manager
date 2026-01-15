"""
XML to XLSX Converter.

Converts ScheduleXMLExporter output to Excel format matching ROSETTA ground truth.

This is the final step in the central dogma pipeline:
    DB → ScheduleXMLExporter → XML → XMLToXlsxConverter → xlsx

The XML serves as the validation checkpoint - if XML matches ROSETTA patterns,
the xlsx output will be correct.
"""

from datetime import date, datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from app.core.logging import get_logger
from app.services.tamc_color_scheme import get_color_scheme

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# ROSETTA FORMAT STRUCTURE (validation-focused xlsx)
# This matches the Block10_ROSETTA_CORRECT.xlsx format for validation
# ═══════════════════════════════════════════════════════════════════════════════

# Row Layout (ROSETTA validation format)
ROW_HEADERS = 1  # Column headers

# Column Layout (ROSETTA format)
COL_RESIDENT_NAME = 1  # Resident name ("Last, First")
COL_PGY = 2  # PGY level
COL_ROTATION1 = 3  # First-half rotation
COL_ROTATION2 = 4  # Second-half rotation (if mid-block switch)
COL_NOTES = 5  # Notes
COL_SCHEDULE_START = 6  # First schedule column (AM slot)

# Date-to-column calculation
# Each date uses 2 columns: AM (even col), PM (odd col+1)
# Block 10: Mar 12-Apr 8 = 28 days = 56 columns (6-61)
COLS_PER_DAY = 2
TOTAL_DAYS = 28
COL_SCHEDULE_END = COL_SCHEDULE_START + (TOTAL_DAYS * COLS_PER_DAY) - 1  # 61


class XMLToXlsxConverter:
    """
    Convert ScheduleXMLExporter XML to Excel xlsx format.

    Supports two modes:
    1. ROSETTA format (validation): Row 1 headers, Row 2+ residents
    2. Block Template2 format (production): Uses template row mappings

    When structure_xml_path is provided, uses Block Template2 layout with
    exact row positions for residents/faculty/call.
    """

    def __init__(
        self,
        template_path: Path | str | None = None,
        apply_colors: bool = True,
        structure_xml_path: Path | str | None = None,
    ):
        """
        Initialize converter with optional template.

        Args:
            template_path: Path to Excel template (e.g., Block_Template2.xlsx).
                          If not provided, creates new workbook.
            apply_colors: Whether to apply TAMC color scheme to cells.
            structure_xml_path: Path to BlockTemplate2_Structure.xml for row mappings.
                               If provided, uses name → row lookup instead of sequential.
        """
        self.template_path = Path(template_path) if template_path else None
        self.apply_colors = apply_colors
        self.color_scheme = get_color_scheme() if apply_colors else None

        # Load row mappings from structure XML if provided
        self.row_mappings: dict[str, int] = {}
        self.call_row: int = 4  # Default
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

        # Load resident row mappings (name → row)
        for resident in root.findall(".//resident"):
            name = resident.get("name", "")
            row = resident.get("row", "")
            if name and row:
                # Normalize name (remove asterisks, extra spaces)
                normalized = name.replace("*", "").strip()
                self.row_mappings[normalized] = int(row)

        # Load faculty row mappings
        for person in root.findall(".//faculty/person"):
            name = person.get("name", "")
            row = person.get("row", "")
            if name and row:
                normalized = name.replace("*", "").strip()
                self.row_mappings[normalized] = int(row)

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
        # Parse XML
        root = ElementTree.fromstring(xml_string)
        block_start = date.fromisoformat(root.get("block_start", ""))
        block_end = date.fromisoformat(root.get("block_end", ""))

        logger.info(f"Converting XML to xlsx: {block_start} to {block_end}")

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

        # Fill header row (skip if using template with row mappings)
        if not self.row_mappings:
            self._fill_header_row(sheet, block_start, block_end)

        # Fill residents from XML
        residents = root.findall(".//resident")
        self._fill_residents(sheet, residents, block_start)

        # Fill call row (Row 4) - single cells for user to merge
        call_section = root.find(".//call")
        if call_section is not None:
            self._fill_call_row(sheet, call_section, block_start, block_end)

        # Save to bytes
        buffer = BytesIO()
        wb.save(buffer)
        xlsx_bytes = buffer.getvalue()

        # Save to file if path provided
        if output_path:
            Path(output_path).write_bytes(xlsx_bytes)
            logger.info(f"Saved xlsx to {output_path}")

        return xlsx_bytes

    def _apply_cell_color(self, cell, code: str) -> None:
        """Apply background and font color to cell based on schedule code.

        Font colors have semantic meaning:
        - Red: +1 AT demand (PR, VAS, COLPO, GER) or high-visibility roles
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

    def _fill_header_row(
        self,
        sheet,
        block_start: date,
        block_end: date,
    ) -> None:
        """Fill header row matching ROSETTA format."""
        # Metadata headers
        sheet.cell(row=ROW_HEADERS, column=COL_RESIDENT_NAME).value = "Resident"
        sheet.cell(row=ROW_HEADERS, column=COL_PGY).value = "PGY"
        sheet.cell(row=ROW_HEADERS, column=COL_ROTATION1).value = "Rotation 1"
        sheet.cell(row=ROW_HEADERS, column=COL_ROTATION2).value = "Rotation 2"
        sheet.cell(row=ROW_HEADERS, column=COL_NOTES).value = "Notes"

        # Schedule column headers (e.g., "Thu Mar 12 AM", "Thu Mar 12 PM")
        current = block_start
        col = COL_SCHEDULE_START
        while current <= block_end:
            day_str = current.strftime("%a %b %d").replace(" 0", " ")  # "Thu Mar 12"

            am_cell = sheet.cell(row=ROW_HEADERS, column=col)
            pm_cell = sheet.cell(row=ROW_HEADERS, column=col + 1)

            am_cell.value = f"{day_str} AM"
            pm_cell.value = f"{day_str} PM"

            # Apply header colors based on day of week
            self._apply_header_color(am_cell, current.weekday())
            self._apply_header_color(pm_cell, current.weekday())

            current += timedelta(days=1)
            col += 2

    def _fill_residents(
        self,
        sheet,
        residents: list,
        block_start: date,
    ) -> None:
        """Fill resident rows from XML elements.

        If row_mappings loaded from structure XML, uses name → row lookup.
        Otherwise, uses sequential rows starting at row 2 (ROSETTA format).
        """
        # Sort residents by name to match ROSETTA order (when no mappings)
        sorted_residents = sorted(residents, key=lambda r: r.get("name", ""))

        for i, resident in enumerate(sorted_residents):
            name = resident.get("name", "")

            # Use row mapping if available, else sequential
            if self.row_mappings:
                # Normalize name for lookup (remove asterisks, extra spaces)
                normalized = name.replace("*", "").strip()
                row = self.row_mappings.get(normalized)

                # Try fuzzy match by last name if exact match fails
                if not row:
                    last_name = (
                        normalized.split(",")[0].strip()
                        if "," in normalized
                        else normalized
                    )
                    for mapping_name, mapping_row in self.row_mappings.items():
                        if mapping_name.startswith(last_name + ","):
                            row = mapping_row
                            logger.info(
                                f"Fuzzy matched '{name}' to '{mapping_name}' (row {row})"
                            )
                            break

                if not row:
                    logger.warning(f"No row mapping for resident: {name}")
                    continue
            else:
                row = i + 2  # Start at row 2 (row 1 is headers)

            pgy = resident.get("pgy", "")
            rotation1 = resident.get("rotation1", "")
            rotation2 = resident.get("rotation2", "")

            # Fill metadata columns (skip if using template - already has names)
            if not self.row_mappings:
                sheet.cell(row=row, column=COL_RESIDENT_NAME).value = name
                sheet.cell(row=row, column=COL_PGY).value = pgy

                rot1_cell = sheet.cell(row=row, column=COL_ROTATION1)
                rot1_cell.value = rotation1
                self._apply_rotation_color(rot1_cell, rotation1)

                rot2_cell = sheet.cell(row=row, column=COL_ROTATION2)
                rot2_cell.value = rotation2 or ""
                if rotation2:
                    self._apply_rotation_color(rot2_cell, rotation2)

                sheet.cell(row=row, column=COL_NOTES).value = ""

            # Fill schedule columns from day elements
            for day in resident.findall("day"):
                day_date = date.fromisoformat(day.get("date", ""))
                am_code = day.get("am", "")
                pm_code = day.get("pm", "")

                # Calculate column from date
                day_offset = (day_date - block_start).days
                am_col = COL_SCHEDULE_START + (day_offset * 2)
                pm_col = am_col + 1

                am_cell = sheet.cell(row=row, column=am_col)
                pm_cell = sheet.cell(row=row, column=pm_col)

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
        call_section,
        block_start: date,
        block_end: date,
    ) -> None:
        """Fill call row with staff names (single cells, user merges manually).

        Writes staff name to AM column only (even columns 6, 8, 10, ...).
        User can manually merge AM/PM cells in Excel if desired.

        Row position comes from self.call_row (default 4, from structure XML).
        """

        # Build date -> staff lookup from XML
        call_lookup: dict[date, str] = {}
        for night in call_section.findall("night"):
            night_date_str = night.get("date", "")
            if night_date_str:
                night_date = date.fromisoformat(night_date_str)
                staff_name = night.get("staff", "")
                if staff_name:
                    call_lookup[night_date] = staff_name

        # Write to call row, AM column only (col 6, 8, 10, ...)
        current = block_start
        col = COL_SCHEDULE_START  # Column 6
        while current <= block_end:
            staff = call_lookup.get(current, "")
            if staff:
                cell = sheet.cell(row=self.call_row, column=col)
                cell.value = staff
            current += timedelta(days=1)
            col += 2  # Skip PM column (write to AM only)

    def _calculate_block_number(self, block_start: date) -> int:
        """Calculate block number from start date."""
        # Block 10 starts Mar 12, 2026
        # Simple lookup for now - could calculate from academic year start
        known_blocks = {
            date(2026, 3, 12): 10,
        }
        return known_blocks.get(block_start, 0)


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
