"""
Request correlation tracking package.

Provides comprehensive correlation tracking for distributed request tracing:

- **Context Management**: Thread-safe correlation context using contextvars
- **Middleware**: FastAPI middleware for automatic correlation tracking
- **Propagation**: Utilities for propagating context to services and tasks
- **Logging Integration**: Automatic correlation ID injection in logs

Quick Start:
-----------

1. Add middleware to FastAPI app:

    from app.correlation import CorrelationMiddleware

    app.add_middleware(CorrelationMiddleware)

2. Use correlation in route handlers:

    from fastapi import Request
    from app.correlation import get_correlation_context

    @app.get("/example")
    async def example(request: Request):
        context = get_correlation_context(request)
        logger.info(f"Processing request {context.correlation_id}")

3. Propagate to external services:

    from app.correlation import get_propagation_headers

    headers = get_propagation_headers()
    response = await httpx.get("https://api.example.com", headers=headers)

4. Use in background tasks:

    from app.correlation import with_correlation

    @with_correlation
    async def process_data():
        logger.info("Processing...")  # Includes correlation IDs

Key Concepts:
------------

- **Correlation ID**: Unique ID for entire request chain (persists across services)
- **Request ID**: Unique ID for specific request
- **Parent ID**: ID of parent request in chain
- **Request Chain**: Full path of requests from root to current
- **Request Depth**: How deep in the chain (0 for root)

Headers:
-------

- X-Correlation-ID: Correlation identifier for request chain
- X-Request-ID: Unique identifier for this request
- X-Parent-ID: Parent request identifier (if nested)
- X-Request-Depth: Depth in request chain
- X-User-ID: User identifier (if authenticated)
"""

from app.correlation.context import (
    CorrelationContext,
    CorrelationContextManager,
    clear_context,
    generate_correlation_id,
    generate_request_id,
    get_context,
    get_correlation_id,
    get_parent_id,
    get_request_chain,
    get_request_depth,
    get_request_id,
    get_user_id,
    initialize_context,
    set_correlation_id,
    set_parent_id,
    set_request_chain,
    set_request_depth,
    set_request_id,
    set_user_id,
)
from app.correlation.middleware import (
    CorrelationMiddleware,
    UserContextMiddleware,
    add_correlation_headers,
    get_correlation_context,
)
from app.correlation.propagation import (
    CorrelatedHTTPXClient,
    CorrelationLogAdapter,
    HTTPClientPropagation,
    create_child_context,
    get_correlation_logger,
    get_propagation_headers,
    inject_correlation_context,
    with_correlation,
)

__all__ = [
    # Context
    "CorrelationContext",
    "CorrelationContextManager",
    "get_context",
    "get_correlation_id",
    "get_request_id",
    "get_parent_id",
    "get_user_id",
    "get_request_depth",
    "get_request_chain",
    "set_correlation_id",
    "set_request_id",
    "set_parent_id",
    "set_user_id",
    "set_request_depth",
    "set_request_chain",
    "initialize_context",
    "clear_context",
    "generate_correlation_id",
    "generate_request_id",
    # Middleware
    "CorrelationMiddleware",
    "UserContextMiddleware",
    "get_correlation_context",
    "add_correlation_headers",
    # Propagation
    "get_propagation_headers",
    "with_correlation",
    "inject_correlation_context",
    "create_child_context",
    "HTTPClientPropagation",
    "CorrelatedHTTPXClient",
    "CorrelationLogAdapter",
    "get_correlation_logger",
]
