"""Person data caching strategies.

Caches person and related data with intelligent invalidation.
"""

import json
import logging
from typing import Optional

from app.cache.cache_manager import get_cache_manager

logger = logging.getLogger(__name__)


class PersonCache:
    """Cache for person data."""

    def __init__(self):
        """Initialize person cache."""
        self.cache = get_cache_manager()
        self.ttl = 7200  # 2 hours - person data changes infrequently

    async def get_person(self, person_id: str) -> dict | None:
        """Get cached person data.

        Args:
            person_id: Person ID

        Returns:
            Cached person data or None
        """
        key = f"person:{person_id}"
        cached = await self.cache.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def set_person(
        self,
        person_id: str,
        person_data: dict,
        ttl: int | None = None,
    ) -> None:
        """Cache person data.

        Args:
            person_id: Person ID
            person_data: Person data
            ttl: Time to live in seconds
        """
        key = f"person:{person_id}"
        await self.cache.set(key, json.dumps(person_data), ttl or self.ttl)

    async def get_persons_by_type(self, person_type: str) -> list | None:
        """Get cached persons by type.

        Args:
            person_type: Person type (resident, faculty, etc.)

        Returns:
            Cached persons list or None
        """
        key = f"persons_by_type:{person_type}"
        cached = await self.cache.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def set_persons_by_type(
        self,
        person_type: str,
        persons: list,
        ttl: int | None = None,
    ) -> None:
        """Cache persons by type.

        Args:
            person_type: Person type
            persons: List of persons
            ttl: Time to live in seconds
        """
        key = f"persons_by_type:{person_type}"
        await self.cache.set(key, json.dumps(persons), ttl or self.ttl)

    async def get_person_preferences(self, person_id: str) -> dict | None:
        """Get cached person preferences.

        Args:
            person_id: Person ID

        Returns:
            Cached preferences or None
        """
        key = f"person_prefs:{person_id}"
        cached = await self.cache.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def set_person_preferences(
        self,
        person_id: str,
        preferences: dict,
        ttl: int | None = None,
    ) -> None:
        """Cache person preferences.

        Args:
            person_id: Person ID
            preferences: Preferences data
            ttl: Time to live in seconds
        """
        key = f"person_prefs:{person_id}"
        await self.cache.set(key, json.dumps(preferences), ttl or self.ttl)

    async def invalidate_person(self, person_id: str) -> int:
        """Invalidate all cache for a person.

        Args:
            person_id: Person ID

        Returns:
            Number of keys invalidated
        """
        keys_to_delete = [
            f"person:{person_id}",
            f"person_prefs:{person_id}",
        ]

        count = await self.cache.delete(*keys_to_delete)

        # Also invalidate person type lists
        count += await self.cache.invalidate_pattern("persons_by_type:*")

        logger.info(f"Invalidated {count} person cache entries for {person_id}")
        return count

    async def invalidate_all_persons(self) -> int:
        """Invalidate all person caches.

        Returns:
            Number of keys invalidated
        """
        patterns = [
            "person:*",
            "person_prefs:*",
            "persons_by_type:*",
        ]

        total = 0
        for pattern in patterns:
            total += await self.cache.invalidate_pattern(pattern)

        logger.info(f"Invalidated {total} person cache entries")
        return total


# Global instance
_person_cache: PersonCache | None = None


def get_person_cache() -> PersonCache:
    """Get global person cache instance.

    Returns:
        PersonCache singleton
    """
    global _person_cache
    if _person_cache is None:
        _person_cache = PersonCache()
    return _person_cache
