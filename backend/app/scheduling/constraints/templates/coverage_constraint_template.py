"""Coverage Constraint Template

Constraints ensuring adequate coverage of required slots/services.

Examples:
    - All clinic sessions must be covered
    - All shifts must have staff
    - All call nights covered
"""

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    SoftConstraint,
    SchedulingContext,
)


class CoverageConstraintTemplate(SoftConstraint):
    """Template for coverage constraints."""

    def __init__(self, weight: float = 1.5):
        super().__init__(
            name="CoverageConstraint",
            constraint_type=ConstraintType.COVERAGE,
            weight=weight,
            priority=ConstraintPriority.HIGH,
        )
        self.required_slots = None  # List of (block_id, rotation_id) tuples
        self.min_coverage = 1  # Minimum per slot (usually 1)

    def validate(
        self,
        assignments: list,
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate coverage requirements."""
        violations = []

        # Count assignments per slot
        coverage = {}
        for assignment in assignments:
            slot_key = (assignment.block_id, assignment.rotation_id)
            coverage[slot_key] = coverage.get(slot_key, 0) + 1

        # Check each required slot
        uncovered_count = 0
        for slot in self.required_slots or []:
            if coverage.get(slot, 0) < self.min_coverage:
                uncovered_count += 1
                violations.append(
                    {
                        "constraint_name": self.name,
                        "message": f"Slot {slot} not covered",
                        "block_id": slot[0],
                    }
                )

        penalty = self.get_penalty(uncovered_count)
        return ConstraintResult(
            satisfied=(uncovered_count == 0),
            violations=violations,
            penalty=penalty,
        )

    def add_to_cpsat(self, model, variables, context):
        pass

    def add_to_pulp(self, model, variables, context):
        pass
