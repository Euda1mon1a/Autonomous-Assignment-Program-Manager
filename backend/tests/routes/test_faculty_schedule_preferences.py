"""Tests for faculty schedule preference admin routes."""

from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import patch

from fastapi.testclient import TestClient


def _make_preference(**overrides):
    base = {
        "id": uuid4(),
        "person_id": uuid4(),
        "preference_type": "clinic",
        "direction": "prefer",
        "rank": 1,
        "day_of_week": 1,
        "time_of_day": "AM",
        "weight": 6,
        "is_active": True,
        "notes": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_list_faculty_schedule_preferences(client: TestClient, auth_headers: dict):
    pref = _make_preference()

    with patch(
        "app.api.routes.faculty_schedule_preferences.FacultySchedulePreferenceService"
    ) as mock_service:
        instance = mock_service.return_value
        instance.list_preferences.return_value = {
            "items": [pref],
            "total": 1,
            "page": 1,
            "page_size": 100,
        }

        response = client.get(
            "/api/v1/admin/faculty-schedule-preferences",
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == str(pref.id)


def test_get_faculty_schedule_preference_not_found(
    client: TestClient, auth_headers: dict
):
    with patch(
        "app.api.routes.faculty_schedule_preferences.FacultySchedulePreferenceService"
    ) as mock_service:
        mock_service.return_value.get_preference.return_value = None
        preference_id = uuid4()

        response = client.get(
            f"/api/v1/admin/faculty-schedule-preferences/{preference_id}",
            headers=auth_headers,
        )

    assert response.status_code == 404


def test_update_faculty_schedule_preference_not_found(
    client: TestClient, auth_headers: dict
):
    with patch(
        "app.api.routes.faculty_schedule_preferences.FacultySchedulePreferenceService"
    ) as mock_service:
        mock_service.return_value.update_preference.return_value = None
        preference_id = uuid4()

        response = client.put(
            f"/api/v1/admin/faculty-schedule-preferences/{preference_id}",
            json={"notes": "adjust"},
            headers=auth_headers,
        )

    assert response.status_code == 404


def test_delete_faculty_schedule_preference_not_found(
    client: TestClient, auth_headers: dict
):
    with patch(
        "app.api.routes.faculty_schedule_preferences.FacultySchedulePreferenceService"
    ) as mock_service:
        mock_service.return_value.delete_preference.return_value = False
        preference_id = uuid4()

        response = client.delete(
            f"/api/v1/admin/faculty-schedule-preferences/{preference_id}",
            headers=auth_headers,
        )

    assert response.status_code == 404
