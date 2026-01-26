"""HalfDayAssignment model - persisted half-day schedule slots.

This model stores the actual daily AM/PM schedule assignments with source tracking.
It is the source of truth for the CP-SAT pipeline; legacy expansion is archived.

Key design principles:
- Uses actual dates (not block references) for natural inter-block constraint handling
- Source priority: preload > manual > solver > template
- Unique constraint on (person_id, date, time_of_day) prevents double-booking

Source Priority System:
1. preload - FMIT, call, absences - NEVER overwritten by solver
2. manual - Human override (coordinator intervention)
3. solver - Computed by CP-SAT optimization
4. template - Default from WeeklyPattern (lowest priority)
"""

import uuid
from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class AssignmentSource(str, Enum):
    """Source priority for half-day assignments.

    Higher priority sources cannot be overwritten by lower priority ones.
    """

    PRELOAD = "preload"  # Priority 1: FMIT, call, absences - LOCKED
    MANUAL = "manual"  # Priority 2: Human override - LOCKED
    SOLVER = "solver"  # Priority 3: Computed by optimizer
    TEMPLATE = "template"  # Priority 4: Default from WeeklyPattern


class HalfDayAssignment(Base):
    """
    Persisted half-day schedule assignment.

    Each row represents a single AM or PM slot for a person on a specific date.
    This is the source of truth for the daily schedule.

    Example:
        Dr. Chu on 2026-03-13 AM has FMIT (source=preload, from inpatient_preloads)
        Dr. Kinkennon on 2026-03-13 AM has C (source=solver, computed by CP-SAT)

    Attributes:
        person_id: Who is assigned
        date: Calendar date (actual date, not block reference)
        time_of_day: AM or PM
        activity_id: What they're doing (FK to activities)
        source: Where this assignment came from (preload/manual/solver/template)
        block_assignment_id: Optional link to BlockAssignment for provenance
        is_override: True if this was manually overridden
        override_reason: Why it was overridden
        overridden_by: Who overrode it
        overridden_at: When it was overridden

    Performance Notes:
        - Composite index on (person_id, date) for person schedule lookups
        - Index on date for date range queries
        - Index on activity_id for activity filtering
        - Index on source for preload/solver filtering
    """

    __tablename__ = "half_day_assignments"

    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Core assignment fields
    person_id = Column(
        GUID(),
        ForeignKey("people.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Person assigned to this slot",
    )
    date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Calendar date (actual date, not block reference)",
    )
    time_of_day = Column(
        String(2),
        nullable=False,
        comment="AM or PM",
    )
    activity_id = Column(
        GUID(),
        ForeignKey("activities.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
        comment="Activity for this slot (FK to activities)",
    )

    # Source tracking (critical for source priority system)
    source = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Source: preload, manual, solver, or template",
    )

    # Provenance link to block assignment
    block_assignment_id = Column(
        GUID(),
        ForeignKey("block_assignments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Optional link to BlockAssignment for provenance",
    )

    # Override tracking
    is_override = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="True if manually overridden",
    )
    override_reason = Column(
        Text,
        nullable=True,
        comment="Why this was overridden",
    )
    overridden_by = Column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who performed the override",
    )
    overridden_at = Column(
        DateTime,
        nullable=True,
        comment="When the override was performed",
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    person = relationship("Person", back_populates="half_day_assignments")
    activity = relationship("Activity")
    block_assignment = relationship("BlockAssignment")
    overridden_by_user = relationship("User", foreign_keys=[overridden_by])

    # Constraints and indexes
    __table_args__ = (
        # Unique constraint: one assignment per person per date per time slot
        UniqueConstraint(
            "person_id",
            "date",
            "time_of_day",
            name="uq_half_day_assignment_person_date_time",
        ),
        # Check constraints
        CheckConstraint(
            "time_of_day IN ('AM', 'PM')", name="check_half_day_time_of_day"
        ),
        CheckConstraint(
            "source IN ('preload', 'manual', 'solver', 'template')",
            name="check_half_day_source",
        ),
        # Composite indexes for common queries
        Index("idx_hda_person_date", "person_id", "date"),
        Index("idx_hda_date_time", "date", "time_of_day"),
    )

    def __repr__(self) -> str:
        return (
            f"<HalfDayAssignment {self.person_id} on {self.date} {self.time_of_day}: "
            f"{self.activity_id} (source={self.source})>"
        )

    @property
    def is_locked(self) -> bool:
        """Check if this assignment is locked (preload or manual source)."""
        return self.source in (
            AssignmentSource.PRELOAD.value,
            AssignmentSource.MANUAL.value,
        )

    @property
    def can_be_overwritten_by_solver(self) -> bool:
        """Check if solver can overwrite this assignment."""
        return self.source in (
            AssignmentSource.SOLVER.value,
            AssignmentSource.TEMPLATE.value,
        )

    @property
    def slot_key(self) -> str:
        """Generate a unique key for this slot (person_date_time)."""
        return f"{self.person_id}_{self.date.isoformat()}_{self.time_of_day}"
