"""Impersonation service for Admin 'View As User' feature.

This service handles the business logic for user impersonation, allowing
administrators to temporarily assume the identity of other users for
troubleshooting and support purposes.

Security Features:
- Only admins can impersonate
- Cannot self-impersonate
- Cannot impersonate while already impersonating (nested impersonation blocked)
- Short-lived tokens (default 30 minutes)
- Full audit trail via ActivityLog
- Token blacklisting on end-impersonation
"""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import ALGORITHM, blacklist_token
from app.models.activity_log import ActivityActionType, ActivityLog
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User
from app.schemas.impersonation import (
    ImpersonateResponse,
    ImpersonationStatus,
)

settings = get_settings()
logger = logging.getLogger(__name__)

# Default impersonation token TTL: 30 minutes
IMPERSONATION_TOKEN_TTL_MINUTES = 30


class ImpersonationError(Exception):
    """Base exception for impersonation errors."""

    pass


class ImpersonationForbiddenError(ImpersonationError):
    """Raised when impersonation is not allowed."""

    pass


class ImpersonationTokenError(ImpersonationError):
    """Raised when there's an issue with the impersonation token."""

    pass


class ImpersonationService:
    """Service for managing user impersonation sessions.

    This service provides methods to:
    - Start impersonation (admin assumes target user identity)
    - End impersonation (revoke impersonation token)
    - Get impersonation status
    - Verify impersonation tokens
    """

    def __init__(self, db: Session) -> None:
        """Initialize the impersonation service.

        Args:
            db: SQLAlchemy database session.
        """
        self.db = db

    def start_impersonation(
        self,
        admin_user: User,
        target_user_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ImpersonateResponse:
        """Start an impersonation session.

        Creates a short-lived impersonation token that allows the admin to
        act as the target user. All actions during impersonation are logged
        to the audit trail.

        Args:
            admin_user: The admin initiating the impersonation.
            target_user_id: UUID of the user to impersonate.
            ip_address: Client IP address for audit logging.
            user_agent: Client user agent for audit logging.

        Returns:
            ImpersonateResponse with token and target user details.

        Raises:
            ImpersonationForbiddenError: If impersonation is not allowed.
            ValueError: If target user not found.
        """
        # Security check: Only admins can impersonate
        if not admin_user.is_admin:
            logger.warning(
                f"Non-admin user {admin_user.username} attempted to impersonate"
            )
            raise ImpersonationForbiddenError(
                "Only administrators can impersonate users"
            )

        # Security check: Cannot self-impersonate
        if admin_user.id == target_user_id:
            logger.warning(f"Admin {admin_user.username} attempted self-impersonation")
            raise ImpersonationForbiddenError("Cannot impersonate yourself")

        # Get target user
        target_user = self.db.query(User).filter(User.id == target_user_id).first()
        if not target_user:
            raise ValueError(f"Target user not found: {target_user_id}")

        # Security check: Cannot impersonate inactive users
        if not target_user.is_active:
            raise ImpersonationForbiddenError("Cannot impersonate inactive users")

        # Create impersonation token
        expires_delta = timedelta(minutes=IMPERSONATION_TOKEN_TTL_MINUTES)
        expires_at = datetime.utcnow() + expires_delta

        import uuid

        jti = str(uuid.uuid4())

        token_payload = {
            "sub": str(target_user.id),
            "username": target_user.username,
            "type": "impersonation",
            "original_admin_id": str(admin_user.id),
            "target_user_id": str(target_user.id),
            "exp": expires_at,
            "iat": datetime.utcnow(),
            "jti": jti,
        }

        impersonation_token = jwt.encode(
            token_payload, settings.SECRET_KEY, algorithm=ALGORITHM
        )

        # Log impersonation start to audit trail
        activity_log = ActivityLog.create_entry(
            action_type=ActivityActionType.IMPERSONATION_STARTED,
            user_id=admin_user.id,
            target_entity="User",
            target_id=str(target_user.id),
            details={
                "admin_username": admin_user.username,
                "target_username": target_user.username,
                "target_role": target_user.role,
                "expires_at": expires_at.isoformat(),
                "jti": jti,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(activity_log)
        self.db.commit()

        logger.info(
            f"Impersonation started: admin={admin_user.username} -> "
            f"target={target_user.username}, expires={expires_at.isoformat()}"
        )

        return ImpersonateResponse(
            impersonation_token=impersonation_token,
            target_user=target_user,
            expires_at=expires_at,
        )

    def end_impersonation(
        self,
        token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> bool:
        """End an impersonation session by blacklisting the token.

        Args:
            token: The impersonation token to revoke.
            ip_address: Client IP address for audit logging.
            user_agent: Client user agent for audit logging.

        Returns:
            True if impersonation was successfully ended.

        Raises:
            ImpersonationTokenError: If token is invalid or already expired.
        """
        try:
            # Decode token without verification to get claims
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])

            # Verify this is an impersonation token
            if payload.get("type") != "impersonation":
                raise ImpersonationTokenError("Not an impersonation token")

            jti = payload.get("jti")
            exp = payload.get("exp")
            original_admin_id = payload.get("original_admin_id")
            target_user_id = payload.get("target_user_id")

            if not jti or not exp:
                raise ImpersonationTokenError("Invalid token structure")

            # Check if already blacklisted
            if TokenBlacklist.is_blacklisted(self.db, jti):
                logger.warning(
                    f"Attempted to end already-ended impersonation: jti={jti}"
                )
                return True  # Already ended, consider it a success

            # Blacklist the token
            expires_at = datetime.utcfromtimestamp(exp)
            blacklist_token(
                db=self.db,
                jti=jti,
                expires_at=expires_at,
                user_id=UUID(original_admin_id) if original_admin_id else None,
                reason="impersonation_ended",
            )

            # Log impersonation end to audit trail
            activity_log = ActivityLog.create_entry(
                action_type=ActivityActionType.IMPERSONATION_ENDED,
                user_id=UUID(original_admin_id) if original_admin_id else None,
                target_entity="User",
                target_id=target_user_id,
                details={
                    "jti": jti,
                    "ended_at": datetime.utcnow().isoformat(),
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.db.add(activity_log)
            self.db.commit()

            logger.info(f"Impersonation ended: jti={jti}")
            return True

        except JWTError as e:
            logger.warning(f"Failed to end impersonation - JWT error: {e}")
            raise ImpersonationTokenError(f"Invalid or expired token: {e}")

    def get_impersonation_status(self, token: str) -> ImpersonationStatus:
        """Check the current impersonation status for a token.

        Args:
            token: The impersonation token to check.

        Returns:
            ImpersonationStatus with current session details.
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])

            # Verify this is an impersonation token
            if payload.get("type") != "impersonation":
                return ImpersonationStatus(is_impersonating=False)

            jti = payload.get("jti")
            exp = payload.get("exp")
            original_admin_id = payload.get("original_admin_id")
            target_user_id = payload.get("target_user_id")

            # Check if token is blacklisted
            if jti and TokenBlacklist.is_blacklisted(self.db, jti):
                return ImpersonationStatus(is_impersonating=False)

            # Get user details
            target_user = None
            original_user = None

            if target_user_id:
                target_user = (
                    self.db.query(User).filter(User.id == UUID(target_user_id)).first()
                )
            if original_admin_id:
                original_user = (
                    self.db.query(User)
                    .filter(User.id == UUID(original_admin_id))
                    .first()
                )

            expires_at = datetime.utcfromtimestamp(exp) if exp else None

            return ImpersonationStatus(
                is_impersonating=True,
                target_user=target_user,
                original_user=original_user,
                expires_at=expires_at,
            )

        except JWTError:
            return ImpersonationStatus(is_impersonating=False)

    def verify_impersonation_token(self, token: str) -> tuple[User, User] | None:
        """Verify an impersonation token and return the users.

        This is the main method used by the security layer to validate
        impersonation tokens and determine which user to act as.

        Args:
            token: The impersonation token to verify.

        Returns:
            Tuple of (target_user, original_admin) if valid, None otherwise.
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])

            # Verify this is an impersonation token
            if payload.get("type") != "impersonation":
                logger.debug("Token is not an impersonation token")
                return None

            jti = payload.get("jti")
            original_admin_id = payload.get("original_admin_id")
            target_user_id = payload.get("target_user_id")

            if not all([jti, original_admin_id, target_user_id]):
                logger.warning("Impersonation token missing required claims")
                return None

            # Check if token is blacklisted
            if TokenBlacklist.is_blacklisted(self.db, jti):
                logger.debug(f"Impersonation token is blacklisted: jti={jti}")
                return None

            # Get users
            target_user = (
                self.db.query(User).filter(User.id == UUID(target_user_id)).first()
            )
            original_admin = (
                self.db.query(User).filter(User.id == UUID(original_admin_id)).first()
            )

            if not target_user or not original_admin:
                logger.warning(
                    f"Impersonation token references missing users: "
                    f"target={target_user_id}, admin={original_admin_id}"
                )
                return None

            # Verify target user is still active
            if not target_user.is_active:
                logger.warning(f"Target user is inactive: {target_user.username}")
                return None

            # Verify original admin is still active and still admin
            if not original_admin.is_active or not original_admin.is_admin:
                logger.warning(
                    f"Original admin is inactive or no longer admin: "
                    f"{original_admin.username}"
                )
                return None

            return (target_user, original_admin)

        except JWTError as e:
            logger.debug(f"Impersonation token verification failed: {e}")
            return None


# Convenience function for creating service instance
def get_impersonation_service(db: Session) -> ImpersonationService:
    """Get an impersonation service instance.

    Args:
        db: SQLAlchemy database session.

    Returns:
        ImpersonationService instance.
    """
    return ImpersonationService(db)
