"""
Faculty Constraint Service with Caching.

This module provides a service layer for Faculty constraints that:
- Caches FacultyPreference lookups to reduce database queries
- Provides authorization helpers to prevent IDOR vulnerabilities
- Handles cache invalidation on preference updates
- Integrates with the scheduling constraint system

Security:
- All faculty_id parameters are validated against the authenticated user
- Direct ID access is prevented through authorization checks
- Cache keys are scoped to prevent cross-user data leakage
"""

import logging
import pickle
from datetime import date, datetime, timedelta
from functools import lru_cache
from threading import RLock
from typing import Any
from uuid import UUID

import redis

from app.core.config import get_settings
from app.models.faculty_preference import FacultyPreference
from app.models.person import Person
from app.models.user import User

logger = logging.getLogger(__name__)


class FacultyPreferenceCache:
    """
    Redis-backed cache for faculty preference lookups.

    Provides efficient caching of faculty preferences to minimize
    database queries during constraint evaluation.

    Cache Keys:
        - faculty_pref:{faculty_id} - Full preference object
        - faculty_pref:blocked:{faculty_id}:{week_iso} - Is week blocked?
        - faculty_pref:preferred:{faculty_id}:{week_iso} - Is week preferred?

    TTL: Default 15 minutes (900 seconds) for preferences
    """

    KEY_PREFIX = "faculty_pref:"
    DEFAULT_TTL = 900  # 15 minutes

    def __init__(self, ttl_seconds: int = DEFAULT_TTL):
        """
        Initialize the cache.

        Args:
            ttl_seconds: Time-to-live for cache entries (default: 15 minutes)
        """
        self.ttl_seconds = ttl_seconds
        self._lock = RLock()

        # Initialize Redis connection
        settings = get_settings()
        redis_url = settings.redis_url_with_password
        try:
            self._redis = redis.from_url(redis_url, decode_responses=False)
            self._redis.ping()
            self._available = True
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Redis unavailable for faculty preference cache: {e}")
            self._redis = None
            self._available = False

        # Local LRU cache fallback when Redis is unavailable
        self._local_cache: dict[str, tuple[Any, datetime]] = {}

    @property
    def is_available(self) -> bool:
        """Check if cache backend is available."""
        return self._available

    def get_preferences(self, faculty_id: UUID) -> FacultyPreference | None:
        """
        Get cached faculty preferences.

        Args:
            faculty_id: UUID of the faculty member

        Returns:
            FacultyPreference object or None if not cached
        """
        key = f"{self.KEY_PREFIX}{faculty_id}"
        return self._get(key)

    def set_preferences(self, faculty_id: UUID, preferences: FacultyPreference) -> None:
        """
        Cache faculty preferences.

        Args:
            faculty_id: UUID of the faculty member
            preferences: FacultyPreference object to cache
        """
        key = f"{self.KEY_PREFIX}{faculty_id}"
        # Cache a dictionary representation, not the ORM object
        pref_data = {
            "id": str(preferences.id),
            "faculty_id": str(preferences.faculty_id),
            "preferred_weeks": preferences.preferred_weeks or [],
            "blocked_weeks": preferences.blocked_weeks or [],
            "max_weeks_per_month": preferences.max_weeks_per_month,
            "max_consecutive_weeks": preferences.max_consecutive_weeks,
            "min_gap_between_weeks": preferences.min_gap_between_weeks,
            "target_weeks_per_year": preferences.target_weeks_per_year,
            "notify_swap_requests": preferences.notify_swap_requests,
            "notify_schedule_changes": preferences.notify_schedule_changes,
            "notify_conflict_alerts": preferences.notify_conflict_alerts,
            "notify_reminder_days": preferences.notify_reminder_days,
            "notes": preferences.notes,
        }
        self._put(key, pref_data)

    def is_week_blocked(self, faculty_id: UUID, week_date: date) -> bool | None:
        """
        Check cached blocked week status.

        Args:
            faculty_id: UUID of the faculty member
            week_date: Date to check

        Returns:
            True/False if cached, None if not in cache
        """
        key = f"{self.KEY_PREFIX}blocked:{faculty_id}:{week_date.isoformat()}"
        return self._get(key)

    def set_week_blocked(
        self, faculty_id: UUID, week_date: date, is_blocked: bool
    ) -> None:
        """Cache whether a week is blocked."""
        key = f"{self.KEY_PREFIX}blocked:{faculty_id}:{week_date.isoformat()}"
        self._put(key, is_blocked)

    def is_week_preferred(self, faculty_id: UUID, week_date: date) -> bool | None:
        """
        Check cached preferred week status.

        Args:
            faculty_id: UUID of the faculty member
            week_date: Date to check

        Returns:
            True/False if cached, None if not in cache
        """
        key = f"{self.KEY_PREFIX}preferred:{faculty_id}:{week_date.isoformat()}"
        return self._get(key)

    def set_week_preferred(
        self, faculty_id: UUID, week_date: date, is_preferred: bool
    ) -> None:
        """Cache whether a week is preferred."""
        key = f"{self.KEY_PREFIX}preferred:{faculty_id}:{week_date.isoformat()}"
        self._put(key, is_preferred)

    def invalidate_faculty(self, faculty_id: UUID) -> int:
        """
        Invalidate all cache entries for a faculty member.

        Called when faculty preferences are updated.

        Args:
            faculty_id: UUID of the faculty member

        Returns:
            Number of cache entries invalidated
        """
        pattern = f"{self.KEY_PREFIX}*{faculty_id}*"
        deleted_count = 0

        if self._redis and self._available:
            try:
                cursor = 0
                while True:
                    cursor, keys = self._redis.scan(cursor, match=pattern, count=100)
                    if keys:
                        self._redis.delete(*keys)
                        deleted_count += len(keys)
                    if cursor == 0:
                        break
            except redis.RedisError as e:
                logger.error(f"Cache invalidation error: {e}")

        # Also clear from local cache
        with self._lock:
            to_delete = [k for k in self._local_cache if str(faculty_id) in k]
            for k in to_delete:
                del self._local_cache[k]
                deleted_count += 1

        logger.info(
            f"Invalidated {deleted_count} cache entries for faculty {faculty_id}"
        )
        return deleted_count

    def invalidate_all(self) -> int:
        """
        Clear all faculty preference cache entries.

        Returns:
            Number of entries deleted
        """
        pattern = f"{self.KEY_PREFIX}*"
        deleted_count = 0

        if self._redis and self._available:
            try:
                cursor = 0
                while True:
                    cursor, keys = self._redis.scan(cursor, match=pattern, count=100)
                    if keys:
                        self._redis.delete(*keys)
                        deleted_count += len(keys)
                    if cursor == 0:
                        break
            except redis.RedisError as e:
                logger.error(f"Cache clear error: {e}")

        # Clear local cache
        with self._lock:
            deleted_count += len(self._local_cache)
            self._local_cache.clear()

        logger.info(f"Cleared {deleted_count} faculty preference cache entries")
        return deleted_count

    def _get(self, key: str) -> Any | None:
        """Get value from cache (Redis or local fallback)."""
        # Try Redis first
        if self._redis and self._available:
            try:
                data = self._redis.get(key)
                if data is not None:
                    return pickle.loads(data)
            except redis.RedisError as e:
                logger.warning(f"Redis get error: {e}")
                self._available = False

        # Fallback to local cache
        with self._lock:
            if key in self._local_cache:
                value, expiry = self._local_cache[key]
                if datetime.utcnow() < expiry:
                    return value
                else:
                    del self._local_cache[key]

        return None

    def _put(self, key: str, value: Any) -> None:
        """Put value in cache (Redis or local fallback)."""
        # Try Redis first
        if self._redis and self._available:
            try:
                data = pickle.dumps(value)
                self._redis.setex(key, self.ttl_seconds, data)
                return
            except redis.RedisError as e:
                logger.warning(f"Redis put error: {e}")
                self._available = False

        # Fallback to local cache
        with self._lock:
            expiry = datetime.utcnow() + timedelta(seconds=self.ttl_seconds)
            self._local_cache[key] = (value, expiry)

            # Limit local cache size
            if len(self._local_cache) > 1000:
                # Remove oldest 20%
                sorted_keys = sorted(
                    self._local_cache.keys(), key=lambda k: self._local_cache[k][1]
                )
                for k in sorted_keys[:200]:
                    del self._local_cache[k]


# Global cache instance
_faculty_pref_cache: FacultyPreferenceCache | None = None


def get_faculty_pref_cache() -> FacultyPreferenceCache:
    """Get or create global faculty preference cache."""
    global _faculty_pref_cache
    if _faculty_pref_cache is None:
        _faculty_pref_cache = FacultyPreferenceCache()
    return _faculty_pref_cache


class CachedFacultyPreferenceService:
    """
    Faculty preference service with caching.

    This service wraps FacultyPreference database lookups with caching
    to improve performance during constraint evaluation.

    Security:
    - Provides authorization helpers to prevent IDOR
    - Validates faculty_id access against authenticated user
    """

    def __init__(self, db, cache: FacultyPreferenceCache | None = None):
        """
        Initialize the service.

        Args:
            db: Database session
            cache: Optional cache instance (uses global if not provided)
        """
        from sqlalchemy.orm import Session

        self.db: Session = db
        self.cache = cache or get_faculty_pref_cache()

    def get_preferences(self, faculty_id: UUID) -> FacultyPreference | None:
        """
        Get faculty preferences with caching.

        Args:
            faculty_id: UUID of the faculty member

        Returns:
            FacultyPreference object or None if not found
        """
        # Check cache first
        cached = self.cache.get_preferences(faculty_id)
        if cached is not None:
            # Reconstruct a FacultyPreference-like object from cached data
            return self._dict_to_preference(cached)

        # Query database
        preferences = (
            self.db.query(FacultyPreference)
            .filter(FacultyPreference.faculty_id == faculty_id)
            .first()
        )

        # Cache result if found
        if preferences:
            self.cache.set_preferences(faculty_id, preferences)

        return preferences

    def is_week_blocked(self, faculty_id: UUID, week_date: date) -> bool:
        """
        Check if a week is blocked with caching.

        Args:
            faculty_id: UUID of the faculty member
            week_date: Date to check

        Returns:
            True if the week is blocked
        """
        # Check cache
        cached = self.cache.is_week_blocked(faculty_id, week_date)
        if cached is not None:
            return cached

        # Query database
        preferences = self.get_preferences(faculty_id)
        if not preferences or not preferences.blocked_weeks:
            result = False
        else:
            result = week_date.isoformat() in preferences.blocked_weeks

        # Cache result
        self.cache.set_week_blocked(faculty_id, week_date, result)
        return result

    def is_week_preferred(self, faculty_id: UUID, week_date: date) -> bool:
        """
        Check if a week is preferred with caching.

        Args:
            faculty_id: UUID of the faculty member
            week_date: Date to check

        Returns:
            True if the week is preferred
        """
        # Check cache
        cached = self.cache.is_week_preferred(faculty_id, week_date)
        if cached is not None:
            return cached

        # Query database
        preferences = self.get_preferences(faculty_id)
        if not preferences or not preferences.preferred_weeks:
            result = False
        else:
            result = week_date.isoformat() in preferences.preferred_weeks

        # Cache result
        self.cache.set_week_preferred(faculty_id, week_date, result)
        return result

    def invalidate_cache(self, faculty_id: UUID) -> int:
        """
        Invalidate cache for a faculty member.

        Call this when preferences are updated.

        Args:
            faculty_id: UUID of the faculty member

        Returns:
            Number of cache entries invalidated
        """
        return self.cache.invalidate_faculty(faculty_id)

    def _dict_to_preference(self, data: dict) -> FacultyPreference:
        """Convert cached dict to FacultyPreference-like object."""
        pref = FacultyPreference()
        pref.id = UUID(data["id"]) if data.get("id") else None
        pref.faculty_id = UUID(data["faculty_id"]) if data.get("faculty_id") else None
        pref.preferred_weeks = data.get("preferred_weeks", [])
        pref.blocked_weeks = data.get("blocked_weeks", [])
        pref.max_weeks_per_month = data.get("max_weeks_per_month", 2)
        pref.max_consecutive_weeks = data.get("max_consecutive_weeks", 1)
        pref.min_gap_between_weeks = data.get("min_gap_between_weeks", 2)
        pref.target_weeks_per_year = data.get("target_weeks_per_year", 6)
        pref.notify_swap_requests = data.get("notify_swap_requests", True)
        pref.notify_schedule_changes = data.get("notify_schedule_changes", True)
        pref.notify_conflict_alerts = data.get("notify_conflict_alerts", True)
        pref.notify_reminder_days = data.get("notify_reminder_days", 7)
        pref.notes = data.get("notes")
        return pref


class FacultyConstraintService:
    """
    Service for faculty constraint validation with authorization.

    This service provides helpers for constraint validation that include
    proper authorization checks to prevent IDOR vulnerabilities.

    Security:
    - validate_faculty_access() must be called before any faculty ID access
    - get_authorized_faculty_id() safely retrieves faculty ID from user context
    """

    def __init__(self, db):
        """
        Initialize the service.

        Args:
            db: Database session
        """
        from sqlalchemy.orm import Session

        self.db: Session = db
        self.pref_service = CachedFacultyPreferenceService(db)

    def get_authorized_faculty_id(self, user: User) -> UUID | None:
        """
        Get faculty ID for an authenticated user.

        This is the safe way to get a faculty ID - it derives it from
        the authenticated user rather than accepting an arbitrary ID.

        Args:
            user: Authenticated User object

        Returns:
            UUID of the linked faculty member, or None if not linked

        Security:
            - Prevents IDOR by deriving faculty_id from authenticated user
            - Returns None if user is not a faculty member
        """
        faculty = (
            self.db.query(Person)
            .filter(
                Person.email == user.email,
                Person.type == "faculty",
            )
            .first()
        )

        return faculty.id if faculty else None

    def validate_faculty_access(self, user: User, faculty_id: UUID) -> bool:
        """
        Validate that a user can access a faculty member's data.

        Args:
            user: Authenticated User object
            faculty_id: UUID of the faculty member to access

        Returns:
            True if access is allowed, False otherwise

        Security:
            - Checks if user is an admin (can access any faculty)
            - Checks if user is the faculty member themselves
            - Returns False for any other access attempt (IDOR prevention)
        """
        # Admin users can access any faculty
        if user.role == "admin":
            return True

        # Non-admin users can only access their own data
        authorized_faculty_id = self.get_authorized_faculty_id(user)
        if authorized_faculty_id is None:
            return False

        return authorized_faculty_id == faculty_id

    def get_preferences_for_constraint(
        self,
        faculty_id: UUID,
        user: User | None = None,
    ) -> FacultyPreference | None:
        """
        Get faculty preferences for constraint evaluation.

        Args:
            faculty_id: UUID of the faculty member
            user: Optional authenticated user for authorization check

        Returns:
            FacultyPreference object or None

        Security:
            - If user is provided, validates access before returning data
            - If user is None, assumes internal/system call (no authz check)
        """
        # Validate access if user provided
        if user is not None:
            if not self.validate_faculty_access(user, faculty_id):
                logger.warning(
                    f"Unauthorized faculty preference access attempt: "
                    f"user={user.id}, faculty_id={faculty_id}"
                )
                return None

        return self.pref_service.get_preferences(faculty_id)

    def check_week_availability(
        self,
        faculty_id: UUID,
        week_date: date,
    ) -> dict:
        """
        Check a faculty member's availability for a week.

        Used by constraints to determine if a faculty member should
        be assigned to a particular week.

        Args:
            faculty_id: UUID of the faculty member
            week_date: Date within the week to check

        Returns:
            Dictionary with:
            - is_blocked: True if week is blocked
            - is_preferred: True if week is preferred
            - constraints: Dict of applicable constraints
        """
        is_blocked = self.pref_service.is_week_blocked(faculty_id, week_date)
        is_preferred = self.pref_service.is_week_preferred(faculty_id, week_date)

        preferences = self.pref_service.get_preferences(faculty_id)
        constraints = {}
        if preferences:
            constraints = {
                "max_weeks_per_month": preferences.max_weeks_per_month,
                "max_consecutive_weeks": preferences.max_consecutive_weeks,
                "min_gap_between_weeks": preferences.min_gap_between_weeks,
            }

        return {
            "is_blocked": is_blocked,
            "is_preferred": is_preferred,
            "constraints": constraints,
        }

    def on_preferences_updated(self, faculty_id: UUID) -> None:
        """
        Handle preference update event - invalidate cache.

        Call this method whenever faculty preferences are modified
        to ensure constraint evaluation uses fresh data.

        Args:
            faculty_id: UUID of the faculty member whose preferences changed
        """
        self.pref_service.invalidate_cache(faculty_id)
        logger.info(
            f"Cache invalidated for faculty {faculty_id} after preference update"
        )
