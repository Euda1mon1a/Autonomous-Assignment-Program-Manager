"""Tests for Utilization Threshold Management (queuing theory scheduling optimization)."""

import math
from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.resilience.utilization import (
    UtilizationForecast,
    UtilizationLevel,
    UtilizationMetrics,
    UtilizationMonitor,
    UtilizationThreshold,
)


# ==================== UtilizationLevel ====================


class TestUtilizationLevel:
    def test_values(self):
        assert UtilizationLevel.GREEN.value == "green"
        assert UtilizationLevel.YELLOW.value == "yellow"
        assert UtilizationLevel.ORANGE.value == "orange"
        assert UtilizationLevel.RED.value == "red"
        assert UtilizationLevel.BLACK.value == "black"

    def test_count(self):
        assert len(UtilizationLevel) == 5


# ==================== UtilizationThreshold ====================


class TestUtilizationThreshold:
    def test_defaults(self):
        t = UtilizationThreshold()
        assert t.max_utilization == 0.80
        assert t.warning_threshold == 0.70
        assert t.critical_threshold == 0.90
        assert t.emergency_threshold == 0.95

    def test_get_level_green(self):
        t = UtilizationThreshold()
        assert t.get_level(0.0) == UtilizationLevel.GREEN
        assert t.get_level(0.5) == UtilizationLevel.GREEN
        assert t.get_level(0.69) == UtilizationLevel.GREEN

    def test_get_level_yellow(self):
        t = UtilizationThreshold()
        assert t.get_level(0.70) == UtilizationLevel.YELLOW
        assert t.get_level(0.75) == UtilizationLevel.YELLOW
        assert t.get_level(0.79) == UtilizationLevel.YELLOW

    def test_get_level_orange(self):
        t = UtilizationThreshold()
        assert t.get_level(0.80) == UtilizationLevel.ORANGE
        assert t.get_level(0.85) == UtilizationLevel.ORANGE
        assert t.get_level(0.89) == UtilizationLevel.ORANGE

    def test_get_level_red(self):
        t = UtilizationThreshold()
        assert t.get_level(0.90) == UtilizationLevel.RED
        assert t.get_level(0.94) == UtilizationLevel.RED

    def test_get_level_black(self):
        t = UtilizationThreshold()
        assert t.get_level(0.95) == UtilizationLevel.BLACK
        assert t.get_level(1.0) == UtilizationLevel.BLACK

    def test_custom_thresholds(self):
        t = UtilizationThreshold(
            max_utilization=0.60,
            warning_threshold=0.50,
            critical_threshold=0.70,
            emergency_threshold=0.80,
        )
        assert t.get_level(0.55) == UtilizationLevel.YELLOW
        assert t.get_level(0.65) == UtilizationLevel.ORANGE
        assert t.get_level(0.75) == UtilizationLevel.RED
        assert t.get_level(0.85) == UtilizationLevel.BLACK


# ==================== UtilizationMetrics ====================


class TestUtilizationMetrics:
    def test_construction(self):
        m = UtilizationMetrics(
            total_capacity=100,
            required_coverage=80,
            current_assignments=75,
            utilization_rate=0.75,
            effective_utilization=0.80,
            level=UtilizationLevel.YELLOW,
            buffer_remaining=0.05,
        )
        assert m.total_capacity == 100
        assert m.level == UtilizationLevel.YELLOW
        assert m.by_service == {}
        assert m.by_faculty == {}


# ==================== UtilizationForecast ====================


class TestUtilizationForecast:
    def test_construction(self):
        f = UtilizationForecast(
            date=date(2026, 1, 15),
            predicted_utilization=0.85,
            predicted_level=UtilizationLevel.ORANGE,
        )
        assert f.predicted_utilization == 0.85
        assert f.contributing_factors == []
        assert f.recommendations == []


# ==================== UtilizationMonitor ====================


class TestUtilizationMonitorInit:
    def test_default_threshold(self):
        m = UtilizationMonitor()
        assert m.threshold.max_utilization == 0.80

    def test_custom_threshold(self):
        t = UtilizationThreshold(max_utilization=0.60)
        m = UtilizationMonitor(threshold=t)
        assert m.threshold.max_utilization == 0.60


class TestCalculateUtilization:
    def test_basic(self):
        m = UtilizationMonitor()
        faculty = [f"fac_{i}" for i in range(10)]
        metrics = m.calculate_utilization(
            faculty, 15, blocks_per_faculty_per_day=2.0, days_in_period=1
        )
        # capacity = 10 * 2.0 * 1 = 20
        assert metrics.total_capacity == 20
        assert metrics.utilization_rate == 0.75  # 15/20
        assert metrics.level == UtilizationLevel.YELLOW

    def test_zero_faculty(self):
        m = UtilizationMonitor()
        metrics = m.calculate_utilization([], 10)
        assert metrics.total_capacity == 0
        assert metrics.utilization_rate == 1.0
        assert metrics.level == UtilizationLevel.BLACK

    def test_zero_faculty_zero_required(self):
        m = UtilizationMonitor()
        metrics = m.calculate_utilization([], 0)
        assert metrics.utilization_rate == 0.0
        assert metrics.level == UtilizationLevel.GREEN

    def test_green_utilization(self):
        m = UtilizationMonitor()
        faculty = [f"fac_{i}" for i in range(10)]
        # 10 * 2 * 1 = 20 capacity; 10/20 = 50%
        metrics = m.calculate_utilization(faculty, 10)
        assert metrics.level == UtilizationLevel.GREEN

    def test_red_utilization(self):
        m = UtilizationMonitor()
        faculty = [f"fac_{i}" for i in range(10)]
        # 10 * 2 * 1 = 20; 18/20 = 90%
        metrics = m.calculate_utilization(faculty, 18)
        assert metrics.level == UtilizationLevel.RED

    def test_buffer_remaining(self):
        m = UtilizationMonitor()
        faculty = [f"fac_{i}" for i in range(10)]
        # capacity = 20; safe max = 16 (80%); required = 10
        metrics = m.calculate_utilization(faculty, 10)
        # buffer = (16 - 10) / 20 = 0.30
        assert abs(metrics.buffer_remaining - 0.30) < 0.01

    def test_multi_day_period(self):
        m = UtilizationMonitor()
        faculty = [f"fac_{i}" for i in range(5)]
        # capacity = 5 * 2 * 5 = 50
        metrics = m.calculate_utilization(faculty, 35, days_in_period=5)
        assert metrics.total_capacity == 50
        assert metrics.utilization_rate == 0.70


class TestGetSafeCapacity:
    def test_basic(self):
        m = UtilizationMonitor()
        faculty = [f"fac_{i}" for i in range(10)]
        # theoretical = 10 * 2 * 5 = 100; safe = 80
        safe = m.get_safe_capacity(faculty, days_in_period=5)
        assert safe == 80

    def test_zero_faculty(self):
        m = UtilizationMonitor()
        assert m.get_safe_capacity([]) == 0

    def test_custom_blocks_per_day(self):
        m = UtilizationMonitor()
        faculty = [f"fac_{i}" for i in range(10)]
        # theoretical = 10 * 3 * 1 = 30; safe = 24
        safe = m.get_safe_capacity(faculty, blocks_per_faculty_per_day=3.0)
        assert safe == 24


class TestCheckAssignmentSafe:
    def test_safe(self):
        m = UtilizationMonitor()
        is_safe, msg = m.check_assignment_safe(0.50, 10, 100)
        assert is_safe is True
        assert "Safe" in msg

    def test_warning(self):
        m = UtilizationMonitor()
        is_safe, msg = m.check_assignment_safe(0.70, 5, 100)
        assert is_safe is True
        assert "Warning" in msg

    def test_unsafe(self):
        m = UtilizationMonitor()
        is_safe, msg = m.check_assignment_safe(0.70, 15, 100)
        assert is_safe is False
        assert "80%" in msg

    def test_zero_capacity(self):
        m = UtilizationMonitor()
        is_safe, msg = m.check_assignment_safe(0.0, 1, 0)
        assert is_safe is False
        assert "No capacity" in msg


class TestForecastUtilization:
    def test_basic_forecast(self):
        m = UtilizationMonitor()
        faculty = [f"fac_{i}" for i in range(10)]
        today = date.today()
        coverage = {today: 10, today + timedelta(days=1): 15}
        forecasts = m.forecast_utilization(faculty, {}, coverage, forecast_days=3)
        assert len(forecasts) == 3

    def test_absent_faculty_raises_utilization(self):
        m = UtilizationMonitor()
        faculty = [f"fac_{i}" for i in range(4)]
        today = date.today()
        uid1, uid2, uid3 = uuid4(), uuid4(), uuid4()
        # 3 of 4 absent, 1 available, capacity = 1 * 2 = 2, need 2 -> 100%
        absences = {today: [uid1, uid2, uid3]}
        coverage = {today: 2}
        forecasts = m.forecast_utilization(faculty, absences, coverage, forecast_days=1)
        assert forecasts[0].predicted_level in (
            UtilizationLevel.BLACK,
            UtilizationLevel.RED,
        )

    def test_forecast_recommendations(self):
        m = UtilizationMonitor()
        faculty = [f"fac_{i}" for i in range(2)]
        today = date.today()
        # 2 faculty, capacity = 4, need 4 -> 100% -> BLACK
        coverage = {today: 4}
        forecasts = m.forecast_utilization(faculty, {}, coverage, forecast_days=1)
        assert len(forecasts[0].recommendations) > 0

    def test_no_coverage_required(self):
        m = UtilizationMonitor()
        faculty = [f"fac_{i}" for i in range(5)]
        forecasts = m.forecast_utilization(faculty, {}, {}, forecast_days=5)
        for f in forecasts:
            assert f.predicted_utilization == 0.0
            assert f.predicted_level == UtilizationLevel.GREEN


class TestCalculateWaitTimeMultiplier:
    def test_zero(self):
        assert UtilizationMonitor.calculate_wait_time_multiplier(0.0) == 0.0

    def test_fifty_percent(self):
        result = UtilizationMonitor.calculate_wait_time_multiplier(0.5)
        assert abs(result - 1.0) < 0.01

    def test_eighty_percent(self):
        result = UtilizationMonitor.calculate_wait_time_multiplier(0.8)
        assert abs(result - 4.0) < 0.01

    def test_ninety_percent(self):
        result = UtilizationMonitor.calculate_wait_time_multiplier(0.9)
        assert abs(result - 9.0) < 0.01

    def test_ninety_five_percent(self):
        result = UtilizationMonitor.calculate_wait_time_multiplier(0.95)
        assert abs(result - 19.0) < 0.01

    def test_hundred_percent(self):
        result = UtilizationMonitor.calculate_wait_time_multiplier(1.0)
        assert result == float("inf")

    def test_negative(self):
        assert UtilizationMonitor.calculate_wait_time_multiplier(-0.1) == 0.0


class TestGetStatusReport:
    def test_green_report(self):
        m = UtilizationMonitor()
        metrics = UtilizationMetrics(
            total_capacity=100,
            required_coverage=50,
            current_assignments=50,
            utilization_rate=0.50,
            effective_utilization=0.50,
            level=UtilizationLevel.GREEN,
            buffer_remaining=0.30,
        )
        report = m.get_status_report(metrics)
        assert report["level"] == "green"
        assert "healthy" in report["message"].lower()
        assert len(report["recommendations"]) > 0

    def test_red_report(self):
        m = UtilizationMonitor()
        metrics = UtilizationMetrics(
            total_capacity=100,
            required_coverage=92,
            current_assignments=92,
            utilization_rate=0.92,
            effective_utilization=0.92,
            level=UtilizationLevel.RED,
            buffer_remaining=0.0,
        )
        report = m.get_status_report(metrics)
        assert report["level"] == "red"
        assert (
            "cascade" in report["message"].lower()
            or "critical" in report["message"].lower()
        )

    def test_report_has_capacity_breakdown(self):
        m = UtilizationMonitor()
        metrics = UtilizationMetrics(
            total_capacity=100,
            required_coverage=60,
            current_assignments=60,
            utilization_rate=0.60,
            effective_utilization=0.60,
            level=UtilizationLevel.GREEN,
            buffer_remaining=0.20,
        )
        report = m.get_status_report(metrics)
        assert "capacity" in report
        assert report["capacity"]["total"] == 100
        assert report["capacity"]["safe_maximum"] == 80
        assert report["capacity"]["current_used"] == 60


class TestGetRecommendations:
    def test_green(self):
        m = UtilizationMonitor()
        recs = m._get_recommendations(UtilizationLevel.GREEN)
        assert len(recs) > 0
        assert any("normal" in r.lower() for r in recs)

    def test_black(self):
        m = UtilizationMonitor()
        recs = m._get_recommendations(UtilizationLevel.BLACK)
        assert len(recs) > 0
        assert any("emergency" in r.lower() for r in recs)

    def test_all_levels_have_recommendations(self):
        m = UtilizationMonitor()
        for level in UtilizationLevel:
            recs = m._get_recommendations(level)
            assert len(recs) > 0, f"No recommendations for {level}"
