"""
Workload Distribution - Analyzes workload distribution across people.
"""

from datetime import date
from typing import Any, Dict, List, Optional
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import numpy as np

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person

logger = logging.getLogger(__name__)


class WorkloadDistribution:
    """Analyzes workload distribution and equity."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def analyze_distribution(
        self, start_date: date, end_date: date
    ) -> dict[str, Any]:
        """Analyze workload distribution across all people."""
        query = (
            select(
                Person.id,
                Person.name,
                Person.type,
                Person.pgy_level,
                func.count(Assignment.id).label("assignment_count"),
            )
            .join(Assignment)
            .join(Block)
            .where(and_(Block.date >= start_date, Block.date <= end_date))
            .group_by(Person.id, Person.name, Person.type, Person.pgy_level)
        )

        result = await self.db.execute(query)
        workload_data = result.all()

        counts = [row.assignment_count for row in workload_data]

        # Calculate Gini coefficient for equity
        gini = self._calculate_gini(counts) if counts else 0

        return {
            "distribution": [
                {
                    "person_id": str(row.id),
                    "name": row.name,
                    "type": row.type,
                    "pgy_level": row.pgy_level,
                    "assignments": row.assignment_count,
                    "estimated_hours": row.assignment_count * 4,
                }
                for row in workload_data
            ],
            "stats": {
                "mean": float(np.mean(counts)) if counts else 0,
                "std": float(np.std(counts)) if counts else 0,
                "min": int(np.min(counts)) if counts else 0,
                "max": int(np.max(counts)) if counts else 0,
                "gini_coefficient": round(gini, 3),
            },
        }

    def _calculate_gini(self, values: list[float]) -> float:
        """Calculate Gini coefficient for inequality measure."""
        if not values:
            return 0
        sorted_values = sorted(values)
        n = len(sorted_values)
        cumsum = np.cumsum(sorted_values)
        return (
            (
                2
                * sum((i + 1) * v for i, v in enumerate(sorted_values))
                / (n * cumsum[-1])
                - (n + 1) / n
            )
            if cumsum[-1] > 0
            else 0
        )
