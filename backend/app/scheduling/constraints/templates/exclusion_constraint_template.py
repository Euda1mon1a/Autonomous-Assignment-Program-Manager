"""Exclusion Constraint Template

Constraints for preventing certain assignments together.

Examples:
    - Adjuncts cannot take call
    - Faculty cannot work in unavailable rotations
    - Ineligible residents cannot work specialty clinics
"""

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    HardConstraint,
    SchedulingContext,
)


class ExclusionConstraintTemplate(HardConstraint):
    """Template for exclusion constraints."""

    def __init__(self):
        super().__init__(
            name="ExclusionConstraint",
            constraint_type=ConstraintType.CAPACITY,
            priority=ConstraintPriority.HIGH,
        )
        self.excluded_person_type = None  # 'adjunct', 'new_faculty', etc.
        self.excluded_rotation_types = []  # Rotations excluded for type
        self.excluded_combinations = []  # (person_type, rotation) tuples

    def validate(
        self,
        assignments: list,
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate exclusion constraints."""
        violations = []

        for assignment in assignments:
            person = self._get_person(assignment.person_id, context)
            rotation = self._get_rotation(assignment.rotation_id, context)

            # Check person type exclusions
            if self._should_be_excluded(person, rotation):
                violations.append(
                    {
                        "constraint_name": self.name,
                        "message": f"{self.excluded_person_type} cannot work {rotation.name}",
                        "person_id": assignment.person_id,
                        "rotation_id": assignment.rotation_id,
                    }
                )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )

    def _should_be_excluded(self, person, rotation):
        """Check if person-rotation combination is excluded."""
        # Check person type
        if self._matches_person_type(person):
            # Check if rotation is excluded
            if rotation.type in self.excluded_rotation_types:
                return True

        # Check specific combinations
        for excluded_type, excluded_rotation in self.excluded_combinations:
            if self._matches_person_type(person, excluded_type):
                if rotation.type == excluded_rotation:
                    return True

        return False

    def _matches_person_type(self, person, person_type=None):
        """Check if person matches type."""
        check_type = person_type or self.excluded_person_type
        if check_type == "adjunct":
            return person.faculty_type == "ADJUNCT"
        elif check_type == "new":
            return person.is_new
        return False

    def _get_person(self, person_id, context):
        """Get person object."""
        for person in context.residents + context.faculty:
            if person.id == person_id:
                return person
        return None

    def _get_rotation(self, rotation_id, context):
        """Get rotation object."""
        for rotation in context.templates:
            if rotation.id == rotation_id:
                return rotation
        return None

    def add_to_cpsat(self, model, variables, context):
        """
        Add exclusion constraint to CP-SAT model.

        Prevents certain person types from being assigned to excluded rotation types
        by setting the corresponding variables to 0.
        """
        x = variables.get("assignments", {})
        template_vars = variables.get("template_assignments", {})

        if not x and not template_vars:
            return

        # For each person, check if they match excluded type
        for person in context.residents + context.faculty:
            if not self._matches_person_type(person):
                continue

            p_i = context.resident_idx.get(person.id)
            if p_i is None:
                continue

            # Exclude from specific rotation types
            for block in context.blocks:
                b_i = context.block_idx[block.id]

                # Check template-specific exclusions
                if template_vars:
                    for template in context.templates:
                        if template.type in self.excluded_rotation_types:
                            # Prevent assignment to this template
                            if (p_i, b_i, template.id) in template_vars:
                                model.Add(template_vars[p_i, b_i, template.id] == 0)

                # Check general exclusions
                if (p_i, b_i) in x:
                    # Check if block has excluded rotation type
                    if (
                        hasattr(block, "rotation_type")
                        and block.rotation_type in self.excluded_rotation_types
                    ):
                        model.Add(x[p_i, b_i] == 0)

            # Check specific exclusion combinations
            for excluded_type, excluded_rotation in self.excluded_combinations:
                if self._matches_person_type(person, excluded_type):
                    for block in context.blocks:
                        b_i = context.block_idx[block.id]

                        if template_vars:
                            for template in context.templates:
                                if (
                                    template.type == excluded_rotation
                                    and (p_i, b_i, template.id) in template_vars
                                ):
                                    model.Add(template_vars[p_i, b_i, template.id] == 0)

    def add_to_pulp(self, model, variables, context):
        """
        Add exclusion constraint to PuLP model.

        Prevents certain person types from being assigned to excluded rotation types
        by constraining the corresponding variables to 0.
        """
        import pulp

        x = variables.get("assignments", {})
        template_vars = variables.get("template_assignments", {})

        if not x and not template_vars:
            return

        # For each person, check if they match excluded type
        for person in context.residents + context.faculty:
            if not self._matches_person_type(person):
                continue

            p_i = context.resident_idx.get(person.id)
            if p_i is None:
                continue

            # Exclude from specific rotation types
            for block in context.blocks:
                b_i = context.block_idx[block.id]

                # Check template-specific exclusions
                if template_vars:
                    for template in context.templates:
                        if template.type in self.excluded_rotation_types:
                            # Prevent assignment to this template
                            if (p_i, b_i, template.id) in template_vars:
                                model += (
                                    template_vars[p_i, b_i, template.id] == 0,
                                    f"exclude_{p_i}_{b_i}_{template.id}",
                                )

                # Check general exclusions
                if (p_i, b_i) in x:
                    # Check if block has excluded rotation type
                    if (
                        hasattr(block, "rotation_type")
                        and block.rotation_type in self.excluded_rotation_types
                    ):
                        model += (
                            x[p_i, b_i] == 0,
                            f"exclude_{p_i}_{b_i}",
                        )

            # Check specific exclusion combinations
            for excluded_type, excluded_rotation in self.excluded_combinations:
                if self._matches_person_type(person, excluded_type):
                    for block in context.blocks:
                        b_i = context.block_idx[block.id]

                        if template_vars:
                            for template in context.templates:
                                if (
                                    template.type == excluded_rotation
                                    and (p_i, b_i, template.id) in template_vars
                                ):
                                    model += (
                                        template_vars[p_i, b_i, template.id] == 0,
                                        f"exclude_combo_{p_i}_{b_i}_{template.id}",
                                    )
