"""
Compliance Benchmark - Benchmarks against industry standards.
"""

from datetime import date
from typing import Any, Dict
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from app.analytics.compliance.compliance_score import ComplianceScore

logger = logging.getLogger(__name__)


class ComplianceBenchmark:
    """Benchmarks compliance against standards."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.compliance_score = ComplianceScore(db)

    # Industry benchmarks (example values)
    BENCHMARKS = {
        "excellent": {"min_score": 95, "percentile": 90},
        "good": {"min_score": 85, "percentile": 75},
        "fair": {"min_score": 70, "percentile": 50},
        "poor": {"min_score": 0, "percentile": 25},
    }

    async def benchmark_program(
        self, start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """Benchmark program against industry standards."""
        score = await self.compliance_score.calculate_score(start_date, end_date)

        # Determine benchmark category
        benchmark_category = "poor"
        for category, criteria in self.BENCHMARKS.items():
            if score["compliance_score"] >= criteria["min_score"]:
                benchmark_category = category
                break

        percentile = self.BENCHMARKS[benchmark_category]["percentile"]

        return {
            "program_score": score,
            "benchmark_category": benchmark_category,
            "estimated_percentile": percentile,
            "comparison": self._generate_comparison(score["compliance_score"]),
        }

    def _generate_comparison(self, score: float) -> Dict[str, Any]:
        """Generate comparison to benchmarks."""
        return {
            "vs_excellent": round(95 - score, 2),
            "vs_good": round(85 - score, 2),
            "vs_fair": round(70 - score, 2),
        }
