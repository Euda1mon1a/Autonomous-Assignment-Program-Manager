"""Rotation half-day requirement model - defines half-day composition per rotation."""

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


class RotationHalfDayRequirement(Base):
    """
    Defines half-day composition for a rotation template.

    Instead of rigid template matching, this model specifies:
    - How many FM Clinic half-days per block
    - How many specialty half-days per block
    - Academic time requirements
    - Optimization preferences

    The solver uses these requirements to optimally place activities
    while respecting protected time (Wednesday academics).

    Example:
        Neurology Elective:
        - fm_clinic_halfdays = 4
        - specialty_halfdays = 6
        - specialty_name = "Neurology"
        - academics_halfdays = 1 (Wednesday AM)

    SQLAlchemy Relationships:
        rotation_template: One-to-one to RotationTemplate.
            Back-populates RotationTemplate.halfday_requirements.
            FK ondelete=CASCADE. Unique constraint enforces one-to-one.
    """

    __tablename__ = "rotation_halfday_requirements"

    # Enforce one-to-one relationship at DB level
    __table_args__ = (
        UniqueConstraint(
            "rotation_template_id",
            name="uq_rotation_halfday_template",
        ),
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    rotation_template_id = Column(
        GUID(),
        ForeignKey("rotation_templates.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Activity breakdown per block (13 blocks/year, typically 10 half-days each)
    fm_clinic_halfdays = Column(Integer, default=4, nullable=False)
    specialty_halfdays = Column(Integer, default=5, nullable=False)  # 4+5+1=10
    specialty_name = Column(String(255))  # e.g., "Neurology", "Dermatology"
    academics_halfdays = Column(Integer, default=1, nullable=False)  # Wednesday AM
    elective_halfdays = Column(Integer, default=0)  # Flexible/buffer time

    # Constraints and preferences
    min_consecutive_specialty = Column(Integer, default=1)  # Batch specialty days?
    prefer_combined_clinic_days = Column(
        Boolean, default=True
    )  # FM + specialty same day

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rotation_template = relationship(
        "RotationTemplate", back_populates="halfday_requirements"
    )

    def __repr__(self):
        return (
            f"<RotationHalfDayRequirement("
            f"specialty='{self.specialty_name}', "
            f"fm_clinic={self.fm_clinic_halfdays}, "
            f"specialty={self.specialty_halfdays})>"
        )

    @property
    def total_halfdays(self) -> int:
        """Total half-days required per block."""
        return (
            self.fm_clinic_halfdays
            + self.specialty_halfdays
            + self.academics_halfdays
            + (self.elective_halfdays or 0)
        )

    @property
    def is_balanced(self) -> bool:
        """Check if total half-days equals standard block (10)."""
        return self.total_halfdays == 10
