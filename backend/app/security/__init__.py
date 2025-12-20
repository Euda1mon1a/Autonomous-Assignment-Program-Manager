"""
Security package for API protection.

This package provides security headers and middleware to protect the API from
common web vulnerabilities:

- XSS (Cross-Site Scripting)
- Clickjacking
- MIME type sniffing
- Information leakage
- Man-in-the-middle attacks

Usage:
    from app.security import SecurityHeadersMiddleware
    from fastapi import FastAPI

    app = FastAPI()
    app.add_middleware(
        SecurityHeadersMiddleware,
        debug=False,
        enable_csp=True,
        api_only=True
    )

Components:
    - SecurityHeaders: Header constants and configuration
    - ContentSecurityPolicy: CSP policy builder
    - SecurityHeadersMiddleware: Middleware for automatic header injection
    - SecurityHeadersConfig: Configuration helper
"""
from app.security.headers import SecurityHeaders
from app.security.csp import ContentSecurityPolicy
from app.security.middleware import (
    SecurityHeadersMiddleware,
    SecurityHeadersConfig,
    create_security_headers_middleware,
)

__all__ = [
    "SecurityHeaders",
    "ContentSecurityPolicy",
    "SecurityHeadersMiddleware",
    "SecurityHeadersConfig",
    "create_security_headers_middleware",
]
