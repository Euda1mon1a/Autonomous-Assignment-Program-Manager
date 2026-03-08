"""
Propulsion Zone Detection for Schedule Optimization.

Identifies schedule regions where intervention has maximum positive effect,
based on the negative viscosity concept from active matter physics.

Key Concepts:
    - Propulsion Zone: Region where constraints cooperate and energy injection
      yields compounding benefits (negative viscosity behavior)
    - Friction Zone: Region where constraints conflict, causing optimization
      to oscillate (positive viscosity / energy dissipation)
    - Intervention Potential: Combined metric of constraint alignment and
      energy flow direction indicating optimization opportunity

Theory:
    In active matter physics, negative viscosity occurs when particles extract
    energy from their environment to move, rather than dissipating energy as
    friction. Similarly, in scheduling optimization:

    - When constraints align (synergy), the solver converges faster and
      changes propagate positively (propulsion)
    - When constraints conflict, optimization effort is wasted fighting
      competing objectives (friction)

    Detecting propulsion zones tells the optimizer WHERE to focus effort
    for maximum return on investment.

References:
    - PR #803: Negative Viscosity Research
    - docs/research/EXOTIC_CONCEPTS_UNIFIED.md (Concept #17)
    - Solon et al. (2015): Active matter viscosity transitions

Usage:
    >>> from app.resilience.propulsion_zones import detect_propulsion_zones
    >>> zones = detect_propulsion_zones(schedule, context)
    >>> for zone in zones:
    ...     if zone.is_propulsion_zone:
    ...         print(f"Block {zone.block_range}: High opportunity!")
"""

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.scheduling.constraint_validator import ConstraintAlignmentMatrix  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)


@dataclass
class PropulsionZone:
    """
    A schedule region characterized by its optimization potential.

    Attributes:
        block_range: Start and end dates of the zone
        constraint_alignment: Score from constraint validator (-1 to +1)
        energy_flow: Rate of entropy change (negative = injection)
        intervention_potential: Combined score (0 to 1)
        is_propulsion_zone: True if net positive intervention opportunity
        is_friction_zone: True if optimization effort would be wasted
        details: Additional metrics and diagnostics
    """

    block_range: tuple[date, date]
    constraint_alignment: float  # -1 to +1 (from ConstraintAlignmentMatrix)
    energy_flow: float  # From entropy.calculate_energy_flow_direction
    intervention_potential: float  # 0 to 1 (combined score)

    is_propulsion_zone: bool = False
    is_friction_zone: bool = False

    details: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Classify zone based on metrics."""
        # Propulsion: positive alignment AND negative energy flow (injection)
        self.is_propulsion_zone = (
            self.constraint_alignment > 0.2 and self.energy_flow < 0
        )

        # Friction: negative alignment OR high positive energy flow (dissipation)
        self.is_friction_zone = (
            self.constraint_alignment < -0.2 or self.energy_flow > 0.5
        )


@dataclass
class PropulsionAnalysis:
    """
    Complete propulsion zone analysis for a schedule.

    Aggregates zone-by-zone analysis with overall metrics.
    """

    zones: list[PropulsionZone] = field(default_factory=list)
    overall_propulsion_potential: float = 0.0
    propulsion_zone_count: int = 0
    friction_zone_count: int = 0
    neutral_zone_count: int = 0
    recommendation: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "overall_propulsion_potential": self.overall_propulsion_potential,
            "propulsion_zone_count": self.propulsion_zone_count,
            "friction_zone_count": self.friction_zone_count,
            "neutral_zone_count": self.neutral_zone_count,
            "recommendation": self.recommendation,
            "zones": [
                {
                    "block_range": (
                        z.block_range[0].isoformat(),
                        z.block_range[1].isoformat(),
                    ),
                    "constraint_alignment": z.constraint_alignment,
                    "energy_flow": z.energy_flow,
                    "intervention_potential": z.intervention_potential,
                    "is_propulsion_zone": z.is_propulsion_zone,
                    "is_friction_zone": z.is_friction_zone,
                }
                for z in self.zones
            ],
        }


def calculate_intervention_potential(
    constraint_alignment: float,
    energy_flow: float,
) -> float:
    """
    Calculate combined intervention potential score.

    Combines constraint alignment (are constraints cooperating?) with
    energy flow direction (is the system gaining or losing organization?)
    to produce a single 0-1 score indicating optimization opportunity.

    Args:
        constraint_alignment: Score from -1 (conflict) to +1 (synergy)
        energy_flow: Rate from entropy change (negative = injection/improvement)

    Returns:
        Intervention potential from 0 (avoid) to 1 (high opportunity)

    Formula:
        potential = (alignment_factor + energy_factor) / 2

        Where:
        - alignment_factor = (alignment + 1) / 2  [maps -1..+1 to 0..1]
        - energy_factor = sigmoid(-energy_flow)   [negative flow = high potential]
    """
    import math

    # Normalize alignment from [-1, +1] to [0, 1]
    alignment_factor = (constraint_alignment + 1) / 2

    # Sigmoid of negative energy flow
    # Negative energy flow (injection) -> high potential
    # Positive energy flow (dissipation) -> low potential
    energy_factor = 1 / (1 + math.exp(energy_flow * 2))

    # Combined score with alignment weighted slightly higher
    # (alignment is more predictable than energy flow)
    potential = 0.6 * alignment_factor + 0.4 * energy_factor

    return min(1.0, max(0.0, potential))


def detect_propulsion_zones(
    schedule: Any,
    context: Any,
    alignment_matrix: "ConstraintAlignmentMatrix | None" = None,
    energy_history: list[float] | None = None,
) -> PropulsionAnalysis:
    """
    Detect propulsion and friction zones in a schedule.

    Analyzes the schedule to identify blocks where optimization effort
    would yield maximum benefit (propulsion) vs where it would be wasted
    fighting competing constraints (friction).

    Args:
        schedule: Schedule object with assignments
        context: SchedulingContext with domain data
        alignment_matrix: Pre-computed constraint alignment (optional)
        energy_history: Pre-computed energy flow history (optional)

    Returns:
        PropulsionAnalysis with zone-by-zone breakdown and recommendations

    Usage:
        >>> analysis = detect_propulsion_zones(schedule, context)
        >>> print(f"Found {analysis.propulsion_zone_count} high-opportunity zones")
        >>> for zone in analysis.zones:
        ...     if zone.is_propulsion_zone:
        ...         print(f"  Focus on {zone.block_range}")
    """
    # Extract blocks from schedule/context
    blocks = _extract_blocks(schedule, context)

    if not blocks:
        logger.warning("No blocks found for propulsion analysis")
        return PropulsionAnalysis(recommendation="No blocks available for analysis")

    # Get constraint alignment (use provided or calculate)
    overall_alignment = 0.0
    if alignment_matrix is not None:
        overall_alignment = alignment_matrix.overall_alignment
    else:
        # Try to calculate from context
        overall_alignment = _estimate_alignment_from_context(context)

    # Get energy flow (use provided or estimate)
    avg_energy_flow = 0.0
    if energy_history:
        avg_energy_flow = sum(energy_history) / len(energy_history)

    # Analyze each block range
    zones: list[PropulsionZone] = []

    # For now, treat the entire schedule as one zone
    # TODO: Implement block-by-block analysis when assignment data is available
    if blocks:
        start_date = min(b.start_date for b in blocks if hasattr(b, "start_date"))
        end_date = max(b.end_date for b in blocks if hasattr(b, "end_date"))

        potential = calculate_intervention_potential(overall_alignment, avg_energy_flow)

        zone = PropulsionZone(
            block_range=(start_date, end_date),
            constraint_alignment=overall_alignment,
            energy_flow=avg_energy_flow,
            intervention_potential=potential,
            details={
                "block_count": len(blocks),
                "alignment_source": "matrix" if alignment_matrix else "estimated",
                "energy_source": "history" if energy_history else "estimated",
            },
        )
        zones.append(zone)

    # Aggregate metrics
    propulsion_count = sum(1 for z in zones if z.is_propulsion_zone)
    friction_count = sum(1 for z in zones if z.is_friction_zone)
    neutral_count = len(zones) - propulsion_count - friction_count

    potentials = [z.intervention_potential for z in zones]
    overall_potential = sum(potentials) / len(potentials) if potentials else 0.0

    # Generate recommendation
    recommendation = _generate_recommendation(
        overall_potential, propulsion_count, friction_count, zones
    )

    return PropulsionAnalysis(
        zones=zones,
        overall_propulsion_potential=overall_potential,
        propulsion_zone_count=propulsion_count,
        friction_zone_count=friction_count,
        neutral_zone_count=neutral_count,
        recommendation=recommendation,
    )


def _extract_blocks(schedule: Any, context: Any) -> list[Any]:
    """Extract blocks from schedule or context."""
    # Try schedule first
    if hasattr(schedule, "blocks"):
        return list(schedule.blocks)

    # Try context
    if hasattr(context, "blocks"):
        return list(context.blocks)

    # Try to get from assignments
    if hasattr(schedule, "assignments"):
        blocks = set()
        for a in schedule.assignments:
            if hasattr(a, "block"):
                blocks.add(a.block)
        return list(blocks)

    return []


def _estimate_alignment_from_context(context: Any) -> float:
    """Estimate constraint alignment from context when matrix not available."""
    # Default to neutral if no data
    if not hasattr(context, "constraints"):
        return 0.0

    # Simple heuristic based on constraint count ratio
    constraints = context.constraints if hasattr(context, "constraints") else []
    if not constraints:
        return 0.0

    # More soft constraints relative to hard = higher flexibility = better alignment
    hard = sum(1 for c in constraints if getattr(c, "is_hard", False))
    soft = len(constraints) - hard

    if hard + soft == 0:
        return 0.0

    soft_ratio = soft / (hard + soft)
    # Map soft ratio to alignment: more soft = positive, more hard = negative
    return (soft_ratio - 0.5) * 2  # Maps [0,1] to [-1,1]


def _generate_recommendation(
    potential: float,
    propulsion_count: int,
    friction_count: int,
    zones: list[PropulsionZone],
) -> str:
    """Generate actionable recommendation based on analysis."""
    if potential > 0.7:
        return (
            f"HIGH OPPORTUNITY: {propulsion_count} propulsion zones detected. "
            "Constraints are well-aligned - optimization will converge quickly."
        )
    elif potential > 0.4:
        return (
            f"MODERATE OPPORTUNITY: Mixed zone profile "
            f"({propulsion_count} propulsion, {friction_count} friction). "
            "Consider constraint weight adjustments to increase alignment."
        )
    elif friction_count > propulsion_count:
        # Find top conflict
        friction_zones = [z for z in zones if z.is_friction_zone]
        if friction_zones:
            worst = min(friction_zones, key=lambda z: z.constraint_alignment)
            return (
                f"HIGH FRICTION: {friction_count} zones show constraint conflicts. "
                f"Focus on resolving conflicts in block range {worst.block_range}."
            )
        return f"HIGH FRICTION: {friction_count} zones show constraint conflicts."
    else:
        return (
            "LOW OPPORTUNITY: Constraints largely orthogonal. "
            "Optimization will work but without synergy benefits."
        )


# Convenience function for MCP tool
def analyze_schedule_viscosity(
    schedule_id: str,
    start_date: date,
    end_date: date,
    db_session: Any = None,
) -> dict:
    """
    High-level API for MCP tool: analyze schedule viscosity.

    Args:
        schedule_id: UUID of schedule to analyze
        start_date: Analysis start date
        end_date: Analysis end date
        db_session: Optional database session

    Returns:
        Dictionary with viscosity analysis results
    """
    # This is a placeholder for the MCP tool integration
    # Will be connected to actual schedule loading in Task 10
    logger.info(f"Analyzing viscosity for schedule {schedule_id}")

    # Return placeholder for now
    return {
        "schedule_id": schedule_id,
        "analysis_range": (start_date.isoformat(), end_date.isoformat()),
        "effective_viscosity": 0.0,
        "propulsion_zones": [],
        "friction_zones": [],
        "energy_injection_rate": 0.0,
        "recommendations": ["Connect to actual schedule data for analysis"],
    }
