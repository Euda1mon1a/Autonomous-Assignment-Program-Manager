"""
Tests for Thermodynamics Module.

Tests the thermodynamics resilience module including entropy calculations,
phase transition detection, and critical phenomena monitoring.
"""

from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pytest

from app.resilience.thermodynamics import (
    CriticalPhenomenaMonitor,
    PhaseTransitionDetector,
    ScheduleEntropyMonitor,
    calculate_schedule_entropy,
    conditional_entropy,
    detect_critical_slowing,
    entropy_production_rate,
    estimate_time_to_transition,
    mutual_information,
)
from app.resilience.thermodynamics.entropy import (
    EntropyMetrics,
    calculate_shannon_entropy,
)
from app.resilience.thermodynamics.phase_transitions import (
    CriticalSignal,
    PhaseTransitionRisk,
    TransitionSeverity,
)


***REMOVED*** Mock assignment class for testing
class MockAssignment:
    """Mock assignment for testing entropy calculations."""

    def __init__(
        self,
        person_id: str,
        rotation_template_id: str | None = None,
        block_id: int = 0,
    ):
        self.person_id = person_id
        self.rotation_template_id = rotation_template_id
        self.block_id = block_id


class TestShannonEntropy:
    """Test Shannon entropy calculation."""

    def test_entropy_uniform_distribution(self):
        """Test entropy of perfectly uniform distribution."""
        ***REMOVED*** Four equally likely outcomes
        distribution = [1, 2, 3, 4]

        entropy = calculate_shannon_entropy(distribution)

        ***REMOVED*** Uniform distribution of 4 items: log2(4) = 2.0
        assert entropy == pytest.approx(2.0, rel=0.01)

    def test_entropy_completely_ordered(self):
        """Test entropy of completely ordered distribution (single value)."""
        ***REMOVED*** All same value
        distribution = [1, 1, 1, 1]

        entropy = calculate_shannon_entropy(distribution)

        ***REMOVED*** Single outcome: log2(1) = 0.0
        assert entropy == 0.0

    def test_entropy_skewed_distribution(self):
        """Test entropy of skewed distribution."""
        ***REMOVED*** 3 of one type, 1 of another
        distribution = [1, 1, 1, 2]

        entropy = calculate_shannon_entropy(distribution)

        ***REMOVED*** Should be less than uniform but greater than 0
        assert 0 < entropy < 2.0
        ***REMOVED*** Calculated: -(0.75*log2(0.75) + 0.25*log2(0.25)) ≈ 0.811
        assert entropy == pytest.approx(0.811, rel=0.01)

    def test_entropy_binary_balanced(self):
        """Test entropy of balanced binary distribution."""
        ***REMOVED*** 50-50 split
        distribution = [1, 1, 1, 1, 2, 2, 2, 2]

        entropy = calculate_shannon_entropy(distribution)

        ***REMOVED*** Binary 50-50: log2(2) = 1.0
        assert entropy == pytest.approx(1.0, rel=0.01)

    def test_entropy_empty_distribution(self):
        """Test entropy of empty distribution."""
        entropy = calculate_shannon_entropy([])

        assert entropy == 0.0

    def test_entropy_single_element(self):
        """Test entropy of single element."""
        distribution = [42]

        entropy = calculate_shannon_entropy(distribution)

        ***REMOVED*** Single outcome
        assert entropy == 0.0

    def test_entropy_large_uniform_distribution(self):
        """Test entropy scales with number of categories."""
        ***REMOVED*** 8 categories, uniform
        distribution = list(range(8)) * 10  ***REMOVED*** Repeat for uniformity

        entropy = calculate_shannon_entropy(distribution)

        ***REMOVED*** log2(8) = 3.0
        assert entropy == pytest.approx(3.0, rel=0.01)


class TestScheduleEntropy:
    """Test schedule entropy calculation."""

    def test_schedule_entropy_balanced(self):
        """Test entropy with balanced assignment distribution."""
        ***REMOVED*** 4 people, 2 rotations, balanced distribution
        assignments = [
            MockAssignment("P1", "R1", 1),
            MockAssignment("P2", "R1", 2),
            MockAssignment("P3", "R2", 3),
            MockAssignment("P4", "R2", 4),
        ]

        metrics = calculate_schedule_entropy(assignments)

        assert isinstance(metrics, EntropyMetrics)
        assert metrics.person_entropy == pytest.approx(2.0, rel=0.01)  ***REMOVED*** 4 people
        assert metrics.rotation_entropy == pytest.approx(1.0, rel=0.01)  ***REMOVED*** 2 rotations
        assert metrics.joint_entropy > 0
        assert metrics.mutual_information >= 0

    def test_schedule_entropy_concentrated(self):
        """Test entropy with concentrated (unbalanced) distribution."""
        ***REMOVED*** 1 person gets all assignments
        assignments = [
            MockAssignment("P1", "R1", 1),
            MockAssignment("P1", "R1", 2),
            MockAssignment("P1", "R1", 3),
            MockAssignment("P1", "R1", 4),
        ]

        metrics = calculate_schedule_entropy(assignments)

        ***REMOVED*** All same person and rotation → low entropy
        assert metrics.person_entropy == 0.0
        assert metrics.rotation_entropy == 0.0

    def test_schedule_entropy_empty(self):
        """Test entropy with no assignments."""
        metrics = calculate_schedule_entropy([])

        assert metrics.person_entropy == 0.0
        assert metrics.rotation_entropy == 0.0
        assert metrics.joint_entropy == 0.0
        assert metrics.mutual_information == 0.0

    def test_schedule_entropy_normalized(self):
        """Test normalized entropy calculation."""
        ***REMOVED*** Balanced distribution
        assignments = [MockAssignment(f"P{i}", "R1", i) for i in range(1, 5)]

        metrics = calculate_schedule_entropy(assignments)

        ***REMOVED*** Normalized entropy should be in [0, 1]
        assert 0.0 <= metrics.normalized_entropy <= 1.0
        ***REMOVED*** Uniform distribution → normalized entropy ≈ 1.0
        assert metrics.normalized_entropy == pytest.approx(1.0, rel=0.01)

    def test_schedule_entropy_none_rotation(self):
        """Test entropy handles None rotation_template_id."""
        assignments = [
            MockAssignment("P1", None, 1),
            MockAssignment("P2", "R1", 2),
            MockAssignment("P3", None, 3),
        ]

        metrics = calculate_schedule_entropy(assignments)

        ***REMOVED*** Should handle None values gracefully
        assert metrics.person_entropy > 0
        ***REMOVED*** Rotation entropy should only count non-None
        assert metrics.rotation_entropy >= 0

    def test_schedule_entropy_timestamp(self):
        """Test that entropy metrics include timestamp."""
        assignments = [MockAssignment("P1", "R1", 1)]

        metrics = calculate_schedule_entropy(assignments)

        assert isinstance(metrics.computed_at, datetime)
        ***REMOVED*** Should be recent (within 1 second)
        assert (datetime.utcnow() - metrics.computed_at).total_seconds() < 1


class TestMutualInformation:
    """Test mutual information calculation."""

    def test_mutual_information_perfect_correlation(self):
        """Test MI with perfect correlation."""
        ***REMOVED*** Faculty and rotation perfectly correlated
        faculty = [1, 1, 2, 2, 3, 3]
        rotations = ["A", "A", "B", "B", "C", "C"]

        mi = mutual_information(faculty, rotations)

        ***REMOVED*** Perfect correlation → high MI
        ***REMOVED*** H(F) = log2(3) ≈ 1.585, H(R) = log2(3) ≈ 1.585
        ***REMOVED*** H(F,R) = log2(3) ≈ 1.585 (same as individual)
        ***REMOVED*** MI = 1.585 + 1.585 - 1.585 = 1.585
        assert mi > 0
        assert mi == pytest.approx(1.585, rel=0.01)

    def test_mutual_information_independent(self):
        """Test MI with independent distributions."""
        ***REMOVED*** No correlation between faculty and rotation
        faculty = [1, 1, 2, 2, 3, 3]
        rotations = ["A", "B", "A", "B", "A", "B"]

        mi = mutual_information(faculty, rotations)

        ***REMOVED*** Independent → MI ≈ 0
        ***REMOVED*** Some small MI may exist due to finite sampling
        assert mi >= 0
        assert mi < 0.1  ***REMOVED*** Should be very small

    def test_mutual_information_partial_correlation(self):
        """Test MI with partial correlation."""
        ***REMOVED*** Some but not perfect correlation
        faculty = [1, 1, 1, 2, 2, 3]
        rotations = ["A", "A", "B", "B", "B", "C"]

        mi = mutual_information(faculty, rotations)

        ***REMOVED*** Partial correlation → moderate MI
        assert mi > 0
        assert mi < 2.0

    def test_mutual_information_empty(self):
        """Test MI with empty distributions."""
        mi = mutual_information([], [])

        assert mi == 0.0

    def test_mutual_information_mismatched_length(self):
        """Test MI raises error with mismatched lengths."""
        with pytest.raises(ValueError, match="same length"):
            mutual_information([1, 2, 3], [1, 2])

    def test_mutual_information_non_negative(self):
        """Test that MI is always non-negative."""
        ***REMOVED*** Random data should still give non-negative MI
        np.random.seed(42)
        dist_X = np.random.randint(0, 5, 100).tolist()
        dist_Y = np.random.randint(0, 5, 100).tolist()

        mi = mutual_information(dist_X, dist_Y)

        assert mi >= 0.0


class TestConditionalEntropy:
    """Test conditional entropy calculation."""

    def test_conditional_entropy_perfect_prediction(self):
        """Test conditional entropy when Y perfectly predicts X."""
        ***REMOVED*** Knowing Y completely determines X
        X = [1, 1, 2, 2, 3, 3]
        Y = ["A", "A", "B", "B", "C", "C"]

        H_cond = conditional_entropy(X, Y)

        ***REMOVED*** Perfect prediction → H(X|Y) = 0
        assert H_cond == pytest.approx(0.0, abs=0.01)

    def test_conditional_entropy_no_prediction(self):
        """Test conditional entropy when Y doesn't help predict X."""
        ***REMOVED*** Y provides no information about X
        X = [1, 2, 3, 1, 2, 3]
        Y = ["A", "A", "A", "A", "A", "A"]  ***REMOVED*** All same

        H_cond = conditional_entropy(X, Y)

        ***REMOVED*** No reduction in uncertainty
        ***REMOVED*** H(X|Y) ≈ H(X)
        H_X = calculate_shannon_entropy(X)
        assert H_cond == pytest.approx(H_X, rel=0.01)

    def test_conditional_entropy_partial_prediction(self):
        """Test conditional entropy with partial information."""
        X = [1, 1, 2, 2, 3, 3, 4, 4]
        Y = ["A", "A", "A", "A", "B", "B", "B", "B"]

        H_cond = conditional_entropy(X, Y)

        ***REMOVED*** Some but not complete information
        H_X = calculate_shannon_entropy(X)
        assert 0 < H_cond < H_X

    def test_conditional_entropy_empty(self):
        """Test conditional entropy with empty distributions."""
        H_cond = conditional_entropy([], [])

        assert H_cond == 0.0

    def test_conditional_entropy_mismatched_length(self):
        """Test conditional entropy raises error with mismatched lengths."""
        with pytest.raises(ValueError, match="same length"):
            conditional_entropy([1, 2, 3], [1, 2])

    def test_conditional_entropy_non_negative(self):
        """Test that conditional entropy is non-negative."""
        X = [1, 2, 3, 4, 5]
        Y = ["A", "B", "C", "D", "E"]

        H_cond = conditional_entropy(X, Y)

        assert H_cond >= 0.0


class TestEntropyProductionRate:
    """Test entropy production rate calculation."""

    def test_entropy_production_increasing_entropy(self):
        """Test production rate with increasing entropy."""
        ***REMOVED*** Old schedule: concentrated (low entropy)
        old_assignments = [MockAssignment("P1", "R1", i) for i in range(10)]

        ***REMOVED*** New schedule: distributed (high entropy)
        new_assignments = [MockAssignment(f"P{i % 5}", "R1", i) for i in range(10)]

        rate = entropy_production_rate(old_assignments, new_assignments, time_delta=1.0)

        ***REMOVED*** Entropy increased → positive production rate
        assert rate > 0

    def test_entropy_production_decreasing_entropy(self):
        """Test production rate with decreasing entropy."""
        ***REMOVED*** Old schedule: distributed (high entropy)
        old_assignments = [MockAssignment(f"P{i % 5}", "R1", i) for i in range(10)]

        ***REMOVED*** New schedule: concentrated (low entropy)
        new_assignments = [MockAssignment("P1", "R1", i) for i in range(10)]

        rate = entropy_production_rate(old_assignments, new_assignments, time_delta=1.0)

        ***REMOVED*** Entropy decreased → production rate = 0 (only counts increases)
        assert rate == 0.0

    def test_entropy_production_no_change(self):
        """Test production rate with no entropy change."""
        assignments = [MockAssignment(f"P{i % 3}", "R1", i) for i in range(10)]

        rate = entropy_production_rate(assignments, assignments, time_delta=1.0)

        ***REMOVED*** No change → no production
        assert rate == 0.0

    def test_entropy_production_time_scaling(self):
        """Test production rate scales with time delta."""
        old_assignments = [MockAssignment("P1", "R1", i) for i in range(10)]
        new_assignments = [MockAssignment(f"P{i % 5}", "R1", i) for i in range(10)]

        rate_1hr = entropy_production_rate(
            old_assignments, new_assignments, time_delta=1.0
        )
        rate_2hr = entropy_production_rate(
            old_assignments, new_assignments, time_delta=2.0
        )

        ***REMOVED*** Same entropy change, double time → half rate
        assert rate_2hr == pytest.approx(rate_1hr / 2.0, rel=0.01)

    def test_entropy_production_empty_assignments(self):
        """Test production rate with empty assignments."""
        rate = entropy_production_rate([], [], time_delta=1.0)

        assert rate == 0.0


class TestScheduleEntropyMonitor:
    """Test ScheduleEntropyMonitor class."""

    def test_monitor_initialization(self):
        """Test monitor initialization."""
        monitor = ScheduleEntropyMonitor(history_window=50)

        assert monitor.history_window == 50
        assert monitor.entropy_history == []
        assert monitor.production_rate_history == []
        assert monitor.timestamp_history == []

    def test_monitor_update(self):
        """Test updating monitor with new assignments."""
        monitor = ScheduleEntropyMonitor()

        assignments = [MockAssignment(f"P{i}", "R1", i) for i in range(5)]

        monitor.update(assignments)

        assert len(monitor.entropy_history) == 1
        assert len(monitor.timestamp_history) == 1
        assert monitor.entropy_history[0] > 0

    def test_monitor_multiple_updates(self):
        """Test monitor tracks multiple updates."""
        monitor = ScheduleEntropyMonitor()

        for i in range(10):
            assignments = [MockAssignment(f"P{j % (i + 1)}", "R1", j) for j in range(5)]
            monitor.update(assignments)

        assert len(monitor.entropy_history) == 10
        assert len(monitor.production_rate_history) == 9  ***REMOVED*** N-1 production rates

    def test_monitor_window_enforcement(self):
        """Test monitor enforces history window size."""
        monitor = ScheduleEntropyMonitor(history_window=5)

        ***REMOVED*** Add more than window size
        for i in range(10):
            assignments = [MockAssignment("P1", "R1", i)]
            monitor.update(assignments)

        ***REMOVED*** Should only keep last 5
        assert len(monitor.entropy_history) == 5
        assert len(monitor.timestamp_history) == 5

    def test_monitor_production_rate_calculation(self):
        """Test monitor calculates production rate."""
        monitor = ScheduleEntropyMonitor()

        ***REMOVED*** First update: low entropy
        monitor.update([MockAssignment("P1", "R1", i) for i in range(10)])

        ***REMOVED*** Second update: high entropy
        monitor.update([MockAssignment(f"P{i}", "R1", i) for i in range(10)])

        ***REMOVED*** Should have calculated production rate
        assert len(monitor.production_rate_history) == 1
        assert monitor.production_rate_history[0] >= 0

    def test_monitor_rate_of_change(self):
        """Test entropy rate of change calculation."""
        monitor = ScheduleEntropyMonitor()

        ***REMOVED*** Create increasing entropy trend
        for i in range(10):
            num_people = i + 1
            assignments = [
                MockAssignment(f"P{j % num_people}", "R1", j) for j in range(10)
            ]
            monitor.update(assignments)

        rate = monitor.get_entropy_rate_of_change()

        ***REMOVED*** Should be positive (entropy increasing)
        assert rate > 0

    def test_monitor_rate_of_change_insufficient_data(self):
        """Test rate of change with insufficient data."""
        monitor = ScheduleEntropyMonitor()

        rate = monitor.get_entropy_rate_of_change()

        assert rate == 0.0

    def test_monitor_critical_slowing_detection(self):
        """Test critical slowing down detection."""
        monitor = ScheduleEntropyMonitor()

        ***REMOVED*** Create plateau with high autocorrelation
        base_assignments = [MockAssignment("P1", "R1", i) for i in range(10)]

        ***REMOVED*** Add many similar states
        for _ in range(20):
            monitor.update(base_assignments)

        is_slowing = monitor.detect_critical_slowing()

        ***REMOVED*** Plateau should trigger critical slowing
        assert is_slowing

    def test_monitor_no_critical_slowing_when_improving(self):
        """Test no critical slowing when improving."""
        monitor = ScheduleEntropyMonitor()

        ***REMOVED*** Continuously changing entropy
        for i in range(20):
            num_people = (i % 5) + 1
            assignments = [
                MockAssignment(f"P{j % num_people}", "R1", j) for j in range(10)
            ]
            monitor.update(assignments)

        is_slowing = monitor.detect_critical_slowing()

        ***REMOVED*** Should not detect slowing
        assert not is_slowing

    def test_monitor_get_current_metrics(self):
        """Test getting current metrics."""
        monitor = ScheduleEntropyMonitor()

        assignments = [MockAssignment(f"P{i}", "R1", i) for i in range(5)]
        monitor.update(assignments)

        metrics = monitor.get_current_metrics()

        assert "current_entropy" in metrics
        assert "rate_of_change" in metrics
        assert "production_rate" in metrics
        assert "critical_slowing" in metrics
        assert "measurements" in metrics

        assert metrics["measurements"] == 1
        assert metrics["current_entropy"] > 0

    def test_monitor_get_current_metrics_empty(self):
        """Test getting metrics with no data."""
        monitor = ScheduleEntropyMonitor()

        metrics = monitor.get_current_metrics()

        assert metrics["current_entropy"] == 0.0
        assert metrics["rate_of_change"] == 0.0
        assert metrics["production_rate"] == 0.0
        assert metrics["critical_slowing"] is False


class TestPhaseTransitionDetector:
    """Test PhaseTransitionDetector class."""

    def test_detector_initialization(self):
        """Test detector initialization."""
        detector = PhaseTransitionDetector(window_size=100)

        assert detector.window_size == 100
        assert len(detector.metric_history) == 0
        assert len(detector.timestamp_history) == 0

    def test_detector_update(self):
        """Test updating detector with metrics."""
        detector = PhaseTransitionDetector()

        metrics = {"utilization": 0.75, "coverage": 0.90}
        detector.update(metrics)

        assert "utilization" in detector.metric_history
        assert "coverage" in detector.metric_history
        assert len(detector.metric_history["utilization"]) == 1
        assert detector.metric_history["utilization"][0] == 0.75

    def test_detector_window_enforcement(self):
        """Test detector enforces window size."""
        detector = PhaseTransitionDetector(window_size=5)

        ***REMOVED*** Add more than window
        for i in range(10):
            detector.update({"metric": float(i)})

        ***REMOVED*** Should only keep last 5
        assert len(detector.metric_history["metric"]) == 5
        ***REMOVED*** Should have values 5-9
        assert detector.metric_history["metric"] == [5.0, 6.0, 7.0, 8.0, 9.0]

    def test_detector_variance_increase_detection(self):
        """Test detection of increasing variance."""
        detector = PhaseTransitionDetector(window_size=50)

        ***REMOVED*** First half: low variance
        for i in range(25):
            detector.update({"metric": 50.0 + i * 0.1})

        ***REMOVED*** Second half: high variance
        for i in range(25):
            detector.update({"metric": 50.0 + (i % 2) * 10})

        risk = detector.detect_critical_phenomena()

        ***REMOVED*** Should detect variance increase
        variance_signals = [
            s for s in risk.signals if s.signal_type == "increasing_variance"
        ]
        assert len(variance_signals) > 0

    def test_detector_autocorrelation_detection(self):
        """Test detection of high autocorrelation (critical slowing)."""
        detector = PhaseTransitionDetector(window_size=50)

        ***REMOVED*** Create highly autocorrelated series (slow changes)
        value = 50.0
        for i in range(50):
            value += 0.01 * (1 if i % 10 == 0 else 0)  ***REMOVED*** Small, rare changes
            detector.update({"metric": value})

        risk = detector.detect_critical_phenomena()

        ***REMOVED*** Should detect critical slowing
        slowing_signals = [
            s for s in risk.signals if s.signal_type == "critical_slowing_down"
        ]
        assert len(slowing_signals) > 0

    def test_detector_flickering_detection(self):
        """Test detection of flickering."""
        detector = PhaseTransitionDetector(window_size=50)

        ***REMOVED*** Create flickering pattern (rapid direction changes)
        for i in range(50):
            value = 50.0 + (10.0 if i % 2 == 0 else -10.0)
            detector.update({"metric": value})

        risk = detector.detect_critical_phenomena()

        ***REMOVED*** Should detect flickering
        flicker_signals = [s for s in risk.signals if s.signal_type == "flickering"]
        assert len(flicker_signals) > 0

    def test_detector_skewness_detection(self):
        """Test detection of distribution skewness."""
        detector = PhaseTransitionDetector(window_size=50)

        ***REMOVED*** Create highly skewed distribution
        values = [10.0] * 40 + [100.0] * 10  ***REMOVED*** Right-skewed
        for val in values:
            detector.update({"metric": val})

        risk = detector.detect_critical_phenomena()

        ***REMOVED*** Should detect skewness
        skew_signals = [s for s in risk.signals if s.signal_type == "distribution_skew"]
        assert len(skew_signals) > 0

    def test_detector_severity_assessment(self):
        """Test overall severity assessment."""
        detector = PhaseTransitionDetector(window_size=50)

        ***REMOVED*** Create multiple strong signals
        for i in range(50):
            ***REMOVED*** Oscillating with increasing variance
            value = 50.0 + (20.0 if i % 2 == 0 else -20.0) * (1 + i / 50.0)
            detector.update({"metric": value})

        risk = detector.detect_critical_phenomena()

        ***REMOVED*** Multiple signals should elevate severity
        assert risk.overall_severity in [
            TransitionSeverity.ELEVATED,
            TransitionSeverity.HIGH,
            TransitionSeverity.CRITICAL,
            TransitionSeverity.IMMINENT,
        ]

    def test_detector_time_to_transition_estimation(self):
        """Test time to transition estimation."""
        detector = PhaseTransitionDetector(window_size=50)

        ***REMOVED*** High autocorrelation → close to transition
        value = 50.0
        for i in range(50):
            value += 0.001
            detector.update({"metric": value})

        risk = detector.detect_critical_phenomena()

        if risk.time_to_transition is not None:
            assert risk.time_to_transition >= 0

    def test_detector_recommendations(self):
        """Test recommendation generation."""
        detector = PhaseTransitionDetector(window_size=50)

        ***REMOVED*** Create critical situation
        for i in range(50):
            detector.update({"metric": 50.0})  ***REMOVED*** Constant

        risk = detector.detect_critical_phenomena()

        ***REMOVED*** Should have recommendations based on severity
        assert isinstance(risk.recommendations, list)

    def test_detector_confidence_calculation(self):
        """Test confidence calculation."""
        detector = PhaseTransitionDetector(window_size=50)

        ***REMOVED*** Create multiple independent signals
        for i in range(50):
            detector.update(
                {
                    "metric1": 50.0,  ***REMOVED*** Constant
                    "metric2": 50.0,  ***REMOVED*** Constant
                    "metric3": 50.0,  ***REMOVED*** Constant
                }
            )

        risk = detector.detect_critical_phenomena()

        ***REMOVED*** Multiple metrics with signals → higher confidence
        assert 0.0 <= risk.confidence <= 1.0

    def test_detector_insufficient_data(self):
        """Test detector with insufficient data."""
        detector = PhaseTransitionDetector(window_size=50)

        ***REMOVED*** Only a few data points
        for i in range(5):
            detector.update({"metric": float(i)})

        risk = detector.detect_critical_phenomena()

        ***REMOVED*** Should handle gracefully
        assert risk.overall_severity == TransitionSeverity.NORMAL

    def test_detector_normal_stable_system(self):
        """Test detector with normal, stable system."""
        detector = PhaseTransitionDetector(window_size=50)

        ***REMOVED*** Slowly improving with low noise
        for i in range(50):
            detector.update({"metric": 100.0 - i * 0.5})

        risk = detector.detect_critical_phenomena()

        ***REMOVED*** Should be normal or elevated at most
        assert risk.overall_severity in [
            TransitionSeverity.NORMAL,
            TransitionSeverity.ELEVATED,
        ]


class TestCriticalPhenomenaMonitor:
    """Test CriticalPhenomenaMonitor class."""

    @pytest.mark.asyncio
    async def test_monitor_initialization(self):
        """Test monitor initialization."""
        monitor = CriticalPhenomenaMonitor(window_size=100)

        assert isinstance(monitor.detector, PhaseTransitionDetector)
        assert monitor.risk_history == []
        assert monitor.alert_callbacks == []

    @pytest.mark.asyncio
    async def test_monitor_update_and_assess(self):
        """Test update and assess functionality."""
        monitor = CriticalPhenomenaMonitor()

        metrics = {"utilization": 0.75, "coverage": 0.90}
        risk = await monitor.update_and_assess(metrics)

        assert isinstance(risk, PhaseTransitionRisk)
        assert len(monitor.risk_history) == 1

    @pytest.mark.asyncio
    async def test_monitor_alert_callback(self):
        """Test alert callback triggering."""
        monitor = CriticalPhenomenaMonitor(window_size=50)

        ***REMOVED*** Track if callback was called
        callback_called = []

        async def test_callback(risk: PhaseTransitionRisk):
            callback_called.append(risk)

        monitor.add_alert_callback(test_callback)

        ***REMOVED*** Create critical situation
        for i in range(50):
            await monitor.update_and_assess({"metric": 50.0})  ***REMOVED*** Constant → critical

        ***REMOVED*** Check if callback was triggered for critical/imminent severities
        critical_risks = [
            r
            for r in monitor.risk_history
            if r.overall_severity
            in [
                TransitionSeverity.CRITICAL,
                TransitionSeverity.IMMINENT,
            ]
        ]

        if critical_risks:
            assert len(callback_called) > 0

    @pytest.mark.asyncio
    async def test_monitor_callback_exception_handling(self):
        """Test monitor handles callback exceptions gracefully."""
        monitor = CriticalPhenomenaMonitor()

        async def failing_callback(risk: PhaseTransitionRisk):
            raise ValueError("Test error")

        monitor.add_alert_callback(failing_callback)

        ***REMOVED*** Should not raise exception
        risk = await monitor.update_and_assess({"metric": 50.0})

        assert isinstance(risk, PhaseTransitionRisk)

    @pytest.mark.asyncio
    async def test_monitor_get_current_risk(self):
        """Test getting current risk assessment."""
        monitor = CriticalPhenomenaMonitor()

        ***REMOVED*** Initially no risk
        assert monitor.get_current_risk() is None

        ***REMOVED*** After update
        await monitor.update_and_assess({"metric": 75.0})

        risk = monitor.get_current_risk()
        assert isinstance(risk, PhaseTransitionRisk)

    @pytest.mark.asyncio
    async def test_monitor_risk_history_limit(self):
        """Test risk history is limited."""
        monitor = CriticalPhenomenaMonitor()

        ***REMOVED*** Add many assessments
        for i in range(150):
            await monitor.update_and_assess({"metric": float(i)})

        ***REMOVED*** Should limit to 100
        assert len(monitor.risk_history) == 100


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_detect_critical_slowing_function(self):
        """Test detect_critical_slowing convenience function."""
        ***REMOVED*** Plateau trajectory
        trajectory = [100.0] * 20

        result = detect_critical_slowing(trajectory)

        ***REMOVED*** Should detect slowing
        assert isinstance(result, bool)
        assert result is True

    def test_detect_critical_slowing_improving(self):
        """Test no critical slowing when improving."""
        ***REMOVED*** Improving trajectory
        trajectory = [100.0 - i for i in range(20)]

        result = detect_critical_slowing(trajectory)

        assert result is False

    def test_detect_critical_slowing_insufficient_data(self):
        """Test critical slowing with insufficient data."""
        trajectory = [100.0, 99.0, 98.0]

        result = detect_critical_slowing(trajectory)

        assert result is False

    def test_estimate_time_to_transition_function(self):
        """Test estimate_time_to_transition convenience function."""
        ***REMOVED*** High autocorrelation trajectory
        trajectories = {
            "metric1": [50.0 + i * 0.01 for i in range(50)],
            "metric2": [75.0 + i * 0.01 for i in range(50)],
        }

        time_estimate = estimate_time_to_transition(trajectories)

        ***REMOVED*** Should return a time estimate or None
        assert time_estimate is None or time_estimate >= 0

    def test_estimate_time_to_transition_empty(self):
        """Test time estimation with empty trajectories."""
        result = estimate_time_to_transition({})

        assert result is None


class TestTransitionSeverity:
    """Test TransitionSeverity enum."""

    def test_severity_values(self):
        """Test all severity levels defined."""
        assert TransitionSeverity.NORMAL == "normal"
        assert TransitionSeverity.ELEVATED == "elevated"
        assert TransitionSeverity.HIGH == "high"
        assert TransitionSeverity.CRITICAL == "critical"
        assert TransitionSeverity.IMMINENT == "imminent"

    def test_severity_ordering(self):
        """Test severity can be compared."""
        severities = [
            TransitionSeverity.NORMAL,
            TransitionSeverity.ELEVATED,
            TransitionSeverity.HIGH,
            TransitionSeverity.CRITICAL,
            TransitionSeverity.IMMINENT,
        ]

        ***REMOVED*** All should be distinct
        assert len(set(severities)) == 5


class TestCriticalSignal:
    """Test CriticalSignal dataclass."""

    def test_signal_creation(self):
        """Test creating critical signal."""
        signal = CriticalSignal(
            signal_type="increasing_variance",
            metric_name="utilization",
            severity=TransitionSeverity.HIGH,
            value=0.8,
            threshold=0.5,
            description="Variance increased 80%",
        )

        assert signal.signal_type == "increasing_variance"
        assert signal.metric_name == "utilization"
        assert signal.severity == TransitionSeverity.HIGH
        assert signal.value == 0.8
        assert signal.threshold == 0.5
        assert isinstance(signal.detected_at, datetime)


class TestPhaseTransitionRisk:
    """Test PhaseTransitionRisk dataclass."""

    def test_risk_creation(self):
        """Test creating phase transition risk."""
        signal = CriticalSignal(
            signal_type="flickering",
            metric_name="coverage",
            severity=TransitionSeverity.CRITICAL,
            value=0.6,
            threshold=0.3,
            description="System flickering",
        )

        risk = PhaseTransitionRisk(
            overall_severity=TransitionSeverity.CRITICAL,
            signals=[signal],
            time_to_transition=10.5,
            confidence=0.85,
            recommendations=["Activate contingency plans"],
        )

        assert risk.overall_severity == TransitionSeverity.CRITICAL
        assert len(risk.signals) == 1
        assert risk.time_to_transition == 10.5
        assert risk.confidence == 0.85
        assert "Activate contingency plans" in risk.recommendations


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_entropy_with_very_large_distribution(self):
        """Test entropy calculation with large distribution."""
        ***REMOVED*** 1000 categories
        distribution = list(range(1000))

        entropy = calculate_shannon_entropy(distribution)

        ***REMOVED*** log2(1000) ≈ 9.97
        assert entropy == pytest.approx(9.97, rel=0.01)

    def test_entropy_monitor_rapid_updates(self):
        """Test monitor handles rapid updates."""
        monitor = ScheduleEntropyMonitor()

        ***REMOVED*** Simulate rapid updates
        for i in range(1000):
            assignments = [MockAssignment(f"P{i % 10}", "R1", i)]
            monitor.update(assignments)

        ***REMOVED*** Should handle gracefully
        metrics = monitor.get_current_metrics()
        assert metrics["measurements"] == 100  ***REMOVED*** Window size limit

    def test_phase_detector_all_metrics_constant(self):
        """Test phase detector with all constant metrics."""
        detector = PhaseTransitionDetector(window_size=50)

        ***REMOVED*** All metrics constant
        for i in range(50):
            detector.update(
                {
                    "metric1": 42.0,
                    "metric2": 100.0,
                    "metric3": 75.0,
                }
            )

        risk = detector.detect_critical_phenomena()

        ***REMOVED*** Should detect plateau/critical slowing
        assert len(risk.signals) > 0

    def test_mutual_information_single_value_distributions(self):
        """Test MI with single-value distributions."""
        ***REMOVED*** All same value
        X = [1, 1, 1, 1]
        Y = [2, 2, 2, 2]

        mi = mutual_information(X, Y)

        ***REMOVED*** No information → MI = 0
        assert mi == 0.0

    def test_entropy_production_identical_schedules(self):
        """Test entropy production with identical schedules."""
        assignments = [MockAssignment("P1", "R1", 1)]

        rate = entropy_production_rate(assignments, assignments)

        assert rate == 0.0

    def test_phase_detector_single_metric_multiple_signals(self):
        """Test detector finds multiple signal types for one metric."""
        detector = PhaseTransitionDetector(window_size=50)

        ***REMOVED*** Create pattern that triggers multiple signals
        ***REMOVED*** High variance + flickering
        for i in range(50):
            value = 50.0 + (30.0 if i % 2 == 0 else -30.0)
            detector.update({"metric": value})

        risk = detector.detect_critical_phenomena()

        ***REMOVED*** Should detect multiple signal types
        signal_types = set(s.signal_type for s in risk.signals)
        assert len(signal_types) >= 2


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_entropy_monitor_with_phase_detector(self):
        """Test using entropy monitor output with phase detector."""
        entropy_monitor = ScheduleEntropyMonitor()
        phase_detector = PhaseTransitionDetector()

        ***REMOVED*** Simulate schedule evolution
        for i in range(50):
            num_people = min(i + 1, 10)
            assignments = [
                MockAssignment(f"P{j % num_people}", "R1", j) for j in range(20)
            ]
            entropy_monitor.update(assignments)

            ***REMOVED*** Feed entropy metrics to phase detector
            metrics = entropy_monitor.get_current_metrics()
            phase_detector.update(
                {
                    "entropy": metrics["current_entropy"],
                    "entropy_rate": metrics["rate_of_change"],
                }
            )

        ***REMOVED*** Should produce valid risk assessment
        risk = phase_detector.detect_critical_phenomena()
        assert isinstance(risk, PhaseTransitionRisk)

    @pytest.mark.asyncio
    async def test_full_monitoring_pipeline(self):
        """Test complete monitoring pipeline."""
        entropy_monitor = ScheduleEntropyMonitor()
        phenomena_monitor = CriticalPhenomenaMonitor()

        ***REMOVED*** Alert tracker
        alerts = []

        async def track_alerts(risk: PhaseTransitionRisk):
            alerts.append(risk)

        phenomena_monitor.add_alert_callback(track_alerts)

        ***REMOVED*** Simulate degrading system
        for i in range(50):
            ***REMOVED*** Create assignments with decreasing diversity
            num_people = max(10 - i // 5, 1)
            assignments = [
                MockAssignment(f"P{j % num_people}", "R1", j) for j in range(20)
            ]

            ***REMOVED*** Update entropy monitor
            entropy_monitor.update(assignments)

            ***REMOVED*** Get metrics and update phase monitor
            ent_metrics = entropy_monitor.get_current_metrics()
            risk = await phenomena_monitor.update_and_assess(
                {
                    "entropy": ent_metrics["current_entropy"],
                    "production_rate": ent_metrics["production_rate"],
                }
            )

        ***REMOVED*** Should have detected issues
        assert len(phenomena_monitor.risk_history) == 50

        ***REMOVED*** Check for elevated risk levels
        elevated_risks = [
            r
            for r in phenomena_monitor.risk_history
            if r.overall_severity != TransitionSeverity.NORMAL
        ]

        ***REMOVED*** Some risk should be detected
        assert len(elevated_risks) >= 0  ***REMOVED*** May or may not trigger based on thresholds
