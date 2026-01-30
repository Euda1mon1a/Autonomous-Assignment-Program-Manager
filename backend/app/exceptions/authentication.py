"""Authentication and authorization exceptions.

These exceptions are raised during login, token validation, permission checks,
and other authentication/authorization operations.
"""

from typing import Any

from app.core.exceptions import ForbiddenError, UnauthorizedError


class AuthenticationError(UnauthorizedError):
    """Base exception for authentication failures."""

    def __init__(
        self,
        message: str = "Authentication failed",
        **context: Any,
    ) -> None:
        """Initialize authentication error.

        Args:
            message: User-friendly error message
            **context: Additional context
        """
        super().__init__(message)
        self.context = context


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""

    def __init__(
        self,
        message: str = "Invalid email or password",
        username: str | None = None,
        **context: Any,
    ) -> None:
        """Initialize invalid credentials error.

        Args:
            message: User-friendly error message
            username: Username/email that failed (for logging, not returned to user)
            **context: Additional context
        """
        super().__init__(message, **context)
        self.username = username  # For internal logging only


class TokenExpiredError(AuthenticationError):
    """Raised when an authentication token has expired."""

    def __init__(
        self,
        message: str = "Authentication token has expired",
        token_type: str = "access",
        expired_at: str | None = None,
        **context: Any,
    ) -> None:
        """Initialize token expired error.

        Args:
            message: User-friendly error message
            token_type: Type of token (access, refresh)
            expired_at: When the token expired
            **context: Additional context
        """
        super().__init__(message, **context)
        self.token_type = token_type
        self.expired_at = expired_at


class InvalidTokenError(AuthenticationError):
    """Raised when an authentication token is invalid or malformed."""

    def __init__(
        self,
        message: str = "Invalid authentication token",
        token_type: str = "access",
        reason: str | None = None,
        **context: Any,
    ) -> None:
        """Initialize invalid token error.

        Args:
            message: User-friendly error message
            token_type: Type of token (access, refresh)
            reason: Technical reason for invalidity
            **context: Additional context
        """
        super().__init__(message, **context)
        self.token_type = token_type
        self.reason = reason


class TokenRevokededError(AuthenticationError):
    """Raised when a token has been revoked."""

    def __init__(
        self,
        message: str = "Authentication token has been revoked",
        token_type: str = "access",
        revoked_at: str | None = None,
        **context: Any,
    ) -> None:
        """Initialize token revoked error.

        Args:
            message: User-friendly error message
            token_type: Type of token (access, refresh)
            revoked_at: When the token was revoked
            **context: Additional context
        """
        super().__init__(message, **context)
        self.token_type = token_type
        self.revoked_at = revoked_at


class PermissionDeniedError(ForbiddenError):
    """Raised when user lacks permission for an operation."""

    def __init__(
        self,
        message: str = "You do not have permission to perform this action",
        required_permission: str | None = None,
        user_role: str | None = None,
        **context: Any,
    ) -> None:
        """Initialize permission denied error.

        Args:
            message: User-friendly error message
            required_permission: Permission that was required
            user_role: User's current role
            **context: Additional context
        """
        super().__init__(message)
        self.required_permission = required_permission
        self.user_role = user_role
        self.context = context


class InsufficientRoleError(PermissionDeniedError):
    """Raised when user's role is insufficient for an operation."""

    def __init__(
        self,
        message: str = "Your role does not allow this action",
        required_role: str | None = None,
        user_role: str | None = None,
        **context: Any,
    ) -> None:
        """Initialize insufficient role error.

        Args:
            message: User-friendly error message
            required_role: Minimum required role
            user_role: User's current role
            **context: Additional context
        """
        super().__init__(
            message=message,
            user_role=user_role,
            **context,
        )
        self.required_role = required_role


class AccountDisabledError(AuthenticationError):
    """Raised when attempting to authenticate with a disabled account."""

    def __init__(
        self,
        message: str = "This account has been disabled",
        user_id: str | None = None,
        disabled_at: str | None = None,
        **context: Any,
    ) -> None:
        """Initialize account disabled error.

        Args:
            message: User-friendly error message
            user_id: ID of disabled user
            disabled_at: When the account was disabled
            **context: Additional context
        """
        super().__init__(message, **context)
        self.user_id = user_id
        self.disabled_at = disabled_at


class MFARequiredError(AuthenticationError):
    """Raised when multi-factor authentication is required but not provided."""

    def __init__(
        self,
        message: str = "Multi-factor authentication required",
        mfa_methods: list[str] | None = None,
        **context: Any,
    ) -> None:
        """Initialize MFA required error.

        Args:
            message: User-friendly error message
            mfa_methods: Available MFA methods
            **context: Additional context
        """
        super().__init__(message, **context)
        self.mfa_methods = mfa_methods or []


class MFAInvalidError(AuthenticationError):
    """Raised when multi-factor authentication code is invalid."""

    def __init__(
        self,
        message: str = "Invalid multi-factor authentication code",
        mfa_method: str | None = None,
        **context: Any,
    ) -> None:
        """Initialize MFA invalid error.

        Args:
            message: User-friendly error message
            mfa_method: MFA method that failed
            **context: Additional context
        """
        super().__init__(message, **context)
        self.mfa_method = mfa_method
