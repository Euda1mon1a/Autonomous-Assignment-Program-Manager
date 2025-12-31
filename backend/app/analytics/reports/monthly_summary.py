"""Monthly Summary Report."""

from datetime import date
from typing import Any, Dict
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from app.analytics.engine.analytics_engine import AnalyticsEngine
from app.analytics.reports.report_builder import ReportBuilder

logger = logging.getLogger(__name__)


class MonthlySummaryReport:
    """Generates monthly summary report."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics_engine = AnalyticsEngine(db)
        self.report_builder = ReportBuilder()

    async def generate(self, year: int, month: int) -> Dict[str, Any]:
        """Generate monthly summary."""
        # Calculate month dates
        import calendar
        start_date = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, last_day)

        # Get metrics
        metrics = await self.analytics_engine.calculate_all_metrics(start_date, end_date)

        # Build report
        report = self.report_builder.build_report(
            title=f"Monthly Summary - {start_date.strftime('%B %Y')}",
            sections=[],
            metadata={"year": year, "month": month, "report_type": "monthly_summary"},
        )

        self.report_builder.add_section(
            report,
            "Overview",
            {
                "coverage_rate": metrics["schedule_metrics"]["coverage_rate"],
                "total_assignments": metrics["schedule_metrics"]["total_assignments"],
                "compliance_score": metrics["compliance_metrics"]["compliance_score"],
            },
        )

        return report
