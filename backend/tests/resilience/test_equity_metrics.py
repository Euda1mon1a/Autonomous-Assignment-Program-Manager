"""Tests for Equity and Fairness Metrics (Gini coefficient, Lorenz curve, equity report)."""

import numpy as np
import pytest

from app.resilience.equity_metrics import (
    equity_report,
    gini_coefficient,
    lorenz_curve,
)


# ==================== gini_coefficient ====================


class TestGiniCoefficient:
    def test_perfect_equality(self):
        assert gini_coefficient([10, 10, 10, 10]) == 0.0

    def test_single_value(self):
        assert gini_coefficient([42]) == 0.0

    def test_all_zeros(self):
        assert gini_coefficient([0, 0, 0]) == 0.0

    def test_known_result(self):
        # [0, 0, 0, 100] -> Gini = 0.75
        g = gini_coefficient([0, 0, 0, 100])
        assert abs(g - 0.75) < 0.001

    def test_moderate_inequality(self):
        g = gini_coefficient([10, 20, 30, 40])
        # Known Gini for uniform step: ~0.25
        assert 0.1 < g < 0.4

    def test_bounded_0_to_1(self):
        g = gini_coefficient([1, 1000])
        assert 0.0 <= g <= 1.0

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            gini_coefficient([])

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="negative"):
            gini_coefficient([-1, 5, 10])

    def test_with_weights(self):
        g = gini_coefficient([20, 30, 40], weights=[1.0, 1.5, 2.0])
        assert 0.0 <= g <= 1.0

    def test_weights_length_mismatch(self):
        with pytest.raises(ValueError, match="weights length"):
            gini_coefficient([1, 2], weights=[1.0])

    def test_negative_weights_raises(self):
        with pytest.raises(ValueError, match="weights.*negative"):
            gini_coefficient([10, 20], weights=[-1.0, 1.0])

    def test_equal_weighted_values_zero(self):
        # Same values -> same weighted values -> Gini = 0
        g = gini_coefficient([5, 5, 5], weights=[2.0, 2.0, 2.0])
        assert g == 0.0

    def test_weights_amplify_inequality(self):
        # Without weights
        g_no_w = gini_coefficient([10, 20])
        # With weights that amplify the spread
        g_w = gini_coefficient([10, 20], weights=[0.5, 2.0])
        assert g_w > g_no_w


# ==================== lorenz_curve ====================


class TestLorenzCurve:
    def test_returns_two_arrays(self):
        x, y = lorenz_curve([1, 2, 3])
        assert isinstance(x, np.ndarray)
        assert isinstance(y, np.ndarray)

    def test_length_n_plus_1(self):
        x, y = lorenz_curve([10, 20, 30, 40])
        assert len(x) == 5
        assert len(y) == 5

    def test_starts_at_zero(self):
        x, y = lorenz_curve([5, 10])
        assert x[0] == 0.0
        assert y[0] == 0.0

    def test_ends_at_one(self):
        x, y = lorenz_curve([5, 10, 15])
        assert abs(x[-1] - 1.0) < 1e-10
        assert abs(y[-1] - 1.0) < 1e-10

    def test_perfect_equality(self):
        x, y = lorenz_curve([25, 25, 25, 25])
        # Perfect equality: y should be close to x
        np.testing.assert_allclose(y, x, atol=0.01)

    def test_inequality(self):
        x, y = lorenz_curve([1, 1, 1, 97])
        # Bottom 75% has only 3% of total -> y[3] << x[3]
        assert y[3] < x[3]

    def test_all_zeros(self):
        x, y = lorenz_curve([0, 0, 0])
        # Should return equality line
        np.testing.assert_allclose(y, x, atol=1e-10)

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            lorenz_curve([])

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="negative"):
            lorenz_curve([-1, 5])

    def test_monotonically_increasing(self):
        _, y = lorenz_curve([10, 5, 20, 50])
        for i in range(1, len(y)):
            assert y[i] >= y[i - 1]


# ==================== equity_report ====================


class TestEquityReport:
    def test_equitable_distribution(self):
        hours = {"A": 40, "B": 41, "C": 39, "D": 40}
        report = equity_report(hours)
        assert report["is_equitable"] is True
        assert report["gini"] < 0.15

    def test_inequitable_distribution(self):
        hours = {"A": 10, "B": 80, "C": 15, "D": 75}
        report = equity_report(hours)
        assert report["is_equitable"] is False
        assert report["gini"] >= 0.15

    def test_report_keys(self):
        hours = {"A": 40, "B": 50}
        report = equity_report(hours)
        expected_keys = {
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
        }
        assert expected_keys == set(report.keys())

    def test_target_gini_is_015(self):
        report = equity_report({"A": 40, "B": 40})
        assert report["target_gini"] == 0.15

    def test_statistics_correct(self):
        hours = {"A": 20, "B": 40, "C": 60}
        report = equity_report(hours)
        assert abs(report["mean_hours"] - 40.0) < 0.01
        assert abs(report["min_hours"] - 20.0) < 0.01
        assert abs(report["max_hours"] - 60.0) < 0.01

    def test_most_overloaded_underloaded(self):
        hours = {"X": 10, "Y": 50, "Z": 30}
        report = equity_report(hours)
        assert report["most_overloaded"] == "Y"
        assert report["most_underloaded"] == "X"

    def test_recommendations_nonempty(self):
        hours = {"A": 40, "B": 40}
        report = equity_report(hours)
        assert len(report["recommendations"]) > 0

    def test_inequitable_has_actionable_recommendations(self):
        hours = {"A": 10, "B": 90}
        report = equity_report(hours)
        assert any(
            "inequality" in r.lower() or "gini" in r.lower()
            for r in report["recommendations"]
        )

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            equity_report({})

    def test_negative_hours_raises(self):
        with pytest.raises(ValueError, match="negative"):
            equity_report({"A": -5, "B": 10})

    def test_with_intensity_weights(self):
        hours = {"A": 40, "B": 40, "C": 40}
        weights = {"A": 1.0, "B": 1.5, "C": 2.0}
        report = equity_report(hours, intensity_weights=weights)
        # With different weights, the same raw hours become unequal
        assert report["gini"] > 0.0

    def test_intensity_weights_key_mismatch(self):
        with pytest.raises(ValueError, match="keys must match"):
            equity_report({"A": 40}, intensity_weights={"B": 1.0})

    def test_negative_intensity_weights_raises(self):
        with pytest.raises(ValueError, match="negative"):
            equity_report({"A": 40}, intensity_weights={"A": -1.0})

    def test_high_intensity_warning(self):
        hours = {"A": 40, "B": 40, "C": 40}
        weights = {"A": 1.0, "B": 1.0, "C": 3.0}
        report = equity_report(hours, intensity_weights=weights)
        assert any("intensity" in r.lower() for r in report["recommendations"])

    def test_overload_delta_positive(self):
        hours = {"A": 10, "B": 90}
        report = equity_report(hours)
        assert report["overload_delta"] > 0
        assert report["underload_delta"] > 0
