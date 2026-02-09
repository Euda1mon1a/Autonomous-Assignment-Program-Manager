"""Tests for Homeostasis and Feedback Loops (Biology/Physiology Pattern)."""

from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.resilience.homeostasis import (
    AllostasisMetrics,
    AllostasisState,
    CorrectiveAction,
    CorrectiveActionType,
    DeviationSeverity,
    FeedbackLoop,
    FeedbackType,
    HomeostasisMonitor,
    HomeostasisStatus,
    PositiveFeedbackRisk,
    Setpoint,
    VolatilityAlert,
    VolatilityLevel,
    VolatilityMetrics,
)


# ==================== Enums ====================


class TestFeedbackType:
    def test_values(self):
        assert FeedbackType.NEGATIVE == "negative"
        assert FeedbackType.POSITIVE == "positive"

    def test_count(self):
        assert len(FeedbackType) == 2


class TestDeviationSeverity:
    def test_values(self):
        assert DeviationSeverity.NONE == "none"
        assert DeviationSeverity.MINOR == "minor"
        assert DeviationSeverity.MODERATE == "moderate"
        assert DeviationSeverity.MAJOR == "major"
        assert DeviationSeverity.CRITICAL == "critical"

    def test_count(self):
        assert len(DeviationSeverity) == 5


class TestVolatilityLevel:
    def test_values(self):
        assert VolatilityLevel.STABLE == "stable"
        assert VolatilityLevel.NORMAL == "normal"
        assert VolatilityLevel.ELEVATED == "elevated"
        assert VolatilityLevel.HIGH == "high"
        assert VolatilityLevel.CRITICAL == "critical"

    def test_count(self):
        assert len(VolatilityLevel) == 5


class TestCorrectiveActionType:
    def test_count(self):
        assert len(CorrectiveActionType) == 6


class TestAllostasisState:
    def test_values(self):
        assert AllostasisState.HOMEOSTASIS == "homeostasis"
        assert AllostasisState.ALLOSTASIS == "allostasis"
        assert AllostasisState.ALLOSTATIC_LOAD == "allostatic_load"
        assert AllostasisState.ALLOSTATIC_OVERLOAD == "allostatic_overload"

    def test_count(self):
        assert len(AllostasisState) == 4


# ==================== Setpoint ====================


class TestSetpoint:
    def _make_setpoint(self, target=0.95, tolerance=0.05):
        return Setpoint(
            id=uuid4(),
            name="test",
            description="Test setpoint",
            target_value=target,
            tolerance=tolerance,
        )

    def test_check_deviation_none(self):
        sp = self._make_setpoint(target=0.95, tolerance=0.05)
        deviation, severity = sp.check_deviation(0.95)
        assert severity == DeviationSeverity.NONE

    def test_check_deviation_within_tolerance(self):
        sp = self._make_setpoint(target=1.0, tolerance=0.05)
        deviation, severity = sp.check_deviation(0.97)
        assert severity == DeviationSeverity.NONE

    def test_check_deviation_minor(self):
        sp = self._make_setpoint(target=1.0, tolerance=0.05)
        # Relative deviation > tolerance (5%) but <= 2*tolerance (10%)
        deviation, severity = sp.check_deviation(0.92)
        assert severity == DeviationSeverity.MINOR

    def test_check_deviation_moderate(self):
        sp = self._make_setpoint(target=1.0, tolerance=0.05)
        # Relative deviation > 2*tolerance (10%) but <= 3*tolerance (15%)
        deviation, severity = sp.check_deviation(0.87)
        assert severity == DeviationSeverity.MODERATE

    def test_check_deviation_major(self):
        sp = self._make_setpoint(target=1.0, tolerance=0.05)
        # Relative deviation > 3*tolerance (15%) but <= 5*tolerance (25%)
        deviation, severity = sp.check_deviation(0.78)
        assert severity == DeviationSeverity.MAJOR

    def test_check_deviation_critical(self):
        sp = self._make_setpoint(target=1.0, tolerance=0.05)
        # Relative deviation > 5*tolerance (25%)
        deviation, severity = sp.check_deviation(0.50)
        assert severity == DeviationSeverity.CRITICAL

    def test_defaults(self):
        sp = self._make_setpoint()
        assert sp.unit == ""
        assert sp.minimum == 0.0
        assert sp.maximum == 1.0
        assert sp.is_critical is False


# ==================== VolatilityMetrics ====================


class TestVolatilityMetrics:
    def test_is_warning_elevated(self):
        vm = VolatilityMetrics(
            volatility=0.2,
            jitter=0.3,
            momentum=0.1,
            distance_to_critical=0.8,
            level=VolatilityLevel.ELEVATED,
        )
        assert vm.is_warning is True
        assert vm.is_critical is False

    def test_is_critical(self):
        vm = VolatilityMetrics(
            volatility=0.5,
            jitter=0.8,
            momentum=-0.5,
            distance_to_critical=0.1,
            level=VolatilityLevel.CRITICAL,
        )
        assert vm.is_warning is True
        assert vm.is_critical is True

    def test_not_warning_stable(self):
        vm = VolatilityMetrics(
            volatility=0.02,
            jitter=0.05,
            momentum=0.0,
            distance_to_critical=0.95,
            level=VolatilityLevel.STABLE,
        )
        assert vm.is_warning is False
        assert vm.is_critical is False


# ==================== FeedbackLoop ====================


class TestFeedbackLoop:
    def _make_loop(self, target=0.95, tolerance=0.05):
        sp = Setpoint(
            id=uuid4(),
            name="coverage",
            description="Coverage rate",
            target_value=target,
            tolerance=tolerance,
        )
        return FeedbackLoop(
            id=uuid4(),
            name="coverage_feedback",
            description="Coverage feedback loop",
            setpoint=sp,
            feedback_type=FeedbackType.NEGATIVE,
        )

    def test_defaults(self):
        loop = self._make_loop()
        assert loop.is_active is True
        assert loop.last_checked is None
        assert loop.consecutive_deviations == 0
        assert loop.total_corrections == 0
        assert loop.value_history == []

    def test_record_value(self):
        loop = self._make_loop()
        loop.record_value(0.95)
        assert len(loop.value_history) == 1
        assert loop.last_checked is not None

    def test_record_value_trims_history(self):
        loop = self._make_loop()
        loop.max_history_size = 5
        for i in range(10):
            loop.record_value(0.9 + i * 0.01)
        assert len(loop.value_history) == 5

    def test_get_trend_insufficient_data(self):
        loop = self._make_loop()
        assert loop.get_trend() == "insufficient_data"

    def test_get_trend_stable(self):
        loop = self._make_loop()
        for _ in range(10):
            loop.record_value(0.95)
        assert loop.get_trend() == "stable"

    def test_get_trend_increasing(self):
        loop = self._make_loop()
        for i in range(10):
            loop.record_value(0.80 + i * 0.02)
        assert loop.get_trend() == "increasing"

    def test_get_trend_decreasing(self):
        loop = self._make_loop()
        for i in range(10):
            loop.record_value(1.0 - i * 0.02)
        assert loop.get_trend() == "decreasing"

    def test_is_improving_toward_target(self):
        loop = self._make_loop(target=1.0)
        loop.record_value(0.80)
        loop.record_value(0.85)
        loop.record_value(0.90)
        assert loop.is_improving() is True

    def test_is_improving_away_from_target(self):
        loop = self._make_loop(target=1.0)
        loop.record_value(0.90)
        loop.record_value(0.85)
        loop.record_value(0.80)
        assert loop.is_improving() is False

    def test_get_volatility_insufficient_data(self):
        loop = self._make_loop()
        assert loop.get_volatility() == 0.0

    def test_get_volatility_stable(self):
        loop = self._make_loop()
        for _ in range(10):
            loop.record_value(0.95)
        assert loop.get_volatility() == 0.0  # No variance

    def test_get_volatility_variable(self):
        loop = self._make_loop()
        for i in range(20):
            loop.record_value(0.90 if i % 2 == 0 else 1.0)
        vol = loop.get_volatility()
        assert vol > 0

    def test_get_jitter_insufficient_data(self):
        loop = self._make_loop()
        assert loop.get_jitter() == 0.0

    def test_get_jitter_oscillating(self):
        loop = self._make_loop()
        for i in range(10):
            loop.record_value(0.90 if i % 2 == 0 else 1.0)
        jitter = loop.get_jitter()
        assert jitter > 0.5  # High oscillation

    def test_get_jitter_monotonic(self):
        loop = self._make_loop()
        for i in range(10):
            loop.record_value(0.80 + i * 0.02)
        jitter = loop.get_jitter()
        assert jitter == 0.0  # No direction changes

    def test_get_momentum_increasing(self):
        loop = self._make_loop()
        for i in range(10):
            loop.record_value(0.80 + i * 0.02)
        momentum = loop.get_momentum()
        assert momentum > 0

    def test_get_momentum_decreasing(self):
        loop = self._make_loop()
        for i in range(10):
            loop.record_value(1.0 - i * 0.02)
        momentum = loop.get_momentum()
        assert momentum < 0

    def test_get_distance_to_criticality_at_target(self):
        loop = self._make_loop(target=0.95, tolerance=0.05)
        loop.record_value(0.95)
        dist = loop.get_distance_to_criticality()
        assert abs(dist - 1.0) < 0.01

    def test_get_distance_to_criticality_no_history(self):
        loop = self._make_loop()
        assert loop.get_distance_to_criticality() == 1.0

    def test_get_volatility_metrics(self):
        loop = self._make_loop()
        for i in range(20):
            loop.record_value(0.90 if i % 2 == 0 else 1.0)
        metrics = loop.get_volatility_metrics()
        assert isinstance(metrics, VolatilityMetrics)
        assert metrics.volatility > 0


# ==================== AllostasisMetrics ====================


class TestAllostasisMetrics:
    def _make_metrics(self, **kwargs):
        defaults = {
            "id": uuid4(),
            "entity_id": uuid4(),
            "entity_type": "faculty",
            "calculated_at": datetime.now(),
        }
        defaults.update(kwargs)
        return AllostasisMetrics(**defaults)

    def test_calculate(self):
        m = self._make_metrics(
            consecutive_weekend_calls=2,
            nights_past_month=5,
            schedule_changes_absorbed=3,
            coverage_gap_responses=1,
            holidays_worked_this_year=2,
            overtime_hours_month=10.0,
            cross_coverage_events=3,
        )
        m.calculate()
        assert m.acute_stress_score > 0
        assert m.chronic_stress_score > 0
        assert m.total_allostatic_load > 0

    def test_state_homeostasis(self):
        m = self._make_metrics()
        m.total_allostatic_load = 10.0  # < 25 (50% of 50)
        assert m.state == AllostasisState.HOMEOSTASIS

    def test_state_allostasis(self):
        m = self._make_metrics()
        m.total_allostatic_load = 35.0  # >= 25, < 50
        assert m.state == AllostasisState.ALLOSTASIS

    def test_state_allostatic_load(self):
        m = self._make_metrics()
        m.total_allostatic_load = 65.0  # >= 50, < 80
        assert m.state == AllostasisState.ALLOSTATIC_LOAD

    def test_state_allostatic_overload(self):
        m = self._make_metrics()
        m.total_allostatic_load = 90.0  # >= 80
        assert m.state == AllostasisState.ALLOSTATIC_OVERLOAD

    def test_risk_levels(self):
        m = self._make_metrics()
        m.total_allostatic_load = 10.0
        assert m.risk_level == "low"
        m.total_allostatic_load = 35.0
        assert m.risk_level == "moderate"
        m.total_allostatic_load = 65.0
        assert m.risk_level == "high"
        m.total_allostatic_load = 90.0
        assert m.risk_level == "critical"


# ==================== HomeostasisMonitor ====================


class TestHomeostasisMonitorInit:
    def test_defaults(self):
        monitor = HomeostasisMonitor()
        assert len(monitor.setpoints) == 5
        assert len(monitor.feedback_loops) == 5
        assert monitor.corrective_actions == []
        assert monitor.positive_feedback_risks == []

    def test_default_setpoints(self):
        monitor = HomeostasisMonitor()
        names = {sp.name for sp in monitor.setpoints.values()}
        assert "coverage_rate" in names
        assert "faculty_utilization" in names
        assert "workload_balance" in names
        assert "schedule_stability" in names
        assert "acgme_compliance" in names


class TestRegisterFeedbackLoop:
    def test_registers(self):
        monitor = HomeostasisMonitor()
        sp = Setpoint(
            id=uuid4(),
            name="custom_metric",
            description="Custom",
            target_value=0.8,
            tolerance=0.1,
        )
        initial_count = len(monitor.feedback_loops)
        loop_id = monitor.register_feedback_loop(
            "custom_feedback", "Custom loop", sp, FeedbackType.NEGATIVE
        )
        assert len(monitor.feedback_loops) == initial_count + 1
        assert loop_id in monitor.feedback_loops


class TestCheckFeedbackLoop:
    def test_no_deviation(self):
        monitor = HomeostasisMonitor()
        loop = monitor.get_feedback_loop("coverage_rate")
        action = monitor.check_feedback_loop(loop.id, 0.95)
        assert action is None

    def test_major_deviation_triggers_correction(self):
        monitor = HomeostasisMonitor()
        loop = monitor.get_feedback_loop("coverage_rate")
        # Major deviation: way below target
        action = monitor.check_feedback_loop(loop.id, 0.50)
        assert action is not None
        assert action.deviation_severity in (
            DeviationSeverity.MAJOR,
            DeviationSeverity.CRITICAL,
        )

    def test_persistent_minor_deviation(self):
        monitor = HomeostasisMonitor()
        loop = monitor.get_feedback_loop("coverage_rate")
        # Minor deviation repeated 3+ times
        for _ in range(3):
            action = monitor.check_feedback_loop(loop.id, 0.88)
        # After 3 consecutive deviations, should trigger
        assert action is not None

    def test_inactive_loop_no_action(self):
        monitor = HomeostasisMonitor()
        loop = monitor.get_feedback_loop("coverage_rate")
        loop.is_active = False
        action = monitor.check_feedback_loop(loop.id, 0.50)
        assert action is None

    def test_invalid_loop_id(self):
        monitor = HomeostasisMonitor()
        action = monitor.check_feedback_loop(uuid4(), 0.50)
        assert action is None


class TestRegisterCorrectionHandler:
    def test_handler_called(self):
        monitor = HomeostasisMonitor()
        handler = MagicMock(return_value=True)
        monitor.register_correction_handler(
            CorrectiveActionType.RECRUIT_BACKUP, handler
        )
        loop = monitor.get_feedback_loop("coverage_rate")
        action = monitor.check_feedback_loop(loop.id, 0.20)
        assert action is not None
        assert action.executed is True
        handler.assert_called_once()

    def test_handler_exception(self):
        monitor = HomeostasisMonitor()
        handler = MagicMock(side_effect=RuntimeError("handler failed"))
        monitor.register_correction_handler(
            CorrectiveActionType.RECRUIT_BACKUP, handler
        )
        loop = monitor.get_feedback_loop("coverage_rate")
        action = monitor.check_feedback_loop(loop.id, 0.20)
        assert action is not None
        assert "error" in action.execution_result


class TestCalculateAllostatic:
    def test_calculates(self):
        monitor = HomeostasisMonitor()
        fac_id = uuid4()
        metrics = monitor.calculate_allostatic_load(
            fac_id,
            "faculty",
            {
                "consecutive_weekend_calls": 3,
                "nights_past_month": 8,
                "holidays_worked_this_year": 4,
            },
        )
        assert isinstance(metrics, AllostasisMetrics)
        assert metrics.total_allostatic_load > 0
        assert fac_id in monitor.allostasis_metrics


class TestDetectPositiveFeedbackRisks:
    def _make_metrics(self, load):
        m = AllostasisMetrics(
            id=uuid4(),
            entity_id=uuid4(),
            entity_type="faculty",
            calculated_at=datetime.now(),
        )
        m.total_allostatic_load = load
        return m

    def test_no_risks(self):
        monitor = HomeostasisMonitor()
        metrics = [self._make_metrics(10.0) for _ in range(5)]
        risks = monitor.detect_positive_feedback_risks(metrics, {"coverage_rate": 0.95})
        assert len(risks) == 0

    def test_burnout_cascade(self):
        monitor = HomeostasisMonitor()
        # >30% with high load
        metrics = [self._make_metrics(90.0) for _ in range(4)] + [
            self._make_metrics(10.0)
        ]
        risks = monitor.detect_positive_feedback_risks(metrics, {"coverage_rate": 0.95})
        burnout = [r for r in risks if r.name == "burnout_cascade"]
        assert len(burnout) == 1

    def test_coverage_spiral(self):
        monitor = HomeostasisMonitor()
        metrics = [self._make_metrics(10.0)]
        risks = monitor.detect_positive_feedback_risks(metrics, {"coverage_rate": 0.80})
        coverage = [r for r in risks if r.name == "coverage_spiral"]
        assert len(coverage) == 1

    def test_attrition_cascade(self):
        monitor = HomeostasisMonitor()
        metrics = [self._make_metrics(70.0) for _ in range(5)]
        risks = monitor.detect_positive_feedback_risks(metrics, {"coverage_rate": 0.95})
        attrition = [r for r in risks if r.name == "attrition_cascade"]
        assert len(attrition) == 1


class TestCheckAllLoops:
    def test_checks_matching_loops(self):
        monitor = HomeostasisMonitor()
        actions = monitor.check_all_loops({"coverage_rate": 0.20})
        # Should trigger correction for coverage_rate
        assert len(actions) >= 1

    def test_no_actions_within_tolerance(self):
        monitor = HomeostasisMonitor()
        actions = monitor.check_all_loops({"coverage_rate": 0.95})
        assert len(actions) == 0


class TestGetStatus:
    def test_healthy_status(self):
        monitor = HomeostasisMonitor()
        status = monitor.get_status()
        assert isinstance(status, HomeostasisStatus)
        assert status.overall_state == AllostasisState.HOMEOSTASIS
        assert status.feedback_loops_healthy == 5

    def test_overload_status(self):
        monitor = HomeostasisMonitor()
        m = AllostasisMetrics(
            id=uuid4(),
            entity_id=uuid4(),
            entity_type="faculty",
            calculated_at=datetime.now(),
        )
        m.total_allostatic_load = 90.0
        status = monitor.get_status(faculty_metrics=[m])
        assert status.overall_state == AllostasisState.ALLOSTATIC_OVERLOAD
        assert any("CRITICAL" in r for r in status.recommendations)


class TestGetSetpoint:
    def test_finds_by_name(self):
        monitor = HomeostasisMonitor()
        sp = monitor.get_setpoint("coverage_rate")
        assert sp is not None
        assert sp.name == "coverage_rate"

    def test_not_found(self):
        monitor = HomeostasisMonitor()
        assert monitor.get_setpoint("nonexistent") is None


class TestGetFeedbackLoop:
    def test_finds_by_setpoint_name(self):
        monitor = HomeostasisMonitor()
        loop = monitor.get_feedback_loop("coverage_rate")
        assert loop is not None
        assert loop.setpoint.name == "coverage_rate"

    def test_not_found(self):
        monitor = HomeostasisMonitor()
        assert monitor.get_feedback_loop("nonexistent") is None


class TestDetectVolatilityRisks:
    def test_no_alerts_insufficient_data(self):
        monitor = HomeostasisMonitor()
        alerts = monitor.detect_volatility_risks()
        assert len(alerts) == 0

    def test_detects_high_volatility(self):
        monitor = HomeostasisMonitor()
        loop = monitor.get_feedback_loop("coverage_rate")
        # Feed highly oscillating values
        for i in range(20):
            loop.record_value(0.70 if i % 2 == 0 else 1.0)
        alerts = monitor.detect_volatility_risks()
        # Should detect volatility in the coverage loop
        assert len(alerts) >= 1
        assert isinstance(alerts[0], VolatilityAlert)
