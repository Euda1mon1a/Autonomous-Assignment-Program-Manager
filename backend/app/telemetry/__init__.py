"""
OpenTelemetry distributed tracing for Residency Scheduler.

This package provides comprehensive distributed tracing capabilities using
OpenTelemetry, including:

- Automatic instrumentation for FastAPI, SQLAlchemy, Redis, and HTTP clients
- Multiple exporter support (Jaeger, Zipkin, OTLP)
- Tracing middleware for automatic span creation
- Decorators for manual instrumentation
- Baggage propagation for cross-service context
- Database query tracing
- External service call tracing

Quick Start:
    from app.telemetry import initialize_tracer, TracerConfig, ExporterType
    from app.telemetry import create_jaeger_processor

    # Initialize tracer
    config = TracerConfig(
        service_name="residency-scheduler",
        environment="production",
        sampling_rate=0.1,
    )
    tracer_provider = initialize_tracer(config)

    # Add exporter
    from app.telemetry import get_tracer_manager
    processor = create_jaeger_processor(endpoint="http://jaeger:4317")
    get_tracer_manager().add_span_processor(processor)

    # Add middleware to FastAPI app
    from app.telemetry import TracingMiddleware
    app.add_middleware(TracingMiddleware)

    # Use decorators
    from app.telemetry import traced

    @traced(name="my_function", capture_args=True)
    async def my_function(arg1: str):
        # Automatically traced
        pass

For more examples, see the module docstrings and examples directory.
"""

from .tracer import (
    TracerConfig,
    TracerManager,
    initialize_tracer,
    get_tracer_manager,
    get_tracer,
    shutdown_tracer,
)

from .exporters import (
    ExporterType,
    ExporterConfig,
    ExporterFactory,
    create_span_processor,
    create_multi_exporter_processor,
    create_jaeger_processor,
    create_zipkin_processor,
    create_otlp_processor,
)

from .middleware import (
    TracingMiddleware,
    DatabaseTracingMiddleware,
    ExternalServiceTracingHelper,
    add_custom_span_attributes,
    add_span_event,
    set_baggage,
    get_baggage,
)

from .decorators import (
    traced,
    trace_class,
    trace_async_generator,
    trace_service_method,
    trace_repository_method,
    trace_controller_method,
    trace_background_task,
)

__all__ = [
    # Tracer configuration
    "TracerConfig",
    "TracerManager",
    "initialize_tracer",
    "get_tracer_manager",
    "get_tracer",
    "shutdown_tracer",
    # Exporters
    "ExporterType",
    "ExporterConfig",
    "ExporterFactory",
    "create_span_processor",
    "create_multi_exporter_processor",
    "create_jaeger_processor",
    "create_zipkin_processor",
    "create_otlp_processor",
    # Middleware
    "TracingMiddleware",
    "DatabaseTracingMiddleware",
    "ExternalServiceTracingHelper",
    "add_custom_span_attributes",
    "add_span_event",
    "set_baggage",
    "get_baggage",
    # Decorators
    "traced",
    "trace_class",
    "trace_async_generator",
    "trace_service_method",
    "trace_repository_method",
    "trace_controller_method",
    "trace_background_task",
]

__version__ = "1.0.0"
