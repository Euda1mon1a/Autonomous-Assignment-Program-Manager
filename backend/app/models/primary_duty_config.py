"""Primary duty configuration — DB-backed replacement for Airtable JSON export."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base
from app.db.types import GUID


class PrimaryDutyConfiguration(Base):
    """
    Per-faculty primary duty configuration.

    Replaces the Airtable JSON export (sanitized_primary_duties.json).
    Coordinators can edit these from the admin UI to control faculty
    clinic limits and availability without a code deploy.
    """

    __tablename__ = "primary_duty_configs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    duty_name = Column(String(100), nullable=False, unique=True, index=True)
    clinic_min_per_week = Column(Integer, nullable=False, default=0)
    clinic_max_per_week = Column(Integer, nullable=False, default=10)
    available_days = Column(
        JSONB,
        nullable=False,
        server_default="[0,1,2,3,4]",
        comment="Available weekdays as JSON array (0=Mon, 4=Fri)",
    )
    faculty_ids = Column(
        JSONB,
        nullable=True,
        comment="Person UUIDs linked to this duty (optional, for lookup)",
    )
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def __repr__(self) -> str:
        return (
            f"<PrimaryDutyConfiguration(duty='{self.duty_name}', "
            f"clinic={self.clinic_min_per_week}-{self.clinic_max_per_week})>"
        )
