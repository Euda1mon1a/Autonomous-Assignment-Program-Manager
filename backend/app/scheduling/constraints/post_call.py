"""
Post-Call Assignment Constraints.

This module contains constraints for automatic post-call activity assignments
following overnight call (Sun-Thurs).

See docs/architecture/FACULTY_SCHEDULING_SPECIFICATION.md for full details.

Post-Call Rules:
    - After Sun-Thurs overnight call:
        - Next day AM: PCAT (Post-Call Attending)
        - Next day PM: DO (Direct Observation)
    - Friday/Saturday call handled by FMIT (different rules)

Classes:
    - PostCallAutoAssignmentConstraint: Auto-assign PCAT/DO after call

Activity Types:
    - PCAT: Post-Call Attending - supervising resident clinic while post-call
    - DO: Direct Observation - observing resident encounters for assessment
"""
import logging
from collections import defaultdict
from datetime import date, timedelta
from typing import Any, Optional

from .base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    HardConstraint,
    SchedulingContext,
)
from .fmit import is_sun_thurs

logger = logging.getLogger(__name__)


class PostCallAutoAssignmentConstraint(HardConstraint):
    """
    Automatically assigns PCAT (AM) and DO (PM) after overnight call.

    When faculty takes Sun-Thurs overnight call:
    - Next day AM block: Must be assigned PCAT (Post-Call Attending)
    - Next day PM block: Must be assigned DO (Direct Observation)

    This ensures:
    1. Post-call faculty has lighter duties (not regular clinic)
    2. Educational activities (DO) are scheduled appropriately
    3. Clinic coverage maintained with post-call attending

    Implementation:
    - Detects overnight call assignments on Sun-Thurs
    - Forces PCAT assignment for following AM block
    - Forces DO assignment for following PM block
    - Validates existing schedules for compliance
    """

    # Activity type identifiers
    PCAT_ACTIVITY = "PCAT"  # Post-Call Attending
    DO_ACTIVITY = "DO"       # Direct Observation

    def __init__(self) -> None:
        """Initialize post-call auto-assignment constraint."""
        super().__init__(
            name="PostCallAutoAssignment",
            constraint_type=ConstraintType.CALL,
            priority=ConstraintPriority.HIGH,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add post-call assignment constraints to CP-SAT model.

        For each Sun-Thurs overnight call assignment:
        - Force PCAT for next day AM
        - Force DO for next day PM
        """
        call_vars = variables.get("call_assignments", {})
        template_vars = variables.get("template_assignments", {})

        if not call_vars or not template_vars:
            return

        # Find PCAT and DO templates
        pcat_template_id = self._find_template_id(context, self.PCAT_ACTIVITY)
        do_template_id = self._find_template_id(context, self.DO_ACTIVITY)

        if not pcat_template_id or not do_template_id:
            logger.warning("PCAT or DO templates not found - post-call constraint inactive")
            return

        pcat_t_i = context.template_idx.get(pcat_template_id)
        do_t_i = context.template_idx.get(do_template_id)

        if pcat_t_i is None or do_t_i is None:
            return

        # Group blocks by date and time
        blocks_by_date_time = self._group_blocks_by_date_time(context)

        # For each faculty and Sun-Thurs date
        for faculty in context.faculty:
            f_i = context.resident_idx.get(faculty.id)
            if f_i is None:
                continue

            for block in context.blocks:
                # Only Sun-Thurs for overnight call
                if not is_sun_thurs(block.date):
                    continue

                b_i = context.block_idx[block.id]

                # Check if overnight call variable exists
                if (f_i, b_i, "overnight") not in call_vars:
                    continue

                call_var = call_vars[f_i, b_i, "overnight"]
                next_day = block.date + timedelta(days=1)

                # Find next day AM and PM blocks
                am_blocks = blocks_by_date_time.get((next_day, "AM"), [])
                pm_blocks = blocks_by_date_time.get((next_day, "PM"), [])

                # If on call => next day AM must be PCAT
                for am_block in am_blocks:
                    am_b_i = context.block_idx[am_block.id]
                    if (f_i, am_b_i, pcat_t_i) in template_vars:
                        # call_var == 1 => pcat_var == 1
                        model.AddImplication(call_var, template_vars[f_i, am_b_i, pcat_t_i])

                # If on call => next day PM must be DO
                for pm_block in pm_blocks:
                    pm_b_i = context.block_idx[pm_block.id]
                    if (f_i, pm_b_i, do_t_i) in template_vars:
                        # call_var == 1 => do_var == 1
                        model.AddImplication(call_var, template_vars[f_i, pm_b_i, do_t_i])

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add post-call assignment constraints to PuLP model."""
        call_vars = variables.get("call_assignments", {})
        template_vars = variables.get("template_assignments", {})

        if not call_vars or not template_vars:
            return

        pcat_template_id = self._find_template_id(context, self.PCAT_ACTIVITY)
        do_template_id = self._find_template_id(context, self.DO_ACTIVITY)

        if not pcat_template_id or not do_template_id:
            return

        pcat_t_i = context.template_idx.get(pcat_template_id)
        do_t_i = context.template_idx.get(do_template_id)

        if pcat_t_i is None or do_t_i is None:
            return

        blocks_by_date_time = self._group_blocks_by_date_time(context)
        constraint_count = 0

        for faculty in context.faculty:
            f_i = context.resident_idx.get(faculty.id)
            if f_i is None:
                continue

            for block in context.blocks:
                if not is_sun_thurs(block.date):
                    continue

                b_i = context.block_idx[block.id]
                if (f_i, b_i, "overnight") not in call_vars:
                    continue

                call_var = call_vars[f_i, b_i, "overnight"]
                next_day = block.date + timedelta(days=1)

                am_blocks = blocks_by_date_time.get((next_day, "AM"), [])
                pm_blocks = blocks_by_date_time.get((next_day, "PM"), [])

                # Implication as linear constraint: pcat >= call
                for am_block in am_blocks:
                    am_b_i = context.block_idx[am_block.id]
                    if (f_i, am_b_i, pcat_t_i) in template_vars:
                        model += (
                            template_vars[f_i, am_b_i, pcat_t_i] >= call_var,
                            f"post_call_pcat_{f_i}_{b_i}_{constraint_count}"
                        )
                        constraint_count += 1

                for pm_block in pm_blocks:
                    pm_b_i = context.block_idx[pm_block.id]
                    if (f_i, pm_b_i, do_t_i) in template_vars:
                        model += (
                            template_vars[f_i, pm_b_i, do_t_i] >= call_var,
                            f"post_call_do_{f_i}_{b_i}_{constraint_count}"
                        )
                        constraint_count += 1

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """
        Validate post-call assignments.

        Checks that faculty with Sun-Thurs overnight call have:
        - PCAT assigned for next day AM
        - DO assigned for next day PM
        """
        violations: list[ConstraintViolation] = []

        # Find overnight call assignments
        call_assignments = self._extract_call_assignments(assignments, context)

        if not call_assignments:
            return ConstraintResult(satisfied=True, violations=[])

        # Build lookups
        faculty_by_id = {f.id: f for f in context.faculty}
        block_by_id = {b.id: b for b in context.blocks}
        template_by_id = {t.id: t for t in context.templates}

        # Find PCAT and DO template IDs
        pcat_template_id = self._find_template_id(context, self.PCAT_ACTIVITY)
        do_template_id = self._find_template_id(context, self.DO_ACTIVITY)

        # Group regular assignments by person, date, time_of_day
        assignments_by_person_date_time = defaultdict(list)
        for a in assignments:
            block = block_by_id.get(a.block_id)
            if block and hasattr(block, 'time_of_day'):
                key = (a.person_id, block.date, block.time_of_day)
                assignments_by_person_date_time[key].append(a)

        # Check each Sun-Thurs call assignment
        for call_a in call_assignments:
            faculty = faculty_by_id.get(call_a.person_id)
            block = block_by_id.get(call_a.block_id)

            if not faculty or not block:
                continue

            if not is_sun_thurs(block.date):
                continue

            next_day = block.date + timedelta(days=1)

            # Check AM assignment
            am_assignments = assignments_by_person_date_time.get(
                (call_a.person_id, next_day, "AM"), []
            )
            has_pcat = any(
                a.rotation_template_id == pcat_template_id
                for a in am_assignments
            ) if pcat_template_id else False

            if not has_pcat and pcat_template_id:
                violations.append(ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity="HIGH",
                    message=f"{faculty.name} on call {block.date} missing PCAT assignment for {next_day} AM",
                    person_id=faculty.id,
                    block_id=call_a.block_id,
                    details={
                        "call_date": str(block.date),
                        "expected_pcat_date": str(next_day),
                        "time_of_day": "AM",
                    },
                ))

            # Check PM assignment
            pm_assignments = assignments_by_person_date_time.get(
                (call_a.person_id, next_day, "PM"), []
            )
            has_do = any(
                a.rotation_template_id == do_template_id
                for a in pm_assignments
            ) if do_template_id else False

            if not has_do and do_template_id:
                violations.append(ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity="HIGH",
                    message=f"{faculty.name} on call {block.date} missing DO assignment for {next_day} PM",
                    person_id=faculty.id,
                    block_id=call_a.block_id,
                    details={
                        "call_date": str(block.date),
                        "expected_do_date": str(next_day),
                        "time_of_day": "PM",
                    },
                ))

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )

    def _find_template_id(self, context: SchedulingContext, activity_name: str) -> Optional[Any]:
        """Find template ID by activity name or abbreviation."""
        for t in context.templates:
            # Check name
            if hasattr(t, 'name') and t.name.upper() == activity_name.upper():
                return t.id
            # Check abbreviation
            if hasattr(t, 'abbreviation') and t.abbreviation:
                if t.abbreviation.upper() == activity_name.upper():
                    return t.id
        return None

    def _group_blocks_by_date_time(self, context: SchedulingContext) -> dict[tuple[date, str], list[Any]]:
        """Group blocks by (date, time_of_day) for quick lookup."""
        result: dict[tuple[date, str], list[Any]] = defaultdict(list)
        for block in context.blocks:
            if hasattr(block, 'time_of_day'):
                key = (block.date, block.time_of_day)
                result[key].append(block)
        return result

    def _extract_call_assignments(self, assignments: list[Any], context: SchedulingContext) -> list[Any]:
        """
        Extract overnight call assignments from assignment list.

        Call assignments may be in a separate model (CallAssignment)
        or flagged within regular assignments.
        """
        call_assignments: list[Any] = []
        for a in assignments:
            # Check if this is a call assignment type
            if hasattr(a, 'call_type') and a.call_type == 'overnight':
                call_assignments.append(a)
            # Check existing_assignments in context
        # Also check context.existing_assignments for call data
        # This depends on how call assignments are stored
        return call_assignments
