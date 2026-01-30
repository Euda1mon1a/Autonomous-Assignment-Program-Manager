"""
Conflict Trends - Analyzes conflict patterns over time.
"""

from datetime import date
from typing import Any, Dict, List
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.conflict_alert import ConflictAlert

logger = logging.getLogger(__name__)


class ConflictTrends:
    """Analyzes conflict trends and patterns."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def analyze_trends(self, start_date: date, end_date: date) -> dict[str, Any]:
        """Analyze conflict trends over time."""
        query = (
            select(
                func.date_trunc("week", ConflictAlert.created_at).label("week"),
                func.count(ConflictAlert.id).label("count"),
            )
            .where(
                and_(
                    ConflictAlert.created_at >= start_date,
                    ConflictAlert.created_at <= end_date,
                )
            )
            .group_by("week")
            .order_by("week")
        )

        result = await self.db.execute(query)
        weekly_conflicts = result.all()

        return {
            "weekly_trends": [
                {"week": str(row.week), "conflicts": row.count}
                for row in weekly_conflicts
            ],
            "total_conflicts": sum(row.count for row in weekly_conflicts),
        }
