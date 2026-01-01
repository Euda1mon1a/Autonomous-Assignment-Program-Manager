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

    def add_to_cpsat(self, model, variables, context):
        """
        Add fairness constraint to CP-SAT model as soft constraint.

        Minimizes deviation from mean assignment count using auxiliary variables.
        For each person, creates a deviation variable capturing |count - mean|.

        Args:
            model: OR-Tools CP-SAT model
            variables: Dict containing 'assignments' decision variables
            context: SchedulingContext with residents/faculty data
        """
        x = variables.get("assignments", {})
        if not x:
            return

        persons = context.residents + context.faculty
        if not persons:
            return

        # Get person indices and count assignments per person
        person_vars = {}
        for person in persons:
            if person in context.residents:
                p_i = context.resident_idx[person.id]
            else:
                p_i = context.faculty_idx[person.id]

            # Collect all assignment variables for this person
            person_assignment_vars = [
                x[key] for key in x if key[0] == p_i
            ]
            if person_assignment_vars:
                person_vars[person.id] = person_assignment_vars

        if not person_vars:
            return

        # Calculate expected mean (total slots / persons)
        total_blocks = len(context.blocks)
        mean_assignments = total_blocks // len(person_vars) if person_vars else 0

        # Create deviation variables and add to objective
        deviations = []
        for person_id, assignment_vars in person_vars.items():
            # Sum of assignments for this person
            person_sum = sum(assignment_vars)

            # Create auxiliary variable for deviation from mean
            dev_var = model.NewIntVar(0, total_blocks, f"fairness_dev_{person_id}")
            deviations.append(dev_var)

            # |person_sum - mean| <= dev_var (absolute value constraint)
            model.Add(person_sum - mean_assignments <= dev_var)
            model.Add(mean_assignments - person_sum <= dev_var)

        # Add weighted sum of deviations to minimize (soft constraint)
        if deviations:
            # Store for later objective composition
            if "soft_objectives" not in variables:
                variables["soft_objectives"] = []
            variables["soft_objectives"].append(
                (int(self.weight), sum(deviations))
            )

    def add_to_pulp(self, model, variables, context):
        """
        Add fairness constraint to PuLP model as soft constraint.

        Minimizes deviation from mean assignment count.

        Args:
            model: PuLP model
            variables: Dict containing 'assignments' decision variables
            context: SchedulingContext with residents/faculty data
        """
        import pulp

        x = variables.get("assignments", {})
        if not x:
            return

        persons = context.residents + context.faculty
        if not persons:
            return

        # Get person indices and count assignments per person
        person_vars = {}
        for person in persons:
            if person in context.residents:
                p_i = context.resident_idx[person.id]
            else:
                p_i = context.faculty_idx[person.id]

            # Collect all assignment variables for this person
            person_assignment_vars = [
                x[key] for key in x if key[0] == p_i
            ]
            if person_assignment_vars:
                person_vars[person.id] = person_assignment_vars

        if not person_vars:
            return

        # Calculate expected mean
        total_blocks = len(context.blocks)
        mean_assignments = total_blocks // len(person_vars) if person_vars else 0

        # Create deviation variables
        deviations = []
        for person_id, assignment_vars in person_vars.items():
            # Create deviation variable
            dev_var = pulp.LpVariable(
                f"fairness_dev_{person_id}",
                lowBound=0,
                cat="Integer"
            )
            deviations.append(dev_var)

            # Add absolute value constraints
            person_sum = pulp.lpSum(assignment_vars)
            model += (
                person_sum - mean_assignments <= dev_var,
                f"fairness_upper_{person_id}"
            )
            model += (
                mean_assignments - person_sum <= dev_var,
                f"fairness_lower_{person_id}"
            )

        # Store weighted deviations for objective composition
        if deviations:
            if "soft_objectives" not in variables:
                variables["soft_objectives"] = []
            variables["soft_objectives"].append(
                (self.weight, pulp.lpSum(deviations))
            )
