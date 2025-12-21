"""
Validation rules for request validation.

Provides reusable validation rules that can be composed and applied
to request data. Rules can be combined and customized for specific use cases.
"""
import re
from datetime import date, datetime
from typing import Any, Callable, Optional
from uuid import UUID

from .context import ValidationContext
from .messages import (
    Locale,
    ValidationMessageType,
    ValidationMessage,
    invalid_enum,
    invalid_type,
    out_of_range,
    required_field,
)


# Type alias for validation rule functions
ValidationRule = Callable[[str, Any, ValidationContext], bool]


def required(field: str, value: Any, ctx: ValidationContext) -> bool:
    """
    Validate that a field is present and not None.

    Args:
        field: Field name
        value: Field value
        ctx: Validation context

    Returns:
        bool: True if valid, False otherwise
    """
    if value is None or (isinstance(value, str) and value.strip() == ""):
        ctx.add_error(required_field(field, ctx.locale))
        return False
    return True


def string_length(
    min_length: Optional[int] = None,
    max_length: Optional[int] = None
) -> ValidationRule:
    """
    Create a validation rule for string length.

    Args:
        min_length: Minimum allowed length
        max_length: Maximum allowed length

    Returns:
        ValidationRule: Validation rule function
    """
    def validate(field: str, value: Any, ctx: ValidationContext) -> bool:
        if value is None:
            return True  # Use 'required' rule for None checks

        if not isinstance(value, str):
            ctx.add_error(invalid_type(field, "string", ctx.locale))
            return False

        valid = True
        if min_length is not None and len(value) < min_length:
            ctx.add_error(ValidationMessage(
                ValidationMessageType.TOO_SHORT,
                field,
                ctx.locale,
                min_length=min_length
            ))
            valid = False

        if max_length is not None and len(value) > max_length:
            ctx.add_error(ValidationMessage(
                ValidationMessageType.TOO_LONG,
                field,
                ctx.locale,
                max_length=max_length
            ))
            valid = False

        return valid

    return validate


def numeric_range(
    min_value: Optional[float] = None,
    max_value: Optional[float] = None
) -> ValidationRule:
    """
    Create a validation rule for numeric ranges.

    Args:
        min_value: Minimum allowed value
        max_value: Maximum allowed value

    Returns:
        ValidationRule: Validation rule function
    """
    def validate(field: str, value: Any, ctx: ValidationContext) -> bool:
        if value is None:
            return True  # Use 'required' rule for None checks

        if not isinstance(value, (int, float)):
            ctx.add_error(invalid_type(field, "number", ctx.locale))
            return False

        if min_value is not None and value < min_value:
            ctx.add_error(out_of_range(field, min_value, max_value, ctx.locale))
            return False

        if max_value is not None and value > max_value:
            ctx.add_error(out_of_range(field, min_value, max_value, ctx.locale))
            return False

        return True

    return validate


def enum_values(allowed_values: list[Any]) -> ValidationRule:
    """
    Create a validation rule for enum/choice fields.

    Args:
        allowed_values: List of allowed values

    Returns:
        ValidationRule: Validation rule function
    """
    def validate(field: str, value: Any, ctx: ValidationContext) -> bool:
        if value is None:
            return True  # Use 'required' rule for None checks

        if value not in allowed_values:
            ctx.add_error(invalid_enum(
                field,
                [str(v) for v in allowed_values],
                ctx.locale
            ))
            return False

        return True

    return validate


def regex_pattern(pattern: str, error_message: Optional[str] = None) -> ValidationRule:
    """
    Create a validation rule for regex pattern matching.

    Args:
        pattern: Regular expression pattern
        error_message: Custom error message (optional)

    Returns:
        ValidationRule: Validation rule function
    """
    compiled_pattern = re.compile(pattern)

    def validate(field: str, value: Any, ctx: ValidationContext) -> bool:
        if value is None:
            return True  # Use 'required' rule for None checks

        if not isinstance(value, str):
            ctx.add_error(invalid_type(field, "string", ctx.locale))
            return False

        if not compiled_pattern.match(value):
            if error_message:
                ctx.add_field_error(field, error_message)
            else:
                ctx.add_error(ValidationMessage(
                    ValidationMessageType.PATTERN_MISMATCH,
                    field,
                    ctx.locale
                ))
            return False

        return True

    return validate


def email_format() -> ValidationRule:
    """
    Create a validation rule for email format.

    Returns:
        ValidationRule: Validation rule function
    """
    # Simple email regex (basic validation)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return regex_pattern(email_pattern, "Invalid email format")


def uuid_format() -> ValidationRule:
    """
    Create a validation rule for UUID format.

    Returns:
        ValidationRule: Validation rule function
    """
    def validate(field: str, value: Any, ctx: ValidationContext) -> bool:
        if value is None:
            return True  # Use 'required' rule for None checks

        # Try to parse as UUID
        try:
            if isinstance(value, str):
                UUID(value)
            elif not isinstance(value, UUID):
                raise ValueError("Not a UUID")
            return True
        except (ValueError, AttributeError):
            ctx.add_field_error(field, "Invalid UUID format")
            return False

    return validate


def date_range(
    min_date: Optional[date] = None,
    max_date: Optional[date] = None
) -> ValidationRule:
    """
    Create a validation rule for date ranges.

    Args:
        min_date: Minimum allowed date
        max_date: Maximum allowed date

    Returns:
        ValidationRule: Validation rule function
    """
    def validate(field: str, value: Any, ctx: ValidationContext) -> bool:
        if value is None:
            return True  # Use 'required' rule for None checks

        # Convert to date if datetime
        if isinstance(value, datetime):
            value = value.date()
        elif isinstance(value, str):
            try:
                value = datetime.fromisoformat(value).date()
            except ValueError:
                ctx.add_field_error(field, "Invalid date format")
                return False
        elif not isinstance(value, date):
            ctx.add_error(invalid_type(field, "date", ctx.locale))
            return False

        if min_date is not None and value < min_date:
            ctx.add_error(out_of_range(
                field,
                min_date.isoformat(),
                max_date.isoformat() if max_date else "present",
                ctx.locale
            ))
            return False

        if max_date is not None and value > max_date:
            ctx.add_error(out_of_range(
                field,
                min_date.isoformat() if min_date else "past",
                max_date.isoformat(),
                ctx.locale
            ))
            return False

        return True

    return validate


def list_items(
    item_rule: ValidationRule,
    min_items: Optional[int] = None,
    max_items: Optional[int] = None
) -> ValidationRule:
    """
    Create a validation rule for list items.

    Args:
        item_rule: Rule to apply to each item
        min_items: Minimum number of items
        max_items: Maximum number of items

    Returns:
        ValidationRule: Validation rule function
    """
    def validate(field: str, value: Any, ctx: ValidationContext) -> bool:
        if value is None:
            return True  # Use 'required' rule for None checks

        if not isinstance(value, list):
            ctx.add_error(invalid_type(field, "list", ctx.locale))
            return False

        # Check list size
        if min_items is not None and len(value) < min_items:
            ctx.add_field_error(
                field,
                f"Must contain at least {min_items} items"
            )
            return False

        if max_items is not None and len(value) > max_items:
            ctx.add_field_error(
                field,
                f"Must not contain more than {max_items} items"
            )
            return False

        # Validate each item
        valid = True
        for i, item in enumerate(value):
            if not item_rule(f"{field}[{i}]", item, ctx):
                valid = False

        return valid

    return validate


def conditional(
    condition: Callable[[dict[str, Any]], bool],
    rule: ValidationRule
) -> ValidationRule:
    """
    Create a conditional validation rule.

    The rule is only applied if the condition returns True.

    Args:
        condition: Function that determines if rule should apply
        rule: Rule to apply when condition is True

    Returns:
        ValidationRule: Validation rule function
    """
    def validate(field: str, value: Any, ctx: ValidationContext) -> bool:
        # Get request data from context
        request_data = ctx.get_data("request_data", {})

        if condition(request_data):
            return rule(field, value, ctx)
        return True

    return validate


def custom(
    validator: Callable[[Any], bool],
    error_message: str
) -> ValidationRule:
    """
    Create a custom validation rule.

    Args:
        validator: Function that returns True if valid, False otherwise
        error_message: Error message if validation fails

    Returns:
        ValidationRule: Validation rule function
    """
    def validate(field: str, value: Any, ctx: ValidationContext) -> bool:
        if value is None:
            return True  # Use 'required' rule for None checks

        if not validator(value):
            ctx.add_field_error(field, error_message)
            return False

        return True

    return validate


def all_of(*rules: ValidationRule) -> ValidationRule:
    """
    Combine multiple rules - all must pass.

    Args:
        *rules: Validation rules to combine

    Returns:
        ValidationRule: Combined validation rule
    """
    def validate(field: str, value: Any, ctx: ValidationContext) -> bool:
        return all(rule(field, value, ctx) for rule in rules)

    return validate


def any_of(*rules: ValidationRule) -> ValidationRule:
    """
    Combine multiple rules - at least one must pass.

    Args:
        *rules: Validation rules to combine

    Returns:
        ValidationRule: Combined validation rule
    """
    def validate(field: str, value: Any, ctx: ValidationContext) -> bool:
        # Try each rule with a temporary context
        for rule in rules:
            temp_ctx = ValidationContext(ctx.locale)
            if rule(field, value, temp_ctx):
                return True

        # If none passed, add error
        ctx.add_field_error(field, "Value does not meet any of the requirements")
        return False

    return validate


# Predefined common rules
def pgy_level_rule() -> ValidationRule:
    """PGY level validation (1-3)."""
    return all_of(
        numeric_range(min_value=1, max_value=3),
        custom(lambda v: isinstance(v, int), "PGY level must be an integer")
    )


def person_type_rule() -> ValidationRule:
    """Person type validation (resident or faculty)."""
    return enum_values(["resident", "faculty"])


def faculty_role_rule() -> ValidationRule:
    """Faculty role validation."""
    return enum_values(["pd", "apd", "oic", "dept_chief", "sports_med", "core"])


def phone_number_rule() -> ValidationRule:
    """Phone number validation (US format)."""
    # Matches: (123) 456-7890, 123-456-7890, 1234567890
    pattern = r'^\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$'
    return regex_pattern(pattern, "Invalid phone number format")


def positive_number_rule() -> ValidationRule:
    """Positive number validation."""
    return numeric_range(min_value=0)


def percentage_rule() -> ValidationRule:
    """Percentage validation (0-100)."""
    return numeric_range(min_value=0, max_value=100)
