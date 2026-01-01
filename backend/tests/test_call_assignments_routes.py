"""Comprehensive tests for call assignment API routes.

Tests all call assignment endpoints with various scenarios including:
- List, create, update, delete call assignments
- Bulk operations for solver-generated assignments
- Coverage and equity reports
- Role-based access control (RBAC)
- Edge cases and error handling
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.call_assignment import CallAssignment
from app.models.person import Person
from app.models.user import User


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def coordinator_user(db: Session) -> User:
    """Create a coordinator user for testing."""
    user = User(
        id=uuid4(),
        username="coordinator",
        email="coordinator@test.org",
        hashed_password=get_password_hash("testpass123"),
        role="coordinator",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def coordinator_headers(client: TestClient, coordinator_user: User) -> dict:
    """Get authentication headers for coordinator user."""
    response = client.post(
        "/api/auth/login/json",
        json={"username": "coordinator", "password": "testpass123"},
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}


@pytest.fixture
def faculty_user(db: Session) -> User:
    """Create a faculty user for testing."""
    user = User(
        id=uuid4(),
        username="facultytest",
        email="facultytest@test.org",
        hashed_password=get_password_hash("testpass123"),
        role="faculty",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def faculty_headers(client: TestClient, faculty_user: User) -> dict:
    """Get authentication headers for faculty user."""
    response = client.post(
        "/api/auth/login/json",
        json={"username": "facultytest", "password": "testpass123"},
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}


@pytest.fixture
def resident_user(db: Session) -> User:
    """Create a resident user for testing."""
    user = User(
        id=uuid4(),
        username="residenttest",
        email="residenttest@test.org",
        hashed_password=get_password_hash("testpass123"),
        role="resident",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def resident_headers(client: TestClient, resident_user: User) -> dict:
    """Get authentication headers for resident user."""
    response = client.post(
        "/api/auth/login/json",
        json={"username": "residenttest", "password": "testpass123"},
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}


@pytest.fixture
def call_assignment(db: Session, sample_faculty: Person) -> CallAssignment:
    """Create a sample call assignment."""
    call = CallAssignment(
        id=uuid4(),
        date=date.today(),
        person_id=sample_faculty.id,
        call_type="overnight",
        is_weekend=False,
        is_holiday=False,
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


@pytest.fixture
def multiple_call_assignments(
    db: Session, sample_faculty_members: list[Person]
) -> list[CallAssignment]:
    """Create multiple call assignments across different dates."""
    calls = []
    start_date = date.today()

    for i in range(7):
        call_date = start_date + timedelta(days=i)
        faculty = sample_faculty_members[i % len(sample_faculty_members)]

        call = CallAssignment(
            id=uuid4(),
            date=call_date,
            person_id=faculty.id,
            call_type="overnight" if i % 3 == 0 else "weekend",
            is_weekend=(i % 7 >= 5),
            is_holiday=False,
        )
        db.add(call)
        calls.append(call)

    db.commit()
    for call in calls:
        db.refresh(call)
    return calls


# ============================================================================
# List Call Assignments Tests
# ============================================================================


def test_list_call_assignments_success(
    client: TestClient,
    auth_headers: dict,
    multiple_call_assignments: list[CallAssignment],
):
    """Test listing call assignments without filters."""
    response = client.get("/api/v1/call-assignments", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == len(multiple_call_assignments)
    assert len(data["items"]) <= 100  # Default limit


def test_list_call_assignments_with_date_filter(
    client: TestClient,
    auth_headers: dict,
    multiple_call_assignments: list[CallAssignment],
):
    """Test listing call assignments with date range filter."""
    start = date.today()
    end = date.today() + timedelta(days=3)

    response = client.get(
        f"/api/v1/call-assignments?start_date={start}&end_date={end}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    # Should return only assignments in the date range
    assert data["total"] <= 4  # 4 days in range


def test_list_call_assignments_with_person_filter(
    client: TestClient,
    auth_headers: dict,
    sample_faculty: Person,
    call_assignment: CallAssignment,
):
    """Test listing call assignments filtered by person."""
    response = client.get(
        f"/api/v1/call-assignments?person_id={sample_faculty.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    # All returned assignments should be for the specified person
    for item in data["items"]:
        assert item["person_id"] == str(sample_faculty.id)


def test_list_call_assignments_with_call_type_filter(
    client: TestClient,
    auth_headers: dict,
    multiple_call_assignments: list[CallAssignment],
):
    """Test listing call assignments filtered by call type."""
    response = client.get(
        "/api/v1/call-assignments?call_type=overnight",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    # All returned assignments should be overnight type
    for item in data["items"]:
        assert item["call_type"] == "overnight"


def test_list_call_assignments_pagination(
    client: TestClient,
    auth_headers: dict,
    multiple_call_assignments: list[CallAssignment],
):
    """Test pagination of call assignments list."""
    # First page
    response = client.get(
        "/api/v1/call-assignments?skip=0&limit=3",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 3
    assert data["skip"] == 0
    assert data["limit"] == 3

    # Second page
    response = client.get(
        "/api/v1/call-assignments?skip=3&limit=3",
        headers=auth_headers,
    )
    assert response.status_code == 200


def test_list_call_assignments_unauthenticated(client: TestClient):
    """Test listing call assignments without authentication."""
    response = client.get("/api/v1/call-assignments")
    assert response.status_code == 401


# ============================================================================
# Get Single Call Assignment Tests
# ============================================================================


def test_get_call_assignment_success(
    client: TestClient,
    auth_headers: dict,
    call_assignment: CallAssignment,
):
    """Test getting a single call assignment by ID."""
    response = client.get(
        f"/api/v1/call-assignments/{call_assignment.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(call_assignment.id)
    assert data["call_type"] == call_assignment.call_type
    assert "person" in data  # Should include person details


def test_get_call_assignment_not_found(
    client: TestClient,
    auth_headers: dict,
):
    """Test getting a non-existent call assignment."""
    fake_id = uuid4()
    response = client.get(
        f"/api/v1/call-assignments/{fake_id}",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_get_call_assignment_invalid_uuid(
    client: TestClient,
    auth_headers: dict,
):
    """Test getting a call assignment with invalid UUID."""
    response = client.get(
        "/api/v1/call-assignments/not-a-uuid",
        headers=auth_headers,
    )

    assert response.status_code == 422  # Validation error


# ============================================================================
# Create Call Assignment Tests
# ============================================================================


def test_create_call_assignment_as_admin(
    client: TestClient,
    auth_headers: dict,
    sample_faculty: Person,
):
    """Test creating a call assignment as admin."""
    call_data = {
        "call_date": str(date.today() + timedelta(days=10)),
        "person_id": str(sample_faculty.id),
        "call_type": "overnight",
        "is_weekend": False,
        "is_holiday": False,
    }

    response = client.post(
        "/api/v1/call-assignments",
        json=call_data,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["call_type"] == "overnight"
    assert data["person_id"] == str(sample_faculty.id)
    assert "id" in data


def test_create_call_assignment_as_coordinator(
    client: TestClient,
    coordinator_headers: dict,
    sample_faculty: Person,
):
    """Test creating a call assignment as coordinator."""
    call_data = {
        "call_date": str(date.today() + timedelta(days=11)),
        "person_id": str(sample_faculty.id),
        "call_type": "weekend",
        "is_weekend": True,
        "is_holiday": False,
    }

    response = client.post(
        "/api/v1/call-assignments",
        json=call_data,
        headers=coordinator_headers,
    )

    assert response.status_code == 201


def test_create_call_assignment_as_faculty(
    client: TestClient,
    faculty_headers: dict,
    sample_faculty: Person,
):
    """Test creating a call assignment as faculty."""
    call_data = {
        "call_date": str(date.today() + timedelta(days=12)),
        "person_id": str(sample_faculty.id),
        "call_type": "backup",
        "is_weekend": False,
        "is_holiday": False,
    }

    response = client.post(
        "/api/v1/call-assignments",
        json=call_data,
        headers=faculty_headers,
    )

    assert response.status_code == 201


def test_create_call_assignment_as_resident_forbidden(
    client: TestClient,
    resident_headers: dict,
    sample_faculty: Person,
):
    """Test that residents cannot create call assignments."""
    call_data = {
        "call_date": str(date.today() + timedelta(days=13)),
        "person_id": str(sample_faculty.id),
        "call_type": "overnight",
        "is_weekend": False,
        "is_holiday": False,
    }

    response = client.post(
        "/api/v1/call-assignments",
        json=call_data,
        headers=resident_headers,
    )

    assert response.status_code == 403  # Forbidden


def test_create_call_assignment_invalid_date(
    client: TestClient,
    auth_headers: dict,
    sample_faculty: Person,
):
    """Test creating a call assignment with invalid date."""
    call_data = {
        "call_date": "not-a-date",
        "person_id": str(sample_faculty.id),
        "call_type": "overnight",
    }

    response = client.post(
        "/api/v1/call-assignments",
        json=call_data,
        headers=auth_headers,
    )

    assert response.status_code == 422  # Validation error


def test_create_call_assignment_missing_required_fields(
    client: TestClient,
    auth_headers: dict,
):
    """Test creating a call assignment with missing required fields."""
    call_data = {
        "call_type": "overnight",
        # Missing call_date and person_id
    }

    response = client.post(
        "/api/v1/call-assignments",
        json=call_data,
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_create_call_assignment_invalid_person_id(
    client: TestClient,
    auth_headers: dict,
):
    """Test creating a call assignment with non-existent person."""
    call_data = {
        "call_date": str(date.today() + timedelta(days=14)),
        "person_id": str(uuid4()),  # Non-existent person
        "call_type": "overnight",
    }

    response = client.post(
        "/api/v1/call-assignments",
        json=call_data,
        headers=auth_headers,
    )

    # Should fail - person doesn't exist
    assert response.status_code in [400, 404]


# ============================================================================
# Update Call Assignment Tests
# ============================================================================


def test_update_call_assignment_as_admin(
    client: TestClient,
    auth_headers: dict,
    call_assignment: CallAssignment,
):
    """Test updating a call assignment as admin."""
    update_data = {
        "call_type": "weekend",
        "is_weekend": True,
    }

    response = client.put(
        f"/api/v1/call-assignments/{call_assignment.id}",
        json=update_data,
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["call_type"] == "weekend"
    assert data["is_weekend"] is True


def test_update_call_assignment_as_coordinator(
    client: TestClient,
    coordinator_headers: dict,
    call_assignment: CallAssignment,
):
    """Test updating a call assignment as coordinator."""
    update_data = {
        "is_holiday": True,
    }

    response = client.put(
        f"/api/v1/call-assignments/{call_assignment.id}",
        json=update_data,
        headers=coordinator_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_holiday"] is True


def test_update_call_assignment_as_resident_forbidden(
    client: TestClient,
    resident_headers: dict,
    call_assignment: CallAssignment,
):
    """Test that residents cannot update call assignments."""
    update_data = {
        "call_type": "backup",
    }

    response = client.put(
        f"/api/v1/call-assignments/{call_assignment.id}",
        json=update_data,
        headers=resident_headers,
    )

    assert response.status_code == 403


def test_update_call_assignment_not_found(
    client: TestClient,
    auth_headers: dict,
):
    """Test updating a non-existent call assignment."""
    fake_id = uuid4()
    update_data = {
        "call_type": "weekend",
    }

    response = client.put(
        f"/api/v1/call-assignments/{fake_id}",
        json=update_data,
        headers=auth_headers,
    )

    assert response.status_code == 404


# ============================================================================
# Delete Call Assignment Tests
# ============================================================================


def test_delete_call_assignment_as_admin(
    client: TestClient,
    auth_headers: dict,
    call_assignment: CallAssignment,
):
    """Test deleting a call assignment as admin."""
    response = client.delete(
        f"/api/v1/call-assignments/{call_assignment.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    # Verify deletion
    get_response = client.get(
        f"/api/v1/call-assignments/{call_assignment.id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404


def test_delete_call_assignment_as_coordinator(
    client: TestClient,
    coordinator_headers: dict,
    call_assignment: CallAssignment,
):
    """Test deleting a call assignment as coordinator."""
    response = client.delete(
        f"/api/v1/call-assignments/{call_assignment.id}",
        headers=coordinator_headers,
    )

    assert response.status_code == 204


def test_delete_call_assignment_as_resident_forbidden(
    client: TestClient,
    resident_headers: dict,
    call_assignment: CallAssignment,
):
    """Test that residents cannot delete call assignments."""
    response = client.delete(
        f"/api/v1/call-assignments/{call_assignment.id}",
        headers=resident_headers,
    )

    assert response.status_code == 403


def test_delete_call_assignment_not_found(
    client: TestClient,
    auth_headers: dict,
):
    """Test deleting a non-existent call assignment."""
    fake_id = uuid4()
    response = client.delete(
        f"/api/v1/call-assignments/{fake_id}",
        headers=auth_headers,
    )

    assert response.status_code == 404


# ============================================================================
# Bulk Create Call Assignments Tests
# ============================================================================


def test_bulk_create_call_assignments_as_admin(
    client: TestClient,
    auth_headers: dict,
    sample_faculty_members: list[Person],
):
    """Test bulk creating call assignments as admin."""
    assignments = []
    start_date = date.today() + timedelta(days=20)

    for i in range(5):
        assignments.append(
            {
                "call_date": str(start_date + timedelta(days=i)),
                "person_id": str(sample_faculty_members[i % len(sample_faculty_members)].id),
                "call_type": "overnight",
                "is_weekend": False,
                "is_holiday": False,
            }
        )

    bulk_data = {
        "assignments": assignments,
        "replace_existing": False,
    }

    response = client.post(
        "/api/v1/call-assignments/bulk",
        json=bulk_data,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["created"] == 5
    assert len(data["errors"]) == 0


def test_bulk_create_call_assignments_as_coordinator(
    client: TestClient,
    coordinator_headers: dict,
    sample_faculty_members: list[Person],
):
    """Test bulk creating call assignments as coordinator."""
    assignments = [
        {
            "call_date": str(date.today() + timedelta(days=30)),
            "person_id": str(sample_faculty_members[0].id),
            "call_type": "weekend",
            "is_weekend": True,
            "is_holiday": False,
        }
    ]

    bulk_data = {
        "assignments": assignments,
        "replace_existing": False,
    }

    response = client.post(
        "/api/v1/call-assignments/bulk",
        json=bulk_data,
        headers=coordinator_headers,
    )

    assert response.status_code == 201


def test_bulk_create_call_assignments_as_faculty_forbidden(
    client: TestClient,
    faculty_headers: dict,
    sample_faculty: Person,
):
    """Test that faculty cannot bulk create call assignments."""
    assignments = [
        {
            "call_date": str(date.today() + timedelta(days=31)),
            "person_id": str(sample_faculty.id),
            "call_type": "overnight",
        }
    ]

    bulk_data = {
        "assignments": assignments,
        "replace_existing": False,
    }

    response = client.post(
        "/api/v1/call-assignments/bulk",
        json=bulk_data,
        headers=faculty_headers,
    )

    # Faculty role is not in the allowed list for bulk operations
    assert response.status_code == 403


def test_bulk_create_call_assignments_with_replace(
    client: TestClient,
    auth_headers: dict,
    sample_faculty: Person,
    call_assignment: CallAssignment,
):
    """Test bulk creating with replace_existing flag."""
    # Create new assignment on same date as existing
    assignments = [
        {
            "call_date": str(call_assignment.date),
            "person_id": str(sample_faculty.id),
            "call_type": "weekend",
            "is_weekend": True,
            "is_holiday": False,
        }
    ]

    bulk_data = {
        "assignments": assignments,
        "replace_existing": True,
    }

    response = client.post(
        "/api/v1/call-assignments/bulk",
        json=bulk_data,
        headers=auth_headers,
    )

    assert response.status_code == 201


# ============================================================================
# Get Call Assignments by Person Tests
# ============================================================================


def test_get_call_assignments_by_person(
    client: TestClient,
    auth_headers: dict,
    sample_faculty: Person,
    call_assignment: CallAssignment,
):
    """Test getting call assignments for a specific person."""
    response = client.get(
        f"/api/v1/call-assignments/by-person/{sample_faculty.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["person_id"] == str(sample_faculty.id)


def test_get_call_assignments_by_person_with_date_filter(
    client: TestClient,
    auth_headers: dict,
    sample_faculty: Person,
):
    """Test getting call assignments for a person with date filter."""
    start = date.today()
    end = date.today() + timedelta(days=7)

    response = client.get(
        f"/api/v1/call-assignments/by-person/{sample_faculty.id}?start_date={start}&end_date={end}",
        headers=auth_headers,
    )

    assert response.status_code == 200


def test_get_call_assignments_by_person_not_found(
    client: TestClient,
    auth_headers: dict,
):
    """Test getting call assignments for non-existent person."""
    fake_id = uuid4()
    response = client.get(
        f"/api/v1/call-assignments/by-person/{fake_id}",
        headers=auth_headers,
    )

    # Should return empty list, not error
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


# ============================================================================
# Get Call Assignments by Date Tests
# ============================================================================


def test_get_call_assignments_by_date(
    client: TestClient,
    auth_headers: dict,
    call_assignment: CallAssignment,
):
    """Test getting call assignments for a specific date."""
    response = client.get(
        f"/api/v1/call-assignments/by-date/{call_assignment.date}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["call_date"] == str(call_assignment.date)


def test_get_call_assignments_by_date_no_assignments(
    client: TestClient,
    auth_headers: dict,
):
    """Test getting call assignments for date with no assignments."""
    future_date = date.today() + timedelta(days=365)
    response = client.get(
        f"/api/v1/call-assignments/by-date/{future_date}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


# ============================================================================
# Coverage Report Tests
# ============================================================================


def test_get_coverage_report_as_admin(
    client: TestClient,
    auth_headers: dict,
    multiple_call_assignments: list[CallAssignment],
):
    """Test getting coverage report as admin."""
    start = date.today()
    end = date.today() + timedelta(days=6)

    response = client.get(
        f"/api/v1/call-assignments/reports/coverage?start_date={start}&end_date={end}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "total_expected_nights" in data
    assert "covered_nights" in data
    assert "coverage_percentage" in data
    assert "gaps" in data
    assert data["start_date"] == str(start)
    assert data["end_date"] == str(end)


def test_get_coverage_report_as_coordinator(
    client: TestClient,
    coordinator_headers: dict,
):
    """Test getting coverage report as coordinator."""
    start = date.today()
    end = date.today() + timedelta(days=6)

    response = client.get(
        f"/api/v1/call-assignments/reports/coverage?start_date={start}&end_date={end}",
        headers=coordinator_headers,
    )

    assert response.status_code == 200


def test_get_coverage_report_as_faculty_forbidden(
    client: TestClient,
    faculty_headers: dict,
):
    """Test that faculty cannot access coverage report."""
    start = date.today()
    end = date.today() + timedelta(days=6)

    response = client.get(
        f"/api/v1/call-assignments/reports/coverage?start_date={start}&end_date={end}",
        headers=faculty_headers,
    )

    assert response.status_code == 403


def test_get_coverage_report_missing_dates(
    client: TestClient,
    auth_headers: dict,
):
    """Test coverage report without required date parameters."""
    response = client.get(
        "/api/v1/call-assignments/reports/coverage",
        headers=auth_headers,
    )

    assert response.status_code == 422  # Missing required query params


# ============================================================================
# Equity Report Tests
# ============================================================================


def test_get_equity_report_as_admin(
    client: TestClient,
    auth_headers: dict,
    multiple_call_assignments: list[CallAssignment],
):
    """Test getting equity report as admin."""
    start = date.today()
    end = date.today() + timedelta(days=6)

    response = client.get(
        f"/api/v1/call-assignments/reports/equity?start_date={start}&end_date={end}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "faculty_count" in data
    assert "total_overnight_calls" in data
    assert "sunday_call_stats" in data
    assert "weekday_call_stats" in data
    assert "distribution" in data


def test_get_equity_report_as_coordinator(
    client: TestClient,
    coordinator_headers: dict,
):
    """Test getting equity report as coordinator."""
    start = date.today()
    end = date.today() + timedelta(days=6)

    response = client.get(
        f"/api/v1/call-assignments/reports/equity?start_date={start}&end_date={end}",
        headers=coordinator_headers,
    )

    assert response.status_code == 200


def test_get_equity_report_as_resident_forbidden(
    client: TestClient,
    resident_headers: dict,
):
    """Test that residents cannot access equity report."""
    start = date.today()
    end = date.today() + timedelta(days=6)

    response = client.get(
        f"/api/v1/call-assignments/reports/equity?start_date={start}&end_date={end}",
        headers=resident_headers,
    )

    assert response.status_code == 403


def test_get_equity_report_invalid_date_range(
    client: TestClient,
    auth_headers: dict,
):
    """Test equity report with invalid date range (end before start)."""
    start = date.today() + timedelta(days=10)
    end = date.today()

    response = client.get(
        f"/api/v1/call-assignments/reports/equity?start_date={start}&end_date={end}",
        headers=auth_headers,
    )

    # Should handle gracefully
    assert response.status_code in [200, 400]
