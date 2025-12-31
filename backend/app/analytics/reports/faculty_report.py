"""Faculty Report - Faculty workload analysis."""

from datetime import date
from typing import Any, Dict
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from app.analytics.engine.analytics_engine import AnalyticsEngine
from app.analytics.engine.aggregator import DataAggregator
from app.analytics.reports.report_builder import ReportBuilder

logger = logging.getLogger(__name__)


class FacultyReport:
    """Generates faculty workload report."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics_engine = AnalyticsEngine(db)
        self.aggregator = DataAggregator(db)
        self.report_builder = ReportBuilder()

    async def generate(
        self, start_date: date, end_date: date, faculty_id: str = None
    ) -> Dict[str, Any]:
        """Generate faculty workload report."""
        workload = await self.aggregator.get_workload_distribution(
            start_date, end_date, faculty_id
        )

        report = self.report_builder.build_report(
            title="Faculty Workload Report",
            sections=[],
            metadata={"report_type": "faculty_workload"},
        )

        self.report_builder.add_section(
            report,
            "Workload Distribution",
            workload,
        )

        return report
