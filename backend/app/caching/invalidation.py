"""
Cache invalidation service.

Provides intelligent cache invalidation strategies:
- Event-based invalidation
- Pattern-based invalidation
- Tag-based invalidation
- Time-based invalidation (TTL)
- Cascade invalidation (invalidate related entries)

Invalidation events can be triggered by:
- Database updates
- Admin actions
- Scheduled tasks
- External webhooks
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from app.caching.http_cache import HTTPCache

logger = logging.getLogger(__name__)


class InvalidationReason(str, Enum):
    """
    Reason for cache invalidation.

    Used for logging and metrics to understand
    why caches are being invalidated.
    """

    MANUAL = "manual"  # Manual invalidation (admin action)
    UPDATE = "update"  # Resource was updated
    DELETE = "delete"  # Resource was deleted
    CREATE = "create"  # Related resource was created
    EXPIRED = "expired"  # TTL expired
    POLICY = "policy"  # Policy-based invalidation
    CASCADE = "cascade"  # Cascading invalidation from related resource
    ERROR = "error"  # Error recovery


@dataclass
class InvalidationEvent:
    """
    Cache invalidation event.

    Represents a single cache invalidation with metadata
    for tracking and debugging.

    Example:
        event = InvalidationEvent(
            resource="users",
            resource_id="123",
            reason=InvalidationReason.UPDATE,
            patterns=["/api/users/123", "/api/users"]
        )
    """

    resource: str  # Resource type (e.g., "users", "schedules")
    resource_id: Optional[str] = None  # Specific resource ID
    reason: InvalidationReason = InvalidationReason.MANUAL
    patterns: list[str] = field(default_factory=list)  # Cache key patterns to invalidate
    tags: list[str] = field(default_factory=list)  # Cache tags to invalidate
    cascade: bool = False  # Whether to cascade to related resources
    metadata: dict[str, Any] = field(default_factory=dict)  # Additional context
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Generate patterns if not provided."""
        if not self.patterns and self.resource:
            # Generate default patterns
            self.patterns = self._generate_default_patterns()

    def _generate_default_patterns(self) -> list[str]:
        """
        Generate default invalidation patterns based on resource.

        Returns:
            List of cache key patterns
        """
        patterns = []

        # Pattern for resource collection
        patterns.append(f"/api/{self.resource}*")

        # Pattern for specific resource
        if self.resource_id:
            patterns.append(f"/api/{self.resource}/{self.resource_id}*")

        return patterns


class CacheInvalidator:
    """
    Cache invalidation service.

    Manages cache invalidation with support for:
    - Pattern-based invalidation
    - Event-driven invalidation
    - Cascade invalidation
    - Invalidation hooks

    Example:
        invalidator = CacheInvalidator()

        # Invalidate single resource
        await invalidator.invalidate_resource("users", "123")

        # Invalidate with event
        event = InvalidationEvent(
            resource="schedules",
            reason=InvalidationReason.UPDATE,
            cascade=True
        )
        await invalidator.invalidate(event)

        # Register invalidation hook
        async def on_user_update(event: InvalidationEvent):
            # Custom invalidation logic
            pass

        invalidator.register_hook("users", on_user_update)
    """

    def __init__(self, http_cache: Optional[HTTPCache] = None):
        """
        Initialize cache invalidator.

        Args:
            http_cache: HTTP cache instance (creates default if not provided)
        """
        self.http_cache = http_cache or HTTPCache()
        self._hooks: dict[str, list[Callable]] = {}
        self._invalidation_count = 0
        self._last_invalidation: Optional[datetime] = None

    async def invalidate(self, event: InvalidationEvent) -> int:
        """
        Invalidate cache based on event.

        Args:
            event: Invalidation event

        Returns:
            Number of cache entries invalidated

        Example:
            event = InvalidationEvent(
                resource="users",
                resource_id="123",
                reason=InvalidationReason.UPDATE
            )
            count = await invalidator.invalidate(event)
        """
        total_invalidated = 0

        logger.info(
            f"Cache invalidation: resource={event.resource} "
            f"id={event.resource_id} reason={event.reason.value}"
        )

        # Invalidate by patterns
        for pattern in event.patterns:
            count = await self.http_cache.invalidate_pattern(pattern)
            total_invalidated += count
            logger.debug(f"Invalidated {count} entries for pattern: {pattern}")

        # Run hooks
        await self._run_hooks(event)

        # Update metrics
        self._invalidation_count += 1
        self._last_invalidation = datetime.utcnow()

        logger.info(f"Total invalidated: {total_invalidated} entries")
        return total_invalidated

    async def invalidate_resource(
        self,
        resource: str,
        resource_id: Optional[str] = None,
        reason: InvalidationReason = InvalidationReason.MANUAL,
        cascade: bool = False,
    ) -> int:
        """
        Invalidate cache for a specific resource.

        Args:
            resource: Resource type (e.g., "users", "schedules")
            resource_id: Optional specific resource ID
            reason: Reason for invalidation
            cascade: Whether to cascade to related resources

        Returns:
            Number of entries invalidated

        Example:
            # Invalidate all users
            await invalidator.invalidate_resource("users")

            # Invalidate specific user
            await invalidator.invalidate_resource("users", "123")

            # Invalidate with cascade
            await invalidator.invalidate_resource("schedules", "456", cascade=True)
        """
        event = InvalidationEvent(
            resource=resource,
            resource_id=resource_id,
            reason=reason,
            cascade=cascade,
        )

        count = await self.invalidate(event)

        # Handle cascade invalidation
        if cascade:
            cascade_count = await self._cascade_invalidate(event)
            count += cascade_count

        return count

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching a pattern.

        Args:
            pattern: Cache key pattern

        Returns:
            Number of entries invalidated

        Example:
            # Invalidate all user endpoints
            await invalidator.invalidate_pattern("/api/users/*")

            # Invalidate specific version
            await invalidator.invalidate_pattern("/api/v1/*")
        """
        return await self.http_cache.invalidate_pattern(pattern)

    async def invalidate_all(self) -> int:
        """
        Invalidate all cached responses.

        Returns:
            Number of entries invalidated

        Example:
            count = await invalidator.invalidate_all()
        """
        logger.warning("Invalidating ALL cache entries")
        count = await self.http_cache.clear()
        self._invalidation_count += 1
        self._last_invalidation = datetime.utcnow()
        return count

    def register_hook(
        self,
        resource: str,
        hook: Callable[[InvalidationEvent], Any],
    ) -> None:
        """
        Register invalidation hook for a resource.

        Hooks are called when a resource is invalidated,
        allowing for custom invalidation logic.

        Args:
            resource: Resource type
            hook: Async function to call on invalidation

        Example:
            async def on_user_invalidate(event: InvalidationEvent):
                # Invalidate user's related caches
                await invalidator.invalidate_pattern(f"/api/schedules?user={event.resource_id}")

            invalidator.register_hook("users", on_user_invalidate)
        """
        if resource not in self._hooks:
            self._hooks[resource] = []

        self._hooks[resource].append(hook)
        logger.debug(f"Registered invalidation hook for resource: {resource}")

    def unregister_hook(
        self,
        resource: str,
        hook: Callable[[InvalidationEvent], Any],
    ) -> bool:
        """
        Unregister invalidation hook.

        Args:
            resource: Resource type
            hook: Hook function to remove

        Returns:
            True if hook was found and removed
        """
        if resource not in self._hooks:
            return False

        try:
            self._hooks[resource].remove(hook)
            logger.debug(f"Unregistered invalidation hook for resource: {resource}")
            return True
        except ValueError:
            return False

    async def _run_hooks(self, event: InvalidationEvent) -> None:
        """
        Run all registered hooks for an event.

        Args:
            event: Invalidation event
        """
        hooks = self._hooks.get(event.resource, [])

        for hook in hooks:
            try:
                # Call hook (may be sync or async)
                result = hook(event)

                # Await if coroutine
                if hasattr(result, "__await__"):
                    await result

            except Exception as e:
                logger.error(
                    f"Error running invalidation hook for {event.resource}: {e}",
                    exc_info=True,
                )

    async def _cascade_invalidate(self, event: InvalidationEvent) -> int:
        """
        Cascade invalidation to related resources.

        This implements common relationships. Override or register
        hooks for custom cascade logic.

        Args:
            event: Original invalidation event

        Returns:
            Number of entries invalidated
        """
        total_invalidated = 0

        # Define cascade relationships
        # Format: {resource: [related_resources]}
        cascade_map = {
            "users": ["schedules", "assignments", "swaps"],
            "schedules": ["assignments", "blocks"],
            "assignments": ["blocks"],
            "rotations": ["assignments"],
        }

        related_resources = cascade_map.get(event.resource, [])

        for related_resource in related_resources:
            # Generate patterns for related resource
            patterns = []

            if event.resource_id:
                # Specific resource - invalidate related queries
                patterns.append(f"/api/{related_resource}?{event.resource}={event.resource_id}")
                patterns.append(f"/api/{related_resource}?{event.resource}_id={event.resource_id}")

            # Invalidate collection (might be affected)
            patterns.append(f"/api/{related_resource}")

            for pattern in patterns:
                count = await self.http_cache.invalidate_pattern(pattern)
                total_invalidated += count

                if count > 0:
                    logger.debug(
                        f"Cascade invalidated {count} entries for "
                        f"{related_resource} (from {event.resource})"
                    )

        return total_invalidated

    def get_stats(self) -> dict[str, Any]:
        """
        Get invalidation statistics.

        Returns:
            Dictionary with invalidation metrics

        Example:
            stats = invalidator.get_stats()
            print(f"Total invalidations: {stats['total_invalidations']}")
        """
        return {
            "total_invalidations": self._invalidation_count,
            "last_invalidation": (
                self._last_invalidation.isoformat() if self._last_invalidation else None
            ),
            "registered_hooks": {
                resource: len(hooks) for resource, hooks in self._hooks.items()
            },
        }


# Global invalidator instance
_invalidator: Optional[CacheInvalidator] = None


def get_invalidator() -> CacheInvalidator:
    """
    Get global cache invalidator instance.

    Returns:
        CacheInvalidator singleton

    Example:
        invalidator = get_invalidator()
        await invalidator.invalidate_resource("users", "123")
    """
    global _invalidator

    if _invalidator is None:
        _invalidator = CacheInvalidator()

    return _invalidator
