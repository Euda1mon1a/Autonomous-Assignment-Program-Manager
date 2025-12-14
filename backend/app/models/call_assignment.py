"""Call assignment model - overnight and weekend call."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Date, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class CallAssignment(Base):
    """
    Represents a call assignment (overnight, weekend, backup).

    Call is tracked separately from regular assignments because:
    - Different duty hour calculations
    - Different rotation requirements
    - Critical coverage that can't be missed
    """
    __tablename__ = "call_assignments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False)
    person_id = Column(GUID(), ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    call_type = Column(String(50), nullable=False)  # 'overnight', 'weekend', 'backup'

    # Call metadata
    is_weekend = Column(Boolean, default=False)
    is_holiday = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    person = relationship("Person", back_populates="call_assignments")

    __table_args__ = (
        UniqueConstraint("date", "person_id", "call_type", name="unique_call_per_day"),
        CheckConstraint("call_type IN ('overnight', 'weekend', 'backup')", name="check_call_type"),
    )

    def __repr__(self):
        return f"<CallAssignment(date='{self.date}', type='{self.call_type}')>"

    @property
    def is_weekend_or_holiday(self) -> bool:
        """Check if this is a weekend or holiday call."""
        return self.is_weekend or self.is_holiday
