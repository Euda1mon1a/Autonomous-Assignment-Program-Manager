"""
Security headers middleware for hardening HTTP responses.

Adds recommended security headers to protect against common web vulnerabilities:
- XSS attacks (Content-Security-Policy, X-XSS-Protection)
- Clickjacking (X-Frame-Options)
- MIME sniffing (X-Content-Type-Options)
- Information disclosure (X-Powered-By removal)
- HTTPS enforcement (Strict-Transport-Security)
"""
import logging
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.

    Args:
        enable_hsts: Enable HTTP Strict Transport Security header
        hsts_max_age: Max age for HSTS in seconds (default: 1 year)
        frame_options: X-Frame-Options value (DENY, SAMEORIGIN, or None to disable)
        content_type_nosniff: Enable X-Content-Type-Options: nosniff
        xss_protection: Enable X-XSS-Protection header
    """

    def __init__(
        self,
        app,
        enable_hsts: bool = True,
        hsts_max_age: int = 31536000,  # 1 year
        frame_options: Optional[str] = "DENY",
        content_type_nosniff: bool = True,
        xss_protection: bool = True,
    ):
        super().__init__(app)
        self.enable_hsts = enable_hsts
        self.hsts_max_age = hsts_max_age
        self.frame_options = frame_options
        self.content_type_nosniff = content_type_nosniff
        self.xss_protection = xss_protection

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add security headers to response."""
        response = await call_next(request)

        # Remove server identification headers
        response.headers.pop("X-Powered-By", None)
        response.headers.pop("Server", None)

        # Prevent clickjacking
        if self.frame_options:
            response.headers["X-Frame-Options"] = self.frame_options

        # Prevent MIME type sniffing
        if self.content_type_nosniff:
            response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS protection (legacy, but still useful for older browsers)
        if self.xss_protection:
            response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS - only add for HTTPS requests or when explicitly enabled
        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = (
                f"max-age={self.hsts_max_age}; includeSubDomains"
            )

        # Referrer policy - don't leak URL info to external sites
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy - restrict browser features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )

        return response
