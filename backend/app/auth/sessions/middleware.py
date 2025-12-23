"""
Session middleware for FastAPI.

Provides automatic session management for HTTP requests:
- Session validation and tracking
- Activity updates
- Session ID extraction from cookies/headers
- Integration with existing JWT authentication
"""

import logging
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.auth.sessions.manager import SessionManager, get_session_manager
from app.auth.sessions.models import SessionData

logger = logging.getLogger(__name__)


class SessionMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic session management.

    Automatically validates and updates sessions for each request.
    Works alongside JWT authentication to provide enhanced session tracking.
    """

    def __init__(
        self,
        app: ASGIApp,
        session_manager: SessionManager | None = None,
        session_cookie_name: str = "session_id",
        session_header_name: str = "X-Session-ID",
        exempt_paths: list[str] | None = None,
    ):
        """
        Initialize session middleware.

        Args:
            app: FastAPI application
            session_manager: Session manager instance
            session_cookie_name: PGY2-01ie name for session ID
            session_header_name: Header name for session ID
            exempt_paths: List of paths to exempt from session validation
        """
        super().__init__(app)
        self.session_manager = session_manager or get_session_manager()
        self.session_cookie_name = session_cookie_name
        self.session_header_name = session_header_name
        self.exempt_paths = exempt_paths or [
            "/api/auth/login",
            "/api/auth/register",
            "/api/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]

    def _is_path_exempt(self, path: str) -> bool:
        """
        Check if path is exempt from session validation.

        Args:
            path: Request path

        Returns:
            True if path is exempt
        """
        return any(path.startswith(exempt) for exempt in self.exempt_paths)

    def _get_session_id(self, request: Request) -> str | None:
        """
        Extract session ID from request.

        Checks in order:
        1. PGY2-01ie
        2. Header
        3. Query parameter (for websockets)

        Args:
            request: FastAPI request

        Returns:
            Session ID if found, None otherwise
        """
        # Check cookie first
        session_id = request.cookies.get(self.session_cookie_name)
        if session_id:
            return session_id

        # Check header
        session_id = request.headers.get(self.session_header_name)
        if session_id:
            return session_id

        # Check query param (for websockets)
        session_id = request.query_params.get("session_id")
        if session_id:
            return session_id

        return None

    def _get_client_ip(self, request: Request) -> str | None:
        """
        Get client IP address from request.

        Checks proxy headers first, then falls back to direct connection.

        Args:
            request: FastAPI request

        Returns:
            Client IP address
        """
        # Check proxy headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take first IP (client)
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct connection
        if request.client:
            return request.client.host

        return None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with session validation.

        Args:
            request: Incoming request
            call_next: Next middleware/handler in chain

        Returns:
            Response from handler
        """
        # Skip exempt paths
        if self._is_path_exempt(request.url.path):
            return await call_next(request)

        # Get session ID
        session_id = self._get_session_id(request)

        # Validate and update session
        session: SessionData | None = None
        if session_id:
            client_ip = self._get_client_ip(request)

            session = await self.session_manager.validate_session(
                session_id=session_id,
                update_activity=True,
                ip_address=client_ip,
            )

            if session:
                # Attach session to request state for route handlers
                request.state.session = session
                logger.debug(
                    f"Session {session_id} validated for user {session.user_id}"
                )
            else:
                logger.debug(f"Session {session_id} validation failed")

        # Process request
        response = await call_next(request)

        # Optionally set session cookie if not present
        # (This would be done by login endpoint, but can refresh here)
        if session and session_id:
            # Refresh cookie expiration
            response.set_cookie(
                key=self.session_cookie_name,
                value=session_id,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=86400,  # 24 hours
            )

        return response


class SessionState:
    """
    Helper class to access session from request state.

    Usage in route handlers:
        @router.get("/profile")
        async def get_profile(request: Request):
            session = SessionState.get_session(request)
            if session:
                user_id = session.user_id
    """

    @staticmethod
    def get_session(request: Request) -> SessionData | None:
        """
        Get session from request state.

        Args:
            request: FastAPI request

        Returns:
            SessionData if available, None otherwise
        """
        return getattr(request.state, "session", None)

    @staticmethod
    def has_session(request: Request) -> bool:
        """
        Check if request has a valid session.

        Args:
            request: FastAPI request

        Returns:
            True if session exists
        """
        return hasattr(request.state, "session") and request.state.session is not None

    @staticmethod
    def get_user_id(request: Request) -> str | None:
        """
        Get user ID from session.

        Args:
            request: FastAPI request

        Returns:
            User ID if session exists, None otherwise
        """
        session = SessionState.get_session(request)
        return session.user_id if session else None


def require_session(request: Request) -> SessionData:
    """
    Dependency to require a valid session.

    Usage in routes:
        @router.get("/protected")
        async def protected_route(session: SessionData = Depends(require_session)):
            user_id = session.user_id

    Args:
        request: FastAPI request

    Returns:
        SessionData from request state

    Raises:
        HTTPException: If no valid session
    """
    from fastapi import HTTPException, status

    session = SessionState.get_session(request)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No valid session",
        )

    return session
