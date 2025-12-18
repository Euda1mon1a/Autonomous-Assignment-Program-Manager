"""
Equity and Continuity Constraints.

This module contains soft constraints that balance workload across residents
and encourage schedule continuity.

Classes:
    - EquityConstraint: Balance workload across residents (soft)
    - ContinuityConstraint: Encourage rotation continuity (soft)
"""
import logging
from collections import defaultdict

from .base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    SchedulingContext,
    SoftConstraint,
)

logger = logging.getLogger(__name__)


class EquityConstraint(SoftConstraint):
    """
    Balances workload across residents.

    Now supports heterogeneous targets:
    - If resident has target_clinical_blocks set, penalizes deviation from that target
    - Otherwise, uses global average for equity

    This fixes the homogeneity assumption where all residents were expected
    to work the same number of blocks.
    """

    def __init__(self, weight: float = 10.0):
        super().__init__(
            name="Equity",
            constraint_type=ConstraintType.EQUITY,
            weight=weight,
            priority=ConstraintPriority.MEDIUM,
        )

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """Add equity objective to model with support for individual targets."""
        x = variables.get("assignments", {})

        if not x:
            return

        # Check if residents have individual targets
        has_individual_targets = any(
            hasattr(r, 'target_clinical_blocks') and r.target_clinical_blocks is not None
            for r in context.residents
        )

        if has_individual_targets:
            # Use individual targets - penalize deviation from each resident's target
            total_deviation = 0
            for resident in context.residents:
                r_i = context.resident_idx[resident.id]
                resident_total = sum(
                    x[r_i, context.block_idx[b.id]]
                    for b in context.blocks
                    if (r_i, context.block_idx[b.id]) in x
                )

                if hasattr(resident, 'target_clinical_blocks') and resident.target_clinical_blocks:
                    target = resident.target_clinical_blocks
                    # Create deviation variable (absolute value approximation)
                    deviation = model.NewIntVar(0, len(context.blocks), f"deviation_{r_i}")
                    model.Add(deviation >= resident_total - target)
                    model.Add(deviation >= target - resident_total)
                    total_deviation += deviation

            variables["equity_penalty"] = total_deviation
        else:
            # Fall back to original equity logic (minimize max assignments)
            max_assigns = model.NewIntVar(0, len(context.blocks), "max_assignments")

            for resident in context.residents:
                r_i = context.resident_idx[resident.id]
                resident_total = sum(
                    x[r_i, context.block_idx[b.id]]
                    for b in context.blocks
                    if (r_i, context.block_idx[b.id]) in x
                )
                model.Add(resident_total <= max_assigns)

            variables["equity_penalty"] = max_assigns

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """Add equity objective to model with support for individual targets."""
        import pulp
        x = variables.get("assignments", {})

        if not x:
            return

        # Check if residents have individual targets
        has_individual_targets = any(
            hasattr(r, 'target_clinical_blocks') and r.target_clinical_blocks is not None
            for r in context.residents
        )

        if has_individual_targets:
            # Use individual targets - penalize deviation from each resident's target
            total_deviation = []

            for resident in context.residents:
                r_i = context.resident_idx[resident.id]
                resident_vars = [
                    x[r_i, context.block_idx[b.id]]
                    for b in context.blocks
                    if (r_i, context.block_idx[b.id]) in x
                ]

                if resident_vars and hasattr(resident, 'target_clinical_blocks') and resident.target_clinical_blocks:
                    resident_total = pulp.lpSum(resident_vars)
                    target = resident.target_clinical_blocks

                    # Create deviation variables (absolute value via two inequalities)
                    deviation_pos = pulp.LpVariable(f"deviation_pos_{r_i}", lowBound=0, cat="Integer")
                    deviation_neg = pulp.LpVariable(f"deviation_neg_{r_i}", lowBound=0, cat="Integer")

                    # resident_total - target = deviation_pos - deviation_neg
                    model += resident_total - target == deviation_pos - deviation_neg, f"deviation_def_{r_i}"

                    total_deviation.append(deviation_pos + deviation_neg)

            if total_deviation:
                variables["equity_penalty"] = pulp.lpSum(total_deviation)
            else:
                # No targets set, use original logic
                max_assigns = pulp.LpVariable("max_assignments", lowBound=0, cat="Integer")
                for resident in context.residents:
                    r_i = context.resident_idx[resident.id]
                    resident_vars = [
                        x[r_i, context.block_idx[b.id]]
                        for b in context.blocks
                        if (r_i, context.block_idx[b.id]) in x
                    ]
                    if resident_vars:
                        model += (
                            pulp.lpSum(resident_vars) <= max_assigns,
                            f"equity_{r_i}"
                        )
                variables["equity_penalty"] = max_assigns
        else:
            # Fall back to original equity logic (minimize max assignments)
            max_assigns = pulp.LpVariable("max_assignments", lowBound=0, cat="Integer")

            for resident in context.residents:
                r_i = context.resident_idx[resident.id]
                resident_vars = [
                    x[r_i, context.block_idx[b.id]]
                    for b in context.blocks
                    if (r_i, context.block_idx[b.id]) in x
                ]
                if resident_vars:
                    model += (
                        pulp.lpSum(resident_vars) <= max_assigns,
                        f"equity_{r_i}"
                    )

            variables["equity_penalty"] = max_assigns

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
        """Calculate equity score."""
        by_resident = defaultdict(int)
        for a in assignments:
            if a.person_id in context.resident_idx:
                by_resident[a.person_id] += 1

        if not by_resident:
            return ConstraintResult(satisfied=True, penalty=0.0)

        counts = list(by_resident.values())
        max_count = max(counts)
        min_count = min(counts)
        spread = max_count - min_count

        # Penalty based on spread
        penalty = spread * self.weight

        violations = []
        if spread > len(context.blocks) // len(context.residents):
            violations.append(ConstraintViolation(
                constraint_name=self.name,
                constraint_type=self.constraint_type,
                severity="MEDIUM",
                message=f"Workload imbalance: {min_count} to {max_count} assignments",
                details={"min": min_count, "max": max_count, "spread": spread},
            ))

        return ConstraintResult(
            satisfied=True,  # Soft constraint
            violations=violations,
            penalty=penalty,
        )


class ContinuityConstraint(SoftConstraint):
    """
    Encourages schedule continuity - residents staying in same rotation
    for consecutive blocks when appropriate.
    """

    def __init__(self, weight: float = 5.0):
        super().__init__(
            name="Continuity",
            constraint_type=ConstraintType.CONTINUITY,
            weight=weight,
            priority=ConstraintPriority.LOW,
        )

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """Continuity is complex for CP-SAT, handled via preference."""
        # This would require tracking template assignments across consecutive blocks
        # For simplicity, we handle this in post-processing or validation
        pass

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """Continuity is complex for PuLP, handled via preference."""
        pass

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
        """Calculate continuity score (template changes)."""
        # Group by resident, sorted by date
        by_resident = defaultdict(list)
        for a in assignments:
            for b in context.blocks:
                if b.id == a.block_id:
                    by_resident[a.person_id].append((b.date, a.rotation_template_id))
                    break

        total_changes = 0
        for _person_id, date_templates in by_resident.items():
            sorted_dt = sorted(date_templates, key=lambda x: x[0])
            for i in range(1, len(sorted_dt)):
                if sorted_dt[i][1] != sorted_dt[i-1][1]:
                    # Different template on consecutive assignment
                    if (sorted_dt[i][0] - sorted_dt[i-1][0]).days <= 1:
                        total_changes += 1

        return ConstraintResult(
            satisfied=True,
            violations=[],
            penalty=total_changes * self.weight,
        )
