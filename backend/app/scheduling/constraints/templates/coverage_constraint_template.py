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

        Ensures required slots have minimum coverage and penalizes
        uncovered slots in the objective.
        """
        x = variables.get("assignments", {})
        template_vars = variables.get("template_assignments", {})

        if not x and not template_vars:
            return

        # For each required slot, ensure minimum coverage
        uncovered_penalties = []

        for slot in self.required_slots or []:
            block_id, rotation_id = slot
            b_i = context.block_idx.get(block_id)

            if b_i is None:
                continue

            # Collect variables for this slot
            slot_vars = []

            # Check regular assignments
            for person in context.residents + context.faculty:
                p_i = context.resident_idx.get(person.id)
                if p_i is not None and (p_i, b_i) in x:
                    slot_vars.append(x[p_i, b_i])

            # Check template-specific assignments
            if template_vars:
                for person in context.residents + context.faculty:
                    p_i = context.resident_idx.get(person.id)
                    if p_i is not None:
                        for template in context.templates:
                            if (
                                template.id == rotation_id
                                and (p_i, b_i, template.id) in template_vars
                            ):
                                slot_vars.append(template_vars[p_i, b_i, template.id])

            if slot_vars:
                # Create penalty variable for uncovered slots
                is_covered = model.NewBoolVar(f"covered_{block_id}_{rotation_id}")
                model.Add(sum(slot_vars) >= self.min_coverage).OnlyEnforceIf(is_covered)
                model.Add(sum(slot_vars) < self.min_coverage).OnlyEnforceIf(
                    is_covered.Not()
                )

                # Penalty for not being covered
                uncovered_penalties.append(is_covered.Not())

        # Add penalties to objective
        if uncovered_penalties:
            objective_vars = variables.get("objective_terms", [])
            for penalty_var in uncovered_penalties:
                objective_vars.append((penalty_var, int(self.weight)))
            variables["objective_terms"] = objective_vars

    def add_to_pulp(self, model, variables, context):
        """
        Add coverage constraint to PuLP model.

        Ensures required slots have minimum coverage with penalty
        for uncovered slots.
        """
        import pulp

        x = variables.get("assignments", {})
        template_vars = variables.get("template_assignments", {})

        if not x and not template_vars:
            return

        # For each required slot, add coverage penalty
        total_penalty = 0

        for slot in self.required_slots or []:
            block_id, rotation_id = slot
            b_i = context.block_idx.get(block_id)

            if b_i is None:
                continue

            # Collect variables for this slot
            slot_vars = []

            # Check regular assignments
            for person in context.residents + context.faculty:
                p_i = context.resident_idx.get(person.id)
                if p_i is not None and (p_i, b_i) in x:
                    slot_vars.append(x[p_i, b_i])

            # Check template-specific assignments
            if template_vars:
                for person in context.residents + context.faculty:
                    p_i = context.resident_idx.get(person.id)
                    if p_i is not None:
                        for template in context.templates:
                            if (
                                template.id == rotation_id
                                and (p_i, b_i, template.id) in template_vars
                            ):
                                slot_vars.append(template_vars[p_i, b_i, template.id])

            if slot_vars:
                # Create binary variable for coverage violation
                is_uncovered = pulp.LpVariable(
                    f"uncovered_{block_id}_{rotation_id}",
                    0,
                    1,
                    cat="Binary",
                )

                # If sum < min_coverage, is_uncovered can be 1 (penalized)
                # This is approximated by: sum + is_uncovered * M >= min_coverage
                # Where M is a large number
                M = len(context.residents) + len(context.faculty)
                model += (
                    pulp.lpSum(slot_vars) + is_uncovered * M >= self.min_coverage,
                    f"coverage_penalty_{block_id}_{rotation_id}",
                )

                total_penalty += is_uncovered

        # Add total penalty to objective
        if total_penalty:
            obj_terms = variables.get("objective_terms", [])
            obj_terms.append(self.weight * total_penalty)
            variables["objective_terms"] = obj_terms
