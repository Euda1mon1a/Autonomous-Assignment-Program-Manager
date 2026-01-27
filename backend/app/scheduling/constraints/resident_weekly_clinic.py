"""
Resident Weekly Clinic Constraints.

This module contains constraints that enforce resident weekly clinic requirements
based on rotation-specific configurations from ResidentWeeklyRequirement model.

The weekly requirement configuration provides per-week half-day scheduling rules:
- FM clinic min/max requirements (ACGME: min 2 on outpatient)
- Specialty half-day requirements
- Academic time protection
- Day-of-week availability

Classes:
    - ResidentWeeklyClinicConstraint: Enforce min/max FM clinic assignments (hard)
    - ResidentAcademicTimeConstraint: Protect Wednesday AM for academics (hard)
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


class ResidentWeeklyClinicConstraint(HardConstraint):
    """
    Enforces weekly FM clinic half-day requirements for residents.

    This constraint uses rotation-specific ResidentWeeklyRequirement configurations
    to enforce:
    - Minimum FM clinic half-days per week (ACGME: 2 on outpatient rotations)
    - Maximum FM clinic half-days per week

    The constraint is resident-agnostic: any resident on the rotation must meet
    the same weekly requirements regardless of PGY level.

    Requirements are loaded from the database via the rotation template's
    weekly_requirements relationship and cached in the scheduling context.
    """

    def __init__(
        self,
        weekly_requirements: dict[UUID, dict[str, Any]] | None = None,
    ) -> None:
        """
        Initialize the constraint.

        Args:
            weekly_requirements: Pre-loaded requirements mapping rotation_template_id
                to requirement dict. If None, uses context.weekly_requirements.
        """
        super().__init__(
            name="ResidentWeeklyClinic",
            constraint_type=ConstraintType.CAPACITY,
            priority=ConstraintPriority.HIGH,
        )
        self._weekly_requirements = weekly_requirements or {}

    def get_requirement(self, template_id: UUID) -> dict[str, Any] | None:
        """
        Get weekly requirement config for a rotation template.

        Args:
            template_id: UUID of the rotation template

        Returns:
            Dict with requirement fields or None if not configured
        """
        return self._weekly_requirements.get(template_id)

    def _get_fm_clinic_template_ids(self, context: SchedulingContext) -> set[UUID]:
        """Get template IDs for outpatient rotations (rotation_type=outpatient)."""
        fm_ids: set[UUID] = set()
        for template in context.templates:
            if hasattr(template, "rotation_type"):
                if template.rotation_type in ("outpatient",):
                    fm_ids.add(template.id)
        return fm_ids

    def _get_resident_current_rotation(
        self,
        resident_id: UUID,
        week_start: date,
        assignments: list[Any],
        block_by_id: dict[UUID, Any],
    ) -> UUID | None:
        """
        Determine what rotation a resident is on during a given week.

        Returns the rotation_template_id for the resident's assignment that
        covers the week, or None if not assigned.
        """
        for assignment in assignments:
            if assignment.person_id != resident_id:
                continue

            block = block_by_id.get(assignment.block_id)
            if not block:
                continue

            # Check if assignment's block overlaps with the week
            block_date = block.date
            if isinstance(block_date, date):
                assignment_week = self._get_week_start(block_date)
                if assignment_week == week_start:
                    return assignment.rotation_template_id

        return None

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add resident weekly clinic constraints to CP-SAT model.

        For each resident on a rotation with weekly requirements:
        - Adds min constraint: sum(clinic_vars) >= fm_clinic_min_per_week
        - Adds max constraint: sum(clinic_vars) <= fm_clinic_max_per_week
        """
        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            logger.debug("No template_assignments variables found")
            return

        fm_clinic_ids = self._get_fm_clinic_template_ids(context)
        if not fm_clinic_ids:
            logger.debug("No FM clinic templates found")
            return

        constraints_added = 0

        # Group blocks by week
        weeks = self._group_blocks_by_week(context.blocks)

        for resident in context.residents:
            r_i = context.resident_idx.get(resident.id)
            if r_i is None:
                continue

            for week_start, week_blocks in weeks.items():
                # Get clinic variables for this resident's week
                week_clinic_vars = []

                for block in week_blocks:
                    b_i = context.block_idx.get(block.id)
                    if b_i is None:
                        continue

                    for template_id in fm_clinic_ids:
                        t_i = context.template_idx.get(template_id)
                        if t_i is not None and (r_i, b_i, t_i) in template_vars:
                            week_clinic_vars.append(template_vars[r_i, b_i, t_i])

                if not week_clinic_vars:
                    continue

                # Apply constraints based on any rotation's weekly requirements
                # that this resident might be on
                for template_id, req in self._weekly_requirements.items():
                    fm_min = req.get("fm_clinic_min_per_week", 2)
                    fm_max = req.get("fm_clinic_max_per_week", 10)

                    # Check if this resident is assigned to this rotation
                    # This is checked dynamically based on existing assignments
                    # For now, apply conservative defaults for all residents

                    week_sum = sum(week_clinic_vars)

                    # Minimum constraint (ACGME requirement)
                    if fm_min > 0:
                        model.Add(week_sum >= fm_min)
                        constraints_added += 1

                    # Maximum constraint
                    if fm_max < 10:
                        model.Add(week_sum <= fm_max)
                        constraints_added += 1

                    # Only apply once per resident-week
                    break

        logger.debug(f"Added {constraints_added} resident weekly clinic constraints")

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add resident weekly clinic constraints to PuLP model."""
        import pulp

        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        fm_clinic_ids = self._get_fm_clinic_template_ids(context)
        if not fm_clinic_ids:
            return

        constraint_count = 0
        weeks = self._group_blocks_by_week(context.blocks)

        for resident in context.residents:
            r_i = context.resident_idx.get(resident.id)
            if r_i is None:
                continue

            for week_start, week_blocks in weeks.items():
                week_clinic_vars = []

                for block in week_blocks:
                    b_i = context.block_idx.get(block.id)
                    if b_i is None:
                        continue

                    for template_id in fm_clinic_ids:
                        t_i = context.template_idx.get(template_id)
                        if t_i is not None and (r_i, b_i, t_i) in template_vars:
                            week_clinic_vars.append(template_vars[(r_i, b_i, t_i)])

                if not week_clinic_vars:
                    continue

                for template_id, req in self._weekly_requirements.items():
                    fm_min = req.get("fm_clinic_min_per_week", 2)
                    fm_max = req.get("fm_clinic_max_per_week", 10)

                    if fm_min > 0:
                        model += (
                            pulp.lpSum(week_clinic_vars) >= fm_min,
                            f"resident_clinic_min_{r_i}_{constraint_count}",
                        )
                        constraint_count += 1

                    if fm_max < 10:
                        model += (
                            pulp.lpSum(week_clinic_vars) <= fm_max,
                            f"resident_clinic_max_{r_i}_{constraint_count}",
                        )
                        constraint_count += 1

                    break

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """
        Validate resident clinic assignments against weekly requirements.

        Checks each resident's FM clinic assignments per week against their
        rotation's requirements.
        """
        violations: list[ConstraintViolation] = []

        resident_by_id = {r.id: r for r in context.residents}
        block_by_id = {b.id: b for b in context.blocks}

        fm_clinic_ids = self._get_fm_clinic_template_ids(context)

        # Count clinic assignments by resident and week
        resident_weekly_counts: dict[UUID, dict[date, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        for assignment in assignments:
            if assignment.person_id not in resident_by_id:
                continue
            if assignment.rotation_template_id not in fm_clinic_ids:
                continue

            block = block_by_id.get(assignment.block_id)
            if not block:
                continue

            week_start = self._get_week_start(block.date)
            resident_weekly_counts[assignment.person_id][week_start] += 1

        # Check constraints
        weeks = self._group_blocks_by_week(context.blocks)

        for resident in context.residents:
            weekly_counts = resident_weekly_counts.get(resident.id, {})

            for week_start in weeks:
                count = weekly_counts.get(week_start, 0)

                # Determine resident's rotation for this week
                rotation_id = self._get_resident_current_rotation(
                    resident.id, week_start, assignments, block_by_id
                )

                if not rotation_id:
                    continue

                req = self.get_requirement(rotation_id)
                if not req:
                    continue

                fm_min = req.get("fm_clinic_min_per_week", 2)
                fm_max = req.get("fm_clinic_max_per_week", 10)

                resident_name = getattr(resident, "name", str(resident.id))

                # Check minimum
                if count < fm_min:
                    violations.append(
                        ConstraintViolation(
                            constraint_name=self.name,
                            constraint_type=self.constraint_type,
                            severity="HIGH",
                            message=(
                                f"{resident_name}: {count} FM clinic half-days in week of "
                                f"{week_start}, requires minimum {fm_min}"
                            ),
                            person_id=resident.id,
                            details={
                                "week_start": str(week_start),
                                "count": count,
                                "minimum": fm_min,
                            },
                        )
                    )

                # Check maximum
                if count > fm_max:
                    violations.append(
                        ConstraintViolation(
                            constraint_name=self.name,
                            constraint_type=self.constraint_type,
                            severity="HIGH",
                            message=(
                                f"{resident_name}: {count} FM clinic half-days in week of "
                                f"{week_start}, exceeds maximum {fm_max}"
                            ),
                            person_id=resident.id,
                            details={
                                "week_start": str(week_start),
                                "count": count,
                                "maximum": fm_max,
                            },
                        )
                    )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )

    def _group_blocks_by_week(self, blocks: list[Any]) -> dict[date, list[Any]]:
        """Group blocks by week (starting Monday)."""
        weeks: dict[date, list[Any]] = defaultdict(list)
        for block in blocks:
            week_start = self._get_week_start(block.date)
            weeks[week_start].append(block)
        return weeks

    def _get_week_start(self, any_date: date) -> date:
        """Get Monday of the week containing the date."""
        days_since_monday = any_date.weekday()
        return any_date - timedelta(days=days_since_monday)


class ResidentAcademicTimeConstraint(HardConstraint):
    """
    Protects academic time (Wednesday AM) from clinic assignments.

    Residents with academics_required=True in their rotation's weekly requirements
    cannot be assigned to clinic on Wednesday AM.

    This constraint implements ACGME protected academic time requirements.
    """

    def __init__(
        self,
        weekly_requirements: dict[UUID, dict[str, Any]] | None = None,
    ) -> None:
        """Initialize the constraint."""
        super().__init__(
            name="ResidentAcademicTime",
            constraint_type=ConstraintType.AVAILABILITY,
            priority=ConstraintPriority.CRITICAL,
        )
        self._weekly_requirements = weekly_requirements or {}

    def _is_academic_slot(self, block: Any) -> bool:
        """Check if block is Wednesday AM (protected academic time)."""
        if not hasattr(block, "date") or not hasattr(block, "time_of_day"):
            return False
        return block.date.weekday() == 2 and block.time_of_day == "AM"

    def _get_clinic_template_ids(self, context: SchedulingContext) -> set[UUID]:
        """Get template IDs for clinic rotations."""
        clinic_ids: set[UUID] = set()
        for template in context.templates:
            if hasattr(template, "rotation_type"):
                if template.rotation_type in ("outpatient",):
                    clinic_ids.add(template.id)
        return clinic_ids

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Block clinic assignments on Wednesday AM for residents needing academic time.
        """
        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        clinic_ids = self._get_clinic_template_ids(context)
        if not clinic_ids:
            return

        blocked_count = 0

        for resident in context.residents:
            r_i = context.resident_idx.get(resident.id)
            if r_i is None:
                continue

            # Check if any of this resident's rotations require academics
            requires_academics = any(
                req.get("academics_required", True)
                for req in self._weekly_requirements.values()
            )

            if not requires_academics:
                continue

            for block in context.blocks:
                if not self._is_academic_slot(block):
                    continue

                b_i = context.block_idx.get(block.id)
                if b_i is None:
                    continue

                # Block clinic assignments on academic slots
                for clinic_id in clinic_ids:
                    t_i = context.template_idx.get(clinic_id)
                    if t_i is not None and (r_i, b_i, t_i) in template_vars:
                        model.Add(template_vars[r_i, b_i, t_i] == 0)
                        blocked_count += 1

        logger.debug(f"Blocked {blocked_count} assignments on academic time")

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Block clinic assignments on Wednesday AM in PuLP model."""
        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        clinic_ids = self._get_clinic_template_ids(context)
        if not clinic_ids:
            return

        constraint_count = 0

        for resident in context.residents:
            r_i = context.resident_idx.get(resident.id)
            if r_i is None:
                continue

            requires_academics = any(
                req.get("academics_required", True)
                for req in self._weekly_requirements.values()
            )

            if not requires_academics:
                continue

            for block in context.blocks:
                if not self._is_academic_slot(block):
                    continue

                b_i = context.block_idx.get(block.id)
                if b_i is None:
                    continue

                for clinic_id in clinic_ids:
                    t_i = context.template_idx.get(clinic_id)
                    if t_i is not None and (r_i, b_i, t_i) in template_vars:
                        model += (
                            template_vars[(r_i, b_i, t_i)] == 0,
                            f"academic_protection_{r_i}_{b_i}_{constraint_count}",
                        )
                        constraint_count += 1

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate no clinic assignments on academic time."""
        violations: list[ConstraintViolation] = []

        resident_by_id = {r.id: r for r in context.residents}
        block_by_id = {b.id: b for b in context.blocks}
        clinic_ids = self._get_clinic_template_ids(context)

        for assignment in assignments:
            resident = resident_by_id.get(assignment.person_id)
            if not resident:
                continue

            if assignment.rotation_template_id not in clinic_ids:
                continue

            block = block_by_id.get(assignment.block_id)
            if not block or not self._is_academic_slot(block):
                continue

            # Check if rotation requires academic time
            req = self._weekly_requirements.get(assignment.rotation_template_id)
            if req and req.get("academics_required", True):
                resident_name = getattr(resident, "name", str(resident.id))
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="CRITICAL",
                        message=(
                            f"{resident_name} assigned to clinic on Wednesday AM "
                            f"({block.date}), but academic time is protected"
                        ),
                        person_id=resident.id,
                        block_id=block.id,
                        details={
                            "date": str(block.date),
                            "time_of_day": "AM",
                        },
                    )
                )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )


class ResidentClinicDayPreferenceConstraint(SoftConstraint):
    """
    Soft constraint that optimizes clinic assignments to allowed days.

    Uses allowed_clinic_days from weekly requirements to penalize
    clinic assignments on non-preferred days.
    """

    def __init__(
        self,
        weight: float = 10.0,
        weekly_requirements: dict[UUID, dict[str, Any]] | None = None,
    ) -> None:
        """Initialize the constraint."""
        super().__init__(
            name="ResidentClinicDayPreference",
            constraint_type=ConstraintType.PREFERENCE,
            weight=weight,
            priority=ConstraintPriority.LOW,
        )
        self._weekly_requirements = weekly_requirements or {}

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add clinic day preference penalties to objective."""
        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        # Get clinic templates
        clinic_ids: set[UUID] = set()
        for template in context.templates:
            if hasattr(template, "rotation_type"):
                if template.rotation_type in ("outpatient",):
                    clinic_ids.add(template.id)

        if not clinic_ids:
            return

        total_penalty = 0

        for resident in context.residents:
            r_i = context.resident_idx.get(resident.id)
            if r_i is None:
                continue

            for block in context.blocks:
                b_i = context.block_idx.get(block.id)
                if b_i is None:
                    continue

                day_of_week = block.date.weekday()

                for template_id, req in self._weekly_requirements.items():
                    allowed_days = req.get("allowed_clinic_days", [])
                    if not allowed_days:
                        continue  # No restriction

                    allowed_set = set(allowed_days)
                    if day_of_week in allowed_set:
                        continue  # Day is allowed

                    # Penalize assignments on non-allowed days
                    for clinic_id in clinic_ids:
                        t_i = context.template_idx.get(clinic_id)
                        if t_i is not None and (r_i, b_i, t_i) in template_vars:
                            total_penalty += template_vars[r_i, b_i, t_i]

        if total_penalty:
            variables["clinic_day_penalty"] = total_penalty

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add clinic day preference penalties to PuLP objective."""
        import pulp

        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        clinic_ids: set[UUID] = set()
        for template in context.templates:
            if hasattr(template, "rotation_type"):
                if template.rotation_type in ("outpatient",):
                    clinic_ids.add(template.id)

        if not clinic_ids:
            return

        penalties = []

        for resident in context.residents:
            r_i = context.resident_idx.get(resident.id)
            if r_i is None:
                continue

            for block in context.blocks:
                b_i = context.block_idx.get(block.id)
                if b_i is None:
                    continue

                day_of_week = block.date.weekday()

                for template_id, req in self._weekly_requirements.items():
                    allowed_days = req.get("allowed_clinic_days", [])
                    if not allowed_days:
                        continue

                    allowed_set = set(allowed_days)
                    if day_of_week in allowed_set:
                        continue

                    for clinic_id in clinic_ids:
                        t_i = context.template_idx.get(clinic_id)
                        if t_i is not None and (r_i, b_i, t_i) in template_vars:
                            penalties.append(template_vars[(r_i, b_i, t_i)])

        if penalties:
            variables["clinic_day_penalty"] = pulp.lpSum(penalties)

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Calculate penalty for clinic assignments on non-preferred days."""
        block_by_id = {b.id: b for b in context.blocks}
        resident_by_id = {r.id: r for r in context.residents}

        clinic_ids: set[UUID] = set()
        for template in context.templates:
            if hasattr(template, "rotation_type"):
                if template.rotation_type in ("outpatient",):
                    clinic_ids.add(template.id)

        total_penalty = 0.0

        for assignment in assignments:
            if assignment.person_id not in resident_by_id:
                continue
            if assignment.rotation_template_id not in clinic_ids:
                continue

            block = block_by_id.get(assignment.block_id)
            if not block:
                continue

            day_of_week = block.date.weekday()

            for req in self._weekly_requirements.values():
                allowed_days = req.get("allowed_clinic_days", [])
                if not allowed_days:
                    continue
                if day_of_week not in set(allowed_days):
                    total_penalty += self.weight

        return ConstraintResult(
            satisfied=True,  # Soft constraint
            violations=[],
            penalty=total_penalty,
        )
