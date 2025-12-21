"""
Temporal and Time-based Constraints.

This module contains constraints related to specific time periods,
days of the week, and scheduling patterns.

Classes:
    - WednesdayAMInternOnlyConstraint: Wednesday AM clinic for interns only (hard)
"""
import logging
from typing import Any

from .base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    HardConstraint,
    SchedulingContext,
)

logger = logging.getLogger(__name__)


class WednesdayAMInternOnlyConstraint(HardConstraint):
    """
    Ensures Wednesday morning clinic is staffed by interns (PGY-1) only.

    Wednesday morning is continuity clinic day for interns. This protected
    time allows them to maintain longitudinal patient relationships and
    should not be disrupted by PGY-2/3 resident assignments.

    Faculty supervision is still required per supervision ratios.

    Note: Rare exceptions may be needed - the constraint can be disabled
    for specific blocks if necessary.
    """

    WEDNESDAY = 2  # Python weekday: Monday=0, Tuesday=1, Wednesday=2

    def __init__(self) -> None:
        """Initialize the constraint."""
        super().__init__(
            name="WednesdayAMInternOnly",
            constraint_type=ConstraintType.ROTATION,
            priority=ConstraintPriority.HIGH,
        )

    def _is_wednesday_am(self, block: Any) -> bool:
        """Check if a block is Wednesday AM."""
        return (
            hasattr(block, 'date') and
            block.date.weekday() == self.WEDNESDAY and
            block.time_of_day == 'AM'
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Prevent non-intern assignments on Wednesday AM."""
        template_vars = variables.get("template_assignments", {})

        if not template_vars:
            return

        # Identify clinic templates
        clinic_template_ids = {
            t.id for t in context.templates
            if hasattr(t, 'activity_type') and t.activity_type == 'clinic'
        }

        if not clinic_template_ids:
            return

        # Get PGY levels for residents
        pgy_levels = {r.id: r.pgy_level for r in context.residents}

        # For Wednesday AM blocks, prevent non-PGY-1 clinic assignments
        for block in context.blocks:
            if not self._is_wednesday_am(block):
                continue

            b_i = context.block_idx[block.id]

            for template in context.templates:
                if template.id not in clinic_template_ids:
                    continue

                t_i = context.template_idx[template.id]

                for r in context.residents:
                    # Skip PGY-1 (they are allowed)
                    if pgy_levels.get(r.id) == 1:
                        continue

                    r_i = context.resident_idx[r.id]
                    if (r_i, b_i, t_i) in template_vars:
                        # Force non-intern to 0 on Wednesday AM clinic
                        model.Add(template_vars[r_i, b_i, t_i] == 0)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Prevent non-intern assignments on Wednesday AM using PuLP."""
        template_vars = variables.get("template_assignments", {})

        if not template_vars:
            return

        clinic_template_ids = {
            t.id for t in context.templates
            if hasattr(t, 'activity_type') and t.activity_type == 'clinic'
        }

        if not clinic_template_ids:
            return

        pgy_levels = {r.id: r.pgy_level for r in context.residents}

        for block in context.blocks:
            if not self._is_wednesday_am(block):
                continue

            b_i = context.block_idx[block.id]

            for template in context.templates:
                if template.id not in clinic_template_ids:
                    continue

                t_i = context.template_idx[template.id]

                for r in context.residents:
                    if pgy_levels.get(r.id) == 1:
                        continue

                    r_i = context.resident_idx[r.id]
                    if (r_i, b_i, t_i) in template_vars:
                        model += (
                            template_vars[(r_i, b_i, t_i)] == 0,
                            f"wed_am_intern_only_{r_i}_{b_i}_{t_i}"
                        )

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Check that Wednesday AM clinic has only interns."""
        violations: list[ConstraintViolation] = []

        # Build lookup tables
        clinic_template_ids = {
            t.id for t in context.templates
            if hasattr(t, 'activity_type') and t.activity_type == 'clinic'
        }

        if not clinic_template_ids:
            return ConstraintResult(satisfied=True, violations=[])

        pgy_levels = {r.id: r.pgy_level for r in context.residents}
        resident_names = {r.id: r.name for r in context.residents}
        block_info = {b.id: b for b in context.blocks}

        for a in assignments:
            # Only check clinic assignments
            if a.rotation_template_id not in clinic_template_ids:
                continue

            # Only check resident assignments (not faculty)
            if a.person_id not in pgy_levels:
                continue

            block = block_info.get(a.block_id)
            if not block or not self._is_wednesday_am(block):
                continue

            # Check if resident is NOT PGY-1
            pgy = pgy_levels.get(a.person_id)
            if pgy and pgy != 1:
                violations.append(ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity="HIGH",
                    message=f"PGY-{pgy} resident {resident_names.get(a.person_id, 'Unknown')} assigned to Wednesday AM clinic on {block.date}",
                    person_id=a.person_id,
                    block_id=a.block_id,
                    details={"pgy_level": pgy, "date": str(block.date)},
                ))

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )
