"""Resilience Report - System resilience analysis."""

from datetime import date
from typing import Any, Dict
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from app.analytics.engine.analytics_engine import AnalyticsEngine
from app.analytics.reports.report_builder import ReportBuilder

logger = logging.getLogger(__name__)


class ResilienceReport:
    """Generates resilience analysis report."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics_engine = AnalyticsEngine(db)
        self.report_builder = ReportBuilder()

    async def generate(self, start_date: date, end_date: date) -> dict[str, Any]:
        """Generate resilience report."""
        metrics = await self.analytics_engine.calculate_all_metrics(
            start_date, end_date
        )

        report = self.report_builder.build_report(
            title="Resilience Report",
            sections=[],
            metadata={"report_type": "resilience"},
        )

        self.report_builder.add_section(
            report,
            "Resilience Metrics",
            metrics["resilience_metrics"],
        )

        self.report_builder.add_section(
            report,
            "Risk Assessment",
            {
                "high_utilization_days": metrics["resilience_metrics"][
                    "high_utilization_count"
                ],
                "n1_vulnerable_days": metrics["resilience_metrics"][
                    "n1_vulnerable_days"
                ],
            },
        )

        return report
