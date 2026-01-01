"""Block API routes.

Thin routing layer that connects URL paths to controllers.
All business logic is in the service layer.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.controllers.block_controller import BlockController
from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.block import BlockCreate, BlockListResponse, BlockResponse

router = APIRouter()


@router.get("", response_model=BlockListResponse)
async def list_blocks(
    start_date: date | None = Query(None, description="Filter blocks from this date"),
    end_date: date | None = Query(None, description="Filter blocks until this date"),
    block_number: int | None = Query(
        None, description="Filter by academic block number"
    ),
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """List schedule blocks with optional filtering.

    Args:
        start_date: Filter blocks starting on or after this date.
        end_date: Filter blocks ending on or before this date.
        block_number: Filter by specific academic block number (1-730).
        db: Database session.
        current_user: Authenticated user.

    Returns:
        BlockListResponse with list of blocks and total count.

    Security:
        Requires authentication.

    Note:
        Blocks are the fundamental time unit in the scheduling system.
        Each day has 2 blocks (AM/PM), resulting in 730 blocks per academic year.
        Block numbers increment sequentially throughout the year.

    Example Queries:
        - All blocks for a specific day: start_date=2024-01-15&end_date=2024-01-15
        - Blocks for a week: start_date=2024-01-15&end_date=2024-01-21
        - Specific block: block_number=42

    Status Codes:
        - 200: Blocks retrieved successfully
    """
    controller = BlockController(db)
    return controller.list_blocks(
        start_date=start_date,
        end_date=end_date,
        block_number=block_number,
    )


@router.get("/{block_id}", response_model=BlockResponse)
async def get_block(
    block_id: UUID,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a schedule block by ID.

    Args:
        block_id: UUID of the block to retrieve.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        BlockResponse with block details including:
        - Date
        - Session (AM or PM)
        - Block number
        - Associated assignments (if any)

    Security:
        Requires authentication.

    Note:
        Blocks are pre-generated for the entire academic year.
        Use this endpoint to retrieve detailed information about a specific block.

    Raises:
        HTTPException: 404 if block not found.

    Status Codes:
        - 200: Block retrieved successfully
        - 404: Block not found
    """
    controller = BlockController(db)
    return controller.get_block(block_id)


@router.post("", response_model=BlockResponse, status_code=201)
async def create_block(
    block_in: BlockCreate,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new schedule block.

    Args:
        block_in: Block creation payload (date, session, block_number).
        db: Database session.
        current_user: Authenticated user.

    Returns:
        BlockResponse with created block details.

    Security:
        Requires authentication.

    Note:
        Manually creating individual blocks is uncommon.
        Use POST /blocks/generate to create blocks for an entire date range.

        Block requirements:
        - date: Valid date within academic year
        - session: 'AM' or 'PM'
        - block_number: Sequential number (1-730 for full year)

    Raises:
        HTTPException:
            - 400: Invalid block data (e.g., invalid session type)
            - 409: Block already exists for this date/session combination

    Status Codes:
        - 201: Block created successfully
        - 400: Invalid block data
        - 409: Duplicate block
    """
    controller = BlockController(db)
    return controller.create_block(block_in)


@router.post("/generate", response_model=BlockListResponse)
async def generate_blocks(
    start_date: date,
    end_date: date,
    base_block_number: int = Query(1, description="Starting block number"),
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate blocks for a date range. Requires authentication.

    Creates AM and PM blocks for each day (730 blocks per year).
    """
    controller = BlockController(db)
    return controller.generate_blocks(
        start_date=start_date,
        end_date=end_date,
        base_block_number=base_block_number,
    )


@router.delete("/{block_id}", status_code=204)
async def delete_block(
    block_id: UUID,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a schedule block.

    Args:
        block_id: UUID of the block to delete.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        No content (204).

    Security:
        Requires authentication.

    Warning:
        Deleting a block will cascade delete all assignments associated with it.
        This operation cannot be undone.

    Note:
        Only delete blocks if:
        - They were created in error
        - The academic year is being reconfigured
        - You're clearing out test data

        For production schedules, consider deleting assignments instead
        of blocks to preserve the time structure.

    Raises:
        HTTPException:
            - 404: Block not found
            - 409: Cannot delete block with active assignments (if cascade disabled)

    Status Codes:
        - 204: Block deleted successfully
        - 404: Block not found
        - 409: Conflict (active assignments exist)
    """
    controller = BlockController(db)
    controller.delete_block(block_id)
