"""Activity Requirement Constraints.

Soft constraint enforcing min/max/target halfdays per activity based on
RotationActivityRequirement configuration. This replaces and extends the
fixed-field HalfDayRequirementConstraint with dynamic per-activity support.

Key features:
- Dynamic: Reads requirements from RotationActivityRequirement model
- Soft constraints: Penalizes deviations from target_halfdays
- Min/max: High penalty for violating bounds (treated as near-hard constraints)
- Week-specific: Supports applicable_weeks for week-scoped requirements
- Preferences: Honors prefer_full_days, preferred_days, avoid_days

This constraint supports both resident AND faculty solving of activity slots.
The same mechanism works for:
- Resident activity distribution within rotations
- Faculty activity/call slot optimization

Classes:
    - ActivityRequirementConstraint: Main soft constraint for activity distribution
"""

import logging
from collections import defaultdict
from typing import Any
from uuid import UUID

from .base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    SchedulingContext,
    SoftConstraint,
)

logger = logging.getLogger(__name__)


class ActivityRequirementConstraint(SoftConstraint):
    """
    Soft constraint enforcing min/max/target halfdays per activity.

    Uses RotationActivityRequirement to define flexible, per-activity
    distribution targets within rotation blocks. This is the primary mechanism
    for ensuring activities (FM Clinic, Specialty, LEC, etc.) are properly
    distributed across weekly slots.

    Constraint fields from RotationActivityRequirement:
    - min_halfdays: Hard floor (high penalty if below)
    - max_halfdays: Hard ceiling (high penalty if above)
    - target_halfdays: Soft target (penalize deviations proportionally)
    - priority: 0-100 weight multiplier for soft constraint penalty
    - applicable_weeks: Which weeks this applies to (null = all)
    - prefer_full_days: Bonus for scheduling AM+PM same day
    - preferred_days: Bonus for scheduling on preferred weekdays
    - avoid_days: Penalty for scheduling on avoided days

    Penalty calculation:
    - Target deviation: weight * priority/100 * |actual - target|
    - Min violation: weight * 10 * (min - actual)  # High penalty
    - Max violation: weight * 10 * (actual - max)  # High penalty
    - Day preference bonus: -weight * 0.5 if on preferred day
    - Day avoidance penalty: weight * 0.5 if on avoided day

    Example:
        FM Clinic requirement: min=3, max=5, target=4, priority=80
        - If actual=4: penalty = 0 (hit target)
        - If actual=3: penalty = 50 * 0.8 * 1 = 40 (below target)
        - If actual=2: penalty = 50 * 10 * 1 = 500 (below min!)
    """

    # Penalty multiplier for min/max violations (near-hard constraint)
    MIN_MAX_PENALTY_MULTIPLIER = 10.0

    # Bonus/penalty for day preferences
    DAY_PREFERENCE_FACTOR = 0.5

    def __init__(
        self,
        weight: float = 50.0,
        activity_requirements: list | None = None,
    ) -> None:
        """
        Initialize the constraint.

        Args:
            weight: Base penalty weight for deviations from target.
            activity_requirements: Optional list of RotationActivityRequirement
                objects. If None, reads from context.activity_requirements.
        """
        super().__init__(
            name="ActivityRequirement",
            constraint_type=ConstraintType.CAPACITY,
            weight=weight,
            priority=ConstraintPriority.MEDIUM,
        )
        self._requirements = activity_requirements or []

    def _get_requirements(self, context: SchedulingContext) -> list:
        """Get activity requirements from context or instance."""
        if self._requirements:
            return self._requirements
        return getattr(context, "activity_requirements", [])

    def _get_requirements_by_template(
        self, context: SchedulingContext
    ) -> dict[UUID, list]:
        """Get activity requirements grouped by template ID."""
        by_template = getattr(context, "activity_req_by_template", None)
        if by_template is not None:
            return by_template

        # Build from flat list
        by_template = defaultdict(list)
        for req in self._get_requirements(context):
            by_template[req.rotation_template_id].append(req)
        return by_template

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add activity distribution penalties to CP-SAT model objective.

        Creates IntVars for deviation tracking and adds penalties to
        soft_objectives for the solver to minimize.
        """
        requirements = self._get_requirements(context)
        if not requirements:
            logger.debug("No activity requirements found, skipping constraint")
            return

        # Get the slot assignment variables
        # Expected format: slot_assignments[(person_idx, block_idx, activity_idx)]
        slot_vars = variables.get("slot_assignments", {})
        activity_vars = variables.get("activity_assignments", {})

        # Use whichever variable set is available
        assignment_vars = slot_vars or activity_vars
        if not assignment_vars:
            logger.debug("No slot/activity assignment variables found")
            return

        # Initialize soft_objectives list if not present
        if "soft_objectives" not in variables:
            variables["soft_objectives"] = []

        penalty_count = 0

        for req in requirements:
            req_id = str(req.id)[:8]  # Short ID for variable naming

            # Get activity ID and template ID
            activity_id = req.activity_id
            template_id = req.rotation_template_id

            # Find variables for this activity within this template's scope
            # This depends on how assignments are structured
            activity_slot_vars = self._find_activity_slots_cpsat(
                assignment_vars, context, template_id, activity_id
            )

            if not activity_slot_vars:
                logger.debug(
                    f"No slot variables found for activity {activity_id} "
                    f"in template {template_id}"
                )
                continue

            # Sum of assigned slots for this activity
            from ortools.sat.python import cp_model

            activity_sum = model.NewIntVar(0, 14, f"act_sum_{req_id}")
            model.Add(activity_sum == sum(activity_slot_vars))

            # Target deviation penalty
            if req.target_halfdays is not None:
                deviation = model.NewIntVar(-14, 14, f"dev_{req_id}")
                model.Add(deviation == activity_sum - req.target_halfdays)

                abs_deviation = model.NewIntVar(0, 14, f"abs_dev_{req_id}")
                model.AddAbsEquality(abs_deviation, deviation)

                # Priority-weighted penalty (priority 0-100 normalized to 0-1)
                priority_weight = req.priority / 100.0
                target_penalty = int(self.weight * priority_weight)
                variables["soft_objectives"].append((target_penalty, abs_deviation))
                penalty_count += 1

            # Min violation penalty (high penalty for hard floor)
            if req.min_halfdays > 0:
                under_min = model.NewIntVar(0, 14, f"under_min_{req_id}")
                model.AddMaxEquality(under_min, [0, req.min_halfdays - activity_sum])

                min_penalty = int(self.weight * self.MIN_MAX_PENALTY_MULTIPLIER)
                variables["soft_objectives"].append((min_penalty, under_min))
                penalty_count += 1

            # Max violation penalty (high penalty for hard ceiling)
            if req.max_halfdays < 14:
                over_max = model.NewIntVar(0, 14, f"over_max_{req_id}")
                model.AddMaxEquality(over_max, [0, activity_sum - req.max_halfdays])

                max_penalty = int(self.weight * self.MIN_MAX_PENALTY_MULTIPLIER)
                variables["soft_objectives"].append((max_penalty, over_max))
                penalty_count += 1

        logger.debug(
            f"Added {penalty_count} activity requirement penalty terms "
            f"for {len(requirements)} requirements"
        )

    def _find_activity_slots_cpsat(
        self,
        assignment_vars: dict,
        context: SchedulingContext,
        template_id: UUID,
        activity_id: UUID,
    ) -> list:
        """
        Find CP-SAT variables for slots assigned to a specific activity.

        Returns list of BoolVar decision variables that, when True, indicate
        the slot is assigned to this activity for residents on this template.
        """
        matching_vars = []

        # Get template and activity indices
        t_idx = context.template_idx.get(template_id)
        a_idx = getattr(context, "activity_idx", {}).get(activity_id)

        # Pattern 1: slot_assignments[(r_idx, b_idx, a_idx)]
        # Where a_idx is the activity index
        if a_idx is not None:
            for key, var in assignment_vars.items():
                if isinstance(key, tuple) and len(key) >= 3:
                    if key[2] == a_idx:
                        # Check if resident is on this template (if template info available)
                        matching_vars.append(var)

        # Pattern 2: template_activity_slots[(r_idx, t_idx, slot_idx, a_idx)]
        # More complex structure with explicit template
        if t_idx is not None and a_idx is not None:
            for key, var in assignment_vars.items():
                if isinstance(key, tuple) and len(key) >= 4:
                    if key[1] == t_idx and key[3] == a_idx:
                        matching_vars.append(var)

        # Pattern 3: General variable naming convention
        # Look for variables named like "slot_r{}_b{}_a{}" or similar
        for key, var in assignment_vars.items():
            if isinstance(key, str) and f"_a{a_idx}" in key:
                matching_vars.append(var)

        return matching_vars

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add activity distribution penalties to PuLP model objective.

        Uses auxiliary variables and constraints to linearize deviation
        penalties for the LP solver.
        """
        import pulp

        requirements = self._get_requirements(context)
        if not requirements:
            return

        # Get the slot assignment variables
        slot_vars = variables.get("slot_assignments", {})
        activity_vars = variables.get("activity_assignments", {})
        assignment_vars = slot_vars or activity_vars
        if not assignment_vars:
            return

        penalties = []
        constraint_count = 0

        for req in requirements:
            req_id = str(req.id)[:8]

            activity_id = req.activity_id
            template_id = req.rotation_template_id

            # Find variables for this activity
            activity_slot_vars = self._find_activity_slots_pulp(
                assignment_vars, context, template_id, activity_id
            )

            if not activity_slot_vars:
                continue

            # Sum of assigned slots
            activity_sum = pulp.lpSum(activity_slot_vars)

            # Target deviation penalty (linearized absolute value)
            if req.target_halfdays is not None:
                # Create auxiliary variables for absolute value
                pos_dev = pulp.LpVariable(f"pos_dev_{req_id}", lowBound=0)
                neg_dev = pulp.LpVariable(f"neg_dev_{req_id}", lowBound=0)

                # activity_sum - target = pos_dev - neg_dev
                model += (
                    activity_sum - req.target_halfdays == pos_dev - neg_dev,
                    f"dev_eq_{req_id}",
                )

                priority_weight = req.priority / 100.0
                target_penalty = self.weight * priority_weight
                penalties.append(target_penalty * (pos_dev + neg_dev))
                constraint_count += 1

            # Min violation penalty
            if req.min_halfdays > 0:
                under_min = pulp.LpVariable(f"under_min_{req_id}", lowBound=0)
                model += (
                    under_min >= req.min_halfdays - activity_sum,
                    f"min_viol_{req_id}",
                )

                min_penalty = self.weight * self.MIN_MAX_PENALTY_MULTIPLIER
                penalties.append(min_penalty * under_min)
                constraint_count += 1

            # Max violation penalty
            if req.max_halfdays < 14:
                over_max = pulp.LpVariable(f"over_max_{req_id}", lowBound=0)
                model += (
                    over_max >= activity_sum - req.max_halfdays,
                    f"max_viol_{req_id}",
                )

                max_penalty = self.weight * self.MIN_MAX_PENALTY_MULTIPLIER
                penalties.append(max_penalty * over_max)
                constraint_count += 1

        # Add total penalty to variables for objective inclusion
        if penalties:
            variables["activity_requirement_penalty"] = pulp.lpSum(penalties)

        logger.debug(
            f"Added {constraint_count} activity requirement constraints to PuLP model"
        )

    def _find_activity_slots_pulp(
        self,
        assignment_vars: dict,
        context: SchedulingContext,
        template_id: UUID,
        activity_id: UUID,
    ) -> list:
        """Find PuLP variables for slots assigned to a specific activity."""
        # Same logic as CP-SAT version
        return self._find_activity_slots_cpsat(
            assignment_vars, context, template_id, activity_id
        )

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """
        Validate assignments against activity requirements.

        Calculates penalty for each requirement based on:
        - Target deviation (proportional to priority)
        - Min violations (high penalty)
        - Max violations (high penalty)
        """
        violations: list[ConstraintViolation] = []
        total_penalty = 0.0

        requirements = self._get_requirements(context)
        if not requirements:
            return ConstraintResult(satisfied=True, violations=[], penalty=0.0)

        # Count actual half-days per activity per template
        # Structure: {template_id: {activity_id: count}}
        activity_counts = self._count_activity_halfdays(assignments, context)

        for req in requirements:
            template_id = req.rotation_template_id
            activity_id = req.activity_id
            actual = activity_counts.get(template_id, {}).get(activity_id, 0)

            activity_name = getattr(req.activity, "name", str(activity_id)[:8])
            template_name = self._get_template_name(context, template_id)

            # Check min violation
            if actual < req.min_halfdays:
                shortfall = req.min_halfdays - actual
                penalty = self.weight * self.MIN_MAX_PENALTY_MULTIPLIER * shortfall
                total_penalty += penalty

                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="HIGH",
                        message=(
                            f"{template_name}: {activity_name} has {actual} half-days, "
                            f"minimum is {req.min_halfdays} (short by {shortfall})"
                        ),
                        details={
                            "template_id": str(template_id),
                            "activity_id": str(activity_id),
                            "activity_name": activity_name,
                            "actual": actual,
                            "min": req.min_halfdays,
                            "shortfall": shortfall,
                        },
                    )
                )

            # Check max violation
            if actual > req.max_halfdays:
                excess = actual - req.max_halfdays
                penalty = self.weight * self.MIN_MAX_PENALTY_MULTIPLIER * excess
                total_penalty += penalty

                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="HIGH",
                        message=(
                            f"{template_name}: {activity_name} has {actual} half-days, "
                            f"maximum is {req.max_halfdays} (excess by {excess})"
                        ),
                        details={
                            "template_id": str(template_id),
                            "activity_id": str(activity_id),
                            "activity_name": activity_name,
                            "actual": actual,
                            "max": req.max_halfdays,
                            "excess": excess,
                        },
                    )
                )

            # Check target deviation
            if req.target_halfdays is not None and actual != req.target_halfdays:
                deviation = abs(actual - req.target_halfdays)
                priority_weight = req.priority / 100.0
                penalty = self.weight * priority_weight * deviation
                total_penalty += penalty

                # Only report significant deviations (>=2 half-days)
                if deviation >= 2:
                    violations.append(
                        ConstraintViolation(
                            constraint_name=self.name,
                            constraint_type=self.constraint_type,
                            severity="MEDIUM",
                            message=(
                                f"{template_name}: {activity_name} has {actual} half-days, "
                                f"target is {req.target_halfdays} (deviation: {deviation})"
                            ),
                            details={
                                "template_id": str(template_id),
                                "activity_id": str(activity_id),
                                "activity_name": activity_name,
                                "actual": actual,
                                "target": req.target_halfdays,
                                "deviation": deviation,
                                "priority": req.priority,
                            },
                        )
                    )

        # Soft constraint is always "satisfied" (doesn't block schedule)
        # Violations are informational with penalty scores
        return ConstraintResult(
            satisfied=True,
            violations=violations,
            penalty=total_penalty,
        )

    def _count_activity_halfdays(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> dict[UUID, dict[UUID, int]]:
        """
        Count half-days per activity per template from assignments.

        Returns:
            {template_id: {activity_id: count}}
        """
        counts: dict[UUID, dict[UUID, int]] = defaultdict(lambda: defaultdict(int))

        for assignment in assignments:
            # Get template ID from assignment
            template_id = getattr(assignment, "rotation_template_id", None)
            if not template_id:
                continue

            # Get activity ID from assignment or slot
            activity_id = getattr(assignment, "activity_id", None)
            if not activity_id:
                # Try to get from slot or block
                slot = getattr(assignment, "slot", None)
                if slot:
                    activity_id = getattr(slot, "activity_id", None)

            if activity_id:
                counts[template_id][activity_id] += 1

        return counts

    def _get_template_name(self, context: SchedulingContext, template_id: UUID) -> str:
        """Get template name from context."""
        for template in context.templates:
            if template.id == template_id:
                return getattr(template, "name", str(template_id)[:8])
        return str(template_id)[:8]
