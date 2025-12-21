"""
Correlation middleware for FastAPI.

Handles correlation tracking for incoming HTTP requests:
- Extracts correlation headers from requests
- Generates new IDs if not present
- Propagates correlation context throughout request lifecycle
- Adds correlation headers to responses
- Integrates with logging
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.correlation.context import (
    CorrelationContext,
    clear_context,
    generate_correlation_id,
    generate_request_id,
    get_context,
    initialize_context,
    set_user_id,
)

logger = logging.getLogger(__name__)


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle request correlation tracking.

    Features:
    - Accepts X-Correlation-ID from client or generates new one
    - Generates X-Request-ID for each request
    - Supports X-Parent-ID for request chain tracking
    - Propagates correlation context to all handlers
    - Adds correlation headers to responses
    - Logs request/response with correlation IDs
    - Measures request duration
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with correlation tracking.

        Args:
            request: Incoming FastAPI request
            call_next: Next middleware/handler in chain

        Returns:
            Response: Response with correlation headers
        """
        start_time = time.perf_counter()

        # Extract correlation headers
        correlation_id = request.headers.get("X-Correlation-ID")
        request_id = request.headers.get("X-Request-ID")
        parent_id = request.headers.get("X-Parent-ID")

        # Generate IDs if not provided
        if not correlation_id:
            correlation_id = generate_correlation_id()

        if not request_id:
            request_id = generate_request_id()

        # Initialize correlation context
        context = initialize_context(
            correlation_id=correlation_id,
            request_id=request_id,
            parent_id=parent_id,
        )

        # Store context in request state for access in route handlers
        request.state.correlation_context = context

        # Log incoming request
        logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra={
                "correlation_id": correlation_id,
                "request_id": request_id,
                "parent_id": parent_id,
                "method": request.method,
                "path": request.url.path,
                "depth": context.depth,
            },
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.perf_counter() - start_time

            # Add correlation headers to response
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Request-ID"] = request_id

            if parent_id:
                response.headers["X-Parent-ID"] = parent_id

            # Log response
            logger.info(
                f"Completed request: {request.method} {request.url.path} "
                f"[{response.status_code}] in {duration:.3f}s",
                extra={
                    "correlation_id": correlation_id,
                    "request_id": request_id,
                    "parent_id": parent_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": duration,
                    "depth": context.depth,
                },
            )

            return response

        except Exception as exc:
            # Calculate duration even on error
            duration = time.perf_counter() - start_time

            # Log error with correlation IDs
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"after {duration:.3f}s: {exc}",
                exc_info=True,
                extra={
                    "correlation_id": correlation_id,
                    "request_id": request_id,
                    "parent_id": parent_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration": duration,
                    "error": str(exc),
                    "depth": context.depth,
                },
            )

            # Re-raise to let error handlers deal with it
            raise

        finally:
            # Clear context after request completes
            clear_context()


class UserContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and set user context from authenticated requests.

    Should be added after authentication middleware.
    Extracts user ID from request.state.user if available.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Extract user ID and add to correlation context.

        Args:
            request: Incoming FastAPI request
            call_next: Next middleware/handler in chain

        Returns:
            Response: Response from next handler
        """
        # Check if user is authenticated
        user = getattr(request.state, "user", None)

        if user:
            # Extract user ID (handle different user object structures)
            user_id = None

            if hasattr(user, "id"):
                user_id = str(user.id)
            elif hasattr(user, "user_id"):
                user_id = str(user.user_id)
            elif isinstance(user, dict):
                user_id = str(user.get("id") or user.get("user_id") or "")

            if user_id:
                set_user_id(user_id)

                logger.debug(
                    f"User context set: {user_id}",
                    extra={
                        "user_id": user_id,
                        "correlation_id": getattr(
                            getattr(request.state, "correlation_context", None),
                            "correlation_id",
                            None,
                        ),
                    },
                )

        return await call_next(request)


def get_correlation_context(request: Request) -> CorrelationContext | None:
    """
    Get correlation context from request.

    Args:
        request: FastAPI request object

    Returns:
        CorrelationContext | None: Correlation context or None if not set
    """
    # Try to get from request state first (set by middleware)
    if hasattr(request.state, "correlation_context"):
        return request.state.correlation_context

    # Fall back to context variables
    return get_context()


def add_correlation_headers(response: Response) -> Response:
    """
    Add correlation headers to an existing response.

    Useful for manually created responses outside normal middleware flow.

    Args:
        response: Response object to add headers to

    Returns:
        Response: Same response with headers added
    """
    context = get_context()

    if context:
        response.headers["X-Correlation-ID"] = context.correlation_id
        response.headers["X-Request-ID"] = context.request_id

        if context.parent_id:
            response.headers["X-Parent-ID"] = context.parent_id

    return response
