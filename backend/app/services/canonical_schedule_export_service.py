"""Canonical schedule export service.

Exports schedules from half_day_assignments (descriptive truth) into
Block Template2 XLSX using a fixed, formatted template.

Pipeline:
  half_day_assignments -> HalfDayJSONExporter -> JSONToXlsxConverter -> xlsx
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any
from sqlalchemy.orm import Session

from app.core.logging import get_logger
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
        )
        return converter.convert_from_json(data, output_path)

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
