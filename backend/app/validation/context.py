"""
Validation context for managing validation state and errors.

Provides a context object that accumulates validation errors during request
processing and maintains state across validation rules.
"""

from contextvars import ContextVar
from typing import Any, Optional

from .messages import Locale, ValidationMessage

# Context variable for storing current validation context
_validation_context: ContextVar[Optional["ValidationContext"]] = ContextVar(
    "validation_context", default=None
)


class ValidationContext:
    """
    Context for accumulating validation errors and managing validation state.

    Tracks validation errors, provides utilities for adding errors,
    and maintains locale settings for error messages.
    """

    def __init__(self, locale: Locale = Locale.EN_US):
        """
        Initialize validation context.

        Args:
            locale: Language/locale for error messages
        """
        self.locale = locale
        self.errors: list[ValidationMessage] = []
        self._data: dict[str, Any] = {}

    def add_error(self, error: ValidationMessage) -> None:
        """
        Add a validation error to the context.

        Args:
            error: Validation error message to add
        """
        self.errors.append(error)

    def add_field_error(self, field: str, message: str) -> None:
        """
        Add a custom field validation error.

        Args:
            field: Field name that failed validation
            message: Error message
        """
        from .messages import custom_message

        self.add_error(custom_message(field, message, self.locale))

    def has_errors(self) -> bool:
        """
        Check if any validation errors have been recorded.

        Returns:
            bool: True if errors exist, False otherwise
        """
        return len(self.errors) > 0

    def get_errors(self) -> list[ValidationMessage]:
        """
        Get all validation errors.

        Returns:
            list[ValidationMessage]: List of all recorded errors
        """
        return self.errors

    def get_error_dict(self) -> dict[str, list[str]]:
        """
        Get errors organized by field name.

        Returns:
            dict: Errors grouped by field name
        """
        error_dict: dict[str, list[str]] = {}
        for error in self.errors:
            if error.field not in error_dict:
                error_dict[error.field] = []
            error_dict[error.field].append(str(error))
        return error_dict

    def get_errors_list(self) -> list[dict[str, Any]]:
        """
        Get errors as list of dictionaries for API responses.

        Returns:
            list[dict]: List of error dictionaries
        """
        return [error.to_dict() for error in self.errors]

    def clear_errors(self) -> None:
        """Clear all validation errors."""
        self.errors.clear()

    def set_data(self, key: str, value: Any) -> None:
        """
        Store arbitrary data in context for cross-field validation.

        Args:
            key: Data key
            value: Data value
        """
        self._data[key] = value

    def get_data(self, key: str, default: Any = None) -> Any:
        """
        Retrieve data from context.

        Args:
            key: Data key
            default: Default value if key doesn't exist

        Returns:
            Any: Stored value or default
        """
        return self._data.get(key, default)

    def has_data(self, key: str) -> bool:
        """
        Check if data key exists in context.

        Args:
            key: Data key to check

        Returns:
            bool: True if key exists, False otherwise
        """
        return key in self._data


def get_validation_context() -> ValidationContext | None:
    """
    Get the current validation context.

    Returns:
        ValidationContext or None: Current context if set, None otherwise
    """
    return _validation_context.get()


def set_validation_context(context: ValidationContext) -> None:
    """
    Set the current validation context.

    Args:
        context: Validation context to set as current
    """
    _validation_context.set(context)


def clear_validation_context() -> None:
    """Clear the current validation context."""
    _validation_context.set(None)


def create_validation_context(locale: Locale = Locale.EN_US) -> ValidationContext:
    """
    Create and set a new validation context.

    Args:
        locale: Language/locale for error messages

    Returns:
        ValidationContext: Newly created context
    """
    context = ValidationContext(locale)
    set_validation_context(context)
    return context


class validation_scope:
    """
    Context manager for scoped validation.

    Creates a validation context for the scope and automatically
    clears it when exiting.

    Example:
        >>> with validation_scope() as ctx:
        ...     ctx.add_field_error("name", "Name is required")
        ...     if ctx.has_errors():
        ...         raise ValueError("Validation failed")
    """

    def __init__(self, locale: Locale = Locale.EN_US):
        """
        Initialize validation scope.

        Args:
            locale: Language/locale for error messages
        """
        self.locale = locale
        self.context: ValidationContext | None = None

    def __enter__(self) -> ValidationContext:
        """
        Enter validation scope.

        Returns:
            ValidationContext: New validation context
        """
        self.context = create_validation_context(self.locale)
        return self.context

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit validation scope and clear context."""
        clear_validation_context()
        return False
