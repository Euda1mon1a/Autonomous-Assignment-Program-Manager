"""Block Assignment model - academic block rotation assignments."""

import uuid
from datetime import datetime, timezone, UTC
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    and_,
    func,
    select,
)
from sqlalchemy.ext.hybrid import hybrid_property
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

    # Block identification (denormalized for convenience - canonical reference is academic_block_id)
    block_number = Column(Integer, nullable=False)  # 1-13
    academic_year = Column(Integer, nullable=False)  # e.g., 2025 (starts July 1)

    # FK to academic_blocks table (nullable for backwards compatibility)
    academic_block_id = Column(
        GUID(),
        ForeignKey("academic_blocks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Assignment links
    resident_id = Column(
        GUID(), ForeignKey("people.id", ondelete="CASCADE"), nullable=False
    )
    rotation_template_id = Column(
        GUID(),
        ForeignKey("rotation_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Half-block indicator: NULL = full block, 1 = days 1-14, 2 = days 15-28.
    # Combined rotations (e.g., NF + Cardiology) are expressed as two rows
    # with block_half=1 and block_half=2, each pointing to an atomic template.
    block_half = Column(SmallInteger, nullable=True)

    # Assignment metadata
    assignment_reason = Column(String(50), nullable=False, default="balanced")
    notes = Column(Text)

    # Audit fields
    created_by = Column(String(255))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # Relationships
    resident = relationship("Person", backref="block_assignments")
    rotation_template = relationship(
        "RotationTemplate",
        foreign_keys=[rotation_template_id],
        backref="block_assignments",
    )
    academic_block = relationship(
        "AcademicBlock",
        back_populates="assignments",
        foreign_keys=[academic_block_id],
    )

    __table_args__ = (
        # Unique constraints are partial indexes (created in migration):
        #   uq_resident_block_full: (block_number, academic_year, resident_id) WHERE block_half IS NULL
        #   uq_resident_block_half: (block_number, academic_year, resident_id, block_half) WHERE block_half IS NOT NULL
        # Plus trigger trg_block_half_exclusion prevents mixing full/half rows.
        CheckConstraint(
            "block_number >= 0 AND block_number <= 13",
            name="check_block_number_range",
        ),
        CheckConstraint(
            "assignment_reason IN ('leave_eligible_match', 'coverage_priority', "
            "'balanced', 'manual', 'specialty_match')",
            name="check_assignment_reason",
        ),
        CheckConstraint(
            "block_half IS NULL OR block_half IN (1, 2)",
            name="check_block_half_range",
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

    @hybrid_property
    def leave_days(self) -> int:
        """Calculate leave days dynamically from absences."""
        if (
            getattr(self, "academic_block", None) is None
            or getattr(self, "resident", None) is None
        ):
            return 0

        # Check if absences relationship is loaded
        if "absences" not in self.resident.__dict__:
            return 0

        leave = 0
        for a in self.resident.absences:
            if getattr(a, "start_date", None) and getattr(a, "end_date", None):
                if (
                    a.start_date <= self.academic_block.end_date
                    and a.end_date >= self.academic_block.start_date
                ):
                    overlap_start = max(a.start_date, self.academic_block.start_date)
                    overlap_end = min(a.end_date, self.academic_block.end_date)
                    leave += (overlap_end - overlap_start).days + 1
        return leave

    @leave_days.expression  # type: ignore[no-redef]
    def leave_days(cls):
        from app.models.absence import Absence
        from app.models.academic_block import AcademicBlock

        return (
            select(
                func.coalesce(
                    func.sum(
                        func.least(Absence.end_date, AcademicBlock.end_date)
                        - func.greatest(Absence.start_date, AcademicBlock.start_date)
                        + 1
                    ),
                    0,
                )
            )
            .where(
                and_(
                    Absence.person_id == cls.resident_id,
                    AcademicBlock.id == cls.academic_block_id,
                    Absence.start_date <= AcademicBlock.end_date,
                    Absence.end_date >= AcademicBlock.start_date,
                )
            )
            .correlate(cls)
            .scalar_subquery()
        )

    @hybrid_property
    def has_leave(self) -> bool:
        """Boolean flag indicating if any leave exists."""
        return self.leave_days > 0

    @has_leave.expression  # type: ignore[no-redef]
    def has_leave(cls):
        return cls.leave_days > 0
