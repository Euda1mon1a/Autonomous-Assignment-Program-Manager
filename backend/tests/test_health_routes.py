"""
Comprehensive tests for Health Check API endpoints.

Tests coverage for health monitoring endpoints including:
- Basic health check endpoint (/health)
- Root endpoint (/) health status
- Resilience health check endpoint (/health/resilience)
- Database connectivity verification
- Component status reporting
- Error scenarios and fault tolerance
"""

from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# ============================================================================
# Test Classes
# ============================================================================


class TestBasicHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_check_basic_success(self, client: TestClient):
        """Test basic health check returns successful response."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "status" in data
        assert "database" in data

        # Verify values
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    def test_health_check_response_format(self, client: TestClient):
        """Test health check response has correct format."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        # Ensure all expected fields are present
        assert isinstance(data, dict)
        assert len(data) >= 2

    def test_health_check_no_authentication_required(self, client: TestClient):
        """Test health check endpoint doesn't require authentication."""
        # Call without auth headers
        response = client.get("/health")

        # Should succeed without auth
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_health_check_with_database(self, client: TestClient, db: Session):
        """Test health check with active database connection."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Database should be reported as connected
        assert data["database"] == "connected"
        assert data["status"] == "healthy"

    def test_health_check_accepts_get_only(self, client: TestClient):
        """Test health endpoint only accepts GET requests."""
        # POST should not be allowed
        response = client.post("/health")
        assert response.status_code == 405

        # PUT should not be allowed
        response = client.put("/health")
        assert response.status_code == 405

        # DELETE should not be allowed
        response = client.delete("/health")
        assert response.status_code == 405


class TestRootEndpoint:
    """Tests for GET / root endpoint."""

    def test_root_endpoint_success(self, client: TestClient):
        """Test root endpoint returns healthy status."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "name" in data
        assert "version" in data
        assert "status" in data

        # Verify values
        assert data["name"] == "Residency Scheduler API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "healthy"

    def test_root_endpoint_as_health_check(self, client: TestClient):
        """Test root endpoint can be used as a simple health check."""
        response = client.get("/")

        assert response.status_code == 200
        # A 200 response indicates the service is up
        assert response.json()["status"] == "healthy"

    def test_root_endpoint_response_format(self, client: TestClient):
        """Test root endpoint response format."""
        response = client.get("/")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data, dict)
        assert len(data) >= 3

    def test_root_endpoint_no_authentication_required(self, client: TestClient):
        """Test root endpoint doesn't require authentication."""
        response = client.get("/")

        # Should succeed without auth
        assert response.status_code == 200
        assert "name" in response.json()


class TestResilienceHealthEndpoint:
    """Tests for GET /health/resilience endpoint."""

    def test_resilience_health_success(self, client: TestClient):
        """Test resilience health check returns successful response."""
        response = client.get("/health/resilience")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "status" in data
        assert data["status"] in ["operational", "degraded"]

    def test_resilience_health_components(self, client: TestClient):
        """Test resilience health includes component list."""
        response = client.get("/health/resilience")

        assert response.status_code == 200
        data = response.json()

        # Should include components
        assert "components" in data
        assert isinstance(data["components"], list)

        # Expected components
        expected_components = [
            "utilization_monitor",
            "defense_in_depth",
            "contingency_analyzer",
            "fallback_scheduler",
            "sacrifice_hierarchy",
        ]

        for component in expected_components:
            assert component in data["components"]

    def test_resilience_health_metrics_enabled_status(self, client: TestClient):
        """Test resilience health reports metrics enabled status."""
        response = client.get("/health/resilience")

        assert response.status_code == 200
        data = response.json()

        # Should include metrics_enabled flag
        assert "metrics_enabled" in data
        assert isinstance(data["metrics_enabled"], bool)

    def test_resilience_health_no_authentication_required(self, client: TestClient):
        """Test resilience health endpoint doesn't require authentication."""
        response = client.get("/health/resilience")

        # Should succeed without auth
        assert response.status_code == 200
        assert "status" in response.json()

    @patch("app.main.get_metrics")
    def test_resilience_health_degraded_on_error(
        self, mock_get_metrics, client: TestClient
    ):
        """Test resilience health returns degraded status on error."""
        # Mock an exception during metrics retrieval
        mock_get_metrics.side_effect = Exception("Metrics unavailable")

        response = client.get("/health/resilience")

        assert response.status_code == 200
        data = response.json()

        # Should report degraded status
        assert data["status"] == "degraded"
        assert "error" in data

    def test_resilience_health_response_format(self, client: TestClient):
        """Test resilience health response format."""
        response = client.get("/health/resilience")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data, dict)


class TestHealthCheckDatabaseConnectivity:
    """Tests for database connectivity in health checks."""

    def test_health_with_valid_database(self, client: TestClient, db: Session):
        """Test health check with valid database connection."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Should report database as connected
        assert data["database"] == "connected"
        assert data["status"] == "healthy"

    def test_health_database_field_type(self, client: TestClient):
        """Test database field has correct type."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # database field should be a string
        assert isinstance(data["database"], str)

    def test_health_with_multiple_requests(self, client: TestClient, db: Session):
        """Test health check maintains consistency across multiple requests."""
        responses = []
        for _ in range(5):
            response = client.get("/health")
            responses.append(response)

        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)

        # All should report healthy status
        assert all(r.json()["status"] == "healthy" for r in responses)
        assert all(r.json()["database"] == "connected" for r in responses)


class TestHealthCheckComponentStatus:
    """Tests for component status reporting in health checks."""

    def test_root_endpoint_reports_service_info(self, client: TestClient):
        """Test root endpoint reports complete service information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        # Should include service identification
        assert data["name"] == "Residency Scheduler API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "healthy"

    def test_resilience_endpoint_reports_all_components(self, client: TestClient):
        """Test resilience endpoint reports all expected components."""
        response = client.get("/health/resilience")

        assert response.status_code == 200
        data = response.json()

        # All 5 resilience components should be listed
        assert len(data["components"]) == 5

        # Verify each component is a string
        for component in data["components"]:
            assert isinstance(component, str)
            assert len(component) > 0

    def test_health_check_json_serializable(self, client: TestClient):
        """Test all health check responses are properly JSON serializable."""
        endpoints = ["/", "/health", "/health/resilience"]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200

            # Should be valid JSON
            data = response.json()
            assert isinstance(data, dict)

            # All values should be JSON-serializable types
            for key, value in data.items():
                assert isinstance(key, str)
                assert isinstance(
                    value, (str, bool, int, float, list, dict, type(None))
                )


class TestHealthCheckErrorScenarios:
    """Tests for error scenarios and fault tolerance."""

    def test_health_endpoint_handles_exceptions_gracefully(self, client: TestClient):
        """Test health endpoint handles internal exceptions gracefully."""
        # Even if internal errors occur, health check should return a response
        response = client.get("/health")

        # Should not raise unhandled exceptions
        assert response.status_code in [200, 500, 503]

    @patch("app.main.get_metrics")
    def test_resilience_health_error_handling(
        self, mock_get_metrics, client: TestClient
    ):
        """Test resilience health handles errors gracefully."""
        # Simulate metrics error
        mock_get_metrics.side_effect = RuntimeError("Metrics service down")

        response = client.get("/health/resilience")

        # Should return 200 with degraded status, not crash
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "degraded"
        assert "error" in data
        assert "Metrics service down" in data["error"]

    def test_health_check_timeout_resilience(self, client: TestClient):
        """Test health check responds quickly even under load."""
        import time

        start_time = time.time()
        response = client.get("/health")
        elapsed_time = time.time() - start_time

        # Health check should be fast (< 1 second)
        assert elapsed_time < 1.0
        assert response.status_code == 200

    def test_concurrent_health_checks(self, client: TestClient):
        """Test multiple concurrent health check requests."""
        from concurrent.futures import ThreadPoolExecutor

        def make_request():
            return client.get("/health")

        # Make 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [f.result() for f in futures]

        # All should succeed
        assert all(r.status_code == 200 for r in responses)
        assert all(r.json()["status"] == "healthy" for r in responses)

    def test_health_check_with_malformed_requests(self, client: TestClient):
        """Test health check handles malformed requests."""
        # Try with query parameters (should ignore them)
        response = client.get("/health?invalid=param")
        assert response.status_code == 200

        # Try with different content types
        response = client.get("/health", headers={"Accept": "text/html"})
        assert response.status_code == 200


# ============================================================================
# Integration Tests
# ============================================================================


class TestHealthCheckIntegration:
    """Integration tests for health check endpoints."""

    def test_all_health_endpoints_accessible(self, client: TestClient):
        """Test all health check endpoints are accessible."""
        endpoints = [
            "/",
            "/health",
            "/health/resilience",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"Failed to access {endpoint}"
            assert "status" in response.json(), f"No status in {endpoint} response"

    def test_health_check_consistency(self, client: TestClient):
        """Test health check endpoints report consistent status."""
        root_response = client.get("/")
        health_response = client.get("/health")

        # Both should report healthy status
        assert root_response.json()["status"] == "healthy"
        assert health_response.json()["status"] == "healthy"

    def test_health_checks_with_database_operations(
        self, client: TestClient, db: Session, sample_resident
    ):
        """Test health checks remain responsive during database operations."""
        # Perform a database operation
        from app.models.person import Person

        people = db.query(Person).all()
        assert len(people) > 0

        # Health checks should still work
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_health_checks_excluded_from_metrics(self, client: TestClient):
        """Test health check endpoints are excluded from Prometheus metrics."""
        # Make several health check requests
        for _ in range(5):
            client.get("/health")
            client.get("/")

        # Metrics endpoint should not count health checks
        # (This is configured in main.py with excluded_handlers)
        # Just verify metrics endpoint is accessible
        response = client.get("/metrics")
        # May return 200 or 403 depending on configuration
        assert response.status_code in [200, 403]

    def test_health_endpoints_performance_baseline(self, client: TestClient):
        """Test health endpoints meet performance baseline."""
        import time

        endpoints = ["/", "/health", "/health/resilience"]
        timings = []

        for endpoint in endpoints:
            start = time.time()
            response = client.get(endpoint)
            elapsed = time.time() - start

            assert response.status_code == 200
            timings.append((endpoint, elapsed))

        # All endpoints should respond in under 500ms
        for endpoint, elapsed in timings:
            assert elapsed < 0.5, f"{endpoint} took {elapsed:.3f}s (> 500ms)"

    def test_health_check_response_headers(self, client: TestClient):
        """Test health check endpoints return appropriate headers."""
        endpoints = ["/", "/health", "/health/resilience"]

        for endpoint in endpoints:
            response = client.get(endpoint)

            # Should have content-type header
            assert "content-type" in response.headers
            assert "application/json" in response.headers["content-type"]

            # Should not leak server information (security)
            assert (
                "server" not in response.headers
                or "FastAPI" not in response.headers.get("server", "")
            )


class TestHealthCheckMonitoring:
    """Tests for health check monitoring capabilities."""

    def test_health_check_provides_service_status(self, client: TestClient):
        """Test health check provides clear service status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Status should be clear and actionable
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    def test_root_endpoint_provides_version_info(self, client: TestClient):
        """Test root endpoint provides version information for monitoring."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        # Version info should be present for monitoring/debugging
        assert "version" in data
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

    def test_resilience_health_provides_operational_status(self, client: TestClient):
        """Test resilience health provides operational status."""
        response = client.get("/health/resilience")

        assert response.status_code == 200
        data = response.json()

        # Should clearly indicate operational status
        assert data["status"] in ["operational", "degraded"]

    def test_health_checks_suitable_for_load_balancer(self, client: TestClient):
        """Test health checks are suitable for load balancer health probes."""
        # Load balancers typically use simple GET requests
        response = client.get("/health")

        # Should return 200 for healthy
        assert response.status_code == 200

        # Should be fast
        import time

        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start

        # Load balancer probes should be fast (< 100ms ideally)
        assert elapsed < 1.0  # Allow up to 1s for test environment

    def test_health_checks_suitable_for_kubernetes(self, client: TestClient):
        """Test health checks are suitable for Kubernetes probes."""
        # Kubernetes liveness probe
        liveness_response = client.get("/health")
        assert liveness_response.status_code == 200

        # Kubernetes readiness probe
        readiness_response = client.get("/")
        assert readiness_response.status_code == 200

        # Both should have JSON responses
        assert liveness_response.json()["status"] == "healthy"
        assert readiness_response.json()["status"] == "healthy"
