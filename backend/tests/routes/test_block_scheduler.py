"""Tests for block scheduler routes."""

import pytest
from fastapi.testclient import TestClient


def test_block_scheduler_dashboard_empty(client: TestClient, auth_headers):
    response = client.get(
        "/api/v1/block-scheduler/dashboard",
        params={"block_number": 1, "academic_year": 2025},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_residents"] == 0
    assert data["current_assignments"] == []
    assert data["leave_eligible_rotations"] == 0


# ---------------------------------------------------------------------------
# POST /api/v1/block-scheduler/schedule — BlockScheduleRequest validation
# ---------------------------------------------------------------------------

VALID_RESIDENT_UUID = "00000000-0000-0000-0000-000000000099"
DUMMY_ASSIGNMENT_UUID = "00000000-0000-0000-0000-000000000001"


@pytest.mark.unit
def test_schedule_block_empty_body_returns_422(client: TestClient, auth_headers):
    response = client.post(
        "/api/v1/block-scheduler/schedule",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_schedule_block_missing_academic_year_returns_422(
    client: TestClient, auth_headers
):
    response = client.post(
        "/api/v1/block-scheduler/schedule",
        json={"block_number": 1},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_schedule_block_invalid_block_number_type_returns_422(
    client: TestClient, auth_headers
):
    response = client.post(
        "/api/v1/block-scheduler/schedule",
        json={"block_number": "abc", "academic_year": 2025},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_schedule_block_block_number_out_of_range_returns_422(
    client: TestClient, auth_headers
):
    response = client.post(
        "/api/v1/block-scheduler/schedule",
        json={"block_number": 99, "academic_year": 2025},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_schedule_block_academic_year_out_of_range_returns_422(
    client: TestClient, auth_headers
):
    response = client.post(
        "/api/v1/block-scheduler/schedule",
        json={"block_number": 1, "academic_year": 1999},
        headers=auth_headers,
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/v1/block-scheduler/assignments — BlockAssignmentCreate validation
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_create_assignment_empty_body_returns_422(client: TestClient, auth_headers):
    response = client.post(
        "/api/v1/block-scheduler/assignments",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_create_assignment_missing_resident_id_returns_422(
    client: TestClient, auth_headers
):
    response = client.post(
        "/api/v1/block-scheduler/assignments",
        json={"block_number": 1, "academic_year": 2025},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_create_assignment_invalid_uuid_returns_422(client: TestClient, auth_headers):
    response = client.post(
        "/api/v1/block-scheduler/assignments",
        json={
            "block_number": 1,
            "academic_year": 2025,
            "resident_id": "not-a-uuid",
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_create_assignment_invalid_reason_returns_422(client: TestClient, auth_headers):
    response = client.post(
        "/api/v1/block-scheduler/assignments",
        json={
            "block_number": 1,
            "academic_year": 2025,
            "resident_id": VALID_RESIDENT_UUID,
            "assignment_reason": "INVALID",
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_create_assignment_negative_leave_days_returns_422(
    client: TestClient, auth_headers
):
    response = client.post(
        "/api/v1/block-scheduler/assignments",
        json={
            "block_number": 1,
            "academic_year": 2025,
            "resident_id": VALID_RESIDENT_UUID,
            "leave_days": -1,
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_create_assignment_notes_too_long_returns_422(client: TestClient, auth_headers):
    response = client.post(
        "/api/v1/block-scheduler/assignments",
        json={
            "block_number": 1,
            "academic_year": 2025,
            "resident_id": VALID_RESIDENT_UUID,
            "notes": "x" * 1001,
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# PUT /api/v1/block-scheduler/assignments/{id} — BlockAssignmentUpdate validation
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_update_assignment_invalid_reason_returns_422(client: TestClient, auth_headers):
    response = client.put(
        f"/api/v1/block-scheduler/assignments/{DUMMY_ASSIGNMENT_UUID}",
        json={"assignment_reason": "INVALID"},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_update_assignment_negative_leave_days_returns_422(
    client: TestClient, auth_headers
):
    response = client.put(
        f"/api/v1/block-scheduler/assignments/{DUMMY_ASSIGNMENT_UUID}",
        json={"leave_days": -5},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.unit
def test_update_assignment_notes_too_long_returns_422(client: TestClient, auth_headers):
    response = client.put(
        f"/api/v1/block-scheduler/assignments/{DUMMY_ASSIGNMENT_UUID}",
        json={"notes": "x" * 1001},
        headers=auth_headers,
    )
    assert response.status_code == 422
