"""
Content Security Policy (CSP) configuration.

CSP is a critical security layer that helps detect and mitigate certain types of attacks,
including Cross-Site Scripting (XSS) and data injection attacks.

Reference: https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP
"""


class ContentSecurityPolicy:
    """
    Content Security Policy builder and configuration.

    Implements CSP directives to control resource loading and execution.
    Different policies for development (more permissive) vs production (strict).
    """

    # CSP Directives
    DEFAULT_SRC = "default-src"
    SCRIPT_SRC = "script-src"
    STYLE_SRC = "style-src"
    IMG_SRC = "img-src"
    FONT_SRC = "font-src"
    CONNECT_SRC = "connect-src"
    FRAME_SRC = "frame-src"
    OBJECT_SRC = "object-src"
    MEDIA_SRC = "media-src"
    WORKER_SRC = "worker-src"
    FORM_ACTION = "form-action"
    FRAME_ANCESTORS = "frame-ancestors"
    BASE_URI = "base-uri"
    UPGRADE_INSECURE_REQUESTS = "upgrade-insecure-requests"

    # CSP Sources
    SELF = "'self'"
    NONE = "'none'"
    UNSAFE_INLINE = "'unsafe-inline'"
    UNSAFE_EVAL = "'unsafe-eval'"
    DATA = "data:"
    BLOB = "blob:"
    HTTPS = "https:"

    @classmethod
    def get_production_policy(cls) -> dict[str, list[str]]:
        """
        Get strict CSP policy for production.

        Production policy:
        - No unsafe-inline or unsafe-eval
        - Strict source whitelisting
        - HTTPS upgrade enforced
        - No object/embed tags allowed

        Returns:
            Dict[str, List[str]]: CSP directives and their values.
        """
        return {
            cls.DEFAULT_SRC: [cls.SELF],
            cls.SCRIPT_SRC: [cls.SELF],
            cls.STYLE_SRC: [cls.SELF],
            cls.IMG_SRC: [cls.SELF, cls.DATA, cls.HTTPS],
            cls.FONT_SRC: [cls.SELF, cls.DATA],
            cls.CONNECT_SRC: [cls.SELF],
            cls.FRAME_SRC: [cls.NONE],
            cls.OBJECT_SRC: [cls.NONE],
            cls.MEDIA_SRC: [cls.SELF],
            cls.WORKER_SRC: [cls.SELF, cls.BLOB],
            cls.FORM_ACTION: [cls.SELF],
            cls.FRAME_ANCESTORS: [cls.NONE],
            cls.BASE_URI: [cls.SELF],
            cls.UPGRADE_INSECURE_REQUESTS: [],  # No value needed
        }

    @classmethod
    def get_development_policy(cls) -> dict[str, list[str]]:
        """
        Get permissive CSP policy for development.

        Development policy:
        - Allows unsafe-inline for hot module replacement
        - Allows localhost connections
        - More permissive for development tools
        - Still blocks dangerous directives (object-src, frame-ancestors)

        Returns:
            Dict[str, List[str]]: CSP directives and their values.
        """
        return {
            cls.DEFAULT_SRC: [cls.SELF],
            cls.SCRIPT_SRC: [
                cls.SELF,
                cls.UNSAFE_INLINE,
                cls.UNSAFE_EVAL,
                "http://localhost:*",
            ],
            cls.STYLE_SRC: [cls.SELF, cls.UNSAFE_INLINE, "http://localhost:*"],
            cls.IMG_SRC: [cls.SELF, cls.DATA, cls.BLOB, "http://localhost:*"],
            cls.FONT_SRC: [cls.SELF, cls.DATA, "http://localhost:*"],
            cls.CONNECT_SRC: [cls.SELF, "http://localhost:*", "ws://localhost:*"],
            cls.FRAME_SRC: [cls.SELF],
            cls.OBJECT_SRC: [cls.NONE],
            cls.MEDIA_SRC: [cls.SELF],
            cls.WORKER_SRC: [cls.SELF, cls.BLOB],
            cls.FORM_ACTION: [cls.SELF],
            cls.FRAME_ANCESTORS: [cls.NONE],
            cls.BASE_URI: [cls.SELF],
        }

    @classmethod
    def get_api_policy(cls) -> dict[str, list[str]]:
        """
        Get strict CSP policy specifically for API endpoints.

        API policy:
        - Very restrictive as APIs don't render HTML
        - Blocks scripts, styles, and media
        - Only allows connections to self

        Returns:
            Dict[str, List[str]]: CSP directives and their values.
        """
        return {
            cls.DEFAULT_SRC: [cls.NONE],
            cls.SCRIPT_SRC: [cls.NONE],
            cls.STYLE_SRC: [cls.NONE],
            cls.IMG_SRC: [cls.NONE],
            cls.FONT_SRC: [cls.NONE],
            cls.CONNECT_SRC: [cls.SELF],
            cls.FRAME_SRC: [cls.NONE],
            cls.OBJECT_SRC: [cls.NONE],
            cls.MEDIA_SRC: [cls.NONE],
            cls.WORKER_SRC: [cls.NONE],
            cls.FORM_ACTION: [cls.NONE],
            cls.FRAME_ANCESTORS: [cls.NONE],
            cls.BASE_URI: [cls.NONE],
        }

    @classmethod
    def build_header_value(cls, policy: dict[str, list[str]]) -> str:
        """
        Build CSP header value from policy dictionary.

        Args:
            policy: Dictionary of CSP directives to source lists.

        Returns:
            str: Formatted CSP header value.

        Example:
            >>> policy = {
            ...     "default-src": ["'self'"],
            ...     "script-src": ["'self'", "'unsafe-inline'"]
            ... }
            >>> build_header_value(policy)
            "default-src 'self'; script-src 'self' 'unsafe-inline'"
        """
        directives = []
        for directive, sources in policy.items():
            if sources:
                # Directive with sources
                sources_str = " ".join(sources)
                directives.append(f"{directive} {sources_str}")
            else:
                # Directive without sources (e.g., upgrade-insecure-requests)
                directives.append(directive)

        return "; ".join(directives)

    @classmethod
    def get_header(cls, debug: bool = False, api_only: bool = False) -> tuple[str, str]:
        """
        Get Content-Security-Policy header name and value.

        Args:
            debug: Whether running in debug/development mode.
            api_only: Whether to use strict API-only policy.

        Returns:
            tuple[str, str]: Header name and formatted policy value.
        """
        if api_only:
            policy = cls.get_api_policy()
        elif debug:
            policy = cls.get_development_policy()
        else:
            policy = cls.get_production_policy()

        header_value = cls.build_header_value(policy)
        return ("Content-Security-Policy", header_value)

    @classmethod
    def get_report_only_header(cls, debug: bool = False) -> tuple[str, str]:
        """
        Get Content-Security-Policy-Report-Only header.

        This header reports violations without blocking them.
        Useful for testing CSP policies before enforcement.

        Args:
            debug: Whether running in debug/development mode.

        Returns:
            tuple[str, str]: Header name and formatted policy value.
        """
        policy = cls.get_development_policy() if debug else cls.get_production_policy()
        header_value = cls.build_header_value(policy)
        return ("Content-Security-Policy-Report-Only", header_value)

    @classmethod
    def add_source(
        cls, policy: dict[str, list[str]], directive: str, source: str
    ) -> None:
        """
        Add a source to a CSP directive in-place.

        Args:
            policy: CSP policy dictionary to modify.
            directive: CSP directive name (e.g., "script-src").
            source: Source to add (e.g., "https://cdn.example.com").
        """
        if directive not in policy:
            policy[directive] = []
        if source not in policy[directive]:
            policy[directive].append(source)

    @classmethod
    def remove_source(
        cls, policy: dict[str, list[str]], directive: str, source: str
    ) -> None:
        """
        Remove a source from a CSP directive in-place.

        Args:
            policy: CSP policy dictionary to modify.
            directive: CSP directive name.
            source: Source to remove.
        """
        if directive in policy and source in policy[directive]:
            policy[directive].remove(source)
