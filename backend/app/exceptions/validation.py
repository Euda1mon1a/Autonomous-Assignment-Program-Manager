"""Input validation and business rule exceptions.

These exceptions are raised during input validation, schema validation,
and business rule enforcement.
"""

from datetime import date, datetime
from typing import Any

from app.core.exceptions import ValidationError as BaseValidationError


class InputValidationError(BaseValidationError):
    """Raised when input data fails validation."""

    def __init__(
        self,
        message: str = "Invalid input data",
        field: str | None = None,
        value: Any = None,
        **context: Any,
    ):
        """Initialize input validation error.

        Args:
            message: User-friendly error message
            field: Field that failed validation
            value: Invalid value (sanitized)
            **context: Additional context
        """
        super().__init__(message)
        self.field = field
        self.value = value
        self.context = context


class DateValidationError(InputValidationError):
    """Raised when date validation fails."""

    def __init__(
        self,
        message: str = "Invalid date",
        field: str | None = None,
        value: date | datetime | str | None = None,
        min_date: date | datetime | None = None,
        max_date: date | datetime | None = None,
        **context: Any,
    ):
        """Initialize date validation error.

        Args:
            message: User-friendly error message
            field: Date field that failed validation
            value: Invalid date value
            min_date: Minimum allowed date
            max_date: Maximum allowed date
            **context: Additional context
        """
        super().__init__(
            message=message,
            field=field,
            value=value,
            **context,
        )
        self.min_date = min_date
        self.max_date = max_date


class DateRangeError(DateValidationError):
    """Raised when a date is outside the allowed range."""

    def __init__(
        self,
        message: str = "Date is outside the allowed range",
        field: str | None = None,
        value: date | datetime | str | None = None,
        min_date: date | datetime | None = None,
        max_date: date | datetime | None = None,
        **context: Any,
    ):
        """Initialize date range error.

        Args:
            message: User-friendly error message
            field: Date field
            value: Out-of-range date value
            min_date: Minimum allowed date
            max_date: Maximum allowed date
            **context: Additional context
        """
        super().__init__(
            message=message,
            field=field,
            value=value,
            min_date=min_date,
            max_date=max_date,
            **context,
        )


class FutureDateError(DateValidationError):
    """Raised when a past date is required but a future date was provided."""

    def __init__(
        self,
        message: str = "Date cannot be in the future",
        field: str | None = None,
        value: date | datetime | str | None = None,
        **context: Any,
    ):
        """Initialize future date error.

        Args:
            message: User-friendly error message
            field: Date field
            value: Future date value
            **context: Additional context
        """
        super().__init__(
            message=message,
            field=field,
            value=value,
            max_date=datetime.now().date(),
            **context,
        )


class PastDateError(DateValidationError):
    """Raised when a future date is required but a past date was provided."""

    def __init__(
        self,
        message: str = "Date cannot be in the past",
        field: str | None = None,
        value: date | datetime | str | None = None,
        **context: Any,
    ):
        """Initialize past date error.

        Args:
            message: User-friendly error message
            field: Date field
            value: Past date value
            **context: Additional context
        """
        super().__init__(
            message=message,
            field=field,
            value=value,
            min_date=datetime.now().date(),
            **context,
        )


class SchemaValidationError(InputValidationError):
    """Raised when data doesn't match required schema."""

    def __init__(
        self,
        message: str = "Data does not match required schema",
        schema: str | None = None,
        errors: list[dict[str, Any]] | None = None,
        **context: Any,
    ):
        """Initialize schema validation error.

        Args:
            message: User-friendly error message
            schema: Schema name or identifier
            errors: List of validation errors
            **context: Additional context
        """
        super().__init__(message, **context)
        self.schema = schema
        self.errors = errors or []


class RequiredFieldError(InputValidationError):
    """Raised when a required field is missing."""

    def __init__(
        self,
        message: str | None = None,
        field: str | None = None,
        **context: Any,
    ):
        """Initialize required field error.

        Args:
            message: User-friendly error message
            field: Missing field name
            **context: Additional context
        """
        if not message:
            message = (
                f"Field '{field}' is required" if field else "Required field is missing"
            )

        super().__init__(
            message=message,
            field=field,
            **context,
        )


class InvalidFormatError(InputValidationError):
    """Raised when a field value has an invalid format."""

    def __init__(
        self,
        message: str = "Invalid format",
        field: str | None = None,
        expected_format: str | None = None,
        **context: Any,
    ):
        """Initialize invalid format error.

        Args:
            message: User-friendly error message
            field: Field with invalid format
            expected_format: Expected format description
            **context: Additional context
        """
        super().__init__(
            message=message,
            field=field,
            **context,
        )
        self.expected_format = expected_format


class BusinessRuleViolationError(BaseValidationError):
    """Raised when a business rule is violated."""

    def __init__(
        self,
        message: str = "Business rule violated",
        rule_name: str | None = None,
        rule_description: str | None = None,
        **context: Any,
    ):
        """Initialize business rule violation error.

        Args:
            message: User-friendly error message
            rule_name: Name of violated rule
            rule_description: Description of the rule
            **context: Additional context
        """
        super().__init__(message)
        self.rule_name = rule_name
        self.rule_description = rule_description
        self.context = context


class InvalidStateTransitionError(BusinessRuleViolationError):
    """Raised when an invalid state transition is attempted."""

    def __init__(
        self,
        message: str = "Invalid state transition",
        current_state: str | None = None,
        requested_state: str | None = None,
        allowed_states: list[str] | None = None,
        **context: Any,
    ):
        """Initialize invalid state transition error.

        Args:
            message: User-friendly error message
            current_state: Current state
            requested_state: Requested new state
            allowed_states: List of allowed next states
            **context: Additional context
        """
        super().__init__(message, **context)
        self.current_state = current_state
        self.requested_state = requested_state
        self.allowed_states = allowed_states or []


class ValueRangeError(InputValidationError):
    """Raised when a value is outside the allowed range."""

    def __init__(
        self,
        message: str = "Value is outside the allowed range",
        field: str | None = None,
        value: Any = None,
        min_value: Any = None,
        max_value: Any = None,
        **context: Any,
    ):
        """Initialize value range error.

        Args:
            message: User-friendly error message
            field: Field name
            value: Invalid value
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            **context: Additional context
        """
        super().__init__(
            message=message,
            field=field,
            value=value,
            **context,
        )
        self.min_value = min_value
        self.max_value = max_value
