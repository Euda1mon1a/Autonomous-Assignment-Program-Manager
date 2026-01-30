"""
Context propagation utilities for correlation tracking.

Provides tools to propagate correlation context to:
- HTTP client requests (httpx, aiohttp, requests)
- Background tasks (Celery)
- Database queries
- External service calls
- Logging
"""

import functools
import logging
from collections.abc import Callable
from typing import Any

from app.correlation.context import (
    CorrelationContext,
    get_context,
    initialize_context,
)

logger = logging.getLogger(__name__)


def get_propagation_headers() -> dict[str, str]:
    """
    Get correlation headers for propagating to external services.

    Returns:
        dict[str, str]: Headers containing correlation IDs
    """
    context = get_context()

    if context:
        return context.to_headers()

    return {}


def with_correlation(func: Callable) -> Callable:
    """
    Decorator to propagate correlation context to a function.

    Useful for background tasks, async functions, or any code
    that needs to maintain correlation tracking.

    Usage:
        @with_correlation
        async def process_data():
            # This function will have correlation context
            logger.info("Processing...")  # Will include correlation IDs

        @with_correlation
        def sync_task():
            # Works with sync functions too
            logger.info("Processing...")

    Args:
        func: Function to wrap

    Returns:
        Callable: Wrapped function with correlation context
    """

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Get current context
        context = get_context()

        if context:
            # Context already exists, just call the function
            return await func(*args, **kwargs)

            # No context, check if we have correlation data in kwargs
        correlation_id = kwargs.pop("_correlation_id", None)
        request_id = kwargs.pop("_request_id", None)
        parent_id = kwargs.pop("_parent_id", None)
        user_id = kwargs.pop("_user_id", None)

        # Initialize context if we have data
        if correlation_id or request_id:
            initialize_context(
                correlation_id=correlation_id,
                request_id=request_id,
                parent_id=parent_id,
                user_id=user_id,
            )

        try:
            return await func(*args, **kwargs)
        finally:
            # Don't clear context if it was already set
            pass

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        # Get current context
        context = get_context()

        if context:
            # Context already exists, just call the function
            return func(*args, **kwargs)

            # No context, check if we have correlation data in kwargs
        correlation_id = kwargs.pop("_correlation_id", None)
        request_id = kwargs.pop("_request_id", None)
        parent_id = kwargs.pop("_parent_id", None)
        user_id = kwargs.pop("_user_id", None)

        # Initialize context if we have data
        if correlation_id or request_id:
            initialize_context(
                correlation_id=correlation_id,
                request_id=request_id,
                parent_id=parent_id,
                user_id=user_id,
            )

        try:
            return func(*args, **kwargs)
        finally:
            # Don't clear context if it was already set
            pass

            # Return appropriate wrapper based on function type

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def inject_correlation_context(**extra_kwargs) -> dict[str, Any]:
    """
    Inject correlation context as keyword arguments.

    Useful for passing context to background tasks or external calls.

    Usage:
        # Pass to Celery task
        task.delay(**inject_correlation_context())

        # Pass to function
        process_data(**inject_correlation_context(some_param="value"))

    Args:
        **extra_kwargs: Additional kwargs to merge with context

    Returns:
        dict: Kwargs including correlation context
    """
    context = get_context()

    kwargs = dict(extra_kwargs)

    if context:
        kwargs.update(
            {
                "_correlation_id": context.correlation_id,
                "_request_id": context.request_id,
                "_parent_id": context.parent_id,
                "_user_id": context.user_id,
            }
        )

    return kwargs


class HTTPClientPropagation:
    """
    Mixin for HTTP clients to automatically propagate correlation headers.

    Usage with httpx:
        import httpx
        from app.correlation.propagation import HTTPClientPropagation

        class CorrelatedHTTPClient(HTTPClientPropagation):
            async def make_request(self, url: str):
                headers = self.get_correlation_headers()
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers)
                return response
    """

    def get_correlation_headers(self, base_headers: dict | None = None) -> dict:
        """
        Get headers with correlation context merged.

        Args:
            base_headers: Existing headers to merge with

        Returns:
            dict: Headers including correlation IDs
        """
        headers = dict(base_headers) if base_headers else {}
        headers.update(get_propagation_headers())
        return headers


class CorrelatedHTTPXClient:
    """
    Wrapper for httpx client with automatic correlation propagation.

    Usage:
        async with CorrelatedHTTPXClient() as client:
            response = await client.get("https://api.example.com/data")
            # Request automatically includes correlation headers
    """

    def __init__(self, **client_kwargs) -> None:
        """
        Initialize correlated HTTP client.

        Args:
            **client_kwargs: Arguments to pass to httpx.AsyncClient
        """
        import httpx

        self.client_kwargs = client_kwargs
        self.client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        """Enter async context manager."""
        import httpx

        self.client = httpx.AsyncClient(**self.client_kwargs)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        if self.client:
            await self.client.aclose()

    async def request(self, method: str, url: str, **kwargs):
        """
        Make HTTP request with correlation headers.

        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional arguments for httpx

        Returns:
            Response from httpx
        """
        if not self.client:
            raise RuntimeError(
                "Client not initialized. Use 'async with' context manager."
            )

            # Merge correlation headers
        headers = kwargs.pop("headers", {})
        headers.update(get_propagation_headers())

        return await self.client.request(method, url, headers=headers, **kwargs)

    async def get(self, url: str, **kwargs):
        """GET request with correlation."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs):
        """POST request with correlation."""
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs):
        """PUT request with correlation."""
        return await self.request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs):
        """PATCH request with correlation."""
        return await self.request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs):
        """DELETE request with correlation."""
        return await self.request("DELETE", url, **kwargs)


class CorrelationLogAdapter(logging.LoggerAdapter):
    """
    Logger adapter that automatically includes correlation IDs.

    Usage:
        from app.correlation.propagation import get_correlation_logger

        logger = get_correlation_logger(__name__)
        logger.info("Processing data")  # Automatically includes correlation IDs
    """

    def process(self, msg, kwargs):
        """
        Add correlation IDs to log extra data.

        Args:
            msg: Log message
            kwargs: Log kwargs

        Returns:
            tuple: Processed message and kwargs
        """
        context = get_context()

        if context:
            extra = kwargs.get("extra", {})
            extra.update(
                {
                    "correlation_id": context.correlation_id,
                    "request_id": context.request_id,
                    "parent_id": context.parent_id,
                    "user_id": context.user_id,
                    "depth": context.depth,
                }
            )
            kwargs["extra"] = extra

        return msg, kwargs


def get_correlation_logger(name: str) -> CorrelationLogAdapter:
    """
    Get logger with automatic correlation ID injection.

    Args:
        name: Logger name (usually __name__)

    Returns:
        CorrelationLogAdapter: Logger that includes correlation IDs
    """
    base_logger = logging.getLogger(name)
    return CorrelationLogAdapter(base_logger, {})


def create_child_context() -> CorrelationContext:
    """
    Create a child correlation context for nested operations.

    Useful for creating sub-requests or background tasks that should
    maintain the correlation chain but have their own request ID.

    Returns:
        CorrelationContext: New child context

    Example:
        # In a request handler
        parent_context = get_context()

        # Create child context for background task
        child_context = create_child_context()

        # Pass to task
        task.delay(
            _correlation_id=child_context.correlation_id,
            _request_id=child_context.request_id,
            _parent_id=child_context.parent_id,
        )
    """
    parent_context = get_context()

    if not parent_context:
        # No parent context, create root context
        return initialize_context()

        # Create child context with same correlation ID but new request ID
    return initialize_context(
        correlation_id=parent_context.correlation_id,
        parent_id=parent_context.request_id,  # Parent's request ID becomes our parent ID
        user_id=parent_context.user_id,
    )

    # Import asyncio for decorator


try:
    import asyncio
except ImportError:
    asyncio = None
