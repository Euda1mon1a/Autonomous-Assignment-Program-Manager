"""Tests for exotic resilience routes."""

from fastapi.testclient import TestClient
import pytest

from app.features.flags import FeatureFlagService


@pytest.mark.asyncio
async def test_phase_transition_returns_normal_when_insufficient_data(
    client: TestClient,
    auth_headers: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_evaluate_flag(self, **kwargs):
        return True, None, "forced"

    monkeypatch.setattr(FeatureFlagService, "evaluate_flag", fake_evaluate_flag)

    response = client.post(
        "/api/v1/resilience/exotic/thermodynamics/phase-transition",
        json={"lookback_days": 30, "sensitivity": 1.0},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["overall_severity"] == "normal"
    assert data["confidence"] == 0.0
    assert any("Insufficient data" in rec for rec in data["recommendations"])
