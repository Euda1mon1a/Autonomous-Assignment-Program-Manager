"""Tests for faculty activity routes validation paths."""

from fastapi.testclient import TestClient


def test_permitted_activities_rejects_invalid_role(
    client: TestClient, auth_headers: dict
) -> None:
    response = client.get(
        "/api/v1/faculty/activities/permitted",
        headers=auth_headers,
        params={"role": "not-a-role"},
    )

    assert response.status_code == 400
    assert "Invalid faculty role" in response.json()["detail"]


def test_faculty_matrix_rejects_end_before_start(
    client: TestClient, auth_headers: dict
) -> None:
    response = client.get(
        "/api/v1/faculty/activities/matrix",
        headers=auth_headers,
        params={"start_date": "2026-01-02", "end_date": "2026-01-01"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "end_date must be >= start_date"
