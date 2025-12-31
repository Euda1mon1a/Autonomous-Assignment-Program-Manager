"""ACGME Annual Report - Comprehensive annual compliance report."""

from datetime import date
from typing import Any, Dict
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from app.analytics.engine.analytics_engine import AnalyticsEngine
from app.analytics.compliance.compliance_score import ComplianceScore
from app.analytics.compliance.violation_tracker import ViolationTracker
from app.analytics.reports.report_builder import ReportBuilder

logger = logging.getLogger(__name__)


class ACGMEAnnualReport:
    """Generates ACGME annual compliance report."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics_engine = AnalyticsEngine(db)
        self.compliance_score = ComplianceScore(db)
        self.violation_tracker = ViolationTracker(db)
        self.report_builder = ReportBuilder()

    async def generate(self, year: int) -> dict[str, Any]:
        """Generate annual ACGME report."""
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        # Get metrics
        metrics = await self.analytics_engine.calculate_all_metrics(
            start_date, end_date
        )
        score = await self.compliance_score.calculate_score(start_date, end_date)
        violations = await self.violation_tracker.track_violations(start_date, end_date)

        # Build report
        report = self.report_builder.build_report(
            title=f"ACGME Annual Report {year}",
            sections=[],
            metadata={"year": year, "report_type": "acgme_annual"},
        )

        # Executive summary
        self.report_builder.add_section(
            report,
            "Executive Summary",
            {
                "compliance_score": score["compliance_score"],
                "rating": score["rating"],
                "total_violations": violations["total_violations"],
                "period": f"January 1, {year} - December 31, {year}",
            },
        )

        # Compliance metrics
        self.report_builder.add_section(
            report,
            "Compliance Metrics",
            metrics["compliance_metrics"],
        )

        # Violations detail
        self.report_builder.add_section(
            report,
            "Violations Report",
            violations,
        )

        return report
