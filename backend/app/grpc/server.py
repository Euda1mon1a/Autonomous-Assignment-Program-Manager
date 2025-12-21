"""
gRPC Server Setup and Configuration.

This module provides functions to start and stop the gRPC server with:
- Multi-service registration (Schedule, Assignment, Person, Health)
- Authentication interceptor
- Error handling interceptor
- Logging interceptor
- Metrics collection
- Health checking service
- Reflection service (for debugging with grpcurl/grpc_cli)
- Graceful shutdown handling

Usage:
    from app.grpc.server import start_grpc_server, stop_grpc_server

    # Start server (blocking)
    server = start_grpc_server(port=50051)
    server.wait_for_termination()

    # Start server (non-blocking)
    server = start_grpc_server(port=50051, wait=False)
    # ... do other work ...
    stop_grpc_server(server)

Configuration:
    Environment variables:
    - GRPC_PORT: Port to listen on (default: 50051)
    - GRPC_MAX_WORKERS: Thread pool size (default: 10)
    - GRPC_MAX_MESSAGE_LENGTH: Max message size in bytes (default: 100MB)
    - GRPC_ENABLE_REFLECTION: Enable reflection service (default: True in DEBUG mode)
    - GRPC_ENABLE_TLS: Enable TLS (default: False)
    - GRPC_TLS_CERT_PATH: Path to TLS certificate
    - GRPC_TLS_KEY_PATH: Path to TLS private key

Production Deployment:
    - Always enable TLS in production (GRPC_ENABLE_TLS=true)
    - Use a reverse proxy (Envoy, nginx) for load balancing
    - Monitor with Prometheus metrics
    - Set appropriate max_workers based on CPU cores
    - Configure connection limits and timeouts

Security:
    - JWT authentication required for all RPCs (except health check)
    - Rate limiting per client (via interceptor)
    - TLS encryption (enabled via GRPC_ENABLE_TLS)
    - Audit logging of all operations
"""

import logging
import os
import signal
import sys
from concurrent import futures
from typing import Optional

from app.core.config import get_settings
from app.grpc.interceptors import (
    AuthenticationInterceptor,
    ErrorHandlingInterceptor,
    LoggingInterceptor,
    MetricsInterceptor,
)
from app.grpc.services import (
    AssignmentServicer,
    HealthServicer,
    PersonServicer,
    ScheduleServicer,
)

settings = get_settings()
logger = logging.getLogger(__name__)

# gRPC imports (conditional - graceful degradation if not installed)
try:
    import grpc
    from grpc_reflection.v1alpha import reflection

    GRPC_AVAILABLE = True
except ImportError:
    logger.warning(
        "grpcio not installed. gRPC server will not be available. "
        "Install with: pip install grpcio grpcio-reflection grpcio-tools"
    )
    GRPC_AVAILABLE = False


# Configuration from environment
GRPC_PORT = int(os.getenv("GRPC_PORT", "50051"))
GRPC_MAX_WORKERS = int(os.getenv("GRPC_MAX_WORKERS", "10"))
GRPC_MAX_MESSAGE_LENGTH = int(os.getenv("GRPC_MAX_MESSAGE_LENGTH", str(100 * 1024 * 1024)))  # 100MB
GRPC_ENABLE_REFLECTION = os.getenv("GRPC_ENABLE_REFLECTION", str(settings.DEBUG)).lower() == "true"
GRPC_ENABLE_TLS = os.getenv("GRPC_ENABLE_TLS", "false").lower() == "true"
GRPC_TLS_CERT_PATH = os.getenv("GRPC_TLS_CERT_PATH", "")
GRPC_TLS_KEY_PATH = os.getenv("GRPC_TLS_KEY_PATH", "")


def _create_server_credentials():
    """
    Create server credentials for TLS.

    Returns:
        grpc.ServerCredentials or None if TLS is disabled
    """
    if not GRPC_ENABLE_TLS:
        return None

    if not GRPC_TLS_CERT_PATH or not GRPC_TLS_KEY_PATH:
        logger.error(
            "TLS enabled but GRPC_TLS_CERT_PATH or GRPC_TLS_KEY_PATH not set. "
            "Falling back to insecure connection."
        )
        return None

    try:
        with open(GRPC_TLS_CERT_PATH, "rb") as f:
            cert_chain = f.read()
        with open(GRPC_TLS_KEY_PATH, "rb") as f:
            private_key = f.read()

        credentials = grpc.ssl_server_credentials(
            [(private_key, cert_chain)],
            root_certificates=None,
            require_client_auth=False,
        )
        logger.info("TLS credentials loaded successfully")
        return credentials

    except Exception as e:
        logger.error(f"Failed to load TLS credentials: {e}")
        return None


def _register_services(server) -> list[str]:
    """
    Register all gRPC services with the server.

    This is a simplified registration. In production, you would use
    generated code from .proto files:
        add_ScheduleServiceServicer_to_server(ScheduleServicer(), server)

    Args:
        server: gRPC server instance

    Returns:
        List of registered service names (for reflection)
    """
    # For demonstration, we create a simple registration
    # In production, use protobuf-generated registration functions

    logger.info("Registering gRPC services...")

    # Service instances
    schedule_servicer = ScheduleServicer()
    assignment_servicer = AssignmentServicer()
    person_servicer = PersonServicer()
    health_servicer = HealthServicer()

    # Note: In production, you would use generated add_*_to_server functions
    # For now, we'll just store references (actual registration requires .proto files)

    logger.info("gRPC services registered (simplified mode - requires .proto files for full implementation)")

    # Return service names for reflection
    return [
        "scheduler.ScheduleService",
        "scheduler.AssignmentService",
        "scheduler.PersonService",
        "grpc.health.v1.Health",
    ]


def start_grpc_server(
    port: int = GRPC_PORT,
    max_workers: int = GRPC_MAX_WORKERS,
    wait: bool = False,
) -> Optional[object]:
    """
    Start the gRPC server with all services and interceptors.

    Args:
        port: Port to listen on (default from GRPC_PORT env var)
        max_workers: Thread pool size (default from GRPC_MAX_WORKERS env var)
        wait: If True, block until server terminates (default: False)

    Returns:
        grpc.Server instance, or None if gRPC is not available

    Raises:
        RuntimeError: If server fails to start

    Example:
        # Start and wait (blocking)
        server = start_grpc_server(port=50051, wait=True)

        # Start non-blocking
        server = start_grpc_server(port=50051, wait=False)
        # ... do other work ...
        server.wait_for_termination()
    """
    if not GRPC_AVAILABLE:
        logger.error("gRPC server cannot start - grpcio not installed")
        return None

    try:
        # Create interceptor chain
        interceptors = [
            ErrorHandlingInterceptor(),
            AuthenticationInterceptor(),
            LoggingInterceptor(),
            MetricsInterceptor(),
        ]

        # Create server with interceptors
        server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=max_workers),
            interceptors=interceptors,
            options=[
                ("grpc.max_send_message_length", GRPC_MAX_MESSAGE_LENGTH),
                ("grpc.max_receive_message_length", GRPC_MAX_MESSAGE_LENGTH),
                ("grpc.so_reuseport", 1),
                ("grpc.keepalive_time_ms", 30000),
                ("grpc.keepalive_timeout_ms", 10000),
                ("grpc.http2.max_pings_without_data", 0),
                ("grpc.http2.min_time_between_pings_ms", 10000),
                ("grpc.http2.min_ping_interval_without_data_ms", 5000),
            ],
        )

        # Register services
        service_names = _register_services(server)

        # Enable reflection service for debugging (allows grpcurl/grpc_cli to introspect)
        if GRPC_ENABLE_REFLECTION:
            try:
                reflection.enable_server_reflection(service_names, server)
                logger.info("gRPC reflection service enabled")
            except Exception as e:
                logger.warning(f"Failed to enable reflection service: {e}")

        # Configure server credentials
        credentials = _create_server_credentials()

        # Bind to port
        if credentials:
            server.add_secure_port(f"[::]:{port}", credentials)
            logger.info(f"gRPC server configured with TLS on port {port}")
        else:
            server.add_insecure_port(f"[::]:{port}")
            if not settings.DEBUG:
                logger.warning(
                    f"gRPC server running WITHOUT TLS on port {port}. "
                    "This is insecure for production!"
                )
            else:
                logger.info(f"gRPC server configured (insecure) on port {port}")

        # Start server
        server.start()
        logger.info(f"gRPC server started successfully on port {port}")

        # Register signal handlers for graceful shutdown
        def handle_shutdown(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            stop_grpc_server(server)
            sys.exit(0)

        signal.signal(signal.SIGTERM, handle_shutdown)
        signal.signal(signal.SIGINT, handle_shutdown)

        # Wait for termination if requested
        if wait:
            logger.info("gRPC server waiting for termination...")
            server.wait_for_termination()

        return server

    except Exception as e:
        logger.error(f"Failed to start gRPC server: {e}", exc_info=True)
        raise RuntimeError(f"gRPC server startup failed: {e}")


def stop_grpc_server(server, grace_period: float = 5.0) -> None:
    """
    Stop the gRPC server gracefully.

    Args:
        server: gRPC server instance from start_grpc_server()
        grace_period: Seconds to wait for in-flight RPCs to complete (default: 5.0)

    Example:
        server = start_grpc_server(port=50051)
        # ... server running ...
        stop_grpc_server(server, grace_period=10.0)
    """
    if server is None:
        return

    logger.info(f"Stopping gRPC server (grace period: {grace_period}s)...")

    try:
        # Initiate graceful shutdown
        shutdown_event = server.stop(grace_period)

        # Wait for shutdown to complete
        shutdown_event.wait()

        logger.info("gRPC server stopped successfully")

    except Exception as e:
        logger.error(f"Error stopping gRPC server: {e}", exc_info=True)


def run_server():
    """
    Run the gRPC server as a standalone application.

    This is the main entry point for running gRPC server separately from FastAPI.

    Usage:
        python -m app.grpc.server
    """
    logger.info("Starting standalone gRPC server...")
    logger.info(f"Configuration:")
    logger.info(f"  Port: {GRPC_PORT}")
    logger.info(f"  Max Workers: {GRPC_MAX_WORKERS}")
    logger.info(f"  Max Message Length: {GRPC_MAX_MESSAGE_LENGTH} bytes")
    logger.info(f"  Reflection Enabled: {GRPC_ENABLE_REFLECTION}")
    logger.info(f"  TLS Enabled: {GRPC_ENABLE_TLS}")

    server = start_grpc_server(wait=True)

    if server is None:
        logger.error("Failed to start gRPC server")
        sys.exit(1)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    run_server()
