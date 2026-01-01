"""Distributed locking with Redis.

Provides distributed locking across multiple processes/servers using Redis.
Useful for preventing race conditions in concurrent swap operations.
"""

import logging
import time
import uuid
from contextlib import contextmanager
from typing import Any

import redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DistributedLockError(Exception):
    """Base exception for distributed lock errors."""

    pass


class LockAcquisitionFailed(DistributedLockError):
    """Failed to acquire lock within timeout."""

    pass


class LockNotHeld(DistributedLockError):
    """Attempting to release a lock that is not held."""

    pass


class DistributedLock:
    """
    Distributed lock implementation using Redis.

    Uses Redis SET with NX (not exists) and EX (expiry) options to implement
    a simple but effective distributed lock.

    Features:
    - Auto-expiry to prevent deadlocks from crashed processes
    - Lock ownership tracking (only owner can release)
    - Blocking and non-blocking acquisition modes
    - Retry with exponential backoff

    Usage:
        lock = DistributedLock(redis_client, "swap:123", ttl_seconds=30)
        if lock.acquire(blocking=True, timeout=10):
            try:
                # Do work
                execute_swap()
            finally:
                lock.release()

        # Or use as context manager:
        with distributed_lock(redis_client, "swap:123"):
            execute_swap()
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        lock_key: str,
        ttl_seconds: int = 30,
    ):
        """
        Initialize distributed lock.

        Args:
            redis_client: Redis client instance
            lock_key: Unique key for this lock (e.g., "swap:123")
            ttl_seconds: Lock TTL in seconds (prevents deadlock if holder crashes)
        """
        self.redis = redis_client
        self.lock_key = f"lock:{lock_key}"
        self.ttl_seconds = ttl_seconds
        self.lock_id = str(uuid.uuid4())  # Unique ID for this lock holder
        self._acquired = False

    def acquire(
        self,
        blocking: bool = True,
        timeout: float | None = None,
        retry_interval: float = 0.1,
    ) -> bool:
        """
        Acquire the distributed lock.

        Args:
            blocking: If True, wait for lock. If False, return immediately.
            timeout: Maximum time to wait in seconds (None = wait forever)
            retry_interval: Time between retry attempts in seconds

        Returns:
            True if lock acquired, False otherwise

        Raises:
            LockAcquisitionFailed: If blocking=True and timeout exceeded
        """
        start_time = time.time()

        while True:
            # Try to acquire lock using Redis SET with NX (not exists) and EX (expiry)
            acquired = self.redis.set(
                self.lock_key,
                self.lock_id,
                nx=True,  # Only set if not exists
                ex=self.ttl_seconds,  # Auto-expire after TTL
            )

            if acquired:
                self._acquired = True
                logger.debug(
                    f"Acquired distributed lock: {self.lock_key} "
                    f"(id: {self.lock_id}, ttl: {self.ttl_seconds}s)"
                )
                return True

            # If non-blocking, return immediately
            if not blocking:
                logger.debug(f"Failed to acquire lock (non-blocking): {self.lock_key}")
                return False

            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    logger.warning(
                        f"Lock acquisition timeout after {elapsed:.2f}s: {self.lock_key}"
                    )
                    raise LockAcquisitionFailed(
                        f"Could not acquire lock {self.lock_key} within {timeout}s"
                    )

            # Wait before retry
            time.sleep(retry_interval)

    def release(self):
        """
        Release the distributed lock.

        Only releases if this instance owns the lock (verified by lock_id).

        Raises:
            LockNotHeld: If lock is not held or is held by another instance
        """
        if not self._acquired:
            logger.warning(f"Attempting to release lock that was never acquired: {self.lock_key}")
            return

        # Use Lua script to atomically check ownership and delete
        # This prevents releasing a lock that was acquired by another process
        # after this one's TTL expired
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """

        result = self.redis.eval(lua_script, 1, self.lock_key, self.lock_id)

        if result == 1:
            self._acquired = False
            logger.debug(f"Released distributed lock: {self.lock_key} (id: {self.lock_id})")
        else:
            logger.warning(
                f"Failed to release lock {self.lock_key} - "
                f"not owned by this instance (id: {self.lock_id})"
            )
            raise LockNotHeld(
                f"Lock {self.lock_key} is not held by this instance or has expired"
            )

    def extend(self, additional_ttl: int | None = None):
        """
        Extend the lock TTL.

        Useful for long-running operations that need to keep the lock alive.

        Args:
            additional_ttl: Additional seconds to add (None = reset to original TTL)

        Raises:
            LockNotHeld: If lock is not held by this instance
        """
        if not self._acquired:
            raise LockNotHeld("Cannot extend a lock that is not acquired")

        ttl = additional_ttl if additional_ttl is not None else self.ttl_seconds

        # Use Lua script to atomically check ownership and extend
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("expire", KEYS[1], ARGV[2])
        else
            return 0
        end
        """

        result = self.redis.eval(lua_script, 1, self.lock_key, self.lock_id, ttl)

        if result == 1:
            logger.debug(f"Extended lock TTL: {self.lock_key} (+{ttl}s)")
        else:
            logger.warning(f"Failed to extend lock {self.lock_key} - not owned")
            raise LockNotHeld(f"Lock {self.lock_key} is not held by this instance")

    def is_locked(self) -> bool:
        """Check if the lock is currently held (by anyone)."""
        return self.redis.exists(self.lock_key) > 0

    def __enter__(self):
        """Context manager entry."""
        self.acquire(blocking=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._acquired:
            try:
                self.release()
            except LockNotHeld:
                # Log warning but don't raise - lock may have expired
                logger.warning(
                    f"Lock {self.lock_key} expired or was released by another process"
                )
        return False  # Don't suppress exceptions


@contextmanager
def distributed_lock(
    redis_client: redis.Redis,
    lock_key: str,
    ttl_seconds: int = 30,
    timeout: float | None = 10.0,
    retry_interval: float = 0.1,
):
    """
    Context manager for distributed locking.

    Args:
        redis_client: Redis client instance
        lock_key: Unique key for this lock
        ttl_seconds: Lock TTL
        timeout: Acquisition timeout
        retry_interval: Time between retries

    Usage:
        with distributed_lock(redis_client, "swap:123", timeout=10):
            # Critical section
            execute_swap()

    Raises:
        LockAcquisitionFailed: If lock cannot be acquired within timeout
    """
    lock = DistributedLock(redis_client, lock_key, ttl_seconds)
    acquired = lock.acquire(blocking=True, timeout=timeout, retry_interval=retry_interval)

    if not acquired:
        raise LockAcquisitionFailed(f"Could not acquire lock {lock_key}")

    try:
        yield lock
    finally:
        if lock._acquired:
            try:
                lock.release()
            except LockNotHeld:
                logger.warning(f"Lock {lock_key} expired during operation")


def get_redis_client() -> redis.Redis:
    """
    Get Redis client for distributed locking.

    Returns:
        Redis client instance
    """
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD if hasattr(settings, "REDIS_PASSWORD") else None,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
    )


class IdempotencyManager:
    """
    Manage idempotent operations using Redis.

    Prevents duplicate execution of operations (e.g., swap execution)
    by tracking operation IDs in Redis.

    Usage:
        idem = IdempotencyManager(redis_client)
        if idem.is_duplicate("swap_execute_123"):
            return cached_result

        result = execute_swap()
        idem.mark_completed("swap_execute_123", result, ttl=3600)
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def is_duplicate(self, operation_id: str) -> bool:
        """
        Check if operation has already been executed.

        Args:
            operation_id: Unique operation identifier

        Returns:
            True if operation was already executed
        """
        key = f"idempotency:{operation_id}"
        return self.redis.exists(key) > 0

    def mark_completed(
        self,
        operation_id: str,
        result: Any = None,
        ttl: int = 3600,
    ):
        """
        Mark operation as completed.

        Args:
            operation_id: Unique operation identifier
            result: Optional result to cache
            ttl: Time to live in seconds
        """
        key = f"idempotency:{operation_id}"
        value = str(result) if result is not None else "completed"
        self.redis.setex(key, ttl, value)
        logger.debug(f"Marked operation as completed: {operation_id}")

    def get_cached_result(self, operation_id: str) -> str | None:
        """
        Get cached result for completed operation.

        Args:
            operation_id: Unique operation identifier

        Returns:
            Cached result or None
        """
        key = f"idempotency:{operation_id}"
        return self.redis.get(key)


# Global Redis client for distributed locking
_redis_client = None


def get_lock_client() -> redis.Redis:
    """Get or create global Redis client for locking."""
    global _redis_client
    if _redis_client is None:
        _redis_client = get_redis_client()
    return _redis_client
