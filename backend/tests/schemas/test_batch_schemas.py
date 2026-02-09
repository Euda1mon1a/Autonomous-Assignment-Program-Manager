"""Tests for batch operation schemas (enums, field_validators, Field bounds)."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.batch import (
    BatchOperationType,
    BatchOperationStatus,
    BatchAssignmentCreate,
    BatchAssignmentUpdate,
    BatchAssignmentDelete,
    BatchCreateRequest,
    BatchUpdateRequest,
    BatchDeleteRequest,
    BatchOperationResult,
    BatchResponse,
    BatchStatusResponse,
    BatchValidationResult,
)


class TestBatchOperationType:
    def test_values(self):
        assert BatchOperationType.CREATE.value == "create"
        assert BatchOperationType.UPDATE.value == "update"
        assert BatchOperationType.DELETE.value == "delete"

    def test_count(self):
        assert len(BatchOperationType) == 3


class TestBatchOperationStatus:
    def test_values(self):
        assert BatchOperationStatus.PENDING.value == "pending"
        assert BatchOperationStatus.PROCESSING.value == "processing"
        assert BatchOperationStatus.COMPLETED.value == "completed"
        assert BatchOperationStatus.FAILED.value == "failed"
        assert BatchOperationStatus.PARTIAL.value == "partial"

    def test_count(self):
        assert len(BatchOperationStatus) == 5


class TestBatchAssignmentCreate:
    def test_valid_minimal(self):
        r = BatchAssignmentCreate(block_id=uuid4(), person_id=uuid4(), role="primary")
        assert r.rotation_template_id is None
        assert r.activity_override is None
        assert r.notes is None
        assert r.override_reason is None

    # --- role field_validator ---

    def test_role_valid(self):
        for role in ("primary", "supervising", "backup"):
            r = BatchAssignmentCreate(block_id=uuid4(), person_id=uuid4(), role=role)
            assert r.role == role

    def test_role_invalid(self):
        with pytest.raises(ValidationError, match="role must be"):
            BatchAssignmentCreate(block_id=uuid4(), person_id=uuid4(), role="observer")


class TestBatchAssignmentUpdate:
    def test_valid_minimal(self):
        r = BatchAssignmentUpdate(
            assignment_id=uuid4(), updated_at=datetime(2026, 3, 1)
        )
        assert r.role is None

    # --- role field_validator (None-aware) ---

    def test_role_invalid(self):
        with pytest.raises(ValidationError, match="role must be"):
            BatchAssignmentUpdate(
                assignment_id=uuid4(),
                role="observer",
                updated_at=datetime(2026, 3, 1),
            )


class TestBatchAssignmentDelete:
    def test_valid(self):
        r = BatchAssignmentDelete(assignment_id=uuid4())
        assert r.soft_delete is False

    def test_soft_delete(self):
        r = BatchAssignmentDelete(assignment_id=uuid4(), soft_delete=True)
        assert r.soft_delete is True


class TestBatchCreateRequest:
    def _make_assignment(self):
        return BatchAssignmentCreate(
            block_id=uuid4(), person_id=uuid4(), role="primary"
        )

    def test_valid_defaults(self):
        r = BatchCreateRequest(assignments=[self._make_assignment()])
        assert r.dry_run is False
        assert r.rollback_on_error is True
        assert r.created_by is None
        assert r.validate_acgme is True

    # --- assignments min_length=1 ---

    def test_assignments_empty(self):
        with pytest.raises(ValidationError):
            BatchCreateRequest(assignments=[])


class TestBatchUpdateRequest:
    def _make_update(self):
        return BatchAssignmentUpdate(
            assignment_id=uuid4(), updated_at=datetime(2026, 3, 1)
        )

    def test_valid_defaults(self):
        r = BatchUpdateRequest(assignments=[self._make_update()])
        assert r.dry_run is False
        assert r.rollback_on_error is True
        assert r.validate_acgme is True

    def test_assignments_empty(self):
        with pytest.raises(ValidationError):
            BatchUpdateRequest(assignments=[])


class TestBatchDeleteRequest:
    def _make_delete(self):
        return BatchAssignmentDelete(assignment_id=uuid4())

    def test_valid_defaults(self):
        r = BatchDeleteRequest(assignments=[self._make_delete()])
        assert r.dry_run is False
        assert r.rollback_on_error is True

    def test_assignments_empty(self):
        with pytest.raises(ValidationError):
            BatchDeleteRequest(assignments=[])


class TestBatchOperationResult:
    def test_success(self):
        r = BatchOperationResult(index=0, success=True, assignment_id=uuid4())
        assert r.error is None
        assert r.warnings == []

    def test_failure(self):
        r = BatchOperationResult(
            index=1,
            success=False,
            error="ACGME violation: 80-hour exceeded",
            warnings=["Approaching limit"],
        )
        assert r.assignment_id is None
        assert len(r.warnings) == 1


class TestBatchResponse:
    def test_valid_minimal(self):
        r = BatchResponse(
            operation_id=uuid4(),
            operation_type=BatchOperationType.CREATE,
            status=BatchOperationStatus.COMPLETED,
            total=5,
            succeeded=5,
            failed=0,
            created_at=datetime(2026, 3, 1),
        )
        assert r.results == []
        assert r.errors == []
        assert r.warnings == []
        assert r.dry_run is False
        assert r.completed_at is None
        assert r.processing_time_ms is None


class TestBatchStatusResponse:
    def test_valid(self):
        r = BatchStatusResponse(
            operation_id=uuid4(),
            operation_type=BatchOperationType.UPDATE,
            status=BatchOperationStatus.PROCESSING,
            total=100,
            succeeded=50,
            failed=0,
            progress_percentage=50.0,
            created_at=datetime(2026, 3, 1),
        )
        assert r.completed_at is None
        assert r.estimated_completion is None


class TestBatchValidationResult:
    def test_valid(self):
        r = BatchValidationResult(valid=True, total_operations=10)
        assert r.validation_errors == []
        assert r.operation_errors == []
        assert r.acgme_warnings == []

    def test_invalid(self):
        r = BatchValidationResult(
            valid=False,
            total_operations=10,
            validation_errors=["Duplicate assignments"],
            acgme_warnings=["80-hour approaching"],
        )
        assert len(r.validation_errors) == 1
        assert len(r.acgme_warnings) == 1
