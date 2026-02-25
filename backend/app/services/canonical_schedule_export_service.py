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

from openpyxl import load_workbook
from sqlalchemy.orm import Session

from app.core.logging import get_logger
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
        xlsx_bytes = converter.convert_from_json(data, output_path)

        # Stamp Phase 1 metadata onto the workbook
        xlsx_bytes = self._stamp_metadata(
            xlsx_bytes, academic_year=academic_year, block_number=block_number
        )
        return xlsx_bytes

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

    def _stamp_metadata(
        self,
        xlsx_bytes: bytes,
        academic_year: int,
        block_number: int,
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
        )
        write_sys_meta_sheet(wb, meta)
        write_ref_sheet(wb, rotation_codes, activity_codes)

        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

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
