"""
Distributed tracing infrastructure.

Provides OpenTelemetry-based tracing with:
- Automatic instrumentation
- Custom span creation
- Trace context propagation
- Multiple exporters (Jaeger, OTLP, Console)
"""

from app.tracing.setup import (
    TracingConfig,
    get_tracer,
    setup_tracing,
    shutdown_tracing,
)
from app.tracing.spans import (
    add_span_attributes,
    add_span_event,
    create_span,
    record_exception,
    trace_function,
)

__all__ = [
    # Setup
    "TracingConfig",
    "setup_tracing",
    "shutdown_tracing",
    "get_tracer",
    # Spans
    "create_span",
    "add_span_attributes",
    "add_span_event",
    "record_exception",
    "trace_function",
]
