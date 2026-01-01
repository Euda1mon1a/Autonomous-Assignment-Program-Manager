"""Sequence Constraint Template

Constraints for ordered relationships between assignments.

Examples:
    - Post-call must follow call duty
    - Recovery must follow intensive rotation
    - Rotation must follow prerequisite
"""

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    HardConstraint,
    SchedulingContext,
)


class SequenceConstraintTemplate(HardConstraint):
    """Template for sequence constraints."""

    def __init__(self):
        super().__init__(
            name="SequenceConstraint",
            constraint_type=ConstraintType.ROTATION,
            priority=ConstraintPriority.HIGH,
        )
        self.prerequisite_rotation = None  # Must come after this
        self.required_rotation = None  # Then must have this
        self.max_gap_days = 1  # Maximum days between sequence

    def validate(
        self,
        assignments: list,
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate sequence constraints."""
        violations = []

        # Group by person and sort by date
        person_assignments = {}
        for assignment in assignments:
            person_id = assignment.person_id
            if person_id not in person_assignments:
                person_assignments[person_id] = []
            person_assignments[person_id].append(assignment)

        # Check sequences
        for person_id, person_assigns in person_assignments.items():
            sorted_assigns = sorted(person_assigns, key=lambda a: a.date)

            for i, assign in enumerate(sorted_assigns):
                if self._is_prerequisite(assign):
                    # Check next assignment
                    if i + 1 < len(sorted_assigns):
                        next_assign = sorted_assigns[i + 1]
                        if not self._is_required_after(next_assign):
                            violations.append(
                                {
                                    "constraint_name": self.name,
                                    "message": "Required rotation missing after sequence",
                                    "person_id": person_id,
                                    "block_id": assign.block_id,
                                }
                            )
                    else:
                        violations.append(
                            {
                                "constraint_name": self.name,
                                "message": "Required rotation missing at end",
                                "person_id": person_id,
                                "block_id": assign.block_id,
                            }
                        )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )

    def _is_prerequisite(self, assignment):
        """Check if assignment is prerequisite."""
        return assignment.rotation_type == self.prerequisite_rotation

    def _is_required_after(self, assignment):
        """Check if assignment is required sequence."""
        return assignment.rotation_type == self.required_rotation

    def add_to_cpsat(self, model, variables, context):
        """
        Add sequence constraint to CP-SAT model.

        Enforces that if a person has a prerequisite rotation,
        the required rotation must follow within max_gap_days.
        """
        x = variables.get("assignments", {})
        template_vars = variables.get("template_assignments", {})

        if not x and not template_vars:
            return

        # For each person, check sequence requirements
        for person in context.residents + context.faculty:
            p_i = context.resident_idx.get(person.id)
            if p_i is None:
                continue

            # Find prerequisite blocks
            for i, block in enumerate(context.blocks):
                b_i = context.block_idx[block.id]

                # Check if this block has prerequisite rotation
                has_prerequisite = None
                if template_vars:
                    for template in context.templates:
                        if (
                            self._matches_prerequisite(template)
                            and (p_i, b_i, template.id) in template_vars
                        ):
                            has_prerequisite = template_vars[p_i, b_i, template.id]
                            break

                if has_prerequisite is None and (p_i, b_i) in x:
                    # Check rotation type from block (if available)
                    if (
                        hasattr(block, "rotation_type")
                        and block.rotation_type == self.prerequisite_rotation
                    ):
                        has_prerequisite = x[p_i, b_i]

                # If prerequisite found, ensure required rotation follows
                if has_prerequisite is not None:
                    # Find blocks within max_gap_days
                    following_blocks = []
                    for j in range(
                        i + 1, min(i + 1 + self.max_gap_days, len(context.blocks))
                    ):
                        next_block = context.blocks[j]
                        next_b_i = context.block_idx[next_block.id]

                        # Check for required rotation in following blocks
                        if template_vars:
                            for template in context.templates:
                                if (
                                    self._matches_required(template)
                                    and (p_i, next_b_i, template.id) in template_vars
                                ):
                                    following_blocks.append(
                                        template_vars[p_i, next_b_i, template.id]
                                    )

                    # Enforce: if has_prerequisite, then at least one following block
                    if following_blocks:
                        model.Add(sum(following_blocks) >= 1).OnlyEnforceIf(
                            has_prerequisite
                        )

    def _matches_prerequisite(self, template):
        """Check if template matches prerequisite rotation."""
        return (
            hasattr(template, "rotation_type")
            and template.rotation_type == self.prerequisite_rotation
        ) or (hasattr(template, "type") and template.type == self.prerequisite_rotation)

    def _matches_required(self, template):
        """Check if template matches required rotation."""
        return (
            hasattr(template, "rotation_type")
            and template.rotation_type == self.required_rotation
        ) or (hasattr(template, "type") and template.type == self.required_rotation)

    def add_to_pulp(self, model, variables, context):
        """
        Add sequence constraint to PuLP model.

        Enforces that if a person has a prerequisite rotation,
        the required rotation must follow within max_gap_days.
        """
        import pulp

        x = variables.get("assignments", {})
        template_vars = variables.get("template_assignments", {})

        if not x and not template_vars:
            return

        # For each person, check sequence requirements
        for person in context.residents + context.faculty:
            p_i = context.resident_idx.get(person.id)
            if p_i is None:
                continue

            # Find prerequisite blocks
            for i, block in enumerate(context.blocks):
                b_i = context.block_idx[block.id]

                # Check if this block has prerequisite rotation
                prereq_vars = []
                if template_vars:
                    for template in context.templates:
                        if (
                            self._matches_prerequisite(template)
                            and (p_i, b_i, template.id) in template_vars
                        ):
                            prereq_vars.append(template_vars[p_i, b_i, template.id])

                if not prereq_vars and (p_i, b_i) in x:
                    # Check rotation type from block (if available)
                    if (
                        hasattr(block, "rotation_type")
                        and block.rotation_type == self.prerequisite_rotation
                    ):
                        prereq_vars.append(x[p_i, b_i])

                # If prerequisite found, ensure required rotation follows
                for prereq_var in prereq_vars:
                    # Find blocks within max_gap_days
                    following_blocks = []
                    for j in range(
                        i + 1, min(i + 1 + self.max_gap_days, len(context.blocks))
                    ):
                        next_block = context.blocks[j]
                        next_b_i = context.block_idx[next_block.id]

                        # Check for required rotation in following blocks
                        if template_vars:
                            for template in context.templates:
                                if (
                                    self._matches_required(template)
                                    and (p_i, next_b_i, template.id) in template_vars
                                ):
                                    following_blocks.append(
                                        template_vars[p_i, next_b_i, template.id]
                                    )

                    # Enforce: if prereq_var = 1, then sum(following) >= 1
                    # Linearized: sum(following) >= prereq_var
                    if following_blocks:
                        model += (
                            pulp.lpSum(following_blocks) >= prereq_var,
                            f"sequence_{p_i}_{b_i}",
                        )
