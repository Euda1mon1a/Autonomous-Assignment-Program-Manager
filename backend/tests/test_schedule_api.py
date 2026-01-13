"""
Tests for the Schedule API endpoints.

Tests schedule generation, validation, and retrieval.
"""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


class TestGenerateSchedule:
    """Tests for POST /api/schedule/generate endpoint."""

    def test_generate_schedule_success(
        self,
        client: TestClient,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """Should generate schedule for date range."""
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        payload = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "algorithm": "greedy",
        }

        response = client.post("/api/schedule/generate", json=payload)
        # Issue #5: Now returns 200 for success, 207 for partial, 422 for failure
        assert response.status_code in [200, 207]

        data = response.json()
        assert data["status"] in ["success", "partial"]
        # total_assignments replaces misleading total_blocks_assigned
        # (field stores assignment count, not block count)
        assert "total_assignments" in data
        assert "total_blocks" in data
        assert "validation" in data
        assert data["total_blocks"] > 0

    def test_generate_schedule_with_pgy_filter(
        self,
        client: TestClient,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """Should generate schedule only for specified PGY levels."""
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        payload = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "pgy_levels": [1, 2],  # Only PGY-1 and PGY-2
            "algorithm": "greedy",
        }

        response = client.post("/api/schedule/generate", json=payload)
        # Issue #5: Now returns 200 for success, 207 for partial, 422 for failure
        assert response.status_code in [200, 207]

        data = response.json()
        assert data["status"] in ["success", "partial"]

    def test_generate_schedule_no_residents(
        self,
        client: TestClient,
        sample_faculty_members: list[Person],
    ):
        """Should return failed status when no residents available."""
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        payload = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        response = client.post("/api/schedule/generate", json=payload)
        # Issue #5: Failed generation now returns 422 Unprocessable Entity
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data
        assert "no residents" in data["detail"].lower()

    def test_generate_schedule_invalid_date_range(self, client: TestClient):
        """Should handle invalid date range gracefully."""
        payload = {
            "start_date": "2024-12-31",
            "end_date": "2024-01-01",  # End before start
        }

        response = client.post("/api/schedule/generate", json=payload)
        # Should either return error or empty result
        assert response.status_code in [200, 400, 422]

    def test_generate_schedule_prevents_double_submit(
        self,
        client: TestClient,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
        sample_rotation_template: RotationTemplate,
        db: Session,
    ):
        """Should prevent concurrent schedule generation for overlapping date ranges."""
        from datetime import datetime

        from app.models.schedule_run import ScheduleRun

        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        # Create an "in_progress" run for the same date range
        in_progress_run = ScheduleRun(
            start_date=start_date,
            end_date=end_date,
            algorithm="greedy",
            status="in_progress",
            total_blocks_assigned=0,
            acgme_violations=0,
            runtime_seconds=0.0,
            config_json={},
            created_at=datetime.utcnow(),
        )
        db.add(in_progress_run)
        db.commit()

        payload = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "algorithm": "greedy",
        }

        # Issue #1: Should reject with 409 Conflict when generation in progress
        response = client.post("/api/schedule/generate", json=payload)
        assert response.status_code == 409
        assert "in progress" in response.json()["detail"].lower()


class TestValidateSchedule:
    """Tests for GET /api/schedule/validate endpoint."""

    def test_validate_schedule_empty(self, client: TestClient):
        """Should validate empty schedule (no violations)."""
        start_date = date.today().isoformat()
        end_date = (date.today() + timedelta(days=6)).isoformat()

        response = client.get(
            f"/api/schedule/validate?start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code == 200

        data = response.json()
        assert "valid" in data
        assert "violations" in data
        assert "total_violations" in data

    def test_validate_schedule_with_assignments(
        self,
        client: TestClient,
        sample_assignment: Assignment,
    ):
        """Should validate schedule with existing assignments."""
        start_date = date.today().isoformat()
        end_date = (date.today() + timedelta(days=6)).isoformat()

        response = client.get(
            f"/api/schedule/validate?start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code == 200

        data = response.json()
        assert "valid" in data
        assert "coverage_rate" in data
        assert isinstance(data["violations"], list)

    def test_validate_schedule_invalid_date_format(self, client: TestClient):
        """Should return 400 for invalid date format."""
        response = client.get(
            "/api/schedule/validate?start_date=invalid&end_date=2024-01-07"
        )
        assert response.status_code == 400
        assert "date" in response.json()["detail"].lower()

    @pytest.mark.acgme
    def test_validate_schedule_acgme_coverage_rate(
        self,
        client: TestClient,
        sample_blocks: list[Block],
        sample_residents: list[Person],
        db: Session,
    ):
        """Should calculate coverage rate correctly."""
        # Create assignments for half the weekday blocks
        from uuid import uuid4

        weekday_blocks = [b for b in sample_blocks if not b.is_weekend]
        for block in weekday_blocks[: len(weekday_blocks) // 2]:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_residents[0].id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        start_date = date.today().isoformat()
        end_date = (date.today() + timedelta(days=6)).isoformat()

        response = client.get(
            f"/api/schedule/validate?start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code == 200

        data = response.json()
        assert "coverage_rate" in data
        assert 0 <= data["coverage_rate"] <= 100


class TestGetSchedule:
    """Tests for GET /api/schedule/{start_date}/{end_date} endpoint."""

    def test_get_schedule_empty(self, client: TestClient):
        """Should return empty schedule when no assignments exist."""
        start_date = date.today().isoformat()
        end_date = (date.today() + timedelta(days=6)).isoformat()

        response = client.get(f"/api/schedule/{start_date}/{end_date}")
        assert response.status_code == 200

        data = response.json()
        assert "schedule" in data
        assert data["total_assignments"] == 0

    def test_get_schedule_with_assignments(
        self,
        client: TestClient,
        sample_assignment: Assignment,
        sample_block: Block,
    ):
        """Should return schedule with assignments."""
        start_date = sample_block.date.isoformat()
        end_date = (sample_block.date + timedelta(days=1)).isoformat()

        response = client.get(f"/api/schedule/{start_date}/{end_date}")
        assert response.status_code == 200

        data = response.json()
        assert data["total_assignments"] >= 1
        assert "schedule" in data

        # Check schedule structure
        date_key = sample_block.date.isoformat()
        if date_key in data["schedule"]:
            assert sample_block.time_of_day in data["schedule"][date_key]

    def test_get_schedule_invalid_date_format(self, client: TestClient):
        """Should return 400 for invalid date format."""
        response = client.get("/api/schedule/not-a-date/2024-01-07")
        assert response.status_code == 400

    def test_get_schedule_grouped_by_date(
        self,
        client: TestClient,
        sample_blocks: list[Block],
        sample_residents: list[Person],
        db: Session,
    ):
        """Should group assignments by date and time of day."""
        from uuid import uuid4

        # Create assignments for multiple blocks
        for block in sample_blocks[:4]:  # First 2 days
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_residents[0].id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        start_date = date.today().isoformat()
        end_date = (date.today() + timedelta(days=6)).isoformat()

        response = client.get(f"/api/schedule/{start_date}/{end_date}")
        assert response.status_code == 200

        data = response.json()
        schedule = data["schedule"]

        # Should have date keys
        for date_key in schedule:
            # Each date should have AM and PM keys
            assert "AM" in schedule[date_key] or "PM" in schedule[date_key]


class TestEmergencyCoverage:
    """Tests for POST /api/schedule/emergency-coverage endpoint."""

    def test_emergency_coverage_success(
        self,
        client: TestClient,
        sample_residents: list[Person],
        sample_assignment: Assignment,
    ):
        """Should handle emergency coverage request."""
        payload = {
            "person_id": str(sample_residents[0].id),
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=5)).isoformat(),
            "reason": "Family emergency",
            "is_deployment": False,
        }

        response = client.post("/api/schedule/emergency-coverage", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] in ["success", "partial", "failed"]
        assert "replacements_found" in data
        assert "coverage_gaps" in data
        assert "requires_manual_review" in data
        assert "details" in data

    def test_emergency_coverage_deployment(
        self,
        client: TestClient,
        sample_residents: list[Person],
    ):
        """Should handle military deployment emergency."""
        payload = {
            "person_id": str(sample_residents[0].id),
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=30)).isoformat(),
            "reason": "Military deployment",
            "is_deployment": True,
        }

        response = client.post("/api/schedule/emergency-coverage", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "status" in data

    def test_emergency_coverage_invalid_person(self, client: TestClient):
        """Should handle non-existent person gracefully."""
        fake_id = "00000000-0000-4000-8000-000000000000"
        payload = {
            "person_id": fake_id,
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=5)).isoformat(),
            "reason": "Test",
        }

        response = client.post("/api/schedule/emergency-coverage", json=payload)
        # Should either return 404 or handle gracefully
        assert response.status_code in [200, 404]
