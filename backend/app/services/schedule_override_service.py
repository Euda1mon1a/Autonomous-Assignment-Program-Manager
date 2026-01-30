"""Service for schedule overrides (post-release coverage layer)."""

from datetime import date, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.activity import ActivityCategory
from app.models.half_day_assignment import HalfDayAssignment
from app.models.person import Person
from app.models.schedule_override import ScheduleOverride
from app.schemas.schedule_override import ScheduleOverrideCreate
from app.utils.academic_blocks import get_block_dates

logger = get_logger(__name__)

PROTECTED_OVERRIDE_CODES = {"FMIT", "PCAT", "DO"}


class ScheduleOverrideService:
    """Create and manage schedule overrides for released schedules."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_overrides(
        self,
        block_number: int | None = None,
        academic_year: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        active_only: bool = True,
    ) -> list[ScheduleOverride]:
        if block_number is not None and academic_year is not None:
            block_dates = get_block_dates(block_number, academic_year)
            start_date = block_dates.start_date
            end_date = block_dates.end_date
        elif start_date is None or end_date is None:
            raise HTTPException(
                status_code=400,
                detail="Either (block_number + academic_year) or (start_date + end_date) required",
            )

        stmt = (
            select(ScheduleOverride)
            .where(
                and_(
                    ScheduleOverride.effective_date >= start_date,
                    ScheduleOverride.effective_date <= end_date,
                )
            )
            .order_by(ScheduleOverride.effective_date, ScheduleOverride.time_of_day)
        )
        if active_only:
            stmt = stmt.where(ScheduleOverride.is_active.is_(True))

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_override(
        self,
        request: ScheduleOverrideCreate,
        created_by_id: UUID | None,
    ) -> ScheduleOverride:
        assignment = await self._get_assignment_or_404(request.half_day_assignment_id)

        if assignment.activity:
            activity_code = (
                assignment.activity.display_abbreviation
                or assignment.activity.code
                or ""
            ).upper()
            if activity_code in PROTECTED_OVERRIDE_CODES:
                if request.override_type == "cancellation":
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot cancel FMIT or PCAT/DO assignments",
                    )
            if assignment.activity.activity_category == ActivityCategory.TIME_OFF.value:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot override time-off assignments",
                )

        existing = await self._get_active_override_for_assignment(assignment.id)
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Active override already exists for this assignment",
            )

        if request.override_type == "coverage":
            await self._validate_replacement_person(
                assignment, request.replacement_person_id
            )

        override = ScheduleOverride(
            half_day_assignment_id=assignment.id,
            original_person_id=assignment.person_id,
            replacement_person_id=request.replacement_person_id,
            override_type=request.override_type,
            reason=request.reason,
            notes=request.notes,
            effective_date=assignment.date,
            time_of_day=assignment.time_of_day,
            created_by_id=created_by_id,
            supersedes_override_id=request.supersedes_override_id,
        )
        self.session.add(override)
        await self.session.flush()
        await self.session.refresh(override)

        logger.info(
            "Created schedule override %s for assignment %s",
            override.id,
            assignment.id,
        )

        return override

    async def deactivate_override(
        self,
        override_id: UUID,
        deactivated_by_id: UUID | None,
    ) -> ScheduleOverride:
        override = await self.session.get(ScheduleOverride, override_id)
        if not override:
            raise HTTPException(status_code=404, detail="Override not found")
        if not override.is_active:
            return override

        override.is_active = False
        override.deactivated_at = datetime.utcnow()
        override.deactivated_by_id = deactivated_by_id
        await self.session.flush()
        await self.session.refresh(override)

        logger.info("Deactivated schedule override %s", override.id)

        return override

    async def _get_assignment_or_404(self, assignment_id: UUID) -> HalfDayAssignment:
        assignment = await self.session.get(
            HalfDayAssignment,
            assignment_id,
            options=[
                selectinload(HalfDayAssignment.activity),
                selectinload(HalfDayAssignment.person),
            ],
        )
        if not assignment:
            raise HTTPException(status_code=404, detail="Half-day assignment not found")
        return assignment

    async def _get_active_override_for_assignment(
        self, assignment_id: UUID
    ) -> ScheduleOverride | None:
        result = await self.session.execute(
            select(ScheduleOverride).where(
                ScheduleOverride.half_day_assignment_id == assignment_id,
                ScheduleOverride.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def _validate_replacement_person(
        self,
        assignment: HalfDayAssignment,
        replacement_person_id: UUID | None,
    ) -> None:
        if replacement_person_id is None:
            raise HTTPException(
                status_code=400,
                detail="Replacement person is required for coverage overrides",
            )
        if replacement_person_id == assignment.person_id:
            raise HTTPException(
                status_code=400,
                detail="Replacement person must differ from original person",
            )

        replacement = await self.session.get(Person, replacement_person_id)
        if not replacement:
            raise HTTPException(status_code=404, detail="Replacement person not found")

        conflict_result = await self.session.execute(
            select(HalfDayAssignment.id).where(
                HalfDayAssignment.person_id == replacement_person_id,
                HalfDayAssignment.date == assignment.date,
                HalfDayAssignment.time_of_day == assignment.time_of_day,
            )
        )
        conflict_id = conflict_result.scalar_one_or_none()
        if conflict_id:
            cancellation_override = await self.session.execute(
                select(ScheduleOverride.id).where(
                    ScheduleOverride.half_day_assignment_id == conflict_id,
                    ScheduleOverride.override_type.in_(["cancellation", "gap"]),
                    ScheduleOverride.is_active.is_(True),
                )
            )
            if cancellation_override.scalar_one_or_none() is None:
                raise HTTPException(
                    status_code=409,
                    detail="Replacement person already assigned for this slot",
                )

        override_conflict = await self.session.execute(
            select(ScheduleOverride.id).where(
                ScheduleOverride.replacement_person_id == replacement_person_id,
                ScheduleOverride.effective_date == assignment.date,
                ScheduleOverride.time_of_day == assignment.time_of_day,
                ScheduleOverride.is_active.is_(True),
            )
        )
        if override_conflict.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail="Replacement person already covering another override at this time",
            )


def get_schedule_override_service(session: AsyncSession) -> ScheduleOverrideService:
    """Dependency helper for schedule override service."""

    return ScheduleOverrideService(session)
