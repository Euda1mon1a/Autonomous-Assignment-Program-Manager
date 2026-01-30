"""Dashboard Data - Main dashboard data provider."""

from datetime import date, timedelta
from typing import Any, Dict
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from app.analytics.engine.analytics_engine import AnalyticsEngine
from app.analytics.dashboard.kpi_calculator import KPICalculator
from app.analytics.dashboard.realtime_stats import RealtimeStats

logger = logging.getLogger(__name__)


class DashboardData:
    """Provides comprehensive dashboard data."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.analytics_engine = AnalyticsEngine(db)
        self.kpi_calculator = KPICalculator(db)
        self.realtime_stats = RealtimeStats(db)

    async def get_dashboard_data(self, date_range: int = 30) -> dict[str, Any]:
        """Get all dashboard data."""
        summary = await self.analytics_engine.get_dashboard_summary(date_range)
        kpis = await self.kpi_calculator.calculate_kpis()
        realtime = await self.realtime_stats.get_stats()

        return {
            "summary": summary,
            "kpis": kpis,
            "realtime": realtime,
            "last_updated": date.today().isoformat(),
        }
