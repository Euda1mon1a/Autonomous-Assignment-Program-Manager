"""Tests for bulk operations schemas (field_validators, Field bounds, defaults)."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.bulk_operations import (
    BulkCreateRequest,
    BulkUpdateRequest,
    BulkDeleteRequest,
    ItemResult,
    BulkOperationResponse,
    BatchAssignmentCreate,
    BatchAssignmentDelete,
    BulkSwapApproval,
    BulkCredentialUpdate,
    AsyncBulkOperationRequest,
    AsyncBulkOperationStatus,
)


class TestBulkCreateRequest:
    def test_valid(self):
        r = BulkCreateRequest(items=[{"name": "Item 1"}])
        assert len(r.items) == 1

    # --- items min_length=1 ---

    def test_items_empty(self):
        with pytest.raises(ValidationError):
            BulkCreateRequest(items=[])


class TestBulkUpdateRequest:
    def test_valid(self):
        r = BulkUpdateRequest(updates=[{"id": "abc", "name": "Updated"}])
        assert len(r.updates) == 1

    # --- updates min_length=1 ---

    def test_updates_empty(self):
        with pytest.raises(ValidationError):
            BulkUpdateRequest(updates=[])

    # --- field_validator: each update must have id ---

    def test_update_missing_id(self):
        with pytest.raises(ValidationError, match="missing 'id' field"):
            BulkUpdateRequest(updates=[{"name": "No ID"}])


class TestBulkDeleteRequest:
    def test_valid(self):
        r = BulkDeleteRequest(ids=[uuid4()])
        assert r.soft_delete is False

    def test_soft_delete(self):
        r = BulkDeleteRequest(ids=[uuid4()], soft_delete=True)
        assert r.soft_delete is True

    # --- ids min_length=1 ---

    def test_ids_empty(self):
        with pytest.raises(ValidationError):
            BulkDeleteRequest(ids=[])


class TestItemResult:
    def test_success(self):
        r = ItemResult(index=0, success=True, id=uuid4())
        assert r.error is None
        assert r.error_code is None

    def test_failure(self):
        r = ItemResult(
            index=1, success=False, error="Not found", error_code="NOT_FOUND"
        )
        assert r.id is None


class TestBulkOperationResponse:
    def test_valid(self):
        result = ItemResult(index=0, success=True)
        r = BulkOperationResponse(total=1, successful=1, failed=0, results=[result])
        assert r.started_at is not None
        assert r.completed_at is not None


class TestBatchAssignmentCreate:
    def test_valid_defaults(self):
        r = BatchAssignmentCreate(person_id=uuid4(), block_ids=[uuid4()])
        assert r.role == "primary"
        assert r.rotation_template_id is None
        assert r.notes is None

    # --- block_ids min_length=1 ---

    def test_block_ids_empty(self):
        with pytest.raises(ValidationError):
            BatchAssignmentCreate(person_id=uuid4(), block_ids=[])

    # --- role field_validator ---

    def test_valid_roles(self):
        for role in ("primary", "supervising", "backup"):
            r = BatchAssignmentCreate(person_id=uuid4(), block_ids=[uuid4()], role=role)
            assert r.role == role

    def test_invalid_role(self):
        with pytest.raises(
            ValidationError,
            match="role must be 'primary', 'supervising', or 'backup'",
        ):
            BatchAssignmentCreate(
                person_id=uuid4(), block_ids=[uuid4()], role="observer"
            )


class TestBatchAssignmentDelete:
    def test_valid(self):
        r = BatchAssignmentDelete(
            person_id=uuid4(),
            start_date="2026-03-01",
            end_date="2026-03-31",
        )
        assert r.rotation_template_id is None

    def test_with_rotation(self):
        r = BatchAssignmentDelete(
            person_id=uuid4(),
            start_date="2026-03-01",
            end_date="2026-03-31",
            rotation_template_id=uuid4(),
        )
        assert r.rotation_template_id is not None


class TestBulkSwapApproval:
    def test_valid(self):
        r = BulkSwapApproval(swap_ids=[uuid4(), uuid4()], approved_by="admin")
        assert r.notes is None

    # --- swap_ids min_length=1 ---

    def test_swap_ids_empty(self):
        with pytest.raises(ValidationError):
            BulkSwapApproval(swap_ids=[], approved_by="admin")


class TestBulkCredentialUpdate:
    def test_valid(self):
        r = BulkCredentialUpdate(
            updates=[
                {
                    "person_id": "p1",
                    "credential_name": "BLS",
                    "expires_at": "2027-01-01",
                }
            ]
        )
        assert len(r.updates) == 1

    # --- updates min_length=1 ---

    def test_updates_empty(self):
        with pytest.raises(ValidationError):
            BulkCredentialUpdate(updates=[])

    # --- field_validator: required fields ---

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError, match="missing required fields"):
            BulkCredentialUpdate(updates=[{"person_id": "p1"}])


class TestAsyncBulkOperationRequest:
    def test_valid(self):
        r = AsyncBulkOperationRequest(
            operation_type="create", items=[{"name": "Item 1"}]
        )
        assert r.callback_url is None

    # --- operation_type field_validator ---

    def test_valid_operation_types(self):
        for op_type in ("create", "update", "delete", "import"):
            r = AsyncBulkOperationRequest(
                operation_type=op_type, items=[{"data": True}]
            )
            assert r.operation_type == op_type

    def test_invalid_operation_type(self):
        with pytest.raises(ValidationError, match="operation_type must be one of"):
            AsyncBulkOperationRequest(operation_type="invalid", items=[{"data": True}])

    # --- items min_length=1 ---

    def test_items_empty(self):
        with pytest.raises(ValidationError):
            AsyncBulkOperationRequest(operation_type="create", items=[])


class TestAsyncBulkOperationStatus:
    def test_valid(self):
        from datetime import datetime

        r = AsyncBulkOperationStatus(
            operation_id=uuid4(),
            status="running",
            total=100,
            processed=50,
            successful=48,
            failed=2,
            started_at=datetime(2026, 3, 1),
            progress_percentage=50.0,
        )
        assert r.completed_at is None

    # --- status field_validator ---

    def test_valid_statuses(self):
        from datetime import datetime

        for status in ("pending", "running", "completed", "failed", "cancelled"):
            r = AsyncBulkOperationStatus(
                operation_id=uuid4(),
                status=status,
                total=10,
                processed=0,
                successful=0,
                failed=0,
                started_at=datetime(2026, 3, 1),
                progress_percentage=0.0,
            )
            assert r.status == status

    def test_invalid_status(self):
        from datetime import datetime

        with pytest.raises(ValidationError, match="status must be one of"):
            AsyncBulkOperationStatus(
                operation_id=uuid4(),
                status="unknown",
                total=10,
                processed=0,
                successful=0,
                failed=0,
                started_at=datetime(2026, 3, 1),
                progress_percentage=0.0,
            )
