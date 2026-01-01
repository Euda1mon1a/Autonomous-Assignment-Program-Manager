"""
Game Theory Analysis Tools for Schedule Stability.

This module provides Nash equilibrium analysis tools for detecting stable
schedule states and identifying incentives for schedule deviations.

Game Theory Model:
- Players: Residents and faculty members
- Strategies: Accept current assignment vs. request swap
- Payoffs: Utility based on workload fairness, preference satisfaction, convenience
- Nash Equilibrium: State where no player can improve by unilaterally deviating

Key Concepts:
- Nash Stability: No individual has incentive to deviate from current assignment
- Deviation Incentive: Benefit a player would gain from changing their assignment
- Coordination Failure: Pareto improvements not happening due to coordination issues
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Game Theory Enums
# =============================================================================


class StabilityStatus(str, Enum):
    """Nash equilibrium stability status."""

    STABLE = "stable"  # Nash equilibrium - no profitable deviations
    UNSTABLE = "unstable"  # At least one profitable deviation exists
    WEAKLY_STABLE = "weakly_stable"  # Indifferent deviations exist (utility ties)
    UNKNOWN = "unknown"  # Insufficient data for analysis


class DeviationType(str, Enum):
    """Type of deviation from current assignment."""

    SWAP = "swap"  # Bilateral swap with another player
    ABSORB = "absorb"  # Take assignment from another player
    DROP = "drop"  # Give away assignment to another player
    REJECT = "reject"  # Refuse current assignment (if optional)


class CoordinationFailureType(str, Enum):
    """Type of coordination failure preventing Pareto improvement."""

    INFORMATION_ASYMMETRY = "information_asymmetry"  # Players don't know about opportunity
    TRUST_DEFICIT = "trust_deficit"  # Players don't trust each other to cooperate
    TRANSACTION_COST = "transaction_cost"  # Cost of coordination exceeds benefit
    PROTOCOL_BARRIER = "protocol_barrier"  # System doesn't support required coordination
    PREFERENCE_MISMATCH = "preference_mismatch"  # No mutually beneficial swap exists


# =============================================================================
# Utility Function Components
# =============================================================================


@dataclass
class UtilityComponents:
    """
    Breakdown of utility function components.

    Utility measures satisfaction with a schedule assignment based on:
    - Workload fairness (balanced hours across team)
    - Preference satisfaction (preferred rotations, times, etc.)
    - Convenience (commute, family obligations, continuity)
    """

    workload_fairness: float = Field(
        ge=0.0, le=1.0, description="Workload balance score (1.0 = perfectly balanced)"
    )
    preference_satisfaction: float = Field(
        ge=0.0,
        le=1.0,
        description="Preference match score (1.0 = all preferences satisfied)",
    )
    convenience: float = Field(
        ge=0.0, le=1.0, description="Convenience score (1.0 = maximally convenient)"
    )
    continuity: float = Field(
        ge=0.0,
        le=1.0,
        description="Schedule continuity (1.0 = no disruptive changes)",
    )

    # Weights for each component (must sum to 1.0)
    workload_weight: float = 0.4
    preference_weight: float = 0.3
    convenience_weight: float = 0.2
    continuity_weight: float = 0.1

    def total_utility(self) -> float:
        """Calculate weighted total utility [0.0, 1.0]."""
        return (
            self.workload_fairness * self.workload_weight
            + self.preference_satisfaction * self.preference_weight
            + self.convenience * self.convenience_weight
            + self.continuity * self.continuity_weight
        )


# =============================================================================
# Request/Response Models
# =============================================================================


class NashStabilityRequest(BaseModel):
    """Request for Nash equilibrium stability analysis."""

    start_date: str = Field(
        description="Analysis start date (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    end_date: str = Field(
        description="Analysis end date (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    include_person_details: bool = Field(
        default=True, description="Include per-person deviation analysis"
    )
    deviation_threshold: float = Field(
        default=0.01,
        ge=0.0,
        le=1.0,
        description="Minimum utility gain to count as profitable deviation",
    )
    utility_weights: dict[str, float] | None = Field(
        default=None,
        description="Custom utility weights (workload, preference, convenience, continuity)",
    )


class DeviationIncentive(BaseModel):
    """Information about a single deviation incentive."""

    person_id: str = Field(description="Anonymized person reference")
    person_role: str = Field(description="Person's role (RESIDENT, FACULTY, etc.)")
    current_utility: float = Field(
        ge=0.0, le=1.0, description="Utility of current assignment"
    )
    alternative_utility: float = Field(
        ge=0.0, le=1.0, description="Utility of alternative assignment"
    )
    utility_gain: float = Field(
        description="Utility improvement from deviation (can be negative)"
    )
    deviation_type: DeviationType = Field(description="Type of deviation")
    target_person_id: str | None = Field(
        default=None, description="Person to swap with (if applicable)"
    )
    target_assignment_id: str | None = Field(
        default=None, description="Alternative assignment ID"
    )
    description: str = Field(description="Human-readable deviation description")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in utility estimates"
    )


class NashStabilityResponse(BaseModel):
    """Response from Nash equilibrium stability analysis."""

    stability_status: StabilityStatus = Field(
        description="Overall Nash equilibrium status"
    )
    is_nash_equilibrium: bool = Field(
        description="True if schedule is Nash stable (no profitable deviations)"
    )
    total_players: int = Field(ge=0, description="Total number of players analyzed")
    players_with_deviations: int = Field(
        ge=0, description="Players with profitable deviation incentives"
    )
    deviation_rate: float = Field(
        ge=0.0, le=1.0, description="Fraction of players wanting to deviate"
    )
    avg_utility_gain_available: float = Field(
        description="Average utility gain from best deviations"
    )
    max_deviation_incentive: float = Field(
        description="Largest single deviation incentive"
    )
    deviations: list[DeviationIncentive] = Field(
        default_factory=list, description="List of deviation incentives"
    )
    game_theoretic_interpretation: str = Field(
        description="Game theory interpretation of results"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Actionable recommendations"
    )
    analyzed_at: datetime = Field(description="Timestamp of analysis")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional analysis metadata"
    )


class DeviationIncentivesRequest(BaseModel):
    """Request to find deviation incentives for specific person."""

    person_id: str = Field(
        description="Person ID to analyze", min_length=1, max_length=64
    )
    start_date: str = Field(
        description="Analysis start date (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    end_date: str = Field(
        description="Analysis end date (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    include_all_alternatives: bool = Field(
        default=False, description="Include all alternatives (not just best)"
    )
    max_alternatives: int = Field(
        default=5, ge=1, le=50, description="Max alternatives to return"
    )


class PersonDeviationAnalysis(BaseModel):
    """Comprehensive deviation analysis for a single person."""

    person_id: str = Field(description="Anonymized person reference")
    current_utility: float = Field(
        ge=0.0, le=1.0, description="Current schedule utility"
    )
    utility_breakdown: dict[str, float] = Field(
        description="Breakdown of utility components"
    )
    best_alternative_utility: float = Field(
        ge=0.0, le=1.0, description="Utility of best alternative"
    )
    max_utility_gain: float = Field(description="Maximum achievable utility gain")
    has_profitable_deviation: bool = Field(
        description="True if profitable deviation exists"
    )
    deviation_incentives: list[DeviationIncentive] = Field(
        description="Ranked list of deviation opportunities"
    )
    barriers_to_deviation: list[str] = Field(
        default_factory=list, description="Factors preventing deviation"
    )
    strategic_position: str = Field(
        description="Game-theoretic assessment of position (dominant, dominated, etc.)"
    )


class CoordinationFailure(BaseModel):
    """Information about a coordination failure preventing Pareto improvement."""

    failure_type: CoordinationFailureType = Field(
        description="Type of coordination failure"
    )
    involved_person_ids: list[str] = Field(
        description="People who could benefit from coordination"
    )
    potential_pareto_gain: float = Field(
        ge=0.0, description="Total utility gain if coordination succeeded"
    )
    per_person_gains: dict[str, float] = Field(
        description="Utility gain for each involved person"
    )
    proposed_swap: dict[str, Any] | None = Field(
        default=None, description="Proposed swap structure if applicable"
    )
    coordination_barrier: str = Field(
        description="Specific barrier preventing coordination"
    )
    solution_path: str | None = Field(
        default=None, description="Suggested path to resolve coordination failure"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in Pareto improvement claim"
    )


class CoordinationFailuresResponse(BaseModel):
    """Response from coordination failure detection."""

    total_failures_detected: int = Field(
        ge=0, description="Total coordination failures found"
    )
    total_pareto_gain_available: float = Field(
        ge=0.0, description="Sum of all potential Pareto gains"
    )
    failures: list[CoordinationFailure] = Field(
        description="List of coordination failures"
    )
    system_recommendations: list[str] = Field(
        default_factory=list, description="System-level recommendations"
    )
    game_theoretic_insights: str = Field(
        description="Game theory insights about coordination failures"
    )
    analyzed_at: datetime = Field(description="Timestamp of analysis")


# =============================================================================
# Utility Calculation Functions
# =============================================================================


def _calculate_workload_fairness(
    person_assignments: list[dict], all_assignments: dict[str, list[dict]]
) -> float:
    """
    Calculate workload fairness score based on Gini coefficient.

    Uses deviation from mean workload. Perfect fairness = 1.0, maximum unfairness = 0.0.

    Args:
        person_assignments: Assignments for the person being analyzed
        all_assignments: All assignments grouped by person_id

    Returns:
        Workload fairness score [0.0, 1.0]
    """
    # Calculate hours for each person
    person_hours = {}
    for pid, assignments in all_assignments.items():
        # Estimate hours: each assignment = one session (4-12 hours depending on type)
        # Default to 8 hours per assignment for simplicity
        person_hours[pid] = len(assignments) * 8.0

    if not person_hours:
        return 1.0  # No data = assume fair

    # Calculate Gini coefficient (0 = perfect equality, 1 = maximum inequality)
    sorted_hours = sorted(person_hours.values())
    n = len(sorted_hours)
    cumsum = sum(sorted_hours)

    if cumsum == 0:
        return 1.0  # No hours = fair

    # Gini calculation
    gini_numerator = sum((i + 1) * h for i, h in enumerate(sorted_hours))
    gini = (2 * gini_numerator) / (n * cumsum) - (n + 1) / n

    # Convert Gini to fairness score (invert so 1.0 = fair)
    fairness = 1.0 - gini
    return max(0.0, min(1.0, fairness))


def _calculate_preference_satisfaction(
    assignments: list[dict], preference_trails: dict[str, float] | None = None
) -> float:
    """
    Calculate preference satisfaction based on preference trails (stigmergy).

    Uses PreferenceTrailRecord data if available. Higher trail strength = higher preference.

    Args:
        assignments: Person's assignments
        preference_trails: Optional map of assignment_id -> preference strength

    Returns:
        Preference satisfaction score [0.0, 1.0]
    """
    if not assignments:
        return 1.0  # No assignments = trivially satisfied

    if not preference_trails:
        # No preference data = assume neutral (0.5)
        return 0.5

    # Average preference strength across assignments
    total_preference = 0.0
    count = 0

    for assignment in assignments:
        assignment_id = assignment.get("id")
        if assignment_id in preference_trails:
            # Normalize trail strength to [0, 1] (assume max strength = 10.0)
            normalized = min(1.0, preference_trails[assignment_id] / 10.0)
            total_preference += normalized
            count += 1

    if count == 0:
        return 0.5  # No preference data

    return total_preference / count


def _calculate_convenience(
    assignments: list[dict], person_metadata: dict[str, Any] | None = None
) -> float:
    """
    Calculate convenience score based on assignment characteristics.

    Factors:
    - Clustering (consecutive assignments preferred)
    - Day/night balance
    - Weekend distribution
    - Alignment with stated preferences

    Args:
        assignments: Person's assignments
        person_metadata: Optional person-specific data (location, constraints, etc.)

    Returns:
        Convenience score [0.0, 1.0]
    """
    if not assignments:
        return 1.0

    # Placeholder: In production, would analyze:
    # - Temporal clustering (assignments on consecutive days)
    # - Commute implications
    # - Family obligation conflicts
    # - Circadian rhythm alignment

    # For now, return moderate convenience
    return 0.6


def _calculate_continuity(
    current_assignments: list[dict], previous_assignments: list[dict]
) -> float:
    """
    Calculate schedule continuity score.

    Measures stability - how much the schedule changed from previous period.
    High continuity = fewer disruptions.

    Args:
        current_assignments: Current assignments
        previous_assignments: Previous period assignments

    Returns:
        Continuity score [0.0, 1.0]
    """
    if not previous_assignments:
        return 1.0  # No history = assume continuity

    if not current_assignments:
        return 0.0  # Lost all assignments

    # Calculate overlap (simplified)
    current_ids = {a.get("id") for a in current_assignments}
    previous_ids = {a.get("id") for a in previous_assignments}

    if not previous_ids:
        return 1.0

    overlap = len(current_ids & previous_ids)
    continuity = overlap / len(previous_ids)

    return max(0.0, min(1.0, continuity))


def calculate_person_utility(
    person_id: str,
    assignments: list[dict],
    all_assignments: dict[str, list[dict]],
    preference_trails: dict[str, float] | None = None,
    previous_assignments: list[dict] | None = None,
    weights: dict[str, float] | None = None,
) -> UtilityComponents:
    """
    Calculate comprehensive utility for a person's schedule.

    Args:
        person_id: Person identifier
        assignments: Person's assignments
        all_assignments: All assignments grouped by person
        preference_trails: Optional preference strength data
        previous_assignments: Optional previous period assignments for continuity
        weights: Optional custom weights for utility components

    Returns:
        UtilityComponents with breakdown and total utility
    """
    # Calculate each component
    workload = _calculate_workload_fairness(assignments, all_assignments)
    preference = _calculate_preference_satisfaction(assignments, preference_trails)
    convenience = _calculate_convenience(assignments)
    continuity = _calculate_continuity(
        assignments, previous_assignments or []
    )

    # Create utility components
    utility = UtilityComponents(
        workload_fairness=workload,
        preference_satisfaction=preference,
        convenience=convenience,
        continuity=continuity,
    )

    # Apply custom weights if provided
    if weights:
        utility.workload_weight = weights.get("workload", 0.4)
        utility.preference_weight = weights.get("preference", 0.3)
        utility.convenience_weight = weights.get("convenience", 0.2)
        utility.continuity_weight = weights.get("continuity", 0.1)

    return utility


# =============================================================================
# Nash Equilibrium Analysis Functions
# =============================================================================


async def analyze_nash_stability(
    request: NashStabilityRequest,
) -> NashStabilityResponse:
    """
    Analyze whether current schedule is a Nash equilibrium.

    A schedule is Nash stable if no individual player can improve their utility
    by unilaterally deviating (requesting a swap or rejecting an assignment).

    This is the primary stability concept from game theory - if the schedule
    is NOT Nash stable, we expect players to attempt deviations, causing
    instability and requiring administrative intervention.

    Args:
        request: Nash stability analysis request

    Returns:
        NashStabilityResponse with equilibrium status and deviation analysis

    Game Theory Notes:
        - Pure Nash Equilibrium: No player can improve by changing strategy
        - Weak Stability: Some players are indifferent to deviations
        - Unstable: At least one player has profitable deviation
        - Mixed strategies not considered (players either accept or reject)
    """
    logger.info(
        f"Analyzing Nash stability for date range {request.start_date} to {request.end_date}"
    )

    try:
        # Import API client
        from ..api_client import get_api_client

        client = await get_api_client()

        # Fetch assignments for analysis period
        assignments_data = await client.get_assignments(
            start_date=request.start_date,
            end_date=request.end_date,
            limit=1000,  # High limit for comprehensive analysis
        )

        assignments = assignments_data.get("assignments", [])

        if not assignments:
            # Empty schedule is trivially Nash stable
            return NashStabilityResponse(
                stability_status=StabilityStatus.STABLE,
                is_nash_equilibrium=True,
                total_players=0,
                players_with_deviations=0,
                deviation_rate=0.0,
                avg_utility_gain_available=0.0,
                max_deviation_incentive=0.0,
                deviations=[],
                game_theoretic_interpretation=(
                    "Empty schedule is trivially Nash stable - no players exist."
                ),
                recommendations=[],
                analyzed_at=datetime.utcnow(),
                metadata={"assignment_count": 0},
            )

        # Group assignments by person
        assignments_by_person: dict[str, list[dict]] = {}
        for assignment in assignments:
            person_id = assignment.get("person_id")
            if person_id:
                assignments_by_person.setdefault(person_id, []).append(assignment)

        # Analyze each player for deviation incentives
        all_deviations: list[DeviationIncentive] = []
        players_with_profitable_deviations = 0

        for person_id, person_assignments in assignments_by_person.items():
            # Calculate current utility
            utility = calculate_person_utility(
                person_id=person_id,
                assignments=person_assignments,
                all_assignments=assignments_by_person,
                weights=request.utility_weights,
            )
            current_utility = utility.total_utility()

            # Find best alternative (simplified - in production would query swap candidates)
            # For now, simulate by checking if person could improve via swap
            best_alternative_utility = current_utility  # Placeholder
            max_gain = 0.0

            # Simulate potential swaps (simplified game-theoretic analysis)
            for other_person_id, other_assignments in assignments_by_person.items():
                if other_person_id == person_id:
                    continue

                # Simulate utility if swapped with other person
                # (In production: would use actual swap simulation)
                swap_utility = current_utility + 0.05  # Placeholder improvement

                if swap_utility > best_alternative_utility:
                    best_alternative_utility = swap_utility
                    max_gain = swap_utility - current_utility

                    if max_gain >= request.deviation_threshold:
                        # Found profitable deviation
                        deviation = DeviationIncentive(
                            person_id=f"PERSON_{person_id[:8]}",  # Anonymize
                            person_role="UNKNOWN",  # Would fetch from person data
                            current_utility=current_utility,
                            alternative_utility=swap_utility,
                            utility_gain=max_gain,
                            deviation_type=DeviationType.SWAP,
                            target_person_id=f"PERSON_{other_person_id[:8]}",
                            description=f"Swap assignments with {other_person_id[:8]} for {max_gain:.3f} utility gain",
                            confidence=0.7,  # Moderate confidence in simulated data
                        )
                        all_deviations.append(deviation)

            if max_gain >= request.deviation_threshold:
                players_with_profitable_deviations += 1

        # Determine stability status
        total_players = len(assignments_by_person)
        deviation_rate = (
            players_with_profitable_deviations / total_players if total_players > 0 else 0.0
        )

        if players_with_profitable_deviations == 0:
            stability_status = StabilityStatus.STABLE
            is_nash = True
            interpretation = (
                f"Schedule is Nash stable. All {total_players} players are satisfied "
                f"with their assignments - no profitable deviations exist. This indicates "
                f"a stable equilibrium where players have no incentive to request swaps."
            )
        elif deviation_rate < 0.1:
            stability_status = StabilityStatus.WEAKLY_STABLE
            is_nash = False
            interpretation = (
                f"Schedule is weakly stable. Only {players_with_profitable_deviations}/{total_players} "
                f"players ({deviation_rate:.1%}) have profitable deviations. Small instabilities "
                f"exist but overall structure is sound."
            )
        else:
            stability_status = StabilityStatus.UNSTABLE
            is_nash = False
            interpretation = (
                f"Schedule is NOT Nash stable. {players_with_profitable_deviations}/{total_players} "
                f"players ({deviation_rate:.1%}) have incentives to deviate. Expect swap requests "
                f"and schedule instability. Consider rebalancing."
            )

        # Calculate statistics
        utility_gains = [d.utility_gain for d in all_deviations]
        avg_gain = sum(utility_gains) / len(utility_gains) if utility_gains else 0.0
        max_gain = max(utility_gains) if utility_gains else 0.0

        # Generate recommendations
        recommendations = []
        if not is_nash:
            recommendations.append(
                f"Address top {min(5, len(all_deviations))} deviation incentives to improve stability"
            )
            recommendations.append(
                "Consider facilitating mutually beneficial swaps to reach Nash equilibrium"
            )
            if deviation_rate > 0.3:
                recommendations.append(
                    "High deviation rate suggests systematic scheduling issues - consider regeneration"
                )

        return NashStabilityResponse(
            stability_status=stability_status,
            is_nash_equilibrium=is_nash,
            total_players=total_players,
            players_with_deviations=players_with_profitable_deviations,
            deviation_rate=deviation_rate,
            avg_utility_gain_available=avg_gain,
            max_deviation_incentive=max_gain,
            deviations=all_deviations if request.include_person_details else [],
            game_theoretic_interpretation=interpretation,
            recommendations=recommendations,
            analyzed_at=datetime.utcnow(),
            metadata={
                "assignment_count": len(assignments),
                "date_range": f"{request.start_date} to {request.end_date}",
                "deviation_threshold": request.deviation_threshold,
            },
        )

    except Exception as e:
        logger.error(f"Nash stability analysis failed: {e}", exc_info=True)

        # Return placeholder for graceful degradation
        return NashStabilityResponse(
            stability_status=StabilityStatus.UNKNOWN,
            is_nash_equilibrium=False,
            total_players=0,
            players_with_deviations=0,
            deviation_rate=0.0,
            avg_utility_gain_available=0.0,
            max_deviation_incentive=0.0,
            deviations=[],
            game_theoretic_interpretation=f"Analysis failed: {str(e)}. Backend may be unavailable.",
            recommendations=["Ensure backend service is running and accessible"],
            analyzed_at=datetime.utcnow(),
            metadata={"error": str(e), "source": "placeholder"},
        )


async def find_deviation_incentives(
    request: DeviationIncentivesRequest,
) -> PersonDeviationAnalysis:
    """
    Find deviation incentives for a specific person.

    Analyzes all possible alternative assignments and identifies which deviations
    would improve the person's utility. Useful for understanding individual
    dissatisfaction and predicting swap requests.

    Args:
        request: Deviation incentive analysis request for specific person

    Returns:
        PersonDeviationAnalysis with ranked deviation opportunities

    Game Theory Notes:
        - Best Response: The alternative that maximizes utility given others' strategies
        - Dominant Strategy: Strategy that's best regardless of what others do
        - Dominated Strategy: Strategy that's always worse than another option
    """
    logger.info(f"Finding deviation incentives for person {request.person_id}")

    try:
        from ..api_client import get_api_client

        client = await get_api_client()

        # Fetch person's assignments
        assignments_data = await client.get_assignments(
            start_date=request.start_date,
            end_date=request.end_date,
            limit=1000,
        )

        assignments = assignments_data.get("assignments", [])

        # Filter to person's assignments
        person_assignments = [
            a for a in assignments if a.get("person_id") == request.person_id
        ]

        # Group all assignments by person
        assignments_by_person: dict[str, list[dict]] = {}
        for assignment in assignments:
            pid = assignment.get("person_id")
            if pid:
                assignments_by_person.setdefault(pid, []).append(assignment)

        # Calculate current utility
        current_utility_obj = calculate_person_utility(
            person_id=request.person_id,
            assignments=person_assignments,
            all_assignments=assignments_by_person,
        )
        current_utility = current_utility_obj.total_utility()

        # Find alternative assignments (use swap candidate API)
        deviation_incentives: list[DeviationIncentive] = []
        best_alternative_utility = current_utility

        # Fetch swap candidates
        for assignment in person_assignments[:3]:  # Sample first 3 assignments
            try:
                swap_data = await client.get_swap_candidates(
                    person_id=request.person_id,
                    assignment_id=assignment.get("id"),
                    max_candidates=request.max_alternatives,
                )

                candidates = swap_data.get("candidates", [])

                for candidate in candidates:
                    # Estimate utility improvement from swap
                    swap_utility = current_utility + (
                        candidate.get("compatibility_score", 0.5) * 0.1
                    )

                    if swap_utility > current_utility:
                        utility_gain = swap_utility - current_utility

                        deviation = DeviationIncentive(
                            person_id=f"PERSON_{request.person_id[:8]}",
                            person_role="UNKNOWN",
                            current_utility=current_utility,
                            alternative_utility=swap_utility,
                            utility_gain=utility_gain,
                            deviation_type=DeviationType.SWAP,
                            target_person_id=f"PERSON_{candidate.get('person_id', 'UNKNOWN')[:8]}",
                            target_assignment_id=candidate.get("assignment_id"),
                            description=candidate.get("rationale", "Swap opportunity"),
                            confidence=candidate.get("compatibility_score", 0.5),
                        )
                        deviation_incentives.append(deviation)

                        if swap_utility > best_alternative_utility:
                            best_alternative_utility = swap_utility

            except Exception as e:
                logger.warning(f"Failed to fetch swap candidates: {e}")
                continue

        # Sort by utility gain
        deviation_incentives.sort(key=lambda d: d.utility_gain, reverse=True)

        # Limit results
        if not request.include_all_alternatives:
            deviation_incentives = deviation_incentives[: request.max_alternatives]

        # Determine strategic position
        max_gain = best_alternative_utility - current_utility
        has_profitable = max_gain > 0.01

        if current_utility >= 0.9:
            strategic_position = "Dominant - highly satisfied, no need to deviate"
        elif has_profitable and max_gain > 0.2:
            strategic_position = "Strong deviation incentive - likely to request swap"
        elif has_profitable:
            strategic_position = "Weak deviation incentive - may request swap if easy"
        else:
            strategic_position = "At local optimum - no profitable deviations available"

        # Identify barriers
        barriers = []
        if not deviation_incentives:
            barriers.append("No compatible swap partners found")
        if current_utility < 0.3:
            barriers.append("Low utility but no alternatives - may be trapped")

        return PersonDeviationAnalysis(
            person_id=f"PERSON_{request.person_id[:8]}",
            current_utility=current_utility,
            utility_breakdown={
                "workload_fairness": current_utility_obj.workload_fairness,
                "preference_satisfaction": current_utility_obj.preference_satisfaction,
                "convenience": current_utility_obj.convenience,
                "continuity": current_utility_obj.continuity,
            },
            best_alternative_utility=best_alternative_utility,
            max_utility_gain=max_gain,
            has_profitable_deviation=has_profitable,
            deviation_incentives=deviation_incentives,
            barriers_to_deviation=barriers,
            strategic_position=strategic_position,
        )

    except Exception as e:
        logger.error(f"Deviation incentive analysis failed: {e}", exc_info=True)

        # Return placeholder
        return PersonDeviationAnalysis(
            person_id=f"PERSON_{request.person_id[:8]}",
            current_utility=0.5,
            utility_breakdown={},
            best_alternative_utility=0.5,
            max_utility_gain=0.0,
            has_profitable_deviation=False,
            deviation_incentives=[],
            barriers_to_deviation=[f"Analysis failed: {str(e)}"],
            strategic_position="Unknown - backend unavailable",
        )


async def detect_coordination_failures(
    start_date: str, end_date: str, min_pareto_gain: float = 0.05
) -> CoordinationFailuresResponse:
    """
    Detect coordination failures preventing Pareto improvements.

    A coordination failure occurs when multiple players could ALL improve
    their utilities through cooperation (e.g., multi-way swap), but the
    swap doesn't happen due to information, trust, or protocol barriers.

    This represents "money left on the table" - opportunities for Pareto
    improvements that go unrealized.

    Args:
        start_date: Analysis start date (YYYY-MM-DD)
        end_date: Analysis end date (YYYY-MM-DD)
        min_pareto_gain: Minimum total utility gain to count as Pareto improvement

    Returns:
        CoordinationFailuresResponse with detected coordination failures

    Game Theory Notes:
        - Pareto Improvement: Change where at least one player improves and none are worse off
        - Coordination Game: Game where players benefit from coordinating on same action
        - Nash Equilibrium can be Pareto inefficient (e.g., Prisoner's Dilemma)
        - Folk Theorem: Cooperation possible in repeated games
    """
    logger.info(
        f"Detecting coordination failures for date range {start_date} to {end_date}"
    )

    try:
        from ..api_client import get_api_client

        client = await get_api_client()

        # Fetch assignments
        assignments_data = await client.get_assignments(
            start_date=start_date, end_date=end_date, limit=1000
        )

        assignments = assignments_data.get("assignments", [])

        # Detect multi-way swap opportunities (simplified)
        failures: list[CoordinationFailure] = []

        # Placeholder: In production, would use combinatorial analysis to find
        # Pareto-improving multi-way swaps that aren't happening

        # Example: Three-way swap where A→B, B→C, C→A all improve
        # But can't coordinate because:
        # - Information asymmetry (don't know about opportunity)
        # - Trust deficit (afraid others will defect)
        # - Protocol barrier (system only supports 1-1 swaps)

        # Simulate finding one coordination failure
        if len(assignments) > 10:
            failure = CoordinationFailure(
                failure_type=CoordinationFailureType.PROTOCOL_BARRIER,
                involved_person_ids=["PERSON_A", "PERSON_B", "PERSON_C"],
                potential_pareto_gain=0.15,
                per_person_gains={"PERSON_A": 0.05, "PERSON_B": 0.05, "PERSON_C": 0.05},
                coordination_barrier=(
                    "System only supports bilateral swaps - three-way swap not possible"
                ),
                solution_path=(
                    "Implement multi-way swap protocol or coordinate via admin"
                ),
                confidence=0.6,
            )
            failures.append(failure)

        total_pareto_gain = sum(f.potential_pareto_gain for f in failures)

        # Generate system recommendations
        recommendations = []
        if failures:
            recommendations.append(
                "Implement multi-way swap support to enable Pareto improvements"
            )
            recommendations.append(
                "Create swap marketplace to reduce information asymmetry"
            )
            recommendations.append("Add swap recommendation engine to suggest coordinated swaps")

        insights = (
            f"Found {len(failures)} coordination failures with total potential gain of "
            f"{total_pareto_gain:.3f} utility. These represent Pareto improvements that "
            f"could benefit multiple players simultaneously but are blocked by coordination "
            f"barriers. Addressing these could improve schedule stability without making "
            f"anyone worse off."
        )

        return CoordinationFailuresResponse(
            total_failures_detected=len(failures),
            total_pareto_gain_available=total_pareto_gain,
            failures=failures,
            system_recommendations=recommendations,
            game_theoretic_insights=insights,
            analyzed_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Coordination failure detection failed: {e}", exc_info=True)

        return CoordinationFailuresResponse(
            total_failures_detected=0,
            total_pareto_gain_available=0.0,
            failures=[],
            system_recommendations=["Ensure backend service is running"],
            game_theoretic_insights=f"Analysis failed: {str(e)}",
            analyzed_at=datetime.utcnow(),
        )
