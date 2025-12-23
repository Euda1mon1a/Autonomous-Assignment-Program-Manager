"""Tests for daily manifest API routes.

Tests the "Where is everyone NOW" functionality used by clinic staff
to see current staffing at each location.
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


class TestDailyManifest:
    """Test suite for daily manifest endpoint."""

    # ========================================================================
    # Authentication Tests
    # ========================================================================

    def test_daily_manifest_requires_auth(self, client: TestClient):
        """Test that daily manifest endpoint requires authentication."""
        response = client.get("/api/assignments/daily-manifest?date=2025-01-15")
        assert response.status_code == 401

    def test_daily_manifest_with_auth(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test that authenticated users can access daily manifest."""
        response = client.get(
            "/api/assignments/daily-manifest?date=2025-01-15",
            headers=auth_headers,
        )
        assert response.status_code == 200

    # ========================================================================
    # Parameter Validation Tests
    # ========================================================================

    def test_daily_manifest_requires_date_param(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that date parameter is required."""
        response = client.get(
            "/api/assignments/daily-manifest",
            headers=auth_headers,
        )
        assert response.status_code == 422  # Validation error

    def test_daily_manifest_invalid_time_of_day(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that invalid time_of_day values are rejected."""
        response = client.get(
            "/api/assignments/daily-manifest?date=2025-01-15&time_of_day=INVALID",
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "AM" in response.json()["detail"] or "PM" in response.json()["detail"]

    def test_daily_manifest_valid_time_of_day_am(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that AM is a valid time_of_day value."""
        response = client.get(
            "/api/assignments/daily-manifest?date=2025-01-15&time_of_day=AM",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["time_of_day"] == "AM"

    def test_daily_manifest_valid_time_of_day_pm(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that PM is a valid time_of_day value."""
        response = client.get(
            "/api/assignments/daily-manifest?date=2025-01-15&time_of_day=PM",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["time_of_day"] == "PM"

    # ========================================================================
    # Empty Response Tests
    # ========================================================================

    def test_daily_manifest_empty_for_no_assignments(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that empty manifest is returned when no assignments exist."""
        response = client.get(
            "/api/assignments/daily-manifest?date=2025-01-15",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == "2025-01-15"
        assert data["locations"] == []
        assert "generated_at" in data

    # ========================================================================
    # Assignment Display Tests
    # ========================================================================

    def test_daily_manifest_shows_assignments(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_resident: Person,
    ):
        """Test that assignments are returned in manifest."""
        # Create a block and assignment
        test_date = date(2025, 1, 15)
        block = Block(
            id=uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.flush()

        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=sample_resident.id,
            role="primary",
            activity_name="Morning Clinic",
        )
        db.add(assignment)
        db.commit()

        response = client.get(
            f"/api/assignments/daily-manifest?date={test_date.isoformat()}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Should have at least one location
        assert len(data["locations"]) >= 1

        # Find the location with our assignment
        found_assignment = False
        for location in data["locations"]:
            for time_slot, assignments in location["time_slots"].items():
                for assignment_data in assignments:
                    if assignment_data["person"]["name"] == sample_resident.name:
                        found_assignment = True
                        assert assignment_data["role"] == "primary"
                        assert assignment_data["activity"] == "Morning Clinic"
                        assert assignment_data["person"]["pgy_level"] == 2
        assert found_assignment, "Expected to find resident assignment in manifest"

    def test_daily_manifest_groups_by_location(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
    ):
        """Test that assignments are grouped by clinic location."""
        test_date = date(2025, 1, 15)

        # Create rotation templates with different locations
        template_a = RotationTemplate(
            id=uuid4(),
            name="Clinic A",
            activity_type="clinic",
            abbreviation="CA",
            clinic_location="Building A",
        )
        template_b = RotationTemplate(
            id=uuid4(),
            name="Clinic B",
            activity_type="clinic",
            abbreviation="CB",
            clinic_location="Building B",
        )
        db.add(template_a)
        db.add(template_b)
        db.flush()

        # Create blocks
        block = Block(
            id=uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.flush()

        # Assign residents to different locations
        assignment_a = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=sample_residents[0].id,
            role="primary",
            rotation_template_id=template_a.id,
        )
        assignment_b = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=sample_residents[1].id,
            role="primary",
            rotation_template_id=template_b.id,
        )
        db.add(assignment_a)
        db.add(assignment_b)
        db.commit()

        response = client.get(
            f"/api/assignments/daily-manifest?date={test_date.isoformat()}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Should have two locations
        location_names = [loc["clinic_location"] for loc in data["locations"]]
        assert "Building A" in location_names
        assert "Building B" in location_names

    def test_daily_manifest_filters_by_time(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
    ):
        """Test that time_of_day filter works correctly."""
        test_date = date(2025, 1, 15)

        # Create AM and PM blocks
        block_am = Block(
            id=uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=1,
        )
        block_pm = Block(
            id=uuid4(),
            date=test_date,
            time_of_day="PM",
            block_number=1,
        )
        db.add(block_am)
        db.add(block_pm)
        db.flush()

        # Create assignments for both time slots
        assignment_am = Assignment(
            id=uuid4(),
            block_id=block_am.id,
            person_id=sample_residents[0].id,
            role="primary",
            activity_name="AM Activity",
        )
        assignment_pm = Assignment(
            id=uuid4(),
            block_id=block_pm.id,
            person_id=sample_residents[1].id,
            role="primary",
            activity_name="PM Activity",
        )
        db.add(assignment_am)
        db.add(assignment_pm)
        db.commit()

        # Query AM only
        response_am = client.get(
            f"/api/assignments/daily-manifest?date={test_date.isoformat()}&time_of_day=AM",
            headers=auth_headers,
        )
        assert response_am.status_code == 200
        data_am = response_am.json()

        # Check only AM assignments returned
        found_am = False
        found_pm = False
        for location in data_am["locations"]:
            for time_slot, assignments in location["time_slots"].items():
                for assignment_data in assignments:
                    if assignment_data["activity"] == "AM Activity":
                        found_am = True
                    if assignment_data["activity"] == "PM Activity":
                        found_pm = True
        assert found_am, "Expected AM assignment in AM-filtered response"
        assert not found_pm, "Did not expect PM assignment in AM-filtered response"

    # ========================================================================
    # Staffing Summary Tests
    # ========================================================================

    def test_daily_manifest_staffing_summary(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
        sample_faculty: Person,
    ):
        """Test that staffing summary correctly counts residents and faculty."""
        test_date = date(2025, 1, 15)

        # Create rotation template
        template = RotationTemplate(
            id=uuid4(),
            name="Mixed Clinic",
            activity_type="clinic",
            abbreviation="MC",
            clinic_location="Main Clinic",
        )
        db.add(template)
        db.flush()

        # Create block
        block = Block(
            id=uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.flush()

        # Assign 2 residents and 1 faculty
        for i, resident in enumerate(sample_residents[:2]):
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=resident.id,
                role="primary",
                rotation_template_id=template.id,
            )
            db.add(assignment)

        faculty_assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=sample_faculty.id,
            role="supervising",
            rotation_template_id=template.id,
        )
        db.add(faculty_assignment)
        db.commit()

        response = client.get(
            f"/api/assignments/daily-manifest?date={test_date.isoformat()}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Find Main Clinic location
        main_clinic = next(
            (loc for loc in data["locations"] if loc["clinic_location"] == "Main Clinic"),
            None,
        )
        assert main_clinic is not None

        # Check staffing summary
        assert main_clinic["staffing_summary"]["total"] == 3
        assert main_clinic["staffing_summary"]["residents"] == 2
        assert main_clinic["staffing_summary"]["faculty"] == 1

    # ========================================================================
    # Response Format Tests
    # ========================================================================

    def test_daily_manifest_response_format(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that response has correct format."""
        response = client.get(
            "/api/assignments/daily-manifest?date=2025-01-15",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "date" in data
        assert "time_of_day" in data
        assert "locations" in data
        assert "generated_at" in data

        # date should be ISO format
        assert data["date"] == "2025-01-15"

        # locations should be a list
        assert isinstance(data["locations"], list)

    def test_daily_manifest_location_format(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_resident: Person,
    ):
        """Test that location objects have correct format."""
        test_date = date(2025, 1, 15)

        # Create block and assignment
        block = Block(
            id=uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.flush()

        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=sample_resident.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        response = client.get(
            f"/api/assignments/daily-manifest?date={test_date.isoformat()}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Should have at least one location
        assert len(data["locations"]) >= 1

        location = data["locations"][0]
        assert "clinic_location" in location
        assert "time_slots" in location
        assert "staffing_summary" in location

        # time_slots should be dict with AM/PM keys
        assert isinstance(location["time_slots"], dict)

        # staffing_summary should have counts
        summary = location["staffing_summary"]
        assert "total" in summary
        assert "residents" in summary
        assert "faculty" in summary

    # ========================================================================
    # Edge Cases
    # ========================================================================

    def test_daily_manifest_unassigned_location(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_resident: Person,
    ):
        """Test that assignments without rotation templates show as Unassigned."""
        test_date = date(2025, 1, 15)

        # Create block and assignment without rotation template
        block = Block(
            id=uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.flush()

        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=sample_resident.id,
            role="primary",
            rotation_template_id=None,  # No template
        )
        db.add(assignment)
        db.commit()

        response = client.get(
            f"/api/assignments/daily-manifest?date={test_date.isoformat()}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Should have "Unassigned" location
        location_names = [loc["clinic_location"] for loc in data["locations"]]
        assert "Unassigned" in location_names

    def test_daily_manifest_sorts_locations(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
    ):
        """Test that locations are sorted alphabetically with Unassigned last."""
        test_date = date(2025, 1, 15)

        # Create templates with different locations
        template_z = RotationTemplate(
            id=uuid4(),
            name="Z Clinic",
            activity_type="clinic",
            abbreviation="ZC",
            clinic_location="Zebra Building",
        )
        template_a = RotationTemplate(
            id=uuid4(),
            name="A Clinic",
            activity_type="clinic",
            abbreviation="AC",
            clinic_location="Alpha Building",
        )
        db.add(template_z)
        db.add(template_a)
        db.flush()

        # Create block
        block = Block(
            id=uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.flush()

        # Assign to different locations (including one with no template)
        assignment_z = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=sample_residents[0].id,
            role="primary",
            rotation_template_id=template_z.id,
        )
        assignment_a = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=sample_residents[1].id,
            role="primary",
            rotation_template_id=template_a.id,
        )
        assignment_none = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=sample_residents[2].id,
            role="primary",
            rotation_template_id=None,  # Will be "Unassigned"
        )
        db.add(assignment_z)
        db.add(assignment_a)
        db.add(assignment_none)
        db.commit()

        response = client.get(
            f"/api/assignments/daily-manifest?date={test_date.isoformat()}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Check location order
        location_names = [loc["clinic_location"] for loc in data["locations"]]
        assert len(location_names) == 3

        # Alpha should come before Zebra
        alpha_idx = location_names.index("Alpha Building")
        zebra_idx = location_names.index("Zebra Building")
        assert alpha_idx < zebra_idx, "Alpha Building should come before Zebra Building"

        # Unassigned should be last
        assert location_names[-1] == "Unassigned", "Unassigned should be sorted last"
