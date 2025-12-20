"""
Audit middleware for tracking user context in version history.

This middleware captures the current user from the request and makes it
available to SQLAlchemy-Continuum for audit trail tracking.

Usage:
    Add to FastAPI app:
        app.add_middleware(AuditContextMiddleware)

    The middleware will automatically:
    1. Extract user ID from the request (via JWT token or session)
    2. Set it in context for the duration of the request
    3. Clear it after the request completes

    Version history will then include who made each change.
"""
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger
from app.db.audit import clear_current_user_id, set_current_user_id

logger = get_logger(__name__)


class AuditContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that captures user context for audit logging.

    Extracts user information from the request and stores it in a context
    variable that SQLAlchemy-Continuum can access when recording changes.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and set audit context."""
        user_id = await self._extract_user_id(request)

        try:
            # Set user context for this request
            set_current_user_id(user_id)

            # Log audit context for significant operations
            if request.method in ("POST", "PUT", "PATCH", "DELETE"):
                logger.debug(
                    f"Audit context: user={user_id or 'anonymous'}, "
                    f"method={request.method}, path={request.url.path}"
                )

            # Process the request
            response = await call_next(request)
            return response

        finally:
            # Always clear context after request
            clear_current_user_id()

    async def _extract_user_id(self, request: Request) -> str | None:
        """
        Extract user ID from the request.

        Attempts to get user from:
        1. request.state.user (set by auth dependency)
        2. Authorization header (JWT token)
        3. Returns None for anonymous requests
        """
        # Check if user was set by auth dependency
        if hasattr(request.state, "user") and request.state.user:
            user = request.state.user
            # Handle both User object and dict
            if hasattr(user, "id"):
                return str(user.id)
            if isinstance(user, dict) and "id" in user:
                return str(user["id"])

        # Could extend to decode JWT here if needed
        # For now, return None for anonymous requests
        return None


def get_audit_info(request: Request) -> dict:
    """
    Get audit information for manual logging.

    Returns a dict with:
    - user_id: Current user ID or None
    - method: HTTP method
    - path: Request path
    - ip: Client IP address

    Usage:
        audit_info = get_audit_info(request)
        logger.info(f"Action performed: {audit_info}")
    """
    user_id = None
    if hasattr(request.state, "user") and request.state.user:
        user = request.state.user
        if hasattr(user, "id"):
            user_id = str(user.id)
        elif isinstance(user, dict) and "id" in user:
            user_id = str(user["id"])

    return {
        "user_id": user_id,
        "method": request.method,
        "path": str(request.url.path),
        "ip": request.client.host if request.client else None,
    }
