"""
Audit Reporter - Generates compliance audit reports.
"""

from datetime import date
from typing import Any, Dict, List
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from app.analytics.compliance.violation_tracker import ViolationTracker
from app.analytics.compliance.compliance_score import ComplianceScore

logger = logging.getLogger(__name__)


class AuditReporter:
    """Generates compliance audit reports."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.violation_tracker = ViolationTracker(db)
        self.compliance_score = ComplianceScore(db)

    async def generate_audit_report(
        self, start_date: date, end_date: date
    ) -> dict[str, Any]:
        """Generate comprehensive audit report."""
        violations = await self.violation_tracker.track_violations(start_date, end_date)
        score = await self.compliance_score.calculate_score(start_date, end_date)

        return {
            "audit_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "compliance_score": score,
            "violations": violations,
            "recommendations": self._generate_recommendations(violations, score),
        }

    def _generate_recommendations(
        self, violations: dict[str, Any], score: dict[str, Any]
    ) -> list[str]:
        """Generate improvement recommendations."""
        recommendations = []

        if score["compliance_score"] < 85:
            recommendations.append("Improve overall compliance monitoring")

        if violations["total_violations"] > 10:
            recommendations.append("Review workload distribution")

        if len(violations["work_hour_violations"]) > 0:
            recommendations.append("Implement stricter 80-hour rule enforcement")

        return recommendations
