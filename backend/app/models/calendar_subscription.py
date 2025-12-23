"""Calendar subscription model for webcal feeds."""

import secrets
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class CalendarSubscription(Base):
    """
    Model for storing calendar subscription tokens.

    Allows users to subscribe to calendar feeds via webcal:// URLs.
    Tokens are secure, revocable, and optionally expire.
    """

    __tablename__ = "calendar_subscriptions"

    # Secure token for URL (32 bytes = 43 chars base64)
    token = Column(String(64), primary_key=True, index=True)

    # Person whose calendar is being subscribed to
    person_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("people.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # User who created the subscription (for audit)
    created_by_user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Optional label for the subscription
    label = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_accessed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Soft delete / revocation
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=True)

    # Optional: limit scope to specific date range or rotation types
    # NULL means "all future assignments"
    scope_start_date = Column(DateTime, nullable=True)
    scope_end_date = Column(DateTime, nullable=True)
    scope_rotation_types = Column(Text, nullable=True)  # JSON array of types

    # Relationships
    person = relationship("Person", backref="calendar_subscriptions")
    created_by = relationship("User", backref="created_calendar_subscriptions")

    @classmethod
    def generate_token(cls) -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(32)

    @classmethod
    def create(
        cls,
        person_id: UUID,
        created_by_user_id: UUID | None = None,
        label: str | None = None,
        expires_days: int | None = None,
    ) -> "CalendarSubscription":
        """
        Create a new calendar subscription.

        Args:
            person_id: Person whose calendar to subscribe to
            created_by_user_id: User creating the subscription
            label: Optional label for the subscription
            expires_days: Optional days until expiration (None = never)

        Returns:
            New CalendarSubscription instance
        """
        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)

        return cls(
            token=cls.generate_token(),
            person_id=person_id,
            created_by_user_id=created_by_user_id,
            label=label,
            expires_at=expires_at,
        )

    def is_valid(self) -> bool:
        """Check if the subscription is valid (active and not expired)."""
        if not self.is_active:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True

    def revoke(self) -> None:
        """Revoke the subscription."""
        self.is_active = False
        self.revoked_at = datetime.utcnow()

    def touch(self) -> None:
        """Update last accessed timestamp."""
        self.last_accessed_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"<CalendarSubscription(token={self.token[:8]}..., person_id={self.person_id})>"
