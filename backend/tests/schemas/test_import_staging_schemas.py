"""Tests for import staging schemas (Field bounds, field_validators, enums, defaults)."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.import_staging import (
    ImportBatchStatus,
    ConflictResolutionMode,
    StagedAssignmentStatus,
    ImportBatchCreate,
    ImportBatchCounts,
    ImportBatchResponse,
    ImportBatchListItem,
    ImportBatchList,
    StagedAssignmentResponse,
    StagedAssignmentUpdate,
    StagedAssignmentBulkUpdate,
    ImportConflictDetail,
    ImportPreviewResponse,
    ImportApplyRequest,
    ImportApplyError,
    ImportApplyResponse,
    ImportRollbackRequest,
    ImportRollbackResponse,
)


# ── Enums ──────────────────────────────────────────────────────────────


class TestImportBatchStatus:
    def test_values(self):
        assert ImportBatchStatus.STAGED == "staged"
        assert ImportBatchStatus.APPROVED == "approved"
        assert ImportBatchStatus.REJECTED == "rejected"
        assert ImportBatchStatus.APPLIED == "applied"
        assert ImportBatchStatus.ROLLED_BACK == "rolled_back"
        assert ImportBatchStatus.FAILED == "failed"

    def test_count(self):
        assert len(ImportBatchStatus) == 6


class TestConflictResolutionMode:
    def test_values(self):
        assert ConflictResolutionMode.REPLACE == "replace"
        assert ConflictResolutionMode.MERGE == "merge"
        assert ConflictResolutionMode.UPSERT == "upsert"

    def test_count(self):
        assert len(ConflictResolutionMode) == 3


class TestStagedAssignmentStatus:
    def test_values(self):
        assert StagedAssignmentStatus.PENDING == "pending"
        assert StagedAssignmentStatus.APPROVED == "approved"
        assert StagedAssignmentStatus.SKIPPED == "skipped"
        assert StagedAssignmentStatus.APPLIED == "applied"
        assert StagedAssignmentStatus.FAILED == "failed"

    def test_count(self):
        assert len(StagedAssignmentStatus) == 5


# ── ImportBatchCreate ──────────────────────────────────────────────────


class TestImportBatchCreate:
    def test_defaults(self):
        r = ImportBatchCreate()
        assert r.filename is None
        assert r.target_block is None
        assert r.target_start_date is None
        assert r.target_end_date is None
        assert r.notes is None
        assert r.conflict_resolution == ConflictResolutionMode.UPSERT

    # --- filename max_length=255 ---

    def test_filename_too_long(self):
        with pytest.raises(ValidationError):
            ImportBatchCreate(filename="x" * 256)

    # --- target_block ge=1, le=26 ---

    def test_target_block_below_min(self):
        with pytest.raises(ValidationError):
            ImportBatchCreate(target_block=0)

    def test_target_block_above_max(self):
        with pytest.raises(ValidationError):
            ImportBatchCreate(target_block=27)

    def test_target_block_valid(self):
        r = ImportBatchCreate(target_block=13)
        assert r.target_block == 13

    # --- notes max_length=2000 ---

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            ImportBatchCreate(notes="x" * 2001)

    # --- target_end_date validator (>= start_date) ---

    def test_valid_date_range(self):
        r = ImportBatchCreate(
            target_start_date=date(2026, 1, 1),
            target_end_date=date(2026, 1, 31),
        )
        assert r.target_end_date == date(2026, 1, 31)

    def test_same_dates_ok(self):
        r = ImportBatchCreate(
            target_start_date=date(2026, 1, 1),
            target_end_date=date(2026, 1, 1),
        )
        assert r.target_end_date == date(2026, 1, 1)

    def test_end_before_start(self):
        with pytest.raises(ValidationError, match="target_end_date must be"):
            ImportBatchCreate(
                target_start_date=date(2026, 2, 1),
                target_end_date=date(2026, 1, 1),
            )

    def test_end_date_none_ok(self):
        r = ImportBatchCreate(target_start_date=date(2026, 1, 1), target_end_date=None)
        assert r.target_end_date is None


# ── ImportBatchCounts ──────────────────────────────────────────────────


class TestImportBatchCounts:
    def test_defaults(self):
        r = ImportBatchCounts()
        assert r.total == 0
        assert r.pending == 0
        assert r.approved == 0
        assert r.skipped == 0
        assert r.applied == 0
        assert r.failed == 0


# ── ImportBatchResponse ────────────────────────────────────────────────


class TestImportBatchResponse:
    def test_defaults(self):
        r = ImportBatchResponse(
            id=uuid4(),
            created_at=datetime(2026, 1, 15),
            status=ImportBatchStatus.STAGED,
            conflict_resolution=ConflictResolutionMode.UPSERT,
        )
        assert r.created_by_id is None
        assert r.filename is None
        assert r.file_hash is None
        assert r.file_size_bytes is None
        assert r.target_block is None
        assert r.notes is None
        assert r.row_count is None
        assert r.error_count == 0
        assert r.warning_count == 0
        assert r.applied_at is None
        assert r.applied_by_id is None
        assert r.rollback_available is True
        assert r.rollback_expires_at is None
        assert r.rolled_back_at is None
        assert r.rolled_back_by_id is None
        assert r.counts.total == 0


# ── ImportBatchList ────────────────────────────────────────────────────


class TestImportBatchList:
    def test_defaults(self):
        r = ImportBatchList(items=[], total=0, has_next=False, has_previous=False)
        assert r.page == 1
        assert r.page_size == 50

    # --- page ge=1 ---

    def test_page_below_min(self):
        with pytest.raises(ValidationError):
            ImportBatchList(
                items=[], total=0, page=0, has_next=False, has_previous=False
            )

    # --- page_size ge=1, le=100 ---

    def test_page_size_below_min(self):
        with pytest.raises(ValidationError):
            ImportBatchList(
                items=[],
                total=0,
                page_size=0,
                has_next=False,
                has_previous=False,
            )

    def test_page_size_above_max(self):
        with pytest.raises(ValidationError):
            ImportBatchList(
                items=[],
                total=0,
                page_size=101,
                has_next=False,
                has_previous=False,
            )


# ── StagedAssignmentResponse ──────────────────────────────────────────


class TestStagedAssignmentResponse:
    def _make_valid(self, **kwargs):
        defaults = {
            "id": uuid4(),
            "batch_id": uuid4(),
            "person_name": "Dr. Smith",
            "assignment_date": date(2026, 1, 15),
            "status": StagedAssignmentStatus.PENDING,
        }
        defaults.update(kwargs)
        return StagedAssignmentResponse(**defaults)

    def test_defaults(self):
        r = self._make_valid()
        assert r.row_number is None
        assert r.sheet_name is None
        assert r.slot is None
        assert r.rotation_name is None
        assert r.raw_cell_value is None
        assert r.matched_person_id is None
        assert r.matched_person_name is None
        assert r.person_match_confidence is None
        assert r.matched_rotation_id is None
        assert r.matched_rotation_name is None
        assert r.rotation_match_confidence is None
        assert r.conflict_type is None
        assert r.existing_assignment_id is None
        assert r.validation_errors is None
        assert r.validation_warnings is None
        assert r.created_assignment_id is None

    # --- person_match_confidence ge=0, le=100 ---

    def test_match_confidence_below_min(self):
        with pytest.raises(ValidationError):
            self._make_valid(person_match_confidence=-1)

    def test_match_confidence_above_max(self):
        with pytest.raises(ValidationError):
            self._make_valid(person_match_confidence=101)

    # --- rotation_match_confidence ge=0, le=100 ---

    def test_rotation_confidence_below_min(self):
        with pytest.raises(ValidationError):
            self._make_valid(rotation_match_confidence=-1)

    def test_rotation_confidence_above_max(self):
        with pytest.raises(ValidationError):
            self._make_valid(rotation_match_confidence=101)

    # --- conflict_type validator (none/duplicate/overwrite) ---

    def test_conflict_type_valid(self):
        for ct in ("none", "duplicate", "overwrite"):
            r = self._make_valid(conflict_type=ct)
            assert r.conflict_type == ct

    def test_conflict_type_invalid(self):
        with pytest.raises(ValidationError, match="conflict_type must be"):
            self._make_valid(conflict_type="merge")

    def test_conflict_type_none_ok(self):
        r = self._make_valid(conflict_type=None)
        assert r.conflict_type is None


# ── StagedAssignmentUpdate ─────────────────────────────────────────────


class TestStagedAssignmentUpdate:
    def test_approved(self):
        r = StagedAssignmentUpdate(status=StagedAssignmentStatus.APPROVED)
        assert r.status == StagedAssignmentStatus.APPROVED

    def test_skipped(self):
        r = StagedAssignmentUpdate(status=StagedAssignmentStatus.SKIPPED)
        assert r.status == StagedAssignmentStatus.SKIPPED

    def test_invalid_status(self):
        with pytest.raises(ValidationError, match="approved.*skipped"):
            StagedAssignmentUpdate(status=StagedAssignmentStatus.PENDING)

    def test_applied_not_allowed(self):
        with pytest.raises(ValidationError):
            StagedAssignmentUpdate(status=StagedAssignmentStatus.APPLIED)


# ── StagedAssignmentBulkUpdate ─────────────────────────────────────────


class TestStagedAssignmentBulkUpdate:
    def test_valid(self):
        r = StagedAssignmentBulkUpdate(
            ids=[uuid4()], status=StagedAssignmentStatus.APPROVED
        )
        assert len(r.ids) == 1

    # --- ids min_length=1, max_length=1000 ---

    def test_ids_empty(self):
        with pytest.raises(ValidationError):
            StagedAssignmentBulkUpdate(ids=[], status=StagedAssignmentStatus.APPROVED)

    def test_ids_too_many(self):
        with pytest.raises(ValidationError):
            StagedAssignmentBulkUpdate(
                ids=[uuid4() for _ in range(1001)],
                status=StagedAssignmentStatus.APPROVED,
            )

    # --- status validator (only approved or skipped) ---

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            StagedAssignmentBulkUpdate(
                ids=[uuid4()], status=StagedAssignmentStatus.FAILED
            )


# ── ImportPreviewResponse ──────────────────────────────────────────────


class TestImportPreviewResponse:
    def test_defaults(self):
        r = ImportPreviewResponse(batch_id=uuid4())
        assert r.new_count == 0
        assert r.update_count == 0
        assert r.conflict_count == 0
        assert r.skip_count == 0
        assert r.acgme_violations == []
        assert r.staged_assignments == []
        assert r.conflicts == []
        assert r.total_staged == 0
        assert r.page == 1
        assert r.page_size == 50

    # --- page ge=1 ---

    def test_page_below_min(self):
        with pytest.raises(ValidationError):
            ImportPreviewResponse(batch_id=uuid4(), page=0)

    # --- page_size ge=1, le=100 ---

    def test_page_size_below_min(self):
        with pytest.raises(ValidationError):
            ImportPreviewResponse(batch_id=uuid4(), page_size=0)

    def test_page_size_above_max(self):
        with pytest.raises(ValidationError):
            ImportPreviewResponse(batch_id=uuid4(), page_size=101)


# ── ImportApplyRequest ─────────────────────────────────────────────────


class TestImportApplyRequest:
    def test_defaults(self):
        r = ImportApplyRequest()
        assert r.conflict_resolution is None
        assert r.dry_run is False
        assert r.validate_acgme is True


# ── ImportApplyResponse ────────────────────────────────────────────────


class TestImportApplyResponse:
    def test_defaults(self):
        r = ImportApplyResponse(
            batch_id=uuid4(),
            status=ImportBatchStatus.APPLIED,
            started_at=datetime(2026, 1, 15),
        )
        assert r.applied_count == 0
        assert r.skipped_count == 0
        assert r.error_count == 0
        assert r.completed_at is None
        assert r.processing_time_ms is None
        assert r.errors == []
        assert r.acgme_warnings == []
        assert r.rollback_available is True
        assert r.rollback_expires_at is None
        assert r.dry_run is False


# ── ImportRollbackRequest ──────────────────────────────────────────────


class TestImportRollbackRequest:
    def test_defaults(self):
        r = ImportRollbackRequest()
        assert r.reason is None

    # --- reason max_length=500 ---

    def test_reason_too_long(self):
        with pytest.raises(ValidationError):
            ImportRollbackRequest(reason="x" * 501)


# ── ImportRollbackResponse ─────────────────────────────────────────────


class TestImportRollbackResponse:
    def test_defaults(self):
        r = ImportRollbackResponse(
            batch_id=uuid4(),
            status=ImportBatchStatus.ROLLED_BACK,
            rolled_back_at=datetime(2026, 1, 15),
        )
        assert r.rolled_back_count == 0
        assert r.failed_count == 0
        assert r.rolled_back_by_id is None
        assert r.errors == []
