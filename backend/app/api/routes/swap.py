"""
API routes for FMIT swap management.

Provides endpoints for:
- Executing swaps
- Getting swap history
- Rolling back swaps
- Validating proposed swaps
"""
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.swap_validation import SwapValidationService
from app.services.swap_executor import SwapExecutor
from app.schemas.swap import (
    SwapExecuteRequest,
    SwapExecuteResponse,
    SwapValidationResult,
    SwapHistoryFilter,
    SwapHistoryResponse,
    SwapRecordResponse,
    SwapRollbackRequest,
)

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
    faculty_id: Optional[UUID] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get swap history with optional filters.
    """
    # TODO: Implement when SwapRecord queries are available
    # For now, return empty response
    return SwapHistoryResponse(
        items=[],
        total=0,
        page=page,
        page_size=page_size,
        pages=0,
    )


@router.get("/{swap_id}", response_model=SwapRecordResponse)
def get_swap(
    swap_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific swap record by ID."""
    # TODO: Implement when SwapRecord model is queryable
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Swap not found",
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
