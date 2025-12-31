"""
OpenTelemetry tracing setup and configuration.

Provides:
- Tracer initialization
- Instrumentation configuration
- Resource detection
- Exporter configuration
"""

from typing import Any

from loguru import logger

try:
    from opentelemetry import trace
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
        SimpleSpanProcessor,
    )

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logger.warning("OpenTelemetry not available - tracing disabled")


class TracingConfig:
    """
    Configuration for distributed tracing.

    Attributes:
        enabled: Enable/disable tracing
        service_name: Service name for traces
        service_version: Service version
        environment: Deployment environment
        jaeger_endpoint: Jaeger collector endpoint
        otlp_endpoint: OTLP collector endpoint
        sample_rate: Trace sampling rate (0.0-1.0)
        console_export: Export to console (development)
    """

    def __init__(
        self,
        enabled: bool = True,
        service_name: str = "residency-scheduler",
        service_version: str = "1.0.0",
        environment: str = "production",
        jaeger_endpoint: str | None = None,
        otlp_endpoint: str | None = None,
        sample_rate: float = 1.0,
        console_export: bool = False,
    ):
        """Initialize tracing configuration."""
        self.enabled = enabled
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.jaeger_endpoint = jaeger_endpoint
        self.otlp_endpoint = otlp_endpoint
        self.sample_rate = sample_rate
        self.console_export = console_export


def setup_tracing(config: TracingConfig, app: Any | None = None) -> None:
    """
    Configure OpenTelemetry tracing.

    Args:
        config: Tracing configuration
        app: FastAPI application (optional)
    """
    if not config.enabled:
        logger.info("Tracing is disabled")
        return

    if not OTEL_AVAILABLE:
        logger.error("OpenTelemetry not available - cannot enable tracing")
        return

    # Create resource with service information
    resource = Resource.create(
        {
            SERVICE_NAME: config.service_name,
            SERVICE_VERSION: config.service_version,
            "deployment.environment": config.environment,
        }
    )

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Configure exporters
    if config.console_export:
        # Console exporter for development
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(console_exporter))
        logger.info("Added console span exporter")

    if config.jaeger_endpoint:
        # Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=config.jaeger_endpoint.split(":")[0],
            agent_port=int(config.jaeger_endpoint.split(":")[1]) if ":" in config.jaeger_endpoint else 6831,
        )
        provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        logger.info(f"Added Jaeger exporter: {config.jaeger_endpoint}")

    if config.otlp_endpoint:
        # OTLP exporter (for OpenTelemetry Collector)
        otlp_exporter = OTLPSpanExporter(endpoint=config.otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(f"Added OTLP exporter: {config.otlp_endpoint}")

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    # Instrument frameworks
    _instrument_frameworks(app)

    logger.info(
        f"Tracing initialized: {config.service_name} v{config.service_version} "
        f"(environment: {config.environment})"
    )


def _instrument_frameworks(app: Any | None) -> None:
    """
    Instrument frameworks for automatic tracing.

    Args:
        app: FastAPI application (optional)
    """
    # Instrument FastAPI
    if app:
        FastAPIInstrumentor.instrument_app(app)
        logger.debug("Instrumented FastAPI")

    # Instrument SQLAlchemy
    try:
        SQLAlchemyInstrumentor().instrument()
        logger.debug("Instrumented SQLAlchemy")
    except Exception as e:
        logger.warning(f"Failed to instrument SQLAlchemy: {e}")

    # Instrument Redis
    try:
        RedisInstrumentor().instrument()
        logger.debug("Instrumented Redis")
    except Exception as e:
        logger.warning(f"Failed to instrument Redis: {e}")

    # Instrument HTTPX
    try:
        HTTPXClientInstrumentor().instrument()
        logger.debug("Instrumented HTTPX")
    except Exception as e:
        logger.warning(f"Failed to instrument HTTPX: {e}")

    # Instrument logging
    try:
        LoggingInstrumentor().instrument()
        logger.debug("Instrumented logging")
    except Exception as e:
        logger.warning(f"Failed to instrument logging: {e}")


def get_tracer(name: str) -> Any:
    """
    Get a tracer instance.

    Args:
        name: Tracer name (typically module name)

    Returns:
        Tracer instance
    """
    if not OTEL_AVAILABLE:
        return None

    return trace.get_tracer(name)


def shutdown_tracing() -> None:
    """Shutdown tracing and flush remaining spans."""
    if not OTEL_AVAILABLE:
        return

    provider = trace.get_tracer_provider()
    if hasattr(provider, "shutdown"):
        provider.shutdown()
        logger.info("Tracing shutdown complete")
