"""ResidentCallPreload model - Resident call assignments.

This model stores preloaded resident call assignments that are managed
by Chief Residents. These are separate from faculty call (CallAssignment).

Resident Call Types:
- ld_24hr: L&D 24-hour call (typically Friday)
- nf_coverage: Night Float coverage
- weekend: Weekend call

Note: Resident call is Chief-assigned and follows different rules than
faculty call. Faculty call uses the existing CallAssignment model and
includes PCAT/DO (post-call admin time) auto-generation.
"""

import uuid
from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class ResidentCallType(str, Enum):
    """Types of resident call."""

    LD_24HR = "ld_24hr"  # L&D 24-hour call
    NF_COVERAGE = "nf_coverage"  # Night Float coverage
    WEEKEND = "weekend"  # Weekend call


class ResidentCallPreload(Base):
    """
    Preloaded resident call assignment.

    Chief Residents assign resident call, which is tracked separately from
    faculty call. This enables different equity tracking and rules.

    Example:
        Resident on L&D 24-hour call on Friday:
        - person_id: Resident's UUID
        - call_date: 2026-03-13
        - call_type: ld_24hr
        - assigned_by: chief

    Post-Call Handling:
        Unlike faculty call, resident post-call rules depend on rotation.
        The expansion service applies PGY-level-specific rules.
    """

    __tablename__ = "resident_call_preloads"

    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Core fields
    person_id = Column(
        GUID(),
        ForeignKey("people.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Resident assigned to call",
    )
    call_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Date of call",
    )
    call_type = Column(
        String(20),
        nullable=False,
        comment="Type: ld_24hr, nf_coverage, weekend",
    )

    # Provenance
    assigned_by = Column(
        String(20),
        nullable=True,
        comment="Who assigned: chief, scheduler",
    )
    notes = Column(
        String(500),
        nullable=True,
        comment="Optional notes about this call assignment",
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    person = relationship("Person", back_populates="resident_call_preloads")

    # Constraints
    __table_args__ = (
        # Unique: one call per resident per date
        UniqueConstraint("person_id", "call_date", name="uq_resident_call_person_date"),
        # Check constraints
        CheckConstraint(
            "call_type IN ('ld_24hr', 'nf_coverage', 'weekend')",
            name="check_resident_call_type",
        ),
        CheckConstraint(
            "assigned_by IS NULL OR assigned_by IN ('chief', 'scheduler')",
            name="check_resident_call_assigned_by",
        ),
        # Index
        Index("idx_resident_call_date", "call_date"),
    )

    def __repr__(self) -> str:
        return f"<ResidentCallPreload {self.call_type}: {self.person_id} on {self.call_date}>"

    @property
    def is_ld_call(self) -> bool:
        """Check if this is L&D 24-hour call."""
        return self.call_type == ResidentCallType.LD_24HR.value

    @property
    def is_weekend_call(self) -> bool:
        """Check if this is weekend call."""
        return self.call_type == ResidentCallType.WEEKEND.value
