"""
Swap metrics tracking and reporting.

Tracks and reports on swap system performance and usage.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.swap import SwapRecord, SwapStatus, SwapType


logger = logging.getLogger(__name__)


@dataclass
class SwapMetrics:
    """Comprehensive swap metrics."""

    # Volume metrics
    total_requests: int
    pending_requests: int
    executed_swaps: int
    rejected_swaps: int
    rolled_back_swaps: int

    # Success metrics
    success_rate: float
    average_time_to_execution_days: float
    rollback_rate: float

    # Type breakdown
    one_to_one_swaps: int
    absorb_swaps: int
    chain_swaps: int

    # Faculty metrics
    most_active_faculty: list[dict[str, Any]]
    fairness_score: float

    # Time period
    period_start: date
    period_end: date

    # Additional stats
    metadata: dict[str, Any]


class SwapMetricsCollector:
    """
    Collects and analyzes swap metrics.

    Provides comprehensive metrics for monitoring swap
    system health and usage patterns.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize metrics collector.

        Args:
            db: Async database session
        """
        self.db = db

    async def collect_metrics(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> SwapMetrics:
        """
        Collect comprehensive swap metrics.

        Args:
            start_date: Start of period (default: 30 days ago)
            end_date: End of period (default: today)

        Returns:
            SwapMetrics with comprehensive data
        """
        if not end_date:
            end_date = datetime.utcnow().date()

        if not start_date:
            start_date = end_date - timedelta(days=30)

            # Get all swaps in period
        result = await self.db.execute(
            select(SwapRecord).where(
                and_(
                    SwapRecord.requested_at >= start_date,
                    SwapRecord.requested_at <= end_date + timedelta(days=1),
                )
            )
        )

        swaps = list(result.scalars().all())

        # Calculate volume metrics
        total_requests = len(swaps)

        pending_requests = sum(1 for s in swaps if s.status == SwapStatus.PENDING)

        executed_swaps = sum(1 for s in swaps if s.status == SwapStatus.EXECUTED)

        rejected_swaps = sum(1 for s in swaps if s.status == SwapStatus.REJECTED)

        rolled_back_swaps = sum(1 for s in swaps if s.status == SwapStatus.ROLLED_BACK)

        # Calculate success metrics
        completed = executed_swaps + rejected_swaps

        success_rate = executed_swaps / completed if completed > 0 else 0.0

        # Calculate average time to execution
        execution_times = []
        for swap in swaps:
            if swap.status == SwapStatus.EXECUTED and swap.executed_at:
                time_to_exec = (swap.executed_at - swap.requested_at).days
                execution_times.append(time_to_exec)

        avg_time_to_execution = (
            sum(execution_times) / len(execution_times) if execution_times else 0.0
        )

        rollback_rate = (
            rolled_back_swaps / executed_swaps if executed_swaps > 0 else 0.0
        )

        # Type breakdown
        one_to_one = sum(1 for s in swaps if s.swap_type == SwapType.ONE_TO_ONE)

        absorb = sum(1 for s in swaps if s.swap_type == SwapType.ABSORB)

        chain_swaps = 0  # Would calculate from chain swap records

        # Faculty activity
        faculty_counts: dict[UUID, int] = {}
        for swap in swaps:
            faculty_counts[swap.source_faculty_id] = (
                faculty_counts.get(swap.source_faculty_id, 0) + 1
            )

        most_active = sorted(
            [
                {"faculty_id": str(fid), "swap_count": count}
                for fid, count in faculty_counts.items()
            ],
            key=lambda x: x["swap_count"],
            reverse=True,
        )[:10]

        # Fairness score (lower standard deviation = more fair)
        if faculty_counts:
            counts = list(faculty_counts.values())
            mean = sum(counts) / len(counts)
            variance = sum((x - mean) ** 2 for x in counts) / len(counts)
            std_dev = variance**0.5

            # Normalize to 0-1 scale (lower std_dev = higher fairness)
            fairness = max(0.0, 1.0 - (std_dev / mean)) if mean > 0 else 1.0
        else:
            fairness = 1.0

        metadata = {
            "swaps_analyzed": len(swaps),
            "unique_faculty": len(faculty_counts),
            "period_days": (end_date - start_date).days,
        }

        logger.info(
            f"Collected metrics for {start_date} to {end_date}: "
            f"{total_requests} requests, {success_rate:.1%} success rate"
        )

        return SwapMetrics(
            total_requests=total_requests,
            pending_requests=pending_requests,
            executed_swaps=executed_swaps,
            rejected_swaps=rejected_swaps,
            rolled_back_swaps=rolled_back_swaps,
            success_rate=success_rate,
            average_time_to_execution_days=avg_time_to_execution,
            rollback_rate=rollback_rate,
            one_to_one_swaps=one_to_one,
            absorb_swaps=absorb,
            chain_swaps=chain_swaps,
            most_active_faculty=most_active,
            fairness_score=fairness,
            period_start=start_date,
            period_end=end_date,
            metadata=metadata,
        )

    async def get_faculty_metrics(
        self,
        faculty_id: UUID,
        days: int = 90,
    ) -> dict[str, Any]:
        """
        Get metrics for a specific faculty member.

        Args:
            faculty_id: Faculty member ID
            days: Number of days to analyze

        Returns:
            Dictionary of faculty-specific metrics
        """
        start_date = datetime.utcnow().date() - timedelta(days=days)

        result = await self.db.execute(
            select(SwapRecord).where(
                and_(
                    SwapRecord.source_faculty_id == faculty_id,
                    SwapRecord.requested_at >= start_date,
                )
            )
        )

        swaps = list(result.scalars().all())

        return {
            "faculty_id": str(faculty_id),
            "total_requests": len(swaps),
            "executed": sum(1 for s in swaps if s.status == SwapStatus.EXECUTED),
            "pending": sum(1 for s in swaps if s.status == SwapStatus.PENDING),
            "rejected": sum(1 for s in swaps if s.status == SwapStatus.REJECTED),
            "success_rate": (
                sum(1 for s in swaps if s.status == SwapStatus.EXECUTED) / len(swaps)
                if swaps
                else 0.0
            ),
            "period_days": days,
        }

    async def get_weekly_report(self) -> dict[str, Any]:
        """
        Get weekly swap report.

        Returns:
            Dictionary with weekly summary
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=7)

        metrics = await self.collect_metrics(start_date, end_date)

        return {
            "period": f"{start_date} to {end_date}",
            "total_requests": metrics.total_requests,
            "executed": metrics.executed_swaps,
            "success_rate": f"{metrics.success_rate:.1%}",
            "avg_time_to_execution": f"{metrics.average_time_to_execution_days:.1f} days",
            "pending": metrics.pending_requests,
            "rollback_rate": f"{metrics.rollback_rate:.1%}",
        }
