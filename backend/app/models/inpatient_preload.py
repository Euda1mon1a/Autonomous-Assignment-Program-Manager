"""InpatientPreload model - FMIT, Night Float, and other inpatient rotations.

This model stores preloaded inpatient rotation assignments that are locked
before the solver runs. These are the highest priority assignments.

Inpatient rotation types:
- FMIT: Family Medicine Inpatient Team (faculty and residents)
- NF: Night Float
- PedW: Pediatrics Ward
- PedNF: Pediatrics Night Float
- KAP: Kapiolani L&D (off-site)
- IM: Internal Medicine ward
- LDNF: L&D Night Float (R2)

FMIT Week Structure:
- Starts: Friday
- Ends: Thursday (following week)
- PC (Post-Call/Day Off): Friday after FMIT ends

Block 10 FMIT Faculty Example:
- Week 1 (Mar 13-19): Tagawa (overlaps from Block 9)
- Week 2 (Mar 20-26): Chu
- Week 3 (Mar 27-Apr 2): Bevis
- Week 4 (Apr 3-9): Chu
- (LaBounty overlaps into Block 11)
"""

import uuid
from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class InpatientRotationType(str, Enum):
    """Types of inpatient rotations that get preloaded."""

    FMIT = "FMIT"  # Family Medicine Inpatient Team
    NF = "NF"  # Night Float
    PEDW = "PedW"  # Pediatrics Ward
    PEDNF = "PedNF"  # Pediatrics Night Float
    KAP = "KAP"  # Kapiolani L&D (off-site, intern)
    IM = "IM"  # Internal Medicine ward
    LDNF = "LDNF"  # L&D Night Float (R2)


class PreloadAssignedBy(str, Enum):
    """Who assigned the preload."""

    CHIEF = "chief"  # Chief residents
    SCHEDULER = "scheduler"  # Scheduler/coordinator
    COORDINATOR = "coordinator"  # Program coordinator
    MANUAL = "manual"  # Manual override


class InpatientPreload(Base):
    """
    Preloaded inpatient rotation assignment.

    These assignments are locked before the solver runs and represent
    the highest priority source (source='preload' in half_day_assignments).

    Example:
        Dr. Chu on FMIT Week 2 (Mar 20-26):
        - person_id: Chu's UUID
        - rotation_type: FMIT
        - start_date: 2026-03-20 (Friday)
        - end_date: 2026-03-26 (Thursday)
        - fmit_week_number: 2
        - includes_post_call: True (PC on Friday Mar 27)

    FMIT Call Rules:
        During FMIT week, faculty covers:
        - Friday night call (start of FMIT)
        - Saturday night call
        Faculty CANNOT be on call Sun-Thu during FMIT (on service).
        Post-FMIT: PC on Friday, cannot be on call Saturday.
    """

    __tablename__ = "inpatient_preloads"

    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Core fields
    person_id = Column(
        GUID(),
        ForeignKey("people.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Person assigned to this inpatient rotation",
    )
    rotation_type = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Type: FMIT, NF, PedW, PedNF, KAP, IM, LDNF",
    )
    start_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="First day of rotation (e.g., Friday for FMIT)",
    )
    end_date = Column(
        Date,
        nullable=False,
        comment="Last day of rotation (e.g., Thursday for FMIT)",
    )

    # FMIT-specific fields
    fmit_week_number = Column(
        Integer,
        nullable=True,
        comment="FMIT week number (1-4) for faculty rotation",
    )
    includes_post_call = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="True if post-call (PC) day should be generated after end_date",
    )

    # Provenance
    assigned_by = Column(
        String(20),
        nullable=True,
        comment="Who assigned: chief, scheduler, coordinator, manual",
    )
    notes = Column(
        String(500),
        nullable=True,
        comment="Optional notes about this assignment",
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
    person = relationship("Person", back_populates="inpatient_preloads")

    # Constraints
    __table_args__ = (
        # Unique: one rotation type per person per start date
        UniqueConstraint(
            "person_id",
            "start_date",
            "rotation_type",
            name="uq_inpatient_preload_person_start_type",
        ),
        # Check constraints
        CheckConstraint(
            "rotation_type IN ('FMIT', 'NF', 'PedW', 'PedNF', 'KAP', 'IM', 'LDNF')",
            name="check_inpatient_rotation_type",
        ),
        CheckConstraint(
            "fmit_week_number IS NULL OR fmit_week_number BETWEEN 1 AND 4",
            name="check_fmit_week_number",
        ),
        CheckConstraint(
            "assigned_by IS NULL OR assigned_by IN ('chief', 'scheduler', 'coordinator', 'manual')",
            name="check_preload_assigned_by",
        ),
        CheckConstraint("end_date >= start_date", name="check_preload_dates"),
        # Indexes
        Index("idx_inpatient_preload_dates", "start_date", "end_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<InpatientPreload {self.rotation_type}: {self.person_id} "
            f"{self.start_date} to {self.end_date}>"
        )

    @property
    def is_fmit(self) -> bool:
        """Check if this is an FMIT rotation."""
        return self.rotation_type == InpatientRotationType.FMIT.value

    @property
    def is_night_float(self) -> bool:
        """Check if this is a night float rotation (NF, PedNF, or LDNF)."""
        return self.rotation_type in (
            InpatientRotationType.NF.value,
            InpatientRotationType.PEDNF.value,
            InpatientRotationType.LDNF.value,
        )

    @property
    def duration_days(self) -> int:
        """Get duration of rotation in days."""
        return (self.end_date - self.start_date).days + 1
