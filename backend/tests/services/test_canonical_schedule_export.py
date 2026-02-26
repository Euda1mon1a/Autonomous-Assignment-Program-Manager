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


def _mock_db_with_codes():
    """Create a mock DB session that returns rotation/activity codes."""
    mock_db = MagicMock()
    rot_query = MagicMock()
    rot_query.distinct.return_value.all.return_value = [("SURG",), ("MED",)]
    act_query = MagicMock()
    act_query.distinct.return_value.all.return_value = [("CLI",), ("LV",)]
    mock_db.query.side_effect = [rot_query, act_query]
    return mock_db


class TestCanonicalScheduleExportService:
    """Tests for CanonicalScheduleExportService."""

    @patch("app.services.canonical_schedule_export_service.get_block_dates")
    @patch("app.services.canonical_schedule_export_service.HalfDayJSONExporter")
    @patch("app.services.canonical_schedule_export_service.JSONToXlsxConverter")
    def test_export_block_xlsx_returns_bytes(
        self, mock_converter_class, mock_exporter_class, mock_get_block_dates
    ):
        """export_block_xlsx() should return bytes."""
        mock_db = _mock_db_with_codes()

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

        with (
            patch.object(
                service, "_template_path", return_value=Path("/fake/template.xlsx")
            ),
            patch.object(
                service, "_structure_path", return_value=Path("/fake/structure.xml")
            ),
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
        mock_db = _mock_db_with_codes()

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
        mock_db = _mock_db_with_codes()

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
        mock_db = _mock_db_with_codes()

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

    @patch("app.services.canonical_schedule_export_service.get_block_dates")
    @patch("app.services.canonical_schedule_export_service.HalfDayJSONExporter")
    @patch("app.services.canonical_schedule_export_service.JSONToXlsxConverter")
    def test_export_passes_metadata_to_converter(
        self, mock_converter_class, mock_exporter_class, mock_get_block_dates
    ):
        """export_block_xlsx() should pass ExportMetadata to converter (single-save)."""
        mock_db = _mock_db_with_codes()

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
            patch("pathlib.Path.exists", return_value=True),
        ):
            result = service.export_block_xlsx(block_number=10, academic_year=2025)

        # Converter should receive metadata kwargs
        call_kwargs = mock_converter.convert_from_json.call_args.kwargs
        assert call_kwargs["export_metadata"] is not None
        assert call_kwargs["export_metadata"].academic_year == 2025
        assert call_kwargs["export_metadata"].block_number == 10
        assert call_kwargs["rotation_codes"] is not None
        assert call_kwargs["activity_codes"] is not None
        assert result == b"raw_xlsx"


class TestTemplatePaths:
    """Tests for template path resolution."""

    def test_data_dir_returns_path(self):
        """_data_dir() should return a Path."""
        mock_db = MagicMock()
        service = CanonicalScheduleExportService(mock_db)

        result = service._data_dir()

        assert isinstance(result, Path)

    def test_template_path_returns_none_if_missing(self):
        """_template_path() should return None if template missing (graceful)."""
        mock_db = MagicMock()
        service = CanonicalScheduleExportService(mock_db)

        with patch.object(service, "_data_dir", return_value=Path("/nonexistent")):
            result = service._template_path()
            assert result is None

    def test_structure_path_returns_none_if_missing(self):
        """_structure_path() should return None if structure missing (graceful)."""
        mock_db = MagicMock()
        service = CanonicalScheduleExportService(mock_db)

        with patch.object(service, "_data_dir", return_value=Path("/nonexistent")):
            result = service._structure_path()
            assert result is None


class TestPhase3DataValidation:
    """Tests that Phase 3 DataValidation survives the single-save pipeline.

    Note: DataValidation requires row_mappings (from the real template) to
    bind DV objects to cell ranges. Without a template, DV objects are created
    but have no cell ranges and are not serialized. This test verifies the
    metadata sheets survive alongside the DV setup code path.
    """

    def test_metadata_survives_single_save_with_dv_code_path(self):
        """__SYS_META__ and __REF__ survive when DV code path is exercised."""
        from openpyxl import load_workbook
        from app.services.excel_metadata import ExportMetadata
        from app.services.xml_to_xlsx_converter import XMLToXlsxConverter

        data = {
            "block_start": "2026-03-12",
            "block_end": "2026-04-08",
            "residents": [
                {
                    "name": "Test Resident",
                    "id": "00000000-0000-0000-0000-000000000001",
                    "pgy": "2",
                    "rotation1": "SURG",
                    "rotation2": "",
                    "block_assignment_id": "00000000-0000-0000-0000-000000000002",
                    "days": [{"am": "C", "pm": "C"}] * 28,
                }
            ],
            "faculty": [],
        }

        meta = ExportMetadata(
            academic_year=2026,
            block_number=10,
            export_timestamp="2026-02-25T10:00:00Z",
        )

        converter = XMLToXlsxConverter(
            use_block_template2=True,
            apply_colors=False,
            strict_row_mapping=False,
        )
        xlsx_bytes = converter.convert_from_data(
            data,
            export_metadata=meta,
            rotation_codes=["SURG", "MED"],
            activity_codes=["C", "NF", "LV"],
        )

        wb = load_workbook(io.BytesIO(xlsx_bytes))

        # Phase 1: metadata sheets survive single-save
        assert "__SYS_META__" in wb.sheetnames
        assert "__REF__" in wb.sheetnames
        assert wb["__SYS_META__"].sheet_state == "veryHidden"
        assert wb["__REF__"].sheet_state == "veryHidden"

        # Verify metadata content
        meta_read = read_sys_meta(wb)
        assert meta_read is not None
        assert meta_read.academic_year == 2026
        assert meta_read.block_number == 10

        # Verify ref codes
        ref = read_ref_codes(wb)
        assert sorted(ref["rotations"]) == ["MED", "SURG"]
        assert sorted(ref["activities"]) == ["C", "LV", "NF"]

        wb.close()


class TestDynamicMappings:
    """Tests for UUID-based dynamic row allocation."""

    def test_dynamic_mappings_assigns_rows_by_pgy(self):
        """Residents get rows by PGY desc; faculty start at row 31."""
        from openpyxl import load_workbook
        from app.services.xml_to_xlsx_converter import XMLToXlsxConverter

        data = {
            "block_start": "2026-05-07",
            "block_end": "2026-06-03",
            "residents": [
                {
                    "name": "Intern Alpha",
                    "id": "aaa-1",
                    "pgy": 1,
                    "rotation1": "FMC",
                    "rotation2": "",
                    "days": [],
                },
                {
                    "name": "Senior Beta",
                    "id": "aaa-3",
                    "pgy": 3,
                    "rotation1": "Hilo",
                    "rotation2": "",
                    "days": [],
                },
                {
                    "name": "Junior Gamma",
                    "id": "aaa-2",
                    "pgy": 2,
                    "rotation1": "SM",
                    "rotation2": "",
                    "days": [],
                },
            ],
            "faculty": [
                {
                    "name": "Dr. Zulu",
                    "id": "bbb-1",
                    "rotation1": "",
                    "rotation2": "",
                    "days": [],
                },
                {
                    "name": "Dr. Alpha",
                    "id": "bbb-2",
                    "rotation1": "",
                    "rotation2": "",
                    "days": [],
                },
            ],
        }

        converter = XMLToXlsxConverter(
            use_block_template2=True,
            apply_colors=False,
            strict_row_mapping=False,
            preserve_template_identity_fields=False,
        )
        xlsx_bytes = converter.convert_from_data(data)
        wb = load_workbook(io.BytesIO(xlsx_bytes))
        sheet = wb["Block Template2"]

        # PGY 3 first (row 9), then PGY 2 (row 10), then PGY 1 (row 11)
        assert sheet.cell(row=9, column=5).value == "Beta, Senior"  # PGY 3
        assert sheet.cell(row=10, column=5).value == "Gamma, Junior"  # PGY 2
        assert sheet.cell(row=11, column=5).value == "Alpha, Intern"  # PGY 1

        # Faculty alphabetical: Dr. Alpha (row 31), Dr. Zulu (row 32)
        assert sheet.cell(row=31, column=5).value == "Alpha, Dr."
        assert sheet.cell(row=32, column=5).value == "Zulu, Dr."

        # Unused rows hidden
        assert sheet.row_dimensions[12].hidden is True  # no 4th resident
        assert sheet.row_dimensions[33].hidden is True  # no 3rd faculty

        wb.close()

    def test_dynamic_mappings_with_fat_template(self):
        """Dynamic mappings work when loading the Fat Template XLSX."""
        from openpyxl import load_workbook
        from app.services.xml_to_xlsx_converter import XMLToXlsxConverter

        template_path = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "BlockTemplate2_Official.xlsx"
        )
        if not template_path.exists():
            pytest.skip("Fat Template not generated yet")

        data = {
            "block_start": "2026-05-07",
            "block_end": "2026-06-03",
            "residents": [
                {
                    "name": "Test Resident",
                    "id": "uuid-r1",
                    "pgy": 2,
                    "rotation1": "SURG",
                    "rotation2": "",
                    "days": [{"date": "2026-05-07", "am": "C", "pm": "NF"}],
                },
            ],
            "faculty": [
                {
                    "name": "Test Faculty",
                    "id": "uuid-f1",
                    "rotation1": "",
                    "rotation2": "",
                    "days": [{"date": "2026-05-07", "am": "C", "pm": "AT"}],
                },
            ],
        }

        converter = XMLToXlsxConverter(
            template_path=template_path,
            use_block_template2=True,
            apply_colors=True,
            strict_row_mapping=False,
            preserve_template_identity_fields=False,
        )
        xlsx_bytes = converter.convert_from_data(data)
        wb = load_workbook(io.BytesIO(xlsx_bytes))
        sheet = wb["Block Template2"]

        # Resident at row 9 (first slot), faculty at row 31
        assert sheet.cell(row=9, column=5).value == "Resident, Test"
        assert sheet.cell(row=31, column=5).value == "Faculty, Test"

        # Schedule data written (col 6=AM day 1, col 7=PM day 1)
        assert sheet.cell(row=9, column=6).value == "C"
        assert sheet.cell(row=9, column=7).value == "NF"
        assert sheet.cell(row=31, column=6).value == "C"
        assert sheet.cell(row=31, column=7).value == "AT"

        wb.close()


class TestPhase1Metadata:
    """Tests for Phase 1 metadata stamping (_inject_metadata).

    Note: _inject_metadata is retained as a utility for year-level export
    but the primary block export now uses single-save via converter kwargs.
    """

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
