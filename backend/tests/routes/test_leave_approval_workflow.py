"""Tests for leave approval workflow."""

from datetime import date, timedelta

from fastapi.testclient import TestClient
import pytest

from app.notifications import tasks as notification_tasks

from app.models.person import Person


@pytest.fixture(autouse=True)
def _disable_leave_conflict_task(monkeypatch):
    class _DummyTask:
        def delay(self, *args, **kwargs):
            return None

    monkeypatch.setattr(
        notification_tasks,
        "detect_leave_conflicts",
        _DummyTask(),
    )


def test_leave_request_approval_flow(
    client: TestClient,
    auth_headers: dict,
    sample_faculty: Person,
):
    start_date = date.today() + timedelta(days=7)
    end_date = start_date + timedelta(days=2)

    request_payload = {
        "faculty_id": str(sample_faculty.id),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "leave_type": "vacation",
        "is_blocking": True,
        "description": "Requested leave",
    }

    create_response = client.post(
        "/api/v1/leave/request",
        json=request_payload,
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    create_data = create_response.json()
    assert create_data["status"] == "pending"
    leave_id = create_data["id"]

    approve_response = client.post(
        f"/api/v1/leave/{leave_id}/approval",
        json={"approved": True, "notes": "Approved"},
        headers=auth_headers,
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"


def test_leave_request_rejection_blocks_execution(
    client: TestClient,
    auth_headers: dict,
    sample_faculty: Person,
):
    start_date = date.today() + timedelta(days=14)
    end_date = start_date + timedelta(days=1)

    request_payload = {
        "faculty_id": str(sample_faculty.id),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "leave_type": "vacation",
        "is_blocking": True,
        "description": "Requested leave",
    }

    create_response = client.post(
        "/api/v1/leave/request",
        json=request_payload,
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    leave_id = create_response.json()["id"]

    reject_response = client.post(
        f"/api/v1/leave/{leave_id}/approval",
        json={"approved": False, "notes": "Denied"},
        headers=auth_headers,
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "rejected"
