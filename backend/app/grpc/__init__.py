"""
gRPC Service Layer for Residency Scheduler.

This module provides gRPC-based APIs for high-performance access to scheduling operations.
It complements the existing FastAPI REST endpoints with:
- Lower latency through binary serialization (Protobuf)
- Streaming RPCs for large datasets
- Bidirectional communication support
- Strong typing with Protobuf schemas

Architecture:
- server.py: gRPC server configuration and startup
- services.py: Service implementations (Schedule, Assignment, Person RPCs)
- interceptors.py: Authentication, logging, error handling
- converters.py: Protobuf <-> Pydantic message conversion

Usage:
    from app.grpc.server import start_grpc_server, stop_grpc_server

    # Start gRPC server on port 50051
    server = start_grpc_server(port=50051)

    # Stop server gracefully
    stop_grpc_server(server)

Security:
- JWT authentication via metadata (similar to HTTP Authorization header)
- Rate limiting per client
- TLS support for production deployments
- Audit logging for all operations

See docs/grpc/README.md for client integration examples.
"""

from app.grpc.server import start_grpc_server, stop_grpc_server

__all__ = [
    "start_grpc_server",
    "stop_grpc_server",
]
