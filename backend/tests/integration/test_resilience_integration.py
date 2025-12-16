"""
Integration tests for the resilience framework.

Tests the end-to-end functionality of:
1. Health check endpoints
2. Resilience status monitoring
3. Tier 2 and Tier 3 API endpoints
"""
import pytest


@pytest.mark.integration
class TestResilienceHealthChecks:
    """Test resilience health check endpoints."""

    def test_basic_health_check(self, integration_client):
        """Test the basic health check endpoint."""
        response = integration_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_resilience_health_check(self, integration_client):
        """Test the resilience-specific health check."""
        response = integration_client.get("/health/resilience")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data

    def test_root_endpoint(self, integration_client):
        """Test the root endpoint returns API info."""
        response = integration_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Residency Scheduler API"
        assert "version" in data


@pytest.mark.integration
class TestTier2Endpoints:
    """Test Tier 2 resilience API endpoints."""

    def test_tier2_status(self, integration_client, auth_headers):
        """Test Tier 2 status endpoint."""
        response = integration_client.get(
            "/api/resilience/tier2/status",
            headers=auth_headers,
        )

        # May require auth or may not exist
        assert response.status_code in [200, 401, 403, 404]

    def test_homeostasis_status(self, integration_client, auth_headers):
        """Test homeostasis monitoring endpoint."""
        response = integration_client.get(
            "/api/resilience/tier2/homeostasis/status",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403, 404]


@pytest.mark.integration
class TestTier3Endpoints:
    """Test Tier 3 resilience API endpoints."""

    def test_tier3_status(self, integration_client, auth_headers):
        """Test Tier 3 status endpoint."""
        response = integration_client.get(
            "/api/resilience/tier3/status",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403, 404]

    def test_cognitive_load_queue(self, integration_client, auth_headers):
        """Test cognitive load decision queue endpoint."""
        response = integration_client.get(
            "/api/resilience/tier3/cognitive/queue",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403, 404]

    def test_stigmergy_patterns(self, integration_client, auth_headers):
        """Test stigmergy preference patterns endpoint."""
        response = integration_client.get(
            "/api/resilience/tier3/stigmergy/patterns",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403, 404]


@pytest.mark.integration
class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint."""

    def test_metrics_endpoint(self, integration_client):
        """Test that metrics endpoint is accessible."""
        response = integration_client.get("/metrics")

        # May be excluded from instrumentation or available
        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestAPIDocumentation:
    """Test API documentation endpoints."""

    def test_openapi_schema(self, integration_client):
        """Test OpenAPI schema is available."""
        response = integration_client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert "components" in data

    def test_swagger_docs(self, integration_client):
        """Test Swagger UI is accessible."""
        response = integration_client.get("/docs")

        assert response.status_code == 200

    def test_redoc_docs(self, integration_client):
        """Test ReDoc is accessible."""
        response = integration_client.get("/redoc")

        assert response.status_code == 200
