"""Tests for institutional events routes."""

from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient

from app.models.activity import Activity, ActivityCategory


def test_institutional_event_lifecycle(client: TestClient, auth_headers, db):
    activity = Activity(
        id=uuid4(),
        name="Institutional Closure",
        code="CLOSE",
        display_abbreviation="CLOSE",
        activity_category=ActivityCategory.ADMINISTRATIVE.value,
    )
    db.add(activity)
    db.commit()

    payload = {
        "name": "Training Day",
        "event_type": "training",
        "start_date": str(date.today()),
        "end_date": str(date.today()),
        "time_of_day": "AM",
        "applies_to": "all",
        "applies_to_inpatient": False,
        "activity_id": str(activity.id),
        "notes": "Annual training",
        "is_active": True,
    }

    create_response = client.post(
        "/api/v1/admin/institutional-events",
        json=payload,
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    event = create_response.json()
    assert event["name"] == "Training Day"

    list_response = client.get(
        "/api/v1/admin/institutional-events",
        headers=auth_headers,
    )
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["total"] == 1

    delete_response = client.delete(
        f"/api/v1/admin/institutional-events/{event['id']}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 204

    list_active_response = client.get(
        "/api/v1/admin/institutional-events",
        headers=auth_headers,
    )
    assert list_active_response.status_code == 200
    assert list_active_response.json()["total"] == 0
