"""Preference Constraint Template

Soft constraints for faculty/resident preferences and scheduling wishes.

Examples:
    - Prefer morning shifts
    - Prefer specific clinics
    - Avoid back-to-back duty
    - Prefer Monday start
"""

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    SoftConstraint,
    SchedulingContext,
)


class PreferenceConstraintTemplate(SoftConstraint):
    """Template for preference soft constraints."""

    def __init__(self, weight: float = 1.0):
        super().__init__(
            name="PreferenceConstraint",
            constraint_type=ConstraintType.PREFERENCE,
            weight=weight,
            priority=ConstraintPriority.MEDIUM,
        )
        self.preference_type = None  # 'time_of_day', 'clinic', 'day_of_week'
        self.preferred_value = None
        self.penalty_for_violation = 1  # Violations count multiplier

    def validate(
        self,
        assignments: list,
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate preferences and calculate penalties."""
        violations = []
        violation_count = 0

        for assignment in assignments:
            if self._violates_preference(assignment, context):
                violation_count += 1
                violations.append(
                    {
                        "constraint_name": self.name,
                        "message": f"Assignment violates {self.preference_type} preference",
                        "person_id": assignment.person_id,
                        "preferred": self.preferred_value,
                    }
                )

        penalty = self.get_penalty(violation_count * self.penalty_for_violation)
        return ConstraintResult(
            satisfied=(violation_count == 0),
            violations=violations,
            penalty=penalty,
        )

    def _violates_preference(self, assignment, context):
        """Check if assignment violates preference."""
        return False

    def add_to_cpsat(self, model, variables, context):
        """
        Add preference to CP-SAT objective as soft constraint.

        Creates penalty variables for assignments that violate preferences.
        Penalty is added to the objective to minimize preference violations.

        Supports preference types:
        - 'time_of_day': AM vs PM blocks
        - 'day_of_week': Specific days (0=Monday, 6=Sunday)

        Args:
            model: OR-Tools CP-SAT model
            variables: Dict containing 'assignments' decision variables
            context: SchedulingContext with block data
        """
        x = variables.get("assignments", {})
        if not x or not self.preference_type:
            return

        # Identify blocks that violate the preference
        violation_vars = []

        for block in context.blocks:
            b_i = context.block_idx[block.id]
            violates = False

            if self.preference_type == "time_of_day":
                # Check AM/PM preference
                block_time = getattr(block, "time_of_day", None) or getattr(
                    block, "session", None
                )
                if block_time and self.preferred_value:
                    violates = (
                        str(block_time).upper() != str(self.preferred_value).upper()
                    )

            elif self.preference_type == "day_of_week":
                # Check weekday preference (0=Monday, 6=Sunday)
                if hasattr(block, "date") and self.preferred_value is not None:
                    violates = block.date.weekday() != self.preferred_value

            if violates:
                # All assignments to this block violate preference
                for key in x:
                    if key[1] == b_i:
                        violation_vars.append(x[key])

        # Add weighted violations to soft objectives
        if violation_vars:
            penalty_weight = int(self.weight * self.penalty_for_violation)
            if "soft_objectives" not in variables:
                variables["soft_objectives"] = []
            variables["soft_objectives"].append((penalty_weight, sum(violation_vars)))

    def add_to_pulp(self, model, variables, context):
        """
        Add preference to PuLP objective as soft constraint.

        Creates penalty terms for assignments that violate preferences.

        Args:
            model: PuLP model
            variables: Dict containing 'assignments' decision variables
            context: SchedulingContext with block data
        """
        import pulp

        x = variables.get("assignments", {})
        if not x or not self.preference_type:
            return

        # Identify blocks that violate the preference
        violation_vars = []

        for block in context.blocks:
            b_i = context.block_idx[block.id]
            violates = False

            if self.preference_type == "time_of_day":
                # Check AM/PM preference
                block_time = getattr(block, "time_of_day", None) or getattr(
                    block, "session", None
                )
                if block_time and self.preferred_value:
                    violates = (
                        str(block_time).upper() != str(self.preferred_value).upper()
                    )

            elif self.preference_type == "day_of_week":
                # Check weekday preference (0=Monday, 6=Sunday)
                if hasattr(block, "date") and self.preferred_value is not None:
                    violates = block.date.weekday() != self.preferred_value

            if violates:
                # All assignments to this block violate preference
                for key in x:
                    if key[1] == b_i:
                        violation_vars.append(x[key])

        # Add weighted violations to soft objectives
        if violation_vars:
            penalty_weight = self.weight * self.penalty_for_violation
            if "soft_objectives" not in variables:
                variables["soft_objectives"] = []
            variables["soft_objectives"].append(
                (penalty_weight, pulp.lpSum(violation_vars))
            )
