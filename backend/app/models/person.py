"""Person model - residents and faculty."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, CheckConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID, StringArrayType


class Person(Base):
    """
    Represents residents and faculty members.

    Residents have PGY levels (1-3) and are supervised.
    Faculty have specialties and can perform procedures.
    """
    __tablename__ = "people"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # 'resident' or 'faculty'
    email = Column(String(255), unique=True)

    # Resident-specific fields
    pgy_level = Column(Integer)  # 1, 2, or 3 for residents

    # Capacity/workload fields
    target_clinical_blocks = Column(Integer)  # Expected number of clinical blocks per scheduling period
    # Examples:
    # - Regular resident: 48-56 blocks (12-14 weeks * 4 blocks/week)
    # - Chief resident: 24 blocks (6 clinical + 6 admin)
    # - Research track: 8 blocks (2 clinical weeks)

    # Faculty-specific fields
    performs_procedures = Column(Boolean, default=False)
    specialties = Column(StringArrayType())  # e.g., ['Sports Medicine', 'Dermatology']
    primary_duty = Column(String(255))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignments = relationship("Assignment", back_populates="person")
    absences = relationship("Absence", back_populates="person")
    call_assignments = relationship("CallAssignment", back_populates="person")
    procedure_credentials = relationship("ProcedureCredential", back_populates="person", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("type IN ('resident', 'faculty')", name="check_person_type"),
        CheckConstraint("pgy_level IS NULL OR pgy_level BETWEEN 1 AND 3", name="check_pgy_level"),
    )

    def __repr__(self):
        return f"<Person(name='{self.name}', type='{self.type}')>"

    @property
    def is_resident(self) -> bool:
        """Check if person is a resident."""
        return self.type == "resident"

    @property
    def is_faculty(self) -> bool:
        """Check if person is faculty."""
        return self.type == "faculty"

    @property
    def supervision_ratio(self) -> int:
        """
        Get ACGME supervision ratio for this person.
        PGY-1: 1:2 (1 faculty per 2 residents)
        PGY-2/3: 1:4 (1 faculty per 4 residents)
        """
        if not self.is_resident:
            return 0
        return 2 if self.pgy_level == 1 else 4
