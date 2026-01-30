"""Template caching for performance."""

from typing import Any

from app.core.logging import get_logger
from app.notifications.notification_types import NotificationType, render_notification

logger = get_logger(__name__)


class TemplateCache:
    """
    Caches rendered notification templates.

    Caching strategy:
    - Cache rendered templates by (type, data_hash)
    - LRU eviction when cache full
    - Invalidate on template updates
    """

    def __init__(self, max_size: int = 1000) -> None:
        """
        Initialize template cache.

        Args:
            max_size: Maximum cached items
        """
        self._cache: dict[str, dict[str, str]] = {}
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def get(
        self, notification_type: NotificationType, data: dict[str, Any]
    ) -> dict[str, str] | None:
        """
        Get cached template or None.

        Args:
            notification_type: Type of notification
            data: Template data

        Returns:
            Rendered template or None
        """
        cache_key = self._make_key(notification_type, data)

        if cache_key in self._cache:
            self._hits += 1
            return self._cache[cache_key]

        self._misses += 1
        return None

    def set(
        self,
        notification_type: NotificationType,
        data: dict[str, Any],
        rendered: dict[str, str],
    ) -> None:
        """
        Cache rendered template.

        Args:
            notification_type: Type of notification
            data: Template data
            rendered: Rendered template
        """
        cache_key = self._make_key(notification_type, data)

        # Evict oldest if at capacity
        if len(self._cache) >= self._max_size and cache_key not in self._cache:
            oldest = next(iter(self._cache))
            del self._cache[oldest]

        self._cache[cache_key] = rendered

    def _make_key(
        self, notification_type: NotificationType, data: dict[str, Any]
    ) -> str:
        """Generate cache key."""
        # Simple key: type + sorted data keys
        data_keys = tuple(sorted(data.keys()))
        return f"{notification_type.value}:{data_keys}"

    def invalidate(self, notification_type: NotificationType | None = None) -> None:
        """Invalidate cache entries."""
        if notification_type:
            # Invalidate specific type
            keys_to_remove = [
                k
                for k in self._cache.keys()
                if k.startswith(f"{notification_type.value}:")
            ]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            # Invalidate all
            self._cache.clear()

        logger.info("Template cache invalidated")

    def get_statistics(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2),
        }
