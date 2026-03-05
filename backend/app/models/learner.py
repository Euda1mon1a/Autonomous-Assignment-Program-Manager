"""Learner models — med students and rotating interns on FM rotation.

Supports 7 concurrent learner tracks with staggered FMIT weeks.
Learners overlay existing clinic assignments (shadow attending/resident).

See: docs/archived/planning/MED_STUDENT_SCHEDULING_REQUIREMENTS.md
"""

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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


class LearnerTrack(Base):
    """
    Generic learner track template (1-7).

    Each track has a default FMIT week assignment (1-4) within a block.
    Actual learners are assigned to tracks for their rotation period.
    """

    __tablename__ = "learner_tracks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    track_number = Column(Integer, nullable=False, unique=True)
    default_fmit_week = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)

    # Relationships
    assignments = relationship(
        "LearnerToTrack", back_populates="track", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("track_number BETWEEN 1 AND 7", name="check_track_number"),
        CheckConstraint("default_fmit_week BETWEEN 1 AND 4", name="check_fmit_week"),
    )

    def __repr__(self) -> str:
        return f"<LearnerTrack(number={self.track_number}, fmit_week={self.default_fmit_week})>"


class LearnerToTrack(Base):
    """
    Assignment of a learner (person) to a track for a date range.

    A learner is a Person with type='med_student' or 'rotating_intern'.
    """

    __tablename__ = "learner_to_tracks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    learner_id = Column(
        GUID(), ForeignKey("people.id", ondelete="CASCADE"), nullable=False
    )
    track_id = Column(
        GUID(), ForeignKey("learner_tracks.id", ondelete="CASCADE"), nullable=False
    )
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Override defaults for this assignment
    requires_fmit = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    learner = relationship("Person", foreign_keys=[learner_id])
    track = relationship("LearnerTrack", back_populates="assignments")

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="check_learner_dates"),
        UniqueConstraint("learner_id", "start_date", name="uq_learner_start_date"),
    )

    def __repr__(self) -> str:
        return f"<LearnerToTrack(learner={self.learner_id}, track={self.track_id})>"


class LearnerAssignment(Base):
    """
    Pairs a learner with an existing clinic assignment (overlay model).

    Learners don't have their own clinic slots — they shadow an attending
    or senior resident during their assigned slot.
    """

    __tablename__ = "learner_assignments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    learner_id = Column(
        GUID(), ForeignKey("people.id", ondelete="CASCADE"), nullable=False
    )
    parent_assignment_id = Column(
        GUID(), ForeignKey("assignments.id", ondelete="CASCADE"), nullable=True
    )
    block_id = Column(
        GUID(), ForeignKey("blocks.id", ondelete="CASCADE"), nullable=False
    )

    # Activity type for this half-day
    activity_type = Column(
        String(20), nullable=False
    )  # FMIT, ASM, clinic, procedures, post_call, inprocessing, outprocessing

    # Day/time within the block
    day_of_week = Column(Integer, nullable=False)  # 0=Mon, 4=Fri
    time_of_day = Column(String(2), nullable=False)  # AM, PM

    # Source tracking
    source = Column(String(20), default="solver")  # solver, manual, preload

    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    learner = relationship("Person", foreign_keys=[learner_id])
    parent_assignment = relationship("Assignment", foreign_keys=[parent_assignment_id])
    block = relationship("Block", foreign_keys=[block_id])

    __table_args__ = (
        CheckConstraint(
            "activity_type IN ('FMIT', 'ASM', 'clinic', 'procedures', "
            "'post_call', 'inprocessing', 'outprocessing', 'didactics', 'advising')",
            name="check_learner_activity_type",
        ),
        CheckConstraint("day_of_week BETWEEN 0 AND 4", name="check_learner_day"),
        CheckConstraint("time_of_day IN ('AM', 'PM')", name="check_learner_time"),
        UniqueConstraint(
            "learner_id",
            "block_id",
            "day_of_week",
            "time_of_day",
            name="uq_learner_slot",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<LearnerAssignment(learner={self.learner_id}, "
            f"activity={self.activity_type}, day={self.day_of_week})>"
        )
