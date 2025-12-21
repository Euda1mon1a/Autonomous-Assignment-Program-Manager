"""
Security headers configuration.

This module defines security headers to protect against common web vulnerabilities:
- XSS attacks
- Clickjacking
- MIME type sniffing
- Information leakage
"""
from typing import Dict


class SecurityHeaders:
    """
    Security headers constants and configuration.

    Implements security best practices from OWASP and industry standards.
    """

    ***REMOVED*** Strict Transport Security (HSTS)
    ***REMOVED*** Forces HTTPS connections for 1 year, including subdomains
    ***REMOVED*** Preload: allows inclusion in browser HSTS preload lists
    HSTS_HEADER = "Strict-Transport-Security"
    HSTS_VALUE_PRODUCTION = "max-age=31536000; includeSubDomains; preload"
    HSTS_VALUE_DEVELOPMENT = "max-age=0"  ***REMOVED*** Disabled in development

    ***REMOVED*** X-Frame-Options
    ***REMOVED*** Prevents clickjacking by disallowing iframe embedding
    FRAME_OPTIONS_HEADER = "X-Frame-Options"
    FRAME_OPTIONS_VALUE = "DENY"  ***REMOVED*** Never allow framing

    ***REMOVED*** X-Content-Type-Options
    ***REMOVED*** Prevents MIME type sniffing
    CONTENT_TYPE_OPTIONS_HEADER = "X-Content-Type-Options"
    CONTENT_TYPE_OPTIONS_VALUE = "nosniff"

    ***REMOVED*** X-XSS-Protection
    ***REMOVED*** Legacy header for older browsers (modern browsers use CSP)
    ***REMOVED*** Mode=block stops page rendering if XSS detected
    XSS_PROTECTION_HEADER = "X-XSS-Protection"
    XSS_PROTECTION_VALUE = "1; mode=block"

    ***REMOVED*** Referrer-Policy
    ***REMOVED*** Controls how much referrer information is included with requests
    ***REMOVED*** strict-origin-when-cross-origin: full URL for same-origin, origin only for cross-origin HTTPS
    REFERRER_POLICY_HEADER = "Referrer-Policy"
    REFERRER_POLICY_VALUE = "strict-origin-when-cross-origin"

    ***REMOVED*** Permissions-Policy (formerly Feature-Policy)
    ***REMOVED*** Controls which browser features can be used
    ***REMOVED*** Restricts access to sensitive APIs like camera, microphone, geolocation
    PERMISSIONS_POLICY_HEADER = "Permissions-Policy"
    PERMISSIONS_POLICY_VALUE = (
        "accelerometer=(), "
        "camera=(), "
        "geolocation=(), "
        "gyroscope=(), "
        "magnetometer=(), "
        "microphone=(), "
        "payment=(), "
        "usb=()"
    )

    @classmethod
    def get_headers(cls, debug: bool = False) -> Dict[str, str]:
        """
        Get all security headers as a dictionary.

        Args:
            debug: Whether running in debug/development mode.
                   In debug mode, HSTS is disabled to allow HTTP.

        Returns:
            Dict[str, str]: Dictionary of header names to values.
        """
        return {
            cls.HSTS_HEADER: cls.HSTS_VALUE_DEVELOPMENT if debug else cls.HSTS_VALUE_PRODUCTION,
            cls.FRAME_OPTIONS_HEADER: cls.FRAME_OPTIONS_VALUE,
            cls.CONTENT_TYPE_OPTIONS_HEADER: cls.CONTENT_TYPE_OPTIONS_VALUE,
            cls.XSS_PROTECTION_HEADER: cls.XSS_PROTECTION_VALUE,
            cls.REFERRER_POLICY_HEADER: cls.REFERRER_POLICY_VALUE,
            cls.PERMISSIONS_POLICY_HEADER: cls.PERMISSIONS_POLICY_VALUE,
        }

    @classmethod
    def get_hsts_header(cls, debug: bool = False) -> tuple[str, str]:
        """
        Get HSTS header name and value.

        Args:
            debug: Whether running in debug/development mode.

        Returns:
            tuple[str, str]: Header name and value.
        """
        value = cls.HSTS_VALUE_DEVELOPMENT if debug else cls.HSTS_VALUE_PRODUCTION
        return (cls.HSTS_HEADER, value)

    @classmethod
    def get_frame_options_header(cls) -> tuple[str, str]:
        """
        Get X-Frame-Options header name and value.

        Returns:
            tuple[str, str]: Header name and value.
        """
        return (cls.FRAME_OPTIONS_HEADER, cls.FRAME_OPTIONS_VALUE)

    @classmethod
    def get_content_type_options_header(cls) -> tuple[str, str]:
        """
        Get X-Content-Type-Options header name and value.

        Returns:
            tuple[str, str]: Header name and value.
        """
        return (cls.CONTENT_TYPE_OPTIONS_HEADER, cls.CONTENT_TYPE_OPTIONS_VALUE)

    @classmethod
    def get_xss_protection_header(cls) -> tuple[str, str]:
        """
        Get X-XSS-Protection header name and value.

        Returns:
            tuple[str, str]: Header name and value.
        """
        return (cls.XSS_PROTECTION_HEADER, cls.XSS_PROTECTION_VALUE)

    @classmethod
    def get_referrer_policy_header(cls) -> tuple[str, str]:
        """
        Get Referrer-Policy header name and value.

        Returns:
            tuple[str, str]: Header name and value.
        """
        return (cls.REFERRER_POLICY_HEADER, cls.REFERRER_POLICY_VALUE)

    @classmethod
    def get_permissions_policy_header(cls) -> tuple[str, str]:
        """
        Get Permissions-Policy header name and value.

        Returns:
            tuple[str, str]: Header name and value.
        """
        return (cls.PERMISSIONS_POLICY_HEADER, cls.PERMISSIONS_POLICY_VALUE)
