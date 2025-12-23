"""Gateway authentication models for API keys, OAuth2 clients, and IP filtering."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class APIKey(Base):
    """
    API key for external service authentication.

    Supports key rotation, rate limiting, and usage tracking.
    Keys are hashed before storage for security.
    """

    __tablename__ = "api_keys"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Key identification
    name = Column(String(255), nullable=False, comment="Human-readable key name")
    key_hash = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="SHA-256 hash of the API key",
    )
    key_prefix = Column(
        String(16),
        nullable=False,
        index=True,
        comment="First 8 chars for identification (e.g., 'sk_live_12345678')",
    )

    # Ownership and permissions
    owner_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    owner = relationship("User", foreign_keys=[owner_id], backref="api_keys")

    scopes = Column(
        Text, nullable=True, comment="Comma-separated list of allowed scopes"
    )
    allowed_ips = Column(
        Text,
        nullable=True,
        comment="Comma-separated list of allowed IP addresses/CIDR ranges",
    )

    # Rate limiting (per API key)
    rate_limit_per_minute = Column(
        Integer,
        nullable=True,
        default=100,
        comment="Max requests per minute (null = unlimited)",
    )
    rate_limit_per_hour = Column(
        Integer,
        nullable=True,
        default=5000,
        comment="Max requests per hour (null = unlimited)",
    )

    # Status and lifecycle
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(
        DateTime, nullable=True, comment="Key expiration time (null = never)"
    )
    revoked_at = Column(DateTime, nullable=True)
    revoked_by_id = Column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    revoked_reason = Column(String(500), nullable=True)

    # Key rotation support
    rotated_from_id = Column(
        GUID(),
        ForeignKey("api_keys.id", ondelete="SET NULL"),
        nullable=True,
        comment="Previous key if this is a rotation",
    )
    rotated_to_id = Column(
        GUID(),
        ForeignKey("api_keys.id", ondelete="SET NULL"),
        nullable=True,
        comment="New key if this has been rotated",
    )

    # Usage tracking
    last_used_at = Column(DateTime, nullable=True)
    last_used_ip = Column(
        String(45), nullable=True, comment="Last IP address that used this key"
    )
    total_requests = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        Index("idx_api_key_active", "is_active", "expires_at"),
        Index("idx_api_key_owner", "owner_id", "is_active"),
    )

    def __repr__(self):
        return f"<APIKey(name='{self.name}', prefix='{self.key_prefix}', active={self.is_active})>"

    @property
    def is_expired(self) -> bool:
        """Check if the API key has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if the API key is valid (active, not expired, not revoked)."""
        return self.is_active and not self.is_expired and self.revoked_at is None

    def get_scopes(self) -> list[str]:
        """Get list of allowed scopes."""
        if not self.scopes:
            return []
        return [s.strip() for s in self.scopes.split(",") if s.strip()]

    def get_allowed_ips(self) -> list[str]:
        """Get list of allowed IP addresses/CIDR ranges."""
        if not self.allowed_ips:
            return []
        return [ip.strip() for ip in self.allowed_ips.split(",") if ip.strip()]


class OAuth2Client(Base):
    """
    OAuth2 client credentials for client_credentials flow.

    Used for machine-to-machine authentication.
    """

    __tablename__ = "oauth2_clients"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Client identification
    client_id = Column(String(255), nullable=False, unique=True, index=True)
    client_secret_hash = Column(
        String(255), nullable=False, comment="Hashed client secret (bcrypt)"
    )

    # Client metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Permissions and scopes
    scopes = Column(
        Text,
        nullable=False,
        default="read",
        comment="Comma-separated list of allowed scopes",
    )
    grant_types = Column(
        String(255),
        nullable=False,
        default="client_credentials",
        comment="Allowed OAuth2 grant types",
    )

    # Ownership
    owner_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    owner = relationship("User", backref="oauth2_clients")

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_confidential = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether client can keep secret confidential",
    )

    # Rate limiting
    rate_limit_per_minute = Column(Integer, nullable=True, default=100)
    rate_limit_per_hour = Column(Integer, nullable=True, default=5000)

    # Token settings
    access_token_lifetime_seconds = Column(
        Integer, default=3600, nullable=False, comment="Access token TTL in seconds"
    )

    # Usage tracking
    last_used_at = Column(DateTime, nullable=True)
    total_tokens_issued = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        Index("idx_oauth2_client_active", "is_active"),
        Index("idx_oauth2_client_owner", "owner_id", "is_active"),
    )

    def __repr__(self):
        return f"<OAuth2Client(name='{self.name}', client_id='{self.client_id}')>"

    def get_scopes(self) -> list[str]:
        """Get list of allowed scopes."""
        if not self.scopes:
            return []
        return [s.strip() for s in self.scopes.split(",") if s.strip()]

    def get_grant_types(self) -> list[str]:
        """Get list of allowed grant types."""
        return [gt.strip() for gt in self.grant_types.split(",") if gt.strip()]


class IPWhitelist(Base):
    """
    IP whitelist for gateway-level access control.

    Allows specific IP addresses or CIDR ranges to bypass certain restrictions.
    """

    __tablename__ = "ip_whitelists"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # IP specification
    ip_address = Column(
        String(45),
        nullable=False,
        index=True,
        comment="IP address or CIDR range (e.g., '192.168.1.0/24')",
    )

    # Metadata
    description = Column(String(500), nullable=True)
    owner_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    owner = relationship("User", backref="ip_whitelists")

    # Scope
    applies_to = Column(
        String(50),
        nullable=False,
        default="all",
        comment="What this whitelist applies to: 'all', 'api_keys', 'oauth2', etc.",
    )

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        Index("idx_ip_whitelist_active", "is_active", "expires_at"),
        Index("idx_ip_whitelist_applies_to", "applies_to", "is_active"),
    )

    def __repr__(self):
        return f"<IPWhitelist(ip='{self.ip_address}', applies_to='{self.applies_to}')>"

    @property
    def is_expired(self) -> bool:
        """Check if the whitelist entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if the whitelist entry is valid."""
        return self.is_active and not self.is_expired


class IPBlacklist(Base):
    """
    IP blacklist for blocking malicious or abusive IP addresses.

    Takes precedence over whitelist.
    """

    __tablename__ = "ip_blacklists"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # IP specification
    ip_address = Column(
        String(45),
        nullable=False,
        index=True,
        comment="IP address or CIDR range to block",
    )

    # Metadata
    reason = Column(String(500), nullable=False, comment="Reason for blocking")
    added_by_id = Column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    added_by = relationship("User", backref="ip_blacklists_added")

    # Detection metadata
    detection_method = Column(
        String(100),
        nullable=True,
        comment="How was this IP detected: 'manual', 'rate_limit', 'brute_force', etc.",
    )
    incident_count = Column(
        Integer, default=1, nullable=False, comment="Number of incidents from this IP"
    )

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(
        DateTime, nullable=True, comment="Auto-unblock time (null = permanent)"
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_hit_at = Column(
        DateTime, nullable=True, comment="Last time this IP attempted access"
    )

    __table_args__ = (
        Index("idx_ip_blacklist_active", "is_active", "expires_at"),
        Index("idx_ip_blacklist_detection", "detection_method", "is_active"),
    )

    def __repr__(self):
        return f"<IPBlacklist(ip='{self.ip_address}', reason='{self.reason[:50]}')>"

    @property
    def is_expired(self) -> bool:
        """Check if the blacklist entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if the blacklist entry is still in effect."""
        return self.is_active and not self.is_expired


class RequestSignature(Base):
    """
    Request signature verification log for HMAC-signed requests.

    Tracks signature verification attempts for audit and replay attack prevention.
    """

    __tablename__ = "request_signatures"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Request identification
    signature_hash = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Hash of the signature to prevent replay attacks",
    )
    api_key_id = Column(
        GUID(), ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=True
    )
    api_key = relationship("APIKey", backref="request_signatures")

    # Request metadata
    request_method = Column(String(10), nullable=False)
    request_path = Column(String(2000), nullable=False)
    request_timestamp = Column(
        DateTime, nullable=False, comment="Timestamp from request signature"
    )

    # Verification result
    is_valid = Column(Boolean, nullable=False)
    failure_reason = Column(String(255), nullable=True)

    # Source
    client_ip = Column(String(45), nullable=False)
    user_agent = Column(String(500), nullable=True)

    # Timestamp
    verified_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_request_signature_timestamp", "request_timestamp", "verified_at"),
        Index("idx_request_signature_api_key", "api_key_id", "verified_at"),
    )

    def __repr__(self):
        return f"<RequestSignature(method='{self.request_method}', path='{self.request_path[:50]}', valid={self.is_valid})>"
