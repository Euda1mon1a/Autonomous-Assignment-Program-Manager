"""Weekly pattern model for rotation template GUI.

Defines individual slots in a 7x2 weekly grid for rotation templates.
Each rotation template can have up to 14 slots (7 days x 2 time periods).

This enables visual editing of weekly patterns in the GUI where coordinators
can click cells to assign activities like FM Clinic, Specialty, etc.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class WeeklyPattern(Base):
    """
    A single slot in a 7x2 weekly grid for a rotation template.

    Grid Layout:
        | Mon | Tue | Wed | Thu | Fri | Sat | Sun |
    AM  |  X  |  X  |  X  |  X  |  X  |  X  |  X  |
    PM  |  X  |  X  |  X  |  X  |  X  |  X  |  X  |

    Each X is one WeeklyPattern record.

    Attributes:
        day_of_week: 0=Sunday, 1=Monday, ..., 6=Saturday
        time_of_day: "AM" or "PM"
        activity_type: DEPRECATED - Legacy string field (fm_clinic, specialty, etc.)
        activity_id: FK to Activity table (new normalized reference)
        is_protected: True for slots that cannot be changed (e.g., Wed AM conference)

    SQLAlchemy Relationships:
        rotation_template: Many-to-one to RotationTemplate
            (via rotation_template_id FK).
            Back-populates RotationTemplate.weekly_patterns.
            FK ondelete=CASCADE. The template this slot belongs to.

        activity: Many-to-one to Activity (via activity_id FK).
            No back-populates. FK ondelete=RESTRICT.
            The activity assigned to this slot.

        linked_template: Many-to-one to RotationTemplate
            (via linked_template_id FK).
            No back-populates. FK ondelete=SET NULL.
            Optional reference to another template for complex patterns.
    """

    __tablename__ = "weekly_patterns"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Foreign key to rotation template
    rotation_template_id = Column(
        GUID(),
        ForeignKey("rotation_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Grid position
    day_of_week = Column(
        Integer,
        nullable=False,
        comment="0=Sunday, 1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday",
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
        comment="Week 1-4 within the block. NULL = same pattern all weeks",
    )

    # Activity assigned to this slot (legacy string field - being deprecated)
    activity_type = Column(
        String(50),
        nullable=False,
        comment="DEPRECATED: Use activity_id. Legacy: fm_clinic, specialty, elective, conference, inpatient, call, procedure, off",
    )

    # Foreign key to Activity table (new normalized relationship)
    # Initially nullable for migration, will be made NOT NULL after backfill
    activity_id = Column(
        GUID(),
        ForeignKey("activities.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
        comment="FK to activities table - the activity assigned to this slot",
    )

    # Optional: link to a specific sub-rotation template for this slot
    # This allows slots to reference other templates for complex patterns
    linked_template_id = Column(
        GUID(),
        ForeignKey("rotation_templates.id", ondelete="SET NULL"),
        nullable=True,
        comment="Optional link to a specific activity template",
    )

    # Protected slots cannot be modified by users
    # Example: Wednesday AM conference time is protected
    is_protected = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="True for slots that cannot be changed (e.g., Wed AM conference)",
    )

    # Optional notes for this slot
    notes = Column(String(200), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    rotation_template = relationship(
        "RotationTemplate",
        back_populates="weekly_patterns",
        foreign_keys=[rotation_template_id],
    )

    linked_template = relationship(
        "RotationTemplate",
        foreign_keys=[linked_template_id],
    )

    # Relationship to Activity (normalized reference)
    activity = relationship("Activity")

    # Unique constraint: one slot per day/time/week per template
    # Week number is included to allow week-specific patterns (NULL = all weeks)
    __table_args__ = (
        UniqueConstraint(
            "rotation_template_id",
            "day_of_week",
            "time_of_day",
            "week_number",
            name="uq_weekly_pattern_slot_v2",
        ),
    )

    def __repr__(self) -> str:
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        week_str = f"W{self.week_number}" if self.week_number else "All"
        return f"<WeeklyPattern {week_str} {days[self.day_of_week]} {self.time_of_day}: {self.activity_type}>"

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
