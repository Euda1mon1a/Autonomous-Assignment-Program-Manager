"""Faculty schedule preferences API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import get_admin_user
from app.db.session import get_db
from app.models.faculty_schedule_preference import FacultyPreferenceType
from app.models.user import User
from app.schemas.faculty_schedule_preference import (
    FacultySchedulePreferenceCreate,
    FacultySchedulePreferenceListResponse,
    FacultySchedulePreferenceResponse,
    FacultySchedulePreferenceUpdate,
)
from app.services.faculty_schedule_preference_service import (
    FacultySchedulePreferenceService,
)

router = APIRouter()


@router.get("", response_model=FacultySchedulePreferenceListResponse)
async def list_faculty_schedule_preferences(
    person_id: UUID | None = Query(None, description="Filter by faculty person_id"),
    preference_type: FacultyPreferenceType | None = Query(
        None, description="Filter by preference type"
    ),
    is_active: bool | None = Query(True, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(100, ge=1, le=500, description="Items per page"),
    db=Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    service = FacultySchedulePreferenceService(db)
    return service.list_preferences(
        person_id=person_id,
        preference_type=preference_type,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )


@router.get("/{preference_id}", response_model=FacultySchedulePreferenceResponse)
async def get_faculty_schedule_preference(
    preference_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    service = FacultySchedulePreferenceService(db)
    pref = service.get_preference(preference_id)
    if not pref:
        raise HTTPException(status_code=404, detail="Preference not found")
    return pref


@router.post("", response_model=FacultySchedulePreferenceResponse, status_code=201)
async def create_faculty_schedule_preference(
    pref_in: FacultySchedulePreferenceCreate,
    db=Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    service = FacultySchedulePreferenceService(db)
    return service.create_preference(pref_in)


@router.put("/{preference_id}", response_model=FacultySchedulePreferenceResponse)
async def update_faculty_schedule_preference(
    preference_id: UUID,
    pref_in: FacultySchedulePreferenceUpdate,
    db=Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    service = FacultySchedulePreferenceService(db)
    pref = service.update_preference(preference_id, pref_in)
    if not pref:
        raise HTTPException(status_code=404, detail="Preference not found")
    return pref


@router.delete("/{preference_id}", status_code=204)
async def delete_faculty_schedule_preference(
    preference_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_admin_user),
) -> None:
    service = FacultySchedulePreferenceService(db)
    ok = service.delete_preference(preference_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Preference not found")
