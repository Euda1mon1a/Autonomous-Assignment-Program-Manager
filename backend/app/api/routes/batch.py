"""Batch operations API routes.

Provides endpoints for bulk assignment operations:
- Batch create (up to 1000 assignments)
- Batch update (up to 1000 assignments)
- Batch delete (up to 1000 assignments)
- Status tracking for long-running operations
"""
import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user, get_scheduler_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.batch import (
    BatchCreateRequest,
    BatchDeleteRequest,
    BatchResponse,
    BatchStatusResponse,
    BatchUpdateRequest,
)
from app.services.batch import BatchService

router = APIRouter()


@router.post("/create", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def batch_create_assignments(
    request: BatchCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_scheduler_user),
):
    """
    Create multiple assignments in a single batch operation.

    Features:
    - Create up to 1000 assignments at once
    - Dry-run mode for validation without creating
    - ACGME compliance validation
    - Rollback on error (all or nothing)
    - Progress tracking via operation ID

    Args:
        request: Batch create request with list of assignments
        db: Database session
        current_user: Current authenticated user (requires scheduler role)

    Returns:
        BatchResponse with operation ID and results

    Raises:
        HTTPException: 400 if validation fails, 403 if unauthorized

    Example:
        ```json
        {
          "assignments": [
            {
              "block_id": "uuid",
              "person_id": "uuid",
              "role": "primary",
              "rotation_template_id": "uuid"
            },
            ...
          ],
          "dry_run": false,
          "rollback_on_error": true,
          "validate_acgme": true
        }
        ```
    """
    service = BatchService(db)

    # Set created_by from current user
    if not request.created_by:
        request.created_by = current_user.email or current_user.username

    response = await service.create_batch(request, created_by=request.created_by)

    # If all operations failed, return 400
    if response.status == "failed" and not request.dry_run:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Batch create operation failed",
                "operation_id": str(response.operation_id),
                "errors": response.errors,
                "results": [r.dict() for r in response.results],
            },
        )

    return response


@router.put("/update", response_model=BatchResponse)
async def batch_update_assignments(
    request: BatchUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_scheduler_user),
):
    """
    Update multiple assignments in a single batch operation.

    Features:
    - Update up to 1000 assignments at once
    - Dry-run mode for validation without updating
    - Optimistic locking (requires updated_at timestamp)
    - ACGME compliance validation
    - Rollback on error (all or nothing)

    Args:
        request: Batch update request with list of assignments
        db: Database session
        current_user: Current authenticated user (requires scheduler role)

    Returns:
        BatchResponse with operation ID and results

    Raises:
        HTTPException: 400 if validation fails, 403 if unauthorized

    Example:
        ```json
        {
          "assignments": [
            {
              "assignment_id": "uuid",
              "role": "supervising",
              "notes": "Updated notes",
              "updated_at": "2024-01-01T00:00:00Z"
            },
            ...
          ],
          "dry_run": false,
          "rollback_on_error": true
        }
        ```
    """
    service = BatchService(db)
    response = await service.update_batch(request)

    # If all operations failed, return 400
    if response.status == "failed" and not request.dry_run:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Batch update operation failed",
                "operation_id": str(response.operation_id),
                "errors": response.errors,
                "results": [r.dict() for r in response.results],
            },
        )

    return response


@router.delete("/delete", response_model=BatchResponse)
async def batch_delete_assignments(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_scheduler_user),
):
    """
    Delete multiple assignments in a single batch operation.

    Features:
    - Delete up to 1000 assignments at once
    - Soft delete option (mark as deleted without removing)
    - Dry-run mode for validation without deleting
    - Rollback on error (all or nothing)

    Args:
        request: Batch delete request with list of assignments
        db: Database session
        current_user: Current authenticated user (requires scheduler role)

    Returns:
        BatchResponse with operation ID and results

    Raises:
        HTTPException: 400 if validation fails, 403 if unauthorized

    Example:
        ```json
        {
          "assignments": [
            {
              "assignment_id": "uuid",
              "soft_delete": false
            },
            ...
          ],
          "dry_run": false,
          "rollback_on_error": true
        }
        ```
    """
    service = BatchService(db)
    response = await service.delete_batch(request)

    # If all operations failed, return 400
    if response.status == "failed" and not request.dry_run:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Batch delete operation failed",
                "operation_id": str(response.operation_id),
                "errors": response.errors,
                "results": [r.dict() for r in response.results],
            },
        )

    return response


@router.get("/status/{operation_id}", response_model=BatchStatusResponse)
async def get_batch_status(
    operation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get the status of a batch operation.

    Provides real-time progress tracking for long-running batch operations.

    Args:
        operation_id: UUID of the batch operation
        db: Database session
        current_user: Current authenticated user

    Returns:
        BatchStatusResponse with current status and progress

    Raises:
        HTTPException: 404 if operation not found

    Example response:
        ```json
        {
          "operation_id": "uuid",
          "operation_type": "create",
          "status": "processing",
          "total": 1000,
          "succeeded": 750,
          "failed": 0,
          "progress_percentage": 75.0,
          "created_at": "2024-01-01T00:00:00Z",
          "estimated_completion": "2024-01-01T00:01:00Z"
        }
        ```
    """
    service = BatchService(db)
    status_response = service.get_batch_status(operation_id)

    if not status_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch operation not found: {operation_id}",
        )

    return status_response
