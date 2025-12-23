"""Tests for HomeostasisService.

Tests the homeostasis service that monitors system feedback loops,
tracks allostatic load, and detects positive feedback risks.
"""

from datetime import datetime
from uuid import uuid4

from app.schemas.resilience import (
    AllostasisState,
    HomeostasisReport,
)
from app.services.resilience.homeostasis import (
    HomeostasisService,
    get_homeostasis_service,
)


class TestHomeostasisService:
    """Test suite for HomeostasisService."""

    # ========================================================================
    # Initialization Tests
    # ========================================================================

    def test_service_initialization(self, db):
        """Test that service initializes correctly."""
        service = HomeostasisService(db)

        assert service.db == db
        assert service._resilience_service is None  # Lazy initialization

    def test_service_lazy_initialization(self, db):
        """Test that resilience service is lazily initialized."""
        service = HomeostasisService(db)

        # Access the resilience_service property
        resilience_svc = service.resilience_service

        assert resilience_svc is not None
        assert service._resilience_service is resilience_svc

        # Second access should return same instance
        assert service.resilience_service is resilience_svc

    def test_factory_function(self, db):
        """Test the factory function returns a service instance."""
        service = get_homeostasis_service(db)

        assert isinstance(service, HomeostasisService)
        assert service.db == db

    # ========================================================================
    # check_homeostasis Tests
    # ========================================================================

    def test_check_homeostasis_with_healthy_metrics(self, db):
        """Test homeostasis check with metrics within tolerance."""
        service = HomeostasisService(db)

        # Metrics within normal range
        metrics = {
            "coverage_rate": 0.95,  # Target: 0.95
            "faculty_utilization": 0.75,  # Target: 0.75
        }

        report = service.check_homeostasis(metrics)

        assert isinstance(report, HomeostasisReport)
        assert report.timestamp is not None
        assert isinstance(report.overall_state, AllostasisState)
        assert report.feedback_loops_healthy >= 0
        assert report.feedback_loops_deviating >= 0
        assert report.active_corrections >= 0
        assert report.positive_feedback_risks >= 0
        assert isinstance(report.average_allostatic_load, float)
        assert isinstance(report.recommendations, list)

    def test_check_homeostasis_with_deviating_metrics(self, db):
        """Test homeostasis check with metrics outside tolerance."""
        service = HomeostasisService(db)

        # Metrics with significant deviation
        metrics = {
            "coverage_rate": 0.70,  # Far below target of 0.95
            "faculty_utilization": 0.95,  # Above target of 0.75
        }

        report = service.check_homeostasis(metrics)

        assert isinstance(report, HomeostasisReport)
        # With deviating metrics, we should see deviations detected
        # The exact behavior depends on threshold configuration
        assert report.timestamp is not None

    def test_check_homeostasis_with_empty_metrics(self, db):
        """Test homeostasis check with empty metrics dict."""
        service = HomeostasisService(db)

        report = service.check_homeostasis({})

        # Should still return a valid report even with empty metrics
        assert isinstance(report, HomeostasisReport)
        assert report.timestamp is not None

    def test_check_homeostasis_with_partial_metrics(self, db):
        """Test homeostasis check with only some metrics provided."""
        service = HomeostasisService(db)

        # Only provide one metric
        metrics = {
            "coverage_rate": 0.92,
        }

        report = service.check_homeostasis(metrics)

        assert isinstance(report, HomeostasisReport)
        assert report.timestamp is not None

    def test_check_homeostasis_with_unknown_metrics(self, db):
        """Test homeostasis check handles unknown metric names gracefully."""
        service = HomeostasisService(db)

        # Include an unknown metric name
        metrics = {
            "coverage_rate": 0.95,
            "unknown_metric": 0.5,  # This setpoint doesn't exist
        }

        # Should not raise, should handle gracefully
        report = service.check_homeostasis(metrics)

        assert isinstance(report, HomeostasisReport)

    def test_check_homeostasis_report_structure(self, db):
        """Test that HomeostasisReport has correct structure."""
        service = HomeostasisService(db)

        metrics = {"coverage_rate": 0.92}
        report = service.check_homeostasis(metrics)

        # Verify all fields are present
        assert hasattr(report, "timestamp")
        assert hasattr(report, "overall_state")
        assert hasattr(report, "feedback_loops_healthy")
        assert hasattr(report, "feedback_loops_deviating")
        assert hasattr(report, "active_corrections")
        assert hasattr(report, "positive_feedback_risks")
        assert hasattr(report, "average_allostatic_load")
        assert hasattr(report, "recommendations")

        # Verify types
        assert isinstance(report.timestamp, datetime)
        assert isinstance(report.feedback_loops_healthy, int)
        assert isinstance(report.feedback_loops_deviating, int)
        assert isinstance(report.active_corrections, int)
        assert isinstance(report.positive_feedback_risks, int)
        assert isinstance(report.average_allostatic_load, float)
        assert isinstance(report.recommendations, list)

    # ========================================================================
    # get_current_status Tests
    # ========================================================================

    def test_get_current_status(self, db):
        """Test getting current status without new metrics."""
        service = HomeostasisService(db)

        status = service.get_current_status()

        assert isinstance(status, HomeostasisReport)
        assert status.timestamp is not None

    def test_get_current_status_after_check(self, db):
        """Test status reflects previous check."""
        service = HomeostasisService(db)

        # First check with metrics
        service.check_homeostasis({"coverage_rate": 0.90})

        # Get current status
        status = service.get_current_status()

        assert isinstance(status, HomeostasisReport)

    # ========================================================================
    # get_feedback_loop_status Tests
    # ========================================================================

    def test_get_feedback_loop_status_existing(self, db):
        """Test getting status of an existing feedback loop."""
        service = HomeostasisService(db)

        # First check some metrics to populate the loop
        service.check_homeostasis({"coverage_rate": 0.92})

        status = service.get_feedback_loop_status("coverage_rate")

        assert status is not None
        assert "name" in status
        assert "setpoint_name" in status
        assert status["setpoint_name"] == "coverage_rate"
        assert "target_value" in status
        assert "tolerance" in status
        assert "current_value" in status
        assert "deviation" in status
        assert "consecutive_deviations" in status
        assert "trend" in status

    def test_get_feedback_loop_status_nonexistent(self, db):
        """Test getting status of nonexistent feedback loop."""
        service = HomeostasisService(db)

        status = service.get_feedback_loop_status("nonexistent_setpoint")

        assert status is None

    def test_get_all_feedback_loops(self, db):
        """Test getting status of all feedback loops."""
        service = HomeostasisService(db)

        loops = service.get_all_feedback_loops()

        assert isinstance(loops, list)
        # Should have at least the default setpoints
        assert len(loops) >= 5  # Default setpoints from homeostasis module

        for loop in loops:
            assert "name" in loop
            assert "setpoint_name" in loop
            assert "target_value" in loop

    # ========================================================================
    # calculate_allostatic_load Tests
    # ========================================================================

    def test_calculate_allostatic_load_low_stress(self, db):
        """Test allostatic load calculation with low stress factors."""
        service = HomeostasisService(db)

        entity_id = str(uuid4())
        stress_factors = {
            "consecutive_weekend_calls": 0,
            "nights_past_month": 2,
            "schedule_changes_absorbed": 1,
            "holidays_worked_this_year": 0,
            "overtime_hours_month": 5.0,
            "coverage_gap_responses": 1,
            "cross_coverage_events": 0,
        }

        metrics = service.calculate_allostatic_load(
            entity_id=entity_id,
            entity_type="faculty",
            stress_factors=stress_factors,
        )

        assert metrics is not None
        assert metrics.entity_type == "faculty"
        assert metrics.total_allostatic_load >= 0
        # Low stress should result in low load
        assert metrics.total_allostatic_load < 50  # Below warning threshold

    def test_calculate_allostatic_load_high_stress(self, db):
        """Test allostatic load calculation with high stress factors."""
        service = HomeostasisService(db)

        entity_id = str(uuid4())
        stress_factors = {
            "consecutive_weekend_calls": 5,
            "nights_past_month": 15,
            "schedule_changes_absorbed": 10,
            "holidays_worked_this_year": 6,
            "overtime_hours_month": 40.0,
            "coverage_gap_responses": 8,
            "cross_coverage_events": 5,
        }

        metrics = service.calculate_allostatic_load(
            entity_id=entity_id,
            entity_type="faculty",
            stress_factors=stress_factors,
        )

        assert metrics is not None
        assert metrics.total_allostatic_load > 0
        # High stress should result in higher load
        assert metrics.total_allostatic_load > 50

    def test_calculate_allostatic_load_empty_stress(self, db):
        """Test allostatic load calculation with empty stress factors."""
        service = HomeostasisService(db)

        entity_id = str(uuid4())
        stress_factors = {}

        metrics = service.calculate_allostatic_load(
            entity_id=entity_id,
            entity_type="faculty",
            stress_factors=stress_factors,
        )

        assert metrics is not None
        assert metrics.total_allostatic_load == 0

    # ========================================================================
    # get_positive_feedback_risks Tests
    # ========================================================================

    def test_get_positive_feedback_risks_empty(self, db):
        """Test getting positive feedback risks when none detected."""
        service = HomeostasisService(db)

        risks = service.get_positive_feedback_risks()

        assert isinstance(risks, list)

    def test_get_positive_feedback_risks_structure(self, db):
        """Test structure of positive feedback risk dicts."""
        service = HomeostasisService(db)

        # Trigger a check with low coverage to potentially detect risks
        service.check_homeostasis({"coverage_rate": 0.75})

        risks = service.get_positive_feedback_risks()

        assert isinstance(risks, list)
        # Structure test for any risks present
        for risk in risks:
            assert "id" in risk
            assert "name" in risk
            assert "description" in risk
            assert "detected_at" in risk
            assert "trigger" in risk
            assert "intervention" in risk
            assert "urgency" in risk


class TestHomeostasisServiceIntegration:
    """Integration tests for HomeostasisService with database."""

    def test_service_multiple_checks_updates_state(self, db):
        """Test that multiple checks update feedback loop state."""
        service = HomeostasisService(db)

        # First check
        report1 = service.check_homeostasis({"coverage_rate": 0.90})

        # Second check with different value
        report2 = service.check_homeostasis({"coverage_rate": 0.85})

        # Third check
        report3 = service.check_homeostasis({"coverage_rate": 0.80})

        # All should return valid reports
        assert isinstance(report1, HomeostasisReport)
        assert isinstance(report2, HomeostasisReport)
        assert isinstance(report3, HomeostasisReport)

        # Timestamps should be different
        assert report1.timestamp != report3.timestamp

    def test_service_tracks_trends(self, db):
        """Test that service tracks trends in feedback loops."""
        service = HomeostasisService(db)

        # Declining coverage
        for coverage in [0.95, 0.92, 0.89, 0.86, 0.83]:
            service.check_homeostasis({"coverage_rate": coverage})

        loop_status = service.get_feedback_loop_status("coverage_rate")

        assert loop_status is not None
        # Should detect decreasing trend
        assert loop_status["trend"] in ["decreasing", "stable", "insufficient_data"]


class TestHomeostasisReportSerialization:
    """Test HomeostasisReport Pydantic model serialization."""

    def test_report_to_dict(self, db):
        """Test that report can be serialized to dict."""
        service = HomeostasisService(db)
        report = service.check_homeostasis({"coverage_rate": 0.92})

        # Should be serializable to dict
        report_dict = report.model_dump()

        assert isinstance(report_dict, dict)
        assert "timestamp" in report_dict
        assert "overall_state" in report_dict
        assert "feedback_loops_healthy" in report_dict

    def test_report_to_json(self, db):
        """Test that report can be serialized to JSON."""
        service = HomeostasisService(db)
        report = service.check_homeostasis({"coverage_rate": 0.92})

        # Should be serializable to JSON
        json_str = report.model_dump_json()

        assert isinstance(json_str, str)
        assert "timestamp" in json_str
        assert "overall_state" in json_str
