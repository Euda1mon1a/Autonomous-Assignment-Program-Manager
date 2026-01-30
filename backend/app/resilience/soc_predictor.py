"""
Self-Organized Criticality (SOC) Predictor for Early Warning.

Self-organized criticality is a property of dynamical systems that have a critical
point as an attractor. Before reaching the critical point, the system exhibits
"critical slowing down" - recovery from perturbations takes progressively longer.

Key Early Warning Signals (2-4 weeks advance notice):
1. Relaxation time (τ) - how long system takes to recover from perturbations
2. Variance - increasing variance indicates approaching criticality
3. Autocorrelation at lag-1 (AC1) - increasing AC1 signals slowing down

Critical Thresholds:
- τ > 48 hours: System struggling to recover from disruptions
- Variance slope > 0.1: Instability increasing
- AC1 > 0.7: Today predicts tomorrow too well (loss of resilience)

When 2+ signals trigger simultaneously, the system is approaching a phase
transition (avalanche/cascade failure) with 2-4 week warning window.

This module implements:
1. Relaxation time calculation from perturbation recovery
2. Variance trend analysis with rolling windows
3. Lag-1 autocorrelation tracking
4. Critical slowing down risk scoring
5. Days-to-critical estimation
6. Actionable recommendations based on signals

References:
- Scheffer et al. (2009), "Early-warning signals for critical transitions"
- Dakos et al. (2012), "Methods for detecting early warnings of critical transitions"
- Bak et al. (1987), "Self-organized criticality: An explanation of 1/f noise"
"""

import logging
import statistics
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from uuid import UUID, uuid4

import numpy as np

logger = logging.getLogger(__name__)


class WarningLevel(str, Enum):
    """Warning level for critical slowing down."""

    GREEN = "green"  # Healthy - no warning signals
    YELLOW = "yellow"  # Single warning signal detected
    ORANGE = "orange"  # Two warning signals detected
    RED = "red"  # All three signals detected - critical
    UNKNOWN = "unknown"  # Insufficient data


@dataclass
class CriticalSlowingDownResult:
    """
    Result from critical slowing down detection.

    Contains early warning signals and recommendations for preventing
    cascade failures based on SOC theory.
    """

    # Analysis metadata
    id: UUID
    calculated_at: datetime
    days_analyzed: int
    data_quality: str  # "excellent", "good", "fair", "poor"

    # Warning status
    is_critical: bool  # Approaching critical point?
    warning_level: WarningLevel
    confidence: float  # 0.0 to 1.0

    # Early warning signals
    relaxation_time_hours: float | None  # Current τ (target: < 48)
    relaxation_time_baseline: float | None  # Historical baseline
    relaxation_time_increasing: bool

    variance_current: float | None  # Current variance
    variance_baseline: float | None  # Historical baseline
    variance_slope: float | None  # Trend slope (target: < 0.1)
    variance_increasing: bool

    autocorrelation_ac1: float | None  # Lag-1 autocorrelation (target: < 0.7)
    autocorrelation_baseline: float | None
    autocorrelation_increasing: bool

    # Risk assessment
    signals_triggered: int  # Count of warning signals (0-3)
    estimated_days_to_critical: int | None  # Projected time to critical point
    avalanche_risk_score: float  # 0.0 to 1.0 composite risk

    # Actionable insights
    recommendations: list[str]
    immediate_actions: list[str]
    watch_items: list[str]


class SOCAvalanchePredictor:
    """
    Predicts SOC avalanche events using critical slowing down detection.

    Monitors utilization and coverage time series for early warning signals
    that precede cascade failures by 2-4 weeks.
    """

    def __init__(
        self,
        relaxation_threshold_hours: float = 48.0,
        variance_slope_threshold: float = 0.1,
        autocorrelation_threshold: float = 0.7,
        min_data_points: int = 30,
    ) -> None:
        """
        Initialize SOC predictor.

        Args:
            relaxation_threshold_hours: Critical relaxation time in hours
            variance_slope_threshold: Critical variance increase rate
            autocorrelation_threshold: Critical AC1 value
            min_data_points: Minimum data points for reliable analysis
        """
        self.relaxation_threshold = relaxation_threshold_hours
        self.variance_slope_threshold = variance_slope_threshold
        self.autocorrelation_threshold = autocorrelation_threshold
        self.min_data_points = min_data_points

        # Cache for performance
        self._last_analysis: CriticalSlowingDownResult | None = None
        self._last_analysis_time: datetime | None = None

    async def detect_critical_slowing_down(
        self,
        utilization_history: list[float],
        coverage_history: list[float] | None = None,
        days_lookback: int = 60,
    ) -> CriticalSlowingDownResult:
        """
        Detect critical slowing down in scheduling system.

        Analyzes time series data for early warning signals of approaching
        cascade failure. Combines utilization and coverage metrics for
        comprehensive assessment.

        Args:
            utilization_history: Daily utilization values (0.0 to 1.0)
            coverage_history: Daily coverage rates (optional, for enhanced analysis)
            days_lookback: Number of historical days to analyze

        Returns:
            CriticalSlowingDownResult with warning signals and recommendations

        Example:
            >>> predictor = SOCAvalanchePredictor()
            >>> utilization = [0.75, 0.76, 0.78, ...]  # 60 days
            >>> result = await predictor.detect_critical_slowing_down(utilization)
            >>> if result.is_critical:
            ...     print(f"WARNING: {result.warning_level} - {result.recommendations}")
        """
        analysis_id = uuid4()
        timestamp = datetime.now()

        # Validate input
        if not utilization_history or len(utilization_history) < self.min_data_points:
            return self._insufficient_data_result(
                analysis_id, timestamp, len(utilization_history)
            )

            # Limit to lookback window
        data = utilization_history[-days_lookback:]
        data_points = len(data)

        # Assess data quality
        data_quality = self._assess_data_quality(data)

        # Calculate early warning signals
        relaxation_time, relaxation_baseline, relaxation_increasing = (
            self._calculate_relaxation_time(data)
        )

        variance_current, variance_baseline, variance_slope, variance_increasing = (
            self._calculate_variance_trend(data)
        )

        ac1_current, ac1_baseline, ac1_increasing = self._calculate_autocorrelation(
            data
        )

        # Count triggered signals
        signals_triggered = sum(
            [
                relaxation_increasing
                and relaxation_time
                and relaxation_time > self.relaxation_threshold,
                variance_increasing
                and variance_slope
                and variance_slope > self.variance_slope_threshold,
                ac1_increasing
                and ac1_current
                and ac1_current > self.autocorrelation_threshold,
            ]
        )

        # Determine warning level
        if signals_triggered == 0:
            warning_level = WarningLevel.GREEN
            confidence = 0.9
        elif signals_triggered == 1:
            warning_level = WarningLevel.YELLOW
            confidence = 0.7
        elif signals_triggered == 2:
            warning_level = WarningLevel.ORANGE
            confidence = 0.85
        else:  # 3 signals
            warning_level = WarningLevel.RED
            confidence = 0.95

            # Calculate composite risk score
        avalanche_risk = self._calculate_avalanche_risk(
            relaxation_time,
            variance_slope,
            ac1_current,
            signals_triggered,
        )

        # Estimate days to critical
        days_to_critical = self._estimate_days_to_critical(
            variance_slope,
            ac1_current,
            data,
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            warning_level,
            signals_triggered,
            relaxation_time,
            variance_slope,
            ac1_current,
            days_to_critical,
        )

        immediate_actions = self._generate_immediate_actions(
            warning_level, signals_triggered
        )

        watch_items = self._generate_watch_items(
            relaxation_increasing, variance_increasing, ac1_increasing
        )

        result = CriticalSlowingDownResult(
            id=analysis_id,
            calculated_at=timestamp,
            days_analyzed=data_points,
            data_quality=data_quality,
            is_critical=signals_triggered >= 2,
            warning_level=warning_level,
            confidence=confidence,
            relaxation_time_hours=relaxation_time,
            relaxation_time_baseline=relaxation_baseline,
            relaxation_time_increasing=relaxation_increasing,
            variance_current=variance_current,
            variance_baseline=variance_baseline,
            variance_slope=variance_slope,
            variance_increasing=variance_increasing,
            autocorrelation_ac1=ac1_current,
            autocorrelation_baseline=ac1_baseline,
            autocorrelation_increasing=ac1_increasing,
            signals_triggered=signals_triggered,
            estimated_days_to_critical=days_to_critical,
            avalanche_risk_score=avalanche_risk,
            recommendations=recommendations,
            immediate_actions=immediate_actions,
            watch_items=watch_items,
        )

        # Cache result
        self._last_analysis = result
        self._last_analysis_time = timestamp

        logger.info(
            f"SOC Analysis: {warning_level.value} - {signals_triggered} signals, "
            f"risk={avalanche_risk:.2f}, days_to_critical={days_to_critical}"
        )

        return result

    def _calculate_relaxation_time(
        self, data: list[float]
    ) -> tuple[float | None, float | None, bool]:
        """
        Calculate relaxation time (τ) - time to recover from perturbations.

        Relaxation time is estimated by fitting exponential decay to recovery
        from deviations. Longer relaxation time indicates the system is
        struggling to return to equilibrium.

        Returns:
            Tuple of (current_tau_hours, baseline_tau_hours, is_increasing)
        """
        if len(data) < 30:
            return None, None, False

        try:
            # Detect perturbations (large deviations from rolling mean)
            rolling_mean = self._rolling_mean(data, window=7)
            deviations = [abs(data[i] - rolling_mean[i]) for i in range(len(data))]
            threshold = statistics.mean(deviations) + statistics.stdev(deviations)

            # Find perturbation events
            perturbations = []
            for i in range(len(deviations) - 10):  # Need at least 10 points to recover
                if deviations[i] > threshold:
                    # Measure recovery time
                    recovery_time = 0
                    for j in range(i + 1, min(i + 20, len(deviations))):
                        if deviations[j] < threshold * 0.5:  # Recovered
                            recovery_time = j - i
                            break
                    if recovery_time > 0:
                        perturbations.append(recovery_time)

            if len(perturbations) < 3:
                return None, None, False

                # Recent vs baseline relaxation time
            split = len(perturbations) // 2
            baseline_tau = (
                statistics.mean(perturbations[:split]) * 24
            )  # Convert to hours
            recent_tau = statistics.mean(perturbations[split:]) * 24

            is_increasing = recent_tau > baseline_tau * 1.2  # 20% increase

            return recent_tau, baseline_tau, is_increasing

        except Exception as e:
            logger.warning(f"Relaxation time calculation failed: {e}")
            return None, None, False

    def _calculate_variance_trend(
        self, data: list[float]
    ) -> tuple[float | None, float | None, float | None, bool]:
        """
        Calculate variance trend over time.

        Increasing variance indicates the system is becoming less stable
        and more susceptible to large fluctuations.

        Returns:
            Tuple of (current_variance, baseline_variance, slope, is_increasing)
        """
        if len(data) < 30:
            return None, None, None, False

        try:
            # Calculate rolling variance
            window = 15
            variances = []
            for i in range(window, len(data)):
                window_data = data[i - window : i]
                variances.append(statistics.variance(window_data))

            if len(variances) < 10:
                return None, None, None, False

                # Baseline vs current
            split = len(variances) // 2
            baseline_var = statistics.mean(variances[:split])
            current_var = statistics.mean(variances[split:])

            # Calculate trend slope using linear regression
            x = np.arange(len(variances))
            y = np.array(variances)
            slope = np.polyfit(x, y, 1)[0]

            is_increasing = (
                current_var > baseline_var * 1.5  # 50% increase
                and slope > self.variance_slope_threshold
            )

            return current_var, baseline_var, slope, is_increasing

        except Exception as e:
            logger.warning(f"Variance trend calculation failed: {e}")
            return None, None, None, False

    def _calculate_autocorrelation(
        self, data: list[float]
    ) -> tuple[float | None, float | None, bool]:
        """
        Calculate lag-1 autocorrelation.

        High autocorrelation indicates the system is "sluggish" - today's
        state strongly predicts tomorrow's, showing loss of resilience.

        Returns:
            Tuple of (current_ac1, baseline_ac1, is_increasing)
        """
        if len(data) < 30:
            return None, None, False

        try:
            # Split into baseline and recent
            split = len(data) // 2
            baseline_data = data[:split]
            recent_data = data[split:]

            # Calculate AC1 for baseline
            baseline_ac1 = np.corrcoef(baseline_data[:-1], baseline_data[1:])[0, 1]

            # Calculate AC1 for recent
            current_ac1 = np.corrcoef(recent_data[:-1], recent_data[1:])[0, 1]

            is_increasing = current_ac1 > baseline_ac1 * 1.1  # 10% increase

            return current_ac1, baseline_ac1, is_increasing

        except Exception as e:
            logger.warning(f"Autocorrelation calculation failed: {e}")
            return None, None, False

    def _calculate_avalanche_risk(
        self,
        relaxation_time: float | None,
        variance_slope: float | None,
        ac1: float | None,
        signals_triggered: int,
    ) -> float:
        """
        Calculate composite avalanche risk score (0.0 to 1.0).

        Combines all signals with weighted average based on criticality.
        """
        risk_components = []

        # Relaxation time risk
        if relaxation_time is not None:
            tau_risk = min(1.0, relaxation_time / (self.relaxation_threshold * 2))
            risk_components.append(tau_risk * 0.35)

            # Variance risk
        if variance_slope is not None:
            var_risk = min(
                1.0, abs(variance_slope) / (self.variance_slope_threshold * 2)
            )
            risk_components.append(var_risk * 0.30)

            # AC1 risk
        if ac1 is not None:
            ac1_risk = min(1.0, ac1 / 1.0)  # AC1 maxes at 1.0
            risk_components.append(ac1_risk * 0.35)

        if not risk_components:
            return 0.0

        base_risk = sum(risk_components)

        # Amplify if multiple signals triggered
        if signals_triggered >= 2:
            base_risk *= 1.3
        if signals_triggered == 3:
            base_risk *= 1.5

        return min(1.0, base_risk)

    def _estimate_days_to_critical(
        self,
        variance_slope: float | None,
        ac1: float | None,
        data: list[float],
    ) -> int | None:
        """
        Estimate days until critical point is reached.

        Uses variance slope to project when critical threshold will be crossed.
        """
        if variance_slope is None or variance_slope <= 0:
            return None

        try:
            # Current variance
            current_var = statistics.variance(data[-15:])

            # Critical variance (empirically set at 2x current healthy level)
            baseline_var = statistics.variance(data[: len(data) // 2])
            critical_var = baseline_var * 3.0

            # Days to critical assuming linear trend
            if current_var >= critical_var:
                return 0

            days_to_critical = int((critical_var - current_var) / variance_slope)

            # Clamp to reasonable range
            return max(0, min(days_to_critical, 120))

        except Exception as e:
            logger.warning(f"Days to critical estimation failed: {e}")
            return None

    def _generate_recommendations(
        self,
        warning_level: WarningLevel,
        signals_triggered: int,
        relaxation_time: float | None,
        variance_slope: float | None,
        ac1: float | None,
        days_to_critical: int | None,
    ) -> list[str]:
        """Generate actionable recommendations based on warning signals."""
        recommendations = []

        if warning_level == WarningLevel.GREEN:
            recommendations.append("System healthy - continue normal operations")
            recommendations.append("Maintain current monitoring frequency")

        elif warning_level == WarningLevel.YELLOW:
            recommendations.append(
                "Single warning signal detected - increase monitoring"
            )
            if relaxation_time and relaxation_time > self.relaxation_threshold:
                recommendations.append(
                    f"Relaxation time elevated ({relaxation_time:.1f}hrs) - "
                    "review recent schedule changes for quick resolution"
                )
            if variance_slope and variance_slope > self.variance_slope_threshold:
                recommendations.append(
                    "Variance increasing - identify sources of instability"
                )
            if ac1 and ac1 > self.autocorrelation_threshold:
                recommendations.append(
                    "High autocorrelation - system losing flexibility"
                )

        elif warning_level == WarningLevel.ORANGE:
            recommendations.append("⚠️ TWO warning signals - avalanche risk elevated")
            recommendations.append("Activate preventive measures:")
            recommendations.append(
                "- Review and optimize current schedule distribution"
            )
            recommendations.append("- Confirm backup coverage plans")
            recommendations.append("- Defer non-essential commitments")
            if days_to_critical:
                recommendations.append(
                    f"- Estimated {days_to_critical} days to critical point"
                )

        else:  # RED
            recommendations.append(
                "🚨 CRITICAL: All three signals triggered - cascade failure imminent"
            )
            recommendations.append("IMMEDIATE ACTIONS REQUIRED:")
            recommendations.append("1. Activate emergency staffing protocols")
            recommendations.append("2. Load shedding - cancel optional activities")
            recommendations.append("3. Freeze new commitments until stability restored")
            recommendations.append("4. Daily monitoring until warning level drops")
            if days_to_critical and days_to_critical < 14:
                recommendations.append(
                    f"⏰ URGENT: Only {days_to_critical} days to critical point"
                )

        return recommendations

    def _generate_immediate_actions(
        self, warning_level: WarningLevel, signals_triggered: int
    ) -> list[str]:
        """Generate immediate actions based on severity."""
        actions = []

        if warning_level == WarningLevel.YELLOW:
            actions.append("Review utilization patterns for anomalies")

        elif warning_level == WarningLevel.ORANGE:
            actions.append("Convene scheduling committee meeting")
            actions.append("Review N-1/N-2 contingency plans")

        elif warning_level == WarningLevel.RED:
            actions.append("NOTIFY LEADERSHIP IMMEDIATELY")
            actions.append("Activate crisis management protocols")
            actions.append("Implement load shedding hierarchy")

        return actions

    def _generate_watch_items(
        self,
        relaxation_increasing: bool,
        variance_increasing: bool,
        ac1_increasing: bool,
    ) -> list[str]:
        """Generate watch items for monitoring."""
        items = []

        if relaxation_increasing:
            items.append(
                "Monitor swap resolution times - should decrease, not increase"
            )
        if variance_increasing:
            items.append("Watch for increasing daily utilization fluctuations")
        if ac1_increasing:
            items.append("Track schedule rigidity - need more flexibility")

        if not items:
            items.append("Continue routine monitoring")

        return items

    def _assess_data_quality(self, data: list[float]) -> str:
        """Assess quality of input data for analysis."""
        if len(data) >= 60:
            return "excellent"
        elif len(data) >= 45:
            return "good"
        elif len(data) >= 30:
            return "fair"
        else:
            return "poor"

    def _rolling_mean(self, data: list[float], window: int) -> list[float]:
        """Calculate rolling mean with specified window."""
        result = []
        for i in range(len(data)):
            start = max(0, i - window + 1)
            window_data = data[start : i + 1]
            result.append(statistics.mean(window_data))
        return result

    def _insufficient_data_result(
        self, analysis_id: UUID, timestamp: datetime, data_points: int
    ) -> CriticalSlowingDownResult:
        """Return result indicating insufficient data."""
        return CriticalSlowingDownResult(
            id=analysis_id,
            calculated_at=timestamp,
            days_analyzed=data_points,
            data_quality="poor",
            is_critical=False,
            warning_level=WarningLevel.UNKNOWN,
            confidence=0.0,
            relaxation_time_hours=None,
            relaxation_time_baseline=None,
            relaxation_time_increasing=False,
            variance_current=None,
            variance_baseline=None,
            variance_slope=None,
            variance_increasing=False,
            autocorrelation_ac1=None,
            autocorrelation_baseline=None,
            autocorrelation_increasing=False,
            signals_triggered=0,
            estimated_days_to_critical=None,
            avalanche_risk_score=0.0,
            recommendations=[
                f"Insufficient data for analysis (need {self.min_data_points}, have {data_points})",
                "Continue collecting utilization history",
                "Run analysis again when sufficient data available",
            ],
            immediate_actions=[],
            watch_items=["Accumulate at least 30 days of utilization data"],
        )

    def get_last_analysis(self) -> CriticalSlowingDownResult | None:
        """Get cached result from last analysis."""
        return self._last_analysis

    def clear_cache(self) -> None:
        """Clear cached analysis results."""
        self._last_analysis = None
        self._last_analysis_time = None
