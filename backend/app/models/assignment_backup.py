"""
Assignment Backup Model for Rollback Support.

Stores original assignment data before MODIFY and DELETE operations,
enabling complete rollback capability for schedule drafts.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.schedule_draft import ScheduleDraftAssignment


class AssignmentBackup(Base):
    """
    Backup of original assignment data for rollback support.

    Created before MODIFY or DELETE operations to preserve original state.
    Used during rollback to restore assignments to their pre-publish state.

    Attributes:
        id: Primary key
        draft_assignment_id: FK to the draft assignment that triggered backup
        original_assignment_id: ID of the original assignment (if applicable)
        backup_type: MODIFY or DELETE
        original_data_json: Complete original assignment data
        source_table: Table the backup came from (assignments or half_day_assignments)
        created_at: When backup was created
        restored_at: When backup was used for restoration (null if not restored)
        restored_by_id: User who triggered restoration
    """

    __tablename__ = "assignment_backups"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Link to draft assignment
    draft_assignment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("schedule_draft_assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Original assignment ID (may be null for HalfDayAssignment backups)
    original_assignment_id = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Backup type
    backup_type = Column(
        String(20),
        nullable=False,
    )

    # Original data as JSON
    original_data_json = Column(
        JSONB,
        nullable=False,
    )

    # Source table
    source_table = Column(
        String(50),
        nullable=False,
        default="half_day_assignments",
    )

    # Audit fields
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    restored_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    restored_by_id = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Relationship
    draft_assignment = relationship(
        "ScheduleDraftAssignment",
        back_populates="backups",
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "backup_type IN ('MODIFY', 'DELETE')",
            name="ck_assignment_backups_backup_type",
        ),
        Index(
            "idx_assignment_backups_unrestored",
            "draft_assignment_id",
            postgresql_where=text("restored_at IS NULL"),
        ),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "draft_assignment_id": str(self.draft_assignment_id),
            "original_assignment_id": str(self.original_assignment_id)
            if self.original_assignment_id
            else None,
            "backup_type": self.backup_type,
            "original_data_json": self.original_data_json,
            "source_table": self.source_table,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "restored_at": self.restored_at.isoformat() if self.restored_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<AssignmentBackup(id={self.id}, type={self.backup_type}, "
            f"draft_assignment={self.draft_assignment_id})>"
        )
