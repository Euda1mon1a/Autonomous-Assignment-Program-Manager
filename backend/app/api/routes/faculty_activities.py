"""Faculty activity API routes for weekly templates and overrides.

Provides endpoints for:
- Faculty weekly template CRUD (default patterns)
- Faculty weekly override CRUD (week-specific exceptions)
- Effective week view (merged template + overrides)
- Permitted activities by role
- Faculty matrix view (all faculty scheduling)
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.person import FacultyRole, Person
from app.models.user import User
from app.schemas.activity import ActivityResponse
from app.schemas.faculty_activity import (
    EffectiveSlot,
    EffectiveWeekResponse,
    FacultyMatrixResponse,
    FacultyMatrixRow,
    FacultyOverrideCreate,
    FacultyOverrideResponse,
    FacultyOverridesListResponse,
    FacultyTemplateResponse,
    FacultyTemplateSlotCreate,
    FacultyTemplateSlotResponse,
    FacultyTemplateUpdateRequest,
    FacultyWeekSlots,
    PermittedActivitiesResponse,
)
from app.services.faculty_activity_service import FacultyActivityService

router = APIRouter()


# =============================================================================
# Helper Functions
# =============================================================================


async def get_faculty_or_404(
    db: AsyncSession, person_id: UUID
) -> Person:
    """Get a faculty member by ID or raise 404."""
    from sqlalchemy import select

    result = await db.execute(
        select(Person).where(
            Person.id == person_id,
            Person.type == "faculty",
        )
    )
    person = result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=404, detail="Faculty member not found")
    return person


# =============================================================================
# Template Endpoints
# =============================================================================


@router.get(
    "/faculty/{person_id}/weekly-template",
    response_model=FacultyTemplateResponse,
)
async def get_faculty_template(
    person_id: UUID,
    week_number: int | None = Query(
        None, ge=1, le=4, description="Filter by week 1-4, or null for all"
    ),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get weekly template for a faculty member.

    Returns the default weekly pattern (7x2 grid) for this faculty member.
    Use week_number to filter to specific week patterns.
    """
    person = await get_faculty_or_404(db, person_id)
    service = FacultyActivityService(db)

    templates = await service.get_template(person_id, week_number)

    return FacultyTemplateResponse(
        person_id=person_id,
        person_name=person.name,
        faculty_role=person.faculty_role,
        slots=[
            FacultyTemplateSlotResponse(
                id=t.id,
                person_id=t.person_id,
                day_of_week=t.day_of_week,
                time_of_day=t.time_of_day,
                week_number=t.week_number,
                activity_id=t.activity_id,
                activity=ActivityResponse.model_validate(t.activity) if t.activity else None,
                is_locked=t.is_locked,
                priority=t.priority,
                notes=t.notes,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in templates
        ],
        total_slots=len(templates),
    )


@router.put(
    "/faculty/{person_id}/weekly-template",
    response_model=FacultyTemplateResponse,
)
async def update_faculty_template(
    person_id: UUID,
    request: FacultyTemplateUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update weekly template for a faculty member (bulk).

    Replaces or updates template slots. Use clear_existing=true to
    delete all existing slots before applying new ones.
    """
    person = await get_faculty_or_404(db, person_id)
    service = FacultyActivityService(db)

    # Convert Pydantic models to dicts
    slots_data = [
        {
            "day_of_week": s.day_of_week,
            "time_of_day": s.time_of_day,
            "week_number": s.week_number,
            "activity_id": s.activity_id,
            "is_locked": s.is_locked,
            "priority": s.priority,
            "notes": s.notes,
        }
        for s in request.slots
    ]

    templates = await service.update_template_bulk(
        person_id, slots_data, clear_existing=request.clear_existing
    )

    await db.commit()

    # Re-fetch to get relationships loaded
    templates = await service.get_template(person_id)

    return FacultyTemplateResponse(
        person_id=person_id,
        person_name=person.name,
        faculty_role=person.faculty_role,
        slots=[
            FacultyTemplateSlotResponse(
                id=t.id,
                person_id=t.person_id,
                day_of_week=t.day_of_week,
                time_of_day=t.time_of_day,
                week_number=t.week_number,
                activity_id=t.activity_id,
                activity=ActivityResponse.model_validate(t.activity) if t.activity else None,
                is_locked=t.is_locked,
                priority=t.priority,
                notes=t.notes,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in templates
        ],
        total_slots=len(templates),
    )


@router.post(
    "/faculty/{person_id}/weekly-template/slots",
    response_model=FacultyTemplateSlotResponse,
    status_code=201,
)
async def create_template_slot(
    person_id: UUID,
    slot: FacultyTemplateSlotCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create or update a single template slot."""
    await get_faculty_or_404(db, person_id)
    service = FacultyActivityService(db)

    template = await service.upsert_template_slot(
        person_id=person_id,
        day_of_week=slot.day_of_week,
        time_of_day=slot.time_of_day,
        week_number=slot.week_number,
        activity_id=slot.activity_id,
        is_locked=slot.is_locked,
        priority=slot.priority,
        notes=slot.notes,
    )

    await db.commit()
    await db.refresh(template, ["activity"])  # Eagerly load activity relationship

    return FacultyTemplateSlotResponse(
        id=template.id,
        person_id=template.person_id,
        day_of_week=template.day_of_week,
        time_of_day=template.time_of_day,
        week_number=template.week_number,
        activity_id=template.activity_id,
        activity=ActivityResponse.model_validate(template.activity) if template.activity else None,
        is_locked=template.is_locked,
        priority=template.priority,
        notes=template.notes,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.delete(
    "/faculty/{person_id}/weekly-template/slots",
    status_code=204,
)
async def delete_template_slot(
    person_id: UUID,
    day_of_week: int = Query(..., ge=0, le=6),
    time_of_day: str = Query(..., regex="^(AM|PM)$"),
    week_number: int | None = Query(None, ge=1, le=4),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a specific template slot."""
    await get_faculty_or_404(db, person_id)
    service = FacultyActivityService(db)

    deleted = await service.delete_template_slot(
        person_id, day_of_week, time_of_day, week_number
    )

    if not deleted:
        raise HTTPException(status_code=404, detail="Template slot not found")

    await db.commit()


# =============================================================================
# Override Endpoints
# =============================================================================


@router.get(
    "/faculty/{person_id}/weekly-overrides",
    response_model=FacultyOverridesListResponse,
)
async def get_faculty_overrides(
    person_id: UUID,
    week_start: date = Query(..., description="Monday of the week (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get overrides for a faculty member for a specific week."""
    await get_faculty_or_404(db, person_id)
    service = FacultyActivityService(db)

    overrides = await service.get_overrides(person_id, week_start)

    return FacultyOverridesListResponse(
        person_id=person_id,
        week_start=week_start,
        overrides=[
            FacultyOverrideResponse(
                id=o.id,
                person_id=o.person_id,
                effective_date=o.effective_date,
                day_of_week=o.day_of_week,
                time_of_day=o.time_of_day,
                activity_id=o.activity_id,
                activity=ActivityResponse.model_validate(o.activity) if o.activity else None,
                is_locked=o.is_locked,
                override_reason=o.override_reason,
                created_by=o.created_by,
                created_at=o.created_at,
            )
            for o in overrides
        ],
        total=len(overrides),
    )


@router.post(
    "/faculty/{person_id}/weekly-overrides",
    response_model=FacultyOverrideResponse,
    status_code=201,
)
async def create_faculty_override(
    person_id: UUID,
    override: FacultyOverrideCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create or replace an override for a specific slot and week."""
    await get_faculty_or_404(db, person_id)
    service = FacultyActivityService(db)

    # Get creator ID (if current user is also a Person)
    created_by = None
    if hasattr(current_user, "person_id"):
        created_by = current_user.person_id

    result = await service.create_override(
        person_id=person_id,
        week_start=override.effective_date,
        day_of_week=override.day_of_week,
        time_of_day=override.time_of_day,
        activity_id=override.activity_id,
        is_locked=override.is_locked,
        override_reason=override.override_reason,
        created_by=created_by,
    )

    await db.commit()
    await db.refresh(result, ["activity"])  # Eagerly load activity relationship

    return FacultyOverrideResponse(
        id=result.id,
        person_id=result.person_id,
        effective_date=result.effective_date,
        day_of_week=result.day_of_week,
        time_of_day=result.time_of_day,
        activity_id=result.activity_id,
        activity=ActivityResponse.model_validate(result.activity) if result.activity else None,
        is_locked=result.is_locked,
        override_reason=result.override_reason,
        created_by=result.created_by,
        created_at=result.created_at,
    )


@router.delete(
    "/faculty/{person_id}/weekly-overrides/{override_id}",
    status_code=204,
)
async def delete_faculty_override(
    person_id: UUID,
    override_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete an override by ID."""
    await get_faculty_or_404(db, person_id)
    service = FacultyActivityService(db)

    deleted = await service.delete_override(override_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Override not found")

    await db.commit()


# =============================================================================
# Effective Week Endpoint
# =============================================================================


@router.get(
    "/faculty/{person_id}/weekly-template/effective",
    response_model=EffectiveWeekResponse,
)
async def get_effective_week(
    person_id: UUID,
    week_start: date = Query(..., description="Monday of the week (YYYY-MM-DD)"),
    week_number: int = Query(
        1, ge=1, le=4, description="Week number within block (1-4)"
    ),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get effective schedule for a faculty member for a specific week.

    Merges template slots with overrides. Overrides take precedence.
    """
    person = await get_faculty_or_404(db, person_id)
    service = FacultyActivityService(db)

    effective = await service.get_effective_week(person_id, week_start, week_number)

    return EffectiveWeekResponse(
        person_id=person_id,
        person_name=person.name,
        faculty_role=person.faculty_role,
        week_start=week_start,
        week_number=week_number,
        slots=[
            EffectiveSlot(
                day_of_week=s["day_of_week"],
                time_of_day=s["time_of_day"],
                activity_id=s["activity_id"],
                activity=ActivityResponse.model_validate(s["activity"]) if s["activity"] else None,
                is_locked=s["is_locked"],
                priority=s["priority"],
                source=s["source"],
                notes=s["notes"],
            )
            for s in effective
        ],
    )


# =============================================================================
# Permission Endpoint
# =============================================================================


@router.get(
    "/faculty/activities/permitted",
    response_model=PermittedActivitiesResponse,
)
async def get_permitted_activities(
    role: str = Query(..., description="Faculty role (pd, apd, oic, dept_chief, sports_med, core, adjunct)"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get activities permitted for a faculty role.

    Returns all activities this role can use, plus which ones are defaults.
    """
    # Validate role
    valid_roles = [r.value for r in FacultyRole]
    if role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid faculty role. Must be one of: {valid_roles}",
        )

    service = FacultyActivityService(db)

    activities = await service.get_permitted_activities(role)
    defaults = await service.get_default_activities(role)

    return PermittedActivitiesResponse(
        faculty_role=role,
        activities=[ActivityResponse.model_validate(a) for a in activities],
        default_activities=[ActivityResponse.model_validate(a) for a in defaults],
    )


# =============================================================================
# Matrix View Endpoint
# =============================================================================


@router.get(
    "/faculty/activities/matrix",
    response_model=FacultyMatrixResponse,
)
async def get_faculty_matrix(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    include_adjunct: bool = Query(False, description="Include adjunct faculty"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get activity matrix for all faculty within a date range.

    Returns a matrix view showing all faculty and their effective schedules
    for each week in the date range.
    """
    if end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail="end_date must be >= start_date",
        )

    service = FacultyActivityService(db)

    matrix = await service.get_faculty_matrix(start_date, end_date, include_adjunct)

    return FacultyMatrixResponse(
        start_date=start_date,
        end_date=end_date,
        faculty=[
            FacultyMatrixRow(
                person_id=f["person_id"],
                name=f["name"],
                faculty_role=f["faculty_role"],
                weeks=[
                    FacultyWeekSlots(
                        week_start=w["week_start"],
                        slots=[
                            EffectiveSlot(
                                day_of_week=s["day_of_week"],
                                time_of_day=s["time_of_day"],
                                activity_id=s["activity_id"],
                                activity=ActivityResponse.model_validate(s["activity"]) if s["activity"] else None,
                                is_locked=s["is_locked"],
                                priority=s["priority"],
                                source=s["source"],
                                notes=s["notes"],
                            )
                            for s in w["slots"]
                        ],
                    )
                    for w in f["weeks"]
                ],
            )
            for f in matrix
        ],
        total_faculty=len(matrix),
    )
