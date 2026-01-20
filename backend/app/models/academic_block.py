"""Academic Block model.

Represents 28-day academic blocks (Block 0-13) as first-class entities with UUIDs.
This enables direct FK relationships instead of composite (block_number, academic_year) keys.

Academic Year Structure:
- Block 0: Orientation (July 1 → first Thursday - 1 day), variable length
- Blocks 1-12: Standard 28-day blocks, Thursday-Wednesday aligned
- Block 13: Variable length, Thursday → June 30
"""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.block_assignment import BlockAssignment


class AcademicBlock(Base):
    """Academic block representing a 28-day scheduling period.

    Attributes:
        id: UUID primary key
        block_number: Block number (0-13)
        academic_year: Starting year of academic year (e.g., 2025 for AY 2025-2026)
        start_date: First day of the block
        end_date: Last day of the block
        name: Display name (e.g., "Block 10", "Orientation")
        is_orientation: True for Block 0
        is_variable_length: True for Block 0 and Block 13
        created_at: Timestamp of creation

    Relationships:
        assignments: BlockAssignments linked to this block
    """

    __tablename__ = "academic_blocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core identifying fields
    block_number = Column(Integer, nullable=False)
    academic_year = Column(Integer, nullable=False)

    # Date range
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Metadata
    name = Column(String(50), nullable=True)
    is_orientation = Column(Boolean, default=False, nullable=False)
    is_variable_length = Column(Boolean, default=False, nullable=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    assignments = relationship(
        "BlockAssignment",
        back_populates="academic_block",
        foreign_keys="BlockAssignment.academic_block_id",
    )

    __table_args__ = (
        UniqueConstraint("block_number", "academic_year", name="uq_block_year"),
        CheckConstraint(
            "block_number >= 0 AND block_number <= 13",
            name="ck_academic_block_number_range",
        ),
        CheckConstraint(
            "academic_year >= 2020 AND academic_year <= 2100",
            name="ck_academic_year_range",
        ),
        CheckConstraint(
            "end_date >= start_date",
            name="ck_academic_block_date_order",
        ),
    )

    def __repr__(self) -> str:
        return f"<AcademicBlock(block={self.block_number}, year={self.academic_year})>"

    @property
    def duration_days(self) -> int:
        """Calculate the number of days in this block."""
        return (self.end_date - self.start_date).days + 1

    @property
    def display_name(self) -> str:
        """User-friendly display name."""
        if self.name:
            return self.name
        if self.block_number == 0:
            return "Orientation"
        return f"Block {self.block_number}"
