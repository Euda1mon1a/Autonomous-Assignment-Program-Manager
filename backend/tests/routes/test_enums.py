"""Tests for enums API endpoints."""

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
