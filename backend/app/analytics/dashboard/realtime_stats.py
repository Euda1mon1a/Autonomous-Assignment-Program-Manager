"""Realtime Stats - Real-time statistics provider."""

from datetime import date, datetime
from typing import Any, Dict
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.assignment import Assignment
from app.models.person import Person
from app.models.swap import SwapRequest

logger = logging.getLogger(__name__)


class RealtimeStats:
    """Provides real-time statistics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self) -> dict[str, Any]:
        """Get real-time statistics."""
        today_stats = await self._get_today_stats()
        active_counts = await self._get_active_counts()
        recent_activity = await self._get_recent_activity()

        return {
            "today": today_stats,
            "active": active_counts,
            "recent_activity": recent_activity,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _get_today_stats(self) -> dict[str, Any]:
        """Get today's statistics."""
        today = date.today()

        assignments_result = await self.db.execute(
            select(func.count(Assignment.id)).join(Block).where(Block.date == today)
        )
        today_assignments = assignments_result.scalar() or 0

        return {
            "date": today.isoformat(),
            "assignments": today_assignments,
        }

    async def _get_active_counts(self) -> dict[str, int]:
        """Get active entity counts."""
        person_result = await self.db.execute(select(func.count(Person.id)))
        total_persons = person_result.scalar() or 0

        resident_result = await self.db.execute(
            select(func.count(Person.id)).where(Person.type == "resident")
        )
        total_residents = resident_result.scalar() or 0

        faculty_result = await self.db.execute(
            select(func.count(Person.id)).where(Person.type == "faculty")
        )
        total_faculty = faculty_result.scalar() or 0

        return {
            "total_persons": total_persons,
            "residents": total_residents,
            "faculty": total_faculty,
        }

    async def _get_recent_activity(self) -> dict[str, int]:
        """Get recent activity counts."""
        # Recent swaps
        recent_swaps_result = await self.db.execute(
            select(func.count(SwapRequest.id)).where(SwapRequest.status == "pending")
        )
        pending_swaps = recent_swaps_result.scalar() or 0

        return {
            "pending_swaps": pending_swaps,
        }
