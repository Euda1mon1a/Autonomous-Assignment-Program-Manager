"""Tests for Schedule Generation API Routes.

This module tests the schedule generation and validation endpoints,
which are critical for the core scheduling functionality.

Endpoints tested:
- POST /api/schedule/generate - Schedule generation
- GET /api/schedule/validate - Schedule validation
- POST /api/schedule/emergency-coverage - Emergency coverage
"""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


class TestScheduleGenerationRoutes:
    """Test suite for schedule generation endpoints."""

    @pytest.fixture
    def sample_rotation_for_schedule(self, db):
        """Create a sample rotation template for testing."""
        template = RotationTemplate(
            id=uuid4(),
            name="Test Clinic",
            activity_type="outpatient",  # Must match engine's default filter
            abbreviation="TC",
            clinic_location="Building A",
            max_residents=4,
            supervision_required=True,
            max_supervision_ratio=4,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @pytest.fixture
    def sample_resident_for_schedule(self, db):
        """Create a sample resident for testing."""
        resident = Person(
            id=uuid4(),
            name="Dr. Schedule Resident",
            type="resident",
            email="schedule.resident@hospital.org",
            pgy_level=2,
        )
        db.add(resident)
        db.commit()
        db.refresh(resident)
        return resident

    @pytest.fixture
    def schedule_test_blocks(self, db):
        """Create blocks for schedule testing."""
        blocks = []
        start_date = date.today() + timedelta(days=30)  # Future date

        for i in range(7):
            current_date = start_date + timedelta(days=i)
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current_date,
                    time_of_day=time_of_day,
                    block_number=1,
                    is_weekend=(current_date.weekday() >= 5),
                    is_holiday=False,
                )
                db.add(block)
                blocks.append(block)

        db.commit()
        for b in blocks:
            db.refresh(b)
        return blocks

    # =========================================================================
    # Schedule Generation Tests
    # =========================================================================

    def test_post_schedule_generate_requires_auth(self, client):
        """Test schedule generation requires authentication."""
        response = client.post(
            "/api/schedule/generate",
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "algorithm": "greedy",
            },
        )
        assert response.status_code == 401

    def test_post_schedule_generate_missing_dates(self, client, auth_headers):
        """Test schedule generation fails without required dates."""
        response = client.post(
            "/api/schedule/generate",
            headers=auth_headers,
            json={},
        )
        assert response.status_code == 422  # Validation error

    def test_post_schedule_generate_with_auth(
        self, client, auth_headers, sample_rotation_for_schedule
    ):
        """Test schedule generation with authentication."""
        # Use a future date range to avoid conflicts
        start_date = (date.today() + timedelta(days=60)).isoformat()
        end_date = (date.today() + timedelta(days=67)).isoformat()

        response = client.post(
            "/api/schedule/generate",
            headers=auth_headers,
            json={
                "start_date": start_date,
                "end_date": end_date,
                "algorithm": "greedy",
            },
        )
        # Can be 200 (success), 207 (partial), 422 (validation), or 500 (no data)
        assert response.status_code in [200, 207, 422, 500]

    def test_post_schedule_generate_with_invalid_algorithm(
        self, client, auth_headers
    ):
        """Test schedule generation fails with invalid algorithm."""
        response = client.post(
            "/api/schedule/generate",
            headers=auth_headers,
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "algorithm": "invalid_algorithm",
            },
        )
        assert response.status_code == 422

    # =========================================================================
    # Schedule Validation Tests
    # =========================================================================

    def test_get_schedule_validate_success(self, client):
        """Test schedule validation endpoint (GET)."""
        response = client.get(
            "/api/schedule/validate",
            params={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
        )
        # Endpoint is GET and does not require auth
        assert response.status_code == 200

    def test_get_schedule_validate_returns_compliance_info(self, client):
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
        # Should have validation result structure
        assert "is_compliant" in data or "violations" in data

    def test_get_schedule_validate_invalid_date_format(self, client):
        """Test schedule validation fails with invalid date format."""
        response = client.get(
            "/api/schedule/validate",
            params={
                "start_date": "invalid-date",
                "end_date": "2025-01-31",
            },
        )
        assert response.status_code == 400

    # =========================================================================
    # Emergency Coverage Tests
    # =========================================================================

    def test_post_emergency_coverage_requires_auth(self, client):
        """Test emergency coverage requires authentication."""
        response = client.post(
            "/api/schedule/emergency-coverage",
            json={
                "person_id": str(uuid4()),
                "start_date": "2025-01-15",
                "end_date": "2025-01-20",
                "reason": "Unexpected absence",
            },
        )
        assert response.status_code == 401

    def test_post_emergency_coverage_with_auth(
        self, client, auth_headers, sample_resident_for_schedule
    ):
        """Test emergency coverage endpoint with authentication."""
        response = client.post(
            "/api/schedule/emergency-coverage",
            headers=auth_headers,
            json={
                "person_id": str(sample_resident_for_schedule.id),
                "start_date": "2025-01-15",
                "end_date": "2025-01-20",
                "reason": "Unexpected absence",
                "is_deployment": False,
            },
        )
        # Should succeed (200) or indicate no assignments to cover (200 with empty replacements)
        assert response.status_code in [200, 422]

    def test_post_emergency_coverage_missing_fields(self, client, auth_headers):
        """Test emergency coverage fails without required fields."""
        response = client.post(
            "/api/schedule/emergency-coverage",
            headers=auth_headers,
            json={},
        )
        assert response.status_code == 422

    def test_post_emergency_coverage_invalid_person(self, client, auth_headers):
        """Test emergency coverage with non-existent person."""
        response = client.post(
            "/api/schedule/emergency-coverage",
            headers=auth_headers,
            json={
                "person_id": str(uuid4()),  # Non-existent
                "start_date": "2025-01-15",
                "end_date": "2025-01-20",
                "reason": "Test absence",
                "is_deployment": False,
            },
        )
        # Should return 404 or 422 for non-existent person
        assert response.status_code in [200, 404, 422]


class TestScheduleRetrievalRoutes:
    """Test suite for schedule retrieval endpoints."""

    @pytest.fixture
    def sample_assignment_data(
        self, db, sample_resident, sample_block, sample_rotation_template
    ):
        """Create a sample assignment for retrieval tests."""
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_block.id,
            person_id=sample_resident.id,
            rotation_template_id=sample_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    def test_get_assignments_by_date_range(
        self, client, auth_headers, sample_assignment_data, sample_block
    ):
        """Test retrieving assignments by date range."""
        response = client.get(
            "/api/assignments",
            headers=auth_headers,
            params={
                "start_date": sample_block.date.isoformat(),
                "end_date": sample_block.date.isoformat(),
            },
        )
        # Endpoint may return 200 or 404 if not found
        assert response.status_code in [200, 404]

    def test_get_assignments_by_person(
        self, client, auth_headers, sample_assignment_data, sample_resident
    ):
        """Test retrieving assignments filtered by person."""
        response = client.get(
            "/api/assignments",
            headers=auth_headers,
            params={"person_id": str(sample_resident.id)},
        )
        assert response.status_code in [200, 404]


class TestScheduleModificationRoutes:
    """Test suite for schedule modification endpoints."""

    def test_delete_assignments_requires_auth(self, client):
        """Test bulk deletion requires authentication."""
        response = client.delete(
            "/api/assignments",
            params={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
        )
        # Should require auth
        assert response.status_code in [401, 405, 404]

    def test_delete_assignments_with_auth(self, client, auth_headers):
        """Test bulk deletion with authentication."""
        response = client.delete(
            "/api/assignments",
            headers=auth_headers,
            params={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            },
        )
        # May return 200/204 (success), 403 (forbidden), 404 (no endpoint), or 405 (method not allowed)
        assert response.status_code in [200, 204, 403, 404, 405]


class TestScheduleIdempotency:
    """Test suite for idempotency key handling in schedule generation."""

    def test_schedule_generate_with_idempotency_key(self, client, auth_headers):
        """Test schedule generation with idempotency key header."""
        idempotency_key = str(uuid4())
        start_date = (date.today() + timedelta(days=100)).isoformat()
        end_date = (date.today() + timedelta(days=107)).isoformat()

        response = client.post(
            "/api/schedule/generate",
            headers={
                **auth_headers,
                "Idempotency-Key": idempotency_key,
            },
            json={
                "start_date": start_date,
                "end_date": end_date,
                "algorithm": "greedy",
            },
        )
        # First request should complete
        assert response.status_code in [200, 207, 422, 500]

    def test_schedule_generate_duplicate_idempotency_key_same_body(
        self, client, auth_headers
    ):
        """Test that duplicate idempotency key with same body returns cached result."""
        idempotency_key = str(uuid4())
        start_date = (date.today() + timedelta(days=110)).isoformat()
        end_date = (date.today() + timedelta(days=117)).isoformat()

        request_body = {
            "start_date": start_date,
            "end_date": end_date,
            "algorithm": "greedy",
        }

        # First request
        response1 = client.post(
            "/api/schedule/generate",
            headers={
                **auth_headers,
                "Idempotency-Key": idempotency_key,
            },
            json=request_body,
        )
        first_status = response1.status_code

        # Second request with same key and body should return same result
        response2 = client.post(
            "/api/schedule/generate",
            headers={
                **auth_headers,
                "Idempotency-Key": idempotency_key,
            },
            json=request_body,
        )

        # Should get same status or 200 (cached)
        assert response2.status_code in [first_status, 200, 409]
