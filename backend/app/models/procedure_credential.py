"""ProcedureCredential model - tracks faculty credentials for procedures."""
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class ProcedureCredential(Base):
    """
    Represents a faculty member's credential to supervise a specific procedure.

    This tracks:
    - Which faculty can supervise which procedures
    - Credential status (active, expired, suspended)
    - Credential dates (issue, expiration)
    - Competency level
    - Supervision capacity limits
    """
    __tablename__ = "procedure_credentials"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    ***REMOVED*** Links to person (faculty) and procedure
    person_id = Column(GUID(), ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    procedure_id = Column(GUID(), ForeignKey("procedures.id", ondelete="CASCADE"), nullable=False)

    ***REMOVED*** Credential status
    status = Column(String(50), nullable=False, default='active')  ***REMOVED*** 'active', 'expired', 'suspended', 'pending'

    ***REMOVED*** Competency level
    competency_level = Column(String(50), default='qualified')  ***REMOVED*** 'trainee', 'qualified', 'expert', 'master'

    ***REMOVED*** Dates
    issued_date = Column(Date, default=date.today)
    expiration_date = Column(Date)  ***REMOVED*** NULL means no expiration
    last_verified_date = Column(Date)

    ***REMOVED*** Supervision capacity (overrides procedure default)
    max_concurrent_residents = Column(Integer)  ***REMOVED*** NULL uses procedure default
    max_per_week = Column(Integer)  ***REMOVED*** Max supervisions per week, NULL = unlimited
    max_per_academic_year = Column(Integer)  ***REMOVED*** NULL = unlimited

    ***REMOVED*** Notes
    notes = Column(Text)

    ***REMOVED*** Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ***REMOVED*** Relationships
    person = relationship("Person", back_populates="procedure_credentials")
    procedure = relationship("Procedure", back_populates="credentials")

    ***REMOVED*** Unique constraint: one credential per person per procedure
    __table_args__ = (
        UniqueConstraint('person_id', 'procedure_id', name='uq_person_procedure_credential'),
    )

    def __repr__(self):
        return f"<ProcedureCredential(person_id='{self.person_id}', procedure_id='{self.procedure_id}', status='{self.status}')>"

    @property
    def is_valid(self) -> bool:
        """Check if credential is currently valid."""
        if self.status != 'active':
            return False
        return not (self.expiration_date and self.expiration_date < date.today())

    @property
    def is_expired(self) -> bool:
        """Check if credential has expired."""
        return bool(self.expiration_date and self.expiration_date < date.today())
