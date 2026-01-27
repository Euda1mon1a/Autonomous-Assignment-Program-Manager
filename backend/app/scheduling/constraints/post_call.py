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
from typing import Any

from .base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    SchedulingContext,
    SoftConstraint,
)
from .fmit import is_sun_thurs

logger = logging.getLogger(__name__)


class PostCallAutoAssignmentConstraint(SoftConstraint):
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
    DO_ACTIVITY = "DO"  # Direct Observation
    DEFAULT_WEIGHT = 35.0

    def __init__(self, weight: float = DEFAULT_WEIGHT) -> None:
        """Initialize post-call auto-assignment constraint."""
        super().__init__(
            name="PostCallAutoAssignment",
            constraint_type=ConstraintType.CALL,
            weight=weight,
            priority=ConstraintPriority.HIGH,
        )

    def _is_exempt_block(
        self,
        faculty_id: Any,
        block: Any,
        context: SchedulingContext,
    ) -> bool:
        """Return True if the next-day block should be exempt from post-call."""
        locked_blocks = getattr(context, "locked_blocks", set())
        if (faculty_id, block.id) in locked_blocks:
            return True
        availability = getattr(context, "availability", {}) or {}
        block_avail = availability.get(faculty_id, {}).get(block.id)
        if block_avail and not block_avail.get("available", True):
            return True
        return False

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add post-call assignment constraints to CP-SAT model.

        For each Sun-Thurs overnight call assignment:
        - Penalize missing PCAT for next day AM (soft)
        - Penalize missing DO for next day PM (soft)
        """
        call_vars = variables.get("call_assignments", {})
        faculty_template_vars = variables.get("faculty_template_assignments", {})
        objective_terms = variables.get("objective_terms", [])

        if not call_vars or not faculty_template_vars:
            return

        # Find PCAT and DO templates
        pcat_template_id = self._find_template_id(context, self.PCAT_ACTIVITY)
        do_template_id = self._find_template_id(context, self.DO_ACTIVITY)

        if not pcat_template_id or not do_template_id:
            logger.warning(
                "PCAT or DO templates not found - post-call constraint inactive"
            )
            return

        pcat_t_i = context.template_idx.get(pcat_template_id)
        do_t_i = context.template_idx.get(do_template_id)

        if pcat_t_i is None or do_t_i is None:
            return

        # Group blocks by date and time
        blocks_by_date_time = self._group_blocks_by_date_time(context)

        call_eligible_faculty = getattr(
            context, "call_eligible_faculty", context.faculty
        )
        call_faculty_by_idx = {i: fac for i, fac in enumerate(call_eligible_faculty)}
        block_by_idx = {context.block_idx[b.id]: b for b in context.blocks}
        # For each call variable, penalize missing next-day PCAT/DO
        for (call_f_i, b_i, call_type), call_var in call_vars.items():
            if call_type != "overnight":
                continue

            block = block_by_idx.get(b_i)
            if not block or not is_sun_thurs(block.date):
                continue

            faculty = call_faculty_by_idx.get(call_f_i)
            if not faculty:
                continue

            f_i = context.faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            next_day = block.date + timedelta(days=1)

            # Find next day AM and PM blocks
            am_blocks = blocks_by_date_time.get((next_day, "AM"), [])
            pm_blocks = blocks_by_date_time.get((next_day, "PM"), [])

            # If on call => next day AM should be PCAT (soft)
            am_has_var = False
            for am_block in am_blocks:
                if self._is_exempt_block(faculty.id, am_block, context):
                    am_has_var = False
                    am_blocks = []
                    break
                am_b_i = context.block_idx[am_block.id]
                key = (f_i, am_b_i, pcat_t_i)
                if key in faculty_template_vars:
                    am_has_var = True
            if am_blocks:
                if am_has_var:
                    pcat_vars = [
                        faculty_template_vars[(f_i, context.block_idx[b.id], pcat_t_i)]
                        for b in am_blocks
                        if (f_i, context.block_idx[b.id], pcat_t_i)
                        in faculty_template_vars
                    ]
                    shortfall = model.NewIntVar(
                        0,
                        1,
                        f"post_call_pcat_shortfall_{f_i}_{b_i}",
                    )
                    model.Add(sum(pcat_vars) + shortfall >= call_var)
                    objective_terms.append((shortfall, int(self.weight)))
                else:
                    objective_terms.append((call_var, int(self.weight)))

            # If on call => next day PM should be DO (soft)
            pm_has_var = False
            for pm_block in pm_blocks:
                if self._is_exempt_block(faculty.id, pm_block, context):
                    pm_has_var = False
                    pm_blocks = []
                    break
                pm_b_i = context.block_idx[pm_block.id]
                key = (f_i, pm_b_i, do_t_i)
                if key in faculty_template_vars:
                    pm_has_var = True
            if pm_blocks:
                if pm_has_var:
                    do_vars = [
                        faculty_template_vars[(f_i, context.block_idx[b.id], do_t_i)]
                        for b in pm_blocks
                        if (f_i, context.block_idx[b.id], do_t_i)
                        in faculty_template_vars
                    ]
                    shortfall = model.NewIntVar(
                        0,
                        1,
                        f"post_call_do_shortfall_{f_i}_{b_i}",
                    )
                    model.Add(sum(do_vars) + shortfall >= call_var)
                    objective_terms.append((shortfall, int(self.weight)))
                else:
                    objective_terms.append((call_var, int(self.weight)))

        variables["objective_terms"] = objective_terms

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add post-call assignment constraints to PuLP model (soft)."""
        call_vars = variables.get("call_assignments", {})
        faculty_template_vars = variables.get("faculty_template_assignments", {})
        objective_terms = variables.get("objective_terms", [])

        if not call_vars or not faculty_template_vars:
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

        call_eligible_faculty = getattr(
            context, "call_eligible_faculty", context.faculty
        )
        call_faculty_by_idx = {i: fac for i, fac in enumerate(call_eligible_faculty)}
        block_by_idx = {context.block_idx[b.id]: b for b in context.blocks}
        for (call_f_i, b_i, call_type), call_var in call_vars.items():
            if call_type != "overnight":
                continue

            block = block_by_idx.get(b_i)
            if not block or not is_sun_thurs(block.date):
                continue

            faculty = call_faculty_by_idx.get(call_f_i)
            if not faculty:
                continue

            f_i = context.faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            next_day = block.date + timedelta(days=1)

            am_blocks = blocks_by_date_time.get((next_day, "AM"), [])
            pm_blocks = blocks_by_date_time.get((next_day, "PM"), [])

            am_has_var = False
            for am_block in am_blocks:
                if self._is_exempt_block(faculty.id, am_block, context):
                    am_has_var = False
                    am_blocks = []
                    break
                am_b_i = context.block_idx[am_block.id]
                key = (f_i, am_b_i, pcat_t_i)
                if key in faculty_template_vars:
                    am_has_var = True
            if am_blocks:
                if am_has_var:
                    import pulp

                    pcat_vars = [
                        faculty_template_vars[(f_i, context.block_idx[b.id], pcat_t_i)]
                        for b in am_blocks
                        if (f_i, context.block_idx[b.id], pcat_t_i)
                        in faculty_template_vars
                    ]
                    shortfall = pulp.LpVariable(
                        f"post_call_pcat_shortfall_{f_i}_{b_i}",
                        lowBound=0,
                        upBound=1,
                        cat=pulp.LpInteger,
                    )
                    model += (
                        pulp.lpSum(pcat_vars) + shortfall >= call_var,
                        f"post_call_pcat_soft_{f_i}_{b_i}_{constraint_count}",
                    )
                    objective_terms.append((shortfall, int(self.weight)))
                    constraint_count += 1
                else:
                    objective_terms.append((call_var, int(self.weight)))

            pm_has_var = False
            for pm_block in pm_blocks:
                if self._is_exempt_block(faculty.id, pm_block, context):
                    pm_has_var = False
                    pm_blocks = []
                    break
                pm_b_i = context.block_idx[pm_block.id]
                key = (f_i, pm_b_i, do_t_i)
                if key in faculty_template_vars:
                    pm_has_var = True
            if pm_blocks:
                if pm_has_var:
                    import pulp

                    do_vars = [
                        faculty_template_vars[(f_i, context.block_idx[b.id], do_t_i)]
                        for b in pm_blocks
                        if (f_i, context.block_idx[b.id], do_t_i)
                        in faculty_template_vars
                    ]
                    shortfall = pulp.LpVariable(
                        f"post_call_do_shortfall_{f_i}_{b_i}",
                        lowBound=0,
                        upBound=1,
                        cat=pulp.LpInteger,
                    )
                    model += (
                        pulp.lpSum(do_vars) + shortfall >= call_var,
                        f"post_call_do_soft_{f_i}_{b_i}_{constraint_count}",
                    )
                    objective_terms.append((shortfall, int(self.weight)))
                    constraint_count += 1
                else:
                    objective_terms.append((call_var, int(self.weight)))

        variables["objective_terms"] = objective_terms

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """
        Validate post-call assignments.

        Checks that faculty with Sun-Thurs overnight call have:
        - PCAT assigned for next day AM (soft)
        - DO assigned for next day PM (soft)
        """
        violations: list[ConstraintViolation] = []
        total_penalty = 0.0

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
            if block and hasattr(block, "time_of_day"):
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
            am_block = next(
                (
                    b
                    for b in context.blocks
                    if b.date == next_day and b.time_of_day == "AM"
                ),
                None,
            )
            has_pcat = (
                any(a.rotation_template_id == pcat_template_id for a in am_assignments)
                if pcat_template_id
                else False
            )

            if (
                not has_pcat
                and pcat_template_id
                and am_block
                and not self._is_exempt_block(faculty.id, am_block, context)
            ):
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="MEDIUM",
                        message=f"{faculty.name} on call {block.date} missing PCAT assignment for {next_day} AM",
                        person_id=faculty.id,
                        block_id=call_a.block_id,
                        details={
                            "call_date": str(block.date),
                            "expected_pcat_date": str(next_day),
                            "time_of_day": "AM",
                        },
                    )
                )

            # Check PM assignment
            pm_assignments = assignments_by_person_date_time.get(
                (call_a.person_id, next_day, "PM"), []
            )
            pm_block = next(
                (
                    b
                    for b in context.blocks
                    if b.date == next_day and b.time_of_day == "PM"
                ),
                None,
            )
            has_do = (
                any(a.rotation_template_id == do_template_id for a in pm_assignments)
                if do_template_id
                else False
            )

            if (
                not has_do
                and do_template_id
                and pm_block
                and not self._is_exempt_block(faculty.id, pm_block, context)
            ):
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="MEDIUM",
                        message=f"{faculty.name} on call {block.date} missing DO assignment for {next_day} PM",
                        person_id=faculty.id,
                        block_id=call_a.block_id,
                        details={
                            "call_date": str(block.date),
                            "expected_do_date": str(next_day),
                            "time_of_day": "PM",
                        },
                    )
                )

        if violations:
            total_penalty = self.get_penalty(len(violations))

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
            penalty=total_penalty,
        )

    def _find_template_id(
        self, context: SchedulingContext, activity_name: str
    ) -> Any | None:
        """Find template ID by activity name or abbreviation."""
        target = activity_name.upper()
        for t in context.templates:
            # Check name
            name = (t.name or "").upper() if hasattr(t, "name") else ""
            if name == target:
                return t.id
            # Check abbreviation
            abbrev = (
                (t.abbreviation or "").upper() if hasattr(t, "abbreviation") else ""
            )
            if abbrev == target:
                return t.id

        # Accept AM/PM suffix variants (e.g., PCAT-AM, DO-PM) for post-call templates.
        if target in {"PCAT", "DO"}:
            for t in context.templates:
                name = (t.name or "").upper() if hasattr(t, "name") else ""
                abbrev = (
                    (t.abbreviation or "").upper() if hasattr(t, "abbreviation") else ""
                )
                if name.startswith(target) or abbrev.startswith(target):
                    return t.id
        return None

    def _group_blocks_by_date_time(
        self, context: SchedulingContext
    ) -> dict[tuple[date, str], list[Any]]:
        """Group blocks by (date, time_of_day) for quick lookup."""
        result: dict[tuple[date, str], list[Any]] = defaultdict(list)
        for block in context.blocks:
            if hasattr(block, "time_of_day"):
                key = (block.date, block.time_of_day)
                result[key].append(block)
        return result

    def _extract_call_assignments(
        self, assignments: list[Any], context: SchedulingContext
    ) -> list[Any]:
        """
        Extract overnight call assignments from assignment list.

        Call assignments may be in a separate model (CallAssignment)
        or flagged within regular assignments.
        """
        call_assignments: list[Any] = []
        for a in assignments:
            # Check if this is a call assignment type
            if hasattr(a, "call_type") and a.call_type == "overnight":
                call_assignments.append(a)
            # Check existing_assignments in context
        # Also check context.existing_assignments for call data
        # This depends on how call assignments are stored
        return call_assignments
