"""Tests for the export factory and related utilities.

Tests the ExportFactory pattern, format/type validation,
content type resolution, filename generation, and the
ScheduledExportConfig data class.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.export.csv_exporter import CSVExporter
from app.services.export.export_factory import (
    ExportFactory,
    ExportFormat,
    ExportType,
    ScheduledExportConfig,
)
from app.services.export.json_exporter import JSONExporter
from app.services.export.xml_exporter import XMLExporter


class TestExportFormat:
    """Test ExportFormat enum values."""

    def test_csv_value(self):
        assert ExportFormat.CSV.value == "csv"

    def test_json_value(self):
        assert ExportFormat.JSON.value == "json"

    def test_xml_value(self):
        assert ExportFormat.XML.value == "xml"

    def test_from_string(self):
        assert ExportFormat("csv") == ExportFormat.CSV
        assert ExportFormat("json") == ExportFormat.JSON
        assert ExportFormat("xml") == ExportFormat.XML

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            ExportFormat("yaml")


class TestExportType:
    """Test ExportType enum values."""

    def test_all_types(self):
        assert ExportType.ASSIGNMENTS.value == "assignments"
        assert ExportType.SCHEDULE.value == "schedule"
        assert ExportType.PEOPLE.value == "people"
        assert ExportType.BLOCKS.value == "blocks"
        assert ExportType.ANALYTICS.value == "analytics"

    def test_from_string(self):
        assert ExportType("assignments") == ExportType.ASSIGNMENTS
        assert ExportType("schedule") == ExportType.SCHEDULE

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError):
            ExportType("rotations")


class TestExportFactory:
    """Test ExportFactory initialization and exporter selection."""

    def setup_method(self):
        self.mock_db = MagicMock()
        self.factory = ExportFactory(self.mock_db)

    def test_get_csv_exporter(self):
        exporter = self.factory.get_exporter(ExportFormat.CSV)
        assert isinstance(exporter, CSVExporter)

    def test_get_json_exporter(self):
        exporter = self.factory.get_exporter(ExportFormat.JSON)
        assert isinstance(exporter, JSONExporter)

    def test_get_xml_exporter(self):
        exporter = self.factory.get_exporter(ExportFormat.XML)
        assert isinstance(exporter, XMLExporter)

    def test_get_exporter_from_string(self):
        exporter = self.factory.get_exporter("csv")
        assert isinstance(exporter, CSVExporter)

    def test_get_exporter_case_insensitive(self):
        exporter = self.factory.get_exporter("CSV")
        assert isinstance(exporter, CSVExporter)

    def test_get_exporter_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Unsupported export format"):
            self.factory.get_exporter("yaml")

    def test_get_supported_formats(self):
        formats = ExportFactory.get_supported_formats()
        assert "csv" in formats
        assert "json" in formats
        assert "xml" in formats
        assert len(formats) == 3

    def test_get_supported_types(self):
        types = ExportFactory.get_supported_types()
        assert "assignments" in types
        assert "schedule" in types
        assert "people" in types
        assert "blocks" in types
        assert "analytics" in types
        assert len(types) == 5


class TestExportFactoryContentType:
    """Test content type and filename generation."""

    def setup_method(self):
        self.mock_db = MagicMock()
        self.factory = ExportFactory(self.mock_db)

    def test_csv_content_type(self):
        ct = self.factory.get_content_type(ExportFormat.CSV)
        assert ct == "text/csv"

    def test_csv_compressed_content_type(self):
        ct = self.factory.get_content_type(ExportFormat.CSV, compress=True)
        assert ct == "application/gzip"

    def test_json_content_type(self):
        ct = self.factory.get_content_type(ExportFormat.JSON)
        assert ct == "application/json"

    def test_xml_content_type(self):
        ct = self.factory.get_content_type(ExportFormat.XML)
        assert ct == "application/xml"

    def test_filename_csv(self):
        fn = self.factory.get_filename(ExportType.ASSIGNMENTS, ExportFormat.CSV)
        assert fn.startswith("assignments_")
        assert fn.endswith(".csv")

    def test_filename_json_compressed(self):
        fn = self.factory.get_filename(
            ExportType.SCHEDULE, ExportFormat.JSON, compress=True
        )
        assert fn.endswith(".json.gz")

    def test_filename_xml_no_timestamp(self):
        fn = self.factory.get_filename(
            ExportType.PEOPLE, ExportFormat.XML, timestamp=False
        )
        assert fn == "people.xml"

    def test_filename_from_string_type(self):
        fn = self.factory.get_filename("assignments", "csv")
        assert fn.startswith("assignments_")
        assert fn.endswith(".csv")

    def test_filename_invalid_type_raises(self):
        with pytest.raises(ValueError, match="Unsupported export type"):
            self.factory.get_filename("invalid_type", ExportFormat.CSV)


class TestScheduledExportConfig:
    """Test ScheduledExportConfig data class."""

    def test_init(self):
        config = ScheduledExportConfig(
            export_type=ExportType.SCHEDULE,
            format=ExportFormat.CSV,
            destination="/exports/",
            schedule="0 0 * * *",
        )
        assert config.export_type == ExportType.SCHEDULE
        assert config.format == ExportFormat.CSV
        assert config.destination == "/exports/"
        assert config.schedule == "0 0 * * *"
        assert config.compress is True  # default

    def test_custom_compress(self):
        config = ScheduledExportConfig(
            export_type=ExportType.PEOPLE,
            format=ExportFormat.JSON,
            destination="/out/",
            schedule="0 6 * * 1",
            compress=False,
        )
        assert config.compress is False

    def test_to_dict(self):
        config = ScheduledExportConfig(
            export_type=ExportType.ASSIGNMENTS,
            format=ExportFormat.XML,
            destination="/data/",
            schedule="0 0 * * *",
            compress=True,
            start_date="2026-01-01",
        )
        d = config.to_dict()
        assert d["export_type"] == ExportType.ASSIGNMENTS
        assert d["format"] == ExportFormat.XML
        assert d["destination"] == "/data/"
        assert d["schedule"] == "0 0 * * *"
        assert d["compress"] is True
        assert d["export_kwargs"]["start_date"] == "2026-01-01"

    def test_from_dict(self):
        data = {
            "export_type": ExportType.SCHEDULE,
            "format": ExportFormat.CSV,
            "destination": "/exports/",
            "schedule": "0 0 * * *",
            "compress": False,
            "export_kwargs": {"fields": ["name", "date"]},
        }
        config = ScheduledExportConfig.from_dict(data)
        assert config.export_type == ExportType.SCHEDULE
        assert config.format == ExportFormat.CSV
        assert config.compress is False


class TestExportFormatters:
    """Test export formatter utility functions."""

    def test_sanitize_for_export_datetime(self):
        from datetime import datetime, UTC

        from app.services.export.formatters import sanitize_for_export

        dt = datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC)
        result = sanitize_for_export(dt)
        assert "2026-01-15" in result
        assert isinstance(result, str)

    def test_sanitize_for_export_date(self):
        from datetime import date

        from app.services.export.formatters import sanitize_for_export

        d = date(2026, 1, 15)
        result = sanitize_for_export(d)
        assert result == "2026-01-15"

    def test_sanitize_for_export_uuid(self):
        from uuid import uuid4

        from app.services.export.formatters import sanitize_for_export

        u = uuid4()
        result = sanitize_for_export(u)
        assert isinstance(result, str)

    def test_sanitize_for_export_none(self):
        from app.services.export.formatters import sanitize_for_export

        assert sanitize_for_export(None) == ""

    def test_sanitize_for_export_string_passthrough(self):
        from app.services.export.formatters import sanitize_for_export

        assert sanitize_for_export("hello") == "hello"

    def test_sanitize_for_export_int_passthrough(self):
        from app.services.export.formatters import sanitize_for_export

        assert sanitize_for_export(42) == 42

    def test_get_available_fields_assignment(self):
        from app.services.export.formatters import get_available_fields

        fields = get_available_fields("assignment")
        assert "id" in fields
        assert "block_id" in fields
        assert "person_id" in fields
        assert "activity_name" in fields

    def test_get_available_fields_person(self):
        from app.services.export.formatters import get_available_fields

        fields = get_available_fields("person")
        assert "id" in fields
        assert "name" in fields
        assert "type" in fields
        assert "pgy_level" in fields

    def test_get_available_fields_block(self):
        from app.services.export.formatters import get_available_fields

        fields = get_available_fields("block")
        assert "id" in fields
        assert "date" in fields
        assert "time_of_day" in fields

    def test_get_available_fields_schedule(self):
        from app.services.export.formatters import get_available_fields

        fields = get_available_fields("schedule")
        assert "assignment_id" in fields
        assert "person_name" in fields
        assert "date" in fields

    def test_get_available_fields_unknown_returns_empty(self):
        from app.services.export.formatters import get_available_fields

        fields = get_available_fields("unknown")
        assert fields == []

    def test_format_datetime_none(self):
        from app.services.export.formatters import format_datetime

        assert format_datetime(None) is None

    def test_format_datetime_value(self):
        from datetime import datetime, UTC

        from app.services.export.formatters import format_datetime

        dt = datetime(2026, 6, 15, 12, 0, 0, tzinfo=UTC)
        result = format_datetime(dt)
        assert "2026-06-15" in result

    def test_format_date_none(self):
        from app.services.export.formatters import format_date

        assert format_date(None) is None

    def test_format_date_value(self):
        from datetime import date

        from app.services.export.formatters import format_date

        d = date(2026, 6, 15)
        assert format_date(d) == "2026-06-15"

    def test_format_uuid_none(self):
        from app.services.export.formatters import format_uuid

        assert format_uuid(None) is None

    def test_format_uuid_value(self):
        from uuid import UUID

        from app.services.export.formatters import format_uuid

        u = UUID("12345678-1234-5678-1234-567812345678")
        assert format_uuid(u) == "12345678-1234-5678-1234-567812345678"
