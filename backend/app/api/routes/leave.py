"""
API routes for leave management with FMIT integration.

Provides endpoints for:
- Leave CRUD operations
- Leave calendar view
- Bulk leave import
- Webhook for external leave systems
"""

import hashlib
import hmac
import logging
from datetime import date, datetime
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Request,
    status,
)
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.dependencies.role_filter import require_admin
from app.core.config import get_settings
from app.core.security import get_current_active_user, get_current_user
from app.db.session import get_db
from app.models.absence import Absence
from app.models.person import Person
from app.models.user import User
from app.schemas.leave import (
    BulkLeaveImportRequest,
    BulkLeaveImportResponse,
    LeaveCalendarEntry,
    LeaveCalendarResponse,
    LeaveCreateRequest,
    LeaveListResponse,
    LeaveResponse,
    LeaveUpdateRequest,
    LeaveWebhookPayload,
)
from app.services.conflict_auto_detector import ConflictAutoDetector

router = APIRouter(prefix="/leave", tags=["leave"])
logger = logging.getLogger(__name__)


async def verify_webhook_signature(
    request: Request,
    x_webhook_signature: str | None = Header(None, alias="X-Webhook-Signature"),
    x_webhook_timestamp: str | None = Header(None, alias="X-Webhook-Timestamp"),
) -> None:
    """
    Verify webhook HMAC signature and timestamp to authenticate webhook requests.

    Args:
        request: FastAPI request object to read the body
        x_webhook_signature: HMAC signature from webhook header
        x_webhook_timestamp: Unix timestamp from webhook header

    Raises:
        HTTPException: 401 if signature is invalid or missing
    """
    settings = get_settings()

    # Check required headers
    if not x_webhook_signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Webhook-Signature header",
        )

    if not x_webhook_timestamp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Webhook-Timestamp header",
        )

        # Validate timestamp to prevent replay attacks
    try:
        webhook_time = datetime.fromtimestamp(int(x_webhook_timestamp))
        current_time = datetime.utcnow()
        time_difference = abs((current_time - webhook_time).total_seconds())

        if time_difference > settings.WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Webhook timestamp outside acceptable range (possible replay attack)",
            )
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid webhook timestamp format: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid timestamp format",
        )

        # Read the raw body for signature verification
    body = await request.body()

    # Compute expected HMAC signature
    # Format: HMAC-SHA256(webhook_secret, timestamp + "." + body)
    message = f"{x_webhook_timestamp}.{body.decode('utf-8')}"
    expected_signature = hmac.new(
        settings.WEBHOOK_SECRET.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    # Compare signatures using constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(expected_signature, x_webhook_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )


@router.get("/", response_model=LeaveListResponse)
async def list_leave(
    faculty_id: UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = 1,
    page_size: int = 20,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List leave records with optional filters.
    """
    query = db.query(Absence)

    if faculty_id:
        query = query.filter(Absence.person_id == faculty_id)
    if start_date:
        query = query.filter(Absence.end_date >= start_date)
    if end_date:
        query = query.filter(Absence.start_date <= end_date)

    total = query.count()
    absences = query.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for absence in absences:
        items.append(
            LeaveResponse(
                id=absence.id,
                faculty_id=absence.person_id,
                faculty_name=absence.person.name if absence.person else "Unknown",
                start_date=absence.start_date,
                end_date=absence.end_date,
                leave_type=absence.absence_type,
                is_blocking=absence.should_block_assignment,
                description=absence.notes,
                created_at=(
                    absence.created_at if hasattr(absence, "created_at") else None
                ),
                updated_at=(
                    absence.updated_at if hasattr(absence, "updated_at") else None
                ),
            )
        )

    return LeaveListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/calendar", response_model=LeaveCalendarResponse)
async def get_leave_calendar(
    start_date: date,
    end_date: date,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get leave calendar for a date range.

    Shows all leave records with conflict indicators for FMIT overlap.
    """
    absences = (
        db.query(Absence)
        .filter(
            Absence.end_date >= start_date,
            Absence.start_date <= end_date,
        )
        .all()
    )

    entries = []
    conflict_count = 0

    # Initialize conflict detector
    conflict_detector = ConflictAutoDetector(db)

    for absence in absences:
        # Check for FMIT conflicts using the conflict detector service
        has_conflict = False
        conflicts = conflict_detector.detect_conflicts_for_absence(absence.id)

        # Check if any conflicts are FMIT-related
        if conflicts:
            has_conflict = any(
                c.conflict_type == "leave_fmit_overlap" for c in conflicts
            )

        entry = LeaveCalendarEntry(
            faculty_id=absence.person_id,
            faculty_name=absence.person.name if absence.person else "Unknown",
            leave_type=absence.absence_type,
            start_date=absence.start_date,
            end_date=absence.end_date,
            is_blocking=absence.should_block_assignment,
            has_fmit_conflict=has_conflict,
        )
        entries.append(entry)
        if has_conflict:
            conflict_count += 1

    return LeaveCalendarResponse(
        start_date=start_date,
        end_date=end_date,
        entries=entries,
        conflict_count=conflict_count,
    )


@router.post("/", response_model=LeaveResponse, status_code=status.HTTP_201_CREATED)
async def create_leave(
    request: LeaveCreateRequest,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new leave record.

    Automatically triggers conflict detection in the background.
    """
    # Verify faculty exists
    person = (
        db.execute(select(Person).where(Person.id == request.faculty_id))
    ).scalar_one_or_none()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faculty not found",
        )

    absence = Absence(
        person_id=request.faculty_id,
        start_date=request.start_date,
        end_date=request.end_date,
        absence_type=request.leave_type.value,
        is_blocking=request.is_blocking,
        notes=request.description,
    )
    db.add(absence)
    db.commit()
    db.refresh(absence)

    # Trigger conflict detection in background using Celery
    from app.notifications.tasks import detect_leave_conflicts

    background_tasks.add_task(detect_leave_conflicts.delay, str(absence.id))

    return LeaveResponse(
        id=absence.id,
        faculty_id=absence.person_id,
        faculty_name=person.name,
        start_date=absence.start_date,
        end_date=absence.end_date,
        leave_type=absence.absence_type,
        is_blocking=absence.is_blocking or absence.absence_type == "deployment",
        description=absence.notes,
        created_at=absence.created_at if hasattr(absence, "created_at") else None,
        updated_at=None,
    )


@router.put("/{leave_id}", response_model=LeaveResponse)
async def update_leave(
    leave_id: UUID,
    request: LeaveUpdateRequest,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing leave record."""
    absence = (
        db.execute(select(Absence).where(Absence.id == leave_id))
    ).scalar_one_or_none()
    if not absence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave record not found",
        )

    if request.start_date is not None:
        absence.start_date = request.start_date
    if request.end_date is not None:
        absence.end_date = request.end_date
    if request.leave_type is not None:
        absence.absence_type = request.leave_type.value
    if request.is_blocking is not None:
        absence.is_blocking = request.is_blocking
    if request.description is not None:
        absence.notes = request.description

    db.commit()
    db.refresh(absence)

    return LeaveResponse(
        id=absence.id,
        faculty_id=absence.person_id,
        faculty_name=absence.person.name if absence.person else "Unknown",
        start_date=absence.start_date,
        end_date=absence.end_date,
        leave_type=absence.absence_type,
        is_blocking=absence.is_blocking or absence.absence_type == "deployment",
        description=absence.notes,
        created_at=absence.created_at if hasattr(absence, "created_at") else None,
        updated_at=absence.updated_at if hasattr(absence, "updated_at") else None,
    )


@router.delete("/{leave_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_leave(
    leave_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete a leave record."""
    absence = (
        db.execute(select(Absence).where(Absence.id == leave_id))
    ).scalar_one_or_none()
    if not absence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave record not found",
        )

    db.delete(absence)
    db.commit()


@router.post("/webhook")
async def leave_webhook(
    payload: LeaveWebhookPayload,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    _: None = Depends(verify_webhook_signature),
):
    """
    Webhook endpoint for external leave systems.

    Accepts leave change notifications and triggers conflict detection.
    Requires valid HMAC signature in X-Webhook-Signature header and
    timestamp in X-Webhook-Timestamp header for authentication.
    """
    if payload.event_type == "created":
        # Handle new leave
        pass
    elif payload.event_type == "updated":
        # Handle leave update
        pass
    elif payload.event_type == "deleted":
        # Handle leave deletion
        pass

    return {"status": "received", "event_type": payload.event_type}


@router.post("/bulk-import", response_model=BulkLeaveImportResponse)
async def bulk_import_leave(
    request: BulkLeaveImportRequest,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
):
    """
    Bulk import leave records. Requires admin role.

    Useful for syncing from external systems.
    """
    imported = 0
    skipped = 0
    errors = []

    for record in request.records:
        try:
            # Check for duplicates if skip_duplicates is enabled
            if request.skip_duplicates:
                existing = (
                    db.query(Absence)
                    .filter(
                        Absence.person_id == record.faculty_id,
                        Absence.start_date == record.start_date,
                        Absence.end_date == record.end_date,
                    )
                    .first()
                )
                if existing:
                    skipped += 1
                    continue

            absence = Absence(
                person_id=record.faculty_id,
                start_date=record.start_date,
                end_date=record.end_date,
                absence_type=record.leave_type.value,
                is_blocking=record.is_blocking,
                notes=record.description,
            )
            db.add(absence)
            imported += 1

        except Exception as e:
            errors.append(f"Failed to import record for {record.faculty_id}: {str(e)}")

    db.commit()

    return BulkLeaveImportResponse(
        success=len(errors) == 0,
        imported_count=imported,
        skipped_count=skipped,
        error_count=len(errors),
        errors=errors,
    )
