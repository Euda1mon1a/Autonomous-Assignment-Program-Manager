"""
Sacrifice Hierarchy (Triage Medicine Load Shedding).

When resources are insufficient for all needs, explicitly prioritize who
receives care and who doesn't, based on pre-established criteria that
remove in-the-moment decision burden.

The key insight: decisions made during crisis are worse than decisions
made beforehand. Having an explicit hierarchy removes guilt, politics,
and cognitive load from crisis decision-making.

Activity Sacrifice Order (Most to Least Protected):
1. Patient Safety - Immediate life/death (NEVER sacrifice)
2. ACGME Requirements - Accreditation = program survival
3. Continuity of Care - Patient outcomes, but deferrable
4. Education (Core) - Trainee development
5. Research - Important but not urgent
6. Administration - First to cut, last to restore
7. Education (Optional) - Pure growth opportunities
"""

import functools
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from uuid import UUID

logger = logging.getLogger(__name__)


class ActivityCategory(IntEnum):
    """
    Activity categories in order of protection priority.

    Lower number = higher priority = more protected.
    These are NEVER sacrificed unless higher-priority items are at risk.
    """

    PATIENT_SAFETY = 1  # ICU coverage, OR staffing, trauma response
    ACGME_REQUIREMENTS = 2  # Minimum case numbers, required rotations
    CONTINUITY_OF_CARE = 3  # Clinic follow-ups, chronic disease management
    EDUCATION_CORE = 4  # Didactics, simulation labs
    RESEARCH = 5  # Studies, publications, grants
    ADMINISTRATION = 6  # Meetings, committees, paperwork
    EDUCATION_OPTIONAL = 7  # Conferences, electives, enrichment


class LoadSheddingLevel(IntEnum):
    """
    Load shedding severity levels.

    Each level suspends activities up to and including that priority.
    """

    NORMAL = 0  # No shedding - all activities
    YELLOW = 1  # Suspend optional education
    ORANGE = 2  # Also suspend admin and research
    RED = 3  # Also suspend core education
    BLACK = 4  # Essential services only (patient safety + ACGME minimum)
    CRITICAL = 5  # Patient safety only


@dataclass
class Activity:
    """An activity that can be scheduled."""

    id: UUID
    name: str
    category: ActivityCategory
    faculty_hours: float
    is_required: bool = False
    min_frequency: str | None = None  # e.g., "weekly", "monthly"
    can_be_deferred: bool = True
    deferral_limit_days: int = 30


@dataclass
class SacrificeDecision:
    """Record of a sacrifice decision for audit trail."""

    timestamp: datetime
    level: LoadSheddingLevel
    activities_suspended: list[str]
    reason: str
    coverage_before: float
    coverage_after: float
    approved_by: str | None = None
    notes: str = ""


@dataclass
class LoadSheddingStatus:
    """Current load shedding status."""

    level: LoadSheddingLevel
    level_name: str
    active_since: datetime | None
    activities_suspended: list[str]
    activities_protected: list[str]
    current_coverage: float
    target_coverage: float
    decisions_log: list[SacrificeDecision] = field(default_factory=list)


class SacrificeHierarchy:
    """
    Manages load shedding based on explicit sacrifice hierarchy.

    Key principles:
    1. Pre-defined priority order removes crisis decision burden
    2. Explicit documentation of what gets cut and why
    3. Automatic recovery in reverse order when capacity returns
    4. Audit trail of all sacrifice decisions
    """

    # Default sacrifice order (index = cut order, 0 = cut first)
    SACRIFICE_ORDER = [
        ActivityCategory.EDUCATION_OPTIONAL,
        ActivityCategory.ADMINISTRATION,
        ActivityCategory.RESEARCH,
        ActivityCategory.EDUCATION_CORE,
        ActivityCategory.CONTINUITY_OF_CARE,
        ActivityCategory.ACGME_REQUIREMENTS,
        # PATIENT_SAFETY is never in sacrifice order
    ]

    def __init__(self) -> None:
        self.current_level = LoadSheddingLevel.NORMAL
        self.level_activated_at: datetime | None = None
        self.activities: dict[UUID, Activity] = {}
        self.decisions_log: list[SacrificeDecision] = []
        self._suspended_activities: set[UUID] = set()

    def register_activity(self, activity: Activity) -> None:
        """Register an activity for load shedding consideration."""
        self.activities[activity.id] = activity

    def get_sacrificed_categories(
        self, level: LoadSheddingLevel
    ) -> list[ActivityCategory]:
        """Get categories that are sacrificed at a given level."""
        if level == LoadSheddingLevel.NORMAL:
            return []
        elif level == LoadSheddingLevel.YELLOW:
            return [ActivityCategory.EDUCATION_OPTIONAL]
        elif level == LoadSheddingLevel.ORANGE:
            return [
                ActivityCategory.EDUCATION_OPTIONAL,
                ActivityCategory.ADMINISTRATION,
                ActivityCategory.RESEARCH,
            ]
        elif level == LoadSheddingLevel.RED:
            return [
                ActivityCategory.EDUCATION_OPTIONAL,
                ActivityCategory.ADMINISTRATION,
                ActivityCategory.RESEARCH,
                ActivityCategory.EDUCATION_CORE,
            ]
        elif level == LoadSheddingLevel.BLACK:
            return [
                ActivityCategory.EDUCATION_OPTIONAL,
                ActivityCategory.ADMINISTRATION,
                ActivityCategory.RESEARCH,
                ActivityCategory.EDUCATION_CORE,
                ActivityCategory.CONTINUITY_OF_CARE,
            ]
        elif level == LoadSheddingLevel.CRITICAL:
            return [
                ActivityCategory.EDUCATION_OPTIONAL,
                ActivityCategory.ADMINISTRATION,
                ActivityCategory.RESEARCH,
                ActivityCategory.EDUCATION_CORE,
                ActivityCategory.CONTINUITY_OF_CARE,
                ActivityCategory.ACGME_REQUIREMENTS,
            ]
        return []

    def get_protected_categories(
        self, level: LoadSheddingLevel
    ) -> list[ActivityCategory]:
        """Get categories that are protected at a given level."""
        sacrificed = set(self.get_sacrificed_categories(level))
        all_categories = set(ActivityCategory)
        return sorted(all_categories - sacrificed, key=lambda c: c.value)

    def calculate_required_level(
        self,
        current_capacity: float,
        required_capacity: float,
    ) -> LoadSheddingLevel:
        """
        Calculate the load shedding level needed to match capacity.

        Args:
            current_capacity: Available faculty-hours
            required_capacity: Required faculty-hours for all activities

        Returns:
            The minimum level needed to fit within capacity
        """
        if current_capacity >= required_capacity:
            return LoadSheddingLevel.NORMAL

        # Calculate capacity at each level
        for level in LoadSheddingLevel:
            if level == LoadSheddingLevel.NORMAL:
                continue

            sacrificed_categories = set(self.get_sacrificed_categories(level))
            remaining_capacity = sum(
                a.faculty_hours
                for a in self.activities.values()
                if a.category not in sacrificed_categories
            )

            if remaining_capacity <= current_capacity:
                return level

        return LoadSheddingLevel.CRITICAL

    def shed_load(
        self,
        current_demand: list[Activity],
        available_capacity: float,
        reason: str = "",
        approved_by: str | None = None,
    ) -> tuple[list[Activity], list[Activity]]:
        """
        Remove activities until demand fits capacity.

        Uses the pre-defined sacrifice hierarchy to determine which activities
        to suspend. Activities are removed starting with least protected
        (EDUCATION_OPTIONAL) until demand fits available capacity.

        The key benefit: decisions are made by algorithm according to
        pre-agreed priorities, removing cognitive burden during crisis.

        Args:
            current_demand: List of Activity objects needing coverage.
            available_capacity: Available faculty-hours for the period.
            reason: Reason for shedding (recorded for audit trail).
            approved_by: Person approving the decision (for audit trail).

        Returns:
            tuple[list[Activity], list[Activity]]: A tuple containing:
                - kept_activities: Activities that will continue
                - sacrificed_activities: Activities being suspended

        Example:
            >>> hierarchy = SacrificeHierarchy()
            >>> kept, sacrificed = hierarchy.shed_load(
            ...     current_demand=activities,
            ...     available_capacity=100.0,
            ...     reason="PCS season understaffing",
            ...     approved_by="Dr. Chief"
            ... )
            >>> print(f"Suspended {len(sacrificed)} activities, freeing "
            ...       f"{sum(a.faculty_hours for a in sacrificed)} hours")
        """
        # Sort by sacrifice order (first to sacrifice = highest index in category)
        sorted_activities = sorted(
            current_demand,
            key=lambda a: (
                a.category.value,  # Higher category value = less protected
                not a.is_required,  # Required activities last within category
                a.faculty_hours,  # Smaller activities first
            ),
            reverse=True,  # So we pop from end (least protected first)
        )

        kept = []
        sacrificed = []
        current_load = 0.0

        # Build from most protected up
        for activity in reversed(sorted_activities):
            if current_load + activity.faculty_hours <= available_capacity:
                kept.append(activity)
                current_load += activity.faculty_hours
            else:
                # Cannot fit - sacrifice
                sacrificed.append(activity)
                self._suspended_activities.add(activity.id)

        # Log the decision
        if sacrificed:
            decision = SacrificeDecision(
                timestamp=datetime.now(),
                level=self.calculate_required_level(
                    available_capacity, sum(a.faculty_hours for a in current_demand)
                ),
                activities_suspended=[a.name for a in sacrificed],
                reason=reason,
                coverage_before=sum(a.faculty_hours for a in current_demand),
                coverage_after=current_load,
                approved_by=approved_by,
            )
            self.decisions_log.append(decision)

            logger.warning(
                f"Load shedding: {len(sacrificed)} activities suspended "
                f"({sum(a.faculty_hours for a in sacrificed):.1f} hours). "
                f"Reason: {reason}"
            )

        return kept, sacrificed

    def activate_level(
        self,
        level: LoadSheddingLevel,
        reason: str = "",
        approved_by: str | None = None,
    ) -> SacrificeDecision:
        """
        Activate a specific load shedding level.

        This suspends all activities in sacrificed categories and creates
        an audit record of the decision.

        Args:
            level: LoadSheddingLevel to activate (YELLOW, ORANGE, RED, BLACK, CRITICAL).
            reason: Description of why this level is being activated.
            approved_by: Person authorizing the level change.

        Example:
            >>> hierarchy = SacrificeHierarchy()
            >>> # Escalate to ORANGE: suspend admin, research, optional education
            >>> hierarchy.activate_level(
            ...     LoadSheddingLevel.ORANGE,
            ...     reason="Multiple faculty out with flu",
            ...     approved_by="Dr. Chief"
            ... )
        """
        if level == self.current_level:
            return

        previous_level = self.current_level
        self.current_level = level
        self.level_activated_at = datetime.now()

        sacrificed_categories = set(self.get_sacrificed_categories(level))

        suspended_names = []
        for activity in self.activities.values():
            if activity.category in sacrificed_categories:
                self._suspended_activities.add(activity.id)
                suspended_names.append(activity.name)

        decision = SacrificeDecision(
            timestamp=datetime.now(),
            level=level,
            activities_suspended=suspended_names,
            reason=reason,
            coverage_before=0.0,  # Would need context to calculate
            coverage_after=0.0,
            approved_by=approved_by,
            notes=f"Level changed from {previous_level.name} to {level.name}",
        )
        self.decisions_log.append(decision)

        logger.warning(
            f"Load shedding level activated: {level.name}. "
            f"Suspended categories: {[c.name for c in sacrificed_categories]}. "
            f"Reason: {reason}"
        )

    def deactivate_level(self, to_level: LoadSheddingLevel = LoadSheddingLevel.NORMAL) -> None:
        """
        Reduce load shedding level (restore services).

        Services are restored in reverse sacrifice order.
        """
        if to_level.value >= self.current_level.value:
            logger.info("Already at or below target level")
            return

        self.current_level = to_level
        new_sacrificed = set(self.get_sacrificed_categories(to_level))

        # Restore activities not in new sacrifice list
        restored = []
        for activity_id in list(self._suspended_activities):
            activity = self.activities.get(activity_id)
            if activity and activity.category not in new_sacrificed:
                self._suspended_activities.discard(activity_id)
                restored.append(activity.name)

        if restored:
            logger.info(
                f"Load shedding reduced to {to_level.name}. Restored: {restored}"
            )

    def is_activity_suspended(self, activity_id: UUID) -> bool:
        """Check if an activity is currently suspended."""
        return activity_id in self._suspended_activities

    def get_suspended_activities(self) -> list[Activity]:
        """Get list of currently suspended activities."""
        return [
            self.activities[aid]
            for aid in self._suspended_activities
            if aid in self.activities
        ]

    def get_active_activities(self) -> list[Activity]:
        """Get list of activities still active."""
        return [
            a
            for a in self.activities.values()
            if a.id not in self._suspended_activities
        ]

    def get_status(self) -> LoadSheddingStatus:
        """Get current load shedding status."""
        suspended = self.get_suspended_activities()
        active = self.get_active_activities()

        return LoadSheddingStatus(
            level=self.current_level,
            level_name=self.current_level.name,
            active_since=self.level_activated_at,
            activities_suspended=[a.name for a in suspended],
            activities_protected=[a.name for a in active],
            current_coverage=sum(a.faculty_hours for a in active),
            target_coverage=sum(a.faculty_hours for a in self.activities.values()),
            decisions_log=self.decisions_log[-10:],  # Last 10 decisions
        )

    def get_recovery_plan(self) -> list[dict]:
        """
        Get plan for recovering from current load shedding level.

        Returns a prioritized list of suspended activities in the order
        they should be restored as capacity becomes available.
        Activities are ordered by priority (most important first).

        Returns:
            list[dict]: Recovery plan with each activity containing:
                - activity: Activity name
                - category: Activity category name
                - hours_required: Faculty hours needed to restore
                - can_defer_further: Whether activity can be delayed more
                - max_deferral_days: Maximum days it can be deferred

        Example:
            >>> hierarchy = SacrificeHierarchy()
            >>> plan = hierarchy.get_recovery_plan()
            >>> for item in plan:
            ...     print(f"Restore {item['activity']}: {item['hours_required']} hours needed")
        """
        suspended = self.get_suspended_activities()

        # Sort by category (most important first = restore first)
        sorted_activities = sorted(suspended, key=lambda a: a.category.value)

        plan = []
        for activity in sorted_activities:
            plan.append(
                {
                    "activity": activity.name,
                    "category": activity.category.name,
                    "hours_required": activity.faculty_hours,
                    "can_defer_further": activity.can_be_deferred,
                    "max_deferral_days": activity.deferral_limit_days,
                }
            )

        return plan

    def get_category_summary(self) -> dict[str, dict]:
        """Get summary of activities by category."""
        summary = {}

        for category in ActivityCategory:
            activities = [a for a in self.activities.values() if a.category == category]
            suspended = [a for a in activities if a.id in self._suspended_activities]

            summary[category.name] = {
                "total_activities": len(activities),
                "total_hours": sum(a.faculty_hours for a in activities),
                "suspended_count": len(suspended),
                "suspended_hours": sum(a.faculty_hours for a in suspended),
                "is_protected": category
                in self.get_protected_categories(self.current_level),
                "sacrifice_order": (
                    self.SACRIFICE_ORDER.index(category)
                    if category in self.SACRIFICE_ORDER
                    else -1
                ),
            }

        return summary
