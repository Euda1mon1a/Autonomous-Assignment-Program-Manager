"""
Trend Detector - Detects trends and patterns in time series data.
"""

from typing import Any, Dict, List, Optional
import logging

import pandas as pd
import numpy as np
from scipy import stats

from app.analytics.constants import (
    MIN_OBSERVATIONS_FOR_TREND,
    MIN_OBSERVATIONS_FOR_CHANGE_POINT,
    MIN_OBSERVATIONS_FOR_VOLATILITY,
    STABLE_TREND_SLOPE_THRESHOLD,
    HIGH_CONFIDENCE_P_VALUE,
    HIGH_CONFIDENCE_R_SQUARED,
    MEDIUM_CONFIDENCE_P_VALUE,
    MEDIUM_CONFIDENCE_R_SQUARED,
    DEFAULT_CHANGE_POINT_Z_THRESHOLD,
    DEFAULT_MAX_CYCLE_PERIOD,
    CYCLE_STRENGTH_THRESHOLD,
    DEFAULT_VOLATILITY_WINDOW,
    DEFAULT_ZSCORE_THRESHOLD,
    DEFAULT_IQR_MULTIPLIER,
    FIRST_QUARTILE,
    THIRD_QUARTILE,
)

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
        time_series_data: dict[str, pd.Series],
        min_observations: int = MIN_OBSERVATIONS_FOR_TREND,
    ) -> dict[str, dict[str, Any]]:
        """
        Detect trends in multiple time series.

        Analyzes each time series to identify directional trends (increasing,
        decreasing, stable) using linear regression with statistical significance
        testing.

        Args:
            time_series_data: Dict mapping metric name to pandas Series
                containing time series data
            min_observations: Minimum number of data points required for
                trend analysis (default: 4)

        Returns:
            dict[str, dict[str, Any]]: Dictionary mapping metric names to
                trend analysis results containing:
                - direction: "increasing" | "decreasing" | "stable" | "insufficient_data"
                - confidence: "high" | "medium" | "low"
                - slope: Trend slope value
                - r_squared: R² goodness of fit
                - p_value: Statistical significance
                - percent_change: Overall percentage change

        Note:
            Trends with fewer than min_observations data points are marked
            as "insufficient_data".
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

    def _analyze_trend(self, series: pd.Series) -> dict[str, Any]:
        """
        Analyze trend for a single time series.

        Performs linear regression on the time series and computes trend
        direction, statistical significance, and magnitude metrics.

        Args:
            series: pandas Series containing time series data

        Returns:
            dict[str, Any]: Analysis containing:
                - direction: Trend direction classification
                - confidence: Statistical confidence level
                - slope: Linear regression slope
                - r_squared: Coefficient of determination
                - p_value: Statistical p-value
                - percent_change: Percentage change from first to last
                - first_value: Initial value
                - last_value: Final value

        Note:
            Direction is "stable" if |slope| < 0.01. Confidence is "high"
            if p < 0.01 and R² > 0.7, "medium" if p < 0.05 and R² > 0.5.
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
        if abs(slope) < STABLE_TREND_SLOPE_THRESHOLD:
            direction = "stable"
        elif slope > 0:
            direction = "increasing"
        else:
            direction = "decreasing"

        # Determine confidence based on p-value and R²
        if p_value < HIGH_CONFIDENCE_P_VALUE and r_value**2 > HIGH_CONFIDENCE_R_SQUARED:
            confidence = "high"
        elif (
            p_value < MEDIUM_CONFIDENCE_P_VALUE
            and r_value**2 > MEDIUM_CONFIDENCE_R_SQUARED
        ):
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
            "r_squared": float(r_value**2),
            "p_value": float(p_value),
            "percent_change": float(percent_change),
            "first_value": float(series.iloc[0]),
            "last_value": float(series.iloc[-1]),
        }

    def detect_change_points(
        self,
        series: pd.Series,
        threshold: float = DEFAULT_CHANGE_POINT_Z_THRESHOLD,
    ) -> list[dict[str, Any]]:
        """
        Detect significant change points in time series.

        Identifies points where the time series exhibits sudden changes
        that exceed a statistical threshold based on z-scores of first
        differences.

        Args:
            series: pandas Series containing time series data
            threshold: Z-score threshold for change point detection
                (default: 2.0 for ~95% confidence)

        Returns:
            list[dict[str, Any]]: List of detected change points, each containing:
                - date: Timestamp of the change point
                - z_score: Z-score of the change magnitude
                - value_change: Absolute change in value
                - value_before: Value immediately before change
                - value_after: Value immediately after change

        Note:
            Returns empty list if series has fewer than 3 points or if
            standard deviation is zero (constant series).
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
                change_points.append(
                    {
                        "date": idx.isoformat()
                        if hasattr(idx, "isoformat")
                        else str(idx),
                        "z_score": float(z_score),
                        "value_change": float(diffs.loc[idx]),
                        "value_before": float(series.loc[idx] - diffs.loc[idx]),
                        "value_after": float(series.loc[idx]),
                    }
                )

        return change_points

    def detect_cycles(
        self,
        series: pd.Series,
        max_period: int = DEFAULT_MAX_CYCLE_PERIOD,
    ) -> dict[str, Any]:
        """
        Detect cyclic patterns in time series.

        Uses autocorrelation analysis to identify periodic patterns in the
        data, useful for detecting weekly, monthly, or other regular cycles.

        Args:
            series: pandas Series containing time series data
            max_period: Maximum cycle period to test in time units
                (default: 30)

        Returns:
            dict[str, Any]: Cycle detection results containing:
                - has_cycle: Boolean indicating if significant cycle detected
                - period: Cycle period in time units (None if no cycle)
                - strength: Autocorrelation strength (0 to 1)
                - autocorrelation: Raw autocorrelation coefficient

        Note:
            A cycle is considered significant if autocorrelation strength
            exceeds 0.3. Requires at least max_period data points.
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
            except (ValueError, TypeError, ZeroDivisionError) as e:
                logger.debug(f"Failed to calculate autocorrelation for lag {lag}: {e}")
                continue

        if not autocorrs:
            return {
                "has_cycle": False,
                "period": None,
                "strength": 0,
            }

        # Find strongest autocorrelation
        best_lag, best_corr = max(autocorrs, key=lambda x: abs(x[1]))

        has_cycle = abs(best_corr) > CYCLE_STRENGTH_THRESHOLD

        return {
            "has_cycle": has_cycle,
            "period": int(best_lag) if has_cycle else None,
            "strength": float(abs(best_corr)),
            "autocorrelation": float(best_corr),
        }

    def calculate_volatility(
        self,
        series: pd.Series,
        window: int = DEFAULT_VOLATILITY_WINDOW,
    ) -> dict[str, float]:
        """
        Calculate volatility metrics.

        Computes multiple measures of time series variability to assess
        how much the metric fluctuates over time.

        Args:
            series: pandas Series containing time series data
            window: Rolling window size for rolling statistics (default: 7)

        Returns:
            dict[str, float]: Volatility metrics containing:
                - std: Standard deviation of entire series
                - coefficient_of_variation: Std dev / mean (normalized volatility)
                - range: Maximum value - minimum value
                - avg_rolling_std: Mean of rolling window standard deviations

        Note:
            Returns zeros if series has fewer than 2 points. Coefficient
            of variation is 0 if mean is zero.
        """
        series = series.dropna()

        if len(series) < MIN_OBSERVATIONS_FOR_VOLATILITY:
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
        threshold: float = DEFAULT_ZSCORE_THRESHOLD,
    ) -> list[dict[str, Any]]:
        """
        Detect outliers in time series.

        Identifies anomalous values that deviate significantly from the
        typical distribution using either z-score or IQR methods.

        Args:
            series: pandas Series containing time series data
            method: Detection method - "zscore" (default) or "iqr"
            threshold: Threshold for outlier detection:
                - For "zscore": Number of standard deviations (default: 3.0)
                - For "iqr": IQR multiplier (default: 3.0)

        Returns:
            list[dict[str, Any]]: List of detected outliers, each containing:
                For "zscore" method:
                    - date: Timestamp of outlier
                    - value: Outlier value
                    - z_score: Z-score of the value
                    - method: "zscore"
                For "iqr" method:
                    - date: Timestamp of outlier
                    - value: Outlier value
                    - lower_bound: IQR lower bound
                    - upper_bound: IQR upper bound
                    - method: "iqr"

        Note:
            Returns empty list if series has fewer than 3 points or if
            standard deviation is zero (for zscore method).

        Example:
            >>> outliers = detector.detect_outliers(data, method="zscore", threshold=2.5)
            >>> for outlier in outliers:
            ...     print(f"Outlier at {outlier['date']}: {outlier['value']}")
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
                    outliers.append(
                        {
                            "date": idx.isoformat()
                            if hasattr(idx, "isoformat")
                            else str(idx),
                            "value": float(series.loc[idx]),
                            "z_score": float(z_score),
                            "method": "zscore",
                        }
                    )

        elif method == "iqr":
            q1 = series.quantile(FIRST_QUARTILE)
            q3 = series.quantile(THIRD_QUARTILE)
            iqr = q3 - q1

            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr

            for idx, value in series.items():
                if value < lower_bound or value > upper_bound:
                    outliers.append(
                        {
                            "date": idx.isoformat()
                            if hasattr(idx, "isoformat")
                            else str(idx),
                            "value": float(value),
                            "lower_bound": float(lower_bound),
                            "upper_bound": float(upper_bound),
                            "method": "iqr",
                        }
                    )

        return outliers
