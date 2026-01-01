"""Assignment model - the actual schedule."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID, JSONType


class Assignment(Base):
    """
    Represents a schedule assignment - linking a person to a block.

    This is the core of the schedule - each assignment says:
    "Person X is doing Activity Y on Block Z in Role R"

    Version history is tracked via SQLAlchemy-Continuum.
    Access history: assignment.versions

    Performance Optimization Notes:
    - Consider adding composite index on (person_id, block_id) for faster lookups
    - Consider adding composite index on (block_id, role) for role-based queries
    - Consider adding index on created_at for temporal queries
    - The schedule_run_id already has an index for provenance tracking

    Suggested indexes (add via Alembic migration):
    CREATE INDEX idx_assignments_person_block ON assignments(person_id, block_id);
    CREATE INDEX idx_assignments_block_role ON assignments(block_id, role);
    CREATE INDEX idx_assignments_created_at ON assignments(created_at);
    CREATE INDEX idx_assignments_person_created ON assignments(person_id, created_at DESC);
    """

    __tablename__ = "assignments"
    __versioned__ = {}  # Enable audit trail - tracks all changes with who/what/when

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    block_id = Column(
        GUID(),
        ForeignKey("blocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # Performance: Indexed for frequent foreign key lookups
    )
    person_id = Column(
        GUID(),
        ForeignKey("people.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # Performance: Indexed for frequent foreign key lookups
    )
    rotation_template_id = Column(
        GUID(), ForeignKey("rotation_templates.id"), index=True
    )  # Performance: Indexed for template-based queries

    role = Column(String(50), nullable=False)  # 'primary', 'supervising', 'backup'

    # Override fields (for manual adjustments)
    activity_override = Column(String(255))  # If different from template
    notes = Column(Text)
    override_reason = Column(Text)  # Reason for acknowledging ACGME violations
    override_acknowledged_at = Column(
        DateTime
    )  # When user acknowledged ACGME violation

    # Explainability fields - transparency into scheduling decisions
    explain_json = Column(JSONType())  # Full DecisionExplanation as JSON
    confidence = Column(Float)  # Confidence score 0-1
    score = Column(Float)  # Objective score for this assignment
    alternatives_json = Column(
        JSONType()
    )  # Top alternatives considered (AlternativeCandidate[])
    audit_hash = Column(
        String(64)
    )  # SHA-256 of inputs+outputs for integrity verification

    # Audit
    created_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Provenance - link to the schedule run that created this assignment
    schedule_run_id = Column(
        GUID(),
        ForeignKey("schedule_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    block = relationship("Block", back_populates="assignments")
    person = relationship("Person", back_populates="assignments")
    rotation_template = relationship("RotationTemplate", back_populates="assignments")
    schedule_run = relationship("ScheduleRun", backref="assignments")

    __table_args__ = (
        UniqueConstraint("block_id", "person_id", name="unique_person_per_block"),
        CheckConstraint(
            "role IN ('primary', 'supervising', 'backup')", name="check_role"
        ),
    )

    def __repr__(self):
        return f"<Assignment(person_id='{self.person_id}', role='{self.role}')>"

    @property
    def activity_name(self) -> str:
        """Get the activity name (override or template name)."""
        if self.activity_override:
            return self.activity_override
        if self.rotation_template:
            return self.rotation_template.name
        return "Unassigned"

    @property
    def abbreviation(self) -> str:
        """Get abbreviation for Excel export."""
        if self.rotation_template and self.rotation_template.abbreviation:
            return self.rotation_template.abbreviation
        return self.activity_name[:3].upper()
