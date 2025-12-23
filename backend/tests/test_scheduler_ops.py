"""Tests for scheduler operations API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestSitrepEndpoint:
    """Test suite for situation report endpoint."""

    def test_sitrep_returns_valid_response(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that sitrep endpoint returns valid structure."""
        response = client.get("/api/scheduler/sitrep", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify required fields
        assert "timestamp" in data
        assert "task_metrics" in data
        assert "health_status" in data
        assert "recent_tasks" in data
        assert "coverage_metrics" in data
        assert "immediate_actions" in data
        assert "watch_items" in data
        assert "last_update" in data
        assert "crisis_mode" in data

    def test_sitrep_task_metrics_structure(
        self, client: TestClient, auth_headers: dict
    ):
        """Test task metrics have correct structure."""
        response = client.get("/api/scheduler/sitrep", headers=auth_headers)

        assert response.status_code == 200
        metrics = response.json()["task_metrics"]

        # Verify task metrics fields
        assert "total_tasks" in metrics
        assert "active_tasks" in metrics
        assert "completed_tasks" in metrics
        assert "failed_tasks" in metrics
        assert "pending_tasks" in metrics
        assert "success_rate" in metrics

        # Verify types and ranges
        assert isinstance(metrics["total_tasks"], int)
        assert metrics["total_tasks"] >= 0
        assert 0.0 <= metrics["success_rate"] <= 1.0

    def test_sitrep_coverage_metrics(self, client: TestClient, auth_headers: dict):
        """Test coverage metrics have correct structure."""
        response = client.get("/api/scheduler/sitrep", headers=auth_headers)

        assert response.status_code == 200
        coverage = response.json()["coverage_metrics"]

        assert "coverage_rate" in coverage
        assert "blocks_covered" in coverage
        assert "blocks_total" in coverage
        assert "critical_gaps" in coverage
        assert "faculty_utilization" in coverage

        assert 0.0 <= coverage["coverage_rate"] <= 1.0
        assert 0.0 <= coverage["faculty_utilization"] <= 1.0

    def test_sitrep_requires_authentication(self, client: TestClient):
        """Test that sitrep requires authentication."""
        response = client.get("/api/scheduler/sitrep")
        assert response.status_code == 401


class TestFixItEndpoint:
    """Test suite for fix-it mode endpoint."""

    def test_fix_it_dry_run(self, client: TestClient, auth_headers: dict):
        """Test fix-it in dry-run mode."""
        response = client.post(
            "/api/scheduler/fix-it",
            headers=auth_headers,
            json={
                "mode": "balanced",
                "max_retries": 3,
                "auto_approve": False,
                "initiated_by": "test_user",
                "dry_run": True,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "dry_run"
        assert "execution_id" in data
        assert data["mode"] == "balanced"
        assert data["initiated_by"] == "test_user"
        assert isinstance(data["warnings"], list)

    def test_fix_it_balanced_mode(self, client: TestClient, auth_headers: dict):
        """Test fix-it in balanced mode."""
        response = client.post(
            "/api/scheduler/fix-it",
            headers=auth_headers,
            json={
                "mode": "balanced",
                "max_retries": 2,
                "auto_approve": False,
                "initiated_by": "test_user",
                "dry_run": False,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "completed"
        assert "execution_id" in data
        assert "tasks_fixed" in data
        assert "tasks_retried" in data
        assert "tasks_skipped" in data
        assert "tasks_failed" in data
        assert isinstance(data["affected_tasks"], list)

    def test_fix_it_greedy_mode(self, client: TestClient, auth_headers: dict):
        """Test fix-it in greedy mode with warnings."""
        response = client.post(
            "/api/scheduler/fix-it",
            headers=auth_headers,
            json={
                "mode": "greedy",
                "max_retries": 3,
                "auto_approve": False,
                "initiated_by": "test_user",
                "dry_run": False,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Greedy mode should have warning
        assert len(data["warnings"]) > 0
        assert any("greedy" in w.lower() for w in data["warnings"])

    def test_fix_it_conservative_mode(self, client: TestClient, auth_headers: dict):
        """Test fix-it in conservative mode."""
        response = client.post(
            "/api/scheduler/fix-it",
            headers=auth_headers,
            json={
                "mode": "conservative",
                "max_retries": 3,
                "auto_approve": False,
                "initiated_by": "test_user",
                "dry_run": False,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["mode"] == "conservative"
        assert data["status"] == "completed"

    def test_fix_it_requires_authentication(self, client: TestClient):
        """Test that fix-it requires authentication."""
        response = client.post(
            "/api/scheduler/fix-it",
            json={
                "mode": "balanced",
                "max_retries": 3,
                "auto_approve": False,
                "initiated_by": "test_user",
            },
        )
        assert response.status_code == 401

    def test_fix_it_validates_max_retries(self, client: TestClient, auth_headers: dict):
        """Test that max_retries is validated."""
        # Too few retries
        response = client.post(
            "/api/scheduler/fix-it",
            headers=auth_headers,
            json={
                "mode": "balanced",
                "max_retries": 0,
                "auto_approve": False,
                "initiated_by": "test_user",
            },
        )
        assert response.status_code == 422  # Validation error

        # Too many retries
        response = client.post(
            "/api/scheduler/fix-it",
            headers=auth_headers,
            json={
                "mode": "balanced",
                "max_retries": 11,
                "auto_approve": False,
                "initiated_by": "test_user",
            },
        )
        assert response.status_code == 422  # Validation error


class TestApproveEndpoint:
    """Test suite for approval endpoint."""

    def test_generate_approval_token(self, client: TestClient, auth_headers: dict):
        """Test generating an approval token."""
        response = client.post(
            "/api/scheduler/approve/token/generate",
            headers=auth_headers,
            json={
                "task_ids": ["task-1", "task-2"],
                "task_type": "schedule_change",
                "expires_in_hours": 24,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "token" in data
        assert len(data["token"]) > 20  # Secure token
        assert data["task_ids"] == ["task-1", "task-2"]
        assert "expires_at" in data

        # Return token for use in other tests
        return data["token"]

    def test_approve_with_invalid_token(self, client: TestClient, auth_headers: dict):
        """Test approval with invalid token."""
        response = client.post(
            "/api/scheduler/approve",
            headers=auth_headers,
            json={
                "token": "invalid_token_that_does_not_exist",
                "action": "approve",
                "approved_by": "test_user",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "invalid_token"
        assert data["approved_tasks"] == 0
        assert len(data["warnings"]) > 0

    def test_approve_with_valid_token(self, client: TestClient, auth_headers: dict):
        """Test approval with valid token."""
        # First generate a token
        token_response = client.post(
            "/api/scheduler/approve/token/generate",
            headers=auth_headers,
            json={
                "task_ids": ["test-task-1"],
                "task_type": "schedule_change",
            },
        )
        token = token_response.json()["token"]

        # Then approve with that token
        response = client.post(
            "/api/scheduler/approve",
            headers=auth_headers,
            json={
                "token": token,
                "action": "approve",
                "approved_by": "test_user",
                "approved_by_id": "user123",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "approved"
        assert data["approved_tasks"] == 1
        assert data["denied_tasks"] == 0
        assert data["approved_by"] == "test_user"

    def test_deny_with_valid_token(self, client: TestClient, auth_headers: dict):
        """Test denial with valid token."""
        # First generate a token
        token_response = client.post(
            "/api/scheduler/approve/token/generate",
            headers=auth_headers,
            json={
                "task_ids": ["test-task-2"],
                "task_type": "schedule_change",
            },
        )
        token = token_response.json()["token"]

        # Then deny with that token
        response = client.post(
            "/api/scheduler/approve",
            headers=auth_headers,
            json={
                "token": token,
                "action": "deny",
                "approved_by": "test_user",
                "notes": "Not approved due to conflict",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "denied"
        assert data["approved_tasks"] == 0
        assert data["denied_tasks"] == 1

    def test_approve_specific_task(self, client: TestClient, auth_headers: dict):
        """Test approving a specific task from multi-task token."""
        # Generate token for multiple tasks
        token_response = client.post(
            "/api/scheduler/approve/token/generate",
            headers=auth_headers,
            json={
                "task_ids": ["task-1", "task-2", "task-3"],
                "task_type": "schedule_change",
            },
        )
        token = token_response.json()["token"]

        # Approve only task-2
        response = client.post(
            "/api/scheduler/approve",
            headers=auth_headers,
            json={
                "token": token,
                "task_id": "task-2",
                "action": "approve",
                "approved_by": "test_user",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["task_id"] == "task-2"
        assert data["approved_tasks"] == 1

    def test_approve_requires_authentication(self, client: TestClient):
        """Test that approve requires authentication."""
        response = client.post(
            "/api/scheduler/approve",
            json={
                "token": "some_token",
                "action": "approve",
                "approved_by": "test_user",
            },
        )
        assert response.status_code == 401


# Fixtures for testing
@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    """Get authentication headers for testing.

    This fixture should be implemented based on your auth setup.
    For now, it's a placeholder.
    """
    # In real tests, you would:
    # 1. Create a test user
    # 2. Login to get JWT token
    # 3. Return headers with Authorization: Bearer <token>

    # Placeholder - update based on your auth implementation
    return {
        "Authorization": "Bearer test_token_here",
        "Content-Type": "application/json",
    }


@pytest.fixture
def client(db_session) -> TestClient:
    """Create test client.

    This fixture should be implemented based on your test setup.
    """
    from app.main import app

    return TestClient(app)
