"""
API routes for FMIT swap management.

Provides endpoints for:
- Executing swaps
- Getting swap history
- Rolling back swaps
- Validating proposed swaps
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
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

router = APIRouter(prefix="/swaps", tags=["swaps"])


@router.post("/execute", response_model=SwapExecuteResponse)
def execute_swap(
    request: SwapExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Execute an FMIT swap between two faculty members.

    Validates the swap first, then executes if valid.
    """
    # Validate the swap
    validator = SwapValidationService(db)
    validation = validator.validate_swap(
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
    result = executor.execute_swap(
        source_faculty_id=request.source_faculty_id,
        source_week=request.source_week,
        target_faculty_id=request.target_faculty_id,
        target_week=request.target_week,
        swap_type=request.swap_type.value,
        reason=request.reason,
        executed_by_id=current_user.id,
    )

    return SwapExecuteResponse(
        success=result.success,
        swap_id=result.swap_id,
        message=result.message,
        validation=validation_result,
    )


@router.post("/validate", response_model=SwapValidationResult)
def validate_swap(
    request: SwapExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Validate a proposed swap without executing it.

    Use this to check if a swap is possible before attempting execution.
    """
    validator = SwapValidationService(db)
    validation = validator.validate_swap(
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
def get_swap_history(
    faculty_id: UUID | None = None,
    status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get swap history with optional filters.

    Filters:
    - faculty_id: Filter by source or target faculty
    - status: Filter by swap status (pending, executed, rolled_back, etc.)
    - start_date: Filter swaps with source_week >= start_date
    - end_date: Filter swaps with source_week <= end_date
    """
    query = db.query(SwapRecord)

    # Filter by faculty (source or target)
    if faculty_id:
        query = query.filter(
            (SwapRecord.source_faculty_id == faculty_id)
            | (SwapRecord.target_faculty_id == faculty_id)
        )

    # Filter by status
    if status:
        query = query.filter(SwapRecord.status == status)

    # Filter by date range (using source_week)
    if start_date:
        query = query.filter(SwapRecord.source_week >= start_date)
    if end_date:
        query = query.filter(SwapRecord.source_week <= end_date)

    # Order by most recent first
    query = query.order_by(SwapRecord.requested_at.desc())

    # Get total count for pagination
    total = query.count()

    # Apply pagination
    swaps = query.offset((page - 1) * page_size).limit(page_size).all()

    # Build response items
    items = []
    for swap in swaps:
        items.append(
            SwapRecordResponse(
                id=swap.id,
                source_faculty_id=swap.source_faculty_id,
                source_faculty_name=swap.source_faculty.name
                if swap.source_faculty
                else "Unknown",
                source_week=swap.source_week,
                target_faculty_id=swap.target_faculty_id,
                target_faculty_name=swap.target_faculty.name
                if swap.target_faculty
                else "Unknown",
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
def get_swap(
    swap_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific swap record by ID.

    Returns detailed information about a single swap including:
    - Source and target faculty names
    - Swap dates and type
    - Status and execution times
    - Reason for the swap
    """
    swap = db.query(SwapRecord).filter(SwapRecord.id == swap_id).first()

    if not swap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Swap with ID {swap_id} not found",
        )

    return SwapRecordResponse(
        id=swap.id,
        source_faculty_id=swap.source_faculty_id,
        source_faculty_name=swap.source_faculty.name
        if swap.source_faculty
        else "Unknown",
        source_week=swap.source_week,
        target_faculty_id=swap.target_faculty_id,
        target_faculty_name=swap.target_faculty.name
        if swap.target_faculty
        else "Unknown",
        target_week=swap.target_week,
        swap_type=swap.swap_type,
        status=swap.status,
        reason=swap.reason,
        requested_at=swap.requested_at,
        executed_at=swap.executed_at,
    )


@router.post("/{swap_id}/rollback")
def rollback_swap(
    swap_id: UUID,
    request: SwapRollbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Rollback an executed swap within the allowed window.

    Only swaps executed within the last 24 hours can be rolled back.
    """
    executor = SwapExecutor(db)

    if not executor.can_rollback(swap_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Swap cannot be rolled back (either not found, already rolled back, or outside rollback window)",
        )

    result = executor.rollback_swap(
        swap_id=swap_id,
        reason=request.reason,
        rolled_back_by_id=current_user.id,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message,
        )

    return {"message": result.message, "success": True}
