"""
Gap Analyzer - Analyzes coverage gaps in schedule.
"""

from datetime import date, timedelta
from typing import Any, Dict, List
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person

logger = logging.getLogger(__name__)


class GapAnalyzer:
    """Analyzes coverage gaps and recommends fixes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_gaps(
        self, start_date: date, end_date: date, threshold: float = 0.7
    ) -> list[dict[str, Any]]:
        """Find coverage gaps below threshold."""
        capacity_result = await self.db.execute(select(func.count(Person.id)))
        capacity = capacity_result.scalar() or 1

        query = (
            select(Block.date, func.count(Assignment.id))
            .join(Assignment, Block.id == Assignment.block_id, isouter=True)
            .where(and_(Block.date >= start_date, Block.date <= end_date))
            .group_by(Block.date)
        )

        result = await self.db.execute(query)
        daily_coverage = result.all()

        gaps = []
        for day_date, count in daily_coverage:
            coverage_rate = count / capacity
            if coverage_rate < threshold:
                gaps.append(
                    {
                        "date": day_date.isoformat(),
                        "coverage_rate": round(coverage_rate, 3),
                        "gap_size": capacity - count,
                    }
                )

        return gaps
