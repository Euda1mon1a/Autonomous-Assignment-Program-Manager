"""Block model - half-day scheduling blocks."""
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class Block(Base):
    """
    Represents a half-day scheduling block.

    730 blocks per year: 365 days × 2 (AM/PM)
    Each block represents a schedulable unit for assignments.
    """
    __tablename__ = "blocks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False)
    time_of_day = Column(String(2), nullable=False)  # 'AM' or 'PM'
    block_number = Column(Integer, nullable=False)  # Academic year block (e.g., Block 2, Block 3)
    is_weekend = Column(Boolean, default=False)
    is_holiday = Column(Boolean, default=False)
    holiday_name = Column(String(255))

    # Relationships
    assignments = relationship("Assignment", back_populates="block")

    __table_args__ = (
        UniqueConstraint("date", "time_of_day", name="unique_block_per_half_day"),
        CheckConstraint("time_of_day IN ('AM', 'PM')", name="check_time_of_day"),
    )

    def __repr__(self):
        return f"<Block(date='{self.date}', time='{self.time_of_day}')>"

    @property
    def display_name(self) -> str:
        """Get display name for this block."""
        return f"{self.date.strftime('%Y-%m-%d')} {self.time_of_day}"

    @property
    def is_workday(self) -> bool:
        """Check if this is a regular workday (not weekend or holiday)."""
        return not self.is_weekend and not self.is_holiday

    @property
    def block_half(self) -> int:
        """
        Determine which half of the 4-week block this date falls into.

        Returns:
            1 = First half (weeks 1-2, days 1-14)
            2 = Second half (weeks 3-4, days 15-28)

        Used for split rotations like Night Float where residents swap
        mid-block to ensure continuous coverage.

        Note: Uses the stored block_number and finds all blocks with same number
        to calculate position within the block.
        """
        from sqlalchemy import func
        from sqlalchemy.orm import object_session

        session = object_session(self)
        if session is None:
            # Fallback if not attached to session - use modulo of day of year
            day_of_year = self.date.timetuple().tm_yday
            return 1 if (day_of_year % 28) < 14 else 2

        # Find the first date of this block_number
        first_date = session.query(func.min(Block.date)).filter(
            Block.block_number == self.block_number
        ).scalar()

        if first_date is None:
            return 1

        # Calculate day within the block (0-27)
        day_in_block = (self.date - first_date).days

        # First half = days 0-13, Second half = days 14-27
        return 1 if day_in_block < 14 else 2

    @property
    def block_half_display(self) -> str:
        """Human-readable block half description."""
        return f"Block {self.block_number} - {'First' if self.block_half == 1 else 'Second'} Half"
