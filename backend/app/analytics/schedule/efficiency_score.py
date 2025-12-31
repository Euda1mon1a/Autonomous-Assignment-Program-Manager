"""
Efficiency Score - Calculates schedule efficiency metrics.
"""

from datetime import date
from typing import Any, Dict
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person

logger = logging.getLogger(__name__)


class EfficiencyScore:
    """Calculates schedule efficiency scores."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_efficiency(
        self, start_date: date, end_date: date
    ) -> dict[str, Any]:
        """Calculate overall schedule efficiency score."""
        # Coverage rate
        blocks_result = await self.db.execute(
            select(func.count(Block.id)).where(
                and_(Block.date >= start_date, Block.date <= end_date)
            )
        )
        total_blocks = blocks_result.scalar() or 1

        assignments_result = await self.db.execute(
            select(func.count(Assignment.id))
            .join(Block)
            .where(and_(Block.date >= start_date, Block.date <= end_date))
        )
        total_assignments = assignments_result.scalar() or 0

        coverage_rate = total_assignments / total_blocks

        # Workload balance (lower std = more balanced)
        person_counts = await self.db.execute(
            select(func.count(Assignment.id))
            .join(Block)
            .where(and_(Block.date >= start_date, Block.date <= end_date))
            .group_by(Assignment.person_id)
        )
        counts = [row[0] for row in person_counts.all()]

        import numpy as np

        workload_std = float(np.std(counts)) if counts else 0
        workload_mean = float(np.mean(counts)) if counts else 1
        balance_score = (
            1 - min(workload_std / workload_mean, 1) if workload_mean > 0 else 0
        )

        # Combined efficiency score (0-100)
        efficiency = (coverage_rate * 0.6 + balance_score * 0.4) * 100

        return {
            "efficiency_score": round(efficiency, 2),
            "coverage_rate": round(coverage_rate, 3),
            "balance_score": round(balance_score, 3),
            "components": {
                "coverage_weight": 0.6,
                "balance_weight": 0.4,
            },
        }
