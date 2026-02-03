"""Tests for swap approval workflow."""

from datetime import date, timedelta
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


def test_swap_request_approval_and_execute(client: TestClient, auth_headers: dict, db):
    faculty_a = _create_faculty(db, "Dr. Alpha", "alpha@example.org")
    faculty_b = _create_faculty(db, "Dr. Beta", "beta@example.org")

    week_start = date.today() + timedelta(days=7)

    request_payload = {
        "source_faculty_id": str(faculty_a.id),
        "source_week": week_start.isoformat(),
        "target_faculty_id": str(faculty_b.id),
        "swap_type": "absorb",
        "reason": "Coverage swap",
    }

    create_response = client.post(
        "/api/v1/swaps/request", json=request_payload, headers=auth_headers
    )
    assert create_response.status_code == 200
    create_data = create_response.json()
    assert create_data["success"] is True
    swap_id = create_data["swap_id"]

    approve_response = client.post(
        f"/api/v1/swaps/{swap_id}/approval",
        json={"approved": True, "notes": "Approved by admin"},
        headers=auth_headers,
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"

    execute_response = client.post(
        f"/api/v1/swaps/{swap_id}/execute",
        headers=auth_headers,
    )
    assert execute_response.status_code == 200
    assert execute_response.json()["status"] == "executed"


def test_swap_request_rejection_blocks_execution(
    client: TestClient, auth_headers: dict, db
):
    faculty_a = _create_faculty(db, "Dr. Gamma", "gamma@example.org")
    faculty_b = _create_faculty(db, "Dr. Delta", "delta@example.org")

    week_start = date.today() + timedelta(days=14)

    request_payload = {
        "source_faculty_id": str(faculty_a.id),
        "source_week": week_start.isoformat(),
        "target_faculty_id": str(faculty_b.id),
        "swap_type": "absorb",
        "reason": "Coverage swap",
    }

    create_response = client.post(
        "/api/v1/swaps/request", json=request_payload, headers=auth_headers
    )
    assert create_response.status_code == 200
    swap_id = create_response.json()["swap_id"]

    reject_response = client.post(
        f"/api/v1/swaps/{swap_id}/approval",
        json={"approved": False, "notes": "Not feasible"},
        headers=auth_headers,
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "rejected"

    execute_response = client.post(
        f"/api/v1/swaps/{swap_id}/execute",
        headers=auth_headers,
    )
    assert execute_response.status_code == 400
