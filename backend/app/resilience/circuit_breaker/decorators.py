"""
Circuit Breaker Decorators.

Provides convenient decorators for applying circuit breakers to functions:

1. @circuit_breaker - Basic decorator for functions
2. @async_circuit_breaker - Decorator for async functions
3. Automatic registration with global registry
4. Fallback support via decorator parameters
"""

import asyncio
import functools
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from app.resilience.circuit_breaker.registry import get_registry

logger = logging.getLogger(__name__)

T = TypeVar("T")


def circuit_breaker(
    name: str | None = None,
    failure_threshold: int = 5,
    success_threshold: int = 2,
    timeout_seconds: float = 60.0,
    call_timeout_seconds: float | None = None,
    excluded_exceptions: tuple[type[Exception], ...] | None = None,
    fallback: Callable | None = None,
):
    """
    Decorator to protect a function with a circuit breaker.

    Automatically registers a circuit breaker with the global registry
    and wraps the function to use it.

    Args:
        name: Breaker name (defaults to function name)
        failure_threshold: Failures before opening circuit
        success_threshold: Successes to close from half-open
        timeout_seconds: Recovery timeout
        call_timeout_seconds: Individual call timeout
        excluded_exceptions: Exceptions to exclude from failure count
        fallback: Fallback function when circuit is open

    Example:
        @circuit_breaker(
            name="database_query",
            failure_threshold=3,
            timeout_seconds=30,
        )
        def query_database(query: str):
            return db.execute(query)

        # With fallback
        def cached_fallback(*args, **kwargs):
            return get_from_cache()

        @circuit_breaker(
            name="external_api",
            fallback=cached_fallback,
        )
        def call_api(endpoint: str):
            return requests.get(endpoint)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        breaker_name = name or func.__name__
        registry = get_registry()

        # Register breaker if not already registered
        if not registry.exists(breaker_name):
            registry.register(
                breaker_name,
                failure_threshold=failure_threshold,
                success_threshold=success_threshold,
                timeout_seconds=timeout_seconds,
                call_timeout_seconds=call_timeout_seconds,
                excluded_exceptions=excluded_exceptions,
                fallback_function=fallback,
            )

        breaker = registry.get(breaker_name)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return breaker.call(func, *args, **kwargs)

        # Attach breaker for introspection
        wrapper._circuit_breaker = breaker  # type: ignore
        wrapper._circuit_breaker_name = breaker_name  # type: ignore

        return wrapper

    return decorator


def async_circuit_breaker(
    name: str | None = None,
    failure_threshold: int = 5,
    success_threshold: int = 2,
    timeout_seconds: float = 60.0,
    call_timeout_seconds: float | None = None,
    excluded_exceptions: tuple[type[Exception], ...] | None = None,
    fallback: Callable | None = None,
):
    """
    Decorator to protect an async function with a circuit breaker.

    Args:
        name: Breaker name (defaults to function name)
        failure_threshold: Failures before opening circuit
        success_threshold: Successes to close from half-open
        timeout_seconds: Recovery timeout
        call_timeout_seconds: Individual call timeout
        excluded_exceptions: Exceptions to exclude from failure count
        fallback: Fallback function when circuit is open (can be sync or async)

    Example:
        @async_circuit_breaker(
            name="async_database",
            failure_threshold=3,
            timeout_seconds=30,
            call_timeout_seconds=5.0,
        )
        async def query_database_async(query: str):
            async with db.connection() as conn:
                return await conn.execute(query)

        # With async fallback
        async def async_cached_fallback(*args, **kwargs):
            return await get_from_cache_async()

        @async_circuit_breaker(
            name="external_api_async",
            fallback=async_cached_fallback,
        )
        async def call_api_async(endpoint: str):
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint)
                return response.json()
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(
                "@async_circuit_breaker can only be applied to async functions. "
                "Use @circuit_breaker for sync functions."
            )

        breaker_name = name or func.__name__
        registry = get_registry()

        # Register breaker if not already registered
        if not registry.exists(breaker_name):
            registry.register(
                breaker_name,
                failure_threshold=failure_threshold,
                success_threshold=success_threshold,
                timeout_seconds=timeout_seconds,
                call_timeout_seconds=call_timeout_seconds,
                excluded_exceptions=excluded_exceptions,
                fallback_function=fallback,
            )

        breaker = registry.get(breaker_name)

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await breaker.call_async(func, *args, **kwargs)

        # Attach breaker for introspection
        wrapper._circuit_breaker = breaker  # type: ignore
        wrapper._circuit_breaker_name = breaker_name  # type: ignore

        return wrapper

    return decorator


def with_circuit_breaker(breaker_name: str):
    """
    Decorator to use an existing circuit breaker.

    Looks up the breaker from the registry by name.

    Args:
        breaker_name: Name of registered breaker

    Example:
        # First, register the breaker
        registry = get_registry()
        registry.register("shared_api", failure_threshold=3)

        # Then use it with multiple functions
        @with_circuit_breaker("shared_api")
        def api_call_1():
            return call_endpoint_1()

        @with_circuit_breaker("shared_api")
        def api_call_2():
            return call_endpoint_2()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        registry = get_registry()

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            breaker = registry.get(breaker_name)
            return breaker.call(func, *args, **kwargs)

        wrapper._circuit_breaker_name = breaker_name  # type: ignore

        return wrapper

    return decorator


def with_async_circuit_breaker(breaker_name: str):
    """
    Decorator to use an existing circuit breaker with async functions.

    Args:
        breaker_name: Name of registered breaker

    Example:
        # First, register the breaker
        registry = get_registry()
        registry.register("shared_database", failure_threshold=5)

        # Then use it with multiple async functions
        @with_async_circuit_breaker("shared_database")
        async def db_query_1():
            return await execute_query_1()

        @with_async_circuit_breaker("shared_database")
        async def db_query_2():
            return await execute_query_2()
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(
                "@with_async_circuit_breaker can only be applied to async functions."
            )

        registry = get_registry()

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            breaker = registry.get(breaker_name)
            return await breaker.call_async(func, *args, **kwargs)

        wrapper._circuit_breaker_name = breaker_name  # type: ignore

        return wrapper

    return decorator


def get_breaker_from_function(func: Callable) -> Any | None:
    """
    Get the circuit breaker attached to a decorated function.

    Args:
        func: Decorated function

    Returns:
        The circuit breaker, or None if not decorated

    Example:
        @circuit_breaker(name="test")
        def my_func():
            pass

        breaker = get_breaker_from_function(my_func)
        print(breaker.get_status())
    """
    return getattr(func, "_circuit_breaker", None)


def get_breaker_name_from_function(func: Callable) -> str | None:
    """
    Get the circuit breaker name from a decorated function.

    Args:
        func: Decorated function

    Returns:
        The breaker name, or None if not decorated
    """
    return getattr(func, "_circuit_breaker_name", None)
