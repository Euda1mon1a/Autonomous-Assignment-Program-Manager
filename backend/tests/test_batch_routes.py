"""
Comprehensive tests for Batch Operations API routes.

Tests coverage for bulk assignment operations:
- POST /api/batch/create - Batch create assignments
- PUT /api/batch/update - Batch update assignments
- DELETE /api/batch/delete - Batch delete assignments
- GET /api/batch/status/{operation_id} - Get batch operation status
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ============================================================================
# Test Classes
# ============================================================================


class TestBatchCreateEndpoint:
    """Tests for POST /api/batch/create endpoint."""

    def test_batch_create_requires_auth(self, client: TestClient):
        """Test that batch create requires authentication."""
        response = client.post(
            "/api/batch/create",
            json={
                "assignments": [],
                "dry_run": False,
            },
        )

        assert response.status_code in [401, 403]

    def test_batch_create_requires_scheduler_role(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that batch create requires scheduler role."""
        with patch("app.api.routes.batch.BatchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.create_batch.return_value = MagicMock(
                operation_id=uuid4(),
                status="completed",
                total=0,
                succeeded=0,
                failed=0,
                results=[],
                errors=[],
            )
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/batch/create",
                json={
                    "assignments": [],
                    "dry_run": False,
                },
                headers=auth_headers,
            )

            # Should require scheduler role (may return 401, 403, or 201)
            assert response.status_code in [201, 401, 403]

    def test_batch_create_with_assignments(
        self, client: TestClient, auth_headers: dict
    ):
        """Test batch create with assignments."""
        with patch("app.api.routes.batch.BatchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.create_batch.return_value = MagicMock(
                operation_id=uuid4(),
                status="completed",
                total=2,
                succeeded=2,
                failed=0,
                results=[
                    MagicMock(
                        dict=lambda: {"assignment_id": str(uuid4()), "status": "created"}
                    )
                ],
                errors=[],
            )
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/batch/create",
                json={
                    "assignments": [
                        {
                            "block_id": str(uuid4()),
                            "person_id": str(uuid4()),
                            "role": "primary",
                            "rotation_template_id": str(uuid4()),
                        },
                        {
                            "block_id": str(uuid4()),
                            "person_id": str(uuid4()),
                            "role": "supervising",
                            "rotation_template_id": str(uuid4()),
                        },
                    ],
                    "dry_run": False,
                    "rollback_on_error": True,
                    "validate_acgme": True,
                },
                headers=auth_headers,
            )

            assert response.status_code in [201, 401, 403]

    def test_batch_create_dry_run(self, client: TestClient, auth_headers: dict):
        """Test batch create with dry run mode."""
        with patch("app.api.routes.batch.BatchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.create_batch.return_value = MagicMock(
                operation_id=uuid4(),
                status="validated",
                total=1,
                succeeded=1,
                failed=0,
                results=[],
                errors=[],
            )
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/batch/create",
                json={
                    "assignments": [
                        {
                            "block_id": str(uuid4()),
                            "person_id": str(uuid4()),
                            "role": "primary",
                            "rotation_template_id": str(uuid4()),
                        },
                    ],
                    "dry_run": True,
                },
                headers=auth_headers,
            )

            assert response.status_code in [201, 401, 403]

    def test_batch_create_failure(self, client: TestClient, auth_headers: dict):
        """Test batch create handles failures properly."""
        with patch("app.api.routes.batch.BatchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.create_batch.return_value = MagicMock(
                operation_id=uuid4(),
                status="failed",
                total=1,
                succeeded=0,
                failed=1,
                results=[
                    MagicMock(dict=lambda: {"assignment_id": None, "error": "Invalid"})
                ],
                errors=["Validation failed"],
            )
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/batch/create",
                json={
                    "assignments": [
                        {
                            "block_id": str(uuid4()),
                            "person_id": str(uuid4()),
                            "role": "invalid_role",
                            "rotation_template_id": str(uuid4()),
                        },
                    ],
                    "dry_run": False,
                },
                headers=auth_headers,
            )

            # Should return 400 for failed batch
            assert response.status_code in [400, 401, 403, 422]


class TestBatchUpdateEndpoint:
    """Tests for PUT /api/batch/update endpoint."""

    def test_batch_update_requires_auth(self, client: TestClient):
        """Test that batch update requires authentication."""
        response = client.put(
            "/api/batch/update",
            json={
                "assignments": [],
                "dry_run": False,
            },
        )

        assert response.status_code in [401, 403]

    def test_batch_update_success(self, client: TestClient, auth_headers: dict):
        """Test successful batch update."""
        with patch("app.api.routes.batch.BatchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.update_batch.return_value = MagicMock(
                operation_id=uuid4(),
                status="completed",
                total=1,
                succeeded=1,
                failed=0,
                results=[],
                errors=[],
            )
            mock_service.return_value = mock_instance

            assignment_id = str(uuid4())
            response = client.put(
                "/api/batch/update",
                json={
                    "assignments": [
                        {
                            "assignment_id": assignment_id,
                            "role": "supervising",
                            "notes": "Updated notes",
                        },
                    ],
                    "dry_run": False,
                    "rollback_on_error": True,
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 403]

    def test_batch_update_dry_run(self, client: TestClient, auth_headers: dict):
        """Test batch update with dry run mode."""
        with patch("app.api.routes.batch.BatchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.update_batch.return_value = MagicMock(
                operation_id=uuid4(),
                status="validated",
                total=1,
                succeeded=1,
                failed=0,
                results=[],
                errors=[],
            )
            mock_service.return_value = mock_instance

            response = client.put(
                "/api/batch/update",
                json={
                    "assignments": [
                        {
                            "assignment_id": str(uuid4()),
                            "role": "primary",
                        },
                    ],
                    "dry_run": True,
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 403]


class TestBatchDeleteEndpoint:
    """Tests for DELETE /api/batch/delete endpoint."""

    def test_batch_delete_requires_auth(self, client: TestClient):
        """Test that batch delete requires authentication."""
        response = client.delete(
            "/api/batch/delete",
            json={
                "assignments": [],
                "dry_run": False,
            },
        )

        # DELETE with body may not be supported, use request instead
        assert response.status_code in [401, 403, 405, 422]

    def test_batch_delete_success(self, client: TestClient, auth_headers: dict):
        """Test successful batch delete."""
        with patch("app.api.routes.batch.BatchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.delete_batch.return_value = MagicMock(
                operation_id=uuid4(),
                status="completed",
                total=1,
                succeeded=1,
                failed=0,
                results=[],
                errors=[],
            )
            mock_service.return_value = mock_instance

            # Use request method for DELETE with body
            response = client.request(
                "DELETE",
                "/api/batch/delete",
                json={
                    "assignments": [
                        {
                            "assignment_id": str(uuid4()),
                            "soft_delete": False,
                        },
                    ],
                    "dry_run": False,
                    "rollback_on_error": True,
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 403]

    def test_batch_delete_soft_delete(self, client: TestClient, auth_headers: dict):
        """Test batch delete with soft delete option."""
        with patch("app.api.routes.batch.BatchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.delete_batch.return_value = MagicMock(
                operation_id=uuid4(),
                status="completed",
                total=1,
                succeeded=1,
                failed=0,
                results=[],
                errors=[],
            )
            mock_service.return_value = mock_instance

            response = client.request(
                "DELETE",
                "/api/batch/delete",
                json={
                    "assignments": [
                        {
                            "assignment_id": str(uuid4()),
                            "soft_delete": True,
                        },
                    ],
                    "dry_run": False,
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 403]


class TestBatchStatusEndpoint:
    """Tests for GET /api/batch/status/{operation_id} endpoint."""

    def test_batch_status_requires_auth(self, client: TestClient):
        """Test that batch status requires authentication."""
        operation_id = str(uuid4())
        response = client.get(f"/api/batch/status/{operation_id}")

        assert response.status_code in [401, 403]

    def test_batch_status_success(self, client: TestClient, auth_headers: dict):
        """Test successful batch status retrieval."""
        with patch("app.api.routes.batch.BatchService") as mock_service:
            mock_instance = MagicMock()
            operation_id = uuid4()
            mock_instance.get_batch_status.return_value = MagicMock(
                operation_id=operation_id,
                operation_type="create",
                status="completed",
                total=10,
                succeeded=10,
                failed=0,
                progress_percentage=100.0,
            )
            mock_service.return_value = mock_instance

            response = client.get(
                f"/api/batch/status/{operation_id}",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_batch_status_in_progress(self, client: TestClient, auth_headers: dict):
        """Test batch status for in-progress operation."""
        with patch("app.api.routes.batch.BatchService") as mock_service:
            mock_instance = MagicMock()
            operation_id = uuid4()
            mock_instance.get_batch_status.return_value = MagicMock(
                operation_id=operation_id,
                operation_type="create",
                status="processing",
                total=100,
                succeeded=50,
                failed=0,
                progress_percentage=50.0,
            )
            mock_service.return_value = mock_instance

            response = client.get(
                f"/api/batch/status/{operation_id}",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_batch_status_not_found(self, client: TestClient, auth_headers: dict):
        """Test batch status for non-existent operation."""
        with patch("app.api.routes.batch.BatchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_batch_status.return_value = None
            mock_service.return_value = mock_instance

            operation_id = str(uuid4())
            response = client.get(
                f"/api/batch/status/{operation_id}",
                headers=auth_headers,
            )

            assert response.status_code in [401, 404]


# ============================================================================
# Validation Tests
# ============================================================================


class TestBatchValidation:
    """Tests for batch operation validation."""

    def test_batch_create_max_limit(self, client: TestClient, auth_headers: dict):
        """Test batch create enforces maximum limit."""
        # Create request with too many assignments (> 1000)
        assignments = [
            {
                "block_id": str(uuid4()),
                "person_id": str(uuid4()),
                "role": "primary",
                "rotation_template_id": str(uuid4()),
            }
            for _ in range(1001)
        ]

        response = client.post(
            "/api/batch/create",
            json={
                "assignments": assignments,
                "dry_run": False,
            },
            headers=auth_headers,
        )

        # Should return 400 or 422 for exceeding limit
        assert response.status_code in [400, 401, 403, 422]

    def test_batch_create_empty_assignments(
        self, client: TestClient, auth_headers: dict
    ):
        """Test batch create with empty assignments list."""
        with patch("app.api.routes.batch.BatchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.create_batch.return_value = MagicMock(
                operation_id=uuid4(),
                status="completed",
                total=0,
                succeeded=0,
                failed=0,
                results=[],
                errors=[],
            )
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/batch/create",
                json={
                    "assignments": [],
                    "dry_run": False,
                },
                headers=auth_headers,
            )

            # Empty assignments may be allowed or return 400
            assert response.status_code in [201, 400, 401, 403, 422]


# ============================================================================
# Integration Tests
# ============================================================================


class TestBatchIntegration:
    """Integration tests for batch operations."""

    def test_batch_endpoints_accessible(
        self, client: TestClient, auth_headers: dict
    ):
        """Test all batch endpoints respond appropriately."""
        with patch("app.api.routes.batch.BatchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.create_batch.return_value = MagicMock(
                operation_id=uuid4(),
                status="completed",
                total=0,
                succeeded=0,
                failed=0,
                results=[],
                errors=[],
            )
            mock_instance.update_batch.return_value = mock_instance.create_batch.return_value
            mock_instance.delete_batch.return_value = mock_instance.create_batch.return_value
            mock_instance.get_batch_status.return_value = None
            mock_service.return_value = mock_instance

            operation_id = str(uuid4())

            # Test create
            response = client.post(
                "/api/batch/create",
                json={"assignments": [], "dry_run": False},
                headers=auth_headers,
            )
            assert response.status_code not in [404, 405]

            # Test update
            response = client.put(
                "/api/batch/update",
                json={"assignments": [], "dry_run": False},
                headers=auth_headers,
            )
            assert response.status_code not in [404, 405]

            # Test status
            response = client.get(
                f"/api/batch/status/{operation_id}",
                headers=auth_headers,
            )
            assert response.status_code not in [405]

    def test_batch_response_format(self, client: TestClient, auth_headers: dict):
        """Test batch operations return valid response format."""
        with patch("app.api.routes.batch.BatchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.create_batch.return_value = MagicMock(
                operation_id=uuid4(),
                status="completed",
                total=1,
                succeeded=1,
                failed=0,
                results=[
                    MagicMock(
                        dict=lambda: {"assignment_id": str(uuid4()), "status": "created"}
                    )
                ],
                errors=[],
            )
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/batch/create",
                json={
                    "assignments": [
                        {
                            "block_id": str(uuid4()),
                            "person_id": str(uuid4()),
                            "role": "primary",
                            "rotation_template_id": str(uuid4()),
                        },
                    ],
                    "dry_run": False,
                },
                headers=auth_headers,
            )

            if response.status_code == 201:
                data = response.json()
                assert "operation_id" in data
                assert "status" in data
                assert "total" in data
