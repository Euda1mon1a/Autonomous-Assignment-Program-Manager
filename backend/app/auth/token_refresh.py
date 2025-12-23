"""
Token refresh service with advanced security features.

Implements secure refresh token management with:
- Refresh token generation and storage in Redis
- Token rotation (new refresh token on each use)
- Refresh token revocation and family tracking
- Reuse detection (prevents token replay attacks)
- Sliding window expiration
- Device-bound tokens
- Concurrent session limiting
- Comprehensive metrics and monitoring

Security Model:
--------------
1. Token Families: Each refresh token belongs to a family identified by family_id.
   When a token is refreshed, a new child token is created in the same family.

2. Reuse Detection: If a revoked token is used, the entire family is revoked.
   This prevents attackers from using stolen tokens after the legitimate user
   has already refreshed.

3. Device Binding: Tokens are bound to device fingerprints (IP + user agent hash).
   Prevents tokens from being used on different devices.

4. Rotation: Every refresh generates a new token and revokes the old one.
   Limits the window of opportunity for token theft.

5. Sliding Window: Token expiration extends on refresh (like rolling sessions).

References:
- OAuth 2.0 Refresh Token Best Practices (RFC 6819)
- OWASP Authentication Cheat Sheet
"""

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.token_blacklist import TokenBlacklist

settings = get_settings()
logger = logging.getLogger(__name__)

# Import observability metrics (graceful degradation)
try:
    from app.core.observability import metrics as obs_metrics
except ImportError:
    obs_metrics = None


class RefreshTokenStatus(str, Enum):
    """Refresh token status enumeration."""

    ACTIVE = "active"
    USED = "used"  # Token has been refreshed (child token created)
    REVOKED = "revoked"  # Manually revoked
    EXPIRED = "expired"  # Time-based expiration
    FAMILY_REVOKED = "family_revoked"  # Entire family revoked due to reuse


class TokenRotationStrategy(str, Enum):
    """Token rotation strategy enumeration."""

    ALWAYS = "always"  # Always issue new refresh token (most secure)
    THRESHOLD = "threshold"  # Issue new token if > X% of lifetime used
    NEVER = "never"  # Reuse same refresh token (least secure)


class DeviceFingerprint(BaseModel):
    """
    Device fingerprint for binding tokens to devices.

    Captures device characteristics to detect token theft across devices.
    """

    ip_address: str | None = None
    user_agent: str | None = None
    device_id: str | None = None  # Optional client-provided device ID

    def generate_hash(self) -> str:
        """
        Generate a hash of device characteristics.

        Returns:
            SHA-256 hash of device fingerprint
        """
        components = [
            self.ip_address or "",
            self.user_agent or "",
            self.device_id or "",
        ]
        fingerprint_str = "|".join(components)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()


class RefreshTokenData(BaseModel):
    """
    Refresh token data structure.

    Stores all information about a refresh token including family tracking,
    device binding, and usage history.
    """

    # Token identifiers
    token_id: str = Field(..., description="Unique refresh token ID (jti)")
    family_id: str = Field(..., description="Token family ID for reuse detection")
    user_id: str = Field(..., description="User UUID")
    username: str = Field(..., description="Username for display")

    # Token lifecycle
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    last_used_at: datetime | None = None
    status: RefreshTokenStatus = RefreshTokenStatus.ACTIVE

    # Token family tree (for reuse detection)
    parent_token_id: str | None = None  # Previous token in family
    child_token_id: str | None = None  # Next token in family (after refresh)

    # Device binding
    device_fingerprint: str | None = Field(
        None, description="Hash of device characteristics"
    )
    device_info: dict[str, Any] = Field(default_factory=dict)

    # Usage tracking
    refresh_count: int = Field(default=0, description="Times this token was used")
    last_ip: str | None = None

    # Metadata
    session_id: str | None = None  # Link to session if using session management
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        """Validate user_id is a valid UUID string."""
        try:
            UUID(v)
        except ValueError:
            raise ValueError("user_id must be a valid UUID")
        return v

    def is_expired(self, current_time: datetime | None = None) -> bool:
        """
        Check if token has expired.

        Args:
            current_time: Current time for comparison (defaults to utcnow)

        Returns:
            True if token is expired
        """
        if self.status != RefreshTokenStatus.ACTIVE:
            return True

        current = current_time or datetime.utcnow()
        return current >= self.expires_at

    def can_refresh(self, device_fingerprint: str | None = None) -> tuple[bool, str]:
        """
        Check if token can be refreshed.

        Args:
            device_fingerprint: Current device fingerprint hash

        Returns:
            Tuple of (can_refresh, reason)
        """
        # Check status
        if self.status != RefreshTokenStatus.ACTIVE:
            return False, f"Token status is {self.status}"

        # Check expiration
        if self.is_expired():
            return False, "Token has expired"

        # Check device binding
        if self.device_fingerprint and device_fingerprint:
            if self.device_fingerprint != device_fingerprint:
                return False, "Device fingerprint mismatch"

        return True, "OK"


class RefreshTokenCreate(BaseModel):
    """Request schema for creating a refresh token."""

    user_id: str
    username: str
    family_id: str | None = None  # Reuse family ID for rotation
    parent_token_id: str | None = None
    device_fingerprint: DeviceFingerprint | None = None
    session_id: str | None = None
    expires_in_days: int = Field(default=30, ge=1, le=365)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RefreshTokenResponse(BaseModel):
    """Response schema for refresh token."""

    refresh_token: str  # Encrypted token string
    token_id: str
    expires_at: datetime
    expires_in_seconds: int


class RefreshTokenMetrics(BaseModel):
    """Refresh token metrics for monitoring."""

    total_active_tokens: int = 0
    tokens_created_24h: int = 0
    tokens_refreshed_24h: int = 0
    tokens_revoked_24h: int = 0
    reuse_attempts_detected_24h: int = 0
    device_mismatch_attempts_24h: int = 0
    average_token_age_hours: float = 0.0


class RefreshTokenService:
    """
    Refresh token service with advanced security features.

    Manages refresh token lifecycle including creation, validation,
    rotation, revocation, and reuse detection. Integrates with Redis
    for distributed token storage.

    Security Features:
    - Token rotation on every refresh
    - Family tracking for reuse detection
    - Device binding to prevent cross-device usage
    - Concurrent session limiting
    - Comprehensive audit logging
    """

    def __init__(
        self,
        db: Session | None = None,
        max_tokens_per_user: int = 5,
        default_expiry_days: int = 30,
        rotation_strategy: TokenRotationStrategy = TokenRotationStrategy.ALWAYS,
        rotation_threshold: float = 0.5,  # Rotate if >50% of lifetime used
        enable_device_binding: bool = True,
        enable_reuse_detection: bool = True,
    ):
        """
        Initialize refresh token service.

        Args:
            db: Database session for token blacklist
            max_tokens_per_user: Maximum concurrent refresh tokens per user
            default_expiry_days: Default token expiration in days
            rotation_strategy: Token rotation strategy
            rotation_threshold: Threshold for THRESHOLD rotation strategy (0.0-1.0)
            enable_device_binding: Enable device fingerprint binding
            enable_reuse_detection: Enable token reuse detection
        """
        self.db = db
        self.max_tokens_per_user = max_tokens_per_user
        self.default_expiry_days = default_expiry_days
        self.rotation_strategy = rotation_strategy
        self.rotation_threshold = rotation_threshold
        self.enable_device_binding = enable_device_binding
        self.enable_reuse_detection = enable_reuse_detection

        # In-memory storage for development (replace with Redis in production)
        # Format: {token_id: RefreshTokenData}
        self._token_storage: dict[str, RefreshTokenData] = {}

        # Token family index for fast lookup
        # Format: {family_id: [token_id1, token_id2, ...]}
        self._family_index: dict[str, list[str]] = {}

        # User token index
        # Format: {user_id: [token_id1, token_id2, ...]}
        self._user_index: dict[str, list[str]] = {}

    def _generate_token_id(self) -> str:
        """
        Generate a secure random token ID (jti).

        Returns:
            URL-safe random token identifier
        """
        return str(uuid.uuid4())

    def _generate_family_id(self) -> str:
        """
        Generate a token family ID.

        Returns:
            UUID for token family
        """
        return str(uuid.uuid4())

    def _generate_token_string(self) -> str:
        """
        Generate a cryptographically secure token string.

        Returns:
            URL-safe random token (64 bytes = 86 characters base64)
        """
        return secrets.token_urlsafe(64)

    def _index_token(self, token_data: RefreshTokenData) -> None:
        """
        Add token to indices for fast lookup.

        Args:
            token_data: Token data to index
        """
        # Add to family index
        if token_data.family_id not in self._family_index:
            self._family_index[token_data.family_id] = []
        self._family_index[token_data.family_id].append(token_data.token_id)

        # Add to user index
        if token_data.user_id not in self._user_index:
            self._user_index[token_data.user_id] = []
        self._user_index[token_data.user_id].append(token_data.token_id)

    def _unindex_token(self, token_data: RefreshTokenData) -> None:
        """
        Remove token from indices.

        Args:
            token_data: Token data to unindex
        """
        # Remove from family index
        if token_data.family_id in self._family_index:
            try:
                self._family_index[token_data.family_id].remove(token_data.token_id)
            except ValueError:
                pass

        # Remove from user index
        if token_data.user_id in self._user_index:
            try:
                self._user_index[token_data.user_id].remove(token_data.token_id)
            except ValueError:
                pass

    async def create_refresh_token(
        self,
        request: RefreshTokenCreate,
        device_fingerprint: DeviceFingerprint | None = None,
    ) -> tuple[RefreshTokenData, str]:
        """
        Create a new refresh token.

        Args:
            request: Token creation request
            device_fingerprint: Optional device fingerprint for binding

        Returns:
            Tuple of (RefreshTokenData, token_string)

        Raises:
            ValueError: If max tokens per user exceeded
        """
        # Check concurrent token limit
        user_tokens = self.get_user_tokens(request.user_id)
        active_tokens = [
            t for t in user_tokens if t.status == RefreshTokenStatus.ACTIVE
        ]

        if len(active_tokens) >= self.max_tokens_per_user:
            # Revoke oldest token to make room
            oldest = min(active_tokens, key=lambda t: t.created_at)
            await self.revoke_token(oldest.token_id, reason="max_tokens_exceeded")
            logger.info(
                f"Revoked oldest refresh token {oldest.token_id} for user "
                f"{request.user_id} (max: {self.max_tokens_per_user})"
            )

        # Generate token identifiers
        token_id = self._generate_token_id()
        family_id = request.family_id or self._generate_family_id()
        token_string = self._generate_token_string()

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)

        # Generate device fingerprint hash
        device_fp_hash = None
        device_info = {}
        if self.enable_device_binding and device_fingerprint:
            device_fp_hash = device_fingerprint.generate_hash()
            device_info = device_fingerprint.model_dump()

        # Create token data
        token_data = RefreshTokenData(
            token_id=token_id,
            family_id=family_id,
            user_id=request.user_id,
            username=request.username,
            expires_at=expires_at,
            parent_token_id=request.parent_token_id,
            device_fingerprint=device_fp_hash,
            device_info=device_info,
            session_id=request.session_id,
            metadata=request.metadata,
        )

        # Store token (map token_string -> token_data)
        # In production, use Redis with token_string as key
        self._token_storage[token_string] = token_data
        self._index_token(token_data)

        # Update parent token to link child
        if request.parent_token_id:
            for stored_token_str, stored_data in self._token_storage.items():
                if stored_data.token_id == request.parent_token_id:
                    stored_data.child_token_id = token_id
                    break

        # Record metric
        if obs_metrics:
            obs_metrics.record_token_issued("refresh")

        logger.info(
            f"Created refresh token {token_id} for user {request.user_id} "
            f"(family: {family_id}, expires: {expires_at})"
        )

        return token_data, token_string

    async def validate_and_rotate_token(
        self,
        token_string: str,
        device_fingerprint: DeviceFingerprint | None = None,
    ) -> tuple[RefreshTokenData | None, str | None, str]:
        """
        Validate a refresh token and optionally rotate it.

        This is the core method for token refresh. It:
        1. Validates the token exists and is active
        2. Checks device binding if enabled
        3. Detects token reuse (security violation)
        4. Rotates the token based on strategy
        5. Returns new token if rotated

        Args:
            token_string: Refresh token string
            device_fingerprint: Current device fingerprint

        Returns:
            Tuple of (new_token_data, new_token_string, status_message)
            - If rotation occurs: (new_data, new_string, "rotated")
            - If validation succeeds: (old_data, None, "valid")
            - If validation fails: (None, None, error_message)
        """
        # Look up token
        token_data = self._token_storage.get(token_string)

        if not token_data:
            if obs_metrics:
                obs_metrics.record_auth_failure("invalid_refresh_token")
            return None, None, "Token not found"

        # Check if token has already been used (potential reuse attack)
        if self.enable_reuse_detection and token_data.status == RefreshTokenStatus.USED:
            # SECURITY: Token reuse detected - revoke entire family
            logger.warning(
                f"SECURITY: Refresh token reuse detected! Token {token_data.token_id} "
                f"family {token_data.family_id} user {token_data.user_id}"
            )

            # Revoke entire family
            revoked_count = await self.revoke_token_family(
                token_data.family_id, reason="reuse_detected"
            )

            if obs_metrics:
                obs_metrics.record_auth_failure("refresh_token_reuse")

            # Log security event
            logger.error(
                f"Revoked {revoked_count} tokens in family {token_data.family_id} "
                f"due to reuse detection"
            )

            return None, None, "Token reuse detected - family revoked"

        # Validate token
        device_fp_hash = None
        if self.enable_device_binding and device_fingerprint:
            device_fp_hash = device_fingerprint.generate_hash()

        can_refresh, reason = token_data.can_refresh(device_fp_hash)

        if not can_refresh:
            if obs_metrics:
                if "Device fingerprint mismatch" in reason:
                    obs_metrics.record_auth_failure("device_mismatch")
                elif "expired" in reason.lower():
                    obs_metrics.record_auth_failure("expired")
                else:
                    obs_metrics.record_auth_failure("invalid_status")

            return None, None, reason

        # Update token usage
        token_data.last_used_at = datetime.utcnow()
        token_data.refresh_count += 1

        # Determine if rotation is needed
        should_rotate = False

        if self.rotation_strategy == TokenRotationStrategy.ALWAYS:
            should_rotate = True
        elif self.rotation_strategy == TokenRotationStrategy.THRESHOLD:
            # Calculate token age percentage
            total_lifetime = (
                token_data.expires_at - token_data.created_at
            ).total_seconds()
            current_age = (datetime.utcnow() - token_data.created_at).total_seconds()
            age_percentage = current_age / total_lifetime if total_lifetime > 0 else 1.0

            if age_percentage >= self.rotation_threshold:
                should_rotate = True

        if should_rotate:
            # Mark current token as USED
            token_data.status = RefreshTokenStatus.USED

            # Create new token in same family (rotation)
            new_request = RefreshTokenCreate(
                user_id=token_data.user_id,
                username=token_data.username,
                family_id=token_data.family_id,  # Same family
                parent_token_id=token_data.token_id,  # Link to parent
                session_id=token_data.session_id,
                expires_in_days=self.default_expiry_days,
                metadata=token_data.metadata,
            )

            new_token_data, new_token_string = await self.create_refresh_token(
                new_request, device_fingerprint
            )

            logger.info(
                f"Rotated refresh token {token_data.token_id} -> {new_token_data.token_id} "
                f"for user {token_data.user_id}"
            )

            return new_token_data, new_token_string, "rotated"

        # No rotation - return existing token
        return token_data, None, "valid"

    async def revoke_token(
        self,
        token_id: str,
        reason: str = "manual_revoke",
        blacklist: bool = True,
    ) -> bool:
        """
        Revoke a specific refresh token.

        Args:
            token_id: Token ID to revoke
            reason: Revocation reason
            blacklist: Add to database blacklist

        Returns:
            True if token was revoked successfully
        """
        # Find token in storage
        token_data = None
        token_string = None

        for stored_token_str, stored_data in self._token_storage.items():
            if stored_data.token_id == token_id:
                token_data = stored_data
                token_string = stored_token_str
                break

        if not token_data:
            return False

        # Update status
        token_data.status = RefreshTokenStatus.REVOKED
        token_data.metadata["revoke_reason"] = reason

        # Add to database blacklist
        if blacklist and self.db:
            TokenBlacklist(
                jti=token_id,
                token_type="refresh",
                user_id=UUID(token_data.user_id),
                expires_at=token_data.expires_at,
                reason=reason,
            )
            self.db.add(TokenBlacklist)
            self.db.commit()

        # Remove from storage
        if token_string:
            del self._token_storage[token_string]
        self._unindex_token(token_data)

        # Record metric
        if obs_metrics:
            obs_metrics.record_token_blacklisted(reason)

        logger.info(f"Revoked refresh token {token_id} (reason: {reason})")

        return True

    async def revoke_token_family(
        self,
        family_id: str,
        reason: str = "family_revoke",
    ) -> int:
        """
        Revoke all tokens in a token family.

        Used when token reuse is detected to invalidate all related tokens.

        Args:
            family_id: Family ID to revoke
            reason: Revocation reason

        Returns:
            Number of tokens revoked
        """
        if family_id not in self._family_index:
            return 0

        token_ids = self._family_index[family_id].copy()
        revoked = 0

        for token_id in token_ids:
            if await self.revoke_token(token_id, reason=reason):
                revoked += 1

        logger.warning(
            f"Revoked {revoked} tokens in family {family_id} (reason: {reason})"
        )

        return revoked

    async def revoke_user_tokens(
        self,
        user_id: str | UUID,
        except_token_id: str | None = None,
    ) -> int:
        """
        Revoke all refresh tokens for a user.

        Args:
            user_id: User identifier
            except_token_id: Optional token to keep (for logout other devices)

        Returns:
            Number of tokens revoked
        """
        user_id_str = str(user_id)

        if user_id_str not in self._user_index:
            return 0

        token_ids = self._user_index[user_id_str].copy()
        revoked = 0

        for token_id in token_ids:
            if except_token_id and token_id == except_token_id:
                continue

            if await self.revoke_token(token_id, reason="user_revoke"):
                revoked += 1

        logger.info(f"Revoked {revoked} refresh tokens for user {user_id_str}")

        return revoked

    def get_user_tokens(self, user_id: str | UUID) -> list[RefreshTokenData]:
        """
        Get all refresh tokens for a user.

        Args:
            user_id: User identifier

        Returns:
            List of RefreshTokenData
        """
        user_id_str = str(user_id)

        if user_id_str not in self._user_index:
            return []

        token_ids = self._user_index[user_id_str]
        tokens = []

        for token_string, token_data in self._token_storage.items():
            if token_data.token_id in token_ids:
                tokens.append(token_data)

        return tokens

    def get_token_family(self, family_id: str) -> list[RefreshTokenData]:
        """
        Get all tokens in a token family.

        Args:
            family_id: Family identifier

        Returns:
            List of RefreshTokenData in chronological order
        """
        if family_id not in self._family_index:
            return []

        token_ids = self._family_index[family_id]
        tokens = []

        for token_string, token_data in self._token_storage.items():
            if token_data.token_id in token_ids:
                tokens.append(token_data)

        # Sort by creation time
        tokens.sort(key=lambda t: t.created_at)

        return tokens

    async def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired refresh tokens.

        Returns:
            Number of tokens cleaned up
        """
        now = datetime.utcnow()
        expired_tokens = []

        for token_string, token_data in self._token_storage.items():
            if token_data.is_expired(now):
                expired_tokens.append((token_string, token_data))

        for token_string, token_data in expired_tokens:
            token_data.status = RefreshTokenStatus.EXPIRED
            del self._token_storage[token_string]
            self._unindex_token(token_data)

        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired refresh tokens")

        return len(expired_tokens)

    def get_metrics(self) -> RefreshTokenMetrics:
        """
        Get refresh token metrics.

        Returns:
            RefreshTokenMetrics with statistics
        """
        now = datetime.utcnow()
        yesterday = now - timedelta(hours=24)

        active_tokens = []
        created_24h = 0
        refreshed_24h = 0
        revoked_24h = 0

        total_age_hours = 0.0

        for token_data in self._token_storage.values():
            if token_data.status == RefreshTokenStatus.ACTIVE:
                active_tokens.append(token_data)

                # Calculate age
                age = (now - token_data.created_at).total_seconds() / 3600
                total_age_hours += age

            if token_data.created_at >= yesterday:
                created_24h += 1

            if token_data.last_used_at and token_data.last_used_at >= yesterday:
                refreshed_24h += 1

            if (
                token_data.status == RefreshTokenStatus.REVOKED
                and token_data.created_at >= yesterday
            ):
                revoked_24h += 1

        avg_age = total_age_hours / len(active_tokens) if active_tokens else 0.0

        return RefreshTokenMetrics(
            total_active_tokens=len(active_tokens),
            tokens_created_24h=created_24h,
            tokens_refreshed_24h=refreshed_24h,
            tokens_revoked_24h=revoked_24h,
            average_token_age_hours=avg_age,
        )


# Global service instance (singleton)
_refresh_token_service: RefreshTokenService | None = None


def get_refresh_token_service(db: Session | None = None) -> RefreshTokenService:
    """
    Get or create global refresh token service instance.

    Args:
        db: Optional database session

    Returns:
        RefreshTokenService instance
    """
    global _refresh_token_service

    if _refresh_token_service is None:
        _refresh_token_service = RefreshTokenService(
            db=db,
            max_tokens_per_user=settings.RATE_LIMIT_LOGIN_ATTEMPTS,  # Reuse config
            default_expiry_days=30,
            rotation_strategy=TokenRotationStrategy.ALWAYS,
            enable_device_binding=True,
            enable_reuse_detection=True,
        )

    return _refresh_token_service
