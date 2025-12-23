"""
Request validation package for FastAPI routes.

Provides comprehensive validation capabilities including:
- Request validation decorators (@validate_request, @validate_query, @validate_body)
- Reusable validation rules
- Cross-field validation
- Conditional validation
- Localized error messages
- Validation context management

Example usage:
    >>> from app.validation import (
    ...     validate_request,
    ...     validate_query,
    ...     validate_body,
    ...     required,
    ...     string_length,
    ...     numeric_range,
    ...     email_format
    ... )
    ...
    >>> @validate_query({
    ...     "page": [required, numeric_range(min_value=1)],
    ...     "limit": [numeric_range(min_value=1, max_value=100)]
    ... })
    ... async def list_items(page: int, limit: int):
    ...     pass
    ...
    >>> @validate_body({
    ...     "name": [required, string_length(min_length=1, max_length=100)],
    ...     "email": [required, email_format()]
    ... })
    ... async def create_user(user_data: dict):
    ...     pass
"""

__version__ = "1.0.0"

# Decorators
# Context
from .context import (
    ValidationContext,
    clear_validation_context,
    create_validation_context,
    get_validation_context,
    set_validation_context,
    validation_scope,
)
from .decorators import (
    validate_body,
    validate_conditional_field,
    validate_cross_field,
    validate_date_range_params,
    validate_pagination,
    validate_query,
    validate_request,
    validate_uuid_param,
)

# Messages
from .messages import (
    Locale,
    ValidationMessage,
    ValidationMessageType,
    custom_message,
    format_field_name,
    get_error_message,
    invalid_enum,
    invalid_type,
    out_of_range,
    required_field,
)

# Validation rules
from .rules import (
    ValidationRule,
    all_of,
    any_of,
    conditional,
    custom,
    date_range,
    email_format,
    enum_values,
    faculty_role_rule,
    list_items,
    numeric_range,
    percentage_rule,
    person_type_rule,
    # Predefined rules
    pgy_level_rule,
    phone_number_rule,
    positive_number_rule,
    regex_pattern,
    required,
    string_length,
    uuid_format,
)

__all__ = [
    # Decorators
    "validate_request",
    "validate_query",
    "validate_body",
    "validate_cross_field",
    "validate_pagination",
    "validate_uuid_param",
    "validate_date_range_params",
    "validate_conditional_field",
    # Validation rules
    "ValidationRule",
    "required",
    "string_length",
    "numeric_range",
    "enum_values",
    "regex_pattern",
    "email_format",
    "uuid_format",
    "date_range",
    "list_items",
    "conditional",
    "custom",
    "all_of",
    "any_of",
    # Predefined rules
    "pgy_level_rule",
    "person_type_rule",
    "faculty_role_rule",
    "phone_number_rule",
    "positive_number_rule",
    "percentage_rule",
    # Context
    "ValidationContext",
    "get_validation_context",
    "set_validation_context",
    "clear_validation_context",
    "create_validation_context",
    "validation_scope",
    # Messages
    "Locale",
    "ValidationMessageType",
    "ValidationMessage",
    "get_error_message",
    "format_field_name",
    "required_field",
    "invalid_type",
    "out_of_range",
    "invalid_enum",
    "custom_message",
]
