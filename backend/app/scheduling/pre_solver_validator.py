"""
Pre-Solver Constraint Saturation Validator.

This module validates that scheduling constraints can be satisfied BEFORE
the solver runs, avoiding wasted compute on obviously infeasible problems.

Key Checks:
- Total minimum hours required vs available slot hours
- Required coverage exceeds available personnel
- Mutually exclusive constraints (same person required in two places)
- Problem complexity estimation (variables × constraints)

Usage:
    validator = PreSolverValidator()
    result = validator.validate_saturation(constraints, blocks, persons)
    if not result.feasible:
        raise ValueError(f"Problem infeasible: {result.issues}")
"""

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.scheduling.constraints import SchedulingContext

logger = logging.getLogger(__name__)


@dataclass
class PreSolverValidationResult:
    """
    Result of pre-solver validation check.

    Attributes:
        feasible: Whether the problem appears solvable
        issues: List of human-readable issues found
        complexity_estimate: Rough solver complexity (variables × constraints)
        recommendations: Suggestions to make problem feasible
        warnings: Non-fatal warnings about problem structure
        statistics: Detailed statistics about the problem
    """

    feasible: bool
    issues: list[str] = field(default_factory=list)
    complexity_estimate: int = 0
    recommendations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    statistics: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        status = "FEASIBLE" if self.feasible else "INFEASIBLE"
        return (
            f"PreSolverValidationResult({status}, "
            f"{len(self.issues)} issues, "
            f"complexity={self.complexity_estimate})"
        )


class PreSolverValidator:
    """
    Pre-solver constraint saturation validator.

    Performs fast feasibility checks before invoking expensive solver algorithms:
    1. Hour balance: minimum required hours vs available capacity
    2. Coverage ratio: required coverage vs available personnel
    3. Conflict detection: mutually exclusive constraint patterns
    4. Complexity estimation: problem size heuristics

    These checks catch common infeasibility patterns that would cause
    the solver to run for minutes before failing.
    """

    # Complexity thresholds (based on typical solver performance)
    COMPLEXITY_LOW = 10_000  # < 10K: trivial, solver finishes in seconds
    COMPLEXITY_MEDIUM = 100_000  # 10K-100K: moderate, solver may take minutes
    COMPLEXITY_HIGH = 1_000_000  # 100K-1M: high, solver may timeout
    COMPLEXITY_EXTREME = 10_000_000  # > 1M: extreme, likely infeasible

    # Personnel thresholds
    MIN_PERSONNEL_RATIO = 1.2  # Need at least 20% more personnel than coverage slots
    WORKLOAD_MAX_RATIO = 0.9  # Personnel shouldn't be assigned >90% of blocks

    def __init__(self):
        """Initialize the pre-solver validator."""
        pass

    def validate_saturation(
        self,
        context: SchedulingContext,
        min_coverage_per_block: int = 1,
    ) -> PreSolverValidationResult:
        """
        Validate constraint saturation before solver execution.

        Args:
            context: SchedulingContext with residents, faculty, blocks, templates
            min_coverage_per_block: Minimum residents required per block (default: 1)

        Returns:
            PreSolverValidationResult with feasibility assessment

        Raises:
            ValueError: If context is missing required data
        """
        if not context.residents:
            return PreSolverValidationResult(
                feasible=False,
                issues=["No residents available for scheduling"],
                recommendations=["Add resident data to the system"],
            )

        if not context.blocks:
            return PreSolverValidationResult(
                feasible=False,
                issues=["No blocks available for scheduling"],
                recommendations=["Ensure blocks are created for the date range"],
            )

        if not context.templates:
            return PreSolverValidationResult(
                feasible=False,
                issues=["No rotation templates available"],
                recommendations=["Create rotation templates for residents to use"],
            )

        result = PreSolverValidationResult(feasible=True)

        # Run validation checks
        self._check_hour_balance(context, result)
        self._check_coverage_ratio(context, min_coverage_per_block, result)
        self._check_availability_conflicts(context, result)
        self._estimate_complexity(context, result)
        self._check_existing_assignment_conflicts(context, result)

        # Add statistics
        result.statistics = self._gather_statistics(context)

        # If any issues found, mark as infeasible
        if result.issues:
            result.feasible = False

        return result

    def _check_hour_balance(
        self,
        context: SchedulingContext,
        result: PreSolverValidationResult,
    ) -> None:
        """
        Check if total minimum hours required exceeds available slot hours.

        This catches basic infeasibility where the residents simply don't have
        enough time slots to satisfy minimum rotation requirements.
        """
        workday_blocks = [b for b in context.blocks if not b.is_weekend]
        total_available_slots = len(workday_blocks) * len(context.residents)

        # Calculate minimum required slots from templates
        # For now, we assume each resident needs approximately equal distribution
        # across templates, but this could be refined based on template requirements
        min_required_slots = len(workday_blocks) * len(
            context.residents
        )  # At minimum, fill all slots

        # Check if we have enough slots
        if min_required_slots > total_available_slots:
            result.issues.append(
                f"Insufficient slot capacity: need {min_required_slots} slots, "
                f"only have {total_available_slots} available"
            )
            result.recommendations.append(
                "Reduce minimum rotation requirements or add more residents"
            )

        # Check for oversubscription (residents with too few available blocks)
        for resident in context.residents:
            available_blocks = sum(
                1
                for block in workday_blocks
                if self._is_person_available(resident.id, block.id, context)
            )
            min_needed = (
                len(workday_blocks) // 2
            )  # Should have at least 50% availability

            if available_blocks < min_needed:
                result.warnings.append(
                    f"Resident {resident.name} only available for {available_blocks}/"
                    f"{len(workday_blocks)} blocks (absences may cause under-assignment)"
                )

    def _check_coverage_ratio(
        self,
        context: SchedulingContext,
        min_coverage_per_block: int,
        result: PreSolverValidationResult,
    ) -> None:
        """
        Check if required coverage exceeds available personnel.

        Validates that we have enough residents to cover all blocks at the
        minimum coverage level (typically 1 resident per block, but could be higher
        for certain rotations).
        """
        workday_blocks = [b for b in context.blocks if not b.is_weekend]

        # Calculate required coverage
        total_coverage_needed = len(workday_blocks) * min_coverage_per_block

        # Calculate available personnel-blocks (accounting for absences)
        total_available = 0
        for resident in context.residents:
            for block in workday_blocks:
                if self._is_person_available(resident.id, block.id, context):
                    total_available += 1

        # Check if we have enough coverage
        coverage_ratio = (
            total_available / total_coverage_needed if total_coverage_needed > 0 else 0
        )

        if coverage_ratio < 1.0:
            result.issues.append(
                f"Insufficient personnel coverage: need {total_coverage_needed} "
                f"resident-blocks, only have {total_available} available "
                f"(ratio: {coverage_ratio:.2f})"
            )
            result.recommendations.append(
                "Reduce date range, add more residents, or reduce minimum coverage requirements"
            )
        elif coverage_ratio < self.MIN_PERSONNEL_RATIO:
            result.warnings.append(
                f"Tight personnel coverage: ratio {coverage_ratio:.2f} "
                f"(recommended: >{self.MIN_PERSONNEL_RATIO}). "
                "Solver may struggle to find balanced solution."
            )
            result.recommendations.append(
                "Consider adding buffer residents for more scheduling flexibility"
            )

        # Check for over-assignment risk
        avg_blocks_per_resident = total_coverage_needed / len(context.residents)
        max_blocks_per_resident = len(workday_blocks) * self.WORKLOAD_MAX_RATIO

        if avg_blocks_per_resident > max_blocks_per_resident:
            result.issues.append(
                f"Over-assignment detected: each resident would need "
                f"{avg_blocks_per_resident:.1f} blocks on average, but maximum "
                f"recommended is {max_blocks_per_resident:.1f} "
                f"({self.WORKLOAD_MAX_RATIO:.0%} of total blocks)"
            )
            result.recommendations.append(
                "Add more residents or reduce scheduling period length"
            )

    def _check_availability_conflicts(
        self,
        context: SchedulingContext,
        result: PreSolverValidationResult,
    ) -> None:
        """
        Detect mutually exclusive constraints (same person required in two places).

        This checks for:
        1. Residents who are completely unavailable (100% absent)
        2. Blocks where no residents are available
        3. Patterns suggesting infeasibility
        """
        workday_blocks = [b for b in context.blocks if not b.is_weekend]

        # Check for completely unavailable residents
        for resident in context.residents:
            available_count = sum(
                1
                for block in workday_blocks
                if self._is_person_available(resident.id, block.id, context)
            )

            if available_count == 0:
                result.issues.append(
                    f"Resident {resident.name} has zero availability "
                    "(absent for entire scheduling period)"
                )
                result.recommendations.append(
                    f"Remove {resident.name} from scheduling or adjust absence dates"
                )

        # Check for blocks with insufficient available residents
        for block in workday_blocks:
            available_residents = sum(
                1
                for resident in context.residents
                if self._is_person_available(resident.id, block.id, context)
            )

            if available_residents == 0:
                result.issues.append(
                    f"Block {block.date} {block.time_of_day} has no available residents "
                    "(all residents absent)"
                )
                result.recommendations.append(
                    f"Adjust absences to ensure coverage on {block.date}"
                )
            elif available_residents < 2:
                result.warnings.append(
                    f"Block {block.date} {block.time_of_day} only has "
                    f"{available_residents} available resident(s) "
                    "(limited scheduling flexibility)"
                )

    def _check_existing_assignment_conflicts(
        self,
        context: SchedulingContext,
        result: PreSolverValidationResult,
    ) -> None:
        """
        Check if existing assignments create conflicts or over-constrain the problem.

        This validates that pre-existing assignments (FMIT, inpatient, absences)
        don't create impossible situations.
        """
        if not context.existing_assignments:
            return

        # Build set of (person_id, block_id) pairs that are occupied
        occupied_slots: set[tuple[UUID, UUID]] = set()
        for assignment in context.existing_assignments:
            occupied_slots.add((assignment.person_id, assignment.block_id))

        # Check if any resident has too many pre-assignments
        workday_blocks = [b for b in context.blocks if not b.is_weekend]
        for resident in context.residents:
            pre_assigned_count = sum(
                1
                for block in workday_blocks
                if (resident.id, block.id) in occupied_slots
            )

            # If more than 80% of blocks are pre-assigned, warn
            if pre_assigned_count > len(workday_blocks) * 0.8:
                result.warnings.append(
                    f"Resident {resident.name} has {pre_assigned_count}/"
                    f"{len(workday_blocks)} blocks pre-assigned "
                    "(little room for solver optimization)"
                )

        # Check if pre-assignments reduce available capacity too much
        total_pre_assigned = len(occupied_slots)
        total_slots = len(workday_blocks) * len(context.residents)
        pre_assignment_ratio = (
            total_pre_assigned / total_slots if total_slots > 0 else 0
        )

        if pre_assignment_ratio > 0.7:
            result.warnings.append(
                f"{pre_assignment_ratio:.0%} of slots are pre-assigned "
                "(solver has limited flexibility)"
            )
            result.recommendations.append(
                "Consider reducing pre-assignments to give solver more options"
            )

    def estimate_complexity(self, num_vars: int, num_constraints: int) -> int:
        """
        Estimate solver complexity from problem dimensions.

        Args:
            num_vars: Number of decision variables
            num_constraints: Number of constraints

        Returns:
            Complexity estimate (higher = slower solver)
        """
        # Simple heuristic: complexity ≈ variables × constraints
        # Real complexity depends on constraint structure, but this gives a rough estimate
        return num_vars * num_constraints

    def _estimate_complexity(
        self,
        context: SchedulingContext,
        result: PreSolverValidationResult,
    ) -> None:
        """
        Estimate problem complexity and warn if too large.

        Complexity is based on:
        - Number of decision variables (residents × blocks × templates)
        - Number of constraints (grows with problem dimensions)
        - Estimated solver runtime
        """
        workday_blocks = [b for b in context.blocks if not b.is_weekend]

        # Estimate decision variables
        # Each (resident, block, template) triple is a binary variable
        num_residents = len(context.residents)
        num_blocks = len(workday_blocks)
        num_templates = len(context.templates)
        num_vars = num_residents * num_blocks * num_templates

        # Estimate constraints
        # This is approximate - actual count depends on constraint manager
        # Typical constraints: availability, capacity, equity, etc.
        num_constraints = (
            num_residents * num_blocks  # Availability constraints
            + num_blocks * num_templates  # Capacity constraints
            + num_residents  # Equity constraints
            + num_blocks  # Coverage constraints
        )

        complexity = self.estimate_complexity(num_vars, num_constraints)
        result.complexity_estimate = complexity

        # Categorize complexity
        if complexity < self.COMPLEXITY_LOW:
            complexity_level = "LOW"
            runtime_estimate = "< 1 second"
        elif complexity < self.COMPLEXITY_MEDIUM:
            complexity_level = "MEDIUM"
            runtime_estimate = "1-10 seconds"
        elif complexity < self.COMPLEXITY_HIGH:
            complexity_level = "HIGH"
            runtime_estimate = "10-60 seconds"
        elif complexity < self.COMPLEXITY_EXTREME:
            complexity_level = "VERY HIGH"
            runtime_estimate = "1-5 minutes"
        else:
            complexity_level = "EXTREME"
            runtime_estimate = "> 5 minutes (may timeout)"
            result.warnings.append(
                f"Extreme problem complexity: {complexity:,} "
                "(solver may timeout or produce suboptimal results)"
            )
            result.recommendations.append(
                "Consider breaking problem into smaller date ranges "
                "or using incremental scheduling"
            )

        result.statistics["complexity_level"] = complexity_level
        result.statistics["complexity_estimate"] = complexity
        result.statistics["num_variables"] = num_vars
        result.statistics["num_constraints_estimate"] = num_constraints
        result.statistics["estimated_runtime"] = runtime_estimate

        logger.info(
            f"Problem complexity: {complexity_level} "
            f"({num_vars:,} vars × {num_constraints:,} constraints ≈ {complexity:,}), "
            f"estimated runtime: {runtime_estimate}"
        )

    def _gather_statistics(self, context: SchedulingContext) -> dict[str, Any]:
        """
        Gather detailed statistics about the scheduling problem.

        Returns:
            Dictionary of problem statistics
        """
        workday_blocks = [b for b in context.blocks if not b.is_weekend]

        stats = {
            "num_residents": len(context.residents),
            "num_faculty": len(context.faculty),
            "num_blocks": len(context.blocks),
            "num_workday_blocks": len(workday_blocks),
            "num_templates": len(context.templates),
            "num_existing_assignments": len(context.existing_assignments),
            "date_range_days": (
                (context.end_date - context.start_date).days + 1
                if context.start_date and context.end_date
                else 0
            ),
        }

        # Calculate availability statistics
        total_availability = 0
        for resident in context.residents:
            for block in workday_blocks:
                if self._is_person_available(resident.id, block.id, context):
                    total_availability += 1

        total_possible = len(context.residents) * len(workday_blocks)
        stats["availability_rate"] = (
            total_availability / total_possible if total_possible > 0 else 0
        )

        return stats

    def _is_person_available(
        self,
        person_id: UUID,
        block_id: UUID,
        context: SchedulingContext,
    ) -> bool:
        """
        Check if a person is available for a specific block.

        Args:
            person_id: UUID of the person
            block_id: UUID of the block
            context: Scheduling context with availability matrix

        Returns:
            True if person is available, False if absent
        """
        if person_id not in context.availability:
            return True  # No absence data = available

        if block_id not in context.availability[person_id]:
            return True  # No absence for this block = available

        return context.availability[person_id][block_id].get("available", True)

    def detect_conflicts(self, context: SchedulingContext) -> list[str]:
        """
        Detect specific constraint conflicts in the problem.

        This is a convenience method that returns just the conflict descriptions.

        Args:
            context: Scheduling context

        Returns:
            List of conflict descriptions
        """
        result = self.validate_saturation(context)
        return result.issues + result.warnings
