"""
Input sanitization package for the Residency Scheduler application.

This package provides comprehensive input sanitization to prevent:
- XSS (Cross-Site Scripting) attacks
- SQL injection attempts
- HTML injection
- Path traversal attacks
- Unicode-based attacks

Main exports:
    - sanitize_html: Clean HTML content
    - sanitize_input: General purpose input sanitization
    - detect_xss: Detect potential XSS payloads
    - prevent_sql_injection: Validate against SQL injection patterns
    - normalize_unicode: Normalize Unicode strings
    - SanitizationMiddleware: FastAPI middleware for automatic sanitization
"""

from app.sanitization.html import (
    sanitize_html,
    sanitize_rich_text,
    strip_all_tags,
)
from app.sanitization.middleware import SanitizationMiddleware
from app.sanitization.sql import (
    detect_sql_injection,
    sanitize_sql_input,
    validate_identifier,
)
from app.sanitization.xss import (
    detect_xss,
    normalize_unicode,
    sanitize_input,
    sanitize_url,
)

__all__ = [
    # HTML sanitization
    "sanitize_html",
    "strip_all_tags",
    "sanitize_rich_text",
    # SQL sanitization
    "detect_sql_injection",
    "sanitize_sql_input",
    "validate_identifier",
    # XSS prevention
    "detect_xss",
    "sanitize_input",
    "normalize_unicode",
    "sanitize_url",
    # Middleware
    "SanitizationMiddleware",
]
