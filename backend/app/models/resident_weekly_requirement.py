"""Resident weekly requirement model - defines agnostic per-week half-day scheduling requirements."""

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
from app.db.types import GUID, JSONType


class ResidentWeeklyRequirement(Base):
    """
    Defines resident-agnostic weekly half-day scheduling requirements per rotation.

    Unlike RotationHalfDayRequirement which defines per-block composition,
    this model specifies per-week constraints for any resident on the rotation,
    regardless of PGY level or individual preferences.

    Key Use Cases:
    - Outpatient rotations requiring 2-3 FM clinic half-days per week
    - Specialty rotations with protected academic time
    - Variable clinic load based on rotation intensity

    ACGME Compliance:
    - Minimum 2 FM clinic half-days per week on outpatient rotations
    - Protected academic time (Wednesday AM conference)

    SQLAlchemy Relationships:
        rotation_template: One-to-one to RotationTemplate.
            FK ondelete=CASCADE. Unique constraint enforces one-to-one.

    Example Configuration:
        Neurology Elective:
        - fm_clinic_min_per_week = 2
        - fm_clinic_max_per_week = 3
        - specialty_min_per_week = 3
        - specialty_max_per_week = 5
        - academics_required = True
        - protected_slots = {"wed_am": "conference"}
        - allowed_clinic_days = [1, 2, 3, 4, 5]  # Mon-Fri
    """

    __tablename__ = "resident_weekly_requirements"

    # Enforce one-to-one relationship at DB level
    __table_args__ = (
        UniqueConstraint(
            "rotation_template_id",
            name="uq_resident_weekly_requirement_template",
        ),
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    rotation_template_id = Column(
        GUID(),
        ForeignKey("rotation_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # FM Clinic half-day requirements (ACGME: min 2 on outpatient)
    fm_clinic_min_per_week = Column(Integer, default=2, nullable=False)
    fm_clinic_max_per_week = Column(Integer, default=3, nullable=False)

    # Specialty half-day requirements (rotation-specific activities)
    specialty_min_per_week = Column(Integer, default=0, nullable=False)
    specialty_max_per_week = Column(Integer, default=10, nullable=False)

    # Academic time requirements
    academics_required = Column(Boolean, default=True, nullable=False)

    # Protected slots (JSON: {"wed_am": "conference", "fri_pm": "didactics"})
    # Keys: day_time (e.g., "mon_am", "tue_pm", "wed_am")
    # Values: activity type protecting the slot
    protected_slots = Column(JSONType, default=dict, nullable=False)

    # Allowed clinic days (JSON array: [0,1,2,3,4] for Mon-Fri, 0=Monday)
    # Empty array = all weekdays allowed
    allowed_clinic_days = Column(JSONType, default=list, nullable=False)

    # Optional descriptive fields
    specialty_name = Column(
        String(255), nullable=True
    )  # e.g., "Neurology", "Dermatology"
    description = Column(String(1024), nullable=True)  # Optional notes

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    rotation_template = relationship(
        "RotationTemplate",
        back_populates="weekly_requirements",
    )

    def __repr__(self):
        return (
            f"<ResidentWeeklyRequirement("
            f"template_id='{self.rotation_template_id}', "
            f"fm_clinic={self.fm_clinic_min_per_week}-{self.fm_clinic_max_per_week}, "
            f"specialty={self.specialty_min_per_week}-{self.specialty_max_per_week})>"
        )

    @property
    def total_min_halfdays(self) -> int:
        """Minimum half-days required per week."""
        academics = 1 if self.academics_required else 0
        return self.fm_clinic_min_per_week + self.specialty_min_per_week + academics

    @property
    def total_max_halfdays(self) -> int:
        """Maximum half-days allowed per week."""
        academics = 1 if self.academics_required else 0
        return self.fm_clinic_max_per_week + self.specialty_max_per_week + academics

    @property
    def is_valid_range(self) -> bool:
        """Check if min/max ranges are valid (min <= max)."""
        return (
            self.fm_clinic_min_per_week <= self.fm_clinic_max_per_week
            and self.specialty_min_per_week <= self.specialty_max_per_week
        )

    def get_allowed_days_set(self) -> set[int]:
        """Get allowed clinic days as a set of weekday integers (0=Mon, 4=Fri)."""
        if not self.allowed_clinic_days:
            return {0, 1, 2, 3, 4}  # Default: all weekdays
        return set(self.allowed_clinic_days)

    def is_slot_protected(self, day: int, time_of_day: str) -> bool:
        """
        Check if a specific slot is protected.

        Args:
            day: Weekday (0=Mon, 4=Fri)
            time_of_day: "AM" or "PM"

        Returns:
            True if slot is protected, False otherwise
        """
        if not self.protected_slots:
            return False
        day_names = ["mon", "tue", "wed", "thu", "fri"]
        if day < 0 or day > 4:
            return False
        slot_key = f"{day_names[day]}_{time_of_day.lower()}"
        return slot_key in self.protected_slots
