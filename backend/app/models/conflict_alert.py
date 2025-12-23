"""Models for conflict alert tracking."""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class ConflictAlertStatus(str, Enum):
    """Status of a conflict alert."""

    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class ConflictSeverity(str, Enum):
    """Severity level of a conflict."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ConflictType(str, Enum):
    """Type of schedule conflict."""

    LEAVE_FMIT_OVERLAP = "leave_fmit_overlap"
    BACK_TO_BACK = "back_to_back"
    EXCESSIVE_ALTERNATING = "excessive_alternating"
    CALL_CASCADE = "call_cascade"
    EXTERNAL_COMMITMENT = "external_commitment"


class ConflictAlert(Base):
    """
    Alert record for a detected schedule conflict.

    Created when the conflict auto-detector finds issues
    between leave records and FMIT assignments.
    """

    __tablename__ = "conflict_alerts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Who is affected
    faculty_id = Column(PGUUID(as_uuid=True), ForeignKey("people.id"), nullable=False)

    # What type of conflict
    conflict_type = Column(SQLEnum(ConflictType), nullable=False)
    severity = Column(
        SQLEnum(ConflictSeverity), default=ConflictSeverity.WARNING, nullable=False
    )

    # When is the conflict
    fmit_week = Column(Date, nullable=False)

    # Related records
    leave_id = Column(PGUUID(as_uuid=True), ForeignKey("absences.id"), nullable=True)
    swap_id = Column(
        PGUUID(as_uuid=True), nullable=True
    )  # FK added when swap model wired

    # Status tracking
    status = Column(
        SQLEnum(ConflictAlertStatus), default=ConflictAlertStatus.NEW, nullable=False
    )

    # Description and notes
    description = Column(Text, nullable=False)
    resolution_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by_id = Column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    resolved_at = Column(DateTime, nullable=True)
    resolved_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    faculty = relationship("Person", foreign_keys=[faculty_id])
    leave = relationship("Absence", foreign_keys=[leave_id])
    acknowledged_by = relationship("User", foreign_keys=[acknowledged_by_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])

    def acknowledge(self, user_id: PGUUID) -> None:
        """Mark alert as acknowledged."""
        self.status = ConflictAlertStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.utcnow()
        self.acknowledged_by_id = user_id

    def resolve(self, user_id: PGUUID, notes: str = None) -> None:
        """Mark alert as resolved."""
        self.status = ConflictAlertStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
        self.resolved_by_id = user_id
        if notes:
            self.resolution_notes = notes

    def ignore(self, user_id: PGUUID, reason: str) -> None:
        """Mark alert as ignored (false positive)."""
        self.status = ConflictAlertStatus.IGNORED
        self.resolved_at = datetime.utcnow()
        self.resolved_by_id = user_id
        self.resolution_notes = f"Ignored: {reason}"
