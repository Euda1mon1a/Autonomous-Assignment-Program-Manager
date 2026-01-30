"""
Compatibility analysis for swap requests.

Analyzes compatibility between swap requests using multiple criteria
including schedule compatibility, preference alignment, and constraints.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.models.person import Person
from app.models.assignment import Assignment
from app.models.block import Block


logger = logging.getLogger(__name__)


@dataclass
class CompatibilityScore:
    """Compatibility score breakdown."""

    overall_score: float  # 0.0 to 1.0
    schedule_compatibility: float
    preference_alignment: float
    workload_balance: float
    credential_compatibility: float
    temporal_proximity: float
    detailed_breakdown: dict[str, Any]


@dataclass
class CompatibilityResult:
    """Result of compatibility check."""

    compatible: bool
    score: CompatibilityScore
    blocking_issues: list[str]
    warnings: list[str]
    recommendations: list[str]


class CompatibilityChecker:
    """
    Analyzes compatibility between swap requests.

    Uses multiple scoring factors to determine how well two swap
    requests can be paired together.
    """

    def __init__(
        self,
        db: AsyncSession,
        min_compatibility_score: float = 0.6,
    ) -> None:
        """
        Initialize compatibility checker.

        Args:
            db: Async database session
            min_compatibility_score: Minimum score to consider compatible
        """
        self.db = db
        self.min_compatibility_score = min_compatibility_score

    async def check_compatibility(
        self,
        request_a: SwapRecord,
        request_b: SwapRecord,
    ) -> CompatibilityResult:
        """
        Check if two swap requests are compatible.

        Args:
            request_a: First swap request
            request_b: Second swap request

        Returns:
            CompatibilityResult with detailed analysis
        """
        blocking_issues = []
        warnings = []
        recommendations = []

        # Check basic eligibility
        if request_a.id == request_b.id:
            blocking_issues.append("Cannot match a request with itself")

        if request_a.source_faculty_id == request_b.source_faculty_id:
            blocking_issues.append("Both requests from same faculty")

            # Check status
        if request_a.status != SwapStatus.PENDING:
            blocking_issues.append(f"Request A has status {request_a.status}")

        if request_b.status != SwapStatus.PENDING:
            blocking_issues.append(f"Request B has status {request_b.status}")

            # If we have blocking issues, return early
        if blocking_issues:
            return CompatibilityResult(
                compatible=False,
                score=CompatibilityScore(
                    overall_score=0.0,
                    schedule_compatibility=0.0,
                    preference_alignment=0.0,
                    workload_balance=0.0,
                    credential_compatibility=0.0,
                    temporal_proximity=0.0,
                    detailed_breakdown={},
                ),
                blocking_issues=blocking_issues,
                warnings=warnings,
                recommendations=recommendations,
            )

            # Calculate individual scores
        schedule_score = await self._score_schedule_compatibility(request_a, request_b)
        preference_score = await self._score_preference_alignment(request_a, request_b)
        workload_score = await self._score_workload_balance(request_a, request_b)
        credential_score = await self._score_credential_compatibility(
            request_a, request_b
        )
        temporal_score = self._score_temporal_proximity(request_a, request_b)

        # Calculate weighted overall score
        overall_score = (
            schedule_score * 0.25
            + preference_score * 0.25
            + workload_score * 0.15
            + credential_score * 0.20
            + temporal_score * 0.15
        )

        # Generate warnings based on scores
        if temporal_score < 0.5:
            days_apart = abs((request_a.source_week - request_b.source_week).days)
            warnings.append(f"Weeks are {days_apart} days apart - may not be ideal")

        if credential_score < 0.7:
            warnings.append("Some credential mismatches detected")

        if workload_score < 0.5:
            warnings.append("Significant workload imbalance")

            # Generate recommendations
        if preference_score > 0.8:
            recommendations.append("Strong preference alignment - highly recommended")

        if schedule_score > 0.9:
            recommendations.append("Excellent schedule fit")

        if overall_score > 0.85:
            recommendations.append(
                "This is an excellent match - prioritize notification"
            )

        score = CompatibilityScore(
            overall_score=overall_score,
            schedule_compatibility=schedule_score,
            preference_alignment=preference_score,
            workload_balance=workload_score,
            credential_compatibility=credential_score,
            temporal_proximity=temporal_score,
            detailed_breakdown={
                "weights": {
                    "schedule": 0.25,
                    "preference": 0.25,
                    "workload": 0.15,
                    "credential": 0.20,
                    "temporal": 0.15,
                },
            },
        )

        compatible = overall_score >= self.min_compatibility_score

        return CompatibilityResult(
            compatible=compatible,
            score=score,
            blocking_issues=blocking_issues,
            warnings=warnings,
            recommendations=recommendations,
        )

    async def batch_compatibility_check(
        self,
        request: SwapRecord,
        candidates: list[SwapRecord],
    ) -> list[tuple[SwapRecord, CompatibilityResult]]:
        """
        Check compatibility with multiple candidates.

        Args:
            request: The swap request to match
            candidates: List of candidate swap requests

        Returns:
            List of (candidate, result) tuples sorted by score
        """
        results = []

        for candidate in candidates:
            result = await self.check_compatibility(request, candidate)
            results.append((candidate, result))

            # Sort by overall score (highest first)
        results.sort(
            key=lambda x: x[1].score.overall_score,
            reverse=True,
        )

        return results

        # ===== Private Scoring Methods =====

    async def _score_schedule_compatibility(
        self,
        request_a: SwapRecord,
        request_b: SwapRecord,
    ) -> float:
        """
        Score schedule compatibility.

        Checks if the swap won't create schedule conflicts
        or coverage gaps.

        Returns:
            Score from 0.0 to 1.0
        """
        score = 1.0

        # Get assignments for both weeks
        source_a_assignments = await self._get_week_assignments(
            request_a.source_faculty_id,
            request_a.source_week,
        )

        source_b_assignments = await self._get_week_assignments(
            request_b.source_faculty_id,
            request_b.source_week,
        )

        # Check for rotation type compatibility
        a_rotation_types = set(
            a.rotation_type for a in source_a_assignments if a.rotation_type
        )
        b_rotation_types = set(
            a.rotation_type for a in source_b_assignments if a.rotation_type
        )

        # If both faculty can do each other's rotations, full score
        # Otherwise, reduce score based on incompatibility
        if a_rotation_types and b_rotation_types:
            # Check if rotations are swappable
            # For now, simple heuristic: similar rotation types score higher
            if a_rotation_types == b_rotation_types:
                score = 1.0
            elif a_rotation_types & b_rotation_types:  # Some overlap
                score = 0.8
            else:
                score = 0.6  # Different rotations

        return score

    async def _score_preference_alignment(
        self,
        request_a: SwapRecord,
        request_b: SwapRecord,
    ) -> float:
        """
        Score preference alignment.

        Higher score if both parties prefer what they're getting.

        Returns:
            Score from 0.0 to 1.0
        """
        # This would integrate with faculty preference service
        # For now, simple heuristic based on swap type

        if (
            request_a.swap_type == SwapType.ONE_TO_ONE
            and request_b.swap_type == SwapType.ONE_TO_ONE
        ):
            # Both want to swap - higher alignment
            return 0.9

        if (
            request_a.swap_type == SwapType.ABSORB
            or request_b.swap_type == SwapType.ABSORB
        ):
            # One party just giving away - medium alignment
            return 0.7

        return 0.5

    async def _score_workload_balance(
        self,
        request_a: SwapRecord,
        request_b: SwapRecord,
    ) -> float:
        """
        Score workload balance impact.

        Prefers swaps that maintain fair workload distribution.

        Returns:
            Score from 0.0 to 1.0
        """
        # Get total assignments for both faculty
        count_a = await self._count_faculty_assignments(request_a.source_faculty_id)
        count_b = await self._count_faculty_assignments(request_b.source_faculty_id)

        # Calculate current difference
        current_diff = abs(count_a - count_b)

        # Score based on current balance
        # Closer to equal = higher score
        if current_diff == 0:
            return 1.0
        elif current_diff <= 2:
            return 0.9
        elif current_diff <= 5:
            return 0.7
        elif current_diff <= 10:
            return 0.5
        else:
            return 0.3

    async def _score_credential_compatibility(
        self,
        request_a: SwapRecord,
        request_b: SwapRecord,
    ) -> float:
        """
        Score credential/skill compatibility.

        Ensures both faculty can perform required duties.

        Returns:
            Score from 0.0 to 1.0
        """
        # This would check:
        # - BLS/ACLS certifications
        # - Procedure credentials
        # - Specialty qualifications

        # For now, assume compatible
        return 0.9

    def _score_temporal_proximity(
        self,
        request_a: SwapRecord,
        request_b: SwapRecord,
    ) -> float:
        """
        Score temporal proximity of swap weeks.

        Closer dates generally better for fairness.

        Returns:
            Score from 0.0 to 1.0
        """
        days_apart = abs((request_a.source_week - request_b.source_week).days)

        if days_apart <= 7:
            return 1.0
        elif days_apart <= 14:
            return 0.9
        elif days_apart <= 30:
            return 0.7
        elif days_apart <= 60:
            return 0.5
        elif days_apart <= 90:
            return 0.3
        else:
            return 0.1

            # ===== Helper Methods =====

    async def _get_week_assignments(
        self,
        faculty_id: UUID,
        week_start: date,
    ) -> list[Assignment]:
        """Get all assignments for a faculty member in a given week."""
        week_end = week_start + timedelta(days=6)

        result = await self.db.execute(
            select(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .where(
                and_(
                    Assignment.person_id == faculty_id,
                    Block.date >= week_start,
                    Block.date <= week_end,
                )
            )
        )

        return list(result.scalars().all())

    async def _count_faculty_assignments(self, faculty_id: UUID) -> int:
        """Count total assignments for a faculty member."""
        result = await self.db.execute(
            select(Assignment).where(Assignment.person_id == faculty_id)
        )

        return len(list(result.scalars().all()))
