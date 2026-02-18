"""Tests for half-day assignments endpoints."""

from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.models.activity import Activity, ActivityCategory
from app.models.half_day_assignment import HalfDayAssignment
from app.models.person import Person


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
