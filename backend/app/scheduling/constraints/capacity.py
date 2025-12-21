"""
Capacity and Coverage Constraints.

This module contains constraints related to clinic capacity limits,
physical space restrictions, and coverage optimization.

Classes:
    - OnePersonPerBlockConstraint: Max one primary resident per block (hard)
    - ClinicCapacityConstraint: Rotation template capacity limits (hard)
    - MaxPhysiciansInClinicConstraint: Physical space limits (hard)
    - CoverageConstraint: Maximize block coverage (soft)
"""
import logging
from collections import defaultdict
from typing import Any

from .base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    HardConstraint,
    SchedulingContext,
    SoftConstraint,
)

logger = logging.getLogger(__name__)


class OnePersonPerBlockConstraint(HardConstraint):
    """
    Ensures at most one primary resident assigned per block.
    (Faculty supervision is separate)
    """

    def __init__(self, max_per_block: int = 1) -> None:
        super().__init__(
            name="OnePersonPerBlock",
            constraint_type=ConstraintType.CAPACITY,
            priority=ConstraintPriority.CRITICAL,
        )
        self.max_per_block: int = max_per_block

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """At most max_per_block residents per block."""
        x = variables.get("assignments", {})

        for block in context.blocks:
            b_i = context.block_idx[block.id]
            resident_vars = [
                x[context.resident_idx[r.id], b_i]
                for r in context.residents
                if (context.resident_idx[r.id], b_i) in x
            ]
            if resident_vars:
                model.Add(sum(resident_vars) <= self.max_per_block)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """At most max_per_block residents per block."""
        import pulp
        x = variables.get("assignments", {})

        for block in context.blocks:
            b_i = context.block_idx[block.id]
            resident_vars = [
                x[context.resident_idx[r.id], b_i]
                for r in context.residents
                if (context.resident_idx[r.id], b_i) in x
            ]
            if resident_vars:
                model += (
                    pulp.lpSum(resident_vars) <= self.max_per_block,
                    f"max_per_block_{b_i}"
                )

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Check for multiple primary assignments per block."""
        violations: list[ConstraintViolation] = []
        block_counts: dict[Any, int] = defaultdict(int)

        for assignment in assignments:
            if assignment.role == "primary":
                block_counts[assignment.block_id] += 1

        for block_id, count in block_counts.items():
            if count > self.max_per_block:
                violations.append(ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity="CRITICAL",
                    message=f"Block has {count} primary assignments (max: {self.max_per_block})",
                    block_id=block_id,
                    details={"count": count, "max": self.max_per_block},
                ))

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )


class ClinicCapacityConstraint(HardConstraint):
    """
    Ensures clinic capacity limits are respected.
    Each rotation template may have a max_residents limit.
    """

    def __init__(self) -> None:
        super().__init__(
            name="ClinicCapacity",
            constraint_type=ConstraintType.CAPACITY,
            priority=ConstraintPriority.HIGH,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Enforce template capacity limits per block."""
        variables.get("assignments", {})
        template_vars = variables.get("template_assignments", {})  # (r, b, t) -> var

        if not template_vars:
            return  # No template-specific variables

        # Group by (block, template)
        for block in context.blocks:
            b_i = context.block_idx[block.id]
            for template in context.templates:
                if template.max_residents and template.max_residents > 0:
                    t_i = context.template_idx[template.id]

                    template_block_vars = [
                        template_vars[r_i, b_i, t_i]
                        for r in context.residents
                        if (r_i := context.resident_idx[r.id], b_i, t_i) in template_vars
                    ]

                    if template_block_vars:
                        model.Add(sum(template_block_vars) <= template.max_residents)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Enforce template capacity limits per block."""
        import pulp
        template_vars = variables.get("template_assignments", {})

        if not template_vars:
            return

        constraint_count = 0
        for block in context.blocks:
            b_i = context.block_idx[block.id]
            for template in context.templates:
                if template.max_residents and template.max_residents > 0:
                    t_i = context.template_idx[template.id]

                    template_block_vars = [
                        template_vars[(context.resident_idx[r.id], b_i, t_i)]
                        for r in context.residents
                        if (context.resident_idx[r.id], b_i, t_i) in template_vars
                    ]

                    if template_block_vars:
                        model += (
                            pulp.lpSum(template_block_vars) <= template.max_residents,
                            f"capacity_{b_i}_{t_i}_{constraint_count}"
                        )
                        constraint_count += 1

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Check capacity violations."""
        violations: list[ConstraintViolation] = []

        # Group by (block, template)
        by_block_template: dict[tuple[Any, Any], int] = defaultdict(int)
        for a in assignments:
            if a.rotation_template_id:
                by_block_template[(a.block_id, a.rotation_template_id)] += 1

        template_limits = {t.id: t.max_residents for t in context.templates}
        template_names = {t.id: t.name for t in context.templates}

        for (block_id, template_id), count in by_block_template.items():
            limit = template_limits.get(template_id)
            if limit and count > limit:
                violations.append(ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity="HIGH",
                    message=f"{template_names.get(template_id, 'Template')}: {count} assigned (max: {limit})",
                    block_id=block_id,
                    details={"count": count, "limit": limit},
                ))

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )


class MaxPhysiciansInClinicConstraint(HardConstraint):
    """
    Ensures physical space limitations are respected.

    Maximum number of physicians (faculty + residents combined) allowed
    in clinic at any one time, regardless of role or PGY level.

    This is a physical space constraint - the clinic can only accommodate
    a limited number of providers simultaneously.

    Default: 6 physicians maximum per clinic session (AM or PM).
    """

    def __init__(self, max_physicians: int = 6) -> None:
        """
        Initialize the constraint.

        Args:
            max_physicians: Maximum providers allowed in clinic per session.
                           Default is 6.
        """
        super().__init__(
            name="MaxPhysiciansInClinic",
            constraint_type=ConstraintType.CAPACITY,
            priority=ConstraintPriority.HIGH,
        )
        self.max_physicians: int = max_physicians

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Enforce maximum physicians per clinic block."""
        x = variables.get("assignments", {})
        template_vars = variables.get("template_assignments", {})

        if not x and not template_vars:
            return

        # Identify clinic templates
        clinic_template_ids = {
            t.id for t in context.templates
            if hasattr(t, 'activity_type') and t.activity_type == 'clinic'
        }

        if not clinic_template_ids:
            return  # No clinic templates defined

        # For each block, sum all clinic assignments (residents + faculty)
        for block in context.blocks:
            b_i = context.block_idx[block.id]
            clinic_vars = []

            # Collect resident assignments to clinic templates
            if template_vars:
                for template in context.templates:
                    if template.id in clinic_template_ids:
                        t_i = context.template_idx[template.id]
                        for r in context.residents:
                            r_i = context.resident_idx[r.id]
                            if (r_i, b_i, t_i) in template_vars:
                                clinic_vars.append(template_vars[r_i, b_i, t_i])

            ***REMOVED*** assignments are typically handled post-hoc,
            # but if faculty variables exist, include them
            faculty_vars = variables.get("faculty_assignments", {})
            if faculty_vars:
                for f in context.faculty:
                    f_i = context.faculty_idx.get(f.id)
                    if f_i is not None and (f_i, b_i) in faculty_vars:
                        clinic_vars.append(faculty_vars[f_i, b_i])

            if clinic_vars:
                model.Add(sum(clinic_vars) <= self.max_physicians)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Enforce maximum physicians per clinic block using PuLP."""
        import pulp

        template_vars = variables.get("template_assignments", {})

        if not template_vars:
            return

        clinic_template_ids = {
            t.id for t in context.templates
            if hasattr(t, 'activity_type') and t.activity_type == 'clinic'
        }

        if not clinic_template_ids:
            return

        constraint_count = 0
        for block in context.blocks:
            b_i = context.block_idx[block.id]
            clinic_vars = []

            for template in context.templates:
                if template.id in clinic_template_ids:
                    t_i = context.template_idx[template.id]
                    for r in context.residents:
                        r_i = context.resident_idx[r.id]
                        if (r_i, b_i, t_i) in template_vars:
                            clinic_vars.append(template_vars[(r_i, b_i, t_i)])

            if clinic_vars:
                model += (
                    pulp.lpSum(clinic_vars) <= self.max_physicians,
                    f"max_physicians_clinic_{b_i}_{constraint_count}"
                )
                constraint_count += 1

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Check maximum physicians in clinic per block."""
        violations: list[ConstraintViolation] = []

        # Identify clinic templates
        clinic_template_ids: set[Any] = {
            t.id for t in context.templates
            if hasattr(t, 'activity_type') and t.activity_type == 'clinic'
        }

        if not clinic_template_ids:
            return ConstraintResult(satisfied=True, violations=[])

        # Count all persons (faculty + residents) per clinic block
        by_block = defaultdict(int)
        for a in assignments:
            if a.rotation_template_id in clinic_template_ids:
                by_block[a.block_id] += 1

        # Check limits
        block_dates = {b.id: (b.date, b.time_of_day) for b in context.blocks}

        for block_id, count in by_block.items():
            if count > self.max_physicians:
                block_info = block_dates.get(block_id, ("Unknown", "Unknown"))
                violations.append(ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity="HIGH",
                    message=f"Clinic has {count} physicians on {block_info[0]} {block_info[1]} (max: {self.max_physicians})",
                    block_id=block_id,
                    details={"count": count, "limit": self.max_physicians},
                ))

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )


class CoverageConstraint(SoftConstraint):
    """
    Maximizes block coverage (number of assigned blocks).
    Primary optimization objective.
    """

    def __init__(self, weight: float = 1000.0) -> None:
        super().__init__(
            name="Coverage",
            constraint_type=ConstraintType.CAPACITY,
            weight=weight,
            priority=ConstraintPriority.HIGH,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add coverage to objective."""
        x = variables.get("assignments", {})

        if not x:
            return

        total = sum(x.values())
        variables["coverage_bonus"] = total

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add coverage to objective."""
        import pulp
        x = variables.get("assignments", {})

        if not x:
            return

        variables["coverage_bonus"] = pulp.lpSum(x.values())

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Calculate coverage rate."""
        workday_blocks = [b for b in context.blocks if not b.is_weekend]
        assigned_blocks = {a.block_id for a in assignments}

        coverage_rate = len(assigned_blocks) / len(workday_blocks) if workday_blocks else 0

        violations = []
        if coverage_rate < 0.9:
            violations.append(ConstraintViolation(
                constraint_name=self.name,
                constraint_type=self.constraint_type,
                severity="MEDIUM",
                message=f"Coverage rate: {coverage_rate * 100:.1f}%",
                details={"coverage_rate": coverage_rate},
            ))

        return ConstraintResult(
            satisfied=True,
            violations=violations,
            penalty=(1 - coverage_rate) * self.weight,
        )
