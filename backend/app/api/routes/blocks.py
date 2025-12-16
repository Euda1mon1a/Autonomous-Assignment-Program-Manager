"""Block API routes.

Thin routing layer that connects URL paths to controllers.
All business logic is in the service layer.
"""

from datetime import date
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query

from app.db.session import get_db
from app.schemas.block import BlockCreate, BlockResponse, BlockListResponse
from app.controllers.block_controller import BlockController

router = APIRouter()


@router.get("", response_model=BlockListResponse)
def list_blocks(
    start_date: Optional[date] = Query(None, description="Filter blocks from this date"),
    end_date: Optional[date] = Query(None, description="Filter blocks until this date"),
    block_number: Optional[int] = Query(None, description="Filter by academic block number"),
    db=Depends(get_db),
):
    """List blocks, optionally filtered by date range or block number."""
    controller = BlockController(db)
    return controller.list_blocks(
        start_date=start_date,
        end_date=end_date,
        block_number=block_number,
    )


@router.get("/{block_id}", response_model=BlockResponse)
def get_block(
    block_id: UUID,
    db=Depends(get_db),
):
    """Get a block by ID."""
    controller = BlockController(db)
    return controller.get_block(block_id)


@router.post("", response_model=BlockResponse, status_code=201)
def create_block(
    block_in: BlockCreate,
    db=Depends(get_db),
):
    """Create a new block."""
    controller = BlockController(db)
    return controller.create_block(block_in)


@router.post("/generate", response_model=BlockListResponse)
def generate_blocks(
    start_date: date,
    end_date: date,
    base_block_number: int = Query(1, description="Starting block number"),
    db=Depends(get_db),
):
    """
    Generate blocks for a date range.

    Creates AM and PM blocks for each day (730 blocks per year).
    """
    controller = BlockController(db)
    return controller.generate_blocks(
        start_date=start_date,
        end_date=end_date,
        base_block_number=base_block_number,
    )


@router.delete("/{block_id}", status_code=204)
def delete_block(
    block_id: UUID,
    db=Depends(get_db),
):
    """Delete a block."""
    controller = BlockController(db)
    controller.delete_block(block_id)
