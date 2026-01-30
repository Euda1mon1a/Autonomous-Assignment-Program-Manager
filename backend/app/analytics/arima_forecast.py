"""
ARIMA Forecasting Module for Workload Time Series.

This module provides ARIMA (AutoRegressive Integrated Moving Average) forecasting
capabilities for medical residency scheduling workload prediction.

Key Capabilities:
-----------------
1. Basic ARIMA(p,d,q) model fitting for workload time series
2. Automatic parameter selection using AIC/BIC criteria
3. Simple forecast generation with confidence intervals
4. Integration with existing analytics patterns

The module supports forecasting future workload demands based on historical
patterns, enabling proactive scheduling adjustments.

Usage:
------
    from app.analytics.arima_forecast import ARIMAForecaster, forecast_workload

    # Quick forecast
    result = forecast_workload(
        workload_history=[8.0, 10.0, 9.5, 11.0, 10.5, ...],
        periods=7
    )

    # Advanced usage with custom parameters
    forecaster = ARIMAForecaster(auto_order=True, criterion="aic")
    forecaster.fit(workload_series)
    predictions = forecaster.forecast(periods=14)
"""

import logging
import warnings
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import TypedDict

import numpy as np
from numpy.typing import NDArray

# Try to import statsmodels ARIMA
try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller

    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    ARIMA = None  # type: ignore
    adfuller = None  # type: ignore

logger = logging.getLogger(__name__)


# =============================================================================
# Type Definitions
# =============================================================================


class ARIMAOrder(TypedDict):
    """ARIMA model order parameters."""

    p: int  # AR order (autoregressive)
    d: int  # Differencing order
    q: int  # MA order (moving average)


class ForecastPoint(TypedDict):
    """Single forecast point with confidence interval."""

    period: int
    value: float
    lower_bound: float
    upper_bound: float
    date: str | None


class ModelDiagnostics(TypedDict):
    """Model fit diagnostics."""

    aic: float
    bic: float
    order: ARIMAOrder
    is_stationary: bool
    residual_mean: float
    residual_std: float


class ForecastResult(TypedDict):
    """Complete forecast result."""

    forecasts: list[ForecastPoint]
    model_order: ARIMAOrder
    diagnostics: ModelDiagnostics
    confidence_level: float
    generated_at: str

    # =============================================================================
    # Dataclasses
    # =============================================================================


@dataclass
class WorkloadSeries:
    """Workload time series for ARIMA modeling."""

    values: NDArray[np.float64]
    dates: list[date] | None = None
    units: str = "hours"

    def __post_init__(self) -> None:
        """Validate time series data."""
        if len(self.values) < 10:
            raise ValueError("Time series must have at least 10 observations for ARIMA")
        if self.dates is not None and len(self.dates) != len(self.values):
            raise ValueError("Dates and values must have same length")

    @property
    def length(self) -> int:
        """Return series length."""
        return len(self.values)

    @property
    def last_date(self) -> date | None:
        """Return last date in series."""
        return self.dates[-1] if self.dates else None


@dataclass
class ARIMAConfig:
    """Configuration for ARIMA model fitting."""

    max_p: int = 5  # Maximum AR order to search
    max_d: int = 2  # Maximum differencing order
    max_q: int = 5  # Maximum MA order to search
    criterion: str = "aic"  # Selection criterion: "aic" or "bic"
    significance_level: float = 0.05  # For stationarity test
    confidence_level: float = 0.95  # For prediction intervals
    seasonal: bool = False  # Seasonal ARIMA (SARIMA) - not implemented yet

    # =============================================================================
    # Core ARIMA Forecaster Class
    # =============================================================================


class ARIMAForecaster:
    """
    ARIMA forecaster for workload time series.

    This class provides ARIMA model fitting and forecasting with automatic
    or manual order selection.

    Example:
        forecaster = ARIMAForecaster(auto_order=True)
        forecaster.fit(workload_values)
        result = forecaster.forecast(periods=7)

    Attributes:
        auto_order: Whether to automatically select ARIMA order
        config: Configuration for model fitting
        model_: Fitted ARIMA model (after fit())
        order_: Selected (p, d, q) order
    """

    def __init__(
        self,
        auto_order: bool = True,
        order: tuple[int, int, int] | None = None,
        config: ARIMAConfig | None = None,
    ) -> None:
        """
        Initialize ARIMA forecaster.

        Args:
            auto_order: Automatically select best (p, d, q) using AIC/BIC
            order: Manual (p, d, q) order if auto_order is False
            config: Configuration for parameter selection
        """
        self.auto_order = auto_order
        self.manual_order = order
        self.config = config or ARIMAConfig()

        self.model_ = None
        self.order_: tuple[int, int, int] | None = None
        self.fitted_values_: NDArray[np.float64] | None = None
        self.residuals_: NDArray[np.float64] | None = None
        self._series: WorkloadSeries | None = None

        if not HAS_STATSMODELS:
            logger.warning(
                "statsmodels not installed. ARIMA forecasting will use fallback methods."
            )

    def fit(
        self,
        data: NDArray[np.float64] | list[float] | WorkloadSeries,
        dates: list[date] | None = None,
    ) -> "ARIMAForecaster":
        """
        Fit ARIMA model to workload data.

        Args:
            data: Workload time series (array, list, or WorkloadSeries)
            dates: Optional dates for the series

        Returns:
            Self for method chaining
        """
        # Convert input to WorkloadSeries
        if isinstance(data, WorkloadSeries):
            self._series = data
        else:
            values = np.array(data, dtype=np.float64)
            self._series = WorkloadSeries(values=values, dates=dates)

        if not HAS_STATSMODELS:
            # Fallback: use simple moving average model
            self._fit_fallback()
            return self

            # Determine differencing order (d) if auto
        if self.auto_order:
            d = self._determine_differencing_order()
            p, q = self._select_arma_order(d)
            self.order_ = (p, d, q)
        else:
            self.order_ = self.manual_order or (1, 1, 1)

            # Fit ARIMA model
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                model = ARIMA(self._series.values, order=self.order_)
                self.model_ = model.fit()
                self.fitted_values_ = self.model_.fittedvalues
                self.residuals_ = self.model_.resid

                logger.info(
                    f"ARIMA{self.order_} fitted: AIC={self.model_.aic:.2f}, "
                    f"BIC={self.model_.bic:.2f}"
                )
            except Exception as e:
                logger.warning(f"ARIMA fitting failed: {e}. Using fallback.")
                self._fit_fallback()

        return self

    def _fit_fallback(self) -> None:
        """Fit simple fallback model when statsmodels unavailable."""
        self.order_ = (0, 0, 0)
        self.fitted_values_ = np.full_like(
            self._series.values, np.mean(self._series.values)
        )
        self.residuals_ = self._series.values - self.fitted_values_
        logger.info("Using fallback model (mean baseline)")

    def _determine_differencing_order(self) -> int:
        """
        Determine differencing order (d) using ADF test.

        Returns:
            Optimal differencing order (0, 1, or 2)
        """
        if not HAS_STATSMODELS:
            return 1  # Default fallback

        series = self._series.values.copy()

        for d in range(self.config.max_d + 1):
            # Apply differencing
            if d > 0:
                series = np.diff(series)

            if len(series) < 10:
                return max(0, d - 1)

                # ADF test for stationarity
            try:
                result = adfuller(series, autolag="AIC")
                p_value = result[1]

                if p_value < self.config.significance_level:
                    logger.debug(f"Series stationary at d={d} (p={p_value:.4f})")
                    return d
            except Exception as e:
                logger.debug(f"ADF test failed at d={d}: {e}")
                continue

        return 1  # Default if no stationarity found

    def _select_arma_order(self, d: int) -> tuple[int, int]:
        """
        Select best (p, q) order using grid search with AIC/BIC.

        Args:
            d: Differencing order

        Returns:
            Tuple of (p, q) orders
        """
        if not HAS_STATSMODELS:
            return (1, 1)

        best_score = float("inf")
        best_order = (1, 1)

        series = self._series.values

        for p in range(self.config.max_p + 1):
            for q in range(self.config.max_q + 1):
                if p == 0 and q == 0:
                    continue  # Skip (0, d, 0)

                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        model = ARIMA(series, order=(p, d, q))
                        fitted = model.fit()

                        if self.config.criterion == "bic":
                            score = fitted.bic
                        else:
                            score = fitted.aic

                        if score < best_score:
                            best_score = score
                            best_order = (p, q)

                except Exception:
                    continue  # Skip failed models

        logger.debug(
            f"Selected ARMA order: p={best_order[0]}, q={best_order[1]} "
            f"({self.config.criterion.upper()}={best_score:.2f})"
        )

        return best_order

    def forecast(
        self,
        periods: int = 7,
        confidence_level: float | None = None,
    ) -> ForecastResult:
        """
        Generate forecasts for future periods.

        Args:
            periods: Number of periods to forecast
            confidence_level: Confidence level for intervals (default: 0.95)

        Returns:
            ForecastResult with predictions and diagnostics
        """
        if self.order_ is None:
            raise ValueError("Model not fitted. Call fit() first.")

        confidence = confidence_level or self.config.confidence_level
        alpha = 1 - confidence

        from datetime import datetime

        forecasts: list[ForecastPoint] = []

        if self.model_ is not None and HAS_STATSMODELS:
            # Use statsmodels forecast
            try:
                forecast_obj = self.model_.get_forecast(steps=periods)
                predictions = forecast_obj.predicted_mean
                conf_int = forecast_obj.conf_int(alpha=alpha)

                # Convert to numpy arrays for consistent indexing
                pred_values = np.asarray(predictions)
                conf_lower = (
                    np.asarray(conf_int.iloc[:, 0])
                    if hasattr(conf_int, "iloc")
                    else conf_int[:, 0]
                )
                conf_upper = (
                    np.asarray(conf_int.iloc[:, 1])
                    if hasattr(conf_int, "iloc")
                    else conf_int[:, 1]
                )

                for i in range(periods):
                    forecast_date = None
                    if self._series.last_date:
                        forecast_date = (
                            self._series.last_date + timedelta(days=i + 1)
                        ).isoformat()

                    forecasts.append(
                        {
                            "period": i + 1,
                            "value": float(pred_values[i]),
                            "lower_bound": float(conf_lower[i]),
                            "upper_bound": float(conf_upper[i]),
                            "date": forecast_date,
                        }
                    )
            except Exception as e:
                logger.warning(f"Statsmodels forecast failed: {e}. Using fallback.")
                forecasts = self._forecast_fallback(periods, alpha)
        else:
            # Fallback forecast
            forecasts = self._forecast_fallback(periods, alpha)

            # Build diagnostics
        diagnostics = self._get_diagnostics()

        return {
            "forecasts": forecasts,
            "model_order": {
                "p": self.order_[0],
                "d": self.order_[1],
                "q": self.order_[2],
            },
            "diagnostics": diagnostics,
            "confidence_level": confidence,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _forecast_fallback(self, periods: int, alpha: float) -> list[ForecastPoint]:
        """Generate fallback forecasts using simple methods."""
        forecasts = []

        # Use last 14 values (or available) for simple forecasting
        recent = self._series.values[-min(14, len(self._series.values)) :]
        mean_val = float(np.mean(recent))
        std_val = float(np.std(recent))

        # Simple z-interval
        z = 1.96 if alpha <= 0.05 else 1.645

        for i in range(periods):
            # Add slight uncertainty growth over time
            uncertainty = std_val * (1 + 0.1 * i)

            forecast_date = None
            if self._series.last_date:
                forecast_date = (
                    self._series.last_date + timedelta(days=i + 1)
                ).isoformat()

            forecasts.append(
                {
                    "period": i + 1,
                    "value": mean_val,
                    "lower_bound": mean_val - z * uncertainty,
                    "upper_bound": mean_val + z * uncertainty,
                    "date": forecast_date,
                }
            )

        return forecasts

    def _get_diagnostics(self) -> ModelDiagnostics:
        """Get model diagnostics."""
        if self.model_ is not None and HAS_STATSMODELS:
            aic = float(self.model_.aic)
            bic = float(self.model_.bic)
        else:
            # Fallback diagnostics
            n = len(self._series.values)
            rss = (
                float(np.sum(self.residuals_**2)) if self.residuals_ is not None else 0
            )
            k = sum(self.order_) + 1  # Number of parameters
            aic = n * np.log(rss / n) + 2 * k
            bic = n * np.log(rss / n) + k * np.log(n)

            # Check stationarity
        is_stationary = True
        if HAS_STATSMODELS and self._series is not None:
            try:
                result = adfuller(self._series.values, autolag="AIC")
                is_stationary = result[1] < self.config.significance_level
            except Exception:
                is_stationary = False

        residual_mean = (
            float(np.mean(self.residuals_)) if self.residuals_ is not None else 0
        )
        residual_std = (
            float(np.std(self.residuals_)) if self.residuals_ is not None else 0
        )

        return {
            "aic": aic,
            "bic": bic,
            "order": {
                "p": self.order_[0],
                "d": self.order_[1],
                "q": self.order_[2],
            },
            "is_stationary": is_stationary,
            "residual_mean": residual_mean,
            "residual_std": residual_std,
        }

    def get_fitted_values(self) -> NDArray[np.float64] | None:
        """Return fitted values from the model."""
        return self.fitted_values_

    def get_residuals(self) -> NDArray[np.float64] | None:
        """Return model residuals."""
        return self.residuals_

        # =============================================================================
        # Convenience Functions
        # =============================================================================


def forecast_workload(
    workload_history: list[float] | NDArray[np.float64],
    periods: int = 7,
    dates: list[date] | None = None,
    auto_order: bool = True,
    order: tuple[int, int, int] | None = None,
) -> ForecastResult:
    """
    Convenience function for quick workload forecasting.

    Args:
        workload_history: Historical workload values (e.g., daily hours)
        periods: Number of future periods to forecast
        dates: Optional dates for the historical series
        auto_order: Whether to auto-select ARIMA order
        order: Manual (p, d, q) order if auto_order is False

    Returns:
        ForecastResult with predictions and diagnostics

    Example:
        result = forecast_workload(
            workload_history=[8, 10, 9.5, 11, 10.5, 9, 8.5, 12, 11, 10],
            periods=7
        )
        for f in result["forecasts"]:
            print(f"Period {f['period']}: {f['value']:.1f} hours")
    """
    forecaster = ARIMAForecaster(auto_order=auto_order, order=order)
    forecaster.fit(np.array(workload_history, dtype=np.float64), dates=dates)
    return forecaster.forecast(periods=periods)


def auto_select_arima_order(
    workload_history: list[float] | NDArray[np.float64],
    criterion: str = "aic",
    max_p: int = 5,
    max_d: int = 2,
    max_q: int = 5,
) -> ARIMAOrder:
    """
    Auto-select optimal ARIMA order using information criteria.

    Args:
        workload_history: Historical workload values
        criterion: Selection criterion ("aic" or "bic")
        max_p: Maximum AR order to search
        max_d: Maximum differencing order
        max_q: Maximum MA order to search

    Returns:
        ARIMAOrder dict with optimal (p, d, q)
    """
    config = ARIMAConfig(
        max_p=max_p,
        max_d=max_d,
        max_q=max_q,
        criterion=criterion,
    )

    forecaster = ARIMAForecaster(auto_order=True, config=config)
    forecaster.fit(np.array(workload_history, dtype=np.float64))

    if forecaster.order_ is None:
        return {"p": 1, "d": 1, "q": 1}  # Default

    return {
        "p": forecaster.order_[0],
        "d": forecaster.order_[1],
        "q": forecaster.order_[2],
    }


def check_stationarity(
    workload_history: list[float] | NDArray[np.float64],
    significance_level: float = 0.05,
) -> dict:
    """
    Check if a workload series is stationary using ADF test.

    Args:
        workload_history: Historical workload values
        significance_level: Significance level for the test

    Returns:
        Dict with stationarity result and test statistics
    """
    if not HAS_STATSMODELS:
        return {
            "is_stationary": None,
            "error": "statsmodels not installed",
        }

    values = np.array(workload_history, dtype=np.float64)

    try:
        result = adfuller(values, autolag="AIC")
        adf_stat = result[0]
        p_value = result[1]
        critical_values = result[4]

        return {
            "is_stationary": p_value < significance_level,
            "adf_statistic": float(adf_stat),
            "p_value": float(p_value),
            "critical_values": {k: float(v) for k, v in critical_values.items()},
            "significance_level": significance_level,
        }
    except Exception as e:
        return {
            "is_stationary": None,
            "error": str(e),
        }
