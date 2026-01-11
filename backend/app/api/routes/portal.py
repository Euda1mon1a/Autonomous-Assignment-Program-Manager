"""
API routes for faculty self-service portal.

This module provides endpoints for faculty members to manage their FMIT
(Faculty Member in Training) schedules, request and respond to schedule swaps,
set scheduling preferences, and view available swap opportunities in the
marketplace.

Key Features:
    - Schedule View: View assigned FMIT weeks with conflict indicators
    - Swap Management: Create, respond to, and track swap requests
    - Preferences: Configure scheduling preferences and notification settings
    - Dashboard: Personalized overview of schedule status and pending actions
    - Marketplace: Browse and claim available swap opportunities from other faculty

Authentication:
    All endpoints require authentication via JWT token. The current user must
    have a linked faculty profile in the Person table (matched by email).

Related Models:
    - Person: Faculty profile information
    - Assignment: Schedule assignments
    - Block: Calendar blocks (AM/PM sessions)
    - SwapRecord: Swap request records
    - FacultyPreference: Faculty scheduling preferences
    - ConflictAlert: Schedule conflict notifications
    - RotationTemplate: Rotation types (e.g., FMIT)

Related Schemas:
    - app.schemas.portal: Request/response models for all portal endpoints
"""

import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from uuid import UUID

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.security import get_current_user, get_current_active_user
from app.db.session import get_db
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.conflict_alert import ConflictAlert, ConflictAlertStatus
from app.models.faculty_preference import FacultyPreference
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.feature_flag import FeatureFlag
from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.models.user import User
from app.features.evaluator import FeatureFlagEvaluator
from app.schemas.portal import (
    DashboardAlert,
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
from app.services.swap_notification_service import SwapNotificationService

router = APIRouter(prefix="/portal", tags=["portal"])

# Feature flag key for swap marketplace access
SWAP_MARKETPLACE_FLAG_KEY = "swap_marketplace_enabled"


def _check_marketplace_access(db: Session, user: User) -> bool:
    """
    Check if the user has access to the swap marketplace.

    Uses the feature flag system to determine access based on user role.
    By default, the marketplace is disabled for residents to prevent
    gamification of swaps (e.g., exploiting post-call PCAT/DO rules).

    Args:
        db: Database session
        user: Authenticated user

    Returns:
        True if user has marketplace access, False otherwise

    Feature Flag Semantics:
        - Flag key: 'swap_marketplace_enabled'
        - If flag doesn't exist: residents blocked, others allowed
        - If flag.enabled=False: all users blocked
        - If flag.target_roles is None: all roles allowed (if enabled)
        - If flag.target_roles is []: no roles allowed
        - If flag.target_user_ids is None: no user-specific targeting
        - If flag.target_user_ids is []: no users allowed (overrides roles)
        - Environment targeting respects TELEMETRY_ENVIRONMENT setting
    """
    # Query the feature flag
    flag = (
        db.query(FeatureFlag)
        .filter(FeatureFlag.key == SWAP_MARKETPLACE_FLAG_KEY)
        .first()
    )

    # If flag doesn't exist, default to allowing access for non-residents
    # This maintains backward compatibility while still blocking residents by default
    if flag is None:
        # Default behavior: residents are blocked, others allowed
        return user.role != "resident"

    # Convert flag to dict for evaluator
    # IMPORTANT: Preserve empty lists vs None semantics:
    # - None means "no targeting" (allow everyone)
    # - [] means "target nobody" (allow no one)
    flag_data = {
        "key": flag.key,
        "enabled": flag.enabled,
        "flag_type": flag.flag_type,
        "rollout_percentage": flag.rollout_percentage,
        "environments": flag.environments,
        "target_user_ids": (
            [str(uid) for uid in flag.target_user_ids]
            if flag.target_user_ids is not None
            else None
        ),
        "target_roles": flag.target_roles,
        "variants": flag.variants,
        "dependencies": flag.dependencies,
        "custom_attributes": flag.custom_attributes,
    }

    # Evaluate flag for this user, respecting environment targeting
    settings = get_settings()
    evaluator = FeatureFlagEvaluator(environment=settings.TELEMETRY_ENVIRONMENT)
    enabled, _, _ = evaluator.evaluate(
        flag_data=flag_data,
        user_id=str(user.id),
        user_role=user.role,
    )

    return enabled


@router.get("/my/schedule", response_model=MyScheduleResponse)
async def get_my_schedule(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get the current user's FMIT schedule.

    Retrieves all FMIT week assignments for the authenticated faculty member,
    including conflict indicators, pending swap requests, and comparison to
    target workload. Weeks are grouped and returned with metadata indicating
    whether they're in the past, have conflicts, or are eligible for swaps.

    Args:
        db: Database session injected via dependency
        current_user: Authenticated user injected via dependency

    Returns:
        MyScheduleResponse: Contains faculty info, list of FMIT weeks with
            metadata (conflicts, swap eligibility), total weeks assigned,
            target weeks per year, and weeks remaining to meet target.

    Raises:
        HTTPException: 403 if current user has no linked faculty profile

    Business Logic:
        - Queries all FMIT assignments for the faculty member
        - Groups assignments by week (Monday-Sunday)
        - Checks for active conflict alerts (NEW or ACKNOWLEDGED status)
        - Identifies weeks with pending swap requests
        - Past weeks (week_end < today) cannot request swaps
        - Uses target_weeks_per_year from preferences (default: 6)
    """
    # Get faculty profile linked to current user
    faculty = _get_faculty_for_user(db, current_user)

    # Query actual FMIT weeks from schedule
    fmit_template = (
        db.execute(select(RotationTemplate).where(RotationTemplate.name == "FMIT"))
    ).scalar_one_or_none()

    fmit_weeks = []
    if fmit_template:
        # Get all FMIT assignments for this faculty (eager load block to avoid N+1)
        assignments = (
            db.query(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .options(joinedload(Assignment.block))
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
        pending_swaps = (
            db.query(SwapRecord)
            .options(joinedload(SwapRecord.source_faculty))
            .filter(
                SwapRecord.source_faculty_id == faculty.id,
                SwapRecord.status == SwapStatus.PENDING,
            )
            .all()
        )

        pending_swap_weeks = {swap.source_week for swap in pending_swaps}

        # Convert to FMITWeekInfo
        today = datetime.utcnow().date()
        for week_start, _week_assignments in sorted(week_map.items()):
            week_end = week_start + timedelta(days=6)
            has_pending_swap = week_start in pending_swap_weeks

            # Check for conflicts from conflict_alerts table
            conflict_alert = (
                db.query(ConflictAlert)
                .options(joinedload(ConflictAlert.faculty))
                .filter(
                    ConflictAlert.faculty_id == faculty.id,
                    ConflictAlert.fmit_week == week_start,
                    ConflictAlert.status.in_(
                        [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                    ),
                )
                .first()
            )

            has_conflict = conflict_alert is not None
            conflict_description = (
                conflict_alert.description if conflict_alert else None
            )

            fmit_weeks.append(
                FMITWeekInfo(
                    week_start=week_start,
                    week_end=week_end,
                    is_past=week_end < today,
                    has_conflict=has_conflict,
                    conflict_description=conflict_description,
                    can_request_swap=not has_pending_swap and week_start > today,
                    pending_swap_request=has_pending_swap,
                )
            )

    # Get target weeks from preferences or use default
    preferences = (
        db.query(FacultyPreference)
        .filter(FacultyPreference.faculty_id == faculty.id)
        .first()
    )
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
async def get_my_swaps(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get swap requests related to the current user.

    Retrieves all swap requests where the authenticated faculty member is
    either the source (requesting) or target (receiving) party. Returns
    three categories: incoming pending requests requiring action, outgoing
    pending requests awaiting response, and recently completed swaps.

    Args:
        db: Database session injected via dependency
        current_user: Authenticated user injected via dependency

    Returns:
        MySwapsResponse: Contains three lists of SwapRequestSummary objects:
            - incoming_requests: Swaps targeting this faculty (PENDING)
            - outgoing_requests: Swaps initiated by this faculty (PENDING)
            - recent_swaps: Completed swaps from last 30 days (EXECUTED,
              APPROVED, or REJECTED status)

    Raises:
        HTTPException: 403 if current user has no linked faculty profile

    Business Logic:
        - Incoming: target_faculty_id matches, status PENDING
        - Outgoing: source_faculty_id matches, status PENDING
        - Recent: either party matches, non-PENDING status, last 30 days
        - Limited to 10 most recent completed swaps
    """
    faculty = _get_faculty_for_user(db, current_user)

    # Query SwapRecord for this faculty
    # Eager load faculty relationships to avoid N+1 queries
    # Incoming requests: where this faculty is the target and status is pending
    incoming_swaps = (
        db.query(SwapRecord)
        .options(
            joinedload(SwapRecord.source_faculty), joinedload(SwapRecord.target_faculty)
        )
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
        .options(
            joinedload(SwapRecord.source_faculty), joinedload(SwapRecord.target_faculty)
        )
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
        .options(
            joinedload(SwapRecord.source_faculty), joinedload(SwapRecord.target_faculty)
        )
        .filter(
            (SwapRecord.source_faculty_id == faculty.id)
            | (SwapRecord.target_faculty_id == faculty.id),
            SwapRecord.status.in_(
                [SwapStatus.EXECUTED, SwapStatus.APPROVED, SwapStatus.REJECTED]
            ),
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
async def create_swap_request(
    request: SwapRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new swap request to offload an FMIT week.

    Allows faculty to request swapping an assigned FMIT week with another
    faculty member. Can either target a specific faculty member (one-to-one
    swap) or post to the marketplace for anyone to claim (absorb). Optionally
    notifies potential swap candidates via the notification service.

    Args:
        request: SwapRequestCreate containing week_to_offload (date),
            optional preferred_target_faculty_id (UUID), reason (str),
            and auto_find_candidates (bool)
        db: Database session injected via dependency
        current_user: Authenticated user injected via dependency

    Returns:
        SwapRequestResponse: Contains success status, created swap request ID,
            confirmation message, and number of candidates notified (if any)

    Raises:
        HTTPException: 404 if FMIT rotation template not found
        HTTPException: 400 if faculty has no FMIT assignment for the specified week
        HTTPException: 400 if a pending swap already exists for the week
        HTTPException: 403 if current user has no linked faculty profile
        HTTPException: 403 if posting to marketplace and access is disabled for role

    Business Logic:
        - Validates the requesting faculty has FMIT assignments for the week
        - Prevents duplicate swap requests for the same week
        - SwapType.ONE_TO_ONE if preferred_target_faculty_id provided
        - SwapType.ABSORB if no target specified (marketplace posting)
        - If auto_find_candidates=True, queries faculty with notification
          preferences enabled and sends swap opportunity notifications
        - Creates SwapRecord with PENDING status
        - Marketplace posting restricted by 'swap_marketplace_enabled' flag
          (disabled for residents by default to prevent gamification)
    """
    # Check marketplace access if posting to marketplace (no target specified)
    if not request.preferred_target_faculty_id:
        if not _check_marketplace_access(db, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Swap marketplace posting is not enabled for your role. "
                "You can still request direct swaps with specific faculty members. "
                "Contact an administrator if you need marketplace access.",
            )

    faculty = _get_faculty_for_user(db, current_user)

    # Implement swap request creation
    # 1. Verify week is assigned to this faculty
    fmit_template = (
        db.execute(select(RotationTemplate).where(RotationTemplate.name == "FMIT"))
    ).scalar_one_or_none()

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
        .options(
            joinedload(Assignment.block),
            joinedload(Assignment.person),
            joinedload(Assignment.rotation_template),
        )
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
    existing_swap = (
        db.query(SwapRecord)
        .options(
            joinedload(SwapRecord.source_faculty), joinedload(SwapRecord.target_faculty)
        )
        .filter(
            SwapRecord.source_faculty_id == faculty.id,
            SwapRecord.source_week == week_start,
            SwapRecord.status == SwapStatus.PENDING,
        )
        .first()
    )

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
            .options(joinedload(FacultyPreference.faculty))
            .filter(
                FacultyPreference.faculty_id != faculty.id,
                FacultyPreference.notify_swap_requests.is_(True),
            )
            .limit(100)
            .all()
        )

        # Create notifications for candidates
        notification_service = SwapNotificationService(db)
        for pref in preferences:
            notification = notification_service.notify_marketplace_match(
                recipient_faculty_id=pref.faculty_id,
                poster_name=faculty.name,
                week_available=week_start,
                request_id=swap_record.id,
            )
            if notification:
                candidates_notified += 1

        # Send all pending notifications
        notification_service.send_pending_notifications()

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
async def respond_to_swap(
    swap_id: UUID,
    request: SwapRespondRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Respond to an incoming swap request.

    Allows faculty to accept or reject swap requests where they are the
    target party. When accepting, can optionally provide a counter-offer
    week to convert an ABSORB swap into a ONE_TO_ONE swap. Updates the
    SwapRecord status and timestamps.

    Args:
        swap_id: UUID of the swap request to respond to
        request: SwapRespondRequest containing accept (bool), optional
            counter_offer_week (date), and optional notes (str)
        db: Database session injected via dependency
        current_user: Authenticated user injected via dependency

    Returns:
        dict: Contains success (bool), message (str), swap_id (UUID),
            and updated status (str)

    Raises:
        HTTPException: 404 if swap request not found
        HTTPException: 403 if current user is not the target of the swap
        HTTPException: 400 if swap is no longer PENDING
        HTTPException: 403 if current user has no linked faculty profile

    Business Logic:
        - Only the target_faculty can respond to a swap
        - Swap must be in PENDING status
        - If accept=True:
            - With counter_offer_week: Sets target_week, type=ONE_TO_ONE
            - Without counter_offer_week: Type=ABSORB, no target_week
            - Status changed to APPROVED, approved_at set
        - If accept=False:
            - Status changed to REJECTED
            - approved_at timestamp still set (tracks when rejected)
        - Notes are appended to swap.notes field
    """
    faculty = _get_faculty_for_user(db, current_user)

    # Implement swap response
    # Query the swap record
    swap = (
        db.query(SwapRecord)
        .options(
            joinedload(SwapRecord.source_faculty), joinedload(SwapRecord.target_faculty)
        )
        .filter(SwapRecord.id == swap_id)
        .first()
    )

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
async def get_my_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get the current user's FMIT scheduling preferences.

    Retrieves the faculty member's scheduling preferences including preferred
    and blocked weeks, workload constraints, and notification settings. Returns
    default values if no preferences have been set yet.

    Args:
        db: Database session injected via dependency
        current_user: Authenticated user injected via dependency

    Returns:
        PreferencesResponse: Contains faculty_id, preferred_weeks (list of dates),
            blocked_weeks (list of dates), max_weeks_per_month (int),
            max_consecutive_weeks (int), min_gap_between_weeks (int),
            target_weeks_per_year (int), notification flags (bool),
            notify_reminder_days (int), notes (str), and updated_at (datetime)

    Raises:
        HTTPException: 403 if current user has no linked faculty profile

    Business Logic:
        - Returns defaults if no FacultyPreference record exists:
            - max_weeks_per_month: 2
            - max_consecutive_weeks: 1
            - min_gap_between_weeks: 2
            - target_weeks_per_year: 6
            - All notification flags: True
            - notify_reminder_days: 7
        - Converts JSON-stored ISO date strings to Python date objects
        - Skips invalid dates in preferred_weeks and blocked_weeks
    """
    faculty = _get_faculty_for_user(db, current_user)

    # Query FacultyPreference for this faculty
    preferences = (
        db.query(FacultyPreference)
        .options(joinedload(FacultyPreference.faculty))
        .filter(FacultyPreference.faculty_id == faculty.id)
        .first()
    )

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
            except (ValueError, TypeError) as e:
                logger.warning(
                    "Invalid date format in preferred_weeks for faculty %s: %s (%s)",
                    faculty.id,
                    week_str,
                    e,
                )

    blocked_weeks = []
    if preferences.blocked_weeks:
        for week_str in preferences.blocked_weeks:
            try:
                blocked_weeks.append(datetime.fromisoformat(week_str).date())
            except (ValueError, TypeError) as e:
                logger.warning(
                    "Invalid date format in blocked_weeks for faculty %s: %s (%s)",
                    faculty.id,
                    week_str,
                    e,
                )

    return PreferencesResponse(
        faculty_id=faculty.id,
        preferred_weeks=preferred_weeks,
        blocked_weeks=blocked_weeks,
        max_weeks_per_month=preferences.max_weeks_per_month or 2,
        max_consecutive_weeks=preferences.max_consecutive_weeks or 1,
        min_gap_between_weeks=preferences.min_gap_between_weeks or 2,
        target_weeks_per_year=preferences.target_weeks_per_year or 6,
        notify_swap_requests=(
            preferences.notify_swap_requests
            if preferences.notify_swap_requests is not None
            else True
        ),
        notify_schedule_changes=(
            preferences.notify_schedule_changes
            if preferences.notify_schedule_changes is not None
            else True
        ),
        notify_conflict_alerts=(
            preferences.notify_conflict_alerts
            if preferences.notify_conflict_alerts is not None
            else True
        ),
        notify_reminder_days=preferences.notify_reminder_days or 7,
        notes=preferences.notes,
        updated_at=preferences.updated_at,
    )


@router.put("/my/preferences", response_model=PreferencesResponse)
async def update_my_preferences(
    request: PreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update the current user's FMIT scheduling preferences.

    Allows faculty to update their scheduling preferences including preferred
    and blocked weeks, workload constraints, and notification settings. Creates
    a new FacultyPreference record if one doesn't exist. Only updates fields
    that are explicitly provided in the request (partial updates supported).

    Args:
        request: PreferencesUpdate containing optional fields: preferred_weeks
            (list of dates), blocked_weeks (list of dates), max_weeks_per_month
            (int), max_consecutive_weeks (int), min_gap_between_weeks (int),
            notification flags (bool), notify_reminder_days (int), notes (str)
        db: Database session injected via dependency
        current_user: Authenticated user injected via dependency

    Returns:
        PreferencesResponse: Updated preferences with all fields populated,
            including faculty_id and updated_at timestamp

    Raises:
        HTTPException: 403 if current user has no linked faculty profile

    Business Logic:
        - Creates new FacultyPreference record with defaults if none exists
        - Only updates fields that are not None in the request
        - Converts date objects to ISO format strings for JSON storage
        - Sets updated_at to current UTC time
        - Commits changes and refreshes to get updated values
        - Converts stored ISO strings back to date objects for response
    """
    faculty = _get_faculty_for_user(db, current_user)

    # Update FacultyPreference
    # Query existing preferences or create new
    preferences = (
        db.query(FacultyPreference)
        .options(joinedload(FacultyPreference.faculty))
        .filter(FacultyPreference.faculty_id == faculty.id)
        .first()
    )

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
            except (ValueError, TypeError) as e:
                logger.warning(
                    "Invalid date format in preferred_weeks for faculty %s: %s (%s)",
                    faculty.id,
                    week_str,
                    e,
                )

    blocked_weeks = []
    if preferences.blocked_weeks:
        for week_str in preferences.blocked_weeks:
            try:
                blocked_weeks.append(datetime.fromisoformat(week_str).date())
            except (ValueError, TypeError) as e:
                logger.warning(
                    "Invalid date format in blocked_weeks for faculty %s: %s (%s)",
                    faculty.id,
                    week_str,
                    e,
                )

    return PreferencesResponse(
        faculty_id=faculty.id,
        preferred_weeks=preferred_weeks,
        blocked_weeks=blocked_weeks,
        max_weeks_per_month=preferences.max_weeks_per_month or 2,
        max_consecutive_weeks=preferences.max_consecutive_weeks or 1,
        min_gap_between_weeks=preferences.min_gap_between_weeks or 2,
        target_weeks_per_year=preferences.target_weeks_per_year or 6,
        notify_swap_requests=(
            preferences.notify_swap_requests
            if preferences.notify_swap_requests is not None
            else True
        ),
        notify_schedule_changes=(
            preferences.notify_schedule_changes
            if preferences.notify_schedule_changes is not None
            else True
        ),
        notify_conflict_alerts=(
            preferences.notify_conflict_alerts
            if preferences.notify_conflict_alerts is not None
            else True
        ),
        notify_reminder_days=preferences.notify_reminder_days or 7,
        notes=preferences.notes,
        updated_at=preferences.updated_at,
    )


@router.get("/my/dashboard", response_model=DashboardResponse)
async def get_my_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get the dashboard view for the current user.

    Provides a comprehensive overview of the faculty member's schedule status
    including workload statistics, upcoming FMIT weeks, recent conflict alerts,
    and pending swap decisions. This is the main landing page view for the
    faculty portal.

    Args:
        db: Database session injected via dependency
        current_user: Authenticated user injected via dependency

    Returns:
        DashboardResponse: Contains faculty_id, faculty_name, stats
            (DashboardStats with weeks assigned/completed/remaining, target,
            pending swaps, unread alerts), upcoming_weeks (list of FMITWeekInfo),
            recent_alerts (list of alert summaries), and pending_swap_decisions
            (list of swaps requiring response)

    Raises:
        HTTPException: 403 if current user has no linked faculty profile

    Business Logic:
        - Queries actual week counts from assignments
        - Shows upcoming weeks (next 4-8 weeks)
        - Displays recent conflict alerts (last 30 days, NEW or ACKNOWLEDGED status)
        - Lists incoming swaps requiring response (PENDING status)
    """
    faculty = _get_faculty_for_user(db, current_user)
    today = datetime.utcnow().date()

    # Get FMIT template
    fmit_template = (
        db.execute(select(RotationTemplate).where(RotationTemplate.name == "FMIT"))
    ).scalar_one_or_none()

    # Initialize counters
    weeks_assigned = 0
    weeks_completed = 0
    weeks_remaining = 0
    upcoming_weeks = []

    if fmit_template:
        # Get all FMIT assignments for this faculty (eager load block to avoid N+1)
        assignments = (
            db.query(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .options(joinedload(Assignment.block))
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

        # Count weeks
        weeks_assigned = len(week_map)

        # Count completed vs remaining weeks
        for week_start in week_map:
            week_end = week_start + timedelta(days=6)
            if week_end < today:
                weeks_completed += 1
            else:
                weeks_remaining += 1

        # Get upcoming weeks (next 8 weeks)
        eight_weeks_out = today + timedelta(weeks=8)
        for week_start, _week_assignments in sorted(week_map.items()):
            week_end = week_start + timedelta(days=6)

            # Only include weeks starting from today up to 8 weeks out
            if week_start >= today and week_start <= eight_weeks_out:
                # Check for conflicts
                conflict_alert = (
                    db.query(ConflictAlert)
                    .filter(
                        ConflictAlert.faculty_id == faculty.id,
                        ConflictAlert.fmit_week == week_start,
                        ConflictAlert.status.in_(
                            [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
                        ),
                    )
                    .first()
                )

                has_conflict = conflict_alert is not None
                conflict_description = (
                    conflict_alert.description if conflict_alert else None
                )

                # Check for pending swaps
                pending_swap = (
                    db.query(SwapRecord)
                    .filter(
                        SwapRecord.source_faculty_id == faculty.id,
                        SwapRecord.source_week == week_start,
                        SwapRecord.status == SwapStatus.PENDING,
                    )
                    .first()
                )

                has_pending_swap = pending_swap is not None

                upcoming_weeks.append(
                    FMITWeekInfo(
                        week_start=week_start,
                        week_end=week_end,
                        is_past=False,  # All upcoming weeks are not past
                        has_conflict=has_conflict,
                        conflict_description=conflict_description,
                        can_request_swap=not has_pending_swap,
                        pending_swap_request=has_pending_swap,
                    )
                )

    # Get target weeks from preferences
    preferences = (
        db.query(FacultyPreference)
        .filter(FacultyPreference.faculty_id == faculty.id)
        .first()
    )
    target_weeks = preferences.target_weeks_per_year if preferences else 6

    # Count pending swap requests (incoming)
    pending_swap_requests_count = (
        db.query(SwapRecord)
        .filter(
            SwapRecord.target_faculty_id == faculty.id,
            SwapRecord.status == SwapStatus.PENDING,
        )
        .count()
    )

    # Count unread alerts (NEW status only)
    unread_alerts_count = (
        db.query(ConflictAlert)
        .filter(
            ConflictAlert.faculty_id == faculty.id,
            ConflictAlert.status == ConflictAlertStatus.NEW,
        )
        .count()
    )

    # Get recent conflict alerts (last 30 days, NEW or ACKNOWLEDGED)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_alerts_query = (
        db.query(ConflictAlert)
        .filter(
            ConflictAlert.faculty_id == faculty.id,
            ConflictAlert.created_at >= thirty_days_ago,
            ConflictAlert.status.in_(
                [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED]
            ),
        )
        .order_by(ConflictAlert.created_at.desc())
        .limit(10)
        .all()
    )

    # Convert to DashboardAlert
    recent_alerts = []
    for alert in recent_alerts_query:
        # Determine severity based on alert type
        severity = "warning"  # Default
        if hasattr(alert, "severity") and alert.severity:
            severity = alert.severity
        elif "critical" in alert.description.lower() if alert.description else False:
            severity = "critical"

        # Determine action URL - link to schedule view with week filter
        action_url = None
        if alert.fmit_week:
            action_url = f"/portal/my/schedule?week={alert.fmit_week.isoformat()}"

        recent_alerts.append(
            DashboardAlert(
                id=alert.id,
                alert_type="conflict",
                severity=severity,
                message=alert.description or "Conflict detected",
                created_at=alert.created_at,
                action_url=action_url,
            )
        )

    # Get pending swap decisions (incoming swaps requiring response)
    incoming_swaps = (
        db.query(SwapRecord)
        .options(joinedload(SwapRecord.source_faculty))
        .filter(
            SwapRecord.target_faculty_id == faculty.id,
            SwapRecord.status == SwapStatus.PENDING,
        )
        .order_by(SwapRecord.requested_at.desc())
        .limit(10)
        .all()
    )

    # Convert to SwapRequestSummary
    pending_swap_decisions = []
    for swap in incoming_swaps:
        pending_swap_decisions.append(
            SwapRequestSummary(
                id=swap.id,
                other_faculty_name=(
                    swap.source_faculty.name if swap.source_faculty else "Unknown"
                ),
                week_to_give=swap.target_week,  # What they want from us
                week_to_receive=swap.source_week,  # What we would get
                status=swap.status.value,
                created_at=swap.requested_at,
                is_incoming=True,
            )
        )

    # Build stats
    stats = DashboardStats(
        weeks_assigned=weeks_assigned,
        weeks_completed=weeks_completed,
        weeks_remaining=weeks_remaining,
        target_weeks=target_weeks,
        pending_swap_requests=pending_swap_requests_count,
        unread_alerts=unread_alerts_count,
    )

    return DashboardResponse(
        faculty_id=faculty.id,
        faculty_name=faculty.name,
        stats=stats,
        upcoming_weeks=upcoming_weeks,
        recent_alerts=recent_alerts,
        pending_swap_decisions=pending_swap_decisions,
    )


@router.get("/marketplace", response_model=MarketplaceResponse)
async def get_swap_marketplace(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get available swap opportunities in the marketplace.

    Displays all open (PENDING) swap requests from other faculty members,
    allowing the current user to browse and claim available weeks. Shows
    compatibility based on the user's existing schedule and calculates
    expiration dates for each posting.

    Args:
        db: Database session injected via dependency
        current_user: Authenticated user injected via dependency

    Returns:
        MarketplaceResponse: Contains entries (list of MarketplaceEntry
            objects with request details, requesting faculty name, week
            available, reason, posted/expires timestamps, compatibility),
            total count of entries, and my_postings count

    Raises:
        HTTPException: 403 if current user has no linked faculty profile (non-admin)
        HTTPException: 403 if marketplace access is disabled for user's role

    Business Logic:
        - Admin users can view marketplace without faculty profile (read-only view)
        - Only shows PENDING swaps from other faculty (excludes own requests)
        - Checks compatibility: week not already assigned to viewer
        - Expiration set to 30 days from posted date
        - Counts user's own active marketplace postings separately
        - Eager loads source_faculty and blocks to avoid N+1 queries
        - Orders by most recently posted first
        - Marketplace access controlled by 'swap_marketplace_enabled' feature flag
          (disabled for residents by default to prevent gamification)
    """
    # Check marketplace access before proceeding
    if not _check_marketplace_access(db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Swap marketplace access is not enabled for your role. "
            "Contact an administrator if you believe this is an error.",
        )

    # Try to get faculty profile - admins/coordinators can view without one
    faculty = _get_faculty_for_user_optional(db, current_user)

    # Query open swap requests for marketplace
    # Get all PENDING swaps that are open to the marketplace
    # (either ABSORB type or not yet accepted)
    # Eager load source_faculty to avoid N+1 when building entries
    query = (
        db.query(SwapRecord)
        .options(joinedload(SwapRecord.source_faculty))
        .filter(SwapRecord.status == SwapStatus.PENDING)
    )

    # Exclude current user's own requests if they have a faculty profile
    if faculty:
        query = query.filter(SwapRecord.source_faculty_id != faculty.id)

    open_swaps = query.order_by(SwapRecord.requested_at.desc()).all()

    # Count user's own postings (0 if no faculty profile)
    my_postings = 0
    if faculty:
        my_postings = (
            db.query(SwapRecord)
            .filter(
                SwapRecord.source_faculty_id == faculty.id,
                SwapRecord.status == SwapStatus.PENDING,
            )
            .count()
        )

    # Get faculty's current FMIT schedule to check compatibility
    faculty_scheduled_weeks = set()
    if faculty:
        fmit_template = (
            db.execute(select(RotationTemplate).where(RotationTemplate.name == "FMIT"))
        ).scalar_one_or_none()

        if fmit_template:
            # Eager load block to avoid N+1 when accessing block.date
            assignments = (
                db.query(Assignment)
                .join(Block, Assignment.block_id == Block.id)
                .options(joinedload(Assignment.block))
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
        # If no faculty profile (admin/coordinator viewing), all are compatible
        is_compatible = (
            faculty is None or swap.source_week not in faculty_scheduled_weeks
        )

        # Calculate expiration (e.g., 30 days from posting)
        expires_at = swap.requested_at + timedelta(days=30)

        entry = MarketplaceEntry(
            request_id=swap.id,
            requesting_faculty_name=(
                swap.source_faculty.name if swap.source_faculty else "Unknown"
            ),
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
    """
    Get the faculty profile linked to a user.

    Finds the Person record with type='faculty' that matches the user's email.
    This links the authentication User record to the faculty profile in the
    scheduling system.

    Args:
        db: Database session
        user: Authenticated User object

    Returns:
        Person: Faculty profile with type='faculty' matching user's email

    Raises:
        HTTPException: 403 if no faculty profile found for user's email
    """
    # First try to find by email match
    faculty = (
        db.query(Person)
        .filter(
            Person.email == user.email,
            Person.type == "faculty",
        )
        .first()
    )

    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No faculty profile linked to this user account",
        )

    return faculty


def _get_faculty_for_user_optional(db: Session, user: User) -> Person | None:
    """
    Get the faculty profile linked to a user, or None if not found.

    Unlike _get_faculty_for_user, this does not raise an exception if no
    faculty profile exists. Used for endpoints where admins/coordinators
    can view data without being faculty members themselves.

    Args:
        db: Database session
        user: Authenticated User object

    Returns:
        Person: Faculty profile if found, None otherwise
    """
    return (
        db.query(Person)
        .filter(
            Person.email == user.email,
            Person.type == "faculty",
        )
        .first()
    )


def _get_week_start(any_date: datetime | date) -> date:
    """
    Get the Monday of the week containing the given date.

    Calculates the start of the week (Monday) for any given date. This is
    used throughout the portal to normalize dates to week boundaries for
    FMIT week assignments and swap requests.

    Args:
        any_date: Any date or datetime within the target week. Automatically
            converts datetime objects to date objects.

    Returns:
        date: The Monday of the week containing the input date. If the input
            is already a Monday, returns that date.

    Note:
        Uses ISO week definition where Monday is day 0 and Sunday is day 6.
        This ensures consistent week boundaries across all swap and scheduling
        operations.
    """
    from datetime import timedelta

    # Ensure we have a date object
    if isinstance(any_date, datetime):
        any_date = any_date.date()

    # Monday is 0, Sunday is 6
    days_since_monday = any_date.weekday()
    week_start = any_date - timedelta(days=days_since_monday)

    return week_start
