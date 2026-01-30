"""
Analytics Engine - Main orchestrator for schedule analytics.

Coordinates metric calculation, aggregation, trend detection, and forecasting.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from functools import lru_cache
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.analytics.engine.metric_calculator import MetricCalculator
from app.analytics.engine.aggregator import DataAggregator
from app.analytics.engine.time_series import TimeSeriesAnalyzer
from app.analytics.engine.trend_detector import TrendDetector
from app.analytics.engine.anomaly_finder import AnomalyFinder
from app.analytics.engine.forecast_engine import ForecastEngine
from app.analytics.engine.comparison import PeriodComparison

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """
    Main analytics orchestrator for schedule analysis.

    Coordinates:
    - Metric calculation
    - Data aggregation
    - Trend detection
    - Anomaly detection
    - Forecasting
    - Period comparisons

    Example:
        engine = AnalyticsEngine(db)
        metrics = await engine.calculate_all_metrics(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize analytics engine.

        Args:
            db: Database session
        """
        self.db = db
        self.metric_calculator = MetricCalculator(db)
        self.aggregator = DataAggregator(db)
        self.time_series = TimeSeriesAnalyzer(db)
        self.trend_detector = TrendDetector()
        self.anomaly_finder = AnomalyFinder()
        self.forecast_engine = ForecastEngine()
        self.comparator = PeriodComparison(db)

    async def calculate_all_metrics(
        self,
        start_date: date,
        end_date: date,
        person_id: str | None = None,
        rotation_type: str | None = None,
    ) -> dict[str, Any]:
        """
        Calculate comprehensive metrics for a period.

        Args:
            start_date: Period start date
            end_date: Period end date
            person_id: Optional person filter
            rotation_type: Optional rotation type filter

        Returns:
            Dict containing:
            - schedule_metrics: Coverage, workload, efficiency
            - compliance_metrics: ACGME compliance stats
            - resilience_metrics: Utilization, N-1 status
            - trend_metrics: Week-over-week changes
            - forecasts: Predicted future metrics
        """
        logger.info(
            f"Calculating metrics from {start_date} to {end_date}, "
            f"person={person_id}, rotation={rotation_type}"
        )

        # Calculate base metrics
        schedule_metrics = await self.metric_calculator.calculate_schedule_metrics(
            start_date, end_date, person_id, rotation_type
        )

        compliance_metrics = await self.metric_calculator.calculate_compliance_metrics(
            start_date, end_date, person_id
        )

        resilience_metrics = await self.metric_calculator.calculate_resilience_metrics(
            start_date, end_date
        )

        # Time series analysis
        time_series_data = await self.time_series.get_time_series(
            start_date, end_date, granularity="week"
        )

        # Trend detection
        trends = self.trend_detector.detect_trends(time_series_data)

        # Anomaly detection
        anomalies = self.anomaly_finder.find_anomalies(time_series_data)

        # Forecasting
        forecasts = self.forecast_engine.forecast(
            time_series_data,
            periods=4,  # 4 weeks ahead
        )

        return {
            "schedule_metrics": schedule_metrics,
            "compliance_metrics": compliance_metrics,
            "resilience_metrics": resilience_metrics,
            "time_series": time_series_data,
            "trends": trends,
            "anomalies": anomalies,
            "forecasts": forecasts,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days,
            },
        }

    async def get_dashboard_summary(
        self,
        date_range: int = 30,
    ) -> dict[str, Any]:
        """
        Get summary metrics for dashboard display.

        Args:
            date_range: Number of days to analyze (default 30)

        Returns:
            Dict with key metrics for dashboard widgets
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=date_range)

        metrics = await self.calculate_all_metrics(start_date, end_date)

        # Extract key KPIs
        schedule = metrics["schedule_metrics"]
        compliance = metrics["compliance_metrics"]
        resilience = metrics["resilience_metrics"]

        return {
            "kpis": {
                "coverage_rate": schedule.get("coverage_rate", 0),
                "avg_workload": schedule.get("avg_workload_hours", 0),
                "compliance_score": compliance.get("compliance_score", 0),
                "utilization": resilience.get("avg_utilization", 0),
                "violations": compliance.get("total_violations", 0),
            },
            "trends": {
                "coverage_trend": metrics["trends"].get("coverage", "stable"),
                "workload_trend": metrics["trends"].get("workload", "stable"),
                "violation_trend": metrics["trends"].get("violations", "stable"),
            },
            "alerts": {
                "anomalies": len(metrics["anomalies"]),
                "high_utilization": resilience.get("high_utilization_count", 0),
                "forecasted_issues": self._count_forecast_issues(metrics["forecasts"]),
            },
            "period": metrics["period"],
        }

    async def compare_periods(
        self,
        period1_start: date,
        period1_end: date,
        period2_start: date,
        period2_end: date,
    ) -> dict[str, Any]:
        """
        Compare metrics between two time periods.

        Args:
            period1_start: First period start
            period1_end: First period end
            period2_start: Second period start
            period2_end: Second period end

        Returns:
            Comparison results with deltas and percent changes
        """
        return await self.comparator.compare(
            period1_start,
            period1_end,
            period2_start,
            period2_end,
        )

    def _count_forecast_issues(self, forecasts: dict[str, Any]) -> int:
        """Count predicted issues in forecast data."""
        count = 0

        for metric, forecast in forecasts.items():
            if "violations" in metric and forecast.get("predicted_mean", 0) > 0:
                count += 1
            if "utilization" in metric and forecast.get("predicted_mean", 0) > 0.8:
                count += 1

        return count

    async def get_person_analytics(
        self,
        person_id: str,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        """
        Get comprehensive analytics for a specific person.

        Args:
            person_id: Person UUID
            start_date: Analysis start date
            end_date: Analysis end date

        Returns:
            Person-specific metrics, workload trends, predictions
        """
        # Get person details
        result = await self.db.execute(select(Person).where(Person.id == person_id))
        person = result.scalar_one_or_none()

        if not person:
            raise ValueError(f"Person {person_id} not found")

            # Calculate person-specific metrics
        metrics = await self.calculate_all_metrics(
            start_date, end_date, person_id=person_id
        )

        # Get workload distribution
        workload_dist = await self.aggregator.get_workload_distribution(
            start_date, end_date, person_id
        )

        # Get rotation history
        rotation_history = await self.aggregator.get_rotation_history(
            start_date, end_date, person_id
        )

        return {
            "person": {
                "id": str(person.id),
                "name": person.name,
                "type": person.type,
                "pgy_level": person.pgy_level,
            },
            "metrics": metrics,
            "workload_distribution": workload_dist,
            "rotation_history": rotation_history,
        }
