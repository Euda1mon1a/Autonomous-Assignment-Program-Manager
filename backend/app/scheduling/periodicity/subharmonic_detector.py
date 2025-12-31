"""
Subharmonic Detector - Time Crystal Inspired Periodicity Analysis.

This module detects natural periodicities and emergent cycle patterns in
medical residency schedules using signal processing techniques inspired by
discrete time crystal physics.

Time Crystal Analogy:
---------------------
| Time Crystal Property     | Scheduling Analog                          |
|---------------------------|--------------------------------------------|
| Periodic driving (T)      | Block structure (7-day week, 28-day ACGME) |
| Subharmonic response (nT) | Q4 call (4×7d), alternating weekends (2×7d)|
| Rigidity under perturbation | Schedule stability despite small changes  |
| Phase locking             | Multiple schedules staying synchronized    |
| Stroboscopic observation  | State advances at discrete checkpoints     |

Key Insight:
------------
Schedules are Floquet systems (periodically driven) with natural cycle
lengths. Instead of treating each block independently, we exploit the
inherent periodicity to create more stable schedules with less churn.

Detected Subharmonics:
----------------------
- 7 days: Weekly pattern (base period)
- 14 days: Biweekly alternation (2×7)
- 21 days: Triweekly rotation (3×7)
- 28 days: ACGME 4-week window (4×7)
- 56 days: 2-month cycles (8×7)
- 84 days: Quarterly rotations (12×7)

References:
-----------
- Section 11 of docs/SYNERGY_ANALYSIS.md (Time Crystal Dynamics)
- Wilczek, F. (2012). Quantum Time Crystals. Physical Review Letters.
- Khemani et al. (2016). Phase Structure of Driven Quantum Systems.

Example:
--------
    from app.scheduling.periodicity import detect_subharmonics

    ***REMOVED*** Detect emergent cycle lengths
    cycles = detect_subharmonics(assignments, base_period=7)
    ***REMOVED*** Returns: [7, 14, 28] - weekly, biweekly, and 4-week ACGME cycles

    ***REMOVED*** Full analysis
    report = analyze_periodicity(schedule)
    print(f"Fundamental: {report.fundamental_period}d")
    print(f"Subharmonics: {report.subharmonic_periods}")
    print(f"Periodicity strength: {report.periodicity_strength:.2f}")
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.signal import find_peaks, periodogram

logger = logging.getLogger(__name__)


***REMOVED*** =============================================================================
***REMOVED*** Data Structures
***REMOVED*** =============================================================================


@dataclass
class PeriodicityReport:
    """
    Comprehensive report on detected periodicities in a schedule.

    This report identifies natural cycle lengths, subharmonic patterns,
    and measures schedule rigidity (resistance to perturbation).

    Attributes:
        fundamental_period: The base period in days (typically 7 for weekly)
        subharmonic_periods: List of detected longer cycles (e.g., [14, 28])
        periodicity_strength: Measure of how regular the schedule is (0-1)
        autocorrelation: Full autocorrelation function
        detected_patterns: Human-readable pattern descriptions
        recommendations: Suggestions for improving schedule periodicity
        metadata: Additional analysis metadata
    """

    fundamental_period: float
    subharmonic_periods: list[float]
    periodicity_strength: float
    autocorrelation: NDArray[np.float64]
    detected_patterns: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Human-readable summary."""
        patterns_str = (
            "\n  - ".join(self.detected_patterns) if self.detected_patterns else "None"
        )
        return (
            f"PeriodicityReport:\n"
            f"  Fundamental Period: {self.fundamental_period:.1f} days\n"
            f"  Subharmonics: {[f'{p:.1f}d' for p in self.subharmonic_periods]}\n"
            f"  Periodicity Strength: {self.periodicity_strength:.2%}\n"
            f"  Detected Patterns:\n  - {patterns_str}"
        )


@dataclass
class TimeSeriesData:
    """
    Time series representation of schedule assignments.

    Attributes:
        values: Signal values (e.g., number of assignments per day)
        dates: Corresponding dates
        person_ids: Person IDs contributing to each time point
        sampling_rate: Samples per day (default: 1.0 for daily)
    """

    values: NDArray[np.float64]
    dates: list[date]
    person_ids: list[list[str]] = field(default_factory=list)
    sampling_rate: float = 1.0

    def __post_init__(self) -> None:
        """Validate time series data."""
        if len(self.values) != len(self.dates):
            raise ValueError(
                f"Values length ({len(self.values)}) != dates length ({len(self.dates)})"
            )
        if len(self.values) < 4:
            raise ValueError(
                f"Time series too short ({len(self.values)} points), need at least 4"
            )


***REMOVED*** =============================================================================
***REMOVED*** Core Detection Functions
***REMOVED*** =============================================================================


def build_assignment_time_series(
    assignments: list[Any],
    person_id: str | None = None,
    aggregation: str = "count",
) -> TimeSeriesData:
    """
    Convert schedule assignments to a time series for periodicity analysis.

    This function transforms assignment data into a temporal signal that can
    be analyzed for periodic patterns. Different aggregation methods reveal
    different aspects of schedule structure.

    Args:
        assignments: List of Assignment objects with block, person_id attributes
        person_id: Optional filter for specific person (None = all people)
        aggregation: How to aggregate assignments per day:
            - "count": Number of assignments per day
            - "hours": Total hours per day (if assignment has hours field)
            - "binary": 1 if any assignment, 0 otherwise
            - "unique_people": Number of unique people assigned per day

    Returns:
        TimeSeriesData with values, dates, and metadata

    Raises:
        ValueError: If no assignments or invalid aggregation method

    Example:
        >>> ts = build_assignment_time_series(assignments, aggregation="count")
        >>> print(f"Signal length: {len(ts.values)} days")
        >>> print(f"Mean assignments/day: {ts.values.mean():.1f}")
    """
    if not assignments:
        raise ValueError("Cannot build time series from empty assignment list")

    ***REMOVED*** Filter by person if requested
    if person_id:
        assignments = [a for a in assignments if a.person_id == person_id]
        if not assignments:
            raise ValueError(f"No assignments found for person_id={person_id}")

    ***REMOVED*** Group assignments by date
    assignments_by_date: dict[date, list[Any]] = defaultdict(list)
    for assignment in assignments:
        if hasattr(assignment, "block") and hasattr(assignment.block, "date"):
            assignment_date = assignment.block.date
            assignments_by_date[assignment_date].append(assignment)
        else:
            logger.warning(
                f"Assignment {assignment.id} missing block or block.date, skipping"
            )

    if not assignments_by_date:
        raise ValueError("No valid assignments with block dates found")

    ***REMOVED*** Sort dates
    sorted_dates = sorted(assignments_by_date.keys())

    ***REMOVED*** Build time series based on aggregation method
    values = []
    person_ids_per_date = []

    for current_date in sorted_dates:
        day_assignments = assignments_by_date[current_date]

        if aggregation == "count":
            values.append(float(len(day_assignments)))
        elif aggregation == "hours":
            ***REMOVED*** Sum hours if available, otherwise count × 12 (half-day assumption)
            total_hours = sum(getattr(a, "hours", 12.0) for a in day_assignments)
            values.append(float(total_hours))
        elif aggregation == "binary":
            values.append(1.0 if day_assignments else 0.0)
        elif aggregation == "unique_people":
            unique_people = len(set(a.person_id for a in day_assignments))
            values.append(float(unique_people))
        else:
            raise ValueError(
                f"Invalid aggregation method: {aggregation}. "
                f"Choose from: count, hours, binary, unique_people"
            )

        ***REMOVED*** Track person IDs
        person_ids_per_date.append([str(a.person_id) for a in day_assignments])

    values_array = np.array(values, dtype=np.float64)

    logger.debug(
        f"Built time series: {len(values_array)} days, "
        f"range=[{sorted_dates[0]} to {sorted_dates[-1]}], "
        f"aggregation={aggregation}"
    )

    return TimeSeriesData(
        values=values_array,
        dates=sorted_dates,
        person_ids=person_ids_per_date,
        sampling_rate=1.0,  ***REMOVED*** Daily samples
    )


def detect_subharmonics(
    assignments: list[Any],
    base_period: int = 7,
    min_significance: float = 0.3,
    max_period: int | None = None,
) -> list[int]:
    """
    Detect emergent subharmonic cycle lengths in assignment patterns.

    Uses autocorrelation to identify natural periodicities in the schedule.
    Subharmonics are longer cycles that are multiples of the base period
    (e.g., Q4 call creates a 28-day cycle from a 7-day week).

    Algorithm:
    ----------
    1. Convert assignments to time series
    2. Compute autocorrelation function (ACF)
    3. Find peaks in ACF (these indicate periodicities)
    4. Filter to multiples of base_period
    5. Return sorted list of detected cycle lengths

    Args:
        assignments: List of Assignment objects
        base_period: Base cycle length in days (default: 7 for weekly)
        min_significance: Minimum ACF correlation for significance (0-1)
        max_period: Maximum period to search (None = half signal length)

    Returns:
        List of detected cycle lengths in days, sorted ascending.
        Always includes base_period if detected.

    Example:
        >>> cycles = detect_subharmonics(assignments, base_period=7)
        >>> print(cycles)
        [7, 14, 28]  ***REMOVED*** Weekly, biweekly, 4-week ACGME cycles
    """
    if not assignments:
        logger.warning("No assignments provided, returning base period only")
        return [base_period]

    ***REMOVED*** Build time series
    try:
        ts = build_assignment_time_series(assignments, aggregation="count")
    except ValueError as e:
        logger.warning(f"Failed to build time series: {e}, returning base period only")
        return [base_period]

    ***REMOVED*** Compute autocorrelation
    signal = ts.values - np.mean(ts.values)  ***REMOVED*** Center the signal
    autocorr = np.correlate(signal, signal, mode="full")
    autocorr = autocorr[len(autocorr) // 2 :]  ***REMOVED*** Take positive lags only

    ***REMOVED*** Normalize autocorrelation
    autocorr = autocorr / autocorr[0] if autocorr[0] != 0 else autocorr

    ***REMOVED*** Set max period if not specified
    if max_period is None:
        max_period = min(len(ts.values) // 2, 90)  ***REMOVED*** Cap at ~3 months

    ***REMOVED*** Find peaks in autocorrelation
    ***REMOVED*** Use find_peaks with minimum height threshold
    peaks, properties = find_peaks(
        autocorr[:max_period],
        height=min_significance,
        distance=base_period // 2,  ***REMOVED*** Peaks should be separated
    )

    if len(peaks) == 0:
        logger.info(f"No significant peaks found, returning base period {base_period}")
        return [base_period]

    ***REMOVED*** Filter to multiples of base period (with tolerance)
    tolerance = 1  ***REMOVED*** Allow ±1 day tolerance
    subharmonics = []

    for peak_lag in peaks:
        ***REMOVED*** Check if this is close to a multiple of base_period
        multiple = round(peak_lag / base_period)
        if multiple == 0:
            continue

        expected_lag = multiple * base_period
        if abs(peak_lag - expected_lag) <= tolerance:
            ***REMOVED*** This is a subharmonic
            detected_period = int(expected_lag)
            if detected_period not in subharmonics:
                subharmonics.append(detected_period)
                logger.debug(
                    f"Detected subharmonic: {detected_period}d "
                    f"(ACF={autocorr[peak_lag]:.3f})"
                )

    ***REMOVED*** Always include base period if not already there
    if base_period not in subharmonics:
        subharmonics.append(base_period)

    ***REMOVED*** Sort and return
    subharmonics.sort()

    logger.info(
        f"Detected {len(subharmonics)} subharmonic cycles: "
        f"{subharmonics} (base={base_period}d)"
    )

    return subharmonics


def analyze_periodicity(
    assignments: list[Any],
    base_period: int = 7,
) -> PeriodicityReport:
    """
    Perform comprehensive periodicity analysis on a schedule.

    This is the main entry point for time crystal-inspired schedule analysis.
    It detects fundamental and subharmonic periods, measures schedule
    regularity, and provides recommendations.

    Analysis includes:
    ------------------
    - Autocorrelation-based cycle detection
    - Spectral analysis (periodogram) for frequency content
    - Pattern identification (Q4 call, alternating weekends, etc.)
    - Periodicity strength measurement
    - Recommendations for improving schedule rigidity

    Args:
        assignments: List of Assignment objects
        base_period: Expected fundamental period in days (default: 7)

    Returns:
        PeriodicityReport with complete analysis results

    Example:
        >>> report = analyze_periodicity(schedule.assignments)
        >>> print(report)
        >>> if report.periodicity_strength < 0.5:
        ...     print("Warning: Schedule lacks strong periodic structure")
    """
    if not assignments:
        logger.warning("No assignments to analyze")
        return PeriodicityReport(
            fundamental_period=float(base_period),
            subharmonic_periods=[],
            periodicity_strength=0.0,
            autocorrelation=np.array([1.0]),
            detected_patterns=["No assignments found"],
            recommendations=["Cannot analyze empty schedule"],
            metadata={"error": "empty_schedule"},
        )

    ***REMOVED*** Build time series
    try:
        ts = build_assignment_time_series(assignments, aggregation="count")
    except ValueError as e:
        logger.error(f"Failed to build time series: {e}")
        return PeriodicityReport(
            fundamental_period=float(base_period),
            subharmonic_periods=[],
            periodicity_strength=0.0,
            autocorrelation=np.array([1.0]),
            detected_patterns=[],
            recommendations=[f"Error: {e}"],
            metadata={"error": str(e)},
        )

    ***REMOVED*** Detect subharmonics
    subharmonics = detect_subharmonics(assignments, base_period=base_period)

    ***REMOVED*** Compute full autocorrelation for report
    signal = ts.values - np.mean(ts.values)
    autocorr = np.correlate(signal, signal, mode="full")
    autocorr = autocorr[len(autocorr) // 2 :]
    autocorr = autocorr / autocorr[0] if autocorr[0] != 0 else autocorr

    ***REMOVED*** Measure periodicity strength using spectral power concentration
    ***REMOVED*** Use periodogram to get power spectral density
    try:
        freqs, psd = periodogram(ts.values, fs=ts.sampling_rate)

        ***REMOVED*** Find peak power
        peak_power = np.max(psd) if len(psd) > 0 else 0
        total_power = np.sum(psd) if len(psd) > 0 else 1

        ***REMOVED*** Periodicity strength = ratio of peak power to total power
        ***REMOVED*** High value means energy concentrated in specific frequencies (periodic)
        periodicity_strength = float(peak_power / total_power if total_power > 0 else 0)

        ***REMOVED*** Clip to [0, 1] and apply square root for better dynamic range
        periodicity_strength = min(1.0, np.sqrt(periodicity_strength))
    except Exception as e:
        logger.warning(f"Periodogram calculation failed: {e}")
        periodicity_strength = 0.5  ***REMOVED*** Default moderate strength

    ***REMOVED*** Identify patterns based on detected subharmonics
    patterns = []
    if 7 in subharmonics:
        patterns.append("Weekly pattern detected (7-day cycle)")
    if 14 in subharmonics:
        patterns.append("Biweekly alternation detected (14-day cycle)")
    if 21 in subharmonics:
        patterns.append("Triweekly rotation detected (21-day cycle)")
    if 28 in subharmonics:
        patterns.append("ACGME 4-week window detected (28-day cycle)")
    if any(s >= 56 for s in subharmonics):
        long_cycles = [s for s in subharmonics if s >= 56]
        patterns.append(f"Long-term cycles detected: {long_cycles} days")

    ***REMOVED*** Generate recommendations
    recommendations = _generate_periodicity_recommendations(
        subharmonics=subharmonics,
        base_period=base_period,
        strength=periodicity_strength,
        ts=ts,
    )

    ***REMOVED*** Metadata
    metadata = {
        "n_assignments": len(assignments),
        "n_days": len(ts.values),
        "date_range": f"{ts.dates[0]} to {ts.dates[-1]}",
        "mean_assignments_per_day": float(np.mean(ts.values)),
        "std_assignments_per_day": float(np.std(ts.values)),
        "autocorr_at_base": float(autocorr[base_period])
        if len(autocorr) > base_period
        else 0.0,
    }

    logger.info(
        f"Periodicity analysis complete: strength={periodicity_strength:.2f}, "
        f"patterns={len(patterns)}"
    )

    return PeriodicityReport(
        fundamental_period=float(base_period),
        subharmonic_periods=[float(s) for s in subharmonics if s != base_period],
        periodicity_strength=periodicity_strength,
        autocorrelation=autocorr,
        detected_patterns=patterns,
        recommendations=recommendations,
        metadata=metadata,
    )


def _generate_periodicity_recommendations(
    subharmonics: list[int],
    base_period: int,
    strength: float,
    ts: TimeSeriesData,
) -> list[str]:
    """
    Generate actionable recommendations based on periodicity analysis.

    Args:
        subharmonics: Detected cycle lengths
        base_period: Fundamental period
        strength: Periodicity strength (0-1)
        ts: Time series data

    Returns:
        List of recommendation strings
    """
    recommendations = []

    ***REMOVED*** Check periodicity strength
    if strength < 0.3:
        recommendations.append(
            "WEAK PERIODICITY: Schedule lacks regular patterns. "
            "Consider enforcing more consistent rotation cycles."
        )
    elif strength < 0.6:
        recommendations.append(
            "MODERATE PERIODICITY: Some regular patterns detected. "
            "Could improve schedule predictability with more consistent cycles."
        )
    else:
        recommendations.append(
            "STRONG PERIODICITY: Schedule exhibits clear regular patterns. "
            "Good rigidity against perturbations."
        )

    ***REMOVED*** Check for expected cycles
    if base_period not in subharmonics:
        recommendations.append(
            f"Missing {base_period}-day fundamental cycle. "
            f"Schedule may lack weekly structure."
        )

    if 28 not in subharmonics:
        recommendations.append(
            "Missing 28-day ACGME cycle. "
            "Consider aligning rotations with 4-week ACGME averaging windows."
        )

    ***REMOVED*** Check for too many or too few subharmonics
    if len(subharmonics) > 6:
        recommendations.append(
            f"Many cycles detected ({len(subharmonics)}). "
            f"Simplify schedule structure to reduce complexity."
        )
    elif len(subharmonics) == 1:
        recommendations.append(
            "Only one cycle detected. "
            "Schedule may be too rigid or lacking emergent patterns."
        )

    ***REMOVED*** Check variance in assignment counts
    if len(ts.values) > 0:
        cv = np.std(ts.values) / np.mean(ts.values) if np.mean(ts.values) > 0 else 0
        if cv > 1.0:
            recommendations.append(
                f"High variability in daily assignments (CV={cv:.2f}). "
                f"Consider more balanced workload distribution."
            )

    return recommendations


***REMOVED*** =============================================================================
***REMOVED*** Subharmonic Detector Class
***REMOVED*** =============================================================================


class SubharmonicDetector:
    """
    Time crystal-inspired detector for schedule periodicities.

    This class provides a stateful interface for detecting and tracking
    subharmonic patterns across multiple schedules or time periods.

    Attributes:
        base_period: Fundamental period in days (default: 7)
        min_significance: Minimum autocorrelation for detection
        history: List of past PeriodicityReports for trend analysis

    Example:
        >>> detector = SubharmonicDetector(base_period=7)
        >>> report = detector.analyze(assignments)
        >>> print(f"Detected {len(report.subharmonic_periods)} subharmonics")
        >>> detector.compare_to_previous(report)  ***REMOVED*** Track changes over time
    """

    def __init__(
        self,
        base_period: int = 7,
        min_significance: float = 0.3,
    ):
        """
        Initialize subharmonic detector.

        Args:
            base_period: Fundamental cycle length in days
            min_significance: Minimum ACF correlation threshold
        """
        self.base_period = base_period
        self.min_significance = min_significance
        self.history: list[PeriodicityReport] = []

        logger.info(
            f"Initialized SubharmonicDetector: base={base_period}d, "
            f"threshold={min_significance}"
        )

    def analyze(self, assignments: list[Any]) -> PeriodicityReport:
        """
        Analyze schedule and detect subharmonics.

        Args:
            assignments: List of Assignment objects

        Returns:
            PeriodicityReport with analysis results
        """
        report = analyze_periodicity(assignments, base_period=self.base_period)
        self.history.append(report)
        return report

    def compare_to_previous(self, current: PeriodicityReport) -> dict[str, Any]:
        """
        Compare current analysis to previous reports.

        Tracks changes in periodicity strength and detected patterns over time.

        Args:
            current: Current periodicity report

        Returns:
            Dict with comparison metrics
        """
        if len(self.history) < 2:
            return {"status": "insufficient_history", "n_reports": len(self.history)}

        previous = self.history[-2]

        ***REMOVED*** Compare periodicity strength
        strength_change = current.periodicity_strength - previous.periodicity_strength

        ***REMOVED*** Compare subharmonics
        prev_set = set(previous.subharmonic_periods)
        curr_set = set(current.subharmonic_periods)
        new_cycles = curr_set - prev_set
        lost_cycles = prev_set - curr_set

        ***REMOVED*** Trend analysis
        if len(self.history) >= 3:
            recent_strengths = [r.periodicity_strength for r in self.history[-3:]]
            trend = (
                "improving"
                if all(
                    recent_strengths[i] < recent_strengths[i + 1]
                    for i in range(len(recent_strengths) - 1)
                )
                else "declining"
                if all(
                    recent_strengths[i] > recent_strengths[i + 1]
                    for i in range(len(recent_strengths) - 1)
                )
                else "stable"
            )
        else:
            trend = "unknown"

        return {
            "status": "compared",
            "strength_change": float(strength_change),
            "strength_trend": trend,
            "new_cycles": list(new_cycles),
            "lost_cycles": list(lost_cycles),
            "n_reports_analyzed": len(self.history),
        }

    def get_stability_score(self) -> float:
        """
        Calculate overall schedule stability score based on history.

        Stability is high when:
        - Periodicity strength is consistently high
        - Subharmonic patterns remain consistent
        - Variance in patterns is low

        Returns:
            Stability score (0-1), higher is more stable
        """
        if not self.history:
            return 0.0

        ***REMOVED*** Average periodicity strength
        avg_strength = np.mean([r.periodicity_strength for r in self.history])

        ***REMOVED*** Consistency in subharmonic counts
        n_subharmonics = [len(r.subharmonic_periods) for r in self.history]
        consistency = 1.0 - (np.std(n_subharmonics) / (np.mean(n_subharmonics) + 1e-6))

        ***REMOVED*** Combine metrics
        stability = 0.7 * avg_strength + 0.3 * consistency

        return float(np.clip(stability, 0.0, 1.0))


***REMOVED*** =============================================================================
***REMOVED*** Utility Functions
***REMOVED*** =============================================================================


def visualize_autocorrelation(
    autocorr: NDArray[np.float64],
    max_lag: int = 60,
    title: str = "Autocorrelation Function",
) -> str:
    """
    Create ASCII visualization of autocorrelation function.

    Useful for debugging and quick inspection in logs.

    Args:
        autocorr: Autocorrelation values
        max_lag: Maximum lag to display
        title: Plot title

    Returns:
        ASCII art string representation
    """
    max_lag = min(max_lag, len(autocorr))
    autocorr_subset = autocorr[:max_lag]

    lines = [title, "=" * 60]

    ***REMOVED*** Scale values to character width
    width = 50
    for lag, val in enumerate(autocorr_subset):
        if lag % 7 == 0:  ***REMOVED*** Mark weekly boundaries
            marker = "*"
        else:
            marker = "|"

        n_chars = int(abs(val) * width)
        if val >= 0:
            bar = " " * 25 + marker + "█" * n_chars
        else:
            bar = " " * (25 - n_chars) + "█" * n_chars + marker

        lines.append(f"{lag:3d}d {bar} {val:+.3f}")

    lines.append("=" * 60)
    return "\n".join(lines)
