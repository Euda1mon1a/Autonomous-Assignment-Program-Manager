"""Institutional events API routes."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import get_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.institutional_event import (
    InstitutionalEventCreate,
    InstitutionalEventListResponse,
    InstitutionalEventResponse,
    InstitutionalEventUpdate,
)
from app.services.institutional_event_service import InstitutionalEventService

router = APIRouter()


@router.get("", response_model=InstitutionalEventListResponse)
async def list_institutional_events(
    start_date: date | None = Query(
        None, description="Filter events overlapping start"
    ),
    end_date: date | None = Query(None, description="Filter events overlapping end"),
    event_type: str | None = Query(None, description="Filter by event type"),
    applies_to: str | None = Query(None, description="Filter by scope"),
    is_active: bool | None = Query(True, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(100, ge=1, le=500, description="Items per page"),
    db=Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    service = InstitutionalEventService(db)
    return service.list_events(
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        applies_to=applies_to,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )


@router.get("/{event_id}", response_model=InstitutionalEventResponse)
async def get_institutional_event(
    event_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    service = InstitutionalEventService(db)
    event = service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Institutional event not found")
    return event


@router.post("", response_model=InstitutionalEventResponse, status_code=201)
async def create_institutional_event(
    event_in: InstitutionalEventCreate,
    db=Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    service = InstitutionalEventService(db)
    return service.create_event(event_in)


@router.put("/{event_id}", response_model=InstitutionalEventResponse)
async def update_institutional_event(
    event_id: UUID,
    event_in: InstitutionalEventUpdate,
    db=Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    service = InstitutionalEventService(db)
    event = service.update_event(event_id, event_in)
    if not event:
        raise HTTPException(status_code=404, detail="Institutional event not found")
    return event


@router.delete("/{event_id}", status_code=204)
async def delete_institutional_event(
    event_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    service = InstitutionalEventService(db)
    ok = service.delete_event(event_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Institutional event not found")
