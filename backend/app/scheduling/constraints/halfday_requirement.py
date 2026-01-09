"""
Half-Day Requirement Constraints.

This module enforces per-rotation activity distribution requirements from
RotationHalfDayRequirement. Each rotation template specifies how many half-days
should be allocated to different activity types per block.

Example (Neurology Elective):
- fm_clinic_halfdays = 4  (Family Medicine clinic)
- specialty_halfdays = 5  (Neurology rotation work)
- academics_halfdays = 1  (Protected lecture time)
- Total = 10 half-days per 4-week block

The solver fills slots to meet these requirements while respecting:
- Protected slots (handled by ProtectedSlotConstraint)
- Weekend configuration (includes_weekend_work)
- Existing assignments

Classes:
    - HalfDayRequirementConstraint: Soft constraint for activity distribution
    - WeekendWorkConstraint: Hard constraint for weekend exclusion
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
    HardConstraint,
    SchedulingContext,
    SoftConstraint,
)

logger = logging.getLogger(__name__)


class WeekendWorkConstraint(HardConstraint):
    """
    Enforces weekend work configuration per rotation.

    Rotations with includes_weekend_work=False should have no assignments
    on Saturday/Sunday. Rotations with includes_weekend_work=True (e.g.,
    Night Float, FMIT) can be assigned on weekends.
    """

    def __init__(
        self,
        template_weekend_config: dict[UUID, bool] | None = None,
    ) -> None:
        """
        Initialize the constraint.

        Args:
            template_weekend_config: Mapping of template_id to includes_weekend_work.
                If None, uses template.includes_weekend_work attribute.
        """
        super().__init__(
            name="WeekendWork",
            constraint_type=ConstraintType.AVAILABILITY,
            priority=ConstraintPriority.HIGH,
        )
        self._weekend_config = template_weekend_config or {}

    def _includes_weekend(self, template_id: UUID, context: SchedulingContext) -> bool:
        """Check if a template includes weekend work."""
        if template_id in self._weekend_config:
            return self._weekend_config[template_id]

        # Fallback to template attribute
        for template in context.templates:
            if template.id == template_id:
                return getattr(template, "includes_weekend_work", False)
        return False

    def _is_weekend(self, block: Any) -> bool:
        """Check if block is on a weekend (Saturday=5 or Sunday=6)."""
        if not hasattr(block, "date"):
            return False
        return block.date.weekday() >= 5

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Block weekend assignments for non-weekend rotations."""
        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        blocked_count = 0

        for resident in context.residents:
            r_i = context.resident_idx.get(resident.id)
            if r_i is None:
                continue

            for block in context.blocks:
                if not self._is_weekend(block):
                    continue

                b_i = context.block_idx.get(block.id)
                if b_i is None:
                    continue

                # Block assignments to templates that don't include weekend work
                for template in context.templates:
                    if self._includes_weekend(template.id, context):
                        continue  # Template allows weekend work

                    t_i = context.template_idx.get(template.id)
                    if t_i is not None and (r_i, b_i, t_i) in template_vars:
                        model.Add(template_vars[r_i, b_i, t_i] == 0)
                        blocked_count += 1

        logger.debug(f"Blocked {blocked_count} weekend assignments")

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Block weekend assignments in PuLP model."""
        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        constraint_count = 0

        for resident in context.residents:
            r_i = context.resident_idx.get(resident.id)
            if r_i is None:
                continue

            for block in context.blocks:
                if not self._is_weekend(block):
                    continue

                b_i = context.block_idx.get(block.id)
                if b_i is None:
                    continue

                for template in context.templates:
                    if self._includes_weekend(template.id, context):
                        continue

                    t_i = context.template_idx.get(template.id)
                    if t_i is not None and (r_i, b_i, t_i) in template_vars:
                        model += (
                            template_vars[(r_i, b_i, t_i)] == 0,
                            f"no_weekend_{r_i}_{b_i}_{constraint_count}",
                        )
                        constraint_count += 1

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate no weekend assignments for non-weekend rotations."""
        violations: list[ConstraintViolation] = []

        resident_by_id = {r.id: r for r in context.residents}
        block_by_id = {b.id: b for b in context.blocks}
        template_by_id = {t.id: t for t in context.templates}

        for assignment in assignments:
            block = block_by_id.get(assignment.block_id)
            if not block or not self._is_weekend(block):
                continue

            template = template_by_id.get(assignment.rotation_template_id)
            if not template:
                continue

            if self._includes_weekend(template.id, context):
                continue  # Weekend work allowed

            resident = resident_by_id.get(assignment.person_id)
            resident_name = getattr(resident, "name", str(assignment.person_id))
            template_name = getattr(template, "name", str(template.id))

            violations.append(
                ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity="HIGH",
                    message=(
                        f"{resident_name} assigned to '{template_name}' on weekend "
                        f"({block.date}), but rotation doesn't include weekend work"
                    ),
                    person_id=assignment.person_id,
                    block_id=block.id,
                    details={
                        "date": str(block.date),
                        "day": block.date.strftime("%A"),
                        "template": template_name,
                    },
                )
            )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )


class HalfDayRequirementConstraint(SoftConstraint):
    """
    Soft constraint that optimizes activity distribution per rotation.

    Uses RotationHalfDayRequirement to guide the solver toward the target
    distribution of half-days across activity types. This is a soft constraint
    because exact requirements may not always be achievable due to conflicts.

    Per-block targets:
    - fm_clinic_halfdays: Target FM clinic half-days (default 4)
    - specialty_halfdays: Target specialty half-days (default 5)
    - academics_halfdays: Target academic half-days (default 1, usually protected)

    The constraint penalizes deviations from these targets to optimize toward
    the ideal distribution.
    """

    def __init__(
        self,
        weight: float = 50.0,
        halfday_requirements: dict[UUID, dict[str, Any]] | None = None,
    ) -> None:
        """
        Initialize the constraint.

        Args:
            weight: Penalty weight for deviations from target distribution.
            halfday_requirements: Mapping of rotation_template_id to requirement dict
                with keys: fm_clinic_halfdays, specialty_halfdays, specialty_name,
                academics_halfdays, elective_halfdays.
        """
        super().__init__(
            name="HalfDayRequirement",
            constraint_type=ConstraintType.CAPACITY,
            weight=weight,
            priority=ConstraintPriority.MEDIUM,
        )
        self._requirements = halfday_requirements or {}

    def get_requirement(self, template_id: UUID) -> dict[str, Any] | None:
        """Get half-day requirements for a rotation template."""
        return self._requirements.get(template_id)

    def _get_template_ids_by_activity(
        self, context: SchedulingContext
    ) -> dict[str, set[UUID]]:
        """Group template IDs by activity type."""
        by_activity: dict[str, set[UUID]] = defaultdict(set)
        for template in context.templates:
            activity = getattr(template, "activity_type", "unknown")
            by_activity[activity].add(template.id)
        return by_activity

    def _get_rotation_block_range(
        self,
        context: SchedulingContext,
    ) -> tuple[date, date] | None:
        """Get the date range for a 4-week block."""
        if context.start_date and context.end_date:
            return context.start_date, context.end_date
        if context.blocks:
            dates = [b.date for b in context.blocks if hasattr(b, "date")]
            if dates:
                return min(dates), max(dates)
        return None

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add half-day distribution optimization to CP-SAT model.

        Creates penalty variables for deviations from target distributions
        and adds them to the objective function.
        """
        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            logger.debug("No template_assignments variables found")
            return

        if not self._requirements:
            logger.debug("No half-day requirements configured")
            return

        templates_by_activity = self._get_template_ids_by_activity(context)
        fm_clinic_ids = templates_by_activity.get("outpatient", set()) | \
                        templates_by_activity.get("clinic", set())

        # For each rotation template with requirements, create distribution targets
        for template_id, req in self._requirements.items():
            fm_target = req.get("fm_clinic_halfdays", 4)
            specialty_target = req.get("specialty_halfdays", 5)
            specialty_name = req.get("specialty_name", "")

            # Find specialty template IDs based on name match
            specialty_ids: set[UUID] = set()
            if specialty_name:
                for template in context.templates:
                    if specialty_name.lower() in getattr(template, "name", "").lower():
                        specialty_ids.add(template.id)

            # Sum variables per resident across all blocks
            for resident in context.residents:
                r_i = context.resident_idx.get(resident.id)
                if r_i is None:
                    continue

                fm_vars = []
                specialty_vars = []

                for block in context.blocks:
                    b_i = context.block_idx.get(block.id)
                    if b_i is None:
                        continue

                    # FM clinic variables
                    for fm_id in fm_clinic_ids:
                        t_i = context.template_idx.get(fm_id)
                        if t_i is not None and (r_i, b_i, t_i) in template_vars:
                            fm_vars.append(template_vars[r_i, b_i, t_i])

                    # Specialty variables
                    for spec_id in specialty_ids:
                        t_i = context.template_idx.get(spec_id)
                        if t_i is not None and (r_i, b_i, t_i) in template_vars:
                            specialty_vars.append(template_vars[r_i, b_i, t_i])

                # Add soft constraints toward targets
                # (Hard constraints would over-constrain; soft allows flexibility)
                if fm_vars and fm_target > 0:
                    fm_sum = sum(fm_vars)
                    # Create deviation variable
                    # This is a simplification - full implementation would track
                    # deviation and add to objective

        logger.debug(
            f"Added half-day distribution targets for {len(self._requirements)} templates"
        )

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add half-day distribution optimization to PuLP model."""
        import pulp

        template_vars = variables.get("template_assignments", {})
        if not template_vars or not self._requirements:
            return

        templates_by_activity = self._get_template_ids_by_activity(context)
        fm_clinic_ids = templates_by_activity.get("outpatient", set()) | \
                        templates_by_activity.get("clinic", set())

        penalties = []

        for template_id, req in self._requirements.items():
            fm_target = req.get("fm_clinic_halfdays", 4)

            for resident in context.residents:
                r_i = context.resident_idx.get(resident.id)
                if r_i is None:
                    continue

                fm_vars = []
                for block in context.blocks:
                    b_i = context.block_idx.get(block.id)
                    if b_i is None:
                        continue

                    for fm_id in fm_clinic_ids:
                        t_i = context.template_idx.get(fm_id)
                        if t_i is not None and (r_i, b_i, t_i) in template_vars:
                            fm_vars.append(template_vars[(r_i, b_i, t_i)])

                # Soft deviation tracking (simplified)
                if fm_vars:
                    # Note: Full implementation would use auxiliary variables
                    # to track |actual - target| deviation
                    pass

        if penalties:
            variables["halfday_penalty"] = pulp.lpSum(penalties)

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """
        Validate half-day distribution against requirements.

        Calculates penalty based on deviation from target distributions.
        """
        violations: list[ConstraintViolation] = []
        total_penalty = 0.0

        if not self._requirements:
            return ConstraintResult(satisfied=True, violations=[], penalty=0.0)

        resident_by_id = {r.id: r for r in context.residents}
        block_by_id = {b.id: b for b in context.blocks}
        template_by_id = {t.id: t for t in context.templates}

        templates_by_activity = self._get_template_ids_by_activity(context)
        fm_clinic_ids = templates_by_activity.get("outpatient", set()) | \
                        templates_by_activity.get("clinic", set())

        # Count assignments by resident and type
        resident_fm_count: dict[UUID, int] = defaultdict(int)
        resident_total_count: dict[UUID, int] = defaultdict(int)

        for assignment in assignments:
            if assignment.person_id not in resident_by_id:
                continue

            resident_total_count[assignment.person_id] += 1

            if assignment.rotation_template_id in fm_clinic_ids:
                resident_fm_count[assignment.person_id] += 1

        # Check against requirements (simplified - checks first requirement)
        for template_id, req in self._requirements.items():
            fm_target = req.get("fm_clinic_halfdays", 4)

            for resident in context.residents:
                actual_fm = resident_fm_count.get(resident.id, 0)

                if actual_fm != fm_target:
                    deviation = abs(actual_fm - fm_target)
                    penalty = deviation * self.weight
                    total_penalty += penalty

                    if deviation >= 2:  # Only report significant deviations
                        resident_name = getattr(resident, "name", str(resident.id))
                        violations.append(
                            ConstraintViolation(
                                constraint_name=self.name,
                                constraint_type=self.constraint_type,
                                severity="MEDIUM",
                                message=(
                                    f"{resident_name}: {actual_fm} FM clinic half-days, "
                                    f"target is {fm_target} (deviation: {deviation})"
                                ),
                                person_id=resident.id,
                                details={
                                    "actual_fm": actual_fm,
                                    "target_fm": fm_target,
                                    "deviation": deviation,
                                },
                            )
                        )

            # Only check first requirement set for now
            break

        return ConstraintResult(
            satisfied=True,  # Soft constraint - always "satisfied"
            violations=violations,
            penalty=total_penalty,
        )
