"""
OpenTelemetry tracing middleware for FastAPI.

Provides automatic span creation for HTTP requests with rich metadata.
"""
import logging
import time
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from opentelemetry import trace, baggage
from opentelemetry.trace import Status, StatusCode, Span
from opentelemetry.semconv.trace import SpanAttributes

logger = logging.getLogger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic request tracing.

    Creates a span for each HTTP request and enriches it with:
    - HTTP method, path, status code
    - Request/response headers (configurable)
    - Query parameters
    - Client IP address
    - User agent
    - Custom attributes from baggage
    - Timing information
    """

    def __init__(
        self,
        app: ASGIApp,
        tracer_provider: Optional[trace.TracerProvider] = None,
        excluded_paths: Optional[list[str]] = None,
        capture_headers: bool = True,
        capture_query_params: bool = True,
        header_allowlist: Optional[list[str]] = None,
    ):
        """
        Initialize tracing middleware.

        Args:
            app: ASGI application
            tracer_provider: Optional tracer provider (uses global if not provided)
            excluded_paths: Paths to exclude from tracing (e.g., /health, /metrics)
            capture_headers: Whether to capture request/response headers
            capture_query_params: Whether to capture query parameters
            header_allowlist: List of headers to capture (captures all if None)
        """
        super().__init__(app)
        self.tracer = trace.get_tracer(
            __name__,
            tracer_provider=tracer_provider,
        )
        self.excluded_paths = excluded_paths or ["/health", "/metrics"]
        self.capture_headers = capture_headers
        self.capture_query_params = capture_query_params
        self.header_allowlist = header_allowlist or [
            "user-agent",
            "content-type",
            "accept",
            "x-request-id",
            "x-forwarded-for",
        ]

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Process request with tracing.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            Response: HTTP response
        """
        # Skip tracing for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Extract trace context from headers (for distributed tracing)
        # Context propagation is handled automatically by OpenTelemetry

        # Create span for this request
        span_name = f"{request.method} {request.url.path}"

        with self.tracer.start_as_current_span(
            span_name,
            kind=trace.SpanKind.SERVER,
        ) as span:
            # Set standard HTTP attributes
            self._set_http_attributes(span, request)

            # Capture request headers if enabled
            if self.capture_headers:
                self._set_header_attributes(span, request)

            # Capture query parameters if enabled
            if self.capture_query_params:
                self._set_query_attributes(span, request)

            # Capture baggage attributes
            self._set_baggage_attributes(span)

            # Process request
            start_time = time.time()
            try:
                response = await call_next(request)

                # Set response attributes
                span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, response.status_code)

                # Set span status based on HTTP status code
                if response.status_code >= 500:
                    span.set_status(Status(StatusCode.ERROR))
                elif response.status_code >= 400:
                    span.set_status(Status(StatusCode.ERROR))
                else:
                    span.set_status(Status(StatusCode.OK))

                # Add response timing
                duration_ms = (time.time() - start_time) * 1000
                span.set_attribute("http.response_time_ms", duration_ms)

                return response

            except Exception as exc:
                # Record exception in span
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))

                # Add error attributes
                span.set_attribute("error", True)
                span.set_attribute("error.type", type(exc).__name__)
                span.set_attribute("error.message", str(exc))

                raise

    def _set_http_attributes(self, span: Span, request: Request):
        """
        Set standard HTTP semantic convention attributes.

        Args:
            span: Current span
            request: HTTP request
        """
        span.set_attribute(SpanAttributes.HTTP_METHOD, request.method)
        span.set_attribute(SpanAttributes.HTTP_URL, str(request.url))
        span.set_attribute(SpanAttributes.HTTP_SCHEME, request.url.scheme)
        span.set_attribute(SpanAttributes.HTTP_HOST, request.url.hostname or "")
        span.set_attribute(SpanAttributes.HTTP_TARGET, request.url.path)

        # Client information
        if request.client:
            span.set_attribute(SpanAttributes.HTTP_CLIENT_IP, request.client.host)

    def _set_header_attributes(self, span: Span, request: Request):
        """
        Set request header attributes.

        Args:
            span: Current span
            request: HTTP request
        """
        for header_name in self.header_allowlist:
            header_value = request.headers.get(header_name)
            if header_value:
                # Use lowercase header name for consistency
                attr_name = f"http.request.header.{header_name.lower().replace('-', '_')}"
                span.set_attribute(attr_name, header_value)

    def _set_query_attributes(self, span: Span, request: Request):
        """
        Set query parameter attributes.

        Args:
            span: Current span
            request: HTTP request
        """
        if request.query_params:
            # Convert query params to string representation
            query_string = str(request.query_params)
            span.set_attribute(SpanAttributes.HTTP_FLAVOR, query_string)

            # Set individual query parameters (limit to avoid span bloat)
            for key, value in list(request.query_params.items())[:10]:
                span.set_attribute(f"http.query.{key}", value)

    def _set_baggage_attributes(self, span: Span):
        """
        Set attributes from baggage context.

        Baggage allows propagating custom key-value pairs across service boundaries.

        Args:
            span: Current span
        """
        # Get all baggage items
        baggage_items = baggage.get_all()

        if baggage_items:
            for key, value in baggage_items.items():
                span.set_attribute(f"baggage.{key}", value)


class DatabaseTracingMiddleware:
    """
    Middleware for tracing database queries.

    This is automatically handled by SQLAlchemy instrumentation,
    but this class provides additional query-specific attributes.
    """

    @staticmethod
    def add_query_attributes(
        span: Span,
        query: str,
        params: Optional[dict] = None,
        table_name: Optional[str] = None,
    ):
        """
        Add database query attributes to a span.

        Args:
            span: Current span
            query: SQL query string
            params: Query parameters (will be sanitized)
            table_name: Name of the table being queried
        """
        span.set_attribute("db.system", "postgresql")
        span.set_attribute("db.statement", query[:1000])  # Limit query length

        if table_name:
            span.set_attribute("db.sql.table", table_name)

        if params:
            # Sanitize parameters (don't include sensitive data)
            sanitized_params = {
                k: "***" if k in ["password", "token", "secret"] else str(v)[:100]
                for k, v in params.items()
            }
            span.set_attribute("db.params", str(sanitized_params))


class ExternalServiceTracingHelper:
    """
    Helper for tracing external service calls.

    Provides utilities for creating spans for HTTP calls to external services.
    """

    @staticmethod
    def trace_http_call(
        tracer: trace.Tracer,
        method: str,
        url: str,
        service_name: str,
    ):
        """
        Create a span for an external HTTP call.

        Args:
            tracer: Tracer instance
            method: HTTP method
            url: Request URL
            service_name: Name of the external service

        Returns:
            Context manager for the span

        Example:
            with ExternalServiceTracingHelper.trace_http_call(
                tracer, "GET", "https://api.example.com/data", "external-api"
            ) as span:
                response = requests.get("https://api.example.com/data")
                span.set_attribute("http.status_code", response.status_code)
        """
        span_name = f"{method} {service_name}"

        span = tracer.start_as_current_span(
            span_name,
            kind=trace.SpanKind.CLIENT,
        )

        # Set HTTP client attributes
        span.set_attribute(SpanAttributes.HTTP_METHOD, method)
        span.set_attribute(SpanAttributes.HTTP_URL, url)
        span.set_attribute("peer.service", service_name)

        return span


def add_custom_span_attributes(
    attributes: dict[str, str | int | float | bool],
):
    """
    Add custom attributes to the current span.

    Args:
        attributes: Dictionary of custom attributes

    Example:
        add_custom_span_attributes({
            "user.id": "12345",
            "user.role": "admin",
            "operation": "schedule_generation",
        })
    """
    current_span = trace.get_current_span()

    if current_span and current_span.is_recording():
        for key, value in attributes.items():
            current_span.set_attribute(key, value)


def add_span_event(
    name: str,
    attributes: Optional[dict[str, str | int | float | bool]] = None,
):
    """
    Add an event to the current span.

    Events are timestamped log entries within a span.

    Args:
        name: Event name
        attributes: Optional event attributes

    Example:
        add_span_event("schedule_validated", {
            "block_count": 730,
            "violations": 0,
        })
    """
    current_span = trace.get_current_span()

    if current_span and current_span.is_recording():
        current_span.add_event(name, attributes or {})


def set_baggage(key: str, value: str):
    """
    Set a baggage item for cross-service propagation.

    Baggage allows propagating custom key-value pairs across service boundaries.

    Args:
        key: Baggage key
        value: Baggage value

    Example:
        set_baggage("user.id", "12345")
        set_baggage("tenant.id", "acme-corp")
    """
    baggage.set_baggage(key, value)


def get_baggage(key: str) -> Optional[str]:
    """
    Get a baggage item.

    Args:
        key: Baggage key

    Returns:
        Baggage value or None if not found
    """
    return baggage.get_baggage(key)
