"""Models for faculty scheduling preferences."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class FacultyPreference(Base):
    """
    Faculty preferences for FMIT scheduling.

    Stores preferred/blocked weeks, limits, and notification preferences
    for the faculty self-service portal.
    """

    __tablename__ = "faculty_preferences"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Link to faculty member (one-to-one)
    faculty_id = Column(
        PGUUID(as_uuid=True), ForeignKey("people.id"), unique=True, nullable=False
    )

    # Week preferences (JSON arrays of ISO date strings)
    preferred_weeks = Column(JSON, default=list)  # Weeks they prefer to work
    blocked_weeks = Column(JSON, default=list)  # Weeks they cannot work

    # Scheduling limits
    max_weeks_per_month = Column(Integer, default=2)
    max_consecutive_weeks = Column(Integer, default=1)
    min_gap_between_weeks = Column(Integer, default=2)  # Minimum weeks between FMIT
    target_weeks_per_year = Column(Integer, default=6)  # Target annual FMIT count

    # Notification preferences
    notify_swap_requests = Column(Boolean, default=True)
    notify_schedule_changes = Column(Boolean, default=True)
    notify_conflict_alerts = Column(Boolean, default=True)
    notify_reminder_days = Column(Integer, default=7)  # Days before FMIT to remind

    # Contact preferences
    preferred_contact_method = Column(Text, default="email")  # email, sms, both

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    faculty = relationship("Person", backref="fmit_preferences")

    def add_preferred_week(self, week_date: str) -> None:
        """Add a week to preferred list."""
        if self.preferred_weeks is None:
            self.preferred_weeks = []
        if week_date not in self.preferred_weeks:
            self.preferred_weeks = self.preferred_weeks + [week_date]

    def add_blocked_week(self, week_date: str) -> None:
        """Add a week to blocked list."""
        if self.blocked_weeks is None:
            self.blocked_weeks = []
        if week_date not in self.blocked_weeks:
            self.blocked_weeks = self.blocked_weeks + [week_date]

    def remove_preferred_week(self, week_date: str) -> None:
        """Remove a week from preferred list."""
        if self.preferred_weeks and week_date in self.preferred_weeks:
            self.preferred_weeks = [w for w in self.preferred_weeks if w != week_date]

    def remove_blocked_week(self, week_date: str) -> None:
        """Remove a week from blocked list."""
        if self.blocked_weeks and week_date in self.blocked_weeks:
            self.blocked_weeks = [w for w in self.blocked_weeks if w != week_date]

    def is_week_blocked(self, week_date: str) -> bool:
        """Check if a week is blocked."""
        return self.blocked_weeks and week_date in self.blocked_weeks

    def is_week_preferred(self, week_date: str) -> bool:
        """Check if a week is preferred."""
        return self.preferred_weeks and week_date in self.preferred_weeks

    def __repr__(self) -> str:
        return f"<FacultyPreference(id={self.id}, faculty_id={self.faculty_id})>"
