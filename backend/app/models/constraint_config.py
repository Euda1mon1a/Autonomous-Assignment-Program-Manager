"""Persisted constraint configuration — DB-backed enable/disable/weight for solver constraints."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Float, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class ConstraintConfiguration(Base):
    """
    Persisted constraint configuration.

    Stores enable/disable state, weight, and priority for each constraint.
    On startup, the ConstraintConfigManager loads these overrides on top of
    its hardcoded defaults.
    """

    __tablename__ = "constraint_configurations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    enabled = Column(Boolean, nullable=False, default=True)
    weight = Column(Float, nullable=False, default=1.0)
    priority = Column(String(20), nullable=False, default="MEDIUM")
    category = Column(String(30), nullable=False)
    description = Column(Text, nullable=True)

    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
    updated_by = Column(String(100), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "priority IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')",
            name="check_constraint_priority",
        ),
        CheckConstraint("weight >= 0", name="check_constraint_weight_positive"),
    )

    def __repr__(self) -> str:
        return (
            f"<ConstraintConfiguration(name='{self.name}', "
            f"enabled={self.enabled}, weight={self.weight})>"
        )
