"""HalfDayScheduleService - Read service for half-day assignments.

This service provides read access to the persisted half_day_assignments table.
Legacy expansion has been archived; HalfDayAssignment is the source of truth.

The half_day_assignments table is the source of truth for daily schedules.
Use PreloadService to populate preloaded assignments, then this service to read.
"""

from datetime import date
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.activity import Activity, ActivityCategory
from app.models.half_day_assignment import AssignmentSource, HalfDayAssignment
from app.models.person import Person
from app.models.schedule_override import ScheduleOverride
from app.utils.academic_blocks import get_block_dates
from app.utils.fmc_capacity import (
    activity_is_proc_or_vas,
    slot_fmc_capacity,
)
from app.utils.supervision import assignment_requires_fmc_supervision

logger = get_logger(__name__)


class HalfDayScheduleService:
    """
    Read service for half-day assignments.

    Provides efficient queries for schedule data from the persisted
    half_day_assignments table.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_schedule_by_date_range(
        self,
        start_date: date,
        end_date: date,
        person_type: str | None = None,
        include_overrides: bool = True,
    ) -> list[HalfDayAssignment]:
        """
        Get all assignments in a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            person_type: Optional filter by person type ('resident' or 'faculty')

        Returns:
            List of HalfDayAssignment objects
        """
        stmt = (
            select(HalfDayAssignment)
            .join(HalfDayAssignment.person)
            .where(
                and_(
                    HalfDayAssignment.date >= start_date,
                    HalfDayAssignment.date <= end_date,
                )
            )
            .options(
                selectinload(HalfDayAssignment.person),
                selectinload(HalfDayAssignment.activity),
            )
            .order_by(HalfDayAssignment.date, HalfDayAssignment.time_of_day)
        )

        if person_type and not include_overrides:
            stmt = stmt.where(Person.type == person_type)

        result = await self.session.execute(stmt)
        assignments = list(result.scalars().all())

        if include_overrides:
            assignments = await self._apply_overrides(assignments, start_date, end_date)
            if person_type:
                assignments = [
                    a for a in assignments if a.person and a.person.type == person_type
                ]

        return assignments

    async def get_schedule_by_person(
        self,
        person_id: UUID,
        start_date: date,
        end_date: date,
        include_overrides: bool = True,
    ) -> list[HalfDayAssignment]:
        """
        Get assignments for a specific person in a date range.

        Args:
            person_id: Person UUID
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of HalfDayAssignment objects
        """
        if include_overrides:
            assignments = await self.get_schedule_by_date_range(
                start_date=start_date,
                end_date=end_date,
                include_overrides=True,
            )
            return [a for a in assignments if a.person_id == person_id]

        stmt = (
            select(HalfDayAssignment)
            .where(
                and_(
                    HalfDayAssignment.person_id == person_id,
                    HalfDayAssignment.date >= start_date,
                    HalfDayAssignment.date <= end_date,
                )
            )
            .options(selectinload(HalfDayAssignment.activity))
            .order_by(HalfDayAssignment.date, HalfDayAssignment.time_of_day)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_schedule_by_block(
        self,
        block_number: int,
        academic_year: int,
        person_type: str | None = None,
        include_overrides: bool = True,
    ) -> list[HalfDayAssignment]:
        """
        Get all assignments for an academic block.

        Args:
            block_number: Block number (1-13)
            academic_year: Academic year (e.g., 2025 for AY 2025-2026)
            person_type: Optional filter by person type

        Returns:
            List of HalfDayAssignment objects
        """
        block_dates = get_block_dates(block_number, academic_year)
        return await self.get_schedule_by_date_range(
            block_dates.start_date,
            block_dates.end_date,
            person_type,
            include_overrides,
        )

    async def get_slot(
        self,
        person_id: UUID,
        date_val: date,
        time_of_day: str,
    ) -> HalfDayAssignment | None:
        """
        Get a specific slot assignment.

        Args:
            person_id: Person UUID
            date_val: Date
            time_of_day: 'AM' or 'PM'

        Returns:
            HalfDayAssignment or None
        """
        stmt = (
            select(HalfDayAssignment)
            .where(
                and_(
                    HalfDayAssignment.person_id == person_id,
                    HalfDayAssignment.date == date_val,
                    HalfDayAssignment.time_of_day == time_of_day,
                )
            )
            .options(
                selectinload(HalfDayAssignment.person),
                selectinload(HalfDayAssignment.activity),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_daily_schedule(
        self,
        date_val: date,
        include_overrides: bool = True,
    ) -> dict[str, list[HalfDayAssignment]]:
        """
        Get all assignments for a specific date, grouped by time of day.

        Args:
            date_val: Date to query

        Returns:
            Dict with 'AM' and 'PM' lists of assignments
        """
        stmt = (
            select(HalfDayAssignment)
            .where(HalfDayAssignment.date == date_val)
            .options(
                selectinload(HalfDayAssignment.person),
                selectinload(HalfDayAssignment.activity),
            )
            .order_by(HalfDayAssignment.time_of_day)
        )
        result = await self.session.execute(stmt)
        assignments = list(result.scalars().all())

        if include_overrides:
            assignments = await self._apply_overrides(assignments, date_val, date_val)

        return {
            "AM": [a for a in assignments if a.time_of_day == "AM"],
            "PM": [a for a in assignments if a.time_of_day == "PM"],
        }

    async def _apply_overrides(
        self,
        assignments: list[HalfDayAssignment],
        start_date: date,
        end_date: date,
    ) -> list[HalfDayAssignment]:
        if not assignments:
            return assignments

        result = await self.session.execute(
            select(ScheduleOverride).where(
                ScheduleOverride.is_active.is_(True),
                ScheduleOverride.effective_date >= start_date,
                ScheduleOverride.effective_date <= end_date,
            )
        )
        overrides = list(result.scalars().all())
        if not overrides:
            return assignments

        replacement_ids = {
            o.replacement_person_id
            for o in overrides
            if o.override_type == "coverage" and o.replacement_person_id
        }
        replacement_people = {}
        if replacement_ids:
            people_result = await self.session.execute(
                select(Person).where(Person.id.in_(replacement_ids))
            )
            replacement_people = {p.id: p for p in people_result.scalars().all()}

        overrides_by_assignment = {o.half_day_assignment_id: o for o in overrides}

        effective: list[HalfDayAssignment] = []
        for assignment in assignments:
            override = overrides_by_assignment.get(assignment.id)
            if not override:
                effective.append(assignment)
                continue
            if override.override_type == "cancellation":
                continue
            if override.override_type == "gap":
                clone = HalfDayAssignment(
                    id=assignment.id,
                    person_id=assignment.person_id,
                    date=assignment.date,
                    time_of_day=assignment.time_of_day,
                    activity_id=None,
                    counts_toward_fmc_capacity=assignment.counts_toward_fmc_capacity,
                    source=assignment.source,
                    block_assignment_id=assignment.block_assignment_id,
                    is_override=assignment.is_override,
                    override_reason=assignment.override_reason,
                    overridden_by=assignment.overridden_by,
                    overridden_at=assignment.overridden_at,
                    created_at=assignment.created_at,
                    updated_at=assignment.updated_at,
                )
                clone.activity = Activity(
                    name="GAP",
                    code="gap",
                    display_abbreviation="GAP",
                    activity_category=ActivityCategory.ADMINISTRATIVE.value,
                )
                clone.person = assignment.person
                clone.is_gap = True
                effective.append(clone)
                continue

            replacement = replacement_people.get(override.replacement_person_id)
            if not replacement:
                effective.append(assignment)
                continue

            clone = HalfDayAssignment(
                id=assignment.id,
                person_id=replacement.id,
                date=assignment.date,
                time_of_day=assignment.time_of_day,
                activity_id=assignment.activity_id,
                counts_toward_fmc_capacity=assignment.counts_toward_fmc_capacity,
                source=assignment.source,
                block_assignment_id=assignment.block_assignment_id,
                is_override=assignment.is_override,
                override_reason=assignment.override_reason,
                overridden_by=assignment.overridden_by,
                overridden_at=assignment.overridden_at,
                created_at=assignment.created_at,
                updated_at=assignment.updated_at,
            )
            clone.activity = assignment.activity
            clone.person = replacement
            effective.append(clone)

        return effective

    async def get_preloaded_slots(
        self,
        start_date: date,
        end_date: date,
    ) -> list[HalfDayAssignment]:
        """
        Get all preloaded (locked) slots in a date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List of preloaded assignments
        """
        stmt = (
            select(HalfDayAssignment)
            .where(
                and_(
                    HalfDayAssignment.date >= start_date,
                    HalfDayAssignment.date <= end_date,
                    HalfDayAssignment.source == AssignmentSource.PRELOAD.value,
                )
            )
            .options(
                selectinload(HalfDayAssignment.person),
                selectinload(HalfDayAssignment.activity),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_source(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[str, int]:
        """
        Count assignments by source in a date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Dict mapping source to count
        """
        stmt = (
            select(
                HalfDayAssignment.source,
                func.count(HalfDayAssignment.id).label("count"),
            )
            .where(
                and_(
                    HalfDayAssignment.date >= start_date,
                    HalfDayAssignment.date <= end_date,
                )
            )
            .group_by(HalfDayAssignment.source)
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        return {row.source: row.count for row in rows}

    async def get_physical_capacity(
        self,
        date_val: date,
        time_of_day: str,
    ) -> dict[str, Any]:
        """
        Calculate physical capacity for a slot.

        FMC physical capacity (soft 6 / hard 8) per half-day.

        Args:
            date_val: Date
            time_of_day: 'AM' or 'PM'

        Returns:
            Dict with count, max, and is_over_capacity
        """
        stmt = (
            select(HalfDayAssignment)
            .options(selectinload(HalfDayAssignment.activity))
            .where(
                and_(
                    HalfDayAssignment.date == date_val,
                    HalfDayAssignment.time_of_day == time_of_day,
                )
            )
        )
        result = await self.session.execute(stmt)
        assignments = result.scalars().all()

        count = slot_fmc_capacity(assignments)
        max_capacity = 8

        return {
            "date": date_val,
            "time_of_day": time_of_day,
            "clinical_count": count,
            "max_capacity": max_capacity,
            "is_over_capacity": count > max_capacity,
            "available_slots": max(0, max_capacity - count),
        }

    async def get_at_coverage(
        self,
        date_val: date,
        time_of_day: str,
    ) -> dict[str, Any]:
        """
        Calculate AT (supervision) coverage for a slot.

        AT demand based on residents in clinic:
        - PGY-1: 0.5 AT each
        - PGY-2/3: 0.25 AT each
        - PROC: +1.0 AT each

        Args:
            date_val: Date
            time_of_day: 'AM' or 'PM'

        Returns:
            Dict with demand, coverage, and is_sufficient
        """
        # Get all assignments for this slot
        stmt = (
            select(HalfDayAssignment)
            .join(HalfDayAssignment.person)
            .join(HalfDayAssignment.activity)
            .where(
                and_(
                    HalfDayAssignment.date == date_val,
                    HalfDayAssignment.time_of_day == time_of_day,
                )
            )
            .options(
                selectinload(HalfDayAssignment.person),
                selectinload(HalfDayAssignment.activity),
            )
        )
        result = await self.session.execute(stmt)
        assignments = result.scalars().all()

        # Calculate demand
        demand = 0.0
        for a in assignments:
            if not a.person or a.person.type != "resident":
                continue

            if not assignment_requires_fmc_supervision(a):
                continue

                # Base clinic supervision demand by PGY
            pgy = a.person.pgy_level or 1
            if pgy == 1:
                demand += 0.5
            else:
                demand += 0.25

                # PROC = +1.0 AT
            if activity_is_proc_or_vas(a.activity):
                demand += 1.0

                # Calculate coverage (faculty providing supervision)
        coverage = 0.0
        for a in assignments:
            if not a.person or a.person.type != "faculty":
                continue
            if a.activity and a.activity.is_supervision:
                coverage += 1.0

                # Round up demand (can't have half a faculty)
        import math

        demand_rounded = math.ceil(demand)

        return {
            "date": date_val,
            "time_of_day": time_of_day,
            "at_demand": demand,
            "at_demand_rounded": demand_rounded,
            "at_coverage": coverage,
            "is_sufficient": coverage >= demand_rounded,
            "gap": max(0, demand_rounded - coverage),
        }

    async def to_schedule_dict(
        self,
        assignments: list[HalfDayAssignment],
    ) -> dict[UUID, dict[date, dict[str, str]]]:
        """
        Convert assignments to a nested dict format.

        Returns:
            Dict mapping person_id -> date -> time_of_day -> activity_code
        """
        schedule: dict[UUID, dict[date, dict[str, str]]] = {}

        for a in assignments:
            if a.person_id not in schedule:
                schedule[a.person_id] = {}
            if a.date not in schedule[a.person_id]:
                schedule[a.person_id][a.date] = {"AM": "", "PM": ""}

            code = a.activity.code if a.activity else ""
            schedule[a.person_id][a.date][a.time_of_day] = code

        return schedule


async def get_block_schedule(
    session: AsyncSession,
    block_number: int,
    academic_year: int,
    person_type: str | None = None,
    include_overrides: bool = True,
) -> list[HalfDayAssignment]:
    """
    Convenience function to get block schedule.

    Args:
        session: Database session
        block_number: Block number (1-13)
        academic_year: Academic year
        person_type: Optional filter

    Returns:
        List of HalfDayAssignment objects
    """
    service = HalfDayScheduleService(session)
    return await service.get_schedule_by_block(
        block_number,
        academic_year,
        person_type,
        include_overrides,
    )
