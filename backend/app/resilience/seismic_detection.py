"""
STA/LTA (Short-Term Average / Long-Term Average) Anomaly Detection.

Adapts seismology P-wave detection algorithms for burnout precursor signals
in medical residency scheduling. Uses signal processing to detect sudden
changes in baseline behavior that indicate impending burnout or system stress.

Key Concepts:
- STA: Short-Term Average over recent window (e.g., 5 data points)
- LTA: Long-Term Average over historical window (e.g., 30 data points)
- Ratio: STA/LTA indicates deviation from baseline
- Threshold: Ratio > 2.5 typically indicates anomaly onset

Precursor Signals Monitored:
- Swap requests (frequency increasing)
- Sick calls (pattern changes)
- Preference declines (declining desired shifts)
- Response delays (slower to respond to requests)
- Voluntary coverage declines (refusing extra shifts)
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID

import numpy as np

logger = logging.getLogger(__name__)


class PrecursorSignal(str, Enum):
    """
    Types of burnout precursor signals to monitor.

    Each signal represents a behavioral change that may indicate
    increasing stress or approaching burnout.
    """

    SWAP_REQUESTS = "swap_requests"  # Frequency of shift swap requests
    SICK_CALLS = "sick_calls"  # Unplanned absences
    PREFERENCE_DECLINE = "preference_decline"  # Declining preferred shifts
    RESPONSE_DELAYS = "response_delays"  # Slower response times (hours)
    VOLUNTARY_COVERAGE_DECLINE = "voluntary_coverage_decline"  # Refusing extra shifts


@dataclass
class SeismicAlert:
    """
    Alert generated when STA/LTA anomaly is detected.

    Represents a detected precursor signal that may indicate
    impending burnout or system stress.
    """

    signal_type: PrecursorSignal
    sta_lta_ratio: float
    trigger_time: datetime
    severity: str  # "low", "medium", "high", "critical"
    predicted_magnitude: float  # 1-10 scale
    time_to_event: timedelta | None = None
    resident_id: UUID | None = None
    context: dict = None

    def __post_init__(self) -> None:
        """Initialize context if not provided."""
        if self.context is None:
            self.context = {}


class BurnoutEarlyWarning:
    """
    STA/LTA-based early warning system for burnout detection.

    Uses seismology signal processing algorithms to detect sudden
    changes in behavioral patterns that precede burnout events.

    The STA/LTA ratio detects when short-term behavior deviates
    from long-term baseline, similar to detecting earthquake P-waves.

    Example:
        detector = BurnoutEarlyWarning(short_window=5, long_window=30)

        # Time series: daily swap request counts
        swap_data = [0, 1, 0, 1, 0, 1, 0, 2, 3, 5, 7, 8]

        alerts = detector.detect_precursors(
            resident_id=uuid4(),
            signal_type=PrecursorSignal.SWAP_REQUESTS,
            time_series=swap_data
        )
    """

    def __init__(self, short_window: int = 5, long_window: int = 30) -> None:
        """
        Initialize the burnout early warning detector.

        Args:
            short_window: Size of short-term average window (STA)
            long_window: Size of long-term average window (LTA)

        Raises:
            ValueError: If short_window >= long_window
        """
        if short_window >= long_window:
            raise ValueError("short_window must be < long_window")

        self.short_window = short_window
        self.long_window = long_window

        logger.info(
            f"BurnoutEarlyWarning initialized (STA={short_window}, LTA={long_window})"
        )

    @staticmethod
    def classic_sta_lta(data: np.ndarray, nsta: int, nlta: int) -> np.ndarray:
        """
        Compute classic STA/LTA characteristic function.

        Uses sliding windows to compute ratio of short-term average
        to long-term average at each point in the time series.

        Args:
            data: Input signal (1D array)
            nsta: Number of samples for short-term average
            nlta: Number of samples for long-term average

        Returns:
            STA/LTA ratio array (same length as input)

        References:
            Withers et al. (1998) - Comparison of select trigger algorithms
        """
        if len(data) < nlta:
            logger.warning(
                f"Data length ({len(data)}) < LTA window ({nlta}), returning zeros"
            )
            return np.zeros_like(data)

            # Ensure float dtype for division
        data = np.asarray(data, dtype=float)

        # Initialize output
        sta_lta = np.zeros(len(data), dtype=float)

        # Compute squared data for energy calculation
        data_sq = data**2

        # Compute STA/LTA for each valid position
        for i in range(nlta, len(data)):
            # Short-term average (recent window)
            sta_start = max(0, i - nsta + 1)
            sta = np.mean(data_sq[sta_start : i + 1])

            # Long-term average (historical window)
            lta_start = max(0, i - nlta + 1)
            lta = np.mean(data_sq[lta_start : i + 1])

            # Compute ratio (avoid division by zero)
            if lta > 1e-10:
                sta_lta[i] = sta / lta
            else:
                sta_lta[i] = 0.0

        return sta_lta

    @staticmethod
    def recursive_sta_lta(data: np.ndarray, nsta: int, nlta: int) -> np.ndarray:
        """
        Compute recursive STA/LTA (memory-efficient version).

        Uses exponential moving average instead of sliding windows,
        making it more suitable for real-time processing with lower
        memory overhead.

        Args:
            data: Input signal (1D array)
            nsta: Number of samples for STA window (determines decay)
            nlta: Number of samples for LTA window (determines decay)

        Returns:
            STA/LTA ratio array (same length as input)

        References:
            Allen (1978) - Automatic earthquake recognition
        """
        if len(data) == 0:
            return np.array([])

        data = np.asarray(data, dtype=float)

        # Decay factors for exponential moving average
        # alpha = 2 / (N + 1) is standard EMA formula
        alpha_sta = 2.0 / (nsta + 1)
        alpha_lta = 2.0 / (nlta + 1)

        # Initialize
        sta = 0.0
        lta = 0.0
        sta_lta = np.zeros(len(data), dtype=float)

        # Compute recursive averages
        for i in range(len(data)):
            value_sq = data[i] ** 2

            # Update exponential moving averages
            sta = alpha_sta * value_sq + (1 - alpha_sta) * sta
            lta = alpha_lta * value_sq + (1 - alpha_lta) * lta

            # Compute ratio
            if lta > 1e-10:
                sta_lta[i] = sta / lta
            else:
                sta_lta[i] = 0.0

        return sta_lta

    @staticmethod
    def trigger_onset(
        sta_lta: np.ndarray, on_threshold: float = 2.5, off_threshold: float = 1.0
    ) -> list[tuple[int, int]]:
        """
        Detect trigger on/off times from STA/LTA characteristic function.

        Identifies periods where the STA/LTA ratio exceeds the threshold,
        indicating anomalous behavior. Uses hysteresis (different on/off
        thresholds) to avoid flickering.

        Args:
            sta_lta: STA/LTA ratio array
            on_threshold: Ratio threshold for trigger activation
            off_threshold: Ratio threshold for trigger deactivation

        Returns:
            List of (start_idx, end_idx) tuples for each triggered period

        Example:
            triggers = trigger_onset(sta_lta, on_threshold=2.5, off_threshold=1.0)
            for start, end in triggers:
                print(f"Anomaly from index {start} to {end}")
        """
        if len(sta_lta) == 0:
            return []

        triggers = []
        is_triggered = False
        trigger_start = 0

        for i in range(len(sta_lta)):
            if not is_triggered:
                # Check for trigger activation
                if sta_lta[i] >= on_threshold:
                    is_triggered = True
                    trigger_start = i
            else:
                # Check for trigger deactivation
                if sta_lta[i] < off_threshold:
                    is_triggered = False
                    triggers.append((trigger_start, i))

                    # Handle case where trigger is still active at end
        if is_triggered:
            triggers.append((trigger_start, len(sta_lta) - 1))

        return triggers

    def detect_precursors(
        self, resident_id: UUID, signal_type: PrecursorSignal, time_series: list[float]
    ) -> list[SeismicAlert]:
        """
        Detect burnout precursor signals in time series data.

        Applies STA/LTA analysis to identify anomalous patterns
        that may indicate approaching burnout.

        Args:
            resident_id: ID of resident being monitored
            signal_type: Type of precursor signal
            time_series: Time series data (chronological order)

        Returns:
            List of SeismicAlert objects for detected anomalies

        Example:
            # Daily swap request counts for last 60 days
            swap_counts = [0, 1, 0, 1, 0, 1, 0, 2, 3, 5, 7, 8, ...]

            alerts = detector.detect_precursors(
                resident_id=person.id,
                signal_type=PrecursorSignal.SWAP_REQUESTS,
                time_series=swap_counts
            )
        """
        if len(time_series) < self.long_window:
            logger.warning(
                f"Time series too short ({len(time_series)} < {self.long_window}), "
                f"cannot analyze {signal_type} for resident {resident_id}"
            )
            return []

            # Convert to numpy array
        data = np.array(time_series, dtype=float)

        # Compute STA/LTA using recursive method (more efficient)
        sta_lta = self.recursive_sta_lta(data, self.short_window, self.long_window)

        # Detect trigger points
        triggers = self.trigger_onset(sta_lta, on_threshold=2.5, off_threshold=1.0)

        if not triggers:
            logger.debug(
                f"No triggers detected for {signal_type}, resident {resident_id}"
            )
            return []

            # Generate alerts for each trigger
        alerts = []
        for start_idx, end_idx in triggers:
            # Maximum STA/LTA ratio during this trigger
            max_ratio = float(np.max(sta_lta[start_idx : end_idx + 1]))

            # Determine severity based on ratio magnitude
            if max_ratio >= 10.0:
                severity = "critical"
            elif max_ratio >= 5.0:
                severity = "high"
            elif max_ratio >= 3.5:
                severity = "medium"
            else:
                severity = "low"

                # Estimate signal growth rate (for time-to-event prediction)
            if end_idx > start_idx:
                growth_rate = (sta_lta[end_idx] - sta_lta[start_idx]) / (
                    end_idx - start_idx
                )
            else:
                growth_rate = 0.0

                # Predict burnout magnitude
            magnitude = self._estimate_magnitude(max_ratio, signal_type)

            # Estimate time to burnout event
            time_to_event = None
            if growth_rate > 0.01:  # Significant growth
                time_to_event = self.estimate_time_to_event(max_ratio, growth_rate)

            alert = SeismicAlert(
                signal_type=signal_type,
                sta_lta_ratio=max_ratio,
                trigger_time=datetime.now(),
                severity=severity,
                predicted_magnitude=magnitude,
                time_to_event=time_to_event,
                resident_id=resident_id,
                context={
                    "trigger_start_idx": start_idx,
                    "trigger_end_idx": end_idx,
                    "growth_rate": growth_rate,
                    "window_data": time_series[start_idx : end_idx + 1],
                },
            )

            alerts.append(alert)

            logger.warning(
                f"Burnout precursor detected: {signal_type} for resident {resident_id}, "
                f"severity={severity}, ratio={max_ratio:.2f}, magnitude={magnitude:.1f}"
            )

        return alerts

    def predict_burnout_magnitude(
        self, precursor_signals: dict[PrecursorSignal, list[float]]
    ) -> float:
        """
        Predict burnout magnitude from multiple precursor signals.

        Combines evidence from multiple signal types to estimate
        the severity of potential burnout event on a 1-10 scale.

        Args:
            precursor_signals: Dict mapping signal types to time series

        Returns:
            Predicted magnitude (1-10 scale, similar to Richter scale)

        Example:
            signals = {
                PrecursorSignal.SWAP_REQUESTS: [0, 1, 2, 5, 8],
                PrecursorSignal.SICK_CALLS: [0, 0, 1, 2, 3],
                PrecursorSignal.RESPONSE_DELAYS: [1, 2, 3, 8, 12]
            }
            magnitude = detector.predict_burnout_magnitude(signals)
        """
        if not precursor_signals:
            return 0.0

            # Analyze each signal
        signal_magnitudes = []

        for signal_type, time_series in precursor_signals.items():
            if len(time_series) < self.long_window:
                continue

                # Compute STA/LTA
            data = np.array(time_series, dtype=float)
            sta_lta = self.recursive_sta_lta(data, self.short_window, self.long_window)

            # Get maximum ratio
            max_ratio = float(np.max(sta_lta))

            # Convert to magnitude estimate
            magnitude = self._estimate_magnitude(max_ratio, signal_type)
            signal_magnitudes.append(magnitude)

        if not signal_magnitudes:
            return 0.0

            # Combine using weighted average and maximum
            # (Multiple signals increase confidence)
        avg_magnitude = np.mean(signal_magnitudes)
        max_magnitude = np.max(signal_magnitudes)

        # Weight toward maximum but consider average
        # (Similar to seismology using multiple stations)
        combined_magnitude = 0.7 * max_magnitude + 0.3 * avg_magnitude

        # Apply bonus for multiple simultaneous signals
        if len(signal_magnitudes) >= 3:
            combined_magnitude *= 1.2  # 20% increase for multi-signal confirmation

            # Clamp to 1-10 range
        combined_magnitude = np.clip(combined_magnitude, 1.0, 10.0)

        logger.info(
            f"Predicted burnout magnitude: {combined_magnitude:.1f} "
            f"(from {len(signal_magnitudes)} signals)"
        )

        return float(combined_magnitude)

    def estimate_time_to_event(
        self, sta_lta_ratio: float, signal_growth_rate: float
    ) -> timedelta:
        """
        Estimate time until burnout event occurs.

        Uses current ratio and growth rate to predict when
        critical threshold will be reached.

        Args:
            sta_lta_ratio: Current STA/LTA ratio
            signal_growth_rate: Rate of ratio increase per time unit

        Returns:
            Estimated time until burnout event

        Notes:
            - Critical threshold is ratio = 10.0
            - Assumes linear growth (conservative estimate)
            - Returns minimum of 1 day for safety margin
        """
        # Critical threshold for burnout event
        critical_threshold = 10.0

        if signal_growth_rate <= 0.0:
            # Not growing - return large value
            return timedelta(days=365)

        if sta_lta_ratio >= critical_threshold:
            # Already at critical threshold
            return timedelta(days=1)

            # Linear extrapolation (conservative)
        days_to_critical = (critical_threshold - sta_lta_ratio) / signal_growth_rate

        # Clamp to reasonable range (1-365 days)
        days_to_critical = np.clip(days_to_critical, 1.0, 365.0)

        return timedelta(days=float(days_to_critical))

    @staticmethod
    def _estimate_magnitude(
        sta_lta_ratio: float, signal_type: PrecursorSignal
    ) -> float:
        """
        Estimate burnout magnitude from STA/LTA ratio.

        Different signal types have different severity interpretations.

        Args:
            sta_lta_ratio: Detected STA/LTA ratio
            signal_type: Type of precursor signal

        Returns:
            Magnitude estimate (1-10 scale)
        """
        # Base magnitude from logarithmic scale (like Richter)
        # log2(ratio) maps: 2->1, 4->2, 8->3, 16->4, etc.
        base_magnitude = np.log2(max(1.0, sta_lta_ratio))

        # Apply signal-type specific weights
        # (Some signals are stronger predictors than others)
        weights = {
            PrecursorSignal.SWAP_REQUESTS: 1.0,  # Moderate indicator
            PrecursorSignal.SICK_CALLS: 1.3,  # Strong indicator
            PrecursorSignal.PREFERENCE_DECLINE: 1.2,  # Strong indicator
            PrecursorSignal.RESPONSE_DELAYS: 0.9,  # Moderate indicator
            PrecursorSignal.VOLUNTARY_COVERAGE_DECLINE: 1.1,  # Moderate-strong
        }

        weight = weights.get(signal_type, 1.0)
        magnitude = base_magnitude * weight

        # Clamp to 1-10 range
        magnitude = np.clip(magnitude, 1.0, 10.0)

        return float(magnitude)
