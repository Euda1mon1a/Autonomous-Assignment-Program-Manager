"""
Diff Guard: Schedule Change Validation.

Validates proposed schedule changes against configurable thresholds to prevent
excessive churn. Integrates with anti_churn module for metrics calculation.

Thresholds:
    - Global: Reject if >20% of total assignments change
    - Per-person: Reject if any individual has >50% of their assignments changed
    - High-churn residents: Warn if >30% of assignments change for any resident

Usage:
    from app.scheduling.diff_guard import DiffGuard, DiffThresholds

    guard = DiffGuard()
    result = guard.validate(old_schedule, new_schedule)

    if result.status == DiffStatus.REJECT:
        raise ValueError(f"Schedule change rejected: {result.reason}")
    elif result.status == DiffStatus.WARN:
        logger.warning(f"Schedule change warning: {result.warnings}")
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from app.models.assignment import Assignment
from app.scheduling.periodicity.anti_churn import (
    ScheduleSnapshot,
    calculate_schedule_rigidity,
    estimate_churn_impact,
    hamming_distance,
    hamming_distance_by_person,
)

logger = logging.getLogger(__name__)


class DiffStatus(Enum):
    """Result status from diff validation."""

    PASS = "pass"
    WARN = "warn"
    REJECT = "reject"


@dataclass
class DiffThresholds:
    """
    Configurable thresholds for diff validation.

    Attributes:
        global_max_churn: Maximum global assignment change rate (0-1).
            Default 0.20 = reject if >20% of assignments change.
        person_max_churn: Maximum per-person change rate (0-1).
            Default 0.50 = reject if any person has >50% changes.
        person_warn_churn: Per-person warning threshold (0-1).
            Default 0.30 = warn if any person has >30% changes.
        min_rigidity: Minimum schedule rigidity score (0-1).
            Default 0.80 = reject if rigidity drops below 80%.
        affected_people_warn: Warn if this many people affected.
            Default 10 = warn if >10 people have changes.
    """

    global_max_churn: float = 0.20
    person_max_churn: float = 0.50
    person_warn_churn: float = 0.30
    min_rigidity: float = 0.80
    affected_people_warn: int = 10

    def __post_init__(self) -> None:
        """Validate threshold values."""
        if not 0.0 <= self.global_max_churn <= 1.0:
            raise ValueError(
                f"global_max_churn must be in [0, 1], got {self.global_max_churn}"
            )
        if not 0.0 <= self.person_max_churn <= 1.0:
            raise ValueError(
                f"person_max_churn must be in [0, 1], got {self.person_max_churn}"
            )
        if not 0.0 <= self.person_warn_churn <= 1.0:
            raise ValueError(
                f"person_warn_churn must be in [0, 1], got {self.person_warn_churn}"
            )
        if not 0.0 <= self.min_rigidity <= 1.0:
            raise ValueError(f"min_rigidity must be in [0, 1], got {self.min_rigidity}")
        if self.affected_people_warn < 0:
            raise ValueError(
                f"affected_people_warn must be >= 0, got {self.affected_people_warn}"
            )


@dataclass
class DiffResult:
    """
    Result of diff validation.

    Attributes:
        status: PASS, WARN, or REJECT
        reason: Primary reason for status (if not PASS)
        warnings: List of warning messages
        metrics: Detailed metrics from analysis
        affected_persons: Set of person IDs with changes
        high_churn_persons: Dict of person_id -> churn_rate for high-churn individuals
        timestamp: When validation was performed
    """

    status: DiffStatus
    reason: str | None = None
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    affected_persons: set[UUID] = field(default_factory=set)
    high_churn_persons: dict[UUID, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def is_acceptable(self) -> bool:
        """Return True if changes can proceed (PASS or WARN)."""
        return self.status in (DiffStatus.PASS, DiffStatus.WARN)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "status": self.status.value,
            "reason": self.reason,
            "warnings": self.warnings,
            "metrics": self.metrics,
            "affected_person_count": len(self.affected_persons),
            "high_churn_person_count": len(self.high_churn_persons),
            "timestamp": self.timestamp.isoformat(),
        }


class DiffGuard:
    """
    Guard against excessive schedule changes.

    Validates proposed schedule changes against configurable thresholds
    to prevent large-scale reshuffling that could disrupt operations.

    Usage:
        guard = DiffGuard(thresholds=DiffThresholds(global_max_churn=0.15))
        result = guard.validate(current_schedule, proposed_schedule)

        if result.status == DiffStatus.REJECT:
            raise ValueError(f"Change rejected: {result.reason}")
    """

    def __init__(self, thresholds: DiffThresholds | None = None) -> None:
        """
        Initialize diff guard.

        Args:
            thresholds: Custom thresholds (uses defaults if None)
        """
        self.thresholds = thresholds or DiffThresholds()

    def validate(
        self,
        old_schedule: ScheduleSnapshot | list[Assignment],
        new_schedule: ScheduleSnapshot | list[Assignment],
    ) -> DiffResult:
        """
        Validate schedule changes against thresholds.

        Args:
            old_schedule: Current schedule (snapshot or assignment list)
            new_schedule: Proposed schedule (snapshot or assignment list)

        Returns:
            DiffResult with status, metrics, and affected persons
        """
        # Convert to snapshots if needed
        if isinstance(old_schedule, list):
            old_schedule = ScheduleSnapshot.from_assignments(old_schedule)
        if isinstance(new_schedule, list):
            new_schedule = ScheduleSnapshot.from_assignments(new_schedule)

        # Calculate metrics
        rigidity = calculate_schedule_rigidity(new_schedule, old_schedule)
        total_changes = hamming_distance(old_schedule, new_schedule)
        churn_by_person = hamming_distance_by_person(old_schedule, new_schedule)
        impact = estimate_churn_impact(old_schedule, new_schedule)

        # Calculate global churn rate
        total_assignments = len(old_schedule.assignments) + len(
            new_schedule.assignments
        )
        global_churn_rate = (
            total_changes / total_assignments if total_assignments > 0 else 0.0
        )

        # Calculate per-person churn rates
        old_by_person = self._count_assignments_by_person(old_schedule)
        new_by_person = self._count_assignments_by_person(new_schedule)

        person_churn_rates = {}
        for person_id, change_count in churn_by_person.items():
            person_total = old_by_person.get(person_id, 0) + new_by_person.get(
                person_id, 0
            )
            if person_total > 0:
                person_churn_rates[person_id] = change_count / person_total

        # Identify affected and high-churn persons
        affected_persons = {pid for pid, rate in person_churn_rates.items() if rate > 0}
        high_churn_persons = {
            pid: rate
            for pid, rate in person_churn_rates.items()
            if rate > self.thresholds.person_warn_churn
        }

        # Build metrics
        metrics = {
            "rigidity": rigidity,
            "global_churn_rate": global_churn_rate,
            "total_changes": total_changes,
            "affected_people": len(affected_persons),
            "max_person_churn_rate": max(person_churn_rates.values())
            if person_churn_rates
            else 0.0,
            "impact_severity": impact.get("severity", "unknown"),
            "recommendation": impact.get("recommendation", ""),
        }

        # Evaluate against thresholds
        warnings = []
        reject_reason = None

        # Check rigidity (global stability)
        if rigidity < self.thresholds.min_rigidity:
            reject_reason = f"Schedule rigidity {rigidity:.2%} below minimum {self.thresholds.min_rigidity:.2%}"

        # Check global churn rate
        if global_churn_rate > self.thresholds.global_max_churn:
            reject_reason = (
                f"Global churn {global_churn_rate:.2%} exceeds maximum "
                f"{self.thresholds.global_max_churn:.2%}"
            )

        # Check per-person churn (rejection threshold)
        for person_id, rate in person_churn_rates.items():
            if rate > self.thresholds.person_max_churn:
                reject_reason = (
                    f"Person {person_id} has {rate:.2%} churn, exceeds maximum "
                    f"{self.thresholds.person_max_churn:.2%}"
                )
                break

        # Check warnings (if not already rejecting)
        if not reject_reason:
            # Per-person warning threshold
            for person_id, rate in high_churn_persons.items():
                warnings.append(
                    f"Person {person_id}: {rate:.2%} churn (above {self.thresholds.person_warn_churn:.2%})"
                )

            # Affected people count warning
            if len(affected_persons) > self.thresholds.affected_people_warn:
                warnings.append(
                    f"{len(affected_persons)} people affected (threshold: "
                    f"{self.thresholds.affected_people_warn})"
                )

        # Determine status
        if reject_reason:
            status = DiffStatus.REJECT
        elif warnings:
            status = DiffStatus.WARN
        else:
            status = DiffStatus.PASS

        logger.info(
            f"Diff validation: status={status.value}, rigidity={rigidity:.2%}, "
            f"global_churn={global_churn_rate:.2%}, affected={len(affected_persons)}"
        )

        return DiffResult(
            status=status,
            reason=reject_reason,
            warnings=warnings,
            metrics=metrics,
            affected_persons=affected_persons,
            high_churn_persons=high_churn_persons,
        )

    def validate_assignments(
        self,
        old_assignments: list[Assignment],
        new_assignments: list[Assignment],
    ) -> DiffResult:
        """
        Convenience method for validating Assignment lists directly.

        Args:
            old_assignments: Current assignment list
            new_assignments: Proposed assignment list

        Returns:
            DiffResult with validation outcome
        """
        old_snapshot = ScheduleSnapshot.from_assignments(old_assignments)
        new_snapshot = ScheduleSnapshot.from_assignments(new_assignments)
        return self.validate(old_snapshot, new_snapshot)

    def _count_assignments_by_person(
        self, schedule: ScheduleSnapshot
    ) -> dict[UUID, int]:
        """Count total assignments per person in a schedule."""
        counts: dict[UUID, int] = {}
        for person_id, _block_id, _template_id in schedule.assignments:
            counts[person_id] = counts.get(person_id, 0) + 1
        return counts


# Convenience function for one-off validation
def validate_schedule_diff(
    old_schedule: ScheduleSnapshot | list[Assignment],
    new_schedule: ScheduleSnapshot | list[Assignment],
    thresholds: DiffThresholds | None = None,
) -> DiffResult:
    """
    Validate schedule changes with optional custom thresholds.

    Convenience function for one-off validation without creating a DiffGuard instance.

    Args:
        old_schedule: Current schedule
        new_schedule: Proposed schedule
        thresholds: Optional custom thresholds

    Returns:
        DiffResult with validation outcome

    Example:
        result = validate_schedule_diff(current, proposed)
        if not result.is_acceptable():
            raise ValueError(result.reason)
    """
    guard = DiffGuard(thresholds=thresholds)
    return guard.validate(old_schedule, new_schedule)
