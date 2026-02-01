"""Route tests for swap API endpoints."""

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.services.swap_executor import SwapExecutor
from app.services.swap_validation import SwapValidationService


def _validation_result(valid: bool):
    return SimpleNamespace(
        valid=valid,
        errors=[],
        warnings=[],
        back_to_back_conflict=False,
        external_conflict=False,
    )


def _execute_result(success: bool, swap_id):
    return SimpleNamespace(success=success, swap_id=swap_id, message="ok")


def _rollback_result(success: bool):
    return SimpleNamespace(success=success, message="rolled back")


class TestSwapRoutes:
    """Smoke tests for swap routes."""

    def test_validate_swap(self, client: TestClient, auth_headers, monkeypatch):
        async def fake_validate(self, **_kwargs):
            return _validation_result(True)

        monkeypatch.setattr(SwapValidationService, "validate_swap", fake_validate)

        payload = {
            "source_faculty_id": str(uuid4()),
            "source_week": date.today().isoformat(),
            "target_faculty_id": str(uuid4()),
            "target_week": date.today().isoformat(),
            "swap_type": "one_to_one",
        }

        response = client.post(
            "/api/v1/swaps/validate", json=payload, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    def test_execute_swap(self, client: TestClient, auth_headers, monkeypatch):
        swap_id = uuid4()

        async def fake_validate(self, **_kwargs):
            return _validation_result(True)

        async def fake_execute(self, **_kwargs):
            return _execute_result(True, swap_id)

        monkeypatch.setattr(SwapValidationService, "validate_swap", fake_validate)
        monkeypatch.setattr(SwapExecutor, "execute_swap", fake_execute)

        async def _noop(*_args, **_kwargs):
            return None

        monkeypatch.setattr("app.api.routes.swap.broadcast_swap_approved", _noop)
        monkeypatch.setattr("app.api.routes.swap.broadcast_schedule_updated", _noop)

        payload = {
            "source_faculty_id": str(uuid4()),
            "source_week": date.today().isoformat(),
            "target_faculty_id": str(uuid4()),
            "target_week": date.today().isoformat(),
            "swap_type": "one_to_one",
        }

        response = client.post(
            "/api/v1/swaps/execute", json=payload, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["swap_id"] == str(swap_id)

    def test_get_swap_history_empty(self, client: TestClient, auth_headers):
        response = client.get("/api/v1/swaps/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_rollback_swap(self, client: TestClient, auth_headers, monkeypatch):
        swap_id = uuid4()

        async def fake_can_rollback(self, _swap_id):
            return True

        async def fake_rollback(self, **_kwargs):
            return _rollback_result(True)

        monkeypatch.setattr(SwapExecutor, "can_rollback", fake_can_rollback)
        monkeypatch.setattr(SwapExecutor, "rollback_swap", fake_rollback)

        payload = {"reason": "rollback requested"}
        response = client.post(
            f"/api/v1/swaps/{swap_id}/rollback", json=payload, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
