"""
Cached wrappers for schedule-related services.

Provides Redis-cached versions of expensive schedule operations
including heatmap generation, calendar exports, and schedule queries.

These wrappers add caching on top of existing service implementations
without modifying the original services.
"""

import logging
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.cache import (
    CachePrefix,
    CacheTTL,
    get_service_cache,
    invalidate_schedule_cache,
)
from app.core.config import get_settings
from app.schemas.visualization import (
    CoverageHeatmapResponse,
    HeatmapResponse,
    TimeRangeType,
)
from app.services.calendar_service import CalendarService
from app.services.heatmap_service import HeatmapService

logger = logging.getLogger(__name__)


class CachedHeatmapService:
    """
    Cached wrapper for HeatmapService.

    Caches expensive heatmap generation operations with configurable TTL.
    Falls back to uncached operations when Redis is unavailable.

    Example:
        service = CachedHeatmapService()
        result = service.generate_unified_heatmap(
            db=db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )
    """

    def __init__(self):
        """Initialize cached service with underlying HeatmapService."""
        self._service = HeatmapService()
        self._cache = get_service_cache()
        self._settings = get_settings()

    def _build_heatmap_cache_key(
        self,
        start_date: date,
        end_date: date,
        person_ids: list[UUID] | None,
        rotation_ids: list[UUID] | None,
        include_fmit: bool,
        group_by: str,
    ) -> str:
        """Build a deterministic cache key for heatmap queries."""
        key_parts = [
            CachePrefix.HEATMAP.value,
            "unified",
            start_date.isoformat(),
            end_date.isoformat(),
            group_by,
            str(include_fmit).lower(),
        ]

        if person_ids:
            sorted_ids = sorted(str(pid) for pid in person_ids)
            key_parts.append(f"persons:[{','.join(sorted_ids[:5])}]")

        if rotation_ids:
            sorted_ids = sorted(str(rid) for rid in rotation_ids)
            key_parts.append(f"rotations:[{','.join(sorted_ids[:5])}]")

        return ":".join(key_parts)

    def generate_unified_heatmap(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        person_ids: list[UUID] | None = None,
        rotation_ids: list[UUID] | None = None,
        include_fmit: bool = True,
        group_by: str = "person",
    ) -> HeatmapResponse:
        """
        Generate unified heatmap with caching.

        Caches the result based on query parameters. Cache is invalidated
        when schedule data is modified.

        Args:
            db: Database session
            start_date: Start date for heatmap
            end_date: End date for heatmap
            person_ids: Optional filter by person IDs
            rotation_ids: Optional filter by rotation template IDs
            include_fmit: Whether to include FMIT swap data
            group_by: Group by 'person', 'rotation', 'daily', or 'weekly'

        Returns:
            HeatmapResponse with visualization data
        """
        # Build cache key
        cache_key = self._build_heatmap_cache_key(
            start_date, end_date, person_ids, rotation_ids, include_fmit, group_by
        )

        # Try cache first
        cached_result = self._cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for heatmap: {cache_key}")
            return cached_result

        # Generate heatmap
        result = self._service.generate_unified_heatmap(
            db=db,
            start_date=start_date,
            end_date=end_date,
            person_ids=person_ids,
            rotation_ids=rotation_ids,
            include_fmit=include_fmit,
            group_by=group_by,
        )

        # Cache the result
        ttl = self._settings.CACHE_HEATMAP_TTL
        self._cache.set(cache_key, result, ttl)
        logger.debug(f"Cached heatmap result: {cache_key} (TTL: {ttl}s)")

        return result

    def generate_unified_heatmap_with_time_range(
        self,
        db: Session,
        time_range: TimeRangeType,
        person_ids: list[UUID] | None = None,
        rotation_ids: list[UUID] | None = None,
        include_fmit: bool = True,
        group_by: str = "person",
    ) -> HeatmapResponse:
        """
        Generate unified heatmap with time range specification and caching.

        Args:
            db: Database session
            time_range: Time range specification
            person_ids: Optional filter by person IDs
            rotation_ids: Optional filter by rotation template IDs
            include_fmit: Whether to include FMIT swap data
            group_by: Group by 'person', 'rotation', 'daily', or 'weekly'

        Returns:
            HeatmapResponse with visualization data
        """
        # Calculate date range
        start_date, end_date = self._service.calculate_date_range(time_range)

        # Use the cached unified heatmap method
        return self.generate_unified_heatmap(
            db=db,
            start_date=start_date,
            end_date=end_date,
            person_ids=person_ids,
            rotation_ids=rotation_ids,
            include_fmit=include_fmit,
            group_by=group_by,
        )

    def generate_coverage_heatmap(
        self,
        db: Session,
        start_date: date,
        end_date: date,
    ) -> CoverageHeatmapResponse:
        """
        Generate coverage heatmap with caching.

        Args:
            db: Database session
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            CoverageHeatmapResponse with coverage data and gaps
        """
        cache_key = f"{CachePrefix.COVERAGE.value}:{start_date.isoformat()}:{end_date.isoformat()}"

        # Try cache first
        cached_result = self._cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for coverage heatmap: {cache_key}")
            return cached_result

        # Generate coverage heatmap
        result = self._service.generate_coverage_heatmap(
            db=db,
            start_date=start_date,
            end_date=end_date,
        )

        # Cache the result
        ttl = self._settings.CACHE_HEATMAP_TTL
        self._cache.set(cache_key, result, ttl)
        logger.debug(f"Cached coverage heatmap: {cache_key} (TTL: {ttl}s)")

        return result

    def generate_person_workload_heatmap(
        self,
        db: Session,
        person_ids: list[UUID],
        start_date: date,
        end_date: date,
        include_weekends: bool = False,
    ) -> HeatmapResponse:
        """
        Generate workload heatmap with caching.

        Args:
            db: Database session
            person_ids: List of person IDs to analyze
            start_date: Start date
            end_date: End date
            include_weekends: Whether to include weekends

        Returns:
            HeatmapResponse with workload data
        """
        # Build cache key
        sorted_ids = sorted(str(pid) for pid in person_ids)
        cache_key = (
            f"{CachePrefix.WORKLOAD.value}:"
            f"{start_date.isoformat()}:{end_date.isoformat()}:"
            f"weekends={include_weekends}:"
            f"persons=[{','.join(sorted_ids[:5])}]"
        )

        # Try cache first
        cached_result = self._cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for workload heatmap: {cache_key}")
            return cached_result

        # Generate workload heatmap
        result = self._service.generate_person_workload_heatmap(
            db=db,
            person_ids=person_ids,
            start_date=start_date,
            end_date=end_date,
            include_weekends=include_weekends,
        )

        # Cache the result
        ttl = self._settings.CACHE_HEATMAP_TTL
        self._cache.set(cache_key, result, ttl)
        logger.debug(f"Cached workload heatmap: {cache_key} (TTL: {ttl}s)")

        return result

    def invalidate_cache(self) -> int:
        """
        Invalidate all heatmap cache entries.

        Returns:
            Number of entries invalidated.
        """
        count = self._cache.invalidate_by_prefix(CachePrefix.HEATMAP)
        count += self._cache.invalidate_by_prefix(CachePrefix.COVERAGE)
        count += self._cache.invalidate_by_prefix(CachePrefix.WORKLOAD)
        logger.info(f"Invalidated {count} heatmap cache entries")
        return count

    # Delegate non-cached methods to underlying service
    @staticmethod
    def calculate_date_range(time_range: TimeRangeType) -> tuple[date, date]:
        """Calculate date range from time range specification."""
        return HeatmapService.calculate_date_range(time_range)

    @staticmethod
    def export_heatmap_image(
        data: Any,
        title: str,
        format: str = "png",
        width: int = 1200,
        height: int = 800,
    ) -> bytes:
        """Export heatmap as image (not cached - generates fresh each time)."""
        return HeatmapService.export_heatmap_image(
            data=data,
            title=title,
            format=format,
            width=width,
            height=height,
        )

    @staticmethod
    def create_plotly_figure(data: Any, title: str) -> dict[str, Any]:
        """Create Plotly figure configuration."""
        return HeatmapService.create_plotly_figure(data=data, title=title)


def get_cached_heatmap_service() -> CachedHeatmapService:
    """Get an instance of the cached heatmap service."""
    return CachedHeatmapService()


class CachedCalendarService:
    """
    Cached wrapper for CalendarService.

    Caches ICS calendar generation for person schedules.
    Falls back to uncached operations when Redis is unavailable.

    Example:
        service = CachedCalendarService()
        ics_content = service.generate_ics_for_person(
            db=db,
            person_id=person_uuid,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
    """

    def __init__(self):
        """Initialize cached service."""
        self._cache = get_service_cache()
        self._settings = get_settings()

    def _build_calendar_cache_key(
        self,
        key_type: str,
        entity_id: UUID,
        start_date: date,
        end_date: date,
        include_types: list[str] | None = None,
    ) -> str:
        """Build a deterministic cache key for calendar queries."""
        key_parts = [
            CachePrefix.CALENDAR.value,
            key_type,
            str(entity_id),
            start_date.isoformat(),
            end_date.isoformat(),
        ]

        if include_types:
            sorted_types = sorted(include_types)
            key_parts.append(f"types:[{','.join(sorted_types)}]")

        return ":".join(key_parts)

    def generate_ics_for_person(
        self,
        db: Session,
        person_id: UUID,
        start_date: date,
        end_date: date,
        include_types: list[str] | None = None,
    ) -> str:
        """
        Generate ICS calendar file for a person's assignments with caching.

        Args:
            db: Database session
            person_id: Person UUID
            start_date: Start date for export
            end_date: End date for export
            include_types: Optional list of activity types to include

        Returns:
            ICS file content as string
        """
        cache_key = self._build_calendar_cache_key(
            "person", person_id, start_date, end_date, include_types
        )

        # Try cache first
        cached_result = self._cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for calendar: {cache_key}")
            return cached_result

        # Generate ICS
        result = CalendarService.generate_ics_for_person(
            db=db,
            person_id=person_id,
            start_date=start_date,
            end_date=end_date,
            include_types=include_types,
        )

        # Cache the result
        ttl = self._settings.CACHE_CALENDAR_TTL
        self._cache.set(cache_key, result, ttl)
        logger.debug(f"Cached calendar result: {cache_key} (TTL: {ttl}s)")

        return result

    def generate_ics_for_rotation(
        self,
        db: Session,
        rotation_id: UUID,
        start_date: date,
        end_date: date,
    ) -> str:
        """
        Generate ICS calendar file for all assignments in a rotation with caching.

        Args:
            db: Database session
            rotation_id: Rotation template UUID
            start_date: Start date for export
            end_date: End date for export

        Returns:
            ICS file content as string
        """
        cache_key = self._build_calendar_cache_key(
            "rotation", rotation_id, start_date, end_date
        )

        # Try cache first
        cached_result = self._cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for rotation calendar: {cache_key}")
            return cached_result

        # Generate ICS
        result = CalendarService.generate_ics_for_rotation(
            db=db,
            rotation_id=rotation_id,
            start_date=start_date,
            end_date=end_date,
        )

        # Cache the result
        ttl = self._settings.CACHE_CALENDAR_TTL
        self._cache.set(cache_key, result, ttl)
        logger.debug(f"Cached rotation calendar: {cache_key} (TTL: {ttl}s)")

        return result

    def invalidate_cache(self, person_id: UUID | None = None) -> int:
        """
        Invalidate calendar cache entries.

        Args:
            person_id: Specific person to invalidate, or all if None.

        Returns:
            Number of entries invalidated.
        """
        if person_id:
            pattern = f"{CachePrefix.CALENDAR.value}:*:{person_id}:*"
            count = self._cache.invalidate_pattern(pattern)
        else:
            count = self._cache.invalidate_by_prefix(CachePrefix.CALENDAR)
        logger.info(f"Invalidated {count} calendar cache entries")
        return count

    # Delegate non-cached methods to CalendarService
    @staticmethod
    def create_subscription(
        db: Session,
        person_id: UUID,
        created_by_user_id: UUID | None = None,
        label: str | None = None,
        expires_days: int | None = None,
    ):
        """Create a calendar subscription (not cached - modifies state)."""
        return CalendarService.create_subscription(
            db=db,
            person_id=person_id,
            created_by_user_id=created_by_user_id,
            label=label,
            expires_days=expires_days,
        )

    @staticmethod
    def validate_subscription_token(db: Session, token: str) -> UUID | None:
        """Validate a subscription token (not cached - updates access time)."""
        return CalendarService.validate_subscription_token(db=db, token=token)

    @staticmethod
    def revoke_subscription(db: Session, token: str) -> bool:
        """Revoke a calendar subscription (not cached - modifies state)."""
        return CalendarService.revoke_subscription(db=db, token=token)


def get_cached_calendar_service() -> CachedCalendarService:
    """Get an instance of the cached calendar service."""
    return CachedCalendarService()
