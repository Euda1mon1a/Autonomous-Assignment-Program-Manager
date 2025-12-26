"""Tests for batch operations API routes.

Tests the batch assignment management functionality including:
- Batch create operations (up to 1000 assignments)
- Batch update operations
- Batch delete operations
- Status tracking for long-running operations
- Dry-run validation mode
- ACGME compliance validation
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.models.user import User
from app.schemas.batch import (
    BatchOperationStatus,
    BatchOperationType,
    BatchOperationResult,
    BatchResponse,
    BatchStatusResponse,
)


class TestBatchRoutes:
    """Test suite for batch operations API endpoints."""

    # ========================================================================
    # Authentication Tests
    # ========================================================================

    def test_batch_create_requires_auth(self, client: TestClient):
        """Test that batch create requires authentication."""
        response = client.post(
            "/api/batch/create",
            json={
                "assignments": [
                    {
                        "block_id": str(uuid4()),
                        "person_id": str(uuid4()),
                        "role": "primary",
                    }
                ]
            },
        )
        assert response.status_code == 401

    def test_batch_update_requires_auth(self, client: TestClient):
        """Test that batch update requires authentication."""
        response = client.put(
            "/api/batch/update",
            json={
                "assignments": [
                    {
                        "assignment_id": str(uuid4()),
                        "role": "supervising",
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                ]
            },
        )
        assert response.status_code == 401

    def test_batch_delete_requires_auth(self, client: TestClient):
        """Test that batch delete requires authentication."""
        response = client.delete(
            "/api/batch/delete",
            json={"assignments": [{"assignment_id": str(uuid4())}]},
        )
        assert response.status_code == 401

    def test_batch_status_requires_auth(self, client: TestClient):
        """Test that batch status requires authentication."""
        response = client.get(f"/api/batch/status/{uuid4()}")
        assert response.status_code == 401

    # ========================================================================
    # Batch Create Tests
    # ========================================================================

    @patch("app.api.routes.batch.BatchService")
    def test_batch_create_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
        admin_user: User,
    ):
        """Test successful batch create operation."""
        operation_id = uuid4()
        mock_service = MagicMock()
        mock_service.create_batch = AsyncMock(
            return_value=BatchResponse(
                operation_id=operation_id,
                operation_type=BatchOperationType.CREATE,
                status=BatchOperationStatus.COMPLETED,
                total=2,
                succeeded=2,
                failed=0,
                results=[
                    BatchOperationResult(index=0, success=True, assignment_id=uuid4()),
                    BatchOperationResult(index=1, success=True, assignment_id=uuid4()),
                ],
                dry_run=False,
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                processing_time_ms=50.0,
            )
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/batch/create",
            headers=auth_headers,
            json={
                "assignments": [
                    {
                        "block_id": str(uuid4()),
                        "person_id": str(uuid4()),
                        "role": "primary",
                    },
                    {
                        "block_id": str(uuid4()),
                        "person_id": str(uuid4()),
                        "role": "supervising",
                    },
                ],
                "dry_run": False,
                "validate_acgme": True,
            },
        )
        assert response.status_code == 201

        data = response.json()
        assert data["operation_type"] == "create"
        assert data["status"] == "completed"
        assert data["succeeded"] == 2
        assert data["failed"] == 0

    @patch("app.api.routes.batch.BatchService")
    def test_batch_create_dry_run(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test batch create with dry run mode."""
        operation_id = uuid4()
        mock_service = MagicMock()
        mock_service.create_batch = AsyncMock(
            return_value=BatchResponse(
                operation_id=operation_id,
                operation_type=BatchOperationType.CREATE,
                status=BatchOperationStatus.COMPLETED,
                total=1,
                succeeded=1,
                failed=0,
                results=[BatchOperationResult(index=0, success=True)],
                dry_run=True,
                created_at=datetime.utcnow(),
            )
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/batch/create",
            headers=auth_headers,
            json={
                "assignments": [
                    {
                        "block_id": str(uuid4()),
                        "person_id": str(uuid4()),
                        "role": "primary",
                    }
                ],
                "dry_run": True,
            },
        )
        assert response.status_code == 201

        data = response.json()
        assert data["dry_run"] is True

    @patch("app.api.routes.batch.BatchService")
    def test_batch_create_with_acgme_validation(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test batch create with ACGME compliance validation."""
        operation_id = uuid4()
        mock_service = MagicMock()
        mock_service.create_batch = AsyncMock(
            return_value=BatchResponse(
                operation_id=operation_id,
                operation_type=BatchOperationType.CREATE,
                status=BatchOperationStatus.COMPLETED,
                total=1,
                succeeded=1,
                failed=0,
                results=[
                    BatchOperationResult(index=0, success=True, assignment_id=uuid4())
                ],
                warnings=["ACGME: Approaching 80-hour limit"],
                dry_run=False,
                created_at=datetime.utcnow(),
            )
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/batch/create",
            headers=auth_headers,
            json={
                "assignments": [
                    {
                        "block_id": str(uuid4()),
                        "person_id": str(uuid4()),
                        "role": "primary",
                    }
                ],
                "validate_acgme": True,
            },
        )
        assert response.status_code == 201

        data = response.json()
        assert "warnings" in data

    @patch("app.api.routes.batch.BatchService")
    def test_batch_create_partial_failure(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test batch create with some operations failing."""
        operation_id = uuid4()
        mock_service = MagicMock()
        mock_service.create_batch = AsyncMock(
            return_value=BatchResponse(
                operation_id=operation_id,
                operation_type=BatchOperationType.CREATE,
                status=BatchOperationStatus.PARTIAL,
                total=3,
                succeeded=2,
                failed=1,
                results=[
                    BatchOperationResult(index=0, success=True, assignment_id=uuid4()),
                    BatchOperationResult(
                        index=1, success=False, error="Block not found"
                    ),
                    BatchOperationResult(index=2, success=True, assignment_id=uuid4()),
                ],
                dry_run=False,
                created_at=datetime.utcnow(),
            )
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/batch/create",
            headers=auth_headers,
            json={
                "assignments": [
                    {
                        "block_id": str(uuid4()),
                        "person_id": str(uuid4()),
                        "role": "primary",
                    },
                    {
                        "block_id": str(uuid4()),
                        "person_id": str(uuid4()),
                        "role": "primary",
                    },
                    {
                        "block_id": str(uuid4()),
                        "person_id": str(uuid4()),
                        "role": "primary",
                    },
                ],
                "rollback_on_error": False,
            },
        )
        assert response.status_code == 201

        data = response.json()
        assert data["status"] == "partial"
        assert data["succeeded"] == 2
        assert data["failed"] == 1

    @patch("app.api.routes.batch.BatchService")
    def test_batch_create_all_failed(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test batch create when all operations fail."""
        operation_id = uuid4()
        mock_service = MagicMock()
        mock_service.create_batch = AsyncMock(
            return_value=BatchResponse(
                operation_id=operation_id,
                operation_type=BatchOperationType.CREATE,
                status=BatchOperationStatus.FAILED,
                total=2,
                succeeded=0,
                failed=2,
                results=[
                    BatchOperationResult(index=0, success=False, error="Invalid block"),
                    BatchOperationResult(
                        index=1, success=False, error="Invalid person"
                    ),
                ],
                errors=["Batch operation failed: all items failed validation"],
                dry_run=False,
                created_at=datetime.utcnow(),
            )
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/batch/create",
            headers=auth_headers,
            json={
                "assignments": [
                    {
                        "block_id": str(uuid4()),
                        "person_id": str(uuid4()),
                        "role": "primary",
                    },
                    {
                        "block_id": str(uuid4()),
                        "person_id": str(uuid4()),
                        "role": "primary",
                    },
                ]
            },
        )
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "errors" in data["detail"]

    def test_batch_create_invalid_role(self, client: TestClient, auth_headers: dict):
        """Test batch create with invalid role value."""
        response = client.post(
            "/api/batch/create",
            headers=auth_headers,
            json={
                "assignments": [
                    {
                        "block_id": str(uuid4()),
                        "person_id": str(uuid4()),
                        "role": "invalid_role",
                    }
                ]
            },
        )
        assert response.status_code == 422

    def test_batch_create_empty_assignments(
        self, client: TestClient, auth_headers: dict
    ):
        """Test batch create with empty assignments list."""
        response = client.post(
            "/api/batch/create",
            headers=auth_headers,
            json={"assignments": []},
        )
        assert response.status_code == 422

    # ========================================================================
    # Batch Update Tests
    # ========================================================================

    @patch("app.api.routes.batch.BatchService")
    def test_batch_update_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful batch update operation."""
        operation_id = uuid4()
        mock_service = MagicMock()
        mock_service.update_batch = AsyncMock(
            return_value=BatchResponse(
                operation_id=operation_id,
                operation_type=BatchOperationType.UPDATE,
                status=BatchOperationStatus.COMPLETED,
                total=2,
                succeeded=2,
                failed=0,
                results=[
                    BatchOperationResult(index=0, success=True, assignment_id=uuid4()),
                    BatchOperationResult(index=1, success=True, assignment_id=uuid4()),
                ],
                dry_run=False,
                created_at=datetime.utcnow(),
            )
        )
        mock_service_class.return_value = mock_service

        response = client.put(
            "/api/batch/update",
            headers=auth_headers,
            json={
                "assignments": [
                    {
                        "assignment_id": str(uuid4()),
                        "role": "supervising",
                        "updated_at": datetime.utcnow().isoformat(),
                    },
                    {
                        "assignment_id": str(uuid4()),
                        "notes": "Updated notes",
                        "updated_at": datetime.utcnow().isoformat(),
                    },
                ]
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["operation_type"] == "update"
        assert data["succeeded"] == 2

    @patch("app.api.routes.batch.BatchService")
    def test_batch_update_optimistic_locking_conflict(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test batch update with optimistic locking conflict."""
        operation_id = uuid4()
        mock_service = MagicMock()
        mock_service.update_batch = AsyncMock(
            return_value=BatchResponse(
                operation_id=operation_id,
                operation_type=BatchOperationType.UPDATE,
                status=BatchOperationStatus.FAILED,
                total=1,
                succeeded=0,
                failed=1,
                results=[
                    BatchOperationResult(
                        index=0,
                        success=False,
                        error="Optimistic locking conflict: record was modified",
                    )
                ],
                errors=["Optimistic locking conflict detected"],
                dry_run=False,
                created_at=datetime.utcnow(),
            )
        )
        mock_service_class.return_value = mock_service

        response = client.put(
            "/api/batch/update",
            headers=auth_headers,
            json={
                "assignments": [
                    {
                        "assignment_id": str(uuid4()),
                        "role": "backup",
                        "updated_at": "2023-01-01T00:00:00",
                    }
                ]
            },
        )
        assert response.status_code == 400

    @patch("app.api.routes.batch.BatchService")
    def test_batch_update_dry_run(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test batch update with dry run mode."""
        operation_id = uuid4()
        mock_service = MagicMock()
        mock_service.update_batch = AsyncMock(
            return_value=BatchResponse(
                operation_id=operation_id,
                operation_type=BatchOperationType.UPDATE,
                status=BatchOperationStatus.COMPLETED,
                total=1,
                succeeded=1,
                failed=0,
                results=[BatchOperationResult(index=0, success=True)],
                dry_run=True,
                created_at=datetime.utcnow(),
            )
        )
        mock_service_class.return_value = mock_service

        response = client.put(
            "/api/batch/update",
            headers=auth_headers,
            json={
                "assignments": [
                    {
                        "assignment_id": str(uuid4()),
                        "role": "primary",
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                ],
                "dry_run": True,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["dry_run"] is True

    # ========================================================================
    # Batch Delete Tests
    # ========================================================================

    @patch("app.api.routes.batch.BatchService")
    def test_batch_delete_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful batch delete operation."""
        operation_id = uuid4()
        mock_service = MagicMock()
        mock_service.delete_batch = AsyncMock(
            return_value=BatchResponse(
                operation_id=operation_id,
                operation_type=BatchOperationType.DELETE,
                status=BatchOperationStatus.COMPLETED,
                total=3,
                succeeded=3,
                failed=0,
                results=[
                    BatchOperationResult(index=0, success=True, assignment_id=uuid4()),
                    BatchOperationResult(index=1, success=True, assignment_id=uuid4()),
                    BatchOperationResult(index=2, success=True, assignment_id=uuid4()),
                ],
                dry_run=False,
                created_at=datetime.utcnow(),
            )
        )
        mock_service_class.return_value = mock_service

        response = client.delete(
            "/api/batch/delete",
            headers=auth_headers,
            json={
                "assignments": [
                    {"assignment_id": str(uuid4())},
                    {"assignment_id": str(uuid4())},
                    {"assignment_id": str(uuid4())},
                ]
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["operation_type"] == "delete"
        assert data["succeeded"] == 3

    @patch("app.api.routes.batch.BatchService")
    def test_batch_delete_soft_delete(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test batch delete with soft delete option."""
        operation_id = uuid4()
        assignment_id = uuid4()
        mock_service = MagicMock()
        mock_service.delete_batch = AsyncMock(
            return_value=BatchResponse(
                operation_id=operation_id,
                operation_type=BatchOperationType.DELETE,
                status=BatchOperationStatus.COMPLETED,
                total=1,
                succeeded=1,
                failed=0,
                results=[
                    BatchOperationResult(
                        index=0, success=True, assignment_id=assignment_id
                    )
                ],
                dry_run=False,
                created_at=datetime.utcnow(),
            )
        )
        mock_service_class.return_value = mock_service

        response = client.delete(
            "/api/batch/delete",
            headers=auth_headers,
            json={
                "assignments": [
                    {"assignment_id": str(assignment_id), "soft_delete": True}
                ]
            },
        )
        assert response.status_code == 200

    @patch("app.api.routes.batch.BatchService")
    def test_batch_delete_not_found(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test batch delete when assignment not found."""
        operation_id = uuid4()
        mock_service = MagicMock()
        mock_service.delete_batch = AsyncMock(
            return_value=BatchResponse(
                operation_id=operation_id,
                operation_type=BatchOperationType.DELETE,
                status=BatchOperationStatus.FAILED,
                total=1,
                succeeded=0,
                failed=1,
                results=[
                    BatchOperationResult(
                        index=0, success=False, error="Assignment not found"
                    )
                ],
                errors=["One or more assignments not found"],
                dry_run=False,
                created_at=datetime.utcnow(),
            )
        )
        mock_service_class.return_value = mock_service

        response = client.delete(
            "/api/batch/delete",
            headers=auth_headers,
            json={"assignments": [{"assignment_id": str(uuid4())}]},
        )
        assert response.status_code == 400

    @patch("app.api.routes.batch.BatchService")
    def test_batch_delete_with_rollback(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test batch delete with rollback on error."""
        operation_id = uuid4()
        mock_service = MagicMock()
        mock_service.delete_batch = AsyncMock(
            return_value=BatchResponse(
                operation_id=operation_id,
                operation_type=BatchOperationType.DELETE,
                status=BatchOperationStatus.FAILED,
                total=2,
                succeeded=0,
                failed=2,
                results=[
                    BatchOperationResult(
                        index=0,
                        success=False,
                        error="Rolled back due to error in item 1",
                    ),
                    BatchOperationResult(
                        index=1, success=False, error="Assignment not found"
                    ),
                ],
                errors=["Batch rolled back due to error"],
                dry_run=False,
                created_at=datetime.utcnow(),
            )
        )
        mock_service_class.return_value = mock_service

        response = client.delete(
            "/api/batch/delete",
            headers=auth_headers,
            json={
                "assignments": [
                    {"assignment_id": str(uuid4())},
                    {"assignment_id": str(uuid4())},
                ],
                "rollback_on_error": True,
            },
        )
        assert response.status_code == 400

    # ========================================================================
    # Batch Status Tests
    # ========================================================================

    @patch("app.api.routes.batch.BatchService")
    def test_get_batch_status_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test successful batch status retrieval."""
        operation_id = uuid4()
        mock_service = MagicMock()
        mock_service.get_batch_status.return_value = BatchStatusResponse(
            operation_id=operation_id,
            operation_type=BatchOperationType.CREATE,
            status=BatchOperationStatus.PROCESSING,
            total=100,
            succeeded=75,
            failed=0,
            progress_percentage=75.0,
            created_at=datetime.utcnow(),
            estimated_completion=datetime.utcnow(),
        )
        mock_service_class.return_value = mock_service

        response = client.get(
            f"/api/batch/status/{operation_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "processing"
        assert data["progress_percentage"] == 75.0
        assert data["succeeded"] == 75

    @patch("app.api.routes.batch.BatchService")
    def test_get_batch_status_completed(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test batch status for completed operation."""
        operation_id = uuid4()
        mock_service = MagicMock()
        mock_service.get_batch_status.return_value = BatchStatusResponse(
            operation_id=operation_id,
            operation_type=BatchOperationType.UPDATE,
            status=BatchOperationStatus.COMPLETED,
            total=50,
            succeeded=50,
            failed=0,
            progress_percentage=100.0,
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        mock_service_class.return_value = mock_service

        response = client.get(
            f"/api/batch/status/{operation_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "completed"
        assert data["progress_percentage"] == 100.0
        assert data["completed_at"] is not None

    @patch("app.api.routes.batch.BatchService")
    def test_get_batch_status_not_found(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test batch status for non-existent operation."""
        mock_service = MagicMock()
        mock_service.get_batch_status.return_value = None
        mock_service_class.return_value = mock_service

        response = client.get(
            f"/api/batch/status/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @patch("app.api.routes.batch.BatchService")
    def test_get_batch_status_with_failures(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test batch status showing failures."""
        operation_id = uuid4()
        mock_service = MagicMock()
        mock_service.get_batch_status.return_value = BatchStatusResponse(
            operation_id=operation_id,
            operation_type=BatchOperationType.DELETE,
            status=BatchOperationStatus.PARTIAL,
            total=100,
            succeeded=95,
            failed=5,
            progress_percentage=100.0,
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        mock_service_class.return_value = mock_service

        response = client.get(
            f"/api/batch/status/{operation_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "partial"
        assert data["failed"] == 5

    # ========================================================================
    # Edge Cases and Validation Tests
    # ========================================================================

    def test_batch_create_max_limit(self, client: TestClient, auth_headers: dict):
        """Test batch create respects max 1000 limit."""
        # Create 1001 assignments to exceed limit
        assignments = [
            {
                "block_id": str(uuid4()),
                "person_id": str(uuid4()),
                "role": "primary",
            }
            for _ in range(1001)
        ]

        response = client.post(
            "/api/batch/create",
            headers=auth_headers,
            json={"assignments": assignments},
        )
        assert response.status_code == 422

    def test_batch_update_missing_updated_at(
        self, client: TestClient, auth_headers: dict
    ):
        """Test batch update requires updated_at for optimistic locking."""
        response = client.put(
            "/api/batch/update",
            headers=auth_headers,
            json={
                "assignments": [
                    {
                        "assignment_id": str(uuid4()),
                        "role": "backup",
                        # Missing updated_at
                    }
                ]
            },
        )
        assert response.status_code == 422

    @patch("app.api.routes.batch.BatchService")
    def test_batch_create_with_notes_and_override(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test batch create with optional fields like notes and override_reason."""
        operation_id = uuid4()
        mock_service = MagicMock()
        mock_service.create_batch = AsyncMock(
            return_value=BatchResponse(
                operation_id=operation_id,
                operation_type=BatchOperationType.CREATE,
                status=BatchOperationStatus.COMPLETED,
                total=1,
                succeeded=1,
                failed=0,
                results=[
                    BatchOperationResult(index=0, success=True, assignment_id=uuid4())
                ],
                dry_run=False,
                created_at=datetime.utcnow(),
            )
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/batch/create",
            headers=auth_headers,
            json={
                "assignments": [
                    {
                        "block_id": str(uuid4()),
                        "person_id": str(uuid4()),
                        "role": "primary",
                        "rotation_template_id": str(uuid4()),
                        "activity_override": "Special clinic",
                        "notes": "Coverage for leave",
                        "override_reason": "Emergency coverage request",
                    }
                ]
            },
        )
        assert response.status_code == 201

    @patch("app.api.routes.batch.BatchService")
    def test_batch_processing_time_tracked(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test that batch operations track processing time."""
        operation_id = uuid4()
        mock_service = MagicMock()
        mock_service.create_batch = AsyncMock(
            return_value=BatchResponse(
                operation_id=operation_id,
                operation_type=BatchOperationType.CREATE,
                status=BatchOperationStatus.COMPLETED,
                total=1,
                succeeded=1,
                failed=0,
                results=[
                    BatchOperationResult(index=0, success=True, assignment_id=uuid4())
                ],
                dry_run=False,
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                processing_time_ms=125.5,
            )
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/batch/create",
            headers=auth_headers,
            json={
                "assignments": [
                    {
                        "block_id": str(uuid4()),
                        "person_id": str(uuid4()),
                        "role": "primary",
                    }
                ]
            },
        )
        assert response.status_code == 201

        data = response.json()
        assert "processing_time_ms" in data
        assert data["processing_time_ms"] == 125.5
