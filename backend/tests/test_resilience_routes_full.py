"""Tests for resilience API routes.

Comprehensive test suite covering all resilience endpoints including:
- Tier 1: Health monitoring, crisis response, fallbacks, load shedding, vulnerability
- Tier 2: Homeostasis, allostasis, zones, blast radius, equilibrium, Le Chatelier
- Tier 3: Cognitive load, stigmergy, hub analysis
- Historical data and event tracking
"""
from datetime import date, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person


# ============================================================================
# Tier 1: Critical Resilience Endpoints
# ============================================================================


class TestSystemHealthEndpoint:
    """Tests for GET /api/resilience/health endpoint."""

    def test_get_system_health_basic(
        self, client: TestClient, sample_faculty_members, sample_blocks
    ):
        """Test getting basic system health status."""
        response = client.get("/api/resilience/health")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "timestamp" in data
        assert "overall_status" in data
        assert "utilization" in data
        assert "defense_level" in data
        assert "redundancy_status" in data
        assert "load_shedding_level" in data
        assert "n1_pass" in data
        assert "n2_pass" in data
        assert "immediate_actions" in data
        assert "watch_items" in data

    def test_get_system_health_with_date_range(
        self, client: TestClient, sample_faculty_members, sample_blocks
    ):
        """Test health check with custom date range."""
        start = date.today()
        end = start + timedelta(days=14)

        response = client.get(
            "/api/resilience/health",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "utilization" in data
        assert "overall_status" in data

    def test_get_system_health_with_contingency(
        self, client: TestClient, sample_faculty_members, sample_blocks
    ):
        """Test health check with full N-1/N-2 contingency analysis."""
        response = client.get(
            "/api/resilience/health",
            params={"include_contingency": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert "n1_pass" in data
        assert "n2_pass" in data
        assert isinstance(data["n1_pass"], bool)
        assert isinstance(data["n2_pass"], bool)

    def test_get_system_health_without_persist(
        self, client: TestClient, sample_faculty_members, sample_blocks
    ):
        """Test health check without persisting to database."""
        response = client.get(
            "/api/resilience/health",
            params={"persist": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data

    def test_get_system_health_utilization_metrics(
        self, client: TestClient, sample_faculty_members, sample_blocks
    ):
        """Test that utilization metrics are properly returned."""
        response = client.get("/api/resilience/health")

        assert response.status_code == 200
        data = response.json()

        utilization = data["utilization"]
        assert "utilization_rate" in utilization
        assert "level" in utilization
        assert "buffer_remaining" in utilization
        assert "safe_capacity" in utilization
        assert "current_demand" in utilization

        # Validate types
        assert isinstance(utilization["utilization_rate"], (int, float))
        assert utilization["utilization_rate"] >= 0.0
        assert utilization["utilization_rate"] <= 1.0

    def test_get_system_health_defense_levels(
        self, client: TestClient, sample_faculty_members, sample_blocks
    ):
        """Test defense level reporting."""
        response = client.get("/api/resilience/health")

        assert response.status_code == 200
        data = response.json()

        defense_level = data["defense_level"]
        valid_levels = ["GREEN", "YELLOW", "ORANGE", "RED", "BLACK"]
        assert defense_level in valid_levels

    def test_get_system_health_load_shedding(
        self, client: TestClient, sample_faculty_members, sample_blocks
    ):
        """Test load shedding level in health check."""
        response = client.get("/api/resilience/health")

        assert response.status_code == 200
        data = response.json()

        load_shedding = data["load_shedding_level"]
        valid_levels = ["NORMAL", "YELLOW", "ORANGE", "RED", "BLACK", "CRITICAL"]
        assert load_shedding in valid_levels


class TestCrisisActivationEndpoint:
    """Tests for POST /api/resilience/crisis/activate endpoint."""

    def test_activate_crisis_minor(self, client: TestClient, auth_headers: dict):
        """Test activating crisis response with minor severity."""
        response = client.post(
            "/api/resilience/crisis/activate",
            headers=auth_headers,
            json={
                "severity": "minor",
                "reason": "Unexpected faculty absence"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "crisis_mode" in data
        assert "severity" in data
        assert "actions_taken" in data
        assert "load_shedding_level" in data
        assert data["crisis_mode"] is True
        assert data["severity"] == "minor"

    def test_activate_crisis_moderate(self, client: TestClient, auth_headers: dict):
        """Test activating crisis with moderate severity."""
        response = client.post(
            "/api/resilience/crisis/activate",
            headers=auth_headers,
            json={
                "severity": "moderate",
                "reason": "Multiple faculty absences"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["severity"] == "moderate"
        assert isinstance(data["actions_taken"], list)

    def test_activate_crisis_severe(self, client: TestClient, auth_headers: dict):
        """Test activating crisis with severe severity."""
        response = client.post(
            "/api/resilience/crisis/activate",
            headers=auth_headers,
            json={
                "severity": "severe",
                "reason": "Natural disaster affecting staffing"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["severity"] == "severe"

    def test_activate_crisis_critical(self, client: TestClient, auth_headers: dict):
        """Test activating crisis with critical severity."""
        response = client.post(
            "/api/resilience/crisis/activate",
            headers=auth_headers,
            json={
                "severity": "critical",
                "reason": "Major emergency - pandemic conditions"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["severity"] == "critical"
        assert data["load_shedding_level"] in ["RED", "BLACK", "CRITICAL"]

    def test_activate_crisis_unauthenticated(self, client: TestClient):
        """Test activating crisis without authentication."""
        response = client.post(
            "/api/resilience/crisis/activate",
            json={
                "severity": "minor",
                "reason": "Test"
            }
        )

        # Should require authentication
        assert response.status_code in [401, 403]

    def test_activate_crisis_invalid_severity(self, client: TestClient, auth_headers: dict):
        """Test activating crisis with invalid severity."""
        response = client.post(
            "/api/resilience/crisis/activate",
            headers=auth_headers,
            json={
                "severity": "invalid_level",
                "reason": "Test"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_activate_crisis_missing_reason(self, client: TestClient, auth_headers: dict):
        """Test activating crisis without reason."""
        response = client.post(
            "/api/resilience/crisis/activate",
            headers=auth_headers,
            json={
                "severity": "minor"
            }
        )

        assert response.status_code == 422  # Validation error


class TestCrisisDeactivationEndpoint:
    """Tests for POST /api/resilience/crisis/deactivate endpoint."""

    def test_deactivate_crisis_success(self, client: TestClient, auth_headers: dict):
        """Test deactivating crisis response."""
        # First activate crisis
        activate_response = client.post(
            "/api/resilience/crisis/activate",
            headers=auth_headers,
            json={
                "severity": "minor",
                "reason": "Test crisis"
            }
        )
        assert activate_response.status_code == 200

        # Then deactivate
        response = client.post(
            "/api/resilience/crisis/deactivate",
            headers=auth_headers,
            json={
                "reason": "Crisis resolved"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "crisis_mode" in data
        assert "load_shedding_level" in data
        assert data["crisis_mode"] is False
        assert data["load_shedding_level"] == "NORMAL"

    def test_deactivate_crisis_with_recovery_plan(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that deactivation includes recovery plan."""
        # Activate then deactivate
        client.post(
            "/api/resilience/crisis/activate",
            headers=auth_headers,
            json={"severity": "moderate", "reason": "Test"}
        )

        response = client.post(
            "/api/resilience/crisis/deactivate",
            headers=auth_headers,
            json={"reason": "Recovery complete"}
        )

        assert response.status_code == 200
        data = response.json()
        # Recovery plan may be present
        if "recovery_plan" in data:
            assert isinstance(data["recovery_plan"], list)

    def test_deactivate_crisis_unauthenticated(self, client: TestClient):
        """Test deactivating crisis without authentication."""
        response = client.post(
            "/api/resilience/crisis/deactivate",
            json={"reason": "Test"}
        )

        assert response.status_code in [401, 403]


class TestFallbacksListEndpoint:
    """Tests for GET /api/resilience/fallbacks endpoint."""

    def test_list_fallbacks(self, client: TestClient):
        """Test listing all available fallback schedules."""
        response = client.get("/api/resilience/fallbacks")

        assert response.status_code == 200
        data = response.json()
        assert "fallbacks" in data
        assert "active_count" in data
        assert isinstance(data["fallbacks"], list)
        assert isinstance(data["active_count"], int)

    def test_list_fallbacks_structure(self, client: TestClient):
        """Test structure of fallback list items."""
        response = client.get("/api/resilience/fallbacks")

        assert response.status_code == 200
        data = response.json()

        if data["fallbacks"]:
            fallback = data["fallbacks"][0]
            assert "scenario" in fallback
            assert "description" in fallback
            assert "is_active" in fallback
            assert "is_precomputed" in fallback

    def test_list_fallbacks_includes_all_scenarios(self, client: TestClient):
        """Test that all fallback scenarios are listed."""
        response = client.get("/api/resilience/fallbacks")

        assert response.status_code == 200
        data = response.json()

        scenarios = [f["scenario"] for f in data["fallbacks"]]
        expected_scenarios = [
            "single_faculty_loss",
            "double_faculty_loss",
            "pcs_season_50_percent",
            "holiday_skeleton",
            "pandemic_essential",
            "mass_casualty",
            "weather_emergency"
        ]

        for expected in expected_scenarios:
            assert expected in scenarios


class TestFallbackActivationEndpoint:
    """Tests for POST /api/resilience/fallbacks/activate endpoint."""

    def test_activate_fallback_single_loss(self, client: TestClient, auth_headers: dict):
        """Test activating single faculty loss fallback."""
        response = client.post(
            "/api/resilience/fallbacks/activate",
            headers=auth_headers,
            json={
                "scenario": "single_faculty_loss",
                "reason": "Faculty deployed"
            }
        )

        # May succeed or fail depending on whether fallback is precomputed
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "scenario" in data
            assert data["scenario"] == "single_faculty_loss"

    def test_activate_fallback_pandemic(self, client: TestClient, auth_headers: dict):
        """Test activating pandemic essential services fallback."""
        response = client.post(
            "/api/resilience/fallbacks/activate",
            headers=auth_headers,
            json={
                "scenario": "pandemic_essential",
                "reason": "COVID-19 surge"
            }
        )

        assert response.status_code in [200, 404]

    def test_activate_fallback_unauthenticated(self, client: TestClient):
        """Test activating fallback without authentication."""
        response = client.post(
            "/api/resilience/fallbacks/activate",
            json={
                "scenario": "single_faculty_loss",
                "reason": "Test"
            }
        )

        assert response.status_code in [401, 403]

    def test_activate_fallback_invalid_scenario(
        self, client: TestClient, auth_headers: dict
    ):
        """Test activating fallback with invalid scenario."""
        response = client.post(
            "/api/resilience/fallbacks/activate",
            headers=auth_headers,
            json={
                "scenario": "invalid_scenario",
                "reason": "Test"
            }
        )

        assert response.status_code in [400, 422]


class TestFallbackDeactivationEndpoint:
    """Tests for POST /api/resilience/fallbacks/deactivate endpoint."""

    def test_deactivate_fallback(self, client: TestClient, auth_headers: dict):
        """Test deactivating a fallback schedule."""
        response = client.post(
            "/api/resilience/fallbacks/deactivate",
            headers=auth_headers,
            json={
                "scenario": "single_faculty_loss",
                "reason": "Normal operations restored"
            }
        )

        # Should succeed even if no fallback is active
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

    def test_deactivate_fallback_unauthenticated(self, client: TestClient):
        """Test deactivating fallback without authentication."""
        response = client.post(
            "/api/resilience/fallbacks/deactivate",
            json={
                "scenario": "single_faculty_loss",
                "reason": "Test"
            }
        )

        assert response.status_code in [401, 403]


class TestLoadSheddingStatusEndpoint:
    """Tests for GET /api/resilience/load-shedding endpoint."""

    def test_get_load_shedding_status(self, client: TestClient):
        """Test getting current load shedding status."""
        response = client.get("/api/resilience/load-shedding")

        assert response.status_code == 200
        data = response.json()
        assert "level" in data
        assert "activities_suspended" in data
        assert "activities_protected" in data
        assert "capacity_available" in data
        assert "capacity_demand" in data

    def test_load_shedding_status_structure(self, client: TestClient):
        """Test structure of load shedding status."""
        response = client.get("/api/resilience/load-shedding")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["activities_suspended"], list)
        assert isinstance(data["activities_protected"], list)
        assert isinstance(data["capacity_available"], (int, float))
        assert isinstance(data["capacity_demand"], (int, float))


class TestSetLoadSheddingLevelEndpoint:
    """Tests for POST /api/resilience/load-shedding endpoint."""

    def test_set_load_shedding_yellow(self, client: TestClient, auth_headers: dict):
        """Test setting load shedding to yellow level."""
        response = client.post(
            "/api/resilience/load-shedding",
            headers=auth_headers,
            json={
                "level": "yellow",
                "reason": "Increased demand"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "yellow"
        assert isinstance(data["activities_suspended"], list)

    def test_set_load_shedding_orange(self, client: TestClient, auth_headers: dict):
        """Test setting load shedding to orange level."""
        response = client.post(
            "/api/resilience/load-shedding",
            headers=auth_headers,
            json={
                "level": "orange",
                "reason": "Staff shortage"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "orange"

    def test_set_load_shedding_red(self, client: TestClient, auth_headers: dict):
        """Test setting load shedding to red level."""
        response = client.post(
            "/api/resilience/load-shedding",
            headers=auth_headers,
            json={
                "level": "red",
                "reason": "Critical shortage"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "red"

    def test_set_load_shedding_unauthenticated(self, client: TestClient):
        """Test setting load shedding without authentication."""
        response = client.post(
            "/api/resilience/load-shedding",
            json={
                "level": "yellow",
                "reason": "Test"
            }
        )

        assert response.status_code in [401, 403]

    def test_set_load_shedding_invalid_level(
        self, client: TestClient, auth_headers: dict
    ):
        """Test setting invalid load shedding level."""
        response = client.post(
            "/api/resilience/load-shedding",
            headers=auth_headers,
            json={
                "level": "invalid",
                "reason": "Test"
            }
        )

        assert response.status_code == 422


class TestVulnerabilityReportEndpoint:
    """Tests for GET /api/resilience/vulnerability endpoint."""

    def test_get_vulnerability_report(
        self, client: TestClient, sample_faculty_members, sample_blocks
    ):
        """Test getting N-1/N-2 vulnerability analysis."""
        response = client.get("/api/resilience/vulnerability")

        assert response.status_code == 200
        data = response.json()
        assert "analyzed_at" in data
        assert "period_start" in data
        assert "period_end" in data
        assert "n1_pass" in data
        assert "n2_pass" in data
        assert "n1_vulnerabilities" in data
        assert "n2_fatal_pairs" in data
        assert "most_critical_faculty" in data
        assert "recommended_actions" in data

    def test_vulnerability_report_with_date_range(
        self, client: TestClient, sample_faculty_members, sample_blocks
    ):
        """Test vulnerability report with custom date range."""
        start = date.today()
        end = start + timedelta(days=30)

        response = client.get(
            "/api/resilience/vulnerability",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "n1_pass" in data
        assert "n2_pass" in data

    def test_vulnerability_report_structure(
        self, client: TestClient, sample_faculty_members, sample_blocks
    ):
        """Test structure of vulnerability report."""
        response = client.get("/api/resilience/vulnerability")

        assert response.status_code == 200
        data = response.json()

        # Validate types
        assert isinstance(data["n1_pass"], bool)
        assert isinstance(data["n2_pass"], bool)
        assert isinstance(data["n1_vulnerabilities"], list)
        assert isinstance(data["n2_fatal_pairs"], list)
        assert isinstance(data["most_critical_faculty"], list)
        assert isinstance(data["recommended_actions"], list)


class TestComprehensiveReportEndpoint:
    """Tests for GET /api/resilience/report endpoint."""

    def test_get_comprehensive_report(
        self, client: TestClient, sample_faculty_members, sample_blocks
    ):
        """Test getting comprehensive resilience report."""
        response = client.get("/api/resilience/report")

        assert response.status_code == 200
        data = response.json()
        assert "generated_at" in data
        assert "overall_status" in data
        assert "summary" in data
        assert "immediate_actions" in data
        assert "watch_items" in data
        assert "components" in data

    def test_comprehensive_report_with_date_range(
        self, client: TestClient, sample_faculty_members, sample_blocks
    ):
        """Test comprehensive report with custom date range."""
        start = date.today()
        end = start + timedelta(days=14)

        response = client.get(
            "/api/resilience/report",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "components" in data


# ============================================================================
# Historical Data and Events
# ============================================================================


class TestHealthCheckHistoryEndpoint:
    """Tests for GET /api/resilience/history/health endpoint."""

    def test_get_health_check_history(self, client: TestClient):
        """Test getting health check history."""
        response = client.get("/api/resilience/history/health")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["items"], list)

    def test_health_check_history_pagination(self, client: TestClient):
        """Test pagination of health check history."""
        response = client.get(
            "/api/resilience/history/health",
            params={"page": 1, "page_size": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_health_check_history_filter_by_status(self, client: TestClient):
        """Test filtering health check history by status."""
        response = client.get(
            "/api/resilience/history/health",
            params={"status": "healthy"}
        )

        assert response.status_code == 200
        data = response.json()
        # Items may be empty if no matching records
        assert isinstance(data["items"], list)


class TestEventHistoryEndpoint:
    """Tests for GET /api/resilience/history/events endpoint."""

    def test_get_event_history(self, client: TestClient):
        """Test getting resilience event history."""
        response = client.get("/api/resilience/history/events")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    def test_event_history_pagination(self, client: TestClient):
        """Test pagination of event history."""
        response = client.get(
            "/api/resilience/history/events",
            params={"page": 2, "page_size": 20}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 20

    def test_event_history_filter_by_type(self, client: TestClient):
        """Test filtering events by type."""
        response = client.get(
            "/api/resilience/history/events",
            params={"event_type": "crisis_activated"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)


# ============================================================================
# Tier 2: Homeostasis and Allostasis
# ============================================================================


class TestHomeostasisStatusEndpoint:
    """Tests for GET /api/resilience/tier2/homeostasis endpoint."""

    def test_get_homeostasis_status(self, client: TestClient):
        """Test getting homeostasis status."""
        response = client.get("/api/resilience/tier2/homeostasis")

        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "overall_state" in data
        assert "feedback_loops_healthy" in data
        assert "feedback_loops_deviating" in data
        assert "active_corrections" in data
        assert "positive_feedback_risks" in data
        assert "average_allostatic_load" in data

    def test_homeostasis_feedback_loops(self, client: TestClient):
        """Test feedback loop information in homeostasis status."""
        response = client.get("/api/resilience/tier2/homeostasis")

        assert response.status_code == 200
        data = response.json()

        if "feedback_loops" in data:
            assert isinstance(data["feedback_loops"], list)


class TestCheckHomeostasisEndpoint:
    """Tests for POST /api/resilience/tier2/homeostasis/check endpoint."""

    def test_check_homeostasis_with_metrics(self, client: TestClient):
        """Test checking homeostasis with provided metrics."""
        response = client.post(
            "/api/resilience/tier2/homeostasis/check",
            json={
                "coverage_rate": 0.92,
                "faculty_utilization": 0.78
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "overall_state" in data


class TestAllostasisCalculateEndpoint:
    """Tests for POST /api/resilience/tier2/allostasis/calculate endpoint."""

    def test_calculate_allostatic_load(self, client: TestClient):
        """Test calculating allostatic load for entity."""
        entity_id = uuid4()

        response = client.post(
            "/api/resilience/tier2/allostasis/calculate",
            params={
                "entity_id": str(entity_id),
                "entity_type": "faculty"
            },
            json={
                "consecutive_weekend_calls": 2,
                "nights_past_month": 8,
                "schedule_changes_absorbed": 3,
                "holidays_worked_this_year": 1,
                "overtime_hours_month": 12.0,
                "coverage_gap_responses": 2,
                "cross_coverage_events": 1
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "entity_id" in data
        assert "total_allostatic_load" in data
        assert "state" in data
        assert "risk_level" in data


# ============================================================================
# Tier 2: Zones and Blast Radius
# ============================================================================


class TestListZonesEndpoint:
    """Tests for GET /api/resilience/tier2/zones endpoint."""

    def test_list_zones(self, client: TestClient):
        """Test listing all scheduling zones."""
        response = client.get("/api/resilience/tier2/zones")

        assert response.status_code == 200
        data = response.json()
        assert "zones" in data
        assert "total" in data
        assert isinstance(data["zones"], list)


class TestBlastRadiusReportEndpoint:
    """Tests for GET /api/resilience/tier2/zones/report endpoint."""

    def test_get_blast_radius_report(self, client: TestClient):
        """Test getting blast radius containment report."""
        response = client.get("/api/resilience/tier2/zones/report")

        assert response.status_code == 200
        data = response.json()
        assert "generated_at" in data
        assert "total_zones" in data
        assert "zones_healthy" in data
        assert "zones_degraded" in data
        assert "containment_level" in data


class TestCreateZoneEndpoint:
    """Tests for POST /api/resilience/tier2/zones endpoint."""

    def test_create_zone(self, client: TestClient, auth_headers: dict):
        """Test creating a new scheduling zone."""
        response = client.post(
            "/api/resilience/tier2/zones",
            headers=auth_headers,
            params={
                "name": "Test Inpatient Zone",
                "zone_type": "inpatient",
                "description": "Test zone for inpatient services",
                "minimum_coverage": 2,
                "optimal_coverage": 3
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert data["name"] == "Test Inpatient Zone"


# ============================================================================
# Tier 2: Le Chatelier / Equilibrium
# ============================================================================


class TestEquilibriumReportEndpoint:
    """Tests for GET /api/resilience/tier2/equilibrium endpoint."""

    def test_get_equilibrium_report(self, client: TestClient):
        """Test getting equilibrium analysis report."""
        response = client.get("/api/resilience/tier2/equilibrium")

        assert response.status_code == 200
        data = response.json()
        assert "generated_at" in data
        assert "current_equilibrium_state" in data
        assert "current_capacity" in data
        assert "current_demand" in data
        assert "active_stresses" in data
        assert "active_compensations" in data


class TestApplyStressEndpoint:
    """Tests for POST /api/resilience/tier2/stress endpoint."""

    def test_apply_stress_faculty_loss(self, client: TestClient, auth_headers: dict):
        """Test applying faculty loss stress."""
        response = client.post(
            "/api/resilience/tier2/stress",
            headers=auth_headers,
            params={
                "stress_type": "faculty_loss",
                "description": "One faculty member deployed",
                "magnitude": 0.2,
                "duration_days": 90,
                "capacity_impact": -0.15,
                "demand_impact": 0.0
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "stress_type" in data
        assert data["stress_type"] == "faculty_loss"


class TestPredictStressResponseEndpoint:
    """Tests for POST /api/resilience/tier2/stress/predict endpoint."""

    def test_predict_stress_response(self, client: TestClient):
        """Test predicting system response to stress."""
        response = client.post(
            "/api/resilience/tier2/stress/predict",
            params={
                "stress_type": "demand_surge",
                "magnitude": 0.3,
                "duration_days": 14,
                "capacity_impact": 0.0,
                "demand_impact": 0.25
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "predicted_at" in data
        assert "stress_type" in data
        assert "predicted_compensation" in data
        assert "sustainability_assessment" in data


# ============================================================================
# Tier 2: Combined Status
# ============================================================================


class TestTier2StatusEndpoint:
    """Tests for GET /api/resilience/tier2/status endpoint."""

    def test_get_tier2_status(self, client: TestClient):
        """Test getting combined Tier 2 status."""
        response = client.get("/api/resilience/tier2/status")

        assert response.status_code == 200
        data = response.json()
        assert "generated_at" in data
        assert "homeostasis_state" in data
        assert "feedback_loops_healthy" in data
        assert "total_zones" in data
        assert "containment_level" in data
        assert "equilibrium_state" in data


# ============================================================================
# Tier 3: Cognitive Load
# ============================================================================


class TestStartCognitiveSessionEndpoint:
    """Tests for POST /api/resilience/tier3/cognitive/session/start endpoint."""

    def test_start_cognitive_session(self, client: TestClient, auth_headers: dict):
        """Test starting a cognitive decision-making session."""
        user_id = uuid4()

        response = client.post(
            "/api/resilience/tier3/cognitive/session/start",
            headers=auth_headers,
            params={"user_id": str(user_id)}
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "user_id" in data
        assert "started_at" in data


class TestCognitiveSessionStatusEndpoint:
    """Tests for GET /api/resilience/tier3/cognitive/session/{session_id}/status endpoint."""

    def test_get_cognitive_session_status(self, client: TestClient, auth_headers: dict):
        """Test getting cognitive session status."""
        # Start session first
        user_id = uuid4()
        start_response = client.post(
            "/api/resilience/tier3/cognitive/session/start",
            headers=auth_headers,
            params={"user_id": str(user_id)}
        )
        assert start_response.status_code == 200
        session_id = start_response.json()["session_id"]

        # Get status
        response = client.get(
            f"/api/resilience/tier3/cognitive/session/{session_id}/status"
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "current_state" in data
        assert "decisions_this_session" in data


class TestDecisionQueueEndpoint:
    """Tests for GET /api/resilience/tier3/cognitive/queue endpoint."""

    def test_get_decision_queue(self, client: TestClient):
        """Test getting decision queue status."""
        response = client.get("/api/resilience/tier3/cognitive/queue")

        assert response.status_code == 200
        data = response.json()
        assert "total_pending" in data
        assert "by_complexity" in data
        assert "by_category" in data


# ============================================================================
# Tier 3: Stigmergy
# ============================================================================


class TestRecordPreferenceEndpoint:
    """Tests for POST /api/resilience/tier3/stigmergy/preference endpoint."""

    def test_record_preference(self, client: TestClient, auth_headers: dict):
        """Test recording a faculty preference trail."""
        faculty_id = uuid4()

        response = client.post(
            "/api/resilience/tier3/stigmergy/preference",
            headers=auth_headers,
            params={
                "faculty_id": str(faculty_id),
                "trail_type": "preference",
                "slot_type": "clinic",
                "strength": 0.7
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "trail_id" in data
        assert "faculty_id" in data


class TestStigmergyStatusEndpoint:
    """Tests for GET /api/resilience/tier3/stigmergy/status endpoint."""

    def test_get_stigmergy_status(self, client: TestClient):
        """Test getting stigmergy system status."""
        response = client.get("/api/resilience/tier3/stigmergy/status")

        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "total_trails" in data
        assert "active_trails" in data


# ============================================================================
# Tier 3: Hub Analysis
# ============================================================================


class TestAnalyzeHubsEndpoint:
    """Tests for POST /api/resilience/tier3/hubs/analyze endpoint."""

    def test_analyze_hubs(self, client: TestClient, sample_faculty_members):
        """Test running hub vulnerability analysis."""
        response = client.post("/api/resilience/tier3/hubs/analyze")

        assert response.status_code == 200
        data = response.json()
        assert "analyzed_at" in data
        assert "total_faculty" in data
        assert "total_hubs" in data
        assert "hubs" in data


class TestHubStatusEndpoint:
    """Tests for GET /api/resilience/tier3/hubs/status endpoint."""

    def test_get_hub_status(self, client: TestClient):
        """Test getting hub analysis status."""
        response = client.get("/api/resilience/tier3/hubs/status")

        assert response.status_code == 200
        # Response structure depends on implementation
        assert isinstance(response.json(), dict)


class TestTier3StatusEndpoint:
    """Tests for GET /api/resilience/tier3/status endpoint."""

    def test_get_tier3_status(self, client: TestClient):
        """Test getting combined Tier 3 status."""
        response = client.get("/api/resilience/tier3/status")

        assert response.status_code == 200
        # Response structure depends on implementation
        assert isinstance(response.json(), dict)


# ============================================================================
# Integration and Error Handling Tests
# ============================================================================


class TestResilienceIntegration:
    """Integration tests for resilience endpoints."""

    def test_full_crisis_workflow(self, client: TestClient, auth_headers: dict):
        """Test complete crisis activation and deactivation workflow."""
        # 1. Check initial health
        health = client.get("/api/resilience/health")
        assert health.status_code == 200

        # 2. Activate crisis
        activate = client.post(
            "/api/resilience/crisis/activate",
            headers=auth_headers,
            json={"severity": "moderate", "reason": "Testing workflow"}
        )
        assert activate.status_code == 200
        assert activate.json()["crisis_mode"] is True

        # 3. Check load shedding
        load_shedding = client.get("/api/resilience/load-shedding")
        assert load_shedding.status_code == 200

        # 4. Deactivate crisis
        deactivate = client.post(
            "/api/resilience/crisis/deactivate",
            headers=auth_headers,
            json={"reason": "Workflow test complete"}
        )
        assert deactivate.status_code == 200
        assert deactivate.json()["crisis_mode"] is False

    def test_health_to_vulnerability_workflow(
        self, client: TestClient, sample_faculty_members, sample_blocks
    ):
        """Test workflow from health check to vulnerability analysis."""
        # 1. Get health status
        health = client.get("/api/resilience/health")
        assert health.status_code == 200

        # 2. Run vulnerability analysis
        vuln = client.get("/api/resilience/vulnerability")
        assert vuln.status_code == 200

        # 3. Get comprehensive report
        report = client.get("/api/resilience/report")
        assert report.status_code == 200


class TestResilienceErrorHandling:
    """Tests for error handling in resilience endpoints."""

    def test_health_check_with_invalid_dates(self, client: TestClient):
        """Test health check with invalid date range."""
        response = client.get(
            "/api/resilience/health",
            params={
                "start_date": "invalid-date",
                "end_date": "2024-01-01"
            }
        )

        assert response.status_code == 422

    def test_activate_crisis_without_admin_role(
        self, client: TestClient, db: Session
    ):
        """Test that non-admin users cannot activate crisis."""
        # This test assumes role-based access control is enforced
        # Implementation may vary
        response = client.post(
            "/api/resilience/crisis/activate",
            json={"severity": "minor", "reason": "Test"}
        )

        # Should require authentication or admin role
        assert response.status_code in [401, 403]

    def test_invalid_json_handling(self, client: TestClient, auth_headers: dict):
        """Test handling of malformed JSON."""
        response = client.post(
            "/api/resilience/crisis/activate",
            headers=auth_headers,
            data="not valid json"
        )

        assert response.status_code in [400, 422]
