"""Tests for swap API routes."""
import pytest
from datetime import date, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient


class TestSwapExecuteEndpoint:
    """Tests for POST /api/swaps/execute endpoint."""

    def test_execute_swap_success(self, client: TestClient, auth_headers: dict, sample_faculty_members):
        """Test successful swap execution."""
        source = sample_faculty_members[0]
        target = sample_faculty_members[1]

        response = client.post(
            "/api/swaps/execute",
            json={
                "source_faculty_id": str(source.id),
                "source_week": (date.today() + timedelta(days=30)).isoformat(),
                "target_faculty_id": str(target.id),
                "target_week": (date.today() + timedelta(days=37)).isoformat(),
                "swap_type": "one_to_one",
                "reason": "Vacation conflict",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "validation" in data

    def test_execute_swap_unauthorized(self, client: TestClient, sample_faculty_members):
        """Test swap execution requires authentication."""
        source = sample_faculty_members[0]
        target = sample_faculty_members[1]

        response = client.post(
            "/api/swaps/execute",
            json={
                "source_faculty_id": str(source.id),
                "source_week": (date.today() + timedelta(days=30)).isoformat(),
                "target_faculty_id": str(target.id),
                "swap_type": "absorb",
            },
        )

        assert response.status_code == 401

    def test_execute_swap_invalid_faculty(self, client: TestClient, auth_headers: dict):
        """Test swap with non-existent faculty."""
        response = client.post(
            "/api/swaps/execute",
            json={
                "source_faculty_id": str(uuid4()),
                "source_week": (date.today() + timedelta(days=30)).isoformat(),
                "target_faculty_id": str(uuid4()),
                "swap_type": "absorb",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["validation"]["valid"] is False

    def test_execute_swap_past_date(self, client: TestClient, auth_headers: dict, sample_faculty_members):
        """Test swap with past date fails validation."""
        source = sample_faculty_members[0]
        target = sample_faculty_members[1]

        response = client.post(
            "/api/swaps/execute",
            json={
                "source_faculty_id": str(source.id),
                "source_week": (date.today() - timedelta(days=7)).isoformat(),
                "target_faculty_id": str(target.id),
                "swap_type": "absorb",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "PAST_DATE" in str(data["validation"]["errors"])


class TestSwapValidateEndpoint:
    """Tests for POST /api/swaps/validate endpoint."""

    def test_validate_swap_valid(self, client: TestClient, auth_headers: dict, sample_faculty_members):
        """Test validating a valid swap."""
        source = sample_faculty_members[0]
        target = sample_faculty_members[1]

        response = client.post(
            "/api/swaps/validate",
            json={
                "source_faculty_id": str(source.id),
                "source_week": (date.today() + timedelta(days=30)).isoformat(),
                "target_faculty_id": str(target.id),
                "swap_type": "absorb",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert "errors" in data
        assert "warnings" in data

    def test_validate_swap_with_conflict(self, client: TestClient, auth_headers: dict, sample_faculty_members, db):
        """Test validation detects external conflicts."""
        from app.models.absence import Absence

        source = sample_faculty_members[0]
        target = sample_faculty_members[1]
        swap_week = date.today() + timedelta(days=30)

        # Create blocking absence for target
        absence = Absence(
            id=uuid4(),
            person_id=target.id,
            start_date=swap_week,
            end_date=swap_week + timedelta(days=4),
            absence_type="deployment",
            is_blocking=True,
        )
        db.add(absence)
        db.commit()

        response = client.post(
            "/api/swaps/validate",
            json={
                "source_faculty_id": str(source.id),
                "source_week": swap_week.isoformat(),
                "target_faculty_id": str(target.id),
                "swap_type": "absorb",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["external_conflict"] is not None


class TestSwapHistoryEndpoint:
    """Tests for GET /api/swaps/history endpoint."""

    def test_get_history_empty(self, client: TestClient, auth_headers: dict):
        """Test getting empty swap history."""
        response = client.get(
            "/api/swaps/history",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    def test_get_history_with_filters(self, client: TestClient, auth_headers: dict, sample_faculty):
        """Test history with filter parameters."""
        response = client.get(
            "/api/swaps/history",
            params={
                "faculty_id": str(sample_faculty.id),
                "status": "pending",
                "page": 1,
                "page_size": 10,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_get_history_unauthorized(self, client: TestClient):
        """Test history requires authentication."""
        response = client.get("/api/swaps/history")
        assert response.status_code == 401


class TestSwapRollbackEndpoint:
    """Tests for POST /api/swaps/{swap_id}/rollback endpoint."""

    def test_rollback_not_found(self, client: TestClient, auth_headers: dict):
        """Test rollback of non-existent swap."""
        response = client.post(
            f"/api/swaps/{uuid4()}/rollback",
            json={"reason": "Test rollback reason for testing purposes"},
            headers=auth_headers,
        )

        assert response.status_code == 400

    def test_rollback_reason_required(self, client: TestClient, auth_headers: dict):
        """Test rollback requires reason with minimum length."""
        response = client.post(
            f"/api/swaps/{uuid4()}/rollback",
            json={"reason": "short"},  # Too short
            headers=auth_headers,
        )

        assert response.status_code == 422  # Validation error


class TestSwapGetEndpoint:
    """Tests for GET /api/swaps/{swap_id} endpoint."""

    def test_get_swap_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent swap."""
        response = client.get(
            f"/api/swaps/{uuid4()}",
            headers=auth_headers,
        )

        assert response.status_code == 404
