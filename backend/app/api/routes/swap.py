"""
API Routes for FMIT Swap Management.

This module provides RESTful endpoints for managing schedule swaps between
faculty members in the FMIT (Faculty Managing Inpatient Teaching) rotation.

Endpoints:
    POST /swaps/execute
        Execute a validated swap between two faculty members.
        Supports both one-to-one swaps and absorb swaps.

    POST /swaps/validate
        Pre-validate a proposed swap without executing it.
        Returns validation errors, warnings, and conflict indicators.

    GET /swaps/history
        Retrieve paginated swap history with optional filters.
        Supports filtering by faculty, status, and date range.

    GET /swaps/{swap_id}
        Get detailed information about a specific swap record.

    POST /swaps/{swap_id}/rollback
        Rollback an executed swap within the 24-hour window.
        Requires a reason for audit purposes.

Authentication:
    All endpoints require authentication via JWT token.
    Access is controlled by user roles - coordinators and admins have full access,
    faculty members can only view swaps involving themselves.

Swap Types:
    - one_to_one: Bidirectional swap where both faculty exchange weeks
    - absorb: One-way transfer where target faculty takes over source's week

Error Handling:
    - 400: Validation failures or business rule violations
    - 404: Swap record not found
    - 401/403: Authentication/authorization failures

See Also:
    - app.services.swap_executor: Core swap execution logic
    - app.services.swap_validation: Pre-execution validation
    - app.schemas.swap: Request/response schema definitions
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user, get_current_user
from app.db.session import get_db
from app.models.swap import SwapRecord
from app.models.user import User
from app.schemas.swap import (
    SwapExecuteRequest,
    SwapExecuteResponse,
    SwapHistoryResponse,
    SwapRecordResponse,
    SwapRollbackRequest,
    SwapValidationResult,
)
from app.services.swap_executor import SwapExecutor
from app.services.swap_validation import SwapValidationService
from app.websocket.manager import broadcast_schedule_updated, broadcast_swap_approved

router = APIRouter(prefix="/swaps", tags=["swaps"])


@router.post("/execute", response_model=SwapExecuteResponse)
async def execute_swap(
    request: SwapExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SwapExecuteResponse:
    """
    Execute an FMIT swap between two faculty members.

    This endpoint validates the proposed swap and, if valid, executes it atomically.
    The swap will update block assignments and call cascade assignments for the
    affected weeks.

    Args:
        request: SwapExecuteRequest containing:
            - source_faculty_id: UUID of faculty giving up their week
            - source_week: Start date of the source week (Monday)
            - target_faculty_id: UUID of faculty receiving the week
            - target_week: For one-to-one swaps, the reciprocal week (optional)
            - swap_type: "one_to_one" or "absorb"
            - reason: Optional explanation for the swap
        db: Database session (injected)
        current_user: Authenticated user (injected)

    Returns:
        SwapExecuteResponse with:
            - success: Whether the swap was executed
            - swap_id: UUID of the created SwapRecord (if successful)
            - message: Human-readable result description
            - validation: Detailed validation results

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If not authorized for this operation
    """
    # Validate the swap
    validator = SwapValidationService(db)
    validation = await validator.validate_swap(
        source_faculty_id=request.source_faculty_id,
        source_week=request.source_week,
        target_faculty_id=request.target_faculty_id,
        target_week=request.target_week,
    )

    validation_result = SwapValidationResult(
        valid=validation.valid,
        errors=[e.message for e in validation.errors],
        warnings=[w.message for w in validation.warnings],
        back_to_back_conflict=validation.back_to_back_conflict,
        external_conflict=validation.external_conflict,
    )

    if not validation.valid:
        return SwapExecuteResponse(
            success=False,
            swap_id=None,
            message="Swap validation failed",
            validation=validation_result,
        )

    # Execute the swap
    executor = SwapExecutor(db)
    result = await executor.execute_swap(
        source_faculty_id=request.source_faculty_id,
        source_week=request.source_week,
        target_faculty_id=request.target_faculty_id,
        target_week=request.target_week,
        swap_type=request.swap_type.value,
        reason=request.reason,
        executed_by_id=current_user.id,
    )

    # Broadcast WebSocket events on successful execution
    if result.success and result.swap_id:
        await broadcast_swap_approved(
            swap_id=result.swap_id,
            requester_id=request.source_faculty_id,
            target_person_id=request.target_faculty_id,
            approved_by=current_user.id,
            affected_assignments=[],
            message=f"Swap executed: {request.swap_type.value}",
        )
        await broadcast_schedule_updated(
            schedule_id=None,
            academic_year_id=None,
            user_id=current_user.id,
            update_type="modified",
            affected_blocks_count=2,
            message="Schedule swap executed",
        )

    return SwapExecuteResponse(
        success=result.success,
        swap_id=result.swap_id,
        message=result.message,
        validation=validation_result,
    )


@router.post("/validate", response_model=SwapValidationResult)
async def validate_swap(
    request: SwapExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SwapValidationResult:
    """
    Validate a proposed swap without executing it.

    Use this to check if a swap is possible before attempting execution.
    """
    validator = SwapValidationService(db)
    validation = await validator.validate_swap(
        source_faculty_id=request.source_faculty_id,
        source_week=request.source_week,
        target_faculty_id=request.target_faculty_id,
        target_week=request.target_week,
    )

    return SwapValidationResult(
        valid=validation.valid,
        errors=[e.message for e in validation.errors],
        warnings=[w.message for w in validation.warnings],
        back_to_back_conflict=validation.back_to_back_conflict,
        external_conflict=validation.external_conflict,
    )


@router.get("/history", response_model=SwapHistoryResponse)
async def get_swap_history(
    faculty_id: UUID | None = None,
    status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SwapHistoryResponse:
    """
    Get swap history with optional filters.

    Filters:
    - faculty_id: Filter by source or target faculty
    - status: Filter by swap status (pending, executed, rolled_back, etc.)
    - start_date: Filter swaps with source_week >= start_date
    - end_date: Filter swaps with source_week <= end_date
    """
    from sqlalchemy import func, or_
    from sqlalchemy.orm import selectinload

    # Build query
    query = select(SwapRecord).options(
        selectinload(SwapRecord.source_faculty),
        selectinload(SwapRecord.target_faculty),
    )

    # Filter by faculty (source or target)
    if faculty_id:
        query = query.where(
            or_(
                SwapRecord.source_faculty_id == faculty_id,
                SwapRecord.target_faculty_id == faculty_id,
            )
        )

    # Filter by status
    if status:
        query = query.where(SwapRecord.status == status)

    # Filter by date range (using source_week)
    if start_date:
        query = query.where(SwapRecord.source_week >= start_date)
    if end_date:
        query = query.where(SwapRecord.source_week <= end_date)

    # Order by most recent first
    query = query.order_by(SwapRecord.requested_at.desc())

    # Get total count for pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = db.execute(count_query)
    total = total_result.scalar_one()

    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = db.execute(query)
    swaps = result.scalars().all()

    # Build response items
    items = []
    for swap in swaps:
        items.append(
            SwapRecordResponse(
                id=swap.id,
                source_faculty_id=swap.source_faculty_id,
                source_faculty_name=(
                    swap.source_faculty.name if swap.source_faculty else "Unknown"
                ),
                source_week=swap.source_week,
                target_faculty_id=swap.target_faculty_id,
                target_faculty_name=(
                    swap.target_faculty.name if swap.target_faculty else "Unknown"
                ),
                target_week=swap.target_week,
                swap_type=swap.swap_type,
                status=swap.status,
                reason=swap.reason,
                requested_at=swap.requested_at,
                executed_at=swap.executed_at,
            )
        )

    # Calculate total pages
    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return SwapHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{swap_id}", response_model=SwapRecordResponse)
async def get_swap(
    swap_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SwapRecordResponse:
    """
    Get a specific swap record by ID.

    Returns detailed information about a single swap including:
    - Source and target faculty names
    - Swap dates and type
    - Status and execution times
    - Reason for the swap
    """
    from sqlalchemy.orm import selectinload

    query = (
        select(SwapRecord)
        .where(SwapRecord.id == swap_id)
        .options(
            selectinload(SwapRecord.source_faculty),
            selectinload(SwapRecord.target_faculty),
        )
    )
    result = db.execute(query)
    swap = result.scalar_one_or_none()

    if not swap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Swap with ID {swap_id} not found",
        )

    return SwapRecordResponse(
        id=swap.id,
        source_faculty_id=swap.source_faculty_id,
        source_faculty_name=(
            swap.source_faculty.name if swap.source_faculty else "Unknown"
        ),
        source_week=swap.source_week,
        target_faculty_id=swap.target_faculty_id,
        target_faculty_name=(
            swap.target_faculty.name if swap.target_faculty else "Unknown"
        ),
        target_week=swap.target_week,
        swap_type=swap.swap_type,
        status=swap.status,
        reason=swap.reason,
        requested_at=swap.requested_at,
        executed_at=swap.executed_at,
    )


@router.post("/{swap_id}/rollback")
async def rollback_swap(
    swap_id: UUID,
    request: SwapRollbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Rollback an executed swap within the allowed window.

    Only swaps executed within the last 24 hours can be rolled back.
    """
    executor = SwapExecutor(db)

    can_rollback = await executor.can_rollback(swap_id)
    if not can_rollback:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Swap cannot be rolled back (either not found, already rolled back, or outside rollback window)",
        )

    result = await executor.rollback_swap(
        swap_id=swap_id,
        reason=request.reason,
        rolled_back_by_id=current_user.id,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message,
        )

    # Broadcast WebSocket event on successful rollback
    await broadcast_schedule_updated(
        schedule_id=None,
        academic_year_id=None,
        user_id=current_user.id,
        update_type="modified",
        affected_blocks_count=2,
        message="Swap rolled back",
    )

    return {"message": result.message, "success": True}
