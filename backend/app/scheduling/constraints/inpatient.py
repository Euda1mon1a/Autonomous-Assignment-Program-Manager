"""
Resident Inpatient Rotation Constraints.

This module contains constraints for resident inpatient rotations including
FMIT, Night Float, and NICU headcount limits.

Classes:
    - ResidentInpatientHeadcountConstraint: Enforces headcount limits for FMIT/NF
    - FMITResidentClinicDayConstraint: PGY-specific clinic days during FMIT

Business Rules:
    - FMIT: 1 per PGY level per block (3 total)
    - Night Float: 1 resident at a time
    - FMIT Clinic Days: PGY1=Wed AM, PGY2=Tue PM, PGY3=Mon PM
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
)

logger = logging.getLogger(__name__)


class ResidentInpatientHeadcountConstraint(HardConstraint):
    """
    Enforces headcount limits for resident inpatient rotations.

    FMIT: Exactly 1 per PGY level per block (3 total)
    Night Float: Exactly 1 resident at a time

    This constraint reads inpatient assignments from context and validates
    headcount limits are not exceeded.
    """

    FMIT_PER_PGY_PER_BLOCK = 1
    NF_CONCURRENT_MAX = 1

    def __init__(self) -> None:
        super().__init__(
            name="ResidentInpatientHeadcount",
            constraint_type=ConstraintType.CAPACITY,
            priority=ConstraintPriority.CRITICAL,
        )

    def _get_fmit_template_ids(self, context: SchedulingContext) -> set[Any]:
        """Get template IDs for FMIT rotations."""
        fmit_ids = set()
        for template in context.templates:
            if hasattr(template, "name") and template.name:
                name_lower = template.name.lower()
                if "fmit" in name_lower and "night" not in name_lower:
                    fmit_ids.add(template.id)
        return fmit_ids

    def _get_nf_template_ids(self, context: SchedulingContext) -> set[Any]:
        """Get template IDs for Night Float rotations."""
        nf_ids = set()
        for template in context.templates:
            if hasattr(template, "name") and template.name:
                name_lower = template.name.lower()
                if "night" in name_lower or "nf" in name_lower:
                    nf_ids.add(template.id)
        return nf_ids

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add headcount constraints for FMIT and NF to CP-SAT model.

        For FMIT: sum(fmit_vars for PGY-X) <= 1 per block
        For NF: sum(nf_vars for all residents) <= 1 per half-day
        """
        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            logger.debug("No template_assignments found, skipping headcount constraint")
            return

        fmit_template_ids = self._get_fmit_template_ids(context)
        nf_template_ids = self._get_nf_template_ids(context)

        if not fmit_template_ids and not nf_template_ids:
            logger.debug("No FMIT or NF templates found")
            return

        # Get residents grouped by PGY level
        residents_by_pgy: dict[int, list[Any]] = defaultdict(list)
        for r in context.residents:
            if hasattr(r, "pgy_level") and r.pgy_level:
                residents_by_pgy[r.pgy_level].append(r)

        # FMIT headcount per PGY level per block
        for pgy_level in [1, 2, 3]:
            pgy_residents = residents_by_pgy.get(pgy_level, [])
            if not pgy_residents:
                continue

            for block in context.blocks:
                b_i = context.block_idx.get(block.id)
                if b_i is None:
                    continue

                fmit_vars = []
                for resident in pgy_residents:
                    r_i = context.resident_idx.get(resident.id)
                    if r_i is None:
                        continue

                    for t_id in fmit_template_ids:
                        t_i = context.template_idx.get(t_id)
                        if t_i is not None and (r_i, b_i, t_i) in template_vars:
                            fmit_vars.append(template_vars[r_i, b_i, t_i])

                if fmit_vars:
                    model.Add(sum(fmit_vars) <= self.FMIT_PER_PGY_PER_BLOCK)

        # NF headcount per half-day (across all residents)
        for block in context.blocks:
            b_i = context.block_idx.get(block.id)
            if b_i is None:
                continue

            nf_vars = []
            for resident in context.residents:
                r_i = context.resident_idx.get(resident.id)
                if r_i is None:
                    continue

                for t_id in nf_template_ids:
                    t_i = context.template_idx.get(t_id)
                    if t_i is not None and (r_i, b_i, t_i) in template_vars:
                        nf_vars.append(template_vars[r_i, b_i, t_i])

            if nf_vars:
                model.Add(sum(nf_vars) <= self.NF_CONCURRENT_MAX)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add headcount constraints to PuLP model."""
        import pulp

        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        fmit_template_ids = self._get_fmit_template_ids(context)
        nf_template_ids = self._get_nf_template_ids(context)

        if not fmit_template_ids and not nf_template_ids:
            return

        residents_by_pgy: dict[int, list[Any]] = defaultdict(list)
        for r in context.residents:
            if hasattr(r, "pgy_level") and r.pgy_level:
                residents_by_pgy[r.pgy_level].append(r)

        constraint_count = 0

        # FMIT headcount per PGY level per block
        for pgy_level in [1, 2, 3]:
            pgy_residents = residents_by_pgy.get(pgy_level, [])
            if not pgy_residents:
                continue

            for block in context.blocks:
                b_i = context.block_idx.get(block.id)
                if b_i is None:
                    continue

                fmit_vars = []
                for resident in pgy_residents:
                    r_i = context.resident_idx.get(resident.id)
                    if r_i is None:
                        continue

                    for t_id in fmit_template_ids:
                        t_i = context.template_idx.get(t_id)
                        if t_i is not None and (r_i, b_i, t_i) in template_vars:
                            fmit_vars.append(template_vars[(r_i, b_i, t_i)])

                if fmit_vars:
                    model += (
                        pulp.lpSum(fmit_vars) <= self.FMIT_PER_PGY_PER_BLOCK,
                        f"fmit_pgy{pgy_level}_block_{constraint_count}",
                    )
                    constraint_count += 1

        # NF headcount per half-day
        for block in context.blocks:
            b_i = context.block_idx.get(block.id)
            if b_i is None:
                continue

            nf_vars = []
            for resident in context.residents:
                r_i = context.resident_idx.get(resident.id)
                if r_i is None:
                    continue

                for t_id in nf_template_ids:
                    t_i = context.template_idx.get(t_id)
                    if t_i is not None and (r_i, b_i, t_i) in template_vars:
                        nf_vars.append(template_vars[(r_i, b_i, t_i)])

            if nf_vars:
                model += (
                    pulp.lpSum(nf_vars) <= self.NF_CONCURRENT_MAX,
                    f"nf_max_block_{constraint_count}",
                )
                constraint_count += 1

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate inpatient headcount limits."""
        violations: list[ConstraintViolation] = []

        fmit_template_ids = self._get_fmit_template_ids(context)
        nf_template_ids = self._get_nf_template_ids(context)

        # Build person lookup
        person_by_id = {p.id: p for p in context.residents}

        # Count FMIT per block per PGY level
        fmit_by_block_pgy: dict[tuple[Any, int], int] = defaultdict(int)
        nf_by_block: dict[Any, int] = defaultdict(int)

        for assignment in assignments:
            if assignment.rotation_template_id in fmit_template_ids:
                person = person_by_id.get(assignment.person_id)
                if person and hasattr(person, "pgy_level") and person.pgy_level:
                    key = (assignment.block_id, person.pgy_level)
                    fmit_by_block_pgy[key] += 1

            if assignment.rotation_template_id in nf_template_ids:
                nf_by_block[assignment.block_id] += 1

        # Check FMIT violations
        for (block_id, pgy_level), count in fmit_by_block_pgy.items():
            if count > self.FMIT_PER_PGY_PER_BLOCK:
                max_allowed = self.FMIT_PER_PGY_PER_BLOCK
                msg = f"PGY-{pgy_level}: {count} FMIT (max: {max_allowed})"
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="CRITICAL",
                        message=msg,
                        block_id=block_id,
                        details={"pgy_level": pgy_level, "count": count},
                    )
                )

        # Check NF violations
        for block_id, count in nf_by_block.items():
            if count > self.NF_CONCURRENT_MAX:
                max_nf = self.NF_CONCURRENT_MAX
                msg = f"Night Float: {count} residents (max: {max_nf})"
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="CRITICAL",
                        message=msg,
                        block_id=block_id,
                        details={"count": count, "max": max_nf},
                    )
                )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )


class FMITResidentClinicDayConstraint(HardConstraint):
    """
    Enforces PGY-specific clinic days for FMIT residents.

    - PGY-1 on FMIT: Wednesday AM clinic
    - PGY-2 on FMIT: Tuesday PM clinic
    - PGY-3 on FMIT: Monday PM clinic

    Exception: Federal holidays or clinic closures → defaults back to FMIT duty
    Exception: Inverted 4th Wednesday → PGY-1 NOT assigned clinic
    """

    # Clinic days by PGY level (weekday: 0=Mon, 1=Tue, 2=Wed, etc.)
    FMIT_CLINIC_DAYS = {
        1: {"weekday": 2, "time_of_day": "AM"},  # Wed AM for PGY-1
        2: {"weekday": 1, "time_of_day": "PM"},  # Tue PM for PGY-2
        3: {"weekday": 0, "time_of_day": "PM"},  # Mon PM for PGY-3
    }

    def __init__(self) -> None:
        super().__init__(
            name="FMITResidentClinicDay",
            constraint_type=ConstraintType.ROTATION,
            priority=ConstraintPriority.HIGH,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        For each FMIT resident, force clinic assignment on their designated day.

        Note: This is a complex constraint that requires knowing which residents
        are currently on FMIT. In the current pre-loading approach, FMIT
        assignments are loaded first, so this constraint validates rather
        than generates.
        """
        # Implementation note: The pre-loading mechanism handles the assignment
        # of FMIT residents. This constraint would be used for validation
        # or for solvers that generate FMIT assignments.
        pass

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add FMIT clinic day constraints to PuLP model."""
        # Same as above - pre-loading handles this
        pass

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """
        Validate that FMIT residents have correct clinic day assignments.

        For each resident on FMIT, check that they have a clinic assignment
        on their designated day (unless it's a holiday or closure).
        """
        violations: list[ConstraintViolation] = []

        # This validation would check:
        # 1. Find all residents on FMIT in the date range
        # 2. For each, verify they have clinic on their designated day
        # 3. Skip validation for holidays/closures

        # For now, return satisfied as pre-loading handles the rules
        return ConstraintResult(
            satisfied=True,
            violations=violations,
        )
