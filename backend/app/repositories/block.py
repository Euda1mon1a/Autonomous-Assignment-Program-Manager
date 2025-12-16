"""Block repository for database operations."""

from datetime import date
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.repositories.base import BaseRepository
from app.models.block import Block


class BlockRepository(BaseRepository[Block]):
    """Repository for Block entity operations."""

    def __init__(self, db: Session):
        super().__init__(Block, db)

    def list_with_filters(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        block_number: Optional[int] = None,
    ) -> List[Block]:
        """List blocks with optional filters, ordered by date and time."""
        query = self.db.query(Block)

        if start_date:
            query = query.filter(Block.date >= start_date)
        if end_date:
            query = query.filter(Block.date <= end_date)
        if block_number is not None:
            query = query.filter(Block.block_number == block_number)

        return query.order_by(Block.date, Block.time_of_day).all()

    def get_by_date_and_time(
        self, date: date, time_of_day: str
    ) -> Optional[Block]:
        """Get a block by date and time of day."""
        return (
            self.db.query(Block)
            .filter(
                Block.date == date,
                Block.time_of_day == time_of_day,
            )
            .first()
        )

    def get_ids_in_date_range(
        self, start_date: date, end_date: date
    ) -> List[UUID]:
        """Get all block IDs in a date range."""
        results = (
            self.db.query(Block.id)
            .filter(
                Block.date >= start_date,
                Block.date <= end_date,
            )
            .all()
        )
        return [r[0] for r in results]

    def exists_for_date_and_time(
        self, date: date, time_of_day: str
    ) -> bool:
        """Check if a block exists for a specific date and time."""
        return (
            self.db.query(Block)
            .filter(
                Block.date == date,
                Block.time_of_day == time_of_day,
            )
            .first()
            is not None
        )

    def bulk_create(self, blocks: List[dict]) -> List[Block]:
        """Create multiple blocks at once."""
        db_blocks = [Block(**b) for b in blocks]
        self.db.add_all(db_blocks)
        self.db.flush()
        return db_blocks
