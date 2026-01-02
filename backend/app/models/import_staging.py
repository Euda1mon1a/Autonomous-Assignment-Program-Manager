"""Import staging models for Excel import workflow.

Provides staging tables for import preview and batch operations:
- ImportBatch: Tracks import sessions with status and rollback capability
- ImportStagedAssignment: Staged assignments before commit to live tables

Workflow:
1. Upload Excel → Parse → Stage (ImportStagedAssignment records)
2. Review staged vs existing (preview conflicts)
3. Apply (commit to assignments table) or Reject
4. Rollback available for applied batches (within window)
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Date,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.person import Person
    from app.models.rotation_template import RotationTemplate
    from app.models.user import User


class ImportBatchStatus(str, enum.Enum):
    """Status of an import batch."""

    STAGED = "staged"  # Parsed and staged, awaiting review
    APPROVED = "approved"  # Approved, ready to apply
    REJECTED = "rejected"  # Rejected by user
    APPLIED = "applied"  # Applied to live tables
    ROLLED_BACK = "rolled_back"  # Applied then rolled back
    FAILED = "failed"  # Apply failed


class ConflictResolutionMode(str, enum.Enum):
    """How to handle conflicts during import apply."""

    REPLACE = "replace"  # Delete existing block assignments, insert staged
    MERGE = "merge"  # Keep existing, add new, skip conflicts
    UPSERT = "upsert"  # Update if person+date+slot exists, else insert


class StagedAssignmentStatus(str, enum.Enum):
    """Status of a staged assignment."""

    PENDING = "pending"  # Awaiting batch decision
    APPROVED = "approved"  # Will be applied
    SKIPPED = "skipped"  # User chose to skip
    APPLIED = "applied"  # Successfully applied
    FAILED = "failed"  # Apply failed


class ImportBatch(Base):
    """Tracks an import session/batch.

    Each Excel upload creates one batch. Batch can be:
    - Previewed (compare staged vs existing)
    - Applied (commit to assignments)
    - Rolled back (undo applied changes)
    """

    __tablename__ = "import_batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # File info
    filename = Column(String(255), nullable=True)
    file_hash = Column(String(64), nullable=True)  # SHA-256 for dedup detection
    file_size_bytes = Column(Integer, nullable=True)

    # Status tracking
    status = Column(
        Enum(ImportBatchStatus),
        nullable=False,
        default=ImportBatchStatus.STAGED,
    )
    conflict_resolution = Column(
        Enum(ConflictResolutionMode),
        nullable=False,
        default=ConflictResolutionMode.UPSERT,
    )

    # Target scope
    target_block = Column(Integer, nullable=True)
    target_start_date = Column(Date, nullable=True)
    target_end_date = Column(Date, nullable=True)

    # Metadata
    notes = Column(Text, nullable=True)
    row_count = Column(Integer, nullable=True)  # Total rows parsed
    error_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)

    # Apply tracking
    applied_at = Column(DateTime, nullable=True)
    applied_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rollback_available = Column(Boolean, default=True)
    rollback_expires_at = Column(DateTime, nullable=True)  # 24h window

    # Rollback tracking
    rolled_back_at = Column(DateTime, nullable=True)
    rolled_back_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    applied_by = relationship("User", foreign_keys=[applied_by_id])
    rolled_back_by = relationship("User", foreign_keys=[rolled_back_by_id])
    staged_assignments = relationship(
        "ImportStagedAssignment",
        back_populates="batch",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ImportBatch {self.id} status={self.status.value} file={self.filename}>"


class ImportStagedAssignment(Base):
    """A single staged assignment from an import batch.

    Stores parsed data with fuzzy match results and conflict detection.
    Not committed to live assignments table until batch is applied.
    """

    __tablename__ = "import_staged_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    batch_id = Column(
        UUID(as_uuid=True),
        ForeignKey("import_batches.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Source tracking
    row_number = Column(Integer, nullable=True)  # Original Excel row
    sheet_name = Column(String(100), nullable=True)

    # Raw parsed data
    person_name = Column(String(255), nullable=False)
    assignment_date = Column(Date, nullable=False)
    slot = Column(String(10), nullable=True)  # AM/PM or null for full day
    rotation_name = Column(String(255), nullable=True)
    raw_cell_value = Column(String(500), nullable=True)  # Original cell content

    # Fuzzy match results
    matched_person_id = Column(
        UUID(as_uuid=True),
        ForeignKey("people.id"),
        nullable=True,
    )
    person_match_confidence = Column(Integer, nullable=True)  # 0-100
    matched_rotation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rotation_templates.id"),
        nullable=True,
    )
    rotation_match_confidence = Column(Integer, nullable=True)  # 0-100

    # Conflict detection
    conflict_type = Column(String(50), nullable=True)  # none/duplicate/overwrite
    existing_assignment_id = Column(UUID(as_uuid=True), nullable=True)

    # Status
    status = Column(
        Enum(StagedAssignmentStatus),
        nullable=False,
        default=StagedAssignmentStatus.PENDING,
    )

    # Validation
    validation_errors = Column(JSONB, nullable=True)
    validation_warnings = Column(JSONB, nullable=True)

    # After apply - link to created assignment
    created_assignment_id = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    batch = relationship("ImportBatch", back_populates="staged_assignments")
    matched_person = relationship("Person", foreign_keys=[matched_person_id])
    matched_rotation = relationship("RotationTemplate", foreign_keys=[matched_rotation_id])

    def __repr__(self) -> str:
        return f"<ImportStagedAssignment {self.person_name} {self.assignment_date} {self.rotation_name}>"
