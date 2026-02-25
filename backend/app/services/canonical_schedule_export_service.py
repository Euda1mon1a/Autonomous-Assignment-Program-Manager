"""Canonical schedule export service.

Exports schedules from half_day_assignments (descriptive truth) into
Block Template2 XLSX using a fixed, formatted template.

Pipeline:
  half_day_assignments -> HalfDayJSONExporter -> JSONToXlsxConverter -> xlsx
"""

from __future__ import annotations

import io
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from openpyxl import load_workbook, Workbook
from openpyxl.styles import PatternFill, Protection
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.academic_block import AcademicBlock
from app.models.activity import Activity
from app.models.rotation_template import RotationTemplate
from app.services.excel_metadata import (
    ExportMetadata,
    write_ref_sheet,
    write_sys_meta_sheet,
)
from app.services.half_day_json_exporter import HalfDayJSONExporter
from app.services.json_to_xlsx_converter import JSONToXlsxConverter
from app.utils.academic_blocks import get_block_dates

logger = get_logger(__name__)

PHANTOM_FILL = PatternFill(start_color="404040", end_color="404040", fill_type="solid")
LOCKED = Protection(locked=True)


class CanonicalScheduleExportService:
    """Export a block schedule in the official Block Template2 format."""

    def __init__(self, db: Session) -> None:
        self.db = db

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

        converter = JSONToXlsxConverter(
            template_path=self._template_path(),
            structure_xml_path=self._structure_path(),
            use_block_template2=True,
            apply_colors=True,
            strict_row_mapping=True,
            include_qa_sheet=include_qa_sheet,
            preserve_template_identity_fields=preserve_template_identity_fields,
            presentation_profile=presentation_profile,
        )
        xlsx_bytes = converter.convert_from_json(data)

        # Stamp Phase 1 metadata onto the workbook
        return self._inject_metadata(
            xlsx_bytes,
            academic_year=academic_year,
            block_number=block_number,
            output_path=output_path,
        )

    def export_year_xlsx(
        self,
        academic_year: int,
        include_faculty: bool = True,
        include_overrides: bool = True,
        output_path: Path | str | None = None,
    ) -> bytes:
        """Export all 14 blocks for an academic year into a single workbook."""
        wb = Workbook()
        wb.remove(wb.active)  # type: ignore

        stmt = (
            select(AcademicBlock)
            .where(AcademicBlock.academic_year == academic_year)
            .order_by(AcademicBlock.block_number)
        )
        blocks = self.db.execute(stmt).scalars().all()

        if not blocks:
            raise ValueError(f"No academic blocks found for year {academic_year}")

        block_map = {}
        converter = JSONToXlsxConverter(
            template_path=self._template_path(),
            structure_xml_path=self._structure_path(),
            use_block_template2=True,
            apply_colors=True,
            strict_row_mapping=True,
            include_qa_sheet=False,  # Single QA sheet for 14 blocks is messy
            preserve_template_identity_fields=True,
            presentation_profile="tamc_handjam_v2",
        )

        for block in blocks:
            logger.info(f"Exporting Block {block.block_number} for yearly workbook")
            data = self._export_json_data(
                block.start_date,
                block.end_date,
                include_faculty=include_faculty,
                include_overrides=include_overrides,
            )

            # Convert to temporary workbook to extract sheet
            temp_bytes = converter.convert_from_json(data)
            temp_wb = load_workbook(io.BytesIO(temp_bytes))
            temp_ws = temp_wb["Block Template2"]

            # Create sheet in master workbook
            sheet_title = f"Block {block.block_number}"
            ws = wb.create_sheet(title=sheet_title)

            # Copy values and styles
            self._copy_worksheet(temp_ws, ws)

            # Apply phantom columns for stub blocks (0 and 13)
            self._apply_phantom_columns(ws, block)

            block_map[sheet_title] = str(block.id)
            temp_wb.close()

        # Save current workbook to bytes
        buffer = io.BytesIO()
        wb.save(buffer)
        wb_bytes = buffer.getvalue()

        # Inject shared system metadata and reference data using helper
        return self._inject_metadata(
            wb_bytes,
            academic_year=academic_year,
            output_path=output_path,
            block_map=block_map,
        )

    def _copy_worksheet(self, source, target) -> None:
        """Deep copy worksheet content and styles between workbooks."""
        from copy import copy

        for row in source.iter_rows():
            for cell in row:
                new_cell = target.cell(
                    row=cell.row, column=cell.column, value=cell.value
                )
                if cell.has_style:
                    new_cell.font = copy(cell.font)
                    new_cell.border = copy(cell.border)
                    new_cell.fill = copy(cell.fill)
                    new_cell.number_format = copy(cell.number_format)
                    new_cell.protection = copy(cell.protection)
                    new_cell.alignment = copy(cell.alignment)

                if cell.comment:
                    new_cell.comment = copy(cell.comment)

        # Copy column dimensions
        for col, dim in source.column_dimensions.items():
            target.column_dimensions[col] = copy(dim)

        # Copy merged cells
        for merged_range in source.merged_cells.ranges:
            target.merge_cells(str(merged_range))

        # Copy data validation
        for dv in source.data_validations.dataValidation:
            target.add_data_validation(copy(dv))

        # Copy conditional formatting
        for rule_range, rules in source.conditional_formatting._cf_rules.items():
            for rule in rules:
                target.conditional_formatting.add(rule_range, copy(rule))

    def _apply_phantom_columns(self, ws, block: AcademicBlock) -> None:
        """Gray out and lock columns for days that don't exist in stub blocks."""
        # BT2_COL_SCHEDULE_START = 6
        # COLS_PER_DAY = 2
        actual_days = (block.end_date - block.start_date).days + 1
        if actual_days >= 28:
            return

        # Data starts at row 9, ends at 69
        for day_index in range(actual_days, 28):
            for slot in range(2):  # AM, PM
                col = 6 + (day_index * 2) + slot
                for row in range(9, 70):
                    cell = ws.cell(row=row, column=col)
                    cell.fill = PHANTOM_FILL
                    cell.protection = LOCKED
                    cell.value = None

        ws.protection.sheet = True
        ws.protection.password = None  # Visual lock only

    def _export_json_data(
        self,
        start_date: date,
        end_date: date,
        include_faculty: bool,
        include_overrides: bool,
    ) -> dict[str, Any]:
        exporter = HalfDayJSONExporter(self.db)
        return exporter.export(
            block_start=start_date,
            block_end=end_date,
            include_faculty=include_faculty,
            include_call=True,
            include_overrides=include_overrides,
        )

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
