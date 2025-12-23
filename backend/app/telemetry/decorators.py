"""
OpenTelemetry tracing decorators.

Provides convenient decorators for adding tracing to functions and methods.
"""

import functools
import inspect
import logging
from collections.abc import Callable
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode

logger = logging.getLogger(__name__)


def traced(
    name: str | None = None,
    tracer_name: str | None = None,
    attributes: dict[str, Any] | None = None,
    capture_args: bool = False,
    capture_result: bool = False,
    span_kind: trace.SpanKind = trace.SpanKind.INTERNAL,
):
    """
    Decorator for tracing function execution.

    Creates a span for the decorated function with optional argument
    and result capture.

    Args:
        name: Span name (defaults to function name)
        tracer_name: Tracer name (defaults to module name)
        attributes: Static attributes to add to span
        capture_args: Whether to capture function arguments
        capture_result: Whether to capture return value
        span_kind: Span kind (INTERNAL, CLIENT, SERVER, etc.)

    Example:
        @traced(name="generate_schedule", attributes={"operation": "schedule_gen"})
        async def generate_schedule(year: int) -> Schedule:
            # ... implementation
            return schedule

        @traced(capture_args=True, capture_result=True)
        def calculate_utilization(assignments: list) -> float:
            return len(assignments) / 100
    """

    def decorator(func: Callable) -> Callable:
        # Get tracer for this function's module
        nonlocal tracer_name
        if tracer_name is None:
            tracer_name = func.__module__

        tracer = trace.get_tracer(tracer_name)

        # Determine span name
        span_name = name or f"{func.__module__}.{func.__name__}"

        # Handle both sync and async functions
        is_coroutine = inspect.iscoroutinefunction(func)

        if is_coroutine:

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                with tracer.start_as_current_span(
                    span_name,
                    kind=span_kind,
                ) as span:
                    # Set static attributes
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, value)

                    # Capture arguments if enabled
                    if capture_args:
                        _capture_function_args(span, func, args, kwargs)

                    try:
                        result = await func(*args, **kwargs)

                        # Capture result if enabled
                        if capture_result:
                            _capture_result(span, result)

                        span.set_status(Status(StatusCode.OK))
                        return result

                    except Exception as exc:
                        # Record exception
                        span.record_exception(exc)
                        span.set_status(Status(StatusCode.ERROR, str(exc)))
                        raise

            return async_wrapper

        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                with tracer.start_as_current_span(
                    span_name,
                    kind=span_kind,
                ) as span:
                    # Set static attributes
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, value)

                    # Capture arguments if enabled
                    if capture_args:
                        _capture_function_args(span, func, args, kwargs)

                    try:
                        result = func(*args, **kwargs)

                        # Capture result if enabled
                        if capture_result:
                            _capture_result(span, result)

                        span.set_status(Status(StatusCode.OK))
                        return result

                    except Exception as exc:
                        # Record exception
                        span.record_exception(exc)
                        span.set_status(Status(StatusCode.ERROR, str(exc)))
                        raise

            return sync_wrapper

    return decorator


def trace_class(
    tracer_name: str | None = None,
    attributes: dict[str, Any] | None = None,
):
    """
    Class decorator for tracing all methods.

    Applies tracing to all public methods of a class.

    Args:
        tracer_name: Tracer name (defaults to module name)
        attributes: Static attributes to add to all spans

    Example:
        @trace_class(attributes={"service": "schedule_generator"})
        class ScheduleGenerator:
            def generate(self, year: int):
                # Automatically traced
                pass

            def validate(self, schedule: Schedule):
                # Automatically traced
                pass
    """

    def decorator(cls):
        # Get all public methods
        for attr_name in dir(cls):
            # Skip private/magic methods
            if attr_name.startswith("_"):
                continue

            attr = getattr(cls, attr_name)

            # Only trace callable methods
            if callable(attr):
                # Apply traced decorator
                traced_method = traced(
                    name=f"{cls.__name__}.{attr_name}",
                    tracer_name=tracer_name or cls.__module__,
                    attributes=attributes,
                )(attr)

                setattr(cls, attr_name, traced_method)

        return cls

    return decorator


def trace_async_generator(
    name: str | None = None,
    tracer_name: str | None = None,
    attributes: dict[str, Any] | None = None,
):
    """
    Decorator for tracing async generators.

    Creates a span that remains active for the entire iteration.

    Args:
        name: Span name (defaults to function name)
        tracer_name: Tracer name (defaults to module name)
        attributes: Static attributes to add to span

    Example:
        @trace_async_generator(name="stream_assignments")
        async def stream_assignments(year: int):
            for assignment in assignments:
                yield assignment
    """

    def decorator(func: Callable):
        nonlocal tracer_name
        if tracer_name is None:
            tracer_name = func.__module__

        tracer = trace.get_tracer(tracer_name)
        span_name = name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                # Set static attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                try:
                    item_count = 0
                    async for item in func(*args, **kwargs):
                        item_count += 1
                        yield item

                    # Record total items yielded
                    span.set_attribute("generator.items_yielded", item_count)
                    span.set_status(Status(StatusCode.OK))

                except Exception as exc:
                    span.record_exception(exc)
                    span.set_status(Status(StatusCode.ERROR, str(exc)))
                    raise

        return wrapper

    return decorator


# Helper functions


def _capture_function_args(
    span: Span,
    func: Callable,
    args: tuple,
    kwargs: dict,
):
    """
    Capture function arguments as span attributes.

    Args:
        span: Current span
        func: Function being traced
        args: Positional arguments
        kwargs: Keyword arguments
    """
    # Get function signature
    sig = inspect.signature(func)
    bound_args = sig.bind_partial(*args, **kwargs)

    # Set arguments as attributes (with sanitization)
    for param_name, param_value in bound_args.arguments.items():
        # Skip 'self' and 'cls' parameters
        if param_name in ("self", "cls"):
            continue

        # Sanitize sensitive parameters
        if param_name.lower() in ("password", "secret", "token", "api_key"):
            param_value = "***REDACTED***"
        else:
            # Convert to string and limit length
            param_value = str(param_value)[:200]

        span.set_attribute(f"function.arg.{param_name}", param_value)


def _capture_result(span: Span, result: Any):
    """
    Capture function result as span attribute.

    Args:
        span: Current span
        result: Function return value
    """
    # Don't capture None results
    if result is None:
        return

    # Handle different result types
    if isinstance(result, (str, int, float, bool)):
        span.set_attribute("function.result", str(result)[:200])
    elif isinstance(result, (list, tuple)):
        span.set_attribute("function.result.type", type(result).__name__)
        span.set_attribute("function.result.length", len(result))
    elif isinstance(result, dict):
        span.set_attribute("function.result.type", "dict")
        span.set_attribute("function.result.keys", len(result))
    else:
        # For other types, just record the type
        span.set_attribute("function.result.type", type(result).__name__)


# Specialized decorators for common use cases


def trace_service_method(
    name: str | None = None,
    capture_args: bool = True,
):
    """
    Decorator for service layer methods.

    Convenience wrapper for @traced with service-appropriate defaults.

    Args:
        name: Span name (defaults to method name)
        capture_args: Whether to capture method arguments

    Example:
        class ScheduleService:
            @trace_service_method()
            async def create_schedule(self, year: int):
                # ... implementation
                pass
    """
    return traced(
        name=name,
        attributes={"layer": "service"},
        capture_args=capture_args,
        span_kind=trace.SpanKind.INTERNAL,
    )


def trace_repository_method(
    name: str | None = None,
    capture_args: bool = False,
):
    """
    Decorator for repository/data access methods.

    Convenience wrapper for @traced with repository-appropriate defaults.

    Args:
        name: Span name (defaults to method name)
        capture_args: Whether to capture method arguments

    Example:
        class ScheduleRepository:
            @trace_repository_method()
            async def get_by_year(self, year: int):
                # ... implementation
                pass
    """
    return traced(
        name=name,
        attributes={"layer": "repository"},
        capture_args=capture_args,
        span_kind=trace.SpanKind.INTERNAL,
    )


def trace_controller_method(
    name: str | None = None,
):
    """
    Decorator for controller methods.

    Convenience wrapper for @traced with controller-appropriate defaults.

    Args:
        name: Span name (defaults to method name)

    Example:
        class ScheduleController:
            @trace_controller_method()
            async def create_schedule(self, request: ScheduleCreate):
                # ... implementation
                pass
    """
    return traced(
        name=name,
        attributes={"layer": "controller"},
        capture_args=False,  # Don't capture args (may contain sensitive data)
        span_kind=trace.SpanKind.INTERNAL,
    )


def trace_background_task(
    name: str | None = None,
    capture_args: bool = True,
):
    """
    Decorator for Celery/background tasks.

    Convenience wrapper for @traced with background task defaults.

    Args:
        name: Span name (defaults to task name)
        capture_args: Whether to capture task arguments

    Example:
        @trace_background_task()
        @celery_app.task
        def generate_schedule_async(year: int):
            # ... implementation
            pass
    """
    return traced(
        name=name,
        attributes={"task.type": "background"},
        capture_args=capture_args,
        span_kind=trace.SpanKind.INTERNAL,
    )
