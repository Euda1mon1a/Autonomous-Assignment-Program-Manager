"""Activity log model for admin audit trail.

Tracks all administrative actions in the system for compliance and security auditing.
Supports user authentication events, CRUD operations, schedule modifications,
configuration changes, and swap approvals/rejections.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID, JSONType


class ActivityActionType(str, enum.Enum):
    """Types of activities that can be logged."""

    # User management actions
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"
    USER_LOCKED = "USER_LOCKED"
    USER_UNLOCKED = "USER_UNLOCKED"

    # Authentication actions
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"

    # Role and permission actions
    ROLE_CHANGED = "ROLE_CHANGED"
    PERMISSION_GRANTED = "PERMISSION_GRANTED"
    PERMISSION_REVOKED = "PERMISSION_REVOKED"

    # Invitation actions
    INVITE_SENT = "INVITE_SENT"
    INVITE_RESENT = "INVITE_RESENT"
    INVITE_ACCEPTED = "INVITE_ACCEPTED"

    # Bulk operations
    BULK_ACTIVATE = "BULK_ACTIVATE"
    BULK_DEACTIVATE = "BULK_DEACTIVATE"
    BULK_DELETE = "BULK_DELETE"

    # Schedule actions
    SCHEDULE_CREATED = "SCHEDULE_CREATED"
    SCHEDULE_UPDATED = "SCHEDULE_UPDATED"
    SCHEDULE_DELETED = "SCHEDULE_DELETED"
    SCHEDULE_PUBLISHED = "SCHEDULE_PUBLISHED"

    # Swap actions
    SWAP_REQUESTED = "SWAP_REQUESTED"
    SWAP_APPROVED = "SWAP_APPROVED"
    SWAP_REJECTED = "SWAP_REJECTED"
    SWAP_CANCELLED = "SWAP_CANCELLED"

    # Configuration actions
    SETTINGS_UPDATED = "SETTINGS_UPDATED"
    FEATURE_FLAG_TOGGLED = "FEATURE_FLAG_TOGGLED"

    # Generic CRUD for other entities
    ENTITY_CREATED = "ENTITY_CREATED"
    ENTITY_UPDATED = "ENTITY_UPDATED"
    ENTITY_DELETED = "ENTITY_DELETED"


class ActivityLog(Base):
    """
    Audit trail for all administrative actions in the system.

    This model maintains a complete, immutable record of all significant
    actions performed in the system. Entries should never be modified or
    deleted (except for data retention compliance).

    Security Considerations:
    - No cascade delete from users (preserve audit trail even if user deleted)
    - Entries are immutable (no UPDATE operations should be performed)
    - Retention policy: 2 years minimum for compliance
    - PHI in details should be minimized and anonymized where possible

    SQLAlchemy Relationships:
        admin_user: Many-to-one to User.
            The user who performed the action.
            FK ondelete=SET NULL to preserve logs if user is deleted.

        target_user: Many-to-one to User.
            The user affected by the action (for user management actions).
            FK ondelete=SET NULL to preserve logs if user is deleted.
    """

    __tablename__ = "activity_log"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # The user who performed the action (admin/coordinator)
    user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Action type from the enum
    action_type = Column(String(50), nullable=False, index=True)

    # Target entity type (e.g., "User", "Person", "Assignment", "SwapRequest")
    target_entity = Column(String(100), nullable=True)

    # Target entity ID (stored as string for flexibility with different ID types)
    target_id = Column(String(100), nullable=True)

    # Additional details as JSON (old values, new values, metadata)
    # IMPORTANT: Avoid storing cleartext PHI; use IDs or anonymized data
    details = Column(JSONType, nullable=True, default=dict)

    # Request metadata for security auditing
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(500), nullable=True)

    # Timestamp (immutable, no updated_at since entries should never change)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    admin_user = relationship(
        "User",
        foreign_keys=[user_id],
        backref="activity_logs_performed",
    )

    def __repr__(self) -> str:
        return (
            f"<ActivityLog(id={self.id}, action='{self.action_type}', "
            f"user_id={self.user_id}, created_at={self.created_at})>"
        )

    @classmethod
    def create_entry(
        cls,
        action_type: str | ActivityActionType,
        user_id: uuid.UUID | None = None,
        target_entity: str | None = None,
        target_id: str | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> "ActivityLog":
        """
        Factory method to create a new activity log entry.

        Args:
            action_type: Type of action being logged.
            user_id: ID of the user performing the action.
            target_entity: Type of entity affected (e.g., "User", "Person").
            target_id: ID of the affected entity.
            details: Additional context (avoid cleartext PHI).
            ip_address: Client IP address.
            user_agent: Client user agent string.

        Returns:
            New ActivityLog instance (not yet added to session).
        """
        if isinstance(action_type, ActivityActionType):
            action_type = action_type.value

        return cls(
            id=uuid.uuid4(),
            user_id=user_id,
            action_type=action_type,
            target_entity=target_entity,
            target_id=str(target_id) if target_id else None,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
        )
