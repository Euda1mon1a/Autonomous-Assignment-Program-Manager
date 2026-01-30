"""Faculty scheduling preferences for clinic or call slots."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class FacultyPreferenceType(str, Enum):
    """Preference category (clinic or call)."""

    CLINIC = "clinic"
    CALL = "call"


class FacultyPreferenceDirection(str, Enum):
    """Preference direction (prefer or avoid)."""

    PREFER = "prefer"
    AVOID = "avoid"


class FacultySchedulePreference(Base):
    """Soft scheduling preference for a faculty member.

    Supports two personal preferences per faculty (rank 1-2). Preferences can
    target clinic slots (day + AM/PM) or call nights (day of week).
    """

    __tablename__ = "faculty_schedule_preferences"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    person_id = Column(
        GUID(),
        ForeignKey("people.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    preference_type = Column(
        SAEnum(
            FacultyPreferenceType,
            name="facultypreferencetype",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        index=True,
    )
    direction = Column(
        SAEnum(
            FacultyPreferenceDirection,
            name="facultypreferencedirection",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        index=True,
    )
    rank = Column(
        Integer,
        nullable=False,
        comment="Preference rank (1 or 2).",
    )
    day_of_week = Column(
        Integer,
        nullable=False,
        comment="0=Monday, 6=Sunday (Python weekday).",
    )
    time_of_day = Column(
        String(2),
        nullable=True,
        comment="AM/PM for clinic preferences; NULL for call.",
    )
    weight = Column(
        Integer,
        nullable=False,
        default=6,
        comment="Soft penalty weight (higher = stronger preference).",
    )
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    notes = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    person = relationship("Person", back_populates="faculty_schedule_preferences")

    __table_args__ = (
        UniqueConstraint(
            "person_id",
            "rank",
            name="uq_faculty_schedule_preference_rank",
        ),
        CheckConstraint(
            "rank IN (1, 2)",
            name="check_faculty_schedule_preference_rank",
        ),
        CheckConstraint(
            "day_of_week BETWEEN 0 AND 6",
            name="check_faculty_schedule_preference_day",
        ),
        CheckConstraint(
            "time_of_day IN ('AM', 'PM') OR time_of_day IS NULL",
            name="check_faculty_schedule_preference_time",
        ),
        CheckConstraint(
            "(preference_type = 'clinic' AND time_of_day IS NOT NULL) "
            "OR (preference_type = 'call' AND time_of_day IS NULL)",
            name="check_faculty_schedule_preference_type",
        ),
        Index(
            "ix_faculty_schedule_preferences_person_active",
            "person_id",
            "is_active",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<FacultySchedulePreference {self.person_id} "
            f"{self.preference_type} {self.direction} rank={self.rank}>"
        )
