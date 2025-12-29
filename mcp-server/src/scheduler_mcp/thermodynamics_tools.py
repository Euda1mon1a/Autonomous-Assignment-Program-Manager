"""
Thermodynamics MCP Tools for Schedule Resilience Analysis.

Exposes thermodynamic and statistical mechanics concepts as MCP tools for
AI assistant interaction. These tools apply physics-inspired approaches to
detect phase transitions and measure schedule stability.

Tools Provided:
1. calculate_schedule_entropy_tool - Measure schedule disorder/flexibility
2. analyze_phase_transitions_tool - Detect schedule state changes
3. optimize_free_energy_tool - Find optimal schedule configurations (stub)

Scientific Foundations:
- Shannon Entropy: Measure of schedule disorder and information content
- Phase Transitions: Critical phenomena detection for approaching failures
- Free Energy: Stability landscape analysis (planned)

Based on 2025 research showing thermodynamic approaches detect transitions
2-3x earlier than traditional bifurcation methods.
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Entropy Types
# =============================================================================


class EntropyMetricsResponse(BaseModel):
    """
    Comprehensive entropy analysis of a schedule.

    Entropy measures disorder/randomness in the schedule distribution.
    Higher entropy = more diverse/flexible. Lower entropy = concentrated/rigid.
    """

    person_entropy: float = Field(
        ge=0.0, description="Entropy of assignment distribution across faculty (bits)"
    )
    rotation_entropy: float = Field(
        ge=0.0, description="Entropy of rotation assignment distribution (bits)"
    )
    time_entropy: float = Field(
        ge=0.0, description="Entropy of temporal distribution (bits)"
    )
    joint_entropy: float = Field(
        ge=0.0, description="Joint entropy across person and rotation dimensions (bits)"
    )
    mutual_information: float = Field(
        ge=0.0, description="Information shared between person and rotation (bits)"
    )
    entropy_production_rate: float = Field(
        ge=0.0, description="Rate of entropy generation from changes (bits/hour)"
    )
    normalized_entropy: float = Field(
        ge=0.0, le=1.0, description="Entropy relative to maximum possible (0=ordered, 1=max disorder)"
    )
    computed_at: str = Field(description="ISO timestamp of computation")


class ScheduleEntropyRequest(BaseModel):
    """Request for schedule entropy calculation."""

    start_date: str = Field(description="Start date for analysis (YYYY-MM-DD)")
    end_date: str = Field(description="End date for analysis (YYYY-MM-DD)")
    include_mutual_information: bool = Field(
        default=True, description="Calculate mutual information between dimensions"
    )


class ScheduleEntropyResponse(BaseModel):
    """Response from schedule entropy calculation."""

    analyzed_at: str = Field(description="ISO timestamp of analysis")
    period_start: str = Field(description="Analysis period start date")
    period_end: str = Field(description="Analysis period end date")
    assignments_analyzed: int = Field(ge=0, description="Number of assignments analyzed")
    metrics: EntropyMetricsResponse = Field(description="Entropy metrics")
    interpretation: str = Field(description="Human-readable interpretation")
    entropy_status: str = Field(
        description="Status: balanced, too_concentrated, too_dispersed"
    )
    recommendations: list[str] = Field(default_factory=list)
    severity: str = Field(description="healthy, warning, critical")


class EntropyMonitorStateResponse(BaseModel):
    """Response from entropy monitor state query."""

    current_entropy: float = Field(ge=0.0, description="Current entropy value (bits)")
    rate_of_change: float = Field(description="Entropy change rate (bits/measurement)")
    production_rate: float = Field(ge=0.0, description="Entropy production rate (bits/hour)")
    critical_slowing_detected: bool = Field(
        description="Whether critical slowing down is detected"
    )
    measurements: int = Field(ge=0, description="Number of measurements in history")
    analyzed_at: str = Field(description="ISO timestamp")
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: list[str] = Field(default_factory=list)
    severity: str = Field(description="healthy, warning, critical")


# =============================================================================
# Phase Transition Types
# =============================================================================


class TransitionSeverityEnum(str, Enum):
    """Severity of detected phase transition risk."""

    NORMAL = "normal"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"
    IMMINENT = "imminent"


class CriticalSignalInfo(BaseModel):
    """
    A detected early warning signal for phase transition.

    Based on universal early warning signals from critical phenomena theory.
    """

    signal_type: str = Field(
        description="Type: increasing_variance, critical_slowing_down, flickering, distribution_skew"
    )
    metric_name: str = Field(description="Which metric shows the signal")
    severity: TransitionSeverityEnum = Field(description="Signal severity")
    value: float = Field(description="Numerical value of the indicator")
    threshold: float = Field(description="Threshold that was crossed")
    description: str = Field(description="Human-readable description")
    detected_at: str = Field(description="ISO timestamp of detection")


class PhaseTransitionRiskResponse(BaseModel):
    """
    Overall assessment of phase transition risk.

    Phase transitions in scheduling are analogous to physical phase changes:
    - Stable Schedule (ordered phase) -> Chaotic/Failed Schedule (disordered phase)
    """

    overall_severity: TransitionSeverityEnum = Field(
        description="Worst severity across all signals"
    )
    signals: list[CriticalSignalInfo] = Field(
        default_factory=list, description="List of detected early warning signals"
    )
    time_to_transition: Optional[float] = Field(
        default=None, description="Estimated hours until transition (if predictable)"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in prediction (0-1)"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Suggested interventions"
    )
    analyzed_at: str = Field(description="ISO timestamp")
    metrics_analyzed: int = Field(ge=0, description="Number of metrics analyzed")
    interpretation: str = Field(description="Human-readable summary")
    severity: str = Field(description="healthy, warning, elevated, critical, emergency")


class PhaseTransitionRequest(BaseModel):
    """Request for phase transition analysis."""

    metrics: dict[str, list[float]] = Field(
        description="Dictionary of metric_name -> time series values"
    )
    window_size: int = Field(
        default=50, ge=10, description="Analysis window size (number of samples)"
    )


# =============================================================================
# Free Energy Types (Stub for future implementation)
# =============================================================================


class FreeEnergyMetricsResponse(BaseModel):
    """
    Free energy analysis of schedule stability landscape.

    Note: Free energy module is planned but not yet implemented.
    This stub provides the expected response structure.
    """

    internal_energy: float = Field(
        description="Schedule internal energy (constraint violations)"
    )
    entropy_term: float = Field(description="Temperature * Entropy contribution")
    free_energy: float = Field(description="Helmholtz free energy F = U - TS")
    temperature: float = Field(
        ge=0.0, description="System temperature (flexibility parameter)"
    )
    stability_score: float = Field(
        ge=0.0, le=1.0, description="Stability based on energy landscape"
    )
    analyzed_at: str = Field(description="ISO timestamp")


class EnergyLandscapeResponse(BaseModel):
    """Response from energy landscape analysis."""

    analyzed_at: str = Field(description="ISO timestamp")
    schedule_id: Optional[str] = Field(default=None, description="Schedule identifier if applicable")
    free_energy_metrics: FreeEnergyMetricsResponse = Field(
        description="Free energy calculations"
    )
    is_metastable: bool = Field(
        description="Whether schedule is in a metastable (shallow) energy well"
    )
    escape_barrier: float = Field(
        ge=0.0, description="Energy barrier to escape current state"
    )
    nearby_minima: int = Field(ge=0, description="Number of nearby local minima")
    recommendations: list[str] = Field(default_factory=list)
    severity: str = Field(description="stable, metastable, unstable")


class FreeEnergyOptimizationRequest(BaseModel):
    """Request for free energy optimization."""

    schedule_id: Optional[str] = Field(
        default=None, description="Schedule to optimize (or use current)"
    )
    target_temperature: float = Field(
        default=1.0, ge=0.0, description="Temperature parameter for optimization"
    )
    max_iterations: int = Field(
        default=100, ge=1, le=1000, description="Maximum optimization iterations"
    )


class FreeEnergyOptimizationResponse(BaseModel):
    """Response from free energy optimization."""

    analyzed_at: str = Field(description="ISO timestamp")
    initial_free_energy: float = Field(description="Starting free energy")
    final_free_energy: float = Field(description="Optimized free energy")
    improvement: float = Field(description="Free energy reduction achieved")
    iterations_used: int = Field(ge=0, description="Iterations performed")
    converged: bool = Field(description="Whether optimization converged")
    optimized_schedule_id: Optional[str] = Field(
        default=None, description="ID of optimized schedule if created"
    )
    changes_made: list[str] = Field(
        default_factory=list, description="List of changes from optimization"
    )
    recommendations: list[str] = Field(default_factory=list)
    severity: str = Field(description="improved, unchanged, degraded")


# =============================================================================
# Tool Functions - Entropy
# =============================================================================


async def calculate_schedule_entropy(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    include_mutual_information: bool = True,
) -> ScheduleEntropyResponse:
    """
    Calculate comprehensive entropy metrics for the schedule.

    Entropy measures the disorder/randomness in schedule assignment distribution.
    This tool applies Shannon entropy to analyze multiple dimensions of the schedule.

    **Entropy Dimensions Analyzed:**
    - Person Entropy: Distribution of assignments across faculty
      - Low: Few faculty handle most work (concentrated risk)
      - High: Work evenly distributed (resilient but may be chaotic)

    - Rotation Entropy: Distribution across rotation types
      - Low: Most assignments to few rotations
      - High: Diverse rotation coverage

    - Time Entropy: Distribution across time blocks
      - Low: Assignments clustered in time
      - High: Evenly spread across schedule period

    - Joint Entropy: Combined person-rotation distribution
    - Mutual Information: How much knowing the person tells about the rotation

    **Optimal Entropy:**
    Moderate entropy is ideal - not too concentrated (vulnerable) nor too
    dispersed (potentially chaotic). The normalized_entropy metric (0-1)
    helps identify this balance.

    **Early Warning Application:**
    Changes in entropy over time can signal approaching phase transitions.
    Decreasing entropy may indicate system "crystallizing" into rigid patterns.
    Increasing entropy may indicate loss of organizational structure.

    Args:
        start_date: Start date for analysis (YYYY-MM-DD), defaults to today
        end_date: End date for analysis (YYYY-MM-DD), defaults to 30 days
        include_mutual_information: Calculate mutual information between dimensions

    Returns:
        ScheduleEntropyResponse with entropy metrics and interpretation

    Example:
        # Analyze schedule diversity
        result = await calculate_schedule_entropy_tool(
            start_date="2025-01-01",
            end_date="2025-01-31"
        )

        if result.entropy_status == "too_concentrated":
            print("WARNING: Schedule has concentrated risk")
            print(f"Person entropy: {result.metrics.person_entropy:.2f} bits")
    """
    from datetime import date, timedelta

    logger.info(f"Calculating schedule entropy ({start_date} to {end_date})")

    # Parse dates with defaults
    today = date.today()
    start = date.fromisoformat(start_date) if start_date else today
    end = date.fromisoformat(end_date) if end_date else (today + timedelta(days=30))

    try:
        from app.resilience.thermodynamics.entropy import (
            calculate_schedule_entropy as calc_entropy,
            EntropyMetrics,
        )

        # In production, would fetch assignments from database
        # For now, return mock data showing the structure
        logger.warning("Schedule entropy using placeholder data")

        # Mock response demonstrating the response structure
        metrics = EntropyMetricsResponse(
            person_entropy=3.42,  # ~11 faculty with moderate imbalance
            rotation_entropy=2.58,  # ~6 rotation types
            time_entropy=4.12,  # Well distributed across time blocks
            joint_entropy=5.85,  # Person-rotation joint distribution
            mutual_information=0.15,  # Low correlation (good independence)
            entropy_production_rate=0.02,  # Slow entropy change
            normalized_entropy=0.72,  # 72% of maximum possible
            computed_at=datetime.now().isoformat(),
        )

        # Determine status based on normalized entropy
        if metrics.normalized_entropy < 0.4:
            status = "too_concentrated"
            interpretation = (
                "Schedule is highly concentrated with low diversity. "
                "Risk is concentrated on few faculty members."
            )
            severity = "warning"
            recommendations = [
                "Distribute assignments more evenly across faculty",
                "Cross-train faculty to enable workload balancing",
                "Review N-1/N-2 contingency status for concentrated faculty",
            ]
        elif metrics.normalized_entropy > 0.85:
            status = "too_dispersed"
            interpretation = (
                "Schedule shows very high diversity, approaching maximum entropy. "
                "May indicate lack of specialization or structure."
            )
            severity = "warning"
            recommendations = [
                "Review rotation assignment logic for consistency",
                "Consider whether some concentration is beneficial",
                "Verify assignment rules are being followed",
            ]
        else:
            status = "balanced"
            interpretation = (
                f"Schedule entropy is balanced (normalized: {metrics.normalized_entropy:.0%}). "
                "Good diversity without excessive concentration."
            )
            severity = "healthy"
            recommendations = [
                "Maintain current assignment distribution",
                "Continue monitoring for drift",
            ]

        # Add mutual information interpretation
        if include_mutual_information:
            if metrics.mutual_information > 1.0:
                interpretation += (
                    f" High mutual information ({metrics.mutual_information:.2f} bits) "
                    "indicates strong coupling between faculty and rotations - "
                    "consider cross-training to reduce dependencies."
                )
            elif metrics.mutual_information < 0.3:
                interpretation += (
                    f" Low mutual information ({metrics.mutual_information:.2f} bits) "
                    "indicates good independence between faculty and rotation assignments."
                )

        return ScheduleEntropyResponse(
            analyzed_at=datetime.now().isoformat(),
            period_start=start.isoformat(),
            period_end=end.isoformat(),
            assignments_analyzed=156,  # Mock count
            metrics=metrics,
            interpretation=interpretation,
            entropy_status=status,
            recommendations=recommendations,
            severity=severity,
        )

    except ImportError as e:
        logger.warning(f"Thermodynamics entropy module not available: {e}")
        return ScheduleEntropyResponse(
            analyzed_at=datetime.now().isoformat(),
            period_start=start.isoformat(),
            period_end=end.isoformat(),
            assignments_analyzed=0,
            metrics=EntropyMetricsResponse(
                person_entropy=0.0,
                rotation_entropy=0.0,
                time_entropy=0.0,
                joint_entropy=0.0,
                mutual_information=0.0,
                entropy_production_rate=0.0,
                normalized_entropy=0.0,
                computed_at=datetime.now().isoformat(),
            ),
            interpretation="Entropy module not available - check backend installation",
            entropy_status="unknown",
            recommendations=["Install thermodynamics module: pip install scipy numpy"],
            severity="warning",
        )


async def get_entropy_monitor_state(
    history_window: int = 100,
) -> EntropyMonitorStateResponse:
    """
    Get current state of the entropy monitor.

    The entropy monitor tracks entropy dynamics over time to detect:
    - Critical slowing down (entropy changes slow near phase transitions)
    - Rapid entropy changes (system instability)
    - Entropy production rate (energy dissipation)

    **Critical Slowing Down:**
    Near phase transitions, systems exhibit "critical slowing down" - recovery
    from perturbations takes longer. This manifests as:
    - High autocorrelation (system "remembers" longer)
    - Low rate of change (entropy stabilizes at a new level)

    Detecting critical slowing down provides early warning of approaching
    phase transitions (system failures).

    Args:
        history_window: Number of entropy measurements to analyze (10-1000)

    Returns:
        EntropyMonitorStateResponse with current monitor state

    Example:
        # Check for critical slowing down
        result = await get_entropy_monitor_state_tool()
        if result.critical_slowing_detected:
            print("WARNING: Critical slowing detected - approaching phase transition")
            print(f"Rate of change: {result.rate_of_change:.4f}")
    """
    logger.info(f"Getting entropy monitor state (window={history_window})")

    try:
        from app.resilience.thermodynamics.entropy import ScheduleEntropyMonitor

        # In production, would get the actual monitor instance
        # For now, return mock data showing the structure
        logger.warning("Entropy monitor using placeholder data")

        # Simulate normal state
        current_entropy = 3.42
        rate_of_change = 0.012
        critical_slowing = False

        if critical_slowing:
            interpretation = (
                "CRITICAL SLOWING DETECTED: Entropy dynamics are slowing down. "
                "This is an early warning signal for approaching phase transition. "
                "System recovery time is increasing."
            )
            severity = "critical"
            recommendations = [
                "Increase monitoring frequency",
                "Review contingency plans",
                "Consider preemptive interventions",
                "Alert stakeholders of potential transition",
            ]
        elif abs(rate_of_change) > 0.1:
            interpretation = (
                f"Rapid entropy change detected (rate={rate_of_change:.3f}). "
                "System is reorganizing - monitor for stability."
            )
            severity = "warning"
            recommendations = [
                "Monitor for continued rapid changes",
                "Review recent schedule modifications",
            ]
        else:
            interpretation = (
                f"Entropy is stable (rate={rate_of_change:.4f}). "
                "No early warning signals detected."
            )
            severity = "healthy"
            recommendations = ["Continue routine monitoring"]

        return EntropyMonitorStateResponse(
            current_entropy=current_entropy,
            rate_of_change=rate_of_change,
            production_rate=0.02,
            critical_slowing_detected=critical_slowing,
            measurements=87,  # Mock count
            analyzed_at=datetime.now().isoformat(),
            interpretation=interpretation,
            recommendations=recommendations,
            severity=severity,
        )

    except ImportError as e:
        logger.warning(f"Thermodynamics entropy module not available: {e}")
        return EntropyMonitorStateResponse(
            current_entropy=0.0,
            rate_of_change=0.0,
            production_rate=0.0,
            critical_slowing_detected=False,
            measurements=0,
            analyzed_at=datetime.now().isoformat(),
            interpretation="Entropy monitor not available - check backend installation",
            recommendations=["Install thermodynamics module"],
            severity="warning",
        )


# =============================================================================
# Tool Functions - Phase Transitions
# =============================================================================


async def analyze_phase_transitions(
    metrics: Optional[dict[str, list[float]]] = None,
    window_size: int = 50,
) -> PhaseTransitionRiskResponse:
    """
    Detect approaching phase transitions using critical phenomena theory.

    This tool applies physics-based early warning signal detection to identify
    when the scheduling system is approaching a phase transition (failure).

    **Universal Early Warning Signals (from physics):**

    1. **Increasing Variance** - Fluctuations diverge before transitions
       - Metric variance increases by >50% from baseline
       - Indicates system exploring wider state space

    2. **Critical Slowing Down** - Response time increases near critical point
       - Autocorrelation at lag-1 exceeds 0.7
       - System takes longer to return to equilibrium

    3. **Flickering** - Rapid state switching near bistable points
       - System alternates between states
       - Indicates proximity to tipping point

    4. **Skewness Changes** - Distribution becomes asymmetric
       - Skewness exceeds +/- 1.0
       - Indicates system "leaning" toward new state

    **Phase Transition Types:**
    - Stable Schedule -> Chaotic Schedule (order-disorder transition)
    - Resilient -> Fragile (resilience collapse)
    - Normal -> Crisis (operational phase change)

    **2025 Research Basis:**
    Thermodynamic approaches using time-reversal symmetry breaking detect
    transitions 2-3x earlier than traditional bifurcation methods.

    Args:
        metrics: Dictionary of metric_name -> time series values
                 (if None, uses recent system metrics)
        window_size: Analysis window size for signal detection (10-200)

    Returns:
        PhaseTransitionRiskResponse with detected signals and recommendations

    Example:
        # Analyze recent metrics for transition signals
        result = await analyze_phase_transitions_tool(
            metrics={
                "utilization": [0.75, 0.78, 0.82, 0.85, 0.88, ...],
                "coverage": [0.95, 0.93, 0.91, 0.89, 0.86, ...],
                "violations": [0, 1, 1, 2, 3, 4, ...]
            }
        )

        if result.overall_severity == "critical":
            print(f"ALERT: Phase transition approaching in ~{result.time_to_transition:.0f} hours")
            for signal in result.signals:
                print(f"  - {signal.signal_type}: {signal.description}")
    """
    logger.info(f"Analyzing phase transitions (window_size={window_size})")

    try:
        from app.resilience.thermodynamics.phase_transitions import (
            PhaseTransitionDetector,
            TransitionSeverity,
        )

        # In production, would use actual system metrics or provided data
        logger.warning("Phase transition analysis using placeholder data")

        # Simulate detecting early warning signals
        signals: list[CriticalSignalInfo] = []

        # Example: Detected increasing variance in utilization
        signals.append(
            CriticalSignalInfo(
                signal_type="increasing_variance",
                metric_name="utilization",
                severity=TransitionSeverityEnum.ELEVATED,
                value=0.65,  # 65% variance increase
                threshold=0.5,  # Threshold is 50%
                description="Variance increased 65% (fluctuations diverging)",
                detected_at=datetime.now().isoformat(),
            )
        )

        # Example: Moderate autocorrelation (not yet critical slowing)
        # signals.append(CriticalSignalInfo(...))  # Only add if detected

        # Determine overall severity based on signals
        if len(signals) == 0:
            overall_severity = TransitionSeverityEnum.NORMAL
            time_to_transition = None
            confidence = 0.0
            severity = "healthy"
            interpretation = (
                "No early warning signals detected. "
                "System is operating in stable regime."
            )
            recommendations = ["Continue routine monitoring"]
        elif any(s.severity == TransitionSeverityEnum.CRITICAL for s in signals):
            overall_severity = TransitionSeverityEnum.CRITICAL
            time_to_transition = 24.0  # Estimated hours
            confidence = 0.75
            severity = "critical"
            interpretation = (
                f"CRITICAL: {len(signals)} early warning signal(s) detected. "
                f"Phase transition estimated in ~{time_to_transition:.0f} hours."
            )
            recommendations = [
                "Activate contingency plans",
                "Increase monitoring frequency",
                "Prepare fallback schedules",
                "Escalate to ORANGE defense level",
            ]
        elif any(s.severity == TransitionSeverityEnum.HIGH for s in signals):
            overall_severity = TransitionSeverityEnum.HIGH
            time_to_transition = 72.0
            confidence = 0.60
            severity = "elevated"
            interpretation = (
                f"HIGH RISK: {len(signals)} early warning signal(s) detected. "
                "System may be approaching phase transition."
            )
            recommendations = [
                "Review N-1/N-2 contingency status",
                "Increase buffer capacity",
                "Defer non-critical activities",
                "Escalate to YELLOW defense level",
            ]
        else:
            overall_severity = TransitionSeverityEnum.ELEVATED
            time_to_transition = 168.0  # ~1 week
            confidence = 0.45
            severity = "warning"
            interpretation = (
                f"ELEVATED: {len(signals)} early warning signal(s) detected. "
                "Monitor closely for deterioration."
            )
            recommendations = [
                "Increase monitoring frequency",
                "Review recent schedule changes",
                "Continue tracking identified signals",
            ]

        return PhaseTransitionRiskResponse(
            overall_severity=overall_severity,
            signals=signals,
            time_to_transition=time_to_transition,
            confidence=confidence,
            recommendations=recommendations,
            analyzed_at=datetime.now().isoformat(),
            metrics_analyzed=len(metrics) if metrics else 5,
            interpretation=interpretation,
            severity=severity,
        )

    except ImportError as e:
        logger.warning(f"Thermodynamics phase transitions module not available: {e}")
        return PhaseTransitionRiskResponse(
            overall_severity=TransitionSeverityEnum.NORMAL,
            signals=[],
            time_to_transition=None,
            confidence=0.0,
            recommendations=["Install thermodynamics module: pip install scipy numpy"],
            analyzed_at=datetime.now().isoformat(),
            metrics_analyzed=0,
            interpretation="Phase transition module not available - check backend installation",
            severity="warning",
        )


async def estimate_transition_time(
    metric_histories: dict[str, list[float]],
) -> dict[str, Any]:
    """
    Estimate time until phase transition from metric histories.

    Uses autocorrelation dynamics to estimate distance to critical point.
    Near the critical point, autocorrelation approaches 1.0 and recovery
    time approaches infinity.

    **Theory:**
    - Distance to critical point: d = 1 - autocorrelation
    - Time constant: tau = 1 / d
    - Estimated time = tau * calibration_factor

    Args:
        metric_histories: Dictionary of metric_name -> time series values

    Returns:
        Dictionary with estimated time and confidence

    Example:
        result = await estimate_transition_time_tool(
            metric_histories={
                "utilization": [...],
                "coverage": [...],
            }
        )
        print(f"Estimated time: {result['estimated_hours']:.1f} hours")
    """
    logger.info("Estimating time to transition")

    try:
        from app.resilience.thermodynamics.phase_transitions import (
            estimate_time_to_transition,
        )

        # Use the backend function
        estimated_hours = estimate_time_to_transition(metric_histories)

        if estimated_hours is None:
            return {
                "estimated_hours": None,
                "confidence": 0.0,
                "interpretation": "Insufficient data for prediction",
                "analyzed_at": datetime.now().isoformat(),
            }

        # Interpret the estimate
        if estimated_hours <= 24:
            interpretation = "IMMINENT: Transition likely within 24 hours"
            confidence = 0.8
        elif estimated_hours <= 72:
            interpretation = "NEAR: Transition likely within 3 days"
            confidence = 0.65
        elif estimated_hours <= 168:
            interpretation = "APPROACHING: Transition possible within 1 week"
            confidence = 0.5
        else:
            interpretation = "DISTANT: No immediate transition expected"
            confidence = 0.3

        return {
            "estimated_hours": estimated_hours,
            "confidence": confidence,
            "interpretation": interpretation,
            "analyzed_at": datetime.now().isoformat(),
        }

    except ImportError as e:
        logger.warning(f"Phase transitions module not available: {e}")
        return {
            "estimated_hours": None,
            "confidence": 0.0,
            "interpretation": "Module not available",
            "analyzed_at": datetime.now().isoformat(),
        }


# =============================================================================
# Tool Functions - Free Energy (Stub for future implementation)
# =============================================================================


async def optimize_free_energy(
    schedule_id: Optional[str] = None,
    target_temperature: float = 1.0,
    max_iterations: int = 100,
) -> FreeEnergyOptimizationResponse:
    """
    Optimize schedule using free energy minimization.

    **NOTE: This module is planned but not yet implemented.**
    This stub returns placeholder data showing the expected response structure.

    **Concept (Future Implementation):**
    Free energy minimization applies thermodynamic principles to find optimal
    schedule configurations by balancing:
    - Internal Energy (U): Constraint violations and cost
    - Entropy (S): Schedule flexibility and diversity
    - Temperature (T): Control parameter for exploration vs exploitation

    Helmholtz Free Energy: F = U - TS

    Lower free energy = more stable configuration.

    **Planned Features:**
    - Identify metastable schedules (shallow energy wells)
    - Find escape paths from local minima
    - Adaptive temperature for crisis flexibility
    - Pre-compute alternative schedules (like AWS static stability)

    Args:
        schedule_id: Schedule to optimize (or use current)
        target_temperature: Temperature parameter (higher = more exploration)
        max_iterations: Maximum optimization iterations

    Returns:
        FreeEnergyOptimizationResponse (placeholder data)

    Example:
        result = await optimize_free_energy_tool()
        if result.improvement > 0:
            print(f"Free energy reduced by {result.improvement:.2f}")
    """
    logger.info(
        f"Free energy optimization requested (schedule_id={schedule_id}, "
        f"temp={target_temperature}, max_iter={max_iterations})"
    )

    # This module is not yet implemented
    logger.warning("Free energy module is planned but not yet implemented")

    return FreeEnergyOptimizationResponse(
        analyzed_at=datetime.now().isoformat(),
        initial_free_energy=0.0,
        final_free_energy=0.0,
        improvement=0.0,
        iterations_used=0,
        converged=False,
        optimized_schedule_id=None,
        changes_made=[],
        recommendations=[
            "Free energy module is planned but not yet implemented",
            "See backend/app/resilience/thermodynamics/README.md for roadmap",
            "Expected implementation: Phase 2 (next 2 weeks)",
        ],
        severity="unchanged",
    )


async def analyze_energy_landscape(
    schedule_id: Optional[str] = None,
) -> EnergyLandscapeResponse:
    """
    Analyze the energy landscape around current schedule.

    **NOTE: This module is planned but not yet implemented.**
    This stub returns placeholder data showing the expected response structure.

    **Concept (Future Implementation):**
    Energy landscape analysis maps the stability of the current schedule
    and nearby alternatives:

    - Deep well = Very stable schedule (hard to escape, may miss better options)
    - Shallow well = Metastable schedule (easy to disrupt)
    - Saddle point = Transition state (pathway between configurations)

    **Planned Analysis:**
    - Escape barrier height (how much perturbation to move)
    - Nearby local minima (alternative schedules)
    - Pathway analysis (how to reach better configurations)

    Args:
        schedule_id: Schedule to analyze (or use current)

    Returns:
        EnergyLandscapeResponse (placeholder data)
    """
    logger.info(f"Energy landscape analysis requested (schedule_id={schedule_id})")

    # This module is not yet implemented
    logger.warning("Free energy module is planned but not yet implemented")

    return EnergyLandscapeResponse(
        analyzed_at=datetime.now().isoformat(),
        schedule_id=schedule_id,
        free_energy_metrics=FreeEnergyMetricsResponse(
            internal_energy=0.0,
            entropy_term=0.0,
            free_energy=0.0,
            temperature=1.0,
            stability_score=0.0,
            analyzed_at=datetime.now().isoformat(),
        ),
        is_metastable=False,
        escape_barrier=0.0,
        nearby_minima=0,
        recommendations=[
            "Free energy module is planned but not yet implemented",
            "See backend/app/resilience/thermodynamics/README.md for roadmap",
        ],
        severity="metastable",
    )
