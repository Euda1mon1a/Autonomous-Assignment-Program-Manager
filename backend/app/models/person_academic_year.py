"""Person academic year model."""

import uuid
from datetime import datetime, timezone, UTC

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class PersonAcademicYear(Base):
    """
    Academic year scoped state for a person.
    Separates the biological person from their time-varying academic state.
    """

    __tablename__ = "person_academic_years"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    person_id = Column(
        GUID(), ForeignKey("people.id", ondelete="CASCADE"), nullable=False, index=True
    )
    academic_year = Column(Integer, nullable=False, index=True)

    # Academic state
    pgy_level = Column(Integer, nullable=True)
    is_graduated = Column(Boolean, default=False, nullable=False)

    # Clinic constraints for this AY
    clinic_min = Column(Integer, nullable=True)
    clinic_max = Column(Integer, nullable=True)

    # Call and FMIT equity tracking (naturally resets per AY)
    sunday_call_count = Column(Integer, default=0, nullable=False)
    weekday_call_count = Column(Integer, default=0, nullable=False)
    fmit_weeks_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # Relationships
    person = relationship("Person", back_populates="academic_years")

    __table_args__ = (
        UniqueConstraint("person_id", "academic_year", name="uq_person_academic_year"),
        CheckConstraint(
            "pgy_level IS NULL OR pgy_level BETWEEN 1 AND 3", name="check_ay_pgy_level"
        ),
    )

    def __repr__(self):
        return f"<PersonAcademicYear(person_id='{self.person_id}', ay={self.academic_year}, pgy={self.pgy_level})>"
