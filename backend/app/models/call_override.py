"""CallOverride model - admin overlay for call assignments."""

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


class CallOverride(Base):
    """Admin override for a call assignment."""

    __tablename__ = "call_overrides"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    call_assignment_id = Column(
        GUID(),
        ForeignKey("call_assignments.id", ondelete="CASCADE"),
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
        comment="coverage only (call must always be staffed)",
    )
    reason = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    effective_date = Column(Date, nullable=False, index=True)
    call_type = Column(String(50), nullable=False)

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
        ForeignKey("call_overrides.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint(
            "override_type IN ('coverage')",
            name="ck_call_override_type",
        ),
        CheckConstraint(
            "replacement_person_id IS NOT NULL",
            name="ck_call_override_replacement",
        ),
        Index(
            "idx_call_overrides_effective",
            "effective_date",
            "call_type",
        ),
    )

    call_assignment = relationship("CallAssignment")
    original_person = relationship("Person", foreign_keys=[original_person_id])
    replacement_person = relationship("Person", foreign_keys=[replacement_person_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    deactivated_by = relationship("User", foreign_keys=[deactivated_by_id])
    supersedes_override = relationship("CallOverride", remote_side=[id], uselist=False)

    def __repr__(self) -> str:
        return (
            f"<CallOverride(id={self.id}, assignment={self.call_assignment_id}, "
            f"active={self.is_active})>"
        )
