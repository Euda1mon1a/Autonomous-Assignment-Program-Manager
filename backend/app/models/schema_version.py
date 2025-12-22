"""Schema version model for schema registry."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)

from app.db.base import Base
from app.db.types import GUID


class SchemaCompatibilityType(str, Enum):
    """Schema compatibility types for evolution."""

    NONE = "none"  # No compatibility guarantees
    BACKWARD = "backward"  # New schema can read old data
    FORWARD = "forward"  # Old schema can read new data
    FULL = "full"  # Both backward and forward compatible
    TRANSITIVE = "transitive"  # Compatibility with all previous versions


class SchemaStatus(str, Enum):
    """Schema version status."""

    ACTIVE = "active"  # Currently in use
    DEPRECATED = "deprecated"  # Marked for removal, still usable
    ARCHIVED = "archived"  # No longer usable, kept for history
    DRAFT = "draft"  # Not yet published


class SchemaVersion(Base):
    """
    Schema version model for schema registry.

    Stores versioned Pydantic schemas with compatibility tracking,
    deprecation handling, and change documentation.

    Attributes:
        id: Unique identifier
        name: Schema name (e.g., 'PersonCreate', 'AssignmentResponse')
        version: Version number (semantic versioning)
        schema_definition: JSON representation of the Pydantic schema
        compatibility_type: How this version relates to previous versions
        status: Current status of this schema version
        is_default: Whether this is the default version for the schema
        deprecated_at: When this version was marked as deprecated
        archived_at: When this version was archived
        removed_at: When this version will be/was removed
        description: Human-readable description of the schema
        changelog: Description of changes from previous version
        migration_notes: Notes for migrating from previous version
        tags: Searchable tags for categorization
        created_by: User ID who created this version
        created_at: When this version was created
        updated_at: When this version was last updated
    """

    __tablename__ = "schema_versions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    schema_definition = Column(JSON, nullable=False)
    compatibility_type = Column(
        String(50), nullable=False, default=SchemaCompatibilityType.BACKWARD.value
    )
    status = Column(
        String(50), nullable=False, default=SchemaStatus.ACTIVE.value, index=True
    )
    is_default = Column(Boolean, default=False, nullable=False)

    # Deprecation tracking
    deprecated_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)
    removed_at = Column(DateTime, nullable=True)

    # Documentation
    description = Column(Text, nullable=True)
    changelog = Column(Text, nullable=True)
    migration_notes = Column(Text, nullable=True)
    tags = Column(JSON, default=list, nullable=False)

    # Metadata
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_schema_name_version"),
        CheckConstraint(
            f"compatibility_type IN ('{SchemaCompatibilityType.NONE.value}', "
            f"'{SchemaCompatibilityType.BACKWARD.value}', "
            f"'{SchemaCompatibilityType.FORWARD.value}', "
            f"'{SchemaCompatibilityType.FULL.value}', "
            f"'{SchemaCompatibilityType.TRANSITIVE.value}')",
            name="check_schema_compatibility_type",
        ),
        CheckConstraint(
            f"status IN ('{SchemaStatus.ACTIVE.value}', "
            f"'{SchemaStatus.DEPRECATED.value}', "
            f"'{SchemaStatus.ARCHIVED.value}', "
            f"'{SchemaStatus.DRAFT.value}')",
            name="check_schema_status",
        ),
        CheckConstraint("version > 0", name="check_version_positive"),
    )

    def __repr__(self) -> str:
        return (
            f"<SchemaVersion(name='{self.name}', "
            f"version={self.version}, status='{self.status}')>"
        )

    @property
    def is_usable(self) -> bool:
        """Check if this schema version can still be used."""
        return self.status in (SchemaStatus.ACTIVE.value, SchemaStatus.DEPRECATED.value)

    @property
    def is_active_or_draft(self) -> bool:
        """Check if this schema version is active or in draft."""
        return self.status in (SchemaStatus.ACTIVE.value, SchemaStatus.DRAFT.value)

    @property
    def full_name(self) -> str:
        """Get the full schema name with version."""
        return f"{self.name}:v{self.version}"


class SchemaChangeEvent(Base):
    """
    Schema change event for audit and notification tracking.

    Records all changes to schemas for compliance and notification purposes.

    Attributes:
        id: Unique identifier
        schema_version_id: ID of the schema version that changed
        schema_name: Name of the schema for quick lookup
        event_type: Type of change (created, updated, deprecated, etc.)
        previous_version: Previous version number (if applicable)
        new_version: New version number
        changed_by: User ID who made the change
        change_description: Description of what changed
        notification_sent: Whether notifications were sent
        notified_at: When notifications were sent
        metadata: Additional metadata about the change
        created_at: When the event occurred
    """

    __tablename__ = "schema_change_events"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    schema_version_id = Column(GUID(), nullable=False, index=True)
    schema_name = Column(String(255), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    previous_version = Column(Integer, nullable=True)
    new_version = Column(Integer, nullable=False)
    changed_by = Column(String(255), nullable=True)
    change_description = Column(Text, nullable=True)
    notification_sent = Column(Boolean, default=False, nullable=False)
    notified_at = Column(DateTime, nullable=True)
    event_metadata = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "event_type IN ('created', 'updated', 'deprecated', "
            "'archived', 'activated', 'made_default')",
            name="check_event_type",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<SchemaChangeEvent(schema='{self.schema_name}', "
            f"type='{self.event_type}', version={self.new_version})>"
        )
