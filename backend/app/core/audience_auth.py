"""
Audience-scoped JWT authentication for elevated agent operations.

This module provides short-lived, audience-scoped JWT tokens for sensitive
operations that require elevated permissions. Each token is scoped to a specific
audience (operation type) and has a short TTL to minimize the window of exposure
if compromised.

Security Features:
- Audience-specific tokens prevent privilege escalation
- Short TTL (default 2 minutes) minimizes exposure window
- Clock skew tolerance prevents timing attack edge cases
- Comprehensive logging for audit trails
- Integration with existing token blacklist infrastructure

Usage:
    # Generate a token for aborting jobs
    token = create_audience_token(
        user_id="user-123",
        audience="jobs.abort",
        ttl_seconds=120
    )

    # Use as FastAPI dependency
    @app.post("/jobs/{job_id}/abort")
    async def abort_job(
        job_id: str,
        user: User = Depends(get_current_active_user),
        audience_token: AudienceTokenPayload = Depends(require_audience("jobs.abort"))
    ):
        # Operation execution
        ...
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Callable

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.token_blacklist import TokenBlacklist

settings = get_settings()
logger = logging.getLogger(__name__)

# Import observability metrics (optional - graceful degradation)
try:
    from app.core.observability import metrics as obs_metrics
except ImportError:
    obs_metrics = None

# JWT algorithm (consistent with main auth)
ALGORITHM = "HS256"

# Clock skew tolerance (seconds) - allows for minor time differences
CLOCK_SKEW_TOLERANCE = 30


class AudienceTokenPayload(BaseModel):
    """Payload for audience-scoped JWT token."""

    sub: str  # User ID
    aud: str  # Audience (operation scope)
    exp: datetime  # Expiration time
    iat: datetime  # Issued at time
    jti: str  # Unique token ID for revocation

    class Config:
        json_encoders = {
            datetime: lambda v: int(v.timestamp()),
        }


class AudienceTokenResponse(BaseModel):
    """Response when creating an audience token."""

    token: str
    audience: str
    expires_at: datetime
    ttl_seconds: int


# Defined audiences for agent operations
# Add new audiences here as needed
VALID_AUDIENCES = {
    "jobs.abort": "Abort running background jobs",
    "jobs.kill": "Force-kill stuck background jobs",
    "schedule.generate": "Generate new schedules",
    "schedule.regenerate": "Regenerate existing schedules",
    "schedule.delete": "Delete schedules",
    "swap.execute": "Execute schedule swaps",
    "swap.rollback": "Rollback schedule swaps",
    "solver.abort": "Abort running solver operations",
    "database.backup": "Create database backups",
    "database.restore": "Restore from database backups",
    "resilience.override": "Override resilience framework limits",
    "admin.impersonate": "Impersonate other users (admin)",
    "audit.export": "Export audit logs",
}


def validate_audience(audience: str) -> None:
    """
    Validate that an audience is recognized.

    Args:
        audience: Audience string to validate

    Raises:
        ValueError: If audience is not in VALID_AUDIENCES
    """
    if audience not in VALID_AUDIENCES:
        raise ValueError(
            f"Invalid audience: {audience}. "
            f"Valid audiences: {', '.join(VALID_AUDIENCES.keys())}"
        )


def create_audience_token(
    user_id: str,
    audience: str,
    ttl_seconds: int = 120,  # 2 minutes default
) -> AudienceTokenResponse:
    """
    Create an audience-scoped JWT token for elevated operations.

    This generates a short-lived token that grants permission for a specific
    operation type. The token should be used immediately and discarded after use.

    Args:
        user_id: ID of the user requesting the token
        audience: Audience scope (e.g., "jobs.abort", "schedule.generate")
        ttl_seconds: Time-to-live in seconds (default: 120, max: 600)

    Returns:
        AudienceTokenResponse with token and metadata

    Raises:
        ValueError: If audience is invalid or TTL exceeds maximum

    Example:
        >>> token = create_audience_token(
        ...     user_id="user-123",
        ...     audience="jobs.abort",
        ...     ttl_seconds=120
        ... )
        >>> print(f"Token expires at: {token.expires_at}")
    """
    # Validate audience
    validate_audience(audience)

    # Enforce maximum TTL (10 minutes)
    if ttl_seconds > 600:
        raise ValueError("TTL cannot exceed 600 seconds (10 minutes)")

    # Enforce minimum TTL (30 seconds)
    if ttl_seconds < 30:
        raise ValueError("TTL must be at least 30 seconds")

    # Generate token metadata
    now = datetime.utcnow()
    expires_at = now + timedelta(seconds=ttl_seconds)
    jti = str(uuid.uuid4())

    # Create payload
    payload = {
        "sub": user_id,
        "aud": audience,
        "exp": expires_at,
        "iat": now,
        "jti": jti,
        "type": "audience",  # Distinguish from access/refresh tokens
    }

    # Encode token
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

    # Log token creation (audit trail)
    logger.info(
        f"Audience token created: user_id={user_id}, audience={audience}, "
        f"jti={jti}, ttl={ttl_seconds}s, expires_at={expires_at.isoformat()}"
    )

    # Record metric
    if obs_metrics:
        obs_metrics.record_token_issued(f"audience_{audience}")

    return AudienceTokenResponse(
        token=token,
        audience=audience,
        expires_at=expires_at,
        ttl_seconds=ttl_seconds,
    )


def verify_audience_token(
    token: str,
    required_audience: str,
    db: Session | None = None,
) -> AudienceTokenPayload:
    """
    Verify and decode an audience-scoped JWT token.

    This performs comprehensive validation:
    - Token signature verification
    - Audience matching
    - Expiration checking (with clock skew tolerance)
    - Issued-at-time validation (prevents future-dated tokens)
    - Blacklist checking (if db provided)
    - Type verification (must be audience token)

    Args:
        token: JWT token string
        required_audience: Expected audience value
        db: Optional database session for blacklist checking

    Returns:
        AudienceTokenPayload if token is valid

    Raises:
        HTTPException: If token is invalid, expired, or has wrong audience

    Security Notes:
        - Clock skew tolerance prevents edge cases but logged for monitoring
        - Future-dated tokens are rejected (prevents time manipulation)
        - Blacklisted tokens are rejected even if not expired
    """
    try:
        # Decode and verify signature
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])

        # Verify this is an audience token (not access/refresh)
        token_type = payload.get("type")
        if token_type != "audience":
            logger.warning(
                f"Token type mismatch: expected 'audience', got '{token_type}'"
            )
            if obs_metrics:
                obs_metrics.record_auth_failure("wrong_token_type_audience")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token type",
            )

        # Extract claims
        user_id = payload.get("sub")
        audience = payload.get("aud")
        jti = payload.get("jti")
        exp = payload.get("exp")
        iat = payload.get("iat")

        # Validate required claims
        if not all([user_id, audience, jti, exp, iat]):
            logger.warning(
                f"Missing required claims in audience token: "
                f"sub={bool(user_id)}, aud={bool(audience)}, "
                f"jti={bool(jti)}, exp={bool(exp)}, iat={bool(iat)}"
            )
            if obs_metrics:
                obs_metrics.record_auth_failure("missing_claims_audience")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token structure",
            )

        # Convert timestamps
        expires_at = datetime.utcfromtimestamp(exp)
        issued_at = datetime.utcfromtimestamp(iat)
        now = datetime.utcnow()

        # Check expiration (with clock skew tolerance)
        if now > expires_at + timedelta(seconds=CLOCK_SKEW_TOLERANCE):
            logger.info(
                f"Audience token expired: jti={jti}, audience={audience}, "
                f"expired_at={expires_at.isoformat()}, now={now.isoformat()}"
            )
            if obs_metrics:
                obs_metrics.record_auth_failure("audience_expired")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token has expired",
            )

        # Check for future-dated tokens (clock skew tolerance)
        if issued_at > now + timedelta(seconds=CLOCK_SKEW_TOLERANCE):
            logger.warning(
                f"Future-dated audience token detected: jti={jti}, "
                f"iat={issued_at.isoformat()}, now={now.isoformat()}"
            )
            if obs_metrics:
                obs_metrics.record_auth_failure("future_dated_token")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token timestamp",
            )

        # Log clock skew if present (for monitoring)
        if now < expires_at - timedelta(seconds=CLOCK_SKEW_TOLERANCE):
            skew = (expires_at - now).total_seconds()
            if skew > CLOCK_SKEW_TOLERANCE:
                logger.debug(
                    f"Clock skew detected: {skew}s (within tolerance), jti={jti}"
                )

        # Verify audience matches
        if audience != required_audience:
            logger.warning(
                f"Audience mismatch: required={required_audience}, "
                f"got={audience}, jti={jti}, user_id={user_id}"
            )
            if obs_metrics:
                obs_metrics.record_auth_failure("audience_mismatch")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Token not valid for this operation (requires: {required_audience})",
            )

        # Check if token is blacklisted
        if db is not None and TokenBlacklist.is_blacklisted(db, jti):
            logger.warning(
                f"Blacklisted audience token attempted: jti={jti}, "
                f"audience={audience}, user_id={user_id}"
            )
            if obs_metrics:
                obs_metrics.record_auth_failure("blacklisted_audience")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token has been revoked",
            )

        # Log successful validation
        logger.info(
            f"Audience token validated: user_id={user_id}, audience={audience}, "
            f"jti={jti}"
        )

        return AudienceTokenPayload(
            sub=user_id,
            aud=audience,
            exp=expires_at,
            iat=issued_at,
            jti=jti,
        )

    except JWTError as e:
        # Categorize JWT errors
        error_str = str(e).lower()
        logger.warning(f"JWT verification failed: {error_str}")

        if obs_metrics:
            if "expired" in error_str:
                obs_metrics.record_auth_failure("audience_jwt_expired")
            elif "signature" in error_str:
                obs_metrics.record_auth_failure("audience_invalid_signature")
            else:
                obs_metrics.record_auth_failure("audience_malformed")

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token",
        )
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error validating audience token: {e}", exc_info=True)
        if obs_metrics:
            obs_metrics.record_auth_failure("audience_validation_error")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token validation failed",
        )


def revoke_audience_token(
    db: Session,
    jti: str,
    expires_at: datetime,
    user_id: str,
    reason: str = "manual_revocation",
) -> TokenBlacklist:
    """
    Revoke an audience token by adding it to the blacklist.

    This is useful for:
    - Manual revocation of compromised tokens
    - Cleanup after operation completion
    - Security incident response

    Args:
        db: Database session
        jti: JWT ID to blacklist
        expires_at: When the token expires (for cleanup)
        user_id: User ID who owned this token
        reason: Reason for revocation

    Returns:
        Created TokenBlacklist record
    """
    from uuid import UUID

    record = TokenBlacklist(
        jti=jti,
        user_id=UUID(user_id),
        expires_at=expires_at,
        reason=reason,
    )
    db.add(record)
    db.commit()

    logger.info(
        f"Audience token revoked: jti={jti}, user_id={user_id}, reason={reason}"
    )

    # Record metric
    if obs_metrics:
        obs_metrics.record_token_blacklisted(f"audience_{reason}")

    return record


def require_audience(audience: str) -> Callable:
    """
    Create a FastAPI dependency that requires a valid audience token.

    This is the primary way to protect endpoints that need elevated permissions.
    The dependency validates the token and returns the payload if valid.

    Args:
        audience: Required audience scope

    Returns:
        FastAPI dependency function

    Example:
        >>> @app.post("/jobs/{job_id}/abort")
        >>> async def abort_job(
        ...     job_id: str,
        ...     token_payload: AudienceTokenPayload = Depends(require_audience("jobs.abort"))
        ... ):
        ...     # Access user_id from token_payload.sub
        ...     logger.info(f"User {token_payload.sub} aborting job {job_id}")
        ...     # Execute operation
        ...     ...

    Security Notes:
        - Token is extracted from Authorization header: "Bearer <token>"
        - Blacklist checking is performed if database available
        - All validation failures result in 403 Forbidden
    """

    async def audience_dependency(
        authorization: str | None = None,
        db: Session = Depends(get_db),
    ) -> AudienceTokenPayload:
        """
        Validate audience-scoped token from Authorization header.

        Args:
            authorization: Authorization header value (format: "Bearer <token>")
            db: Database session for blacklist checking

        Returns:
            AudienceTokenPayload if valid

        Raises:
            HTTPException: If token missing, invalid, or has wrong audience
        """
        # Extract token from header
        if not authorization:
            logger.warning(f"Missing Authorization header for audience: {audience}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authorization header required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Parse "Bearer <token>" format
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.warning(f"Invalid Authorization header format for audience: {audience}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = parts[1]

        # Verify token
        return verify_audience_token(token, audience, db)

    return audience_dependency


# Convenience function for manual header extraction (non-dependency use)
def get_audience_token(
    authorization: str,
    audience: str,
    db: Session | None = None,
) -> AudienceTokenPayload:
    """
    Extract and verify audience token from Authorization header.

    This is a non-dependency version for use outside FastAPI routes
    (e.g., in service layer or background tasks).

    Args:
        authorization: Authorization header value ("Bearer <token>")
        audience: Required audience scope
        db: Optional database session for blacklist checking

    Returns:
        AudienceTokenPayload if valid

    Raises:
        ValueError: If token is missing or invalid format
        HTTPException: If token verification fails

    Example:
        >>> from app.db.session import SessionLocal
        >>> db = SessionLocal()
        >>> try:
        ...     payload = get_audience_token(
        ...         authorization=request.headers.get("Authorization"),
        ...         audience="jobs.abort",
        ...         db=db
        ...     )
        ...     print(f"Authorized user: {payload.sub}")
        ... finally:
        ...     db.close()
    """
    if not authorization:
        raise ValueError("Authorization header is required")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ValueError("Invalid authorization format (expected: Bearer <token>)")

    token = parts[1]
    return verify_audience_token(token, audience, db)


# Export all public functions and classes
__all__ = [
    "AudienceTokenPayload",
    "AudienceTokenResponse",
    "VALID_AUDIENCES",
    "validate_audience",
    "create_audience_token",
    "verify_audience_token",
    "revoke_audience_token",
    "require_audience",
    "get_audience_token",
]
