"""
Security headers middleware for API responses.

Implements security headers based on OWASP recommendations to protect
against common web vulnerabilities including XSS, clickjacking, and
content-type sniffing attacks.
"""

import logging
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all HTTP responses.

    Headers implemented:
    - X-Content-Type-Options: Prevents MIME-type sniffing
    - X-Frame-Options: Prevents clickjacking attacks
    - X-XSS-Protection: Legacy XSS protection (for older browsers)
    - Strict-Transport-Security: Enforces HTTPS connections
    - Referrer-Policy: Controls referrer information in requests
    - Content-Security-Policy: Prevents XSS and injection attacks
    - Permissions-Policy: Controls browser features/APIs
    - Cache-Control: Prevents caching of sensitive responses
    """

    def __init__(
        self,
        app: ASGIApp,
        hsts_max_age: int = 31536000,  # 1 year in seconds
        include_subdomains: bool = True,
        hsts_preload: bool = False,
        content_security_policy: str | None = None,
        permissions_policy: str | None = None,
    ):
        """
        Initialize the security headers middleware.

        Args:
            app: The ASGI application.
            hsts_max_age: Max-Age for Strict-Transport-Security header (seconds).
            include_subdomains: Include subdomains in HSTS policy.
            hsts_preload: Enable HSTS preload list inclusion.
            content_security_policy: Custom CSP policy. If None, uses default.
            permissions_policy: Custom Permissions-Policy. If None, uses default.
        """
        super().__init__(app)
        self.hsts_max_age = hsts_max_age
        self.include_subdomains = include_subdomains
        self.hsts_preload = hsts_preload
        self.content_security_policy = content_security_policy
        self.permissions_policy = permissions_policy

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add security headers to response.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware/handler in the chain.

        Returns:
            Response with security headers added.
        """
        response = await call_next(request)

        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking (use DENY for APIs, SAMEORIGIN for web apps)
        response.headers["X-Frame-Options"] = "DENY"

        # Legacy XSS protection for older browsers
        # Modern browsers use CSP instead, but this helps older clients
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information
        # strict-origin-when-cross-origin: sends full URL to same origin,
        # only origin to cross-origin, nothing to less secure destination
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HTTP Strict Transport Security (HSTS)
        # Only add in production (non-DEBUG mode) to avoid issues in development
        if not settings.DEBUG:
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value

        # Content Security Policy
        # Default is restrictive for API-only applications
        if self.content_security_policy:
            csp = self.content_security_policy
        else:
            # Default CSP for API responses
            csp = (
                "default-src 'none'; "
                "frame-ancestors 'none'; "
                "base-uri 'none'; "
                "form-action 'none'"
            )
        response.headers["Content-Security-Policy"] = csp

        # Permissions Policy (formerly Feature-Policy)
        # Disable sensitive browser features that APIs don't need
        if self.permissions_policy:
            permissions = self.permissions_policy
        else:
            permissions = (
                "accelerometer=(), "
                "camera=(), "
                "geolocation=(), "
                "gyroscope=(), "
                "magnetometer=(), "
                "microphone=(), "
                "payment=(), "
                "usb=()"
            )
        response.headers["Permissions-Policy"] = permissions

        # Cache-Control for sensitive API responses
        # Prevent caching of authenticated responses
        # Only set if not already set by the route handler
        if "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response


def get_security_headers_middleware(
    app: ASGIApp,
    hsts_max_age: int = 31536000,
    include_subdomains: bool = True,
    hsts_preload: bool = False,
    content_security_policy: str | None = None,
    permissions_policy: str | None = None,
) -> SecurityHeadersMiddleware:
    """
    Factory function to create SecurityHeadersMiddleware instance.

    Args:
        app: The ASGI application.
        hsts_max_age: Max-Age for HSTS header (default: 1 year).
        include_subdomains: Include subdomains in HSTS (default: True).
        hsts_preload: Enable HSTS preload (default: False).
        content_security_policy: Custom CSP policy.
        permissions_policy: Custom Permissions-Policy.

    Returns:
        Configured SecurityHeadersMiddleware instance.
    """
    return SecurityHeadersMiddleware(
        app=app,
        hsts_max_age=hsts_max_age,
        include_subdomains=include_subdomains,
        hsts_preload=hsts_preload,
        content_security_policy=content_security_policy,
        permissions_policy=permissions_policy,
    )
