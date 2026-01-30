"""
Coverage validation for swaps.

Ensures that executing a swap won't create coverage gaps
in critical services or rotations.
"""

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.swap import SwapRecord
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person


logger = logging.getLogger(__name__)


@dataclass
class CoverageCheckResult:
    """Result of coverage validation."""

    adequate: bool
    gaps: list[dict[str, Any]]
    warnings: list[str]
    coverage_metrics: dict[str, Any]


class CoverageValidator:
    """
    Validates coverage requirements for swaps.

    Ensures critical services maintain minimum staffing
    levels after a swap is executed.
    """

    # Minimum coverage requirements by rotation type
    MIN_COVERAGE = {
        "inpatient": 2,  # At least 2 faculty on inpatient
        "emergency": 1,  # At least 1 faculty in emergency
        "call": 1,  # At least 1 faculty on call
    }

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize coverage validator.

        Args:
            db: Async database session
        """
        self.db = db

    async def validate_coverage(
        self,
        swap: SwapRecord,
    ) -> CoverageCheckResult:
        """
        Validate coverage after swap execution.

        Args:
            swap: Swap request to validate

        Returns:
            CoverageCheckResult with coverage analysis
        """
        gaps = []
        warnings = []
        metrics = {}

        # Check coverage for source week after swap
        source_coverage = await self._check_week_coverage(
            swap.source_week,
            removing_faculty=swap.source_faculty_id,
            adding_faculty=swap.target_faculty_id,
        )

        if source_coverage["gaps"]:
            gaps.extend(source_coverage["gaps"])

        if source_coverage["warnings"]:
            warnings.extend(source_coverage["warnings"])

        metrics["source_week"] = source_coverage["metrics"]

        # Check coverage for target week after swap (if one-to-one)
        if swap.target_week:
            target_coverage = await self._check_week_coverage(
                swap.target_week,
                removing_faculty=swap.target_faculty_id,
                adding_faculty=swap.source_faculty_id,
            )

            if target_coverage["gaps"]:
                gaps.extend(target_coverage["gaps"])

            if target_coverage["warnings"]:
                warnings.extend(target_coverage["warnings"])

            metrics["target_week"] = target_coverage["metrics"]

        adequate = len(gaps) == 0

        logger.info(
            f"Coverage validation for swap {swap.id}: "
            f"{'ADEQUATE' if adequate else 'GAPS FOUND'} "
            f"({len(gaps)} gaps, {len(warnings)} warnings)"
        )

        return CoverageCheckResult(
            adequate=adequate,
            gaps=gaps,
            warnings=warnings,
            coverage_metrics=metrics,
        )

    async def _check_week_coverage(
        self,
        week_start: date,
        removing_faculty: UUID | None = None,
        adding_faculty: UUID | None = None,
    ) -> dict[str, Any]:
        """Check coverage for a specific week."""
        gaps = []
        warnings = []
        metrics = {}

        week_end = week_start + timedelta(days=6)

        # Get all assignments for this week
        result = await self.db.execute(
            select(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .where(
                and_(
                    Block.date >= week_start,
                    Block.date <= week_end,
                )
            )
        )

        assignments = list(result.scalars().all())

        # Simulate swap effect
        if removing_faculty:
            assignments = [a for a in assignments if a.person_id != removing_faculty]

            # Would add assignments for adding_faculty
            # (simplified - actual implementation would create new assignments)

            # Group assignments by rotation type and count faculty
        rotation_counts = {}

        for assignment in assignments:
            rotation_type = assignment.rotation_type or "unspecified"

            if rotation_type not in rotation_counts:
                rotation_counts[rotation_type] = set()

            rotation_counts[rotation_type].add(assignment.person_id)

            # Check against minimum requirements
        for rotation_type, min_count in self.MIN_COVERAGE.items():
            actual_count = len(rotation_counts.get(rotation_type, set()))

            if actual_count < min_count:
                gaps.append(
                    {
                        "rotation_type": rotation_type,
                        "week": week_start.isoformat(),
                        "required": min_count,
                        "actual": actual_count,
                        "severity": "critical" if actual_count == 0 else "warning",
                    }
                )

            elif actual_count == min_count:
                warnings.append(
                    f"{rotation_type} at minimum coverage ({min_count}) "
                    f"for week {week_start}"
                )

        metrics["rotation_counts"] = {k: len(v) for k, v in rotation_counts.items()}

        metrics["total_faculty"] = len(set(a.person_id for a in assignments))

        return {
            "gaps": gaps,
            "warnings": warnings,
            "metrics": metrics,
        }

    async def check_specialty_coverage(
        self,
        swap: SwapRecord,
    ) -> dict[str, Any]:
        """
        Check specialty-specific coverage requirements.

        Some rotations may require specific specialty expertise.
        """
        # Get specialties of faculty involved
        source_faculty = await self._get_faculty_specialty(swap.source_faculty_id)

        target_faculty = await self._get_faculty_specialty(swap.target_faculty_id)

        gaps = []

        # Check if specialty requirements are met
        # (Simplified - would check against rotation requirements)

        return {
            "gaps": gaps,
            "source_specialty": source_faculty,
            "target_specialty": target_faculty,
        }

    async def _get_faculty_specialty(self, faculty_id: UUID) -> str | None:
        """Get faculty member's specialty."""
        result = await self.db.execute(select(Person).where(Person.id == faculty_id))

        faculty = result.scalar_one_or_none()

        if faculty:
            # Would get from faculty.specialty field
            return "general"  # Placeholder

        return None
