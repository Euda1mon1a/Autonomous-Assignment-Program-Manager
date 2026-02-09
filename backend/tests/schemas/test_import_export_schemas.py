"""Tests for import/export schemas (enums, field_validators, defaults, nested models)."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.import_export import (
    ImportFormat,
    ExportFormat,
    ImportRequest,
    ExportRequest,
    ImportValidationError,
    ImportValidationResult,
    ImportResult,
    ExportResult,
    ImportTemplate,
    ScheduleImportRequest,
    ScheduleExportRequest,
    PersonImportRow,
    AssignmentImportRow,
)


class TestImportFormat:
    def test_values(self):
        assert ImportFormat.CSV == "csv"
        assert ImportFormat.JSON == "json"
        assert ImportFormat.EXCEL == "excel"

    def test_count(self):
        assert len(ImportFormat) == 3


class TestExportFormat:
    def test_values(self):
        assert ExportFormat.CSV == "csv"
        assert ExportFormat.JSON == "json"
        assert ExportFormat.EXCEL == "excel"
        assert ExportFormat.PDF == "pdf"

    def test_count(self):
        assert len(ExportFormat) == 4


class TestImportRequest:
    def test_valid(self):
        r = ImportRequest(
            format=ImportFormat.CSV,
            data="base64data",
            entity_type="person",
        )
        assert r.validate_only is False
        assert r.options is None

    # --- entity_type field_validator ---

    def test_valid_entity_types(self):
        for etype in (
            "person",
            "assignment",
            "block",
            "rotation_template",
            "certification",
        ):
            r = ImportRequest(format=ImportFormat.JSON, data="data", entity_type=etype)
            assert r.entity_type == etype

    def test_invalid_entity_type(self):
        with pytest.raises(ValidationError, match="entity_type must be one of"):
            ImportRequest(format=ImportFormat.CSV, data="data", entity_type="invalid")


class TestExportRequest:
    def test_valid(self):
        r = ExportRequest(format=ExportFormat.PDF, entity_type="person")
        assert r.include_related is False
        assert r.filters is None
        assert r.fields is None

    # --- entity_type field_validator ---

    def test_valid_entity_types(self):
        for etype in (
            "person",
            "assignment",
            "block",
            "rotation_template",
            "certification",
            "swap",
        ):
            r = ExportRequest(format=ExportFormat.CSV, entity_type=etype)
            assert r.entity_type == etype

    def test_invalid_entity_type(self):
        with pytest.raises(ValidationError, match="entity_type must be one of"):
            ExportRequest(format=ExportFormat.CSV, entity_type="unknown")


class TestImportValidationError:
    def test_valid(self):
        r = ImportValidationError(row=1, message="Bad value", severity="error")
        assert r.field is None

    # --- severity field_validator ---

    def test_valid_severities(self):
        for sev in ("error", "warning"):
            r = ImportValidationError(row=1, message="msg", severity=sev)
            assert r.severity == sev

    def test_invalid_severity(self):
        with pytest.raises(
            ValidationError, match="severity must be 'error' or 'warning'"
        ):
            ImportValidationError(row=1, message="msg", severity="info")


class TestImportValidationResult:
    def test_defaults(self):
        r = ImportValidationResult(
            is_valid=True, total_rows=10, valid_rows=10, invalid_rows=0
        )
        assert r.warnings == []
        assert r.errors == []


class TestImportResult:
    def test_defaults(self):
        r = ImportResult(total_rows=50, imported=48, skipped=1, failed=1)
        assert r.errors == []
        assert r.started_at is not None
        assert r.completed_at is not None


class TestExportResult:
    def test_valid(self):
        r = ExportResult(
            format=ExportFormat.EXCEL,
            filename="export.xlsx",
            data="base64data",
            size_bytes=1024,
            row_count=100,
        )
        assert r.generated_at is not None
        assert r.size_bytes == 1024


class TestImportTemplate:
    def test_defaults(self):
        r = ImportTemplate(
            entity_type="person",
            format=ImportFormat.CSV,
            required_fields=["name", "type"],
        )
        assert r.optional_fields == []
        assert r.field_descriptions == {}
        assert r.example_data is None


class TestScheduleImportRequest:
    def test_defaults(self):
        r = ScheduleImportRequest(
            academic_year="2024-2025",
            format=ImportFormat.EXCEL,
            data="data",
        )
        assert r.overwrite_existing is False
        assert r.validate_acgme is True


class TestScheduleExportRequest:
    def test_defaults(self):
        r = ScheduleExportRequest(
            start_date="2026-01-01",
            end_date="2026-03-31",
            format=ExportFormat.CSV,
        )
        assert r.include_person_details is True
        assert r.include_rotation_details is True
        assert r.group_by is None

    # --- group_by field_validator ---

    def test_valid_group_by(self):
        for gb in ("person", "date", "rotation"):
            r = ScheduleExportRequest(
                start_date="2026-01-01",
                end_date="2026-03-31",
                format=ExportFormat.CSV,
                group_by=gb,
            )
            assert r.group_by == gb

    def test_group_by_none(self):
        r = ScheduleExportRequest(
            start_date="2026-01-01",
            end_date="2026-03-31",
            format=ExportFormat.CSV,
            group_by=None,
        )
        assert r.group_by is None

    def test_invalid_group_by(self):
        with pytest.raises(
            ValidationError, match="group_by must be 'person', 'date', or 'rotation'"
        ):
            ScheduleExportRequest(
                start_date="2026-01-01",
                end_date="2026-03-31",
                format=ExportFormat.CSV,
                group_by="block",
            )


class TestPersonImportRow:
    def test_valid(self):
        r = PersonImportRow(name="Dr. Smith", type="resident")
        assert r.email is None
        assert r.pgy_level is None
        assert r.faculty_role is None
        assert r.specialties is None
        assert r.primary_duty is None

    # --- type field_validator ---

    def test_valid_types(self):
        for t in ("resident", "faculty"):
            r = PersonImportRow(name="Dr. Smith", type=t)
            assert r.type == t

    def test_invalid_type(self):
        with pytest.raises(
            ValidationError, match="type must be 'resident' or 'faculty'"
        ):
            PersonImportRow(name="Dr. Smith", type="staff")


class TestAssignmentImportRow:
    def test_valid_defaults(self):
        r = AssignmentImportRow(
            person_name="Dr. Smith",
            date="2026-01-15",
            session="AM",
            rotation_name="FM Clinic",
        )
        assert r.role == "primary"
        assert r.notes is None

    # --- session field_validator (case-insensitive) ---

    def test_session_uppercase(self):
        r = AssignmentImportRow(
            person_name="Dr. Smith",
            date="2026-01-15",
            session="am",
            rotation_name="FM Clinic",
        )
        assert r.session == "AM"

    def test_session_pm(self):
        r = AssignmentImportRow(
            person_name="Dr. Smith",
            date="2026-01-15",
            session="pm",
            rotation_name="FM Clinic",
        )
        assert r.session == "PM"

    def test_invalid_session(self):
        with pytest.raises(ValidationError, match="session must be 'AM' or 'PM'"):
            AssignmentImportRow(
                person_name="Dr. Smith",
                date="2026-01-15",
                session="evening",
                rotation_name="FM Clinic",
            )

    # --- role field_validator ---

    def test_valid_roles(self):
        for role in ("primary", "supervising", "backup"):
            r = AssignmentImportRow(
                person_name="Dr. Smith",
                date="2026-01-15",
                session="AM",
                rotation_name="FM Clinic",
                role=role,
            )
            assert r.role == role

    def test_invalid_role(self):
        with pytest.raises(
            ValidationError,
            match="role must be 'primary', 'supervising', or 'backup'",
        ):
            AssignmentImportRow(
                person_name="Dr. Smith",
                date="2026-01-15",
                session="AM",
                rotation_name="FM Clinic",
                role="observer",
            )
