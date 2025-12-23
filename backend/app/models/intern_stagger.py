"""Intern stagger pattern model - defines PGY-1 orientation schedules."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Column, DateTime, Integer, String, Time

from app.db.base import Base
from app.db.types import GUID


class InternStaggerPattern(Base):
    """
    Represents an intern (PGY-1) staggered start pattern.

    Medical residency programs often stagger intern start times to ensure
    experienced coverage during orientation. This model defines the pattern:
    - Intern Group A starts earlier (e.g., 7 AM)
    - Intern Group B starts later (e.g., 9 AM)
    - Overlap period for handoff and supervision

    The overlap allows Group A interns to gain experience before
    supervising/training Group B interns during the overlap window.
    """

    __tablename__ = "intern_stagger_patterns"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)

    # Start times for each group
    intern_a_start = Column(Time, nullable=False)  # e.g., 07:00
    intern_b_start = Column(Time, nullable=False)  # e.g., 09:00

    # Overlap metrics
    overlap_duration_minutes = Column(Integer, nullable=False)  # e.g., 240 (4 hours)
    overlap_efficiency = Column(
        Integer, nullable=False, default=85
    )  # Percentage (0-100)

    # Experience requirements
    min_intern_a_experience_weeks = Column(
        Integer, nullable=False, default=2
    )  # Weeks before overlap starts

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    # Note: Will be connected to schedule assignments when intern staggering is implemented

    __table_args__ = (
        CheckConstraint("overlap_duration_minutes > 0", name="check_overlap_duration"),
        CheckConstraint(
            "overlap_efficiency BETWEEN 0 AND 100", name="check_overlap_efficiency"
        ),
        CheckConstraint(
            "min_intern_a_experience_weeks >= 0", name="check_min_experience"
        ),
    )

    def __repr__(self):
        return f"<InternStaggerPattern(name='{self.name}', overlap={self.overlap_duration_minutes}min)>"

    @property
    def overlap_hours(self) -> float:
        """
        Get overlap duration in hours.

        Returns:
            float: Overlap duration in hours (e.g., 4.0 for 240 minutes)
        """
        return self.overlap_duration_minutes / 60.0

    @property
    def effective_overlap_hours(self) -> float:
        """
        Get effective overlap hours accounting for efficiency.

        Returns:
            float: Effective overlap hours with efficiency factored in
        """
        return (self.overlap_duration_minutes / 60.0) * (
            self.overlap_efficiency / 100.0
        )

    @property
    def display_schedule(self) -> str:
        """
        Get human-readable schedule display.

        Returns:
            str: Formatted schedule string (e.g., "Group A: 07:00, Group B: 09:00 (4h overlap)")
        """
        return (
            f"Group A: {self.intern_a_start.strftime('%H:%M')}, "
            f"Group B: {self.intern_b_start.strftime('%H:%M')} "
            f"({self.overlap_hours:.1f}h overlap)"
        )
