"""
Fourier/FFT Analysis Tools for Schedule Periodicity Detection.

Provides spectral analysis capabilities to detect natural cycles in scheduling
patterns (workload, swaps, absences) using Fast Fourier Transform (FFT).
Complements time crystal periodicity detection with frequency domain analysis.

Key Capabilities:
- FFT-based periodicity detection
- Dominant frequency identification
- Harmonic resonance with ACGME windows (7d, 28d)
- Spectral entropy calculation
- Power spectrum analysis

Scientific Background:
- Uses numpy.fft for efficient FFT computation
- Maps frequencies to interpretable periods (days)
- Detects alignment with regulatory cycles
- Measures signal complexity via spectral entropy

References:
    - TIME_CRYSTAL_ANTI_CHURN.md - Time crystal scheduling concepts
    - cross-disciplinary-resilience.md - Subharmonic detection patterns
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any

import numpy as np
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


# =============================================================================
# Response Models
# =============================================================================


class DominantPeriod(BaseModel):
    """A detected dominant period in the schedule."""

    period_days: float = Field(
        ...,
        gt=0.0,
        description="Period length in days",
    )
    frequency_hz: float = Field(
        ...,
        description="Frequency in cycles per day (1/period_days)",
    )
    power: float = Field(
        ...,
        ge=0.0,
        description="Power/magnitude at this frequency",
    )
    relative_power: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Power normalized to strongest peak (0.0-1.0)",
    )
    interpretation: str = Field(
        ...,
        description="Human-readable interpretation of this period",
    )


class ScheduleCyclesResponse(BaseModel):
    """Response from FFT-based schedule cycle detection."""

    dominant_period_days: float | None = Field(
        None,
        description="Strongest detected period in days (None if no clear period)",
    )
    all_periods: list[DominantPeriod] = Field(
        default_factory=list,
        description="All detected periods sorted by power (strongest first)",
    )
    signal_length_days: int = Field(
        ...,
        ge=0,
        description="Length of analyzed signal in days",
    )
    mean_value: float = Field(
        ...,
        description="Mean value of the signal (DC component)",
    )
    signal_std: float = Field(
        ...,
        ge=0.0,
        description="Standard deviation of the signal",
    )
    periodicity_detected: bool = Field(
        ...,
        description="True if clear periodic patterns were detected",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Actionable recommendations based on detected cycles",
    )


class HarmonicResonanceResponse(BaseModel):
    """Response from harmonic resonance analysis with ACGME windows."""

    acgme_7d_alignment: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Alignment strength with 7-day weekly cycle (0.0-1.0)",
    )
    acgme_14d_alignment: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Alignment strength with 14-day biweekly cycle (0.0-1.0)",
    )
    acgme_28d_alignment: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Alignment strength with 28-day ACGME window (0.0-1.0)",
    )
    resonant_harmonics: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Detected harmonics that align with ACGME windows",
    )
    dissonant_frequencies: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Strong frequencies that conflict with ACGME cycles",
    )
    overall_resonance: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall alignment with ACGME regulatory cycles (0.0-1.0)",
    )
    health_status: str = Field(
        ...,
        description="Health status: healthy, degraded, critical",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommendations for improving ACGME alignment",
    )


class SpectralEntropyResponse(BaseModel):
    """Response from spectral entropy calculation."""

    spectral_entropy: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Shannon entropy of power spectrum (0.0-1.0, normalized)",
    )
    entropy_interpretation: str = Field(
        ...,
        description="Interpretation of entropy value",
    )
    signal_complexity: str = Field(
        ...,
        description="Complexity level: simple, moderate, complex, chaotic",
    )
    dominant_frequencies_count: int = Field(
        ...,
        ge=0,
        description="Number of significant frequency components",
    )
    frequency_concentration: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How concentrated the spectrum is (1.0 = single frequency)",
    )
    predictability: str = Field(
        ...,
        description="Predictability level: high, moderate, low",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommendations based on spectral characteristics",
    )


# =============================================================================
# Helper Functions
# =============================================================================


def _validate_signal(signal: list[float], min_length: int = 7) -> tuple[bool, str | None]:
    """
    Validate signal for FFT analysis.

    Args:
        signal: Time series data
        min_length: Minimum required length

    Returns:
        (is_valid, error_message) tuple
    """
    if len(signal) < min_length:
        return False, f"Signal too short: {len(signal)} samples (minimum {min_length})"

    if all(x == 0 for x in signal):
        return False, "Signal is all zeros"

    if any(not np.isfinite(x) for x in signal):
        return False, "Signal contains NaN or infinite values"

    return True, None


def _interpret_period(period_days: float) -> str:
    """
    Generate human-readable interpretation of a period.

    Args:
        period_days: Period length in days

    Returns:
        Interpretation string
    """
    if abs(period_days - 7.0) < 0.5:
        return "Weekly cycle (7-day ACGME 1-in-7 rule)"
    elif abs(period_days - 14.0) < 1.0:
        return "Biweekly cycle (alternating weekends pattern)"
    elif abs(period_days - 28.0) < 2.0:
        return "ACGME 4-week rolling average window"
    elif abs(period_days - 3.5) < 0.5:
        return "Half-week cycle (possible mid-week pattern)"
    elif abs(period_days - 21.0) < 1.5:
        return "Three-week rotation cycle"
    elif period_days < 3.0:
        return "Short-term variation (daily/sub-weekly)"
    elif period_days > 60.0:
        return "Long-term seasonal pattern"
    else:
        return f"{period_days:.1f}-day cycle"


def _calculate_alignment_score(
    detected_period: float, target_period: float, tolerance: float = 0.15
) -> float:
    """
    Calculate alignment score between detected and target period.

    Args:
        detected_period: Detected period in days
        target_period: Target period (e.g., 7.0 for weekly)
        tolerance: Fractional tolerance (0.15 = ±15%)

    Returns:
        Alignment score 0.0-1.0
    """
    if target_period == 0:
        return 0.0

    # Calculate fractional deviation
    deviation = abs(detected_period - target_period) / target_period

    if deviation <= tolerance:
        # Linear decay within tolerance
        return 1.0 - (deviation / tolerance)
    else:
        return 0.0


# =============================================================================
# Tool Implementation Functions
# =============================================================================


async def detect_schedule_cycles(
    signal: list[float],
    sampling_period_days: float = 1.0,
    num_peaks: int = 5,
) -> ScheduleCyclesResponse:
    """
    Detect dominant cycles in schedule metrics using FFT.

    Performs Fast Fourier Transform on time series data (workload, swaps,
    absences) to identify periodic patterns. Returns dominant frequencies
    mapped to interpretable periods in days.

    Args:
        signal: Time series data (e.g., daily workload hours, swap counts)
        sampling_period_days: Sampling period in days (default 1.0 for daily data)
        num_peaks: Number of strongest peaks to return

    Returns:
        ScheduleCyclesResponse with detected periods and recommendations

    Example:
        # Analyze daily workload hours
        workload = [40, 45, 50, 48, 40, 0, 0, 42, 46, ...]  # Daily hours
        result = await detect_schedule_cycles(workload)

        if result.dominant_period_days:
            print(f"Strongest cycle: {result.dominant_period_days} days")
    """
    # Validate signal
    is_valid, error_msg = _validate_signal(signal, min_length=7)
    if not is_valid:
        logger.warning(f"Invalid signal for FFT: {error_msg}")
        return ScheduleCyclesResponse(
            dominant_period_days=None,
            all_periods=[],
            signal_length_days=len(signal),
            mean_value=0.0,
            signal_std=0.0,
            periodicity_detected=False,
            recommendations=[f"Cannot analyze: {error_msg}"],
        )

    try:
        # Convert to numpy array and remove DC component (mean)
        signal_array = np.array(signal, dtype=float)
        mean_value = float(np.mean(signal_array))
        signal_std = float(np.std(signal_array))
        signal_detrended = signal_array - mean_value

        # Compute FFT
        fft_result = np.fft.rfft(signal_detrended)
        power_spectrum = np.abs(fft_result) ** 2
        freqs = np.fft.rfftfreq(len(signal), d=sampling_period_days)

        # Skip DC component (index 0) and find peaks
        if len(power_spectrum) < 2:
            return ScheduleCyclesResponse(
                dominant_period_days=None,
                all_periods=[],
                signal_length_days=len(signal),
                mean_value=mean_value,
                signal_std=signal_std,
                periodicity_detected=False,
                recommendations=["Signal too short for meaningful FFT analysis"],
            )

        # Get indices of strongest peaks (excluding DC)
        power_no_dc = power_spectrum[1:]
        freqs_no_dc = freqs[1:]

        # Sort by power (descending)
        sorted_indices = np.argsort(power_no_dc)[::-1]
        top_indices = sorted_indices[:num_peaks]

        # Build period list
        max_power = float(power_no_dc[sorted_indices[0]]) if len(sorted_indices) > 0 else 1.0
        periods: list[DominantPeriod] = []

        for idx in top_indices:
            freq = float(freqs_no_dc[idx])
            power = float(power_no_dc[idx])

            if freq > 0:  # Avoid division by zero
                period_days = 1.0 / freq
                relative_power = power / max_power if max_power > 0 else 0.0

                periods.append(
                    DominantPeriod(
                        period_days=period_days,
                        frequency_hz=freq,
                        power=power,
                        relative_power=relative_power,
                        interpretation=_interpret_period(period_days),
                    )
                )

        # Determine if clear periodicity exists
        # Criteria: strongest peak has >20% of total power (excluding DC)
        total_power = float(np.sum(power_no_dc))
        periodicity_detected = False
        if total_power > 0 and len(periods) > 0:
            strongest_fraction = periods[0].power / total_power
            periodicity_detected = strongest_fraction > 0.2

        # Generate recommendations
        recommendations = []
        if periodicity_detected and len(periods) > 0:
            dominant_period = periods[0].period_days
            recommendations.append(
                f"Detected strong {dominant_period:.1f}-day cycle - "
                "consider preserving in schedule regeneration"
            )

            # Check alignment with ACGME windows
            if abs(dominant_period - 7.0) < 1.0:
                recommendations.append("Weekly pattern aligns with ACGME 1-in-7 rule")
            elif abs(dominant_period - 28.0) < 3.0:
                recommendations.append("Pattern aligns with ACGME 4-week rolling window")
        else:
            recommendations.append(
                "No strong periodic patterns detected - schedule may be irregular"
            )

        return ScheduleCyclesResponse(
            dominant_period_days=periods[0].period_days if periods else None,
            all_periods=periods,
            signal_length_days=len(signal),
            mean_value=mean_value,
            signal_std=signal_std,
            periodicity_detected=periodicity_detected,
            recommendations=recommendations,
        )

    except Exception as e:
        logger.error(f"FFT analysis failed: {e}", exc_info=True)
        return ScheduleCyclesResponse(
            dominant_period_days=None,
            all_periods=[],
            signal_length_days=len(signal),
            mean_value=0.0,
            signal_std=0.0,
            periodicity_detected=False,
            recommendations=[f"Analysis failed: {str(e)}"],
        )


async def analyze_harmonic_resonance(
    signal: list[float],
    sampling_period_days: float = 1.0,
) -> HarmonicResonanceResponse:
    """
    Analyze harmonic resonance with ACGME regulatory windows.

    Checks if detected natural cycles align with or conflict with ACGME
    regulatory periods (7-day, 14-day, 28-day). High alignment indicates
    schedule naturally respects regulatory boundaries.

    Args:
        signal: Time series data (e.g., workload, swap frequency)
        sampling_period_days: Sampling period in days (default 1.0)

    Returns:
        HarmonicResonanceResponse with ACGME alignment scores

    Example:
        result = await analyze_harmonic_resonance(daily_workload)
        if result.overall_resonance > 0.7:
            print("Schedule naturally aligns with ACGME cycles")
    """
    # First detect cycles
    cycles = await detect_schedule_cycles(signal, sampling_period_days)

    # Target ACGME periods
    acgme_periods = {
        "7d": 7.0,
        "14d": 14.0,
        "28d": 28.0,
    }

    # Calculate alignment for each ACGME period
    alignments = {
        "7d": 0.0,
        "14d": 0.0,
        "28d": 0.0,
    }

    resonant_harmonics: list[dict[str, Any]] = []
    dissonant_frequencies: list[dict[str, Any]] = []

    for period_obj in cycles.all_periods:
        for acgme_key, acgme_period in acgme_periods.items():
            # Check alignment with target period
            alignment = _calculate_alignment_score(
                period_obj.period_days, acgme_period, tolerance=0.15
            )
            alignments[acgme_key] = max(alignments[acgme_key], alignment)

            # Track resonant harmonics
            if alignment > 0.5:
                resonant_harmonics.append(
                    {
                        "detected_period_days": period_obj.period_days,
                        "target_period_days": acgme_period,
                        "alignment_score": alignment,
                        "relative_power": period_obj.relative_power,
                        "interpretation": period_obj.interpretation,
                    }
                )

        # Check for dissonant frequencies (strong but not aligned)
        if period_obj.relative_power > 0.3:
            is_dissonant = all(
                _calculate_alignment_score(period_obj.period_days, target, tolerance=0.15) < 0.5
                for target in acgme_periods.values()
            )
            if is_dissonant:
                dissonant_frequencies.append(
                    {
                        "period_days": period_obj.period_days,
                        "relative_power": period_obj.relative_power,
                        "interpretation": period_obj.interpretation,
                    }
                )

    # Overall resonance (weighted average)
    overall_resonance = (
        0.5 * alignments["7d"] + 0.3 * alignments["14d"] + 0.2 * alignments["28d"]
    )

    # Health status
    if overall_resonance >= 0.7:
        health_status = "healthy"
    elif overall_resonance >= 0.4:
        health_status = "degraded"
    else:
        health_status = "critical"

    # Recommendations
    recommendations = []
    if alignments["7d"] < 0.5:
        recommendations.append(
            "Low alignment with 7-day weekly cycle - "
            "consider weekly rotation boundaries"
        )
    if alignments["28d"] < 0.5:
        recommendations.append(
            "Pattern does not align with ACGME 4-week window - "
            "may complicate compliance tracking"
        )
    if len(dissonant_frequencies) > 0:
        recommendations.append(
            f"Detected {len(dissonant_frequencies)} strong non-ACGME cycles - "
            "investigate source of irregular patterns"
        )
    if overall_resonance >= 0.7:
        recommendations.append("Schedule naturally aligns with ACGME regulatory cycles")

    return HarmonicResonanceResponse(
        acgme_7d_alignment=alignments["7d"],
        acgme_14d_alignment=alignments["14d"],
        acgme_28d_alignment=alignments["28d"],
        resonant_harmonics=resonant_harmonics,
        dissonant_frequencies=dissonant_frequencies,
        overall_resonance=overall_resonance,
        health_status=health_status,
        recommendations=recommendations,
    )


async def calculate_spectral_entropy(
    signal: list[float],
    sampling_period_days: float = 1.0,
) -> SpectralEntropyResponse:
    """
    Calculate spectral entropy to measure schedule complexity.

    Spectral entropy quantifies how distributed (complex) vs concentrated
    (simple) the frequency content is. High entropy = many frequencies
    (chaotic/unpredictable). Low entropy = few dominant frequencies
    (periodic/predictable).

    Shannon Entropy: H = -Σ p(f) * log2(p(f))
    Normalized: 0.0 (single frequency) to 1.0 (white noise)

    Args:
        signal: Time series data
        sampling_period_days: Sampling period in days (default 1.0)

    Returns:
        SpectralEntropyResponse with entropy and complexity metrics

    Example:
        result = await calculate_spectral_entropy(workload_series)
        if result.spectral_entropy > 0.8:
            print("Schedule is highly complex/chaotic")
        elif result.spectral_entropy < 0.3:
            print("Schedule is highly regular/predictable")
    """
    # Validate signal
    is_valid, error_msg = _validate_signal(signal, min_length=7)
    if not is_valid:
        logger.warning(f"Invalid signal for entropy: {error_msg}")
        return SpectralEntropyResponse(
            spectral_entropy=0.0,
            entropy_interpretation=f"Cannot calculate: {error_msg}",
            signal_complexity="unknown",
            dominant_frequencies_count=0,
            frequency_concentration=0.0,
            predictability="unknown",
            recommendations=[],
        )

    try:
        # Compute power spectrum
        signal_array = np.array(signal, dtype=float)
        signal_detrended = signal_array - np.mean(signal_array)
        fft_result = np.fft.rfft(signal_detrended)
        power_spectrum = np.abs(fft_result) ** 2

        # Remove DC component
        power_no_dc = power_spectrum[1:]

        if len(power_no_dc) == 0 or np.sum(power_no_dc) == 0:
            return SpectralEntropyResponse(
                spectral_entropy=0.0,
                entropy_interpretation="No AC power (flat signal)",
                signal_complexity="simple",
                dominant_frequencies_count=0,
                frequency_concentration=1.0,
                predictability="high",
                recommendations=["Signal has no variation - completely uniform"],
            )

        # Normalize to probability distribution
        power_normalized = power_no_dc / np.sum(power_no_dc)

        # Shannon entropy: H = -Σ p * log2(p)
        # Avoid log(0) by filtering near-zero values
        power_nonzero = power_normalized[power_normalized > 1e-10]
        entropy_raw = -np.sum(power_nonzero * np.log2(power_nonzero))

        # Normalize to [0, 1] by dividing by max possible entropy
        max_entropy = np.log2(len(power_no_dc))
        spectral_entropy = float(entropy_raw / max_entropy) if max_entropy > 0 else 0.0

        # Count significant frequency components (>5% of max power)
        max_power = float(np.max(power_no_dc))
        significant_freqs = int(np.sum(power_no_dc > 0.05 * max_power))

        # Frequency concentration (inverse of entropy)
        frequency_concentration = 1.0 - spectral_entropy

        # Complexity classification
        if spectral_entropy < 0.3:
            complexity = "simple"
            predictability = "high"
        elif spectral_entropy < 0.6:
            complexity = "moderate"
            predictability = "moderate"
        elif spectral_entropy < 0.8:
            complexity = "complex"
            predictability = "low"
        else:
            complexity = "chaotic"
            predictability = "very low"

        # Interpretation
        if spectral_entropy < 0.3:
            interpretation = "Highly regular schedule with dominant periodic pattern"
        elif spectral_entropy < 0.6:
            interpretation = "Moderately complex schedule with several periodic components"
        elif spectral_entropy < 0.8:
            interpretation = "Complex schedule with many frequency components"
        else:
            interpretation = "Chaotic/irregular schedule approaching white noise"

        # Recommendations
        recommendations = []
        if spectral_entropy > 0.7:
            recommendations.append(
                "High entropy indicates irregular patterns - "
                "consider simplifying rotation structure"
            )
            recommendations.append("Schedule may be unpredictable for residents")
        elif spectral_entropy < 0.3:
            recommendations.append(
                "Low entropy indicates strong regularity - "
                "good for predictability"
            )
            recommendations.append("Schedule has clear periodic structure")
        else:
            recommendations.append(
                "Moderate entropy indicates balanced complexity - "
                "some regularity with flexibility"
            )

        return SpectralEntropyResponse(
            spectral_entropy=spectral_entropy,
            entropy_interpretation=interpretation,
            signal_complexity=complexity,
            dominant_frequencies_count=significant_freqs,
            frequency_concentration=frequency_concentration,
            predictability=predictability,
            recommendations=recommendations,
        )

    except Exception as e:
        logger.error(f"Spectral entropy calculation failed: {e}", exc_info=True)
        return SpectralEntropyResponse(
            spectral_entropy=0.0,
            entropy_interpretation=f"Calculation failed: {str(e)}",
            signal_complexity="unknown",
            dominant_frequencies_count=0,
            frequency_concentration=0.0,
            predictability="unknown",
            recommendations=[],
        )
