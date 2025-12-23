"""
Validation error messages with localization support.

Provides centralized error messages for validation failures with support
for multiple languages and formatted message templates.
"""

from enum import Enum
from typing import Any


class Locale(str, Enum):
    """Supported locales for error messages."""

    EN_US = "en_US"
    ES_ES = "es_ES"
    FR_FR = "fr_FR"


class ValidationMessageType(str, Enum):
    """Types of validation error messages."""

    REQUIRED = "required"
    INVALID_TYPE = "invalid_type"
    INVALID_FORMAT = "invalid_format"
    OUT_OF_RANGE = "out_of_range"
    TOO_SHORT = "too_short"
    TOO_LONG = "too_long"
    INVALID_ENUM = "invalid_enum"
    PATTERN_MISMATCH = "pattern_mismatch"
    CUSTOM = "custom"
    CROSS_FIELD = "cross_field"
    CONDITIONAL = "conditional"


# Error message templates by locale
ERROR_MESSAGES: dict[Locale, dict[ValidationMessageType, str]] = {
    Locale.EN_US: {
        ValidationMessageType.REQUIRED: "{field} is required",
        ValidationMessageType.INVALID_TYPE: "{field} must be of type {expected_type}",
        ValidationMessageType.INVALID_FORMAT: "{field} has invalid format",
        ValidationMessageType.OUT_OF_RANGE: (
            "{field} must be between {min_value} and {max_value}"
        ),
        ValidationMessageType.TOO_SHORT: (
            "{field} must be at least {min_length} characters"
        ),
        ValidationMessageType.TOO_LONG: (
            "{field} must not exceed {max_length} characters"
        ),
        ValidationMessageType.INVALID_ENUM: (
            "{field} must be one of: {allowed_values}"
        ),
        ValidationMessageType.PATTERN_MISMATCH: (
            "{field} does not match required pattern"
        ),
        ValidationMessageType.CUSTOM: "{message}",
        ValidationMessageType.CROSS_FIELD: "{message}",
        ValidationMessageType.CONDITIONAL: "{message}",
    },
    Locale.ES_ES: {
        ValidationMessageType.REQUIRED: "{field} es requerido",
        ValidationMessageType.INVALID_TYPE: "{field} debe ser de tipo {expected_type}",
        ValidationMessageType.INVALID_FORMAT: "{field} tiene formato inválido",
        ValidationMessageType.OUT_OF_RANGE: (
            "{field} debe estar entre {min_value} y {max_value}"
        ),
        ValidationMessageType.TOO_SHORT: (
            "{field} debe tener al menos {min_length} caracteres"
        ),
        ValidationMessageType.TOO_LONG: (
            "{field} no debe exceder {max_length} caracteres"
        ),
        ValidationMessageType.INVALID_ENUM: (
            "{field} debe ser uno de: {allowed_values}"
        ),
        ValidationMessageType.PATTERN_MISMATCH: (
            "{field} no coincide con el patrón requerido"
        ),
        ValidationMessageType.CUSTOM: "{message}",
        ValidationMessageType.CROSS_FIELD: "{message}",
        ValidationMessageType.CONDITIONAL: "{message}",
    },
    Locale.FR_FR: {
        ValidationMessageType.REQUIRED: "{field} est requis",
        ValidationMessageType.INVALID_TYPE: "{field} doit être de type {expected_type}",
        ValidationMessageType.INVALID_FORMAT: "{field} a un format invalide",
        ValidationMessageType.OUT_OF_RANGE: (
            "{field} doit être entre {min_value} et {max_value}"
        ),
        ValidationMessageType.TOO_SHORT: (
            "{field} doit contenir au moins {min_length} caractères"
        ),
        ValidationMessageType.TOO_LONG: (
            "{field} ne doit pas dépasser {max_length} caractères"
        ),
        ValidationMessageType.INVALID_ENUM: (
            "{field} doit être l'un de: {allowed_values}"
        ),
        ValidationMessageType.PATTERN_MISMATCH: (
            "{field} ne correspond pas au modèle requis"
        ),
        ValidationMessageType.CUSTOM: "{message}",
        ValidationMessageType.CROSS_FIELD: "{message}",
        ValidationMessageType.CONDITIONAL: "{message}",
    },
}


def get_error_message(
    message_type: ValidationMessageType, locale: Locale = Locale.EN_US, **params: Any
) -> str:
    """
    Get formatted error message for a validation failure.

    Args:
        message_type: Type of validation error
        locale: Language/locale for message
        **params: Parameters to format into message template

    Returns:
        str: Formatted error message

    Example:
        >>> get_error_message(
        ...     ValidationMessageType.OUT_OF_RANGE,
        ...     field="age",
        ...     min_value=18,
        ...     max_value=65
        ... )
        'age must be between 18 and 65'
    """
    template = ERROR_MESSAGES.get(locale, ERROR_MESSAGES[Locale.EN_US]).get(
        message_type, "{field}: validation failed"
    )
    return template.format(**params)


def format_field_name(field: str) -> str:
    """
    Format a field name for display in error messages.

    Converts snake_case to Title Case and handles special cases.

    Args:
        field: Field name in snake_case

    Returns:
        str: Human-readable field name

    Example:
        >>> format_field_name("first_name")
        'First Name'
        >>> format_field_name("pgy_level")
        'PGY Level'
    """
    # Special cases
    special_cases = {
        "pgy_level": "PGY Level",
        "acgme": "ACGME",
        "id": "ID",
        "uuid": "UUID",
        "url": "URL",
        "api": "API",
    }

    if field.lower() in special_cases:
        return special_cases[field.lower()]

    # Convert snake_case to Title Case
    return " ".join(word.capitalize() for word in field.split("_"))


class ValidationMessage:
    """Container for validation error messages with context."""

    def __init__(
        self,
        message_type: ValidationMessageType,
        field: str,
        locale: Locale = Locale.EN_US,
        **params: Any,
    ):
        """
        Initialize validation message.

        Args:
            message_type: Type of validation error
            field: Field name that failed validation
            locale: Language/locale for message
            **params: Additional parameters for message formatting
        """
        self.message_type = message_type
        self.field = field
        self.locale = locale
        self.params = params
        self._formatted_field = format_field_name(field)

    def __str__(self) -> str:
        """
        Get formatted error message.

        Returns:
            str: Human-readable error message
        """
        return get_error_message(
            self.message_type, self.locale, field=self._formatted_field, **self.params
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert message to dictionary for API responses.

        Returns:
            dict: Message data including type, field, and formatted message
        """
        return {
            "type": self.message_type.value,
            "field": self.field,
            "message": str(self),
            "params": self.params,
        }


# Predefined common validation messages
def required_field(field: str, locale: Locale = Locale.EN_US) -> ValidationMessage:
    """Create 'required field' validation message."""
    return ValidationMessage(ValidationMessageType.REQUIRED, field, locale)


def invalid_type(
    field: str, expected_type: str, locale: Locale = Locale.EN_US
) -> ValidationMessage:
    """Create 'invalid type' validation message."""
    return ValidationMessage(
        ValidationMessageType.INVALID_TYPE, field, locale, expected_type=expected_type
    )


def out_of_range(
    field: str, min_value: Any, max_value: Any, locale: Locale = Locale.EN_US
) -> ValidationMessage:
    """Create 'out of range' validation message."""
    return ValidationMessage(
        ValidationMessageType.OUT_OF_RANGE,
        field,
        locale,
        min_value=min_value,
        max_value=max_value,
    )


def invalid_enum(
    field: str, allowed_values: list[str], locale: Locale = Locale.EN_US
) -> ValidationMessage:
    """Create 'invalid enum value' validation message."""
    return ValidationMessage(
        ValidationMessageType.INVALID_ENUM,
        field,
        locale,
        allowed_values=", ".join(str(v) for v in allowed_values),
    )


def custom_message(
    field: str, message: str, locale: Locale = Locale.EN_US
) -> ValidationMessage:
    """Create custom validation message."""
    return ValidationMessage(
        ValidationMessageType.CUSTOM, field, locale, message=message
    )
