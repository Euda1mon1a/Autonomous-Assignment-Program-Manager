"""
OpenTelemetry tracer configuration and initialization.

This module provides the core tracer setup for distributed tracing across
the Residency Scheduler application.
"""

import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import (
    ALWAYS_OFF,
    ALWAYS_ON,
    ParentBasedTraceIdRatio,
)
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = logging.getLogger(__name__)


class TracerConfig:
    """
    Configuration for OpenTelemetry tracer.

    Attributes:
        service_name: Name of the service for trace identification
        service_version: Version of the service
        environment: Deployment environment (dev, staging, prod)
        sampling_rate: Trace sampling rate (0.0 to 1.0)
        console_export: Enable console exporter for debugging
        enable_sqlalchemy: Enable SQLAlchemy instrumentation
        enable_redis: Enable Redis instrumentation
        enable_http: Enable HTTP client instrumentation
        exporter_type: Type of exporter (otlp_grpc, otlp_http, jaeger, zipkin, console)
        exporter_endpoint: Endpoint URL for the exporter
        exporter_insecure: Use insecure connection (no TLS)
        exporter_headers: Custom headers for authentication
    """

    def __init__(
        self,
        service_name: str = "residency-scheduler",
        service_version: str = "1.0.0",
        environment: str = "development",
        sampling_rate: float = 1.0,
        console_export: bool = False,
        enable_sqlalchemy: bool = True,
        enable_redis: bool = True,
        enable_http: bool = True,
        exporter_type: str = "otlp_grpc",
        exporter_endpoint: str = "http://localhost:4317",
        exporter_insecure: bool = True,
        exporter_headers: dict[str, str] | None = None,
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.sampling_rate = sampling_rate
        self.console_export = console_export
        self.enable_sqlalchemy = enable_sqlalchemy
        self.enable_redis = enable_redis
        self.enable_http = enable_http
        self.exporter_type = exporter_type
        self.exporter_endpoint = exporter_endpoint
        self.exporter_insecure = exporter_insecure
        self.exporter_headers = exporter_headers or {}


class TracerManager:
    """
    Manages OpenTelemetry tracer lifecycle and configuration.

    This class handles:
    - Tracer provider initialization
    - Span processor configuration
    - Auto-instrumentation setup
    - Propagator configuration
    """

    def __init__(self, config: TracerConfig):
        """
        Initialize tracer manager.

        Args:
            config: Tracer configuration
        """
        self.config = config
        self._tracer_provider: TracerProvider | None = None
        self._is_initialized = False

    def initialize(self) -> TracerProvider:
        """
        Initialize OpenTelemetry tracer provider and instrumentation.

        Returns:
            TracerProvider: Configured tracer provider

        Raises:
            RuntimeError: If tracer is already initialized
        """
        if self._is_initialized:
            raise RuntimeError("Tracer already initialized")

        # Create resource with service metadata
        resource = Resource.create(
            {
                SERVICE_NAME: self.config.service_name,
                SERVICE_VERSION: self.config.service_version,
                "deployment.environment": self.config.environment,
            }
        )

        # Create tracer provider with sampling
        sampler = self._create_sampler()
        self._tracer_provider = TracerProvider(
            resource=resource,
            sampler=sampler,
        )

        # Add OTLP exporter if configured
        exporter = self._create_exporter()
        if exporter:
            span_processor = BatchSpanProcessor(exporter)
            self._tracer_provider.add_span_processor(span_processor)
            logger.info(
                f"{self.config.exporter_type.upper()} span exporter enabled: "
                f"endpoint={self.config.exporter_endpoint}"
            )

        # Add console exporter for debugging if enabled
        if self.config.console_export:
            console_processor = BatchSpanProcessor(ConsoleSpanExporter())
            self._tracer_provider.add_span_processor(console_processor)
            logger.info("Console span exporter enabled")

        # Set as global tracer provider
        trace.set_tracer_provider(self._tracer_provider)

        # Configure propagators for context propagation
        self._setup_propagators()

        # Set up auto-instrumentation
        self._setup_instrumentation()

        self._is_initialized = True
        logger.info(
            f"OpenTelemetry tracer initialized: service={self.config.service_name}, "
            f"environment={self.config.environment}, sampling_rate={self.config.sampling_rate}"
        )

        return self._tracer_provider

    def _create_sampler(self):
        """
        Create trace sampler based on configuration.

        Returns:
            Sampler: Configured sampler
        """
        if self.config.sampling_rate >= 1.0:
            return ALWAYS_ON
        elif self.config.sampling_rate <= 0.0:
            return ALWAYS_OFF
        else:
            # Use parent-based sampling with ratio-based root sampling
            return ParentBasedTraceIdRatio(self.config.sampling_rate)

    def _create_exporter(self):
        """
        Create span exporter based on configuration.

        Returns:
            SpanExporter: Configured exporter, or None if no exporter configured

        Raises:
            ValueError: If exporter type is unsupported
        """
        exporter_type = self.config.exporter_type.lower()

        if exporter_type == "console":
            # Console exporter is handled separately
            return None

        elif exporter_type == "otlp_grpc":
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                    OTLPSpanExporter,
                )

                return OTLPSpanExporter(
                    endpoint=self.config.exporter_endpoint,
                    insecure=self.config.exporter_insecure,
                    headers=tuple(self.config.exporter_headers.items())
                    if self.config.exporter_headers
                    else None,
                )
            except ImportError as e:
                logger.warning(
                    f"OTLP gRPC exporter not available: {e}. "
                    "Install with: pip install opentelemetry-exporter-otlp-proto-grpc"
                )
                return None

        elif exporter_type == "otlp_http":
            try:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                    OTLPSpanExporter,
                )

                return OTLPSpanExporter(
                    endpoint=self.config.exporter_endpoint,
                    headers=self.config.exporter_headers,
                )
            except ImportError as e:
                logger.warning(
                    f"OTLP HTTP exporter not available: {e}. "
                    "Install with: pip install opentelemetry-exporter-otlp-proto-http"
                )
                return None

        elif exporter_type == "jaeger":
            try:
                from opentelemetry.exporter.jaeger.thrift import JaegerExporter

                return JaegerExporter(
                    agent_host_name=self.config.exporter_endpoint.split("://")[1].split(
                        ":"
                    )[0],
                    agent_port=int(
                        self.config.exporter_endpoint.split(":")[-1]
                        if ":" in self.config.exporter_endpoint
                        else "6831"
                    ),
                )
            except ImportError as e:
                logger.warning(
                    f"Jaeger exporter not available: {e}. "
                    "Install with: pip install opentelemetry-exporter-jaeger"
                )
                return None

        elif exporter_type == "zipkin":
            try:
                from opentelemetry.exporter.zipkin.json import ZipkinExporter

                return ZipkinExporter(endpoint=self.config.exporter_endpoint)
            except ImportError as e:
                logger.warning(
                    f"Zipkin exporter not available: {e}. "
                    "Install with: pip install opentelemetry-exporter-zipkin-json"
                )
                return None

        else:
            raise ValueError(
                f"Unsupported exporter type: {exporter_type}. "
                f"Supported types: otlp_grpc, otlp_http, jaeger, zipkin, console"
            )

    def _setup_propagators(self):
        """
        Set up trace context propagators.

        Configures multiple propagators for compatibility:
        - W3C Trace Context (standard)
        - B3 Multi (Zipkin compatibility)
        - W3C Baggage (for custom attributes)
        """
        set_global_textmap(
            CompositePropagator(
                [
                    TraceContextTextMapPropagator(),  # W3C standard
                    B3MultiFormat(),  # Zipkin/B3 compatibility
                    W3CBaggagePropagator(),  # Baggage propagation
                ]
            )
        )
        logger.info("Trace propagators configured: W3C TraceContext, B3, W3C Baggage")

    def _setup_instrumentation(self):
        """Set up auto-instrumentation for common libraries."""
        # SQLAlchemy instrumentation for database tracing
        if self.config.enable_sqlalchemy:
            try:
                SQLAlchemyInstrumentor().instrument(
                    enable_commenter=True,  # Add trace context to SQL comments
                    commenter_options={"db_framework": True},
                )
                logger.info("SQLAlchemy instrumentation enabled")
            except Exception as e:
                logger.warning(f"Failed to instrument SQLAlchemy: {e}")

        # Redis instrumentation
        if self.config.enable_redis:
            try:
                RedisInstrumentor().instrument()
                logger.info("Redis instrumentation enabled")
            except Exception as e:
                logger.warning(f"Failed to instrument Redis: {e}")

        # HTTP client instrumentation
        if self.config.enable_http:
            try:
                RequestsInstrumentor().instrument()
                HTTPXClientInstrumentor().instrument()
                logger.info("HTTP client instrumentation enabled (requests, httpx)")
            except Exception as e:
                logger.warning(f"Failed to instrument HTTP clients: {e}")

    def add_span_processor(self, processor: BatchSpanProcessor):
        """
        Add a span processor to the tracer provider.

        Args:
            processor: Span processor to add

        Raises:
            RuntimeError: If tracer is not initialized
        """
        if not self._is_initialized or not self._tracer_provider:
            raise RuntimeError("Tracer must be initialized before adding processors")

        self._tracer_provider.add_span_processor(processor)

    def get_tracer(self, name: str, version: str | None = None) -> trace.Tracer:
        """
        Get a tracer instance.

        Args:
            name: Tracer name (typically module name)
            version: Optional tracer version

        Returns:
            Tracer: Tracer instance

        Raises:
            RuntimeError: If tracer is not initialized
        """
        if not self._is_initialized:
            raise RuntimeError("Tracer must be initialized first")

        return trace.get_tracer(name, version)

    def shutdown(self):
        """
        Shutdown tracer provider and flush all spans.

        This should be called during application shutdown to ensure
        all spans are exported before termination.
        """
        if self._tracer_provider:
            self._tracer_provider.shutdown()
            logger.info("Tracer provider shutdown complete")
            self._is_initialized = False


# Global tracer manager instance
_tracer_manager: TracerManager | None = None


def initialize_tracer(config: TracerConfig) -> TracerProvider:
    """
    Initialize the global tracer manager.

    Args:
        config: Tracer configuration

    Returns:
        TracerProvider: Configured tracer provider

    Raises:
        RuntimeError: If tracer is already initialized
    """
    global _tracer_manager

    if _tracer_manager is not None:
        raise RuntimeError("Tracer already initialized")

    _tracer_manager = TracerManager(config)
    return _tracer_manager.initialize()


def get_tracer_manager() -> TracerManager:
    """
    Get the global tracer manager instance.

    Returns:
        TracerManager: Global tracer manager

    Raises:
        RuntimeError: If tracer is not initialized
    """
    if _tracer_manager is None:
        raise RuntimeError("Tracer not initialized. Call initialize_tracer() first")

    return _tracer_manager


def get_tracer(name: str, version: str | None = None) -> trace.Tracer:
    """
    Get a tracer instance from the global tracer manager.

    Args:
        name: Tracer name (typically module name)
        version: Optional tracer version

    Returns:
        Tracer: Tracer instance
    """
    return get_tracer_manager().get_tracer(name, version)


def shutdown_tracer():
    """Shutdown the global tracer manager."""
    global _tracer_manager

    if _tracer_manager:
        _tracer_manager.shutdown()
        _tracer_manager = None
