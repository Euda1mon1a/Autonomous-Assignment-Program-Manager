"""
Sensitive data filters for request/response logging.

Provides utilities to mask, redact, or remove sensitive information from logs
to prevent leakage of passwords, tokens, PII, and other confidential data.
"""

import re
from typing import Any, Dict, List, Optional, Set, Union


class SensitiveDataFilter:
    """
    Filter for masking sensitive data in logs.

    Provides multiple strategies for protecting sensitive information:
    - Field-based masking (e.g., password, token fields)
    - Pattern-based masking (e.g., credit card numbers, SSNs)
    - Path-based masking (e.g., /api/v1/auth/login body)
    """

    # Default sensitive field names (case-insensitive)
    DEFAULT_SENSITIVE_FIELDS: Set[str] = {
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "apikey",
        "authorization",
        "auth",
        "bearer",
        "cookie",
        "session",
        "csrf",
        "xsrf",
        "private_key",
        "privatekey",
        "credit_card",
        "creditcard",
        "cvv",
        "ssn",
        "social_security",
        "tax_id",
        "license",
        "passport",
        "pin",
    }

    # Patterns for sensitive data (compiled regex)
    SENSITIVE_PATTERNS: List[tuple[re.Pattern, str]] = [
        # Credit card numbers (basic pattern)
        (re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"), "[REDACTED-CARD]"),
        # SSN format (XXX-XX-XXXX)
        (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED-SSN]"),
        # Email addresses
        (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[REDACTED-EMAIL]"),
        # Bearer tokens (Authorization header pattern)
        (re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), "Bearer [REDACTED]"),
        # API keys (common formats: 32+ hex/alphanumeric chars)
        (re.compile(r"\b[a-f0-9]{32,}\b", re.IGNORECASE), "[REDACTED-KEY]"),
    ]

    def __init__(
        self,
        sensitive_fields: Optional[Set[str]] = None,
        mask_char: str = "*",
        show_prefix_chars: int = 0,
        show_suffix_chars: int = 0,
        custom_patterns: Optional[List[tuple[str, str]]] = None,
    ):
        """
        Initialize sensitive data filter.

        Args:
            sensitive_fields: Set of field names to mask (extends defaults)
            mask_char: Character to use for masking (default: "*")
            show_prefix_chars: Number of characters to show at start (0 = full mask)
            show_suffix_chars: Number of characters to show at end (0 = full mask)
            custom_patterns: Additional regex patterns as [(pattern, replacement), ...]
        """
        self.sensitive_fields = self.DEFAULT_SENSITIVE_FIELDS.copy()
        if sensitive_fields:
            self.sensitive_fields.update(f.lower() for f in sensitive_fields)

        self.mask_char = mask_char
        self.show_prefix_chars = show_prefix_chars
        self.show_suffix_chars = show_suffix_chars

        # Compile custom patterns
        self.custom_patterns = []
        if custom_patterns:
            for pattern, replacement in custom_patterns:
                self.custom_patterns.append((re.compile(pattern), replacement))

    def mask_value(self, value: str, field_name: Optional[str] = None) -> str:
        """
        Mask a single value.

        Args:
            value: String value to mask
            field_name: Optional field name for context-aware masking

        Returns:
            str: Masked value
        """
        if not value:
            return value

        # For known sensitive fields, use configured masking strategy
        if field_name and field_name.lower() in self.sensitive_fields:
            return self._partial_mask(value)

        # Apply pattern-based masking
        masked = value
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            masked = pattern.sub(replacement, masked)

        # Apply custom patterns
        for pattern, replacement in self.custom_patterns:
            masked = pattern.sub(replacement, masked)

        return masked

    def _partial_mask(self, value: str) -> str:
        """
        Create partial mask showing prefix/suffix chars.

        Examples:
            - "password123" -> "********" (full mask)
            - "password123" -> "pas*****23" (prefix=3, suffix=2)
        """
        length = len(value)

        # Full mask if value is too short or no chars to show
        if length <= (self.show_prefix_chars + self.show_suffix_chars):
            return self.mask_char * min(length, 8)

        # Partial mask
        prefix = value[: self.show_prefix_chars] if self.show_prefix_chars > 0 else ""
        suffix = value[-self.show_suffix_chars :] if self.show_suffix_chars > 0 else ""
        mask_length = length - self.show_prefix_chars - self.show_suffix_chars
        mask = self.mask_char * min(mask_length, 8)

        return f"{prefix}{mask}{suffix}"

    def filter_dict(
        self, data: Dict[str, Any], recursive: bool = True
    ) -> Dict[str, Any]:
        """
        Filter sensitive fields from a dictionary.

        Args:
            data: Dictionary to filter
            recursive: Whether to recursively filter nested dicts/lists

        Returns:
            Dict with sensitive fields masked
        """
        if not isinstance(data, dict):
            return data

        filtered = {}
        for key, value in data.items():
            # Check if field name is sensitive
            is_sensitive = key.lower() in self.sensitive_fields

            if is_sensitive:
                # Mask the entire value
                if isinstance(value, str):
                    filtered[key] = self._partial_mask(value)
                else:
                    filtered[key] = "[REDACTED]"
            elif recursive:
                # Recursively filter nested structures
                if isinstance(value, dict):
                    filtered[key] = self.filter_dict(value, recursive=True)
                elif isinstance(value, list):
                    filtered[key] = self._filter_list(value)
                elif isinstance(value, str):
                    # Apply pattern-based masking to string values
                    filtered[key] = self.mask_value(value, field_name=key)
                else:
                    filtered[key] = value
            else:
                filtered[key] = value

        return filtered

    def _filter_list(self, data: List[Any]) -> List[Any]:
        """Filter sensitive data from list items."""
        filtered = []
        for item in data:
            if isinstance(item, dict):
                filtered.append(self.filter_dict(item, recursive=True))
            elif isinstance(item, list):
                filtered.append(self._filter_list(item))
            elif isinstance(item, str):
                filtered.append(self.mask_value(item))
            else:
                filtered.append(item)
        return filtered

    def filter_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Filter sensitive headers.

        Common sensitive headers:
        - Authorization
        - Cookie
        - X-API-Key
        - X-Auth-Token
        """
        filtered = {}
        for key, value in headers.items():
            key_lower = key.lower()

            # Check if header name contains sensitive keywords
            is_sensitive = any(
                sensitive in key_lower for sensitive in self.sensitive_fields
            )

            if is_sensitive:
                filtered[key] = self._partial_mask(value)
            else:
                # Still apply pattern-based masking to catch tokens in custom headers
                filtered[key] = self.mask_value(value, field_name=key)

        return filtered

    def should_log_body(self, path: str, method: str) -> bool:
        """
        Determine if request/response body should be logged.

        Args:
            path: Request path
            method: HTTP method

        Returns:
            bool: True if body should be logged
        """
        # Don't log bodies for auth endpoints (even masked, avoid logging)
        sensitive_paths = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/token",
            "/api/v1/auth/refresh",
            "/api/v1/auth/reset-password",
            "/api/v1/auth/change-password",
        ]

        for sensitive_path in sensitive_paths:
            if path.startswith(sensitive_path):
                return False

        return True


# Global filter instance with sensible defaults
default_filter = SensitiveDataFilter(
    show_prefix_chars=0,  # Full masking by default
    show_suffix_chars=0,
)


def mask_sensitive_data(
    data: Union[Dict[str, Any], List[Any], str],
    filter_instance: Optional[SensitiveDataFilter] = None,
) -> Union[Dict[str, Any], List[Any], str]:
    """
    Convenience function to mask sensitive data.

    Args:
        data: Data to mask (dict, list, or string)
        filter_instance: Optional custom filter instance

    Returns:
        Masked data
    """
    filter_obj = filter_instance or default_filter

    if isinstance(data, dict):
        return filter_obj.filter_dict(data)
    elif isinstance(data, list):
        return filter_obj._filter_list(data)
    elif isinstance(data, str):
        return filter_obj.mask_value(data)
    else:
        return data
