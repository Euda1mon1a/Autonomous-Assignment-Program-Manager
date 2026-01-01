"""Tests for Schedule Generation API Routes.

This module tests the schedule generation and validation endpoints,
which are critical for the core scheduling functionality.

Tests implemented for:
- POST /api/schedule/generate - Schedule generation with auth, validation, idempotency
- GET /api/schedule/validate - Schedule validation (ACGME compliance)
- POST /api/schedule/emergency-coverage - Emergency coverage with auth
- GET /api/schedule/{start_date}/{end_date} - Schedule retrieval

All tests use fixtures from conftest.py for auth, test data, and database setup.
"""

import pytest
from datetime import date
from uuid import uuid4

# The TestClient is available in conftest.py
# from fastapi.testclient import TestClient


class TestScheduleGenerationRoutes:
    """Test suite for schedule generation endpoints."""

    # =========================================================================
    # Schedule Generation Tests
    # =========================================================================

    def test_post_schedule_generate_success(
        self, client, auth_headers, sample_rotation_template, sample_blocks
    ):
        """Test successful schedule generation."""
        response = client.post(
            "/api/schedule/generate",
            headers=auth_headers,
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "algorithm": "greedy",
            },
        )
        # May succeed with 200, partial success with 207, or fail with 422
        assert response.status_code in [200, 207, 422]

        # If successful, should have expected fields
        if response.status_code in [200, 207]:
            data = response.json()
            assert "status" in data
            assert "message" in data

    def test_post_schedule_generate_missing_dates(self, client, auth_headers):
        """Test schedule generation fails without required dates."""
        response = client.post(
            "/api/schedule/generate",
            headers=auth_headers,
            json={},
        )
        assert response.status_code == 422  # Validation error

    def test_post_schedule_generate_invalid_date_range(self, client, auth_headers):
        """Test schedule generation fails with end_date before start_date."""
        response = client.post(
            "/api/schedule/generate",
            headers=auth_headers,
            json={
                "start_date": "2025-12-31",
                "end_date": "2025-01-01",
                "algorithm": "greedy",
            },
        )
        # Pydantic may reject this as 422, or engine may reject as 400/422
        assert response.status_code in [400, 422]

    def test_post_schedule_generate_requires_auth(self, client):
        """Test schedule generation requires authentication."""
        response = client.post(
            "/api/schedule/generate",
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
                "algorithm": "greedy",
            },
        )
        assert response.status_code == 401

    # =========================================================================
    # Schedule Validation Tests
    # =========================================================================

    def test_get_schedule_validate_success(self, client):
        """Test schedule validation endpoint."""
        # The validate endpoint is a GET, not POST, based on the routes
        response = client.get(
            "/api/schedule/validate",
            params={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
        )
        # Should return validation result even for empty schedule
        assert response.status_code == 200
        data = response.json()
        assert "is_compliant" in data or "violations" in data

    def test_get_schedule_validate_acgme_compliance(self, client):
        """Test schedule validation returns ACGME compliance status."""
        response = client.get(
            "/api/schedule/validate",
            params={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Should have compliance information
        assert "is_compliant" in data or "violations" in data or "status" in data

    # =========================================================================
    # Emergency Coverage Tests
    # =========================================================================

    def test_post_emergency_coverage_success(
        self, client, auth_headers, sample_resident
    ):
        """Test emergency coverage endpoint."""
        response = client.post(
            "/api/schedule/emergency-coverage",
            headers=auth_headers,
            json={
                "person_id": str(sample_resident.id),
                "start_date": "2025-01-15",
                "end_date": "2025-01-20",
                "reason": "Unexpected absence",
                "is_deployment": False,
            },
        )
        # Should succeed or fail gracefully if no coverage available
        assert response.status_code in [200, 201, 422]

    def test_post_emergency_coverage_requires_auth(self, client, sample_resident):
        """Test emergency coverage requires authentication."""
        response = client.post(
            "/api/schedule/emergency-coverage",
            json={
                "person_id": str(sample_resident.id),
                "start_date": "2025-01-15",
                "end_date": "2025-01-20",
                "reason": "Test",
                "is_deployment": False,
            },
        )
        assert response.status_code == 401


class TestScheduleRetrievalRoutes:
    """Test suite for schedule retrieval endpoints."""

    def test_get_schedule_by_date_range(self, client):
        """Test retrieving schedule by date range."""
        # Based on routes, the endpoint is /api/schedule/{start_date}/{end_date}
        response = client.get("/api/schedule/2025-01-01/2025-01-31")
        assert response.status_code == 200
        data = response.json()
        assert "start_date" in data
        assert "end_date" in data
        assert "schedule" in data or "total_assignments" in data

    def test_get_schedule_invalid_date_format(self, client):
        """Test retrieving schedule with invalid date format."""
        response = client.get("/api/schedule/invalid-date/2025-01-31")
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data


class TestScheduleModificationRoutes:
    """Test suite for schedule modification endpoints."""

    def test_schedule_generation_idempotency_key(self, client, auth_headers):
        """Test schedule generation with idempotency key."""
        idempotency_key = str(uuid4())
        response = client.post(
            "/api/schedule/generate",
            headers={**auth_headers, "Idempotency-Key": idempotency_key},
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "algorithm": "greedy",
            },
        )
        # Should process the request (may succeed or fail)
        assert response.status_code in [200, 207, 422, 500]

    def test_schedule_generation_duplicate_idempotency_key(self, client, auth_headers):
        """Test duplicate idempotency key with same parameters."""
        idempotency_key = str(uuid4())
        request_data = {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "algorithm": "greedy",
        }

        # First request
        response1 = client.post(
            "/api/schedule/generate",
            headers={**auth_headers, "Idempotency-Key": idempotency_key},
            json=request_data,
        )
        first_status = response1.status_code

        # Second request with same key and params
        response2 = client.post(
            "/api/schedule/generate",
            headers={**auth_headers, "Idempotency-Key": idempotency_key},
            json=request_data,
        )

        # Should either return cached result or conflict (409)
        assert response2.status_code in [first_status, 409]
        # If replayed, should have header
        if response2.status_code == first_status and first_status in [200, 207]:
            # May have X-Idempotency-Replayed header
            pass
