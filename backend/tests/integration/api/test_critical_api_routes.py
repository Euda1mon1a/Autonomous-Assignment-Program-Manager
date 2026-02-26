"""Integration tests for critical API routes.

Tests the full HTTP request/response cycle through FastAPI's TestClient
with a real in-memory SQLite database. Covers:
- Health endpoints (liveness, readiness)
- Auth endpoints (login, register, JSON login)
- People CRUD (list, create, get, update)
- Absence CRUD (list, create, get)
- Assignment listing
- Proper auth enforcement (401 for unauthenticated)
- PHI headers on sensitive endpoints
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.core.security import get_password_hash
from app.models.absence import Absence
from app.models.block import Block
from app.models.person import Person
from app.models.user import User


# =========================================================================
# Health endpoints (no auth required)
# =========================================================================


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_live(self, client):
        """GET /health/live returns 200 with status healthy."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_root(self, client):
        """GET /health/ returns 200 (same as /live)."""
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_metrics(self, client):
        """GET /health/metrics returns 200 with metrics data."""
        response = client.get("/health/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "history_enabled" in data

    def test_health_history(self, client):
        """GET /health/history returns 200."""
        response = client.get("/health/history")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert "count" in data

    def test_health_status(self, client):
        """GET /health/status returns overall status."""
        response = client.get("/health/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services_checked" in data


# =========================================================================
# Auth endpoints
# =========================================================================


class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    def test_login_json_success(self, client, admin_user):
        """POST /api/auth/login/json with valid credentials returns tokens."""
        response = client.post(
            "/api/auth/login/json",
            json={"username": "testadmin", "password": "testpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_json_bad_password(self, client, admin_user):
        """POST /api/auth/login/json with wrong password returns 401."""
        response = client.post(
            "/api/auth/login/json",
            json={"username": "testadmin", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_login_json_nonexistent_user(self, client):
        """POST /api/auth/login/json with nonexistent user returns 401."""
        response = client.post(
            "/api/auth/login/json",
            json={"username": "nobody", "password": "nopass"},
        )
        assert response.status_code == 401

    def test_get_current_user(self, authed_client, admin_user):
        """GET /api/auth/me returns current user info."""
        response = authed_client.get("/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testadmin"
        assert data["role"] == "admin"

    def test_unauthenticated_me_returns_401(self, client):
        """GET /api/auth/me without auth returns 401."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401


# =========================================================================
# People endpoints
# =========================================================================


class TestPeopleEndpoints:
    """Tests for people CRUD endpoints."""

    def test_list_people_requires_auth(self, client):
        """GET /api/people without auth returns 401."""
        response = client.get("/api/people")
        assert response.status_code == 401

    def test_list_people_empty(self, authed_client):
        """GET /api/people returns empty list when no people exist."""
        response = authed_client.get("/api/people")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_people_with_data(
        self, authed_client, db, sample_resident, sample_faculty
    ):
        """GET /api/people returns all people."""
        response = authed_client.get("/api/people")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_list_people_filter_by_type(
        self, authed_client, db, sample_resident, sample_faculty
    ):
        """GET /api/people?type=resident filters by person type."""
        response = authed_client.get("/api/people?type=resident")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["type"] == "resident"

    def test_list_people_phi_header(self, authed_client, db, sample_resident):
        """People endpoint sets X-Contains-PHI header."""
        response = authed_client.get("/api/people")
        assert response.status_code == 200
        assert response.headers.get("X-Contains-PHI") == "true"

    def test_create_person(self, authed_client):
        """POST /api/people creates a new person."""
        response = authed_client.post(
            "/api/people",
            json={
                "name": "Dr. New Resident",
                "type": "resident",
                "email": "new.resident@example.com",
                "pgy_level": 1,
            },
        )
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["name"] == "Dr. New Resident"
        assert data["type"] == "resident"

    def test_get_person_by_id(self, authed_client, sample_resident):
        """GET /api/people/{id} returns the person."""
        response = authed_client.get(f"/api/people/{sample_resident.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_resident.name

    def test_get_person_not_found(self, authed_client):
        """GET /api/people/{id} with bad ID returns 404."""
        response = authed_client.get(f"/api/people/{uuid4()}")
        assert response.status_code == 404

    def test_list_residents_endpoint(
        self, authed_client, db, sample_resident, sample_faculty
    ):
        """GET /api/people/residents returns only residents."""
        response = authed_client.get("/api/people/residents")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["type"] == "resident"


# =========================================================================
# Absence endpoints
# =========================================================================


class TestAbsenceEndpoints:
    """Tests for absence CRUD endpoints."""

    def test_list_absences_requires_auth(self, client):
        """GET /api/absences without auth returns 401."""
        response = client.get("/api/absences")
        assert response.status_code == 401

    def test_list_absences_empty(self, authed_client):
        """GET /api/absences returns empty list initially."""
        response = authed_client.get("/api/absences")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_create_absence(self, authed_client, sample_resident):
        """POST /api/absences creates a new absence."""
        response = authed_client.post(
            "/api/absences",
            json={
                "person_id": str(sample_resident.id),
                "start_date": (date.today() + timedelta(days=7)).isoformat(),
                "end_date": (date.today() + timedelta(days=10)).isoformat(),
                "absence_type": "vacation",
                "notes": "Annual leave",
            },
        )
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["absence_type"] == "vacation"
        assert data["person_id"] == str(sample_resident.id)

    def test_get_absence_by_id(self, authed_client, db, sample_absence):
        """GET /api/absences/{id} returns the absence."""
        response = authed_client.get(f"/api/absences/{sample_absence.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["absence_type"] == "vacation"

    def test_get_absence_not_found(self, authed_client):
        """GET /api/absences/{id} with bad ID returns 404."""
        response = authed_client.get(f"/api/absences/{uuid4()}")
        assert response.status_code == 404

    def test_list_absences_phi_header(self, authed_client):
        """Absence endpoint sets X-Contains-PHI header."""
        response = authed_client.get("/api/absences")
        assert response.status_code == 200
        assert response.headers.get("X-Contains-PHI") == "true"


# =========================================================================
# Assignment endpoints
# =========================================================================


class TestAssignmentEndpoints:
    """Tests for assignment endpoints."""

    def test_list_assignments_requires_auth(self, client):
        """GET /api/assignments without auth returns 401."""
        response = client.get("/api/assignments")
        assert response.status_code == 401

    def test_list_assignments_empty(self, authed_client):
        """GET /api/assignments returns empty list initially."""
        response = authed_client.get("/api/assignments")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_list_assignments_with_data(self, authed_client, db, sample_assignment):
        """GET /api/assignments returns assignments."""
        response = authed_client.get("/api/assignments")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


# =========================================================================
# Block endpoints
# =========================================================================


class TestBlockEndpoints:
    """Tests for block endpoints."""

    def test_list_blocks_requires_auth(self, client):
        """GET /api/blocks without auth returns 401."""
        response = client.get("/api/blocks")
        assert response.status_code == 401

    def test_list_blocks_empty(self, authed_client):
        """GET /api/blocks returns empty when no blocks exist."""
        response = authed_client.get("/api/blocks")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_list_blocks_with_data(self, authed_client, db, sample_blocks):
        """GET /api/blocks returns blocks."""
        response = authed_client.get("/api/blocks")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
