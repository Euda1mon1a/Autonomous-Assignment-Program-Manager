"""
JSON to XLSX Converter.

Canonical pipeline:
    DB → HalfDayJSONExporter → JSON → JSONToXlsxConverter → xlsx
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.services.xml_to_xlsx_converter import XMLToXlsxConverter


class JSONToXlsxConverter(XMLToXlsxConverter):
    """Convert JSON schedule data to Excel xlsx format."""

    def convert_from_json(
        self,
        json_input: str | bytes | dict[str, Any],
        output_path: Path | str | None = None,
    ) -> bytes:
        """Convert JSON schedule to xlsx.

        Args:
            json_input: JSON string/bytes or schedule dict
            output_path: Optional path to save xlsx

        Returns:
            xlsx bytes (openpyxl workbook)
        """
        if isinstance(json_input, (bytes, bytearray)):
            json_input = json_input.decode("utf-8")

        if isinstance(json_input, str):
            data = json.loads(json_input)
        else:
            data = json_input

        return self.convert_from_data(data, output_path=output_path)
