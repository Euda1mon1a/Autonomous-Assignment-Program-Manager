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

        Ensures that when a prerequisite rotation is assigned, the required
        rotation must follow within max_gap_days.

        Uses implication constraints:
        - If x[p, b_prereq] = 1, then sum(x[p, b_following]) >= 1

        Args:
            model: OR-Tools CP-SAT model
            variables: Dict containing 'assignments' decision variables
            context: SchedulingContext with blocks sorted by date
        """
        from datetime import timedelta

        x = variables.get("assignments", {})
        if not x or not self.prerequisite_rotation or not self.required_rotation:
            return

        # Sort blocks by date for temporal ordering
        sorted_blocks = sorted(context.blocks, key=lambda b: b.date)

        # Build block index to date mapping
        block_dates = {context.block_idx[b.id]: b.date for b in context.blocks}

        # For each person, check all blocks
        all_persons = context.residents + context.faculty
        for person in all_persons:
            if person in context.residents:
                p_i = context.resident_idx[person.id]
            else:
                p_i = context.faculty_idx[person.id]

            # Find all prerequisite block indices for this person
            for prereq_block in sorted_blocks:
                prereq_b_i = context.block_idx[prereq_block.id]
                prereq_key = (p_i, prereq_b_i)

                if prereq_key not in x:
                    continue

                # Find valid following blocks (within max_gap_days)
                following_keys = []
                for follow_block in sorted_blocks:
                    follow_b_i = context.block_idx[follow_block.id]
                    follow_key = (p_i, follow_b_i)

                    if follow_key not in x:
                        continue

                    # Check if this block is within valid gap
                    gap = (follow_block.date - prereq_block.date).days
                    if 1 <= gap <= self.max_gap_days:
                        following_keys.append(follow_key)

                # Add implication: prereq -> at least one following
                if following_keys:
                    # If prereq is assigned, at least one following must be assigned
                    # prereq => sum(following) >= 1
                    # Equivalently: sum(following) >= prereq
                    model.Add(sum(x[k] for k in following_keys) >= x[prereq_key])

    def add_to_pulp(self, model, variables, context):
        """
        Add sequence constraint to PuLP model.

        Ensures that when a prerequisite rotation is assigned, the required
        rotation must follow within max_gap_days.

        Args:
            model: PuLP model
            variables: Dict containing 'assignments' decision variables
            context: SchedulingContext with blocks sorted by date
        """
        import pulp

        x = variables.get("assignments", {})
        if not x or not self.prerequisite_rotation or not self.required_rotation:
            return

        # Sort blocks by date for temporal ordering
        sorted_blocks = sorted(context.blocks, key=lambda b: b.date)

        constraint_count = 0
        # For each person, check all blocks
        all_persons = context.residents + context.faculty
        for person in all_persons:
            if person in context.residents:
                p_i = context.resident_idx[person.id]
            else:
                p_i = context.faculty_idx[person.id]

            # Find all prerequisite block indices for this person
            for prereq_block in sorted_blocks:
                prereq_b_i = context.block_idx[prereq_block.id]
                prereq_key = (p_i, prereq_b_i)

                if prereq_key not in x:
                    continue

                # Find valid following blocks (within max_gap_days)
                following_keys = []
                for follow_block in sorted_blocks:
                    follow_b_i = context.block_idx[follow_block.id]
                    follow_key = (p_i, follow_b_i)

                    if follow_key not in x:
                        continue

                    # Check if this block is within valid gap
                    gap = (follow_block.date - prereq_block.date).days
                    if 1 <= gap <= self.max_gap_days:
                        following_keys.append(follow_key)

                # Add implication constraint
                if following_keys:
                    model += (
                        pulp.lpSum(x[k] for k in following_keys) >= x[prereq_key],
                        f"sequence_{p_i}_{constraint_count}"
                    )
                    constraint_count += 1
