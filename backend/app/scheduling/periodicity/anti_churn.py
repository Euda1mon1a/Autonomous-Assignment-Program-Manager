"""
Time Crystal Anti-Churn Objective for Schedule Stability.

This module implements anti-churn optimization inspired by time crystal physics
and minimal disruption planning. The key insight: schedules should be "rigid" -
small perturbations (like adding one absence) should not cause large-scale
reshuffling of assignments.

Theoretical Background:
    Time crystals exhibit rigid periodic behavior that persists under perturbation.
    Medical residency schedules are inherently periodic systems with:
    - Drive periods: 7 days (week), 28 days (ACGME 4-week window)
    - Subharmonic responses: Q4 call (4-day cycle), alternating weekends (14-day)
    - Natural rigidity: Assignments should stay stable unless constraints violated

Research Foundations:
    - Discrete time crystals: Break time-translation symmetry with rigid periodicity
    - Minimal disruption planning (Shleyfman et al., 2025): Balance goal achievement
      with minimal changes to initial state
    - Production rescheduling: Minimize deviation from original schedule to reduce
      negative impact on downstream preparations

Usage:
    # Compare current and proposed schedules
    rigidity = calculate_schedule_rigidity(new_schedule, current_schedule)
    # rigidity = 0.92 means 92% of assignments unchanged

    # Use as optimization objective
    score = time_crystal_objective(
        new_schedule,
        current_schedule,
        constraints,
        alpha=0.3  # 30% weight on stability, 70% on constraints
    )

References:
    - Shleyfman et al. (2025). Planning with Minimal Disruption. arXiv:2508.15358
    - SYNERGY_ANALYSIS.md Section 11: Time Crystal Dynamics
    - Wilczek, F. (2012). Quantum Time Crystals. Physical Review Letters.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

import numpy as np

from app.models.assignment import Assignment
from app.scheduling.constraints.base import Constraint, ConstraintResult

logger = logging.getLogger(__name__)


@dataclass
class ScheduleSnapshot:
    """
    Immutable snapshot of a schedule state for comparison.

    Represents assignments as a frozen set of (person_id, block_id, template_id)
    tuples for efficient comparison using Hamming distance.

    Attributes:
        assignments: Set of assignment tuples (person_id, block_id, template_id)
        timestamp: When this snapshot was taken
        metadata: Additional information (algorithm, runtime, etc.)
    """

    assignments: frozenset[tuple[UUID, UUID, UUID | None]]
    timestamp: datetime
    metadata: dict[str, Any] | None = None

    @classmethod
    def from_assignments(
        cls,
        assignments: list[Assignment],
        timestamp: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "ScheduleSnapshot":
        """
        Create snapshot from Assignment objects.

        Args:
            assignments: List of Assignment model instances
            timestamp: Snapshot timestamp (defaults to now)
            metadata: Optional metadata dict

        Returns:
            ScheduleSnapshot with frozen assignment set
        """
        assignment_tuples = frozenset(
            (
                a.person_id,
                a.block_id,
                a.rotation_template_id if hasattr(a, "rotation_template_id") else None,
            )
            for a in assignments
        )

        return cls(
            assignments=assignment_tuples,
            timestamp=timestamp or datetime.utcnow(),
            metadata=metadata or {},
        )

    @classmethod
    def from_tuples(
        cls,
        assignment_tuples: list[tuple[UUID, UUID, UUID | None]],
        timestamp: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "ScheduleSnapshot":
        """
        Create snapshot from raw tuples (e.g., from solver output).

        Args:
            assignment_tuples: List of (person_id, block_id, template_id) tuples
            timestamp: Snapshot timestamp (defaults to now)
            metadata: Optional metadata dict

        Returns:
            ScheduleSnapshot with frozen assignment set
        """
        return cls(
            assignments=frozenset(assignment_tuples),
            timestamp=timestamp or datetime.utcnow(),
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[tuple[UUID, UUID], UUID | None]:
        """
        Convert to dictionary mapping (person_id, block_id) -> template_id.

        Useful for fast lookups during comparison.

        Returns:
            Dictionary for O(1) lookup of assignments
        """
        return {
            (person_id, block_id): template_id
            for person_id, block_id, template_id in self.assignments
        }


def hamming_distance(
    schedule_a: ScheduleSnapshot,
    schedule_b: ScheduleSnapshot,
) -> int:
    """
    Calculate Hamming distance between two schedules.

    The Hamming distance counts the number of positions where schedules differ.
    In scheduling context, this means:
    - New assignments not in original schedule
    - Removed assignments from original schedule
    - Changed template assignments for same person-block pair

    Args:
        schedule_a: First schedule snapshot
        schedule_b: Second schedule snapshot

    Returns:
        Number of differing assignments (0 = identical schedules)

    Example:
        >>> current = ScheduleSnapshot.from_tuples([
        ...     (person1, block1, template_clinic),
        ...     (person2, block2, template_procedures)
        ... ])
        >>> proposed = ScheduleSnapshot.from_tuples([
        ...     (person1, block1, template_clinic),      # Same
        ...     (person2, block2, template_elective)     # Changed template
        ... ])
        >>> hamming_distance(current, proposed)
        1  # Only one assignment changed
    """
    # Convert to sets for symmetric difference
    set_a = schedule_a.assignments
    set_b = schedule_b.assignments

    # Symmetric difference gives all positions that differ
    # (assignments in A but not B) ∪ (assignments in B but not A)
    differences = set_a.symmetric_difference(set_b)

    return len(differences)


def hamming_distance_by_person(
    schedule_a: ScheduleSnapshot,
    schedule_b: ScheduleSnapshot,
) -> dict[UUID, int]:
    """
    Calculate per-person Hamming distance.

    Useful for identifying which residents experience the most churn
    during schedule regeneration.

    Args:
        schedule_a: First schedule snapshot
        schedule_b: Second schedule snapshot

    Returns:
        Dictionary mapping person_id to number of changed assignments

    Example:
        >>> churn_by_person = hamming_distance_by_person(current, proposed)
        >>> # {person1: 0, person2: 3, person3: 1}
        >>> # person2 had 3 assignment changes - highest churn
    """
    dict_a = defaultdict(set)
    dict_b = defaultdict(set)

    # Group assignments by person
    for person_id, block_id, template_id in schedule_a.assignments:
        dict_a[person_id].add((block_id, template_id))

    for person_id, block_id, template_id in schedule_b.assignments:
        dict_b[person_id].add((block_id, template_id))

    # Calculate per-person differences
    all_people = set(dict_a.keys()) | set(dict_b.keys())
    result = {}

    for person_id in all_people:
        assignments_a = dict_a.get(person_id, set())
        assignments_b = dict_b.get(person_id, set())
        result[person_id] = len(assignments_a.symmetric_difference(assignments_b))

    return result


def calculate_schedule_rigidity(
    new_schedule: ScheduleSnapshot,
    current_schedule: ScheduleSnapshot,
) -> float:
    """
    Calculate schedule rigidity score (0.0 to 1.0).

    Rigidity measures how stable a schedule is under perturbation.
    High rigidity (close to 1.0) means few changes from current schedule.
    Low rigidity (close to 0.0) means many changes.

    This is the complement of normalized Hamming distance:
        rigidity = 1 - (hamming_distance / max_possible_distance)

    Args:
        new_schedule: Proposed schedule snapshot
        current_schedule: Current schedule snapshot

    Returns:
        Rigidity score (0.0 = completely different, 1.0 = identical)

    Example:
        >>> rigidity = calculate_schedule_rigidity(new, current)
        >>> if rigidity < 0.7:
        ...     logger.warning("Schedule changed significantly (rigidity={rigidity:.2f})")
        >>> # "Schedule changed significantly (rigidity=0.65)"
    """
    # Calculate Hamming distance
    distance = hamming_distance(new_schedule, current_schedule)

    # Normalize by maximum possible distance
    # Maximum distance occurs when schedules share no assignments
    max_distance = len(new_schedule.assignments) + len(current_schedule.assignments)

    if max_distance == 0:
        # Both schedules empty - perfect rigidity
        return 1.0

    # Rigidity = 1 - normalized_distance
    normalized_distance = distance / max_distance
    rigidity = 1.0 - normalized_distance

    return rigidity


def time_crystal_objective(
    new_schedule: ScheduleSnapshot,
    current_schedule: ScheduleSnapshot,
    constraint_results: list[ConstraintResult],
    alpha: float = 0.3,
    beta: float = 0.1,
) -> float:
    """
    Time-crystal-inspired optimization objective.

    Combines constraint satisfaction with anti-churn (rigidity) to create
    schedules that are both compliant and stable. Inspired by:
    - Time crystal physics: Rigid periodic behavior under perturbation
    - Minimal disruption planning: Balance goals with minimal state changes

    Objective Function:
        score = (1-α-β)*constraint_score + α*rigidity_score + β*fairness_score

    Where:
        - constraint_score: How well schedule satisfies constraints (0-1)
        - rigidity_score: How similar to current schedule (0-1)
        - fairness_score: How evenly churn is distributed across people (0-1)
        - α (alpha): Weight for rigidity (default 0.3 = 30%)
        - β (beta): Weight for fairness (default 0.1 = 10%)

    Weight Recommendations:
        - α = 0.0: Pure constraint optimization (may cause large reshuffles)
        - α = 0.3: Balanced - satisfy constraints with minimal disruption
        - α = 0.5: Conservative - prefer stability over minor improvements
        - α = 1.0: Pure stability (no changes even if suboptimal)

    Args:
        new_schedule: Proposed schedule snapshot
        current_schedule: Current schedule snapshot
        constraint_results: Results from constraint evaluation
        alpha: Weight for rigidity term (0.0 to 1.0)
        beta: Weight for fairness term (0.0 to 1.0)

    Returns:
        Combined objective score (higher is better)

    Raises:
        ValueError: If alpha + beta > 1.0 (weights must sum to <= 1.0)

    Example:
        >>> constraint_results = [
        ...     ConstraintResult(satisfied=True, penalty=0.0),
        ...     ConstraintResult(satisfied=True, penalty=0.1),  # Soft violation
        ...     ConstraintResult(satisfied=False, penalty=10.0) # Hard violation
        ... ]
        >>> score = time_crystal_objective(new, current, constraint_results, alpha=0.3)
        >>> # Lower score due to hard constraint violation and churn
    """
    if alpha + beta > 1.0:
        raise ValueError(
            f"alpha ({alpha}) + beta ({beta}) must be <= 1.0 (got {alpha + beta:.3f})"
        )

    if not 0.0 <= alpha <= 1.0:
        raise ValueError(f"alpha must be in [0, 1], got {alpha}")

    if not 0.0 <= beta <= 1.0:
        raise ValueError(f"beta must be in [0, 1], got {beta}")

    # 1. Constraint satisfaction score
    # Count hard constraint violations (must be zero for valid schedule)
    hard_violations = sum(1 for r in constraint_results if not r.satisfied)

    # Sum soft constraint penalties
    total_penalty = sum(r.penalty for r in constraint_results)

    # Normalize constraint score
    # Perfect score = 1.0 (no violations, no penalties)
    # Each hard violation subtracts 0.5
    # Penalties normalized by reasonable maximum (10.0)
    max_penalty = 10.0
    constraint_score = max(
        0.0, 1.0 - (hard_violations * 0.5) - min(total_penalty / max_penalty, 0.5)
    )

    # 2. Rigidity score (anti-churn)
    rigidity_score = calculate_schedule_rigidity(new_schedule, current_schedule)

    # 3. Fairness score (churn distribution)
    # Churn should be evenly distributed, not concentrated on a few people
    churn_by_person = hamming_distance_by_person(new_schedule, current_schedule)

    if len(churn_by_person) > 0:
        churn_values = list(churn_by_person.values())
        mean_churn = np.mean(churn_values)
        std_churn = np.std(churn_values)

        # Fairness = 1 - (coefficient_of_variation)
        # CV = std / mean, measures relative variability
        # Low CV = fair distribution, High CV = concentrated churn
        if mean_churn > 0:
            cv = std_churn / mean_churn
            fairness_score = max(0.0, 1.0 - min(cv, 1.0))
        else:
            # No churn = perfect fairness
            fairness_score = 1.0
    else:
        fairness_score = 1.0

    # 4. Combined objective
    # Weights: (1-α-β) for constraints, α for rigidity, β for fairness
    objective = (
        (1.0 - alpha - beta) * constraint_score
        + alpha * rigidity_score
        + beta * fairness_score
    )

    logger.debug(
        f"Time crystal objective: {objective:.3f} "
        f"(constraints={constraint_score:.3f}, "
        f"rigidity={rigidity_score:.3f}, "
        f"fairness={fairness_score:.3f}, "
        f"α={alpha}, β={beta})"
    )

    return objective


def estimate_churn_impact(
    current_schedule: ScheduleSnapshot,
    proposed_schedule: ScheduleSnapshot,
) -> dict[str, Any]:
    """
    Estimate the operational impact of schedule churn.

    Provides metrics to help administrators understand what changing
    the schedule will mean in practice.

    Args:
        current_schedule: Current schedule snapshot
        proposed_schedule: Proposed schedule snapshot

    Returns:
        Dictionary with impact metrics:
        - total_changes: Total assignment changes
        - affected_people: Number of people with changed assignments
        - max_person_churn: Maximum changes for any single person
        - mean_person_churn: Average changes per affected person
        - rigidity: Overall schedule stability (0-1)
        - severity: Text severity rating (low/moderate/high/critical)

    Example:
        >>> impact = estimate_churn_impact(current, proposed)
        >>> print(f"Impact: {impact['severity']}")
        >>> print(f"{impact['affected_people']} residents affected")
        >>> # Impact: moderate
        >>> # 8 residents affected
    """
    total_changes = hamming_distance(current_schedule, proposed_schedule)
    churn_by_person = hamming_distance_by_person(current_schedule, proposed_schedule)

    affected_people = sum(1 for count in churn_by_person.values() if count > 0)
    max_person_churn = max(churn_by_person.values()) if churn_by_person else 0
    mean_person_churn = (
        np.mean([c for c in churn_by_person.values() if c > 0])
        if affected_people > 0
        else 0.0
    )

    rigidity = calculate_schedule_rigidity(proposed_schedule, current_schedule)

    # Severity classification
    if rigidity >= 0.95:
        severity = "minimal"
    elif rigidity >= 0.85:
        severity = "low"
    elif rigidity >= 0.70:
        severity = "moderate"
    elif rigidity >= 0.50:
        severity = "high"
    else:
        severity = "critical"

    return {
        "total_changes": total_changes,
        "affected_people": affected_people,
        "max_person_churn": max_person_churn,
        "mean_person_churn": float(mean_person_churn),
        "rigidity": rigidity,
        "severity": severity,
        "recommendation": _generate_churn_recommendation(rigidity, affected_people),
    }


def _generate_churn_recommendation(rigidity: float, affected_people: int) -> str:
    """Generate human-readable recommendation based on churn metrics."""
    if rigidity >= 0.95:
        return "Schedule is highly stable. Safe to publish."
    elif rigidity >= 0.85:
        return "Minor changes only. Consider publishing after review."
    elif rigidity >= 0.70:
        return f"Moderate churn affecting {affected_people} people. Review changes carefully."
    elif rigidity >= 0.50:
        return (
            f"High churn affecting {affected_people} people. Consider phased rollout."
        )
    else:
        return (
            f"Critical churn affecting {affected_people} people. "
            f"Investigate root cause before publishing."
        )


def detect_periodic_patterns(
    assignments: list[Assignment],
    base_period_days: int = 7,
    min_correlation: float = 0.7,
) -> list[int]:
    """
    Detect emergent periodic patterns in assignment data.

    Uses autocorrelation to identify subharmonic cycles - natural longer
    periods that emerge from the base scheduling rhythm. For example:
    - Base period: 7 days (weekly)
    - Subharmonics: 14 days (alternating weekends), 28 days (Q4 call)

    This helps identify natural rigidity in the schedule that should be
    preserved during regeneration.

    Args:
        assignments: List of Assignment objects
        base_period_days: Base period in days (default 7 for weekly)
        min_correlation: Minimum autocorrelation to count as periodic (0-1)

    Returns:
        List of detected cycle lengths in days (e.g., [7, 14, 28])

    Example:
        >>> periods = detect_periodic_patterns(assignments)
        >>> # [7, 14, 28]  # Found weekly, bi-weekly, and 4-week cycles
        >>> logger.info(f"Detected natural cycles: {periods} days")
    """
    if not assignments:
        return []

    # Build time series of assignment counts per day
    assignment_counts_by_day = defaultdict(int)

    min_date = min(a.block.date for a in assignments if a.block)
    max_date = max(a.block.date for a in assignments if a.block)

    if not min_date or not max_date:
        return []

    # Count assignments for each day
    for assignment in assignments:
        if assignment.block:
            assignment_counts_by_day[assignment.block.date] += 1

    # Create time series array
    num_days = (max_date - min_date).days + 1
    time_series = np.zeros(num_days)

    for i in range(num_days):
        current_date = min_date + timedelta(days=i)
        time_series[i] = assignment_counts_by_day.get(current_date, 0)

    if len(time_series) < base_period_days * 2:
        # Not enough data for meaningful autocorrelation
        return []

    # Calculate autocorrelation
    autocorr = np.correlate(time_series, time_series, mode="full")
    autocorr = autocorr[len(autocorr) // 2 :]  # Take positive lags only

    # Normalize
    autocorr = autocorr / autocorr[0] if autocorr[0] > 0 else autocorr

    # Find peaks that are multiples of base period
    detected_periods = []

    # Check multiples of base period (1x, 2x, 3x, 4x)
    for multiplier in range(1, 5):
        period = base_period_days * multiplier
        if period < len(autocorr):
            # Check autocorrelation at this lag
            if autocorr[period] >= min_correlation:
                detected_periods.append(period)

    return detected_periods
