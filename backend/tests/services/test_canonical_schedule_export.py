"""Tests for canonical_schedule_export_service.py - Export orchestration.

These tests use mocking to avoid JSONB/SQLite compatibility issues.
"""

import io
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from openpyxl import Workbook

from app.services.canonical_schedule_export_service import (
    CanonicalScheduleExportService,
)
from app.services.excel_metadata import read_ref_codes, read_sys_meta


class TestCanonicalScheduleExportService:
    """Tests for CanonicalScheduleExportService."""

    @patch("app.services.canonical_schedule_export_service.get_block_dates")
    @patch("app.services.canonical_schedule_export_service.HalfDayJSONExporter")
    @patch("app.services.canonical_schedule_export_service.JSONToXlsxConverter")
    def test_export_block_xlsx_returns_bytes(
        self, mock_converter_class, mock_exporter_class, mock_get_block_dates
    ):
        """export_block_xlsx() should return bytes."""
        mock_db = MagicMock()

        # Mock block dates
        mock_block_dates = MagicMock()
        mock_block_dates.start_date = date(2026, 3, 12)
        mock_block_dates.end_date = date(2026, 4, 8)
        mock_get_block_dates.return_value = mock_block_dates

        # Mock exporter
        mock_exporter = MagicMock()
        mock_exporter.export.return_value = {"residents": [], "faculty": []}
        mock_exporter_class.return_value = mock_exporter

        # Mock converter
        mock_converter = MagicMock()
        mock_converter.convert_from_json.return_value = b"xlsx_content"
        mock_converter_class.return_value = mock_converter

        service = CanonicalScheduleExportService(mock_db)

        # Mock template paths + stamp_metadata (avoids loading fake bytes as xlsx)
        with (
            patch.object(
                service, "_template_path", return_value=Path("/fake/template.xlsx")
            ),
            patch.object(
                service, "_structure_path", return_value=Path("/fake/structure.xml")
            ),
            patch.object(service, "_inject_metadata", return_value=b"xlsx_with_meta"),
            patch("pathlib.Path.exists", return_value=True),
        ):
            result = service.export_block_xlsx(block_number=10, academic_year=2025)

        assert isinstance(result, bytes)
        mock_converter_class.assert_called_once()
        assert (
            mock_converter_class.call_args.kwargs.get("include_qa_sheet", True) is True
        )
        assert (
            mock_converter_class.call_args.kwargs.get(
                "preserve_template_identity_fields", True
            )
            is True
        )
        assert (
            mock_converter_class.call_args.kwargs.get("presentation_profile")
            == "tamc_handjam_v2"
        )

    @patch("app.services.canonical_schedule_export_service.get_block_dates")
    def test_export_uses_block_dates(self, mock_get_block_dates):
        """export_block_xlsx() should use correct block dates."""
        mock_db = MagicMock()

        mock_block_dates = MagicMock()
        mock_block_dates.start_date = date(2026, 3, 12)
        mock_block_dates.end_date = date(2026, 4, 8)
        mock_get_block_dates.return_value = mock_block_dates

        service = CanonicalScheduleExportService(mock_db)

        with (
            patch.object(service, "_export_json_data", return_value={}),
            patch(
                "app.services.canonical_schedule_export_service.JSONToXlsxConverter"
            ) as mock_conv,
            patch.object(
                service, "_template_path", return_value=Path("/fake/template.xlsx")
            ),
            patch.object(
                service, "_structure_path", return_value=Path("/fake/structure.xml")
            ),
            patch.object(service, "_inject_metadata", return_value=b"xlsx_with_meta"),
            patch("pathlib.Path.exists", return_value=True),
        ):
            mock_conv.return_value.convert_from_json.return_value = b"xlsx"
            service.export_block_xlsx(block_number=10, academic_year=2025)

        mock_get_block_dates.assert_called_once_with(10, 2025)

    @patch("app.services.canonical_schedule_export_service.get_block_dates")
    @patch("app.services.canonical_schedule_export_service.HalfDayJSONExporter")
    @patch("app.services.canonical_schedule_export_service.JSONToXlsxConverter")
    def test_export_can_disable_qa_sheet(
        self, mock_converter_class, mock_exporter_class, mock_get_block_dates
    ):
        """export_block_xlsx() should pass include_qa_sheet through to converter."""
        mock_db = MagicMock()

        mock_block_dates = MagicMock()
        mock_block_dates.start_date = date(2026, 3, 12)
        mock_block_dates.end_date = date(2026, 4, 8)
        mock_get_block_dates.return_value = mock_block_dates

        mock_exporter = MagicMock()
        mock_exporter.export.return_value = {"residents": [], "faculty": []}
        mock_exporter_class.return_value = mock_exporter

        mock_converter = MagicMock()
        mock_converter.convert_from_json.return_value = b"xlsx_content"
        mock_converter_class.return_value = mock_converter

        service = CanonicalScheduleExportService(mock_db)
        with (
            patch.object(
                service, "_template_path", return_value=Path("/fake/template.xlsx")
            ),
            patch.object(
                service, "_structure_path", return_value=Path("/fake/structure.xml")
            ),
            patch.object(service, "_inject_metadata", return_value=b"xlsx_with_meta"),
            patch("pathlib.Path.exists", return_value=True),
        ):
            service.export_block_xlsx(
                block_number=10,
                academic_year=2025,
                include_qa_sheet=False,
            )

        assert mock_converter_class.call_args.kwargs["include_qa_sheet"] is False

    @patch("app.services.canonical_schedule_export_service.get_block_dates")
    @patch("app.services.canonical_schedule_export_service.HalfDayJSONExporter")
    @patch("app.services.canonical_schedule_export_service.JSONToXlsxConverter")
    def test_export_can_override_identity_and_profile(
        self, mock_converter_class, mock_exporter_class, mock_get_block_dates
    ):
        """export_block_xlsx() should pass identity/profile options through."""
        mock_db = MagicMock()

        mock_block_dates = MagicMock()
        mock_block_dates.start_date = date(2026, 3, 12)
        mock_block_dates.end_date = date(2026, 4, 8)
        mock_get_block_dates.return_value = mock_block_dates

        mock_exporter = MagicMock()
        mock_exporter.export.return_value = {"residents": [], "faculty": []}
        mock_exporter_class.return_value = mock_exporter

        mock_converter = MagicMock()
        mock_converter.convert_from_json.return_value = b"xlsx_content"
        mock_converter_class.return_value = mock_converter

        service = CanonicalScheduleExportService(mock_db)
        with (
            patch.object(
                service, "_template_path", return_value=Path("/fake/template.xlsx")
            ),
            patch.object(
                service, "_structure_path", return_value=Path("/fake/structure.xml")
            ),
            patch.object(service, "_inject_metadata", return_value=b"xlsx_with_meta"),
            patch("pathlib.Path.exists", return_value=True),
        ):
            service.export_block_xlsx(
                block_number=10,
                academic_year=2025,
                preserve_template_identity_fields=False,
                presentation_profile="none",
            )

        kwargs = mock_converter_class.call_args.kwargs
        assert kwargs["preserve_template_identity_fields"] is False
        assert kwargs["presentation_profile"] == "none"


class TestTemplatePaths:
    """Tests for template path resolution."""

    def test_data_dir_returns_path(self):
        """_data_dir() should return a Path."""
        mock_db = MagicMock()
        service = CanonicalScheduleExportService(mock_db)

        result = service._data_dir()

        assert isinstance(result, Path)

    def test_template_path_raises_if_missing(self):
        """_template_path() should raise FileNotFoundError if template missing."""
        mock_db = MagicMock()
        service = CanonicalScheduleExportService(mock_db)

        with patch.object(service, "_data_dir", return_value=Path("/nonexistent")):
            with pytest.raises(FileNotFoundError):
                service._template_path()

    def test_structure_path_raises_if_missing(self):
        """_structure_path() should raise FileNotFoundError if structure missing."""
        mock_db = MagicMock()
        service = CanonicalScheduleExportService(mock_db)

        with patch.object(service, "_data_dir", return_value=Path("/nonexistent")):
            with pytest.raises(FileNotFoundError):
                service._structure_path()


class TestPhase1Metadata:
    """Tests for Phase 1 metadata stamping (_inject_metadata)."""

    def _make_blank_xlsx(self) -> bytes:
        """Create a minimal valid XLSX for _inject_metadata to load."""
        wb = Workbook()
        ws = wb.active
        ws.title = "Schedule"
        ws.cell(row=1, column=1, value="test")
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    def test_inject_metadata_adds_sys_meta(self):
        """_inject_metadata() should add __SYS_META__ sheet."""
        mock_db = MagicMock()
        mock_db.query.return_value.distinct.return_value.all.return_value = []

        service = CanonicalScheduleExportService(mock_db)
        xlsx_bytes = self._make_blank_xlsx()

        result = service._inject_metadata(
            xlsx_bytes, academic_year=2026, block_number=10
        )

        from openpyxl import load_workbook

        wb = load_workbook(io.BytesIO(result))
        assert "__SYS_META__" in wb.sheetnames

        meta = read_sys_meta(wb)
        assert meta is not None
        assert meta.academic_year == 2026
        assert meta.block_number == 10
        assert meta.export_version == 1
        wb.close()

    def test_inject_metadata_adds_ref_sheet(self):
        """_inject_metadata() should add __REF__ sheet with rotation/activity codes."""
        mock_db = MagicMock()

        # First call returns rotation codes, second returns activity codes
        rot_query = MagicMock()
        rot_query.distinct.return_value.all.return_value = [
            ("SURG",),
            ("MED",),
            ("PEDS",),
        ]
        act_query = MagicMock()
        act_query.distinct.return_value.all.return_value = [("CLI",), ("OR",), ("LV",)]
        mock_db.query.side_effect = [rot_query, act_query]

        service = CanonicalScheduleExportService(mock_db)
        xlsx_bytes = self._make_blank_xlsx()

        result = service._inject_metadata(
            xlsx_bytes, academic_year=2026, block_number=10
        )

        from openpyxl import load_workbook

        wb = load_workbook(io.BytesIO(result))
        assert "__REF__" in wb.sheetnames

        ref = read_ref_codes(wb)
        assert sorted(ref["rotations"]) == ["MED", "PEDS", "SURG"]
        assert sorted(ref["activities"]) == ["CLI", "LV", "OR"]
        wb.close()

    def test_inject_metadata_sys_meta_is_veryhidden(self):
        """Metadata sheets should be veryHidden."""
        mock_db = MagicMock()
        mock_db.query.return_value.distinct.return_value.all.return_value = []

        service = CanonicalScheduleExportService(mock_db)
        xlsx_bytes = self._make_blank_xlsx()

        result = service._inject_metadata(
            xlsx_bytes, academic_year=2026, block_number=5
        )

        from openpyxl import load_workbook

        wb = load_workbook(io.BytesIO(result))
        assert wb["__SYS_META__"].sheet_state == "veryHidden"
        assert wb["__REF__"].sheet_state == "veryHidden"
        wb.close()

    @patch("app.services.canonical_schedule_export_service.get_block_dates")
    @patch("app.services.canonical_schedule_export_service.HalfDayJSONExporter")
    @patch("app.services.canonical_schedule_export_service.JSONToXlsxConverter")
    def test_export_calls_inject_metadata(
        self, mock_converter_class, mock_exporter_class, mock_get_block_dates
    ):
        """export_block_xlsx() should call _inject_metadata with correct args."""
        mock_db = MagicMock()

        mock_block_dates = MagicMock()
        mock_block_dates.start_date = date(2026, 3, 12)
        mock_block_dates.end_date = date(2026, 4, 8)
        mock_get_block_dates.return_value = mock_block_dates

        mock_exporter = MagicMock()
        mock_exporter.export.return_value = {"residents": []}
        mock_exporter_class.return_value = mock_exporter

        mock_converter = MagicMock()
        mock_converter.convert_from_json.return_value = b"raw_xlsx"
        mock_converter_class.return_value = mock_converter

        service = CanonicalScheduleExportService(mock_db)
        with (
            patch.object(
                service, "_template_path", return_value=Path("/fake/template.xlsx")
            ),
            patch.object(
                service, "_structure_path", return_value=Path("/fake/structure.xml")
            ),
            patch.object(
                service, "_inject_metadata", return_value=b"stamped"
            ) as mock_stamp,
            patch("pathlib.Path.exists", return_value=True),
        ):
            result = service.export_block_xlsx(block_number=10, academic_year=2025)

        mock_stamp.assert_called_once_with(
            b"raw_xlsx", academic_year=2025, block_number=10, output_path=None
        )
        assert result == b"stamped"
