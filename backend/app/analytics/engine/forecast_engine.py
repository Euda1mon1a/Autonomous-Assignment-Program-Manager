"""
Forecast Engine - Forecasts future metrics based on historical data.
"""

from typing import Any, Dict, List, Optional
import logging

import pandas as pd
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


class ForecastEngine:
    """
    Forecasts future schedule metrics.

    Methods:
    - Simple moving average
    - Exponential smoothing
    - Linear trend projection
    - Seasonal decomposition
    """

    def forecast(
        self,
        time_series_data: Dict[str, pd.Series],
        periods: int = 4,
        method: str = "auto",
    ) -> Dict[str, Dict[str, Any]]:
        """
        Forecast multiple metrics.

        Args:
            time_series_data: Dict of metric name to Series
            periods: Number of periods to forecast
            method: Forecast method (auto, moving_average, exponential, linear)

        Returns:
            Dict of metric name to forecast results
        """
        forecasts = {}

        for metric_name, series in time_series_data.items():
            if len(series) >= 3:
                if method == "auto":
                    forecast_method = self._select_best_method(series)
                else:
                    forecast_method = method

                forecasts[metric_name] = self._forecast_series(
                    series, periods, forecast_method
                )
            else:
                forecasts[metric_name] = {
                    "method": "insufficient_data",
                    "predicted_values": [],
                    "confidence_intervals": [],
                }

        return forecasts

    def _select_best_method(self, series: pd.Series) -> str:
        """
        Select best forecast method based on data characteristics.

        Args:
            series: Time series data

        Returns:
            Best method name
        """
        # Check for trend
        x = np.arange(len(series))
        y = series.values
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        has_strong_trend = (abs(slope) > 0.1 and r_value ** 2 > 0.5)

        # Check for seasonality
        if len(series) > 7:
            autocorr_7 = series.autocorr(lag=7)
            has_seasonality = abs(autocorr_7) > 0.3
        else:
            has_seasonality = False

        # Select method
        if has_strong_trend:
            return "linear"
        elif has_seasonality:
            return "exponential"
        else:
            return "moving_average"

    def _forecast_series(
        self,
        series: pd.Series,
        periods: int,
        method: str,
    ) -> Dict[str, Any]:
        """
        Forecast a single time series.

        Args:
            series: Time series data
            periods: Number of periods to forecast
            method: Forecast method

        Returns:
            Forecast results with predictions and confidence intervals
        """
        series = series.dropna()

        if method == "moving_average":
            return self._forecast_moving_average(series, periods)
        elif method == "exponential":
            return self._forecast_exponential_smoothing(series, periods)
        elif method == "linear":
            return self._forecast_linear_trend(series, periods)
        else:
            return self._forecast_moving_average(series, periods)

    def _forecast_moving_average(
        self,
        series: pd.Series,
        periods: int,
        window: int = 4,
    ) -> Dict[str, Any]:
        """Forecast using simple moving average."""
        if len(series) < window:
            window = len(series)

        # Calculate moving average
        ma = series.rolling(window=window).mean()
        last_ma = ma.iloc[-1]

        # Predict constant value
        predicted_values = [last_ma] * periods

        # Calculate prediction interval using historical std
        std = series.std()
        confidence_intervals = [
            {"lower": last_ma - 2 * std, "upper": last_ma + 2 * std}
            for _ in range(periods)
        ]

        return {
            "method": "moving_average",
            "window": window,
            "predicted_values": [float(v) for v in predicted_values],
            "predicted_mean": float(last_ma),
            "confidence_intervals": [
                {"lower": float(ci["lower"]), "upper": float(ci["upper"])}
                for ci in confidence_intervals
            ],
        }

    def _forecast_exponential_smoothing(
        self,
        series: pd.Series,
        periods: int,
        alpha: float = 0.3,
    ) -> Dict[str, Any]:
        """Forecast using exponential smoothing."""
        # Calculate exponential moving average
        ema = series.ewm(alpha=alpha, adjust=False).mean()
        last_ema = ema.iloc[-1]

        # Simple exponential smoothing (constant prediction)
        predicted_values = [last_ema] * periods

        # Confidence intervals
        residuals = series - ema
        std = residuals.std()
        confidence_intervals = [
            {"lower": last_ema - 2 * std, "upper": last_ema + 2 * std}
            for _ in range(periods)
        ]

        return {
            "method": "exponential_smoothing",
            "alpha": alpha,
            "predicted_values": [float(v) for v in predicted_values],
            "predicted_mean": float(last_ema),
            "confidence_intervals": [
                {"lower": float(ci["lower"]), "upper": float(ci["upper"])}
                for ci in confidence_intervals
            ],
        }

    def _forecast_linear_trend(
        self,
        series: pd.Series,
        periods: int,
    ) -> Dict[str, Any]:
        """Forecast using linear trend projection."""
        x = np.arange(len(series))
        y = series.values

        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        # Predict future values
        future_x = np.arange(len(series), len(series) + periods)
        predicted_values = slope * future_x + intercept

        # Confidence intervals
        residuals = y - (slope * x + intercept)
        std = np.std(residuals)

        confidence_intervals = []
        for i, pred in enumerate(predicted_values):
            # Wider intervals for further predictions
            interval_width = std * (1 + i * 0.1)
            confidence_intervals.append({
                "lower": pred - 2 * interval_width,
                "upper": pred + 2 * interval_width,
            })

        return {
            "method": "linear_trend",
            "slope": float(slope),
            "intercept": float(intercept),
            "r_squared": float(r_value ** 2),
            "predicted_values": [float(v) for v in predicted_values],
            "predicted_mean": float(np.mean(predicted_values)),
            "confidence_intervals": [
                {"lower": float(ci["lower"]), "upper": float(ci["upper"])}
                for ci in confidence_intervals
            ],
        }

    def forecast_violations(
        self,
        violation_series: pd.Series,
        periods: int = 4,
    ) -> Dict[str, Any]:
        """
        Forecast ACGME violations.

        Args:
            violation_series: Time series of violation counts
            periods: Number of periods to forecast

        Returns:
            Forecast with risk assessment
        """
        forecast = self._forecast_series(violation_series, periods, "linear")

        # Risk assessment
        predicted_mean = forecast["predicted_mean"]
        if predicted_mean > 5:
            risk_level = "high"
        elif predicted_mean > 2:
            risk_level = "medium"
        elif predicted_mean > 0:
            risk_level = "low"
        else:
            risk_level = "minimal"

        forecast["risk_level"] = risk_level
        forecast["metric_type"] = "violations"

        return forecast

    def forecast_utilization(
        self,
        utilization_series: pd.Series,
        periods: int = 4,
    ) -> Dict[str, Any]:
        """
        Forecast utilization with capacity warnings.

        Args:
            utilization_series: Time series of utilization rates
            periods: Number of periods to forecast

        Returns:
            Forecast with capacity warnings
        """
        forecast = self._forecast_series(utilization_series, periods, "auto")

        # Capacity warnings
        warnings = []
        for i, value in enumerate(forecast["predicted_values"]):
            if value > 0.9:
                warnings.append({
                    "period": i + 1,
                    "utilization": float(value),
                    "message": "Critical: Utilization approaching capacity",
                })
            elif value > 0.8:
                warnings.append({
                    "period": i + 1,
                    "utilization": float(value),
                    "message": "Warning: High utilization threshold exceeded",
                })

        forecast["warnings"] = warnings
        forecast["metric_type"] = "utilization"

        return forecast
