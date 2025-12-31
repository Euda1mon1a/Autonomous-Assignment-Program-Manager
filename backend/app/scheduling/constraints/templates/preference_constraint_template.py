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
                violations.append({
                    'constraint_name': self.name,
                    'message': f'Assignment violates {self.preference_type} preference',
                    'person_id': assignment.person_id,
                    'preferred': self.preferred_value,
                })

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
        """Add preference to CP-SAT objective."""
        pass

    def add_to_pulp(self, model, variables, context):
        """Add preference to PuLP objective."""
        pass
