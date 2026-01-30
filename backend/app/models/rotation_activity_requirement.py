"""Rotation activity requirement model for dynamic per-activity constraints.

This model replaces the fixed-field RotationHalfDayRequirement with a flexible
one-to-many structure allowing any number of activity requirements per rotation.

Key features:
- Dynamic: Add any activity as a requirement
- Week-specific: Can apply to all weeks or specific weeks (1-4)
- Soft constraints: min/max/target with priority for solver optimization
- Scheduling preferences: prefer_full_days, preferred_days, avoid_days

Example for Neurology Elective rotation:
- Activity=FM Clinic, min=4, max=4, weeks=all
- Activity=Specialty, min=5, max=6, weeks=all
- Activity=LEC, min=1, max=1, weeks=[1,2,3]
- Activity=Advising, min=1, max=1, weeks=[4]
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class RotationActivityRequirement(Base):
    """
    Dynamic per-activity requirements for a rotation template.

    This model enables flexible specification of how many half-days of each
    activity should be assigned within a rotation block. Unlike the legacy
    RotationHalfDayRequirement with fixed fields, this supports:

    1. Any number of activities per rotation
    2. Week-specific requirements (weeks 1-3 vs week 4)
    3. Soft constraints with priority for solver optimization
    4. Scheduling preferences (full days, preferred days)

    Attributes:
        rotation_template_id: The rotation this requirement belongs to
        activity_id: The activity being constrained
        min_halfdays: Minimum half-days required (hard constraint)
        max_halfdays: Maximum half-days allowed (hard constraint)
        target_halfdays: Preferred count (soft constraint for optimization)
        applicable_weeks: JSON array of weeks [1,2,3,4] or null for all weeks
        prefer_full_days: If true, solver prefers AM+PM same day for this activity
        preferred_days: JSON array of day numbers [1,2,3,4,5] (Mon-Fri)
        avoid_days: JSON array of days to avoid [0,6] (Sun, Sat)
        priority: 0-100, higher = more important to satisfy (soft constraint)

    SQLAlchemy Relationships:
        rotation_template: Many-to-one to RotationTemplate.
            FK ondelete=CASCADE.

        activity: Many-to-one to Activity.
            FK ondelete=RESTRICT (can't delete activity if used in requirements).

    Example usage:
        # Require 4 FM clinic half-days per block
        fm_req = RotationActivityRequirement(
            rotation_template_id=neurology.id,
            activity_id=fm_clinic.id,
            min_halfdays=4,
            max_halfdays=4,
            target_halfdays=4,
            priority=80,  # High priority
            prefer_full_days=True,
        )

        # LEC only weeks 1-3 (week 4 is different)
        lec_req = RotationActivityRequirement(
            rotation_template_id=neurology.id,
            activity_id=lec.id,
            min_halfdays=1,
            max_halfdays=1,
            applicable_weeks=[1, 2, 3],  # Not week 4
            priority=100,  # Highest - protected time
        )
    """

    __tablename__ = "rotation_activity_requirements"

    # Unique constraint: one requirement per activity per rotation per week scope
    # This allows separate requirements for same activity with different week scopes
    __table_args__ = (
        UniqueConstraint(
            "rotation_template_id",
            "activity_id",
            "applicable_weeks_hash",
            name="uq_rotation_activity_req",
        ),
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    rotation_template_id = Column(
        GUID(),
        ForeignKey("rotation_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    activity_id = Column(
        GUID(),
        ForeignKey("activities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Quantity requirements (half-days per block or per applicable_weeks scope)
    min_halfdays = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Minimum half-days required (hard constraint)",
    )
    max_halfdays = Column(
        Integer,
        default=14,
        nullable=False,
        comment="Maximum half-days allowed (hard constraint)",
    )
    target_halfdays = Column(
        Integer,
        nullable=True,
        comment="Preferred count (soft constraint for solver optimization)",
    )

    # Week scope: which weeks does this requirement apply to?
    # NULL = entire block (all 4 weeks)
    # [1,2,3] = weeks 1-3 only
    # [4] = week 4 only
    applicable_weeks = Column(
        JSONB,
        nullable=True,
        comment="JSON array of week numbers [1,2,3,4] or null for all weeks",
    )

    # Hash of applicable_weeks for unique constraint
    # Computed as: NULL -> 'all', [1,2,3] -> '1,2,3', [4] -> '4'
    applicable_weeks_hash = Column(
        GUID(),
        nullable=False,
        default=lambda: uuid.uuid5(uuid.NAMESPACE_DNS, "all"),
        comment="Hash of applicable_weeks for unique constraint",
    )

    # Scheduling preferences (soft constraints)
    prefer_full_days = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="If true, solver prefers AM+PM together for this activity",
    )
    preferred_days = Column(
        JSONB,
        nullable=True,
        comment="JSON array of preferred day numbers [1,2,3,4,5] (Mon-Fri)",
    )
    avoid_days = Column(
        JSONB,
        nullable=True,
        comment="JSON array of days to avoid [0,6] (Sun, Sat)",
    )

    # Priority for solver optimization
    # Higher priority = more important to satisfy
    # 0-30: Low priority (nice to have)
    # 31-60: Medium priority (should satisfy)
    # 61-90: High priority (strong preference)
    # 91-100: Critical (near-hard constraint)
    priority = Column(
        Integer,
        default=50,
        nullable=False,
        comment="0-100, higher = more important to satisfy (soft constraint)",
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    rotation_template = relationship(
        "RotationTemplate",
        back_populates="activity_requirements",
    )
    activity = relationship("Activity")

    def __repr__(self) -> str:
        weeks_str = f"W{self.applicable_weeks}" if self.applicable_weeks else "All"
        return (
            f"<RotationActivityRequirement "
            f"{self.min_halfdays}-{self.max_halfdays} half-days, {weeks_str}>"
        )

    @property
    def is_hard_constraint(self) -> bool:
        """Check if min == max (exact requirement)."""
        return self.min_halfdays == self.max_halfdays

    @property
    def weeks_display(self) -> str:
        """Human-readable week scope."""
        if self.applicable_weeks is None:
            return "All weeks"
        return f"Week{'s' if len(self.applicable_weeks) > 1 else ''} {', '.join(map(str, self.applicable_weeks))}"

    def compute_weeks_hash(self) -> uuid.UUID:
        """Compute hash for applicable_weeks for unique constraint."""
        if self.applicable_weeks is None:
            return uuid.uuid5(uuid.NAMESPACE_DNS, "all")
        weeks_str = ",".join(map(str, sorted(self.applicable_weeks)))
        return uuid.uuid5(uuid.NAMESPACE_DNS, weeks_str)

        # Event listener to auto-compute applicable_weeks_hash before insert/update


from sqlalchemy import event


@event.listens_for(RotationActivityRequirement, "before_insert")
@event.listens_for(RotationActivityRequirement, "before_update")
def compute_weeks_hash_before_save(mapper, connection, target) -> None:
    """Auto-compute applicable_weeks_hash before save."""
    target.applicable_weeks_hash = target.compute_weeks_hash()
