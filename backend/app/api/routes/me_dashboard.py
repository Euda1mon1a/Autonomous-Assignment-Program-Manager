"""Personal dashboard API route for logged-in users.

This endpoint provides a unified view of a user's schedule, swaps, and absences.
"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.swap import SwapRecord, SwapStatus
from app.models.user import User
from app.schemas.me_dashboard import (
    DashboardAbsenceItem,
    DashboardScheduleItem,
    DashboardSummary,
    DashboardSwapItem,
    DashboardUserInfo,
    MeDashboardResponse,
)
from app.services.calendar_service import CalendarService

router = APIRouter()


def _get_base_url(request: Request) -> str:
    """Get the base URL for subscription URLs from the request."""
    # Use X-Forwarded-Proto and X-Forwarded-Host if behind a proxy
    proto = request.headers.get("X-Forwarded-Proto", request.url.scheme)
    host = request.headers.get("X-Forwarded-Host", request.url.netloc)
    return f"{proto}://{host}/api/calendar"


async def _get_person_for_user(db: Session, current_user: User) -> Person | None:
    """
    Get the Person associated with the current User.

    Currently matches by email. In future, User model could have a person_id field.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        Person object if found, None otherwise
    """
    # Try to find person by matching email
    person = (
        db.execute(select(Person).where(Person.email == current_user.email))
    ).scalar_one_or_none()
    return person


@router.get("/dashboard", response_model=MeDashboardResponse)
async def get_my_dashboard(
    request: Request,
    days_ahead: int = Query(
        30, ge=1, le=365, description="Number of days to look ahead"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MeDashboardResponse:
    """
    Get personal dashboard for the logged-in user.

    Returns:
    - User information
    - Upcoming schedule assignments
    - Pending swap requests
    - Absences
    - Calendar sync URL
    - Summary statistics

    Args:
        request: HTTP request (for URL generation)
        days_ahead: Number of days to look ahead (default: 30, max: 365)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Complete dashboard response with schedule and activity data
    """
    # Get the person associated with this user
    person = await _get_person_for_user(db, current_user)

    if not person:
        raise HTTPException(
            status_code=404,
            detail="No person profile found for current user. Please contact your administrator to link your account to a person record.",
        )

    # Calculate date range
    today = date.today()
    end_date = today + timedelta(days=days_ahead)
    four_weeks_date = today + timedelta(weeks=4)

    # --- Get upcoming schedule ---
    assignments = (
        db.query(Assignment)
        .options(
            joinedload(Assignment.block),
            joinedload(Assignment.rotation_template),
        )
        .join(Block)
        .filter(
            Assignment.person_id == person.id,
            Block.date >= today,
            Block.date <= end_date,
        )
        .order_by(Block.date, Block.time_of_day)
        .all()
    )

    upcoming_schedule = []
    for assignment in assignments:
        # Determine location
        location = None
        if (
            assignment.rotation_template
            and assignment.rotation_template.clinic_location
        ):
            location = assignment.rotation_template.clinic_location

        # Determine if can trade (primary role assignments can typically be traded)
        can_trade = assignment.role == "primary"

        upcoming_schedule.append(
            DashboardScheduleItem(
                date=assignment.block.date,
                time_of_day=assignment.block.time_of_day,
                activity=assignment.activity_name,
                location=location,
                can_trade=can_trade,
                role=assignment.role,
                assignment_id=assignment.id,
            )
        )

    # --- Get pending swaps ---
    # Get swaps where this person is either source or target and status is pending
    pending_swaps_query = (
        db.query(SwapRecord)
        .options(
            joinedload(SwapRecord.source_faculty),
            joinedload(SwapRecord.target_faculty),
        )
        .filter(
            (
                (SwapRecord.source_faculty_id == person.id)
                | (SwapRecord.target_faculty_id == person.id)
            ),
            SwapRecord.status == SwapStatus.PENDING,
        )
        .order_by(SwapRecord.requested_at.desc())
        .all()
    )

    pending_swaps = []
    for swap in pending_swaps_query:
        # Determine the "other party" (not the current user)
        if swap.source_faculty_id == person.id:
            other_party_name = (
                swap.target_faculty.name if swap.target_faculty else "Unknown"
            )
        else:
            other_party_name = (
                swap.source_faculty.name if swap.source_faculty else "Unknown"
            )

        pending_swaps.append(
            DashboardSwapItem(
                swap_id=swap.id,
                swap_type=swap.swap_type.value,
                status=swap.status.value,
                source_week=swap.source_week,
                target_week=swap.target_week,
                other_party_name=other_party_name,
                requested_at=swap.requested_at,
            )
        )

    # --- Get absences ---
    absences_query = (
        db.query(Absence)
        .filter(
            Absence.person_id == person.id,
            Absence.end_date >= today,  # Only show current and future absences
        )
        .order_by(Absence.start_date)
        .all()
    )

    absences = []
    for absence in absences_query:
        absences.append(
            DashboardAbsenceItem(
                absence_id=absence.id,
                start_date=absence.start_date,
                end_date=absence.end_date,
                absence_type=absence.absence_type,
                notes=absence.notes,
            )
        )

    # --- Generate calendar sync URL ---
    # Try to get or create a subscription for this person
    calendar_sync_url = None
    try:
        # Check if there's already an active subscription
        existing_subscriptions = CalendarService.list_subscriptions(
            db=db,
            person_id=person.id,
            created_by_user_id=current_user.id,
            active_only=True,
        )

        if existing_subscriptions:
            # Use the first active subscription
            subscription = existing_subscriptions[0]
        else:
            # Create a new subscription
            subscription = CalendarService.create_subscription(
                db=db,
                person_id=person.id,
                created_by_user_id=current_user.id,
                label="My Dashboard Calendar",
                expires_days=365,  # 1 year expiration
            )

        base_url = _get_base_url(request)
        calendar_sync_url = CalendarService.generate_subscription_url(
            subscription.token, base_url
        )
    except Exception:
        # If calendar sync fails, continue without it
        calendar_sync_url = None

    # --- Calculate summary statistics ---
    # Next assignment date
    next_assignment = upcoming_schedule[0].date if upcoming_schedule else None

    # Workload in next 4 weeks (count blocks)
    workload_next_4_weeks = sum(
        1 for item in upcoming_schedule if item.date <= four_weeks_date
    )

    pending_swap_count = len(pending_swaps)
    upcoming_absences_count = len(absences)

    summary = DashboardSummary(
        next_assignment=next_assignment,
        workload_next_4_weeks=workload_next_4_weeks,
        pending_swap_count=pending_swap_count,
        upcoming_absences_count=upcoming_absences_count,
    )

    # --- Build user info ---
    user_info = DashboardUserInfo(
        id=person.id,
        name=person.name,
        role=person.type,
        email=person.email,
        pgy_level=person.pgy_level,
    )

    return MeDashboardResponse(
        user=user_info,
        upcoming_schedule=upcoming_schedule,
        pending_swaps=pending_swaps,
        absences=absences,
        calendar_sync_url=calendar_sync_url,
        summary=summary,
    )
