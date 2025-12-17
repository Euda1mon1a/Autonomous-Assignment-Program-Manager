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


class Absence(Base):
    """
    Represents an absence period for a person.

    Types include:
    - vacation: Regular leave
    - deployment: Military deployment (orders-based)
    - tdy: Temporary Duty (military)
    - medical: Medical leave
    - family_emergency: Emergency leave

    Version history is tracked via SQLAlchemy-Continuum.
    Access history: absence.versions
    """
    __tablename__ = "absences"
    __versioned__ = {}  # Enable audit trail - tracks all changes with who/what/when

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    person_id = Column(GUID(), ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    absence_type = Column(String(50), nullable=False)

    # Blocking vs partial absence
    # True = blocks entire period (deployment, extended medical leave)
    # False = partial absence, should be tracked but doesn't prevent assignment (single day, appointment)
    is_blocking = Column(Boolean, default=False)

    # Military-specific
    deployment_orders = Column(Boolean, default=False)
    tdy_location = Column(String(255))

    # Replacement activity (shown in schedule)
    replacement_activity = Column(String(255))  # e.g., "TDY - Korea"

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    person = relationship("Person", back_populates="absences")

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="check_absence_dates"),
        CheckConstraint(
            "absence_type IN ('vacation', 'deployment', 'tdy', 'medical', 'family_emergency', 'conference')",
            name="check_absence_type"
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
        - Otherwise, auto-determine based on absence type:
          - Blocking: deployment, extended medical (>7 days), TDY
          - Partial: vacation (<=7 days), conference, family_emergency, short medical
        """
        if self.is_blocking is not None:
            return self.is_blocking

        # Auto-determine based on type and duration
        if self.absence_type in ("deployment", "tdy"):
            return True

        # Medical leave >7 days is blocking, everything else is partial
        return self.absence_type == "medical" and self.duration_days > 7
