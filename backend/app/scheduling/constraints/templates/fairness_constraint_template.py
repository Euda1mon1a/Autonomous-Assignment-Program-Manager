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

    def __init__(self, weight: float = 2.0) -> None:
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
                violations.append(
                    {
                        "constraint_name": self.name,
                        "message": f"Person {person_id} has {count} vs mean {mean_count:.1f}",
                        "person_id": person_id,
                        "count": count,
                        "mean": mean_count,
                    }
                )

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

    def add_to_cpsat(self, model, variables, context) -> None:
        """
        Add fairness constraint to CP-SAT model.

        Minimizes the maximum assignment count across people to promote
        even distribution using a min-max objective.
        """
        x = variables.get("assignments", {})
        if not x:
            return

            # Count assignments per person
        person_counts = {}
        for person in context.residents + context.faculty:
            p_i = context.resident_idx.get(person.id)
            if p_i is None:
                continue

            person_vars = []
            for block in context.blocks:
                b_i = context.block_idx[block.id]
                if (p_i, b_i) in x:
                    person_vars.append(x[p_i, b_i])

            if person_vars:
                person_counts[p_i] = person_vars

        if not person_counts:
            return

            # Create max count variable to minimize inequality
        max_count = model.NewIntVar(0, len(context.blocks), "max_fairness_count")
        for p_i, vars_list in person_counts.items():
            model.Add(sum(vars_list) <= max_count)

            # Add to objective (minimize max to promote fairness)
        objective_vars = variables.get("objective_terms", [])
        objective_vars.append((max_count, int(self.weight)))
        variables["objective_terms"] = objective_vars

    def add_to_pulp(self, model, variables, context) -> None:
        """
        Add fairness constraint to PuLP model.

        Minimizes the maximum assignment count across people using
        auxiliary variables and linear programming.
        """
        import pulp

        x = variables.get("assignments", {})
        if not x:
            return

            # Count assignments per person
        person_counts = {}
        for person in context.residents + context.faculty:
            p_i = context.resident_idx.get(person.id)
            if p_i is None:
                continue

            person_vars = []
            for block in context.blocks:
                b_i = context.block_idx[block.id]
                if (p_i, b_i) in x:
                    person_vars.append(x[p_i, b_i])

            if person_vars:
                person_counts[p_i] = person_vars

        if not person_counts:
            return

            # Create max count variable
        max_count = pulp.LpVariable(
            "max_fairness_count", 0, len(context.blocks), cat="Integer"
        )

        # Constrain max count to be >= each person's count
        for p_i, vars_list in person_counts.items():
            model += (
                pulp.lpSum(vars_list) <= max_count,
                f"fairness_max_{p_i}",
            )

            # Add max count to objective (minimize)
        obj_terms = variables.get("objective_terms", [])
        obj_terms.append(self.weight * max_count)
        variables["objective_terms"] = obj_terms
