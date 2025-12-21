"""
Common validation functions for input validation framework.

Provides reusable validators for common data types and patterns:
- Email validation
- Phone number validation
- Name validation
- UUID validation
- Numeric range validation
- String length and pattern validation
"""
import re
import uuid
from typing import Any

from pydantic import EmailStr, ValidationError, validate_email


class ValidationError(Exception):
    """Base exception for validation errors."""
    pass


def validate_email_address(email: str) -> str:
    """
    Validate email address format.

    Uses Pydantic's EmailStr validation for RFC-compliant email checking.

    Args:
        email: Email address to validate

    Returns:
        str: Validated and normalized email address (lowercase)

    Raises:
        ValidationError: If email format is invalid

    Examples:
        >>> validate_email_address("user@example.com")
        'user@example.com'
        >>> validate_email_address("Invalid.Email")
        ValidationError: Invalid email format
    """
    if not email:
        raise ValidationError("Email address cannot be empty")

    try:
        # Pydantic v2 validation
        validated = validate_email(email)
        # Return normalized email (lowercase)
        return validated[1].lower()
    except (ValidationError, ValueError) as e:
        raise ValidationError(f"Invalid email format: {email}") from e


def validate_phone_number(phone: str, allow_international: bool = True) -> str:
    """
    Validate phone number format.

    Supports US and international phone numbers.
    Strips formatting characters and validates digit count.

    Args:
        phone: Phone number to validate
        allow_international: Allow international format (default: True)

    Returns:
        str: Validated phone number (digits only)

    Raises:
        ValidationError: If phone number format is invalid

    Examples:
        >>> validate_phone_number("(555) 123-4567")
        '5551234567'
        >>> validate_phone_number("+1-555-123-4567")
        '15551234567'
    """
    if not phone:
        raise ValidationError("Phone number cannot be empty")

    # Remove common formatting characters
    digits_only = re.sub(r'[\s\-\(\)\+\.]', '', phone)

    # Check if contains only digits (and optionally leading +)
    if not re.match(r'^\+?\d+$', phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('.', '')):
        raise ValidationError(f"Phone number contains invalid characters: {phone}")

    # US phone number: 10 digits
    if len(digits_only) == 10:
        return digits_only

    # US with country code: 11 digits (1 + 10)
    if len(digits_only) == 11 and digits_only.startswith('1'):
        return digits_only

    # International numbers (allow if enabled)
    if allow_international and 7 <= len(digits_only) <= 15:
        return digits_only

    raise ValidationError(
        f"Invalid phone number length: {len(digits_only)} digits. "
        f"Expected 10 (US) or 11 (US with country code) digits"
    )


def validate_name(name: str, min_length: int = 1, max_length: int = 255) -> str:
    """
    Validate person name.

    Checks for:
    - Non-empty string
    - Reasonable length
    - Valid characters (letters, spaces, hyphens, apostrophes)
    - No SQL injection patterns

    Args:
        name: Name to validate
        min_length: Minimum name length (default: 1)
        max_length: Maximum name length (default: 255)

    Returns:
        str: Validated and trimmed name

    Raises:
        ValidationError: If name is invalid
    """
    if not name:
        raise ValidationError("Name cannot be empty")

    # Trim whitespace
    name = name.strip()

    # Check length
    if len(name) < min_length:
        raise ValidationError(f"Name too short: minimum {min_length} characters")

    if len(name) > max_length:
        raise ValidationError(f"Name too long: maximum {max_length} characters")

    # Allow letters (including unicode), spaces, hyphens, apostrophes, and periods
    # This supports names like "O'Brien", "Jean-Pierre", "Dr. Smith", "José María"
    if not re.match(r"^[\w\s\-'\.]+$", name, re.UNICODE):
        raise ValidationError(
            f"Name contains invalid characters. Only letters, spaces, "
            f"hyphens, apostrophes, and periods are allowed"
        )

    # Check for suspicious SQL patterns (defense in depth)
    sql_patterns = [
        r'(;|\-\-|\/\*|\*\/)',  # SQL comment markers
        r'(union|select|insert|update|delete|drop|create|alter)\s',  # SQL keywords
        r'(\bor\b|\band\b)\s*[\'\"0-9]',  # OR/AND with quotes or numbers
    ]

    for pattern in sql_patterns:
        if re.search(pattern, name.lower()):
            raise ValidationError(
                "Name contains suspicious patterns that are not allowed"
            )

    return name


def validate_uuid(value: str | uuid.UUID) -> uuid.UUID:
    """
    Validate UUID format.

    Args:
        value: UUID string or UUID object

    Returns:
        uuid.UUID: Validated UUID object

    Raises:
        ValidationError: If UUID format is invalid
    """
    if isinstance(value, uuid.UUID):
        return value

    if not value:
        raise ValidationError("UUID cannot be empty")

    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError) as e:
        raise ValidationError(f"Invalid UUID format: {value}") from e


def validate_integer_range(
    value: int,
    min_value: int | None = None,
    max_value: int | None = None,
    field_name: str = "Value"
) -> int:
    """
    Validate integer is within specified range.

    Args:
        value: Integer value to validate
        min_value: Minimum allowed value (inclusive, optional)
        max_value: Maximum allowed value (inclusive, optional)
        field_name: Name of field for error messages

    Returns:
        int: Validated integer

    Raises:
        ValidationError: If value is out of range
    """
    if not isinstance(value, int):
        raise ValidationError(f"{field_name} must be an integer, got {type(value).__name__}")

    if min_value is not None and value < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}, got {value}")

    if max_value is not None and value > max_value:
        raise ValidationError(f"{field_name} must be at most {max_value}, got {value}")

    return value


def validate_float_range(
    value: float,
    min_value: float | None = None,
    max_value: float | None = None,
    field_name: str = "Value"
) -> float:
    """
    Validate float is within specified range.

    Args:
        value: Float value to validate
        min_value: Minimum allowed value (inclusive, optional)
        max_value: Maximum allowed value (inclusive, optional)
        field_name: Name of field for error messages

    Returns:
        float: Validated float

    Raises:
        ValidationError: If value is out of range
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{field_name} must be a number, got {type(value).__name__}")

    value = float(value)

    if min_value is not None and value < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}, got {value}")

    if max_value is not None and value > max_value:
        raise ValidationError(f"{field_name} must be at most {max_value}, got {value}")

    return value


def validate_string_length(
    value: str,
    min_length: int | None = None,
    max_length: int | None = None,
    field_name: str = "String"
) -> str:
    """
    Validate string length.

    Args:
        value: String to validate
        min_length: Minimum length (optional)
        max_length: Maximum length (optional)
        field_name: Name of field for error messages

    Returns:
        str: Validated string

    Raises:
        ValidationError: If string length is invalid
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string, got {type(value).__name__}")

    length = len(value)

    if min_length is not None and length < min_length:
        raise ValidationError(
            f"{field_name} must be at least {min_length} characters, got {length}"
        )

    if max_length is not None and length > max_length:
        raise ValidationError(
            f"{field_name} must be at most {max_length} characters, got {length}"
        )

    return value


def validate_enum_value(value: Any, allowed_values: list[Any], field_name: str = "Value") -> Any:
    """
    Validate value is in allowed set.

    Args:
        value: Value to validate
        allowed_values: List of allowed values
        field_name: Name of field for error messages

    Returns:
        Any: Validated value

    Raises:
        ValidationError: If value not in allowed set
    """
    if value not in allowed_values:
        raise ValidationError(
            f"{field_name} must be one of {allowed_values}, got '{value}'"
        )

    return value


def validate_military_id(military_id: str) -> str:
    """
    Validate military ID format (DoD ID Number).

    DoD ID Numbers (EDIPI) are 10-digit numbers.

    Args:
        military_id: Military ID to validate

    Returns:
        str: Validated military ID

    Raises:
        ValidationError: If military ID format is invalid
    """
    if not military_id:
        raise ValidationError("Military ID cannot be empty")

    # Remove spaces and hyphens
    clean_id = military_id.replace(' ', '').replace('-', '')

    # Must be exactly 10 digits
    if not re.match(r'^\d{10}$', clean_id):
        raise ValidationError(
            f"Invalid military ID format. Expected 10 digits, got: {military_id}"
        )

    return clean_id


def validate_non_empty_list(value: list[Any], field_name: str = "List") -> list[Any]:
    """
    Validate list is not empty.

    Args:
        value: List to validate
        field_name: Name of field for error messages

    Returns:
        list: Validated list

    Raises:
        ValidationError: If list is empty or not a list
    """
    if not isinstance(value, list):
        raise ValidationError(f"{field_name} must be a list, got {type(value).__name__}")

    if len(value) == 0:
        raise ValidationError(f"{field_name} cannot be empty")

    return value
