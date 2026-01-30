"""Block controller for request/response handling."""

from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.block import (
    BlockCreate,
    BlockListResponse,
    BlockResponse,
)
from app.services.block_service import BlockService


class BlockController:
    """Controller for block endpoints."""

    def __init__(self, db: Session) -> None:
        self.service = BlockService(db)

    def list_blocks(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        block_number: int | None = None,
    ) -> BlockListResponse:
        """List blocks with optional filters."""
        result = self.service.list_blocks(
            start_date=start_date,
            end_date=end_date,
            block_number=block_number,
        )
        return BlockListResponse(
            items=[BlockResponse.model_validate(item) for item in result["items"]],
            total=result["total"],
        )

    def get_block(self, block_id: UUID) -> BlockResponse:
        """Get a single block by ID."""
        block = self.service.get_block(block_id)
        if not block:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Block not found",
            )
        return block

    def create_block(self, block_in: BlockCreate) -> BlockResponse:
        """Create a new block."""
        result = self.service.create_block(
            block_date=block_in.date,
            time_of_day=block_in.time_of_day,
            block_number=getattr(block_in, "block_number", None),
            is_weekend=getattr(block_in, "is_weekend", None),
            is_holiday=getattr(block_in, "is_holiday", False),
        )

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return result["block"]

    def generate_blocks(
        self,
        start_date: date,
        end_date: date,
        base_block_number: int = 1,
    ) -> BlockListResponse:
        """Generate blocks for a date range."""
        result = self.service.generate_blocks(
            start_date=start_date,
            end_date=end_date,
            base_block_number=base_block_number,
        )
        return BlockListResponse(
            items=[BlockResponse.model_validate(item) for item in result["items"]],
            total=result["total"],
        )

    def delete_block(self, block_id: UUID) -> None:
        """Delete a block."""
        result = self.service.delete_block(block_id)
        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )
