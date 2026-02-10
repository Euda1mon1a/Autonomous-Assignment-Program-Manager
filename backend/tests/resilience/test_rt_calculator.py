"""Tests for Rt calculator (pure logic, no DB)."""

import pytest

from app.resilience.epidemiology.rt_calculator import (
    RT_DECLINING_THRESHOLD,
    RT_GROWING_THRESHOLD,
    MIN_CASES_FOR_CONFIDENCE,
    RtCalculator,
    RtEstimate,
)


# -- RtEstimate dataclass ---------------------------------------------------


class TestRtEstimate:
    def test_creation(self):
        from datetime import date

        est = RtEstimate(
            date=date(2026, 1, 15),
            rt_mean=1.2,
            rt_lower=0.8,
            rt_upper=1.6,
            confidence=0.9,
            interpretation="growing",
        )
        assert est.rt_mean == 1.2
        assert est.rt_lower == 0.8
        assert est.rt_upper == 1.6
        assert est.confidence == 0.9
        assert est.interpretation == "growing"

    def test_date_field(self):
        from datetime import date

        est = RtEstimate(
            date=date(2026, 6, 1),
            rt_mean=0.5,
            rt_lower=0.3,
            rt_upper=0.7,
            confidence=1.0,
            interpretation="declining",
        )
        assert est.date == date(2026, 6, 1)


# -- Module-level constants --------------------------------------------------


class TestModuleConstants:
    def test_threshold_values(self):
        assert RT_DECLINING_THRESHOLD == 0.9
        assert RT_GROWING_THRESHOLD == 1.1

    def test_min_cases_for_confidence(self):
        assert MIN_CASES_FOR_CONFIDENCE == 10.0


# -- RtCalculator init -------------------------------------------------------


class TestRtCalculatorInit:
    def test_default_init(self):
        calc = RtCalculator()
        assert calc.serial_interval_mean == 7.0
        assert calc.serial_interval_std == 3.0

    def test_custom_init(self):
        calc = RtCalculator(serial_interval_mean=5.0, serial_interval_std=2.0)
        assert calc.serial_interval_mean == 5.0
        assert calc.serial_interval_std == 2.0


# -- _discretize_serial_interval ---------------------------------------------


class TestDiscretizeSerialInterval:
    def test_sums_to_one(self):
        calc = RtCalculator()
        dist = calc._discretize_serial_interval(20)
        assert sum(dist) == pytest.approx(1.0, abs=0.01)

    def test_all_non_negative(self):
        calc = RtCalculator()
        dist = calc._discretize_serial_interval(20)
        assert all(p >= 0.0 for p in dist)

    def test_length_matches_max_days(self):
        calc = RtCalculator()
        dist = calc._discretize_serial_interval(15)
        assert len(dist) == 15

    def test_peak_near_serial_interval_mean(self):
        calc = RtCalculator(serial_interval_mean=7.0, serial_interval_std=3.0)
        dist = calc._discretize_serial_interval(20)
        peak_day = dist.index(max(dist))
        # Peak should be near the mean (7 days) — within +/- 3 days
        assert 4 <= peak_day <= 10

    def test_single_day(self):
        calc = RtCalculator()
        dist = calc._discretize_serial_interval(1)
        assert len(dist) == 1
        # Single day gets normalized to 1.0
        assert dist[0] == pytest.approx(1.0, abs=0.01)


# -- _calculate_infectiousness -----------------------------------------------


class TestCalculateInfectiousness:
    def test_zero_cases_zero_infectiousness(self):
        calc = RtCalculator()
        result = calc._calculate_infectiousness([0, 0, 0, 0, 0])
        assert result == 0.0

    def test_positive_cases_positive_infectiousness(self):
        calc = RtCalculator()
        result = calc._calculate_infectiousness([5, 3, 2, 4, 6])
        assert result > 0.0

    def test_more_cases_more_infectiousness(self):
        calc = RtCalculator()
        low = calc._calculate_infectiousness([1, 1, 1, 1, 1])
        high = calc._calculate_infectiousness([10, 10, 10, 10, 10])
        assert high > low

    def test_empty_list(self):
        calc = RtCalculator()
        result = calc._calculate_infectiousness([])
        assert result == 0.0


# -- _estimate_rt_cori -------------------------------------------------------


class TestEstimateRtCori:
    def test_empty_window_returns_default(self):
        calc = RtCalculator()
        mean, lower, upper = calc._estimate_rt_cori([], 0)
        assert mean == 1.0
        assert lower == 0.5
        assert upper == 2.0

    def test_all_zeros_returns_default(self):
        calc = RtCalculator()
        mean, lower, upper = calc._estimate_rt_cori([0, 0, 0, 0, 0], 5)
        assert mean == 1.0
        assert lower == 0.5
        assert upper == 2.0

    def test_returns_float_tuple(self):
        calc = RtCalculator()
        result = calc._estimate_rt_cori([5, 3, 4, 6, 5], 5)
        assert len(result) == 3
        assert all(isinstance(v, float) for v in result)

    def test_lower_less_than_upper(self):
        calc = RtCalculator()
        _, lower, upper = calc._estimate_rt_cori([5, 3, 4, 6, 5], 5)
        assert lower < upper

    def test_mean_between_bounds(self):
        calc = RtCalculator()
        mean, lower, upper = calc._estimate_rt_cori([5, 3, 4, 6, 5], 5)
        assert lower <= mean <= upper


# -- calculate_rt ------------------------------------------------------------


class TestCalculateRt:
    def test_insufficient_data_returns_empty(self):
        calc = RtCalculator()
        result = calc.calculate_rt([1, 2, 3], window_size=7)
        assert result == []

    def test_returns_list_of_rt_estimates(self):
        calc = RtCalculator()
        incidence = [5, 3, 4, 6, 5, 7, 8, 6, 5, 4, 3, 5, 6, 7]
        result = calc.calculate_rt(incidence, window_size=7)
        assert len(result) > 0
        assert all(isinstance(r, RtEstimate) for r in result)

    def test_result_count(self):
        calc = RtCalculator()
        incidence = [5] * 14
        result = calc.calculate_rt(incidence, window_size=7)
        # Estimates from index 7 through 13 = 7 estimates
        assert len(result) == 7

    def test_interpretation_values(self):
        calc = RtCalculator()
        incidence = [5, 3, 4, 6, 5, 7, 8, 6, 5, 4, 3, 5, 6, 7]
        result = calc.calculate_rt(incidence, window_size=7)
        valid_interpretations = {"declining", "stable", "growing"}
        for est in result:
            assert est.interpretation in valid_interpretations

    def test_confidence_between_0_and_1(self):
        calc = RtCalculator()
        incidence = [5, 3, 4, 6, 5, 7, 8, 6, 5, 4, 3, 5, 6, 7]
        result = calc.calculate_rt(incidence, window_size=7)
        for est in result:
            assert 0.0 <= est.confidence <= 1.0

    def test_high_cases_high_confidence(self):
        calc = RtCalculator()
        incidence = [20] * 14  # High case counts
        result = calc.calculate_rt(incidence, window_size=7)
        for est in result:
            assert est.confidence == 1.0

    def test_low_cases_low_confidence(self):
        calc = RtCalculator()
        incidence = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0]
        result = calc.calculate_rt(incidence, window_size=7)
        for est in result:
            assert est.confidence < 1.0

    def test_growing_interpretation(self):
        """Steadily increasing cases should produce growing Rt at some point."""
        calc = RtCalculator()
        incidence = [1, 1, 1, 1, 1, 1, 1, 2, 4, 8, 16, 32, 64, 128]
        result = calc.calculate_rt(incidence, window_size=7)
        interpretations = [r.interpretation for r in result]
        assert "growing" in interpretations


# -- calculate_rt_from_r0 ----------------------------------------------------


class TestCalculateRtFromR0:
    def test_fully_susceptible(self):
        calc = RtCalculator()
        rt = calc.calculate_rt_from_r0(r0=2.5, susceptible=100, total_population=100)
        assert rt == pytest.approx(2.5)

    def test_half_susceptible(self):
        calc = RtCalculator()
        rt = calc.calculate_rt_from_r0(r0=2.0, susceptible=50, total_population=100)
        assert rt == pytest.approx(1.0)

    def test_no_susceptible(self):
        calc = RtCalculator()
        rt = calc.calculate_rt_from_r0(r0=3.0, susceptible=0, total_population=100)
        assert rt == pytest.approx(0.0)

    def test_zero_population(self):
        calc = RtCalculator()
        rt = calc.calculate_rt_from_r0(r0=2.5, susceptible=0, total_population=0)
        assert rt == 0.0

    def test_proportional_to_susceptible_fraction(self):
        calc = RtCalculator()
        rt_25 = calc.calculate_rt_from_r0(r0=4.0, susceptible=25, total_population=100)
        rt_75 = calc.calculate_rt_from_r0(r0=4.0, susceptible=75, total_population=100)
        assert rt_75 == pytest.approx(3.0 * rt_25)


# -- forecast_rt_trend -------------------------------------------------------


class TestForecastRtTrend:
    def test_returns_list_of_correct_length(self):
        calc = RtCalculator()
        forecast = calc.forecast_rt_trend(current_rt=1.5, intervention_effect=0.7)
        assert len(forecast) == 14  # Default days_ahead=14

    def test_custom_days_ahead(self):
        calc = RtCalculator()
        forecast = calc.forecast_rt_trend(
            current_rt=1.5, intervention_effect=0.7, days_ahead=30
        )
        assert len(forecast) == 30

    def test_intervention_reduces_rt(self):
        """Strong intervention (0.5 = 50% reduction) should reduce Rt over time."""
        calc = RtCalculator()
        forecast = calc.forecast_rt_trend(current_rt=2.0, intervention_effect=0.5)
        # Later values should be lower than earlier ones
        assert forecast[-1] < forecast[0]

    def test_no_intervention_no_change(self):
        """intervention_effect=1.0 means no reduction."""
        calc = RtCalculator()
        forecast = calc.forecast_rt_trend(current_rt=1.5, intervention_effect=1.0)
        # effective_reduction = 1 - (1 - 1.0) * (...) = 1.0 always
        # So rt * 1.0 = rt at each step... but it compounds:
        # day 0: 1 - 0 * (1 - exp(0)) = 1 - 0 = 1.0, so rt stays same
        for val in forecast:
            assert val == pytest.approx(1.5, abs=0.01)

    def test_all_values_positive(self):
        calc = RtCalculator()
        forecast = calc.forecast_rt_trend(current_rt=2.0, intervention_effect=0.3)
        assert all(v > 0 for v in forecast)

    def test_first_day_effect(self):
        """Day 0: decay_rate=0.1, effective_reduction = 1 - (1-effect)*(1-exp(0)) = 1.0."""
        calc = RtCalculator()
        forecast = calc.forecast_rt_trend(current_rt=2.0, intervention_effect=0.7)
        # Day 0: 1 - (1-0.7)*(1-exp(0)) = 1 - 0.3*0 = 1.0
        # rt * 1.0 = 2.0
        assert forecast[0] == pytest.approx(2.0)


# -- assess_outbreak_control -------------------------------------------------


class TestAssessOutbreakControl:
    def test_controlled_outbreak(self):
        calc = RtCalculator()
        rt_history = [0.8, 0.7, 0.6, 0.5, 0.6, 0.7, 0.6, 0.5, 0.4, 0.5]
        result = calc.assess_outbreak_control(current_rt=0.5, rt_history=rt_history)
        assert result["is_controlled"] is True
        assert result["assessment"] == "Outbreak under control"

    def test_uncontrolled_outbreak(self):
        calc = RtCalculator()
        rt_history = [1.5, 1.3, 1.1, 1.2, 1.4]
        result = calc.assess_outbreak_control(current_rt=1.2, rt_history=rt_history)
        assert result["is_controlled"] is False
        assert "more days" in result["assessment"]

    def test_consecutive_days_count(self):
        calc = RtCalculator()
        # Last 5 values are below 1, but need 7
        rt_history = [1.5, 1.2, 0.9, 0.8, 0.7, 0.6, 0.5]
        result = calc.assess_outbreak_control(
            current_rt=0.5, rt_history=rt_history, days_below_one=7
        )
        assert result["consecutive_days_below_1"] == 5
        assert result["is_controlled"] is False

    def test_current_rt_above_one_not_controlled(self):
        """Even if history is all below 1, current Rt >= 1 means not controlled."""
        calc = RtCalculator()
        rt_history = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        result = calc.assess_outbreak_control(current_rt=1.1, rt_history=rt_history)
        assert result["is_controlled"] is False

    def test_result_keys(self):
        calc = RtCalculator()
        result = calc.assess_outbreak_control(
            current_rt=0.8, rt_history=[0.9, 0.8, 0.7]
        )
        expected_keys = {
            "is_controlled",
            "current_rt",
            "consecutive_days_below_1",
            "days_required",
            "trend_direction",
            "assessment",
        }
        assert set(result.keys()) == expected_keys

    def test_trend_direction_insufficient_data(self):
        calc = RtCalculator()
        result = calc.assess_outbreak_control(
            current_rt=0.8, rt_history=[0.9, 0.8, 0.7]
        )
        assert result["trend_direction"] == "insufficient_data"

    def test_trend_direction_decreasing(self):
        calc = RtCalculator()
        # 14+ values, last 7 much lower than previous 7
        rt_history = [
            2.0,
            1.9,
            1.8,
            1.7,
            1.6,
            1.5,
            1.4,
            0.5,
            0.4,
            0.3,
            0.2,
            0.3,
            0.2,
            0.1,
        ]
        result = calc.assess_outbreak_control(current_rt=0.1, rt_history=rt_history)
        assert result["trend_direction"] == "decreasing"

    def test_trend_direction_increasing(self):
        calc = RtCalculator()
        # 14+ values, last 7 much higher than previous 7
        rt_history = [
            0.2,
            0.3,
            0.2,
            0.1,
            0.2,
            0.3,
            0.2,
            1.5,
            1.6,
            1.7,
            1.8,
            1.9,
            2.0,
            2.1,
        ]
        result = calc.assess_outbreak_control(current_rt=2.0, rt_history=rt_history)
        assert result["trend_direction"] == "increasing"

    def test_trend_direction_stable(self):
        calc = RtCalculator()
        # 14+ values, last 7 ~ same as previous 7
        rt_history = [
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
        ]
        result = calc.assess_outbreak_control(current_rt=1.0, rt_history=rt_history)
        assert result["trend_direction"] == "stable"

    def test_custom_days_below_one(self):
        calc = RtCalculator()
        rt_history = [0.9, 0.8, 0.7]
        result = calc.assess_outbreak_control(
            current_rt=0.7, rt_history=rt_history, days_below_one=3
        )
        assert result["days_required"] == 3
        assert result["is_controlled"] is True

    def test_break_in_consecutive_days(self):
        """A value >= 1 breaks the consecutive count."""
        calc = RtCalculator()
        rt_history = [0.5, 0.6, 1.1, 0.5, 0.6, 0.7, 0.8]
        result = calc.assess_outbreak_control(current_rt=0.8, rt_history=rt_history)
        # Only last 4 are below 1 (after 1.1 break)
        assert result["consecutive_days_below_1"] == 4
