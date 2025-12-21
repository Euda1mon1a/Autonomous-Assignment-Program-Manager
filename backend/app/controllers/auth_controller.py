"""Auth controller for request/response handling."""


from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.error_codes import ErrorCode, get_error_code_from_message
from app.core.rate_limit import get_account_lockout
from app.models.user import User
from app.schemas.auth import (
    Token,
    UserCreate,
    UserResponse,
)
from app.services.auth_service import AuthService


class AuthController:
    """Controller for authentication endpoints."""

    def __init__(self, db: Session):
        self.service = AuthService(db)
        self.lockout = get_account_lockout()

    def login(self, username: str, password: str) -> Token:
        """
        Authenticate user and return JWT token.

        Security: Implements per-user account lockout with exponential backoff
        to prevent distributed brute force attacks. This complements IP-based
        rate limiting by tracking failed attempts per username.

        Note: This is independent of token handling - lockout only tracks
        failed authentication attempts before any tokens are issued.
        """
        # Check if account is locked out
        is_locked, lockout_seconds = self.lockout.check_lockout(username)
        if is_locked:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Account temporarily locked",
                    "message": f"Too many failed login attempts. Try again in {lockout_seconds} seconds.",
                    "lockout_seconds": lockout_seconds,
                },
                headers={"Retry-After": str(lockout_seconds)},
            )

        result = self.service.authenticate(username, password)

        if result["error"]:
            # Record failed attempt and check if account should be locked
            is_now_locked, attempts_remaining, new_lockout_seconds = self.lockout.record_failed_attempt(username)

            if is_now_locked:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Account temporarily locked",
                        "message": f"Too many failed login attempts. Try again in {new_lockout_seconds} seconds.",
                        "lockout_seconds": new_lockout_seconds,
                    },
                    headers={"Retry-After": str(new_lockout_seconds)},
                )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result["error"],
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Successful login - clear any lockout/failed attempts
        self.lockout.clear_lockout(username)

        return Token(
            access_token=result["access_token"],
            token_type=result["token_type"],
        )

    def register_user(
        self,
        user_in: UserCreate,
        current_user: User | None = None,
    ) -> UserResponse:
        """Register a new user."""
        result = self.service.register_user(
            username=user_in.username,
            email=user_in.email,
            password=user_in.password,
            role=user_in.role,
            current_user=current_user,
        )

        if result["error"]:
            # Determine appropriate status code using structured error codes
            error_code = result.get("error_code") or get_error_code_from_message(result["error"])

            if error_code == ErrorCode.FORBIDDEN:
                status_code = status.HTTP_403_FORBIDDEN
            elif error_code == ErrorCode.UNAUTHORIZED:
                status_code = status.HTTP_401_UNAUTHORIZED
            else:
                status_code = status.HTTP_400_BAD_REQUEST

            raise HTTPException(status_code=status_code, detail=result["error"])

        return result["user"]

    def list_users(self) -> list[UserResponse]:
        """List all users."""
        return self.service.list_users()
