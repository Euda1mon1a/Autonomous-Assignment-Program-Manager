"""
Custom span utilities and decorators for tracing.

Provides:
- Span creation helpers
- Decorators for tracing functions
- Span attribute management
- Custom span processors
"""

from functools import wraps
from typing import Any, Callable

from loguru import logger

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False


def trace_function(
    name: str | None = None,
    attributes: dict[str, Any] | None = None,
):
    """
    Decorator to trace function execution.

    Args:
        name: Span name (defaults to function name)
        attributes: Additional span attributes

    Example:
        @trace_function("schedule_generation")
        def generate_schedule():
            # ... implementation
            pass
    """

    def decorator(func: Callable) -> Callable:
        if not OTEL_AVAILABLE:
            return func

        span_name = name or func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)

            with tracer.start_as_current_span(span_name) as span:
                # Add attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                # Add function info
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)

            with tracer.start_as_current_span(span_name) as span:
                # Add attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                # Add function info
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper

    return decorator


def create_span(name: str, attributes: dict[str, Any] | None = None):
    """
    Create a new span context manager.

    Args:
        name: Span name
        attributes: Span attributes

    Example:
        with create_span("database_query", {"table": "users"}):
            result = db.query(User).all()
    """
    if not OTEL_AVAILABLE:
        from contextlib import nullcontext

        return nullcontext()

    tracer = trace.get_tracer(__name__)
    span = tracer.start_span(name)

    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)

    return span


def add_span_attributes(**attributes):
    """
    Add attributes to current span.

    Args:
        **attributes: Attributes to add

    Example:
        add_span_attributes(user_id="123", operation="schedule_generation")
    """
    if not OTEL_AVAILABLE:
        return

    span = trace.get_current_span()
    if span:
        for key, value in attributes.items():
            span.set_attribute(key, value)


def add_span_event(name: str, attributes: dict[str, Any] | None = None):
    """
    Add event to current span.

    Args:
        name: Event name
        attributes: Event attributes

    Example:
        add_span_event("acgme_violation", {"rule": "80_hour", "person_id": "123"})
    """
    if not OTEL_AVAILABLE:
        return

    span = trace.get_current_span()
    if span:
        span.add_event(name, attributes=attributes or {})


def record_exception(exception: Exception):
    """
    Record exception in current span.

    Args:
        exception: Exception to record
    """
    if not OTEL_AVAILABLE:
        return

    span = trace.get_current_span()
    if span:
        span.record_exception(exception)
        span.set_status(Status(StatusCode.ERROR, str(exception)))
