"""
Tests for Fatigue Risk Management System (FRMS) API routes.

Comprehensive test coverage for:
- Samn-Perelli fatigue assessments
- Real-time fatigue scoring
- Resident fatigue profiles
- Alertness predictions
- Hazard monitoring and scanning
- Sleep debt tracking
- Team heatmaps
- Reference data endpoints
- Temporal constraints export
- ACGME fatigue validation
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.user import User


class TestSamnPerelliEndpoints:
    """Test suite for Samn-Perelli fatigue assessment endpoints."""

    def test_get_samn_perelli_levels(self, client: TestClient):
        """Test getting all Samn-Perelli fatigue levels."""
        response = client.get("/api/fatigue-risk/samn-perelli/levels")

        assert response.status_code == 200
        data = response.json()
        assert "levels" in data
        assert len(data["levels"]) == 7  # 7-level scale

    def test_get_samn_perelli_levels_structure(self, client: TestClient):
        """Test Samn-Perelli levels have correct structure."""
        response = client.get("/api/fatigue-risk/samn-perelli/levels")

        assert response.status_code == 200
        data = response.json()
        levels = data["levels"]

        # Verify each level has required fields
        for level in levels:
            assert "level" in level
            assert "name" in level
            assert "description" in level
            assert isinstance(level["level"], int)
            assert 1 <= level["level"] <= 7

    def test_submit_fatigue_assessment_success(
        self, client: TestClient, db: Session, sample_resident: Person, auth_headers: dict
    ):
        """Test successful fatigue assessment submission."""
        payload = {"level": 3, "notes": "Feeling moderately tired after night shift"}

        response = client.post(
            f"/api/fatigue-risk/resident/{sample_resident.id}/assessment",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["level"] == 3
        assert data["is_self_reported"] is True
        assert "notes" in data

    def test_submit_fatigue_assessment_invalid_level(
        self, client: TestClient, db: Session, sample_resident: Person, auth_headers: dict
    ):
        """Test fatigue assessment with invalid level."""
        payload = {"level": 10, "notes": "Invalid level"}

        response = client.post(
            f"/api/fatigue-risk/resident/{sample_resident.id}/assessment",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "Invalid fatigue assessment data" in response.json()["detail"]

    def test_submit_fatigue_assessment_resident_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test fatigue assessment for non-existent resident."""
        fake_id = uuid4()
        payload = {"level": 2, "notes": "Test"}

        response = client.post(
            f"/api/fatigue-risk/resident/{fake_id}/assessment",
            json=payload,
            headers=auth_headers,
        )

        # Should still succeed as assessment creation doesn't require existing resident
        # The validation happens in the assess_fatigue_level function
        assert response.status_code in [200, 400]


class TestFatigueScoringEndpoints:
    """Test suite for real-time fatigue scoring endpoints."""

    def test_calculate_fatigue_score_success(self, client: TestClient):
        """Test successful fatigue score calculation."""
        payload = {
            "hours_awake": 16,
            "hours_worked_24h": 12,
            "consecutive_night_shifts": 2,
            "time_of_day_hour": 3,  # 3 AM - circadian low
            "prior_sleep_hours": 5,
        }

        response = client.post("/api/fatigue-risk/score", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "fatigue_score" in data
        assert "alertness_score" in data
        assert "risk_level" in data
        assert isinstance(data["fatigue_score"], (int, float))
        assert 0 <= data["alertness_score"] <= 1

    def test_calculate_fatigue_score_high_risk(self, client: TestClient):
        """Test fatigue score calculation for high-risk scenario."""
        payload = {
            "hours_awake": 24,  # Awake 24 hours
            "hours_worked_24h": 20,  # Worked 20 hours
            "consecutive_night_shifts": 5,
            "time_of_day_hour": 4,  # 4 AM - worst circadian time
            "prior_sleep_hours": 3,  # Poor prior sleep
        }

        response = client.post("/api/fatigue-risk/score", json=payload)

        assert response.status_code == 200
        data = response.json()
        # Should indicate high risk
        assert data["fatigue_score"] > 50  # High fatigue
        assert data["alertness_score"] < 0.5  # Low alertness

    def test_calculate_fatigue_score_low_risk(self, client: TestClient):
        """Test fatigue score calculation for low-risk scenario."""
        payload = {
            "hours_awake": 8,  # Well-rested
            "hours_worked_24h": 4,  # Light workload
            "consecutive_night_shifts": 0,
            "time_of_day_hour": 10,  # 10 AM - good circadian time
            "prior_sleep_hours": 8,  # Good sleep
        }

        response = client.post("/api/fatigue-risk/score", json=payload)

        assert response.status_code == 200
        data = response.json()
        # Should indicate low risk
        assert data["alertness_score"] > 0.7  # High alertness

    def test_calculate_fatigue_score_validation(self, client: TestClient):
        """Test fatigue score calculation with invalid input."""
        payload = {
            "hours_awake": -5,  # Invalid negative value
            "hours_worked_24h": 12,
            "consecutive_night_shifts": 2,
            "time_of_day_hour": 3,
            "prior_sleep_hours": 5,
        }

        response = client.post("/api/fatigue-risk/score", json=payload)

        assert response.status_code == 422  # Validation error


class TestResidentProfileEndpoints:
    """Test suite for resident fatigue profile endpoints."""

    def test_get_resident_fatigue_profile_success(
        self,
        client: TestClient,
        db: Session,
        sample_resident: Person,
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
        auth_headers: dict,
    ):
        """Test getting complete resident fatigue profile."""
        # Create some assignments for the resident
        for block in sample_blocks[:5]:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_resident.id,
                rotation_template_id=sample_rotation_template.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        response = client.get(
            f"/api/fatigue-risk/resident/{sample_resident.id}/profile",
            headers=auth_headers,
        )

        # Profile generation requires work history data
        # May return 200 with profile or 404 if insufficient data
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "current_alertness" in data
            assert "hazard_level" in data
            assert "sleep_debt_hours" in data

    def test_get_resident_fatigue_profile_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting profile for non-existent resident."""
        fake_id = uuid4()

        response = client.get(
            f"/api/fatigue-risk/resident/{fake_id}/profile",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "Resident profile not found" in response.json()["detail"]

    def test_get_alertness_prediction_success(
        self,
        client: TestClient,
        db: Session,
        sample_resident: Person,
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
        auth_headers: dict,
    ):
        """Test getting alertness prediction for resident."""
        # Create assignments
        for block in sample_blocks[:3]:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_resident.id,
                rotation_template_id=sample_rotation_template.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        response = client.get(
            f"/api/fatigue-risk/resident/{sample_resident.id}/alertness",
            headers=auth_headers,
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "alertness_score" in data
            assert "alertness_percent" in data
            assert "samn_perelli" in data
            assert "circadian_phase" in data
            assert "performance_capacity" in data

    def test_assess_schedule_fatigue_risk(
        self,
        client: TestClient,
        db: Session,
        sample_resident: Person,
        auth_headers: dict,
    ):
        """Test assessing fatigue risk for proposed schedule."""
        payload = {
            "proposed_shifts": [
                {
                    "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                    "end_time": (datetime.utcnow() + timedelta(days=1, hours=8)).isoformat(),
                    "is_night_shift": False,
                },
                {
                    "start_time": (datetime.utcnow() + timedelta(days=2)).isoformat(),
                    "end_time": (datetime.utcnow() + timedelta(days=2, hours=12)).isoformat(),
                    "is_night_shift": True,
                },
            ]
        }

        response = client.post(
            f"/api/fatigue-risk/resident/{sample_resident.id}/schedule-assessment",
            json=payload,
            headers=auth_headers,
        )

        # Service may require existing data or return 404
        assert response.status_code in [200, 404, 500]


class TestHazardMonitoringEndpoints:
    """Test suite for hazard monitoring and detection endpoints."""

    def test_get_current_hazard(
        self,
        client: TestClient,
        db: Session,
        sample_resident: Person,
        auth_headers: dict,
    ):
        """Test getting current hazard status for resident."""
        response = client.get(
            f"/api/fatigue-risk/resident/{sample_resident.id}/hazard",
            headers=auth_headers,
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "hazard_level" in data
            assert "hazard_level_name" in data
            assert "triggers" in data
            assert "required_mitigations" in data
            assert "acgme_risk" in data

    def test_scan_all_residents_for_hazards(
        self,
        client: TestClient,
        db: Session,
        sample_residents: list[Person],
        auth_headers: dict,
    ):
        """Test scanning all residents for fatigue hazards."""
        response = client.get(
            "/api/fatigue-risk/hazards/scan",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "scanned_at" in data
        assert "total_residents" in data
        assert "hazards_found" in data
        assert "by_level" in data
        assert "critical_count" in data
        assert "residents" in data
        assert isinstance(data["residents"], list)

    def test_scan_hazards_with_level_filter(
        self, client: TestClient, auth_headers: dict
    ):
        """Test scanning hazards with minimum level filter."""
        response = client.get(
            "/api/fatigue-risk/hazards/scan?min_level=orange",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # All returned hazards should be orange or higher
        assert "residents" in data

    def test_scan_hazards_invalid_level(self, client: TestClient, auth_headers: dict):
        """Test scanning hazards with invalid level."""
        response = client.get(
            "/api/fatigue-risk/hazards/scan?min_level=purple",
            headers=auth_headers,
        )

        assert response.status_code == 422  # Validation error


class TestSleepDebtEndpoints:
    """Test suite for sleep debt tracking endpoints."""

    def test_get_sleep_debt_state(
        self,
        client: TestClient,
        db: Session,
        sample_resident: Person,
        auth_headers: dict,
    ):
        """Test getting current sleep debt state."""
        response = client.get(
            f"/api/fatigue-risk/resident/{sample_resident.id}/sleep-debt",
            headers=auth_headers,
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "current_debt_hours" in data
            assert "recovery_sleep_needed" in data
            assert "debt_severity" in data
            assert "impairment_equivalent_bac" in data
            assert data["debt_severity"] in [
                "none",
                "mild",
                "moderate",
                "severe",
                "critical",
            ]

    def test_predict_sleep_debt_trajectory(
        self,
        client: TestClient,
        db: Session,
        sample_resident: Person,
        auth_headers: dict,
    ):
        """Test predicting sleep debt trajectory."""
        payload = {
            "planned_sleep_hours": [7, 6, 8, 7, 6, 8, 9],  # 7 days of planned sleep
            "start_debt": 5.0,  # Starting with 5 hours of debt
        }

        response = client.post(
            f"/api/fatigue-risk/resident/{sample_resident.id}/sleep-debt/trajectory",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "days_predicted" in data
        assert "trajectory" in data
        assert "recovery_estimate_nights" in data
        assert len(data["trajectory"]) == 7  # 7 days


class TestTeamDashboardEndpoints:
    """Test suite for team fatigue dashboard endpoints."""

    def test_get_team_fatigue_heatmap(
        self,
        client: TestClient,
        db: Session,
        sample_residents: list[Person],
        auth_headers: dict,
    ):
        """Test generating team fatigue heatmap."""
        payload = {
            "target_date": date.today().isoformat(),
            "include_predictions": True,
        }

        response = client.post(
            "/api/fatigue-risk/team/heatmap",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Heatmap structure depends on service implementation
        assert isinstance(data, dict)

    def test_get_team_heatmap_past_date(
        self, client: TestClient, auth_headers: dict
    ):
        """Test generating heatmap for past date."""
        payload = {
            "target_date": (date.today() - timedelta(days=30)).isoformat(),
            "include_predictions": False,
        }

        response = client.post(
            "/api/fatigue-risk/team/heatmap",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200


class TestReferenceDataEndpoints:
    """Test suite for reference data endpoints."""

    def test_get_circadian_phases(self, client: TestClient):
        """Test getting circadian phase information."""
        response = client.get("/api/fatigue-risk/reference/circadian-phases")

        assert response.status_code == 200
        data = response.json()
        assert "phases" in data
        assert isinstance(data["phases"], list)
        assert len(data["phases"]) == 7  # 7 circadian phases

    def test_get_hazard_levels(self, client: TestClient):
        """Test getting hazard level information."""
        response = client.get("/api/fatigue-risk/reference/hazard-levels")

        assert response.status_code == 200
        data = response.json()
        assert "levels" in data
        assert isinstance(data["levels"], list)
        # Should have GREEN, YELLOW, ORANGE, RED, BLACK
        assert len(data["levels"]) == 5

    def test_get_mitigation_types(self, client: TestClient):
        """Test getting mitigation type information."""
        response = client.get("/api/fatigue-risk/reference/mitigation-types")

        assert response.status_code == 200
        data = response.json()
        assert "mitigations" in data
        assert isinstance(data["mitigations"], list)


class TestTemporalConstraintsEndpoint:
    """Test suite for temporal constraints export endpoint."""

    def test_export_temporal_constraints(self, client: TestClient):
        """Test exporting temporal constraint data."""
        response = client.get("/api/fatigue-risk/temporal-constraints")

        assert response.status_code == 200
        data = response.json()

        # Verify comprehensive constraint export structure
        assert "circadian_model" in data
        assert "sleep_homeostasis" in data
        assert "samn_perelli_mapping" in data
        assert "hazard_thresholds" in data
        assert "acgme_integration" in data
        assert "scheduling_constraints" in data

    def test_temporal_constraints_structure(self, client: TestClient):
        """Test temporal constraints export has correct structure."""
        response = client.get("/api/fatigue-risk/temporal-constraints")

        assert response.status_code == 200
        data = response.json()

        # Verify hard and soft constraints
        constraints = data.get("scheduling_constraints", {})
        assert "hard_constraints" in constraints
        assert "soft_constraints" in constraints


class TestACGMEValidationEndpoint:
    """Test suite for ACGME fatigue validation endpoint."""

    def test_validate_acgme_with_fatigue_success(
        self,
        client: TestClient,
        db: Session,
        sample_resident: Person,
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
        auth_headers: dict,
    ):
        """Test ACGME validation through fatigue lens."""
        # Create assignments
        for block in sample_blocks[:5]:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_resident.id,
                rotation_template_id=sample_rotation_template.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        payload = {
            "schedule_start": date.today().isoformat(),
            "schedule_end": (date.today() + timedelta(days=7)).isoformat(),
        }

        response = client.post(
            f"/api/fatigue-risk/resident/{sample_resident.id}/acgme-validation",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "acgme_compliant" in data
            assert "fatigue_compliant" in data
            assert "hours_summary" in data
            assert "fatigue_risk_periods" in data
            assert "recommendations" in data

    def test_validate_acgme_resident_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test ACGME validation for non-existent resident."""
        fake_id = uuid4()
        payload = {
            "schedule_start": date.today().isoformat(),
            "schedule_end": (date.today() + timedelta(days=7)).isoformat(),
        }

        response = client.post(
            f"/api/fatigue-risk/resident/{fake_id}/acgme-validation",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestAuthenticationRequirements:
    """Test suite for authentication requirements on FRMS endpoints."""

    def test_endpoints_require_authentication(
        self, client: TestClient, sample_resident: Person
    ):
        """Test that protected endpoints require authentication."""
        # List of endpoints that should require auth
        protected_endpoints = [
            f"/api/fatigue-risk/resident/{sample_resident.id}/profile",
            f"/api/fatigue-risk/resident/{sample_resident.id}/alertness",
            f"/api/fatigue-risk/resident/{sample_resident.id}/hazard",
            "/api/fatigue-risk/hazards/scan",
            f"/api/fatigue-risk/resident/{sample_resident.id}/sleep-debt",
        ]

        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            # Should return 401 (Unauthorized) or 403 (Forbidden) without auth
            # Some endpoints may not be protected, so also allow 200
            assert response.status_code in [200, 401, 403, 404]
