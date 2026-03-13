import logging
from typing import Any

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    SchedulingContext,
    SoftConstraint,
)

logger = logging.getLogger(__name__)


class GraduationRequirementConstraint(SoftConstraint):
    """
    Soft constraint to optimize clinic-type placement based on graduation requirements.

    Encourages the solver to assign residents to rotation templates (clinics)
    where they have not yet met their target graduation requirements.
    """

    def __init__(
        self,
        weight: float = 5.0,  # Base weight for optimization
        enabled: bool = True,
    ) -> None:
        super().__init__(
            name="GraduationRequirements",
            constraint_type=ConstraintType.ROTATION,
            weight=weight,
            priority=ConstraintPriority.LOW,
            enabled=enabled,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add constraint to OR-Tools CP-SAT model."""
        if not context.graduation_requirements:
            return

        x = variables.get("template_assignments")
        if not x:
            return

        objective_terms = variables.setdefault("objective_terms", [])
        workday_blocks = [b for b in context.blocks if not b.is_weekend]
        template_idx = context.template_idx

        # For each resident, find missing requirements and add a bonus for assigning them
        for resident in context.residents:
            pgy = getattr(resident, "pgy_level", 0)
            reqs = context.graduation_requirements.get(pgy, {})
            if not reqs:
                continue

            r_i = context.resident_idx.get(resident.id)
            if r_i is None:
                continue

            for template_id, req in reqs.items():
                t_i = template_idx.get(template_id)
                if t_i is None:
                    continue

                ytd_count = context.ytd_clinic_counts.get((resident.id, template_id), 0)

                # Bonus calculation
                # 1. Focus on meeting min_halves first (high weight)
                # 2. Focus on meeting target_halves second (medium weight)
                min_halves = req.min_halves or 0
                target_halves = req.target_halves or min_halves

                bonus_weight = 0
                if ytd_count < min_halves:
                    bonus_weight = int(self.weight * 3)  # Strong incentive to hit min
                elif ytd_count < target_halves:
                    bonus_weight = int(self.weight)  # Standard incentive to hit target

                if bonus_weight > 0:
                    # Gather all variables for this resident and template
                    assigned_vars = [
                        x[r_i, context.block_idx[b.id], t_i]
                        for b in workday_blocks
                        if (r_i, context.block_idx[b.id], t_i) in x
                    ]

                    if assigned_vars:
                        # Negative penalty = bonus in objective_terms (since solver subtracts these)
                        for var in assigned_vars:
                            objective_terms.append((var, -bonus_weight))

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add constraint to PuLP model."""
        if not context.graduation_requirements:
            return

        x = variables.get("template_assignments")
        if not x:
            return

        objective_terms = variables.setdefault("objective_terms", [])
        workday_blocks = [b for b in context.blocks if not b.is_weekend]
        template_idx = context.template_idx

        for resident in context.residents:
            pgy = getattr(resident, "pgy_level", 0)
            reqs = context.graduation_requirements.get(pgy, {})
            if not reqs:
                continue

            r_i = context.resident_idx.get(resident.id)
            if r_i is None:
                continue

            for template_id, req in reqs.items():
                t_i = template_idx.get(template_id)
                if t_i is None:
                    continue

                ytd_count = context.ytd_clinic_counts.get((resident.id, template_id), 0)

                min_halves = req.min_halves or 0
                target_halves = req.target_halves or min_halves

                bonus_weight = 0
                if ytd_count < min_halves:
                    bonus_weight = int(self.weight * 3)
                elif ytd_count < target_halves:
                    bonus_weight = int(self.weight)

                if bonus_weight > 0:
                    assigned_vars = [
                        x[r_i, context.block_idx[b.id], t_i]
                        for b in workday_blocks
                        if (r_i, context.block_idx[b.id], t_i) in x
                    ]

                    if assigned_vars:
                        for var in assigned_vars:
                            objective_terms.append((var, -bonus_weight))

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate constraint against assignments (no-op for soft constraint)."""
        return ConstraintResult(satisfied=True)
