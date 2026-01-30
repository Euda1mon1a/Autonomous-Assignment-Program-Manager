"""
Compliance Score - Calculates overall compliance scores.
"""

from datetime import date
from typing import Any, Dict
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from app.analytics.compliance.violation_tracker import ViolationTracker

logger = logging.getLogger(__name__)


class ComplianceScore:
    """Calculates compliance scores and ratings."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.violation_tracker = ViolationTracker(db)

    async def calculate_score(self, start_date: date, end_date: date) -> dict[str, Any]:
        """Calculate overall compliance score (0-100)."""
        violations = await self.violation_tracker.track_violations(start_date, end_date)

        total_violations = violations["total_violations"]
        days = (end_date - start_date).days + 1
        expected_compliant_days = days

        # Score calculation: 100 - (violations / expected days * 100)
        if expected_compliant_days > 0:
            score = max(0, 100 - (total_violations / expected_compliant_days * 100))
        else:
            score = 100

            # Rating
        if score >= 95:
            rating = "excellent"
        elif score >= 85:
            rating = "good"
        elif score >= 70:
            rating = "fair"
        else:
            rating = "poor"

        return {
            "compliance_score": round(score, 2),
            "rating": rating,
            "total_violations": total_violations,
            "period_days": days,
        }
