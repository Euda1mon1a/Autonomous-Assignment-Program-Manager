"""
Integration tests for Kalman Filter Workload Estimation Bridge.

Tests the Kalman filter implementation for estimating faculty workload from
noisy measurements (scheduled hours, self-reports, call volume).

Reference:
    docs/architecture/bridges/KALMAN_WORKLOAD_BRIDGE.md

Test Coverage:
    1. Consistent measurements (low residuals)
    2. Noisy self-reports (filter smooths noise)
    3. Sudden workload changes (filter adapts)
    4. Missing data (predict-only mode)
    5. Confidence interval coverage (95% CI validation)
    6. Kalman gain calculation (verify mathematics)
"""

from uuid import uuid4

import numpy as np
import pytest


# NOTE: This assumes the implementation will be at this location
# If the implementation doesn't exist yet, these tests serve as specifications
try:
    from app.resilience.kalman_filters import WorkloadKalmanFilter
    IMPLEMENTATION_EXISTS = True
except ImportError:
    IMPLEMENTATION_EXISTS = False
    # Create a mock for development
    class WorkloadKalmanFilter:
        """Mock implementation for testing purposes."""
        def __init__(self, person_id, initial_hours=60.0, **kwargs):
            self.person_id = person_id
            self.x = np.array([initial_hours, 0.0, 0.0])
            self.P = np.array([[25.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 4.0]])
            self.history = []

        def update(self, measurements):
            raise NotImplementedError("WorkloadKalmanFilter not yet implemented")


@pytest.mark.integration
@pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="WorkloadKalmanFilter not yet implemented")
class TestKalmanConsistentMeasurements:
    """Test Kalman filter with consistent, low-noise measurements."""

    def test_convergence_with_consistent_data(self):
        """
        Verify filter converges to true value when all measurements agree.

        Scenario:
            - True workload: 65 hours/week
            - All measurements (scheduled, self-report, call) agree within small noise
            - Run for 10 weeks

        Expected:
            - Final estimate within 1 hour of truth
            - Low uncertainty (< 1.0 hours)
            - Small measurement residuals (< 0.5 hours)
        """
        kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=60.0)

        true_workload = 65.0

        # Simulate 10 weeks of consistent measurements
        for week in range(10):
            measurements = {
                "scheduled_hours": true_workload + np.random.normal(0, 0.2),  # Very low noise
                "self_reported": true_workload + np.random.normal(0, 0.5),   # Low noise
                "call_volume": true_workload + np.random.normal(0, 0.3),     # Low noise
            }
            estimate = kf.update(measurements)

        # Assertions
        assert abs(estimate.estimated_hours - true_workload) < 1.0, (
            f"Estimate {estimate.estimated_hours:.2f} should be within 1 hour of true value {true_workload}"
        )

        assert estimate.uncertainty_std < 1.0, (
            f"Uncertainty {estimate.uncertainty_std:.2f} should converge to < 1.0 after 10 consistent measurements"
        )

        assert estimate.measurement_residual is not None, "Should have measurement residual"
        assert abs(estimate.measurement_residual) < 0.5, (
            f"Residual {estimate.measurement_residual:.2f} should be small with consistent data"
        )

    def test_uncertainty_decreases_over_time(self):
        """
        Verify that uncertainty decreases as more measurements are collected.

        With consistent measurements, the filter should become more confident.
        """
        kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=60.0)

        true_workload = 70.0
        uncertainties = []

        # Collect 15 weeks of data
        for week in range(15):
            measurements = {"scheduled_hours": true_workload + np.random.normal(0, 0.3)}
            estimate = kf.update(measurements)
            uncertainties.append(estimate.uncertainty_std)

        # Check that uncertainty is decreasing
        initial_uncertainty = uncertainties[0]
        final_uncertainty = uncertainties[-1]

        assert final_uncertainty < initial_uncertainty, (
            f"Final uncertainty {final_uncertainty:.2f} should be less than "
            f"initial uncertainty {initial_uncertainty:.2f}"
        )

        # Check monotonic decrease (allowing for small numerical fluctuations)
        # Use windowed comparison to handle potential numerical instability
        window_size = 3
        for i in range(window_size, len(uncertainties)):
            avg_early = np.mean(uncertainties[i-window_size:i])
            avg_late = np.mean(uncertainties[i:i+window_size])
            # Allow for small increases due to numerical effects
            assert avg_late <= avg_early * 1.1, (
                f"Uncertainty should generally decrease over time (week {i})"
            )


@pytest.mark.integration
@pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="WorkloadKalmanFilter not yet implemented")
class TestKalmanNoisyMeasurements:
    """Test Kalman filter's ability to smooth noisy measurements."""

    def test_filters_noisy_self_reports(self):
        """
        Verify filter smooths high-variance self-reports.

        Scenario:
            - True workload: 70 hours
            - Scheduled hours: Low noise (± 0.3)
            - Self-reports: HIGH noise (± 5.0) - simulates subjective reporting
            - Run for 20 weeks

        Expected:
            - Final estimate within 2 hours of truth despite noisy self-reports
            - Estimate variance < self-report variance (demonstrates smoothing)
        """
        kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=60.0)

        true_workload = 70.0
        estimates = []

        for week in range(20):
            measurements = {
                "scheduled_hours": true_workload + np.random.normal(0, 0.3),  # Low noise
                "self_reported": true_workload + np.random.normal(0, 5.0),    # HIGH noise
            }
            estimate = kf.update(measurements)
            estimates.append(estimate.estimated_hours)

        # Final estimate should be close to true value
        final_estimate = estimates[-1]
        assert abs(final_estimate - true_workload) < 2.0, (
            f"Estimate {final_estimate:.2f} should be within 2 hours of true value {true_workload} "
            "despite noisy self-reports"
        )

        # Variance of estimates should be much lower than self-report noise
        estimate_std = np.std(estimates[-10:])  # Last 10 estimates
        assert estimate_std < 3.0, (
            f"Estimate std {estimate_std:.2f} should be < 3.0 (much less than self-report noise of 5.0)"
        )

    def test_differential_weighting_by_noise(self):
        """
        Verify filter weights low-noise measurements more than high-noise.

        Create two scenarios:
        1. Low-noise scheduled hours says 65, high-noise self-report says 75
        2. High-noise scheduled hours says 75, low-noise self-report says 65

        The filter should weight the low-noise measurement more heavily.
        """
        # Scenario 1: Trust scheduled hours (low noise)
        kf1 = WorkloadKalmanFilter(
            person_id=uuid4(),
            initial_hours=60.0,
            measurement_noise_scheduled=0.05,   # Low noise
            measurement_noise_self_report=5.0,  # High noise
        )

        # Give 5 measurements to stabilize
        for _ in range(5):
            kf1.update({
                "scheduled_hours": 65.0 + np.random.normal(0, 0.2),
                "self_reported": 75.0 + np.random.normal(0, 3.0),  # Consistently higher
            })

        estimate1 = kf1.history[-1]

        # Estimate should be closer to scheduled hours (65) than self-report (75)
        distance_to_scheduled = abs(estimate1.estimated_hours - 65.0)
        distance_to_self_report = abs(estimate1.estimated_hours - 75.0)

        assert distance_to_scheduled < distance_to_self_report, (
            f"Estimate {estimate1.estimated_hours:.2f} should be closer to low-noise scheduled (65) "
            f"than high-noise self-report (75)"
        )


@pytest.mark.integration
@pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="WorkloadKalmanFilter not yet implemented")
class TestKalmanAdaptation:
    """Test Kalman filter's ability to adapt to sudden changes."""

    def test_adapts_to_sudden_workload_increase(self):
        """
        Verify filter tracks sudden workload change (e.g., deployment coverage).

        Scenario:
            - Weeks 1-10: Stable at 60 hours
            - Weeks 11-20: Sudden jump to 75 hours (deployment)

        Expected:
            - Final estimate within 2 hours of new level (75)
            - Positive trend detected (> 0.5 hours/week)
        """
        kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=60.0)

        # Phase 1: Stable at 60 hours
        for week in range(10):
            measurements = {"scheduled_hours": 60.0 + np.random.normal(0, 0.3)}
            kf.update(measurements)

        # Phase 2: Jump to 75 hours
        for week in range(10):
            measurements = {"scheduled_hours": 75.0 + np.random.normal(0, 0.3)}
            estimate = kf.update(measurements)

        # Should track new level
        assert abs(estimate.estimated_hours - 75.0) < 2.0, (
            f"Estimate {estimate.estimated_hours:.2f} should adapt to new level 75.0"
        )

        # Should detect positive trend (may have decayed, but should be detectable in history)
        # Check trend was positive during transition
        trends_during_transition = [h.trend for h in kf.history[10:15]]  # Weeks 11-15
        max_trend = max(trends_during_transition)

        assert max_trend > 0.5, (
            f"Max trend {max_trend:.2f} during transition should be > 0.5 hours/week"
        )

    def test_adapts_to_workload_decrease(self):
        """
        Verify filter also adapts to workload decreases.

        Scenario:
            - Weeks 1-10: High workload (80 hours)
            - Weeks 11-20: Return to normal (65 hours)

        Expected:
            - Final estimate within 2 hours of 65
            - Negative trend detected during transition
        """
        kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=80.0)

        # Phase 1: High workload
        for week in range(10):
            measurements = {"scheduled_hours": 80.0 + np.random.normal(0, 0.3)}
            kf.update(measurements)

        # Phase 2: Drop to 65 hours
        for week in range(10):
            measurements = {"scheduled_hours": 65.0 + np.random.normal(0, 0.3)}
            estimate = kf.update(measurements)

        assert abs(estimate.estimated_hours - 65.0) < 2.0, (
            f"Estimate {estimate.estimated_hours:.2f} should adapt to decreased level 65.0"
        )

        # Check for negative trend during transition
        trends_during_transition = [h.trend for h in kf.history[10:15]]
        min_trend = min(trends_during_transition)

        assert min_trend < -0.5, (
            f"Min trend {min_trend:.2f} during decrease should be < -0.5 hours/week"
        )


@pytest.mark.integration
@pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="WorkloadKalmanFilter not yet implemented")
class TestKalmanMissingData:
    """Test Kalman filter's predict-only mode when measurements are missing."""

    def test_handles_missing_measurements_gracefully(self):
        """
        Verify filter operates in predict-only mode when no measurements available.

        Scenario:
            - Weeks 1-5: Build up estimate with data
            - Weeks 6-8: No measurements (faculty didn't complete survey)
            - Filter should still produce estimates

        Expected:
            - Estimates continue (using prediction only)
            - Uncertainty increases without measurements
            - No crashes or errors
        """
        kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=60.0)

        # Build up estimate with data
        for week in range(5):
            measurements = {"scheduled_hours": 65.0 + np.random.normal(0, 0.3)}
            kf.update(measurements)

        initial_uncertainty = kf.history[-1].uncertainty_std

        # Now missing data for 3 weeks
        estimates_predict_only = []
        for week in range(3):
            estimate = kf.update({})  # No measurements
            estimates_predict_only.append(estimate.estimated_hours)

        # Should still produce valid estimates
        assert all(e > 0 for e in estimates_predict_only), (
            "All estimates should be positive even without measurements"
        )

        # Should have recorded that no measurements were used
        assert kf.history[-1].measurements_used == [], (
            "Should record that no measurements were used"
        )

        # Measurement residual should be None (no measurements to compare)
        assert kf.history[-1].measurement_residual is None, (
            "Measurement residual should be None when no measurements available"
        )

        # Uncertainty should increase without measurements
        final_uncertainty = kf.history[-1].uncertainty_std
        assert final_uncertainty > initial_uncertainty, (
            f"Uncertainty should increase from {initial_uncertainty:.2f} to {final_uncertainty:.2f} "
            "without new measurements"
        )

    def test_recovers_after_missing_data_period(self):
        """
        Verify filter recovers and re-converges after missing data period.

        Scenario:
            - Weeks 1-5: Normal measurements
            - Weeks 6-8: Missing data
            - Weeks 9-15: Resume measurements

        Expected:
            - Uncertainty increases during gap
            - Uncertainty decreases again after measurements resume
            - Final estimate still accurate
        """
        kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=60.0)

        true_workload = 68.0

        # Phase 1: Build estimate
        for week in range(5):
            measurements = {"scheduled_hours": true_workload + np.random.normal(0, 0.3)}
            kf.update(measurements)

        uncertainty_before_gap = kf.history[-1].uncertainty_std

        # Phase 2: Missing data
        for week in range(3):
            kf.update({})

        uncertainty_during_gap = kf.history[-1].uncertainty_std

        # Phase 3: Resume measurements
        for week in range(7):
            measurements = {"scheduled_hours": true_workload + np.random.normal(0, 0.3)}
            estimate = kf.update(measurements)

        uncertainty_after_recovery = kf.history[-1].uncertainty_std

        # Verify uncertainty behavior
        assert uncertainty_during_gap > uncertainty_before_gap, (
            "Uncertainty should increase during gap"
        )

        assert uncertainty_after_recovery < uncertainty_during_gap, (
            "Uncertainty should decrease after measurements resume"
        )

        # Final estimate should still be accurate
        assert abs(estimate.estimated_hours - true_workload) < 2.0, (
            f"Estimate {estimate.estimated_hours:.2f} should recover to true value {true_workload} "
            "after missing data period"
        )


@pytest.mark.integration
@pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="WorkloadKalmanFilter not yet implemented")
class TestKalmanConfidenceIntervals:
    """Test Kalman filter confidence interval calibration."""

    def test_95_percent_coverage(self):
        """
        Verify 95% confidence intervals contain true value ~95% of the time.

        Statistical test:
            - Run 100 trials
            - Each trial: 20 weeks of measurements with known true value
            - Count how many times true value falls within 95% CI

        Expected:
            - Coverage rate between 90% and 100% (allowing for statistical variation)
            - This validates the uncertainty quantification is well-calibrated
        """
        true_workload = 68.0
        coverage_count = 0
        trials = 100

        np.random.seed(42)  # Reproducibility

        for trial in range(trials):
            kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=60.0)

            # Simulate 20 weeks
            for week in range(20):
                measurements = {
                    "scheduled_hours": true_workload + np.random.normal(0, 0.5),
                    "self_reported": true_workload + np.random.normal(0, 3.0),
                }
                estimate = kf.update(measurements)

            # Check if true value is within 95% CI
            if estimate.confidence_95_lower <= true_workload <= estimate.confidence_95_upper:
                coverage_count += 1

        coverage_rate = coverage_count / trials

        # Should be approximately 0.95 (allow 0.90-1.00 for statistical variation)
        assert 0.90 <= coverage_rate <= 1.00, (
            f"95% CI coverage rate {coverage_rate:.2%} should be between 90% and 100%"
        )

    def test_confidence_interval_width_decreases(self):
        """
        Verify confidence intervals narrow as filter converges.

        With more measurements, the filter should become more certain,
        resulting in narrower confidence intervals.
        """
        kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=60.0)

        true_workload = 65.0
        ci_widths = []

        for week in range(20):
            measurements = {"scheduled_hours": true_workload + np.random.normal(0, 0.3)}
            estimate = kf.update(measurements)

            ci_width = estimate.confidence_95_upper - estimate.confidence_95_lower
            ci_widths.append(ci_width)

        # Initial CI should be wider than final CI
        initial_width = ci_widths[0]
        final_width = ci_widths[-1]

        assert final_width < initial_width, (
            f"Final CI width {final_width:.2f} should be narrower than "
            f"initial CI width {initial_width:.2f}"
        )

        # CI width should generally decrease
        # Check that average width in second half is less than first half
        avg_first_half = np.mean(ci_widths[:10])
        avg_second_half = np.mean(ci_widths[10:])

        assert avg_second_half < avg_first_half, (
            f"Average CI width should decrease over time (first half: {avg_first_half:.2f}, "
            f"second half: {avg_second_half:.2f})"
        )


@pytest.mark.integration
@pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="WorkloadKalmanFilter not yet implemented")
class TestKalmanGainCalculation:
    """Test Kalman gain calculation and mathematical correctness."""

    def test_kalman_gain_formula(self):
        """
        Verify Kalman gain is computed correctly: K = P × H^T × (H × P × H^T + R)^-1

        This tests the mathematical correctness of the core Kalman filter equation.

        Method:
            - Update filter with measurements
            - Extract Kalman gain from result
            - Manually compute expected Kalman gain using matrix operations
            - Verify they match
        """
        kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=60.0)

        # Perform predict step manually to get P_pred
        x_pred = kf.F @ kf.x
        P_pred = kf.F @ kf.P @ kf.F.T + kf.Q

        # Create measurements
        measurements = {
            "scheduled_hours": 65.0,
            "self_reported": 67.0,
        }

        # Update filter
        estimate = kf.update(measurements)

        # Extract Kalman gain from estimate
        K_actual = estimate.kalman_gain

        assert K_actual is not None, "Kalman gain should be recorded"

        # Manually compute expected Kalman gain
        # Build observation matrices for available measurements
        H_obs = np.array([
            kf.H[0],  # scheduled_hours
            kf.H[1],  # self_reported
        ])

        R_obs = np.array([
            [kf.R[0, 0], 0.0],
            [0.0, kf.R[1, 1]],
        ])

        # K = P_pred @ H^T @ inv(H @ P_pred @ H^T + R)
        S = H_obs @ P_pred @ H_obs.T + R_obs  # Innovation covariance
        K_expected = P_pred @ H_obs.T @ np.linalg.inv(S)

        # Verify match (within numerical tolerance)
        np.testing.assert_allclose(
            K_actual,
            K_expected,
            rtol=1e-5,
            atol=1e-8,
            err_msg="Kalman gain should match theoretical formula"
        )

    def test_kalman_gain_weighting(self):
        """
        Verify Kalman gain correctly weights prediction vs measurement.

        Test two extremes:
        1. Low measurement noise → High Kalman gain (trust measurement more)
        2. High measurement noise → Low Kalman gain (trust prediction more)
        """
        # Scenario 1: Low measurement noise (trust measurements)
        kf_low_noise = WorkloadKalmanFilter(
            person_id=uuid4(),
            initial_hours=60.0,
            measurement_noise_scheduled=0.01,  # Very low noise
        )

        # Build up some history
        for _ in range(3):
            kf_low_noise.update({"scheduled_hours": 60.0})

        # Now give a measurement far from current estimate
        estimate_low_noise = kf_low_noise.update({"scheduled_hours": 70.0})

        # Scenario 2: High measurement noise (trust prediction)
        kf_high_noise = WorkloadKalmanFilter(
            person_id=uuid4(),
            initial_hours=60.0,
            measurement_noise_scheduled=10.0,  # Very high noise
        )

        # Build up some history
        for _ in range(3):
            kf_high_noise.update({"scheduled_hours": 60.0})

        # Give same measurement
        estimate_high_noise = kf_high_noise.update({"scheduled_hours": 70.0})

        # Low noise case should move estimate closer to measurement
        # High noise case should keep estimate closer to prediction

        movement_low_noise = abs(estimate_low_noise.estimated_hours - 60.0)
        movement_high_noise = abs(estimate_high_noise.estimated_hours - 60.0)

        assert movement_low_noise > movement_high_noise, (
            f"Low-noise filter should move more toward measurement "
            f"(moved {movement_low_noise:.2f}) than high-noise filter "
            f"(moved {movement_high_noise:.2f})"
        )

    def test_innovation_calculation(self):
        """
        Verify innovation (measurement residual) is computed correctly.

        Innovation = measurement - predicted_measurement
                   = z - H × x_pred

        This is the "surprise" in the measurement.
        """
        kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=60.0)

        # Build up estimate
        for _ in range(5):
            kf.update({"scheduled_hours": 65.0})

        # Get current state (before update)
        x_current = kf.x.copy()

        # Predict next state
        x_pred = kf.F @ x_current

        # New measurement
        measurement_value = 70.0

        # Expected innovation (for scheduled_hours)
        # H[0] = [1.0, 0.0, 0.0] (observes workload directly)
        expected_innovation = measurement_value - (kf.H[0] @ x_pred)

        # Update filter
        estimate = kf.update({"scheduled_hours": measurement_value})

        # Check innovation is recorded correctly
        # Note: if multiple measurements, innovation is averaged
        # With single measurement, should match our calculation
        assert estimate.measurement_residual is not None

        # Allow for small numerical differences
        assert abs(estimate.measurement_residual - expected_innovation) < 0.1, (
            f"Innovation {estimate.measurement_residual:.2f} should match "
            f"expected {expected_innovation:.2f}"
        )


@pytest.mark.integration
@pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="WorkloadKalmanFilter not yet implemented")
class TestKalmanIntegration:
    """Integration tests for complete workflows."""

    def test_realistic_workload_scenario(self):
        """
        Test realistic scenario with mixed measurements over multiple months.

        Simulates:
            - 12 weeks of realistic faculty workload
            - Variable measurement availability (sometimes missing self-reports)
            - Realistic noise levels
            - Gradual workload changes

        Validates:
            - Filter produces reasonable estimates throughout
            - Handles missing data gracefully
            - Adapts to trends
            - Maintains calibrated uncertainty
        """
        kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=65.0)

        # Simulate realistic scenario
        true_workload_pattern = [
            65, 66, 67, 68, 70, 72,  # Gradual increase (deployment season)
            73, 72, 70, 68, 66, 65,  # Gradual decrease (return to normal)
        ]

        for week, true_hours in enumerate(true_workload_pattern, 1):
            measurements = {}

            # Scheduled hours: Always available, low noise
            measurements["scheduled_hours"] = true_hours + np.random.normal(0, 0.5)

            # Self-reports: Only every other week, high noise
            if week % 2 == 0:
                measurements["self_reported"] = true_hours + np.random.normal(0, 3.0)

            # Call volume: Available 75% of time, medium noise
            if np.random.random() < 0.75:
                measurements["call_volume"] = true_hours * 0.7 + np.random.normal(0, 2.0)

            estimate = kf.update(measurements)

            # Sanity checks each week
            assert estimate.estimated_hours > 0, f"Week {week}: Estimate should be positive"
            assert estimate.uncertainty_std > 0, f"Week {week}: Uncertainty should be positive"
            assert estimate.confidence_95_lower < estimate.confidence_95_upper, (
                f"Week {week}: CI bounds should be ordered"
            )

        # Final estimate should be reasonably close to final true value
        final_true = true_workload_pattern[-1]
        final_estimate = kf.history[-1].estimated_hours

        assert abs(final_estimate - final_true) < 3.0, (
            f"Final estimate {final_estimate:.2f} should be within 3 hours of "
            f"true value {final_true}"
        )

    def test_utilization_estimate_calculation(self):
        """
        Test the utilization estimate calculation.

        Utilization = estimated_hours / target_hours

        Should provide utilization with confidence bounds.
        """
        kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=60.0)

        # Build estimate
        target_hours = 75.0
        actual_hours = 60.0  # 80% utilization

        for _ in range(10):
            kf.update({"scheduled_hours": actual_hours})

        utilization, lower, upper = kf.get_utilization_estimate(target_hours=target_hours)

        expected_utilization = actual_hours / target_hours

        assert abs(utilization - expected_utilization) < 0.05, (
            f"Utilization {utilization:.2%} should be close to {expected_utilization:.2%}"
        )

        assert lower < utilization < upper, (
            "Utilization should be within confidence bounds"
        )

        assert 0 <= lower <= 1.5, "Lower bound should be reasonable"
        assert 0 <= upper <= 1.5, "Upper bound should be reasonable"

    def test_filter_reliability_check(self):
        """
        Test the is_estimate_reliable() method.

        Estimates should be unreliable initially and become reliable
        after sufficient measurements.
        """
        kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=60.0)

        # Initially should be unreliable (high uncertainty)
        initial_reliable = kf.is_estimate_reliable(threshold_std=3.0)

        # After many measurements, should be reliable
        for _ in range(15):
            kf.update({"scheduled_hours": 65.0 + np.random.normal(0, 0.5)})

        final_reliable = kf.is_estimate_reliable(threshold_std=3.0)

        # Pattern: initially unreliable, then becomes reliable
        # (Though with default initial P, might already be reliable)
        # At minimum, uncertainty should decrease
        initial_uncertainty = kf.history[0].uncertainty_std if kf.history else 5.0
        final_uncertainty = kf.history[-1].uncertainty_std

        assert final_uncertainty < initial_uncertainty or final_reliable, (
            "Filter should become more reliable or already be reliable"
        )


@pytest.mark.integration
@pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="WorkloadKalmanFilter not yet implemented")
class TestKalmanEdgeCases:
    """Test edge cases and error handling."""

    def test_extreme_measurement_values(self):
        """
        Test filter handles extreme but valid measurements.

        E.g., very high workload (90 hours) or very low (20 hours).
        """
        kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=60.0)

        # Extreme high workload
        for _ in range(5):
            estimate = kf.update({"scheduled_hours": 90.0})

        assert 85.0 < estimate.estimated_hours < 95.0, (
            f"Should track extreme high workload: {estimate.estimated_hours:.2f}"
        )

        # Reset and test extreme low
        kf.reset(initial_hours=60.0)

        for _ in range(5):
            estimate = kf.update({"scheduled_hours": 20.0})

        assert 15.0 < estimate.estimated_hours < 25.0, (
            f"Should track extreme low workload: {estimate.estimated_hours:.2f}"
        )

    def test_single_measurement_type(self):
        """
        Test filter works with only one type of measurement.

        Common scenario: Only scheduled hours available (no surveys).
        """
        kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=60.0)

        # Only scheduled hours for 10 weeks
        for week in range(10):
            estimate = kf.update({"scheduled_hours": 68.0 + np.random.normal(0, 0.3)})

        assert abs(estimate.estimated_hours - 68.0) < 2.0, (
            "Should work with single measurement type"
        )

        assert estimate.measurements_used == ["scheduled_hours"], (
            "Should record which measurement was used"
        )

    def test_filter_reset(self):
        """
        Test filter reset functionality.

        After reset, filter should return to initial state.
        """
        kf = WorkloadKalmanFilter(person_id=uuid4(), initial_hours=60.0)

        # Build up some history
        for _ in range(10):
            kf.update({"scheduled_hours": 75.0})

        assert len(kf.history) == 10, "Should have 10 estimates"

        # Reset
        kf.reset(initial_hours=60.0)

        assert len(kf.history) == 0, "History should be cleared"
        assert abs(kf.x[0] - 60.0) < 0.01, "State should reset to initial value"

        # Should work normally after reset
        estimate = kf.update({"scheduled_hours": 70.0})
        assert estimate is not None, "Should work after reset"
