"""Block API routes."""
from datetime import date
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.block import Block
from app.schemas.block import BlockCreate, BlockResponse, BlockListResponse

router = APIRouter()


@router.get("", response_model=BlockListResponse)
def list_blocks(
    start_date: Optional[date] = Query(None, description="Filter blocks from this date"),
    end_date: Optional[date] = Query(None, description="Filter blocks until this date"),
    block_number: Optional[int] = Query(None, description="Filter by academic block number"),
    db: Session = Depends(get_db),
):
    """List blocks, optionally filtered by date range or block number."""
    query = db.query(Block)

    if start_date:
        query = query.filter(Block.date >= start_date)
    if end_date:
        query = query.filter(Block.date <= end_date)
    if block_number is not None:
        query = query.filter(Block.block_number == block_number)

    blocks = query.order_by(Block.date, Block.time_of_day).all()
    return BlockListResponse(items=blocks, total=len(blocks))


@router.get("/{block_id}", response_model=BlockResponse)
def get_block(block_id: UUID, db: Session = Depends(get_db)):
    """Get a block by ID."""
    block = db.query(Block).filter(Block.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    return block


@router.post("", response_model=BlockResponse, status_code=201)
def create_block(block_in: BlockCreate, db: Session = Depends(get_db)):
    """Create a new block."""
    # Check for duplicate
    existing = db.query(Block).filter(
        Block.date == block_in.date,
        Block.time_of_day == block_in.time_of_day
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Block already exists for this date and time")

    block = Block(**block_in.model_dump())
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


@router.post("/generate", response_model=BlockListResponse)
def generate_blocks(
    start_date: date,
    end_date: date,
    base_block_number: int = Query(1, description="Starting block number"),
    db: Session = Depends(get_db),
):
    """
    Generate blocks for a date range.

    Creates AM and PM blocks for each day (730 blocks per year).
    """
    from datetime import timedelta

    blocks_created = []
    current_date = start_date
    current_block = base_block_number

    # Calculate block duration (typically 4 weeks)
    block_duration_days = 28

    while current_date <= end_date:
        for time_of_day in ["AM", "PM"]:
            # Check if block already exists
            existing = db.query(Block).filter(
                Block.date == current_date,
                Block.time_of_day == time_of_day
            ).first()

            if not existing:
                block = Block(
                    date=current_date,
                    time_of_day=time_of_day,
                    block_number=current_block,
                    is_weekend=(current_date.weekday() >= 5),
                    is_holiday=False,  # Can be updated later
                )
                db.add(block)
                blocks_created.append(block)

        # Update block number every 28 days
        days_from_start = (current_date - start_date).days
        current_block = base_block_number + (days_from_start // block_duration_days)

        current_date += timedelta(days=1)

    db.commit()

    # Refresh all blocks
    for block in blocks_created:
        db.refresh(block)

    return BlockListResponse(items=blocks_created, total=len(blocks_created))


@router.delete("/{block_id}", status_code=204)
def delete_block(block_id: UUID, db: Session = Depends(get_db)):
    """Delete a block."""
    block = db.query(Block).filter(Block.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")

    db.delete(block)
    db.commit()
