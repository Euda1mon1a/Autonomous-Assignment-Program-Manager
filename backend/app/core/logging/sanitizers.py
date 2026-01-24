"""
Data sanitizers for removing PII and sensitive information from logs.

Provides:
- PII detection and redaction
- Sensitive field masking
- Pattern-based sanitization
- Custom sanitization rules
"""

import re
from typing import Any, Callable, Pattern

# Patterns for PII detection
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_PATTERN = re.compile(
    r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b"
)
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CREDIT_CARD_PATTERN = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")
IP_ADDRESS_PATTERN = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")

# Default sensitive field names
SENSITIVE_FIELDS = {
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
    "private_key",
    "privatekey",
    "authorization",
    "auth",
    "bearer",
    "cookie",
    "session",
    "csrf",
    "xsrf",
    "ssn",
    "social_security",
    "credit_card",
    "creditcard",
    "cvv",
    "pin",
    "license",
    "passport",
    "dob",
    "date_of_birth",
    "birthdate",
}


class SanitizationRule:
    """
    A sanitization rule for detecting and redacting sensitive data.
    """

    def __init__(
        self,
        name: str,
        pattern: Pattern | None = None,
        field_matcher: Callable[[str], bool] | None = None,
        replacement: str = "[REDACTED]",
        enabled: bool = True,
    ):
        """
        Initialize sanitization rule.

        Args:
            name: Rule name
            pattern: Regex pattern to match sensitive data
            field_matcher: Function to match field names
            replacement: Replacement text for redacted data
            enabled: Whether rule is enabled
        """
        self.name = name
        self.pattern = pattern
        self.field_matcher = field_matcher
        self.replacement = replacement
        self.enabled = enabled

    def should_redact_field(self, field_name: str) -> bool:
        """
        Check if field should be redacted.

        Args:
            field_name: Field name to check

        Returns:
            bool: True if field should be redacted
        """
        if not self.enabled or not self.field_matcher:
            return False

        return self.field_matcher(field_name)

    def sanitize_value(self, value: str) -> str:
        """
        Sanitize value using pattern matching.

        Args:
            value: Value to sanitize

        Returns:
            str: Sanitized value
        """
        if not self.enabled or not self.pattern or not isinstance(value, str):
            return value

        return self.pattern.sub(self.replacement, value)


class DataSanitizer:
    """
    Comprehensive data sanitizer for log output.

    Features:
    - PII detection and redaction
    - Sensitive field masking
    - Custom sanitization rules
    - Configurable field and pattern matching
    """

    def __init__(
        self,
        sensitive_fields: set[str] | None = None,
        custom_rules: list[SanitizationRule] | None = None,
        enable_pii_detection: bool = True,
        partial_mask: bool = False,
        mask_char: str = "*",
    ):
        """
        Initialize data sanitizer.

        Args:
            sensitive_fields: Set of field names to redact (extends defaults)
            custom_rules: Custom sanitization rules
            enable_pii_detection: Enable pattern-based PII detection
            partial_mask: Show partial values (e.g., "***-**-1234")
            mask_char: Character to use for masking
        """
        self.sensitive_fields = SENSITIVE_FIELDS.copy()
        if sensitive_fields:
            self.sensitive_fields.update(f.lower() for f in sensitive_fields)

        self.enable_pii_detection = enable_pii_detection
        self.partial_mask = partial_mask
        self.mask_char = mask_char

        # Built-in sanitization rules
        self.rules: list[SanitizationRule] = [
            SanitizationRule(
                name="email",
                pattern=EMAIL_PATTERN,
                replacement="[REDACTED-EMAIL]",
                enabled=enable_pii_detection,
            ),
            SanitizationRule(
                name="phone",
                pattern=PHONE_PATTERN,
                replacement="[REDACTED-PHONE]",
                enabled=enable_pii_detection,
            ),
            SanitizationRule(
                name="ssn",
                pattern=SSN_PATTERN,
                replacement="[REDACTED-SSN]",
                enabled=enable_pii_detection,
            ),
            SanitizationRule(
                name="credit_card",
                pattern=CREDIT_CARD_PATTERN,
                replacement="[REDACTED-CARD]",
                enabled=enable_pii_detection,
            ),
            SanitizationRule(
                name="sensitive_field",
                field_matcher=lambda field: field.lower() in self.sensitive_fields,
                replacement="[REDACTED]",
                enabled=True,
            ),
        ]

        # Add custom rules
        if custom_rules:
            self.rules.extend(custom_rules)

    def sanitize_dict(
        self, data: dict[str, Any], recursive: bool = True
    ) -> dict[str, Any]:
        """
        Sanitize dictionary by redacting sensitive fields.

        Args:
            data: Dictionary to sanitize
            recursive: Whether to recursively sanitize nested structures

        Returns:
            dict: Sanitized dictionary
        """
        if not isinstance(data, dict):
            return data

        sanitized: dict[str, Any] = {}

        for key, value in data.items():
            # Check if field should be redacted by name
            should_redact = self._should_redact_field(key)

            if should_redact:
                if isinstance(value, str):
                    sanitized[key] = self._mask_value(value)
                else:
                    sanitized[key] = "[REDACTED]"
            elif recursive:
                # Recursively sanitize nested structures
                if isinstance(value, dict):
                    sanitized[key] = self.sanitize_dict(value, recursive=True)
                elif isinstance(value, list):
                    sanitized[key] = self._sanitize_list(value)
                elif isinstance(value, str):
                    # Apply pattern-based sanitization
                    sanitized[key] = self._sanitize_string(value)
                else:
                    sanitized[key] = value
            else:
                sanitized[key] = value

        return sanitized

    def _sanitize_list(self, data: list[Any]) -> list[Any]:
        """Sanitize list items."""
        sanitized: list[Any] = []

        for item in data:
            if isinstance(item, dict):
                sanitized.append(self.sanitize_dict(item, recursive=True))
            elif isinstance(item, list):
                sanitized.append(self._sanitize_list(item))
            elif isinstance(item, str):
                sanitized.append(self._sanitize_string(item))
            else:
                sanitized.append(item)

        return sanitized

    def _sanitize_string(self, value: str) -> str:
        """Sanitize string value using pattern matching."""
        sanitized = value

        # Apply all pattern-based rules
        for rule in self.rules:
            if rule.pattern:
                sanitized = rule.sanitize_value(sanitized)

        return sanitized

    def _should_redact_field(self, field_name: str) -> bool:
        """Check if field should be redacted."""
        for rule in self.rules:
            if rule.should_redact_field(field_name):
                return True

        return False

    def _mask_value(self, value: str) -> str:
        """
        Mask sensitive value.

        Args:
            value: Value to mask

        Returns:
            str: Masked value
        """
        if not value:
            return value

        length = len(value)

        if self.partial_mask and length > 4:
            # Show last 4 characters: "***-1234"
            visible = value[-4:]
            mask_length = min(length - 4, 8)
            return self.mask_char * mask_length + visible
        else:
            # Full mask
            return self.mask_char * min(length, 8)

    def sanitize_exception(self, exc: Exception) -> str:
        """
        Sanitize exception message.

        Args:
            exc: Exception to sanitize

        Returns:
            str: Sanitized exception message
        """
        message = str(exc)
        return self._sanitize_string(message)

    def sanitize_log_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize entire log record.

        Args:
            record: Log record dictionary

        Returns:
            dict: Sanitized log record
        """
        sanitized = record.copy()

        # Sanitize message
        if "message" in sanitized and isinstance(sanitized["message"], str):
            sanitized["message"] = self._sanitize_string(sanitized["message"])

        # Sanitize extra fields
        if "extra" in sanitized and isinstance(sanitized["extra"], dict):
            sanitized["extra"] = self.sanitize_dict(sanitized["extra"])

        # Sanitize exception
        if "exception" in sanitized and sanitized["exception"]:
            exc_info = sanitized["exception"]
            if isinstance(exc_info, dict) and "value" in exc_info:
                exc_info["value"] = self._sanitize_string(str(exc_info["value"]))

        return sanitized


# Global sanitizer instance
_global_sanitizer: DataSanitizer | None = None


def get_global_sanitizer() -> DataSanitizer:
    """Get or create global sanitizer instance."""
    global _global_sanitizer
    if _global_sanitizer is None:
        _global_sanitizer = DataSanitizer()
    return _global_sanitizer


def set_global_sanitizer(sanitizer: DataSanitizer) -> None:
    """Set global sanitizer instance."""
    global _global_sanitizer
    _global_sanitizer = sanitizer


def sanitize(data: Any) -> Any:
    """
    Sanitize data using global sanitizer.

    Args:
        data: Data to sanitize (dict, list, or string)

    Returns:
        Any: Sanitized data
    """
    sanitizer = get_global_sanitizer()

    if isinstance(data, dict):
        return sanitizer.sanitize_dict(data)
    elif isinstance(data, list):
        return sanitizer._sanitize_list(data)
    elif isinstance(data, str):
        return sanitizer._sanitize_string(data)
    else:
        return data


def create_custom_rule(
    name: str,
    pattern: str,
    replacement: str = "[REDACTED]",
) -> SanitizationRule:
    """
    Create custom sanitization rule.

    Args:
        name: Rule name
        pattern: Regex pattern string
        replacement: Replacement text

    Returns:
        SanitizationRule: Created rule

    Example:
        # Redact military ID numbers
        rule = create_custom_rule(
            name="military_id",
            pattern=r"\bM\\d{8}\b",
            replacement="[REDACTED-MIL-ID]"
        )
        sanitizer = DataSanitizer(custom_rules=[rule])
    """
    compiled_pattern = re.compile(pattern)
    return SanitizationRule(
        name=name,
        pattern=compiled_pattern,
        replacement=replacement,
    )
