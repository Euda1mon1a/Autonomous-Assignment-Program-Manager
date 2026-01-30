"""
Security headers middleware.

Automatically adds security headers to all HTTP responses.
Implements defense-in-depth security strategy for the API.
"""

import logging
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.security.csp import ContentSecurityPolicy
from app.security.headers import SecurityHeaders

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.

    Features:
    - HSTS (HTTP Strict Transport Security)
    - X-Frame-Options (clickjacking protection)
    - X-Content-Type-Options (MIME sniffing protection)
    - X-XSS-Protection (XSS filter for legacy browsers)
    - Content-Security-Policy (XSS and injection protection)
    - Referrer-Policy (referrer information control)
    - Permissions-Policy (browser feature control)

    The middleware adapts headers based on debug mode:
    - Production: Strict security headers enforced
    - Development: Relaxed headers to allow local development

    Args:
        app: ASGI application instance.
        debug: Whether running in debug/development mode.
        enable_csp: Whether to enable Content-Security-Policy header.
        api_only: Whether to use strict API-only CSP policy.
    """

    def __init__(
        self,
        app: ASGIApp,
        debug: bool = False,
        enable_csp: bool = True,
        api_only: bool = True,
    ) -> None:
        """
        Initialize security headers middleware.

        Args:
            app: ASGI application.
            debug: Debug mode flag.
            enable_csp: Enable Content-Security-Policy.
            api_only: Use API-only CSP policy (recommended for JSON APIs).
        """
        super().__init__(app)
        self.debug = debug
        self.enable_csp = enable_csp
        self.api_only = api_only

        # Pre-compute static headers for performance
        self._static_headers = SecurityHeaders.get_headers(debug=self.debug)

        # Log configuration at startup
        mode = "development" if self.debug else "production"
        csp_status = (
            "enabled (API-only)"
            if self.api_only
            else "enabled"
            if self.enable_csp
            else "disabled"
        )
        logger.info(
            f"Security headers middleware initialized: mode={mode}, CSP={csp_status}"
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add security headers to response.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware/handler in chain.

        Returns:
            Response: HTTP response with security headers added.
        """
        # Process request through the application
        response = await call_next(request)

        # Add static security headers
        for header_name, header_value in self._static_headers.items():
            response.headers[header_name] = header_value

            # Add Content-Security-Policy if enabled
        if self.enable_csp:
            csp_header, csp_value = ContentSecurityPolicy.get_header(
                debug=self.debug, api_only=self.api_only
            )
            response.headers[csp_header] = csp_value

        return response


class SecurityHeadersConfig:
    """
    Configuration for security headers middleware.

    Provides a centralized configuration interface for security headers.
    """

    def __init__(
        self,
        debug: bool = False,
        enable_hsts: bool = True,
        enable_frame_options: bool = True,
        enable_content_type_options: bool = True,
        enable_xss_protection: bool = True,
        enable_referrer_policy: bool = True,
        enable_permissions_policy: bool = True,
        enable_csp: bool = True,
        csp_api_only: bool = True,
    ) -> None:
        """
        Initialize security headers configuration.

        Args:
            debug: Debug mode flag.
            enable_hsts: Enable HSTS header.
            enable_frame_options: Enable X-Frame-Options header.
            enable_content_type_options: Enable X-Content-Type-Options header.
            enable_xss_protection: Enable X-XSS-Protection header.
            enable_referrer_policy: Enable Referrer-Policy header.
            enable_permissions_policy: Enable Permissions-Policy header.
            enable_csp: Enable Content-Security-Policy header.
            csp_api_only: Use strict API-only CSP policy.
        """
        self.debug = debug
        self.enable_hsts = enable_hsts
        self.enable_frame_options = enable_frame_options
        self.enable_content_type_options = enable_content_type_options
        self.enable_xss_protection = enable_xss_protection
        self.enable_referrer_policy = enable_referrer_policy
        self.enable_permissions_policy = enable_permissions_policy
        self.enable_csp = enable_csp
        self.csp_api_only = csp_api_only

    def get_headers(self) -> dict[str, str]:
        """
        Get all enabled security headers as a dictionary.

        Returns:
            dict[str, str]: Dictionary of enabled headers.
        """
        headers = {}

        if self.enable_hsts:
            name, value = SecurityHeaders.get_hsts_header(debug=self.debug)
            headers[name] = value

        if self.enable_frame_options:
            name, value = SecurityHeaders.get_frame_options_header()
            headers[name] = value

        if self.enable_content_type_options:
            name, value = SecurityHeaders.get_content_type_options_header()
            headers[name] = value

        if self.enable_xss_protection:
            name, value = SecurityHeaders.get_xss_protection_header()
            headers[name] = value

        if self.enable_referrer_policy:
            name, value = SecurityHeaders.get_referrer_policy_header()
            headers[name] = value

        if self.enable_permissions_policy:
            name, value = SecurityHeaders.get_permissions_policy_header()
            headers[name] = value

        if self.enable_csp:
            name, value = ContentSecurityPolicy.get_header(
                debug=self.debug, api_only=self.csp_api_only
            )
            headers[name] = value

        return headers


def create_security_headers_middleware(
    debug: bool = False,
    enable_csp: bool = True,
    api_only: bool = True,
) -> type[SecurityHeadersMiddleware]:
    """
    Factory function to create configured SecurityHeadersMiddleware.

    Args:
        debug: Whether running in debug/development mode.
        enable_csp: Whether to enable Content-Security-Policy.
        api_only: Whether to use strict API-only CSP policy.

    Returns:
        type[SecurityHeadersMiddleware]: Configured middleware class.

    Example:
        >>> from fastapi import FastAPI
        >>> from app.security.middleware import create_security_headers_middleware
        >>>
        >>> app = FastAPI()
        >>> middleware = create_security_headers_middleware(debug=False)
        >>> app.add_middleware(middleware)
    """

    # Create a configured middleware class
    class ConfiguredSecurityHeadersMiddleware(SecurityHeadersMiddleware):
        def __init__(self, app: ASGIApp) -> None:
            super().__init__(
                app=app,
                debug=debug,
                enable_csp=enable_csp,
                api_only=api_only,
            )

    return ConfiguredSecurityHeadersMiddleware
