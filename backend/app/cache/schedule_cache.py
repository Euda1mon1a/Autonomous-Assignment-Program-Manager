"""Schedule-specific caching strategies.

Optimized caching for schedule data with intelligent invalidation.
"""
import hashlib
import json
import logging
from datetime import date, timedelta
from typing import Any, Optional

from app.cache.cache_manager import get_cache_manager

logger = logging.getLogger(__name__)


class ScheduleCache:
    """Specialized cache for schedule data."""

    def __init__(self):
        """Initialize schedule cache."""
        self.cache = get_cache_manager()
        self.default_ttl = 3600  # 1 hour

    async def get_schedule(
        self,
        start_date: date,
        end_date: date,
        filters: Optional[dict] = None,
    ) -> Optional[dict]:
        """Get cached schedule for date range.

        Args:
            start_date: Schedule start date
            end_date: Schedule end date
            filters: Optional filters (person_id, rotation_id, etc.)

        Returns:
            Cached schedule or None
        """
        key = self._generate_schedule_key(start_date, end_date, filters)
        return await self.cache.get(key)

    async def set_schedule(
        self,
        start_date: date,
        end_date: date,
        schedule_data: dict,
        filters: Optional[dict] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """Cache schedule data.

        Args:
            start_date: Schedule start date
            end_date: Schedule end date
            schedule_data: Schedule data to cache
            filters: Optional filters applied
            ttl: Time to live in seconds
        """
        key = self._generate_schedule_key(start_date, end_date, filters)
        await self.cache.set(key, json.dumps(schedule_data), ttl or self.default_ttl)

    async def get_person_schedule(
        self,
        person_id: str,
        start_date: date,
        end_date: date,
    ) -> Optional[dict]:
        """Get cached schedule for a specific person.

        Args:
            person_id: Person ID
            start_date: Schedule start date
            end_date: Schedule end date

        Returns:
            Cached person schedule or None
        """
        key = f"person_schedule:{person_id}:{start_date}:{end_date}"
        cached = await self.cache.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def set_person_schedule(
        self,
        person_id: str,
        start_date: date,
        end_date: date,
        schedule_data: dict,
        ttl: Optional[int] = None,
    ) -> None:
        """Cache person-specific schedule.

        Args:
            person_id: Person ID
            start_date: Schedule start date
            end_date: Schedule end date
            schedule_data: Schedule data
            ttl: Time to live in seconds
        """
        key = f"person_schedule:{person_id}:{start_date}:{end_date}"
        await self.cache.set(key, json.dumps(schedule_data), ttl or self.default_ttl)

    async def get_rotation_coverage(
        self,
        rotation_id: str,
        target_date: date,
    ) -> Optional[dict]:
        """Get cached rotation coverage for a date.

        Args:
            rotation_id: Rotation ID
            target_date: Date to check

        Returns:
            Cached coverage data or None
        """
        key = f"rotation_coverage:{rotation_id}:{target_date}"
        cached = await self.cache.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def set_rotation_coverage(
        self,
        rotation_id: str,
        target_date: date,
        coverage_data: dict,
        ttl: Optional[int] = None,
    ) -> None:
        """Cache rotation coverage data.

        Args:
            rotation_id: Rotation ID
            target_date: Date
            coverage_data: Coverage data
            ttl: Time to live in seconds
        """
        key = f"rotation_coverage:{rotation_id}:{target_date}"
        await self.cache.set(key, json.dumps(coverage_data), ttl or 1800)  # 30 min

    async def invalidate_schedule(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> int:
        """Invalidate schedule cache for date range.

        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering

        Returns:
            Number of keys invalidated
        """
        if start_date and end_date:
            # Invalidate specific date range
            pattern = f"schedule:*:{start_date}:*:{end_date}:*"
        else:
            # Invalidate all schedules
            pattern = "schedule:*"

        count = await self.cache.invalidate_pattern(pattern)
        logger.info(f"Invalidated {count} schedule cache entries")
        return count

    async def invalidate_person_schedule(self, person_id: str) -> int:
        """Invalidate all schedule cache for a person.

        Args:
            person_id: Person ID

        Returns:
            Number of keys invalidated
        """
        pattern = f"person_schedule:{person_id}:*"
        count = await self.cache.invalidate_pattern(pattern)
        logger.info(f"Invalidated {count} person schedule cache entries for {person_id}")
        return count

    async def invalidate_rotation_coverage(self, rotation_id: str) -> int:
        """Invalidate rotation coverage cache.

        Args:
            rotation_id: Rotation ID

        Returns:
            Number of keys invalidated
        """
        pattern = f"rotation_coverage:{rotation_id}:*"
        count = await self.cache.invalidate_pattern(pattern)
        logger.info(f"Invalidated {count} rotation coverage cache entries")
        return count

    async def invalidate_date_range(
        self,
        start_date: date,
        end_date: date,
    ) -> int:
        """Invalidate all caches that intersect with date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Number of keys invalidated
        """
        total_invalidated = 0

        # Invalidate schedule caches
        total_invalidated += await self.invalidate_schedule(start_date, end_date)

        # Invalidate person schedules in range
        total_invalidated += await self.cache.invalidate_pattern(
            f"person_schedule:*:{start_date}:*"
        )

        # Invalidate rotation coverage in range
        current_date = start_date
        while current_date <= end_date:
            total_invalidated += await self.cache.invalidate_pattern(
                f"rotation_coverage:*:{current_date}"
            )
            current_date += timedelta(days=1)

        logger.info(f"Invalidated {total_invalidated} cache entries for date range")
        return total_invalidated

    async def warm_person_schedule(
        self,
        person_id: str,
        start_date: date,
        num_days: int = 90,
    ) -> None:
        """Pre-warm cache with person schedule data.

        Args:
            person_id: Person ID
            start_date: Start date
            num_days: Number of days to warm
        """
        from app.services.schedule_service import get_person_schedule

        end_date = start_date + timedelta(days=num_days)

        # Fetch and cache schedule
        schedule_data = await get_person_schedule(person_id, start_date, end_date)
        await self.set_person_schedule(person_id, start_date, end_date, schedule_data)

        logger.info(f"Warmed cache for person {person_id}, {num_days} days")

    def _generate_schedule_key(
        self,
        start_date: date,
        end_date: date,
        filters: Optional[dict],
    ) -> str:
        """Generate cache key for schedule query.

        Args:
            start_date: Start date
            end_date: End date
            filters: Optional filters

        Returns:
            Cache key
        """
        # Create deterministic key from parameters
        filter_str = json.dumps(filters or {}, sort_keys=True)
        key_content = f"{start_date}:{end_date}:{filter_str}"
        key_hash = hashlib.sha256(key_content.encode()).hexdigest()[:16]

        return f"schedule:{start_date}:{end_date}:{key_hash}"


# Global instance
_schedule_cache: Optional[ScheduleCache] = None


def get_schedule_cache() -> ScheduleCache:
    """Get global schedule cache instance.

    Returns:
        ScheduleCache singleton
    """
    global _schedule_cache
    if _schedule_cache is None:
        _schedule_cache = ScheduleCache()
    return _schedule_cache
