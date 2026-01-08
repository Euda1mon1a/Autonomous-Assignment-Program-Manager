"""Activity model for slot-level schedule events.

Activities are distinct from Rotations:
- Rotation = Multi-week block assignment (e.g., "Neurology" for 4 weeks)
- Activity = Slot-level event (e.g., "FM Clinic AM", "LEC Wednesday PM")

Activities are the building blocks that fill weekly pattern slots within rotations.
They can be dynamically created and assigned to half-day slots.

Examples:
- FM Clinic: Core family medicine clinic sessions
- Specialty: Rotation-specific clinical work (e.g., Neurology, Dermatology)
- LEC: Protected lecture/education time (typically Wednesday PM)
- OFF: Day off (ACGME-protected rest)
- Call: Extended duty coverage
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
)

from app.db.base import Base
from app.db.types import GUID


class ActivityCategory(str, Enum):
    """Categories for activities to enable filtering and business logic."""

    CLINICAL = "clinical"  # Patient care activities (FM clinic, specialty)
    EDUCATIONAL = "educational"  # Learning activities (lecture, conference)
    ADMINISTRATIVE = "administrative"  # Admin duties, meetings
    TIME_OFF = "time_off"  # Days off, recovery


class Activity(Base):
    """
    A slot-level activity that can be assigned to half-day slots.

    Activities are the atomic building blocks that fill the 14 weekly slots
    (7 days x 2 time periods) within a rotation template. They represent
    what a resident is doing during a specific half-day.

    Key differences from RotationTemplate:
    - Activity = Single slot type (e.g., "FM Clinic")
    - RotationTemplate = Multi-week experience containing multiple activities

    Attributes:
        name: Human-readable name (e.g., "FM Clinic", "Lecture")
        code: Stable identifier for solver/constraints (e.g., "fm_clinic", "lec")
        display_abbreviation: Short code for UI grid display (e.g., "C", "LEC")
        activity_category: Classification for filtering/logic
        is_protected: True for locked slots that solver cannot modify

    SQLAlchemy Relationships:
        weekly_patterns: One-to-many to WeeklyPattern (via activity_id FK).
            Back-populates WeeklyPattern.activity.

    Example usage:
        # Create a new activity for sports medicine lectures
        sports_lec = Activity(
            name="Sports Medicine Lecture",
            code="sports_lec",
            display_abbreviation="SPT",
            activity_category="educational",
            is_protected=True,  # Cannot be moved by solver
            font_color="white",
            background_color="purple-700",
        )
    """

    __tablename__ = "activities"

    # Ensure unique name and code
    __table_args__ = (
        UniqueConstraint("name", name="uq_activity_name"),
        UniqueConstraint("code", name="uq_activity_code"),
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Core identification
    name = Column(
        String(255),
        nullable=False,
        comment="Human-readable name (e.g., 'FM Clinic', 'Lecture')",
    )
    code = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Stable identifier for solver/constraints (e.g., 'fm_clinic', 'lec')",
    )
    display_abbreviation = Column(
        String(20),
        nullable=True,
        comment="Short code for UI grid display (e.g., 'C', 'LEC')",
    )

    # Classification
    activity_category = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Category: clinical, educational, administrative, time_off",
    )

    # Visual styling (Tailwind CSS classes)
    font_color = Column(
        String(50),
        nullable=True,
        comment="Tailwind color class for text (e.g., 'white', 'gray-800')",
    )
    background_color = Column(
        String(50),
        nullable=True,
        comment="Tailwind color class for background (e.g., 'green-500', 'purple-700')",
    )

    # Constraints and flags
    requires_supervision = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="True if activity requires faculty supervision (ACGME)",
    )
    is_protected = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="True for locked slots that solver cannot modify (e.g., LEC)",
    )
    counts_toward_clinical_hours = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="True if activity counts toward ACGME clinical hour limits",
    )

    # UI ordering
    display_order = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Sort order for UI dropdowns/lists",
    )

    # Soft delete
    is_archived = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Soft delete flag",
    )
    archived_at = Column(
        DateTime,
        nullable=True,
        comment="When activity was archived",
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Activity {self.code}: {self.name}>"

    @property
    def is_clinical(self) -> bool:
        """Check if this is a clinical activity."""
        return self.activity_category == ActivityCategory.CLINICAL.value

    @property
    def is_educational(self) -> bool:
        """Check if this is an educational activity."""
        return self.activity_category == ActivityCategory.EDUCATIONAL.value

    @property
    def is_time_off(self) -> bool:
        """Check if this is a time-off activity."""
        return self.activity_category == ActivityCategory.TIME_OFF.value
