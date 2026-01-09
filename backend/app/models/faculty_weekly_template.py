"""Faculty weekly template model for default activity patterns.

Defines individual slots in a 7x2 weekly grid for faculty members.
Each faculty can have up to 14 slots per week (7 days x 2 time periods).

This enables visual editing of default weekly patterns where coordinators
can click cells to assign activities like AT, FM Clinic, GME, etc.

Templates represent the default pattern for a faculty member.
Week-specific exceptions use FacultyWeeklyOverride instead.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    Column,
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


class FacultyWeeklyTemplate(Base):
    """
    A single slot in a 7x2 weekly grid for a faculty member's default pattern.

    Grid Layout:
        | Mon | Tue | Wed | Thu | Fri | Sat | Sun |
    AM  |  X  |  X  |  X  |  X  |  X  |  X  |  X  |
    PM  |  X  |  X  |  X  |  X  |  X  |  X  |  X  |

    Each X is one FacultyWeeklyTemplate record.

    Attributes:
        person_id: FK to faculty member this template belongs to
        day_of_week: 0=Sunday, 1=Monday, ..., 6=Saturday
        time_of_day: "AM" or "PM"
        week_number: Week 1-4 within block (NULL = same pattern all weeks)
        activity_id: FK to Activity table (NULL = unassigned slot)
        is_locked: HARD constraint - solver cannot change this slot
        priority: Soft preference 0-100 (higher = more important for solver)
        notes: Optional notes for this slot

    SQLAlchemy Relationships:
        person: Many-to-one to Person (faculty member)
        activity: Many-to-one to Activity

    Example usage:
        # OIC likes admin time Monday mornings
        template_slot = FacultyWeeklyTemplate(
            person_id=oic_faculty.id,
            day_of_week=1,  # Monday
            time_of_day="AM",
            activity_id=dfm_activity.id,
            is_locked=True,  # Hard constraint
            notes="OIC prefers Monday admin due to weekend issues",
        )
    """

    __tablename__ = "faculty_weekly_templates"

    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Foreign key to faculty member
    person_id = Column(
        GUID(),
        ForeignKey("people.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
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

    # Week number within the block (1-4)
    # NULL means same pattern applies to all weeks
    week_number = Column(
        Integer,
        nullable=True,
        comment="Week 1-4 within block. NULL = same pattern all weeks",
    )

    # Activity assigned to this slot
    activity_id = Column(
        GUID(),
        ForeignKey("activities.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
        comment="Activity assigned to this slot (NULL = unassigned)",
    )

    # Constraint flags
    is_locked = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="HARD constraint - solver cannot change this slot",
    )

    priority = Column(
        Integer,
        default=50,
        nullable=False,
        comment="Soft preference 0-100 (higher = more important)",
    )

    # Optional notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    person: Mapped["Person"] = relationship(
        "Person",
        back_populates="faculty_weekly_templates",
    )

    activity: Mapped[Optional["Activity"]] = relationship("Activity")

    # Unique constraint: one slot per person/day/time/week
    __table_args__ = (
        UniqueConstraint(
            "person_id",
            "day_of_week",
            "time_of_day",
            "week_number",
            name="uq_faculty_weekly_template_slot",
        ),
    )

    def __repr__(self) -> str:
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        week_str = f"W{self.week_number}" if self.week_number else "All"
        activity_str = self.activity.code if self.activity else "empty"
        locked_str = " [LOCKED]" if self.is_locked else ""
        return f"<FacultyWeeklyTemplate {week_str} {days[self.day_of_week]} {self.time_of_day}: {activity_str}{locked_str}>"

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
