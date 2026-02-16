"""
Tests for health deep endpoint.

Validates that `/api/v1/health/deep` reports connectivity and status
for critical dependencies.
"""

from datetime import datetime

from app.api.routes import health as health_routes
from app.health.aggregator import HealthCheckResult, HealthStatus


def _health_result(status: HealthStatus) -> HealthCheckResult:
    now = datetime.utcnow()
    return HealthCheckResult(
        service="database",
        status=status,
        response_time_ms=12.5,
        timestamp=now,
        details={"pool": {"size": 5}},
    )


def test_health_deep_reports_connectivity(client, monkeypatch):
    """Healthy dependencies should yield healthy status with connected flags."""

    async def fake_check_service(name: str):
        return _health_result(HealthStatus.HEALTHY)

    monkeypatch.setattr(
        health_routes.health_aggregator, "check_service", fake_check_service
    )
    monkeypatch.setattr(health_routes, "_read_backend_version", lambda: "1.2.3")

    response = client.get("/api/v1/health/deep")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["version"] == "1.2.3"
    assert payload["checks"]["database"]["connected"] is True
    assert payload["checks"]["redis"]["connected"] is True


def test_health_deep_flags_unhealthy_dependencies(client, monkeypatch):
    """Exceptions and unhealthy statuses should surface as disconnected."""

    async def fake_check_service(name: str):
        if name == "database":
            return _health_result(HealthStatus.UNHEALTHY)
        raise RuntimeError("connection refused")

    monkeypatch.setattr(
        health_routes.health_aggregator, "check_service", fake_check_service
    )
    monkeypatch.setattr(health_routes, "_read_backend_version", lambda: "1.2.3")

    response = client.get("/api/v1/health/deep")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "unhealthy"
    assert payload["checks"]["database"]["connected"] is False
    assert payload["checks"]["redis"]["connected"] is False
    assert payload["checks"]["redis"]["status"] == "unhealthy"
