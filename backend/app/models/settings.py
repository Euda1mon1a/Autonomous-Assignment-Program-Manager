"""Application settings model for database persistence."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Integer, String

from app.db.base import Base
from app.db.types import GUID


class ApplicationSettings(Base):
    """
    Application settings stored in database.

    This is a singleton table - only one row should exist.
    The row is created on first access with default values.
    """
    __tablename__ = "application_settings"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Scheduling algorithm configuration
    scheduling_algorithm = Column(
        String(50),
        nullable=False,
        default="greedy"
    )

    # Work hour limits (ACGME compliance)
    work_hours_per_week = Column(Integer, nullable=False, default=80)
    max_consecutive_days = Column(Integer, nullable=False, default=6)
    min_days_off_per_week = Column(Integer, nullable=False, default=1)

    # Supervision ratios by PGY level
    pgy1_supervision_ratio = Column(String(10), nullable=False, default="1:2")
    pgy2_supervision_ratio = Column(String(10), nullable=False, default="1:4")
    pgy3_supervision_ratio = Column(String(10), nullable=False, default="1:4")

    # Scheduling options
    enable_weekend_scheduling = Column(Boolean, nullable=False, default=True)
    enable_holiday_scheduling = Column(Boolean, nullable=False, default=False)
    default_block_duration_hours = Column(Integer, nullable=False, default=4)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "scheduling_algorithm IN ('greedy', 'min_conflicts', 'cp_sat', 'pulp', 'hybrid')",
            name="check_scheduling_algorithm"
        ),
        CheckConstraint(
            "work_hours_per_week >= 40 AND work_hours_per_week <= 100",
            name="check_work_hours"
        ),
        CheckConstraint(
            "max_consecutive_days >= 1 AND max_consecutive_days <= 7",
            name="check_consecutive_days"
        ),
        CheckConstraint(
            "min_days_off_per_week >= 1 AND min_days_off_per_week <= 3",
            name="check_days_off"
        ),
        CheckConstraint(
            "default_block_duration_hours >= 1 AND default_block_duration_hours <= 12",
            name="check_block_duration"
        ),
    )

    def __repr__(self):
        return f"<ApplicationSettings(algorithm='{self.scheduling_algorithm}', work_hours={self.work_hours_per_week})>"

    def to_dict(self) -> dict:
        """Convert settings to dictionary."""
        return {
            "scheduling_algorithm": self.scheduling_algorithm,
            "work_hours_per_week": self.work_hours_per_week,
            "max_consecutive_days": self.max_consecutive_days,
            "min_days_off_per_week": self.min_days_off_per_week,
            "pgy1_supervision_ratio": self.pgy1_supervision_ratio,
            "pgy2_supervision_ratio": self.pgy2_supervision_ratio,
            "pgy3_supervision_ratio": self.pgy3_supervision_ratio,
            "enable_weekend_scheduling": self.enable_weekend_scheduling,
            "enable_holiday_scheduling": self.enable_holiday_scheduling,
            "default_block_duration_hours": self.default_block_duration_hours,
        }
