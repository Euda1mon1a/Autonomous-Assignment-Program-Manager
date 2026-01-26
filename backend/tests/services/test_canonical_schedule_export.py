"""Tests for canonical_schedule_export_service.py - Export orchestration.

These tests use mocking to avoid JSONB/SQLite compatibility issues.
"""

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.canonical_schedule_export_service import (
    CanonicalScheduleExportService,
)


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

        # Mock template paths
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
            patch("pathlib.Path.exists", return_value=True),
        ):
            mock_conv.return_value.convert_from_json.return_value = b"xlsx"
            service.export_block_xlsx(block_number=10, academic_year=2025)

        mock_get_block_dates.assert_called_once_with(10, 2025)


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
