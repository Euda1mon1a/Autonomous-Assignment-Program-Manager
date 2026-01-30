"""Comparison Data - Period comparison for dashboards."""

from datetime import date, timedelta
from typing import Any, Dict
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from app.analytics.engine.comparison import PeriodComparison

logger = logging.getLogger(__name__)


class ComparisonData:
    """Provides period comparison data for dashboards."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.comparator = PeriodComparison(db)

    async def get_week_over_week(self) -> dict[str, Any]:
        """Get week-over-week comparison."""
        today = date.today()
        this_week_start = today - timedelta(days=today.weekday())
        this_week_end = this_week_start + timedelta(days=6)

        last_week_start = this_week_start - timedelta(days=7)
        last_week_end = last_week_start + timedelta(days=6)

        comparison = await self.comparator.compare(
            last_week_start,
            last_week_end,
            this_week_start,
            this_week_end,
        )

        return {
            "type": "week_over_week",
            "comparison": comparison,
        }

    async def get_month_over_month(self) -> dict[str, Any]:
        """Get month-over-month comparison."""
        today = date.today()
        this_month_start = date(today.year, today.month, 1)

        # Calculate last month
        if today.month == 1:
            last_month = 12
            last_month_year = today.year - 1
        else:
            last_month = today.month - 1
            last_month_year = today.year

        import calendar

        last_month_start = date(last_month_year, last_month, 1)
        last_month_end = date(
            last_month_year,
            last_month,
            calendar.monthrange(last_month_year, last_month)[1],
        )

        this_month_end = today

        comparison = await self.comparator.compare(
            last_month_start,
            last_month_end,
            this_month_start,
            this_month_end,
        )

        return {
            "type": "month_over_month",
            "comparison": comparison,
        }
