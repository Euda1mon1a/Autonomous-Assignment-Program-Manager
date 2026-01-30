"""
Time Series Analyzer - Analyzes temporal patterns in schedule data.
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
import pandas as pd
import numpy as np

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person

logger = logging.getLogger(__name__)


class TimeSeriesAnalyzer:
    """
    Analyzes time series data for schedule metrics.

    Provides:
    - Time series extraction
    - Trend calculation
    - Seasonality detection
    - Moving averages
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize time series analyzer.

        Args:
            db: Database session
        """
        self.db = db

    async def get_time_series(
        self,
        start_date: date,
        end_date: date,
        granularity: str = "week",
        metrics: list[str] | None = None,
    ) -> dict[str, pd.Series]:
        """
        Extract time series data for various metrics.

        Args:
            start_date: Series start date
            end_date: Series end date
            granularity: Time granularity (day, week, month)
            metrics: List of metrics to extract (None = all)

        Returns:
            Dict mapping metric names to pandas Series
        """
        if metrics is None:
            metrics = [
                "assignment_count",
                "coverage_rate",
                "workload_hours",
                "utilization",
            ]

        time_series = {}

        # Get assignment counts over time
        if "assignment_count" in metrics:
            time_series["assignment_count"] = await self._get_assignment_count_series(
                start_date, end_date, granularity
            )

            # Get coverage rate over time
        if "coverage_rate" in metrics:
            time_series["coverage_rate"] = await self._get_coverage_rate_series(
                start_date, end_date, granularity
            )

            # Get workload hours over time
        if "workload_hours" in metrics:
            time_series["workload_hours"] = await self._get_workload_series(
                start_date, end_date, granularity
            )

            # Get utilization over time
        if "utilization" in metrics:
            time_series["utilization"] = await self._get_utilization_series(
                start_date, end_date, granularity
            )

        return time_series

    async def _get_assignment_count_series(
        self,
        start_date: date,
        end_date: date,
        granularity: str,
    ) -> pd.Series:
        """Get time series of assignment counts."""
        query = (
            select(
                Block.date,
                func.count(Assignment.id).label("count"),
            )
            .join(Assignment, Block.id == Assignment.block_id, isouter=True)
            .where(
                and_(
                    Block.date >= start_date,
                    Block.date <= end_date,
                )
            )
            .group_by(Block.date)
            .order_by(Block.date)
        )

        result = await self.db.execute(query)
        data = result.all()

        df = pd.DataFrame([{"date": row.date, "count": row.count} for row in data])

        if df.empty:
            return pd.Series(dtype=float)

        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

        # Resample based on granularity
        if granularity == "week":
            series = df["count"].resample("W").sum()
        elif granularity == "month":
            series = df["count"].resample("M").sum()
        else:
            series = df["count"]

        return series

    async def _get_coverage_rate_series(
        self,
        start_date: date,
        end_date: date,
        granularity: str,
    ) -> pd.Series:
        """Get time series of coverage rates."""
        # Get total capacity
        person_result = await self.db.execute(select(func.count(Person.id)))
        total_capacity = person_result.scalar() or 1

        # Get assignment counts
        assignment_series = await self._get_assignment_count_series(
            start_date, end_date, granularity
        )

        # Calculate coverage rate
        # For daily: coverage = assignments / capacity
        # For weekly/monthly: coverage = avg assignments per day / capacity
        if granularity == "day":
            coverage_series = assignment_series / total_capacity
        else:
            # For aggregated periods, divide by number of days in period
            coverage_series = assignment_series / (
                total_capacity * 7
            )  # Assume 7 days per week

        return coverage_series

    async def _get_workload_series(
        self,
        start_date: date,
        end_date: date,
        granularity: str,
    ) -> pd.Series:
        """Get time series of workload hours."""
        # Get assignment counts
        assignment_series = await self._get_assignment_count_series(
            start_date, end_date, granularity
        )

        # Convert to hours (4 hours per half-day block)
        workload_series = assignment_series * 4

        return workload_series

    async def _get_utilization_series(
        self,
        start_date: date,
        end_date: date,
        granularity: str,
    ) -> pd.Series:
        """Get time series of utilization rates."""
        # Utilization = assignments / total capacity
        return await self._get_coverage_rate_series(start_date, end_date, granularity)

    def calculate_moving_average(
        self,
        series: pd.Series,
        window: int = 4,
    ) -> pd.Series:
        """
        Calculate moving average.

        Args:
            series: Input time series
            window: Window size (e.g., 4 weeks)

        Returns:
            Moving average series
        """
        return series.rolling(window=window, min_periods=1).mean()

    def calculate_trend(
        self,
        series: pd.Series,
    ) -> dict[str, Any]:
        """
        Calculate trend statistics.

        Args:
            series: Input time series

        Returns:
            Dict with trend direction, slope, R²
        """
        if len(series) < 2:
            return {
                "direction": "insufficient_data",
                "slope": 0,
                "r_squared": 0,
            }

            # Convert to numpy arrays
        x = np.arange(len(series))
        y = series.values

        # Calculate linear regression
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]

        # Calculate R²
        y_pred = np.polyval(coeffs, x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        # Determine direction
        if abs(slope) < 0.01:
            direction = "stable"
        elif slope > 0:
            direction = "increasing"
        else:
            direction = "decreasing"

        return {
            "direction": direction,
            "slope": float(slope),
            "r_squared": float(r_squared),
        }

    def detect_seasonality(
        self,
        series: pd.Series,
        period: int = 7,
    ) -> dict[str, Any]:
        """
        Detect seasonality in time series.

        Args:
            series: Input time series
            period: Seasonal period (e.g., 7 for weekly)

        Returns:
            Dict with seasonality metrics
        """
        if len(series) < period * 2:
            return {
                "has_seasonality": False,
                "strength": 0,
            }

            # Simple autocorrelation at lag=period
        if len(series) > period:
            autocorr = series.autocorr(lag=period)
            has_seasonality = abs(autocorr) > 0.3
            strength = abs(autocorr)
        else:
            has_seasonality = False
            strength = 0

        return {
            "has_seasonality": has_seasonality,
            "strength": float(strength),
            "period": period,
        }

    def calculate_percent_change(
        self,
        series: pd.Series,
        periods: int = 1,
    ) -> pd.Series:
        """
        Calculate percent change between periods.

        Args:
            series: Input time series
            periods: Number of periods to shift

        Returns:
            Percent change series
        """
        return series.pct_change(periods=periods) * 100

    def get_summary_statistics(
        self,
        series: pd.Series,
    ) -> dict[str, float]:
        """
        Calculate summary statistics for time series.

        Args:
            series: Input time series

        Returns:
            Dict with mean, std, min, max, etc.
        """
        return {
            "mean": float(series.mean()),
            "std": float(series.std()),
            "min": float(series.min()),
            "max": float(series.max()),
            "median": float(series.median()),
            "count": int(series.count()),
        }
