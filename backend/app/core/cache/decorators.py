"""
Caching decorators for easy integration with service functions.

Provides decorators for common caching patterns:
- @cached: Cache function results
- @cache_invalidate: Invalidate cache on function execution
- @cache_warm: Warm cache on application startup

This module provides:
- cached(): Decorator for caching function results
- cache_invalidate(): Decorator for cache invalidation
- cache_warm(): Decorator for cache warming
- invalidate_on_write(): Decorator for write-through invalidation
"""
import asyncio
import functools
import inspect
import logging
from typing import Any, Callable

from app.core.cache.keys import CacheKeyGenerator
from app.core.cache.redis_cache import get_cache

logger = logging.getLogger(__name__)


def cached(
    namespace: str = "default",
    ttl: int = 300,
    key_prefix: str | None = None,
    tags: list[str] | Callable[..., list[str]] | None = None,
    use_l1: bool = True,
    use_l2: bool = True,
    key_builder: Callable[..., str] | None = None
):
    """
    Decorator to cache function results.

    Caches the return value of the decorated function based on its
    arguments. Supports both sync and async functions.

    Args:
        namespace: Cache namespace
        ttl: Time-to-live in seconds
        key_prefix: Optional prefix for cache keys (defaults to function name)
        tags: Static tags or callable that returns tags from function args
        use_l1: Use L1 (memory) cache
        use_l2: Use L2 (Redis) cache
        key_builder: Custom function to build cache key from args

    Returns:
        Decorated function with caching

    Example:
        @cached(namespace="schedule", ttl=300, tags=["schedule"])
        async def get_schedule(user_id: int, date: str):
            return await db.fetch_schedule(user_id, date)

        # With dynamic tags
        @cached(
            namespace="user",
            ttl=600,
            tags=lambda user_id: [f"user:{user_id}"]
        )
        async def get_user_profile(user_id: int):
            return await db.fetch_user(user_id)
    """
    def decorator(func: Callable) -> Callable:
        cache = get_cache(namespace)
        func_name = key_prefix or func.__name__

        # Determine if function is async
        is_async = asyncio.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = _build_cache_key(func_name, args, kwargs)

            # Determine tags
            cache_tags = _resolve_tags(tags, args, kwargs)

            # Try to get from cache
            cached_value = await cache.get(cache_key, use_l1=use_l1, use_l2=use_l2)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func_name}: {cache_key}")
                return cached_value

            # Cache miss - call function
            logger.debug(f"Cache miss for {func_name}: {cache_key}")
            result = await func(*args, **kwargs)

            # Cache the result
            if result is not None:
                await cache.set(
                    cache_key,
                    result,
                    ttl=ttl,
                    tags=cache_tags,
                    use_l1=use_l1,
                    use_l2=use_l2
                )

            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we need to run async cache operations in event loop
            # This is a simplified version - in production, consider using a sync cache
            # or running in a thread pool
            result = func(*args, **kwargs)
            return result

        return async_wrapper if is_async else sync_wrapper

    return decorator


def cache_invalidate(
    namespace: str = "default",
    tags: list[str] | Callable[..., list[str]] | None = None,
    patterns: list[str] | Callable[..., list[str]] | None = None,
    clear_all: bool = False
):
    """
    Decorator to invalidate cache when function executes.

    Invalidates specified cache entries before or after function execution.
    Useful for write operations that modify data.

    Args:
        namespace: Cache namespace to invalidate
        tags: Tags to invalidate (static list or callable)
        patterns: Patterns to invalidate (static list or callable)
        clear_all: Clear entire namespace (use with caution)

    Returns:
        Decorated function with cache invalidation

    Example:
        @cache_invalidate(
            namespace="schedule",
            tags=lambda user_id: [f"user:{user_id}", "schedule"]
        )
        async def update_schedule(user_id: int, schedule_data: dict):
            await db.update_schedule(user_id, schedule_data)

        # Invalidate multiple patterns
        @cache_invalidate(
            namespace="user",
            patterns=lambda user_id: [f"user:{user_id}:*"]
        )
        async def delete_user(user_id: int):
            await db.delete_user(user_id)
    """
    def decorator(func: Callable) -> Callable:
        cache = get_cache(namespace)
        is_async = asyncio.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Invalidate before function execution (for write-through)
            await _invalidate_cache(
                cache,
                tags,
                patterns,
                clear_all,
                args,
                kwargs
            )

            # Execute function
            result = await func(*args, **kwargs)

            # Could also invalidate after if needed
            # await _invalidate_cache(...)

            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Execute function (simplified for sync)
            result = func(*args, **kwargs)
            return result

        return async_wrapper if is_async else sync_wrapper

    return decorator


def cache_warm(
    namespace: str = "default",
    entries_func: Callable[..., dict[str, Any]] | None = None,
    ttl: int = 3600
):
    """
    Decorator to warm cache on function execution.

    Typically used on startup functions to pre-populate cache
    with frequently accessed data.

    Args:
        namespace: Cache namespace
        entries_func: Function that returns {key: value} dict to cache
        ttl: Time-to-live for cached entries

    Returns:
        Decorated function with cache warming

    Example:
        @cache_warm(
            namespace="config",
            entries_func=lambda: load_config_entries(),
            ttl=3600
        )
        async def startup():
            # Initialization code
            pass

        # Or use function's return value
        @cache_warm(namespace="reference", ttl=7200)
        async def load_reference_data():
            # Return dict of {key: value} to cache
            return {
                "countries": await db.get_countries(),
                "states": await db.get_states()
            }
    """
    def decorator(func: Callable) -> Callable:
        cache = get_cache(namespace)
        is_async = asyncio.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Execute function
            result = await func(*args, **kwargs)

            # Determine entries to cache
            if entries_func:
                if asyncio.iscoroutinefunction(entries_func):
                    entries = await entries_func(*args, **kwargs)
                else:
                    entries = entries_func(*args, **kwargs)
            elif isinstance(result, dict):
                entries = result
            else:
                entries = {}

            # Warm cache
            if entries:
                count = await cache.warm(entries, ttl=ttl)
                logger.info(f"Cache warmed with {count} entries in namespace '{namespace}'")

            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return result

        return async_wrapper if is_async else sync_wrapper

    return decorator


def invalidate_on_write(
    namespace: str = "default",
    key_builder: Callable[..., str | list[str]] | None = None,
    invalidate_before: bool = True
):
    """
    Decorator for write-through cache invalidation.

    Invalidates specific cache keys when data is written.
    Ensures cache consistency by invalidating before or after writes.

    Args:
        namespace: Cache namespace
        key_builder: Function to build cache keys from function args
        invalidate_before: Invalidate before (True) or after (False) write

    Returns:
        Decorated function with write-through invalidation

    Example:
        @invalidate_on_write(
            namespace="schedule",
            key_builder=lambda user_id, **kwargs: f"schedule:{user_id}"
        )
        async def update_user_schedule(user_id: int, schedule: dict):
            await db.update(user_id, schedule)

        # Invalidate multiple keys
        @invalidate_on_write(
            namespace="user",
            key_builder=lambda user_id: [
                f"user:{user_id}:profile",
                f"user:{user_id}:settings"
            ]
        )
        async def update_user(user_id: int, data: dict):
            await db.update_user(user_id, data)
    """
    def decorator(func: Callable) -> Callable:
        cache = get_cache(namespace)
        is_async = asyncio.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Build cache keys to invalidate
            if key_builder:
                keys = key_builder(*args, **kwargs)
                if isinstance(keys, str):
                    keys = [keys]
            else:
                keys = []

            # Invalidate before write
            if invalidate_before and keys:
                for key in keys:
                    await cache.delete(key)
                logger.debug(f"Invalidated {len(keys)} cache entries before write")

            # Execute function
            result = await func(*args, **kwargs)

            # Invalidate after write
            if not invalidate_before and keys:
                for key in keys:
                    await cache.delete(key)
                logger.debug(f"Invalidated {len(keys)} cache entries after write")

            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return result

        return async_wrapper if is_async else sync_wrapper

    return decorator


# Helper functions

def _build_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    Build a cache key from function arguments.

    Args:
        func_name: Function name
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Cache key string
    """
    # Combine args and kwargs into a consistent key
    key_parts = [func_name]

    # Add positional args
    for arg in args:
        key_parts.append(str(arg))

    # Add keyword args (sorted for consistency)
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}={v}")

    return ":".join(key_parts)


def _resolve_tags(
    tags: list[str] | Callable | None,
    args: tuple,
    kwargs: dict
) -> list[str]:
    """
    Resolve tags from static list or callable.

    Args:
        tags: Static tags or callable
        args: Function arguments
        kwargs: Function keyword arguments

    Returns:
        List of tag strings
    """
    if tags is None:
        return []

    if callable(tags):
        # Get function signature to map args to parameters
        result = tags(*args, **kwargs)
        return result if isinstance(result, list) else [result]

    return tags


async def _invalidate_cache(
    cache,
    tags: list[str] | Callable | None,
    patterns: list[str] | Callable | None,
    clear_all: bool,
    args: tuple,
    kwargs: dict
) -> None:
    """
    Execute cache invalidation.

    Args:
        cache: Cache instance
        tags: Tags to invalidate
        patterns: Patterns to invalidate
        clear_all: Clear all entries
        args: Function arguments
        kwargs: Function keyword arguments
    """
    if clear_all:
        count = await cache.clear()
        logger.info(f"Cleared all cache entries: {count}")
        return

    # Invalidate by tags
    if tags:
        resolved_tags = _resolve_tags(tags, args, kwargs)
        for tag in resolved_tags:
            count = await cache.invalidate_by_tag(tag)
            logger.debug(f"Invalidated {count} entries for tag '{tag}'")

    # Invalidate by patterns
    if patterns:
        resolved_patterns = (
            patterns(*args, **kwargs) if callable(patterns) else patterns
        )
        if isinstance(resolved_patterns, str):
            resolved_patterns = [resolved_patterns]

        for pattern in resolved_patterns:
            count = await cache.invalidate_by_pattern(pattern)
            logger.debug(f"Invalidated {count} entries for pattern '{pattern}'")


# Utility decorators for specific patterns

def cached_property_async(ttl: int = 300, namespace: str = "default"):
    """
    Decorator for caching async property-like methods.

    Args:
        ttl: Time-to-live in seconds
        namespace: Cache namespace

    Returns:
        Decorated method with caching

    Example:
        class UserService:
            @cached_property_async(ttl=600, namespace="user")
            async def expensive_computation(self, user_id: int):
                return await self._compute(user_id)
    """
    return cached(
        namespace=namespace,
        ttl=ttl,
        use_l1=True,
        use_l2=True
    )


def read_through(
    namespace: str,
    ttl: int = 300,
    tags: list[str] | Callable | None = None
):
    """
    Decorator for read-through caching pattern.

    Automatically caches function results on first call.

    Args:
        namespace: Cache namespace
        ttl: Time-to-live in seconds
        tags: Tags for invalidation

    Returns:
        Decorated function with read-through caching

    Example:
        @read_through(namespace="user", ttl=300, tags=["users"])
        async def get_user(user_id: int):
            return await db.get_user(user_id)
    """
    return cached(
        namespace=namespace,
        ttl=ttl,
        tags=tags,
        use_l1=True,
        use_l2=True
    )


def write_through(
    namespace: str,
    key_builder: Callable[..., str | list[str]]
):
    """
    Decorator for write-through caching pattern.

    Invalidates cache immediately on writes.

    Args:
        namespace: Cache namespace
        key_builder: Function to build cache keys from args

    Returns:
        Decorated function with write-through invalidation

    Example:
        @write_through(
            namespace="user",
            key_builder=lambda user_id, **kw: f"user:{user_id}"
        )
        async def update_user(user_id: int, data: dict):
            await db.update_user(user_id, data)
    """
    return invalidate_on_write(
        namespace=namespace,
        key_builder=key_builder,
        invalidate_before=True
    )
