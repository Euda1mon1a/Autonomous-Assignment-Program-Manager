"""
Request validation decorators for FastAPI routes.

Provides decorators for validating query parameters, request bodies,
and combined request data with support for custom rules and cross-field validation.
"""
import functools
import inspect
from typing import Any, Callable, Optional

from fastapi import HTTPException, Request
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from .context import ValidationContext, create_validation_context, clear_validation_context
from .messages import Locale
from .rules import ValidationRule


def validate_request(
    query_rules: Optional[dict[str, list[ValidationRule]]] = None,
    body_rules: Optional[dict[str, list[ValidationRule]]] = None,
    cross_field_validator: Optional[Callable[[dict[str, Any], ValidationContext], None]] = None,
    locale: Locale = Locale.EN_US,
) -> Callable:
    """
    Decorator for comprehensive request validation.

    Validates both query parameters and request body, with support for
    cross-field validation rules that span multiple fields.

    Args:
        query_rules: Validation rules for query parameters
        body_rules: Validation rules for request body fields
        cross_field_validator: Function for cross-field validation
        locale: Language/locale for error messages

    Returns:
        Callable: Decorated function

    Example:
        >>> @validate_request(
        ...     query_rules={
        ...         "page": [required, numeric_range(min_value=1)],
        ...         "limit": [numeric_range(min_value=1, max_value=100)]
        ...     },
        ...     body_rules={
        ...         "name": [required, string_length(min_length=1, max_length=100)]
        ...     }
        ... )
        ... async def create_item(request: Request, page: int, limit: int):
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Create validation context
            ctx = create_validation_context(locale)

            try:
                # Extract request object
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                if request is None and "request" in kwargs:
                    request = kwargs["request"]

                # Validate query parameters
                if query_rules and request:
                    query_params = dict(request.query_params)
                    _validate_fields(query_params, query_rules, ctx)

                # Validate request body
                if body_rules and request:
                    try:
                        body = await request.json()
                        _validate_fields(body, body_rules, ctx)

                        # Store body for cross-field validation
                        ctx.set_data("request_data", {**query_params, **body})
                    except Exception:
                        # If body can't be parsed, let FastAPI handle it
                        pass

                # Cross-field validation
                if cross_field_validator:
                    request_data = ctx.get_data("request_data", {})
                    cross_field_validator(request_data, ctx)

                # Check for validation errors
                if ctx.has_errors():
                    raise HTTPException(
                        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                        detail={
                            "message": "Validation failed",
                            "errors": ctx.get_errors_list(),
                        }
                    )

                # Call original function
                if inspect.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)

            finally:
                clear_validation_context()

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Create validation context
            ctx = create_validation_context(locale)

            try:
                # Extract request object
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                if request is None and "request" in kwargs:
                    request = kwargs["request"]

                # Validate query parameters
                if query_rules and request:
                    query_params = dict(request.query_params)
                    _validate_fields(query_params, query_rules, ctx)

                # Note: Sync functions can't validate body easily
                # For body validation, use async functions

                # Cross-field validation
                if cross_field_validator:
                    request_data = ctx.get_data("request_data", query_params if request else {})
                    cross_field_validator(request_data, ctx)

                # Check for validation errors
                if ctx.has_errors():
                    raise HTTPException(
                        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                        detail={
                            "message": "Validation failed",
                            "errors": ctx.get_errors_list(),
                        }
                    )

                # Call original function
                return func(*args, **kwargs)

            finally:
                clear_validation_context()

        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def validate_query(
    rules: dict[str, list[ValidationRule]],
    locale: Locale = Locale.EN_US,
) -> Callable:
    """
    Decorator for validating query parameters.

    Args:
        rules: Validation rules for each query parameter
        locale: Language/locale for error messages

    Returns:
        Callable: Decorated function

    Example:
        >>> @validate_query({
        ...     "page": [required, numeric_range(min_value=1)],
        ...     "type": [enum_values(["resident", "faculty"])]
        ... })
        ... async def list_people(page: int, type: str):
        ...     pass
    """
    return validate_request(query_rules=rules, locale=locale)


def validate_body(
    rules: dict[str, list[ValidationRule]],
    locale: Locale = Locale.EN_US,
) -> Callable:
    """
    Decorator for validating request body.

    Args:
        rules: Validation rules for each body field
        locale: Language/locale for error messages

    Returns:
        Callable: Decorated function

    Example:
        >>> @validate_body({
        ...     "name": [required, string_length(min_length=1, max_length=100)],
        ...     "email": [required, email_format()]
        ... })
        ... async def create_user(user_data: dict):
        ...     pass
    """
    return validate_request(body_rules=rules, locale=locale)


def validate_cross_field(
    validator: Callable[[dict[str, Any], ValidationContext], None],
    locale: Locale = Locale.EN_US,
) -> Callable:
    """
    Decorator for cross-field validation.

    Useful for validation that depends on multiple fields.

    Args:
        validator: Function that performs cross-field validation
        locale: Language/locale for error messages

    Returns:
        Callable: Decorated function

    Example:
        >>> def validate_dates(data: dict, ctx: ValidationContext):
        ...     if data.get("start_date") > data.get("end_date"):
        ...         ctx.add_field_error("end_date", "Must be after start date")
        ...
        >>> @validate_cross_field(validate_dates)
        ... async def create_schedule(schedule_data: dict):
        ...     pass
    """
    return validate_request(cross_field_validator=validator, locale=locale)


def _validate_fields(
    data: dict[str, Any],
    rules: dict[str, list[ValidationRule]],
    ctx: ValidationContext
) -> None:
    """
    Validate fields against rules.

    Args:
        data: Data to validate
        rules: Validation rules for each field
        ctx: Validation context for error accumulation
    """
    # Store data in context for conditional rules
    ctx.set_data("request_data", data)

    # Apply rules to each field
    for field, field_rules in rules.items():
        value = data.get(field)

        # Apply each rule
        for rule in field_rules:
            rule(field, value, ctx)


# Convenience decorators for common validation patterns


def validate_pagination(
    default_limit: int = 20,
    max_limit: int = 100,
    locale: Locale = Locale.EN_US,
) -> Callable:
    """
    Decorator for pagination parameter validation.

    Args:
        default_limit: Default limit value
        max_limit: Maximum allowed limit
        locale: Language/locale for error messages

    Returns:
        Callable: Decorated function

    Example:
        >>> @validate_pagination(max_limit=50)
        ... async def list_items(page: int = 1, limit: int = 20):
        ...     pass
    """
    from .rules import numeric_range

    return validate_query(
        rules={
            "page": [numeric_range(min_value=1)],
            "limit": [numeric_range(min_value=1, max_value=max_limit)],
        },
        locale=locale
    )


def validate_uuid_param(
    param_name: str = "id",
    locale: Locale = Locale.EN_US,
) -> Callable:
    """
    Decorator for UUID parameter validation.

    Args:
        param_name: Name of the UUID parameter
        locale: Language/locale for error messages

    Returns:
        Callable: Decorated function

    Example:
        >>> @validate_uuid_param("person_id")
        ... async def get_person(person_id: str):
        ...     pass
    """
    from .rules import uuid_format, required

    return validate_query(
        rules={
            param_name: [required, uuid_format()],
        },
        locale=locale
    )


def validate_date_range_params(
    start_param: str = "start_date",
    end_param: str = "end_date",
    locale: Locale = Locale.EN_US,
) -> Callable:
    """
    Decorator for date range parameter validation.

    Validates that start_date is before end_date.

    Args:
        start_param: Name of start date parameter
        end_param: Name of end date parameter
        locale: Language/locale for error messages

    Returns:
        Callable: Decorated function

    Example:
        >>> @validate_date_range_params()
        ... async def get_schedule(start_date: date, end_date: date):
        ...     pass
    """
    from datetime import datetime

    def cross_validator(data: dict[str, Any], ctx: ValidationContext) -> None:
        start = data.get(start_param)
        end = data.get(end_param)

        if start and end:
            # Convert to dates if strings
            if isinstance(start, str):
                try:
                    start = datetime.fromisoformat(start).date()
                except ValueError:
                    return  # Let other validators handle format errors

            if isinstance(end, str):
                try:
                    end = datetime.fromisoformat(end).date()
                except ValueError:
                    return  # Let other validators handle format errors

            if start > end:
                ctx.add_field_error(
                    end_param,
                    f"{end_param} must be after {start_param}"
                )

    return validate_request(cross_field_validator=cross_validator, locale=locale)


def validate_conditional_field(
    field: str,
    condition_field: str,
    condition_value: Any,
    rules: list[ValidationRule],
    locale: Locale = Locale.EN_US,
) -> Callable:
    """
    Decorator for conditional field validation.

    Field is only validated if condition_field equals condition_value.

    Args:
        field: Field to validate conditionally
        condition_field: Field that determines if validation applies
        condition_value: Value that triggers validation
        rules: Validation rules to apply
        locale: Language/locale for error messages

    Returns:
        Callable: Decorated function

    Example:
        >>> @validate_conditional_field(
        ...     field="pgy_level",
        ...     condition_field="type",
        ...     condition_value="resident",
        ...     rules=[required, pgy_level_rule()]
        ... )
        ... async def create_person(person_data: dict):
        ...     pass
    """
    def cross_validator(data: dict[str, Any], ctx: ValidationContext) -> None:
        if data.get(condition_field) == condition_value:
            value = data.get(field)
            for rule in rules:
                rule(field, value, ctx)

    return validate_request(cross_field_validator=cross_validator, locale=locale)
