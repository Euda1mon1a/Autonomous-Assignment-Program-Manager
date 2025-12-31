"""
Coverage Analyzer - Analyzes schedule coverage patterns.
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


class CoverageAnalyzer:
    """
    Analyzes schedule coverage patterns and gaps.

    Provides metrics for:
    - Overall coverage rates
    - Coverage by rotation type
    - Coverage gaps and risks
    - Redundancy analysis
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize coverage analyzer.

        Args:
            db: Database session
        """
        self.db = db

    async def analyze_coverage(
        self,
        start_date: date,
        end_date: date,
        rotation_type: str | None = None,
    ) -> dict[str, Any]:
        """
        Analyze overall coverage for a period.

        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            rotation_type: Optional rotation filter

        Returns:
            Coverage analysis with rates, gaps, and trends
        """
        # Get total blocks
        blocks_query = select(func.count(Block.id)).where(
            and_(
                Block.date >= start_date,
                Block.date <= end_date,
            )
        )
        total_blocks_result = await self.db.execute(blocks_query)
        total_blocks = total_blocks_result.scalar() or 0

        # Get assignments
        assignments_query = (
            select(func.count(Assignment.id))
            .join(Block)
            .where(
                and_(
                    Block.date >= start_date,
                    Block.date <= end_date,
                )
            )
        )
        if rotation_type:
            assignments_query = assignments_query.join(
                Assignment.rotation_template
            ).where(Assignment.rotation_template.has(name=rotation_type))

        assignments_result = await self.db.execute(assignments_query)
        total_assignments = assignments_result.scalar() or 0

        # Calculate coverage rate
        coverage_rate = (total_assignments / total_blocks) if total_blocks > 0 else 0

        # Get coverage gaps
        gaps = await self._find_coverage_gaps(start_date, end_date, rotation_type)

        # Get coverage by day of week
        day_of_week_coverage = await self._analyze_day_of_week_coverage(
            start_date, end_date, rotation_type
        )

        # Calculate redundancy
        redundancy = await self._calculate_redundancy(start_date, end_date)

        return {
            "coverage_rate": round(coverage_rate, 3),
            "total_blocks": total_blocks,
            "assigned_blocks": total_assignments,
            "uncovered_blocks": total_blocks - total_assignments,
            "gaps": gaps,
            "day_of_week_coverage": day_of_week_coverage,
            "redundancy": redundancy,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": (end_date - start_date).days + 1,
            },
        }

    async def _find_coverage_gaps(
        self,
        start_date: date,
        end_date: date,
        rotation_type: str | None = None,
        threshold: float = 0.5,
    ) -> list[dict[str, Any]]:
        """Find blocks with low coverage."""
        # Get daily coverage
        query = (
            select(
                Block.date,
                func.count(Assignment.id).label("assignment_count"),
            )
            .join(Assignment, Block.id == Assignment.block_id, isouter=True)
            .where(
                and_(
                    Block.date >= start_date,
                    Block.date <= end_date,
                )
            )
            .group_by(Block.date)
        )

        result = await self.db.execute(query)
        daily_coverage = result.all()

        # Get total capacity
        capacity_result = await self.db.execute(select(func.count(Person.id)))
        total_capacity = capacity_result.scalar() or 1

        # Find gaps
        gaps = []
        for day_date, assignment_count in daily_coverage:
            coverage = assignment_count / total_capacity
            if coverage < threshold:
                gaps.append(
                    {
                        "date": day_date.isoformat(),
                        "coverage_rate": round(coverage, 3),
                        "assignments": assignment_count,
                        "capacity": total_capacity,
                        "severity": "high" if coverage < 0.3 else "medium",
                    }
                )

        return gaps

    async def _analyze_day_of_week_coverage(
        self,
        start_date: date,
        end_date: date,
        rotation_type: str | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Analyze coverage by day of week."""
        query = (
            select(Block.date, func.count(Assignment.id))
            .join(Assignment, Block.id == Assignment.block_id, isouter=True)
            .where(
                and_(
                    Block.date >= start_date,
                    Block.date <= end_date,
                )
            )
            .group_by(Block.date)
        )

        result = await self.db.execute(query)
        daily_data = result.all()

        # Group by day of week
        dow_coverage: dict[int, list[int]] = {i: [] for i in range(7)}

        for day_date, assignment_count in daily_data:
            dow = day_date.weekday()  # 0 = Monday, 6 = Sunday
            dow_coverage[dow].append(assignment_count)

        # Calculate stats for each day
        dow_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        day_stats = {}

        for dow, assignments in dow_coverage.items():
            if assignments:
                day_stats[dow_names[dow]] = {
                    "mean": round(np.mean(assignments), 2),
                    "std": round(np.std(assignments), 2),
                    "min": int(np.min(assignments)),
                    "max": int(np.max(assignments)),
                    "count": len(assignments),
                }

        return day_stats

    async def _calculate_redundancy(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        """Calculate redundancy (backup coverage)."""
        # Get blocks with multiple assignments
        query = (
            select(
                Block.date,
                func.count(Assignment.id).label("assignment_count"),
            )
            .join(Assignment)
            .where(
                and_(
                    Block.date >= start_date,
                    Block.date <= end_date,
                )
            )
            .group_by(Block.date, Block.id)
            .having(func.count(Assignment.id) > 1)
        )

        result = await self.db.execute(query)
        redundant_blocks = result.all()

        total_query = select(func.count(Block.id)).where(
            and_(
                Block.date >= start_date,
                Block.date <= end_date,
            )
        )
        total_result = await self.db.execute(total_query)
        total_blocks = total_result.scalar() or 1

        redundancy_rate = len(redundant_blocks) / total_blocks

        return {
            "redundancy_rate": round(redundancy_rate, 3),
            "redundant_blocks": len(redundant_blocks),
            "total_blocks": total_blocks,
        }

    async def get_coverage_trends(
        self,
        start_date: date,
        end_date: date,
        granularity: str = "week",
    ) -> pd.DataFrame:
        """
        Get coverage trends over time.

        Args:
            start_date: Analysis start
            end_date: Analysis end
            granularity: Time granularity (day, week, month)

        Returns:
            DataFrame with time-indexed coverage rates
        """
        query = (
            select(
                Block.date,
                func.count(Assignment.id).label("assignments"),
            )
            .join(Assignment, Block.id == Assignment.block_id, isouter=True)
            .where(
                and_(
                    Block.date >= start_date,
                    Block.date <= end_date,
                )
            )
            .group_by(Block.date)
        )

        result = await self.db.execute(query)
        daily_data = result.all()

        # Get capacity
        capacity_result = await self.db.execute(select(func.count(Person.id)))
        capacity = capacity_result.scalar() or 1

        # Create DataFrame
        df = pd.DataFrame(
            [
                {
                    "date": row.date,
                    "coverage_rate": row.assignments / capacity,
                }
                for row in daily_data
            ]
        )

        if df.empty:
            return df

        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

        # Resample
        if granularity == "week":
            df = df.resample("W").mean()
        elif granularity == "month":
            df = df.resample("M").mean()

        return df
