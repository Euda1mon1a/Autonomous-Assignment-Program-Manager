"""Tests for block scheduler routes."""

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
