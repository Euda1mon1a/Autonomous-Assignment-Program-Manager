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

        template_path = self._template_path()
        structure_path = self._structure_path()

        # When no structure XML exists, dynamic UUID-based mappings are used
        # and identity fields (rotations, template, role, name) must be written
        # by the converter — can't preserve what doesn't exist in the template.
        # Only preserve identity fields when BOTH template AND structure XML exist
        # (i.e., using a hand-jam template with pre-filled names).
        effective_preserve = (
            preserve_template_identity_fields and structure_path is not None
        )

        converter = JSONToXlsxConverter(
            template_path=template_path,
            structure_xml_path=structure_path,
            use_block_template2=True,
            apply_colors=True,
            strict_row_mapping=structure_path is not None,
            include_qa_sheet=include_qa_sheet,
            preserve_template_identity_fields=effective_preserve,
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
        template_path = self._template_path()
        structure_path = self._structure_path()
        effective_preserve = structure_path is not None

        converter = JSONToXlsxConverter(
            template_path=template_path,
            structure_xml_path=structure_path,
            use_block_template2=True,
            apply_colors=True,
            strict_row_mapping=structure_path is not None,
            include_qa_sheet=False,  # Single QA sheet for 14 blocks is messy
            preserve_template_identity_fields=effective_preserve,
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

            # Hide unused faculty rows for cleaner presentation
            # Base template has 50 faculty rows starting at row 31
            active_faculty_count = len(data.get("faculty", []))
            last_populated_row = 30 + active_faculty_count
            for row_idx in range(last_populated_row + 1, 81):
                ws.row_dimensions[row_idx].hidden = True

            block_map[sheet_title] = str(block.id)
            temp_wb.close()

        # Build YTD Summary sheet as the first sheet
        summary_ws = wb.create_sheet(title="YTD_SUMMARY", index=0)
        self._build_ytd_summary_sheet(summary_ws, blocks, data.get("faculty", []))

        # Ensure YTD_SUMMARY is active
        wb.active = summary_ws

        # Phase 1 metadata — single-save (write directly to wb before save)
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
            export_timestamp=datetime.now(UTC).isoformat(),
            block_map=block_map,
        )
        write_sys_meta_sheet(wb, meta)
        write_ref_sheet(wb, rotation_codes, activity_codes)

        # Save to bytes (single save — no double load/save cycle)
        buffer = io.BytesIO()
        wb.save(buffer)
        xlsx_bytes = buffer.getvalue()

        if output_path:
            Path(output_path).write_bytes(xlsx_bytes)

        return xlsx_bytes

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

    def _build_ytd_summary_sheet(
        self, ws, blocks: list[AcademicBlock], faculty: list[dict[str, Any]]
    ) -> None:
        """Build YTD_SUMMARY sheet using dynamic cross-sheet SUMIF formulas."""
        headers = [
            "Faculty Name",
            "YTD Clinic (C+SM)",
            "YTD CC",
            "YTD CV",
            "YTD Total Clinic",
            "YTD AT (AT+PCAT+DO)",
            "YTD Admin",
            "YTD Leave",
            "YTD FMIT Weeks",
            "YTD Call Nights",
        ]

        # Write headers
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = copy(cell.font)  # Will apply bold formatting in real use

        block_names = [f"'Block {b.block_number}'" for b in blocks]

        # Write faculty rows
        for row_idx, f in enumerate(faculty, start=2):
            name = f.get("name", "")
            ws.cell(row=row_idx, column=1, value=name)

            if not name:
                continue

            # Helper to generate cross-sheet SUMIF
            def cross_sheet_sumif(col_letter: str, current_row: int = row_idx) -> str:
                # e.g., SUMIF('Block 0'!$E$31:$E$80, $A2, 'Block 0'!BJ$31:BJ$80) + ...
                terms = [
                    f"SUMIF({b}!$E$31:$E$80, $A{current_row}, {b}!{col_letter}$31:{col_letter}$80)"
                    for b in block_names
                ]
                return f"=({'+'.join(terms)})"

            # B: YTD Clinic (C+SM) -> BJ
            ws.cell(row=row_idx, column=2, value=cross_sheet_sumif("BJ"))
            # C: YTD CC -> BK
            ws.cell(row=row_idx, column=3, value=cross_sheet_sumif("BK"))
            # D: YTD CV -> BL
            ws.cell(row=row_idx, column=4, value=cross_sheet_sumif("BL"))
            # E: YTD Total Clinic -> B+C+D
            ws.cell(row=row_idx, column=5, value=f"=B{row_idx}+C{row_idx}+D{row_idx}")
            # F: YTD AT (AT+PCAT+DO) -> BN
            ws.cell(row=row_idx, column=6, value=cross_sheet_sumif("BN"))
            # G: YTD Admin -> BO
            ws.cell(row=row_idx, column=7, value=cross_sheet_sumif("BO"))
            # H: YTD Leave -> BP
            ws.cell(row=row_idx, column=8, value=cross_sheet_sumif("BP"))
            # I: YTD FMIT Weeks -> BQ / 14
            ws.cell(row=row_idx, column=9, value=f"{cross_sheet_sumif('BQ')}/14")
            # J: YTD Call Nights -> BR
            ws.cell(row=row_idx, column=10, value=cross_sheet_sumif("BR"))

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

    def _template_path(self) -> Path | None:
        template = self._data_dir() / "BlockTemplate2_Official.xlsx"
        if not template.exists():
            logger.warning(
                "Canonical template missing: %s — export will generate BT2 layout "
                "programmatically (no pre-formatted styling).",
                template,
            )
            return None
        return template

    def _structure_path(self) -> Path | None:
        structure = self._data_dir() / "BlockTemplate2_Structure.xml"
        if not structure.exists():
            logger.info(
                "Structure XML not found at %s — using dynamic UUID-based row mappings.",
                structure,
            )
            return None
        return structure
