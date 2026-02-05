"""Tests for enums API endpoints."""

from types import SimpleNamespace

from fastapi.testclient import TestClient


def test_enums_endpoints_return_options(client: TestClient):
    response = client.get("/api/v1/enums/scheduling-algorithms")
    assert response.status_code == 200
    algorithms = response.json()

    values = {item["value"] for item in algorithms}
    assert {"greedy", "cp_sat", "pulp", "hybrid"}.issubset(values)

    response = client.get("/api/v1/enums/activity-categories")
    assert response.status_code == 200
    categories = response.json()

    category_values = {item["value"] for item in categories}
    assert "clinical" in category_values


def test_enums_scheduling_algorithms_production_only_cp_sat(
    client: TestClient, monkeypatch
):
    import app.api.routes.enums as enums_routes

    monkeypatch.setattr(
        enums_routes, "get_settings", lambda: SimpleNamespace(DEBUG=False)
    )

    response = client.get("/api/v1/enums/scheduling-algorithms")
    assert response.status_code == 200
    algorithms = response.json()

    assert algorithms == [{"value": "cp_sat", "label": "CP-SAT (Canonical)"}]
