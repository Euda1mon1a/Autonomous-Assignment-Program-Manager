"""Tests for daily manifest API routes.

Tests the "Where is everyone NOW" endpoint critical for clinic staff.
Validates staffing summaries, location grouping, and time filtering.
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.user import User

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user for authentication."""
    user = User(
        id=uuid4(),
        username="testuser",
        email="testuser@test.com",
        hashed_password=get_password_hash("password123"),
        role="coordinator",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user: User) -> str:
    """Create an authentication token for the test user."""
    return create_access_token(
        data={"sub": str(test_user.id), "username": test_user.username}
    )


@pytest.fixture
def manifest_test_date() -> date:
    """Return a consistent test date for manifest tests."""
    return date(2025, 1, 15)


@pytest.fixture
def test_residents(db: Session) -> list[Person]:
    """Create test residents with different PGY levels."""
    residents = []
    for i, pgy in enumerate([1, 2, 3, 2], start=1):
        resident = Person(
            id=uuid4(),
            name=f"Dr. Resident {i}",
            type="resident",
            email=f"resident{i}@test.com",
            pgy_level=pgy,
        )
        db.add(resident)
        residents.append(resident)
    db.commit()
    for r in residents:
        db.refresh(r)
    return residents


@pytest.fixture
def test_faculty(db: Session) -> list[Person]:
    """Create test faculty members."""
    faculty = []
    for i in range(1, 3):
        fac = Person(
            id=uuid4(),
            name=f"Dr. Faculty {i}",
            type="faculty",
            email=f"faculty{i}@test.com",
            performs_procedures=True,
            specialties=["Sports Medicine"],
        )
        db.add(fac)
        faculty.append(fac)
    db.commit()
    for f in faculty:
        db.refresh(f)
    return faculty


@pytest.fixture
def test_rotation_templates(db: Session) -> dict[str, RotationTemplate]:
    """Create test rotation templates with different clinic locations."""
    templates = {
        "clinic_a": RotationTemplate(
            id=uuid4(),
            name="Sports Medicine Clinic A",
            activity_type="clinic",
            abbreviation="SMA",
            clinic_location="Building A - Sports Medicine",
            max_residents=4,
            supervision_required=True,
        ),
        "clinic_b": RotationTemplate(
            id=uuid4(),
            name="Primary Care Clinic B",
            activity_type="clinic",
            abbreviation="PCB",
            clinic_location="Building B - Primary Care",
            max_residents=3,
            supervision_required=True,
        ),
        "no_location": RotationTemplate(
            id=uuid4(),
            name="Administrative",
            activity_type="admin",
            abbreviation="ADM",
            clinic_location=None,  # No location set
            max_residents=0,
            supervision_required=False,
        ),
    }
    for template in templates.values():
        db.add(template)
    db.commit()
    for template in templates.values():
        db.refresh(template)
    return templates


@pytest.fixture
def test_blocks(db: Session, manifest_test_date: date) -> dict[str, list[Block]]:
    """Create test blocks for the manifest test date and surrounding dates."""
    blocks = {"test_day": [], "day_before": [], "day_after": []}

    dates = {
        "test_day": manifest_test_date,
        "day_before": manifest_test_date - timedelta(days=1),
        "day_after": manifest_test_date + timedelta(days=1),
    }

    for key, current_date in dates.items():
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
            blocks[key].append(block)

    db.commit()
    for block_list in blocks.values():
        for block in block_list:
            db.refresh(block)
    return blocks


@pytest.fixture
def populated_manifest(
    db: Session,
    test_residents: list[Person],
    test_faculty: list[Person],
    test_rotation_templates: dict[str, RotationTemplate],
    test_blocks: dict[str, list[Block]],
    test_user: User,
) -> dict:
    """Create a fully populated manifest with assignments across locations and times."""
    assignments = []
    test_day_blocks = test_blocks["test_day"]

    # Building A - Sports Medicine (AM and PM)
    # AM: 2 residents + 1 faculty
    assignments.append(
        Assignment(
            id=uuid4(),
            block_id=test_day_blocks[0].id,  # AM block
            person_id=test_residents[0].id,  # PGY1
            rotation_template_id=test_rotation_templates["clinic_a"].id,
            role="primary",
            created_by=test_user.username,
        )
    )
    assignments.append(
        Assignment(
            id=uuid4(),
            block_id=test_day_blocks[0].id,  # AM block
            person_id=test_residents[1].id,  # PGY2
            rotation_template_id=test_rotation_templates["clinic_a"].id,
            role="primary",
            created_by=test_user.username,
        )
    )
    assignments.append(
        Assignment(
            id=uuid4(),
            block_id=test_day_blocks[0].id,  # AM block
            person_id=test_faculty[0].id,
            rotation_template_id=test_rotation_templates["clinic_a"].id,
            role="supervising",
            created_by=test_user.username,
        )
    )

    # PM: 1 resident + 1 faculty
    assignments.append(
        Assignment(
            id=uuid4(),
            block_id=test_day_blocks[1].id,  # PM block
            person_id=test_residents[2].id,  # PGY3
            rotation_template_id=test_rotation_templates["clinic_a"].id,
            role="primary",
            created_by=test_user.username,
        )
    )
    assignments.append(
        Assignment(
            id=uuid4(),
            block_id=test_day_blocks[1].id,  # PM block
            person_id=test_faculty[1].id,
            rotation_template_id=test_rotation_templates["clinic_a"].id,
            role="supervising",
            created_by=test_user.username,
        )
    )

    # Building B - Primary Care (AM only)
    # AM: 1 resident
    assignments.append(
        Assignment(
            id=uuid4(),
            block_id=test_day_blocks[0].id,  # AM block
            person_id=test_residents[3].id,  # PGY2
            rotation_template_id=test_rotation_templates["clinic_b"].id,
            role="primary",
            created_by=test_user.username,
        )
    )

    # Unassigned location (no clinic_location)
    # PM: 1 faculty on admin duty
    assignments.append(
        Assignment(
            id=uuid4(),
            block_id=test_day_blocks[1].id,  # PM block
            person_id=test_faculty[0].id,
            rotation_template_id=test_rotation_templates["no_location"].id,
            role="primary",
            created_by=test_user.username,
        )
    )

    for assignment in assignments:
        db.add(assignment)
    db.commit()
    for assignment in assignments:
        db.refresh(assignment)

    return {
        "assignments": assignments,
        "blocks": test_day_blocks,
        "residents": test_residents,
        "faculty": test_faculty,
        "templates": test_rotation_templates,
    }


# ============================================================================
# Authentication Tests
# ============================================================================


class TestDailyManifestAuthentication:
    """Test authentication requirements for daily manifest endpoint."""

    def test_requires_authentication(
        self, client: TestClient, manifest_test_date: date
    ):
        """Test that the daily manifest endpoint requires authentication."""
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": manifest_test_date.isoformat()},
        )
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_authenticated_user_can_access(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
    ):
        """Test that authenticated users can access the daily manifest."""
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": manifest_test_date.isoformat()},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "date" in data
        assert "locations" in data
        assert "generated_at" in data


# ============================================================================
# Basic Functionality Tests
# ============================================================================


class TestDailyManifestBasicFunctionality:
    """Test basic daily manifest functionality."""

    def test_get_manifest_for_date(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        populated_manifest: dict,
    ):
        """Test retrieving daily manifest for a specific date."""
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": manifest_test_date.isoformat()},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["date"] == manifest_test_date.isoformat()
        assert data["time_of_day"] is None  # No filter, should be None
        assert isinstance(data["locations"], list)
        assert len(data["locations"]) > 0
        assert "generated_at" in data

    def test_manifest_with_no_assignments(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
    ):
        """Test manifest endpoint returns empty locations for date with no assignments."""
        # Use a date far in the future with no assignments
        future_date = date(2026, 12, 31)
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": future_date.isoformat()},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == future_date.isoformat()
        assert data["locations"] == []

    def test_manifest_response_structure(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        populated_manifest: dict,
    ):
        """Test that manifest response has correct schema structure."""
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": manifest_test_date.isoformat()},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Verify top-level structure
        assert "date" in data
        assert "time_of_day" in data
        assert "locations" in data
        assert "generated_at" in data

        # Verify location structure
        for location in data["locations"]:
            assert "clinic_location" in location
            assert "time_slots" in location
            assert "staffing_summary" in location

            # Verify time_slots structure
            time_slots = location["time_slots"]
            assert isinstance(time_slots, dict)
            assert "AM" in time_slots
            assert "PM" in time_slots

            # Verify staffing_summary structure
            staffing = location["staffing_summary"]
            assert "total" in staffing
            assert "residents" in staffing
            assert "faculty" in staffing

            # Verify assignment structure
            for time_slot, assignments in time_slots.items():
                for assignment in assignments:
                    assert "person" in assignment
                    assert "role" in assignment
                    assert "activity" in assignment

                    # Verify person structure
                    person = assignment["person"]
                    assert "id" in person
                    assert "name" in person
                    assert "pgy_level" in person


# ============================================================================
# Date Filtering Tests
# ============================================================================


class TestDailyManifestDateFiltering:
    """Test date filtering functionality."""

    def test_date_parameter_required(
        self,
        client: TestClient,
        auth_token: str,
    ):
        """Test that date parameter is required."""
        response = client.get(
            "/api/assignments/daily-manifest",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        # FastAPI will return 422 for missing required query parameter
        assert response.status_code == 422

    def test_filters_by_specific_date(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        test_blocks: dict[str, list[Block]],
        test_residents: list[Person],
        test_rotation_templates: dict[str, RotationTemplate],
        test_user: User,
        db: Session,
    ):
        """Test that manifest only returns assignments for the specified date."""
        # Create assignments on different dates
        day_before_assignment = Assignment(
            id=uuid4(),
            block_id=test_blocks["day_before"][0].id,
            person_id=test_residents[0].id,
            rotation_template_id=test_rotation_templates["clinic_a"].id,
            role="primary",
            created_by=test_user.username,
        )
        test_day_assignment = Assignment(
            id=uuid4(),
            block_id=test_blocks["test_day"][0].id,
            person_id=test_residents[1].id,
            rotation_template_id=test_rotation_templates["clinic_a"].id,
            role="primary",
            created_by=test_user.username,
        )
        day_after_assignment = Assignment(
            id=uuid4(),
            block_id=test_blocks["day_after"][0].id,
            person_id=test_residents[2].id,
            rotation_template_id=test_rotation_templates["clinic_a"].id,
            role="primary",
            created_by=test_user.username,
        )
        db.add_all([day_before_assignment, test_day_assignment, day_after_assignment])
        db.commit()

        # Query for the test date
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": manifest_test_date.isoformat()},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Should only have assignments from test_day
        assert data["date"] == manifest_test_date.isoformat()
        assert len(data["locations"]) == 1

        # Count total assignments across all time slots
        total_assignments = sum(
            len(assignments)
            for location in data["locations"]
            for assignments in location["time_slots"].values()
        )
        assert total_assignments == 1


# ============================================================================
# Time of Day Filtering Tests
# ============================================================================


class TestDailyManifestTimeOfDayFiltering:
    """Test time of day filtering functionality."""

    def test_filter_by_am(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        populated_manifest: dict,
    ):
        """Test filtering manifest to show only AM assignments."""
        response = client.get(
            "/api/assignments/daily-manifest",
            params={
                "date": manifest_test_date.isoformat(),
                "time_of_day": "AM",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["time_of_day"] == "AM"

        # Verify only AM assignments are present
        for location in data["locations"]:
            am_assignments = location["time_slots"]["AM"]
            pm_assignments = location["time_slots"]["PM"]

            # AM should have assignments (based on populated_manifest)
            # PM should be empty
            assert isinstance(am_assignments, list)
            assert pm_assignments == []

    def test_filter_by_pm(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        populated_manifest: dict,
    ):
        """Test filtering manifest to show only PM assignments."""
        response = client.get(
            "/api/assignments/daily-manifest",
            params={
                "date": manifest_test_date.isoformat(),
                "time_of_day": "PM",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["time_of_day"] == "PM"

        # Verify only PM assignments are present
        for location in data["locations"]:
            am_assignments = location["time_slots"]["AM"]
            pm_assignments = location["time_slots"]["PM"]

            # AM should be empty
            # PM should have assignments (based on populated_manifest)
            assert am_assignments == []
            assert isinstance(pm_assignments, list)

    def test_no_time_filter_shows_both(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        populated_manifest: dict,
    ):
        """Test that omitting time_of_day parameter shows both AM and PM."""
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": manifest_test_date.isoformat()},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["time_of_day"] is None

        # Find a location that has both AM and PM assignments
        found_am = False
        found_pm = False

        for location in data["locations"]:
            if location["time_slots"]["AM"]:
                found_am = True
            if location["time_slots"]["PM"]:
                found_pm = True

        # Based on populated_manifest, we should have both
        assert found_am, "Should have AM assignments"
        assert found_pm, "Should have PM assignments"

    def test_invalid_time_of_day(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
    ):
        """Test that invalid time_of_day values return 400 error."""
        invalid_values = ["MORNING", "AFTERNOON", "am", "pm", "ALLDAY", "123"]

        for invalid_value in invalid_values:
            response = client.get(
                "/api/assignments/daily-manifest",
                params={
                    "date": manifest_test_date.isoformat(),
                    "time_of_day": invalid_value,
                },
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            assert response.status_code == 400
            assert "must be 'AM' or 'PM'" in response.json()["detail"]


# ============================================================================
# Location Grouping Tests
# ============================================================================


class TestDailyManifestLocationGrouping:
    """Test location grouping functionality."""

    def test_groups_by_clinic_location(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        populated_manifest: dict,
    ):
        """Test that assignments are grouped by clinic location."""
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": manifest_test_date.isoformat()},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Should have multiple locations
        assert len(data["locations"]) >= 2

        # Verify expected locations are present
        location_names = {loc["clinic_location"] for loc in data["locations"]}
        assert "Building A - Sports Medicine" in location_names
        assert "Building B - Primary Care" in location_names

    def test_unassigned_location_for_null_clinic_location(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        populated_manifest: dict,
    ):
        """Test that assignments without clinic_location are grouped as 'Unassigned'."""
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": manifest_test_date.isoformat()},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Should have an "Unassigned" location
        location_names = [loc["clinic_location"] for loc in data["locations"]]
        assert "Unassigned" in location_names

        # Verify Unassigned location has the expected assignment
        unassigned_location = next(
            loc for loc in data["locations"] if loc["clinic_location"] == "Unassigned"
        )

        # Based on populated_manifest, should have 1 faculty in PM slot
        pm_assignments = unassigned_location["time_slots"]["PM"]
        assert len(pm_assignments) >= 1

    def test_locations_sorted_alphabetically_unassigned_last(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        populated_manifest: dict,
    ):
        """Test that locations are sorted alphabetically with 'Unassigned' last."""
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": manifest_test_date.isoformat()},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        location_names = [loc["clinic_location"] for loc in data["locations"]]

        # Unassigned should be last
        if "Unassigned" in location_names:
            assert location_names[-1] == "Unassigned"

            # Other locations should be sorted alphabetically
            other_locations = location_names[:-1]
            assert other_locations == sorted(other_locations)
        else:
            # If no Unassigned, all should be sorted
            assert location_names == sorted(location_names)

    def test_separate_time_slots_within_location(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        populated_manifest: dict,
    ):
        """Test that assignments are properly separated by time slot within each location."""
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": manifest_test_date.isoformat()},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Find Building A location (has both AM and PM assignments)
        building_a = next(
            loc
            for loc in data["locations"]
            if loc["clinic_location"] == "Building A - Sports Medicine"
        )

        am_assignments = building_a["time_slots"]["AM"]
        pm_assignments = building_a["time_slots"]["PM"]

        # Based on populated_manifest:
        # AM: 2 residents + 1 faculty = 3
        # PM: 1 resident + 1 faculty = 2
        assert len(am_assignments) == 3
        assert len(pm_assignments) == 2

        # Verify person IDs are different between slots
        am_person_ids = {a["person"]["id"] for a in am_assignments}
        pm_person_ids = {a["person"]["id"] for a in pm_assignments}

        # There should be some overlap (faculty might work both shifts)
        # but they should not be identical
        assert am_person_ids != pm_person_ids


# ============================================================================
# Staffing Summary Tests
# ============================================================================


class TestDailyManifestStaffingSummary:
    """Test staffing summary accuracy."""

    def test_staffing_summary_counts_residents_correctly(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        populated_manifest: dict,
    ):
        """Test that resident count in staffing summary is accurate."""
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": manifest_test_date.isoformat()},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Find Building A location
        building_a = next(
            loc
            for loc in data["locations"]
            if loc["clinic_location"] == "Building A - Sports Medicine"
        )

        # Based on populated_manifest:
        # AM: 2 residents (PGY1, PGY2)
        # PM: 1 resident (PGY3)
        # Total: 3 residents across both time slots
        assert building_a["staffing_summary"]["residents"] == 3

    def test_staffing_summary_counts_faculty_correctly(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        populated_manifest: dict,
    ):
        """Test that faculty count in staffing summary is accurate."""
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": manifest_test_date.isoformat()},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Find Building A location
        building_a = next(
            loc
            for loc in data["locations"]
            if loc["clinic_location"] == "Building A - Sports Medicine"
        )

        # Based on populated_manifest:
        # AM: 1 faculty
        # PM: 1 faculty (different person)
        # Total: 2 faculty across both time slots
        assert building_a["staffing_summary"]["faculty"] == 2

    def test_staffing_summary_total_equals_residents_plus_faculty(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        populated_manifest: dict,
    ):
        """Test that total count equals residents + faculty."""
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": manifest_test_date.isoformat()},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        for location in data["locations"]:
            staffing = location["staffing_summary"]
            assert staffing["total"] == staffing["residents"] + staffing["faculty"]

    def test_staffing_summary_with_time_filter(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        populated_manifest: dict,
    ):
        """Test that staffing summary is accurate when filtering by time of day."""
        # Get AM only
        response = client.get(
            "/api/assignments/daily-manifest",
            params={
                "date": manifest_test_date.isoformat(),
                "time_of_day": "AM",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Find Building A location
        building_a = next(
            loc
            for loc in data["locations"]
            if loc["clinic_location"] == "Building A - Sports Medicine"
        )

        # AM only: 2 residents + 1 faculty = 3 total
        assert building_a["staffing_summary"]["residents"] == 2
        assert building_a["staffing_summary"]["faculty"] == 1
        assert building_a["staffing_summary"]["total"] == 3

    def test_staffing_summary_identifies_residents_by_pgy_level(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        db: Session,
        test_blocks: dict[str, list[Block]],
        test_rotation_templates: dict[str, RotationTemplate],
        test_user: User,
    ):
        """Test that residents are identified by having a pgy_level."""
        # Create a person with pgy_level and one without
        resident = Person(
            id=uuid4(),
            name="Dr. Resident Test",
            type="resident",
            email="resident.test@test.com",
            pgy_level=3,
        )
        faculty = Person(
            id=uuid4(),
            name="Dr. Faculty Test",
            type="faculty",
            email="faculty.test@test.com",
            pgy_level=None,  # Faculty should not have pgy_level
        )
        db.add_all([resident, faculty])
        db.commit()

        # Create assignments
        assignment_resident = Assignment(
            id=uuid4(),
            block_id=test_blocks["test_day"][0].id,
            person_id=resident.id,
            rotation_template_id=test_rotation_templates["clinic_a"].id,
            role="primary",
            created_by=test_user.username,
        )
        assignment_faculty = Assignment(
            id=uuid4(),
            block_id=test_blocks["test_day"][0].id,
            person_id=faculty.id,
            rotation_template_id=test_rotation_templates["clinic_a"].id,
            role="supervising",
            created_by=test_user.username,
        )
        db.add_all([assignment_resident, assignment_faculty])
        db.commit()

        # Query manifest
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": manifest_test_date.isoformat()},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Find Building A location
        building_a = next(
            loc
            for loc in data["locations"]
            if loc["clinic_location"] == "Building A - Sports Medicine"
        )

        # Should have 1 resident and 1 faculty
        assert building_a["staffing_summary"]["residents"] == 1
        assert building_a["staffing_summary"]["faculty"] == 1

    def test_staffing_summary_handles_zero_counts(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        db: Session,
        test_blocks: dict[str, list[Block]],
        test_rotation_templates: dict[str, RotationTemplate],
        test_user: User,
    ):
        """Test staffing summary when location has only residents or only faculty."""
        # Create location with only residents
        resident = Person(
            id=uuid4(),
            name="Dr. Solo Resident",
            type="resident",
            email="solo.resident@test.com",
            pgy_level=2,
        )
        db.add(resident)
        db.commit()

        assignment = Assignment(
            id=uuid4(),
            block_id=test_blocks["test_day"][0].id,
            person_id=resident.id,
            rotation_template_id=test_rotation_templates["clinic_b"].id,
            role="primary",
            created_by=test_user.username,
        )
        db.add(assignment)
        db.commit()

        # Query manifest
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": manifest_test_date.isoformat()},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Find Building B location
        building_b = next(
            loc
            for loc in data["locations"]
            if loc["clinic_location"] == "Building B - Primary Care"
        )

        # Should have 1 resident, 0 faculty
        assert building_b["staffing_summary"]["residents"] == 1
        assert building_b["staffing_summary"]["faculty"] == 0
        assert building_b["staffing_summary"]["total"] == 1


# ============================================================================
# Assignment Details Tests
# ============================================================================


class TestDailyManifestAssignmentDetails:
    """Test assignment detail accuracy in manifest."""

    def test_person_details_included(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        populated_manifest: dict,
    ):
        """Test that person details are included in assignments."""
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": manifest_test_date.isoformat()},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Get first assignment
        first_location = data["locations"][0]
        am_assignments = first_location["time_slots"]["AM"]
        if am_assignments:
            assignment = am_assignments[0]
            person = assignment["person"]

            assert "id" in person
            assert "name" in person
            assert "pgy_level" in person
            assert person["name"]  # Should have a name

    def test_role_included_in_assignment(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        populated_manifest: dict,
    ):
        """Test that role is included in assignment details."""
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": manifest_test_date.isoformat()},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Check that all assignments have roles
        for location in data["locations"]:
            for time_slot, assignments in location["time_slots"].items():
                for assignment in assignments:
                    assert "role" in assignment
                    assert assignment["role"] in ["primary", "supervising", "backup"]

    def test_activity_name_included(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        populated_manifest: dict,
    ):
        """Test that activity name is included in assignment details."""
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": manifest_test_date.isoformat()},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Check that all assignments have activity names
        for location in data["locations"]:
            for time_slot, assignments in location["time_slots"].items():
                for assignment in assignments:
                    assert "activity" in assignment
                    # Activity should be the template name or override
                    assert assignment["activity"]  # Should not be empty

    def test_activity_override_used_when_present(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        db: Session,
        test_blocks: dict[str, list[Block]],
        test_residents: list[Person],
        test_rotation_templates: dict[str, RotationTemplate],
        test_user: User,
    ):
        """Test that activity_override is used instead of template name when present."""
        custom_activity = "Special Research Project"

        assignment = Assignment(
            id=uuid4(),
            block_id=test_blocks["test_day"][0].id,
            person_id=test_residents[0].id,
            rotation_template_id=test_rotation_templates["clinic_a"].id,
            role="primary",
            activity_override=custom_activity,
            created_by=test_user.username,
        )
        db.add(assignment)
        db.commit()

        # Query manifest
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": manifest_test_date.isoformat()},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Find the assignment with override
        found_override = False
        for location in data["locations"]:
            for time_slot, assignments in location["time_slots"].items():
                for assignment in assignments:
                    if assignment["activity"] == custom_activity:
                        found_override = True
                        break

        assert found_override, "Activity override should be used in manifest"


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestDailyManifestEdgeCases:
    """Test edge cases and error handling."""

    def test_handles_multiple_assignments_same_person(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        db: Session,
        test_blocks: dict[str, list[Block]],
        test_residents: list[Person],
        test_rotation_templates: dict[str, RotationTemplate],
        test_user: User,
    ):
        """Test manifest when same person has multiple assignments same day."""
        # Create two assignments for same person, same day, different times
        assignment_am = Assignment(
            id=uuid4(),
            block_id=test_blocks["test_day"][0].id,  # AM
            person_id=test_residents[0].id,
            rotation_template_id=test_rotation_templates["clinic_a"].id,
            role="primary",
            created_by=test_user.username,
        )
        assignment_pm = Assignment(
            id=uuid4(),
            block_id=test_blocks["test_day"][1].id,  # PM
            person_id=test_residents[0].id,
            rotation_template_id=test_rotation_templates["clinic_b"].id,
            role="primary",
            created_by=test_user.username,
        )
        db.add_all([assignment_am, assignment_pm])
        db.commit()

        # Query manifest
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": manifest_test_date.isoformat()},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Both assignments should appear
        resident_id = str(test_residents[0].id)
        found_am = False
        found_pm = False

        for location in data["locations"]:
            for assignment in location["time_slots"]["AM"]:
                if assignment["person"]["id"] == resident_id:
                    found_am = True
            for assignment in location["time_slots"]["PM"]:
                if assignment["person"]["id"] == resident_id:
                    found_pm = True

        assert found_am, "Should find resident in AM slot"
        assert found_pm, "Should find resident in PM slot"

    def test_handles_missing_rotation_template(
        self,
        client: TestClient,
        manifest_test_date: date,
        auth_token: str,
        db: Session,
        test_blocks: dict[str, list[Block]],
        test_residents: list[Person],
        test_user: User,
    ):
        """Test manifest handles assignments without rotation template gracefully."""
        # Create assignment without rotation_template_id
        assignment = Assignment(
            id=uuid4(),
            block_id=test_blocks["test_day"][0].id,
            person_id=test_residents[0].id,
            rotation_template_id=None,
            role="primary",
            created_by=test_user.username,
        )
        db.add(assignment)
        db.commit()

        # Query should still work
        response = client.get(
            "/api/assignments/daily-manifest",
            params={"date": manifest_test_date.isoformat()},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        # Should have Unassigned location
        location_names = [loc["clinic_location"] for loc in data["locations"]]
        assert "Unassigned" in location_names

    def test_date_format_validation(
        self,
        client: TestClient,
        auth_token: str,
    ):
        """Test that invalid date formats are rejected."""
        invalid_dates = ["2025/01/15", "15-01-2025", "January 15, 2025", "not-a-date"]

        for invalid_date in invalid_dates:
            response = client.get(
                "/api/assignments/daily-manifest",
                params={"date": invalid_date},
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            # Should return 422 for invalid date format
            assert response.status_code == 422
