"""Service for call overrides (post-release call coverage layer)."""

from datetime import date, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.call_assignment import CallAssignment
from app.models.call_override import CallOverride
from app.models.person import Person
from app.schemas.call_override import CallOverrideCreate
from app.utils.academic_blocks import get_block_dates

logger = get_logger(__name__)


class CallOverrideService:
    """Create and manage call overrides for released schedules."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_overrides(
        self,
        block_number: int | None = None,
        academic_year: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        active_only: bool = True,
    ) -> list[CallOverride]:
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
            select(CallOverride)
            .where(
                and_(
                    CallOverride.effective_date >= start_date,
                    CallOverride.effective_date <= end_date,
                )
            )
            .order_by(CallOverride.effective_date)
        )
        if active_only:
            stmt = stmt.where(CallOverride.is_active.is_(True))

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_override(
        self,
        request: CallOverrideCreate,
        created_by_id: UUID | None,
    ) -> CallOverride:
        assignment = await self._get_assignment_or_404(request.call_assignment_id)

        existing = await self._get_active_override_for_assignment(assignment.id)
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Active override already exists for this call assignment",
            )

        await self._validate_replacement_person(
            assignment, request.replacement_person_id
        )

        override = CallOverride(
            call_assignment_id=assignment.id,
            original_person_id=assignment.person_id,
            replacement_person_id=request.replacement_person_id,
            override_type=request.override_type,
            reason=request.reason,
            notes=request.notes,
            effective_date=assignment.date,
            call_type=assignment.call_type,
            created_by_id=created_by_id,
            supersedes_override_id=request.supersedes_override_id,
        )
        self.session.add(override)
        await self.session.flush()
        await self.session.refresh(override)

        logger.info(
            "Created call override %s for call assignment %s",
            override.id,
            assignment.id,
        )

        return override

    async def deactivate_override(
        self,
        override_id: UUID,
        deactivated_by_id: UUID | None,
    ) -> CallOverride:
        override = await self.session.get(CallOverride, override_id)
        if not override:
            raise HTTPException(status_code=404, detail="Override not found")
        if not override.is_active:
            return override

        override.is_active = False
        override.deactivated_at = datetime.utcnow()
        override.deactivated_by_id = deactivated_by_id
        await self.session.flush()
        await self.session.refresh(override)

        logger.info("Deactivated call override %s", override.id)

        return override

    async def apply_overrides(
        self,
        call_assignments: list[CallAssignment],
        include_overrides: bool = True,
    ) -> list[CallAssignment]:
        if not include_overrides or not call_assignments:
            return call_assignments

        assignment_ids = [ca.id for ca in call_assignments]
        result = await self.session.execute(
            select(CallOverride).where(
                CallOverride.call_assignment_id.in_(assignment_ids),
                CallOverride.is_active.is_(True),
            )
        )
        overrides = list(result.scalars().all())
        if not overrides:
            return call_assignments

        override_map = {o.call_assignment_id: o for o in overrides}
        replacement_ids = {
            o.replacement_person_id
            for o in overrides
            if o.replacement_person_id is not None
        }
        replacements = {}
        if replacement_ids:
            replacement_result = await self.session.execute(
                select(Person).where(Person.id.in_(replacement_ids))
            )
            replacements = {
                person.id: person for person in replacement_result.scalars().all()
            }

        output: list[CallAssignment] = []
        for assignment in call_assignments:
            override = override_map.get(assignment.id)
            if not override:
                output.append(assignment)
                continue

            replacement = replacements.get(override.replacement_person_id)
            if not replacement:
                # If replacement missing, fall back to original assignment
                output.append(assignment)
                continue

            clone = CallAssignment(
                id=assignment.id,
                date=assignment.date,
                person_id=replacement.id,
                call_type=assignment.call_type,
                is_weekend=assignment.is_weekend,
                is_holiday=assignment.is_holiday,
                created_at=assignment.created_at,
            )
            clone.person = replacement
            output.append(clone)

        return output

    async def _get_assignment_or_404(self, assignment_id: UUID) -> CallAssignment:
        assignment = await self.session.get(
            CallAssignment,
            assignment_id,
            options=[selectinload(CallAssignment.person)],
        )
        if not assignment:
            raise HTTPException(status_code=404, detail="Call assignment not found")
        return assignment

    async def _get_active_override_for_assignment(
        self, assignment_id: UUID
    ) -> CallOverride | None:
        result = await self.session.execute(
            select(CallOverride).where(
                CallOverride.call_assignment_id == assignment_id,
                CallOverride.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def _validate_replacement_person(
        self,
        assignment: CallAssignment,
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

        original_person = assignment.person
        # NOTE: Call overrides currently require same person type (faculty-only).
        # Extend for resident call coverage when resident call workflows exist.
        if original_person and replacement.type != original_person.type:
            raise HTTPException(
                status_code=400,
                detail="Replacement person must match call assignment person type",
            )

        if replacement.is_faculty and replacement.faculty_role == "adjunct":
            raise HTTPException(
                status_code=400,
                detail="Adjunct faculty cannot cover call",
            )

        conflict = await self.session.execute(
            select(CallAssignment.id).where(
                CallAssignment.person_id == replacement_person_id,
                CallAssignment.date == assignment.date,
            )
        )
        if conflict.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail="Replacement person already assigned to call on this date",
            )

        override_conflict = await self.session.execute(
            select(CallOverride.id).where(
                CallOverride.replacement_person_id == replacement_person_id,
                CallOverride.effective_date == assignment.date,
                CallOverride.is_active.is_(True),
            )
        )
        if override_conflict.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail="Replacement person already covering another call override on this date",
            )


def get_call_override_service(session: AsyncSession) -> CallOverrideService:
    """Dependency helper for call override service."""

    return CallOverrideService(session)
