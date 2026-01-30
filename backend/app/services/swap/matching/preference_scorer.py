"""
Preference-based scoring for swap matching.

Scores swap matches based on faculty preferences, historical
data, and learned patterns.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.models.person import Person


logger = logging.getLogger(__name__)


@dataclass
class PreferenceScore:
    """Preference-based compatibility score."""

    overall_score: float  # 0.0 to 1.0
    preference_match: float
    historical_success: float
    temporal_alignment: float
    workload_fairness: float
    details: dict[str, Any]


class PreferenceScorer:
    """
    Scores swap matches based on preferences.

    Uses multiple preference-based factors:
    - Explicit faculty preferences (blocked/preferred weeks)
    - Historical acceptance patterns
    - Temporal preferences (time of year, day of week)
    - Workload balancing preferences
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize preference scorer.

        Args:
            db: Async database session
        """
        self.db = db

    async def score_match(
        self,
        request_a: SwapRecord,
        request_b: SwapRecord,
    ) -> PreferenceScore:
        """
        Score a potential swap match based on preferences.

        Args:
            request_a: First swap request
            request_b: Second swap request

        Returns:
            PreferenceScore with detailed scoring
        """
        # Score individual components
        preference_match = await self._score_explicit_preferences(
            request_a,
            request_b,
        )

        historical_success = await self._score_historical_patterns(
            request_a.source_faculty_id,
            request_b.source_faculty_id,
        )

        temporal_alignment = self._score_temporal_alignment(
            request_a.source_week,
            request_b.source_week,
        )

        workload_fairness = await self._score_workload_fairness(
            request_a.source_faculty_id,
            request_b.source_faculty_id,
        )

        # Calculate weighted overall score
        overall = (
            preference_match * 0.4
            + historical_success * 0.25
            + temporal_alignment * 0.20
            + workload_fairness * 0.15
        )

        details = {
            "faculty_a_id": str(request_a.source_faculty_id),
            "faculty_b_id": str(request_b.source_faculty_id),
            "week_a": request_a.source_week.isoformat(),
            "week_b": request_b.source_week.isoformat(),
            "weights": {
                "preference": 0.4,
                "historical": 0.25,
                "temporal": 0.20,
                "workload": 0.15,
            },
        }

        logger.debug(
            f"Preference score for {request_a.id} <-> {request_b.id}: {overall:.3f}"
        )

        return PreferenceScore(
            overall_score=overall,
            preference_match=preference_match,
            historical_success=historical_success,
            temporal_alignment=temporal_alignment,
            workload_fairness=workload_fairness,
            details=details,
        )

    async def learn_from_history(
        self,
        faculty_id: UUID,
        days: int = 180,
    ) -> dict[str, Any]:
        """
        Learn preference patterns from historical swap data.

        Args:
            faculty_id: Faculty member ID
            days: Number of days to analyze

        Returns:
            Dictionary of learned patterns
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get historical swaps
        result = await self.db.execute(
            select(SwapRecord).where(
                and_(
                    SwapRecord.source_faculty_id == faculty_id,
                    SwapRecord.requested_at >= start_date,
                )
            )
        )

        swaps = list(result.scalars().all())

        if not swaps:
            return {
                "patterns_found": False,
                "message": "Insufficient historical data",
            }

            # Analyze patterns
        accepted_swaps = [s for s in swaps if s.status == SwapStatus.EXECUTED]

        rejected_swaps = [s for s in swaps if s.status == SwapStatus.REJECTED]

        # Preferred months
        accepted_months = [s.source_week.month for s in accepted_swaps]
        month_preference = {}
        for month in set(accepted_months):
            month_preference[month] = accepted_months.count(month)

            # Preferred days of week
        accepted_days = [s.source_week.weekday() for s in accepted_swaps]
        day_preference = {}
        for day in set(accepted_days):
            day_preference[day] = accepted_days.count(day)

            # Success rate
        total = len(swaps)
        success_rate = len(accepted_swaps) / total if total > 0 else 0.0

        # Average time to accept
        accept_times = []
        for swap in accepted_swaps:
            if swap.executed_at:
                time_diff = (swap.executed_at - swap.requested_at).days
                accept_times.append(time_diff)

        avg_accept_time = (
            sum(accept_times) / len(accept_times) if accept_times else None
        )

        return {
            "patterns_found": True,
            "total_swaps": total,
            "success_rate": success_rate,
            "preferred_months": month_preference,
            "preferred_days": day_preference,
            "avg_accept_time_days": avg_accept_time,
            "analysis_period_days": days,
        }

        # ===== Private Scoring Methods =====

    async def _score_explicit_preferences(
        self,
        request_a: SwapRecord,
        request_b: SwapRecord,
    ) -> float:
        """
        Score based on explicit preferences.

        Checks if faculty have marked weeks as blocked or preferred.
        """
        # This would integrate with faculty preference service
        # For now, basic scoring

        # Check if weeks are explicitly requested
        if request_a.target_week == request_b.source_week:
            score = 1.0  # Perfect match
        elif request_a.target_faculty_id == request_b.source_faculty_id:
            score = 0.9  # Targeted match
        else:
            score = 0.5  # General availability

        return score

    async def _score_historical_patterns(
        self,
        faculty_a_id: UUID,
        faculty_b_id: UUID,
    ) -> float:
        """
        Score based on historical acceptance patterns.

        Checks if these faculty have successfully swapped before.
        """
        # Check for past swaps between these faculty
        result = await self.db.execute(
            select(SwapRecord).where(
                and_(
                    SwapRecord.source_faculty_id == faculty_a_id,
                    SwapRecord.target_faculty_id == faculty_b_id,
                    SwapRecord.status == SwapStatus.EXECUTED,
                )
            )
        )

        past_swaps_ab = list(result.scalars().all())

        # Check reverse direction
        result = await self.db.execute(
            select(SwapRecord).where(
                and_(
                    SwapRecord.source_faculty_id == faculty_b_id,
                    SwapRecord.target_faculty_id == faculty_a_id,
                    SwapRecord.status == SwapStatus.EXECUTED,
                )
            )
        )

        past_swaps_ba = list(result.scalars().all())

        total_past = len(past_swaps_ab) + len(past_swaps_ba)

        if total_past >= 3:
            return 1.0  # Proven successful partnership
        elif total_past == 2:
            return 0.9
        elif total_past == 1:
            return 0.8
        else:
            return 0.6  # No history (neutral)

    def _score_temporal_alignment(
        self,
        week_a: date,
        week_b: date,
    ) -> float:
        """
        Score based on temporal alignment.

        Closer dates and similar times of year score higher.
        """
        # Date proximity
        days_apart = abs((week_a - week_b).days)

        if days_apart <= 7:
            proximity_score = 1.0
        elif days_apart <= 30:
            proximity_score = 0.8
        elif days_apart <= 60:
            proximity_score = 0.6
        else:
            proximity_score = 0.4

            # Same season/month bonus
        month_diff = abs(week_a.month - week_b.month)

        if month_diff <= 1:
            season_score = 1.0
        elif month_diff <= 3:
            season_score = 0.8
        else:
            season_score = 0.6

            # Combine scores
        return (proximity_score * 0.6) + (season_score * 0.4)

    async def _score_workload_fairness(
        self,
        faculty_a_id: UUID,
        faculty_b_id: UUID,
    ) -> float:
        """
        Score based on workload fairness.

        Prefers swaps that maintain or improve workload balance.
        """
        # Get total swaps for each faculty
        result_a = await self.db.execute(
            select(func.count())
            .select_from(SwapRecord)
            .where(SwapRecord.source_faculty_id == faculty_a_id)
        )

        count_a = result_a.scalar() or 0

        result_b = await self.db.execute(
            select(func.count())
            .select_from(SwapRecord)
            .where(SwapRecord.source_faculty_id == faculty_b_id)
        )

        count_b = result_b.scalar() or 0

        # Score based on balance
        diff = abs(count_a - count_b)

        if diff == 0:
            return 1.0
        elif diff <= 2:
            return 0.9
        elif diff <= 5:
            return 0.7
        else:
            return 0.5
