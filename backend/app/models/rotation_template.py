"""Rotation template model - reusable activity patterns."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class RotationTemplate(Base):
    """
    Represents a reusable rotation template with constraints.

    Templates define activity patterns like:
    - PGY-1 Clinic (max 4 residents, supervision required)
    - Sports Medicine (requires specialty faculty)
    - FMIT Inpatient (24/7 coverage, NOT leave-eligible)
    """
    __tablename__ = "rotation_templates"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)  # e.g., "PGY-1 Clinic", "FMIT", "Sports Medicine"
    activity_type = Column(String(255), nullable=False)  # "clinic", "inpatient", "procedure", "conference"
    abbreviation = Column(String(10))  # For Excel export: "C", "FMIT", "LEC"

    # Leave eligibility
    # True = scheduled leave is allowed on this rotation (most electives, clinic)
    # False = leave not normally allowed, requires coverage (FMIT, inpatient coverage)
    # Emergency absences still generate conflict alerts regardless of this setting
    leave_eligible = Column(Boolean, default=True, nullable=False)

    # Clinic constraints
    clinic_location = Column(String(255))  # "Main Clinic", "Procedure Clinic"
    max_residents = Column(Integer)  # Physical space constraint
    requires_specialty = Column(String(255))  # "Sports Medicine", "Dermatology"
    requires_procedure_credential = Column(Boolean, default=False)

    # ACGME requirements
    supervision_required = Column(Boolean, default=True)
    max_supervision_ratio = Column(Integer, default=4)  # 1 faculty : N residents

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    assignments = relationship("Assignment", back_populates="rotation_template")

    def __repr__(self):
        return f"<RotationTemplate(name='{self.name}', type='{self.activity_type}')>"

    @property
    def has_capacity_limit(self) -> bool:
        """Check if this template has a capacity limit."""
        return self.max_residents is not None and self.max_residents > 0

    @property
    def requires_specialty_faculty(self) -> bool:
        """Check if this template requires specialty faculty."""
        return self.requires_specialty is not None
