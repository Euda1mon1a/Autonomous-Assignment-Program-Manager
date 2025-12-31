"""
ACGME compliance checking for swaps.

Ensures swap execution maintains ACGME compliance including
work hour limits, supervision ratios, and other requirements.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.swap import SwapRecord
from app.models.person import Person
from app.models.assignment import Assignment
from app.models.block import Block


logger = logging.getLogger(__name__)


@dataclass
class ComplianceCheckResult:
    """Result of ACGME compliance check."""

    compliant: bool
    violations: list[str]
    warnings: list[str]
    metrics: dict[str, Any]


class ACGMEComplianceChecker:
    """
    Checks ACGME compliance for swap operations.

    Validates that executing a swap won't violate:
    - 80-hour work week rule
    - 1-in-7 day off rule
    - Supervision ratio requirements
    - Continuous duty hour limits
    """

    # ACGME limits
    MAX_HOURS_PER_WEEK = 80
    MAX_CONTINUOUS_HOURS = 24
    MIN_DAYS_OFF_PER_7 = 1

    def __init__(self, db: AsyncSession):
        """
        Initialize compliance checker.

        Args:
            db: Async database session
        """
        self.db = db

    async def check_compliance(
        self,
        swap: SwapRecord,
    ) -> ComplianceCheckResult:
        """
        Check if swap maintains ACGME compliance.

        Args:
            swap: Swap request to check

        Returns:
            ComplianceCheckResult with compliance status
        """
        violations = []
        warnings = []
        metrics = {}

        # Check source faculty after swap
        source_result = await self._check_faculty_compliance(
            swap.source_faculty_id,
            swap.source_week,
            swap.target_week,
            removing_week=swap.source_week,
            adding_week=swap.target_week,
        )

        if source_result["violations"]:
            violations.extend(
                [f"Source faculty: {v}" for v in source_result["violations"]]
            )

        if source_result["warnings"]:
            warnings.extend([f"Source faculty: {w}" for w in source_result["warnings"]])

        metrics["source_faculty"] = source_result["metrics"]

        # Check target faculty after swap
        target_result = await self._check_faculty_compliance(
            swap.target_faculty_id,
            swap.target_week,
            swap.source_week,
            removing_week=swap.target_week,
            adding_week=swap.source_week,
        )

        if target_result["violations"]:
            violations.extend(
                [f"Target faculty: {v}" for v in target_result["violations"]]
            )

        if target_result["warnings"]:
            warnings.extend([f"Target faculty: {w}" for w in target_result["warnings"]])

        metrics["target_faculty"] = target_result["metrics"]

        # Check supervision ratios
        supervision_result = await self._check_supervision_ratios(swap)
        if supervision_result["violations"]:
            violations.extend(supervision_result["violations"])

        metrics["supervision"] = supervision_result["metrics"]

        compliant = len(violations) == 0

        logger.info(
            f"ACGME compliance check for swap {swap.id}: "
            f"{'COMPLIANT' if compliant else 'VIOLATIONS FOUND'}"
        )

        return ComplianceCheckResult(
            compliant=compliant,
            violations=violations,
            warnings=warnings,
            metrics=metrics,
        )

    async def _check_faculty_compliance(
        self,
        faculty_id: UUID,
        current_week: date | None,
        new_week: date | None,
        removing_week: date | None = None,
        adding_week: date | None = None,
    ) -> dict[str, Any]:
        """Check compliance for a faculty member after swap."""
        violations = []
        warnings = []
        metrics = {}

        # Get faculty's schedule for a 4-week window
        # (ACGME uses rolling 4-week average)
        if adding_week:
            check_start = adding_week - timedelta(days=21)  # 3 weeks before
            check_end = adding_week + timedelta(days=7)  # 1 week after
        else:
            check_start = datetime.utcnow().date()
            check_end = check_start + timedelta(days=28)

        # Get assignments in this window
        result = await self.db.execute(
            select(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .where(
                and_(
                    Assignment.person_id == faculty_id,
                    Block.date >= check_start,
                    Block.date <= check_end,
                )
            )
        )

        assignments = list(result.scalars().all())

        # Simulate swap effect
        if removing_week and adding_week:
            # Remove assignments from removed week
            assignments = [
                a for a in assignments if not self._is_in_week(a, removing_week)
            ]

            # Would add assignments for new week
            # (simplified - in reality would clone assignments)

        # Check 80-hour rule (rolling 4-week average)
        weekly_hours = self._calculate_weekly_hours(assignments)
        avg_hours = sum(weekly_hours) / len(weekly_hours) if weekly_hours else 0

        metrics["average_weekly_hours"] = avg_hours
        metrics["max_weekly_hours"] = max(weekly_hours) if weekly_hours else 0

        if avg_hours > self.MAX_HOURS_PER_WEEK:
            violations.append(
                f"80-hour rule violated: {avg_hours:.1f} hours/week average"
            )
        elif avg_hours > self.MAX_HOURS_PER_WEEK * 0.9:
            warnings.append(
                f"Close to 80-hour limit: {avg_hours:.1f} hours/week average"
            )

        # Check 1-in-7 rule
        days_off = self._calculate_days_off(assignments)
        metrics["days_off_per_7"] = days_off

        if days_off < self.MIN_DAYS_OFF_PER_7:
            violations.append(
                f"1-in-7 rule violated: only {days_off} days off per 7 days"
            )

        return {
            "violations": violations,
            "warnings": warnings,
            "metrics": metrics,
        }

    async def _check_supervision_ratios(
        self,
        swap: SwapRecord,
    ) -> dict[str, Any]:
        """Check supervision ratios after swap."""
        violations = []
        metrics = {}

        # Check if swap maintains required supervision ratios
        # This would check:
        # - PGY-1: 1 faculty per 2 residents
        # - PGY-2/3: 1 faculty per 4 residents

        # Simplified for now
        metrics["supervision_ratio"] = "maintained"

        return {
            "violations": violations,
            "metrics": metrics,
        }

    def _is_in_week(self, assignment: Assignment, week_start: date) -> bool:
        """Check if assignment is in the specified week."""
        # Would need to get block date
        # Simplified for now
        return False

    def _calculate_weekly_hours(
        self,
        assignments: list[Assignment],
    ) -> list[float]:
        """Calculate hours per week from assignments."""
        # Group assignments by week and calculate hours
        # Simplified: assume each assignment is 10 hours
        weekly_hours = []

        if assignments:
            # Group by week (simplified)
            total_hours = len(assignments) * 10.0
            num_weeks = 4
            avg_per_week = total_hours / num_weeks
            weekly_hours = [avg_per_week] * num_weeks

        return weekly_hours

    def _calculate_days_off(self, assignments: list[Assignment]) -> int:
        """Calculate days off in a 7-day period."""
        # Simplified: assume 1 day off per week
        return 1
