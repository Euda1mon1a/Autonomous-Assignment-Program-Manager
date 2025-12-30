"""Block Assignment model - academic block rotation assignments."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class AssignmentReason(str, Enum):
    """Reason for block assignment."""

    LEAVE_ELIGIBLE_MATCH = "leave_eligible_match"  # Auto-assigned due to leave
    COVERAGE_PRIORITY = "coverage_priority"  # Assigned to fill coverage needs
    BALANCED = "balanced"  # Assigned for workload balance
    MANUAL = "manual"  # Manually assigned by coordinator
    SPECIALTY_MATCH = "specialty_match"  # Matches specialty requirements


class BlockAssignment(Base):
    """
    Represents a resident's rotation assignment for an academic block.

    Academic blocks are 28-day periods (1-13 per year).
    This links a resident to a rotation template for a specific block,
    factoring in leave eligibility and coverage requirements.

    Key concept: Residents with approved leave get auto-assigned to
    leave_eligible=True rotations so they don't disrupt FMIT/inpatient coverage.
    """

    __tablename__ = "block_assignments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Block identification
    block_number = Column(Integer, nullable=False)  # 1-13
    academic_year = Column(Integer, nullable=False)  # e.g., 2025 (starts July 1)

    # Assignment links
    resident_id = Column(
        GUID(), ForeignKey("people.id", ondelete="CASCADE"), nullable=False
    )
    rotation_template_id = Column(
        GUID(),
        ForeignKey("rotation_templates.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Leave tracking
    has_leave = Column(Boolean, default=False, nullable=False)
    leave_days = Column(Integer, default=0, nullable=False)

    # Assignment metadata
    assignment_reason = Column(String(50), nullable=False, default="balanced")
    notes = Column(Text)

    # Audit fields
    created_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    resident = relationship("Person", backref="block_assignments")
    rotation_template = relationship("RotationTemplate", backref="block_assignments")

    __table_args__ = (
        UniqueConstraint(
            "block_number",
            "academic_year",
            "resident_id",
            name="unique_resident_per_block",
        ),
        CheckConstraint(
            "block_number >= 0 AND block_number <= 13",
            name="check_block_number_range",
        ),
        CheckConstraint(
            "leave_days >= 0",
            name="check_leave_days_positive",
        ),
        CheckConstraint(
            "assignment_reason IN ('leave_eligible_match', 'coverage_priority', "
            "'balanced', 'manual', 'specialty_match')",
            name="check_assignment_reason",
        ),
    )

    def __repr__(self):
        return (
            f"<BlockAssignment(block={self.block_number}, "
            f"year={self.academic_year}, resident_id='{self.resident_id}')>"
        )

    @property
    def block_display(self) -> str:
        """Get display name for the block."""
        return f"Block {self.block_number} ({self.academic_year})"

    @property
    def is_leave_eligible_rotation(self) -> bool:
        """Check if assigned rotation is leave-eligible."""
        if self.rotation_template:
            return self.rotation_template.leave_eligible
        return True  # Assume eligible if no template assigned
