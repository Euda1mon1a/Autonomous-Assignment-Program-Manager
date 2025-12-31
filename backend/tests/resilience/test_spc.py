"""
Tests for Statistical Process Control (SPC) charts.

Tests Shewhart charts, CUSUM, EWMA, and Western Electric rules.
"""

import pytest
from datetime import datetime

from app.resilience.spc.control_chart import ControlChart, ControlChartType, CUSUMChart, EWMAChart
from app.resilience.spc.western_electric import WesternElectricRules


class TestControlChart:
    """Test suite for SPC control charts."""

    def test_calculate_limits_from_baseline(self):
        """Test calculating control limits from baseline data."""
        chart = ControlChart()

        baseline = [10.0, 12.0, 11.0, 13.0, 10.5, 11.5, 12.5, 11.0, 12.0, 11.5]
        limits = chart.calculate_limits(baseline)

        # Mean should be around 11.5
        assert limits.center_line == pytest.approx(11.5, abs=0.5)
        assert limits.ucl > limits.center_line
        assert limits.lcl < limits.center_line
        assert limits.uwl < limits.ucl
        assert limits.lwl > limits.lcl

    def test_in_control_point(self):
        """Test point within control limits."""
        chart = ControlChart()

        baseline = [10.0] * 10
        chart.calculate_limits(baseline)

        point = chart.add_point(10.5)

        assert point.is_in_control
        assert point.violated_rule is None

    def test_out_of_control_point(self):
        """Test point beyond control limits."""
        chart = ControlChart()

        baseline = [10.0] * 10
        limits = chart.calculate_limits(baseline)

        # Add point far beyond UCL
        point = chart.add_point(limits.ucl + 10)

        assert not point.is_in_control
        assert point.violated_rule == "out_of_control"

    def test_zone_classification(self):
        """Test zone classification (A, B, C, Out)."""
        chart = ControlChart()

        baseline = [100.0] * 10
        limits = chart.calculate_limits(baseline)

        # Zone A (within 1σ)
        point_a = chart.add_point(100.0 + 0.5 * limits.sigma)
        assert point_a.zone == "A"

        # Zone B (1-2σ)
        point_b = chart.add_point(100.0 + 1.5 * limits.sigma)
        assert point_b.zone == "B"

        # Zone C (2-3σ)
        point_c = chart.add_point(100.0 + 2.5 * limits.sigma)
        assert point_c.zone == "C"

        # Out (>3σ)
        point_out = chart.add_point(100.0 + 4.0 * limits.sigma)
        assert point_out.zone == "Out"

    def test_capability_indices(self):
        """Test Cp and Cpk calculation."""
        chart = ControlChart()

        baseline = [10.0] * 20
        chart.calculate_limits(baseline)

        # Add stable process data
        for _ in range(10):
            chart.add_point(10.0)

        capability = chart.get_capability_indices()

        assert "cp" in capability
        assert "cpk" in capability
        assert capability["cp"] > 0

    def test_detect_trends(self):
        """Test trend detection."""
        chart = ControlChart()

        baseline = [10.0] * 10
        chart.calculate_limits(baseline)

        # Add increasing trend
        for i in range(10):
            chart.add_point(10.0 + i * 0.1)

        trends = chart.detect_trends(window_size=7)

        assert trends["trend"] == "increasing"
        assert trends["slope"] > 0


class TestCUSUMChart:
    """Test suite for CUSUM charts."""

    def test_cusum_detects_shift(self):
        """Test CUSUM detects small persistent shift."""
        cusum = CUSUMChart(target=10.0, sigma=1.0)

        # Process shifts from 10 to 10.5
        for i in range(20):
            value = 10.5
            point = cusum.add_point(value)

            # Should eventually go out of control
            if i > 10:
                assert not point.is_in_control

    def test_cusum_stays_in_control_no_shift(self):
        """Test CUSUM stays in control with no shift."""
        cusum = CUSUMChart(target=10.0, sigma=1.0)

        # No shift
        for _ in range(20):
            point = cusum.add_point(10.0)

        # Should stay in control
        assert point.is_in_control
        assert point.cusum_high < cusum.h
        assert point.cusum_low < cusum.h

    def test_cusum_reset(self):
        """Test CUSUM reset."""
        cusum = CUSUMChart(target=10.0, sigma=1.0)

        cusum.add_point(15.0)  # Cause accumulation
        cusum.reset()

        assert cusum.cusum_high == 0.0
        assert cusum.cusum_low == 0.0


class TestEWMAChart:
    """Test suite for EWMA charts."""

    def test_ewma_smooths_data(self):
        """Test EWMA provides smoothing."""
        ewma = EWMAChart(target=10.0, sigma=1.0, lambda_=0.2)

        # Add noisy data
        values = [10.5, 9.5, 10.2, 9.8, 10.1]

        for value in values:
            point = ewma.add_point(value)

        # EWMA should be smoother than raw data
        # and converge toward mean
        assert abs(point.ewma - 10.0) < 1.0

    def test_ewma_detects_shift(self):
        """Test EWMA detects gradual shift."""
        ewma = EWMAChart(target=10.0, sigma=0.5, lambda_=0.3)

        # Gradual shift upward
        for i in range(50):
            value = 10.0 + i * 0.05  # Slow drift
            point = ewma.add_point(value)

        # Should eventually go out of control
        assert not point.is_in_control


class TestWesternElectricRules:
    """Test suite for Western Electric rules."""

    def test_rule_1_beyond_3sigma(self):
        """Test Rule 1: One point beyond 3σ."""
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)

        data = [10.0] * 10 + [14.0]  # Last point beyond 3σ

        violations = rules.check_all_rules(data)

        rule_1_violations = [v for v in violations if v.rule_number == 1]
        assert len(rule_1_violations) > 0
        assert rule_1_violations[0].severity == "critical"

    def test_rule_4_eight_same_side(self):
        """Test Rule 4: Eight consecutive points same side."""
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)

        data = [10.5] * 8  # All above center line

        violations = rules.check_all_rules(data)

        rule_4_violations = [v for v in violations if v.rule_number == 4]
        assert len(rule_4_violations) > 0

    def test_rule_5_six_trending(self):
        """Test Rule 5: Six consecutive points trending."""
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)

        data = [10.0, 10.1, 10.2, 10.3, 10.4, 10.5]  # Increasing trend

        violations = rules.check_all_rules(data)

        rule_5_violations = [v for v in violations if v.rule_number == 5]
        assert len(rule_5_violations) > 0

    def test_no_violations_in_control(self):
        """Test no violations for in-control process."""
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)

        # Random but in-control data
        data = [10.0, 10.2, 9.8, 10.1, 9.9, 10.0, 10.1, 9.9]

        violations = rules.check_all_rules(data)

        # Should have minimal violations
        critical = [v for v in violations if v.severity == "critical"]
        assert len(critical) == 0

    def test_get_rule_summary(self):
        """Test rule violation summary."""
        rules = WesternElectricRules(center_line=10.0, sigma=1.0)

        data = [10.0] * 5 + [14.0] + [10.0] * 5  # One outlier

        violations = rules.check_all_rules(data)
        summary = rules.get_rule_summary(violations)

        assert summary["total_violations"] >= 0
        assert "status" in summary
        assert summary["status"] in ["in_control", "warning", "out_of_control", "stable"]
