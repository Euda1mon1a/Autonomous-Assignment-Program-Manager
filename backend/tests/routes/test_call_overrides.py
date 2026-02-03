"""Tests for call override admin routes."""

from datetime import date, datetime
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def _make_override(**overrides):
    base = {
        "id": uuid4(),
        "call_assignment_id": uuid4(),
        "original_person_id": uuid4(),
        "replacement_person_id": uuid4(),
        "override_type": "coverage",
        "reason": "sick",
        "notes": None,
        "effective_date": date.today(),
        "call_type": "weekday",
        "is_active": True,
        "created_by_id": uuid4(),
        "created_at": datetime.utcnow(),
        "deactivated_at": None,
        "deactivated_by_id": None,
        "supersedes_override_id": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_create_call_override_success(client: TestClient, auth_headers: dict):
    override = _make_override()

    with patch(
        "app.api.routes.call_overrides.get_call_override_service"
    ) as mock_service:
        service = SimpleNamespace(
            create_override=AsyncMock(return_value=override),
        )
        mock_service.return_value = service

        payload = {
            "call_assignment_id": str(override.call_assignment_id),
            "replacement_person_id": str(override.replacement_person_id),
            "override_type": "coverage",
            "reason": "sick",
            "notes": "coverage swap",
        }

        response = client.post(
            "/api/v1/admin/call-overrides",
            json=payload,
            headers=auth_headers,
        )

    assert response.status_code == 201
    data = response.json()
    assert data["call_assignment_id"] == str(override.call_assignment_id)
    assert data["replacement_person_id"] == str(override.replacement_person_id)
    assert data["is_active"] is True


def test_list_call_overrides_success(client: TestClient, auth_headers: dict):
    override = _make_override()

    with patch(
        "app.api.routes.call_overrides.get_call_override_service"
    ) as mock_service:
        service = SimpleNamespace(
            list_overrides=AsyncMock(return_value=[override]),
        )
        mock_service.return_value = service

        response = client.get(
            "/api/v1/admin/call-overrides?block_number=5&academic_year=2025",
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["block_number"] == 5
    assert data["academic_year"] == 2025
    assert data["overrides"][0]["id"] == str(override.id)


def test_deactivate_call_override_success(client: TestClient, auth_headers: dict):
    override = _make_override(is_active=False)

    with patch(
        "app.api.routes.call_overrides.get_call_override_service"
    ) as mock_service:
        service = SimpleNamespace(
            deactivate_override=AsyncMock(return_value=override),
        )
        mock_service.return_value = service

        response = client.delete(
            f"/api/v1/admin/call-overrides/{override.id}",
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(override.id)
    assert data["is_active"] is False
