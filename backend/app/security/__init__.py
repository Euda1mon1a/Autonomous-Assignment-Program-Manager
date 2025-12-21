"""
Security package for API protection.

This package provides security headers and middleware to protect the API from
common web vulnerabilities:

- XSS (Cross-Site Scripting)
- Clickjacking
- MIME type sniffing
- Information leakage
- Man-in-the-middle attacks

It also provides secret rotation services for automated credential management.

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
    - SecretRotationService: Service for rotating sensitive secrets
"""
from app.security.headers import SecurityHeaders
from app.security.csp import ContentSecurityPolicy
from app.security.middleware import (
    SecurityHeadersMiddleware,
    SecurityHeadersConfig,
    create_security_headers_middleware,
)
from app.security.secret_rotation import (
    RotationConfig,
    RotationPriority,
    RotationResult,
    RotationStatus,
    SecretRotationHistory,
    SecretRotationService,
    SecretType,
    check_rotation_status,
    rotate_api_keys,
    rotate_jwt_key,
)

__all__ = [
    "SecurityHeaders",
    "ContentSecurityPolicy",
    "SecurityHeadersMiddleware",
    "SecurityHeadersConfig",
    "create_security_headers_middleware",
    # Secret Rotation
    "SecretRotationService",
    "SecretRotationHistory",
    "SecretType",
    "RotationStatus",
    "RotationPriority",
    "RotationConfig",
    "RotationResult",
    "rotate_jwt_key",
    "rotate_api_keys",
    "check_rotation_status",
]
