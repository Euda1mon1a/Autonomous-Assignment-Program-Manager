"""Smoke tests for resilience API routes with minimal dependencies."""

from datetime import datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient


def test_defense_level_route(client: TestClient):
    response = client.post(
        "/api/v1/resilience/defense-level", json={"coverage_rate": 0.9}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["level"]
    assert data["level_number"] == 2
    assert data["recommended_actions"]


def test_utilization_threshold_route(client: TestClient):
    payload = {
        "available_faculty": 10,
        "required_blocks": 5,
        "blocks_per_faculty_per_day": 2,
        "days_in_period": 7,
    }
    response = client.post("/api/v1/resilience/utilization-threshold", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "utilization_rate" in data
    assert "level" in data
    assert "recommendations" in data


def test_burnout_rt_route(client: TestClient):
    payload = {"burned_out_provider_ids": ["provider-1", "provider-2"]}
    response = client.post("/api/v1/resilience/burnout/rt", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["rt"] >= 0
    assert data["status"]
    assert data["interventions"]


def test_circuit_breaker_routes(client: TestClient, monkeypatch):
    class DummyRegistry:
        def health_check(self):
            return {
                "total_breakers": 1,
                "closed_breakers": 1,
                "open_breakers": 0,
                "half_open_breakers": 0,
                "open_breaker_names": [],
                "half_open_breaker_names": [],
                "overall_failure_rate": 0.0,
            }

        def get_all_statuses(self):
            return {
                "db": {
                    "state": "closed",
                    "failure_rate": 0.0,
                    "total_requests": 1,
                    "successful_requests": 1,
                    "failed_requests": 0,
                    "rejected_requests": 0,
                    "consecutive_failures": 0,
                    "consecutive_successes": 1,
                    "opened_at": None,
                    "last_failure_time": None,
                    "last_success_time": datetime.utcnow().isoformat(),
                }
            }

    from app.resilience.circuit_breaker import registry as registry_module

    monkeypatch.setattr(registry_module, "get_registry", lambda: DummyRegistry())

    response = client.get("/api/v1/resilience/circuit-breakers")
    assert response.status_code == 200
    data = response.json()
    assert data["total_breakers"] == 1
    assert data["overall_health"]

    response = client.get("/api/v1/resilience/circuit-breakers/health")
    assert response.status_code == 200
    data = response.json()
    assert data["metrics"]["total_requests"] == 1
    assert data["severity"]


def test_tier2_status_route(client: TestClient, monkeypatch):
    import app.api.routes.resilience as resilience_routes

    class DummyService:
        def get_tier2_status(self):
            return {
                "generated_at": datetime.utcnow().isoformat(),
                "homeostasis": {
                    "state": "homeostasis",
                    "feedback_loops_healthy": 2,
                    "feedback_loops_deviating": 0,
                    "average_allostatic_load": 0.1,
                    "positive_feedback_risks": [],
                },
                "blast_radius": {
                    "total_zones": 1,
                    "zones_healthy": 1,
                    "zones_critical": 0,
                    "containment_active": False,
                    "containment_level": "none",
                },
                "equilibrium": {
                    "state": "stable",
                    "current_coverage_rate": 0.9,
                    "compensation_debt": 0.0,
                    "sustainability_score": 0.9,
                },
                "tier2_status": "healthy",
                "recommendations": [],
            }

    monkeypatch.setattr(
        resilience_routes, "get_resilience_service", lambda _db: DummyService()
    )

    response = client.get("/api/v1/resilience/tier2/status")
    assert response.status_code == 200
    data = response.json()
    assert data["tier2_status"] == "healthy"
    assert data["equilibrium_state"] == "stable"


def test_tier3_status_route(client: TestClient, monkeypatch):
    import app.api.routes.resilience as resilience_routes

    class DummyService:
        def get_tier3_status(self):
            return {
                "generated_at": datetime.utcnow().isoformat(),
                "pending_decisions": 0,
                "urgent_decisions": 0,
                "estimated_cognitive_cost": 0.0,
                "can_auto_decide": 0,
                "total_trails": 0,
                "active_trails": 0,
                "average_strength": 0.0,
                "popular_slots": [],
                "unpopular_slots": [],
                "total_hubs": 0,
                "catastrophic_hubs": 0,
                "critical_hubs": 0,
                "active_protection_plans": 0,
                "pending_cross_training": 0,
                "tier3_status": "healthy",
                "issues": [],
                "recommendations": [],
            }

    monkeypatch.setattr(
        resilience_routes, "get_resilience_service", lambda _db: DummyService()
    )

    response = client.get("/api/v1/resilience/tier3/status")
    assert response.status_code == 200
    data = response.json()
    assert data["tier3_status"] == "healthy"
    assert data["total_hubs"] == 0


def test_history_endpoints_empty(client: TestClient):
    response = client.get("/api/v1/resilience/history/health")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0

    response = client.get("/api/v1/resilience/history/events")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


def test_health_route_with_dummy_report(client: TestClient, monkeypatch):
    import app.api.routes.resilience as resilience_routes

    class DummyUtilization:
        utilization_rate = 0.5
        level = SimpleNamespace(value="green")
        buffer_remaining = 0.5
        total_capacity = 10
        current_assignments = 5

    class DummyReport:
        timestamp = datetime.utcnow()
        overall_status = "healthy"
        utilization = DummyUtilization()
        defense_level = SimpleNamespace(name="PREVENTION")
        redundancy_status = [
            SimpleNamespace(
                function_name="coverage",
                status="N+2",
                current_available=10,
                required_minimum=8,
                redundancy_level=2,
            )
        ]
        load_shedding_level = SimpleNamespace(name="NORMAL")
        active_fallbacks = []
        n1_pass = True
        n2_pass = True
        phase_transition_risk = "low"
        immediate_actions = []
        watch_items = []

    class DummyService:
        _crisis_mode = False

        def check_health(self, **_kwargs):
            return DummyReport()

    monkeypatch.setattr(
        resilience_routes, "get_resilience_service", lambda _db: DummyService()
    )

    response = client.get("/api/v1/resilience/health", params={"persist": False})
    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] == "healthy"
    assert data["utilization"]["level"] == "GREEN"


def test_fallbacks_list_route(client: TestClient, monkeypatch):
    import app.api.routes.resilience as resilience_routes

    class DummyFallbacks:
        def get_fallback(self, _scenario):
            return None

    class DummyService:
        fallback = DummyFallbacks()

    monkeypatch.setattr(
        resilience_routes, "get_resilience_service", lambda _db: DummyService()
    )

    response = client.get("/api/v1/resilience/fallbacks")
    assert response.status_code == 200
    data = response.json()
    assert "fallbacks" in data


def test_load_shedding_status_route(client: TestClient, monkeypatch):
    import app.api.routes.resilience as resilience_routes

    class DummyStatus:
        level = SimpleNamespace(name="NORMAL")
        activities_suspended = []
        activities_protected = []
        capacity_available = 1.0
        capacity_demand = 0.5

    class DummySacrifice:
        def get_status(self):
            return DummyStatus()

    class DummyService:
        sacrifice = DummySacrifice()

    monkeypatch.setattr(
        resilience_routes, "get_resilience_service", lambda _db: DummyService()
    )

    response = client.get("/api/v1/resilience/load-shedding")
    assert response.status_code == 200
    data = response.json()
    assert data["level"] == "NORMAL"
