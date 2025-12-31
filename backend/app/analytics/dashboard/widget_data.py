"""Widget Data - Individual dashboard widget data."""

from datetime import date, timedelta
from typing import Any, Dict, List
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.assignment import Assignment
from app.models.block import Block

logger = logging.getLogger(__name__)


class WidgetData:
    """Provides data for individual dashboard widgets."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_coverage_widget(self) -> dict[str, Any]:
        """Get coverage widget data."""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        blocks_result = await self.db.execute(
            select(func.count(Block.id)).where(Block.date.between(week_start, week_end))
        )
        total_blocks = blocks_result.scalar() or 1

        assignments_result = await self.db.execute(
            select(func.count(Assignment.id))
            .join(Block)
            .where(Block.date.between(week_start, week_end))
        )
        total_assignments = assignments_result.scalar() or 0

        coverage_rate = total_assignments / total_blocks

        return {
            "title": "This Week's Coverage",
            "value": f"{coverage_rate:.1%}",
            "trend": "stable",
            "data": {"covered": total_assignments, "total": total_blocks},
        }

    async def get_violations_widget(self) -> dict[str, Any]:
        """Get violations widget data."""
        # Simplified - would integrate with violation tracker
        return {
            "title": "Active Violations",
            "value": "0",
            "trend": "down",
            "severity": "low",
        }

    async def get_utilization_widget(self) -> dict[str, Any]:
        """Get utilization widget data."""
        return {
            "title": "Current Utilization",
            "value": "75%",
            "trend": "stable",
            "threshold_status": "normal",
        }
