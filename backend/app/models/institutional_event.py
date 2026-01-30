"""Institutional events that block or annotate the schedule."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class InstitutionalEventType(str, Enum):
    """High-level classification for institutional events."""

    HOLIDAY = "holiday"
    CONFERENCE = "conference"
    RETREAT = "retreat"
    TRAINING = "training"
    CLOSURE = "closure"
    OTHER = "other"


class InstitutionalEventScope(str, Enum):
    """Who the event applies to."""

    ALL = "all"
    FACULTY = "faculty"
    RESIDENT = "resident"


class InstitutionalEvent(Base):
    """Represents an institutional event that blocks schedule slots."""

    __tablename__ = "institutional_events"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    event_type = Column(
        SAEnum(InstitutionalEventType, name="institutionaleventtype"),
        nullable=False,
        index=True,
    )
    applies_to = Column(
        SAEnum(InstitutionalEventScope, name="institutionaleventscope"),
        nullable=False,
        default=InstitutionalEventScope.ALL,
        index=True,
    )
    activity_id = Column(
        GUID(),
        ForeignKey("activities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    time_of_day = Column(String(2), nullable=True)
    applies_to_inpatient = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    activity = relationship("Activity")

    __table_args__ = (
        CheckConstraint(
            "time_of_day IN ('AM', 'PM') OR time_of_day IS NULL",
            name="check_institutional_event_time_of_day",
        ),
        CheckConstraint(
            "end_date >= start_date",
            name="check_institutional_event_dates",
        ),
        Index(
            "ix_institutional_events_date_range",
            "start_date",
            "end_date",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<InstitutionalEvent {self.name} ({self.event_type}) "
            f"{self.start_date} to {self.end_date}>"
        )
