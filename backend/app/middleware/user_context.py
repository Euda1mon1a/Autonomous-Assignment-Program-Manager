"""
User context middleware for injecting user information into request state.

Features:
- User identification from JWT token
- User context injection into logging
- Role-based context enrichment
- Session tracking
"""

from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging.context import set_user_id, set_session_id, set_custom_field
from app.core.security import decode_access_token
from loguru import logger


class UserContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware for enriching requests with user context.

    Features:
    - Extracts user from JWT token
    - Injects user context into logging
    - Tracks user sessions
    - Provides user information to downstream handlers
    """

    def __init__(
        self,
        app,
        inject_logging_context: bool = True,
        track_user_activity: bool = True,
    ):
        """
        Initialize user context middleware.

        Args:
            app: FastAPI application
            inject_logging_context: Inject user context into logging
            track_user_activity: Track user activity metrics
        """
        super().__init__(app)
        self.inject_logging_context = inject_logging_context
        self.track_user_activity = track_user_activity

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and enrich with user context.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response: HTTP response
        """
        # Extract user from token
        user_context = await self._extract_user_context(request)

        # Store in request state for downstream use
        request.state.user = user_context.get("user")
        request.state.user_id = user_context.get("user_id")
        request.state.user_role = user_context.get("role")
        request.state.session_id = user_context.get("session_id")

        # Inject into logging context
        if self.inject_logging_context:
            if user_context.get("user_id"):
                set_user_id(user_context["user_id"])
            if user_context.get("session_id"):
                set_session_id(user_context["session_id"])
            if user_context.get("role"):
                set_custom_field("user_role", user_context["role"])
            if user_context.get("username"):
                set_custom_field("username", user_context["username"])

        # Track activity
        if self.track_user_activity and user_context.get("user_id"):
            self._track_activity(request, user_context)

        # Process request
        response = await call_next(request)

        return response

    async def _extract_user_context(self, request: Request) -> dict[str, Any]:
        """
        Extract user context from request.

        Args:
            request: HTTP request

        Returns:
            dict: User context information
        """
        context: dict[str, Any] = {
            "user": None,
            "user_id": None,
            "username": None,
            "role": None,
            "session_id": None,
        }

        # Try to get user from JWT token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]

            try:
                # Decode token (assuming you have this function)
                payload = decode_access_token(token)

                if payload:
                    context["user_id"] = payload.get("sub")
                    context["username"] = payload.get("username")
                    context["role"] = payload.get("role")
                    context["session_id"] = payload.get("session_id")
                    context["user"] = {
                        "id": payload.get("sub"),
                        "username": payload.get("username"),
                        "role": payload.get("role"),
                    }

            except Exception as e:
                logger.debug(f"Failed to decode token: {e}")

        # Alternative: Get from session cookie
        if not context["user_id"]:
            session_id = request.cookies.get("session_id")
            if session_id:
                context["session_id"] = session_id
                # In production, would fetch user from session store

        return context

    def _track_activity(self, request: Request, user_context: dict[str, Any]) -> None:
        """
        Track user activity for analytics.

        Args:
            request: HTTP request
            user_context: User context information
        """
        logger.debug(
            f"User activity: {request.method} {request.url.path}",
            user_id=user_context.get("user_id"),
            username=user_context.get("username"),
            role=user_context.get("role"),
            method=request.method,
            path=request.url.path,
            ip=request.client.host if request.client else None,
        )


class RoleEnrichmentMiddleware(BaseHTTPMiddleware):
    """
    Middleware for enriching requests with role-based context.

    Adds role-specific information to request state.
    """

    def __init__(self, app):
        """Initialize role enrichment middleware."""
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add role-specific context.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response: HTTP response
        """
        # Get user role from request state (set by UserContextMiddleware)
        user_role = getattr(request.state, "user_role", None)

        if user_role:
            # Add role-specific permissions and context
            request.state.permissions = self._get_role_permissions(user_role)
            request.state.is_admin = user_role in ("ADMIN", "COORDINATOR")
            request.state.is_faculty = user_role in ("FACULTY", "ADMIN", "COORDINATOR")
            request.state.is_resident = user_role == "RESIDENT"

            # Inject into logging context
            set_custom_field("is_admin", request.state.is_admin)
            set_custom_field("is_faculty", request.state.is_faculty)

        # Process request
        response = await call_next(request)

        return response

    def _get_role_permissions(self, role: str) -> set[str]:
        """
        Get permissions for role.

        Args:
            role: User role

        Returns:
            set: Set of permission strings
        """
        # Define role-based permissions
        permissions_map = {
            "ADMIN": {
                "read:all",
                "write:all",
                "delete:all",
                "manage:users",
                "manage:schedules",
                "override:acgme",
            },
            "COORDINATOR": {
                "read:all",
                "write:schedules",
                "manage:schedules",
                "approve:swaps",
            },
            "FACULTY": {
                "read:schedules",
                "read:own",
                "write:own",
                "request:swaps",
            },
            "RESIDENT": {
                "read:own",
                "request:swaps",
            },
        }

        return permissions_map.get(role, set())


def create_user_context_middleware(
    inject_logging_context: bool = True,
    track_user_activity: bool = True,
) -> type[UserContextMiddleware]:
    """
    Create user context middleware factory.

    Args:
        inject_logging_context: Inject user context into logging
        track_user_activity: Track user activity

    Returns:
        UserContextMiddleware class configured with parameters
    """

    class ConfiguredUserContextMiddleware(UserContextMiddleware):
        def __init__(self, app):
            super().__init__(
                app,
                inject_logging_context=inject_logging_context,
                track_user_activity=track_user_activity,
            )

    return ConfiguredUserContextMiddleware
