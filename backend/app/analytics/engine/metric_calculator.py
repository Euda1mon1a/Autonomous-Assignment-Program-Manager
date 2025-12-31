"""
Metric Calculator - Computes schedule, compliance, and resilience metrics.
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
import numpy as np

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.absence import Absence
from app.models.swap import SwapRequest

logger = logging.getLogger(__name__)


class MetricCalculator:
    """
    Calculates various metrics for schedule analysis.

    Metrics include:
    - Schedule metrics: Coverage, workload, efficiency
    - Compliance metrics: ACGME violations, work hours
    - Resilience metrics: Utilization, N-1 status
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize metric calculator.

        Args:
            db: Database session
        """
        self.db = db

    async def calculate_schedule_metrics(
        self,
        start_date: date,
        end_date: date,
        person_id: str | None = None,
        rotation_type: str | None = None,
    ) -> dict[str, Any]:
        """
        Calculate schedule-related metrics.

        Args:
            start_date: Period start date
            end_date: Period end date
            person_id: Optional person filter
            rotation_type: Optional rotation filter

        Returns:
            Dict containing:
            - coverage_rate: % of blocks filled
            - avg_workload_hours: Average weekly hours
            - total_assignments: Total assignment count
            - unique_persons: Number of people assigned
            - rotation_distribution: Assignments by rotation type
        """
        # Build query for assignments in date range
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
        )

        if person_id:
            query = query.where(Assignment.person_id == person_id)

        result = await self.db.execute(query)
        assignments = result.scalars().all()

        # Get total blocks in period
        blocks_query = select(func.count(Block.id)).where(
            and_(
                Block.date >= start_date,
                Block.date <= end_date,
            )
        )
        total_blocks_result = await self.db.execute(blocks_query)
        total_blocks = total_blocks_result.scalar() or 0

        # Calculate metrics
        total_assignments = len(assignments)
        unique_persons = len(set(a.person_id for a in assignments))

        coverage_rate = (
            (total_assignments / total_blocks * 100) if total_blocks > 0 else 0
        )

        # Calculate workload (estimate 4 hours per half-day block)
        total_hours = total_assignments * 4
        days = (end_date - start_date).days + 1
        weeks = days / 7
        avg_weekly_hours = total_hours / weeks if weeks > 0 else 0

        # Rotation distribution
        rotation_counts: dict[str, int] = {}
        for assignment in assignments:
            rotation_name = assignment.activity_name
            rotation_counts[rotation_name] = rotation_counts.get(rotation_name, 0) + 1

        return {
            "coverage_rate": round(coverage_rate, 2),
            "avg_workload_hours": round(avg_weekly_hours, 2),
            "total_assignments": total_assignments,
            "total_blocks": total_blocks,
            "unique_persons": unique_persons,
            "rotation_distribution": rotation_counts,
            "period_days": days,
            "period_weeks": round(weeks, 2),
        }

    async def calculate_compliance_metrics(
        self,
        start_date: date,
        end_date: date,
        person_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Calculate ACGME compliance metrics.

        Args:
            start_date: Period start date
            end_date: Period end date
            person_id: Optional person filter

        Returns:
            Dict containing:
            - compliance_score: Overall compliance (0-100)
            - total_violations: Count of violations
            - work_hour_violations: 80-hour rule violations
            - day_off_violations: 1-in-7 violations
            - avg_weekly_hours: Average hours per week
            - max_weekly_hours: Maximum weekly hours
        """
        # Get all residents (or specific person)
        person_query = select(Person).where(Person.type == "resident")
        if person_id:
            person_query = person_query.where(Person.id == person_id)

        result = await self.db.execute(person_query)
        persons = result.scalars().all()

        total_violations = 0
        work_hour_violations = 0
        day_off_violations = 0
        weekly_hours_list = []

        for person in persons:
            # Get assignments for this person in date range
            query = (
                select(Assignment)
                .join(Block)
                .where(
                    and_(
                        Assignment.person_id == person.id,
                        Block.date >= start_date,
                        Block.date <= end_date,
                    )
                )
                .options(selectinload(Assignment.block))
            )

            result = await self.db.execute(query)
            assignments = result.scalars().all()

            # Check 80-hour rule (rolling 4-week average)
            violations_80hr = self._check_80_hour_rule(assignments)
            work_hour_violations += len(violations_80hr)

            # Check 1-in-7 rule
            violations_1in7 = self._check_1_in_7_rule(assignments)
            day_off_violations += len(violations_1in7)

            # Calculate weekly hours
            for week_hours in self._calculate_weekly_hours(assignments):
                weekly_hours_list.append(week_hours)

        total_violations = work_hour_violations + day_off_violations

        # Calculate compliance score (100 = perfect, 0 = many violations)
        expected_compliant_weeks = len(persons) * ((end_date - start_date).days // 7)
        if expected_compliant_weeks > 0:
            compliance_score = max(
                0, 100 - (total_violations / expected_compliant_weeks * 100)
            )
        else:
            compliance_score = 100

        return {
            "compliance_score": round(compliance_score, 2),
            "total_violations": total_violations,
            "work_hour_violations": work_hour_violations,
            "day_off_violations": day_off_violations,
            "avg_weekly_hours": (
                round(np.mean(weekly_hours_list), 2) if weekly_hours_list else 0
            ),
            "max_weekly_hours": max(weekly_hours_list) if weekly_hours_list else 0,
            "min_weekly_hours": min(weekly_hours_list) if weekly_hours_list else 0,
        }

    async def calculate_resilience_metrics(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        """
        Calculate resilience framework metrics.

        Args:
            start_date: Period start date
            end_date: Period end date

        Returns:
            Dict containing:
            - avg_utilization: Average utilization rate (0-1)
            - max_utilization: Peak utilization
            - high_utilization_count: Days above 80% threshold
            - n1_vulnerable_days: Days vulnerable to N-1 failure
            - swap_count: Number of swaps executed
        """
        # Get all persons
        result = await self.db.execute(select(Person))
        persons = result.scalars().all()
        total_capacity = len(persons)

        # Get assignments per day
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
        daily_assignments = result.all()

        utilizations = []
        high_util_count = 0
        n1_vulnerable_count = 0

        for day_date, assignment_count in daily_assignments:
            if total_capacity > 0:
                utilization = assignment_count / total_capacity
                utilizations.append(utilization)

                if utilization > 0.8:
                    high_util_count += 1

                # N-1 vulnerable if losing 1 person would exceed capacity
                if utilization > 0.9:
                    n1_vulnerable_count += 1

        # Get swap count
        swap_query = select(func.count(SwapRequest.id)).where(
            and_(
                SwapRequest.created_at >= start_date,
                SwapRequest.created_at <= end_date,
                SwapRequest.status == "approved",
            )
        )
        swap_result = await self.db.execute(swap_query)
        swap_count = swap_result.scalar() or 0

        return {
            "avg_utilization": round(np.mean(utilizations), 3) if utilizations else 0,
            "max_utilization": round(max(utilizations), 3) if utilizations else 0,
            "min_utilization": round(min(utilizations), 3) if utilizations else 0,
            "high_utilization_count": high_util_count,
            "high_utilization_rate": (
                round(high_util_count / len(utilizations), 3) if utilizations else 0
            ),
            "n1_vulnerable_days": n1_vulnerable_count,
            "swap_count": swap_count,
            "total_capacity": total_capacity,
        }

    def _check_80_hour_rule(
        self, assignments: list[Assignment]
    ) -> list[dict[str, Any]]:
        """
        Check for 80-hour rule violations.

        Returns list of violations with date and hours.
        """
        violations = []

        # Group by week
        weeks: dict[int, list[Assignment]] = {}
        for assignment in assignments:
            if assignment.block and assignment.block.date:
                week_num = assignment.block.date.isocalendar()[1]
                if week_num not in weeks:
                    weeks[week_num] = []
                weeks[week_num].append(assignment)

        # Check each 4-week rolling window
        week_nums = sorted(weeks.keys())
        for i in range(len(week_nums) - 3):
            window_assignments = []
            for j in range(4):
                window_assignments.extend(weeks[week_nums[i + j]])

            # Estimate hours (4 per half-day block)
            total_hours = len(window_assignments) * 4

            if total_hours > 80 * 4:  # 80 hours/week * 4 weeks
                violations.append(
                    {
                        "type": "80_hour_rule",
                        "week_start": week_nums[i],
                        "hours": total_hours,
                    }
                )

        return violations

    def _check_1_in_7_rule(self, assignments: list[Assignment]) -> list[dict[str, Any]]:
        """
        Check for 1-in-7 day off rule violations.

        Returns list of violations with date ranges.
        """
        violations = []

        if not assignments:
            return violations

        # Sort by date
        sorted_assignments = sorted(
            assignments, key=lambda a: a.block.date if a.block else date.min
        )

        # Check for 7 consecutive days with assignments
        consecutive_days = 0
        last_date = None

        for assignment in sorted_assignments:
            if not assignment.block:
                continue

            current_date = assignment.block.date

            if last_date and (current_date - last_date).days == 1:
                consecutive_days += 1
            else:
                consecutive_days = 1

            if consecutive_days >= 7:
                violations.append(
                    {
                        "type": "1_in_7_rule",
                        "date": current_date.isoformat(),
                        "consecutive_days": consecutive_days,
                    }
                )

            last_date = current_date

        return violations

    def _calculate_weekly_hours(self, assignments: list[Assignment]) -> list[float]:
        """
        Calculate hours per week for assignments.

        Returns list of weekly hour totals.
        """
        weeks: dict[int, int] = {}

        for assignment in assignments:
            if assignment.block and assignment.block.date:
                week_num = assignment.block.date.isocalendar()[1]
                weeks[week_num] = weeks.get(week_num, 0) + 1

        # Convert block counts to hours (4 hours per half-day)
        return [count * 4 for count in weeks.values()]
