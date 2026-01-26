"""
Integrated Workload Constraint.

Combines call, FMIT, and clinic burden into a unified workload score
for faculty equity optimization.

This is especially important for Core faculty who don't have fixed
role-based assignments (unlike PD, APD, OIC, Dept Chief).

Workload Formula:
    workload_score = (
        call_count × CALL_WEIGHT +
        fmit_weeks × FMIT_WEIGHT +
        clinic_halfdays × CLINIC_WEIGHT
    )

The constraint minimizes the maximum workload score across faculty,
ensuring no one person carries a disproportionate burden.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from .base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    SchedulingContext,
    SoftConstraint,
)

logger = logging.getLogger(__name__)


# Workload weights - can be tuned based on actual burden
CALL_WEIGHT = 1.0  # Each overnight call = 1 point
FMIT_WEIGHT = 3.0  # Each FMIT week = 3 points (intensive inpatient)
CLINIC_WEIGHT = 0.5  # Each clinic half-day = 0.5 points
ADMIN_WEIGHT = 0.25  # Each admin half-day = 0.25 points (GME, DFM)
ACADEMIC_WEIGHT = 0.25  # Each academic half-day = 0.25 points (LEC, ADV)


@dataclass
class FacultyWorkload:
    """Workload breakdown for a single faculty member."""

    person_id: str
    person_name: str
    call_count: int = 0
    fmit_weeks: int = 0
    clinic_halfdays: int = 0
    admin_halfdays: int = 0  # GME, DFM
    academic_halfdays: int = 0  # LEC, ADV

    @property
    def total_score(self) -> float:
        """Calculate total workload score."""
        return (
            self.call_count * CALL_WEIGHT
            + self.fmit_weeks * FMIT_WEIGHT
            + self.clinic_halfdays * CLINIC_WEIGHT
            + self.admin_halfdays * ADMIN_WEIGHT
            + self.academic_halfdays * ACADEMIC_WEIGHT
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "person_id": self.person_id,
            "person_name": self.person_name,
            "call_count": self.call_count,
            "fmit_weeks": self.fmit_weeks,
            "clinic_halfdays": self.clinic_halfdays,
            "admin_halfdays": self.admin_halfdays,
            "academic_halfdays": self.academic_halfdays,
            "total_score": self.total_score,
        }


class IntegratedWorkloadConstraint(SoftConstraint):
    """
    Ensures fair distribution of total workload across faculty.

    Combines call, FMIT, and clinic assignments into a single workload
    score, then applies min-max fairness to ensure balanced distribution.

    This is particularly important for Core faculty who have variable
    assignments across all three duty types. Role-based faculty (PD, APD,
    OIC, Dept Chief) have fixed patterns and may be excluded.

    The penalty increases when workload scores are imbalanced, encouraging
    the solver to distribute duties more evenly.
    """

    def __init__(
        self,
        weight: float = 15.0,
        call_weight: float = CALL_WEIGHT,
        fmit_weight: float = FMIT_WEIGHT,
        clinic_weight: float = CLINIC_WEIGHT,
        include_titled_faculty: bool = False,
    ) -> None:
        """
        Initialize integrated workload constraint.

        Args:
            weight: Penalty weight for workload imbalance (default 15.0 - high priority)
            call_weight: Points per call shift (default 1.0)
            fmit_weight: Points per FMIT week (default 3.0)
            clinic_weight: Points per clinic half-day (default 0.5)
            include_titled_faculty: Whether to include PD/APD/OIC/Dept Chief
                                   (default False - Core faculty only)
        """
        super().__init__(
            name="IntegratedWorkload",
            constraint_type=ConstraintType.EQUITY,
            weight=weight,
            priority=ConstraintPriority.MEDIUM,
        )
        self.call_weight = call_weight
        self.fmit_weight = fmit_weight
        self.clinic_weight = clinic_weight
        self.include_titled_faculty = include_titled_faculty

    def _is_eligible_faculty(self, faculty: Any) -> bool:
        """
        Check if faculty should be included in workload balancing.

        By default, excludes titled faculty (PD, APD, OIC, Dept Chief)
        since they have fixed role-based assignments.
        """
        if self.include_titled_faculty:
            return True

        # Exclude faculty with specific titles that have fixed patterns
        titled_roles = {"pd", "apd", "oic", "dept_chief", "department_chief"}

        if hasattr(faculty, "faculty_role"):
            role = (faculty.faculty_role or "").lower().replace(" ", "_")
            if role in titled_roles:
                return False

        if hasattr(faculty, "title"):
            title = (faculty.title or "").lower().replace(" ", "_")
            if title in titled_roles:
                return False

        return True

    def _is_call_assignment(self, assignment: Any) -> bool:
        """Check if assignment is an overnight call."""
        return hasattr(assignment, "call_type") and assignment.call_type == "overnight"

    def _is_fmit_assignment(self, assignment: Any, context: SchedulingContext) -> bool:
        """Check if assignment is FMIT (inpatient teaching)."""
        if not hasattr(assignment, "rotation_template_id"):
            return False

        # Check if rotation template is FMIT
        for template in context.templates:
            if template.id == assignment.rotation_template_id:
                template_name = getattr(template, "name", "").upper()
                return "FMIT" in template_name

        return False

    def _is_clinic_assignment(
        self, assignment: Any, context: SchedulingContext
    ) -> bool:
        """Check if assignment is clinic (outpatient/clinic activity)."""
        if not hasattr(assignment, "rotation_template_id"):
            return False

        # Check if rotation template has clinic rotation type
        for template in context.templates:
            if template.id == assignment.rotation_template_id:
                rotation_type = getattr(template, "rotation_type", "")
                return rotation_type in ("outpatient", "clinic", "fm_clinic")

        return False

    def _is_admin_assignment(self, assignment: Any, context: SchedulingContext) -> bool:
        """Check if assignment is admin (GME, DFM)."""
        if not hasattr(assignment, "rotation_template_id"):
            return False

        for template in context.templates:
            if template.id == assignment.rotation_template_id:
                template_name = getattr(template, "name", "").upper()
                rotation_type = getattr(template, "rotation_type", "").lower()
                # GME = Graduate Medical Education, DFM = Department of Family Medicine
                return (
                    "GME" in template_name
                    or "DFM" in template_name
                    or rotation_type in ("admin", "administrative", "gme", "dfm")
                )

        return False

    def _is_academic_assignment(
        self, assignment: Any, context: SchedulingContext
    ) -> bool:
        """Check if assignment is academic time (LEC, ADV)."""
        if not hasattr(assignment, "rotation_template_id"):
            return False

        for template in context.templates:
            if template.id == assignment.rotation_template_id:
                template_name = getattr(template, "name", "").upper()
                rotation_type = getattr(template, "rotation_type", "").lower()
                # LEC = Lecture, ADV = Advising
                return (
                    "LEC" in template_name
                    or "ADV" in template_name
                    or "LECTURE" in template_name
                    or "ADVISING" in template_name
                    or rotation_type
                    in ("academic", "lecture", "advising", "lec", "adv")
                )

        return False

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add integrated workload equity to CP-SAT objective.

        Calculates workload scores per faculty and minimizes the maximum.
        """
        # Get relevant variables
        call_vars = variables.get("call_assignments", {})
        assignment_vars = variables.get("assignments", {})

        if not context.faculty:
            return

        # Filter to eligible faculty
        eligible_faculty = [f for f in context.faculty if self._is_eligible_faculty(f)]

        if not eligible_faculty:
            logger.debug("No eligible faculty for integrated workload constraint")
            return

        # Calculate workload score per faculty
        # Note: This is approximate since we can't easily track FMIT weeks
        # in the solver. We use assignment counts as proxies.

        workload_vars = {}
        max_blocks = len(context.blocks)

        for faculty in eligible_faculty:
            f_i = context.resident_idx.get(faculty.id)
            if f_i is None:
                continue

            # Count call assignments for this faculty
            call_count_vars = []
            for block in context.blocks:
                b_i = context.block_idx.get(block.id)
                if b_i is not None and (f_i, b_i, "overnight") in call_vars:
                    call_count_vars.append(call_vars[f_i, b_i, "overnight"])

            # Count general assignments (proxy for FMIT + clinic)
            assign_count_vars = []
            for block in context.blocks:
                b_i = context.block_idx.get(block.id)
                if b_i is not None and (f_i, b_i) in assignment_vars:
                    assign_count_vars.append(assignment_vars[f_i, b_i])

            # Create workload score variable (scaled by 10 for integer math)
            # workload = call * 10 + assignments * 5 (simplified)
            workload = model.NewIntVar(0, max_blocks * 15, f"workload_{f_i}")

            call_sum = sum(call_count_vars) if call_count_vars else 0
            assign_sum = sum(assign_count_vars) if assign_count_vars else 0

            # Weighted sum (scaled to integers)
            model.Add(workload == call_sum * 10 + assign_sum * 5)

            workload_vars[f_i] = workload

        if not workload_vars:
            return

        # Minimize maximum workload
        max_workload = model.NewIntVar(0, max_blocks * 15, "max_workload")
        for f_i, workload in workload_vars.items():
            model.Add(workload <= max_workload)

        # Add to objective
        objective_vars = variables.get("objective_terms", [])
        objective_vars.append((max_workload, int(self.weight)))
        variables["objective_terms"] = objective_vars

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add integrated workload equity to PuLP objective."""
        import pulp

        call_vars = variables.get("call_assignments", {})
        assignment_vars = variables.get("assignments", {})

        if not context.faculty:
            return

        eligible_faculty = [f for f in context.faculty if self._is_eligible_faculty(f)]

        if not eligible_faculty:
            return

        max_blocks = len(context.blocks)
        workload_exprs = []

        for faculty in eligible_faculty:
            f_i = context.resident_idx.get(faculty.id)
            if f_i is None:
                continue

            # Count call assignments
            call_count_vars = []
            for block in context.blocks:
                b_i = context.block_idx.get(block.id)
                if b_i is not None and (f_i, b_i, "overnight") in call_vars:
                    call_count_vars.append(call_vars[f_i, b_i, "overnight"])

            # Count assignments
            assign_count_vars = []
            for block in context.blocks:
                b_i = context.block_idx.get(block.id)
                if b_i is not None and (f_i, b_i) in assignment_vars:
                    assign_count_vars.append(assignment_vars[f_i, b_i])

            # Workload expression
            call_sum = pulp.lpSum(call_count_vars) if call_count_vars else 0
            assign_sum = pulp.lpSum(assign_count_vars) if assign_count_vars else 0

            workload_expr = call_sum * 10 + assign_sum * 5
            workload_exprs.append(workload_expr)

        if not workload_exprs:
            return

        # Minimize maximum workload
        max_workload = pulp.LpVariable("max_workload", lowBound=0, cat="Integer")
        for i, expr in enumerate(workload_exprs):
            model += expr <= max_workload, f"workload_max_{i}"

        if "objective" in variables:
            variables["objective"] += self.weight * max_workload

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """
        Validate workload distribution and calculate penalty.

        Returns detailed workload breakdown per faculty and overall
        fairness metrics.
        """
        faculty_by_id = {f.id: f for f in context.faculty}

        # Filter to eligible faculty
        eligible_ids = {f.id for f in context.faculty if self._is_eligible_faculty(f)}

        if not eligible_ids:
            return ConstraintResult(satisfied=True, penalty=0.0)

        # Calculate workload per faculty
        workloads: dict[str, FacultyWorkload] = {}
        fmit_weeks_seen: dict[str, set] = defaultdict(set)  # Track FMIT weeks

        for faculty_id in eligible_ids:
            faculty = faculty_by_id.get(faculty_id)
            name = getattr(faculty, "name", "Unknown") if faculty else "Unknown"
            workloads[faculty_id] = FacultyWorkload(
                person_id=str(faculty_id),
                person_name=name,
            )

        for assignment in assignments:
            if assignment.person_id not in eligible_ids:
                continue

            workload = workloads[assignment.person_id]

            # Count call
            if self._is_call_assignment(assignment):
                workload.call_count += 1

            # Count FMIT (by week to avoid double-counting)
            if self._is_fmit_assignment(assignment, context):
                # Get block date to determine week
                block = next(
                    (b for b in context.blocks if b.id == assignment.block_id), None
                )
                if block:
                    iso_week = block.date.isocalendar()[:2]  # (year, week)
                    if iso_week not in fmit_weeks_seen[assignment.person_id]:
                        fmit_weeks_seen[assignment.person_id].add(iso_week)
                        workload.fmit_weeks += 1

            # Count clinic
            if self._is_clinic_assignment(assignment, context):
                workload.clinic_halfdays += 1

            # Count admin
            if self._is_admin_assignment(assignment, context):
                workload.admin_halfdays += 1

            # Count academic
            if self._is_academic_assignment(assignment, context):
                workload.academic_halfdays += 1

        if not workloads:
            return ConstraintResult(satisfied=True, penalty=0.0)

        # Calculate per-category statistics
        def calc_stats(values: list) -> dict:
            if not values:
                return {"min": 0, "max": 0, "mean": 0.0, "spread": 0}
            return {
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / len(values),
                "spread": max(values) - min(values),
            }

        workload_list = list(workloads.values())

        call_stats = calc_stats([w.call_count for w in workload_list])
        fmit_stats = calc_stats([w.fmit_weeks for w in workload_list])
        clinic_stats = calc_stats([w.clinic_halfdays for w in workload_list])
        admin_stats = calc_stats([w.admin_halfdays for w in workload_list])
        academic_stats = calc_stats([w.academic_halfdays for w in workload_list])

        # Calculate total score statistics
        scores = [w.total_score for w in workload_list]
        max_score = max(scores) if scores else 0
        min_score = min(scores) if scores else 0
        mean_score = sum(scores) / len(scores) if scores else 0
        spread = max_score - min_score

        # Variance-based penalty
        variance = (
            sum((s - mean_score) ** 2 for s in scores) / len(scores) if scores else 0
        )
        penalty = variance * self.weight

        # Generate violations for significant imbalances
        violations = []

        if (
            spread > mean_score * 0.5 and mean_score > 0
        ):  # More than 50% spread is concerning
            # Find outliers
            high_workload = [
                w for w in workload_list if w.total_score > mean_score * 1.25
            ]
            low_workload = [
                w for w in workload_list if w.total_score < mean_score * 0.75
            ]

            if high_workload or low_workload:
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="MEDIUM",
                        message=f"Workload imbalance: scores range {min_score:.1f} to {max_score:.1f} (mean: {mean_score:.1f})",
                        details={
                            "min_score": min_score,
                            "max_score": max_score,
                            "mean_score": mean_score,
                            "spread": spread,
                            "variance": variance,
                            "high_workload_faculty": [
                                w.person_name for w in high_workload
                            ],
                            "low_workload_faculty": [
                                w.person_name for w in low_workload
                            ],
                        },
                    )
                )

        # Flag specific category imbalances
        if clinic_stats["spread"] > 3:  # More than 3 half-days difference
            violations.append(
                ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity="LOW",
                    message=f"Clinic imbalance: {clinic_stats['min']}-{clinic_stats['max']} half-days",
                    details=clinic_stats,
                )
            )

        return ConstraintResult(
            satisfied=True,  # Soft constraint
            violations=violations,
            penalty=penalty,
            details={
                "workloads": [w.to_dict() for w in workload_list],
                "category_stats": {
                    "call": call_stats,
                    "fmit": fmit_stats,
                    "clinic": clinic_stats,
                    "admin": admin_stats,
                    "academic": academic_stats,
                },
                "total_score_stats": {
                    "min": min_score,
                    "max": max_score,
                    "mean": mean_score,
                    "spread": spread,
                    "variance": variance,
                },
            },
        )


def calculate_workload_report(
    assignments: list[Any],
    context: SchedulingContext,
    include_titled: bool = False,
) -> dict:
    """
    Convenience function to generate a workload report.

    Returns a dictionary with workload breakdown per faculty and
    overall statistics.

    Args:
        assignments: List of assignment objects
        context: Scheduling context with faculty, blocks, templates
        include_titled: Whether to include titled faculty (PD, APD, etc.)

    Returns:
        Dictionary with 'workloads' and 'statistics' keys
    """
    constraint = IntegratedWorkloadConstraint(include_titled_faculty=include_titled)
    result = constraint.validate(assignments, context)
    return result.details or {}
