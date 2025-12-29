"""
Signal Processing Suite for Workload Pattern Analysis.

This module provides frequency domain analysis tools for medical residency
scheduling, including wavelet transforms, FFT, spectral decomposition, and
anomaly detection algorithms adapted from seismic analysis.

Key Capabilities:
-----------------
1. Multi-Resolution Wavelet Analysis: Decompose workload into daily/weekly/monthly
   patterns using discrete and continuous wavelet transforms.

2. FFT Pipeline: Identify periodic patterns in resident schedules through
   Fourier analysis.

3. STA/LTA Anomaly Detection: Adapted from seismic analysis to detect sudden
   workload pattern changes (borrowed from earthquake detection).

4. Spectral Decomposition: Separate workload into trend, seasonal, and residual
   components for cleaner analysis.

5. Frequency-Based Constraint Validation: Detect physically impossible scheduling
   patterns (e.g., too-rapid shift alternations).

6. Adaptive Filtering: Remove noise from workload predictions while preserving
   true patterns.

7. Harmonic Analysis: Identify resonances between shift patterns that could
   indicate systemic scheduling issues.

8. Change Point Detection: Detect regime shifts, policy changes, and structural
   breaks using CUSUM and PELT algorithms.

Cross-Disciplinary Origins:
---------------------------
- Seismology: STA/LTA algorithm for detecting earthquakes
- Signal Processing: Wavelet transforms, FFT, spectral analysis
- Telecommunications: Adaptive filtering (Wiener, Kalman)
- Music: Harmonic analysis for resonance detection

References:
-----------
- Mallat, S. (2009). A Wavelet Tour of Signal Processing, 3rd ed.
- Allen, R.V. (1978). Automatic earthquake recognition and timing from
  single traces. Bulletin of the Seismological Society of America.
- Oppenheim, A.V. & Schafer, R.W. (2010). Discrete-Time Signal Processing.

Usage:
------
    from app.analytics.signal_processing import WorkloadSignalProcessor

    processor = WorkloadSignalProcessor()

    # Analyze workload patterns
    result = processor.analyze_workload_patterns(
        workload_series=daily_hours,
        dates=date_list,
        analysis_types=["wavelet", "fft", "sta_lta", "changepoint"]
    )

    # Detect change points for regime shifts
    changepoint_results = processor.analyze_schedule_changepoints(ts)

    # Export for visualization
    json_data = processor.export_to_holographic_format(result)
"""

import logging
import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import TypedDict
from uuid import UUID

import numpy as np
from numpy.typing import NDArray
from scipy import signal as scipy_signal
from scipy.fft import fft, fftfreq, ifft
from scipy.ndimage import uniform_filter1d
from scipy.stats import zscore

# Try to import pywt (PyWavelets)
try:
    import pywt

    HAS_PYWT = True
except ImportError:
    HAS_PYWT = False
    pywt = None  # type: ignore

# Try to import statsmodels for STL decomposition
try:
    from statsmodels.tsa.seasonal import STL

    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    STL = None  # type: ignore

logger = logging.getLogger(__name__)


# =============================================================================
# Type Definitions
# =============================================================================


class WaveletFamily(str, Enum):
    """Supported wavelet families for analysis."""

    DAUBECHIES = "db"  # Daubechies wavelets (db1-db20)
    SYMLET = "sym"  # Symlets (sym2-sym20)
    COIFLET = "coif"  # Coiflets (coif1-coif17)
    HAAR = "haar"  # Haar wavelet (simplest)
    MEXICAN_HAT = "mexh"  # Mexican hat (for continuous WT)
    MORLET = "morl"  # Morlet wavelet (for time-frequency)


class AnomalyType(str, Enum):
    """Types of detected anomalies."""

    WORKLOAD_SPIKE = "workload_spike"
    WORKLOAD_DROP = "workload_drop"
    PATTERN_CHANGE = "pattern_change"
    RAPID_ALTERNATION = "rapid_alternation"
    SUSTAINED_OVERLOAD = "sustained_overload"
    HARMONIC_RESONANCE = "harmonic_resonance"


class FrequencyBand(str, Enum):
    """Frequency bands for workload analysis."""

    DAILY = "daily"  # < 1 cycle per day
    WEEKLY = "weekly"  # 1 cycle per week (0.14 cycles/day)
    BIWEEKLY = "biweekly"  # 2 weeks
    MONTHLY = "monthly"  # ~30 days
    QUARTERLY = "quarterly"  # ~90 days


# TypedDict definitions for JSON-serializable outputs


class WaveletCoefficients(TypedDict):
    """Wavelet decomposition coefficients."""

    level: int
    approximation: list[float]
    details: list[list[float]]
    frequency_bands: list[str]


class FFTResult(TypedDict):
    """FFT analysis result."""

    frequencies: list[float]
    magnitudes: list[float]
    phases: list[float]
    dominant_frequencies: list[dict]
    periodicity_detected: bool


class STALTAResult(TypedDict):
    """STA/LTA anomaly detection result."""

    characteristic_function: list[float]
    anomalies: list[dict]
    trigger_threshold: float
    detection_rate: float


class SpectralComponent(TypedDict):
    """Component from spectral decomposition."""

    name: str
    values: list[float]
    statistics: dict


class HarmonicPeak(TypedDict):
    """Detected harmonic peak."""

    frequency: float
    period_days: float
    magnitude: float
    phase: float
    significance: float


class ConstraintViolation(TypedDict):
    """Frequency-based constraint violation."""

    violation_type: str
    location_indices: list[int]
    severity: str
    description: str


class SignalAnalysisResult(TypedDict, total=False):
    """Complete signal analysis result."""

    analysis_id: str
    generated_at: str
    input_summary: dict
    wavelet_analysis: WaveletCoefficients | None
    cwt_analysis: dict | None
    fft_analysis: FFTResult | None
    sta_lta_analysis: STALTAResult | None
    spectral_decomposition: dict | None
    constraint_violations: list[ConstraintViolation]
    harmonic_analysis: dict | None
    adaptive_filtered: dict | None
    changepoint_analysis: dict[str, ChangePointAnalysisResult] | None
    recommendations: list[str]


class HolographicExport(TypedDict):
    """Export format for holographic visualization."""

    version: str
    export_type: str
    generated_at: str
    time_domain: dict
    frequency_domain: dict
    wavelet_domain: dict
    anomalies: list[dict]
    metadata: dict


class ChangePoint(TypedDict):
    """Detected change point in time series."""

    index: int
    timestamp: str  # ISO format date
    change_type: str  # mean_shift, variance_change, trend_change
    magnitude: float
    confidence: float  # 0-1
    description: str


class ChangePointAnalysisResult(TypedDict):
    """Result of change point detection analysis."""

    method: str  # cusum, pelt, or ensemble
    change_points: list[ChangePoint]
    num_changepoints: int
    segmentation_quality: float  # 0-1, higher is better
    algorithm_parameters: dict


# =============================================================================
# Dataclasses for Internal Processing
# =============================================================================


@dataclass
class WorkloadTimeSeries:
    """Workload time series data with metadata."""

    values: NDArray[np.float64]
    dates: list[date]
    person_id: UUID | None = None
    sample_rate_per_day: float = 1.0  # 1 = daily samples
    units: str = "hours"

    def __post_init__(self) -> None:
        """Validate time series data."""
        if len(self.values) != len(self.dates):
            raise ValueError("Values and dates must have same length")
        if len(self.values) < 4:
            raise ValueError("Time series must have at least 4 points")

    @property
    def duration_days(self) -> int:
        """Total duration in days."""
        return (self.dates[-1] - self.dates[0]).days + 1

    @property
    def nyquist_frequency(self) -> float:
        """Nyquist frequency (highest detectable frequency)."""
        return self.sample_rate_per_day / 2.0


@dataclass
class AnomalyEvent:
    """Detected anomaly event."""

    anomaly_type: AnomalyType
    index: int
    timestamp: date
    severity: float  # 0.0 to 1.0
    sta_lta_ratio: float | None = None
    description: str = ""
    related_indices: list[int] = field(default_factory=list)


@dataclass
class FrequencyConstraint:
    """Constraint on allowable frequency patterns."""

    name: str
    max_frequency: float  # cycles per day
    min_period_days: float  # minimum period in days
    description: str
    severity: str = "warning"  # "info", "warning", "error"


# =============================================================================
# Core Signal Processing Functions
# =============================================================================


def _ensure_power_of_two(n: int) -> int:
    """Round up to nearest power of two for FFT efficiency."""
    return 1 << (n - 1).bit_length()


def _pad_signal(signal: NDArray[np.float64], target_length: int) -> NDArray[np.float64]:
    """Zero-pad signal to target length."""
    if len(signal) >= target_length:
        return signal[:target_length]
    padded = np.zeros(target_length)
    padded[: len(signal)] = signal
    return padded


def _detrend_signal(
    signal: NDArray[np.float64], method: str = "linear"
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Remove trend from signal.

    Args:
        signal: Input signal
        method: "linear" or "mean"

    Returns:
        Tuple of (detrended signal, trend)
    """
    if method == "mean":
        trend = np.full_like(signal, np.mean(signal))
    else:  # linear
        x = np.arange(len(signal))
        coeffs = np.polyfit(x, signal, 1)
        trend = np.polyval(coeffs, x)

    return signal - trend, trend


# =============================================================================
# Main Signal Processor Class
# =============================================================================


class WorkloadSignalProcessor:
    """
    Signal processing engine for workload pattern analysis.

    This class provides comprehensive frequency-domain analysis of medical
    residency workload patterns, enabling detection of periodic patterns,
    anomalies, and constraint violations.

    The processor implements multiple signal analysis techniques:

    1. Discrete Wavelet Transform (DWT): Multi-resolution decomposition
       into daily, weekly, and monthly components.

    2. Continuous Wavelet Transform (CWT): Time-frequency analysis for
       detecting transient patterns.

    3. Fast Fourier Transform (FFT): Identify dominant periodicities in
       schedule patterns.

    4. STA/LTA Detector: Adapted from seismology for detecting sudden
       workload changes.

    5. STL Decomposition: Separate trend, seasonal, and residual components.

    6. Adaptive Filtering: Noise reduction while preserving true patterns.

    7. Harmonic Analysis: Detect resonances between shift patterns.

    Example:
        processor = WorkloadSignalProcessor()

        # Create time series from daily hours
        ts = WorkloadTimeSeries(
            values=np.array(daily_hours),
            dates=date_list,
            person_id=resident_uuid
        )

        # Full analysis
        result = processor.analyze_workload_patterns(ts)

        # Export for visualization
        export_data = processor.export_to_holographic_format(result, ts)
    """

    # Default frequency constraints for medical scheduling
    DEFAULT_CONSTRAINTS: list[FrequencyConstraint] = [
        FrequencyConstraint(
            name="minimum_rest_period",
            max_frequency=1.0,  # max 1 on/off cycle per day
            min_period_days=1.0,
            description="Cannot alternate on/off faster than once per day",
            severity="error",
        ),
        FrequencyConstraint(
            name="minimum_recovery_period",
            max_frequency=0.5,  # max 1 cycle per 2 days
            min_period_days=2.0,
            description="After call, minimum 1 day rest recommended",
            severity="warning",
        ),
        FrequencyConstraint(
            name="weekly_rest_requirement",
            max_frequency=1.0 / 7.0,  # 1 day off per 7 days
            min_period_days=7.0,
            description="ACGME requires 1 day off every 7 days",
            severity="error",
        ),
    ]

    def __init__(
        self,
        wavelet: str = "db4",
        decomposition_level: int | None = None,
        sta_window: int = 5,
        lta_window: int = 20,
        sta_lta_threshold: float = 3.0,
        constraints: list[FrequencyConstraint] | None = None,
    ):
        """
        Initialize the signal processor.

        Args:
            wavelet: Wavelet to use for DWT (default: Daubechies 4)
            decomposition_level: Number of wavelet decomposition levels
                (None = auto-calculate based on signal length)
            sta_window: Short-term average window for STA/LTA (days)
            lta_window: Long-term average window for STA/LTA (days)
            sta_lta_threshold: Threshold for anomaly detection
            constraints: Frequency constraints (None = use defaults)
        """
        self.wavelet = wavelet
        self.decomposition_level = decomposition_level
        self.sta_window = sta_window
        self.lta_window = lta_window
        self.sta_lta_threshold = sta_lta_threshold
        self.constraints = constraints or self.DEFAULT_CONSTRAINTS

        logger.info(
            f"Initialized WorkloadSignalProcessor: wavelet={wavelet}, "
            f"STA={sta_window}d, LTA={lta_window}d, threshold={sta_lta_threshold}"
        )

    # =========================================================================
    # Wavelet Transform Methods
    # =========================================================================

    def discrete_wavelet_transform(
        self,
        ts: WorkloadTimeSeries,
        level: int | None = None,
    ) -> WaveletCoefficients:
        """
        Perform discrete wavelet transform for multi-resolution analysis.

        The DWT decomposes the workload signal into approximation (trend)
        and detail (fluctuation) coefficients at multiple scales:

        - Level 1: Daily fluctuations (high frequency)
        - Level 2: 2-3 day patterns
        - Level 3: Weekly patterns
        - Level 4: Biweekly patterns
        - Level 5+: Monthly and longer patterns

        Args:
            ts: Workload time series
            level: Decomposition level (None = auto-calculate)

        Returns:
            WaveletCoefficients with approximation and detail coefficients
        """
        if not HAS_PYWT:
            logger.warning("PyWavelets not installed, returning empty result")
            return {
                "level": 0,
                "approximation": [],
                "details": [],
                "frequency_bands": [],
            }

        # Auto-calculate level if not specified
        if level is None:
            level = self.decomposition_level or min(
                pywt.dwt_max_level(len(ts.values), self.wavelet),
                5,  # Cap at 5 levels for interpretability
            )

        # Perform wavelet decomposition
        coeffs = pywt.wavedec(ts.values, self.wavelet, level=level)

        # Extract approximation and details
        approximation = coeffs[0]
        details = coeffs[1:]

        # Map levels to frequency bands
        frequency_bands = []
        for i in range(level):
            period_days = 2 ** (i + 1)  # Each level doubles the period
            if period_days <= 2:
                band = FrequencyBand.DAILY.value
            elif period_days <= 7:
                band = FrequencyBand.WEEKLY.value
            elif period_days <= 14:
                band = FrequencyBand.BIWEEKLY.value
            elif period_days <= 30:
                band = FrequencyBand.MONTHLY.value
            else:
                band = FrequencyBand.QUARTERLY.value
            frequency_bands.append(band)

        logger.debug(
            f"DWT completed: level={level}, "
            f"approx_len={len(approximation)}, "
            f"detail_levels={len(details)}"
        )

        return {
            "level": level,
            "approximation": approximation.tolist(),
            "details": [d.tolist() for d in details],
            "frequency_bands": frequency_bands,
        }

    def continuous_wavelet_transform(
        self,
        ts: WorkloadTimeSeries,
        wavelet: str = "morl",
        scales: NDArray[np.float64] | None = None,
    ) -> dict:
        """
        Perform continuous wavelet transform for time-frequency analysis.

        CWT provides higher time-frequency resolution than DWT, useful for:
        - Detecting transient patterns (temporary workload spikes)
        - Identifying when patterns change over time
        - Visualizing schedule "rhythm" in time-frequency space

        Args:
            ts: Workload time series
            wavelet: Wavelet to use (default: Morlet)
            scales: Scale values (None = auto-generate)

        Returns:
            Dict with CWT coefficients and scale information
        """
        if not HAS_PYWT:
            logger.warning("PyWavelets not installed, returning empty CWT result")
            return {
                "coefficients": [],
                "scales": [],
                "frequencies": [],
                "power": [],
            }

        # Generate scales if not provided (logarithmic spacing)
        if scales is None:
            # Scales corresponding to periods from 2 days to half the signal length
            min_scale = 1
            max_scale = min(len(ts.values) // 2, 64)
            num_scales = min(32, max_scale - min_scale + 1)
            scales = np.logspace(
                np.log10(min_scale), np.log10(max_scale), num_scales
            ).astype(np.float64)

        # Perform CWT
        coefficients, frequencies = pywt.cwt(
            ts.values, scales, wavelet, sampling_period=1.0 / ts.sample_rate_per_day
        )

        # Calculate power (magnitude squared)
        power = np.abs(coefficients) ** 2

        # Convert to periods for interpretability
        periods = 1.0 / np.where(frequencies > 0, frequencies, np.inf)

        logger.debug(
            f"CWT completed: shape={coefficients.shape}, "
            f"scale_range=[{scales[0]:.1f}, {scales[-1]:.1f}]"
        )

        return {
            "coefficients": np.abs(coefficients).tolist(),  # Magnitude only for JSON
            "scales": scales.tolist(),
            "frequencies": frequencies.tolist(),
            "periods": periods.tolist(),
            "power": power.tolist(),
            "time_indices": list(range(len(ts.values))),
        }

    def wavelet_reconstruct(
        self,
        coeffs: WaveletCoefficients,
        keep_levels: list[int] | None = None,
    ) -> NDArray[np.float64]:
        """
        Reconstruct signal from wavelet coefficients.

        Useful for filtering: keep only specific frequency bands.

        Args:
            coeffs: Wavelet coefficients from DWT
            keep_levels: Which detail levels to keep (None = all)

        Returns:
            Reconstructed signal
        """
        if not HAS_PYWT:
            logger.warning("PyWavelets not installed, cannot reconstruct")
            return np.array(coeffs["approximation"])

        # Prepare coefficients for reconstruction
        approx = np.array(coeffs["approximation"])
        details = [np.array(d) for d in coeffs["details"]]

        # Zero out unwanted levels
        if keep_levels is not None:
            for i in range(len(details)):
                if i not in keep_levels:
                    details[i] = np.zeros_like(details[i])

        # Reconstruct
        all_coeffs = [approx] + details
        reconstructed = pywt.waverec(all_coeffs, self.wavelet)

        return reconstructed

    # =========================================================================
    # FFT Methods
    # =========================================================================

    def fft_analysis(
        self,
        ts: WorkloadTimeSeries,
        n_dominant: int = 5,
        min_significance: float = 0.1,
    ) -> FFTResult:
        """
        Perform FFT analysis to identify periodic patterns.

        The FFT reveals dominant periodicities in the schedule:
        - 7-day period = strong weekly pattern
        - 14-day period = biweekly rotation
        - 30-day period = monthly block rotation

        Args:
            ts: Workload time series
            n_dominant: Number of dominant frequencies to report
            min_significance: Minimum relative magnitude for significance

        Returns:
            FFTResult with frequencies, magnitudes, and dominant peaks
        """
        # Detrend to focus on oscillations
        detrended, _ = _detrend_signal(ts.values)

        # Apply Hann window to reduce spectral leakage
        window = np.hanning(len(detrended))
        windowed = detrended * window

        # Pad to power of 2 for efficiency
        n_fft = _ensure_power_of_two(len(windowed))
        padded = _pad_signal(windowed, n_fft)

        # Compute FFT
        fft_result = fft(padded)
        frequencies = fftfreq(n_fft, d=1.0 / ts.sample_rate_per_day)

        # Get positive frequencies only
        positive_mask = frequencies > 0
        pos_freqs = frequencies[positive_mask]
        pos_fft = fft_result[positive_mask]

        # Magnitudes and phases
        magnitudes = np.abs(pos_fft)
        phases = np.angle(pos_fft)

        # Normalize magnitudes
        max_magnitude = np.max(magnitudes) if len(magnitudes) > 0 else 1.0
        normalized_magnitudes = magnitudes / max_magnitude if max_magnitude > 0 else magnitudes

        # Find dominant frequencies
        dominant = []
        if len(magnitudes) > 0:
            # Find peaks
            peak_indices, _ = scipy_signal.find_peaks(
                normalized_magnitudes, height=min_significance
            )

            # Sort by magnitude
            sorted_peaks = sorted(peak_indices, key=lambda i: -magnitudes[i])

            for idx in sorted_peaks[:n_dominant]:
                freq = float(pos_freqs[idx])
                period = 1.0 / freq if freq > 0 else float("inf")
                dominant.append(
                    {
                        "frequency": freq,
                        "period_days": period,
                        "magnitude": float(magnitudes[idx]),
                        "normalized_magnitude": float(normalized_magnitudes[idx]),
                        "phase": float(phases[idx]),
                    }
                )

        # Check if periodicity is detected (strong peaks)
        periodicity_detected = any(d["normalized_magnitude"] > 0.5 for d in dominant)

        logger.debug(
            f"FFT analysis: {len(dominant)} dominant frequencies found, "
            f"periodicity_detected={periodicity_detected}"
        )

        return {
            "frequencies": pos_freqs.tolist(),
            "magnitudes": magnitudes.tolist(),
            "phases": phases.tolist(),
            "dominant_frequencies": dominant,
            "periodicity_detected": periodicity_detected,
        }

    def inverse_fft_filter(
        self,
        ts: WorkloadTimeSeries,
        keep_frequencies: list[float] | None = None,
        remove_frequencies: list[float] | None = None,
        bandwidth: float = 0.05,
    ) -> NDArray[np.float64]:
        """
        Filter signal by keeping or removing specific frequencies.

        Args:
            ts: Workload time series
            keep_frequencies: Frequencies to keep (None = keep all)
            remove_frequencies: Frequencies to remove (None = remove none)
            bandwidth: Frequency bandwidth for selection

        Returns:
            Filtered signal
        """
        # Compute FFT
        n_fft = _ensure_power_of_two(len(ts.values))
        padded = _pad_signal(ts.values, n_fft)
        fft_result = fft(padded)
        frequencies = fftfreq(n_fft, d=1.0 / ts.sample_rate_per_day)

        # Create filter mask
        mask = np.ones(n_fft, dtype=bool)

        if keep_frequencies is not None:
            mask = np.zeros(n_fft, dtype=bool)
            for freq in keep_frequencies:
                mask |= np.abs(np.abs(frequencies) - freq) < bandwidth

        if remove_frequencies is not None:
            for freq in remove_frequencies:
                mask &= np.abs(np.abs(frequencies) - freq) >= bandwidth

        # Always keep DC component
        mask[0] = True

        # Apply filter
        filtered_fft = fft_result * mask.astype(float)

        # Inverse FFT
        filtered = np.real(ifft(filtered_fft))[: len(ts.values)]

        return filtered

    # =========================================================================
    # STA/LTA Anomaly Detection
    # =========================================================================

    def sta_lta_detector(
        self,
        ts: WorkloadTimeSeries,
        sta_window: int | None = None,
        lta_window: int | None = None,
        threshold: float | None = None,
    ) -> STALTAResult:
        """
        STA/LTA anomaly detector adapted from seismic analysis.

        The Short-Term Average / Long-Term Average algorithm detects sudden
        changes in signal characteristics. Originally used for earthquake
        detection, it's effective for identifying:

        - Sudden workload spikes (P-wave equivalent)
        - Rapid pattern changes (S-wave equivalent)
        - Sustained overload onset

        Algorithm:
        1. Calculate short-term average (STA) over recent samples
        2. Calculate long-term average (LTA) over extended window
        3. Compute ratio: when STA >> LTA, an event is occurring
        4. Trigger when ratio exceeds threshold

        Args:
            ts: Workload time series
            sta_window: Short-term window (days)
            lta_window: Long-term window (days)
            threshold: Trigger threshold for ratio

        Returns:
            STALTAResult with characteristic function and detected anomalies
        """
        sta_window = sta_window or self.sta_window
        lta_window = lta_window or self.lta_window
        threshold = threshold or self.sta_lta_threshold

        # Ensure windows fit the data
        if len(ts.values) < lta_window:
            lta_window = len(ts.values) // 2
            sta_window = max(1, lta_window // 4)

        # Calculate characteristic function (absolute values for energy detection)
        signal = np.abs(ts.values - np.mean(ts.values))

        # Calculate STA and LTA using uniform filter
        sta = uniform_filter1d(signal, sta_window, mode="nearest")
        lta = uniform_filter1d(signal, lta_window, mode="nearest")

        # Avoid division by zero
        lta = np.where(lta > 0, lta, 1e-10)

        # STA/LTA ratio (characteristic function)
        cf = sta / lta

        # Detect triggers (ratio exceeds threshold)
        triggers = np.where(cf > threshold)[0]

        # Group consecutive triggers into events
        anomalies = []
        if len(triggers) > 0:
            # Find event boundaries
            gaps = np.diff(triggers)
            event_starts = [triggers[0]]
            for i, gap in enumerate(gaps):
                if gap > sta_window:  # New event if gap > STA window
                    event_starts.append(triggers[i + 1])

            for start_idx in event_starts:
                # Find event end
                event_end = start_idx
                for idx in range(start_idx, len(cf)):
                    if cf[idx] < threshold * 0.7:  # Event ends when ratio drops
                        event_end = idx
                        break
                    event_end = idx

                # Determine anomaly type based on signal characteristics
                event_values = ts.values[start_idx : event_end + 1]
                pre_event = ts.values[max(0, start_idx - lta_window) : start_idx]

                if len(pre_event) > 0 and len(event_values) > 0:
                    mean_event = np.mean(event_values)
                    mean_pre = np.mean(pre_event)

                    if mean_event > mean_pre * 1.2:
                        atype = AnomalyType.WORKLOAD_SPIKE
                        desc = f"Workload spike: {mean_pre:.1f} → {mean_event:.1f}"
                    elif mean_event < mean_pre * 0.8:
                        atype = AnomalyType.WORKLOAD_DROP
                        desc = f"Workload drop: {mean_pre:.1f} → {mean_event:.1f}"
                    else:
                        atype = AnomalyType.PATTERN_CHANGE
                        desc = f"Pattern change at index {start_idx}"
                else:
                    atype = AnomalyType.PATTERN_CHANGE
                    desc = f"Pattern change at index {start_idx}"

                severity = min(1.0, (cf[start_idx] - threshold) / threshold)

                anomaly = AnomalyEvent(
                    anomaly_type=atype,
                    index=int(start_idx),
                    timestamp=ts.dates[start_idx] if start_idx < len(ts.dates) else ts.dates[-1],
                    severity=severity,
                    sta_lta_ratio=float(cf[start_idx]),
                    description=desc,
                    related_indices=list(range(start_idx, min(event_end + 1, len(ts.values)))),
                )
                anomalies.append(anomaly)

        detection_rate = len(anomalies) / (len(ts.values) / 30)  # Per 30 days

        logger.debug(
            f"STA/LTA: {len(anomalies)} anomalies detected, "
            f"detection_rate={detection_rate:.2f}/month"
        )

        return {
            "characteristic_function": cf.tolist(),
            "anomalies": [
                {
                    "type": a.anomaly_type.value,
                    "index": a.index,
                    "date": a.timestamp.isoformat(),
                    "severity": a.severity,
                    "sta_lta_ratio": a.sta_lta_ratio,
                    "description": a.description,
                    "related_indices": a.related_indices,
                }
                for a in anomalies
            ],
            "trigger_threshold": threshold,
            "detection_rate": detection_rate,
        }

    # =========================================================================
    # Spectral Decomposition
    # =========================================================================

    def spectral_decomposition(
        self,
        ts: WorkloadTimeSeries,
        period: int = 7,
        seasonal: int = 7,
        robust: bool = True,
    ) -> dict:
        """
        Decompose workload into trend, seasonal, and residual components.

        Uses STL (Seasonal and Trend decomposition using Loess) when
        statsmodels is available, falls back to simple decomposition otherwise.

        Components:
        - Trend: Long-term direction of workload
        - Seasonal: Repeating patterns (weekly, monthly)
        - Residual: Unexplained variation (noise or irregular events)

        Args:
            ts: Workload time series
            period: Seasonal period in days (default: 7 for weekly)
            seasonal: Seasonal smoother length (must be odd)
            robust: Use robust fitting to reduce outlier influence

        Returns:
            Dict with trend, seasonal, and residual components
        """
        if len(ts.values) < 2 * period:
            # Not enough data for decomposition
            return {
                "trend": ts.values.tolist(),
                "seasonal": [0.0] * len(ts.values),
                "residual": [0.0] * len(ts.values),
                "method": "insufficient_data",
                "statistics": {
                    "trend_strength": 0.0,
                    "seasonal_strength": 0.0,
                    "residual_variance": float(np.var(ts.values)),
                },
            }

        if HAS_STATSMODELS:
            # Use STL decomposition
            try:
                stl = STL(
                    ts.values,
                    period=period,
                    seasonal=seasonal if seasonal % 2 == 1 else seasonal + 1,
                    robust=robust,
                )
                result = stl.fit()

                trend = result.trend
                seasonal_component = result.seasonal
                residual = result.resid

                method = "stl"
            except Exception as e:
                logger.warning(f"STL decomposition failed: {e}, using fallback")
                trend, seasonal_component, residual = self._simple_decomposition(
                    ts.values, period
                )
                method = "simple_fallback"
        else:
            # Simple decomposition without statsmodels
            trend, seasonal_component, residual = self._simple_decomposition(ts.values, period)
            method = "simple"

        # Calculate strength metrics
        var_residual = np.var(residual)
        var_detrended = np.var(ts.values - trend)
        var_deseasoned = np.var(ts.values - seasonal_component)

        trend_strength = max(0, 1 - var_residual / var_deseasoned) if var_deseasoned > 0 else 0
        seasonal_strength = max(0, 1 - var_residual / var_detrended) if var_detrended > 0 else 0

        return {
            "trend": trend.tolist() if isinstance(trend, np.ndarray) else list(trend),
            "seasonal": (
                seasonal_component.tolist()
                if isinstance(seasonal_component, np.ndarray)
                else list(seasonal_component)
            ),
            "residual": (
                residual.tolist() if isinstance(residual, np.ndarray) else list(residual)
            ),
            "method": method,
            "period": period,
            "statistics": {
                "trend_strength": float(trend_strength),
                "seasonal_strength": float(seasonal_strength),
                "residual_variance": float(var_residual),
                "residual_mean": float(np.mean(residual)),
                "residual_std": float(np.std(residual)),
            },
        }

    def _simple_decomposition(
        self,
        values: NDArray[np.float64],
        period: int,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
        """Simple moving average decomposition fallback."""
        # Trend: centered moving average
        if period % 2 == 0:
            # Two-pass for even period
            ma = uniform_filter1d(values, period, mode="nearest")
            trend = uniform_filter1d(ma, 2, mode="nearest")
        else:
            trend = uniform_filter1d(values, period, mode="nearest")

        # Detrended
        detrended = values - trend

        # Seasonal: average of detrended values at each seasonal position
        seasonal = np.zeros_like(values)
        for i in range(period):
            seasonal_positions = detrended[i::period]
            seasonal[i::period] = np.mean(seasonal_positions)

        # Residual
        residual = values - trend - seasonal

        return trend, seasonal, residual

    # =========================================================================
    # Frequency-Based Constraint Validation
    # =========================================================================

    def validate_frequency_constraints(
        self,
        ts: WorkloadTimeSeries,
        constraints: list[FrequencyConstraint] | None = None,
    ) -> list[ConstraintViolation]:
        """
        Validate schedule against frequency-based constraints.

        Detects impossible or unhealthy patterns by checking if the
        schedule contains frequency components that violate constraints.

        For example:
        - Alternating on-call every day (too rapid alternation)
        - No weekly rest day (missing 7-day component)
        - Patterns that exceed human endurance limits

        Args:
            ts: Workload time series
            constraints: Constraints to check (None = use defaults)

        Returns:
            List of ConstraintViolation for any detected violations
        """
        constraints = constraints or self.constraints
        violations: list[ConstraintViolation] = []

        # Perform FFT
        fft_result = self.fft_analysis(ts)

        for constraint in constraints:
            # Check for frequencies above the maximum allowed
            for i, freq in enumerate(fft_result["frequencies"]):
                if freq > constraint.max_frequency:
                    # Check if this high frequency has significant power
                    normalized_mag = (
                        fft_result["magnitudes"][i] / max(fft_result["magnitudes"])
                        if max(fft_result["magnitudes"]) > 0
                        else 0
                    )

                    if normalized_mag > 0.2:  # 20% of max power
                        # Find locations where this pattern occurs
                        # (approximate using inverse FFT filter)
                        filtered = self.inverse_fft_filter(
                            ts,
                            keep_frequencies=[freq],
                            bandwidth=0.05,
                        )

                        # Find peaks in filtered signal
                        peaks, _ = scipy_signal.find_peaks(np.abs(filtered))

                        violations.append(
                            {
                                "violation_type": constraint.name,
                                "location_indices": peaks.tolist()[:10],  # First 10
                                "severity": constraint.severity,
                                "description": (
                                    f"{constraint.description}: detected frequency "
                                    f"{freq:.3f} cycles/day (period: {1/freq:.1f} days) "
                                    f"exceeds max {constraint.max_frequency:.3f} cycles/day"
                                ),
                            }
                        )
                        break  # One violation per constraint

        # Also check for rapid alternation using run length
        alternation_violations = self._check_rapid_alternation(ts)
        violations.extend(alternation_violations)

        logger.debug(f"Frequency constraint validation: {len(violations)} violations found")

        return violations

    def _check_rapid_alternation(
        self,
        ts: WorkloadTimeSeries,
        high_threshold: float = 10.0,  # Hours considered "high" workload
        max_alternations: int = 5,  # Max rapid alternations before violation
    ) -> list[ConstraintViolation]:
        """Check for rapid alternation between high and low workload."""
        violations: list[ConstraintViolation] = []

        # Binary signal: high (1) or low (0) workload
        binary = (ts.values > high_threshold).astype(int)

        # Find runs
        changes = np.diff(binary)
        change_indices = np.where(changes != 0)[0]

        # Check for rapid alternation patterns
        if len(change_indices) > max_alternations:
            # Look for consecutive short runs
            for i in range(len(change_indices) - max_alternations):
                window = change_indices[i : i + max_alternations + 1]
                run_lengths = np.diff(window)

                if np.all(run_lengths <= 2):  # All runs <= 2 days
                    violations.append(
                        {
                            "violation_type": "rapid_alternation",
                            "location_indices": list(range(window[0], window[-1] + 1)),
                            "severity": "warning",
                            "description": (
                                f"Rapid workload alternation detected from day "
                                f"{window[0]} to {window[-1]}: pattern changes every "
                                f"1-2 days which may cause fatigue"
                            ),
                        }
                    )
                    break  # One violation is enough

        return violations

    # =========================================================================
    # Adaptive Filtering
    # =========================================================================

    def adaptive_filter(
        self,
        ts: WorkloadTimeSeries,
        method: str = "wiener",
        noise_estimate: float | None = None,
        window_size: int = 5,
    ) -> dict:
        """
        Apply adaptive filtering for noise reduction.

        Removes noise while preserving true workload patterns.

        Methods:
        - wiener: Wiener filter (optimal for stationary noise)
        - savgol: Savitzky-Golay filter (preserves peaks)
        - kalman: Simple Kalman-like smoothing

        Args:
            ts: Workload time series
            method: Filtering method
            noise_estimate: Estimated noise variance (None = auto-estimate)
            window_size: Filter window size

        Returns:
            Dict with filtered signal and quality metrics
        """
        if method == "wiener":
            # Estimate noise if not provided
            if noise_estimate is None:
                # Use median absolute deviation for robust estimate
                residual = np.abs(np.diff(ts.values))
                noise_estimate = float(np.median(residual) * 1.4826)  # MAD to std

            # Wiener filter
            # Using scipy's built-in wiener filter
            try:
                filtered = scipy_signal.wiener(ts.values, mysize=window_size)
            except Exception:
                # Fallback to simple smoothing
                filtered = uniform_filter1d(ts.values, window_size, mode="nearest")

        elif method == "savgol":
            # Savitzky-Golay filter (polynomial smoothing)
            # Window must be odd
            win = window_size if window_size % 2 == 1 else window_size + 1
            if win >= len(ts.values):
                win = len(ts.values) - 1 if len(ts.values) % 2 == 0 else len(ts.values) - 2
            if win < 3:
                filtered = ts.values.copy()
            else:
                filtered = scipy_signal.savgol_filter(ts.values, win, polyorder=2)

        elif method == "kalman":
            # Simple exponential smoothing (Kalman-like)
            alpha = 2.0 / (window_size + 1)
            filtered = np.zeros_like(ts.values)
            filtered[0] = ts.values[0]
            for i in range(1, len(ts.values)):
                filtered[i] = alpha * ts.values[i] + (1 - alpha) * filtered[i - 1]

        else:
            # Default: uniform filter
            filtered = uniform_filter1d(ts.values, window_size, mode="nearest")

        # Calculate quality metrics
        noise_reduction = 1 - (np.std(filtered) / np.std(ts.values))
        correlation = float(np.corrcoef(ts.values, filtered)[0, 1])
        mse = float(np.mean((ts.values - filtered) ** 2))

        return {
            "filtered_values": filtered.tolist(),
            "original_values": ts.values.tolist(),
            "method": method,
            "window_size": window_size,
            "quality_metrics": {
                "noise_reduction": float(noise_reduction),
                "correlation_with_original": correlation,
                "mean_squared_error": mse,
                "estimated_noise_std": float(noise_estimate) if noise_estimate else 0,
            },
        }

    # =========================================================================
    # Harmonic Analysis
    # =========================================================================

    def harmonic_analysis(
        self,
        ts: WorkloadTimeSeries,
        n_harmonics: int = 10,
        fundamental_period: float | None = None,
    ) -> dict:
        """
        Perform harmonic analysis to identify resonances.

        Detects harmonically related frequencies that might indicate:
        - Reinforcing patterns (constructive interference)
        - Conflicting schedules (destructive interference)
        - Natural rhythms in the scheduling system

        Args:
            ts: Workload time series
            n_harmonics: Number of harmonics to analyze
            fundamental_period: Expected fundamental period (None = auto-detect)

        Returns:
            Dict with harmonic structure and resonance information
        """
        # Get FFT results
        fft_result = self.fft_analysis(ts, n_dominant=20)

        if not fft_result["dominant_frequencies"]:
            return {
                "fundamental_frequency": None,
                "fundamental_period": None,
                "harmonics": [],
                "resonances": [],
                "total_harmonic_distortion": 0.0,
            }

        # Identify fundamental frequency
        if fundamental_period is not None:
            fundamental = 1.0 / fundamental_period
        else:
            # Use the strongest low-frequency component
            low_freq_peaks = [
                d for d in fft_result["dominant_frequencies"] if d["period_days"] >= 5
            ]
            if low_freq_peaks:
                fundamental = low_freq_peaks[0]["frequency"]
            else:
                fundamental = fft_result["dominant_frequencies"][0]["frequency"]

        fundamental_period_detected = 1.0 / fundamental if fundamental > 0 else float("inf")

        # Find harmonics
        harmonics: list[HarmonicPeak] = []
        tolerance = fundamental * 0.1  # 10% tolerance for harmonic detection

        for n in range(1, n_harmonics + 1):
            expected_freq = fundamental * n

            # Find closest peak
            for dom in fft_result["dominant_frequencies"]:
                if abs(dom["frequency"] - expected_freq) < tolerance:
                    harmonics.append(
                        {
                            "frequency": dom["frequency"],
                            "period_days": dom["period_days"],
                            "magnitude": dom["magnitude"],
                            "phase": dom["phase"],
                            "significance": dom["normalized_magnitude"],
                        }
                    )
                    break

        # Detect resonances (harmonics with unusual phase relationships)
        resonances = []
        if len(harmonics) >= 2:
            for i, h1 in enumerate(harmonics[:-1]):
                for h2 in harmonics[i + 1 :]:
                    phase_diff = abs(h1["phase"] - h2["phase"])

                    # In-phase resonance (constructive)
                    if phase_diff < 0.3 or abs(phase_diff - 2 * math.pi) < 0.3:
                        resonances.append(
                            {
                                "type": "constructive",
                                "frequencies": [h1["frequency"], h2["frequency"]],
                                "periods": [h1["period_days"], h2["period_days"]],
                                "phase_difference": float(phase_diff),
                                "description": (
                                    f"Constructive resonance between "
                                    f"{h1['period_days']:.1f}-day and "
                                    f"{h2['period_days']:.1f}-day patterns"
                                ),
                            }
                        )

                    # Anti-phase resonance (destructive)
                    elif abs(phase_diff - math.pi) < 0.3:
                        resonances.append(
                            {
                                "type": "destructive",
                                "frequencies": [h1["frequency"], h2["frequency"]],
                                "periods": [h1["period_days"], h2["period_days"]],
                                "phase_difference": float(phase_diff),
                                "description": (
                                    f"Destructive resonance between "
                                    f"{h1['period_days']:.1f}-day and "
                                    f"{h2['period_days']:.1f}-day patterns"
                                ),
                            }
                        )

        # Calculate total harmonic distortion (THD)
        if harmonics and harmonics[0]["magnitude"] > 0:
            fundamental_power = harmonics[0]["magnitude"] ** 2
            harmonic_power = sum(h["magnitude"] ** 2 for h in harmonics[1:])
            thd = math.sqrt(harmonic_power / fundamental_power) if fundamental_power > 0 else 0
        else:
            thd = 0.0

        return {
            "fundamental_frequency": float(fundamental),
            "fundamental_period": float(fundamental_period_detected),
            "harmonics": harmonics,
            "resonances": resonances,
            "total_harmonic_distortion": float(thd),
        }

    # =========================================================================
    # Change Point Detection
    # =========================================================================

    def detect_change_points_cusum(
        self,
        series: NDArray[np.float64],
        threshold: float = 5.0,
        drift: float = 0.0,
    ) -> list[ChangePoint]:
        """
        Detect change points using CUSUM (Cumulative Sum) algorithm.

        CUSUM detects mean shifts by accumulating deviations from the target
        mean. It's sensitive to persistent changes but robust to transient
        spikes.

        Algorithm:
            S_high[t] = max(0, S_high[t-1] + (x[t] - mean - drift))
            S_low[t] = min(0, S_low[t-1] + (x[t] - mean + drift))
            Trigger when |S| > threshold

        Args:
            series: Input time series (workload values)
            threshold: Alarm threshold (typically 4-5 for 3-sigma shifts)
            drift: Allowable drift parameter (typically half the shift to detect)

        Returns:
            List of detected change points with metadata
        """
        n = len(series)
        if n < 4:
            logger.warning("Series too short for CUSUM analysis")
            return []

        # Compute mean and std for reference
        mean = np.mean(series)
        std = np.std(series)

        # Standardize series
        standardized = (series - mean) / (std + 1e-10)

        # CUSUM statistics
        s_high = np.zeros(n)
        s_low = np.zeros(n)

        change_points: list[ChangePoint] = []

        for t in range(1, n):
            # Upper CUSUM (detect upward shifts)
            s_high[t] = max(0, s_high[t - 1] + standardized[t] - drift)

            # Lower CUSUM (detect downward shifts)
            s_low[t] = min(0, s_low[t - 1] + standardized[t] + drift)

            # Check for alarm
            if s_high[t] > threshold:
                # Upward shift detected
                # Estimate change magnitude
                segment_start = max(0, t - 20)
                pre_mean = np.mean(series[segment_start:t])
                post_mean = np.mean(series[t : min(t + 10, n)])
                magnitude = float(post_mean - pre_mean)

                # Confidence based on CUSUM statistic
                confidence = min(1.0, s_high[t] / (threshold * 2))

                change_points.append(
                    {
                        "index": int(t),
                        "timestamp": "",  # Will be filled by caller
                        "change_type": "mean_shift_upward",
                        "magnitude": magnitude,
                        "confidence": confidence,
                        "description": (
                            f"Upward mean shift detected: "
                            f"{pre_mean:.1f} → {post_mean:.1f} "
                            f"(CUSUM={s_high[t]:.2f})"
                        ),
                    }
                )

                # Reset CUSUM after detection
                s_high[t] = 0

            if s_low[t] < -threshold:
                # Downward shift detected
                segment_start = max(0, t - 20)
                pre_mean = np.mean(series[segment_start:t])
                post_mean = np.mean(series[t : min(t + 10, n)])
                magnitude = float(post_mean - pre_mean)

                confidence = min(1.0, abs(s_low[t]) / (threshold * 2))

                change_points.append(
                    {
                        "index": int(t),
                        "timestamp": "",
                        "change_type": "mean_shift_downward",
                        "magnitude": magnitude,
                        "confidence": confidence,
                        "description": (
                            f"Downward mean shift detected: "
                            f"{pre_mean:.1f} → {post_mean:.1f} "
                            f"(CUSUM={abs(s_low[t]):.2f})"
                        ),
                    }
                )

                # Reset CUSUM
                s_low[t] = 0

        logger.debug(f"CUSUM detected {len(change_points)} change points")
        return change_points

    def detect_change_points_pelt(
        self,
        series: NDArray[np.float64],
        penalty: float = 1.0,
        min_segment_length: int = 5,
    ) -> list[ChangePoint]:
        """
        Detect change points using PELT (Pruned Exact Linear Time) algorithm.

        PELT finds optimal segmentation by minimizing:
            sum(segment_costs) + penalty * num_changepoints

        It can detect multiple change points simultaneously and is optimal
        for detecting structural breaks.

        Args:
            series: Input time series
            penalty: Penalty for adding new segments (higher = fewer changepoints)
            min_segment_length: Minimum samples between change points

        Returns:
            List of detected change points with metadata
        """
        n = len(series)
        if n < 2 * min_segment_length:
            logger.warning("Series too short for PELT analysis")
            return []

        # Try using ruptures library if available
        try:
            import ruptures as rpt

            # Use PELT with RBF (Radial Basis Function) cost
            # RBF is good for detecting both mean and variance changes
            algo = rpt.Pelt(model="rbf", min_size=min_segment_length, jump=1)
            algo.fit(series.reshape(-1, 1))

            # Get change points
            breakpoints = algo.predict(pen=penalty)

            # Remove last point (always end of series)
            if breakpoints and breakpoints[-1] == n:
                breakpoints = breakpoints[:-1]

            change_points: list[ChangePoint] = []

            for cp_idx in breakpoints:
                # Analyze segment before and after change point
                segment_start = max(0, cp_idx - min_segment_length)
                segment_end = min(n, cp_idx + min_segment_length)

                pre_segment = series[segment_start:cp_idx]
                post_segment = series[cp_idx:segment_end]

                if len(pre_segment) > 0 and len(post_segment) > 0:
                    # Compute statistics
                    pre_mean = np.mean(pre_segment)
                    post_mean = np.mean(post_segment)
                    pre_std = np.std(pre_segment)
                    post_std = np.std(post_segment)

                    mean_change = abs(post_mean - pre_mean)
                    var_change = abs(post_std - pre_std)

                    # Classify change type
                    if mean_change > 2 * var_change:
                        change_type = "mean_shift"
                        magnitude = float(post_mean - pre_mean)
                        desc = f"Mean shift: {pre_mean:.1f} → {post_mean:.1f}"
                    elif var_change > 2 * mean_change:
                        change_type = "variance_change"
                        magnitude = float(post_std - pre_std)
                        desc = f"Variance change: {pre_std:.1f} → {post_std:.1f}"
                    else:
                        change_type = "trend_change"
                        magnitude = float(mean_change + var_change)
                        desc = (
                            f"Trend change: mean {pre_mean:.1f}→{post_mean:.1f}, "
                            f"std {pre_std:.1f}→{post_std:.1f}"
                        )

                    # Estimate confidence based on effect size
                    effect_size = mean_change / (
                        (pre_std + post_std) / 2 + 1e-10
                    )
                    confidence = min(1.0, effect_size / 3.0)

                    change_points.append(
                        {
                            "index": int(cp_idx),
                            "timestamp": "",
                            "change_type": change_type,
                            "magnitude": magnitude,
                            "confidence": confidence,
                            "description": desc,
                        }
                    )

            logger.debug(
                f"PELT detected {len(change_points)} change points "
                f"(penalty={penalty})"
            )
            return change_points

        except ImportError:
            logger.warning(
                "ruptures library not available, using simplified PELT implementation"
            )
            # Fallback to simplified implementation
            return self._pelt_simplified(series, penalty, min_segment_length)

    def _pelt_simplified(
        self,
        series: NDArray[np.float64],
        penalty: float = 1.0,
        min_segment_length: int = 5,
    ) -> list[ChangePoint]:
        """
        Simplified PELT implementation without ruptures library.

        Uses variance-based cost function and greedy search.
        """
        n = len(series)

        # Compute variance cost for each potential segment
        def segment_cost(start: int, end: int) -> float:
            """Variance of segment as cost."""
            if end - start < 2:
                return 0.0
            segment = series[start:end]
            return float(np.var(segment) * (end - start))

        # Greedy search for change points
        change_points_idx: list[int] = []
        current_pos = 0

        while current_pos < n - min_segment_length:
            # Try different segment lengths
            best_cost = float("inf")
            best_split = current_pos + min_segment_length

            for split in range(
                current_pos + min_segment_length, n - min_segment_length
            ):
                # Cost of two segments vs. one segment
                cost_one = segment_cost(current_pos, n)
                cost_two = (
                    segment_cost(current_pos, split)
                    + segment_cost(split, n)
                    + penalty
                )

                if cost_two < cost_one and cost_two < best_cost:
                    best_cost = cost_two
                    best_split = split

            if best_cost < segment_cost(current_pos, n):
                change_points_idx.append(best_split)
                current_pos = best_split
            else:
                break

        # Convert to ChangePoint format
        change_points: list[ChangePoint] = []
        for cp_idx in change_points_idx:
            segment_start = max(0, cp_idx - min_segment_length)
            segment_end = min(n, cp_idx + min_segment_length)

            pre_mean = np.mean(series[segment_start:cp_idx])
            post_mean = np.mean(series[cp_idx:segment_end])

            change_points.append(
                {
                    "index": int(cp_idx),
                    "timestamp": "",
                    "change_type": "variance_change",
                    "magnitude": float(abs(post_mean - pre_mean)),
                    "confidence": 0.7,  # Fixed confidence for simplified version
                    "description": f"Segment boundary at index {cp_idx}",
                }
            )

        logger.debug(
            f"Simplified PELT detected {len(change_points)} change points"
        )
        return change_points

    def analyze_schedule_changepoints(
        self,
        ts: WorkloadTimeSeries,
        methods: list[str] | None = None,
    ) -> dict[str, ChangePointAnalysisResult]:
        """
        Comprehensive change point analysis using multiple methods.

        Detects regime shifts, policy changes, and structural breaks in
        schedule patterns.

        Args:
            ts: Workload time series
            methods: List of methods to use (default: ["cusum", "pelt"])
                - "cusum": CUSUM algorithm for mean shifts
                - "pelt": PELT algorithm for optimal segmentation
                - "both": Run both and compare

        Returns:
            Dictionary with results from each method
        """
        if methods is None:
            methods = ["cusum", "pelt"]

        results: dict[str, ChangePointAnalysisResult] = {}

        # CUSUM analysis
        if "cusum" in methods or "both" in methods:
            cusum_cps = self.detect_change_points_cusum(
                ts.values, threshold=5.0, drift=0.0
            )

            # Fill in timestamps
            for cp in cusum_cps:
                if cp["index"] < len(ts.dates):
                    cp["timestamp"] = ts.dates[cp["index"]].isoformat()

            # Compute segmentation quality (variance reduction)
            quality = self._compute_segmentation_quality(ts.values, cusum_cps)

            results["cusum"] = {
                "method": "cusum",
                "change_points": cusum_cps,
                "num_changepoints": len(cusum_cps),
                "segmentation_quality": quality,
                "algorithm_parameters": {"threshold": 5.0, "drift": 0.0},
            }

        # PELT analysis
        if "pelt" in methods or "both" in methods:
            pelt_cps = self.detect_change_points_pelt(
                ts.values, penalty=1.0, min_segment_length=5
            )

            # Fill in timestamps
            for cp in pelt_cps:
                if cp["index"] < len(ts.dates):
                    cp["timestamp"] = ts.dates[cp["index"]].isoformat()

            quality = self._compute_segmentation_quality(ts.values, pelt_cps)

            results["pelt"] = {
                "method": "pelt",
                "change_points": pelt_cps,
                "num_changepoints": len(pelt_cps),
                "segmentation_quality": quality,
                "algorithm_parameters": {"penalty": 1.0, "min_segment_length": 5},
            }

        logger.info(
            f"Change point analysis completed: "
            f"CUSUM={len(results.get('cusum', {}).get('change_points', []))}, "
            f"PELT={len(results.get('pelt', {}).get('change_points', []))}"
        )

        return results

    def _compute_segmentation_quality(
        self,
        series: NDArray[np.float64],
        change_points: list[ChangePoint],
    ) -> float:
        """
        Compute segmentation quality as variance reduction.

        Returns:
            Quality score 0-1, where 1 = perfect segmentation
        """
        if not change_points:
            return 0.0

        # Variance of original series
        total_var = np.var(series)
        if total_var < 1e-10:
            return 0.0

        # Variance within segments
        breakpoints = [0] + [cp["index"] for cp in change_points] + [len(series)]
        breakpoints = sorted(set(breakpoints))

        segment_var = 0.0
        for i in range(len(breakpoints) - 1):
            segment = series[breakpoints[i] : breakpoints[i + 1]]
            if len(segment) > 1:
                segment_var += np.var(segment) * len(segment)

        segment_var /= len(series)

        # Variance reduction
        quality = 1.0 - (segment_var / total_var)
        return float(max(0.0, min(1.0, quality)))

    # =========================================================================
    # Main Analysis Pipeline
    # =========================================================================

    def analyze_workload_patterns(
        self,
        ts: WorkloadTimeSeries,
        analysis_types: list[str] | None = None,
    ) -> SignalAnalysisResult:
        """
        Perform comprehensive workload pattern analysis.

        This is the main entry point that runs selected analysis types
        and combines results into a unified report.

        Args:
            ts: Workload time series
            analysis_types: List of analyses to run. Options:
                - "wavelet": Discrete wavelet transform
                - "cwt": Continuous wavelet transform
                - "fft": Fast Fourier transform
                - "sta_lta": STA/LTA anomaly detection
                - "spectral": Spectral decomposition (trend/seasonal/residual)
                - "constraints": Frequency constraint validation
                - "harmonic": Harmonic analysis
                - "filter": Adaptive filtering
                - "changepoint": Change point detection (CUSUM, PELT)
                - "all": Run all analyses (default)

        Returns:
            SignalAnalysisResult with comprehensive analysis
        """
        if analysis_types is None or "all" in analysis_types:
            analysis_types = [
                "wavelet",
                "cwt",
                "fft",
                "sta_lta",
                "spectral",
                "constraints",
                "harmonic",
                "filter",
                "changepoint",
            ]

        analysis_id = datetime.utcnow().strftime("%Y%m%d%H%M%S")

        result: SignalAnalysisResult = {
            "analysis_id": analysis_id,
            "generated_at": datetime.utcnow().isoformat(),
            "input_summary": {
                "length": len(ts.values),
                "duration_days": ts.duration_days,
                "sample_rate": ts.sample_rate_per_day,
                "mean": float(np.mean(ts.values)),
                "std": float(np.std(ts.values)),
                "min": float(np.min(ts.values)),
                "max": float(np.max(ts.values)),
                "person_id": str(ts.person_id) if ts.person_id else None,
            },
            "recommendations": [],
            "constraint_violations": [],
        }

        # Run selected analyses
        if "wavelet" in analysis_types:
            result["wavelet_analysis"] = self.discrete_wavelet_transform(ts)

        if "cwt" in analysis_types:
            result["cwt_analysis"] = self.continuous_wavelet_transform(ts)

        if "fft" in analysis_types:
            result["fft_analysis"] = self.fft_analysis(ts)

        if "sta_lta" in analysis_types:
            result["sta_lta_analysis"] = self.sta_lta_detector(ts)

        if "spectral" in analysis_types:
            result["spectral_decomposition"] = self.spectral_decomposition(ts)

        if "constraints" in analysis_types:
            result["constraint_violations"] = self.validate_frequency_constraints(ts)

        if "harmonic" in analysis_types:
            result["harmonic_analysis"] = self.harmonic_analysis(ts)

        if "filter" in analysis_types:
            result["adaptive_filtered"] = self.adaptive_filter(ts)

        if "changepoint" in analysis_types:
            result["changepoint_analysis"] = self.analyze_schedule_changepoints(ts)

        # Generate recommendations based on analysis
        result["recommendations"] = self._generate_recommendations(result)

        logger.info(
            f"Workload pattern analysis completed: "
            f"id={analysis_id}, "
            f"analyses={len(analysis_types)}, "
            f"violations={len(result.get('constraint_violations', []))}"
        )

        return result

    def _generate_recommendations(
        self,
        result: SignalAnalysisResult,
    ) -> list[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []

        # Check for violations
        violations = result.get("constraint_violations", [])
        if violations:
            for v in violations:
                if v["severity"] == "error":
                    recommendations.append(f"CRITICAL: {v['description']}")
                elif v["severity"] == "warning":
                    recommendations.append(f"Warning: {v['description']}")

        # Check STA/LTA anomalies
        sta_lta = result.get("sta_lta_analysis")
        if sta_lta:
            anomalies = sta_lta.get("anomalies", [])
            high_severity = [a for a in anomalies if a["severity"] > 0.7]
            if high_severity:
                recommendations.append(
                    f"Detected {len(high_severity)} high-severity workload anomalies. "
                    f"Review dates: {', '.join(a['date'] for a in high_severity[:3])}"
                )

        # Check spectral decomposition
        spectral = result.get("spectral_decomposition")
        if spectral:
            stats = spectral.get("statistics", {})
            if stats.get("seasonal_strength", 0) < 0.3:
                recommendations.append(
                    "Low seasonal pattern strength detected. "
                    "Consider establishing more regular weekly/monthly schedules."
                )
            if stats.get("trend_strength", 0) > 0.7:
                recommendations.append(
                    "Strong trend detected in workload. "
                    "Check if workload is consistently increasing or decreasing."
                )

        # Check harmonic analysis
        harmonic = result.get("harmonic_analysis")
        if harmonic:
            resonances = harmonic.get("resonances", [])
            destructive = [r for r in resonances if r["type"] == "destructive"]
            if destructive:
                recommendations.append(
                    f"Detected {len(destructive)} destructive resonances between "
                    f"schedule patterns. These may cause irregular workload fluctuations."
                )

        # Check change point analysis
        changepoint = result.get("changepoint_analysis")
        if changepoint:
            # Combine change points from all methods
            all_cps = []
            for method_name, method_result in changepoint.items():
                all_cps.extend(method_result.get("change_points", []))

            # High-confidence change points
            high_conf_cps = [cp for cp in all_cps if cp.get("confidence", 0) > 0.7]
            if high_conf_cps:
                recommendations.append(
                    f"Detected {len(high_conf_cps)} high-confidence regime shifts. "
                    f"Review schedule structure changes at: "
                    f"{', '.join(cp.get('timestamp', 'unknown')[:10] for cp in high_conf_cps[:3])}"
                )

            # Mean shift warnings
            mean_shifts = [
                cp
                for cp in all_cps
                if "mean_shift" in cp.get("change_type", "")
                and abs(cp.get("magnitude", 0)) > 5.0
            ]
            if mean_shifts:
                recommendations.append(
                    f"Detected {len(mean_shifts)} significant workload level changes. "
                    "May indicate staffing changes or policy updates."
                )

        if not recommendations:
            recommendations.append(
                "No significant issues detected. "
                "Schedule patterns appear regular and within constraints."
            )

        return recommendations

    # =========================================================================
    # Export Methods
    # =========================================================================

    def export_to_holographic_format(
        self,
        result: SignalAnalysisResult,
        ts: WorkloadTimeSeries,
    ) -> HolographicExport:
        """
        Export analysis results for holographic visualization.

        Creates a structured JSON format suitable for 3D/holographic
        visualization systems with time, frequency, and wavelet domains.

        Args:
            result: Analysis result from analyze_workload_patterns
            ts: Original time series

        Returns:
            HolographicExport ready for JSON serialization
        """
        # Time domain data
        time_domain = {
            "dates": [d.isoformat() for d in ts.dates],
            "values": ts.values.tolist(),
            "units": ts.units,
        }

        # Add filtered version if available
        if result.get("adaptive_filtered"):
            time_domain["filtered"] = result["adaptive_filtered"]["filtered_values"]

        # Frequency domain data
        frequency_domain = {}
        if result.get("fft_analysis"):
            fft = result["fft_analysis"]
            frequency_domain = {
                "frequencies": fft["frequencies"],
                "magnitudes": fft["magnitudes"],
                "phases": fft["phases"],
                "dominant_peaks": fft["dominant_frequencies"],
            }

        # Wavelet domain data
        wavelet_domain = {}
        if result.get("cwt_analysis"):
            cwt = result["cwt_analysis"]
            wavelet_domain["cwt"] = {
                "coefficients": cwt["coefficients"],
                "scales": cwt["scales"],
                "frequencies": cwt["frequencies"],
                "power": cwt["power"],
            }
        if result.get("wavelet_analysis"):
            dwt = result["wavelet_analysis"]
            wavelet_domain["dwt"] = {
                "approximation": dwt["approximation"],
                "details": dwt["details"],
                "frequency_bands": dwt["frequency_bands"],
            }

        # Anomalies
        anomalies = []
        if result.get("sta_lta_analysis"):
            for a in result["sta_lta_analysis"].get("anomalies", []):
                anomalies.append(
                    {
                        "type": a["type"],
                        "date": a["date"],
                        "index": a["index"],
                        "severity": a["severity"],
                        "description": a["description"],
                    }
                )

        # Add constraint violations
        for v in result.get("constraint_violations", []):
            anomalies.append(
                {
                    "type": v["violation_type"],
                    "date": ts.dates[v["location_indices"][0]].isoformat()
                    if v["location_indices"]
                    else None,
                    "indices": v["location_indices"],
                    "severity": 1.0 if v["severity"] == "error" else 0.5,
                    "description": v["description"],
                }
            )

        # Add change points
        if result.get("changepoint_analysis"):
            for method_name, method_result in result["changepoint_analysis"].items():
                for cp in method_result.get("change_points", []):
                    anomalies.append(
                        {
                            "type": f"changepoint_{cp['change_type']}",
                            "date": cp["timestamp"],
                            "index": cp["index"],
                            "severity": cp["confidence"],
                            "description": f"[{method_name.upper()}] {cp['description']}",
                            "magnitude": cp["magnitude"],
                        }
                    )

        # Metadata
        metadata = {
            "analysis_id": result["analysis_id"],
            "generated_at": result["generated_at"],
            "input_summary": result["input_summary"],
            "recommendations": result.get("recommendations", []),
        }

        # Add spectral decomposition if available
        if result.get("spectral_decomposition"):
            spectral = result["spectral_decomposition"]
            time_domain["trend"] = spectral["trend"]
            time_domain["seasonal"] = spectral["seasonal"]
            time_domain["residual"] = spectral["residual"]
            metadata["spectral_statistics"] = spectral["statistics"]

        # Add harmonic analysis if available
        if result.get("harmonic_analysis"):
            harmonic = result["harmonic_analysis"]
            frequency_domain["harmonics"] = harmonic.get("harmonics", [])
            frequency_domain["resonances"] = harmonic.get("resonances", [])
            metadata["harmonic_distortion"] = harmonic.get("total_harmonic_distortion", 0)

        return {
            "version": "1.0",
            "export_type": "holographic_signal_analysis",
            "generated_at": datetime.utcnow().isoformat(),
            "time_domain": time_domain,
            "frequency_domain": frequency_domain,
            "wavelet_domain": wavelet_domain,
            "anomalies": anomalies,
            "metadata": metadata,
        }


# =============================================================================
# Convenience Functions
# =============================================================================


def analyze_resident_workload(
    daily_hours: Sequence[float],
    dates: Sequence[date],
    person_id: UUID | None = None,
) -> SignalAnalysisResult:
    """
    Convenience function for analyzing a resident's workload pattern.

    Args:
        daily_hours: Daily hours worked
        dates: Corresponding dates
        person_id: Optional resident ID

    Returns:
        Complete signal analysis result
    """
    ts = WorkloadTimeSeries(
        values=np.array(daily_hours, dtype=np.float64),
        dates=list(dates),
        person_id=person_id,
    )

    processor = WorkloadSignalProcessor()
    return processor.analyze_workload_patterns(ts)


def detect_schedule_anomalies(
    daily_hours: Sequence[float],
    dates: Sequence[date],
    threshold: float = 3.0,
) -> list[dict]:
    """
    Quick anomaly detection for a schedule.

    Args:
        daily_hours: Daily hours worked
        dates: Corresponding dates
        threshold: STA/LTA threshold for detection

    Returns:
        List of detected anomalies
    """
    ts = WorkloadTimeSeries(
        values=np.array(daily_hours, dtype=np.float64),
        dates=list(dates),
    )

    processor = WorkloadSignalProcessor(sta_lta_threshold=threshold)
    sta_lta_result = processor.sta_lta_detector(ts)

    return sta_lta_result.get("anomalies", [])


def detect_schedule_changepoints(
    daily_hours: Sequence[float],
    dates: Sequence[date],
    methods: list[str] | None = None,
) -> dict[str, ChangePointAnalysisResult]:
    """
    Quick change point detection for schedule regime shifts.

    Detects structural breaks, policy changes, and workload pattern shifts
    in schedule time series.

    Args:
        daily_hours: Daily hours worked
        dates: Corresponding dates
        methods: Detection methods to use (default: ["cusum", "pelt"])

    Returns:
        Dictionary with change point results from each method

    Example:
        >>> results = detect_schedule_changepoints(
        ...     daily_hours=[8, 8, 10, 10, 12, 12, 12],
        ...     dates=[date(2025, 1, i) for i in range(1, 8)],
        ...     methods=["cusum", "pelt"]
        ... )
        >>> for method, result in results.items():
        ...     print(f"{method}: {result['num_changepoints']} change points")
    """
    ts = WorkloadTimeSeries(
        values=np.array(daily_hours, dtype=np.float64),
        dates=list(dates),
    )

    processor = WorkloadSignalProcessor()
    return processor.analyze_schedule_changepoints(ts, methods=methods)


def export_for_visualization(
    analysis_result: SignalAnalysisResult,
    daily_hours: Sequence[float],
    dates: Sequence[date],
) -> str:
    """
    Export analysis to JSON for visualization.

    Args:
        analysis_result: Result from analyze_workload_patterns
        daily_hours: Original daily hours
        dates: Corresponding dates

    Returns:
        JSON string for visualization systems
    """
    import json

    ts = WorkloadTimeSeries(
        values=np.array(daily_hours, dtype=np.float64),
        dates=list(dates),
    )

    processor = WorkloadSignalProcessor()
    export_data = processor.export_to_holographic_format(analysis_result, ts)

    return json.dumps(export_data, indent=2, default=str)
