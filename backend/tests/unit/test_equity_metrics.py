"""
Tests for equity and fairness metrics.

This module tests the Gini coefficient, Lorenz curve, and equity report
functionality used for workload fairness analysis in medical scheduling.
"""
import numpy as np
import pytest

from app.resilience.equity_metrics import (
    equity_report,
    gini_coefficient,
    lorenz_curve,
)


class TestGiniCoefficient:
    """Test suite for Gini coefficient calculation."""

    def test_perfect_equality_all_same_values(self) -> None:
        """Test Gini coefficient for perfect equality (all same values)."""
        values = [10.0, 10.0, 10.0, 10.0]
        result = gini_coefficient(values)
        assert result == 0.0, "Perfect equality should have Gini = 0"

    def test_perfect_equality_single_value(self) -> None:
        """Test Gini coefficient for single value."""
        values = [42.0]
        result = gini_coefficient(values)
        assert result == 0.0, "Single value should have Gini = 0"

    def test_perfect_equality_two_same_values(self) -> None:
        """Test Gini coefficient for two identical values."""
        values = [25.0, 25.0]
        result = gini_coefficient(values)
        assert result == 0.0, "Two identical values should have Gini = 0"

    def test_maximum_inequality(self) -> None:
        """Test Gini coefficient approaching maximum inequality."""
        # One person has everything, others have nothing
        values = [0.0, 0.0, 0.0, 100.0]
        result = gini_coefficient(values)
        # For n=4, max Gini = (n-1)/n = 3/4 = 0.75
        assert result == 0.75, "Maximum inequality should approach 1"

    def test_maximum_inequality_large_group(self) -> None:
        """Test Gini coefficient with larger group of zeros."""
        values = [0.0] * 99 + [100.0]
        result = gini_coefficient(values)
        # For n=100, max Gini = (n-1)/n = 99/100 = 0.99
        assert result == pytest.approx(0.99, abs=0.01)

    def test_moderate_inequality(self) -> None:
        """Test Gini coefficient for moderate inequality."""
        values = [10.0, 20.0, 30.0, 40.0]
        result = gini_coefficient(values)
        # This should be between 0 and 1, closer to 0 (relatively equitable)
        assert 0.0 < result < 0.5
        assert result == pytest.approx(0.25, abs=0.01)

    def test_high_inequality(self) -> None:
        """Test Gini coefficient for high inequality."""
        values = [1.0, 2.0, 3.0, 94.0]
        result = gini_coefficient(values)
        # Very unequal distribution
        assert 0.5 < result < 1.0
        assert result > 0.6

    def test_weighted_calculation_equal_weights(self) -> None:
        """Test weighted Gini with equal weights (should equal unweighted)."""
        values = [10.0, 20.0, 30.0, 40.0]
        weights = [1.0, 1.0, 1.0, 1.0]
        weighted_result = gini_coefficient(values, weights=weights)
        unweighted_result = gini_coefficient(values)
        assert weighted_result == pytest.approx(unweighted_result, abs=0.001)

    def test_weighted_calculation_different_weights(self) -> None:
        """Test weighted Gini with different intensity weights."""
        # Same hours but different intensity
        values = [40.0, 40.0, 40.0, 40.0]
        weights = [1.0, 1.0, 1.5, 2.0]  # Last two have higher intensity
        result = gini_coefficient(values, weights=weights)
        # Should show inequality due to intensity differences
        assert result > 0.0

    def test_weighted_calculation_compensating_inequality(self) -> None:
        """Test weighted Gini where weights compensate for hour differences."""
        # Person A: 60 hours at 1.0 intensity = 60 weighted hours
        # Person B: 40 hours at 1.5 intensity = 60 weighted hours
        values = [60.0, 40.0]
        weights = [1.0, 1.5]
        result = gini_coefficient(values, weights=weights)
        # Weighted values are equal, so should be perfect equality
        assert result == pytest.approx(0.0, abs=0.001)

    def test_empty_list_raises_error(self) -> None:
        """Test that empty values list raises ValueError."""
        with pytest.raises(ValueError, match="values list cannot be empty"):
            gini_coefficient([])

    def test_negative_values_raises_error(self) -> None:
        """Test that negative values raise ValueError."""
        with pytest.raises(ValueError, match="values cannot contain negative"):
            gini_coefficient([10.0, -5.0, 20.0])

    def test_negative_weights_raises_error(self) -> None:
        """Test that negative weights raise ValueError."""
        values = [10.0, 20.0, 30.0]
        weights = [1.0, -0.5, 1.0]
        with pytest.raises(ValueError, match="weights cannot contain negative"):
            gini_coefficient(values, weights=weights)

    def test_mismatched_weights_length_raises_error(self) -> None:
        """Test that mismatched weights length raises ValueError."""
        values = [10.0, 20.0, 30.0]
        weights = [1.0, 1.5]  # Wrong length
        with pytest.raises(ValueError, match="weights length.*must match"):
            gini_coefficient(values, weights=weights)

    def test_all_zeros(self) -> None:
        """Test Gini coefficient when all values are zero."""
        values = [0.0, 0.0, 0.0, 0.0]
        result = gini_coefficient(values)
        assert result == 0.0, "All zeros should have Gini = 0"

    def test_floating_point_precision(self) -> None:
        """Test Gini coefficient with floating point values."""
        values = [10.5, 20.3, 30.7, 40.1]
        result = gini_coefficient(values)
        assert 0.0 <= result <= 1.0
        assert isinstance(result, float)

    def test_large_values(self) -> None:
        """Test Gini coefficient with large hour values."""
        values = [1000.0, 2000.0, 3000.0, 4000.0]
        result = gini_coefficient(values)
        # Scale shouldn't affect Gini (it's scale-invariant)
        small_values = [1.0, 2.0, 3.0, 4.0]
        small_result = gini_coefficient(small_values)
        assert result == pytest.approx(small_result, abs=0.001)

    def test_medical_scheduling_scenario_equitable(self) -> None:
        """Test realistic equitable medical scheduling scenario."""
        # 5 residents with similar hours (within 10%)
        values = [165.0, 168.0, 170.0, 162.0, 165.0]
        result = gini_coefficient(values)
        # Should be very equitable (< 0.15 threshold)
        assert result < 0.15

    def test_medical_scheduling_scenario_inequitable(self) -> None:
        """Test realistic inequitable medical scheduling scenario."""
        # One resident significantly overloaded, one underutilized
        values = [80.0, 160.0, 170.0, 165.0, 280.0]
        result = gini_coefficient(values)
        # Should exceed equity threshold
        assert result > 0.15


class TestLorenzCurve:
    """Test suite for Lorenz curve generation."""

    def test_lorenz_curve_perfect_equality(self) -> None:
        """Test Lorenz curve for perfect equality."""
        values = [10.0, 10.0, 10.0, 10.0]
        x_coords, y_coords = lorenz_curve(values)

        # Should have n+1 points (including origin)
        assert len(x_coords) == 5
        assert len(y_coords) == 5

        # First point should be origin
        assert x_coords[0] == 0.0
        assert y_coords[0] == 0.0

        # Last point should be (1, 1)
        assert x_coords[-1] == 1.0
        assert y_coords[-1] == 1.0

        # For perfect equality, Lorenz curve should equal y=x line
        assert np.allclose(x_coords, y_coords)

    def test_lorenz_curve_maximum_inequality(self) -> None:
        """Test Lorenz curve for maximum inequality."""
        values = [0.0, 0.0, 0.0, 100.0]
        x_coords, y_coords = lorenz_curve(values)

        # Should have n+1 points
        assert len(x_coords) == 5
        assert len(y_coords) == 5

        # First 3 people have 0 cumulative share
        assert y_coords[0] == 0.0
        assert y_coords[1] == 0.0
        assert y_coords[2] == 0.0
        assert y_coords[3] == 0.0

        # Last person has 100%
        assert y_coords[4] == 1.0

    def test_lorenz_curve_moderate_distribution(self) -> None:
        """Test Lorenz curve for moderate distribution."""
        values = [10.0, 20.0, 30.0, 40.0]
        x_coords, y_coords = lorenz_curve(values)

        # Check points are properly ordered
        assert all(x_coords[i] <= x_coords[i+1] for i in range(len(x_coords)-1))
        assert all(y_coords[i] <= y_coords[i+1] for i in range(len(y_coords)-1))

        # Lorenz curve should be below or on the equality line (except endpoints)
        for x, y in zip(x_coords, y_coords):
            assert y <= x or np.isclose(y, x)

    def test_lorenz_curve_empty_list_raises_error(self) -> None:
        """Test that empty values list raises ValueError."""
        with pytest.raises(ValueError, match="values list cannot be empty"):
            lorenz_curve([])

    def test_lorenz_curve_negative_values_raises_error(self) -> None:
        """Test that negative values raise ValueError."""
        with pytest.raises(ValueError, match="values cannot contain negative"):
            lorenz_curve([10.0, -5.0, 20.0])

    def test_lorenz_curve_all_zeros(self) -> None:
        """Test Lorenz curve when all values are zero."""
        values = [0.0, 0.0, 0.0, 0.0]
        x_coords, y_coords = lorenz_curve(values)

        # Should return equality line when all values are zero
        assert np.allclose(x_coords, y_coords)

    def test_lorenz_curve_single_value(self) -> None:
        """Test Lorenz curve with single value."""
        values = [42.0]
        x_coords, y_coords = lorenz_curve(values)

        # Should have 2 points: (0, 0) and (1, 1)
        assert len(x_coords) == 2
        assert len(y_coords) == 2
        assert np.allclose(x_coords, [0.0, 1.0])
        assert np.allclose(y_coords, [0.0, 1.0])

    def test_lorenz_curve_returns_numpy_arrays(self) -> None:
        """Test that Lorenz curve returns numpy arrays."""
        values = [10.0, 20.0, 30.0]
        x_coords, y_coords = lorenz_curve(values)

        assert isinstance(x_coords, np.ndarray)
        assert isinstance(y_coords, np.ndarray)

    def test_lorenz_curve_unsorted_input(self) -> None:
        """Test that Lorenz curve handles unsorted input correctly."""
        # Lorenz curve should sort internally
        values_unsorted = [40.0, 10.0, 30.0, 20.0]
        values_sorted = [10.0, 20.0, 30.0, 40.0]

        x_unsorted, y_unsorted = lorenz_curve(values_unsorted)
        x_sorted, y_sorted = lorenz_curve(values_sorted)

        # Results should be identical regardless of input order
        assert np.allclose(x_unsorted, x_sorted)
        assert np.allclose(y_unsorted, y_sorted)


class TestEquityReport:
    """Test suite for comprehensive equity report generation."""

    def test_equity_report_perfect_equality(self) -> None:
        """Test equity report for perfectly equal distribution."""
        provider_hours = {
            "A": 40.0,
            "B": 40.0,
            "C": 40.0,
            "D": 40.0,
        }
        report = equity_report(provider_hours)

        assert report["gini"] == 0.0
        assert report["is_equitable"] is True
        assert report["mean_hours"] == 40.0
        assert report["std_hours"] == 0.0
        assert report["min_hours"] == 40.0
        assert report["max_hours"] == 40.0
        assert "equitable" in report["recommendations"][0].lower()

    def test_equity_report_high_inequality(self) -> None:
        """Test equity report for highly unequal distribution."""
        provider_hours = {
            "A": 20.0,
            "B": 30.0,
            "C": 40.0,
            "D": 110.0,
        }
        report = equity_report(provider_hours)

        assert report["gini"] > 0.15
        assert report["is_equitable"] is False
        assert report["most_overloaded"] == "D"
        assert report["most_underloaded"] == "A"
        assert report["overload_delta"] > 0
        assert report["underload_delta"] > 0
        assert len(report["recommendations"]) > 0

    def test_equity_report_with_intensity_weights(self) -> None:
        """Test equity report with intensity weighting."""
        provider_hours = {
            "A": 40.0,
            "B": 40.0,
            "C": 40.0,
        }
        # Provider C has high-intensity assignments
        intensity_weights = {
            "A": 1.0,
            "B": 1.0,
            "C": 2.0,
        }
        report = equity_report(provider_hours, intensity_weights)

        # Should detect inequality due to intensity differences
        assert report["gini"] > 0.0
        assert report["most_overloaded"] == "C"

    def test_equity_report_statistics(self) -> None:
        """Test that equity report calculates statistics correctly."""
        provider_hours = {
            "A": 30.0,
            "B": 40.0,
            "C": 50.0,
            "D": 60.0,
        }
        report = equity_report(provider_hours)

        assert report["mean_hours"] == 45.0
        assert report["min_hours"] == 30.0
        assert report["max_hours"] == 60.0
        assert report["most_overloaded"] == "D"
        assert report["most_underloaded"] == "A"
        assert report["overload_delta"] == 15.0  # 60 - 45
        assert report["underload_delta"] == 15.0  # 45 - 30

    def test_equity_report_recommendations_overload(self) -> None:
        """Test that recommendations flag overloaded providers."""
        provider_hours = {
            "A": 40.0,
            "B": 40.0,
            "C": 40.0,
            "D": 80.0,  # 100% overload
        }
        report = equity_report(provider_hours)

        recommendations_text = " ".join(report["recommendations"])
        assert "D" in recommendations_text
        assert "above average" in recommendations_text.lower()

    def test_equity_report_recommendations_underload(self) -> None:
        """Test that recommendations flag underloaded providers."""
        provider_hours = {
            "A": 10.0,  # Significantly underloaded
            "B": 40.0,
            "C": 40.0,
            "D": 40.0,
        }
        report = equity_report(provider_hours)

        recommendations_text = " ".join(report["recommendations"])
        assert "A" in recommendations_text
        assert "below average" in recommendations_text.lower()

    def test_equity_report_recommendations_rebalancing(self) -> None:
        """Test that recommendations suggest rebalancing."""
        provider_hours = {
            "A": 30.0,
            "B": 40.0,
            "C": 40.0,
            "D": 70.0,
        }
        report = equity_report(provider_hours)

        # Should suggest transferring hours
        recommendations_text = " ".join(report["recommendations"])
        assert "transfer" in recommendations_text.lower()

    def test_equity_report_target_gini(self) -> None:
        """Test that report includes target Gini threshold."""
        provider_hours = {"A": 40.0, "B": 50.0}
        report = equity_report(provider_hours)

        assert "target_gini" in report
        assert report["target_gini"] == 0.15  # Medical scheduling threshold

    def test_equity_report_empty_dict_raises_error(self) -> None:
        """Test that empty provider_hours dict raises ValueError."""
        with pytest.raises(ValueError, match="provider_hours cannot be empty"):
            equity_report({})

    def test_equity_report_negative_hours_raises_error(self) -> None:
        """Test that negative hours raise ValueError."""
        provider_hours = {"A": 40.0, "B": -10.0}
        with pytest.raises(ValueError, match="cannot contain negative"):
            equity_report(provider_hours)

    def test_equity_report_negative_weights_raises_error(self) -> None:
        """Test that negative intensity weights raise ValueError."""
        provider_hours = {"A": 40.0, "B": 50.0}
        intensity_weights = {"A": 1.0, "B": -0.5}
        with pytest.raises(ValueError, match="cannot contain negative"):
            equity_report(provider_hours, intensity_weights)

    def test_equity_report_mismatched_weights_raises_error(self) -> None:
        """Test that mismatched weight keys raise ValueError."""
        provider_hours = {"A": 40.0, "B": 50.0, "C": 60.0}
        intensity_weights = {"A": 1.0, "B": 1.5}  # Missing C
        with pytest.raises(ValueError, match="keys must match"):
            equity_report(provider_hours, intensity_weights)

    def test_equity_report_high_intensity_warning(self) -> None:
        """Test that report warns about high intensity providers."""
        provider_hours = {"A": 40.0, "B": 40.0, "C": 40.0}
        intensity_weights = {"A": 1.0, "B": 1.0, "C": 3.0}  # C has very high intensity

        report = equity_report(provider_hours, intensity_weights)

        recommendations_text = " ".join(report["recommendations"])
        assert "C" in recommendations_text
        assert "intensity" in recommendations_text.lower()

    def test_equity_report_single_provider(self) -> None:
        """Test equity report with single provider."""
        provider_hours = {"A": 40.0}
        report = equity_report(provider_hours)

        assert report["gini"] == 0.0
        assert report["is_equitable"] is True
        assert report["most_overloaded"] == "A"
        assert report["most_underloaded"] == "A"

    def test_equity_report_two_providers(self) -> None:
        """Test equity report with two providers."""
        provider_hours = {"A": 30.0, "B": 50.0}
        report = equity_report(provider_hours)

        assert report["mean_hours"] == 40.0
        assert report["most_overloaded"] == "B"
        assert report["most_underloaded"] == "A"

    def test_equity_report_real_world_scenario(self) -> None:
        """Test equity report with realistic medical scheduling data."""
        provider_hours = {
            "Resident_001": 168.0,
            "Resident_002": 172.0,
            "Resident_003": 165.0,
            "Resident_004": 170.0,
            "Resident_005": 163.0,
            "Resident_006": 175.0,
        }
        report = equity_report(provider_hours)

        # This should be equitable (low variation)
        assert report["is_equitable"] is True
        assert report["gini"] < 0.15
        assert 163.0 <= report["mean_hours"] <= 175.0

    def test_equity_report_intensity_compensated_scenario(self) -> None:
        """Test scenario where intensity weights compensate for hour differences."""
        # Junior residents work more hours but at lower intensity
        # Senior residents work fewer hours but higher intensity
        provider_hours = {
            "PGY1_A": 80.0,
            "PGY1_B": 80.0,
            "PGY3_A": 60.0,
            "PGY3_B": 60.0,
        }
        intensity_weights = {
            "PGY1_A": 1.0,
            "PGY1_B": 1.0,
            "PGY3_A": 1.33,  # 80/60 = 1.33
            "PGY3_B": 1.33,
        }
        report = equity_report(provider_hours, intensity_weights)

        # Should be equitable when intensity-adjusted
        assert report["gini"] < 0.15
        assert report["is_equitable"] is True

    def test_equity_report_contains_all_required_fields(self) -> None:
        """Test that equity report contains all required fields."""
        provider_hours = {"A": 40.0, "B": 50.0, "C": 60.0}
        report = equity_report(provider_hours)

        required_fields = [
            "gini",
            "target_gini",
            "is_equitable",
            "mean_hours",
            "std_hours",
            "min_hours",
            "max_hours",
            "most_overloaded",
            "most_underloaded",
            "overload_delta",
            "underload_delta",
            "recommendations",
        ]

        for field in required_fields:
            assert field in report, f"Missing required field: {field}"

    def test_equity_report_recommendations_is_list(self) -> None:
        """Test that recommendations field is a list."""
        provider_hours = {"A": 40.0, "B": 50.0}
        report = equity_report(provider_hours)

        assert isinstance(report["recommendations"], list)
        assert len(report["recommendations"]) > 0
        assert all(isinstance(rec, str) for rec in report["recommendations"])
