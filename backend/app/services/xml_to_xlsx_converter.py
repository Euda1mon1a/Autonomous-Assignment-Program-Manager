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

    Generates xlsx matching ROSETTA format for validation:
    - Row 1: Headers
    - Row 2+: Residents with schedule data
    - Cols 1-5: Metadata (Name, PGY, Rotation1, Rotation2, Notes)
    - Cols 6-61: Schedule (28 days × 2 AM/PM slots)
    """

    def __init__(self, template_path: Path | str | None = None):
        """
        Initialize converter with optional template.

        Args:
            template_path: Path to Excel template (e.g., ROSETTA xlsx).
                          If not provided, creates new workbook.
        """
        self.template_path = Path(template_path) if template_path else None

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

        # Create workbook (ROSETTA validation format)
        wb = self._create_new_workbook(block_start, block_end)
        sheet = wb.active

        # Fill header row
        self._fill_header_row(sheet, block_start, block_end)

        # Fill residents from XML (sorted by name to match ROSETTA)
        residents = root.findall(".//resident")
        self._fill_residents(sheet, residents, block_start)

        # Save to bytes
        buffer = BytesIO()
        wb.save(buffer)
        xlsx_bytes = buffer.getvalue()

        # Save to file if path provided
        if output_path:
            Path(output_path).write_bytes(xlsx_bytes)
            logger.info(f"Saved xlsx to {output_path}")

        return xlsx_bytes

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

            sheet.cell(row=ROW_HEADERS, column=col).value = f"{day_str} AM"
            sheet.cell(row=ROW_HEADERS, column=col + 1).value = f"{day_str} PM"

            current += timedelta(days=1)
            col += 2

    def _fill_residents(
        self,
        sheet,
        residents: list,
        block_start: date,
    ) -> None:
        """Fill resident rows from XML elements (sorted by name)."""
        # Sort residents by name to match ROSETTA order
        sorted_residents = sorted(residents, key=lambda r: r.get("name", ""))

        for i, resident in enumerate(sorted_residents):
            row = i + 2  # Start at row 2 (row 1 is headers)

            name = resident.get("name", "")
            pgy = resident.get("pgy", "")
            rotation1 = resident.get("rotation1", "")
            rotation2 = resident.get("rotation2", "")

            # Fill metadata columns
            sheet.cell(row=row, column=COL_RESIDENT_NAME).value = name
            sheet.cell(row=row, column=COL_PGY).value = pgy
            sheet.cell(row=row, column=COL_ROTATION1).value = rotation1
            sheet.cell(row=row, column=COL_ROTATION2).value = rotation2 or ""
            sheet.cell(row=row, column=COL_NOTES).value = ""  # Notes can be added later

            # Fill schedule columns from day elements
            for day in resident.findall("day"):
                day_date = date.fromisoformat(day.get("date", ""))
                am_code = day.get("am", "")
                pm_code = day.get("pm", "")

                # Calculate column from date
                day_offset = (day_date - block_start).days
                am_col = COL_SCHEDULE_START + (day_offset * 2)
                pm_col = am_col + 1

                sheet.cell(row=row, column=am_col).value = am_code
                sheet.cell(row=row, column=pm_col).value = pm_code

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
) -> bytes:
    """
    Convenience function to convert XML to xlsx.

    Args:
        xml_string: XML from ScheduleXMLExporter
        output_path: Optional path to save xlsx
        template_path: Optional template xlsx

    Returns:
        xlsx bytes
    """
    converter = XMLToXlsxConverter(template_path)
    return converter.convert_from_string(xml_string, output_path)
