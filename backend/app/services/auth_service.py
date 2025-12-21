"""Authentication service for business logic."""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.rate_limit import get_account_lockout
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    get_user_by_id,
    verify_password,
    verify_refresh_token,
)
from app.models.user import User
from app.repositories.user import UserRepository

settings = get_settings()


class AuthService:
    """Service for authentication business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def authenticate(self, username: str, password: str) -> dict:
        """
        Authenticate a user and generate access + refresh tokens.

        Includes per-user account lockout protection against distributed
        brute force attacks.

        Returns dict with:
        - user: The authenticated user
        - access_token: JWT access token (short-lived)
        - refresh_token: JWT refresh token (long-lived, for token rotation)
        - token_type: Token type (bearer)
        - jti: JWT ID (for blacklist support)
        - expires_at: Token expiration time
        - expires_in: Access token lifetime in seconds
        - error: Error message if authentication failed
        - locked_seconds: Seconds remaining if account is locked
        """
        lockout = get_account_lockout()

        # Check if account is locked out
        is_locked, remaining = lockout.is_locked_out(username)
        if is_locked:
            return {
                "user": None,
                "error": "Account temporarily locked due to too many failed attempts",
                "locked_seconds": remaining,
            }

        user = self.user_repo.get_by_username(username)
        if not user:
            # Record failed attempt even for non-existent users
            # (prevents username enumeration via lockout behavior)
            lockout.record_failed_attempt(username)
            return {"user": None, "error": "Incorrect username or password"}

        if not verify_password(password, user.hashed_password):
            # Record failed attempt
            is_now_locked, lockout_seconds, attempts = lockout.record_failed_attempt(username)
            if is_now_locked:
                return {
                    "user": None,
                    "error": "Account temporarily locked due to too many failed attempts",
                    "locked_seconds": lockout_seconds,
                }
            return {"user": None, "error": "Incorrect username or password"}

        # Clear failed attempts on successful login
        lockout.record_successful_login(username)

        # Update last login
        user.last_login = datetime.utcnow()
        self.user_repo.commit()

        # Create access token with jti for blacklist support (short-lived)
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token, jti, expires_at = create_access_token(
            data={"sub": str(user.id), "username": user.username},
            expires_delta=access_token_expires,
        )

        # Create refresh token (long-lived)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token, refresh_jti, refresh_expires_at = create_refresh_token(
            data={"sub": str(user.id), "username": user.username},
            expires_delta=refresh_token_expires,
        )

        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "jti": jti,
            "expires_at": expires_at,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "error": None,
        }

    def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Generate a new access token using a valid refresh token.

        If REFRESH_TOKEN_ROTATE is enabled, also issues a new refresh token
        (token rotation for enhanced security).

        Args:
            refresh_token: The JWT refresh token

        Returns dict with:
        - access_token: New JWT access token
        - refresh_token: New refresh token (if rotation enabled)
        - token_type: Token type (bearer)
        - expires_in: Access token lifetime in seconds
        - error: Error message if refresh failed
        """
        from uuid import UUID

        # Verify the refresh token
        token_data = verify_refresh_token(refresh_token, self.db)
        if token_data is None:
            return {"error": "Invalid or expired refresh token"}

        # Get the user
        user = get_user_by_id(self.db, UUID(token_data.user_id))
        if user is None or not user.is_active:
            return {"error": "User not found or inactive"}

        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token, jti, expires_at = create_access_token(
            data={"sub": str(user.id), "username": user.username},
            expires_delta=access_token_expires,
        )

        result = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "error": None,
        }

        # Optionally rotate refresh token
        if settings.REFRESH_TOKEN_ROTATE:
            refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            new_refresh_token, refresh_jti, refresh_expires_at = create_refresh_token(
                data={"sub": str(user.id), "username": user.username},
                expires_delta=refresh_token_expires,
            )
            result["refresh_token"] = new_refresh_token

        return result

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        role: str = "coordinator",
        current_user: User | None = None,
    ) -> dict:
        """
        Register a new user.

        First user becomes admin. Otherwise requires admin to create users.

        Returns dict with:
        - user: The created user
        - error: Error message if registration failed
        """
        user_count = self.user_repo.count()

        # If users exist, require admin to create new users
        if user_count > 0:
            if current_user is None or not current_user.is_admin:
                return {
                    "user": None,
                    "error": "Admin access required to create users",
                }

        # Check if username already exists
        if self.user_repo.username_exists(username):
            return {"user": None, "error": "Username already registered"}

        # Check if email already exists
        if self.user_repo.email_exists(email):
            return {"user": None, "error": "Email already registered"}

        # First user becomes admin
        actual_role = "admin" if user_count == 0 else role

        user_data = {
            "username": username,
            "email": email,
            "hashed_password": get_password_hash(password),
            "role": actual_role,
        }

        user = self.user_repo.create(user_data)
        self.user_repo.commit()
        self.user_repo.refresh(user)

        return {"user": user, "error": None}

    def list_users(self) -> list[User]:
        """List all users ordered by username."""
        return self.user_repo.list_ordered_by_username()
