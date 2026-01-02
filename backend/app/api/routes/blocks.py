"""Block API routes.

Thin routing layer that connects URL paths to controllers.
All business logic is in the service layer.

Note: GET endpoints are public (no authentication required) as block data
is not sensitive - it contains only date ranges and block numbers. This allows
the frontend to display schedule views before user login.
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
):
    """List blocks, optionally filtered by date range or block number.

    This endpoint is public (no authentication required) as block data
    is not sensitive - it contains only date ranges and block numbers.
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
):
    """Get a block by ID.

    This endpoint is public (no authentication required) as block data
    is not sensitive - it contains only date ranges and block numbers.
    """
    controller = BlockController(db)
    return controller.get_block(block_id)


@router.post("", response_model=BlockResponse, status_code=201)
async def create_block(
    block_in: BlockCreate,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new block. Requires authentication."""
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
    """Delete a block. Requires authentication."""
    controller = BlockController(db)
    await controller.delete_block(block_id)
