"""
Assignment Patterns - Detects patterns in assignments.
"""

from datetime import date
from typing import Any, Dict, List
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person

logger = logging.getLogger(__name__)


class AssignmentPatterns:
    """Detects and analyzes assignment patterns."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_patterns(self, start_date: date, end_date: date) -> dict[str, Any]:
        """Detect assignment patterns."""
        # Most common assignment combinations
        combo_patterns = await self._find_common_combinations(start_date, end_date)

        # Consecutive assignment patterns
        consecutive = await self._find_consecutive_patterns(start_date, end_date)

        return {
            "common_combinations": combo_patterns,
            "consecutive_patterns": consecutive,
        }

    async def _find_common_combinations(
        self, start_date: date, end_date: date, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Find most common person-rotation combinations."""
        query = (
            select(
                Person.name,
                Assignment.activity_override,
                func.count(Assignment.id).label("count"),
            )
            .join(Person)
            .join(Block)
            .where(and_(Block.date >= start_date, Block.date <= end_date))
            .group_by(Person.name, Assignment.activity_override)
            .order_by(func.count(Assignment.id).desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        patterns = result.all()

        return [
            {"person": row.name, "activity": row.activity_override, "count": row.count}
            for row in patterns
        ]

    async def _find_consecutive_patterns(
        self, start_date: date, end_date: date
    ) -> dict[str, int]:
        """Find consecutive assignment patterns."""
        # Simplified: count streaks
        return {"consecutive_days_worked": 0}  # Placeholder
