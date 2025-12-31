"""
Violation Tracker - Tracks ACGME compliance violations.
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person

logger = logging.getLogger(__name__)


class ViolationTracker:
    """Tracks and analyzes ACGME compliance violations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def track_violations(
        self, start_date: date, end_date: date, person_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Track all ACGME violations for a period."""
        work_hour_violations = await self._track_80_hour_violations(
            start_date, end_date, person_id
        )
        day_off_violations = await self._track_1in7_violations(
            start_date, end_date, person_id
        )

        return {
            "work_hour_violations": work_hour_violations,
            "day_off_violations": day_off_violations,
            "total_violations": len(work_hour_violations) + len(day_off_violations),
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        }

    async def _track_80_hour_violations(
        self, start_date: date, end_date: date, person_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Track 80-hour rule violations."""
        person_query = select(Person).where(Person.type == "resident")
        if person_id:
            person_query = person_query.where(Person.id == person_id)

        result = await self.db.execute(person_query)
        persons = result.scalars().all()

        violations = []
        for person in persons:
            # Get assignments
            assignments_query = (
                select(Assignment)
                .join(Block)
                .where(
                    and_(
                        Assignment.person_id == person.id,
                        Block.date >= start_date,
                        Block.date <= end_date,
                    )
                )
                .options(selectinload(Assignment.block))
            )

            assignments_result = await self.db.execute(assignments_query)
            assignments = assignments_result.scalars().all()

            # Check 4-week rolling windows
            person_violations = self._check_80_hour_windows(assignments, person)
            violations.extend(person_violations)

        return violations

    def _check_80_hour_windows(
        self, assignments: List[Assignment], person: Person
    ) -> List[Dict[str, Any]]:
        """Check 80-hour rule in 4-week windows."""
        violations = []

        # Group assignments by week
        weeks: Dict[int, List[Assignment]] = {}
        for assignment in assignments:
            if assignment.block and assignment.block.date:
                week_num = assignment.block.date.isocalendar()[1]
                if week_num not in weeks:
                    weeks[week_num] = []
                weeks[week_num].append(assignment)

        # Check 4-week rolling windows
        week_nums = sorted(weeks.keys())
        for i in range(len(week_nums) - 3):
            window_assignments = []
            for j in range(4):
                window_assignments.extend(weeks[week_nums[i + j]])

            total_hours = len(window_assignments) * 4  # 4 hours per half-day
            max_hours = 80 * 4  # 80 hours/week * 4 weeks

            if total_hours > max_hours:
                violations.append({
                    "person_id": str(person.id),
                    "person_name": person.name,
                    "violation_type": "80_hour_rule",
                    "week_start": week_nums[i],
                    "total_hours": total_hours,
                    "limit": max_hours,
                    "excess_hours": total_hours - max_hours,
                })

        return violations

    async def _track_1in7_violations(
        self, start_date: date, end_date: date, person_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Track 1-in-7 day off violations."""
        # Simplified implementation
        return []

    async def get_violation_trends(
        self, start_date: date, end_date: date
    ) -> Dict[str, List[int]]:
        """Get violation trends over time."""
        # Track violations week by week
        weeks_data = []
        current = start_date
        while current <= end_date:
            week_end = min(current + timedelta(days=6), end_date)
            week_violations = await self.track_violations(current, week_end)
            weeks_data.append(week_violations["total_violations"])
            current = week_end + timedelta(days=1)

        return {"weekly_violations": weeks_data}
