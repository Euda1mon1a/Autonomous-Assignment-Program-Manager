"""
Integration utilities for OpenTelemetry tracing.

Provides helper functions for integrating tracing into the FastAPI application.
"""
import logging
from typing import Optional

from fastapi import FastAPI

from app.core.config import get_settings
from app.telemetry.tracer import TracerConfig, initialize_tracer, get_tracer_manager
from app.telemetry.exporters import (
    ExporterType,
    ExporterConfig,
    create_span_processor,
)
from app.telemetry.middleware import TracingMiddleware

logger = logging.getLogger(__name__)


def setup_telemetry(app: FastAPI) -> bool:
    """
    Set up OpenTelemetry tracing for the FastAPI application.

    This function:
    1. Initializes the tracer provider
    2. Configures exporters based on settings
    3. Adds tracing middleware to the app
    4. Sets up auto-instrumentation

    Args:
        app: FastAPI application instance

    Returns:
        bool: True if telemetry was enabled, False otherwise

    Example:
        from fastapi import FastAPI
        from app.telemetry.integration import setup_telemetry

        app = FastAPI()
        setup_telemetry(app)
    """
    settings = get_settings()

    # Skip if telemetry is disabled
    if not settings.TELEMETRY_ENABLED:
        logger.info("OpenTelemetry tracing is disabled")
        return False

    try:
        # Initialize tracer
        config = TracerConfig(
            service_name=settings.TELEMETRY_SERVICE_NAME,
            service_version=settings.APP_VERSION,
            environment=settings.TELEMETRY_ENVIRONMENT,
            sampling_rate=settings.TELEMETRY_SAMPLING_RATE,
            console_export=settings.TELEMETRY_CONSOLE_EXPORT,
            enable_sqlalchemy=settings.TELEMETRY_TRACE_SQLALCHEMY,
            enable_redis=settings.TELEMETRY_TRACE_REDIS,
            enable_http=settings.TELEMETRY_TRACE_HTTP,
        )

        initialize_tracer(config)
        logger.info(
            f"OpenTelemetry tracer initialized: "
            f"service={settings.TELEMETRY_SERVICE_NAME}, "
            f"environment={settings.TELEMETRY_ENVIRONMENT}"
        )

        # Add exporter
        exporter_config = ExporterConfig(
            exporter_type=ExporterType(settings.TELEMETRY_EXPORTER_TYPE),
            endpoint=settings.TELEMETRY_EXPORTER_ENDPOINT,
            service_name=settings.TELEMETRY_SERVICE_NAME,
            headers=settings.TELEMETRY_EXPORTER_HEADERS,
            insecure=settings.TELEMETRY_EXPORTER_INSECURE,
        )

        processor = create_span_processor(exporter_config)
        get_tracer_manager().add_span_processor(processor)

        logger.info(
            f"Trace exporter configured: "
            f"type={settings.TELEMETRY_EXPORTER_TYPE}, "
            f"endpoint={settings.TELEMETRY_EXPORTER_ENDPOINT}"
        )

        # Add tracing middleware
        app.add_middleware(
            TracingMiddleware,
            excluded_paths=["/health", "/metrics", "/docs", "/redoc", "/openapi.json"],
            capture_headers=True,
            capture_query_params=True,
        )

        logger.info("Tracing middleware added to FastAPI application")

        return True

    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry tracing: {e}", exc_info=True)
        return False


def shutdown_telemetry():
    """
    Shutdown telemetry and flush all pending spans.

    This should be called during application shutdown to ensure
    all traces are exported before the application terminates.

    Example:
        @app.on_event("shutdown")
        async def shutdown():
            shutdown_telemetry()
    """
    from app.telemetry.tracer import shutdown_tracer

    try:
        shutdown_tracer()
        logger.info("OpenTelemetry tracer shutdown complete")
    except Exception as e:
        logger.error(f"Error shutting down telemetry: {e}", exc_info=True)


# Example usage patterns

def example_fastapi_integration():
    """
    Example of integrating telemetry into a FastAPI application.

    This is for documentation purposes - not meant to be executed.
    """
    from fastapi import FastAPI

    app = FastAPI(title="My API")

    # Setup telemetry during application startup
    @app.on_event("startup")
    async def startup():
        setup_telemetry(app)

    @app.on_event("shutdown")
    async def shutdown():
        shutdown_telemetry()

    # Now all requests will be automatically traced
    @app.get("/users/{user_id}")
    async def get_user(user_id: int):
        # This request is automatically traced by the middleware
        return {"user_id": user_id}


def example_manual_tracing():
    """
    Example of using manual tracing decorators.

    This is for documentation purposes - not meant to be executed.
    """
    from app.telemetry import traced, trace_service_method

    # Basic tracing
    @traced(name="process_data", capture_args=True)
    async def process_data(data: dict):
        # Function execution is automatically traced
        return {"processed": True}

    # Service method tracing
    class MyService:
        @trace_service_method()
        async def create_item(self, item_data: dict):
            # Service method is traced with service-specific attributes
            return {"id": 1}


def example_custom_spans():
    """
    Example of creating custom spans.

    This is for documentation purposes - not meant to be executed.
    """
    from app.telemetry import get_tracer
    from opentelemetry.trace import Status, StatusCode

    tracer = get_tracer(__name__)

    async def complex_operation():
        # Create a parent span
        with tracer.start_as_current_span("complex_operation") as parent_span:
            parent_span.set_attribute("operation.type", "complex")

            # Create child span for sub-operation
            with tracer.start_as_current_span("fetch_data") as child_span:
                child_span.set_attribute("data.source", "database")
                # ... fetch data
                child_span.set_status(Status(StatusCode.OK))

            # Create another child span
            with tracer.start_as_current_span("process_data") as child_span:
                child_span.set_attribute("records.count", 100)
                # ... process data
                child_span.set_status(Status(StatusCode.OK))


def example_baggage_propagation():
    """
    Example of using baggage for cross-service context propagation.

    This is for documentation purposes - not meant to be executed.
    """
    from app.telemetry import set_baggage, get_baggage

    async def handle_request(user_id: str, tenant_id: str):
        # Set baggage that will be propagated to downstream services
        set_baggage("user.id", user_id)
        set_baggage("tenant.id", tenant_id)

        # Call other services - baggage is automatically propagated
        await call_external_service()

    async def downstream_handler():
        # Retrieve baggage from upstream service
        user_id = get_baggage("user.id")
        tenant_id = get_baggage("tenant.id")

        # Use the context in this service
        print(f"Processing request for user {user_id} in tenant {tenant_id}")
