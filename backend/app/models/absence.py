"""Absence model - leave, deployments, TDY."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID

# Valid absence types with their default blocking behavior
# Blocking types: person cannot be assigned to any rotation during absence
# Non-blocking types: tracked but person can still be assigned
ABSENCE_TYPES = {
    # Original types
    "vacation": False,  # Planned leave - non-blocking by default
    "deployment": True,  # Military deployment - always blocking
    "tdy": True,  # Temporary duty - always blocking
    "medical": None,  # Duration-based: >7 days = blocking
    "family_emergency": True,  # Emergency - blocking (Hawaii reality: 7+ days travel)
    "conference": False,  # Educational - non-blocking
    # New types (Hawaii-appropriate defaults)
    "bereavement": True,  # Death in family - blocking (mainland travel required)
    "emergency_leave": True,  # Urgent personal emergency - blocking
    "sick": None,  # Duration-based: >3 days = blocking
    "convalescent": True,  # Post-surgery/injury recovery - always blocking
    "maternity_paternity": True,  # Parental leave - always blocking
}

# Types that are always blocking regardless of duration
ALWAYS_BLOCKING_TYPES = {t for t, blocking in ABSENCE_TYPES.items() if blocking is True}


class Absence(Base):
    """
    Represents an absence period for a person.

    Types include:
    - vacation: Regular planned leave
    - deployment: Military deployment (orders-based)
    - tdy: Temporary Duty (military)
    - medical: Medical leave (blocking if >7 days)
    - family_emergency: Emergency leave (blocking - Hawaii travel reality)
    - conference: Educational conference
    - bereavement: Death in family (blocking - mainland travel)
    - emergency_leave: Urgent personal emergency (blocking)
    - sick: Short-term illness (blocking if >3 days)
    - convalescent: Post-surgery/injury recovery (blocking)
    - maternity_paternity: Parental leave (blocking)

    Version history is tracked via SQLAlchemy-Continuum.
    Access history: absence.versions
    """

    __tablename__ = "absences"
    __versioned__ = {}  # Enable audit trail - tracks all changes with who/what/when

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    person_id = Column(
        GUID(), ForeignKey("people.id", ondelete="CASCADE"), nullable=False
    )
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    absence_type = Column(String(50), nullable=False)

    # Blocking vs partial absence
    # True = blocks entire period (deployment, extended medical leave)
    # False = partial absence, should be tracked but doesn't prevent assignment (single day, appointment)
    is_blocking = Column(Boolean, default=False)

    # Away-from-program tracking for training extension threshold
    # Residents who exceed 28 days away from program per academic year must extend training
    # - Residents: defaults to True for all absence types (all time away counts)
    # - Faculty: always False (faculty don't have away-from-program tracking)
    # Note: Away rotations (Hilo, Okinawa, Kapiolani) are rotation templates, not absences
    is_away_from_program = Column(Boolean, nullable=False, default=True)

    # Return date tracking for admin workflow
    # When admin enters emergency absence, exact return date is often unknown
    # This flags the absence for follow-up to confirm actual return date
    return_date_tentative = Column(Boolean, default=False, nullable=False)

    # Track who entered the absence (for on-behalf-of workflow)
    # When admin enters absence for resident during emergency, this tracks who entered it
    created_by_id = Column(
        GUID(), ForeignKey("people.id", ondelete="SET NULL"), nullable=True
    )

    # Military-specific
    deployment_orders = Column(Boolean, default=False)
    tdy_location = Column(String(255))

    # Replacement activity (shown in schedule)
    replacement_activity = Column(String(255))  # e.g., "TDY - Korea"

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    person = relationship("Person", back_populates="absences", foreign_keys=[person_id])
    created_by = relationship("Person", foreign_keys=[created_by_id])

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="check_absence_dates"),
        CheckConstraint(
            "absence_type IN ('vacation', 'deployment', 'tdy', 'medical', 'family_emergency', "
            "'conference', 'bereavement', 'emergency_leave', 'sick', 'convalescent', 'maternity_paternity')",
            name="check_absence_type",
        ),
    )

    def __repr__(self):
        return f"<Absence(person_id='{self.person_id}', type='{self.absence_type}')>"

    @property
    def is_military(self) -> bool:
        """Check if this is a military-related absence."""
        return self.absence_type in ("deployment", "tdy")

    @property
    def duration_days(self) -> int:
        """Get the duration of the absence in days."""
        return (self.end_date - self.start_date).days + 1

    @property
    def should_block_assignment(self) -> bool:
        """
        Determine if this absence should block assignment to clinical blocks.

        Logic:
        - If is_blocking is explicitly set, use that value
        - Otherwise, auto-determine based on absence type (Hawaii-appropriate defaults):
          - Always blocking: deployment, tdy, family_emergency, bereavement,
            emergency_leave, convalescent, maternity_paternity
          - Duration-based: medical (>7 days), sick (>3 days)
          - Non-blocking: vacation, conference
        """
        if self.is_blocking is not None:
            return self.is_blocking

        # Auto-determine based on type and duration
        if self.absence_type in ALWAYS_BLOCKING_TYPES:
            return True

        # Duration-based blocking thresholds
        if self.absence_type == "medical":
            return self.duration_days > 7
        if self.absence_type == "sick":
            return self.duration_days > 3

        # Non-blocking types: vacation, conference
        return False
