"""Faculty weekly override model for week-specific exceptions.

Overrides allow week-specific changes to a faculty member's default template.
When computing the effective schedule for a specific week, overrides take
precedence over the template.

Use cases:
- Conference week: Override clinic slots with "OFF" or "Conference"
- Vacation: Clear slots for specific dates
- Special duty: Lock in FMIT supervision for a specific week
- Manual adjustment: Coordinator manually sets a slot for specific circumstances
"""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, relationship

from app.db.base import Base
from app.db.types import GUID

if TYPE_CHECKING:
    from app.models.activity import Activity
    from app.models.person import Person


class FacultyWeeklyOverride(Base):
    """
    A week-specific override for a faculty member's default template.

    Overrides replace the template slot for a specific week, identified by
    effective_date (the Monday of that week).

    Attributes:
        person_id: FK to faculty member
        effective_date: Monday of the week this override applies to
        day_of_week: 0=Sunday, 1=Monday, ..., 6=Saturday
        time_of_day: "AM" or "PM"
        activity_id: FK to Activity (NULL = clear/empty slot)
        is_locked: HARD constraint for this specific week
        override_reason: Why this override was created
        created_by: Who created this override (audit trail)

    SQLAlchemy Relationships:
        person: Many-to-one to Person (faculty member)
        activity: Many-to-one to Activity
        creator: Many-to-one to Person (who created the override)

    Example usage:
        # Dr. Smith is at a conference week of Jan 6
        override = FacultyWeeklyOverride(
            person_id=dr_smith.id,
            effective_date=date(2026, 1, 6),  # Monday of that week
            day_of_week=1,  # Monday
            time_of_day="AM",
            activity_id=None,  # Clear the slot
            is_locked=True,
            override_reason="AAFP Conference",
            created_by=coordinator.id,
        )
    """

    __tablename__ = "faculty_weekly_overrides"

    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Foreign key to faculty member
    person_id = Column(
        GUID(),
        ForeignKey("people.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Week identifier (Monday of the week)
    effective_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Monday of the week this override applies to",
    )

    # Grid position
    day_of_week = Column(
        Integer,
        nullable=False,
        comment="0=Sunday, 1=Monday, ..., 6=Saturday",
    )

    time_of_day = Column(
        String(2),
        nullable=False,
        comment="AM or PM",
    )

    # Activity for this override (NULL = clear slot)
    activity_id = Column(
        GUID(),
        ForeignKey("activities.id", ondelete="RESTRICT"),
        nullable=True,
        comment="Activity for this override (NULL = clear slot)",
    )

    # Constraint flag
    is_locked = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="HARD constraint for this specific week",
    )

    # Audit fields
    override_reason = Column(
        Text,
        nullable=True,
        comment="Why this override was created",
    )

    created_by = Column(
        GUID(),
        ForeignKey("people.id", ondelete="SET NULL"),
        nullable=True,
        comment="Who created this override",
    )

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    person: Mapped["Person"] = relationship(
        "Person",
        back_populates="faculty_weekly_overrides",
        foreign_keys=[person_id],
    )

    activity: Mapped[Optional["Activity"]] = relationship("Activity")

    creator: Mapped[Optional["Person"]] = relationship(
        "Person",
        foreign_keys=[created_by],
    )

    # Unique constraint: one override per person/date/day/time
    __table_args__ = (
        UniqueConstraint(
            "person_id",
            "effective_date",
            "day_of_week",
            "time_of_day",
            name="uq_faculty_weekly_override_slot",
        ),
    )

    def __repr__(self) -> str:
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        activity_str = self.activity.code if self.activity else "empty"
        locked_str = " [LOCKED]" if self.is_locked else ""
        return f"<FacultyWeeklyOverride {self.effective_date} {days[self.day_of_week]} {self.time_of_day}: {activity_str}{locked_str}>"

    @property
    def day_name(self) -> str:
        """Return human-readable day name."""
        days = [
            "Sunday",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
        ]
        return days[self.day_of_week]

    @property
    def is_weekend(self) -> bool:
        """Check if this slot is on a weekend."""
        return self.day_of_week in (0, 6)  # Sunday or Saturday

    @property
    def slot_key(self) -> str:
        """Return unique key for this slot within a week."""
        return f"{self.day_of_week}_{self.time_of_day}"

    @property
    def week_start(self) -> date:
        """Return the Monday of this override's week."""
        return self.effective_date
