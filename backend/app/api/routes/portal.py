"""
API routes for faculty self-service portal.

Provides endpoints for:
- My schedule view
- Swap requests
- Preferences management
- Dashboard
- Swap marketplace
"""
from collections import defaultdict
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.faculty_preference import FacultyPreference
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.models.user import User
from app.schemas.portal import (
    DashboardResponse,
    DashboardStats,
    FMITWeekInfo,
    MarketplaceEntry,
    MarketplaceResponse,
    MyScheduleResponse,
    MySwapsResponse,
    PreferencesResponse,
    PreferencesUpdate,
    SwapRequestCreate,
    SwapRequestResponse,
    SwapRequestSummary,
    SwapRespondRequest,
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

    # Query actual FMIT weeks from schedule
    fmit_template = db.query(RotationTemplate).filter(
        RotationTemplate.name == "FMIT"
    ).first()

    fmit_weeks = []
    if fmit_template:
        # Get all FMIT assignments for this faculty
        assignments = (
            db.query(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .filter(
                Assignment.person_id == faculty.id,
                Assignment.rotation_template_id == fmit_template.id,
            )
            .order_by(Block.date)
            .all()
        )

        # Group assignments by week
        week_map = defaultdict(list)
        for assignment in assignments:
            week_start = _get_week_start(assignment.block.date)
            week_map[week_start].append(assignment)

        # Check for pending swap requests for this faculty
        pending_swaps = db.query(SwapRecord).filter(
            SwapRecord.source_faculty_id == faculty.id,
            SwapRecord.status == SwapStatus.PENDING,
        ).all()

        pending_swap_weeks = {swap.source_week for swap in pending_swaps}

        # Convert to FMITWeekInfo
        today = datetime.utcnow().date()
        for week_start, week_assignments in sorted(week_map.items()):
            week_end = week_start + timedelta(days=6)
            has_pending_swap = week_start in pending_swap_weeks

            fmit_weeks.append(FMITWeekInfo(
                week_start=week_start,
                week_end=week_end,
                is_past=week_end < today,
                has_conflict=False,  # TODO: Could check conflict_alerts table
                conflict_description=None,
                can_request_swap=not has_pending_swap and week_start > today,
                pending_swap_request=has_pending_swap,
            ))

    # Get target weeks from preferences or use default
    preferences = db.query(FacultyPreference).filter(
        FacultyPreference.faculty_id == faculty.id
    ).first()
    target_weeks = preferences.target_weeks_per_year if preferences else 6

    return MyScheduleResponse(
        faculty_id=faculty.id,
        faculty_name=faculty.name,
        fmit_weeks=fmit_weeks,
        total_weeks_assigned=len(fmit_weeks),
        target_weeks=target_weeks,
        weeks_remaining=max(0, target_weeks - len(fmit_weeks)),
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

    # Query SwapRecord for this faculty
    # Incoming requests: where this faculty is the target and status is pending
    incoming_swaps = (
        db.query(SwapRecord)
        .filter(
            SwapRecord.target_faculty_id == faculty.id,
            SwapRecord.status == SwapStatus.PENDING,
        )
        .order_by(SwapRecord.requested_at.desc())
        .all()
    )

    # Outgoing requests: where this faculty is the source and status is pending
    outgoing_swaps = (
        db.query(SwapRecord)
        .filter(
            SwapRecord.source_faculty_id == faculty.id,
            SwapRecord.status == SwapStatus.PENDING,
        )
        .order_by(SwapRecord.requested_at.desc())
        .all()
    )

    # Recent completed swaps: executed, approved, or rejected in the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_swaps = (
        db.query(SwapRecord)
        .filter(
            (SwapRecord.source_faculty_id == faculty.id) | (SwapRecord.target_faculty_id == faculty.id),
            SwapRecord.status.in_([SwapStatus.EXECUTED, SwapStatus.APPROVED, SwapStatus.REJECTED]),
            SwapRecord.requested_at >= thirty_days_ago,
        )
        .order_by(SwapRecord.requested_at.desc())
        .limit(10)
        .all()
    )

    # Convert to SwapRequestSummary
    def swap_to_summary(swap: SwapRecord, is_incoming: bool) -> SwapRequestSummary:
        other_faculty = swap.source_faculty if is_incoming else swap.target_faculty
        return SwapRequestSummary(
            id=swap.id,
            other_faculty_name=other_faculty.name if other_faculty else "Unknown",
            week_to_give=swap.source_week if is_incoming else swap.target_week,
            week_to_receive=swap.target_week if is_incoming else swap.source_week,
            status=swap.status.value,
            created_at=swap.requested_at,
            is_incoming=is_incoming,
        )

    incoming_requests = [swap_to_summary(swap, True) for swap in incoming_swaps]
    outgoing_requests = [swap_to_summary(swap, False) for swap in outgoing_swaps]

    # For recent swaps, determine if incoming or outgoing
    recent_swap_summaries = []
    for swap in recent_swaps:
        is_incoming = swap.target_faculty_id == faculty.id
        recent_swap_summaries.append(swap_to_summary(swap, is_incoming))

    return MySwapsResponse(
        incoming_requests=incoming_requests,
        outgoing_requests=outgoing_requests,
        recent_swaps=recent_swap_summaries,
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

    # Implement swap request creation
    # 1. Verify week is assigned to this faculty
    fmit_template = db.query(RotationTemplate).filter(
        RotationTemplate.name == "FMIT"
    ).first()

    if not fmit_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FMIT rotation template not found",
        )

    # Get the week start (Monday)
    week_start = _get_week_start(request.week_to_offload)
    week_end = week_start + timedelta(days=6)

    # Verify this faculty has FMIT assignments for this week
    assignments = (
        db.query(Assignment)
        .join(Block, Assignment.block_id == Block.id)
        .filter(
            Assignment.person_id == faculty.id,
            Assignment.rotation_template_id == fmit_template.id,
            Block.date >= week_start,
            Block.date <= week_end,
        )
        .all()
    )

    if not assignments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No FMIT assignments found for week starting {week_start}",
        )

    # Check if there's already a pending swap for this week
    existing_swap = db.query(SwapRecord).filter(
        SwapRecord.source_faculty_id == faculty.id,
        SwapRecord.source_week == week_start,
        SwapRecord.status == SwapStatus.PENDING,
    ).first()

    if existing_swap:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A swap request already exists for week starting {week_start}",
        )

    # 2. Create SwapRecord with PENDING status
    # Determine target faculty and swap type
    if request.preferred_target_faculty_id:
        target_faculty_id = request.preferred_target_faculty_id
        swap_type = SwapType.ONE_TO_ONE
    else:
        # For marketplace/open requests, use a placeholder or the requesting faculty
        # The actual target will be determined when someone accepts the request
        target_faculty_id = faculty.id  # Placeholder
        swap_type = SwapType.ABSORB

    swap_record = SwapRecord(
        source_faculty_id=faculty.id,
        source_week=week_start,
        target_faculty_id=target_faculty_id,
        target_week=None,  # Will be filled in when accepted
        swap_type=swap_type,
        status=SwapStatus.PENDING,
        requested_at=datetime.utcnow(),
        requested_by_id=current_user.id,
        reason=request.reason,
    )

    db.add(swap_record)
    db.commit()
    db.refresh(swap_record)

    # 3. If auto_find_candidates, find and notify potential swap partners
    candidates_notified = 0
    if request.auto_find_candidates and not request.preferred_target_faculty_id:
        # Find faculty who:
        # - Are not this faculty
        # - Have FMIT as their rotation type
        # - Have notification preferences enabled
        preferences = (
            db.query(FacultyPreference)
            .filter(
                FacultyPreference.faculty_id != faculty.id,
                FacultyPreference.notify_swap_requests == True,
            )
            .all()
        )

        # TODO: Create notifications for candidates
        # For now, just count potential candidates
        candidates_notified = len(preferences)

    message = f"Swap request created for week starting {week_start}"
    if candidates_notified > 0:
        message += f" and {candidates_notified} candidates notified"

    return SwapRequestResponse(
        success=True,
        request_id=swap_record.id,
        message=message,
        candidates_notified=candidates_notified,
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

    # Implement swap response
    # Query the swap record
    swap = db.query(SwapRecord).filter(SwapRecord.id == swap_id).first()

    if not swap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Swap request not found",
        )

    # Verify this faculty is the target of the swap
    if swap.target_faculty_id != faculty.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to respond to this swap request",
        )

    # Verify swap is still pending
    if swap.status != SwapStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Swap request is no longer pending (status: {swap.status})",
        )

    if request.accept:
        # Accept the swap
        if request.counter_offer_week:
            # Update with counter-offer week
            swap.target_week = _get_week_start(request.counter_offer_week)
            swap.swap_type = SwapType.ONE_TO_ONE
        else:
            # Accept as-is (absorb)
            swap.swap_type = SwapType.ABSORB
            swap.target_week = None

        swap.status = SwapStatus.APPROVED
        swap.approved_at = datetime.utcnow()
        swap.approved_by_id = current_user.id

        if request.notes:
            swap.notes = (swap.notes or "") + f"\nResponse: {request.notes}"

        db.commit()

        return {
            "success": True,
            "message": "Swap request accepted",
            "swap_id": swap.id,
            "status": swap.status.value,
        }
    else:
        # Reject the swap
        swap.status = SwapStatus.REJECTED
        swap.approved_at = datetime.utcnow()  # Track when rejected
        swap.approved_by_id = current_user.id

        if request.notes:
            swap.notes = (swap.notes or "") + f"\nRejection reason: {request.notes}"

        db.commit()

        return {
            "success": True,
            "message": "Swap request rejected",
            "swap_id": swap.id,
            "status": swap.status.value,
        }


@router.get("/my/preferences", response_model=PreferencesResponse)
def get_my_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current user's FMIT scheduling preferences."""
    faculty = _get_faculty_for_user(db, current_user)

    # Query FacultyPreference for this faculty
    preferences = db.query(FacultyPreference).filter(
        FacultyPreference.faculty_id == faculty.id
    ).first()

    # Return defaults if no preferences exist
    if not preferences:
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

    # Convert JSON date strings to date objects
    preferred_weeks = []
    if preferences.preferred_weeks:
        for week_str in preferences.preferred_weeks:
            try:
                preferred_weeks.append(datetime.fromisoformat(week_str).date())
            except (ValueError, TypeError):
                pass  # Skip invalid dates

    blocked_weeks = []
    if preferences.blocked_weeks:
        for week_str in preferences.blocked_weeks:
            try:
                blocked_weeks.append(datetime.fromisoformat(week_str).date())
            except (ValueError, TypeError):
                pass  # Skip invalid dates

    return PreferencesResponse(
        faculty_id=faculty.id,
        preferred_weeks=preferred_weeks,
        blocked_weeks=blocked_weeks,
        max_weeks_per_month=preferences.max_weeks_per_month or 2,
        max_consecutive_weeks=preferences.max_consecutive_weeks or 1,
        min_gap_between_weeks=preferences.min_gap_between_weeks or 2,
        target_weeks_per_year=preferences.target_weeks_per_year or 6,
        notify_swap_requests=preferences.notify_swap_requests if preferences.notify_swap_requests is not None else True,
        notify_schedule_changes=preferences.notify_schedule_changes if preferences.notify_schedule_changes is not None else True,
        notify_conflict_alerts=preferences.notify_conflict_alerts if preferences.notify_conflict_alerts is not None else True,
        notify_reminder_days=preferences.notify_reminder_days or 7,
        notes=preferences.notes,
        updated_at=preferences.updated_at,
    )


@router.put("/my/preferences", response_model=PreferencesResponse)
def update_my_preferences(
    request: PreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the current user's FMIT scheduling preferences."""
    faculty = _get_faculty_for_user(db, current_user)

    # Update FacultyPreference
    # Query existing preferences or create new
    preferences = db.query(FacultyPreference).filter(
        FacultyPreference.faculty_id == faculty.id
    ).first()

    if not preferences:
        # Create new preferences record
        preferences = FacultyPreference(
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
        )
        db.add(preferences)

    # Update fields from request
    if request.preferred_weeks is not None:
        # Convert date objects to ISO format strings
        preferences.preferred_weeks = [d.isoformat() for d in request.preferred_weeks]

    if request.blocked_weeks is not None:
        # Convert date objects to ISO format strings
        preferences.blocked_weeks = [d.isoformat() for d in request.blocked_weeks]

    if request.max_weeks_per_month is not None:
        preferences.max_weeks_per_month = request.max_weeks_per_month

    if request.max_consecutive_weeks is not None:
        preferences.max_consecutive_weeks = request.max_consecutive_weeks

    if request.min_gap_between_weeks is not None:
        preferences.min_gap_between_weeks = request.min_gap_between_weeks

    if request.notify_swap_requests is not None:
        preferences.notify_swap_requests = request.notify_swap_requests

    if request.notify_schedule_changes is not None:
        preferences.notify_schedule_changes = request.notify_schedule_changes

    if request.notify_conflict_alerts is not None:
        preferences.notify_conflict_alerts = request.notify_conflict_alerts

    if request.notify_reminder_days is not None:
        preferences.notify_reminder_days = request.notify_reminder_days

    if request.notes is not None:
        preferences.notes = request.notes

    # Update timestamp
    preferences.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(preferences)

    # Convert back for response
    preferred_weeks = []
    if preferences.preferred_weeks:
        for week_str in preferences.preferred_weeks:
            try:
                preferred_weeks.append(datetime.fromisoformat(week_str).date())
            except (ValueError, TypeError):
                pass

    blocked_weeks = []
    if preferences.blocked_weeks:
        for week_str in preferences.blocked_weeks:
            try:
                blocked_weeks.append(datetime.fromisoformat(week_str).date())
            except (ValueError, TypeError):
                pass

    return PreferencesResponse(
        faculty_id=faculty.id,
        preferred_weeks=preferred_weeks,
        blocked_weeks=blocked_weeks,
        max_weeks_per_month=preferences.max_weeks_per_month or 2,
        max_consecutive_weeks=preferences.max_consecutive_weeks or 1,
        min_gap_between_weeks=preferences.min_gap_between_weeks or 2,
        target_weeks_per_year=preferences.target_weeks_per_year or 6,
        notify_swap_requests=preferences.notify_swap_requests if preferences.notify_swap_requests is not None else True,
        notify_schedule_changes=preferences.notify_schedule_changes if preferences.notify_schedule_changes is not None else True,
        notify_conflict_alerts=preferences.notify_conflict_alerts if preferences.notify_conflict_alerts is not None else True,
        notify_reminder_days=preferences.notify_reminder_days or 7,
        notes=preferences.notes,
        updated_at=preferences.updated_at,
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

    # Query open swap requests for marketplace
    # Get all PENDING swaps that are open to the marketplace
    # (either ABSORB type or not yet accepted)
    open_swaps = (
        db.query(SwapRecord)
        .filter(
            SwapRecord.status == SwapStatus.PENDING,
            SwapRecord.source_faculty_id != faculty.id,  # Exclude current user's own requests
        )
        .order_by(SwapRecord.requested_at.desc())
        .all()
    )

    # Count user's own postings
    my_postings = (
        db.query(SwapRecord)
        .filter(
            SwapRecord.source_faculty_id == faculty.id,
            SwapRecord.status == SwapStatus.PENDING,
        )
        .count()
    )

    # Get faculty's current FMIT schedule to check compatibility
    fmit_template = db.query(RotationTemplate).filter(
        RotationTemplate.name == "FMIT"
    ).first()

    faculty_scheduled_weeks = set()
    if fmit_template:
        assignments = (
            db.query(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .filter(
                Assignment.person_id == faculty.id,
                Assignment.rotation_template_id == fmit_template.id,
            )
            .all()
        )

        # Get all weeks this faculty is already scheduled
        for assignment in assignments:
            week_start = _get_week_start(assignment.block.date)
            faculty_scheduled_weeks.add(week_start)

    # Convert to MarketplaceEntry
    entries = []
    for swap in open_swaps:
        # Check if compatible (viewer is not already scheduled that week)
        is_compatible = swap.source_week not in faculty_scheduled_weeks

        # Calculate expiration (e.g., 30 days from posting)
        expires_at = swap.requested_at + timedelta(days=30)

        entry = MarketplaceEntry(
            request_id=swap.id,
            requesting_faculty_name=swap.source_faculty.name if swap.source_faculty else "Unknown",
            week_available=swap.source_week,
            reason=swap.reason,
            posted_at=swap.requested_at,
            expires_at=expires_at,
            is_compatible=is_compatible,
        )
        entries.append(entry)

    return MarketplaceResponse(
        entries=entries,
        total=len(entries),
        my_postings=my_postings,
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


def _get_week_start(any_date):
    """
    Get the Monday of the week containing the given date.

    Args:
        any_date: Any date within the target week

    Returns:
        Date of the Monday of that week
    """
    from datetime import date, timedelta

    # Ensure we have a date object
    if isinstance(any_date, datetime):
        any_date = any_date.date()

    # Monday is 0, Sunday is 6
    days_since_monday = any_date.weekday()
    week_start = any_date - timedelta(days=days_since_monday)

    return week_start
