"""OpenTelemetry distributed tracing configuration."""

import logging
from typing import Any, Dict, List, Optional

from opentelemetry import metrics, trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor


# ============================================================================
# TRACING CONFIGURATION
# ============================================================================

class TracingConfig:
    """Configuration for distributed tracing."""

    def __init__(
        self,
        service_name: str = 'residency-scheduler',
        environment: str = 'production',
        jaeger_host: str = 'localhost',
        jaeger_port: int = 6831,
        otlp_endpoint: str = 'http://localhost:4317',
        sample_rate: float = 1.0,
        enable_jaeger: bool = True,
        enable_otlp: bool = False,
    ):
        """
        Initialize tracing configuration.

        Args:
            service_name: Service name for tracing
            environment: Deployment environment
            jaeger_host: Jaeger collector host
            jaeger_port: Jaeger collector port
            otlp_endpoint: OTLP exporter endpoint
            sample_rate: Trace sampling rate (0.0-1.0)
            enable_jaeger: Enable Jaeger exporter
            enable_otlp: Enable OTLP exporter
        """
        self.service_name = service_name
        self.environment = environment
        self.jaeger_host = jaeger_host
        self.jaeger_port = jaeger_port
        self.otlp_endpoint = otlp_endpoint
        self.sample_rate = sample_rate
        self.enable_jaeger = enable_jaeger
        self.enable_otlp = enable_otlp

        self.logger = logging.getLogger('app.tracing')


class TracingSetup:
    """Setup distributed tracing infrastructure."""

    def __init__(self, config: TracingConfig):
        """
        Initialize tracing setup.

        Args:
            config: Tracing configuration
        """
        self.config = config
        self.tracer_provider: Optional[TracerProvider] = None
        self.meter_provider: Optional[MeterProvider] = None
        self.logger = logging.getLogger('app.tracing')

    def setup_tracer_provider(self) -> TracerProvider:
        """
        Setup tracer provider with exporters.

        Returns:
            Configured TracerProvider instance
        """
        # Create resource
        resource = Resource.create({
            SERVICE_NAME: self.config.service_name,
            'environment': self.config.environment,
            'service.version': '1.0.0',
        })

        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)

        # Add Jaeger exporter
        if self.config.enable_jaeger:
            try:
                jaeger_exporter = JaegerExporter(
                    agent_host_name=self.config.jaeger_host,
                    agent_port=self.config.jaeger_port,
                )
                tracer_provider.add_span_processor(
                    BatchSpanProcessor(jaeger_exporter)
                )
                self.logger.info(
                    f"Jaeger exporter configured: {self.config.jaeger_host}:{self.config.jaeger_port}"
                )
            except Exception as e:
                self.logger.warning(f"Failed to configure Jaeger: {e}")

        # Add OTLP exporter
        if self.config.enable_otlp:
            try:
                otlp_exporter = OTLPSpanExporter(
                    endpoint=self.config.otlp_endpoint
                )
                tracer_provider.add_span_processor(
                    BatchSpanProcessor(otlp_exporter)
                )
                self.logger.info(f"OTLP exporter configured: {self.config.otlp_endpoint}")
            except Exception as e:
                self.logger.warning(f"Failed to configure OTLP: {e}")

        # Set global tracer provider
        trace.set_tracer_provider(tracer_provider)
        self.tracer_provider = tracer_provider

        return tracer_provider

    def setup_meter_provider(self) -> MeterProvider:
        """
        Setup meter provider with exporters.

        Returns:
            Configured MeterProvider instance
        """
        # Create resource
        resource = Resource.create({
            SERVICE_NAME: self.config.service_name,
            'environment': self.config.environment,
        })

        # Create readers for exporters
        readers = []

        # Add OTLP metric reader
        if self.config.enable_otlp:
            try:
                otlp_metric_exporter = OTLPMetricExporter(
                    endpoint=self.config.otlp_endpoint
                )
                reader = PeriodicExportingMetricReader(otlp_metric_exporter)
                readers.append(reader)
                self.logger.info(f"OTLP metrics exporter configured")
            except Exception as e:
                self.logger.warning(f"Failed to configure OTLP metrics: {e}")

        # Create meter provider
        meter_provider = MeterProvider(
            resource=resource,
            metric_readers=readers
        )

        # Set global meter provider
        metrics.set_meter_provider(meter_provider)
        self.meter_provider = meter_provider

        return meter_provider

    def instrument_fastapi(self, app: Any) -> None:
        """
        Instrument FastAPI application.

        Args:
            app: FastAPI application instance
        """
        try:
            FastAPIInstrumentor.instrument_app(
                app,
                tracer_provider=self.tracer_provider,
            )
            self.logger.info("FastAPI instrumentation configured")
        except Exception as e:
            self.logger.warning(f"Failed to instrument FastAPI: {e}")

    def instrument_sqlalchemy(self, engine: Any) -> None:
        """
        Instrument SQLAlchemy engine.

        Args:
            engine: SQLAlchemy engine instance
        """
        try:
            SQLAlchemyInstrumentor().instrument(
                engine_factory=lambda: engine,
                tracer_provider=self.tracer_provider,
            )
            self.logger.info("SQLAlchemy instrumentation configured")
        except Exception as e:
            self.logger.warning(f"Failed to instrument SQLAlchemy: {e}")

    def instrument_redis(self) -> None:
        """Instrument Redis client."""
        try:
            RedisInstrumentor().instrument(
                tracer_provider=self.tracer_provider,
            )
            self.logger.info("Redis instrumentation configured")
        except Exception as e:
            self.logger.warning(f"Failed to instrument Redis: {e}")

    def instrument_requests(self) -> None:
        """Instrument requests library."""
        try:
            RequestsInstrumentor().instrument(
                tracer_provider=self.tracer_provider,
            )
            self.logger.info("Requests instrumentation configured")
        except Exception as e:
            self.logger.warning(f"Failed to instrument Requests: {e}")

    def setup_all(self, app: Optional[Any] = None) -> None:
        """
        Setup all tracing infrastructure.

        Args:
            app: FastAPI application (optional)
        """
        self.setup_tracer_provider()
        self.setup_meter_provider()

        if app:
            self.instrument_fastapi(app)

        self.instrument_requests()
        self.instrument_redis()

        self.logger.info(f"Tracing setup completed for {self.config.service_name}")


# ============================================================================
# SPAN HELPERS
# ============================================================================

def get_tracer(name: str = 'app') -> Any:
    """
    Get tracer instance.

    Args:
        name: Tracer name

    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)


def create_span(
    name: str,
    attributes: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Create a span.

    Args:
        name: Span name
        attributes: Span attributes

    Returns:
        Active span context
    """
    tracer = get_tracer()
    span = tracer.start_span(name)

    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)

    return span


# ============================================================================
# TRACE CONTEXT MANAGEMENT
# ============================================================================

class TraceContext:
    """Manage trace context information."""

    def __init__(self):
        """Initialize trace context."""
        self.logger = logging.getLogger('app.tracing')

    @staticmethod
    def get_current_span() -> Optional[Any]:
        """
        Get current active span.

        Returns:
            Current span or None
        """
        return trace.get_current_span()

    @staticmethod
    def set_span_attribute(key: str, value: Any) -> None:
        """
        Set attribute on current span.

        Args:
            key: Attribute key
            value: Attribute value
        """
        span = trace.get_current_span()
        if span:
            span.set_attribute(key, value)

    @staticmethod
    def get_trace_id() -> str:
        """
        Get current trace ID.

        Returns:
            Trace ID or empty string
        """
        span = trace.get_current_span()
        if span and span.get_span_context():
            return format(span.get_span_context().trace_id, '032x')
        return ''

    @staticmethod
    def get_span_id() -> str:
        """
        Get current span ID.

        Returns:
            Span ID or empty string
        """
        span = trace.get_current_span()
        if span and span.get_span_context():
            return format(span.get_span_context().span_id, '016x')
        return ''


# ============================================================================
# PERFORMANCE TRACING
# ============================================================================

class PerformanceTracer:
    """Trace performance metrics."""

    def __init__(self, tracer_name: str = 'performance'):
        """
        Initialize performance tracer.

        Args:
            tracer_name: Name of tracer
        """
        self.tracer = get_tracer(tracer_name)
        self.logger = logging.getLogger('app.tracing')

    def trace_database_query(
        self,
        operation: str,
        table: str,
        query_time_ms: float,
        rows_affected: int
    ) -> None:
        """
        Trace database query performance.

        Args:
            operation: Database operation
            table: Table name
            query_time_ms: Query time in milliseconds
            rows_affected: Number of rows affected
        """
        attributes = {
            'db.operation': operation,
            'db.table': table,
            'db.query_time_ms': query_time_ms,
            'db.rows_affected': rows_affected,
        }

        with self.tracer.start_as_current_span(
            'db.query',
            attributes=attributes
        ):
            pass

        # Log slow queries
        if query_time_ms > 500:
            self.logger.warning(
                f"Slow database query: {operation} on {table} took {query_time_ms}ms"
            )

    def trace_scheduler_execution(
        self,
        execution_time_ms: float,
        block_count: int,
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """
        Trace scheduler execution.

        Args:
            execution_time_ms: Execution time in milliseconds
            block_count: Number of blocks processed
            success: Whether execution succeeded
            error: Error message if failed
        """
        attributes = {
            'scheduler.execution_time_ms': execution_time_ms,
            'scheduler.block_count': block_count,
            'scheduler.success': success,
        }

        if error:
            attributes['scheduler.error'] = error

        with self.tracer.start_as_current_span(
            'scheduler.execute',
            attributes=attributes
        ):
            pass

    def trace_api_call(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float
    ) -> None:
        """
        Trace API call.

        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            response_time_ms: Response time in milliseconds
        """
        attributes = {
            'http.method': method,
            'http.endpoint': endpoint,
            'http.status_code': status_code,
            'http.response_time_ms': response_time_ms,
        }

        with self.tracer.start_as_current_span(
            'http.request',
            attributes=attributes
        ):
            pass


# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

trace_context = TraceContext()
performance_tracer = PerformanceTracer()
