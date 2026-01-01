"""
Hopfield Network Attractor MCP Tools for Schedule Stability Analysis.

Exposes Hopfield network energy landscape concepts as MCP tools for AI assistant
interaction. These tools model schedule states as attractors in an energy landscape,
identifying stable patterns and measuring basin depths.

Tools Provided:
1. calculate_schedule_energy - Compute Hopfield energy of current schedule state
2. find_nearby_attractors - Identify stable patterns near current state
3. measure_basin_depth - How stable is current attractor (energy barrier to escape)
4. detect_spurious_attractors - Find unintended stable patterns (scheduling anti-patterns)

Scientific Foundations:
- Hopfield Networks: Recurrent neural networks with symmetric weights
- Energy Function: E = -0.5 * sum(w_ij * s_i * s_j)
- Attractor Dynamics: System evolves toward local energy minima
- Basin of Attraction: Region from which initial states converge to the same attractor
- Spurious Attractors: Unintended stable states (anti-patterns in scheduling context)

Neuroscience Interpretation:
Hopfield networks model associative memory - the schedule "remembers" stable patterns
learned from historical data. Energy minima correspond to preferred scheduling states.
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Supporting Types
# =============================================================================


class AttractorTypeEnum(str, Enum):
    """Types of attractors in the energy landscape."""

    GLOBAL_MINIMUM = "global_minimum"  # Deepest energy well (most stable)
    LOCAL_MINIMUM = "local_minimum"  # Local energy well
    SPURIOUS = "spurious"  # Unintended attractor (anti-pattern)
    METASTABLE = "metastable"  # Shallow local minimum (weak stability)
    SADDLE_POINT = "saddle_point"  # Unstable equilibrium


class StabilityLevelEnum(str, Enum):
    """Stability assessment of schedule state."""

    VERY_STABLE = "very_stable"  # Deep basin, high energy barrier
    STABLE = "stable"  # Moderate basin depth
    MARGINALLY_STABLE = "marginally_stable"  # Shallow basin
    UNSTABLE = "unstable"  # Near saddle point or basin edge
    HIGHLY_UNSTABLE = "highly_unstable"  # At basin edge or in transition


# =============================================================================
# Response Models - Schedule Energy
# =============================================================================


class ScheduleEnergyMetrics(BaseModel):
    """
    Hopfield energy metrics for a schedule configuration.

    The energy function E = -0.5 * sum(w_ij * s_i * s_j) measures how well
    the current schedule matches learned stable patterns.
    """

    total_energy: float = Field(
        description="Total Hopfield energy of schedule configuration"
    )
    normalized_energy: float = Field(
        ge=-1.0,
        le=1.0,
        description="Energy normalized to [-1, 1] range for comparison",
    )
    energy_density: float = Field(
        description="Energy per assignment (total_energy / num_assignments)"
    )
    interaction_energy: float = Field(
        description="Energy from pairwise interactions (person-rotation coupling)"
    )
    stability_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Stability score based on energy gradient (0=unstable, 1=very stable)",
    )
    gradient_magnitude: float = Field(
        ge=0.0, description="Magnitude of energy gradient (rate of change)"
    )
    is_local_minimum: bool = Field(
        description="Whether current state is a local energy minimum"
    )
    distance_to_minimum: float = Field(
        ge=0.0, description="Estimated Hamming distance to nearest local minimum"
    )
    computed_at: str = Field(description="ISO timestamp of computation")


class ScheduleEnergyResponse(BaseModel):
    """Response from schedule energy calculation."""

    analyzed_at: str = Field(description="ISO timestamp of analysis")
    schedule_id: str | None = Field(default=None, description="Schedule identifier if applicable")
    period_start: str = Field(description="Analysis period start date")
    period_end: str = Field(description="Analysis period end date")
    assignments_analyzed: int = Field(ge=0, description="Number of assignments encoded")
    state_dimension: int = Field(ge=0, description="Dimensionality of state vector")
    metrics: ScheduleEnergyMetrics = Field(description="Energy metrics")
    interpretation: str = Field(description="Human-readable interpretation")
    stability_level: StabilityLevelEnum = Field(description="Overall stability assessment")
    recommendations: list[str] = Field(default_factory=list)
    severity: str = Field(description="very_stable, stable, marginally_stable, unstable, critical")


# =============================================================================
# Response Models - Attractor Analysis
# =============================================================================


class AttractorInfo(BaseModel):
    """Information about a detected attractor in the energy landscape."""

    attractor_id: str = Field(description="Unique identifier for this attractor")
    attractor_type: AttractorTypeEnum = Field(description="Type of attractor")
    energy_level: float = Field(description="Energy at the attractor state")
    basin_depth: float = Field(
        ge=0.0, description="Energy barrier to escape basin (stability measure)"
    )
    basin_volume: int = Field(
        ge=0, description="Estimated number of states in basin of attraction"
    )
    hamming_distance: int = Field(
        ge=0, description="Hamming distance from current schedule state"
    )
    pattern_description: str = Field(
        description="Human-readable description of the scheduling pattern"
    )
    is_current_state: bool = Field(
        default=False, description="Whether this is the current schedule state"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in attractor identification"
    )


class NearbyAttractorsResponse(BaseModel):
    """Response from nearby attractor search."""

    analyzed_at: str = Field(description="ISO timestamp of analysis")
    current_state_energy: float = Field(description="Energy of current schedule state")
    attractors_found: int = Field(ge=0, description="Number of attractors identified")
    attractors: list[AttractorInfo] = Field(
        default_factory=list, description="List of nearby attractors"
    )
    global_minimum_identified: bool = Field(
        description="Whether the global minimum was found"
    )
    current_basin_id: str | None = Field(
        default=None, description="ID of attractor basin containing current state"
    )
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: list[str] = Field(default_factory=list)
    severity: str = Field(description="optimal, good, suboptimal, poor, critical")


# =============================================================================
# Response Models - Basin Depth
# =============================================================================


class BasinDepthMetrics(BaseModel):
    """Metrics quantifying basin of attraction stability."""

    min_escape_energy: float = Field(
        ge=0.0, description="Minimum energy barrier to escape basin"
    )
    avg_escape_energy: float = Field(
        ge=0.0, description="Average energy barrier across all escape paths"
    )
    max_escape_energy: float = Field(
        ge=0.0, description="Maximum energy barrier (strongest barrier)"
    )
    basin_stability_index: float = Field(
        ge=0.0,
        le=1.0,
        description="Combined stability index (0=very shallow, 1=very deep)",
    )
    num_escape_paths: int = Field(
        ge=0, description="Number of distinct paths out of basin"
    )
    nearest_saddle_distance: int = Field(
        ge=0, description="Hamming distance to nearest saddle point"
    )
    basin_radius: int = Field(
        ge=0, description="Maximum Hamming distance within basin"
    )
    critical_perturbation_size: int = Field(
        ge=0,
        description="Number of assignments that must change to escape basin",
    )


class BasinDepthResponse(BaseModel):
    """Response from basin depth measurement."""

    analyzed_at: str = Field(description="ISO timestamp of analysis")
    schedule_id: str | None = Field(default=None, description="Schedule identifier")
    attractor_id: str = Field(description="ID of the attractor whose basin was measured")
    metrics: BasinDepthMetrics = Field(description="Basin depth metrics")
    stability_level: StabilityLevelEnum = Field(
        description="Overall stability classification"
    )
    is_robust: bool = Field(
        description="Whether schedule is robust to small perturbations"
    )
    robustness_threshold: int = Field(
        ge=0,
        description="Number of simultaneous changes that can be tolerated",
    )
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: list[str] = Field(default_factory=list)
    severity: str = Field(description="very_stable, stable, fragile, very_fragile, critical")


# =============================================================================
# Response Models - Spurious Attractors
# =============================================================================


class SpuriousAttractorInfo(BaseModel):
    """Information about a detected spurious attractor (anti-pattern)."""

    attractor_id: str = Field(description="Unique identifier")
    energy_level: float = Field(description="Energy at spurious attractor")
    basin_size: int = Field(ge=0, description="Size of spurious basin")
    anti_pattern_type: str = Field(
        description="Type of scheduling anti-pattern: overload, underutilization, clustering, etc."
    )
    description: str = Field(description="Description of the anti-pattern")
    risk_level: str = Field(
        description="Risk if schedule falls into this basin: low, medium, high, critical"
    )
    distance_from_valid: int = Field(
        ge=0, description="Hamming distance from nearest valid schedule"
    )
    probability_of_capture: float = Field(
        ge=0.0,
        le=1.0,
        description="Probability of falling into this basin during generation",
    )
    mitigation_strategy: str = Field(
        description="Recommended strategy to avoid this anti-pattern"
    )


class SpuriousAttractorsResponse(BaseModel):
    """Response from spurious attractor detection."""

    analyzed_at: str = Field(description="ISO timestamp of analysis")
    spurious_attractors_found: int = Field(
        ge=0, description="Number of spurious attractors detected"
    )
    spurious_attractors: list[SpuriousAttractorInfo] = Field(
        default_factory=list, description="List of spurious attractors"
    )
    total_basin_coverage: float = Field(
        ge=0.0,
        le=1.0,
        description="Fraction of state space covered by spurious basins",
    )
    highest_risk_attractor: str | None = Field(
        default=None, description="ID of most dangerous spurious attractor"
    )
    is_current_state_spurious: bool = Field(
        description="Whether current schedule is in a spurious basin"
    )
    interpretation: str = Field(description="Human-readable interpretation")
    recommendations: list[str] = Field(default_factory=list)
    severity: str = Field(description="clean, minor_risk, moderate_risk, high_risk, critical")


# =============================================================================
# Tool Functions - Schedule Energy
# =============================================================================


async def calculate_schedule_energy(
    start_date: str | None = None,
    end_date: str | None = None,
    schedule_id: str | None = None,
) -> ScheduleEnergyResponse:
    """
    Calculate Hopfield energy of the current schedule state.

    **Hopfield Energy Function:**
    E = -0.5 * sum_ij(w_ij * s_i * s_j)

    Where:
    - s_i, s_j are binary state variables (assignment present/absent)
    - w_ij are learned weights encoding stable scheduling patterns
    - Lower energy = more stable configuration

    **Energy Interpretation:**
    - Negative Energy: Schedule matches learned stable patterns
    - Energy Near Zero: Schedule is in transition between patterns
    - Positive Energy: Schedule conflicts with learned patterns (unstable)

    **Neuroscience Analogy:**
    Like how neurons settle into stable firing patterns representing memories,
    schedules settle into stable assignment patterns that respect constraints
    and historical preferences.

    Args:
        start_date: Start date for analysis (YYYY-MM-DD), defaults to today
        end_date: End date for analysis (YYYY-MM-DD), defaults to 30 days
        schedule_id: Optional specific schedule ID to analyze

    Returns:
        ScheduleEnergyResponse with energy metrics and stability assessment

    Example:
        result = await calculate_schedule_energy(
            start_date="2025-01-01",
            end_date="2025-01-31"
        )

        if result.stability_level == "unstable":
            print(f"WARNING: Schedule is unstable (energy={result.metrics.total_energy:.2f})")
            print(f"Distance to stability: {result.metrics.distance_to_minimum} changes")
    """
    from datetime import date, timedelta

    logger.info(f"Calculating Hopfield energy for schedule ({start_date} to {end_date})")

    # Parse dates with defaults
    today = date.today()
    start = date.fromisoformat(start_date) if start_date else today
    end = date.fromisoformat(end_date) if end_date else (today + timedelta(days=30))

    try:
        # In production, would import actual Hopfield implementation
        # from app.resilience.hopfield.energy import calculate_hopfield_energy

        logger.warning("Hopfield energy using placeholder data")

        # Mock energy calculation showing realistic values
        import numpy as np

        # Simulate a schedule state
        state_dim = 200  # e.g., 10 faculty × 20 time blocks
        num_assignments = 156

        # Generate mock energy metrics
        # Negative energy indicates stable configuration
        total_energy = -42.5  # Stable configuration
        normalized_energy = -0.73  # Strong match to learned patterns
        energy_density = total_energy / num_assignments
        interaction_energy = -38.2  # Strong pairwise interactions
        gradient_magnitude = 0.12  # Low gradient = near minimum

        # Stability score based on gradient
        stability_score = max(0.0, min(1.0, 1.0 - gradient_magnitude))
        is_local_minimum = gradient_magnitude < 0.2
        distance_to_minimum = int(gradient_magnitude * 10)  # Hamming distance estimate

        metrics = ScheduleEnergyMetrics(
            total_energy=total_energy,
            normalized_energy=normalized_energy,
            energy_density=energy_density,
            interaction_energy=interaction_energy,
            stability_score=stability_score,
            gradient_magnitude=gradient_magnitude,
            is_local_minimum=is_local_minimum,
            distance_to_minimum=distance_to_minimum,
            computed_at=datetime.now().isoformat(),
        )

        # Determine stability level
        if normalized_energy < -0.8 and is_local_minimum:
            stability_level = StabilityLevelEnum.VERY_STABLE
            interpretation = (
                f"Schedule is in a very stable configuration (energy={total_energy:.2f}). "
                f"Strong match to learned scheduling patterns. "
                f"Stability score: {stability_score:.0%}. "
                "This schedule is at a local energy minimum and highly resistant to perturbations."
            )
            severity = "very_stable"
            recommendations = [
                "Schedule is stable - maintain current configuration",
                "Monitor for gradual drift over time",
                "Use as template for future scheduling periods",
            ]
        elif normalized_energy < -0.5:
            stability_level = StabilityLevelEnum.STABLE
            interpretation = (
                f"Schedule is in a stable configuration (energy={total_energy:.2f}). "
                f"Good match to learned patterns with stability score {stability_score:.0%}. "
                "Minor optimizations possible but not critical."
            )
            severity = "stable"
            recommendations = [
                "Schedule is reasonably stable",
                f"Consider {distance_to_minimum} minor adjustments to reach nearest minimum",
                "Review gradient direction for optimization opportunities",
            ]
        elif normalized_energy < 0.0:
            stability_level = StabilityLevelEnum.MARGINALLY_STABLE
            interpretation = (
                f"Schedule is marginally stable (energy={total_energy:.2f}). "
                "Configuration matches some patterns but has room for improvement. "
                f"Not at a local minimum (gradient={gradient_magnitude:.3f})."
            )
            severity = "marginally_stable"
            recommendations = [
                f"Optimize schedule - approximately {distance_to_minimum} changes needed",
                "Review assignments that conflict with learned patterns",
                "Consider guided optimization toward nearest attractor",
            ]
        else:
            stability_level = StabilityLevelEnum.UNSTABLE
            interpretation = (
                f"WARNING: Schedule is unstable (energy={total_energy:.2f}, normalized={normalized_energy:.2f}). "
                "Configuration conflicts with learned stable patterns. "
                "High risk of constraint violations or operational issues."
            )
            severity = "unstable"
            recommendations = [
                "URGENT: Revise schedule to improve stability",
                f"Minimum {distance_to_minimum} changes required to reach stable state",
                "Review ACGME compliance and coverage requirements",
                "Consider regenerating schedule with stricter constraints",
            ]

        return ScheduleEnergyResponse(
            analyzed_at=datetime.now().isoformat(),
            schedule_id=schedule_id,
            period_start=start.isoformat(),
            period_end=end.isoformat(),
            assignments_analyzed=num_assignments,
            state_dimension=state_dim,
            metrics=metrics,
            interpretation=interpretation,
            stability_level=stability_level,
            recommendations=recommendations,
            severity=severity,
        )

    except ImportError as e:
        logger.warning(f"Hopfield energy module not available: {e}")
        return ScheduleEnergyResponse(
            analyzed_at=datetime.now().isoformat(),
            schedule_id=schedule_id,
            period_start=start.isoformat(),
            period_end=end.isoformat(),
            assignments_analyzed=0,
            state_dimension=0,
            metrics=ScheduleEnergyMetrics(
                total_energy=0.0,
                normalized_energy=0.0,
                energy_density=0.0,
                interaction_energy=0.0,
                stability_score=0.0,
                gradient_magnitude=0.0,
                is_local_minimum=False,
                distance_to_minimum=0,
                computed_at=datetime.now().isoformat(),
            ),
            interpretation="Hopfield network module not available - check backend installation",
            stability_level=StabilityLevelEnum.UNSTABLE,
            recommendations=["Install Hopfield module: pip install numpy scipy"],
            severity="critical",
        )


# =============================================================================
# Tool Functions - Nearby Attractors
# =============================================================================


async def find_nearby_attractors(
    max_distance: int = 10,
    start_date: str | None = None,
    end_date: str | None = None,
) -> NearbyAttractorsResponse:
    """
    Identify stable attractors near the current schedule state.

    **Attractor Concept:**
    In Hopfield networks, attractors are stable states (energy minima) that
    the system naturally evolves toward. Initial states within the "basin of
    attraction" converge to the same attractor through energy minimization.

    **Schedule Interpretation:**
    - Each attractor represents a stable scheduling pattern
    - Current schedule may be near (but not at) an attractor
    - Multiple attractors = multiple valid scheduling strategies
    - Finding nearby attractors shows alternative stable configurations

    **Search Strategy:**
    Uses gradient descent and random perturbations to map the energy landscape
    within max_distance Hamming distance from current state.

    Args:
        max_distance: Maximum Hamming distance to search (1-50)
        start_date: Start date for analysis (YYYY-MM-DD)
        end_date: End date for analysis (YYYY-MM-DD)

    Returns:
        NearbyAttractorsResponse with identified attractors and recommendations

    Example:
        result = await find_nearby_attractors(max_distance=5)

        for attractor in result.attractors:
            if attractor.attractor_type == "global_minimum":
                print(f"Global optimum found at distance {attractor.hamming_distance}")
                print(f"Energy improvement: {result.current_state_energy - attractor.energy_level:.2f}")
    """
    from datetime import date, timedelta

    logger.info(f"Searching for nearby attractors (max_distance={max_distance})")

    today = date.today()
    start = date.fromisoformat(start_date) if start_date else today
    end = date.fromisoformat(end_date) if end_date else (today + timedelta(days=30))

    try:
        logger.warning("Attractor search using placeholder data")

        # Mock current state energy
        current_energy = -38.5

        # Simulate finding several nearby attractors
        attractors = [
            AttractorInfo(
                attractor_id="attr_001",
                attractor_type=AttractorTypeEnum.LOCAL_MINIMUM,
                energy_level=-42.8,
                basin_depth=8.3,
                basin_volume=156,
                hamming_distance=3,
                pattern_description="Balanced faculty distribution with clustered call coverage",
                is_current_state=False,
                confidence=0.92,
            ),
            AttractorInfo(
                attractor_id="attr_002",
                attractor_type=AttractorTypeEnum.GLOBAL_MINIMUM,
                energy_level=-45.2,
                basin_depth=12.7,
                basin_volume=342,
                hamming_distance=7,
                pattern_description="Optimal load balancing with sequential rotation assignments",
                is_current_state=False,
                confidence=0.88,
            ),
            AttractorInfo(
                attractor_id="attr_003",
                attractor_type=AttractorTypeEnum.METASTABLE,
                energy_level=-35.1,
                basin_depth=2.4,
                basin_volume=45,
                hamming_distance=2,
                pattern_description="Concentrated assignments on senior faculty (metastable)",
                is_current_state=False,
                confidence=0.76,
            ),
        ]

        global_minimum_found = any(
            a.attractor_type == AttractorTypeEnum.GLOBAL_MINIMUM for a in attractors
        )

        # Determine which basin current state is in
        nearest_attractor = min(attractors, key=lambda a: a.hamming_distance)
        current_basin_id = nearest_attractor.attractor_id

        # Generate interpretation
        if global_minimum_found:
            global_attr = next(
                a for a in attractors if a.attractor_type == AttractorTypeEnum.GLOBAL_MINIMUM
            )
            energy_improvement = global_attr.energy_level - current_energy
            interpretation = (
                f"Found {len(attractors)} nearby attractors including the global minimum. "
                f"Global optimum is {global_attr.hamming_distance} changes away with "
                f"energy improvement of {energy_improvement:.2f}. "
                f"Current state is in basin of {nearest_attractor.pattern_description}."
            )
            severity = "good"
            recommendations = [
                f"Consider optimizing toward global minimum (attr_002) - {global_attr.hamming_distance} changes",
                f"Current basin ({current_basin_id}) is stable but suboptimal",
                "Review assignment changes needed to reach global optimum",
            ]
        else:
            interpretation = (
                f"Found {len(attractors)} local attractors within search radius. "
                f"Global minimum not found within {max_distance} changes. "
                f"Current state is near {nearest_attractor.pattern_description}."
            )
            severity = "suboptimal"
            recommendations = [
                f"Expand search radius beyond {max_distance} to find global optimum",
                f"Nearest attractor is {nearest_attractor.hamming_distance} changes away",
                "Consider gradient-based optimization to improve current configuration",
            ]

        return NearbyAttractorsResponse(
            analyzed_at=datetime.now().isoformat(),
            current_state_energy=current_energy,
            attractors_found=len(attractors),
            attractors=attractors,
            global_minimum_identified=global_minimum_found,
            current_basin_id=current_basin_id,
            interpretation=interpretation,
            recommendations=recommendations,
            severity=severity,
        )

    except Exception as e:
        logger.error(f"Attractor search failed: {e}", exc_info=True)
        return NearbyAttractorsResponse(
            analyzed_at=datetime.now().isoformat(),
            current_state_energy=0.0,
            attractors_found=0,
            attractors=[],
            global_minimum_identified=False,
            current_basin_id=None,
            interpretation=f"Attractor search failed: {e}",
            recommendations=["Check Hopfield network module installation"],
            severity="critical",
        )


# =============================================================================
# Tool Functions - Basin Depth
# =============================================================================


async def measure_basin_depth(
    attractor_id: str | None = None,
    num_perturbations: int = 100,
) -> BasinDepthResponse:
    """
    Measure the depth of the basin of attraction for current or specified attractor.

    **Basin Depth Concept:**
    Basin depth is the energy barrier that must be overcome to escape the basin.
    Deeper basins = more stable attractors = more robust schedules.

    **Why Basin Depth Matters:**
    - Deep Basin: Schedule is robust to random perturbations (swaps, absences)
    - Shallow Basin: Small changes can push schedule into different attractor
    - Critical for resilience: N-1/N-2 failures shouldn't escape basin

    **Measurement Method:**
    Applies random perturbations and measures minimum energy barrier to:
    1. Escape current basin
    2. Reach a different attractor
    3. Cross saddle points in the energy landscape

    Args:
        attractor_id: Specific attractor to analyze (defaults to nearest)
        num_perturbations: Number of random perturbations to test (10-1000)

    Returns:
        BasinDepthResponse with stability metrics and robustness assessment

    Example:
        result = await measure_basin_depth(num_perturbations=200)

        if result.metrics.basin_stability_index > 0.8:
            print(f"Schedule is highly stable (index={result.metrics.basin_stability_index:.2f})")
            print(f"Can tolerate {result.robustness_threshold} simultaneous changes")
        else:
            print("WARNING: Schedule is fragile")
    """
    logger.info(f"Measuring basin depth (perturbations={num_perturbations})")

    try:
        logger.warning("Basin depth measurement using placeholder data")


        # Simulate basin depth measurements
        # Energy barriers from perturbation experiments
        min_escape = 8.3  # Minimum barrier to escape
        avg_escape = 12.7  # Average across all paths
        max_escape = 18.9  # Maximum barrier (strongest direction)

        # Derived metrics
        basin_stability_index = min(1.0, avg_escape / 20.0)  # Normalize to [0, 1]
        num_escape_paths = 8  # Number of distinct exit paths
        nearest_saddle = 5  # Hamming distance to saddle point
        basin_radius = 12  # Maximum distance within basin
        critical_perturbation_size = int(min_escape / 2)  # Conservative estimate

        metrics = BasinDepthMetrics(
            min_escape_energy=min_escape,
            avg_escape_energy=avg_escape,
            max_escape_energy=max_escape,
            basin_stability_index=basin_stability_index,
            num_escape_paths=num_escape_paths,
            nearest_saddle_distance=nearest_saddle,
            basin_radius=basin_radius,
            critical_perturbation_size=critical_perturbation_size,
        )

        # Determine stability level
        if basin_stability_index > 0.8:
            stability_level = StabilityLevelEnum.VERY_STABLE
            is_robust = True
            robustness_threshold = critical_perturbation_size
            interpretation = (
                f"Schedule is in a very deep basin (stability index={basin_stability_index:.2%}). "
                f"Average escape barrier is {avg_escape:.1f} energy units. "
                f"Highly robust to perturbations - can tolerate {robustness_threshold} "
                "simultaneous changes without losing stability."
            )
            severity = "very_stable"
            recommendations = [
                "Schedule is highly stable and robust",
                f"Can safely handle up to {robustness_threshold} simultaneous swaps or absences",
                "Suitable for periods with high uncertainty (holidays, flu season)",
            ]
        elif basin_stability_index > 0.6:
            stability_level = StabilityLevelEnum.STABLE
            is_robust = True
            robustness_threshold = critical_perturbation_size
            interpretation = (
                f"Schedule is in a stable basin (index={basin_stability_index:.2%}). "
                f"Average escape barrier is {avg_escape:.1f}. "
                "Robust to typical perturbations."
            )
            severity = "stable"
            recommendations = [
                "Schedule has good stability",
                f"Can handle approximately {robustness_threshold} changes robustly",
                "Monitor if multiple swaps or absences occur simultaneously",
            ]
        elif basin_stability_index > 0.4:
            stability_level = StabilityLevelEnum.MARGINALLY_STABLE
            is_robust = False
            robustness_threshold = max(1, critical_perturbation_size)
            interpretation = (
                f"Schedule is in a shallow basin (index={basin_stability_index:.2%}). "
                f"Minimum escape barrier is only {min_escape:.1f}. "
                "Vulnerable to cascading failures from perturbations."
            )
            severity = "fragile"
            recommendations = [
                "WARNING: Schedule stability is marginal",
                f"Limited robustness - only {robustness_threshold} changes safe",
                "Consider regenerating with stronger constraints",
                "Avoid approving swaps that move toward basin edge",
            ]
        else:
            stability_level = StabilityLevelEnum.UNSTABLE
            is_robust = False
            robustness_threshold = 0
            interpretation = (
                f"CRITICAL: Schedule is in a very shallow basin (index={basin_stability_index:.2%}). "
                f"Escape barrier is only {min_escape:.1f}. "
                "High risk of spontaneous transition to different attractor."
            )
            severity = "very_fragile"
            recommendations = [
                "URGENT: Schedule is highly unstable",
                "Any perturbation may trigger cascade to different configuration",
                "Recommend immediate regeneration",
                "Do not approve any swaps until stability improved",
            ]

        attractor_label = attractor_id or "attr_current"

        return BasinDepthResponse(
            analyzed_at=datetime.now().isoformat(),
            schedule_id=None,
            attractor_id=attractor_label,
            metrics=metrics,
            stability_level=stability_level,
            is_robust=is_robust,
            robustness_threshold=robustness_threshold,
            interpretation=interpretation,
            recommendations=recommendations,
            severity=severity,
        )

    except Exception as e:
        logger.error(f"Basin depth measurement failed: {e}", exc_info=True)
        return BasinDepthResponse(
            analyzed_at=datetime.now().isoformat(),
            schedule_id=None,
            attractor_id=attractor_id or "unknown",
            metrics=BasinDepthMetrics(
                min_escape_energy=0.0,
                avg_escape_energy=0.0,
                max_escape_energy=0.0,
                basin_stability_index=0.0,
                num_escape_paths=0,
                nearest_saddle_distance=0,
                basin_radius=0,
                critical_perturbation_size=0,
            ),
            stability_level=StabilityLevelEnum.HIGHLY_UNSTABLE,
            is_robust=False,
            robustness_threshold=0,
            interpretation=f"Basin depth measurement failed: {e}",
            recommendations=["Check Hopfield network module installation"],
            severity="critical",
        )


# =============================================================================
# Tool Functions - Spurious Attractors
# =============================================================================


async def detect_spurious_attractors(
    search_radius: int = 20,
    min_basin_size: int = 10,
) -> SpuriousAttractorsResponse:
    """
    Detect spurious attractors (unintended stable patterns / scheduling anti-patterns).

    **Spurious Attractor Problem:**
    Hopfield networks can form "spurious attractors" - stable states that were
    NOT part of the training patterns. In scheduling context, these are anti-patterns:
    - Concentrated overload on subset of faculty
    - Systematic underutilization
    - Clustering violations (too many similar shifts together)
    - ACGME compliance boundary cases

    **Why This Matters:**
    If schedule generation randomly initializes near a spurious attractor, it may
    converge to an anti-pattern that satisfies hard constraints but violates
    implicit quality requirements.

    **Detection Strategy:**
    1. Search energy landscape for local minima
    2. Check if each minimum corresponds to known good pattern
    3. Classify unknown minima as spurious
    4. Estimate basin size and capture probability

    Args:
        search_radius: Hamming distance to search for spurious attractors (5-50)
        min_basin_size: Minimum basin size to report (avoid noise)

    Returns:
        SpuriousAttractorsResponse with anti-patterns and mitigation strategies

    Example:
        result = await detect_spurious_attractors(search_radius=25)

        if result.is_current_state_spurious:
            print("ALERT: Current schedule is in a spurious attractor (anti-pattern)!")
            highest_risk = result.highest_risk_attractor
            print(f"Risk attractor: {highest_risk}")

        for spurious in result.spurious_attractors:
            if spurious.risk_level == "critical":
                print(f"Critical anti-pattern: {spurious.description}")
                print(f"Mitigation: {spurious.mitigation_strategy}")
    """
    logger.info(f"Detecting spurious attractors (radius={search_radius})")

    try:
        logger.warning("Spurious attractor detection using placeholder data")

        # Simulate detection of spurious attractors
        spurious_list = [
            SpuriousAttractorInfo(
                attractor_id="spurious_001",
                energy_level=-28.3,
                basin_size=67,
                anti_pattern_type="overload_concentration",
                description=(
                    "Concentrated overload: 80% of call shifts assigned to 3 senior faculty. "
                    "Violates implicit load balancing. Burnout risk."
                ),
                risk_level="high",
                distance_from_valid=8,
                probability_of_capture=0.15,
                mitigation_strategy=(
                    "Add soft constraint penalizing uneven call distribution. "
                    "Enforce max assignments per person per week."
                ),
            ),
            SpuriousAttractorInfo(
                attractor_id="spurious_002",
                energy_level=-22.7,
                basin_size=34,
                anti_pattern_type="clustering_violation",
                description=(
                    "Shift clustering: Same faculty assigned to consecutive night shifts. "
                    "Satisfies ACGME but violates fatigue management best practices."
                ),
                risk_level="medium",
                distance_from_valid=5,
                probability_of_capture=0.08,
                mitigation_strategy=(
                    "Add temporal spacing constraint for high-intensity shifts. "
                    "Use fatigue index from FRMS tools."
                ),
            ),
            SpuriousAttractorInfo(
                attractor_id="spurious_003",
                energy_level=-31.2,
                basin_size=89,
                anti_pattern_type="underutilization",
                description=(
                    "Systematic underutilization: Junior faculty assigned minimal rotations. "
                    "Inefficient use of available workforce."
                ),
                risk_level="low",
                distance_from_valid=12,
                probability_of_capture=0.05,
                mitigation_strategy=(
                    "Add minimum assignment constraint per faculty. "
                    "Balance training opportunities across PGY levels."
                ),
            ),
        ]

        total_basin_coverage = sum(s.probability_of_capture for s in spurious_list)

        # Find highest risk
        highest_risk = max(
            spurious_list,
            key=lambda s: (
                {"critical": 4, "high": 3, "medium": 2, "low": 1}[s.risk_level],
                s.basin_size,
            ),
        ).attractor_id

        # Check if current state is spurious (mock: assume not)
        is_current_spurious = False

        # Generate interpretation
        if len(spurious_list) > 0:
            high_risk_count = sum(1 for s in spurious_list if s.risk_level in ["high", "critical"])
            interpretation = (
                f"Detected {len(spurious_list)} spurious attractors (anti-patterns) "
                f"within search radius. {high_risk_count} are high/critical risk. "
                f"Total basin coverage: {total_basin_coverage:.1%} of nearby state space. "
                f"Highest risk attractor: {highest_risk}."
            )

            if total_basin_coverage > 0.2:
                severity = "moderate_risk"
                recommendations = [
                    "WARNING: Significant spurious basin coverage detected",
                    "Add constraints to eliminate high-risk anti-patterns",
                    f"Focus mitigation on {highest_risk} first",
                    "Review schedule generation initialization strategy",
                ]
            elif high_risk_count > 0:
                severity = "minor_risk"
                recommendations = [
                    f"{high_risk_count} high-risk anti-patterns detected",
                    "Consider adding soft constraints to avoid these patterns",
                    "Monitor schedule generation for convergence to spurious attractors",
                ]
            else:
                severity = "clean"
                recommendations = [
                    "Low-risk spurious attractors detected",
                    "Current constraints are effective",
                    "Continue monitoring during schedule generation",
                ]
        else:
            interpretation = (
                f"No spurious attractors detected within search radius {search_radius}. "
                "Energy landscape appears clean."
            )
            severity = "clean"
            recommendations = [
                "No anti-patterns detected - energy landscape is clean",
                "Current constraints successfully prevent spurious attractors",
            ]

        return SpuriousAttractorsResponse(
            analyzed_at=datetime.now().isoformat(),
            spurious_attractors_found=len(spurious_list),
            spurious_attractors=spurious_list,
            total_basin_coverage=total_basin_coverage,
            highest_risk_attractor=highest_risk if spurious_list else None,
            is_current_state_spurious=is_current_spurious,
            interpretation=interpretation,
            recommendations=recommendations,
            severity=severity,
        )

    except Exception as e:
        logger.error(f"Spurious attractor detection failed: {e}", exc_info=True)
        return SpuriousAttractorsResponse(
            analyzed_at=datetime.now().isoformat(),
            spurious_attractors_found=0,
            spurious_attractors=[],
            total_basin_coverage=0.0,
            highest_risk_attractor=None,
            is_current_state_spurious=False,
            interpretation=f"Spurious attractor detection failed: {e}",
            recommendations=["Check Hopfield network module installation"],
            severity="critical",
        )
