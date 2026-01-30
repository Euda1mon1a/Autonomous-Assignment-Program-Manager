"""
Data Aggregator - Aggregates schedule data for analytics.
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import selectinload
import pandas as pd

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate

logger = logging.getLogger(__name__)


class DataAggregator:
    """
    Aggregates schedule data for analysis.

    Provides methods to:
    - Aggregate assignments by various dimensions
    - Calculate distributions
    - Generate summary statistics
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize data aggregator.

        Args:
            db: Database session
        """
        self.db = db

    async def get_workload_distribution(
        self,
        start_date: date,
        end_date: date,
        person_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Get workload distribution statistics.

        Args:
            start_date: Period start
            end_date: Period end
            person_id: Optional person filter

        Returns:
            Dict with workload stats per person
        """
        query = (
            select(
                Person.id,
                Person.name,
                Person.type,
                Person.pgy_level,
                func.count(Assignment.id).label("assignment_count"),
            )
            .join(Assignment, Person.id == Assignment.person_id)
            .join(Block, Assignment.block_id == Block.id)
            .where(
                and_(
                    Block.date >= start_date,
                    Block.date <= end_date,
                )
            )
            .group_by(Person.id, Person.name, Person.type, Person.pgy_level)
        )

        if person_id:
            query = query.where(Person.id == person_id)

        result = await self.db.execute(query)
        workload_data = result.all()

        # Calculate statistics
        assignment_counts = [row.assignment_count for row in workload_data]

        distribution = []
        for row in workload_data:
            estimated_hours = row.assignment_count * 4  # 4 hours per half-day
            distribution.append(
                {
                    "person_id": str(row.id),
                    "person_name": row.name,
                    "person_type": row.type,
                    "pgy_level": row.pgy_level,
                    "assignment_count": row.assignment_count,
                    "estimated_hours": estimated_hours,
                }
            )

        return {
            "distribution": distribution,
            "stats": {
                "mean": sum(assignment_counts) / len(assignment_counts)
                if assignment_counts
                else 0,
                "min": min(assignment_counts) if assignment_counts else 0,
                "max": max(assignment_counts) if assignment_counts else 0,
                "total": sum(assignment_counts),
                "person_count": len(assignment_counts),
            },
        }

    async def get_rotation_history(
        self,
        start_date: date,
        end_date: date,
        person_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get rotation assignment history.

        Args:
            start_date: Period start
            end_date: Period end
            person_id: Optional person filter

        Returns:
            List of rotation assignments with dates
        """
        query = (
            select(Assignment)
            .join(Block)
            .where(
                and_(
                    Block.date >= start_date,
                    Block.date <= end_date,
                )
            )
            .options(selectinload(Assignment.block))
            .options(selectinload(Assignment.person))
            .options(selectinload(Assignment.rotation_template))
            .order_by(Block.date)
        )

        if person_id:
            query = query.where(Assignment.person_id == person_id)

        result = await self.db.execute(query)
        assignments = result.scalars().all()

        history = []
        for assignment in assignments:
            if assignment.block:
                history.append(
                    {
                        "date": assignment.block.date.isoformat(),
                        "person_id": str(assignment.person_id),
                        "person_name": assignment.person.name
                        if assignment.person
                        else "Unknown",
                        "rotation": assignment.activity_name,
                        "role": assignment.role,
                        "block_session": assignment.block.session,
                    }
                )

        return history

    async def aggregate_by_rotation(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[str, dict[str, Any]]:
        """
        Aggregate assignments by rotation type.

        Args:
            start_date: Period start
            end_date: Period end

        Returns:
            Dict mapping rotation name to stats
        """
        query = (
            select(
                RotationTemplate.name,
                func.count(Assignment.id).label("count"),
            )
            .join(
                Assignment,
                RotationTemplate.id == Assignment.rotation_template_id,
                isouter=True,
            )
            .join(Block, Assignment.block_id == Block.id)
            .where(
                and_(
                    Block.date >= start_date,
                    Block.date <= end_date,
                )
            )
            .group_by(RotationTemplate.name)
        )

        result = await self.db.execute(query)
        rotation_data = result.all()

        aggregated = {}
        for row in rotation_data:
            aggregated[row.name] = {
                "count": row.count,
                "percentage": 0,  # Will calculate after getting total
            }

            # Calculate percentages
        total = sum(data["count"] for data in aggregated.values())
        for rotation_name, data in aggregated.items():
            data["percentage"] = (data["count"] / total * 100) if total > 0 else 0

        return aggregated

    async def aggregate_by_time(
        self,
        start_date: date,
        end_date: date,
        granularity: str = "week",
    ) -> pd.DataFrame:
        """
        Aggregate assignments by time period.

        Args:
            start_date: Period start
            end_date: Period end
            granularity: Time granularity (day, week, month)

        Returns:
            DataFrame with time-indexed aggregations
        """
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
            .order_by(Block.date)
        )

        result = await self.db.execute(query)
        daily_data = result.all()

        # Convert to DataFrame
        df = pd.DataFrame(
            [
                {"date": row.date, "assignment_count": row.assignment_count}
                for row in daily_data
            ]
        )

        if df.empty:
            return df

        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

        # Resample based on granularity
        if granularity == "week":
            df = df.resample("W").sum()
        elif granularity == "month":
            df = df.resample("M").sum()

        return df

    async def get_coverage_gaps(
        self,
        start_date: date,
        end_date: date,
        threshold: float = 0.5,
    ) -> list[dict[str, Any]]:
        """
        Find coverage gaps (blocks with low assignment rates).

        Args:
            start_date: Period start
            end_date: Period end
            threshold: Coverage threshold (0-1)

        Returns:
            List of dates with coverage below threshold
        """
        # Get expected capacity (total persons)
        person_result = await self.db.execute(select(func.count(Person.id)))
        total_capacity = person_result.scalar() or 1

        # Get daily assignments
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
        daily_data = result.all()

        gaps = []
        for row in daily_data:
            coverage_rate = row.assignment_count / total_capacity
            if coverage_rate < threshold:
                gaps.append(
                    {
                        "date": row.date.isoformat(),
                        "coverage_rate": round(coverage_rate, 3),
                        "assignments": row.assignment_count,
                        "capacity": total_capacity,
                        "gap_size": total_capacity - row.assignment_count,
                    }
                )

        return gaps

    async def get_person_rotation_summary(
        self,
        person_id: str,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        """
        Get rotation summary for a specific person.

        Args:
            person_id: Person UUID
            start_date: Period start
            end_date: Period end

        Returns:
            Summary of rotations completed
        """
        query = (
            select(
                RotationTemplate.name,
                func.count(Assignment.id).label("count"),
            )
            .join(Assignment, RotationTemplate.id == Assignment.rotation_template_id)
            .join(Block, Assignment.block_id == Block.id)
            .where(
                and_(
                    Assignment.person_id == person_id,
                    Block.date >= start_date,
                    Block.date <= end_date,
                )
            )
            .group_by(RotationTemplate.name)
        )

        result = await self.db.execute(query)
        rotation_data = result.all()

        rotations = []
        total_blocks = 0
        for row in rotation_data:
            rotations.append(
                {
                    "rotation": row.name,
                    "blocks": row.count,
                    "weeks": round(
                        row.count / 4, 2
                    ),  # 4 blocks per week (AM/PM * 2.5 days)
                }
            )
            total_blocks += row.count

        return {
            "person_id": person_id,
            "total_blocks": total_blocks,
            "total_weeks": round(total_blocks / 4, 2),
            "rotations": rotations,
        }
