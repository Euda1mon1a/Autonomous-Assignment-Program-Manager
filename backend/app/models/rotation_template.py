"""Rotation template model - reusable activity patterns."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
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

    Version history is tracked via SQLAlchemy-Continuum.
    Access history: template.versions
    """

    __tablename__ = "rotation_templates"
    __versioned__ = {}  # Enable audit trail - tracks all changes with who/what/when

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(
        String(255), nullable=False
    )  # e.g., "PGY-1 Clinic", "FMIT", "Sports Medicine"
    activity_type = Column(
        String(255), nullable=False
    )  # "clinic", "inpatient", "outpatient", "procedure", "procedures", "conference", "education", "absence", "off", "recovery"
    abbreviation = Column(String(10))  # For Excel export: "C", "FMIT", "LEC"
    display_abbreviation = Column(String(20))  # User-facing code for schedule grid
    font_color = Column(String(50))  # Tailwind color class for text
    background_color = Column(String(50))  # Tailwind color class for background

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

    # Archive fields (soft delete)
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    archived_at = Column(DateTime, nullable=True)
    archived_by = Column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    assignments = relationship("Assignment", back_populates="rotation_template")
    halfday_requirements = relationship(
        "RotationHalfDayRequirement",
        back_populates="rotation_template",
        uselist=False,  # One-to-one relationship
        cascade="all, delete-orphan",
    )
    preferences = relationship(
        "RotationPreference",
        back_populates="rotation_template",
        cascade="all, delete-orphan",
    )
    weekly_patterns = relationship(
        "WeeklyPattern",
        back_populates="rotation_template",
        foreign_keys="[WeeklyPattern.rotation_template_id]",
        cascade="all, delete-orphan",
    )
    weekly_requirements = relationship(
        "ResidentWeeklyRequirement",
        back_populates="rotation_template",
        uselist=False,  # One-to-one relationship
        cascade="all, delete-orphan",
    )

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
