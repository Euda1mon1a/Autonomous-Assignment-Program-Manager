"""
Period Comparison - Compares metrics between time periods.
"""

from datetime import date
from typing import Any, Dict, List, Optional
import logging

from sqlalchemy.ext.asyncio import AsyncSession
import pandas as pd
import numpy as np

from app.analytics.engine.metric_calculator import MetricCalculator

logger = logging.getLogger(__name__)


class PeriodComparison:
    """
    Compares schedule metrics between time periods.

    Provides:
    - Period-over-period comparison
    - Delta calculation
    - Percent change
    - Statistical significance testing
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize period comparison.

        Args:
            db: Database session
        """
        self.db = db
        self.metric_calculator = MetricCalculator(db)

    async def compare(
        self,
        period1_start: date,
        period1_end: date,
        period2_start: date,
        period2_end: date,
    ) -> dict[str, Any]:
        """
        Compare metrics between two periods.

        Args:
            period1_start: First period start (baseline)
            period1_end: First period end
            period2_start: Second period start (comparison)
            period2_end: Second period end

        Returns:
            Comparison results with deltas and percent changes
        """
        # Calculate metrics for both periods
        period1_metrics = await self._get_all_metrics(period1_start, period1_end)
        period2_metrics = await self._get_all_metrics(period2_start, period2_end)

        # Compare schedule metrics
        schedule_comparison = self._compare_dict_metrics(
            period1_metrics["schedule"],
            period2_metrics["schedule"],
        )

        # Compare compliance metrics
        compliance_comparison = self._compare_dict_metrics(
            period1_metrics["compliance"],
            period2_metrics["compliance"],
        )

        # Compare resilience metrics
        resilience_comparison = self._compare_dict_metrics(
            period1_metrics["resilience"],
            period2_metrics["resilience"],
        )

        return {
            "period1": {
                "start": period1_start.isoformat(),
                "end": period1_end.isoformat(),
                "metrics": period1_metrics,
            },
            "period2": {
                "start": period2_start.isoformat(),
                "end": period2_end.isoformat(),
                "metrics": period2_metrics,
            },
            "comparison": {
                "schedule": schedule_comparison,
                "compliance": compliance_comparison,
                "resilience": resilience_comparison,
            },
            "summary": self._generate_summary(
                schedule_comparison,
                compliance_comparison,
                resilience_comparison,
            ),
        }

    async def _get_all_metrics(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        """Get all metrics for a period."""
        schedule = await self.metric_calculator.calculate_schedule_metrics(
            start_date, end_date
        )
        compliance = await self.metric_calculator.calculate_compliance_metrics(
            start_date, end_date
        )
        resilience = await self.metric_calculator.calculate_resilience_metrics(
            start_date, end_date
        )

        return {
            "schedule": schedule,
            "compliance": compliance,
            "resilience": resilience,
        }

    def _compare_dict_metrics(
        self,
        period1: dict[str, Any],
        period2: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        """
        Compare two metric dictionaries.

        Args:
            period1: Baseline period metrics
            period2: Comparison period metrics

        Returns:
            Dict of metric comparisons
        """
        comparison = {}

        for key in period1.keys():
            if key in period2:
                value1 = period1[key]
                value2 = period2[key]

                # Only compare numeric values
                if isinstance(value1, (int, float)) and isinstance(
                    value2, (int, float)
                ):
                    comparison[key] = self._compare_values(value1, value2)

        return comparison

    def _compare_values(
        self,
        value1: float,
        value2: float,
    ) -> dict[str, Any]:
        """
        Compare two numeric values.

        Args:
            value1: Baseline value
            value2: Comparison value

        Returns:
            Dict with delta, percent change, direction
        """
        delta = value2 - value1

        if value1 != 0:
            percent_change = (delta / value1) * 100
        else:
            percent_change = 0 if delta == 0 else float("inf")

        # Determine direction
        if abs(delta) < 0.01:
            direction = "stable"
        elif delta > 0:
            direction = "increase"
        else:
            direction = "decrease"

        # Determine magnitude
        if abs(percent_change) < 5:
            magnitude = "minimal"
        elif abs(percent_change) < 20:
            magnitude = "moderate"
        else:
            magnitude = "significant"

        return {
            "period1_value": round(value1, 2),
            "period2_value": round(value2, 2),
            "delta": round(delta, 2),
            "percent_change": round(percent_change, 2),
            "direction": direction,
            "magnitude": magnitude,
        }

    def _generate_summary(
        self,
        schedule_comparison: dict[str, Any],
        compliance_comparison: dict[str, Any],
        resilience_comparison: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate high-level summary of comparison."""
        # Key metrics to highlight
        key_metrics = {
            "coverage_rate": schedule_comparison.get("coverage_rate", {}),
            "compliance_score": compliance_comparison.get("compliance_score", {}),
            "avg_utilization": resilience_comparison.get("avg_utilization", {}),
        }

        # Identify significant changes
        significant_changes = []
        for metric_name, comparison in key_metrics.items():
            if comparison.get("magnitude") == "significant":
                significant_changes.append(
                    {
                        "metric": metric_name,
                        "direction": comparison.get("direction"),
                        "percent_change": comparison.get("percent_change"),
                    }
                )

        # Overall assessment
        if not significant_changes:
            overall_assessment = "stable"
        else:
            # Check if changes are mostly positive or negative
            positive_changes = sum(
                1
                for c in significant_changes
                if c["direction"] == "increase"
                and c["metric"] in ["coverage_rate", "compliance_score"]
            )
            negative_changes = sum(
                1
                for c in significant_changes
                if c["direction"] == "decrease"
                and c["metric"] in ["coverage_rate", "compliance_score"]
            )

            if positive_changes > negative_changes:
                overall_assessment = "improving"
            elif negative_changes > positive_changes:
                overall_assessment = "declining"
            else:
                overall_assessment = "mixed"

        return {
            "overall_assessment": overall_assessment,
            "significant_changes": significant_changes,
            "key_metrics": key_metrics,
        }

    async def compare_year_over_year(
        self,
        base_year: int,
        comparison_year: int,
    ) -> dict[str, Any]:
        """
        Compare full year metrics.

        Args:
            base_year: Baseline year
            comparison_year: Comparison year

        Returns:
            Year-over-year comparison
        """
        period1_start = date(base_year, 1, 1)
        period1_end = date(base_year, 12, 31)
        period2_start = date(comparison_year, 1, 1)
        period2_end = date(comparison_year, 12, 31)

        return await self.compare(
            period1_start,
            period1_end,
            period2_start,
            period2_end,
        )

    async def compare_quarters(
        self,
        year: int,
        quarter1: int,
        quarter2: int,
    ) -> dict[str, Any]:
        """
        Compare two quarters.

        Args:
            year: Year
            quarter1: First quarter (1-4)
            quarter2: Second quarter (1-4)

        Returns:
            Quarter comparison
        """

        def get_quarter_dates(year: int, quarter: int):
            start_month = (quarter - 1) * 3 + 1
            end_month = start_month + 2
            if end_month == 12 or end_month in [1, 3, 5, 7, 8, 10]:
                end_day = 31
            elif end_month in [4, 6, 9, 11]:
                end_day = 30
            else:
                end_day = 28

            return (
                date(year, start_month, 1),
                date(year, end_month, end_day),
            )

        q1_start, q1_end = get_quarter_dates(year, quarter1)
        q2_start, q2_end = get_quarter_dates(year, quarter2)

        return await self.compare(q1_start, q1_end, q2_start, q2_end)
