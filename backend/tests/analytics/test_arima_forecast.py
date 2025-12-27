"""
Tests for ARIMA forecasting module.

This module tests the ARIMA forecasting capabilities for workload prediction,
including model fitting, parameter selection, and forecast generation.
"""

from datetime import date, timedelta

import numpy as np
import pytest

from app.analytics.arima_forecast import (
    ARIMAConfig,
    ARIMAForecaster,
    WorkloadSeries,
    auto_select_arima_order,
    check_stationarity,
    forecast_workload,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_dates() -> list[date]:
    """Generate 60 days of dates for time series."""
    return [date(2025, 1, 1) + timedelta(days=i) for i in range(60)]


@pytest.fixture
def stable_workload() -> np.ndarray:
    """Create stable workload around 8 hours with small noise."""
    np.random.seed(42)
    return np.full(60, 8.0) + np.random.normal(0, 0.5, 60)


@pytest.fixture
def trending_workload() -> np.ndarray:
    """Create workload with upward trend."""
    np.random.seed(42)
    trend = np.linspace(6.0, 12.0, 60)
    noise = np.random.normal(0, 0.3, 60)
    return trend + noise


@pytest.fixture
def seasonal_workload() -> np.ndarray:
    """Create workload with weekly seasonal pattern."""
    np.random.seed(42)
    t = np.arange(60)
    seasonal = 2.0 * np.sin(2 * np.pi * t / 7)  # Weekly cycle
    base = 8.0
    noise = np.random.normal(0, 0.2, 60)
    return base + seasonal + noise


@pytest.fixture
def workload_series(
    stable_workload: np.ndarray, sample_dates: list[date]
) -> WorkloadSeries:
    """Create WorkloadSeries fixture."""
    return WorkloadSeries(values=stable_workload, dates=sample_dates)


# =============================================================================
# WorkloadSeries Tests
# =============================================================================


class TestWorkloadSeries:
    """Tests for WorkloadSeries dataclass."""

    def test_create_valid_series(
        self, stable_workload: np.ndarray, sample_dates: list[date]
    ):
        """Test creating a valid workload series."""
        series = WorkloadSeries(values=stable_workload, dates=sample_dates)
        assert series.length == 60
        assert series.last_date == sample_dates[-1]
        assert series.units == "hours"

    def test_create_series_without_dates(self, stable_workload: np.ndarray):
        """Test creating series without dates."""
        series = WorkloadSeries(values=stable_workload)
        assert series.length == 60
        assert series.last_date is None

    def test_series_minimum_length(self):
        """Test that series requires minimum 10 observations."""
        with pytest.raises(ValueError, match="at least 10 observations"):
            WorkloadSeries(values=np.array([1, 2, 3, 4, 5]))

    def test_series_date_length_mismatch(self, sample_dates: list[date]):
        """Test error on date/value length mismatch."""
        with pytest.raises(ValueError, match="same length"):
            WorkloadSeries(
                values=np.full(30, 8.0),
                dates=sample_dates,  # 60 dates
            )


# =============================================================================
# ARIMAForecaster Tests
# =============================================================================


class TestARIMAForecaster:
    """Tests for ARIMAForecaster class."""

    def test_create_forecaster_default(self):
        """Test creating forecaster with defaults."""
        forecaster = ARIMAForecaster()
        assert forecaster.auto_order is True
        assert forecaster.manual_order is None
        assert forecaster.order_ is None

    def test_create_forecaster_manual_order(self):
        """Test creating forecaster with manual order."""
        forecaster = ARIMAForecaster(auto_order=False, order=(1, 1, 1))
        assert forecaster.auto_order is False
        assert forecaster.manual_order == (1, 1, 1)

    def test_create_forecaster_with_config(self):
        """Test creating forecaster with custom config."""
        config = ARIMAConfig(max_p=3, max_q=3, criterion="bic")
        forecaster = ARIMAForecaster(config=config)
        assert forecaster.config.max_p == 3
        assert forecaster.config.criterion == "bic"

    def test_fit_returns_self(self, stable_workload: np.ndarray):
        """Test that fit() returns self for chaining."""
        forecaster = ARIMAForecaster(auto_order=False, order=(1, 0, 1))
        result = forecaster.fit(stable_workload)
        assert result is forecaster

    def test_fit_sets_order(self, stable_workload: np.ndarray):
        """Test that fit() sets the model order."""
        forecaster = ARIMAForecaster(auto_order=False, order=(1, 1, 1))
        forecaster.fit(stable_workload)
        assert forecaster.order_ == (1, 1, 1)

    def test_fit_auto_order(self, stable_workload: np.ndarray):
        """Test fit with automatic order selection."""
        forecaster = ARIMAForecaster(auto_order=True)
        forecaster.fit(stable_workload)
        assert forecaster.order_ is not None
        assert len(forecaster.order_) == 3

    def test_fit_with_workload_series(self, workload_series: WorkloadSeries):
        """Test fit with WorkloadSeries input."""
        forecaster = ARIMAForecaster(auto_order=False, order=(1, 0, 1))
        forecaster.fit(workload_series)
        assert forecaster.order_ is not None

    def test_fit_with_list(self):
        """Test fit with list input."""
        data = [8.0 + 0.1 * i for i in range(30)]
        forecaster = ARIMAForecaster(auto_order=False, order=(1, 0, 0))
        forecaster.fit(data)
        assert forecaster.order_ is not None

    def test_forecast_not_fitted_error(self):
        """Test forecast() raises error if not fitted."""
        forecaster = ARIMAForecaster()
        with pytest.raises(ValueError, match="not fitted"):
            forecaster.forecast(periods=7)

    def test_forecast_returns_result(self, stable_workload: np.ndarray):
        """Test forecast() returns proper result structure."""
        forecaster = ARIMAForecaster(auto_order=False, order=(1, 0, 1))
        forecaster.fit(stable_workload)
        result = forecaster.forecast(periods=7)

        assert "forecasts" in result
        assert "model_order" in result
        assert "diagnostics" in result
        assert "confidence_level" in result
        assert "generated_at" in result

    def test_forecast_correct_periods(self, stable_workload: np.ndarray):
        """Test forecast() returns correct number of periods."""
        forecaster = ARIMAForecaster(auto_order=False, order=(1, 0, 1))
        forecaster.fit(stable_workload)
        result = forecaster.forecast(periods=14)

        assert len(result["forecasts"]) == 14
        for i, f in enumerate(result["forecasts"]):
            assert f["period"] == i + 1

    def test_forecast_includes_confidence_intervals(self, stable_workload: np.ndarray):
        """Test forecast includes confidence intervals."""
        forecaster = ARIMAForecaster(auto_order=False, order=(1, 0, 1))
        forecaster.fit(stable_workload)
        result = forecaster.forecast(periods=7)

        for f in result["forecasts"]:
            assert "lower_bound" in f
            assert "upper_bound" in f
            assert f["lower_bound"] <= f["value"] <= f["upper_bound"]

    def test_forecast_with_dates(
        self, stable_workload: np.ndarray, sample_dates: list[date]
    ):
        """Test forecast includes future dates when provided."""
        forecaster = ARIMAForecaster(auto_order=False, order=(1, 0, 1))
        forecaster.fit(stable_workload, dates=sample_dates)
        result = forecaster.forecast(periods=7)

        for i, f in enumerate(result["forecasts"]):
            expected_date = (sample_dates[-1] + timedelta(days=i + 1)).isoformat()
            assert f["date"] == expected_date

    def test_forecast_diagnostics(self, stable_workload: np.ndarray):
        """Test forecast returns model diagnostics."""
        forecaster = ARIMAForecaster(auto_order=False, order=(1, 0, 1))
        forecaster.fit(stable_workload)
        result = forecaster.forecast(periods=7)

        diag = result["diagnostics"]
        assert "aic" in diag
        assert "bic" in diag
        assert "order" in diag
        assert "is_stationary" in diag
        assert "residual_mean" in diag
        assert "residual_std" in diag

    def test_get_fitted_values(self, stable_workload: np.ndarray):
        """Test get_fitted_values() returns array."""
        forecaster = ARIMAForecaster(auto_order=False, order=(1, 0, 1))
        forecaster.fit(stable_workload)
        fitted = forecaster.get_fitted_values()

        assert fitted is not None
        assert len(fitted) > 0

    def test_get_residuals(self, stable_workload: np.ndarray):
        """Test get_residuals() returns array."""
        forecaster = ARIMAForecaster(auto_order=False, order=(1, 0, 1))
        forecaster.fit(stable_workload)
        residuals = forecaster.get_residuals()

        assert residuals is not None
        assert len(residuals) > 0


# =============================================================================
# Convenience Function Tests
# =============================================================================


class TestForecastWorkload:
    """Tests for forecast_workload convenience function."""

    def test_basic_forecast(self, stable_workload: np.ndarray):
        """Test basic workload forecasting."""
        result = forecast_workload(stable_workload, periods=7)

        assert len(result["forecasts"]) == 7
        assert result["model_order"] is not None

    def test_forecast_with_dates(
        self, stable_workload: np.ndarray, sample_dates: list[date]
    ):
        """Test forecast with dates."""
        result = forecast_workload(stable_workload, periods=7, dates=sample_dates)

        assert result["forecasts"][0]["date"] is not None

    def test_forecast_manual_order(self, stable_workload: np.ndarray):
        """Test forecast with manual order."""
        result = forecast_workload(
            stable_workload, periods=7, auto_order=False, order=(2, 1, 2)
        )

        assert result["model_order"]["p"] == 2
        assert result["model_order"]["d"] == 1
        assert result["model_order"]["q"] == 2

    def test_forecast_list_input(self):
        """Test forecast with list input."""
        data = [8.0, 8.5, 9.0, 8.2, 7.8, 9.1, 8.3, 8.7, 9.2, 8.1, 8.4, 8.6]
        result = forecast_workload(data, periods=3)

        assert len(result["forecasts"]) == 3


class TestAutoSelectOrder:
    """Tests for auto_select_arima_order function."""

    def test_auto_select_returns_order(self, stable_workload: np.ndarray):
        """Test auto selection returns valid order."""
        order = auto_select_arima_order(stable_workload)

        assert "p" in order
        assert "d" in order
        assert "q" in order
        assert order["p"] >= 0
        assert order["d"] >= 0
        assert order["q"] >= 0

    def test_auto_select_with_bic(self, stable_workload: np.ndarray):
        """Test auto selection with BIC criterion."""
        order = auto_select_arima_order(stable_workload, criterion="bic")

        assert order["p"] >= 0
        assert order["q"] >= 0

    def test_auto_select_constrained_search(self, stable_workload: np.ndarray):
        """Test auto selection with constrained search space."""
        order = auto_select_arima_order(stable_workload, max_p=2, max_d=1, max_q=2)

        assert order["p"] <= 2
        assert order["d"] <= 1
        assert order["q"] <= 2


class TestCheckStationarity:
    """Tests for check_stationarity function."""

    def test_stationary_series(self, stable_workload: np.ndarray):
        """Test stationarity check on stable series."""
        result = check_stationarity(stable_workload)

        # Stable workload should likely be stationary
        assert "is_stationary" in result
        if result.get("error") is None:
            assert "adf_statistic" in result
            assert "p_value" in result
            assert "critical_values" in result

    def test_non_stationary_series(self, trending_workload: np.ndarray):
        """Test stationarity check on trending series."""
        result = check_stationarity(trending_workload)

        # Trending series may not be stationary
        assert "is_stationary" in result

    def test_stationarity_custom_significance(self, stable_workload: np.ndarray):
        """Test stationarity with custom significance level."""
        result = check_stationarity(stable_workload, significance_level=0.01)

        assert result.get("significance_level") == 0.01


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_minimum_data_length(self):
        """Test with minimum data length (10 observations)."""
        data = np.full(10, 8.0)
        forecaster = ARIMAForecaster(auto_order=False, order=(1, 0, 0))
        forecaster.fit(data)
        result = forecaster.forecast(periods=3)

        assert len(result["forecasts"]) == 3

    def test_constant_series(self):
        """Test with constant (no variation) series."""
        data = np.full(30, 8.0)
        result = forecast_workload(data, periods=5, auto_order=False, order=(0, 0, 0))

        # Should still produce forecasts
        assert len(result["forecasts"]) == 5

    def test_negative_values(self):
        """Test with negative values (edge case)."""
        data = np.array([-1.0, 0.0, 1.0, -0.5, 0.5, 1.5, -0.2, 0.8, 1.2, 0.3])
        result = forecast_workload(data, periods=3, auto_order=False, order=(1, 0, 0))

        assert len(result["forecasts"]) == 3

    def test_large_values(self):
        """Test with large values."""
        np.random.seed(42)
        data = np.full(30, 1000.0) + np.random.normal(0, 10, 30)
        result = forecast_workload(data, periods=5, auto_order=False, order=(1, 0, 1))

        # Forecasts should be in similar range
        for f in result["forecasts"]:
            assert 900 < f["value"] < 1100

    def test_forecast_long_horizon(self, stable_workload: np.ndarray):
        """Test forecasting with long horizon."""
        result = forecast_workload(stable_workload, periods=30)

        assert len(result["forecasts"]) == 30
        # Confidence intervals should widen over time
        first_width = (
            result["forecasts"][0]["upper_bound"]
            - result["forecasts"][0]["lower_bound"]
        )
        last_width = (
            result["forecasts"][-1]["upper_bound"]
            - result["forecasts"][-1]["lower_bound"]
        )
        assert last_width >= first_width
