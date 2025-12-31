"""Resident Report - Resident hours and compliance."""

from datetime import date
from typing import Any, Dict
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from app.analytics.engine.analytics_engine import AnalyticsEngine
from app.analytics.compliance.violation_tracker import ViolationTracker
from app.analytics.reports.report_builder import ReportBuilder

logger = logging.getLogger(__name__)


class ResidentReport:
    """Generates resident hours report."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics_engine = AnalyticsEngine(db)
        self.violation_tracker = ViolationTracker(db)
        self.report_builder = ReportBuilder()

    async def generate(
        self, start_date: date, end_date: date, resident_id: str = None
    ) -> dict[str, Any]:
        """Generate resident hours report."""
        metrics = await self.analytics_engine.calculate_all_metrics(
            start_date, end_date, person_id=resident_id
        )
        violations = await self.violation_tracker.track_violations(
            start_date, end_date, resident_id
        )

        report = self.report_builder.build_report(
            title="Resident Hours Report",
            sections=[],
            metadata={"report_type": "resident_hours"},
        )

        self.report_builder.add_section(
            report,
            "Hours Summary",
            metrics["schedule_metrics"],
        )

        self.report_builder.add_section(
            report,
            "Compliance Status",
            {"violations": violations, "compliance": metrics["compliance_metrics"]},
        )

        return report
