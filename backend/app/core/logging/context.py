"""
Logging context management for request correlation and tracing.

Provides:
- Request correlation ID tracking
- User context injection
- Session context tracking
- Distributed tracing context
- Custom context variables
"""

import contextvars
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from loguru import logger

# Context variables for request tracking
request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)
user_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "user_id", default=None
)
session_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "session_id", default=None
)
trace_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "trace_id", default=None
)
span_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "span_id", default=None
)
custom_ctx: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar("custom")


def _get_custom_ctx_default() -> dict[str, Any]:
    """Get custom context with default empty dict if not set."""
    try:
        return custom_ctx.get()
    except LookupError:
        return {}


@dataclass
class LogContext:
    """
    Comprehensive logging context.

    Captures all relevant context information for a request/operation.
    """

    request_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    endpoint: str | None = None
    method: str | None = None
    custom_fields: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "endpoint": self.endpoint,
            "method": self.method,
            **self.custom_fields,
        }

    def bind_to_logger(self) -> dict[str, Any]:
        """
        Get context fields for logger binding.

        Returns:
            dict: Fields to bind to logger
        """
        fields = {}
        if self.request_id:
            fields["request_id"] = self.request_id
        if self.user_id:
            fields["user_id"] = self.user_id
        if self.session_id:
            fields["session_id"] = self.session_id
        if self.trace_id:
            fields["trace_id"] = self.trace_id
        if self.span_id:
            fields["span_id"] = self.span_id

        # Add custom fields
        fields.update(self.custom_fields)

        return fields


class LogContextManager:
    """
    Context manager for logging context.

    Automatically sets and clears context variables.
    """

    def __init__(self, context: LogContext):
        """
        Initialize context manager.

        Args:
            context: LogContext to set
        """
        self.context = context
        self._tokens: list[contextvars.Token] = []

    def __enter__(self) -> LogContext:
        """Enter context and set context variables."""
        # Set context variables
        if self.context.request_id:
            token = request_id_ctx.set(self.context.request_id)
            self._tokens.append(("request_id", token))

        if self.context.user_id:
            token = user_id_ctx.set(self.context.user_id)
            self._tokens.append(("user_id", token))

        if self.context.session_id:
            token = session_id_ctx.set(self.context.session_id)
            self._tokens.append(("session_id", token))

        if self.context.trace_id:
            token = trace_id_ctx.set(self.context.trace_id)
            self._tokens.append(("trace_id", token))

        if self.context.span_id:
            token = span_id_ctx.set(self.context.span_id)
            self._tokens.append(("span_id", token))

        # Set custom fields
        if self.context.custom_fields:
            current = custom_ctx.get({})
            updated = {**current, **self.context.custom_fields}
            token = custom_ctx.set(updated)
            self._tokens.append(("custom", token))

        return self.context

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and reset context variables."""
        # Reset in reverse order
        for var_name, token in reversed(self._tokens):
            if var_name == "request_id":
                request_id_ctx.reset(token)
            elif var_name == "user_id":
                user_id_ctx.reset(token)
            elif var_name == "session_id":
                session_id_ctx.reset(token)
            elif var_name == "trace_id":
                trace_id_ctx.reset(token)
            elif var_name == "span_id":
                span_id_ctx.reset(token)
            elif var_name == "custom":
                custom_ctx.reset(token)


def get_request_id() -> str | None:
    """Get current request ID from context."""
    return request_id_ctx.get()


def set_request_id(request_id: str) -> contextvars.Token:
    """
    Set request ID in context.

    Args:
        request_id: Request correlation ID

    Returns:
        Token: Context variable token (for manual reset)
    """
    return request_id_ctx.set(request_id)


def get_user_id() -> str | None:
    """Get current user ID from context."""
    return user_id_ctx.get()


def set_user_id(user_id: str) -> contextvars.Token:
    """
    Set user ID in context.

    Args:
        user_id: User identifier

    Returns:
        Token: Context variable token
    """
    return user_id_ctx.set(user_id)


def get_session_id() -> str | None:
    """Get current session ID from context."""
    return session_id_ctx.get()


def set_session_id(session_id: str) -> contextvars.Token:
    """
    Set session ID in context.

    Args:
        session_id: Session identifier

    Returns:
        Token: Context variable token
    """
    return session_id_ctx.set(session_id)


def get_trace_id() -> str | None:
    """Get current trace ID from context."""
    return trace_id_ctx.get()


def set_trace_id(trace_id: str) -> contextvars.Token:
    """
    Set trace ID in context.

    Args:
        trace_id: Distributed trace identifier

    Returns:
        Token: Context variable token
    """
    return trace_id_ctx.set(trace_id)


def get_span_id() -> str | None:
    """Get current span ID from context."""
    return span_id_ctx.get()


def set_span_id(span_id: str) -> contextvars.Token:
    """
    Set span ID in context.

    Args:
        span_id: Current span identifier

    Returns:
        Token: Context variable token
    """
    return span_id_ctx.set(span_id)


def get_custom_field(key: str) -> Any:
    """
    Get custom field from context.

    Args:
        key: Field name

    Returns:
        Any: Field value or None
    """
    custom = custom_ctx.get({})
    return custom.get(key)


def set_custom_field(key: str, value: Any) -> None:
    """
    Set custom field in context.

    Args:
        key: Field name
        value: Field value
    """
    custom = custom_ctx.get({})
    custom[key] = value
    custom_ctx.set(custom)


def get_all_context() -> dict[str, Any]:
    """
    Get all context variables.

    Returns:
        dict: All context variables
    """
    context = {}

    if request_id := get_request_id():
        context["request_id"] = request_id

    if user_id := get_user_id():
        context["user_id"] = user_id

    if session_id := get_session_id():
        context["session_id"] = session_id

    if trace_id := get_trace_id():
        context["trace_id"] = trace_id

    if span_id := get_span_id():
        context["span_id"] = span_id

    # Add custom fields
    custom = custom_ctx.get({})
    context.update(custom)

    return context


def bind_context_to_logger() -> dict[str, Any]:
    """
    Bind current context to logger.

    Returns:
        dict: Context fields for logger binding

    Example:
        logger.bind(**bind_context_to_logger()).info("Message with context")
    """
    return get_all_context()


def create_request_context(
    request_id: str | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
    **kwargs,
) -> LogContext:
    """
    Create log context for a request.

    Args:
        request_id: Request correlation ID (auto-generated if not provided)
        user_id: User identifier
        session_id: Session identifier
        **kwargs: Additional custom fields

    Returns:
        LogContext: Created context

    Example:
        with LogContextManager(create_request_context(user_id="123")):
            logger.info("Processing request")  # Will include user_id
    """
    return LogContext(
        request_id=request_id or str(uuid4()),
        user_id=user_id,
        session_id=session_id,
        custom_fields=kwargs,
    )


def with_log_context(**context_fields):
    """
    Decorator to add context to function logging.

    Args:
        **context_fields: Context fields to add

    Example:
        @with_log_context(operation="schedule_generation")
        def generate_schedule():
            logger.info("Starting")  # Will include operation="schedule_generation"
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Set custom fields
            for key, value in context_fields.items():
                set_custom_field(key, value)

            try:
                return func(*args, **kwargs)
            finally:
                # Note: In production, would need proper cleanup
                pass

        return wrapper

    return decorator
