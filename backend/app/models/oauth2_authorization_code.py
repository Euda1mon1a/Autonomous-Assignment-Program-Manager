"""OAuth2 authorization code model for PKCE flow."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Index, String, Text

from app.db.base import Base
from app.db.types import GUID


class OAuth2AuthorizationCode(Base):
    """
    OAuth2 authorization code for PKCE flow.

    Authorization codes are short-lived tokens that can be exchanged
    for access tokens. With PKCE, they include a code challenge that
    must be verified during token exchange.
    """

    __tablename__ = "oauth2_authorization_codes"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # The authorization code itself (unique, short-lived)
    code = Column(String(255), unique=True, nullable=False, index=True)

    # Client that requested this code
    client_id = Column(String(255), nullable=False, index=True)

    # User who authorized this code
    user_id = Column(GUID(), nullable=False, index=True)

    # Redirect URI used in the authorization request
    redirect_uri = Column(String(512), nullable=False)

    # Scope granted (space-separated)
    scope = Column(Text, nullable=True)

    # PKCE code challenge (SHA256 hash of code verifier)
    code_challenge = Column(String(255), nullable=False)

    # PKCE code challenge method (S256 or plain)
    code_challenge_method = Column(String(10), nullable=False, default="S256")

    # State parameter for CSRF protection
    state = Column(String(255), nullable=True)

    # Nonce for OpenID Connect (optional)
    nonce = Column(String(255), nullable=True)

    # Whether this code has been used (codes are single-use)
    is_used = Column(String(10), default="false", nullable=False)

    # When this code was created
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # When this code expires (typically 10 minutes)
    expires_at = Column(DateTime, nullable=False, index=True)

    # When this code was used (if applicable)
    used_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_authz_code_client_user", "client_id", "user_id"),
        Index("idx_authz_code_expires", "expires_at", "is_used"),
    )

    def __repr__(self):
        return f"<OAuth2AuthorizationCode(code='{self.code[:8]}...', client_id='{self.client_id}')>"

    def is_expired(self) -> bool:
        """
        Check if this authorization code has expired.

        Returns:
            True if expired, False otherwise
        """
        return datetime.utcnow() > self.expires_at

    def mark_as_used(self) -> None:
        """Mark this authorization code as used."""
        self.is_used = "true"
        self.used_at = datetime.utcnow()

    @classmethod
    def cleanup_expired(cls, db) -> int:
        """
        Remove expired authorization codes.

        Should be called periodically (e.g., via Celery task).

        Args:
            db: Database session

        Returns:
            Number of codes removed
        """
        now = datetime.utcnow()
        count = db.query(cls).filter(cls.expires_at < now).delete()
        db.commit()
        return count
