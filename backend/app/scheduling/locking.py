"""Distributed locking for schedule generation using Redis."""

import time
from contextlib import contextmanager
from uuid import uuid4

import redis

from app.core.config import get_settings


# Distributed Lock Configuration
LOCK_TIMEOUT_SECONDS = 600  # 10 minutes - Maximum lock duration
DEFAULT_LOCK_ACQUISITION_TIMEOUT = 30  # 30 seconds - Default timeout for acquiring lock
INITIAL_RETRY_DELAY_SECONDS = 0.1  # 100ms - Initial retry delay
MAX_RETRY_DELAY_SECONDS = 2.0  # 2 seconds - Maximum retry delay


class LockAcquisitionError(Exception):
    """Raised when a lock cannot be acquired."""

    pass


class ScheduleGenerationLock:
    """Distributed lock for schedule generation using Redis.

    This class implements a distributed locking mechanism to ensure that only
    one schedule generation process runs at a time per academic year. It uses
    Redis SETNX pattern with expiry to prevent race conditions and deadlocks.

    Example:
        >>> lock = ScheduleGenerationLock()
        >>> with lock.acquire(year_id="2024"):
        ...     # Generate schedule - guaranteed exclusive access
        ...     pass
    """

    # Lua script for atomic lock release (only release if we own the lock)
    RELEASE_SCRIPT = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """

    def __init__(self, redis_client: redis.Redis | None = None) -> None:
        """Initialize the distributed lock.

        Args:
            redis_client: Optional Redis client. If not provided, creates one
                from settings.REDIS_URL with password authentication.
        """
        if redis_client is None:
            settings = get_settings()
            # Use authenticated Redis URL if password is configured
            redis_url = settings.redis_url_with_password
            self.redis = redis.from_url(redis_url)
        else:
            self.redis = redis_client

        self.lock_timeout = LOCK_TIMEOUT_SECONDS  # Maximum lock duration
        self._release_script = self.redis.register_script(self.RELEASE_SCRIPT)

    @contextmanager
    def acquire(self, year_id: str, timeout: int = DEFAULT_LOCK_ACQUISITION_TIMEOUT):
        """Acquire lock for schedule generation.

        This context manager attempts to acquire an exclusive lock for schedule
        generation for a specific academic year. If the lock is already held,
        it will retry until the timeout expires.

        Args:
            year_id: Academic year identifier (e.g., "2024" or year DB ID)
            timeout: Maximum seconds to wait for lock acquisition (default: 30)

        Yields:
            None - Lock is held during the context

        Raises:
            LockAcquisitionError: If lock cannot be acquired within timeout

        Example:
            >>> lock = ScheduleGenerationLock()
            >>> try:
            ...     with lock.acquire(year_id="2024", timeout=60):
            ...         generate_schedule()
            ... except LockAcquisitionError:
            ...     print("Another generation is already running")
        """
        lock_key = f"lock:schedule_generation:{year_id}"
        lock_value = str(uuid4())

        # Try to acquire lock
        acquired = self._try_acquire(lock_key, lock_value, timeout)
        if not acquired:
            raise LockAcquisitionError(
                f"Could not acquire lock for year {year_id} within {timeout} seconds. "
                "Another schedule generation may already be running."
            )

        try:
            yield
        finally:
            # Always attempt to release lock, even if generation failed
            self._release(lock_key, lock_value)

    def _try_acquire(self, key: str, value: str, timeout: int) -> bool:
        """Try to acquire lock with retry logic.

        Attempts to acquire the lock using SETNX (SET if Not eXists) pattern.
        Retries with exponential backoff until timeout expires.

        Args:
            key: Redis key for the lock
            value: Unique identifier (UUID) for this lock acquisition
            timeout: Maximum seconds to wait

        Returns:
            bool: True if lock acquired, False if timeout expired
        """
        start_time = time.time()
        retry_delay = INITIAL_RETRY_DELAY_SECONDS
        max_retry_delay = MAX_RETRY_DELAY_SECONDS

        while True:
            # Try to set the key with expiry (atomic operation)
            # NX = only set if key doesn't exist
            # EX = set expiry in seconds
            acquired = self.redis.set(
                key,
                value,
                nx=True,  # SET if Not eXists
                ex=self.lock_timeout,  # EXpiry in seconds
            )

            if acquired:
                return True

            # Check if timeout expired
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                return False

            # Sleep before retry with exponential backoff
            time.sleep(min(retry_delay, timeout - elapsed))
            retry_delay = min(retry_delay * 2, max_retry_delay)

    def _release(self, key: str, value: str) -> bool:
        """Release the lock if we own it.

        Uses a Lua script to atomically check lock ownership and delete.
        This prevents releasing a lock that was acquired by another process
        (e.g., if our lock expired and another process acquired it).

        Args:
            key: Redis key for the lock
            value: Unique identifier (UUID) for this lock acquisition

        Returns:
            bool: True if lock was released, False if we didn't own it
        """
        try:
            # Execute Lua script atomically
            # Returns 1 if deleted, 0 if we didn't own the lock
            result = self._release_script(keys=[key], args=[value])
            return bool(result)
        except redis.RedisError:
            # If Redis is unavailable, we can't release the lock
            # It will expire automatically after lock_timeout
            return False

    def is_locked(self, year_id: str) -> bool:
        """Check if generation is currently running for a year.

        Args:
            year_id: Academic year identifier

        Returns:
            bool: True if a lock exists, False otherwise

        Example:
            >>> lock = ScheduleGenerationLock()
            >>> if lock.is_locked("2024"):
            ...     print("Generation already running")
        """
        lock_key = f"lock:schedule_generation:{year_id}"
        try:
            return self.redis.exists(lock_key) > 0
        except redis.RedisError:
            # If Redis is unavailable, assume not locked
            # This allows operations to proceed in degraded mode
            return False

    def get_lock_ttl(self, year_id: str) -> int | None:
        """Get remaining time-to-live for a lock in seconds.

        Useful for showing users how long until the current generation finishes
        (or at least how long until the lock expires).

        Args:
            year_id: Academic year identifier

        Returns:
            Optional[int]: Remaining seconds, or None if lock doesn't exist

        Example:
            >>> lock = ScheduleGenerationLock()
            >>> ttl = lock.get_lock_ttl("2024")
            >>> if ttl:
            ...     print(f"Generation will complete in ~{ttl} seconds")
        """
        lock_key = f"lock:schedule_generation:{year_id}"
        try:
            ttl = self.redis.ttl(lock_key)
            # ttl returns -2 if key doesn't exist, -1 if no expiry set
            return ttl if ttl > 0 else None
        except redis.RedisError:
            return None

    def force_release(self, year_id: str) -> bool:
        """Force release a lock regardless of ownership.

        WARNING: This should only be used in emergency situations where a lock
        is stuck (e.g., during development or if a bug caused improper cleanup).
        In production, locks should always expire automatically.

        Args:
            year_id: Academic year identifier

        Returns:
            bool: True if lock was deleted, False otherwise
        """
        lock_key = f"lock:schedule_generation:{year_id}"
        try:
            return bool(self.redis.delete(lock_key))
        except redis.RedisError:
            return False
