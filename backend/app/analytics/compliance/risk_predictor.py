"""
Risk Predictor - Predicts compliance risks.
"""

from datetime import date, timedelta
from typing import Any, Dict, List
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person

logger = logging.getLogger(__name__)


class RiskPredictor:
    """Predicts compliance risks based on current patterns."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def predict_risks(
        self, start_date: date, forecast_days: int = 30
    ) -> Dict[str, Any]:
        """Predict compliance risks for future period."""
        end_date = start_date + timedelta(days=forecast_days)

        # Get current workload patterns
        high_risk_persons = await self._identify_high_risk_persons(
            start_date - timedelta(days=30), start_date
        )

        return {
            "high_risk_persons": high_risk_persons,
            "forecast_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": forecast_days,
            },
            "risk_level": "medium" if len(high_risk_persons) > 0 else "low",
        }

    async def _identify_high_risk_persons(
        self, start_date: date, end_date: date, threshold_hours: float = 75
    ) -> List[Dict[str, Any]]:
        """Identify persons at risk of violations."""
        query = (
            select(
                Person.id,
                Person.name,
                func.count(Assignment.id).label("assignment_count"),
            )
            .join(Assignment)
            .join(Block)
            .where(
                and_(
                    Person.type == "resident",
                    Block.date >= start_date,
                    Block.date <= end_date,
                )
            )
            .group_by(Person.id, Person.name)
        )

        result = await self.db.execute(query)
        person_data = result.all()

        high_risk = []
        for row in person_data:
            estimated_hours = row.assignment_count * 4  # 4 hours per half-day
            weeks = (end_date - start_date).days / 7
            weekly_avg = estimated_hours / weeks if weeks > 0 else 0

            if weekly_avg > threshold_hours:
                high_risk.append({
                    "person_id": str(row.id),
                    "person_name": row.name,
                    "weekly_average_hours": round(weekly_avg, 2),
                    "risk_factor": "high_workload",
                })

        return high_risk
