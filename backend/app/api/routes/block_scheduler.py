"""Block scheduler API routes.

Endpoints for leave-eligible rotation scheduling:
- Dashboard view for block scheduler UI
- Schedule/preview block assignments
- CRUD operations for manual assignments
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.controllers.block_scheduler_controller import BlockSchedulerController
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.block_assignment import (
    BlockAssignmentCreate,
    BlockAssignmentResponse,
    BlockAssignmentUpdate,
    BlockScheduleRequest,
    BlockScheduleResponse,
    BlockSchedulerDashboard,
)
from app.websocket.manager import broadcast_schedule_updated

router = APIRouter()


@router.get(
    "/dashboard",
    response_model=BlockSchedulerDashboard,
    summary="Get block scheduler dashboard",
    description="""
    Get dashboard view for the block scheduler UI.

    Shows:
    - Residents with leave in the block
    - Rotation capacities (leave-eligible and non-leave-eligible)
    - Current assignments
    - Unassigned residents
    """,
)
def get_dashboard(
    block_number: int = Query(..., ge=0, le=13, description="Academic block (0-13)"),
    academic_year: int = Query(..., ge=2020, le=2100, description="Academic year"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get dashboard for block scheduler."""
    controller = BlockSchedulerController(db)
    return controller.get_dashboard(block_number, academic_year)


@router.post(
    "/schedule",
    response_model=BlockScheduleResponse,
    summary="Schedule block assignments",
    description="""
    Schedule residents for a block using leave-eligible matching algorithm.

    **Algorithm:**
    1. Residents with approved leave → leave-eligible rotations
    2. Remaining residents → coverage needs first, then balanced distribution
    3. Coverage gaps identified for non-leave-eligible rotations

    **Options:**
    - `dry_run=True`: Preview assignments without saving (default)
    - `dry_run=False`: Save assignments to database
    - `include_all_residents=True`: Schedule all residents (default)
    - `include_all_residents=False`: Only schedule residents with leave
    """,
)
async def schedule_block(
    request: BlockScheduleRequest,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Schedule residents for a block."""
    controller = BlockSchedulerController(db)
    result = controller.schedule_block(request, created_by=current_user.email)

    # Broadcast WebSocket event if assignments were saved (not dry run)
    if not request.dry_run and result.assignments:
        await broadcast_schedule_updated(
            schedule_id=None,
            academic_year_id=None,
            user_id=current_user.id,
            update_type="generated",
            affected_blocks_count=len(result.assignments),
            message=f"Block {request.block_number} scheduled with {len(result.assignments)} assignments",
        )

    return result


@router.get(
    "/assignments/{assignment_id}",
    response_model=BlockAssignmentResponse,
    summary="Get block assignment",
)
async def get_assignment(
    assignment_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a single block assignment by ID."""
    controller = BlockSchedulerController(db)
    return controller.get_assignment(assignment_id)


@router.post(
    "/assignments",
    response_model=BlockAssignmentResponse,
    status_code=201,
    summary="Create manual assignment",
    description="""
    Create a manual block assignment.

    Use this for overriding auto-scheduled assignments or
    manually assigning residents to specific rotations.
    """,
)
async def create_assignment(
    assignment_in: BlockAssignmentCreate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a manual block assignment."""
    # Set created_by if not provided
    if not assignment_in.created_by:
        assignment_in.created_by = current_user.email

    controller = BlockSchedulerController(db)
    result = controller.create_assignment(assignment_in)

    # Broadcast WebSocket event
    await broadcast_schedule_updated(
        schedule_id=None,
        academic_year_id=None,
        user_id=current_user.id,
        update_type="modified",
        affected_blocks_count=1,
        message=f"Block assignment created for block {assignment_in.block_number}",
    )

    return result


@router.put(
    "/assignments/{assignment_id}",
    response_model=BlockAssignmentResponse,
    summary="Update block assignment",
)
async def update_assignment(
    assignment_id: UUID,
    assignment_in: BlockAssignmentUpdate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a block assignment."""
    controller = BlockSchedulerController(db)
    result = controller.update_assignment(assignment_id, assignment_in)

    # Broadcast WebSocket event
    await broadcast_schedule_updated(
        schedule_id=None,
        academic_year_id=None,
        user_id=current_user.id,
        update_type="modified",
        affected_blocks_count=1,
        message="Block assignment updated",
    )

    return result


@router.delete(
    "/assignments/{assignment_id}",
    status_code=204,
    summary="Delete block assignment",
)
async def delete_assignment(
    assignment_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a block assignment."""
    controller = BlockSchedulerController(db)
    controller.delete_assignment(assignment_id)

    # Broadcast WebSocket event
    await broadcast_schedule_updated(
        schedule_id=None,
        academic_year_id=None,
        user_id=current_user.id,
        update_type="modified",
        affected_blocks_count=1,
        message="Block assignment deleted",
    )
