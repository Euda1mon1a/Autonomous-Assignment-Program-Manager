"""
Rotation Metrics - Analyzes rotation-specific metrics.
"""

from datetime import date
from typing import Any, Dict, Optional
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.rotation_template import RotationTemplate

logger = logging.getLogger(__name__)


class RotationMetrics:
    """Analyzes rotation-specific metrics and patterns."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_rotation_metrics(
        self, start_date: date, end_date: date, rotation_id: str | None = None
    ) -> dict[str, Any]:
        """Analyze metrics for all rotations or a specific rotation."""
        query = (
            select(
                RotationTemplate.id,
                RotationTemplate.name,
                RotationTemplate.abbreviation,
                func.count(Assignment.id).label("assignment_count"),
            )
            .join(Assignment)
            .join(Block)
            .where(and_(Block.date >= start_date, Block.date <= end_date))
            .group_by(
                RotationTemplate.id,
                RotationTemplate.name,
                RotationTemplate.abbreviation,
            )
        )

        if rotation_id:
            query = query.where(RotationTemplate.id == rotation_id)

        result = await self.db.execute(query)
        rotation_data = result.all()

        total_assignments = sum(row.assignment_count for row in rotation_data)

        return {
            "rotations": [
                {
                    "rotation_id": str(row.id),
                    "name": row.name,
                    "abbreviation": row.abbreviation,
                    "assignment_count": row.assignment_count,
                    "percentage": round(
                        row.assignment_count / total_assignments * 100, 2
                    )
                    if total_assignments > 0
                    else 0,
                }
                for row in rotation_data
            ],
            "total_assignments": total_assignments,
        }
