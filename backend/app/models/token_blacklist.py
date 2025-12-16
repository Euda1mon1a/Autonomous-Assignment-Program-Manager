"""Token blacklist model for JWT invalidation."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Index

from app.db.base import Base
from app.db.types import GUID


class TokenBlacklist(Base):
    """
    Stores invalidated JWT tokens.

    When a user logs out, their token is added to this blacklist.
    Tokens are automatically cleaned up after expiration.

    This provides stateful token invalidation for the otherwise
    stateless JWT authentication system.
    """
    __tablename__ = "token_blacklist"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # The JWT ID (jti claim) - unique identifier for each token
    jti = Column(String(36), unique=True, nullable=False, index=True)

    # Token type (access, refresh)
    token_type = Column(String(20), default="access")

    # User who owned this token
    user_id = Column(GUID(), nullable=True)

    # When the token was blacklisted
    blacklisted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # When the token expires (for cleanup)
    expires_at = Column(DateTime, nullable=False, index=True)

    # Reason for blacklisting
    reason = Column(String(100), default="logout")

    __table_args__ = (
        Index('idx_blacklist_jti_expires', 'jti', 'expires_at'),
    )

    def __repr__(self):
        return f"<TokenBlacklist(jti='{self.jti}', reason='{self.reason}')>"

    @classmethod
    def is_blacklisted(cls, db, jti: str) -> bool:
        """
        Check if a token (by jti) is blacklisted.

        Args:
            db: Database session
            jti: JWT ID to check

        Returns:
            True if blacklisted, False otherwise
        """
        return db.query(cls).filter(cls.jti == jti).first() is not None

    @classmethod
    def cleanup_expired(cls, db) -> int:
        """
        Remove expired tokens from the blacklist.

        Should be called periodically (e.g., via Celery task).

        Args:
            db: Database session

        Returns:
            Number of tokens removed
        """
        now = datetime.utcnow()
        count = db.query(cls).filter(cls.expires_at < now).delete()
        db.commit()
        return count
