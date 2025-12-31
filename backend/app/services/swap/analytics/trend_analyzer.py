"""
Swap trend analysis.

Analyzes trends in swap requests and identifies patterns
that can help optimize the swap system.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.swap import SwapRecord, SwapStatus


logger = logging.getLogger(__name__)


@dataclass
class TrendAnalysis:
    """Swap trend analysis results."""

    period_start: date
    period_end: date

    # Volume trends
    requests_by_week: dict[str, int]
    trend_direction: str  # "increasing", "decreasing", "stable"
    change_percentage: float

    # Timing patterns
    peak_request_days: list[str]  # Days of week
    peak_request_months: list[str]

    # Success patterns
    success_by_week: dict[str, float]
    average_success_rate: float

    # Recommendations
    recommendations: list[str]


class SwapTrendAnalyzer:
    """
    Analyzes trends in swap requests.

    Identifies patterns that can help:
    - Predict busy periods
    - Optimize matching algorithms
    - Improve user experience
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize trend analyzer.

        Args:
            db: Async database session
        """
        self.db = db

    async def analyze_trends(
        self,
        days: int = 90,
    ) -> TrendAnalysis:
        """
        Analyze swap trends over a period.

        Args:
            days: Number of days to analyze

        Returns:
            TrendAnalysis with comprehensive trend data
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        # Get all swaps in period
        result = await self.db.execute(
            select(SwapRecord).where(
                SwapRecord.requested_at >= start_date
            )
        )

        swaps = list(result.scalars().all())

        # Analyze volume trends
        requests_by_week = self._group_by_week(swaps)

        trend_direction, change_pct = self._calculate_trend(requests_by_week)

        # Analyze timing patterns
        peak_days = self._find_peak_days(swaps)
        peak_months = self._find_peak_months(swaps)

        # Analyze success rates
        success_by_week = self._calculate_success_by_week(swaps)
        avg_success = sum(success_by_week.values()) / len(success_by_week) if success_by_week else 0.0

        # Generate recommendations
        recommendations = self._generate_recommendations(
            trend_direction,
            change_pct,
            peak_days,
            avg_success,
        )

        logger.info(
            f"Trend analysis complete: {trend_direction} trend, "
            f"{change_pct:+.1f}% change"
        )

        return TrendAnalysis(
            period_start=start_date,
            period_end=end_date,
            requests_by_week=requests_by_week,
            trend_direction=trend_direction,
            change_percentage=change_pct,
            peak_request_days=peak_days,
            peak_request_months=peak_months,
            success_by_week=success_by_week,
            average_success_rate=avg_success,
            recommendations=recommendations,
        )

    async def predict_volume(
        self,
        weeks_ahead: int = 4,
    ) -> dict[str, Any]:
        """
        Predict swap request volume for coming weeks.

        Args:
            weeks_ahead: Number of weeks to predict

        Returns:
            Dictionary with predictions
        """
        # Get historical data
        result = await self.db.execute(
            select(SwapRecord).where(
                SwapRecord.requested_at >= datetime.utcnow() - timedelta(days=90)
            )
        )

        swaps = list(result.scalars().all())

        requests_by_week = self._group_by_week(swaps)

        # Simple moving average prediction
        if not requests_by_week:
            return {
                "predictions": [],
                "confidence": "low",
                "method": "insufficient_data",
            }

        recent_weeks = list(requests_by_week.values())[-4:]  # Last 4 weeks
        avg_requests = sum(recent_weeks) / len(recent_weeks) if recent_weeks else 0

        predictions = []
        for i in range(1, weeks_ahead + 1):
            week_start = datetime.utcnow().date() + timedelta(weeks=i)

            predictions.append({
                "week_starting": week_start.isoformat(),
                "predicted_requests": int(avg_requests),
                "confidence_interval": [
                    int(avg_requests * 0.7),
                    int(avg_requests * 1.3),
                ],
            })

        return {
            "predictions": predictions,
            "confidence": "medium",
            "method": "moving_average",
            "based_on_weeks": len(recent_weeks),
        }

    async def identify_bottlenecks(self) -> list[dict[str, Any]]:
        """
        Identify bottlenecks in the swap process.

        Returns:
            List of identified bottlenecks with recommendations
        """
        bottlenecks = []

        # Check for long-pending requests
        result = await self.db.execute(
            select(SwapRecord).where(
                and_(
                    SwapRecord.status == SwapStatus.PENDING,
                    SwapRecord.requested_at < datetime.utcnow() - timedelta(days=7),
                )
            )
        )

        old_pending = list(result.scalars().all())

        if len(old_pending) > 5:
            bottlenecks.append({
                "type": "slow_processing",
                "severity": "high",
                "count": len(old_pending),
                "description": f"{len(old_pending)} requests pending over 7 days",
                "recommendation": "Review approval workflow, consider auto-matching",
            })

        # Check for low match rates
        # (Would analyze match success)

        return bottlenecks

    # ===== Private Helper Methods =====

    def _group_by_week(
        self,
        swaps: list[SwapRecord],
    ) -> dict[str, int]:
        """Group swaps by week."""
        weekly_counts: dict[str, int] = {}

        for swap in swaps:
            # Get week starting Monday
            week_start = swap.requested_at.date() - timedelta(
                days=swap.requested_at.weekday()
            )

            week_key = week_start.isoformat()

            weekly_counts[week_key] = weekly_counts.get(week_key, 0) + 1

        return weekly_counts

    def _calculate_trend(
        self,
        requests_by_week: dict[str, int],
    ) -> tuple[str, float]:
        """Calculate trend direction and change percentage."""
        if len(requests_by_week) < 2:
            return "stable", 0.0

        weeks = sorted(requests_by_week.keys())

        # Compare first half to second half
        midpoint = len(weeks) // 2

        first_half = sum(
            requests_by_week[w] for w in weeks[:midpoint]
        ) / midpoint

        second_half = sum(
            requests_by_week[w] for w in weeks[midpoint:]
        ) / (len(weeks) - midpoint)

        if first_half == 0:
            change_pct = 100.0 if second_half > 0 else 0.0
        else:
            change_pct = ((second_half - first_half) / first_half) * 100

        if change_pct > 10:
            direction = "increasing"
        elif change_pct < -10:
            direction = "decreasing"
        else:
            direction = "stable"

        return direction, change_pct

    def _find_peak_days(self, swaps: list[SwapRecord]) -> list[str]:
        """Find days of week with most requests."""
        day_counts: dict[int, int] = {}

        for swap in swaps:
            day = swap.requested_at.weekday()  # 0 = Monday
            day_counts[day] = day_counts.get(day, 0) + 1

        # Get top 3 days
        top_days = sorted(
            day_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:3]

        day_names = [
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday",
        ]

        return [day_names[day] for day, _ in top_days]

    def _find_peak_months(self, swaps: list[SwapRecord]) -> list[str]:
        """Find months with most requests."""
        month_counts: dict[int, int] = {}

        for swap in swaps:
            month = swap.requested_at.month
            month_counts[month] = month_counts.get(month, 0) + 1

        top_months = sorted(
            month_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:3]

        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]

        return [month_names[month - 1] for month, _ in top_months]

    def _calculate_success_by_week(
        self,
        swaps: list[SwapRecord],
    ) -> dict[str, float]:
        """Calculate success rate by week."""
        weekly_success: dict[str, tuple[int, int]] = {}  # (executed, total)

        for swap in swaps:
            week_start = swap.requested_at.date() - timedelta(
                days=swap.requested_at.weekday()
            )

            week_key = week_start.isoformat()

            if week_key not in weekly_success:
                weekly_success[week_key] = (0, 0)

            executed, total = weekly_success[week_key]

            total += 1
            if swap.status == SwapStatus.EXECUTED:
                executed += 1

            weekly_success[week_key] = (executed, total)

        return {
            week: executed / total if total > 0 else 0.0
            for week, (executed, total) in weekly_success.items()
        }

    def _generate_recommendations(
        self,
        trend: str,
        change_pct: float,
        peak_days: list[str],
        avg_success: float,
    ) -> list[str]:
        """Generate recommendations based on trends."""
        recommendations = []

        if trend == "increasing":
            recommendations.append(
                "Swap requests are increasing. Consider proactive matching "
                "to handle higher volume."
            )

        if avg_success < 0.6:
            recommendations.append(
                f"Success rate is low ({avg_success:.1%}). Review matching "
                "criteria and faculty preferences."
            )

        if peak_days:
            recommendations.append(
                f"Most requests come in on {', '.join(peak_days)}. "
                "Consider automated notifications on these days."
            )

        if not recommendations:
            recommendations.append(
                "Swap system performing well. Continue monitoring trends."
            )

        return recommendations
