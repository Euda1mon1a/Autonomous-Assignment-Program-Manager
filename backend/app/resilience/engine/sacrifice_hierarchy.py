"""
Sacrifice Hierarchy - Load Shedding.

Implements priority-based load shedding inspired by power grid load shedding.

When system is overloaded, shed lowest-priority assignments first to prevent
cascade failure.

Concept from:
- Power grid automatic load shedding
- Network traffic QoS (Quality of Service)
- Emergency triage protocols
"""

from dataclasses import dataclass
from enum import Enum


class AssignmentPriority(int, Enum):
    """Assignment priority levels (lower number = higher priority)."""

    CRITICAL = 1  # Cannot shed (patient safety, required coverage)
    HIGH = 2  # Should avoid shedding (core clinical duties)
    MEDIUM = 3  # Can shed if needed (educational activities)
    LOW = 4  # Shed first (administrative, optional)
    DISCRETIONARY = 5  # Always sheddable (research time, electives)


@dataclass
class SheddableAssignment:
    """Assignment that can be shed."""

    assignment_id: str
    priority: AssignmentPriority
    person_id: str
    date: str
    rotation: str
    load_hours: float
    can_defer: bool
    deferral_deadline: str


@dataclass
class LoadSheddingPlan:
    """Plan for shedding load."""

    total_load_to_shed: float
    assignments_to_shed: list[SheddableAssignment]
    load_shed: float
    load_remaining: float
    success: bool
    rationale: str


class SacrificeHierarchy:
    """
    Implement priority-based load shedding.

    Priorities (highest to lowest):
    1. CRITICAL: Emergency coverage, required supervision
    2. HIGH: Core clinical duties, ACGME requirements
    3. MEDIUM: Educational conferences, teaching
    4. LOW: Administrative tasks, committee work
    5. DISCRETIONARY: Research, electives, optional activities
    """

    def __init__(self) -> None:
        """Initialize sacrifice hierarchy."""
        self.priority_order = [
            AssignmentPriority.DISCRETIONARY,
            AssignmentPriority.LOW,
            AssignmentPriority.MEDIUM,
            AssignmentPriority.HIGH,
            AssignmentPriority.CRITICAL,
        ]

    def calculate_shedding_plan(
        self,
        current_load: float,
        capacity: float,
        assignments: list[SheddableAssignment],
        target_utilization: float = 0.80,
    ) -> LoadSheddingPlan:
        """
        Calculate which assignments to shed to reach target utilization.

        Args:
            current_load: Current total load (hours)
            capacity: Total capacity (hours)
            assignments: List of sheddable assignments
            target_utilization: Target utilization ratio (default 80%)

        Returns:
            LoadSheddingPlan with assignments to shed
        """
        # Calculate target load
        target_load = capacity * target_utilization
        load_to_shed = max(0, current_load - target_load)

        if load_to_shed == 0:
            return LoadSheddingPlan(
                total_load_to_shed=0.0,
                assignments_to_shed=[],
                load_shed=0.0,
                load_remaining=current_load,
                success=True,
                rationale="No load shedding needed - within target",
            )

        # Sort assignments by priority (lowest first)
        sorted_assignments = sorted(
            assignments, key=lambda a: (a.priority.value, -a.load_hours)
        )

        # Greedily shed assignments
        to_shed = []
        shed_so_far = 0.0

        for assignment in sorted_assignments:
            if shed_so_far >= load_to_shed:
                break

            # Don't shed CRITICAL assignments
            if assignment.priority == AssignmentPriority.CRITICAL:
                continue

            to_shed.append(assignment)
            shed_so_far += assignment.load_hours

        success = shed_so_far >= load_to_shed
        remaining_load = current_load - shed_so_far

        rationale = self._generate_rationale(
            load_to_shed, shed_so_far, len(to_shed), success
        )

        return LoadSheddingPlan(
            total_load_to_shed=load_to_shed,
            assignments_to_shed=to_shed,
            load_shed=shed_so_far,
            load_remaining=remaining_load,
            success=success,
            rationale=rationale,
        )

    def classify_assignment_priority(
        self,
        rotation_type: str,
        is_required: bool,
        affects_patient_safety: bool,
        is_acgme_mandated: bool,
    ) -> AssignmentPriority:
        """
        Classify assignment priority.

        Args:
            rotation_type: Type of rotation
            is_required: Whether rotation is required for graduation
            affects_patient_safety: Whether affects patient safety
            is_acgme_mandated: Whether mandated by ACGME

        Returns:
            AssignmentPriority
        """
        # Critical: patient safety or emergency coverage
        if affects_patient_safety or "emergency" in rotation_type.lower():
            return AssignmentPriority.CRITICAL

        # High: ACGME required or core clinical
        if is_acgme_mandated or is_required:
            return AssignmentPriority.HIGH

        # Medium: educational but not required
        if "conference" in rotation_type.lower() or "teaching" in rotation_type.lower():
            return AssignmentPriority.MEDIUM

        # Low: administrative
        if "admin" in rotation_type.lower() or "committee" in rotation_type.lower():
            return AssignmentPriority.LOW

        # Discretionary: research, electives
        if "research" in rotation_type.lower() or "elective" in rotation_type.lower():
            return AssignmentPriority.DISCRETIONARY

        # Default: medium
        return AssignmentPriority.MEDIUM

    def _generate_rationale(
        self,
        target: float,
        achieved: float,
        num_assignments: int,
        success: bool,
    ) -> str:
        """Generate human-readable rationale."""
        if success:
            return (
                f"Successfully shed {achieved:.1f} hours by removing {num_assignments} "
                f"low-priority assignments (target: {target:.1f} hours)"
            )
        else:
            shortfall = target - achieved
            return (
                f"Partial success: Shed {achieved:.1f} hours of {target:.1f} target "
                f"({num_assignments} assignments). Shortfall: {shortfall:.1f} hours. "
                f"All remaining assignments are high priority."
            )

    def get_shedding_recommendations(
        self,
        utilization: float,
    ) -> dict:
        """
        Get load shedding recommendations based on utilization.

        Args:
            utilization: Current utilization ratio

        Returns:
            Dict with recommendations
        """
        if utilization < 0.80:
            return {
                "action": "none",
                "message": "Utilization healthy - no shedding needed",
                "priorities_to_shed": [],
            }
        elif utilization < 0.90:
            return {
                "action": "consider",
                "message": "Consider shedding DISCRETIONARY assignments",
                "priorities_to_shed": [AssignmentPriority.DISCRETIONARY],
            }
        elif utilization < 0.95:
            return {
                "action": "recommended",
                "message": "Shed DISCRETIONARY and LOW priority assignments",
                "priorities_to_shed": [
                    AssignmentPriority.DISCRETIONARY,
                    AssignmentPriority.LOW,
                ],
            }
        else:
            return {
                "action": "urgent",
                "message": "URGENT: Shed up to MEDIUM priority assignments",
                "priorities_to_shed": [
                    AssignmentPriority.DISCRETIONARY,
                    AssignmentPriority.LOW,
                    AssignmentPriority.MEDIUM,
                ],
            }
