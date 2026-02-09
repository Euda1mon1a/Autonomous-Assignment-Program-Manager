"""Tests for block assignment import schemas (Pydantic validation and field_validator)."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.block_assignment_import import (
    ImportFormat,
    MatchStatus,
    DuplicateAction,
    ExportFormat,
    BlockAssignmentPreviewItem,
    UnknownRotationItem,
    BlockAssignmentPreviewResponse,
    BlockAssignmentImportRequest,
    BlockAssignmentImportResult,
    QuickTemplateCreateRequest,
    QuickTemplateCreateResponse,
    BlockAssignmentExportRequest,
    BlockAssignmentExportResult,
    BlockAssignmentUploadRequest,
)


# ===========================================================================
# Enum Tests
# ===========================================================================


class TestImportFormat:
    def test_values(self):
        assert ImportFormat.CSV.value == "csv"
        assert ImportFormat.XLSX.value == "xlsx"

    def test_count(self):
        assert len(ImportFormat) == 2


class TestMatchStatus:
    def test_values(self):
        assert MatchStatus.MATCHED.value == "matched"
        assert MatchStatus.UNKNOWN_ROTATION.value == "unknown_rotation"
        assert MatchStatus.UNKNOWN_RESIDENT.value == "unknown_resident"
        assert MatchStatus.DUPLICATE.value == "duplicate"
        assert MatchStatus.INVALID.value == "invalid"

    def test_count(self):
        assert len(MatchStatus) == 5


class TestDuplicateAction:
    def test_values(self):
        assert DuplicateAction.SKIP.value == "skip"
        assert DuplicateAction.UPDATE.value == "update"

    def test_count(self):
        assert len(DuplicateAction) == 2


class TestExportFormat:
    def test_values(self):
        assert ExportFormat.CSV.value == "csv"
        assert ExportFormat.XLSX.value == "xlsx"

    def test_count(self):
        assert len(ExportFormat) == 2


# ===========================================================================
# BlockAssignmentPreviewItem Tests
# ===========================================================================


class TestBlockAssignmentPreviewItem:
    def _valid_kwargs(self):
        return {
            "row_number": 1,
            "block_number": 5,
            "rotation_input": "FM Clinic",
            "resident_display": "S*****, J***",
            "match_status": MatchStatus.MATCHED,
        }

    def test_valid_minimal(self):
        r = BlockAssignmentPreviewItem(**self._valid_kwargs())
        assert r.rotation_confidence == 1.0
        assert r.resident_confidence == 1.0
        assert r.matched_rotation_id is None
        assert r.matched_resident_id is None
        assert r.secondary_rotation_input is None
        assert r.secondary_rotation_confidence == 0.0
        assert r.is_duplicate is False
        assert r.existing_assignment_id is None
        assert r.duplicate_action == DuplicateAction.SKIP
        assert r.errors == []
        assert r.warnings == []

    # --- rotation_confidence ge=0.0, le=1.0 ---

    def test_rotation_confidence_boundaries(self):
        kw = self._valid_kwargs()
        kw["rotation_confidence"] = 0.0
        r = BlockAssignmentPreviewItem(**kw)
        assert r.rotation_confidence == 0.0

        kw["rotation_confidence"] = 1.0
        r = BlockAssignmentPreviewItem(**kw)
        assert r.rotation_confidence == 1.0

    def test_rotation_confidence_negative(self):
        kw = self._valid_kwargs()
        kw["rotation_confidence"] = -0.1
        with pytest.raises(ValidationError):
            BlockAssignmentPreviewItem(**kw)

    def test_rotation_confidence_above_one(self):
        kw = self._valid_kwargs()
        kw["rotation_confidence"] = 1.1
        with pytest.raises(ValidationError):
            BlockAssignmentPreviewItem(**kw)

    # --- resident_confidence ge=0.0, le=1.0 ---

    def test_resident_confidence_negative(self):
        kw = self._valid_kwargs()
        kw["resident_confidence"] = -0.1
        with pytest.raises(ValidationError):
            BlockAssignmentPreviewItem(**kw)

    def test_resident_confidence_above_one(self):
        kw = self._valid_kwargs()
        kw["resident_confidence"] = 1.1
        with pytest.raises(ValidationError):
            BlockAssignmentPreviewItem(**kw)

    # --- secondary_rotation_confidence ge=0.0, le=1.0 ---

    def test_secondary_rotation_confidence_negative(self):
        kw = self._valid_kwargs()
        kw["secondary_rotation_confidence"] = -0.1
        with pytest.raises(ValidationError):
            BlockAssignmentPreviewItem(**kw)

    def test_secondary_rotation_confidence_above_one(self):
        kw = self._valid_kwargs()
        kw["secondary_rotation_confidence"] = 1.1
        with pytest.raises(ValidationError):
            BlockAssignmentPreviewItem(**kw)


# ===========================================================================
# UnknownRotationItem Tests
# ===========================================================================


class TestUnknownRotationItem:
    def test_valid(self):
        r = UnknownRotationItem(abbreviation="ICU", occurrences=3)
        assert r.suggested_name is None

    def test_with_suggestion(self):
        r = UnknownRotationItem(
            abbreviation="FM",
            occurrences=10,
            suggested_name="Family Medicine",
        )
        assert r.suggested_name == "Family Medicine"


# ===========================================================================
# BlockAssignmentPreviewResponse Tests
# ===========================================================================


class TestBlockAssignmentPreviewResponse:
    def test_valid(self):
        r = BlockAssignmentPreviewResponse(
            preview_id="prev-1",
            academic_year=2026,
            format_detected=ImportFormat.CSV,
        )
        assert r.items == []
        assert r.total_rows == 0
        assert r.matched_count == 0
        assert r.unknown_rotation_count == 0
        assert r.unknown_resident_count == 0
        assert r.duplicate_count == 0
        assert r.invalid_count == 0
        assert r.unknown_rotations == []
        assert r.warnings == []


# ===========================================================================
# BlockAssignmentImportRequest Tests
# ===========================================================================


class TestBlockAssignmentImportRequest:
    def test_valid(self):
        r = BlockAssignmentImportRequest(preview_id="prev-1", academic_year=2026)
        assert r.skip_duplicates is True
        assert r.update_duplicates is False
        assert r.import_unmatched is False
        assert r.row_overrides == {}


# ===========================================================================
# BlockAssignmentImportResult Tests
# ===========================================================================


class TestBlockAssignmentImportResult:
    def test_valid(self):
        r = BlockAssignmentImportResult(success=True, academic_year=2026)
        assert r.total_rows == 0
        assert r.imported_count == 0
        assert r.updated_count == 0
        assert r.skipped_count == 0
        assert r.failed_count == 0
        assert r.failed_rows == []
        assert r.error_messages == []


# ===========================================================================
# QuickTemplateCreateRequest Tests
# ===========================================================================


class TestQuickTemplateCreateRequest:
    def test_valid(self):
        r = QuickTemplateCreateRequest(abbreviation="FM", name="Family Medicine")
        assert r.rotation_type == "outpatient"
        assert r.leave_eligible is True

    # --- abbreviation min_length=1, max_length=20 ---

    def test_abbreviation_empty(self):
        with pytest.raises(ValidationError):
            QuickTemplateCreateRequest(abbreviation="", name="Test")

    def test_abbreviation_too_long(self):
        with pytest.raises(ValidationError):
            QuickTemplateCreateRequest(abbreviation="x" * 21, name="Test")

    # --- name min_length=1, max_length=100 ---

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            QuickTemplateCreateRequest(abbreviation="FM", name="")

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            QuickTemplateCreateRequest(abbreviation="FM", name="x" * 101)

    # --- field_validator: rotation_type ---

    def test_valid_rotation_types(self):
        for rt in ["inpatient", "outpatient", "education", "off", "conference"]:
            r = QuickTemplateCreateRequest(
                abbreviation="X", name="Test", rotation_type=rt
            )
            assert r.rotation_type == rt

    def test_rotation_type_alias_clinic(self):
        r = QuickTemplateCreateRequest(
            abbreviation="X", name="Test", rotation_type="clinic"
        )
        assert r.rotation_type == "outpatient"

    def test_rotation_type_alias_procedure(self):
        r = QuickTemplateCreateRequest(
            abbreviation="X", name="Test", rotation_type="procedure"
        )
        assert r.rotation_type == "outpatient"

    def test_rotation_type_alias_procedures(self):
        r = QuickTemplateCreateRequest(
            abbreviation="X", name="Test", rotation_type="procedures"
        )
        assert r.rotation_type == "outpatient"

    def test_rotation_type_case_insensitive(self):
        r = QuickTemplateCreateRequest(
            abbreviation="X", name="Test", rotation_type="INPATIENT"
        )
        assert r.rotation_type == "inpatient"

    def test_invalid_rotation_type(self):
        with pytest.raises(ValidationError):
            QuickTemplateCreateRequest(
                abbreviation="X", name="Test", rotation_type="surgical"
            )


# ===========================================================================
# QuickTemplateCreateResponse Tests
# ===========================================================================


class TestQuickTemplateCreateResponse:
    def test_valid(self):
        r = QuickTemplateCreateResponse(
            id=uuid4(),
            abbreviation="FM",
            name="Family Medicine",
            rotation_type="outpatient",
        )
        assert r.abbreviation == "FM"


# ===========================================================================
# BlockAssignmentExportRequest Tests
# ===========================================================================


class TestBlockAssignmentExportRequest:
    def test_defaults(self):
        r = BlockAssignmentExportRequest(academic_year=2026)
        assert r.format == ExportFormat.CSV
        assert r.block_numbers is None
        assert r.rotation_ids is None
        assert r.resident_ids is None
        assert r.include_pgy_level is True
        assert r.include_leave_status is False
        assert r.group_by is None

    def test_group_by_valid(self):
        for gb in ["block", "resident", "rotation"]:
            r = BlockAssignmentExportRequest(academic_year=2026, group_by=gb)
            assert r.group_by == gb

    def test_group_by_invalid(self):
        with pytest.raises(ValidationError):
            BlockAssignmentExportRequest(academic_year=2026, group_by="date")


# ===========================================================================
# BlockAssignmentExportResult Tests
# ===========================================================================


class TestBlockAssignmentExportResult:
    def test_valid(self):
        r = BlockAssignmentExportResult(
            success=True,
            format=ExportFormat.XLSX,
            filename="schedule_2026.xlsx",
            row_count=100,
        )
        assert r.download_url is None
        assert r.data is None


# ===========================================================================
# BlockAssignmentUploadRequest Tests
# ===========================================================================


class TestBlockAssignmentUploadRequest:
    def test_valid(self):
        r = BlockAssignmentUploadRequest(content="block,rotation,resident\n1,FM,Doe")
        assert r.academic_year is None
        assert r.format == ImportFormat.CSV
        assert r.block_number is None
        assert r.rotation_id is None
