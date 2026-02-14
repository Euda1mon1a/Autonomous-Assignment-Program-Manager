"""Tests for activity endpoints."""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.models.activity import Activity, ActivityCategory


def test_create_activity_duplicate_name_returns_400(
    client: TestClient, auth_headers, db
):
    existing = Activity(
        id=uuid4(),
        name="FM Clinic",
        code="fm_clinic",
        display_abbreviation="C",
        activity_category=ActivityCategory.CLINICAL.value,
    )
    db.add(existing)
    db.commit()

    response = client.post(
        "/api/v1/activities",
        headers=auth_headers,
        json={
            "name": "FM Clinic",
            "code": "fm_clinic_b",
            "display_abbreviation": "C2",
            "activity_category": ActivityCategory.CLINICAL.value,
        },
    )

    assert response.status_code == 400
    assert "name" in response.json()["detail"]


def test_update_activity_duplicate_code_returns_400(
    client: TestClient, auth_headers, db
):
    activity_a = Activity(
        id=uuid4(),
        name="FM Clinic",
        code="fm_clinic",
        display_abbreviation="C",
        activity_category=ActivityCategory.CLINICAL.value,
    )
    activity_b = Activity(
        id=uuid4(),
        name="Didactics",
        code="didactics",
        display_abbreviation="LEC",
        activity_category=ActivityCategory.EDUCATIONAL.value,
    )
    db.add_all([activity_a, activity_b])
    db.commit()

    response = client.put(
        f"/api/v1/activities/{activity_b.id}",
        headers=auth_headers,
        json={"code": "fm_clinic"},
    )

    assert response.status_code == 400
    assert "code" in response.json()["detail"]
