"""
Sports Medicine Coordination Constraints.

This module contains constraints for coordinating Sports Medicine (SM)
resident rotations with SM faculty availability.

See docs/architecture/FACULTY_SCHEDULING_SPECIFICATION.md for full details.

Key Rules:
    - SM residents on SM rotation MUST be scheduled with SM faculty
    - Residents see faculty's patients under direct supervision
    - SM clinic includes specialized procedures and ultrasound
    - SM clinic cancelled when SM faculty is on FMIT (no backup)

Classes:
    - SMResidentFacultyAlignmentConstraint: Hard constraint for alignment
"""
import logging
from collections import defaultdict
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


class SMResidentFacultyAlignmentConstraint(HardConstraint):
    """
    Ensures SM residents are scheduled with SM faculty.

    When a resident is on Sports Medicine rotation, they MUST be
    scheduled in SM clinic blocks at the same time as the Sports
    Medicine faculty member.

    Rationale:
        - Residents see faculty's patients under direct supervision
        - Specialized procedures require faculty oversight
        - Ultrasound training requires hands-on supervision
        - No SM clinic when SM faculty unavailable (FMIT week)

    Implementation:
        - Identifies SM rotation assignments for residents
        - Verifies SM faculty is assigned to same blocks
        - Generates violation if resident scheduled without faculty

    Note:
        When SM faculty is on FMIT, SM clinic is cancelled entirely.
        This is not a violation - it's expected behavior.
    """

    def __init__(self) -> None:
        """Initialize SM alignment constraint."""
        super().__init__(
            name="SMResidentFacultyAlignment",
            constraint_type=ConstraintType.SPECIALTY,
            priority=ConstraintPriority.HIGH,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add SM alignment constraints to CP-SAT model.

        For each SM clinic block where a resident is assigned,
        ensures SM faculty is also assigned.
        """
        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        # Identify SM clinic templates
        sm_template_ids = self._get_sm_template_ids(context)
        if not sm_template_ids:
            return

        # Find SM faculty
        sm_faculty = self._get_sm_faculty(context)
        if not sm_faculty:
            logger.warning("No SM faculty found - SM alignment constraint inactive")
            return

        sm_faculty_indices = [
            context.resident_idx.get(f.id) for f in sm_faculty
            if context.resident_idx.get(f.id) is not None
        ]

        if not sm_faculty_indices:
            return

        # Find SM rotation residents
        sm_residents = self._get_sm_rotation_residents(context)
        if not sm_residents:
            return

        # For each block and SM template, if any SM resident is assigned,
        # at least one SM faculty must be assigned
        for block in context.blocks:
            b_i = context.block_idx[block.id]

            for template_id in sm_template_ids:
                t_i = context.template_idx.get(template_id)
                if t_i is None:
                    continue

                # Collect resident assignment variables for this block/template
                resident_vars = []
                for resident in sm_residents:
                    r_i = context.resident_idx.get(resident.id)
                    if r_i is not None and (r_i, b_i, t_i) in template_vars:
                        resident_vars.append(template_vars[r_i, b_i, t_i])

                # Collect faculty assignment variables
                faculty_vars = []
                for f_i in sm_faculty_indices:
                    if (f_i, b_i, t_i) in template_vars:
                        faculty_vars.append(template_vars[f_i, b_i, t_i])

                # If any resident assigned, at least one faculty must be assigned
                # sum(resident_vars) > 0 => sum(faculty_vars) >= 1
                if resident_vars and faculty_vars:
                    # Create indicator: any_resident = 1 if any resident assigned
                    any_resident = model.NewBoolVar(f"any_sm_res_{b_i}_{t_i}")
                    model.AddMaxEquality(any_resident, resident_vars)

                    # any_faculty = 1 if any faculty assigned
                    any_faculty = model.NewBoolVar(f"any_sm_fac_{b_i}_{t_i}")
                    model.AddMaxEquality(any_faculty, faculty_vars)

                    # Implication: any_resident => any_faculty
                    model.AddImplication(any_resident, any_faculty)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add SM alignment constraints to PuLP model."""
        import pulp

        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        sm_template_ids = self._get_sm_template_ids(context)
        if not sm_template_ids:
            return

        sm_faculty = self._get_sm_faculty(context)
        if not sm_faculty:
            return

        sm_faculty_indices = [
            context.resident_idx.get(f.id) for f in sm_faculty
            if context.resident_idx.get(f.id) is not None
        ]

        sm_residents = self._get_sm_rotation_residents(context)
        if not sm_residents:
            return

        constraint_count = 0
        for block in context.blocks:
            b_i = context.block_idx[block.id]

            for template_id in sm_template_ids:
                t_i = context.template_idx.get(template_id)
                if t_i is None:
                    continue

                resident_vars = []
                for resident in sm_residents:
                    r_i = context.resident_idx.get(resident.id)
                    if r_i is not None and (r_i, b_i, t_i) in template_vars:
                        resident_vars.append(template_vars[r_i, b_i, t_i])

                faculty_vars = []
                for f_i in sm_faculty_indices:
                    if (f_i, b_i, t_i) in template_vars:
                        faculty_vars.append(template_vars[f_i, b_i, t_i])

                # Linear approximation: sum(faculty) >= sum(residents) / max_residents
                # This ensures faculty present if any residents
                if resident_vars and faculty_vars:
                    # Simpler: if sum(residents) >= 1, sum(faculty) >= 1
                    # Using big-M: sum(faculty) >= sum(residents) - M*(1-y)
                    # where y=1 if residents present
                    # Simplified: sum(faculty) >= (1/N) * sum(residents) where N = max residents
                    max_residents = len(resident_vars)
                    model += (
                        pulp.lpSum(faculty_vars) >= (1.0 / max_residents) * pulp.lpSum(resident_vars),
                        f"sm_alignment_{b_i}_{t_i}_{constraint_count}"
                    )
                    constraint_count += 1

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """
        Validate SM resident/faculty alignment.

        Checks that whenever an SM resident is assigned to SM clinic,
        SM faculty is also assigned to the same block.
        """
        violations: list[ConstraintViolation] = []

        sm_template_ids = self._get_sm_template_ids(context)
        if not sm_template_ids:
            return ConstraintResult(satisfied=True, violations=[])

        sm_faculty = self._get_sm_faculty(context)
        sm_faculty_ids = {f.id for f in sm_faculty}

        sm_residents = self._get_sm_rotation_residents(context)
        sm_resident_ids = {r.id for r in sm_residents}

        # Build lookups
        person_by_id = {p.id: p for p in context.residents + context.faculty}
        block_by_id = {b.id: b for b in context.blocks}
        template_by_id = {t.id: t for t in context.templates}

        # Group assignments by block and template
        assignments_by_block_template = defaultdict(lambda: {"residents": [], "faculty": []})

        for a in assignments:
            if a.rotation_template_id not in sm_template_ids:
                continue

            key = (a.block_id, a.rotation_template_id)

            if a.person_id in sm_resident_ids:
                assignments_by_block_template[key]["residents"].append(a)
            elif a.person_id in sm_faculty_ids:
                assignments_by_block_template[key]["faculty"].append(a)

        # Check each block/template combination
        for (block_id, template_id), personnel in assignments_by_block_template.items():
            residents = personnel["residents"]
            faculty = personnel["faculty"]

            if residents and not faculty:
                block = block_by_id.get(block_id)
                template = template_by_id.get(template_id)

                for a in residents:
                    resident = person_by_id.get(a.person_id)
                    violations.append(ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="HIGH",
                        message=f"SM resident {resident.name if resident else 'Unknown'} assigned to SM clinic on {block.date if block else 'Unknown'} without SM faculty",
                        person_id=a.person_id,
                        block_id=block_id,
                        details={
                            "template": template.name if template else "Unknown",
                            "date": str(block.date) if block else "Unknown",
                        },
                    ))

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )

    def _get_sm_template_ids(self, context: SchedulingContext) -> set[Any]:
        """Get IDs of Sports Medicine clinic templates."""
        sm_templates: set[Any] = set()
        for t in context.templates:
            # Check requires_specialty field
            if hasattr(t, 'requires_specialty') and t.requires_specialty == 'Sports Medicine':
                sm_templates.add(t.id)
            # Also check name for "Sports Medicine" or "SM"
            elif hasattr(t, 'name'):
                name_upper = t.name.upper()
                if 'SPORTS MEDICINE' in name_upper or name_upper == 'SM':
                    sm_templates.add(t.id)
        return sm_templates

    def _get_sm_faculty(self, context: SchedulingContext) -> list[Any]:
        """Get Sports Medicine faculty members."""
        sm_faculty: list[Any] = []
        for f in context.faculty:
            if hasattr(f, 'is_sports_medicine') and f.is_sports_medicine:
                sm_faculty.append(f)
            elif hasattr(f, 'faculty_role') and f.faculty_role == 'sports_med':
                sm_faculty.append(f)
            elif hasattr(f, 'specialties') and f.specialties and 'Sports Medicine' in f.specialties:
                sm_faculty.append(f)
        return sm_faculty

    def _get_sm_rotation_residents(self, context: SchedulingContext) -> list[Any]:
        """
        Get residents currently on SM rotation.

        This checks existing assignments to see which residents
        have SM rotation assignments in the scheduling period.
        """
        sm_template_ids = self._get_sm_template_ids(context)
        if not sm_template_ids:
            return []

        # Find residents with SM assignments
        sm_resident_ids = set()
        for a in context.existing_assignments:
            if a.rotation_template_id in sm_template_ids:
                sm_resident_ids.add(a.person_id)

        # Return resident objects
        return [r for r in context.residents if r.id in sm_resident_ids]
