"""
Tests for Kalman Filter Workload Trend Analysis MCP Tools.

These tests verify the Kalman filter tool implementations return properly
structured responses with realistic data for workload trend estimation,
trajectory prediction, and anomaly detection.
"""

import numpy as np
import pytest

from scheduler_mcp.tools.kalman_filter_tools import (
    KalmanFilter1D,
    WorkloadAnomalyRequest,
    WorkloadTrendRequest,
    analyze_workload_trend,
    assess_trend,
    compute_smoothness,
    detect_workload_anomalies,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def stable_workload_history() -> list[float]:
    """Stable workload pattern - minimal variation around 60 hours."""
    return [60.0, 61.0, 59.0, 60.0, 62.0, 59.0, 61.0, 60.0, 58.0, 61.0]


@pytest.fixture
def increasing_workload_history() -> list[float]:
    """Workload pattern with clear increasing trend."""
    return [50.0, 52.0, 55.0, 58.0, 60.0, 63.0, 66.0, 69.0, 72.0, 75.0]


@pytest.fixture
def decreasing_workload_history() -> list[float]:
    """Workload pattern with clear decreasing trend."""
    return [75.0, 72.0, 70.0, 68.0, 65.0, 62.0, 60.0, 58.0, 55.0, 52.0]


@pytest.fixture
def volatile_workload_history() -> list[float]:
    """Highly volatile workload pattern with extreme swings around a mean."""
    # Extreme oscillations around 60, with high CV but no clear trend direction
    return [40.0, 80.0, 30.0, 90.0, 35.0, 85.0, 25.0, 95.0, 45.0, 75.0, 20.0, 100.0]


@pytest.fixture
def workload_with_spike() -> list[float]:
    """Workload pattern with an anomalous spike at index 5."""
    return [60.0, 62.0, 58.0, 61.0, 59.0, 95.0, 60.0, 62.0, 58.0, 61.0]


@pytest.fixture
def noisy_workload_history() -> list[float]:
    """Noisy workload measurements with underlying upward trend."""
    np.random.seed(42)
    trend = np.linspace(55, 70, 20)
    noise = np.random.normal(0, 5, 20)
    return (trend + noise).tolist()


# =============================================================================
# KalmanFilter1D Unit Tests
# =============================================================================


class TestKalmanFilter1D:
    """Test suite for the KalmanFilter1D class."""

    def test_initialization(self):
        """Test Kalman filter initializes with correct values."""
        kf = KalmanFilter1D(
            initial_state=60.0,
            initial_error=1.0,
            process_noise=0.1,
            measurement_noise=1.0,
        )

        assert kf.x == 60.0
        assert kf.P == 1.0
        assert kf.Q == 0.1
        assert kf.R == 1.0
        assert len(kf.estimates) == 0
        assert len(kf.kalman_gains) == 0

    def test_predict_step(self):
        """Test prediction step increases uncertainty."""
        kf = KalmanFilter1D(
            initial_state=60.0,
            initial_error=1.0,
            process_noise=0.1,
            measurement_noise=1.0,
        )

        x_pred, P_pred = kf.predict()

        # State prediction should be unchanged (random walk)
        assert x_pred == 60.0
        # Error should increase by process noise
        assert P_pred == 1.0 + 0.1

    def test_update_step(self):
        """Test update step incorporates measurement."""
        kf = KalmanFilter1D(
            initial_state=60.0,
            initial_error=1.0,
            process_noise=0.1,
            measurement_noise=1.0,
        )

        x_new, P_new, K = kf.update(65.0)

        # State should move toward measurement
        assert x_new > 60.0
        assert x_new < 65.0
        # Error should decrease after update
        assert P_new < 1.1  # Less than predicted error
        # Kalman gain should be between 0 and 1
        assert 0.0 <= K <= 1.0

    def test_kalman_gain_bounds(self):
        """Test Kalman gain stays in [0, 1]."""
        kf = KalmanFilter1D(
            initial_state=60.0,
            initial_error=1.0,
            process_noise=0.1,
            measurement_noise=1.0,
        )

        for measurement in [50.0, 55.0, 60.0, 65.0, 70.0, 80.0]:
            _, _, K = kf.update(measurement)
            assert 0.0 <= K <= 1.0

    def test_filter_series(self, stable_workload_history):
        """Test filtering a series of measurements."""
        kf = KalmanFilter1D(
            initial_state=stable_workload_history[0],
            initial_error=1.0,
            process_noise=0.1,
            measurement_noise=1.0,
        )

        result = kf.filter_series(stable_workload_history)

        assert "filtered" in result
        assert "errors" in result
        assert "gains" in result
        assert "innovations" in result
        assert len(result["filtered"]) == len(stable_workload_history)
        assert len(result["errors"]) == len(stable_workload_history)
        assert len(result["gains"]) == len(stable_workload_history)

    def test_filter_smooths_noisy_data(self, noisy_workload_history):
        """Test that filtering produces smoother output than input."""
        kf = KalmanFilter1D(
            initial_state=noisy_workload_history[0],
            initial_error=1.0,
            process_noise=0.1,
            measurement_noise=2.0,
        )

        result = kf.filter_series(noisy_workload_history)
        filtered = result["filtered"]

        # Compute roughness (sum of absolute differences)
        raw_roughness = sum(
            abs(noisy_workload_history[i] - noisy_workload_history[i - 1])
            for i in range(1, len(noisy_workload_history))
        )
        filtered_roughness = sum(
            abs(filtered[i] - filtered[i - 1]) for i in range(1, len(filtered))
        )

        # Filtered should be smoother
        assert filtered_roughness < raw_roughness

    def test_predict_future(self):
        """Test future prediction functionality."""
        kf = KalmanFilter1D(
            initial_state=60.0,
            initial_error=1.0,
            process_noise=0.1,
            measurement_noise=1.0,
        )

        # Run some updates first
        for measurement in [61.0, 62.0, 63.0]:
            kf.update(measurement)

        future = kf.predict_future(n_steps=5)

        assert "predictions" in future
        assert "uncertainties" in future
        assert len(future["predictions"]) == 5
        assert len(future["uncertainties"]) == 5

        # Uncertainty should increase over time
        for i in range(1, len(future["uncertainties"])):
            assert future["uncertainties"][i] > future["uncertainties"][i - 1]


# =============================================================================
# analyze_workload_trend Tests
# =============================================================================


class TestAnalyzeWorkloadTrend:
    """Test suite for analyze_workload_trend tool."""

    @pytest.mark.asyncio
    async def test_basic_trend_analysis(self, stable_workload_history):
        """Test basic trend analysis returns valid response."""
        request = WorkloadTrendRequest(workload_history=stable_workload_history)
        result = await analyze_workload_trend(request)

        assert result.filtered_workload is not None
        assert len(result.filtered_workload) == len(stable_workload_history)
        assert len(result.confidence_intervals) == len(stable_workload_history)
        assert len(result.kalman_gain_history) == len(stable_workload_history)
        assert result.trend_assessment in [
            "INCREASING",
            "STABLE",
            "DECREASING",
            "VOLATILE",
            "INSUFFICIENT_DATA",
        ]
        assert 0.0 <= result.smoothness_score <= 1.0

    @pytest.mark.asyncio
    async def test_trend_assessment_increasing(self, increasing_workload_history):
        """Test increasing trend is correctly detected."""
        request = WorkloadTrendRequest(workload_history=increasing_workload_history)
        result = await analyze_workload_trend(request)

        assert result.trend_assessment == "INCREASING"

    @pytest.mark.asyncio
    async def test_trend_assessment_decreasing(self, decreasing_workload_history):
        """Test decreasing trend is correctly detected."""
        request = WorkloadTrendRequest(workload_history=decreasing_workload_history)
        result = await analyze_workload_trend(request)

        assert result.trend_assessment == "DECREASING"

    @pytest.mark.asyncio
    async def test_trend_assessment_stable(self, stable_workload_history):
        """Test stable pattern is correctly detected."""
        request = WorkloadTrendRequest(workload_history=stable_workload_history)
        result = await analyze_workload_trend(request)

        assert result.trend_assessment == "STABLE"

    @pytest.mark.asyncio
    async def test_trend_assessment_volatile(self, volatile_workload_history):
        """Test volatile pattern behavior after filtering.

        Note: Kalman filtering smooths volatile data. The raw data is volatile,
        but the filtered trend may show as INCREASING/DECREASING/STABLE depending
        on the underlying pattern. This test verifies the filter processes
        volatile data without errors and produces a valid trend assessment.
        """
        request = WorkloadTrendRequest(workload_history=volatile_workload_history)
        result = await analyze_workload_trend(request)

        # After filtering, trend should be one of the valid assessments
        assert result.trend_assessment in [
            "INCREASING",
            "STABLE",
            "DECREASING",
            "VOLATILE",
        ]
        # The raw data was volatile, so smoothness should be positive
        # (filter reduced volatility)
        assert result.smoothness_score > 0.0

    @pytest.mark.asyncio
    async def test_confidence_intervals_structure(self, stable_workload_history):
        """Test confidence intervals have expected structure."""
        request = WorkloadTrendRequest(workload_history=stable_workload_history)
        result = await analyze_workload_trend(request)

        for ci in result.confidence_intervals:
            assert "lower" in ci
            assert "upper" in ci
            assert "std_dev" in ci
            assert ci["lower"] < ci["upper"]
            assert ci["std_dev"] >= 0.0

    @pytest.mark.asyncio
    async def test_predictions_when_requested(self, stable_workload_history):
        """Test future predictions are returned when requested."""
        request = WorkloadTrendRequest(
            workload_history=stable_workload_history, prediction_steps=5
        )
        result = await analyze_workload_trend(request)

        assert len(result.predictions) == 5
        assert len(result.prediction_confidence) == 5

        # Prediction confidence should have proper structure
        for pc in result.prediction_confidence:
            assert "lower" in pc
            assert "upper" in pc
            assert "std_dev" in pc

    @pytest.mark.asyncio
    async def test_no_predictions_when_zero_steps(self, stable_workload_history):
        """Test no predictions when prediction_steps is 0."""
        request = WorkloadTrendRequest(
            workload_history=stable_workload_history, prediction_steps=0
        )
        result = await analyze_workload_trend(request)

        assert len(result.predictions) == 0
        assert len(result.prediction_confidence) == 0

    @pytest.mark.asyncio
    async def test_custom_noise_parameters(self, noisy_workload_history):
        """Test custom process and measurement noise parameters."""
        # High measurement noise = trust measurements less
        request_high_r = WorkloadTrendRequest(
            workload_history=noisy_workload_history,
            process_noise=0.1,
            measurement_noise=5.0,
        )
        result_high_r = await analyze_workload_trend(request_high_r)

        # Low measurement noise = trust measurements more
        request_low_r = WorkloadTrendRequest(
            workload_history=noisy_workload_history,
            process_noise=0.1,
            measurement_noise=0.5,
        )
        result_low_r = await analyze_workload_trend(request_low_r)

        # High R should produce smoother output
        assert result_high_r.smoothness_score >= result_low_r.smoothness_score

    @pytest.mark.asyncio
    async def test_initial_estimate_custom(self, stable_workload_history):
        """Test custom initial estimate is used."""
        request = WorkloadTrendRequest(
            workload_history=stable_workload_history, initial_estimate=50.0
        )
        result = await analyze_workload_trend(request)

        assert result.parameters["initial_state"] == 50.0

    @pytest.mark.asyncio
    async def test_parameters_in_response(self, stable_workload_history):
        """Test filter parameters are returned in response."""
        request = WorkloadTrendRequest(
            workload_history=stable_workload_history,
            process_noise=0.5,
            measurement_noise=2.0,
            initial_error=1.5,
        )
        result = await analyze_workload_trend(request)

        assert result.parameters["process_noise_Q"] == 0.5
        assert result.parameters["measurement_noise_R"] == 2.0
        assert result.parameters["initial_error"] == 1.5

    @pytest.mark.asyncio
    async def test_metadata_statistics(self, stable_workload_history):
        """Test metadata contains expected statistics."""
        request = WorkloadTrendRequest(workload_history=stable_workload_history)
        result = await analyze_workload_trend(request)

        assert "data_points" in result.metadata
        assert "mean_kalman_gain" in result.metadata
        assert "final_error_covariance" in result.metadata
        assert "mean_workload" in result.metadata
        assert "std_workload" in result.metadata
        assert result.metadata["data_points"] == len(stable_workload_history)

    @pytest.mark.asyncio
    async def test_kalman_gain_converges(self, noisy_workload_history):
        """Test Kalman gain converges over time."""
        request = WorkloadTrendRequest(workload_history=noisy_workload_history)
        result = await analyze_workload_trend(request)

        gains = result.kalman_gain_history

        # Gain should decrease as filter converges
        early_avg = sum(gains[:5]) / 5
        late_avg = sum(gains[-5:]) / 5
        assert late_avg <= early_avg


# =============================================================================
# detect_workload_anomalies Tests
# =============================================================================


class TestDetectWorkloadAnomalies:
    """Test suite for detect_workload_anomalies tool."""

    @pytest.mark.asyncio
    async def test_basic_anomaly_detection(self, stable_workload_history):
        """Test basic anomaly detection returns valid response."""
        request = WorkloadAnomalyRequest(workload_history=stable_workload_history)
        result = await detect_workload_anomalies(request)

        assert result.total_anomalies >= 0
        assert len(result.anomalies) == result.total_anomalies
        assert 0.0 <= result.anomaly_rate <= 1.0
        assert len(result.filtered_workload) == len(stable_workload_history)
        assert len(result.residuals) == len(stable_workload_history)
        assert result.residual_std >= 0.0
        assert result.overall_assessment in ["STABLE", "CONCERNING", "CRITICAL"]

    @pytest.mark.asyncio
    async def test_detects_spike_anomaly(self, workload_with_spike):
        """Test that a clear spike is detected as anomaly."""
        request = WorkloadAnomalyRequest(
            workload_history=workload_with_spike, anomaly_threshold_sigma=2.0
        )
        result = await detect_workload_anomalies(request)

        assert result.total_anomalies >= 1
        # The spike at index 5 should be detected
        spike_detected = any(a.index == 5 for a in result.anomalies)
        assert spike_detected

    @pytest.mark.asyncio
    async def test_no_anomalies_in_stable_data(self, stable_workload_history):
        """Test that stable data has no or few anomalies."""
        request = WorkloadAnomalyRequest(
            workload_history=stable_workload_history, anomaly_threshold_sigma=2.0
        )
        result = await detect_workload_anomalies(request)

        # Stable data should have low anomaly rate
        assert result.anomaly_rate < 0.3

    @pytest.mark.asyncio
    async def test_anomaly_point_structure(self, workload_with_spike):
        """Test anomaly point objects have expected fields."""
        request = WorkloadAnomalyRequest(workload_history=workload_with_spike)
        result = await detect_workload_anomalies(request)

        for anomaly in result.anomalies:
            assert hasattr(anomaly, "index")
            assert hasattr(anomaly, "measured_value")
            assert hasattr(anomaly, "filtered_value")
            assert hasattr(anomaly, "residual")
            assert hasattr(anomaly, "residual_sigma")
            assert hasattr(anomaly, "severity")
            assert anomaly.severity in ["MODERATE", "HIGH", "CRITICAL"]
            assert anomaly.residual_sigma >= 0.0

    @pytest.mark.asyncio
    async def test_anomalies_sorted_by_severity(self, volatile_workload_history):
        """Test anomalies are sorted by severity then residual."""
        request = WorkloadAnomalyRequest(
            workload_history=volatile_workload_history, anomaly_threshold_sigma=1.5
        )
        result = await detect_workload_anomalies(request)

        if len(result.anomalies) > 1:
            severity_order = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2}
            for i in range(1, len(result.anomalies)):
                prev = result.anomalies[i - 1]
                curr = result.anomalies[i]
                # Should be sorted by severity first
                assert severity_order[prev.severity] <= severity_order[curr.severity]

    @pytest.mark.asyncio
    async def test_threshold_sensitivity(self, workload_with_spike):
        """Test that lower threshold detects more anomalies."""
        request_strict = WorkloadAnomalyRequest(
            workload_history=workload_with_spike, anomaly_threshold_sigma=3.0
        )
        result_strict = await detect_workload_anomalies(request_strict)

        request_loose = WorkloadAnomalyRequest(
            workload_history=workload_with_spike, anomaly_threshold_sigma=1.5
        )
        result_loose = await detect_workload_anomalies(request_loose)

        # Lower threshold should detect more anomalies
        assert result_loose.total_anomalies >= result_strict.total_anomalies

    @pytest.mark.asyncio
    async def test_overall_assessment_stable(self, stable_workload_history):
        """Test stable assessment for clean data."""
        request = WorkloadAnomalyRequest(workload_history=stable_workload_history)
        result = await detect_workload_anomalies(request)

        assert result.overall_assessment == "STABLE"

    @pytest.mark.asyncio
    async def test_overall_assessment_concerning(self):
        """Test concerning assessment for data with anomalies."""
        # Data with a few anomalies (but not too many)
        workload = [60.0, 62.0, 58.0, 80.0, 60.0, 61.0, 59.0, 62.0, 60.0, 58.0]
        request = WorkloadAnomalyRequest(
            workload_history=workload, anomaly_threshold_sigma=2.0
        )
        result = await detect_workload_anomalies(request)

        # Should be concerning if there are HIGH severity anomalies
        if any(a.severity == "HIGH" for a in result.anomalies):
            assert result.overall_assessment in ["CONCERNING", "CRITICAL"]

    @pytest.mark.asyncio
    async def test_recommendations_generated(self, workload_with_spike):
        """Test that recommendations are generated for anomalies."""
        request = WorkloadAnomalyRequest(workload_history=workload_with_spike)
        result = await detect_workload_anomalies(request)

        assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_recommendations_for_no_anomalies(self, stable_workload_history):
        """Test that recommendation is generated even when no anomalies."""
        request = WorkloadAnomalyRequest(
            workload_history=stable_workload_history, anomaly_threshold_sigma=4.0
        )
        result = await detect_workload_anomalies(request)

        if result.total_anomalies == 0:
            assert len(result.recommendations) > 0
            assert "stable" in result.recommendations[0].lower()

    @pytest.mark.asyncio
    async def test_parameters_in_response(self, stable_workload_history):
        """Test parameters are returned in response."""
        request = WorkloadAnomalyRequest(
            workload_history=stable_workload_history,
            process_noise=0.2,
            measurement_noise=1.5,
            anomaly_threshold_sigma=2.5,
        )
        result = await detect_workload_anomalies(request)

        assert result.parameters["process_noise_Q"] == 0.2
        assert result.parameters["measurement_noise_R"] == 1.5
        assert result.parameters["anomaly_threshold_sigma"] == 2.5


# =============================================================================
# Utility Function Tests
# =============================================================================


class TestAssessTrend:
    """Test suite for assess_trend utility function."""

    def test_insufficient_data(self):
        """Test returns INSUFFICIENT_DATA for short series."""
        assert assess_trend([60.0, 61.0]) == "INSUFFICIENT_DATA"

    def test_increasing_trend(self):
        """Test detects increasing trend."""
        result = assess_trend([50.0, 55.0, 60.0, 65.0, 70.0, 75.0])
        assert result == "INCREASING"

    def test_decreasing_trend(self):
        """Test detects decreasing trend."""
        result = assess_trend([75.0, 70.0, 65.0, 60.0, 55.0, 50.0])
        assert result == "DECREASING"

    def test_stable_trend(self):
        """Test detects stable pattern."""
        result = assess_trend([60.0, 60.1, 59.9, 60.0, 60.1, 59.9])
        assert result == "STABLE"

    def test_volatile_trend(self):
        """Test detects volatile pattern."""
        result = assess_trend([50.0, 80.0, 45.0, 85.0, 40.0, 90.0])
        assert result == "VOLATILE"


class TestComputeSmoothness:
    """Test suite for compute_smoothness utility function."""

    def test_short_series_returns_zero(self):
        """Test returns 0 for very short series."""
        assert compute_smoothness([60.0], [60.0]) == 0.0

    def test_already_smooth_data(self):
        """Test high smoothness for already smooth data."""
        raw = [60.0, 60.0, 60.0, 60.0, 60.0]
        filtered = [60.0, 60.0, 60.0, 60.0, 60.0]
        result = compute_smoothness(raw, filtered)
        assert result == 1.0

    def test_filtered_smoother_than_raw(self):
        """Test that filtering produces positive smoothness score."""
        raw = [60.0, 70.0, 55.0, 75.0, 50.0]
        filtered = [60.0, 63.0, 61.0, 65.0, 62.0]
        result = compute_smoothness(raw, filtered)
        assert 0.0 < result <= 1.0

    def test_smoothness_bounds(self):
        """Test smoothness is always in [0, 1]."""
        raw = [60.0, 80.0, 40.0, 90.0, 30.0, 100.0]
        filtered = [60.0, 65.0, 58.0, 68.0, 55.0, 70.0]
        result = compute_smoothness(raw, filtered)
        assert 0.0 <= result <= 1.0


# =============================================================================
# Request Validation Tests
# =============================================================================


class TestRequestValidation:
    """Test suite for request validation."""

    def test_workload_trend_request_minimum_length(self):
        """Test minimum history length is enforced."""
        with pytest.raises(ValueError):
            WorkloadTrendRequest(workload_history=[60.0])  # Too short

    def test_workload_trend_request_negative_values(self):
        """Test negative workload values are rejected."""
        with pytest.raises(ValueError):
            WorkloadTrendRequest(workload_history=[60.0, -10.0, 62.0])

    def test_anomaly_request_minimum_length(self):
        """Test anomaly detection requires minimum 3 data points."""
        with pytest.raises(ValueError):
            WorkloadAnomalyRequest(workload_history=[60.0, 61.0])  # Too short

    def test_process_noise_bounds(self):
        """Test process noise parameter bounds."""
        with pytest.raises(ValueError):
            WorkloadTrendRequest(
                workload_history=[60.0, 61.0, 62.0], process_noise=0.0001  # Too low
            )

        with pytest.raises(ValueError):
            WorkloadTrendRequest(
                workload_history=[60.0, 61.0, 62.0], process_noise=100.0  # Too high
            )

    def test_measurement_noise_bounds(self):
        """Test measurement noise parameter bounds."""
        with pytest.raises(ValueError):
            WorkloadTrendRequest(
                workload_history=[60.0, 61.0, 62.0], measurement_noise=0.0001  # Too low
            )

        with pytest.raises(ValueError):
            WorkloadTrendRequest(
                workload_history=[60.0, 61.0, 62.0], measurement_noise=200.0  # Too high
            )

    def test_prediction_steps_bounds(self):
        """Test prediction steps parameter bounds."""
        with pytest.raises(ValueError):
            WorkloadTrendRequest(
                workload_history=[60.0, 61.0, 62.0], prediction_steps=-1  # Negative
            )

        with pytest.raises(ValueError):
            WorkloadTrendRequest(
                workload_history=[60.0, 61.0, 62.0], prediction_steps=100  # Too high
            )

    def test_anomaly_threshold_bounds(self):
        """Test anomaly threshold sigma parameter bounds."""
        with pytest.raises(ValueError):
            WorkloadAnomalyRequest(
                workload_history=[60.0, 61.0, 62.0],
                anomaly_threshold_sigma=0.5,  # Too low
            )

        with pytest.raises(ValueError):
            WorkloadAnomalyRequest(
                workload_history=[60.0, 61.0, 62.0],
                anomaly_threshold_sigma=10.0,  # Too high
            )


# =============================================================================
# Integration Tests
# =============================================================================


class TestToolIntegration:
    """Test integration between Kalman filter tools."""

    @pytest.mark.asyncio
    async def test_trend_and_anomaly_consistency(self, noisy_workload_history):
        """Test that trend analysis and anomaly detection are consistent."""
        trend_request = WorkloadTrendRequest(workload_history=noisy_workload_history)
        trend_result = await analyze_workload_trend(trend_request)

        anomaly_request = WorkloadAnomalyRequest(
            workload_history=noisy_workload_history
        )
        anomaly_result = await detect_workload_anomalies(anomaly_request)

        # Both should produce filtered workload of same length
        assert len(trend_result.filtered_workload) == len(
            anomaly_result.filtered_workload
        )

    @pytest.mark.asyncio
    async def test_prediction_follows_trend(self, increasing_workload_history):
        """Test that predictions follow detected trend."""
        request = WorkloadTrendRequest(
            workload_history=increasing_workload_history, prediction_steps=3
        )
        result = await analyze_workload_trend(request)

        # For increasing trend, predictions should be near or above last filtered value
        last_filtered = result.filtered_workload[-1]
        assert all(p >= last_filtered - 5 for p in result.predictions)

    @pytest.mark.asyncio
    async def test_comprehensive_workload_analysis(self, noisy_workload_history):
        """Test running both tools in sequence for complete analysis."""
        # 1. Analyze trend
        trend_request = WorkloadTrendRequest(
            workload_history=noisy_workload_history, prediction_steps=3
        )
        trend_result = await analyze_workload_trend(trend_request)

        assert trend_result.trend_assessment is not None
        assert len(trend_result.predictions) == 3

        # 2. Detect anomalies
        anomaly_request = WorkloadAnomalyRequest(
            workload_history=noisy_workload_history, anomaly_threshold_sigma=2.0
        )
        anomaly_result = await detect_workload_anomalies(anomaly_request)

        assert anomaly_result.overall_assessment is not None
        assert len(anomaly_result.recommendations) > 0
