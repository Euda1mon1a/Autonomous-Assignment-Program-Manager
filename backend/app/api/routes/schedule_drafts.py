"""
Schedule drafts API routes for staging workflow.

Provides endpoints for creating, previewing, publishing, and managing
schedule drafts:
- POST /schedules/drafts - Create new draft
- GET /schedules/drafts - List drafts with pagination
- GET /schedules/drafts/{id} - Get draft details
- GET /schedules/drafts/{id}/preview - Preview changes vs live
- POST /schedules/drafts/{id}/assignments - Add assignment to draft
- POST /schedules/drafts/{id}/flags/{flag_id}/acknowledge - Acknowledge flag
- POST /schedules/drafts/{id}/publish - Publish draft to live
- POST /schedules/drafts/{id}/rollback - Rollback published draft
- DELETE /schedules/drafts/{id} - Discard draft
"""

from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.logging import get_logger
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.schedule_draft import (
    DraftAssignmentChangeType,
    ScheduleDraft,
    ScheduleDraftAssignment,
    ScheduleDraftFlag,
    ScheduleDraftStatus,
)
from app.models.user import User
from app.schemas.schedule_draft import (
    DraftAssignmentCreate,
    DraftAssignmentResponse,
    DraftFlagAcknowledge,
    DraftFlagBulkAcknowledge,
    DraftFlagResponse,
    DraftPreviewResponse,
    DraftSourceType,
    PublishRequest,
    PublishResponse,
    RollbackRequest,
    RollbackResponse,
    ScheduleDraftCounts,
    ScheduleDraftCreate,
    ScheduleDraftList,
    ScheduleDraftListItem,
    ScheduleDraftResponse,
)
from app.services.schedule_draft_service import ScheduleDraftService

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "",
    response_model=dict,
    status_code=201,
    summary="Create a schedule draft",
    description="Create a new draft for a block or date range.",
)
async def create_draft(
    request: ScheduleDraftCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new schedule draft.

    If a draft already exists for the same block/date range, returns
    that draft instead of creating a new one.

    Returns the draft ID for subsequent operations.
    """
    service = ScheduleDraftService(db)
    result = await service.create_draft(
        source_type=request.source_type,
        start_date=request.target_start_date,
        end_date=request.target_end_date,
        block_number=request.target_block,
        created_by_id=current_user.id,
        schedule_run_id=request.schedule_run_id,
        notes=request.notes,
    )

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": result.message,
                "error_code": result.error_code,
            },
        )

    return {
        "success": True,
        "draft_id": str(result.draft_id),
        "message": result.message,
    }


@router.get(
    "",
    response_model=ScheduleDraftList,
    summary="List schedule drafts",
    description="List all schedule drafts with pagination.",
)
async def list_drafts(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    status: str | None = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List schedule drafts with pagination.

    Supports filtering by status (draft, published, rolled_back, discarded).
    """
    # Parse status filter
    status_enum = None
    if status:
        try:
            status_enum = ScheduleDraftStatus(status.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={"error": f"Invalid status: {status}"},
            )

    service = ScheduleDraftService(db)
    offset = (page - 1) * page_size
    drafts = await service.list_drafts(
        status=status_enum,
        limit=page_size,
        offset=offset,
    )

    # Get total count for pagination
    total_query = db.query(ScheduleDraft)
    if status_enum:
        total_query = total_query.filter(ScheduleDraft.status == status_enum)
    total = total_query.count()

    # Convert to response format
    items = []
    for draft in drafts:
        # Calculate counts
        counts = ScheduleDraftCounts(
            assignments_total=len(draft.assignments) if draft.assignments else 0,
            added=sum(
                1
                for a in (draft.assignments or [])
                if a.change_type == DraftAssignmentChangeType.ADD
            ),
            modified=sum(
                1
                for a in (draft.assignments or [])
                if a.change_type == DraftAssignmentChangeType.MODIFY
            ),
            deleted=sum(
                1
                for a in (draft.assignments or [])
                if a.change_type == DraftAssignmentChangeType.DELETE
            ),
            flags_total=draft.flags_total or 0,
            flags_acknowledged=draft.flags_acknowledged or 0,
            flags_unacknowledged=(draft.flags_total or 0)
            - (draft.flags_acknowledged or 0),
        )

        items.append(
            ScheduleDraftListItem(
                id=draft.id,
                created_at=draft.created_at,
                status=draft.status,
                source_type=draft.source_type,
                target_block=draft.target_block,
                target_start_date=draft.target_start_date,
                target_end_date=draft.target_end_date,
                flags_total=draft.flags_total or 0,
                flags_acknowledged=draft.flags_acknowledged or 0,
                counts=counts,
            )
        )

    return ScheduleDraftList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=page * page_size < total,
        has_previous=page > 1,
    )


@router.get(
    "/{draft_id}",
    response_model=ScheduleDraftResponse,
    summary="Get draft details",
    description="Get details of a specific schedule draft.",
)
async def get_draft(
    draft_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get details of a specific schedule draft."""
    draft = db.query(ScheduleDraft).filter(ScheduleDraft.id == draft_id).first()

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    # Calculate counts
    counts = ScheduleDraftCounts(
        assignments_total=len(draft.assignments) if draft.assignments else 0,
        added=sum(
            1
            for a in (draft.assignments or [])
            if a.change_type == DraftAssignmentChangeType.ADD
        ),
        modified=sum(
            1
            for a in (draft.assignments or [])
            if a.change_type == DraftAssignmentChangeType.MODIFY
        ),
        deleted=sum(
            1
            for a in (draft.assignments or [])
            if a.change_type == DraftAssignmentChangeType.DELETE
        ),
        flags_total=draft.flags_total or 0,
        flags_acknowledged=draft.flags_acknowledged or 0,
        flags_unacknowledged=(draft.flags_total or 0) - (draft.flags_acknowledged or 0),
    )

    return ScheduleDraftResponse(
        id=draft.id,
        created_at=draft.created_at,
        created_by_id=draft.created_by_id,
        target_block=draft.target_block,
        target_start_date=draft.target_start_date,
        target_end_date=draft.target_end_date,
        status=draft.status,
        source_type=draft.source_type,
        source_schedule_run_id=draft.source_schedule_run_id,
        published_at=draft.published_at,
        published_by_id=draft.published_by_id,
        rollback_available=draft.rollback_available,
        rollback_expires_at=draft.rollback_expires_at,
        rolled_back_at=draft.rolled_back_at,
        rolled_back_by_id=draft.rolled_back_by_id,
        notes=draft.notes,
        change_summary=draft.change_summary,
        flags_total=draft.flags_total or 0,
        flags_acknowledged=draft.flags_acknowledged or 0,
        override_comment=draft.override_comment,
        override_by_id=draft.override_by_id,
        counts=counts,
    )


@router.get(
    "/{draft_id}/preview",
    response_model=DraftPreviewResponse,
    summary="Preview draft",
    description="Preview changes in draft compared to live assignments.",
)
async def preview_draft(
    draft_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Preview a draft before publishing.

    Shows all staged assignments and flags that require review.
    """
    service = ScheduleDraftService(db)
    result = await service.get_draft_preview(draft_id)

    if not result:
        raise HTTPException(status_code=404, detail="Draft not found")

    # Convert assignments to response format
    assignment_responses = []
    if result.assignments:
        for a in result.assignments:
            assignment_responses.append(
                DraftAssignmentResponse(
                    id=UUID(a["id"]),
                    draft_id=draft_id,
                    person_id=UUID(a["person_id"]),
                    person_name=a.get("person_name"),
                    assignment_date=a["date"],
                    time_of_day=a.get("time_of_day"),
                    activity_code=a.get("activity_code"),
                    change_type=DraftAssignmentChangeType(a["change_type"]),
                )
            )

    # Convert flags to response format
    flag_responses = []
    if result.flags:
        for f in result.flags:
            from app.models.schedule_draft import DraftFlagSeverity, DraftFlagType

            flag_responses.append(
                DraftFlagResponse(
                    id=UUID(f["id"]),
                    draft_id=draft_id,
                    flag_type=DraftFlagType(f["type"]),
                    severity=DraftFlagSeverity(f["severity"]),
                    message=f["message"],
                    affected_date=f.get("date"),
                    acknowledged_at=f.get("acknowledged_at"),
                    created_at=f.get("created_at", datetime.utcnow()),
                )
            )

    return DraftPreviewResponse(
        draft_id=draft_id,
        add_count=result.add_count,
        modify_count=result.modify_count,
        delete_count=result.delete_count,
        flags_total=result.flags_total,
        flags_acknowledged=result.flags_acknowledged,
        acgme_violations=result.acgme_violations or [],
        assignments=assignment_responses,
        flags=flag_responses,
    )


@router.post(
    "/{draft_id}/assignments",
    response_model=dict,
    status_code=201,
    summary="Add assignment to draft",
    description="Add a new assignment to an existing draft.",
)
async def add_assignment(
    draft_id: UUID,
    request: DraftAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Add an assignment to a draft.

    Can be used for adding new assignments, modifying existing ones,
    or marking assignments for deletion.
    """
    service = ScheduleDraftService(db)
    assignment_id = await service.add_assignment_to_draft(
        draft_id=draft_id,
        person_id=request.person_id,
        assignment_date=request.assignment_date,
        time_of_day=request.time_of_day,
        activity_code=request.activity_code,
        rotation_id=request.rotation_id,
        change_type=request.change_type,
        existing_assignment_id=request.existing_assignment_id,
    )

    if not assignment_id:
        raise HTTPException(
            status_code=400,
            detail={"error": "Failed to add assignment to draft"},
        )

    return {
        "success": True,
        "assignment_id": str(assignment_id),
        "message": "Assignment added to draft",
    }


@router.post(
    "/{draft_id}/flags/{flag_id}/acknowledge",
    response_model=dict,
    summary="Acknowledge flag",
    description="Acknowledge a review flag on a draft.",
)
async def acknowledge_flag(
    draft_id: UUID,
    flag_id: UUID,
    request: DraftFlagAcknowledge | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Acknowledge a flag on a draft.

    Tier 1 users must acknowledge all flags before publishing,
    or provide an override comment.
    """
    service = ScheduleDraftService(db)
    success = await service.acknowledge_flag(
        flag_id=flag_id,
        acknowledged_by_id=current_user.id,
        resolution_note=request.resolution_note if request else None,
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail={"error": "Flag not found or already acknowledged"},
        )

    return {
        "success": True,
        "flag_id": str(flag_id),
        "message": "Flag acknowledged",
    }


@router.post(
    "/{draft_id}/flags/acknowledge",
    response_model=dict,
    summary="Bulk acknowledge flags",
    description="Acknowledge multiple flags at once.",
)
async def bulk_acknowledge_flags(
    draft_id: UUID,
    request: DraftFlagBulkAcknowledge,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Acknowledge multiple flags on a draft.

    Useful for acknowledging all warnings at once before publish.
    """
    service = ScheduleDraftService(db)
    acknowledged_count = 0
    failed_ids = []

    for flag_id in request.flag_ids:
        success = await service.acknowledge_flag(
            flag_id=flag_id,
            acknowledged_by_id=current_user.id,
            resolution_note=request.resolution_note,
        )
        if success:
            acknowledged_count += 1
        else:
            failed_ids.append(str(flag_id))

    return {
        "success": len(failed_ids) == 0,
        "acknowledged_count": acknowledged_count,
        "failed_count": len(failed_ids),
        "failed_ids": failed_ids,
    }


@router.post(
    "/{draft_id}/publish",
    response_model=PublishResponse,
    summary="Publish draft",
    description="Publish draft to live assignments table.",
)
async def publish_draft(
    draft_id: UUID,
    request: PublishRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Publish a draft to the live assignments table.

    Commits all staged assignments. Tier 1 users must acknowledge
    all flags or provide an override comment. Tier 2 users can
    override without acknowledgment.
    """
    if request is None:
        request = PublishRequest()

    service = ScheduleDraftService(db)
    result = await service.publish_draft(
        draft_id=draft_id,
        published_by_id=current_user.id,
        override_comment=request.override_comment,
        validate_acgme=request.validate_acgme,
    )

    if not result.success and result.error_code:
        if result.error_code == "DRAFT_NOT_FOUND":
            raise HTTPException(status_code=404, detail="Draft not found")
        raise HTTPException(
            status_code=400,
            detail={
                "error": result.message,
                "error_code": result.error_code,
            },
        )

    # Convert error dicts to PublishError objects
    error_responses = []
    if result.errors:
        from app.schemas.schedule_draft import PublishError

        for err in result.errors:
            error_responses.append(
                PublishError(
                    draft_assignment_id=UUID(err["draft_assignment_id"]),
                    person_id=UUID(err["person_id"]),
                    assignment_date=date.fromisoformat(err["date"]),
                    error_message=err["error"],
                )
            )

    return PublishResponse(
        draft_id=result.draft_id,
        status=result.status,
        published_count=result.published_count,
        error_count=result.error_count,
        errors=error_responses,
        acgme_warnings=result.acgme_warnings or [],
        rollback_available=result.rollback_available,
        rollback_expires_at=result.rollback_expires_at,
        message=result.message,
    )


@router.post(
    "/{draft_id}/rollback",
    response_model=RollbackResponse,
    summary="Rollback draft",
    description="Rollback a published draft within the 24-hour window.",
)
async def rollback_draft(
    draft_id: UUID,
    request: RollbackRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Rollback a published draft.

    Deletes all assignments created by this draft. Only available
    within 24 hours of publish.
    """
    service = ScheduleDraftService(db)
    result = await service.rollback_draft(
        draft_id=draft_id,
        rolled_back_by_id=current_user.id,
    )

    if not result.success and result.error_code:
        if result.error_code == "DRAFT_NOT_FOUND":
            raise HTTPException(status_code=404, detail="Draft not found")
        raise HTTPException(
            status_code=400,
            detail={
                "error": result.message,
                "error_code": result.error_code,
            },
        )

    return RollbackResponse(
        draft_id=result.draft_id,
        status=result.status,
        rolled_back_count=result.rolled_back_count,
        failed_count=result.failed_count,
        rolled_back_at=datetime.utcnow(),
        rolled_back_by_id=current_user.id,
        errors=result.errors or [],
        message=result.message,
    )


@router.delete(
    "/{draft_id}",
    status_code=204,
    summary="Discard draft",
    description="Discard a draft without publishing.",
)
async def discard_draft(
    draft_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Discard a draft without publishing.

    Marks the draft as discarded. Cannot discard published drafts.
    """
    service = ScheduleDraftService(db)
    success = await service.discard_draft(draft_id)

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Cannot discard draft. It may not exist or is already published.",
        )

    return None  # 204 No Content
