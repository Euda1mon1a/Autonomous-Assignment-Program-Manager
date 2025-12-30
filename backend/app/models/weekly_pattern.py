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
        activity_type: The activity assigned (fm_clinic, specialty, etc.)
        is_protected: True for slots that cannot be changed (e.g., Wed AM conference)
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

    # Activity assigned to this slot
    activity_type = Column(
        String(50),
        nullable=False,
        comment="fm_clinic, specialty, elective, conference, inpatient, call, procedure, off",
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

    # Unique constraint: one slot per day/time per template
    __table_args__ = (
        UniqueConstraint(
            "rotation_template_id",
            "day_of_week",
            "time_of_day",
            name="uq_weekly_pattern_slot",
        ),
    )

    def __repr__(self) -> str:
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        return f"<WeeklyPattern {days[self.day_of_week]} {self.time_of_day}: {self.activity_type}>"

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
