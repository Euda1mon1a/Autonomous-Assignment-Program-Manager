"""ACGME compliance calculation caching.

Caches expensive compliance calculations with smart invalidation.
"""

import hashlib
import json
import logging
from datetime import date, timedelta
from typing import Optional

from app.cache.cache_manager import get_cache_manager

logger = logging.getLogger(__name__)


class ComplianceCache:
    """Cache for ACGME compliance calculations."""

    def __init__(self):
        """Initialize compliance cache."""
        self.cache = get_cache_manager()
        self.ttl = 1800  # 30 minutes

    async def get_work_hours(
        self,
        person_id: str,
        week_start: date,
    ) -> dict | None:
        """Get cached work hours for a week.

        Args:
            person_id: Person ID
            week_start: Start date of week

        Returns:
            Cached work hours or None
        """
        key = f"work_hours:{person_id}:{week_start}"
        cached = await self.cache.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def set_work_hours(
        self,
        person_id: str,
        week_start: date,
        hours_data: dict,
    ) -> None:
        """Cache work hours calculation.

        Args:
            person_id: Person ID
            week_start: Start date of week
            hours_data: Work hours data
        """
        key = f"work_hours:{person_id}:{week_start}"
        await self.cache.set(key, json.dumps(hours_data), self.ttl)

    async def get_rolling_4week_hours(
        self,
        person_id: str,
        end_date: date,
    ) -> dict | None:
        """Get cached rolling 4-week hours.

        Args:
            person_id: Person ID
            end_date: End date for calculation

        Returns:
            Cached hours or None
        """
        key = f"rolling_4week:{person_id}:{end_date}"
        cached = await self.cache.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def set_rolling_4week_hours(
        self,
        person_id: str,
        end_date: date,
        hours_data: dict,
    ) -> None:
        """Cache rolling 4-week hours.

        Args:
            person_id: Person ID
            end_date: End date
            hours_data: Hours data
        """
        key = f"rolling_4week:{person_id}:{end_date}"
        await self.cache.set(key, json.dumps(hours_data), self.ttl)

    async def get_one_in_seven(
        self,
        person_id: str,
        period_start: date,
    ) -> dict | None:
        """Get cached 1-in-7 compliance check.

        Args:
            person_id: Person ID
            period_start: Period start date

        Returns:
            Cached compliance data or None
        """
        key = f"one_in_seven:{person_id}:{period_start}"
        cached = await self.cache.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def set_one_in_seven(
        self,
        person_id: str,
        period_start: date,
        compliance_data: dict,
    ) -> None:
        """Cache 1-in-7 compliance check.

        Args:
            person_id: Person ID
            period_start: Period start date
            compliance_data: Compliance data
        """
        key = f"one_in_seven:{person_id}:{period_start}"
        await self.cache.set(key, json.dumps(compliance_data), self.ttl)

    async def invalidate_person_compliance(self, person_id: str) -> int:
        """Invalidate all compliance cache for a person.

        Args:
            person_id: Person ID

        Returns:
            Number of keys invalidated
        """
        patterns = [
            f"work_hours:{person_id}:*",
            f"rolling_4week:{person_id}:*",
            f"one_in_seven:{person_id}:*",
        ]

        total = 0
        for pattern in patterns:
            total += await self.cache.invalidate_pattern(pattern)

        logger.info(f"Invalidated {total} compliance cache entries for {person_id}")
        return total

    async def invalidate_date_range(
        self,
        start_date: date,
        end_date: date,
    ) -> int:
        """Invalidate compliance cache for date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Number of keys invalidated
        """
        total = 0

        # Invalidate all work hours that might be affected
        current_date = start_date
        while current_date <= end_date:
            # Get week start for this date
            week_start = current_date - timedelta(days=current_date.weekday())

            total += await self.cache.invalidate_pattern(f"work_hours:*:{week_start}")
            total += await self.cache.invalidate_pattern(
                f"rolling_4week:*:{current_date}"
            )
            total += await self.cache.invalidate_pattern(f"one_in_seven:*:{week_start}")

            current_date += timedelta(days=1)

        logger.info(f"Invalidated {total} compliance cache entries for date range")
        return total


# Global instance
_compliance_cache: ComplianceCache | None = None


def get_compliance_cache() -> ComplianceCache:
    """Get global compliance cache instance.

    Returns:
        ComplianceCache singleton
    """
    global _compliance_cache
    if _compliance_cache is None:
        _compliance_cache = ComplianceCache()
    return _compliance_cache
