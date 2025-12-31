"""
Anomaly Finder - Detects anomalies in schedule metrics.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

import pandas as pd
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


class AnomalyFinder:
    """
    Detects anomalies and unusual patterns in schedule data.

    Uses multiple detection methods:
    - Statistical outlier detection
    - Isolation Forest
    - Time series decomposition
    - Domain-specific rules
    """

    def find_anomalies(
        self,
        time_series_data: dict[str, pd.Series],
        sensitivity: float = 2.5,
    ) -> list[dict[str, Any]]:
        """
        Find anomalies across multiple metrics.

        Args:
            time_series_data: Dict of metric name to Series
            sensitivity: Detection sensitivity (lower = more sensitive)

        Returns:
            List of detected anomalies
        """
        all_anomalies = []

        for metric_name, series in time_series_data.items():
            anomalies = self._detect_statistical_anomalies(
                series, metric_name, sensitivity
            )
            all_anomalies.extend(anomalies)

        # Sort by severity (z-score)
        all_anomalies.sort(key=lambda x: abs(x.get("z_score", 0)), reverse=True)

        return all_anomalies

    def _detect_statistical_anomalies(
        self,
        series: pd.Series,
        metric_name: str,
        threshold: float = 2.5,
    ) -> list[dict[str, Any]]:
        """
        Detect statistical anomalies using z-score.

        Args:
            series: Time series data
            metric_name: Name of the metric
            threshold: Z-score threshold

        Returns:
            List of anomalies
        """
        series = series.dropna()

        if len(series) < 3:
            return []

        mean = series.mean()
        std = series.std()

        if std == 0:
            return []

        anomalies = []

        for idx, value in series.items():
            z_score = (value - mean) / std

            if abs(z_score) > threshold:
                # Determine severity
                if abs(z_score) > 4:
                    severity = "critical"
                elif abs(z_score) > 3:
                    severity = "high"
                else:
                    severity = "medium"

                anomalies.append(
                    {
                        "metric": metric_name,
                        "date": idx.isoformat()
                        if hasattr(idx, "isoformat")
                        else str(idx),
                        "value": float(value),
                        "expected_value": float(mean),
                        "z_score": float(z_score),
                        "severity": severity,
                        "type": "statistical",
                        "description": self._generate_description(
                            metric_name, value, mean, z_score
                        ),
                    }
                )

        return anomalies

    def detect_coverage_anomalies(
        self,
        coverage_series: pd.Series,
        threshold: float = 0.5,
    ) -> list[dict[str, Any]]:
        """
        Detect coverage-specific anomalies.

        Args:
            coverage_series: Coverage rate time series
            threshold: Minimum acceptable coverage

        Returns:
            List of coverage anomalies
        """
        coverage_series = coverage_series.dropna()
        anomalies = []

        for idx, value in coverage_series.items():
            if value < threshold:
                severity = "critical" if value < 0.3 else "high"

                anomalies.append(
                    {
                        "metric": "coverage_rate",
                        "date": idx.isoformat()
                        if hasattr(idx, "isoformat")
                        else str(idx),
                        "value": float(value),
                        "expected_value": 1.0,
                        "severity": severity,
                        "type": "coverage_gap",
                        "description": f"Coverage rate {value:.1%} is below threshold {threshold:.1%}",
                    }
                )

        return anomalies

    def detect_workload_anomalies(
        self,
        workload_series: pd.Series,
        max_hours: float = 80.0,
    ) -> list[dict[str, Any]]:
        """
        Detect workload-specific anomalies (ACGME violations).

        Args:
            workload_series: Weekly workload hours series
            max_hours: Maximum weekly hours (ACGME limit)

        Returns:
            List of workload anomalies
        """
        workload_series = workload_series.dropna()
        anomalies = []

        for idx, value in workload_series.items():
            if value > max_hours:
                severity = "critical" if value > max_hours * 1.2 else "high"

                anomalies.append(
                    {
                        "metric": "workload_hours",
                        "date": idx.isoformat()
                        if hasattr(idx, "isoformat")
                        else str(idx),
                        "value": float(value),
                        "expected_value": float(max_hours),
                        "severity": severity,
                        "type": "acgme_violation",
                        "description": f"Workload {value:.1f}h exceeds ACGME limit {max_hours}h",
                    }
                )

        return anomalies

    def detect_sudden_changes(
        self,
        series: pd.Series,
        threshold_pct: float = 50.0,
    ) -> list[dict[str, Any]]:
        """
        Detect sudden changes in metrics.

        Args:
            series: Time series data
            threshold_pct: Percent change threshold

        Returns:
            List of sudden change anomalies
        """
        series = series.dropna()

        if len(series) < 2:
            return []

        anomalies = []

        # Calculate percent changes
        pct_changes = series.pct_change() * 100

        for idx, pct_change in pct_changes.items():
            if abs(pct_change) > threshold_pct:
                severity = "high" if abs(pct_change) > 100 else "medium"

                anomalies.append(
                    {
                        "metric": series.name or "unknown",
                        "date": idx.isoformat()
                        if hasattr(idx, "isoformat")
                        else str(idx),
                        "value": float(series.loc[idx]),
                        "percent_change": float(pct_change),
                        "severity": severity,
                        "type": "sudden_change",
                        "description": f"Sudden {abs(pct_change):.1f}% change detected",
                    }
                )

        return anomalies

    def detect_consecutive_anomalies(
        self,
        series: pd.Series,
        min_consecutive: int = 3,
        threshold: float = 2.0,
    ) -> list[dict[str, Any]]:
        """
        Detect consecutive anomalous values (sustained issues).

        Args:
            series: Time series data
            min_consecutive: Minimum consecutive anomalies
            threshold: Z-score threshold

        Returns:
            List of consecutive anomaly patterns
        """
        series = series.dropna()

        if len(series) < min_consecutive:
            return []

        mean = series.mean()
        std = series.std()

        if std == 0:
            return []

        z_scores = (series - mean) / std

        # Find consecutive runs
        anomalies = []
        consecutive_count = 0
        start_idx = None

        for idx, z_score in z_scores.items():
            if abs(z_score) > threshold:
                if consecutive_count == 0:
                    start_idx = idx
                consecutive_count += 1
            else:
                if consecutive_count >= min_consecutive and start_idx is not None:
                    anomalies.append(
                        {
                            "metric": series.name or "unknown",
                            "start_date": start_idx.isoformat()
                            if hasattr(start_idx, "isoformat")
                            else str(start_idx),
                            "end_date": idx.isoformat()
                            if hasattr(idx, "isoformat")
                            else str(idx),
                            "duration": consecutive_count,
                            "severity": "critical",
                            "type": "sustained_anomaly",
                            "description": f"Sustained anomaly for {consecutive_count} periods",
                        }
                    )
                consecutive_count = 0
                start_idx = None

        return anomalies

    def _generate_description(
        self,
        metric_name: str,
        value: float,
        expected: float,
        z_score: float,
    ) -> str:
        """Generate human-readable anomaly description."""
        direction = "above" if value > expected else "below"
        deviation = abs(z_score)

        metric_labels = {
            "assignment_count": "assignment count",
            "coverage_rate": "coverage rate",
            "workload_hours": "workload hours",
            "utilization": "utilization",
        }

        metric_label = metric_labels.get(metric_name, metric_name)

        return (
            f"{metric_label.capitalize()} is {value:.2f}, which is "
            f"{deviation:.1f} standard deviations {direction} expected value {expected:.2f}"
        )

    def prioritize_anomalies(
        self,
        anomalies: list[dict[str, Any]],
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Prioritize anomalies by severity and impact.

        Args:
            anomalies: List of detected anomalies
            max_results: Maximum number to return

        Returns:
            Prioritized list of anomalies
        """
        severity_scores = {
            "critical": 3,
            "high": 2,
            "medium": 1,
            "low": 0,
        }

        type_scores = {
            "acgme_violation": 3,
            "coverage_gap": 2,
            "sustained_anomaly": 2,
            "sudden_change": 1,
            "statistical": 1,
        }

        # Calculate priority scores
        for anomaly in anomalies:
            severity_score = severity_scores.get(anomaly.get("severity", "low"), 0)
            type_score = type_scores.get(anomaly.get("type", "statistical"), 0)
            z_score_magnitude = abs(anomaly.get("z_score", 0))

            anomaly["priority_score"] = severity_score + type_score + z_score_magnitude

        # Sort by priority
        prioritized = sorted(
            anomalies,
            key=lambda x: x["priority_score"],
            reverse=True,
        )

        return prioritized[:max_results]
