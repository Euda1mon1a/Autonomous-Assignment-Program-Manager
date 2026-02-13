"""Tests for deep health endpoint."""

from datetime import datetime, timezone, UTC
from unittest.mock import AsyncMock, patch

from app.health.aggregator import HealthCheckResult, HealthStatus


def _make_service_result(
    service: str, status: HealthStatus = HealthStatus.HEALTHY
) -> HealthCheckResult:
    """Build a HealthCheckResult for deterministic route tests."""
    return HealthCheckResult(
        service=service,
        status=status,
        response_time_ms=12.5,
        timestamp=datetime.now(UTC),
        details={"source": "test"},
        error=None,
        warning=None,
    )


class TestDeepHealthEndpoint:
    """Behavioral tests for /api/v1/health/deep."""

    def test_deep_health_reports_connectivity_and_version(self, client):
        """Endpoint should include dependency status and backend version."""
        database_result = _make_service_result("database", HealthStatus.HEALTHY)
        redis_result = _make_service_result("redis", HealthStatus.DEGRADED)

        with (
            patch(
                "app.api.routes.health.health_aggregator.check_service",
                new=AsyncMock(side_effect=[database_result, redis_result]),
            ),
            patch("app.api.routes.health._read_backend_version", return_value="9.9.9"),
        ):
            response = client.get("/api/v1/health/deep")

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "healthy"
        assert payload["version"] == "9.9.9"
        assert payload["checks"]["database"]["connected"] is True
        assert payload["checks"]["database"]["status"] == "healthy"
        assert payload["checks"]["redis"]["connected"] is True
        assert payload["checks"]["redis"]["status"] == "degraded"

    def test_deep_health_marks_unhealthy_when_dependency_fails(self, client):
        """Dependency failures should mark overall deep health as unhealthy."""
        database_result = _make_service_result("database", HealthStatus.HEALTHY)

        with (
            patch(
                "app.api.routes.health.health_aggregator.check_service",
                new=AsyncMock(
                    side_effect=[database_result, RuntimeError("redis down")]
                ),
            ),
            patch("app.api.routes.health._read_backend_version", return_value="1.0.0"),
        ):
            response = client.get("/api/health/deep")

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "unhealthy"
        assert payload["checks"]["database"]["connected"] is True
        assert payload["checks"]["redis"]["connected"] is False
        assert payload["checks"]["redis"]["status"] == "unhealthy"
        assert "redis down" in payload["checks"]["redis"]["error"]
