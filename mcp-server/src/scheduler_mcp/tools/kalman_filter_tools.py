"""
Kalman Filter Tools for Workload Trend Analysis.

This module provides Kalman filtering for noisy workload measurements,
enabling extraction of true underlying workload trends and anomaly detection.

Kalman Filter Concept:
---------------------
A Kalman filter is an optimal recursive algorithm for estimating the true
state of a system from noisy measurements. It maintains:
- State estimate (x): Our best guess of the true workload
- Error covariance (P): Uncertainty in our estimate

The filter operates in two phases:
1. PREDICT: Project current state forward in time
   - Assumes state evolves with some process noise (Q)
2. UPDATE: Incorporate new measurement
   - Balances prediction vs measurement based on uncertainties
   - Measurement noise (R) indicates sensor reliability

For workload filtering:
- State (x): True underlying workload level
- Observation (z): Measured workload (may be noisy due to sampling, variability)
- Process noise (Q): Natural workload variation over time
- Measurement noise (R): Uncertainty in workload measurements

The filter produces cleaner signals than raw measurements, enabling better
trend detection and anomaly identification.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


# =============================================================================
# Request/Response Models
# =============================================================================


class WorkloadTrendRequest(BaseModel):
    """Request to analyze workload trend using Kalman filter."""

    workload_history: list[float] = Field(
        ...,
        min_length=2,
        description="Historical workload measurements (e.g., hours per week)",
    )
    process_noise: float = Field(
        default=0.1,
        ge=0.001,
        le=10.0,
        description="Process noise (Q) - natural workload variation. "
        "Higher values make filter more responsive to changes. "
        "Typical: 0.1-1.0",
    )
    measurement_noise: float = Field(
        default=1.0,
        ge=0.001,
        le=100.0,
        description="Measurement noise (R) - uncertainty in observations. "
        "Higher values trust measurements less. "
        "Typical: 0.5-5.0",
    )
    initial_estimate: float | None = Field(
        default=None,
        description="Initial state estimate. If None, uses first measurement.",
    )
    initial_error: float = Field(
        default=1.0,
        ge=0.001,
        description="Initial error covariance. Higher = more uncertainty. "
        "Typical: 1.0",
    )
    prediction_steps: int = Field(
        default=0,
        ge=0,
        le=10,
        description="Number of future steps to predict. 0 = filter only.",
    )

    @field_validator("workload_history")
    @classmethod
    def validate_workload_values(cls, v: list[float]) -> list[float]:
        """Validate workload values are reasonable."""
        if any(w < 0 for w in v):
            raise ValueError("Workload values must be non-negative")
        if any(w > 168 for w in v):  # 168 hours = 1 week
            logger.warning("Workload values exceed 168 hours/week")
        return v


class WorkloadTrendResponse(BaseModel):
    """Response from workload trend analysis."""

    filtered_workload: list[float] = Field(
        description="Kalman-filtered workload estimates (same length as input)"
    )
    confidence_intervals: list[dict[str, float]] = Field(
        description="Confidence intervals for each estimate. "
        "Each entry has 'lower', 'upper', 'std_dev' keys."
    )
    predictions: list[float] = Field(
        default_factory=list,
        description="Future workload predictions (if requested)",
    )
    prediction_confidence: list[dict[str, float]] = Field(
        default_factory=list,
        description="Confidence intervals for predictions",
    )
    kalman_gain_history: list[float] = Field(
        description="Kalman gain at each step (0=trust prediction, 1=trust measurement)"
    )
    trend_assessment: str = Field(
        description="Overall trend: INCREASING, STABLE, DECREASING, or VOLATILE"
    )
    smoothness_score: float = Field(
        ge=0.0,
        le=1.0,
        description="How smooth the filtered signal is (1=very smooth, 0=noisy)",
    )
    parameters: dict[str, float] = Field(
        description="Filter parameters used (Q, R, initial values)"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional statistics and diagnostics",
    )


class WorkloadAnomalyRequest(BaseModel):
    """Request to detect workload anomalies using Kalman filter."""

    workload_history: list[float] = Field(
        ...,
        min_length=3,
        description="Historical workload measurements",
    )
    process_noise: float = Field(
        default=0.1,
        ge=0.001,
        le=10.0,
        description="Process noise (Q)",
    )
    measurement_noise: float = Field(
        default=1.0,
        ge=0.001,
        le=100.0,
        description="Measurement noise (R)",
    )
    anomaly_threshold_sigma: float = Field(
        default=2.0,
        ge=1.0,
        le=5.0,
        description="Anomaly threshold in standard deviations. "
        "2.0 = moderate (95% confidence), "
        "3.0 = strict (99.7% confidence)",
    )

    @field_validator("workload_history")
    @classmethod
    def validate_workload_values(cls, v: list[float]) -> list[float]:
        """Validate workload values are reasonable."""
        if any(w < 0 for w in v):
            raise ValueError("Workload values must be non-negative")
        return v


class AnomalyPoint(BaseModel):
    """A detected anomaly point."""

    index: int = Field(description="Index in the workload history")
    measured_value: float = Field(description="Raw measured workload")
    filtered_value: float = Field(description="Kalman filter estimate")
    residual: float = Field(description="Difference (measured - filtered)")
    residual_sigma: float = Field(
        description="Residual in standard deviations from expected"
    )
    severity: str = Field(
        description="Anomaly severity: MODERATE, HIGH, or CRITICAL"
    )


class WorkloadAnomalyResponse(BaseModel):
    """Response from workload anomaly detection."""

    anomalies: list[AnomalyPoint] = Field(
        description="Detected anomalies sorted by severity"
    )
    total_anomalies: int = Field(description="Total number of anomalies detected")
    anomaly_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Proportion of measurements that are anomalous",
    )
    filtered_workload: list[float] = Field(
        description="Kalman-filtered baseline for comparison"
    )
    residuals: list[float] = Field(
        description="Residuals (measured - filtered) for all points"
    )
    residual_std: float = Field(
        ge=0.0,
        description="Standard deviation of residuals",
    )
    overall_assessment: str = Field(
        description="Overall assessment: STABLE, CONCERNING, or CRITICAL"
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommended actions based on anomalies",
    )
    parameters: dict[str, float] = Field(
        description="Filter parameters used"
    )


# =============================================================================
# Kalman Filter Implementation
# =============================================================================


class KalmanFilter1D:
    """
    Simple 1D Kalman filter for scalar time series.

    This implements a basic Kalman filter for tracking a single variable
    (workload) that evolves over time with some process noise and is
    observed with measurement noise.

    State equation: x(k) = x(k-1) + w(k)  where w ~ N(0, Q)
    Observation: z(k) = x(k) + v(k)       where v ~ N(0, R)

    Attributes:
        x: Current state estimate
        P: Current error covariance
        Q: Process noise covariance
        R: Measurement noise covariance
    """

    def __init__(
        self,
        initial_state: float,
        initial_error: float,
        process_noise: float,
        measurement_noise: float,
    ):
        """
        Initialize Kalman filter.

        Args:
            initial_state: Initial state estimate (x0)
            initial_error: Initial error covariance (P0)
            process_noise: Process noise covariance (Q)
            measurement_noise: Measurement noise covariance (R)
        """
        self.x = initial_state  # State estimate
        self.P = initial_error  # Error covariance
        self.Q = process_noise  # Process noise
        self.R = measurement_noise  # Measurement noise

        # History tracking
        self.estimates: list[float] = []
        self.error_covariances: list[float] = []
        self.kalman_gains: list[float] = []
        self.innovations: list[float] = []

    def predict(self) -> tuple[float, float]:
        """
        Prediction step: Project state forward.

        For this simple model, state doesn't change (random walk),
        but uncertainty increases due to process noise.

        Returns:
            Tuple of (predicted_state, predicted_error)
        """
        # State prediction (no change in expectation)
        x_pred = self.x

        # Error covariance prediction (uncertainty increases)
        P_pred = self.P + self.Q

        return x_pred, P_pred

    def update(self, measurement: float) -> tuple[float, float, float]:
        """
        Update step: Incorporate measurement.

        Computes optimal Kalman gain and updates state estimate
        and error covariance.

        Args:
            measurement: Observed measurement (z)

        Returns:
            Tuple of (updated_state, updated_error, kalman_gain)
        """
        # Predict
        x_pred, P_pred = self.predict()

        # Compute Kalman gain
        # K = P_pred / (P_pred + R)
        # K close to 0: trust prediction
        # K close to 1: trust measurement
        K = P_pred / (P_pred + self.R)

        # Innovation (residual)
        innovation = measurement - x_pred

        # Update state estimate
        self.x = x_pred + K * innovation

        # Update error covariance
        self.P = (1 - K) * P_pred

        # Store history
        self.estimates.append(self.x)
        self.error_covariances.append(self.P)
        self.kalman_gains.append(K)
        self.innovations.append(innovation)

        return self.x, self.P, K

    def filter_series(self, measurements: list[float]) -> dict[str, Any]:
        """
        Filter entire time series.

        Args:
            measurements: List of measurements to filter

        Returns:
            Dictionary with filtered results and diagnostics
        """
        filtered = []
        errors = []
        gains = []
        innovations = []

        for z in measurements:
            x, P, K = self.update(z)
            filtered.append(x)
            errors.append(P)
            gains.append(K)
            innovations.append(z - x)

        return {
            "filtered": filtered,
            "errors": errors,
            "gains": gains,
            "innovations": innovations,
        }

    def predict_future(self, n_steps: int) -> dict[str, Any]:
        """
        Predict future values.

        For random walk model, prediction is constant but
        uncertainty grows linearly with time.

        Args:
            n_steps: Number of steps to predict

        Returns:
            Dictionary with predictions and uncertainties
        """
        predictions = []
        uncertainties = []

        # Start from current state
        x_pred = self.x
        P_pred = self.P

        for _ in range(n_steps):
            # State stays constant (random walk expectation)
            predictions.append(x_pred)

            # Uncertainty increases
            P_pred = P_pred + self.Q
            uncertainties.append(P_pred)

        return {
            "predictions": predictions,
            "uncertainties": uncertainties,
        }


# =============================================================================
# Analysis Functions
# =============================================================================


def assess_trend(filtered_values: list[float]) -> str:
    """
    Assess overall trend in filtered data.

    Args:
        filtered_values: Kalman-filtered workload values

    Returns:
        Trend assessment string
    """
    if len(filtered_values) < 3:
        return "INSUFFICIENT_DATA"

    # Compute linear trend
    x = np.arange(len(filtered_values))
    y = np.array(filtered_values)

    # Simple linear regression
    slope = np.polyfit(x, y, 1)[0]

    # Compute coefficient of variation (volatility)
    mean = np.mean(y)
    std = np.std(y)
    cv = std / mean if mean > 0 else 0

    # Classify trend
    if cv > 0.3:  # High volatility
        return "VOLATILE"
    elif abs(slope) < 0.1:  # Flat
        return "STABLE"
    elif slope > 0.1:
        return "INCREASING"
    else:
        return "DECREASING"


def compute_smoothness(
    raw_values: list[float], filtered_values: list[float]
) -> float:
    """
    Compute smoothness score.

    Measures how much smoother the filtered signal is compared to raw.
    Higher score = filter is effectively smoothing.

    Args:
        raw_values: Raw measurements
        filtered_values: Filtered values

    Returns:
        Smoothness score in [0, 1]
    """
    if len(raw_values) < 2:
        return 0.0

    # Compute differences (proxy for signal roughness)
    raw_diffs = np.abs(np.diff(raw_values))
    filtered_diffs = np.abs(np.diff(filtered_values))

    raw_roughness = np.mean(raw_diffs)
    filtered_roughness = np.mean(filtered_diffs)

    if raw_roughness == 0:
        return 1.0

    # Smoothness = reduction in roughness
    smoothness = 1.0 - (filtered_roughness / raw_roughness)
    return max(0.0, min(1.0, smoothness))


# =============================================================================
# MCP Tool Functions
# =============================================================================


async def analyze_workload_trend(
    request: WorkloadTrendRequest,
) -> WorkloadTrendResponse:
    """
    Apply Kalman filter to workload history to extract underlying trend.

    This tool filters noisy workload measurements to reveal the true
    underlying workload pattern. It's useful for:
    - Identifying long-term workload trends
    - Smoothing out measurement noise and short-term fluctuations
    - Predicting future workload levels
    - Providing confidence intervals for workload estimates

    Args:
        request: Workload trend analysis request

    Returns:
        WorkloadTrendResponse with filtered trend and predictions

    Example:
        >>> request = WorkloadTrendRequest(
        ...     workload_history=[60, 65, 62, 70, 68, 75, 72],
        ...     process_noise=0.5,
        ...     measurement_noise=2.0,
        ...     prediction_steps=3
        ... )
        >>> response = await analyze_workload_trend(request)
        >>> print(response.trend_assessment)
        INCREASING
    """
    logger.info(
        "Analyzing workload trend with Kalman filter",
        extra={
            "data_points": len(request.workload_history),
            "Q": request.process_noise,
            "R": request.measurement_noise,
        },
    )

    # Initialize Kalman filter
    initial_state = (
        request.initial_estimate
        if request.initial_estimate is not None
        else request.workload_history[0]
    )

    kf = KalmanFilter1D(
        initial_state=initial_state,
        initial_error=request.initial_error,
        process_noise=request.process_noise,
        measurement_noise=request.measurement_noise,
    )

    # Filter the series
    result = kf.filter_series(request.workload_history)

    # Compute confidence intervals (±2 sigma)
    confidence_intervals = []
    for i, (x_est, P) in enumerate(zip(result["filtered"], result["errors"])):
        std_dev = np.sqrt(P)
        confidence_intervals.append({
            "lower": x_est - 2 * std_dev,
            "upper": x_est + 2 * std_dev,
            "std_dev": std_dev,
        })

    # Predict future if requested
    predictions = []
    prediction_confidence = []
    if request.prediction_steps > 0:
        future = kf.predict_future(request.prediction_steps)
        predictions = future["predictions"]

        for P in future["uncertainties"]:
            std_dev = np.sqrt(P)
            prediction_confidence.append({
                "lower": predictions[len(prediction_confidence)] - 2 * std_dev,
                "upper": predictions[len(prediction_confidence)] + 2 * std_dev,
                "std_dev": std_dev,
            })

    # Assess trend
    trend = assess_trend(result["filtered"])

    # Compute smoothness
    smoothness = compute_smoothness(request.workload_history, result["filtered"])

    # Build response
    return WorkloadTrendResponse(
        filtered_workload=result["filtered"],
        confidence_intervals=confidence_intervals,
        predictions=predictions,
        prediction_confidence=prediction_confidence,
        kalman_gain_history=result["gains"],
        trend_assessment=trend,
        smoothness_score=smoothness,
        parameters={
            "process_noise_Q": request.process_noise,
            "measurement_noise_R": request.measurement_noise,
            "initial_state": initial_state,
            "initial_error": request.initial_error,
        },
        metadata={
            "data_points": len(request.workload_history),
            "mean_kalman_gain": float(np.mean(result["gains"])),
            "final_error_covariance": result["errors"][-1],
            "mean_workload": float(np.mean(result["filtered"])),
            "std_workload": float(np.std(result["filtered"])),
        },
    )


async def detect_workload_anomalies(
    request: WorkloadAnomalyRequest,
) -> WorkloadAnomalyResponse:
    """
    Detect workload anomalies by comparing raw measurements to Kalman filter.

    This tool identifies outliers and anomalous workload measurements by:
    1. Filtering workload history with Kalman filter to get baseline
    2. Computing residuals (measured - filtered)
    3. Flagging points where residuals exceed threshold

    Large residuals indicate:
    - Unexpected workload spikes
    - Data quality issues
    - Special events or circumstances

    Args:
        request: Workload anomaly detection request

    Returns:
        WorkloadAnomalyResponse with detected anomalies

    Example:
        >>> request = WorkloadAnomalyRequest(
        ...     workload_history=[60, 62, 65, 95, 63, 64, 67],  # Spike at index 3
        ...     anomaly_threshold_sigma=2.0
        ... )
        >>> response = await detect_workload_anomalies(request)
        >>> print(len(response.anomalies))
        1
    """
    logger.info(
        "Detecting workload anomalies",
        extra={
            "data_points": len(request.workload_history),
            "threshold_sigma": request.anomaly_threshold_sigma,
        },
    )

    # Initialize and run Kalman filter
    kf = KalmanFilter1D(
        initial_state=request.workload_history[0],
        initial_error=1.0,
        process_noise=request.process_noise,
        measurement_noise=request.measurement_noise,
    )

    result = kf.filter_series(request.workload_history)

    # Compute residuals
    residuals = np.array(request.workload_history) - np.array(result["filtered"])
    residual_std = float(np.std(residuals))

    # Detect anomalies
    anomalies = []
    for i, (measured, filtered, residual) in enumerate(
        zip(request.workload_history, result["filtered"], residuals)
    ):
        # Compute residual in standard deviations
        if residual_std > 0:
            residual_sigma = abs(residual) / residual_std
        else:
            residual_sigma = 0.0

        # Check if exceeds threshold
        if residual_sigma >= request.anomaly_threshold_sigma:
            # Classify severity
            if residual_sigma >= 4.0:
                severity = "CRITICAL"
            elif residual_sigma >= 3.0:
                severity = "HIGH"
            else:
                severity = "MODERATE"

            anomalies.append(
                AnomalyPoint(
                    index=i,
                    measured_value=measured,
                    filtered_value=filtered,
                    residual=float(residual),
                    residual_sigma=residual_sigma,
                    severity=severity,
                )
            )

    # Sort by severity (CRITICAL > HIGH > MODERATE) then by residual_sigma
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2}
    anomalies.sort(key=lambda a: (severity_order[a.severity], -a.residual_sigma))

    # Compute anomaly rate
    anomaly_rate = len(anomalies) / len(request.workload_history)

    # Overall assessment
    if len(anomalies) == 0:
        overall = "STABLE"
    elif any(a.severity == "CRITICAL" for a in anomalies) or anomaly_rate > 0.3:
        overall = "CRITICAL"
    elif any(a.severity == "HIGH" for a in anomalies) or anomaly_rate > 0.15:
        overall = "CONCERNING"
    else:
        overall = "STABLE"

    # Generate recommendations
    recommendations = []
    if len(anomalies) > 0:
        recommendations.append(
            f"Found {len(anomalies)} anomalous workload measurement(s)"
        )

        critical_count = sum(1 for a in anomalies if a.severity == "CRITICAL")
        if critical_count > 0:
            recommendations.append(
                f"CRITICAL: {critical_count} severe outlier(s) detected - "
                "investigate data quality or special circumstances"
            )

        if anomaly_rate > 0.3:
            recommendations.append(
                "High anomaly rate (>30%) suggests systematic issue or "
                "inappropriate filter parameters"
            )

        # Suggest parameter adjustment if needed
        mean_gain = float(np.mean(result["gains"]))
        if mean_gain > 0.8:
            recommendations.append(
                "Kalman gain is high (trusting measurements heavily) - "
                "consider increasing measurement_noise if data is unreliable"
            )
        elif mean_gain < 0.2:
            recommendations.append(
                "Kalman gain is low (trusting predictions heavily) - "
                "consider increasing process_noise if workload is volatile"
            )
    else:
        recommendations.append("No anomalies detected - workload tracking is stable")

    return WorkloadAnomalyResponse(
        anomalies=anomalies,
        total_anomalies=len(anomalies),
        anomaly_rate=anomaly_rate,
        filtered_workload=result["filtered"],
        residuals=residuals.tolist(),
        residual_std=residual_std,
        overall_assessment=overall,
        recommendations=recommendations,
        parameters={
            "process_noise_Q": request.process_noise,
            "measurement_noise_R": request.measurement_noise,
            "anomaly_threshold_sigma": request.anomaly_threshold_sigma,
        },
    )
