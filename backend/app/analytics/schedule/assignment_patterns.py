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

    def __init__(self, db: AsyncSession) -> None:
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
    ) -> dict[str, Any]:
        """
        Find consecutive assignment patterns.

        Analyzes streaks of consecutive working days for all persons
        in the specified date range.

        Args:
            start_date: Start of analysis period
            end_date: End of analysis period

        Returns:
            Dictionary with pattern statistics including:
            - max_consecutive_days: Longest streak found
            - avg_consecutive_days: Average streak length
            - persons_with_long_streaks: Count of persons with 5+ day streaks
            - streak_distribution: Distribution of streak lengths
        """
        # Get all assignment dates per person
        query = (
            select(Assignment.person_id, Block.date)
            .join(Block, Assignment.block_id == Block.id)
            .where(and_(Block.date >= start_date, Block.date <= end_date))
            .order_by(Assignment.person_id, Block.date)
            .distinct()
        )

        result = await self.db.execute(query)
        rows = result.all()

        if not rows:
            return {
                "max_consecutive_days": 0,
                "avg_consecutive_days": 0.0,
                "persons_with_long_streaks": 0,
                "streak_distribution": {},
            }

            # Group dates by person
        person_dates: dict[str, list[date]] = {}
        for person_id, work_date in rows:
            person_key = str(person_id)
            if person_key not in person_dates:
                person_dates[person_key] = []
            person_dates[person_key].append(work_date)

            # Analyze streaks for each person
        all_streaks: list[int] = []
        max_consecutive = 0
        persons_with_long_streaks = 0
        streak_distribution: dict[int, int] = {}

        for person_id, dates in person_dates.items():
            sorted_dates = sorted(dates)
            current_streak = 1
            person_max_streak = 1

            for i in range(1, len(sorted_dates)):
                if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
                    current_streak += 1
                else:
                    # Record this streak
                    if current_streak > 1:
                        all_streaks.append(current_streak)
                        streak_distribution[current_streak] = (
                            streak_distribution.get(current_streak, 0) + 1
                        )
                    person_max_streak = max(person_max_streak, current_streak)
                    current_streak = 1

                    # Don't forget the last streak
            if current_streak > 1:
                all_streaks.append(current_streak)
                streak_distribution[current_streak] = (
                    streak_distribution.get(current_streak, 0) + 1
                )
            person_max_streak = max(person_max_streak, current_streak)

            max_consecutive = max(max_consecutive, person_max_streak)

            # Count persons with 5+ day streaks
            if person_max_streak >= 5:
                persons_with_long_streaks += 1

        avg_consecutive = sum(all_streaks) / len(all_streaks) if all_streaks else 0.0

        return {
            "max_consecutive_days": max_consecutive,
            "avg_consecutive_days": round(avg_consecutive, 2),
            "persons_with_long_streaks": persons_with_long_streaks,
            "streak_distribution": streak_distribution,
            "total_streaks_analyzed": len(all_streaks),
        }
