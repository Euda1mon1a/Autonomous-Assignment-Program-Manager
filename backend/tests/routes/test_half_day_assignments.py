"""Tests for half-day assignments endpoints."""

from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_scheduler_user
from app.main import app
from app.models.activity import Activity, ActivityCategory
from app.models.half_day_assignment import HalfDayAssignment
from app.models.person import Person
from app.models.user import User


def test_list_half_day_assignments_by_date_range(client: TestClient, db):
    resident = Person(
        id=uuid4(),
        name="Dr. Resident",
        type="resident",
        email="resident@hospital.org",
        pgy_level=2,
    )
    activity = Activity(
        id=uuid4(),
        name="Clinic",
        code="CLN",
        display_abbreviation="C",
        activity_category=ActivityCategory.CLINICAL.value,
    )
    db.add_all([resident, activity])
    db.commit()

    slot_date = date.today()
    assignment = HalfDayAssignment(
        id=uuid4(),
        person_id=resident.id,
        date=slot_date,
        time_of_day="AM",
        activity_id=activity.id,
        source="solver",
    )
    db.add(assignment)
    db.commit()

    response = client.get(
        "/api/v1/half-day-assignments",
        params={"start_date": slot_date.isoformat(), "end_date": slot_date.isoformat()},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["assignments"][0]["person_name"] == "Dr. Resident"
    assert data["assignments"][0]["activity_code"] == "CLN"
    assert data["assignments"][0]["is_gap"] is False


@pytest.mark.unit
def test_list_assignments_no_params_returns_400(client: TestClient):
    response = client.get(
        "/api/v1/half-day-assignments",
    )
    assert response.status_code == 400


@pytest.mark.unit
def test_list_assignments_block_number_out_of_range_returns_422(client: TestClient):
    response = client.get(
        "/api/v1/half-day-assignments",
        params={"block_number": 0, "academic_year": 2025},
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_list_assignments_block_number_too_high_returns_422(client: TestClient):
    response = client.get(
        "/api/v1/half-day-assignments",
        params={"block_number": 14, "academic_year": 2025},
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_list_assignments_invalid_date_format_returns_422(client: TestClient):
    response = client.get(
        "/api/v1/half-day-assignments",
        params={"start_date": "not-a-date", "end_date": "2025-01-07"},
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_list_assignments_partial_block_params_returns_400(client: TestClient):
    response = client.get(
        "/api/v1/half-day-assignments",
        params={"block_number": 1},
    )
    assert response.status_code == 400


@pytest.mark.unit
def test_list_assignments_partial_date_params_returns_400(client: TestClient):
    response = client.get(
        "/api/v1/half-day-assignments",
        params={"start_date": "2025-01-01"},
    )
    assert response.status_code == 400


@pytest.mark.unit
def test_list_assignments_block_number_string_returns_422(client: TestClient):
    response = client.get(
        "/api/v1/half-day-assignments",
        params={"block_number": "abc"},
    )
    assert response.status_code == 422


# ============================================================================
# DELETE /api/v1/half-day-assignments Tests
# ============================================================================


@pytest.fixture
def scheduler_user():
    """Override get_scheduler_user dependency for tests."""
    user = User(
        id=uuid4(),
        username="test_scheduler",
        email="scheduler@test.org",
        hashed_password="hashed",
        role="coordinator",
        is_active=True,
    )
    app.dependency_overrides[get_scheduler_user] = lambda: user
    yield user
    app.dependency_overrides.pop(get_scheduler_user, None)


def test_clear_half_day_assignments_deletes_solver_and_template(
    client: TestClient, db, scheduler_user
):
    """Should delete solver/template assignments but preserve preload/manual."""
    activity = Activity(
        id=uuid4(),
        name="Clinic",
        code="CLN",
        display_abbreviation="C",
        activity_category=ActivityCategory.CLINICAL.value,
    )
    db.add(activity)
    db.commit()

    slot_date = date.today()
    # Create 4 people so each source gets a unique (person, date, time) slot
    people = []
    for i, source in enumerate(["preload", "manual", "solver", "template"]):
        p = Person(
            id=uuid4(),
            name=f"Resident {i}",
            type="resident",
            email=f"r{i}@hospital.org",
            pgy_level=2,
        )
        db.add(p)
        db.commit()
        db.add(
            HalfDayAssignment(
                id=uuid4(),
                person_id=p.id,
                date=slot_date,
                time_of_day="AM",
                activity_id=activity.id,
                source=source,
            )
        )
        people.append(p)
    db.commit()

    # Verify 4 total assignments
    total_before = db.query(HalfDayAssignment).count()
    assert total_before == 4

    response = client.delete(
        "/api/v1/half-day-assignments",
        params={
            "start_date": slot_date.isoformat(),
            "end_date": slot_date.isoformat(),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] == 2  # solver + template
    assert set(data["sources"]) == {"solver", "template"}

    # Verify preload and manual are preserved
    remaining = db.query(HalfDayAssignment).all()
    assert len(remaining) == 2
    remaining_sources = {a.source for a in remaining}
    assert remaining_sources == {"preload", "manual"}


def test_clear_half_day_assignments_rejects_protected_sources(
    client: TestClient, scheduler_user
):
    """Should reject attempts to clear preload or manual sources."""
    response = client.delete(
        "/api/v1/half-day-assignments",
        params={
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "sources": "preload,solver",
        },
    )
    assert response.status_code == 400
    assert "protected sources" in response.json()["detail"].lower()


def test_clear_half_day_assignments_requires_auth(client: TestClient):
    """Should return 401 without scheduler credentials."""
    response = client.delete(
        "/api/v1/half-day-assignments",
        params={
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
        },
    )
    assert response.status_code == 401


def test_clear_half_day_assignments_invalid_date_order(
    client: TestClient, scheduler_user
):
    """Should return 400 when start_date > end_date."""
    response = client.delete(
        "/api/v1/half-day-assignments",
        params={
            "start_date": "2026-02-01",
            "end_date": "2026-01-01",
        },
    )
    assert response.status_code == 400
    assert "start_date" in response.json()["detail"]


def test_clear_half_day_assignments_solver_only(client: TestClient, db, scheduler_user):
    """Should clear only solver assignments when sources=solver."""
    resident = Person(
        id=uuid4(),
        name="Solver Resident",
        type="resident",
        email="solver@hospital.org",
        pgy_level=1,
    )
    activity = Activity(
        id=uuid4(),
        name="Ward",
        code="WRD",
        display_abbreviation="W",
        activity_category=ActivityCategory.CLINICAL.value,
    )
    db.add_all([resident, activity])
    db.commit()

    slot_date = date.today()
    db.add(
        HalfDayAssignment(
            id=uuid4(),
            person_id=resident.id,
            date=slot_date,
            time_of_day="AM",
            activity_id=activity.id,
            source="solver",
        )
    )
    db.add(
        HalfDayAssignment(
            id=uuid4(),
            person_id=resident.id,
            date=slot_date,
            time_of_day="PM",
            activity_id=activity.id,
            source="template",
        )
    )
    db.commit()

    response = client.delete(
        "/api/v1/half-day-assignments",
        params={
            "start_date": slot_date.isoformat(),
            "end_date": slot_date.isoformat(),
            "sources": "solver",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] == 1
    assert data["sources"] == ["solver"]

    # Template should remain
    remaining = db.query(HalfDayAssignment).all()
    assert len(remaining) == 1
    assert remaining[0].source == "template"


# ============================================================================
# PATCH /api/v1/half-day-assignments/{assignment_id} Tests
# ============================================================================


def test_update_half_day_assignment_prefers_exact_activity_code_match(
    client: TestClient, db, scheduler_user
):
    """Should resolve activity by exact code before display abbreviation fallback."""
    resident = Person(
        id=uuid4(),
        name="Patch Resident",
        type="resident",
        email="patch@hospital.org",
        pgy_level=2,
    )
    original_activity = Activity(
        id=uuid4(),
        name="Clinic",
        code="CLN",
        display_abbreviation="C",
        activity_category=ActivityCategory.CLINICAL.value,
    )
    exact_code_activity = Activity(
        id=uuid4(),
        name="Conference",
        code="ECHO",
        display_abbreviation="X",
        activity_category=ActivityCategory.DIDACTIC.value,
    )
    abbreviation_collision_activity = Activity(
        id=uuid4(),
        name="Echo Backup",
        code="ZZZ",
        display_abbreviation="ECHO",
        activity_category=ActivityCategory.CLINICAL.value,
    )
    db.add_all(
        [
            resident,
            original_activity,
            exact_code_activity,
            abbreviation_collision_activity,
        ]
    )
    db.commit()

    assignment = HalfDayAssignment(
        id=uuid4(),
        person_id=resident.id,
        date=date.today(),
        time_of_day="AM",
        activity_id=original_activity.id,
        source="solver",
    )
    db.add(assignment)
    db.commit()

    response = client.patch(
        f"/api/v1/half-day-assignments/{assignment.id}",
        json={"activity_code": "ECHO", "override_reason": "Manual correction"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["activity_id"] == str(exact_code_activity.id)
    assert payload["activity_code"] == "ECHO"
    assert payload["source"] == "manual"
    assert payload["is_locked"] is True

    db.refresh(assignment)
    assert assignment.activity_id == exact_code_activity.id
    assert assignment.is_override is True
    assert assignment.overridden_by == scheduler_user.id


def test_update_half_day_assignment_unknown_activity_code_returns_400(
    client: TestClient, db, scheduler_user
):
    """Should reject unknown activity code and preserve existing assignment."""
    resident = Person(
        id=uuid4(),
        name="Unknown Code Resident",
        type="resident",
        email="unknown@hospital.org",
        pgy_level=1,
    )
    activity = Activity(
        id=uuid4(),
        name="Ward",
        code="WRD",
        display_abbreviation="W",
        activity_category=ActivityCategory.CLINICAL.value,
    )
    db.add_all([resident, activity])
    db.commit()

    assignment = HalfDayAssignment(
        id=uuid4(),
        person_id=resident.id,
        date=date.today(),
        time_of_day="PM",
        activity_id=activity.id,
        source="solver",
    )
    db.add(assignment)
    db.commit()

    response = client.patch(
        f"/api/v1/half-day-assignments/{assignment.id}",
        json={"activity_code": "NOT_REAL"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unknown activity code: NOT_REAL"

    db.refresh(assignment)
    assert assignment.activity_id == activity.id
    assert assignment.source == "solver"
