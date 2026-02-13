"""
Tests for health dashboard endpoint.

Validates that `/api/v1/health/dashboard` returns a consolidated payload
for frontend dashboards and produces alert severity as expected.
"""

from datetime import datetime

from app.api.routes import health as health_routes
from app.health.aggregator import (
    AggregatedHealthResult,
    HealthCheckResult,
    HealthStatus,
)


def _build_result(
    *,
    database_status: HealthStatus = HealthStatus.HEALTHY,
    redis_status: HealthStatus = HealthStatus.HEALTHY,
    celery_status: HealthStatus = HealthStatus.HEALTHY,
) -> AggregatedHealthResult:
    now = datetime.utcnow()
    return AggregatedHealthResult(
        status=(
            HealthStatus.UNHEALTHY
            if database_status == HealthStatus.UNHEALTHY
            else HealthStatus.DEGRADED
            if celery_status == HealthStatus.DEGRADED
            else HealthStatus.HEALTHY
        ),
        timestamp=now,
        services={
            "database": HealthCheckResult(
                service="database",
                status=database_status,
                response_time_ms=15.0,
                timestamp=now,
                details={"connection_pool": {"size": 10, "checked_out": 2}},
            ),
            "redis": HealthCheckResult(
                service="redis",
                status=redis_status,
                response_time_ms=4.0,
                timestamp=now,
                details={"memory_used_mb": 128.0, "connected_clients": 7},
            ),
            "celery": HealthCheckResult(
                service="celery",
                status=celery_status,
                response_time_ms=45.0,
                timestamp=now,
                details={"workers_online": 3, "scheduled_tasks": 12},
                warning="worker latency elevated"
                if celery_status == HealthStatus.DEGRADED
                else None,
            ),
        },
        summary={
            "total_services": 3,
            "healthy_count": 2 if celery_status == HealthStatus.DEGRADED else 3,
            "degraded_count": 1 if celery_status == HealthStatus.DEGRADED else 0,
            "unhealthy_count": 1 if database_status == HealthStatus.UNHEALTHY else 0,
            "avg_response_time_ms": 21.33,
        },
    )


def test_health_dashboard_returns_consolidated_payload(client, monkeypatch):
    """Endpoint returns core metadata, services, summary, and metrics."""

    async def fake_check_detailed():
        return _build_result(celery_status=HealthStatus.DEGRADED)

    def fake_get_metrics():
        return {
            "history_enabled": True,
            "history_size": 5,
            "uptime_percentage": 99.0,
            "recent_checks": 5,
            "avg_response_times_ms": {"database": 15.0, "redis": 4.0, "celery": 45.0},
        }

    monkeypatch.setattr(
        health_routes.health_aggregator, "check_detailed", fake_check_detailed
    )
    monkeypatch.setattr(
        health_routes.health_aggregator, "get_metrics", fake_get_metrics
    )

    response = client.get("/api/v1/health/dashboard")
    assert response.status_code == 200

    payload = response.json()
    assert payload["overall_status"] == "degraded"
    assert payload["environment"] in {"development", "production"}
    assert isinstance(payload["uptime_seconds"], int)
    assert payload["summary"]["total_services"] == 3
    assert "database" in payload["services"]
    assert "redis" in payload["services"]
    assert "celery" in payload["services"]
    assert payload["metrics"]["history_enabled"] is True
    assert len(payload["alerts"]) == 1
    assert payload["alerts"][0]["severity"] == "warning"


def test_health_dashboard_marks_critical_service_failures(client, monkeypatch):
    """Unhealthy database should produce a critical severity alert."""

    async def fake_check_detailed():
        return _build_result(database_status=HealthStatus.UNHEALTHY)

    monkeypatch.setattr(
        health_routes.health_aggregator, "check_detailed", fake_check_detailed
    )
    monkeypatch.setattr(
        health_routes.health_aggregator,
        "get_metrics",
        lambda: {"history_enabled": False, "history_size": 0},
    )

    response = client.get("/api/v1/health/dashboard")
    assert response.status_code == 200

    payload = response.json()
    db_alerts = [a for a in payload["alerts"] if a["id"] == "health-database"]
    assert len(db_alerts) == 1
    assert db_alerts[0]["severity"] == "critical"
