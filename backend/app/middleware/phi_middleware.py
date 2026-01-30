"""PHI Middleware.

This middleware adds warning headers to responses that may contain Protected Health Information (PHI)
and logs access to these endpoints for audit purposes.
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.logging import get_logger

logger = get_logger(__name__)


class PHIMiddleware(BaseHTTPMiddleware):
    """Middleware for PHI tagging and auditing."""

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the middleware."""
        super().__init__(app)
        # Endpoints that are known to return PHI
        self.phi_prefixes = [
            "/api/v1/people",
            "/api/v1/export",
            "/api/v1/schedule",
            "/api/v1/absences",
            # Legacy paths (handled by redirect but good to catch)
            "/api/people",
            "/api/export",
            "/api/schedule",
            "/api/absences",
        ]

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process the request."""
        # Check if request targets a PHI endpoint
        is_phi_endpoint = any(
            request.url.path.startswith(prefix) for prefix in self.phi_prefixes
        )

        if is_phi_endpoint:
            # Audit logging
            # Note: valid user might not be set yet depending on middleware order,
            # but we log what we can.
            user_id = "anonymous"
            if hasattr(request.state, "user") and request.state.user is not None:
                user = request.state.user
                # Handle different user representations (User object, dict, etc.)
                if hasattr(user, "username"):
                    user_id = user.username
                elif hasattr(user, "id"):
                    user_id = str(user.id)
                elif isinstance(user, dict):
                    user_id = user.get("username", str(user.get("id", "unknown")))

            logger.info(
                "PHI_ACCESS_ATTEMPT",
                user=user_id,
                endpoint=request.url.path,
                method=request.method,
                ip=request.client.host if request.client else "unknown",
            )

        response = await call_next(request)

        # Add warning headers if it was a PHI endpoint
        if is_phi_endpoint:
            response.headers["X-Contains-PHI"] = "true"
            # We don't list specific fields in the header to avoid leaking schema info,
            # just a general warning.
            response.headers["X-PHI-Handling"] = "CONFIDENTIAL - DO NOT DISTRIBUTE"

        return response
