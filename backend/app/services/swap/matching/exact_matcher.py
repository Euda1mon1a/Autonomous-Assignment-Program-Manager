"""
Exact swap matching algorithm.

Finds perfect matches where two faculty members want exactly
what each other has (mutual swap).
"""

import logging
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.swap import SwapRecord, SwapStatus, SwapType


logger = logging.getLogger(__name__)


@dataclass
class ExactMatch:
    """Represents an exact mutual match."""

    request_a_id: UUID
    request_b_id: UUID
    faculty_a_id: UUID
    faculty_b_id: UUID
    week_a: date
    week_b: date
    match_score: float  # Always 1.0 for exact matches
    is_mutual: bool = True


class ExactMatcher:
    """
    Finds exact mutual matches between swap requests.

    An exact match occurs when:
    - Faculty A wants to give week X and get week Y
    - Faculty B wants to give week Y and get week X
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize exact matcher.

        Args:
            db: Async database session
        """
        self.db = db

    async def find_exact_matches(
        self,
        pending_only: bool = True,
    ) -> list[ExactMatch]:
        """
        Find all exact mutual matches.

        Args:
            pending_only: Only consider pending requests

        Returns:
            List of ExactMatch objects
        """
        # Get all swap requests
        query = select(SwapRecord)

        if pending_only:
            query = query.where(SwapRecord.status == SwapStatus.PENDING)

        query = query.where(SwapRecord.swap_type == SwapType.ONE_TO_ONE)

        result = await self.db.execute(query)
        requests = list(result.scalars().all())

        matches = []

        # Check each pair of requests
        for i, request_a in enumerate(requests):
            for request_b in requests[i + 1 :]:
                if self._is_exact_match(request_a, request_b):
                    match = ExactMatch(
                        request_a_id=request_a.id,
                        request_b_id=request_b.id,
                        faculty_a_id=request_a.source_faculty_id,
                        faculty_b_id=request_b.source_faculty_id,
                        week_a=request_a.source_week,
                        week_b=request_b.source_week,
                        match_score=1.0,
                        is_mutual=True,
                    )
                    matches.append(match)

        logger.info(f"Found {len(matches)} exact matches")

        return matches

    async def find_exact_match_for_request(
        self,
        request_id: UUID,
    ) -> ExactMatch | None:
        """
        Find exact match for a specific request.

        Args:
            request_id: The swap request ID

        Returns:
            ExactMatch if found, None otherwise
        """
        # Get the request
        result = await self.db.execute(
            select(SwapRecord).where(SwapRecord.id == request_id)
        )
        request = result.scalar_one_or_none()

        if not request:
            return None

        # Find matching request
        matching_query = select(SwapRecord).where(
            and_(
                SwapRecord.id != request_id,
                SwapRecord.status == SwapStatus.PENDING,
                SwapRecord.swap_type == SwapType.ONE_TO_ONE,
                SwapRecord.source_faculty_id == request.target_faculty_id,
                SwapRecord.target_faculty_id == request.source_faculty_id,
                SwapRecord.source_week == request.target_week,
                SwapRecord.target_week == request.source_week,
            )
        )

        result = await self.db.execute(matching_query)
        matching_request = result.scalar_one_or_none()

        if not matching_request:
            return None

        return ExactMatch(
            request_a_id=request.id,
            request_b_id=matching_request.id,
            faculty_a_id=request.source_faculty_id,
            faculty_b_id=matching_request.source_faculty_id,
            week_a=request.source_week,
            week_b=matching_request.source_week,
            match_score=1.0,
            is_mutual=True,
        )

    def _is_exact_match(
        self,
        request_a: SwapRecord,
        request_b: SwapRecord,
    ) -> bool:
        """
        Check if two requests are an exact match.

        Args:
            request_a: First request
            request_b: Second request

        Returns:
            True if exact match
        """
        if not request_a.target_week or not request_b.target_week:
            return False

        if not request_a.target_faculty_id or not request_b.target_faculty_id:
            return False

        # Check if they want each other's weeks
        a_wants_b = (
            request_a.target_faculty_id == request_b.source_faculty_id
            and request_a.target_week == request_b.source_week
        )

        b_wants_a = (
            request_b.target_faculty_id == request_a.source_faculty_id
            and request_b.target_week == request_a.source_week
        )

        return a_wants_b and b_wants_a
