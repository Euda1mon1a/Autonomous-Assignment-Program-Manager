"""Tests for half-day assignments endpoints."""

from datetime import date
from uuid import uuid4

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
