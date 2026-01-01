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
        """
        Add coverage constraint to CP-SAT model.

        Ensures that required slots have at least min_coverage assignments.
        Uses slack variables for soft constraint handling (penalize undercoverage).

        Args:
            model: OR-Tools CP-SAT model
            variables: Dict containing 'assignments' decision variables
            context: SchedulingContext with block data
        """
        x = variables.get("assignments", {})
        if not x or not self.required_slots:
            return

        # Build block index mapping
        block_to_idx = {b.id: context.block_idx[b.id] for b in context.blocks}

        # For each required slot, ensure coverage
        undercoverage_vars = []
        for slot in self.required_slots:
            block_id, rotation_id = slot
            if block_id not in block_to_idx:
                continue

            b_i = block_to_idx[block_id]

            # Collect all assignment variables for this block
            # (summing across all persons assigned to this block)
            slot_vars = [x[key] for key in x if key[1] == b_i]

            if slot_vars:
                slot_sum = sum(slot_vars)

                # Create undercoverage slack variable
                slack = model.NewIntVar(0, self.min_coverage, f"coverage_slack_{block_id}")
                undercoverage_vars.append(slack)

                # coverage + slack >= min_coverage
                model.Add(slot_sum + slack >= self.min_coverage)

        # Add weighted undercoverage to soft objectives
        if undercoverage_vars:
            if "soft_objectives" not in variables:
                variables["soft_objectives"] = []
            variables["soft_objectives"].append(
                (int(self.weight * 10), sum(undercoverage_vars))  # Higher weight for coverage
            )

    def add_to_pulp(self, model, variables, context):
        """
        Add coverage constraint to PuLP model.

        Ensures that required slots have at least min_coverage assignments.

        Args:
            model: PuLP model
            variables: Dict containing 'assignments' decision variables
            context: SchedulingContext with block data
        """
        import pulp

        x = variables.get("assignments", {})
        if not x or not self.required_slots:
            return

        # Build block index mapping
        block_to_idx = {b.id: context.block_idx[b.id] for b in context.blocks}

        # For each required slot, ensure coverage
        undercoverage_vars = []
        for slot in self.required_slots:
            block_id, rotation_id = slot
            if block_id not in block_to_idx:
                continue

            b_i = block_to_idx[block_id]

            # Collect all assignment variables for this block
            slot_vars = [x[key] for key in x if key[1] == b_i]

            if slot_vars:
                # Create undercoverage slack variable
                slack = pulp.LpVariable(
                    f"coverage_slack_{block_id}",
                    lowBound=0,
                    upBound=self.min_coverage,
                    cat="Integer"
                )
                undercoverage_vars.append(slack)

                # coverage + slack >= min_coverage
                model += (
                    pulp.lpSum(slot_vars) + slack >= self.min_coverage,
                    f"coverage_{block_id}"
                )

        # Add weighted undercoverage to soft objectives
        if undercoverage_vars:
            if "soft_objectives" not in variables:
                variables["soft_objectives"] = []
            variables["soft_objectives"].append(
                (self.weight * 10, pulp.lpSum(undercoverage_vars))
            )
