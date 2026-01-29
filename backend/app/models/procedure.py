"""Procedure model - medical procedures that can be supervised."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class Procedure(Base):
    """
    Represents a medical procedure that requires credentialed supervision.

    Examples:
    - Mastectomy
    - Botox injection
    - IUD placement/removal
    - Labor and delivery
    - Sports medicine clinic
    - Colposcopy
    - Vasectomy
    """

    __tablename__ = "procedures"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)

    # Categorization
    category = Column(String(100))  # e.g., 'surgical', 'office', 'obstetric', 'clinic'
    specialty = Column(String(100))  # e.g., 'Sports Medicine', 'OB/GYN', 'Dermatology'

    # Supervision requirements
    supervision_ratio = Column(
        Integer, default=1
    )  # Max residents per faculty (1 = 1:1)
    requires_certification = Column(
        Boolean, default=True
    )  # Must have explicit credential

    # Complexity/training
    complexity_level = Column(
        String(50), default="standard"
    )  # 'basic', 'standard', 'advanced', 'complex'
    min_pgy_level = Column(Integer, default=1)  # Minimum PGY level to perform

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    credentials = relationship(
        "ProcedureCredential", back_populates="procedure", cascade="all, delete-orphan"
    )
    activities = relationship("Activity", back_populates="procedure")

    def __repr__(self):
        return f"<Procedure(name='{self.name}', specialty='{self.specialty}')>"
