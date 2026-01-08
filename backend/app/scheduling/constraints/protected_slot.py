"""
Protected Slot Constraints.

This module enforces protected weekly pattern slots that coordinators have locked.
Protected slots (is_protected=True) cannot be overridden by the solver.

Examples of protected slots:
- Wednesday PM lecture time (LEC) - institutional protected education
- Weekend off (W) - for rotations without weekend work

Classes:
    - ProtectedSlotConstraint: Hard constraint that blocks solver from overriding protected patterns
"""

import logging
from collections import defaultdict
from datetime import date
from typing import Any
from uuid import UUID

from .base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    HardConstraint,
    SchedulingContext,
)

logger = logging.getLogger(__name__)


class ProtectedSlotConstraint(HardConstraint):
    """
    Enforces protected slots from weekly patterns.

    Coordinators can mark certain slots as protected (is_protected=True) in the
    weekly pattern editor. These slots represent locked institutional requirements:
    - Wednesday PM = lecture (all residents, all rotations)
    - Saturday/Sunday = off (for rotations without weekend work)

    The solver must respect these protected slots by:
    1. Pre-filling the slot with the protected activity
    2. Blocking any conflicting assignments

    Protected patterns are loaded per rotation template and applied to all
    residents assigned to that rotation.
    """

    def __init__(
        self,
        protected_patterns: dict[UUID, list[dict]] | None = None,
    ) -> None:
        """
        Initialize the constraint.

        Args:
            protected_patterns: Mapping of rotation_template_id to list of protected
                pattern dicts with keys: day_of_week, time_of_day, activity_type,
                week_number (optional), linked_template_id (optional).
                If None, patterns must be in context.
        """
        super().__init__(
            name="ProtectedSlot",
            constraint_type=ConstraintType.AVAILABILITY,
            priority=ConstraintPriority.CRITICAL,
        )
        self._protected_patterns = protected_patterns or {}

    def get_protected_patterns(self, template_id: UUID) -> list[dict]:
        """Get protected patterns for a rotation template."""
        return self._protected_patterns.get(template_id, [])

    def _is_protected_slot(
        self,
        block: Any,
        pattern: dict,
    ) -> bool:
        """
        Check if a block matches a protected pattern.

        Args:
            block: Block object with date and time_of_day
            pattern: Protected pattern dict with day_of_week, time_of_day, week_number

        Returns:
            True if block matches the protected pattern
        """
        if not hasattr(block, "date") or not hasattr(block, "time_of_day"):
            return False

        # Check day of week (0=Monday through 6=Sunday in Python, pattern may use 0=Sunday)
        block_dow = block.date.weekday()  # Python: 0=Monday
        pattern_dow = pattern.get("day_of_week")

        # Convert if pattern uses Sunday=0 convention
        # Our weekly_pattern uses: 0=Sunday, 1=Monday, ..., 6=Saturday
        # Python weekday() uses: 0=Monday, ..., 6=Sunday
        # Convert pattern to Python convention
        if pattern_dow == 0:
            pattern_dow_python = 6  # Sunday
        else:
            pattern_dow_python = pattern_dow - 1  # Shift others

        if block_dow != pattern_dow_python:
            return False

        # Check time of day
        if block.time_of_day != pattern.get("time_of_day"):
            return False

        # Check week number if specified (1-4 for week-specific patterns)
        pattern_week = pattern.get("week_number")
        if pattern_week is not None:
            # Calculate which week of the block this is
            # Blocks are organized in 4-week rotations
            # We need to determine which week (1-4) this block falls into
            block_week = getattr(block, "week_number", None)
            if block_week is not None and block_week != pattern_week:
                return False

        return True

    def _get_conflicting_templates(
        self,
        protected_activity: str,
        context: SchedulingContext,
    ) -> set[UUID]:
        """
        Get template IDs that conflict with a protected activity.

        If slot is protected for 'lecture', any non-lecture template assignment
        would be a conflict.

        Args:
            protected_activity: Activity type of the protected slot
            context: Scheduling context with templates

        Returns:
            Set of template IDs that would conflict with this protected slot
        """
        conflicting: set[UUID] = set()
        for template in context.templates:
            # If protected slot is for a specific activity, block all others
            # e.g., if slot is 'lecture', block 'clinic', 'inpatient', etc.
            if hasattr(template, "activity_type"):
                if template.activity_type != protected_activity:
                    conflicting.add(template.id)
        return conflicting

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add protected slot constraints to CP-SAT model.

        For each protected pattern:
        - Find all blocks that match the pattern (day/time/week)
        - Block assignments to conflicting templates on those blocks
        """
        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            logger.debug("No template_assignments variables found")
            return

        blocked_count = 0

        # Process each rotation template's protected patterns
        for template_id, patterns in self._protected_patterns.items():
            if not patterns:
                continue

            # Get residents who might be on this rotation
            # For now, apply to all residents (conservative approach)
            # In practice, should check block assignments

            for pattern in patterns:
                protected_activity = pattern.get("activity_type", "")
                if not protected_activity:
                    continue

                # Get templates that conflict with this protected activity
                conflicting = self._get_conflicting_templates(
                    protected_activity, context
                )

                for resident in context.residents:
                    r_i = context.resident_idx.get(resident.id)
                    if r_i is None:
                        continue

                    for block in context.blocks:
                        if not self._is_protected_slot(block, pattern):
                            continue

                        b_i = context.block_idx.get(block.id)
                        if b_i is None:
                            continue

                        # Block all conflicting template assignments
                        for conflict_id in conflicting:
                            t_i = context.template_idx.get(conflict_id)
                            if t_i is not None and (r_i, b_i, t_i) in template_vars:
                                model.Add(template_vars[r_i, b_i, t_i] == 0)
                                blocked_count += 1

        logger.debug(f"Blocked {blocked_count} assignments on protected slots")

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add protected slot constraints to PuLP model."""
        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        constraint_count = 0

        for template_id, patterns in self._protected_patterns.items():
            if not patterns:
                continue

            for pattern in patterns:
                protected_activity = pattern.get("activity_type", "")
                if not protected_activity:
                    continue

                conflicting = self._get_conflicting_templates(
                    protected_activity, context
                )

                for resident in context.residents:
                    r_i = context.resident_idx.get(resident.id)
                    if r_i is None:
                        continue

                    for block in context.blocks:
                        if not self._is_protected_slot(block, pattern):
                            continue

                        b_i = context.block_idx.get(block.id)
                        if b_i is None:
                            continue

                        for conflict_id in conflicting:
                            t_i = context.template_idx.get(conflict_id)
                            if t_i is not None and (r_i, b_i, t_i) in template_vars:
                                model += (
                                    template_vars[(r_i, b_i, t_i)] == 0,
                                    f"protected_slot_{r_i}_{b_i}_{constraint_count}",
                                )
                                constraint_count += 1

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """
        Validate that no assignments violate protected slots.

        Checks each assignment to ensure it doesn't place a conflicting
        activity on a protected slot.
        """
        violations: list[ConstraintViolation] = []

        resident_by_id = {r.id: r for r in context.residents}
        block_by_id = {b.id: b for b in context.blocks}
        template_by_id = {t.id: t for t in context.templates}

        for assignment in assignments:
            resident = resident_by_id.get(assignment.person_id)
            if not resident:
                continue

            block = block_by_id.get(assignment.block_id)
            if not block:
                continue

            assigned_template = template_by_id.get(assignment.rotation_template_id)
            if not assigned_template:
                continue

            assigned_activity = getattr(assigned_template, "activity_type", "")

            # Check if any protected pattern is violated
            for template_id, patterns in self._protected_patterns.items():
                for pattern in patterns:
                    if not self._is_protected_slot(block, pattern):
                        continue

                    protected_activity = pattern.get("activity_type", "")
                    if not protected_activity:
                        continue

                    # Violation if assigned activity != protected activity
                    if assigned_activity != protected_activity:
                        resident_name = getattr(resident, "name", str(resident.id))
                        violations.append(
                            ConstraintViolation(
                                constraint_name=self.name,
                                constraint_type=self.constraint_type,
                                severity="CRITICAL",
                                message=(
                                    f"{resident_name} assigned to '{assigned_activity}' "
                                    f"on protected '{protected_activity}' slot "
                                    f"({block.date} {block.time_of_day})"
                                ),
                                person_id=resident.id,
                                block_id=block.id,
                                details={
                                    "date": str(block.date),
                                    "time_of_day": block.time_of_day,
                                    "protected_activity": protected_activity,
                                    "assigned_activity": assigned_activity,
                                },
                            )
                        )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )
