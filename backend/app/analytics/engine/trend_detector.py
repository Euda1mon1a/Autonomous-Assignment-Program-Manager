"""
Trend Detector - Detects trends and patterns in time series data.
"""

from typing import Any, Dict, List, Optional
import logging

import pandas as pd
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


class TrendDetector:
    """
    Detects trends and patterns in schedule metrics.

    Provides:
    - Trend direction detection
    - Slope calculation
    - Statistical significance testing
    - Pattern recognition
    """

    def detect_trends(
        self,
        time_series_data: Dict[str, pd.Series],
        min_observations: int = 4,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Detect trends in multiple time series.

        Args:
            time_series_data: Dict of metric name to Series
            min_observations: Minimum observations needed

        Returns:
            Dict of metric name to trend analysis
        """
        trends = {}

        for metric_name, series in time_series_data.items():
            if len(series) >= min_observations:
                trends[metric_name] = self._analyze_trend(series)
            else:
                trends[metric_name] = {
                    "direction": "insufficient_data",
                    "confidence": "low",
                    "slope": 0,
                }

        return trends

    def _analyze_trend(self, series: pd.Series) -> Dict[str, Any]:
        """
        Analyze trend for a single time series.

        Args:
            series: Time series data

        Returns:
            Dict with trend analysis
        """
        # Remove NaN values
        series = series.dropna()

        if len(series) < 2:
            return {
                "direction": "insufficient_data",
                "confidence": "low",
                "slope": 0,
            }

        # Linear regression
        x = np.arange(len(series))
        y = series.values

        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        # Determine trend direction
        if abs(slope) < 0.01:
            direction = "stable"
        elif slope > 0:
            direction = "increasing"
        else:
            direction = "decreasing"

        # Determine confidence based on p-value and R²
        if p_value < 0.01 and r_value ** 2 > 0.7:
            confidence = "high"
        elif p_value < 0.05 and r_value ** 2 > 0.5:
            confidence = "medium"
        else:
            confidence = "low"

        # Calculate percent change
        if len(series) >= 2:
            first_value = series.iloc[0]
            last_value = series.iloc[-1]
            if first_value != 0:
                percent_change = ((last_value - first_value) / first_value) * 100
            else:
                percent_change = 0
        else:
            percent_change = 0

        return {
            "direction": direction,
            "confidence": confidence,
            "slope": float(slope),
            "r_squared": float(r_value ** 2),
            "p_value": float(p_value),
            "percent_change": float(percent_change),
            "first_value": float(series.iloc[0]),
            "last_value": float(series.iloc[-1]),
        }

    def detect_change_points(
        self,
        series: pd.Series,
        threshold: float = 2.0,
    ) -> List[Dict[str, Any]]:
        """
        Detect significant change points in time series.

        Args:
            series: Time series data
            threshold: Z-score threshold for detection

        Returns:
            List of change points with dates and magnitudes
        """
        series = series.dropna()

        if len(series) < 3:
            return []

        # Calculate differences
        diffs = series.diff().dropna()

        # Calculate z-scores
        mean_diff = diffs.mean()
        std_diff = diffs.std()

        if std_diff == 0:
            return []

        z_scores = (diffs - mean_diff) / std_diff

        # Find points exceeding threshold
        change_points = []
        for idx, z_score in z_scores.items():
            if abs(z_score) > threshold:
                change_points.append({
                    "date": idx.isoformat() if hasattr(idx, "isoformat") else str(idx),
                    "z_score": float(z_score),
                    "value_change": float(diffs.loc[idx]),
                    "value_before": float(series.loc[idx] - diffs.loc[idx]),
                    "value_after": float(series.loc[idx]),
                })

        return change_points

    def detect_cycles(
        self,
        series: pd.Series,
        max_period: int = 30,
    ) -> Dict[str, Any]:
        """
        Detect cyclic patterns in time series.

        Args:
            series: Time series data
            max_period: Maximum cycle period to check

        Returns:
            Dict with cycle detection results
        """
        series = series.dropna()

        if len(series) < max_period:
            return {
                "has_cycle": False,
                "period": None,
                "strength": 0,
            }

        # Calculate autocorrelation for different lags
        autocorrs = []
        for lag in range(1, min(max_period, len(series) // 2)):
            try:
                autocorr = series.autocorr(lag=lag)
                if not np.isnan(autocorr):
                    autocorrs.append((lag, autocorr))
            except:
                pass

        if not autocorrs:
            return {
                "has_cycle": False,
                "period": None,
                "strength": 0,
            }

        # Find strongest autocorrelation
        best_lag, best_corr = max(autocorrs, key=lambda x: abs(x[1]))

        has_cycle = abs(best_corr) > 0.3

        return {
            "has_cycle": has_cycle,
            "period": int(best_lag) if has_cycle else None,
            "strength": float(abs(best_corr)),
            "autocorrelation": float(best_corr),
        }

    def calculate_volatility(
        self,
        series: pd.Series,
        window: int = 7,
    ) -> Dict[str, float]:
        """
        Calculate volatility metrics.

        Args:
            series: Time series data
            window: Rolling window size

        Returns:
            Dict with volatility metrics
        """
        series = series.dropna()

        if len(series) < 2:
            return {
                "std": 0,
                "coefficient_of_variation": 0,
                "range": 0,
            }

        std = series.std()
        mean = series.mean()

        coefficient_of_variation = (std / mean) if mean != 0 else 0
        value_range = series.max() - series.min()

        # Rolling volatility
        if len(series) >= window:
            rolling_std = series.rolling(window=window).std()
            avg_rolling_std = rolling_std.mean()
        else:
            avg_rolling_std = std

        return {
            "std": float(std),
            "coefficient_of_variation": float(coefficient_of_variation),
            "range": float(value_range),
            "avg_rolling_std": float(avg_rolling_std),
        }

    def detect_outliers(
        self,
        series: pd.Series,
        method: str = "zscore",
        threshold: float = 3.0,
    ) -> List[Dict[str, Any]]:
        """
        Detect outliers in time series.

        Args:
            series: Time series data
            method: Detection method (zscore, iqr)
            threshold: Threshold for outlier detection

        Returns:
            List of outliers with dates and values
        """
        series = series.dropna()

        if len(series) < 3:
            return []

        outliers = []

        if method == "zscore":
            mean = series.mean()
            std = series.std()

            if std == 0:
                return []

            z_scores = (series - mean) / std

            for idx, z_score in z_scores.items():
                if abs(z_score) > threshold:
                    outliers.append({
                        "date": idx.isoformat() if hasattr(idx, "isoformat") else str(idx),
                        "value": float(series.loc[idx]),
                        "z_score": float(z_score),
                        "method": "zscore",
                    })

        elif method == "iqr":
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1

            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr

            for idx, value in series.items():
                if value < lower_bound or value > upper_bound:
                    outliers.append({
                        "date": idx.isoformat() if hasattr(idx, "isoformat") else str(idx),
                        "value": float(value),
                        "lower_bound": float(lower_bound),
                        "upper_bound": float(upper_bound),
                        "method": "iqr",
                    })

        return outliers
