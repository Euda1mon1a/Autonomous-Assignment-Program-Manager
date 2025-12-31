"""KPI Calculator - Calculates key performance indicators."""

from datetime import date, timedelta
from typing import Any, Dict
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person

logger = logging.getLogger(__name__)


class KPICalculator:
    """Calculates key performance indicators."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_kpis(self, days_back: int = 30) -> Dict[str, Any]:
        """Calculate all KPIs."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)

        coverage_kpi = await self._calculate_coverage_kpi(start_date, end_date)
        workload_kpi = await self._calculate_workload_kpi(start_date, end_date)
        utilization_kpi = await self._calculate_utilization_kpi(start_date, end_date)

        return {
            "coverage": coverage_kpi,
            "workload": workload_kpi,
            "utilization": utilization_kpi,
            "period_days": days_back,
        }

    async def _calculate_coverage_kpi(
        self, start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """Calculate coverage KPI."""
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

        coverage = total_assignments / total_blocks

        return {
            "value": round(coverage * 100, 2),
            "unit": "%",
            "target": 95.0,
            "status": "good" if coverage >= 0.95 else "needs_attention",
        }

    async def _calculate_workload_kpi(
        self, start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """Calculate workload KPI."""
        assignments_result = await self.db.execute(
            select(func.count(Assignment.id))
            .join(Block)
            .where(and_(Block.date >= start_date, Block.date <= end_date))
        )
        total_assignments = assignments_result.scalar() or 0

        days = (end_date - start_date).days + 1
        weeks = days / 7
        avg_weekly_hours = (total_assignments * 4) / weeks if weeks > 0 else 0

        return {
            "value": round(avg_weekly_hours, 2),
            "unit": "hours/week",
            "target": 60.0,
            "status": "good" if avg_weekly_hours <= 70 else "high",
        }

    async def _calculate_utilization_kpi(
        self, start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """Calculate utilization KPI."""
        capacity_result = await self.db.execute(select(func.count(Person.id)))
        capacity = capacity_result.scalar() or 1

        assignments_result = await self.db.execute(
            select(func.count(Assignment.id))
            .join(Block)
            .where(and_(Block.date >= start_date, Block.date <= end_date))
        )
        total_assignments = assignments_result.scalar() or 0

        blocks_result = await self.db.execute(
            select(func.count(Block.id)).where(
                and_(Block.date >= start_date, Block.date <= end_date)
            )
        )
        total_blocks = blocks_result.scalar() or 1

        utilization = total_assignments / (capacity * total_blocks)

        return {
            "value": round(utilization * 100, 2),
            "unit": "%",
            "target": 75.0,
            "threshold": 80.0,
            "status": "good" if utilization <= 0.8 else "high",
        }
