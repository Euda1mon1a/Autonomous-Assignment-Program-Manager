"""Fairness Constraint Template

Soft constraints for equitable distribution of assignments.

Examples:
    - Equal call distribution
    - Balanced clinic assignments
    - Fair weekend duty
"""

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    SoftConstraint,
    SchedulingContext,
)


class FairnessConstraintTemplate(SoftConstraint):
    """Template for fairness soft constraints."""

    def __init__(self, weight: float = 2.0):
        super().__init__(
            name="FairnessConstraint",
            constraint_type=ConstraintType.EQUITY,
            weight=weight,
            priority=ConstraintPriority.MEDIUM,
        )
        self.assignment_type = None  # 'call', 'clinic', 'weekend'
        self.target_distribution = None  # Expected distribution

    def validate(
        self,
        assignments: list,
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate fairness and calculate penalties."""
        violations = []

        # Count assignments per person
        counts = self._count_assignments(assignments, context)

        # Calculate deviations from mean
        mean_count = sum(counts.values()) / len(counts) if counts else 0
        total_deviation = 0

        for person_id, count in counts.items():
            deviation = abs(count - mean_count)
            if deviation > 0.5:  # Threshold
                total_deviation += deviation
                violations.append({
                    'constraint_name': self.name,
                    'message': f'Person {person_id} has {count} vs mean {mean_count:.1f}',
                    'person_id': person_id,
                    'count': count,
                    'mean': mean_count,
                })

        penalty = self.get_penalty(int(total_deviation))
        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
            penalty=penalty,
        )

    def _count_assignments(self, assignments, context):
        """Count assignments by person."""
        counts = {}
        for assignment in assignments:
            person_id = assignment.person_id
            counts[person_id] = counts.get(person_id, 0) + 1
        return counts

    def add_to_cpsat(self, model, variables, context):
        pass

    def add_to_pulp(self, model, variables, context):
        pass
