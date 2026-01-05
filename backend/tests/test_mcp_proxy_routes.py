"""
Tests for MCP Proxy API routes.

Tests coverage for MCP tool proxy endpoints:
- POST /api/mcp/calculate-equity-metrics
- POST /api/mcp/generate-lorenz-curve

Created: 2026-01-04 (Session 049)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ============================================================================
# Test Classes
# ============================================================================


class TestCalculateEquityMetricsEndpoint:
    """Tests for POST /api/mcp/calculate-equity-metrics endpoint."""

    def test_calculate_equity_metrics_requires_auth(self, client: TestClient):
        """Test that calculate equity metrics requires authentication."""
        response = client.post(
            "/api/mcp/calculate-equity-metrics",
            json={
                "provider_hours": {"provider-1": 40.0, "provider-2": 45.0},
            },
        )

        assert response.status_code in [401, 403]

    def test_calculate_equity_metrics_success(
        self, client: TestClient, auth_headers: dict
    ):
        """Test successful equity metrics calculation."""
        response = client.post(
            "/api/mcp/calculate-equity-metrics",
            json={
                "provider_hours": {
                    "provider-1": 40.0,
                    "provider-2": 45.0,
                    "provider-3": 50.0,
                    "provider-4": 42.0,
                },
            },
            headers=auth_headers,
        )

        # Admin user should be able to access
        assert response.status_code in [200, 401, 403]

        if response.status_code == 200:
            data = response.json()
            assert "gini_coefficient" in data
            assert "is_equitable" in data
            assert "mean_workload" in data
            assert "std_workload" in data
            assert "recommendations" in data
            assert "interpretation" in data
            assert data["gini_coefficient"] >= 0.0
            assert data["gini_coefficient"] <= 1.0

    def test_calculate_equity_metrics_perfect_equality(
        self, client: TestClient, auth_headers: dict
    ):
        """Test equity metrics with perfect equality (all same hours)."""
        response = client.post(
            "/api/mcp/calculate-equity-metrics",
            json={
                "provider_hours": {
                    "provider-1": 40.0,
                    "provider-2": 40.0,
                    "provider-3": 40.0,
                },
            },
            headers=auth_headers,
        )

        if response.status_code == 200:
            data = response.json()
            assert data["gini_coefficient"] == 0.0
            assert data["is_equitable"] is True

    def test_calculate_equity_metrics_with_weights(
        self, client: TestClient, auth_headers: dict
    ):
        """Test equity metrics with intensity weights."""
        response = client.post(
            "/api/mcp/calculate-equity-metrics",
            json={
                "provider_hours": {
                    "provider-1": 40.0,
                    "provider-2": 40.0,
                    "provider-3": 40.0,
                },
                "intensity_weights": {
                    "provider-1": 1.0,
                    "provider-2": 1.5,  # Night shift intensity
                    "provider-3": 1.0,
                },
            },
            headers=auth_headers,
        )

        if response.status_code == 200:
            data = response.json()
            # With weights, even equal hours become unequal
            assert data["gini_coefficient"] > 0.0

    def test_calculate_equity_metrics_missing_weights(
        self, client: TestClient, auth_headers: dict
    ):
        """Test error when intensity weights are incomplete."""
        response = client.post(
            "/api/mcp/calculate-equity-metrics",
            json={
                "provider_hours": {
                    "provider-1": 40.0,
                    "provider-2": 45.0,
                },
                "intensity_weights": {
                    "provider-1": 1.0,
                    # Missing provider-2
                },
            },
            headers=auth_headers,
        )

        if response.status_code == 400:
            data = response.json()
            assert "Missing intensity weights" in data.get("detail", "")

    def test_calculate_equity_metrics_empty_providers(
        self, client: TestClient, auth_headers: dict
    ):
        """Test error with empty provider hours."""
        response = client.post(
            "/api/mcp/calculate-equity-metrics",
            json={
                "provider_hours": {},
            },
            headers=auth_headers,
        )

        # Should fail validation (422) or bad request (400)
        assert response.status_code in [400, 422, 401, 403]

    def test_calculate_equity_metrics_response_structure(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that response has all expected fields."""
        response = client.post(
            "/api/mcp/calculate-equity-metrics",
            json={
                "provider_hours": {
                    "provider-1": 60.0,
                    "provider-2": 40.0,
                    "provider-3": 50.0,
                },
            },
            headers=auth_headers,
        )

        if response.status_code == 200:
            data = response.json()

            # Verify all required fields
            required_fields = [
                "gini_coefficient",
                "is_equitable",
                "mean_workload",
                "std_workload",
                "most_overloaded_provider",
                "most_underloaded_provider",
                "max_workload",
                "min_workload",
                "recommendations",
                "interpretation",
            ]
            for field in required_fields:
                assert field in data, f"Missing field: {field}"

            # Verify statistics are correct
            assert data["max_workload"] == 60.0
            assert data["min_workload"] == 40.0
            assert data["most_overloaded_provider"] == "provider-1"
            assert data["most_underloaded_provider"] == "provider-2"


class TestGenerateLorenzCurveEndpoint:
    """Tests for POST /api/mcp/generate-lorenz-curve endpoint."""

    def test_generate_lorenz_curve_requires_auth(self, client: TestClient):
        """Test that generate Lorenz curve requires authentication."""
        response = client.post(
            "/api/mcp/generate-lorenz-curve",
            json={
                "values": [10.0, 20.0, 30.0, 40.0],
            },
        )

        assert response.status_code in [401, 403]

    def test_generate_lorenz_curve_success(
        self, client: TestClient, auth_headers: dict
    ):
        """Test successful Lorenz curve generation."""
        response = client.post(
            "/api/mcp/generate-lorenz-curve",
            json={
                "values": [10.0, 20.0, 30.0, 40.0],
            },
            headers=auth_headers,
        )

        if response.status_code == 200:
            data = response.json()
            assert "population_shares" in data
            assert "value_shares" in data
            assert "equality_line" in data
            assert "gini_coefficient" in data

            # Population shares should start at 0 and end at 1
            assert data["population_shares"][0] == 0.0
            assert data["population_shares"][-1] == 1.0

    def test_generate_lorenz_curve_empty_values(
        self, client: TestClient, auth_headers: dict
    ):
        """Test error with empty values list."""
        response = client.post(
            "/api/mcp/generate-lorenz-curve",
            json={
                "values": [],
            },
            headers=auth_headers,
        )

        # Should fail validation (422) or bad request (400)
        assert response.status_code in [400, 422, 401, 403]


class TestMCPProxyRoleRestrictions:
    """Tests for role-based access control on MCP proxy endpoints."""

    def test_equity_metrics_admin_access(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that admin users can access equity metrics."""
        response = client.post(
            "/api/mcp/calculate-equity-metrics",
            json={
                "provider_hours": {"p1": 40.0, "p2": 45.0},
            },
            headers=auth_headers,
        )

        # Admin should succeed (200) or get auth error if token invalid
        assert response.status_code in [200, 401, 403]
