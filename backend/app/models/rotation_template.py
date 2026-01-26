"""Rotation template model - reusable rotation patterns."""

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

    NOTE on terminology:
    - RotationTemplate = the rotation (multi-week container).
    - rotation_type = rotation category/setting (NOT an Activity).
    """

    __tablename__ = "rotation_templates"
    __versioned__ = {}  # Enable audit trail - tracks all changes with who/what/when

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(
        String(255), nullable=False
    )  # e.g., "PGY-1 Clinic", "FMIT", "Sports Medicine"
    # Rotation category/setting (not an Activity). Used for solver filtering + constraints.
    rotation_type = Column(
        String(255), nullable=False
    )  # "clinic", "inpatient", "outpatient", "procedure", "procedures", "conference", "education", "lecture", "absence", "off", "recovery"

    # Template category for UI grouping and filtering
    # - rotation: Clinical work (clinic, inpatient, outpatient, procedure)
    # - time_off: ACGME-protected rest (off, recovery)
    # - absence: Days away from program (absence rotation type)
    # - educational: Structured learning (conference, education, lecture)
    template_category = Column(
        String(20),
        nullable=False,
        default="rotation",
        index=True,
    )

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

    # Block duration settings
    # is_block_half_rotation: True = 14 days (2 weeks), False = 28 days (4 weeks)
    is_block_half_rotation = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="True for half-block rotations (14 days instead of 28)",
    )

    # Weekend work configuration
    # True = rotation includes weekend assignments (Night Float, FMIT, etc.)
    # False = weekends are automatically off (most outpatient rotations)
    includes_weekend_work = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="True if rotation includes weekend assignments",
    )

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
    activity_requirements = relationship(
        "RotationActivityRequirement",
        back_populates="rotation_template",
        cascade="all, delete-orphan",
        order_by="RotationActivityRequirement.priority.desc()",
    )

    def __repr__(self):
        return f"<RotationTemplate(name='{self.name}', type='{self.rotation_type}')>"

    @property
    def has_capacity_limit(self) -> bool:
        """Check if this template has a capacity limit."""
        return self.max_residents is not None and self.max_residents > 0

    @property
    def requires_specialty_faculty(self) -> bool:
        """Check if this template requires specialty faculty."""
        return self.requires_specialty is not None
