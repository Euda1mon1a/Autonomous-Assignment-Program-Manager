"""Async utility functions for coroutine management."""

import asyncio
import functools
import time
from typing import Any, Callable, Coroutine, TypeVar

T = TypeVar("T")


async def run_with_timeout(coro: Coroutine[Any, Any, T], timeout: float) -> T:
    """
    Run a coroutine with a timeout.

    Args:
        coro: Coroutine to run
        timeout: Timeout in seconds

    Returns:
        Result of the coroutine

    Raises:
        asyncio.TimeoutError: If coroutine exceeds timeout
    """
    return await asyncio.wait_for(coro, timeout=timeout)


async def gather_with_errors(*coros: Coroutine[Any, Any, Any]) -> list[Any]:
    """
    Gather coroutines, catching exceptions instead of failing fast.

    Returns results or exceptions for each coroutine.

    Args:
        *coros: Coroutines to gather

    Returns:
        List of results or exceptions (Exception objects for failed coroutines)
    """
    results = await asyncio.gather(*coros, return_exceptions=True)
    return list(results)


async def retry_async(
    coro_func: Callable[[], Coroutine[Any, Any, T]],
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
) -> T:
    """
    Retry an async function with exponential backoff.

    Args:
        coro_func: Callable that returns a coroutine (to allow retries)
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for each retry

    Returns:
        Result of the coroutine

    Raises:
        Exception: The last exception if all retries fail
    """
    last_exception = None
    current_delay = delay

    for attempt in range(max_retries + 1):
        try:
            return await coro_func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                await asyncio.sleep(current_delay)
                current_delay *= backoff
            else:
                raise last_exception


def async_cache(ttl: int):
    """
    Decorator to cache async function results with time-to-live.

    Args:
        ttl: Time-to-live in seconds

    Returns:
        Decorator function
    """

    def decorator(
        func: Callable[..., Coroutine[Any, Any, T]],
    ) -> Callable[..., Coroutine[Any, Any, T]]:
        cache: dict[str, tuple[T, float]] = {}

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Create cache key from args and kwargs
            cache_key = str((args, tuple(sorted(kwargs.items()))))

            # Check if cached value exists and is still valid
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if time.time() - timestamp < ttl:
                    return result

            # Call function and cache result
            result = await func(*args, **kwargs)
            cache[cache_key] = (result, time.time())

            return result

        # Add cache clearing function
        wrapper.clear_cache = lambda: cache.clear()  # type: ignore

        return wrapper

    return decorator
