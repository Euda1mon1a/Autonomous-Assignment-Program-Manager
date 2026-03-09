"""Tests for leave approval workflow."""

from datetime import date, timedelta
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.models.person import Person


def _create_faculty(db, name: str, email: str) -> Person:
    faculty = Person(
        id=uuid4(),
        name=name,
        type="faculty",
        email=email,
        faculty_role="core",
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


def test_leave_request_approval_flow(client: TestClient, auth_headers: dict, db):
    faculty = _create_faculty(db, "Dr. Leave", "leave@example.org")
    start_date = date.today() + timedelta(days=7)
    end_date = start_date + timedelta(days=4)

    request_payload = {
        "faculty_id": str(faculty.id),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "leave_type": "vacation",
        "is_blocking": False,
        "description": "Planned leave",
    }

    create_response = client.post(
        "/api/v1/leave/request", json=request_payload, headers=auth_headers
    )
    assert create_response.status_code == 200
    create_data = create_response.json()
    assert create_data["success"] is True
    assert create_data["status"] == "pending"
    leave_id = create_data["leave_id"]

    with patch("app.notifications.tasks.detect_leave_conflicts") as mock_task:
        mock_task.delay.return_value = None
        approve_response = client.post(
            f"/api/v1/leave/{leave_id}/approval",
            json={"approved": True, "notes": "Approved"},
            headers=auth_headers,
        )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"


def test_leave_request_rejection(client: TestClient, auth_headers: dict, db):
    faculty = _create_faculty(db, "Dr. Reject", "reject@example.org")
    start_date = date.today() + timedelta(days=14)
    end_date = start_date + timedelta(days=2)

    request_payload = {
        "faculty_id": str(faculty.id),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "leave_type": "vacation",
        "is_blocking": False,
        "description": "Short leave",
    }

    create_response = client.post(
        "/api/v1/leave/request", json=request_payload, headers=auth_headers
    )
    assert create_response.status_code == 200
    leave_id = create_response.json()["leave_id"]

    reject_response = client.post(
        f"/api/v1/leave/{leave_id}/approval",
        json={"approved": False, "notes": "Not feasible"},
        headers=auth_headers,
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "rejected"
