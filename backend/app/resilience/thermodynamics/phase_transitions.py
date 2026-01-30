"""
Phase Transitions and Critical Phenomena Detection.

Implements early warning signal detection for scheduling system phase transitions
using critical phenomena theory from statistical physics.

Key Concepts:
- Critical Slowing Down: Response time τ → ∞ near critical point
- Increasing Variance: Fluctuations diverge at transitions
- Increasing Autocorrelation: System "remembers" longer
- Flickering: Rapid state switching near bistable points
- Spatial Correlations: Long-range correlations emerge

Early Warning Signals (Universal across systems):
1. Variance increase
2. Autocorrelation increase
3. Skewness changes
4. Flickering/intermittency
5. Critical slowing down

References:
- Scheffer et al. (2009): "Early-warning signals for critical transitions"
- Dakos et al. (2012): "Methods for detecting early warnings"
- 2025 Nature Communications: "Thermodynamic predictions for bifurcations"
- 2025 Royal Society: "Universal early warning signals in climate systems"
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


class TransitionSeverity(str, Enum):
    """Severity of detected phase transition risk."""

    NORMAL = "normal"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"
    IMMINENT = "imminent"


@dataclass
class CriticalSignal:
    """
    A detected early warning signal for phase transition.

    Attributes:
        signal_type: Type of signal (variance, autocorr, flicker, etc.)
        metric_name: Which metric shows the signal
        severity: How severe the signal is
        value: Numerical value of the indicator
        threshold: Threshold that was crossed
        description: Human-readable description
        detected_at: When signal was detected
    """

    signal_type: str
    metric_name: str
    severity: TransitionSeverity
    value: float
    threshold: float
    description: str
    detected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PhaseTransitionRisk:
    """
    Overall assessment of phase transition risk.

    Attributes:
        overall_severity: Worst severity across all signals
        signals: List of detected early warning signals
        time_to_transition: Estimated time until transition (if predictable)
        confidence: Confidence in prediction (0-1)
        recommendations: Suggested interventions
    """

    overall_severity: TransitionSeverity
    signals: list[CriticalSignal]
    time_to_transition: float | None = None
    confidence: float = 0.0
    recommendations: list[str] = field(default_factory=list)


class PhaseTransitionDetector:
    """
    Detect approaching phase transitions using critical phenomena theory.

    Monitors universal early warning signals that appear before
    system transitions regardless of the specific mechanism.

    Theory:
        Near phase transitions, systems exhibit universal behaviors:
        - Slowing response (critical slowing down)
        - Increasing variance (diverging fluctuations)
        - Increasing autocorrelation (memory effects)
        - Flickering between states (bistability)

    Based on 2025 research showing thermodynamic approaches detect
    transitions earlier than traditional bifurcation methods.
    """

    def __init__(self, window_size: int = 50) -> None:
        """
        Initialize phase transition detector.

        Args:
            window_size: Number of samples for analysis window
        """
        self.window_size = window_size
        self.metric_history: dict[str, list[float]] = defaultdict(list)
        self.timestamp_history: dict[str, list[datetime]] = defaultdict(list)

        logger.info(f"PhaseTransitionDetector initialized with window={window_size}")

    def update(self, metrics: dict[str, float]) -> None:
        """
        Update with latest metrics.

        Args:
            metrics: Dictionary of metric name → value
        """
        timestamp = datetime.utcnow()

        for key, value in metrics.items():
            self.metric_history[key].append(value)
            self.timestamp_history[key].append(timestamp)

            # Maintain window size
            if len(self.metric_history[key]) > self.window_size:
                self.metric_history[key].pop(0)
                self.timestamp_history[key].pop(0)

    def detect_critical_phenomena(self) -> PhaseTransitionRisk:
        """
        Detect universal early warning signals across all metrics.

        Returns:
            PhaseTransitionRisk with detected signals and assessment
        """
        all_signals: list[CriticalSignal] = []

        for metric_name, values in self.metric_history.items():
            if len(values) < 10:
                continue

                # 1. Increasing Variance
            signal = self._detect_variance_trend(metric_name, values)
            if signal:
                all_signals.append(signal)

                # 2. Increasing Autocorrelation (Critical Slowing Down)
            signal = self._detect_autocorrelation(metric_name, values)
            if signal:
                all_signals.append(signal)

                # 3. Flickering (rapid state changes)
            signal = self._detect_flickering(metric_name, values)
            if signal:
                all_signals.append(signal)

                # 4. Skewness change
            signal = self._detect_skewness(metric_name, values)
            if signal:
                all_signals.append(signal)

                # Assess overall severity
        overall_severity = self._assess_overall_severity(all_signals)

        # Estimate time to transition
        time_to_transition = self._estimate_time_to_transition()

        # Generate recommendations
        recommendations = self._generate_recommendations(all_signals, overall_severity)

        # Calculate confidence
        confidence = self._calculate_confidence(all_signals)

        return PhaseTransitionRisk(
            overall_severity=overall_severity,
            signals=all_signals,
            time_to_transition=time_to_transition,
            confidence=confidence,
            recommendations=recommendations,
        )

    def _detect_variance_trend(
        self, metric_name: str, values: list[float]
    ) -> CriticalSignal | None:
        """
        Detect increasing variance (diverging fluctuations).

        Near phase transitions, fluctuations increase dramatically.
        """
        if len(values) < 20:
            return None

            # Split into early and recent halves
        mid = len(values) // 2
        var_early = np.var(values[:mid])
        var_recent = np.var(values[mid:])

        if var_early == 0:
            return None

            # Percentage increase
        variance_increase = (var_recent - var_early) / var_early

        # Thresholds
        if variance_increase > 0.5:  # 50% increase
            severity = (
                TransitionSeverity.CRITICAL
                if variance_increase > 1.0
                else TransitionSeverity.HIGH
            )
            return CriticalSignal(
                signal_type="increasing_variance",
                metric_name=metric_name,
                severity=severity,
                value=variance_increase,
                threshold=0.5,
                description=f"Variance increased {variance_increase:.1%} (fluctuations diverging)",
            )

        return None

    def _detect_autocorrelation(
        self, metric_name: str, values: list[float]
    ) -> CriticalSignal | None:
        """
        Detect increasing autocorrelation (critical slowing down).

        System response time increases near critical point.
        """
        if len(values) < 10:
            return None

            # Calculate autocorrelation at lag=1
        autocorr = self._autocorrelation(values, lag=1)

        # High autocorrelation indicates critical slowing
        if autocorr > 0.7:
            severity = (
                TransitionSeverity.CRITICAL
                if autocorr > 0.85
                else TransitionSeverity.HIGH
            )
            return CriticalSignal(
                signal_type="critical_slowing_down",
                metric_name=metric_name,
                severity=severity,
                value=autocorr,
                threshold=0.7,
                description=f"Critical slowing detected (autocorr={autocorr:.2f})",
            )

        return None

    def _detect_flickering(
        self, metric_name: str, values: list[float]
    ) -> CriticalSignal | None:
        """
        Detect flickering (rapid state changes).

        Near bistable points, system rapidly switches between states.
        """
        if len(values) < 5:
            return None

            # Calculate flicker rate
        flicker_rate = self._calculate_flicker_rate(values)

        if flicker_rate > 0.3:  # 30% of samples show flickering
            severity = (
                TransitionSeverity.HIGH
                if flicker_rate > 0.5
                else TransitionSeverity.ELEVATED
            )
            return CriticalSignal(
                signal_type="flickering",
                metric_name=metric_name,
                severity=severity,
                value=flicker_rate,
                threshold=0.3,
                description=f"System flickering between states ({flicker_rate:.1%} rate)",
            )

        return None

    def _detect_skewness(
        self, metric_name: str, values: list[float]
    ) -> CriticalSignal | None:
        """
        Detect skewness changes in distribution.

        Distribution becoming asymmetric indicates approaching transition.
        """
        if len(values) < 20:
            return None

            # Calculate skewness
        skewness = stats.skew(values)

        if abs(skewness) > 1.0:
            severity = TransitionSeverity.ELEVATED
            return CriticalSignal(
                signal_type="distribution_skew",
                metric_name=metric_name,
                severity=severity,
                value=skewness,
                threshold=1.0,
                description=f"Distribution becoming skewed (skew={skewness:.2f})",
            )

        return None

    def _autocorrelation(self, values: list[float], lag: int = 1) -> float:
        """Calculate autocorrelation at given lag."""
        if len(values) < lag + 2:
            return 0.0

        mean = np.mean(values)
        c0 = np.sum((np.array(values) - mean) ** 2)

        if c0 == 0:
            return 0.0

        c_lag = np.sum(
            (np.array(values[:-lag]) - mean) * (np.array(values[lag:]) - mean)
        )

        return c_lag / c0

    def _calculate_flicker_rate(self, values: list[float]) -> float:
        """
        Calculate rate of rapid direction changes (flickering).
        """
        if len(values) < 3:
            return 0.0

            # Threshold for significant change
        threshold = np.std(values) * 0.5 if np.std(values) > 0 else 0.1

        # Count direction changes
        changes = 0
        for i in range(1, len(values) - 1):
            diff_before = values[i] - values[i - 1]
            diff_after = values[i + 1] - values[i]

            # Significant direction change?
            if abs(diff_before) > threshold and abs(diff_after) > threshold:
                if np.sign(diff_before) != np.sign(diff_after):
                    changes += 1

        return changes / (len(values) - 2)

    def _assess_overall_severity(
        self, signals: list[CriticalSignal]
    ) -> TransitionSeverity:
        """Assess overall severity from all signals."""
        if not signals:
            return TransitionSeverity.NORMAL

            # Count by severity
        critical_count = sum(
            1 for s in signals if s.severity == TransitionSeverity.CRITICAL
        )
        high_count = sum(1 for s in signals if s.severity == TransitionSeverity.HIGH)

        if critical_count >= 2:
            return TransitionSeverity.IMMINENT
        elif critical_count >= 1:
            return TransitionSeverity.CRITICAL
        elif high_count >= 3:
            return TransitionSeverity.HIGH
        elif high_count >= 1:
            return TransitionSeverity.ELEVATED
        else:
            return TransitionSeverity.NORMAL

    def _estimate_time_to_transition(self) -> float | None:
        """
        Estimate time until phase transition.

        Uses average autocorrelation as proxy for distance to critical point.
        Near critical point, autocorr → 1, distance → 0.

        Returns:
            Estimated time in hours, or None if insufficient data
        """
        autocorrs = []

        for values in self.metric_history.values():
            if len(values) >= 10:
                autocorr = self._autocorrelation(values, lag=1)
                autocorrs.append(autocorr)

        if not autocorrs:
            return None

        avg_autocorr = np.mean(autocorrs)

        # Distance to critical point ∝ (1 - autocorr)
        distance = 1.0 - avg_autocorr

        if distance < 0.05:
            return 0.0  # Imminent

            # Rough estimate: time constant ∝ 1 / (1 - r)
            # This is a simplified model
        time_constant = 1.0 / distance

        # Convert to hours (calibration factor)
        estimated_hours = time_constant * 10  # Calibrate based on empirical data

        return estimated_hours

    def _generate_recommendations(
        self, signals: list[CriticalSignal], severity: TransitionSeverity
    ) -> list[str]:
        """Generate intervention recommendations."""
        recommendations = []

        if severity == TransitionSeverity.IMMINENT:
            recommendations.extend(
                [
                    "URGENT: Activate fallback schedules immediately",
                    "Escalate to RED defense level",
                    "Initiate load shedding protocols",
                    "Alert all stakeholders of imminent transition",
                ]
            )
        elif severity == TransitionSeverity.CRITICAL:
            recommendations.extend(
                [
                    "Activate contingency plans",
                    "Increase monitoring frequency",
                    "Prepare fallback schedules",
                    "Escalate to ORANGE defense level",
                ]
            )
        elif severity == TransitionSeverity.HIGH:
            recommendations.extend(
                [
                    "Review N-1/N-2 contingency status",
                    "Increase buffer capacity",
                    "Defer non-critical activities",
                    "Escalate to YELLOW defense level",
                ]
            )

            # Signal-specific recommendations
        for signal in signals:
            if signal.signal_type == "increasing_variance":
                recommendations.append(
                    f"Stabilize {signal.metric_name} (high variance detected)"
                )
            elif signal.signal_type == "flickering":
                recommendations.append(
                    f"System unstable for {signal.metric_name} - reduce perturbations"
                )

        return list(set(recommendations))  # Remove duplicates

    def _calculate_confidence(self, signals: list[CriticalSignal]) -> float:
        """
        Calculate confidence in prediction.

        More independent signals → higher confidence.
        """
        if not signals:
            return 0.0

            # Count distinct metric names (independent evidence)
        unique_metrics = len(set(s.metric_name for s in signals))

        # Count distinct signal types
        unique_types = len(set(s.signal_type for s in signals))

        # Confidence increases with multiple independent lines of evidence
        confidence = min(1.0, (unique_metrics * 0.2) + (unique_types * 0.15))

        return confidence


class CriticalPhenomenaMonitor:
    """
    Real-time monitoring service for phase transition early warnings.

    Integrates with resilience service to provide continuous
    phase transition risk assessment.
    """

    def __init__(self, window_size: int = 50) -> None:
        """
        Initialize critical phenomena monitor.

        Args:
            window_size: Analysis window size
        """
        self.detector = PhaseTransitionDetector(window_size)
        self.risk_history: list[PhaseTransitionRisk] = []
        self.alert_callbacks: list[callable] = []

        logger.info("CriticalPhenomenaMonitor initialized")

    def add_alert_callback(self, callback: callable) -> None:
        """Register callback for critical alerts."""
        self.alert_callbacks.append(callback)

    async def update_and_assess(self, metrics: dict[str, float]) -> PhaseTransitionRisk:
        """
        Update with metrics and assess risk.

        Args:
            metrics: Current system metrics

        Returns:
            PhaseTransitionRisk assessment
        """
        # Update detector
        self.detector.update(metrics)

        # Detect critical phenomena
        risk = self.detector.detect_critical_phenomena()

        # Store in history
        self.risk_history.append(risk)
        if len(self.risk_history) > 100:
            self.risk_history.pop(0)

            # Trigger alerts if critical
        if risk.overall_severity in (
            TransitionSeverity.CRITICAL,
            TransitionSeverity.IMMINENT,
        ):
            logger.error(
                f"Critical phase transition risk detected: {risk.overall_severity.value}, "
                f"{len(risk.signals)} signals, "
                f"time_to_transition={risk.time_to_transition}"
            )

            # Call alert callbacks
            for callback in self.alert_callbacks:
                try:
                    await callback(risk)
                except Exception as e:
                    logger.error(f"Alert callback failed: {e}")

        return risk

    def get_current_risk(self) -> PhaseTransitionRisk | None:
        """Get most recent risk assessment."""
        return self.risk_history[-1] if self.risk_history else None


def detect_critical_slowing(metric_history: list[float]) -> bool:
    """
    Convenience function to detect critical slowing down.

    Args:
        metric_history: Time series of metric values

    Returns:
        True if critical slowing detected
    """
    if len(metric_history) < 10:
        return False

    detector = PhaseTransitionDetector()
    detector.metric_history["metric"] = metric_history

    risk = detector.detect_critical_phenomena()

    return any(s.signal_type == "critical_slowing_down" for s in risk.signals)


def estimate_time_to_transition(
    metric_histories: dict[str, list[float]],
) -> float | None:
    """
    Convenience function to estimate time to transition.

    Args:
        metric_histories: Dictionary of metric name → time series

    Returns:
        Estimated time in hours, or None
    """
    detector = PhaseTransitionDetector()

    for name, history in metric_histories.items():
        detector.metric_history[name] = history

    risk = detector.detect_critical_phenomena()

    return risk.time_to_transition
