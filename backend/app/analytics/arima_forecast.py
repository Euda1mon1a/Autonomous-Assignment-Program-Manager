"""ARIMA forecasting module for time series predictions.

Provides ARIMAForecaster class for fitting ARIMA models and generating
forecasts for scheduling analytics (workload, coverage, demand patterns).
"""

from typing import Optional, Tuple, List
import warnings

import numpy as np
from numpy.typing import ArrayLike
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller


class ARIMAForecaster:
    """ARIMA time series forecaster with auto parameter selection.

    Fits ARIMA(p, d, q) models to time series data and generates forecasts.
    Supports automatic parameter selection via grid search with AIC criterion.

    Attributes:
        order: Tuple of (p, d, q) ARIMA parameters.
        model: Fitted ARIMA model instance.
        fitted: Whether the model has been fit to data.

    Example:
        >>> forecaster = ARIMAForecaster()
        >>> forecaster.fit([10, 12, 14, 13, 15, 17, 16, 18, 20])
        >>> predictions = forecaster.forecast(steps=3)
    """

    def __init__(
        self,
        order: Optional[Tuple[int, int, int]] = None,
        max_p: int = 3,
        max_d: int = 2,
        max_q: int = 3
    ) -> None:
        """Initialize ARIMAForecaster.

        Args:
            order: Optional fixed (p, d, q) order. If None, auto-selects.
            max_p: Maximum AR order for auto selection.
            max_d: Maximum differencing order for auto selection.
            max_q: Maximum MA order for auto selection.
        """
        self.order = order
        self.max_p = max_p
        self.max_d = max_d
        self.max_q = max_q
        self.model = None
        self.model_fit = None
        self.fitted = False
        self._data = None

    def fit(self, data: ArrayLike) -> "ARIMAForecaster":
        """Fit ARIMA model to time series data.

        Args:
            data: Time series data as array-like of numeric values.
                  Must have at least 10 observations for reliable fitting.

        Returns:
            Self for method chaining.

        Raises:
            ValueError: If data has fewer than 10 observations.
        """
        data = np.asarray(data, dtype=np.float64)

        if len(data) < 10:
            raise ValueError("ARIMA requires at least 10 observations")

        self._data = data

        if self.order is None:
            self.order = self._auto_select_order(data)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.model = ARIMA(data, order=self.order)
            self.model_fit = self.model.fit()

        self.fitted = True
        return self

    def forecast(self, steps: int = 1) -> np.ndarray:
        """Generate forecast for future time steps.

        Args:
            steps: Number of steps ahead to forecast.

        Returns:
            Array of forecasted values.

        Raises:
            RuntimeError: If model has not been fit.
            ValueError: If steps is not positive.
        """
        if not self.fitted:
            raise RuntimeError("Model must be fit before forecasting")

        if steps < 1:
            raise ValueError("steps must be positive")

        forecast = self.model_fit.forecast(steps=steps)
        return np.asarray(forecast)

    def forecast_with_confidence(
        self,
        steps: int = 1,
        alpha: float = 0.05
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Generate forecast with confidence intervals.

        Args:
            steps: Number of steps ahead to forecast.
            alpha: Significance level for confidence interval (default 0.05 = 95% CI).

        Returns:
            Tuple of (forecast, lower_bound, upper_bound) arrays.

        Raises:
            RuntimeError: If model has not been fit.
        """
        if not self.fitted:
            raise RuntimeError("Model must be fit before forecasting")

        forecast = self.model_fit.get_forecast(steps=steps)
        pred = forecast.predicted_mean
        conf_int = forecast.conf_int(alpha=alpha)

        return (
            np.asarray(pred),
            np.asarray(conf_int.iloc[:, 0]),
            np.asarray(conf_int.iloc[:, 1])
        )

    def get_aic(self) -> float:
        """Get Akaike Information Criterion of fitted model.

        Returns:
            AIC value (lower is better).

        Raises:
            RuntimeError: If model has not been fit.
        """
        if not self.fitted:
            raise RuntimeError("Model must be fit first")
        return self.model_fit.aic

    def get_residuals(self) -> np.ndarray:
        """Get model residuals.

        Returns:
            Array of residual values.

        Raises:
            RuntimeError: If model has not been fit.
        """
        if not self.fitted:
            raise RuntimeError("Model must be fit first")
        return np.asarray(self.model_fit.resid)

    def _auto_select_order(self, data: np.ndarray) -> Tuple[int, int, int]:
        """Auto-select ARIMA order using AIC criterion.

        Uses grid search over (p, d, q) combinations and selects
        the model with lowest AIC.

        Args:
            data: Time series data.

        Returns:
            Best (p, d, q) order tuple.
        """
        d = self._determine_differencing(data)

        best_aic = float("inf")
        best_order = (1, d, 1)

        for p in range(self.max_p + 1):
            for q in range(self.max_q + 1):
                if p == 0 and q == 0:
                    continue

                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        model = ARIMA(data, order=(p, d, q))
                        fit = model.fit()

                        if fit.aic < best_aic:
                            best_aic = fit.aic
                            best_order = (p, d, q)
                except Exception:
                    continue

        return best_order

    def _determine_differencing(self, data: np.ndarray) -> int:
        """Determine differencing order using ADF test.

        Args:
            data: Time series data.

        Returns:
            Recommended differencing order (0, 1, or 2).
        """
        for d in range(self.max_d + 1):
            if d == 0:
                test_data = data
            else:
                test_data = np.diff(data, n=d)

            if len(test_data) < 5:
                return d

            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    result = adfuller(test_data, autolag="AIC")
                    p_value = result[1]

                    if p_value < 0.05:
                        return d
            except Exception:
                continue

        return 1
