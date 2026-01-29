"""ScheduleOverride model - admin overlay for released schedules.

Overrides provide a delta layer on top of the base schedule without
mutating original assignments. This supports short-notice coverage
changes (deployment, illness) while preserving audit history.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

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
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class ScheduleOverride(Base):
    """Admin override for a half-day assignment."""

    __tablename__ = "schedule_overrides"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    half_day_assignment_id = Column(
        GUID(),
        ForeignKey("half_day_assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_person_id = Column(
        GUID(),
        ForeignKey("people.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    replacement_person_id = Column(
        GUID(),
        ForeignKey("people.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    override_type = Column(
        String(20),
        nullable=False,
        default="coverage",
        comment="coverage or cancellation",
    )
    reason = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    effective_date = Column(Date, nullable=False, index=True)
    time_of_day = Column(String(2), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False, index=True)

    created_by_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    deactivated_at = Column(DateTime, nullable=True)
    deactivated_by_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    supersedes_override_id = Column(
        GUID(),
        ForeignKey("schedule_overrides.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint(
            "override_type IN ('coverage', 'cancellation')",
            name="ck_schedule_override_type",
        ),
        CheckConstraint(
            "time_of_day IN ('AM', 'PM')",
            name="ck_schedule_override_time_of_day",
        ),
        CheckConstraint(
            "(override_type = 'coverage' AND replacement_person_id IS NOT NULL) "
            "OR (override_type = 'cancellation' AND replacement_person_id IS NULL)",
            name="ck_schedule_override_replacement",
        ),
        Index(
            "idx_schedule_overrides_effective",
            "effective_date",
            "time_of_day",
        ),
    )

    half_day_assignment = relationship("HalfDayAssignment")
    original_person = relationship("Person", foreign_keys=[original_person_id])
    replacement_person = relationship("Person", foreign_keys=[replacement_person_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    deactivated_by = relationship("User", foreign_keys=[deactivated_by_id])
    supersedes_override = relationship(
        "ScheduleOverride", remote_side=[id], uselist=False
    )

    def __repr__(self) -> str:
        return (
            f"<ScheduleOverride(id={self.id}, assignment={self.half_day_assignment_id}, "
            f"override_type={self.override_type}, active={self.is_active})>"
        )
