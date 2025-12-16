"""Procedure model - medical procedures that can be supervised."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
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

    ***REMOVED*** Categorization
    category = Column(String(100))  ***REMOVED*** e.g., 'surgical', 'office', 'obstetric', 'clinic'
    specialty = Column(String(100))  ***REMOVED*** e.g., 'Sports Medicine', 'OB/GYN', 'Dermatology'

    ***REMOVED*** Supervision requirements
    supervision_ratio = Column(Integer, default=1)  ***REMOVED*** Max residents per faculty (1 = 1:1)
    requires_certification = Column(Boolean, default=True)  ***REMOVED*** Must have explicit credential

    ***REMOVED*** Complexity/training
    complexity_level = Column(String(50), default='standard')  ***REMOVED*** 'basic', 'standard', 'advanced', 'complex'
    min_pgy_level = Column(Integer, default=1)  ***REMOVED*** Minimum PGY level to perform

    ***REMOVED*** Status
    is_active = Column(Boolean, default=True)

    ***REMOVED*** Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ***REMOVED*** Relationships
    credentials = relationship("ProcedureCredential", back_populates="procedure", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Procedure(name='{self.name}', specialty='{self.specialty}')>"
