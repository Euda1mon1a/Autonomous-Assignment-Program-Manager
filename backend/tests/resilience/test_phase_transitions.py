"""Tests for phase transition detection (pure logic, no DB)."""

import numpy as np
import pytest

from app.resilience.thermodynamics.phase_transitions import (
    CriticalSignal,
    PhaseTransitionDetector,
    PhaseTransitionRisk,
    TransitionSeverity,
    detect_critical_slowing,
    estimate_time_to_transition,
)


# ── TransitionSeverity enum ──────────────────────────────────────────────


class TestTransitionSeverity:
    def test_normal_value(self):
        assert TransitionSeverity.NORMAL.value == "normal"

    def test_elevated_value(self):
        assert TransitionSeverity.ELEVATED.value == "elevated"

    def test_high_value(self):
        assert TransitionSeverity.HIGH.value == "high"

    def test_critical_value(self):
        assert TransitionSeverity.CRITICAL.value == "critical"

    def test_imminent_value(self):
        assert TransitionSeverity.IMMINENT.value == "imminent"

    def test_member_count(self):
        assert len(TransitionSeverity) == 5

    def test_is_str_enum(self):
        assert isinstance(TransitionSeverity.NORMAL, str)


# ── CriticalSignal dataclass ─────────────────────────────────────────────


class TestCriticalSignal:
    def test_creation(self):
        signal = CriticalSignal(
            signal_type="increasing_variance",
            metric_name="utilization",
            severity=TransitionSeverity.HIGH,
            value=0.75,
            threshold=0.5,
            description="Test signal",
        )
        assert signal.signal_type == "increasing_variance"
        assert signal.metric_name == "utilization"
        assert signal.severity == TransitionSeverity.HIGH
        assert signal.value == 0.75
        assert signal.threshold == 0.5

    def test_detected_at_auto_set(self):
        signal = CriticalSignal(
            signal_type="test",
            metric_name="m",
            severity=TransitionSeverity.NORMAL,
            value=0.0,
            threshold=0.0,
            description="test",
        )
        assert signal.detected_at is not None


# ── PhaseTransitionRisk dataclass ─────────────────────────────────────────


class TestPhaseTransitionRisk:
    def test_creation(self):
        risk = PhaseTransitionRisk(
            overall_severity=TransitionSeverity.NORMAL,
            signals=[],
        )
        assert risk.overall_severity == TransitionSeverity.NORMAL
        assert risk.signals == []
        assert risk.time_to_transition is None
        assert risk.confidence == 0.0
        assert risk.recommendations == []

    def test_with_signals(self):
        signal = CriticalSignal(
            signal_type="test",
            metric_name="m",
            severity=TransitionSeverity.HIGH,
            value=0.8,
            threshold=0.5,
            description="desc",
        )
        risk = PhaseTransitionRisk(
            overall_severity=TransitionSeverity.HIGH,
            signals=[signal],
            time_to_transition=24.0,
            confidence=0.6,
        )
        assert len(risk.signals) == 1
        assert risk.time_to_transition == 24.0
        assert risk.confidence == 0.6


# ── PhaseTransitionDetector.__init__ and update ───────────────────────────


class TestDetectorInit:
    def test_default_window_size(self):
        d = PhaseTransitionDetector()
        assert d.window_size == 50

    def test_custom_window_size(self):
        d = PhaseTransitionDetector(window_size=100)
        assert d.window_size == 100

    def test_empty_histories(self):
        d = PhaseTransitionDetector()
        assert len(d.metric_history) == 0
        assert len(d.timestamp_history) == 0


class TestDetectorUpdate:
    def test_single_update(self):
        d = PhaseTransitionDetector()
        d.update({"cpu": 0.5, "mem": 0.3})
        assert len(d.metric_history["cpu"]) == 1
        assert len(d.metric_history["mem"]) == 1
        assert d.metric_history["cpu"][0] == 0.5

    def test_multiple_updates(self):
        d = PhaseTransitionDetector()
        for i in range(5):
            d.update({"m": float(i)})
        assert d.metric_history["m"] == [0.0, 1.0, 2.0, 3.0, 4.0]

    def test_window_size_maintained(self):
        d = PhaseTransitionDetector(window_size=3)
        for i in range(5):
            d.update({"m": float(i)})
        assert len(d.metric_history["m"]) == 3
        assert d.metric_history["m"] == [2.0, 3.0, 4.0]

    def test_timestamps_maintained(self):
        d = PhaseTransitionDetector(window_size=3)
        for i in range(5):
            d.update({"m": float(i)})
        assert len(d.timestamp_history["m"]) == 3


# ── _autocorrelation ──────────────────────────────────────────────────────


class TestAutocorrelation:
    def test_too_few_values(self):
        d = PhaseTransitionDetector()
        assert d._autocorrelation([1.0], lag=1) == 0.0

    def test_constant_series(self):
        d = PhaseTransitionDetector()
        assert d._autocorrelation([5.0, 5.0, 5.0, 5.0], lag=1) == 0.0

    def test_increasing_series_positive(self):
        d = PhaseTransitionDetector()
        values = list(np.arange(1.0, 20.0))
        result = d._autocorrelation(values, lag=1)
        assert result > 0.5

    def test_alternating_series_negative(self):
        d = PhaseTransitionDetector()
        values = [1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0]
        result = d._autocorrelation(values, lag=1)
        assert result < 0.0

    def test_lag_2(self):
        d = PhaseTransitionDetector()
        values = list(np.arange(1.0, 20.0))
        result = d._autocorrelation(values, lag=2)
        assert result > 0.0

    def test_returns_float(self):
        d = PhaseTransitionDetector()
        result = d._autocorrelation([1.0, 2.0, 3.0, 4.0, 5.0], lag=1)
        assert isinstance(float(result), float)


# ── _calculate_flicker_rate ───────────────────────────────────────────────


class TestCalculateFlickerRate:
    def test_too_few_values(self):
        d = PhaseTransitionDetector()
        assert d._calculate_flicker_rate([1.0, 2.0]) == 0.0

    def test_monotonic_no_flickering(self):
        d = PhaseTransitionDetector()
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert d._calculate_flicker_rate(values) == 0.0

    def test_high_flickering(self):
        """Rapidly alternating values should show high flicker rate."""
        d = PhaseTransitionDetector()
        values = [0.0, 10.0, 0.0, 10.0, 0.0, 10.0, 0.0]
        rate = d._calculate_flicker_rate(values)
        assert rate > 0.3

    def test_constant_series(self):
        d = PhaseTransitionDetector()
        values = [5.0, 5.0, 5.0, 5.0, 5.0]
        assert d._calculate_flicker_rate(values) == 0.0

    def test_returns_between_0_and_1(self):
        d = PhaseTransitionDetector()
        values = [0.0, 10.0, 0.0, 10.0, 0.0, 10.0]
        rate = d._calculate_flicker_rate(values)
        assert 0.0 <= rate <= 1.0


# ── _detect_variance_trend ────────────────────────────────────────────────


class TestDetectVarianceTrend:
    def test_insufficient_data(self):
        d = PhaseTransitionDetector()
        assert d._detect_variance_trend("m", list(range(10))) is None

    def test_constant_data_no_signal(self):
        d = PhaseTransitionDetector()
        values = [5.0] * 30
        assert d._detect_variance_trend("m", values) is None

    def test_increasing_variance_detected(self):
        """Early half low variance, recent half high variance."""
        d = PhaseTransitionDetector()
        # Early: small fluctuations around 5.0 (non-zero variance)
        early = [
            4.9,
            5.1,
            4.9,
            5.1,
            4.9,
            5.1,
            4.9,
            5.1,
            4.9,
            5.1,
            4.9,
            5.1,
            4.9,
            5.1,
            4.9,
        ]
        # Recent: large fluctuations (much higher variance)
        recent = [
            0.0,
            10.0,
            0.0,
            10.0,
            0.0,
            10.0,
            0.0,
            10.0,
            0.0,
            10.0,
            0.0,
            10.0,
            0.0,
            10.0,
            0.0,
        ]
        values = early + recent
        signal = d._detect_variance_trend("m", values)
        assert signal is not None
        assert signal.signal_type == "increasing_variance"

    def test_critical_severity_for_large_increase(self):
        """Over 100% variance increase should be CRITICAL."""
        d = PhaseTransitionDetector()
        # Early half: low variance; recent half: very high variance
        early = [5.0, 5.1, 4.9, 5.0, 5.1, 4.9, 5.0, 5.1, 4.9, 5.0]
        recent = [0.0, 20.0, 0.0, 20.0, 0.0, 20.0, 0.0, 20.0, 0.0, 20.0]
        values = early + recent
        signal = d._detect_variance_trend("m", values)
        assert signal is not None
        assert signal.severity == TransitionSeverity.CRITICAL

    def test_zero_early_variance_no_signal(self):
        """If early half has zero variance, return None (division by zero guard)."""
        d = PhaseTransitionDetector()
        values = [5.0] * 15 + [
            0.0,
            10.0,
            0.0,
            10.0,
            0.0,
            10.0,
            0.0,
            10.0,
            0.0,
            10.0,
            0.0,
            10.0,
            0.0,
            10.0,
            0.0,
        ]
        # Early variance is 0 (all 5.0), so function returns None
        signal = d._detect_variance_trend("m", values)
        assert signal is None


# ── _detect_autocorrelation ───────────────────────────────────────────────


class TestDetectAutocorrelation:
    def test_insufficient_data(self):
        d = PhaseTransitionDetector()
        assert d._detect_autocorrelation("m", [1.0] * 5) is None

    def test_no_signal_for_random_data(self):
        d = PhaseTransitionDetector()
        rng = np.random.default_rng(42)
        values = rng.standard_normal(50).tolist()
        signal = d._detect_autocorrelation("m", values)
        assert signal is None

    def test_signal_for_highly_correlated_data(self):
        """Slowly trending data should have high autocorrelation."""
        d = PhaseTransitionDetector()
        values = list(np.cumsum(np.ones(50)))  # Monotonically increasing
        signal = d._detect_autocorrelation("m", values)
        assert signal is not None
        assert signal.signal_type == "critical_slowing_down"
        assert signal.value > 0.7

    def test_critical_severity_for_very_high_autocorr(self):
        d = PhaseTransitionDetector()
        values = list(np.cumsum(np.ones(50)))
        signal = d._detect_autocorrelation("m", values)
        assert signal is not None
        assert signal.severity == TransitionSeverity.CRITICAL


# ── _detect_flickering ────────────────────────────────────────────────────


class TestDetectFlickering:
    def test_insufficient_data(self):
        d = PhaseTransitionDetector()
        assert d._detect_flickering("m", [1.0, 2.0]) is None

    def test_no_signal_for_monotonic(self):
        d = PhaseTransitionDetector()
        values = list(range(10))
        signal = d._detect_flickering("m", [float(v) for v in values])
        assert signal is None

    def test_signal_for_rapid_switching(self):
        d = PhaseTransitionDetector()
        values = [0.0, 100.0, 0.0, 100.0, 0.0, 100.0, 0.0, 100.0, 0.0, 100.0]
        signal = d._detect_flickering("m", values)
        assert signal is not None
        assert signal.signal_type == "flickering"


# ── _detect_skewness ─────────────────────────────────────────────────────


class TestDetectSkewness:
    def test_insufficient_data(self):
        d = PhaseTransitionDetector()
        assert d._detect_skewness("m", [1.0] * 10) is None

    def test_no_signal_for_symmetric(self):
        d = PhaseTransitionDetector()
        rng = np.random.default_rng(42)
        values = rng.standard_normal(100).tolist()
        signal = d._detect_skewness("m", values)
        # Standard normal is symmetric, so skewness should be near 0
        assert signal is None

    def test_signal_for_skewed_data(self):
        d = PhaseTransitionDetector()
        rng = np.random.default_rng(42)
        # Exponential distribution is positively skewed
        values = rng.exponential(1.0, 100).tolist()
        signal = d._detect_skewness("m", values)
        # May or may not trigger depending on sample; check type if present
        if signal is not None:
            assert signal.signal_type == "distribution_skew"
            assert signal.severity == TransitionSeverity.ELEVATED

    def test_heavily_skewed_triggers(self):
        """Deliberately create a very skewed distribution."""
        d = PhaseTransitionDetector()
        # Many small values, a few very large ones
        values = [1.0] * 25 + [100.0] * 5
        signal = d._detect_skewness("m", values)
        assert signal is not None
        assert abs(signal.value) > 1.0


# ── _assess_overall_severity ──────────────────────────────────────────────


class TestAssessOverallSeverity:
    def _signal(self, severity: TransitionSeverity) -> CriticalSignal:
        return CriticalSignal(
            signal_type="test",
            metric_name="m",
            severity=severity,
            value=0.0,
            threshold=0.0,
            description="test",
        )

    def test_no_signals_normal(self):
        d = PhaseTransitionDetector()
        assert d._assess_overall_severity([]) == TransitionSeverity.NORMAL

    def test_two_critical_is_imminent(self):
        d = PhaseTransitionDetector()
        signals = [self._signal(TransitionSeverity.CRITICAL)] * 2
        assert d._assess_overall_severity(signals) == TransitionSeverity.IMMINENT

    def test_one_critical_is_critical(self):
        d = PhaseTransitionDetector()
        signals = [self._signal(TransitionSeverity.CRITICAL)]
        assert d._assess_overall_severity(signals) == TransitionSeverity.CRITICAL

    def test_three_high_is_high(self):
        d = PhaseTransitionDetector()
        signals = [self._signal(TransitionSeverity.HIGH)] * 3
        assert d._assess_overall_severity(signals) == TransitionSeverity.HIGH

    def test_one_high_is_elevated(self):
        d = PhaseTransitionDetector()
        signals = [self._signal(TransitionSeverity.HIGH)]
        assert d._assess_overall_severity(signals) == TransitionSeverity.ELEVATED

    def test_only_elevated_is_normal(self):
        """Elevated-only signals without HIGH/CRITICAL → NORMAL (per code)."""
        d = PhaseTransitionDetector()
        signals = [self._signal(TransitionSeverity.ELEVATED)] * 5
        assert d._assess_overall_severity(signals) == TransitionSeverity.NORMAL

    def test_critical_trumps_high(self):
        d = PhaseTransitionDetector()
        signals = [
            self._signal(TransitionSeverity.CRITICAL),
            self._signal(TransitionSeverity.HIGH),
            self._signal(TransitionSeverity.HIGH),
        ]
        assert d._assess_overall_severity(signals) == TransitionSeverity.CRITICAL


# ── _estimate_time_to_transition ──────────────────────────────────────────


class TestEstimateTimeToTransition:
    def test_no_data_returns_none(self):
        d = PhaseTransitionDetector()
        assert d._estimate_time_to_transition() is None

    def test_insufficient_data_returns_none(self):
        d = PhaseTransitionDetector()
        d.metric_history["m"] = [1.0, 2.0, 3.0]
        assert d._estimate_time_to_transition() is None

    def test_returns_float_with_data(self):
        d = PhaseTransitionDetector()
        d.metric_history["m"] = list(range(20))
        result = d._estimate_time_to_transition()
        assert result is not None
        assert isinstance(float(result), float)

    def test_imminent_when_very_high_autocorr(self):
        """Near-perfect autocorrelation → time ≈ 0 (imminent)."""
        d = PhaseTransitionDetector()
        # Perfectly linearly increasing → autocorr very close to 1
        d.metric_history["m"] = list(np.arange(0.0, 100.0, 1.0))
        result = d._estimate_time_to_transition()
        assert result is not None
        assert result == 0.0  # distance < 0.05 → imminent


# ── _calculate_confidence ──────────────────────────────────────────────────


class TestCalculateConfidence:
    def _signal(self, metric_name: str, signal_type: str) -> CriticalSignal:
        return CriticalSignal(
            signal_type=signal_type,
            metric_name=metric_name,
            severity=TransitionSeverity.HIGH,
            value=0.0,
            threshold=0.0,
            description="test",
        )

    def test_no_signals_zero(self):
        d = PhaseTransitionDetector()
        assert d._calculate_confidence([]) == 0.0

    def test_single_signal(self):
        d = PhaseTransitionDetector()
        signals = [self._signal("m1", "variance")]
        conf = d._calculate_confidence(signals)
        assert conf > 0.0
        assert conf <= 1.0

    def test_more_metrics_higher_confidence(self):
        d = PhaseTransitionDetector()
        one = [self._signal("m1", "variance")]
        two = [self._signal("m1", "variance"), self._signal("m2", "variance")]
        assert d._calculate_confidence(two) > d._calculate_confidence(one)

    def test_more_types_higher_confidence(self):
        d = PhaseTransitionDetector()
        one = [self._signal("m1", "variance")]
        two = [self._signal("m1", "variance"), self._signal("m1", "autocorr")]
        assert d._calculate_confidence(two) > d._calculate_confidence(one)

    def test_capped_at_1(self):
        d = PhaseTransitionDetector()
        signals = [
            self._signal(f"m{i}", f"type{j}") for i in range(10) for j in range(5)
        ]
        assert d._calculate_confidence(signals) <= 1.0


# ── detect_critical_phenomena (integration) ───────────────────────────────


class TestDetectCriticalPhenomena:
    def test_empty_history_normal(self):
        d = PhaseTransitionDetector()
        risk = d.detect_critical_phenomena()
        assert risk.overall_severity == TransitionSeverity.NORMAL
        assert risk.signals == []

    def test_insufficient_data_no_signals(self):
        d = PhaseTransitionDetector()
        for i in range(5):
            d.update({"m": float(i)})
        risk = d.detect_critical_phenomena()
        assert len(risk.signals) == 0

    def test_returns_phase_transition_risk(self):
        d = PhaseTransitionDetector()
        for i in range(30):
            d.update({"m": float(i)})
        risk = d.detect_critical_phenomena()
        assert isinstance(risk, PhaseTransitionRisk)

    def test_monotonic_triggers_autocorrelation(self):
        """Slowly increasing metric should trigger critical slowing."""
        d = PhaseTransitionDetector()
        for i in range(50):
            d.update({"m": float(i)})
        risk = d.detect_critical_phenomena()
        signal_types = [s.signal_type for s in risk.signals]
        assert "critical_slowing_down" in signal_types


# ── Convenience functions ─────────────────────────────────────────────────


class TestDetectCriticalSlowing:
    def test_insufficient_data(self):
        assert detect_critical_slowing([1.0, 2.0, 3.0]) is False

    def test_random_data_no_slowing(self):
        rng = np.random.default_rng(42)
        values = rng.standard_normal(50).tolist()
        assert detect_critical_slowing(values) is False

    def test_trending_data_slowing(self):
        values = list(np.arange(0.0, 50.0))
        assert detect_critical_slowing(values) is True


class TestEstimateTimeToTransitionFunc:
    def test_empty_histories(self):
        assert estimate_time_to_transition({}) is None

    def test_insufficient_data(self):
        result = estimate_time_to_transition({"m": [1.0, 2.0, 3.0]})
        assert result is None

    def test_returns_value_with_data(self):
        histories = {"m": list(np.arange(0.0, 50.0))}
        result = estimate_time_to_transition(histories)
        assert result is not None

    def test_multiple_metrics(self):
        histories = {
            "m1": list(np.arange(0.0, 50.0)),
            "m2": list(np.arange(0.0, 50.0)),
        }
        result = estimate_time_to_transition(histories)
        assert result is not None
