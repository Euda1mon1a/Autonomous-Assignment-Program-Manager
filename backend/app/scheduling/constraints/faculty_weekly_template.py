"""
Faculty Weekly Template Constraints.

This module enforces faculty weekly activity templates and overrides during
schedule generation. Faculty can define their default weekly patterns (templates)
and week-specific exceptions (overrides).

Locked slots (is_locked=True) are treated as HARD constraints - the solver
cannot override them. Unlocked slots with priority values are SOFT constraints
that add penalties for deviation.

Classes:
    - FacultyWeeklyTemplateConstraint: Mixed hard/soft constraint for faculty templates
"""

import logging
from collections import defaultdict
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from .base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    SoftConstraint,
    SchedulingContext,
)

logger = logging.getLogger(__name__)


class FacultyWeeklyTemplateConstraint(SoftConstraint):
    """
    Enforces faculty weekly activity templates and overrides.

    Faculty members can configure their default weekly patterns (templates) and
    create week-specific overrides. This constraint ensures the solver respects
    these preferences during schedule generation.

    Hard Constraints (is_locked=True):
    - Locked slots MUST be assigned the specified activity
    - If activity_id is None (cleared), the slot MUST remain empty
    - Used for institutional requirements (e.g., PD has GME on Monday AM)

    Soft Constraints (is_locked=False):
    - Priority 0-100 determines penalty weight for deviation
    - Higher priority = stronger preference = higher penalty for deviation
    - Used for preferences (e.g., APD prefers clinic on Tuesday PM)

    Template Resolution:
    1. Check for week-specific override first
    2. If no override, check for week-specific template (week_number match)
    3. If no week-specific, check for default template (week_number=NULL)
    """

    def __init__(
        self,
        templates: dict[UUID, list[dict]] | None = None,
        overrides: dict[UUID, dict[date, list[dict]]] | None = None,
        weight: float = 10.0,
    ) -> None:
        """
        Initialize the constraint.

        Args:
            templates: Mapping of person_id to list of template slot dicts.
                      Each slot has: day_of_week, time_of_day, week_number,
                      activity_id, is_locked, priority, notes.
            overrides: Mapping of person_id to dict of week_start -> list of
                      override dicts. Each override has: day_of_week, time_of_day,
                      activity_id, is_locked.
            weight: Base weight for soft constraint penalties.
        """
        super().__init__(
            name="FacultyWeeklyTemplate",
            constraint_type=ConstraintType.PREFERENCE,
            weight=weight,
            priority=ConstraintPriority.HIGH,
        )
        self._templates = templates or {}
        self._overrides = overrides or {}
        # Cache for resolved effective slots
        self._effective_cache: dict[tuple[UUID, date, int, str], dict | None] = {}

    def _get_week_start(self, d: date) -> date:
        """Get Monday of the week containing date d."""
        days_since_monday = d.weekday()
        return d - timedelta(days=days_since_monday)

    def _get_week_number(self, block_date: date, block_start: date | None) -> int:
        """
        Calculate week number (1-4) within a block rotation.

        Args:
            block_date: Date to calculate week for
            block_start: Start date of the block rotation

        Returns:
            Week number 1-4, cycling if rotation is longer than 4 weeks
        """
        if block_start is None:
            return 1

        days_diff = (block_date - block_start).days
        weeks_diff = days_diff // 7
        return (weeks_diff % 4) + 1

    def _get_effective_slot(
        self,
        person_id: UUID,
        block_date: date,
        day_of_week: int,
        time_of_day: str,
        week_number: int,
    ) -> dict | None:
        """
        Get the effective template/override slot for a faculty member.

        Resolution order:
        1. Week-specific override (takes precedence)
        2. Week-specific template (week_number matches)
        3. Default template (week_number=NULL)

        Args:
            person_id: Faculty member UUID
            block_date: Date of the block
            day_of_week: Day of week (0=Sunday, 6=Saturday)
            time_of_day: "AM" or "PM"
            week_number: Week number within block (1-4)

        Returns:
            Effective slot dict or None if no template defined
        """
        cache_key = (person_id, block_date, day_of_week, time_of_day)
        if cache_key in self._effective_cache:
            return self._effective_cache[cache_key]

        week_start = self._get_week_start(block_date)

        # Check for override first
        person_overrides = self._overrides.get(person_id, {})
        week_overrides = person_overrides.get(week_start, [])
        for override in week_overrides:
            if (
                override.get("day_of_week") == day_of_week
                and override.get("time_of_day") == time_of_day
            ):
                self._effective_cache[cache_key] = override
                return override

        # Check templates
        person_templates = self._templates.get(person_id, [])
        week_specific: dict | None = None
        default: dict | None = None

        for template in person_templates:
            if (
                template.get("day_of_week") != day_of_week
                or template.get("time_of_day") != time_of_day
            ):
                continue

            template_week = template.get("week_number")
            if template_week == week_number:
                week_specific = template
            elif template_week is None:
                default = template

        # Week-specific takes precedence over default
        result = week_specific or default
        self._effective_cache[cache_key] = result
        return result

    def _python_weekday_to_pattern(self, python_weekday: int) -> int:
        """
        Convert Python weekday to pattern convention.

        Python: 0=Monday, 6=Sunday
        Pattern: 0=Sunday, 6=Saturday

        Args:
            python_weekday: Python weekday (0-6)

        Returns:
            Pattern day of week (0-6)
        """
        return (python_weekday + 1) % 7

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add faculty template constraints to CP-SAT model.

        For faculty activity assignment variables:
        - Locked slots: Add hard constraint forcing activity assignment
        - Priority slots: Add soft constraint with weighted penalty

        Note: This assumes the solver has faculty activity decision variables.
        The variable structure depends on how faculty activities are modeled.
        """
        # Look for faculty activity variables
        # Common patterns: "faculty_activities", "faculty_slots", "slot_assignments"
        faculty_vars = variables.get("faculty_activities", {})
        if not faculty_vars:
            faculty_vars = variables.get("faculty_slots", {})
        if not faculty_vars:
            logger.debug("No faculty activity variables found for template constraints")
            return

        locked_count = 0
        soft_penalties = []

        for faculty in context.faculty:
            f_i = context.faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            for block in context.blocks:
                b_i = context.block_idx.get(block.id)
                if b_i is None:
                    continue

                # Convert Python weekday to pattern convention
                pattern_dow = self._python_weekday_to_pattern(block.date.weekday())

                # Get week number within block
                week_number = self._get_week_number(block.date, context.start_date)

                # Check both AM and PM
                for time_of_day in ["AM", "PM"]:
                    effective = self._get_effective_slot(
                        faculty.id,
                        block.date,
                        pattern_dow,
                        time_of_day,
                        week_number,
                    )
                    if effective is None:
                        continue

                    is_locked = effective.get("is_locked", False)
                    activity_id = effective.get("activity_id")
                    priority = effective.get("priority", 50)

                    # Variable key depends on model structure
                    # Typical: (faculty_idx, block_idx, activity_idx, time_of_day)
                    var_key = (f_i, b_i, time_of_day)

                    if is_locked:
                        # Hard constraint: must assign this activity
                        if activity_id:
                            a_i = context.activity_idx.get(activity_id)
                            if a_i is not None and (*var_key, a_i) in faculty_vars:
                                model.Add(faculty_vars[(*var_key, a_i)] == 1)
                                locked_count += 1
                        else:
                            # Locked to empty - block all activities
                            for activity in context.activities:
                                a_i = context.activity_idx.get(activity.id)
                                if a_i is not None and (*var_key, a_i) in faculty_vars:
                                    model.Add(faculty_vars[(*var_key, a_i)] == 0)
                                    locked_count += 1
                    elif activity_id and priority > 0:
                        # Soft constraint: prefer this activity based on priority
                        a_i = context.activity_idx.get(activity_id)
                        if a_i is not None and (*var_key, a_i) in faculty_vars:
                            # Create indicator for deviation
                            deviation = model.NewBoolVar(
                                f"template_dev_{f_i}_{b_i}_{time_of_day}_{a_i}"
                            )
                            # deviation = 1 if NOT assigned to preferred activity
                            model.Add(faculty_vars[(*var_key, a_i)] == 0).OnlyEnforceIf(
                                deviation
                            )
                            model.Add(faculty_vars[(*var_key, a_i)] == 1).OnlyEnforceIf(
                                deviation.Not()
                            )

                            # Weight by priority (higher priority = higher penalty)
                            penalty_weight = int(self.weight * (priority / 100.0))
                            soft_penalties.append((deviation, penalty_weight))

        # Add soft penalties to objective if any
        if soft_penalties:
            objective_var = variables.get("objective")
            if objective_var is not None and hasattr(objective_var, "append"):
                for deviation, weight in soft_penalties:
                    objective_var.append((deviation, weight))

        logger.debug(
            f"Added {locked_count} locked slots, {len(soft_penalties)} soft preferences"
        )

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add faculty template constraints to PuLP model."""
        faculty_vars = variables.get("faculty_activities", {})
        if not faculty_vars:
            faculty_vars = variables.get("faculty_slots", {})
        if not faculty_vars:
            return

        constraint_count = 0

        for faculty in context.faculty:
            f_i = context.faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            for block in context.blocks:
                b_i = context.block_idx.get(block.id)
                if b_i is None:
                    continue

                pattern_dow = self._python_weekday_to_pattern(block.date.weekday())
                week_number = self._get_week_number(block.date, context.start_date)

                for time_of_day in ["AM", "PM"]:
                    effective = self._get_effective_slot(
                        faculty.id,
                        block.date,
                        pattern_dow,
                        time_of_day,
                        week_number,
                    )
                    if effective is None:
                        continue

                    is_locked = effective.get("is_locked", False)
                    activity_id = effective.get("activity_id")

                    if not is_locked:
                        continue  # PuLP doesn't have built-in soft constraint support

                    var_key = (f_i, b_i, time_of_day)

                    if activity_id:
                        a_i = context.activity_idx.get(activity_id)
                        if a_i is not None and (*var_key, a_i) in faculty_vars:
                            model += (
                                faculty_vars[(*var_key, a_i)] == 1,
                                f"locked_template_{f_i}_{b_i}_{time_of_day}_{constraint_count}",
                            )
                            constraint_count += 1
                    else:
                        for activity in context.activities:
                            a_i = context.activity_idx.get(activity.id)
                            if a_i is not None and (*var_key, a_i) in faculty_vars:
                                model += (
                                    faculty_vars[(*var_key, a_i)] == 0,
                                    f"locked_empty_{f_i}_{b_i}_{time_of_day}_{constraint_count}",
                                )
                                constraint_count += 1

        logger.debug(f"Added {constraint_count} PuLP template constraints")

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """
        Validate assignments against faculty templates.

        Checks each faculty assignment to ensure:
        - Locked slots have the correct activity (or are empty if activity_id=None)
        - Unlocked slots are tracked for penalty calculation

        Args:
            assignments: List of assignment objects (faculty-block-activity)
            context: Scheduling context

        Returns:
            ConstraintResult with violations for locked slot breaches
            and penalty for soft preference deviations.
        """
        violations: list[ConstraintViolation] = []
        total_penalty = 0.0

        faculty_by_id = {f.id: f for f in context.faculty}
        block_by_id = {b.id: b for b in context.blocks}
        activity_by_id = {a.id: a for a in context.activities}

        # Group assignments by (faculty, block, time_of_day) for comparison
        assigned: dict[tuple[UUID, UUID, str], UUID | None] = {}
        for assignment in assignments:
            faculty_id = getattr(assignment, "person_id", None)
            block_id = getattr(assignment, "block_id", None)
            activity_id = getattr(assignment, "activity_id", None)
            time_of_day = getattr(assignment, "time_of_day", None)

            if faculty_id and block_id and time_of_day:
                key = (faculty_id, block_id, time_of_day)
                assigned[key] = activity_id

        # Check templates against assignments
        for faculty in context.faculty:
            for block in context.blocks:
                pattern_dow = self._python_weekday_to_pattern(block.date.weekday())
                week_number = self._get_week_number(block.date, context.start_date)

                for time_of_day in ["AM", "PM"]:
                    effective = self._get_effective_slot(
                        faculty.id,
                        block.date,
                        pattern_dow,
                        time_of_day,
                        week_number,
                    )
                    if effective is None:
                        continue

                    is_locked = effective.get("is_locked", False)
                    expected_activity_id = effective.get("activity_id")
                    priority = effective.get("priority", 50)

                    key = (faculty.id, block.id, time_of_day)
                    actual_activity_id = assigned.get(key)

                    # Compare expected vs actual
                    if is_locked:
                        if actual_activity_id != expected_activity_id:
                            expected_name = "empty"
                            actual_name = "empty"
                            if expected_activity_id:
                                act = activity_by_id.get(expected_activity_id)
                                if act:
                                    expected_name = getattr(
                                        act, "name", str(expected_activity_id)
                                    )
                            if actual_activity_id:
                                act = activity_by_id.get(actual_activity_id)
                                if act:
                                    actual_name = getattr(
                                        act, "name", str(actual_activity_id)
                                    )

                            faculty_name = getattr(faculty, "name", str(faculty.id))
                            violations.append(
                                ConstraintViolation(
                                    constraint_name=self.name,
                                    constraint_type=self.constraint_type,
                                    severity="CRITICAL",
                                    message=(
                                        f"{faculty_name} has locked '{expected_name}' on "
                                        f"{block.date} {time_of_day}, but assigned '{actual_name}'"
                                    ),
                                    person_id=faculty.id,
                                    block_id=block.id,
                                    details={
                                        "date": str(block.date),
                                        "time_of_day": time_of_day,
                                        "expected_activity": str(expected_activity_id),
                                        "actual_activity": str(actual_activity_id),
                                        "is_locked": True,
                                    },
                                )
                            )
                    else:
                        # Soft constraint - calculate penalty
                        if (
                            expected_activity_id
                            and actual_activity_id != expected_activity_id
                        ):
                            # Add penalty based on priority
                            deviation_penalty = self.weight * (priority / 100.0)
                            total_penalty += deviation_penalty

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
            penalty=total_penalty,
        )

    def clear_cache(self) -> None:
        """Clear the effective slot cache. Call when templates/overrides change."""
        self._effective_cache.clear()
