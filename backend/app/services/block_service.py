"""Block service for business logic."""

from datetime import date, timedelta
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.repositories.block import BlockRepository
from app.models.block import Block


class BlockService:
    """Service for block business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.block_repo = BlockRepository(db)

    def get_block(self, block_id: UUID) -> Optional[Block]:
        """Get a single block by ID."""
        return self.block_repo.get_by_id(block_id)

    def list_blocks(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        block_number: Optional[int] = None,
    ) -> dict:
        """List blocks with optional filters."""
        blocks = self.block_repo.list_with_filters(
            start_date=start_date,
            end_date=end_date,
            block_number=block_number,
        )
        return {"items": blocks, "total": len(blocks)}

    def create_block(
        self,
        block_date: date,
        time_of_day: str,
        block_number: Optional[int] = None,
        is_weekend: Optional[bool] = None,
        is_holiday: bool = False,
    ) -> dict:
        """
        Create a new block.

        Returns dict with:
        - block: The created block
        - error: Error message if creation failed
        """
        # Check for duplicate
        if self.block_repo.exists_for_date_and_time(block_date, time_of_day):
            return {
                "block": None,
                "error": "Block already exists for this date and time",
            }

        # Calculate is_weekend if not provided
        if is_weekend is None:
            is_weekend = block_date.weekday() >= 5

        block_data = {
            "date": block_date,
            "time_of_day": time_of_day,
            "is_weekend": is_weekend,
            "is_holiday": is_holiday,
        }
        if block_number is not None:
            block_data["block_number"] = block_number

        block = self.block_repo.create(block_data)
        self.block_repo.commit()
        self.block_repo.refresh(block)

        return {"block": block, "error": None}

    def generate_blocks(
        self,
        start_date: date,
        end_date: date,
        base_block_number: int = 1,
    ) -> dict:
        """
        Generate blocks for a date range.

        Creates AM and PM blocks for each day (730 blocks per year).
        Returns dict with:
        - blocks: List of created blocks
        - total: Number of blocks created
        """
        block_duration_days = 28  # Block number changes every 4 weeks
        blocks_created = []
        current_date = start_date

        while current_date <= end_date:
            for time_of_day in ["AM", "PM"]:
                # Skip if block already exists
                if self.block_repo.exists_for_date_and_time(current_date, time_of_day):
                    continue

                days_from_start = (current_date - start_date).days
                current_block = base_block_number + (days_from_start // block_duration_days)

                block_data = {
                    "date": current_date,
                    "time_of_day": time_of_day,
                    "block_number": current_block,
                    "is_weekend": current_date.weekday() >= 5,
                    "is_holiday": False,
                }
                block = self.block_repo.create(block_data)
                blocks_created.append(block)

            current_date += timedelta(days=1)

        self.block_repo.commit()

        # Refresh all blocks
        for block in blocks_created:
            self.block_repo.refresh(block)

        return {"items": blocks_created, "total": len(blocks_created)}

    def delete_block(self, block_id: UUID) -> dict:
        """Delete a block."""
        block = self.block_repo.get_by_id(block_id)
        if not block:
            return {"success": False, "error": "Block not found"}

        self.block_repo.delete(block)
        self.block_repo.commit()
        return {"success": True, "error": None}
