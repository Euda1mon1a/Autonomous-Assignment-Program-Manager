"""
API routes for faculty self-service portal.

Provides endpoints for:
- My schedule view
- Swap requests
- Preferences management
- Dashboard
- Swap marketplace
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.person import Person
from app.schemas.portal import (
    MyScheduleResponse,
    FMITWeekInfo,
    MySwapsResponse,
    SwapRequestSummary,
    SwapRequestCreate,
    SwapRequestResponse,
    SwapRespondRequest,
    PreferencesUpdate,
    PreferencesResponse,
    DashboardResponse,
    DashboardStats,
    DashboardAlert,
    MarketplaceResponse,
    MarketplaceEntry,
)

router = APIRouter(prefix="/portal", tags=["portal"])


@router.get("/my/schedule", response_model=MyScheduleResponse)
def get_my_schedule(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the current user's FMIT schedule.

    Shows assigned FMIT weeks with conflict indicators.
    """
    # Get faculty profile linked to current user
    faculty = _get_faculty_for_user(db, current_user)

    # TODO: Query actual FMIT weeks from schedule
    fmit_weeks = []

    return MyScheduleResponse(
        faculty_id=faculty.id,
        faculty_name=faculty.name,
        fmit_weeks=fmit_weeks,
        total_weeks_assigned=len(fmit_weeks),
        target_weeks=6,  # Default target
        weeks_remaining=6 - len(fmit_weeks),
    )


@router.get("/my/swaps", response_model=MySwapsResponse)
def get_my_swaps(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get swap requests related to the current user.

    Returns incoming requests, outgoing requests, and recent completed swaps.
    """
    faculty = _get_faculty_for_user(db, current_user)

    # TODO: Query SwapRecord for this faculty
    return MySwapsResponse(
        incoming_requests=[],
        outgoing_requests=[],
        recent_swaps=[],
    )


@router.post("/my/swaps", response_model=SwapRequestResponse)
def create_swap_request(
    request: SwapRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new swap request to offload an FMIT week.

    Can specify a preferred target or let the system find candidates.
    """
    faculty = _get_faculty_for_user(db, current_user)

    # TODO: Implement swap request creation
    # 1. Verify week is assigned to this faculty
    # 2. Create SwapRecord with PENDING status
    # 3. If auto_find_candidates, find and notify potential swap partners

    return SwapRequestResponse(
        success=False,
        request_id=None,
        message="Swap request creation not yet implemented",
        candidates_notified=0,
    )


@router.post("/my/swaps/{swap_id}/respond")
def respond_to_swap(
    swap_id: UUID,
    request: SwapRespondRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Respond to an incoming swap request.

    Can accept, reject, or counter-offer with a different week.
    """
    faculty = _get_faculty_for_user(db, current_user)

    # TODO: Implement swap response
    return {
        "success": False,
        "message": "Swap response not yet implemented",
    }


@router.get("/my/preferences", response_model=PreferencesResponse)
def get_my_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current user's FMIT scheduling preferences."""
    faculty = _get_faculty_for_user(db, current_user)

    # TODO: Query FacultyPreference for this faculty
    # Return defaults if no preferences exist
    return PreferencesResponse(
        faculty_id=faculty.id,
        preferred_weeks=[],
        blocked_weeks=[],
        max_weeks_per_month=2,
        max_consecutive_weeks=1,
        min_gap_between_weeks=2,
        target_weeks_per_year=6,
        notify_swap_requests=True,
        notify_schedule_changes=True,
        notify_conflict_alerts=True,
        notify_reminder_days=7,
        notes=None,
        updated_at=datetime.utcnow(),
    )


@router.put("/my/preferences", response_model=PreferencesResponse)
def update_my_preferences(
    request: PreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the current user's FMIT scheduling preferences."""
    faculty = _get_faculty_for_user(db, current_user)

    # TODO: Update FacultyPreference
    return PreferencesResponse(
        faculty_id=faculty.id,
        preferred_weeks=request.preferred_weeks or [],
        blocked_weeks=request.blocked_weeks or [],
        max_weeks_per_month=request.max_weeks_per_month or 2,
        max_consecutive_weeks=request.max_consecutive_weeks or 1,
        min_gap_between_weeks=request.min_gap_between_weeks or 2,
        target_weeks_per_year=6,
        notify_swap_requests=request.notify_swap_requests if request.notify_swap_requests is not None else True,
        notify_schedule_changes=request.notify_schedule_changes if request.notify_schedule_changes is not None else True,
        notify_conflict_alerts=request.notify_conflict_alerts if request.notify_conflict_alerts is not None else True,
        notify_reminder_days=request.notify_reminder_days or 7,
        notes=request.notes,
        updated_at=datetime.utcnow(),
    )


@router.get("/my/dashboard", response_model=DashboardResponse)
def get_my_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the dashboard view for the current user.

    Includes stats, upcoming weeks, alerts, and pending actions.
    """
    faculty = _get_faculty_for_user(db, current_user)

    stats = DashboardStats(
        weeks_assigned=0,
        weeks_completed=0,
        weeks_remaining=0,
        target_weeks=6,
        pending_swap_requests=0,
        unread_alerts=0,
    )

    return DashboardResponse(
        faculty_id=faculty.id,
        faculty_name=faculty.name,
        stats=stats,
        upcoming_weeks=[],
        recent_alerts=[],
        pending_swap_decisions=[],
    )


@router.get("/marketplace", response_model=MarketplaceResponse)
def get_swap_marketplace(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get available swap opportunities in the marketplace.

    Shows open swap requests from other faculty.
    """
    faculty = _get_faculty_for_user(db, current_user)

    # TODO: Query open swap requests
    return MarketplaceResponse(
        entries=[],
        total=0,
        my_postings=0,
    )


def _get_faculty_for_user(db: Session, user: User) -> Person:
    """Get the faculty profile linked to a user."""
    # First try to find by email match
    faculty = db.query(Person).filter(
        Person.email == user.email,
        Person.type == "faculty",
    ).first()

    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No faculty profile linked to this user account",
        )

    return faculty
