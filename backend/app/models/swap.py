"""Models for FMIT swap tracking."""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Boolean, Column, Date, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class SwapStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTED = "executed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"


class SwapType(str, Enum):
    ONE_TO_ONE = "one_to_one"
    ABSORB = "absorb"


class SwapRecord(Base):
    """Record of an FMIT swap between faculty members."""

    __tablename__ = "swap_records"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_faculty_id = Column(
        PGUUID(as_uuid=True), ForeignKey("people.id"), nullable=False
    )
    source_week = Column(Date, nullable=False)
    target_faculty_id = Column(
        PGUUID(as_uuid=True), ForeignKey("people.id"), nullable=False
    )
    target_week = Column(Date, nullable=True)
    swap_type = Column(SQLEnum(SwapType), nullable=False)
    status = Column(SQLEnum(SwapStatus), default=SwapStatus.PENDING, nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    requested_by_id = Column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approved_at = Column(DateTime, nullable=True)
    approved_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    executed_at = Column(DateTime, nullable=True)
    executed_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rolled_back_at = Column(DateTime, nullable=True)
    rolled_back_by_id = Column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    rollback_reason = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    source_faculty = relationship("Person", foreign_keys=[source_faculty_id])
    target_faculty = relationship("Person", foreign_keys=[target_faculty_id])

    __versioned__ = {}

    def __repr__(self) -> str:
        return f"<SwapRecord(id={self.id}, type='{self.swap_type.value}', status='{self.status.value}')>"


class SwapApproval(Base):
    """
    Approval record for a swap request.

    Tracks individual approvals required for swap execution.
    Different swap types require different approval workflows
    (e.g., source, target, coordinator approvals).
    """

    __tablename__ = "swap_approvals"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    swap_id = Column(
        PGUUID(as_uuid=True), ForeignKey("swap_records.id"), nullable=False
    )
    faculty_id = Column(PGUUID(as_uuid=True), ForeignKey("people.id"), nullable=False)
    role = Column(String(20), nullable=False)
    approved = Column(Boolean, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    response_notes = Column(Text, nullable=True)

    swap = relationship("SwapRecord", backref="approvals")
    faculty = relationship("Person")

    def __repr__(self) -> str:
        return f"<SwapApproval(id={self.id}, swap_id={self.swap_id}, role='{self.role}', approved={self.approved})>"
