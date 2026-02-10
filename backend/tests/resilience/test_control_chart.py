"""Tests for SPC control charts (pure logic, no DB)."""

from datetime import datetime

import numpy as np
import pytest

from app.resilience.spc.control_chart import (
    ControlChart,
    ControlChartPoint,
    ControlChartType,
    ControlLimits,
    CUSUMChart,
    CUSUMPoint,
    EWMAChart,
    EWMAPoint,
)


# ── ControlChartType enum ──────────────────────────────────────────────


class TestControlChartType:
    def test_xbar_value(self):
        assert ControlChartType.XBAR.value == "xbar"

    def test_cusum_value(self):
        assert ControlChartType.CUSUM.value == "cusum"

    def test_ewma_value(self):
        assert ControlChartType.EWMA.value == "ewma"

    def test_member_count(self):
        assert len(ControlChartType) == 3


# ── ControlLimits dataclass ────────────────────────────────────────────


class TestControlLimits:
    def test_creation(self):
        cl = ControlLimits(
            center_line=50.0,
            ucl=65.0,
            lcl=35.0,
            uwl=60.0,
            lwl=40.0,
            sigma=5.0,
        )
        assert cl.center_line == 50.0
        assert cl.ucl == 65.0
        assert cl.lcl == 35.0
        assert cl.uwl == 60.0
        assert cl.lwl == 40.0
        assert cl.sigma == 5.0


# ── ControlChartPoint dataclass ────────────────────────────────────────


class TestControlChartPoint:
    def test_default_zone(self):
        pt = ControlChartPoint(
            timestamp=datetime(2026, 1, 1),
            value=50.0,
            is_in_control=True,
        )
        assert pt.zone == "A"
        assert pt.violated_rule is None

    def test_out_of_control(self):
        pt = ControlChartPoint(
            timestamp=datetime(2026, 1, 1),
            value=100.0,
            is_in_control=False,
            violated_rule="out_of_control",
            zone="Out",
        )
        assert pt.is_in_control is False
        assert pt.violated_rule == "out_of_control"


# ── ControlChart init ──────────────────────────────────────────────────


class TestControlChartInit:
    def test_default_params(self):
        chart = ControlChart()
        assert chart.chart_type == ControlChartType.XBAR
        assert chart.sigma_multiplier == 3.0
        assert chart.limits is None
        assert chart.data_points == []

    def test_custom_params(self):
        chart = ControlChart(
            chart_type=ControlChartType.EWMA,
            sigma_multiplier=2.0,
        )
        assert chart.chart_type == ControlChartType.EWMA
        assert chart.sigma_multiplier == 2.0


# ── ControlChart.calculate_limits ──────────────────────────────────────


class TestCalculateLimits:
    def test_basic_limits(self):
        chart = ControlChart()
        baseline = [10.0, 12.0, 11.0, 9.0, 10.0, 11.0, 10.0]
        limits = chart.calculate_limits(baseline)
        assert isinstance(limits, ControlLimits)
        assert limits.ucl > limits.center_line > limits.lcl

    def test_center_line_is_mean(self):
        chart = ControlChart()
        baseline = [10.0, 20.0, 30.0, 40.0, 50.0]
        limits = chart.calculate_limits(baseline)
        assert abs(limits.center_line - 30.0) < 1e-10

    def test_custom_target(self):
        chart = ControlChart()
        baseline = [10.0, 20.0, 30.0, 40.0, 50.0]
        limits = chart.calculate_limits(baseline, target=25.0)
        assert limits.center_line == 25.0

    def test_warning_limits_closer(self):
        """Warning limits (2σ) should be inside control limits (3σ)."""
        chart = ControlChart()
        baseline = [10.0, 12.0, 11.0, 9.0, 10.0, 11.0, 10.0]
        limits = chart.calculate_limits(baseline)
        assert limits.uwl < limits.ucl
        assert limits.lwl > limits.lcl

    def test_sigma_is_sample_std(self):
        """Sigma should use ddof=1 (sample std dev)."""
        chart = ControlChart()
        baseline = [10.0, 20.0, 30.0, 40.0, 50.0]
        limits = chart.calculate_limits(baseline)
        expected_sigma = float(np.std(baseline, ddof=1))
        assert abs(limits.sigma - expected_sigma) < 1e-10

    def test_insufficient_data_raises(self):
        chart = ControlChart()
        with pytest.raises(ValueError, match="at least 5"):
            chart.calculate_limits([1.0, 2.0, 3.0])

    def test_limits_stored_on_chart(self):
        chart = ControlChart()
        baseline = [10.0, 11.0, 12.0, 9.0, 10.0]
        chart.calculate_limits(baseline)
        assert chart.limits is not None

    def test_ucl_lcl_symmetric(self):
        """UCL and LCL should be symmetric around center_line."""
        chart = ControlChart()
        baseline = [10.0, 11.0, 12.0, 9.0, 10.0]
        limits = chart.calculate_limits(baseline)
        ucl_dist = limits.ucl - limits.center_line
        lcl_dist = limits.center_line - limits.lcl
        assert abs(ucl_dist - lcl_dist) < 1e-10

    def test_custom_sigma_multiplier(self):
        chart = ControlChart(sigma_multiplier=2.0)
        baseline = [10.0, 11.0, 12.0, 9.0, 10.0]
        limits = chart.calculate_limits(baseline)
        expected_ucl = limits.center_line + 2.0 * limits.sigma
        assert abs(limits.ucl - expected_ucl) < 1e-10


# ── ControlChart.add_point ─────────────────────────────────────────────


class TestAddPoint:
    def _make_chart(self):
        chart = ControlChart()
        chart.calculate_limits([10.0, 11.0, 12.0, 9.0, 10.0, 11.0])
        return chart

    def test_returns_control_chart_point(self):
        chart = self._make_chart()
        pt = chart.add_point(10.5, timestamp=datetime(2026, 1, 1))
        assert isinstance(pt, ControlChartPoint)

    def test_in_control_point(self):
        chart = self._make_chart()
        pt = chart.add_point(10.5, timestamp=datetime(2026, 1, 1))
        assert pt.is_in_control is True
        assert pt.violated_rule is None

    def test_out_of_control_point(self):
        chart = self._make_chart()
        pt = chart.add_point(1000.0, timestamp=datetime(2026, 1, 1))
        assert pt.is_in_control is False
        assert pt.violated_rule == "out_of_control"

    def test_point_added_to_data(self):
        chart = self._make_chart()
        chart.add_point(10.5)
        assert len(chart.data_points) == 1
        chart.add_point(11.0)
        assert len(chart.data_points) == 2

    def test_no_limits_raises(self):
        chart = ControlChart()
        with pytest.raises(ValueError, match="calculate limits"):
            chart.add_point(10.0)

    def test_zone_assignment(self):
        chart = self._make_chart()
        pt = chart.add_point(chart.limits.center_line, timestamp=datetime(2026, 1, 1))
        assert pt.zone == "A"


# ── ControlChart._determine_zone ───────────────────────────────────────


class TestDetermineZone:
    def test_zone_a_center(self):
        chart = ControlChart()
        chart.calculate_limits([10.0, 11.0, 12.0, 9.0, 10.0, 11.0])
        zone = chart._determine_zone(chart.limits.center_line)
        assert zone == "A"

    def test_zone_b(self):
        chart = ControlChart()
        chart.calculate_limits([10.0, 11.0, 12.0, 9.0, 10.0, 11.0])
        # Just beyond 1σ
        value = chart.limits.center_line + 1.5 * chart.limits.sigma
        zone = chart._determine_zone(value)
        assert zone == "B"

    def test_zone_c(self):
        chart = ControlChart()
        chart.calculate_limits([10.0, 11.0, 12.0, 9.0, 10.0, 11.0])
        value = chart.limits.center_line + 2.5 * chart.limits.sigma
        zone = chart._determine_zone(value)
        assert zone == "C"

    def test_zone_out(self):
        chart = ControlChart()
        chart.calculate_limits([10.0, 11.0, 12.0, 9.0, 10.0, 11.0])
        value = chart.limits.center_line + 3.5 * chart.limits.sigma
        zone = chart._determine_zone(value)
        assert zone == "Out"

    def test_zone_unknown_no_limits(self):
        chart = ControlChart()
        zone = chart._determine_zone(10.0)
        assert zone == "unknown"

    def test_negative_side_zones(self):
        chart = ControlChart()
        chart.calculate_limits([10.0, 11.0, 12.0, 9.0, 10.0, 11.0])
        # Below center by 1.5σ → zone B
        value = chart.limits.center_line - 1.5 * chart.limits.sigma
        assert chart._determine_zone(value) == "B"


# ── ControlChart.get_capability_indices ────────────────────────────────


class TestGetCapabilityIndices:
    def test_no_limits_returns_insufficient(self):
        chart = ControlChart()
        result = chart.get_capability_indices()
        assert result["interpretation"] == "insufficient_data"

    def test_no_data_returns_insufficient(self):
        chart = ControlChart()
        chart.calculate_limits([10.0, 11.0, 12.0, 9.0, 10.0, 11.0])
        result = chart.get_capability_indices()
        assert result["interpretation"] == "insufficient_data"

    def test_centered_process(self):
        chart = ControlChart()
        chart.calculate_limits([10.0, 11.0, 12.0, 9.0, 10.0, 11.0])
        # Add centered points
        for v in [10.0, 10.5, 11.0, 10.5]:
            chart.add_point(v)
        result = chart.get_capability_indices()
        assert "cp" in result
        assert "cpk" in result
        assert "interpretation" in result

    def test_zero_sigma_returns_inf(self):
        chart = ControlChart()
        chart.limits = ControlLimits(
            center_line=10.0, ucl=13.0, lcl=7.0, uwl=12.0, lwl=8.0, sigma=0.0
        )
        chart.data_points = [10.0]
        result = chart.get_capability_indices()
        assert result["cp"] == float("inf")

    def test_interpretation_ranges(self):
        """Check all interpretation labels are valid."""
        valid_labels = {
            "excellent",
            "good",
            "adequate",
            "poor",
            "insufficient_data",
            "no_variation",
        }
        chart = ControlChart()
        chart.calculate_limits([10.0, 11.0, 12.0, 9.0, 10.0, 11.0])
        for v in [10.0, 10.5]:
            chart.add_point(v)
        result = chart.get_capability_indices()
        assert result["interpretation"] in valid_labels

    def test_has_all_keys(self):
        chart = ControlChart()
        chart.calculate_limits([10.0, 11.0, 12.0, 9.0, 10.0, 11.0])
        for v in [10.0, 10.5, 11.0]:
            chart.add_point(v)
        result = chart.get_capability_indices()
        assert "cp" in result
        assert "cpk" in result
        assert "cpu" in result
        assert "cpl" in result
        assert "process_mean" in result


# ── ControlChart.detect_trends ─────────────────────────────────────────


class TestDetectTrends:
    def test_insufficient_data(self):
        chart = ControlChart()
        chart.data_points = [1.0, 2.0]
        result = chart.detect_trends(window_size=7)
        assert result["trend"] == "insufficient_data"

    def test_stable_trend(self):
        chart = ControlChart()
        chart.data_points = [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0]
        result = chart.detect_trends(window_size=7)
        assert result["trend"] == "stable"

    def test_increasing_trend(self):
        chart = ControlChart()
        chart.data_points = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
        result = chart.detect_trends(window_size=7)
        assert result["trend"] == "increasing"

    def test_decreasing_trend(self):
        chart = ControlChart()
        chart.data_points = [7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0]
        result = chart.detect_trends(window_size=7)
        assert result["trend"] == "decreasing"

    def test_has_slope(self):
        chart = ControlChart()
        chart.data_points = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
        result = chart.detect_trends(window_size=7)
        assert result["slope"] > 0

    def test_has_recent_stats(self):
        chart = ControlChart()
        chart.data_points = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
        result = chart.detect_trends(window_size=7)
        assert "recent_mean" in result
        assert "recent_std" in result


# ── CUSUMPoint dataclass ──────────────────────────────────────────────


class TestCUSUMPoint:
    def test_creation(self):
        pt = CUSUMPoint(
            timestamp=datetime(2026, 1, 1),
            value=10.0,
            cusum_high=2.0,
            cusum_low=0.5,
            is_in_control=True,
        )
        assert pt.cusum_high == 2.0
        assert pt.cusum_low == 0.5


# ── CUSUMChart ─────────────────────────────────────────────────────────


class TestCUSUMChart:
    def test_init(self):
        chart = CUSUMChart(target=10.0, sigma=2.0)
        assert chart.target == 10.0
        assert chart.sigma == 2.0
        assert chart.cusum_high == 0.0
        assert chart.cusum_low == 0.0

    def test_k_and_h_scaled(self):
        """k and h are specified in sigma units but stored as absolute."""
        chart = CUSUMChart(target=10.0, sigma=2.0, k=0.5, h=4.0)
        assert chart.k == 1.0  # 0.5 * 2.0
        assert chart.h == 8.0  # 4.0 * 2.0

    def test_add_on_target_point(self):
        chart = CUSUMChart(target=10.0, sigma=2.0, k=0.5, h=4.0)
        pt = chart.add_point(10.0, timestamp=datetime(2026, 1, 1))
        assert isinstance(pt, CUSUMPoint)
        assert pt.is_in_control is True

    def test_cusum_accumulates_upward(self):
        """Points above target accumulate cusum_high."""
        chart = CUSUMChart(target=10.0, sigma=1.0, k=0.5, h=5.0)
        # Add points 2σ above target
        for _ in range(5):
            pt = chart.add_point(12.0)
        assert chart.cusum_high > 0

    def test_cusum_accumulates_downward(self):
        chart = CUSUMChart(target=10.0, sigma=1.0, k=0.5, h=5.0)
        for _ in range(5):
            pt = chart.add_point(8.0)
        assert chart.cusum_low > 0

    def test_cusum_never_negative(self):
        """CUSUM values are clamped to 0 minimum."""
        chart = CUSUMChart(target=10.0, sigma=1.0, k=0.5, h=5.0)
        # On-target points → cusums stay at 0
        for _ in range(10):
            pt = chart.add_point(10.0)
        assert chart.cusum_high == 0.0
        assert chart.cusum_low == 0.0

    def test_detect_upward_shift(self):
        """Large upward shift should trigger out of control."""
        chart = CUSUMChart(target=10.0, sigma=1.0, k=0.5, h=4.0)
        pt = None
        for _ in range(20):
            pt = chart.add_point(13.0)  # 3σ above
        assert pt.is_in_control is False

    def test_detect_downward_shift(self):
        chart = CUSUMChart(target=10.0, sigma=1.0, k=0.5, h=4.0)
        pt = None
        for _ in range(20):
            pt = chart.add_point(7.0)  # 3σ below
        assert pt.is_in_control is False

    def test_reset(self):
        chart = CUSUMChart(target=10.0, sigma=1.0)
        for _ in range(5):
            chart.add_point(15.0)
        assert chart.cusum_high > 0
        chart.reset()
        assert chart.cusum_high == 0.0
        assert chart.cusum_low == 0.0


# ── EWMAPoint dataclass ───────────────────────────────────────────────


class TestEWMAPoint:
    def test_creation(self):
        pt = EWMAPoint(
            timestamp=datetime(2026, 1, 1),
            value=10.0,
            ewma=10.5,
            ucl=15.0,
            lcl=5.0,
            is_in_control=True,
        )
        assert pt.ewma == 10.5
        assert pt.ucl == 15.0


# ── EWMAChart ─────────────────────────────────────────────────────────


class TestEWMAChart:
    def test_init(self):
        chart = EWMAChart(target=10.0, sigma=2.0)
        assert chart.target == 10.0
        assert chart.sigma == 2.0
        assert chart.lambda_ == 0.2
        assert chart.L == 3.0
        assert chart.ewma == 10.0
        assert chart.n == 0

    def test_custom_params(self):
        chart = EWMAChart(target=10.0, sigma=2.0, lambda_=0.3, L=2.5)
        assert chart.lambda_ == 0.3
        assert chart.L == 2.5

    def test_add_point_returns_ewma_point(self):
        chart = EWMAChart(target=10.0, sigma=2.0)
        pt = chart.add_point(10.0, timestamp=datetime(2026, 1, 1))
        assert isinstance(pt, EWMAPoint)

    def test_ewma_on_target(self):
        """EWMA stays at target when all points are on target."""
        chart = EWMAChart(target=10.0, sigma=2.0, lambda_=0.2)
        for _ in range(10):
            pt = chart.add_point(10.0)
        assert abs(pt.ewma - 10.0) < 1e-10

    def test_ewma_update_formula(self):
        """z_t = λ*x_t + (1-λ)*z_{t-1}."""
        chart = EWMAChart(target=10.0, sigma=2.0, lambda_=0.2)
        pt = chart.add_point(15.0)
        # z_1 = 0.2 * 15.0 + 0.8 * 10.0 = 3 + 8 = 11.0
        assert abs(pt.ewma - 11.0) < 1e-10

    def test_ewma_converges_to_shift(self):
        """EWMA should gradually approach a shifted mean."""
        chart = EWMAChart(target=10.0, sigma=2.0, lambda_=0.2)
        for _ in range(100):
            pt = chart.add_point(15.0)
        # Should converge close to 15.0
        assert abs(pt.ewma - 15.0) < 0.1

    def test_in_control_on_target(self):
        chart = EWMAChart(target=10.0, sigma=2.0)
        pt = chart.add_point(10.0)
        assert pt.is_in_control == True  # noqa: E712 (numpy bool)

    def test_out_of_control_shift(self):
        """Large shift should eventually trigger out of control."""
        chart = EWMAChart(target=10.0, sigma=1.0, lambda_=0.3, L=3.0)
        pt = None
        for _ in range(50):
            pt = chart.add_point(20.0)  # 10σ shift
        assert pt.is_in_control == False  # noqa: E712 (numpy bool)

    def test_control_limits_widen_then_stabilize(self):
        """EWMA control limits widen initially then stabilize."""
        chart = EWMAChart(target=10.0, sigma=2.0, lambda_=0.2, L=3.0)
        ucls = []
        for _ in range(20):
            pt = chart.add_point(10.0)
            ucls.append(pt.ucl)
        # UCL should increase initially
        assert ucls[-1] > ucls[0]
        # But stabilize (last few should be close)
        assert abs(ucls[-1] - ucls[-2]) < abs(ucls[1] - ucls[0])

    def test_n_increments(self):
        chart = EWMAChart(target=10.0, sigma=2.0)
        chart.add_point(10.0)
        chart.add_point(11.0)
        assert chart.n == 2

    def test_ucl_above_lcl(self):
        chart = EWMAChart(target=10.0, sigma=2.0)
        pt = chart.add_point(10.0)
        assert pt.ucl > pt.lcl
