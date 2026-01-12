"""Block model - half-day scheduling blocks."""

import uuid
from datetime import date

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    Enum,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID
from app.models.day_type import DayType, OperationalIntent


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
    block_number = Column(
        Integer, nullable=False
    )  # Academic year block (e.g., Block 2, Block 3)
    is_weekend = Column(Boolean, default=False)
    is_holiday = Column(Boolean, default=False)
    holiday_name = Column(String(255))

    # MEDCOM day-type system
    day_type = Column(Enum(DayType), default=DayType.NORMAL, nullable=False)
    operational_intent = Column(
        Enum(OperationalIntent), default=OperationalIntent.NORMAL, nullable=False
    )
    actual_date = Column(Date, nullable=True)  # When observed != actual for holidays

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
    def is_non_operational(self) -> bool:
        """Check if this block is non-operational (DONSA, EO closure, etc.)."""
        return self.operational_intent == OperationalIntent.NON_OPERATIONAL

    @property
    def is_reduced_capacity(self) -> bool:
        """Check if this block has reduced capacity (federal holiday, minimal manning)."""
        return self.operational_intent == OperationalIntent.REDUCED_CAPACITY

    @property
    def block_half(self) -> int:
        """
        Return which half of the block this date falls in.

        Uses Thursday-Wednesday aligned blocks for calculation.

        Returns:
            1 for days 1-14 (first half)
            2 for days 15+ (second half)
        """
        # Import here to avoid circular dependency
        from app.utils.academic_blocks import get_block_half

        return get_block_half(self.date)
