"""
Redis-based distributed locking implementation.

Provides distributed locks for coordinating concurrent operations across
multiple processes and servers with support for:
- Lock acquisition with timeout
- Automatic lock renewal/extension
- Reentrant locks (same owner can acquire multiple times)
- Fair locks (FIFO queue-based)
- Deadlock detection
- Comprehensive metrics

Implementation based on Redis Redlock algorithm with single-node optimization.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from threading import RLock
from typing import Any

import redis.asyncio as redis

from app.core.config import get_settings
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

# Lock configuration constants
DEFAULT_LOCK_TIMEOUT = 30  # Default lock timeout in seconds
DEFAULT_ACQUISITION_TIMEOUT = 10  # Default time to wait for lock acquisition
DEFAULT_RENEWAL_INTERVAL = 10  # Default lock renewal interval in seconds
LOCK_KEY_PREFIX = "distributed_lock"
FAIR_LOCK_QUEUE_PREFIX = "fair_lock_queue"
LOCK_OWNER_PREFIX = "lock_owner"


# ============================================================================
# Exceptions
# ============================================================================


class LockError(AppException):
    """Base exception for lock-related errors."""

    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class LockAcquisitionError(LockError):
    """Lock could not be acquired."""

    pass


class LockTimeoutError(LockAcquisitionError):
    """Lock acquisition timed out."""

    def __init__(self, lock_name: str, timeout: float):
        super().__init__(
            f"Failed to acquire lock '{lock_name}' within {timeout} seconds"
        )


class LockRenewalError(LockError):
    """Lock renewal failed."""

    pass


# ============================================================================
# Lock Metrics
# ============================================================================


@dataclass
class LockMetrics:
    """
    Metrics for distributed lock monitoring.

    Tracks lock operations, timing, and failures for observability.
    """

    acquisitions_total: int = 0
    acquisition_failures: int = 0
    timeouts: int = 0
    releases_total: int = 0
    renewals_total: int = 0
    renewal_failures: int = 0
    deadlocks_detected: int = 0

    # Timing metrics (in seconds)
    total_acquisition_time: float = 0.0
    total_hold_time: float = 0.0
    max_acquisition_time: float = 0.0
    max_hold_time: float = 0.0

    # Lock tracking
    active_locks: dict[str, dict[str, Any]] = field(default_factory=dict)

    _lock: RLock = field(default_factory=RLock)

    def record_acquisition(self, lock_name: str, duration: float, owner: str) -> None:
        """
        Record successful lock acquisition.

        Args:
            lock_name: Name of the acquired lock
            duration: Time taken to acquire the lock in seconds
            owner: Owner/token of the lock
        """
        with self._lock:
            self.acquisitions_total += 1
            self.total_acquisition_time += duration
            self.max_acquisition_time = max(self.max_acquisition_time, duration)

            self.active_locks[lock_name] = {
                "owner": owner,
                "acquired_at": time.time(),
                "acquisition_duration": duration,
            }

    def record_acquisition_failure(self, lock_name: str, timed_out: bool = False):
        """
        Record failed lock acquisition.

        Args:
            lock_name: Name of the lock
            timed_out: Whether the failure was due to timeout
        """
        with self._lock:
            self.acquisition_failures += 1
            if timed_out:
                self.timeouts += 1

    def record_release(self, lock_name: str) -> None:
        """
        Record lock release.

        Args:
            lock_name: Name of the released lock
        """
        with self._lock:
            self.releases_total += 1

            if lock_name in self.active_locks:
                lock_info = self.active_locks.pop(lock_name)
                hold_time = time.time() - lock_info["acquired_at"]
                self.total_hold_time += hold_time
                self.max_hold_time = max(self.max_hold_time, hold_time)

    def record_renewal(self, success: bool = True) -> None:
        """
        Record lock renewal attempt.

        Args:
            success: Whether the renewal was successful
        """
        with self._lock:
            if success:
                self.renewals_total += 1
            else:
                self.renewal_failures += 1

    def record_deadlock(self) -> None:
        """Record deadlock detection."""
        with self._lock:
            self.deadlocks_detected += 1

    def get_stats(self) -> dict[str, Any]:
        """
        Get current lock statistics.

        Returns:
            Dictionary with comprehensive lock metrics
        """
        with self._lock:
            total_requests = self.acquisitions_total + self.acquisition_failures

            return {
                "acquisitions_total": self.acquisitions_total,
                "acquisition_failures": self.acquisition_failures,
                "timeouts": self.timeouts,
                "releases_total": self.releases_total,
                "renewals_total": self.renewals_total,
                "renewal_failures": self.renewal_failures,
                "deadlocks_detected": self.deadlocks_detected,
                "active_locks_count": len(self.active_locks),
                "active_locks": list(self.active_locks.keys()),
                "success_rate": (
                    self.acquisitions_total / total_requests
                    if total_requests > 0
                    else 0.0
                ),
                "avg_acquisition_time": (
                    self.total_acquisition_time / self.acquisitions_total
                    if self.acquisitions_total > 0
                    else 0.0
                ),
                "max_acquisition_time": self.max_acquisition_time,
                "avg_hold_time": (
                    self.total_hold_time / self.releases_total
                    if self.releases_total > 0
                    else 0.0
                ),
                "max_hold_time": self.max_hold_time,
            }


# Global metrics instance
_lock_metrics: LockMetrics | None = None
_metrics_lock = RLock()


def get_lock_metrics() -> LockMetrics:
    """
    Get or create the global lock metrics instance.

    Returns:
        LockMetrics instance
    """
    global _lock_metrics

    with _metrics_lock:
        if _lock_metrics is None:
            _lock_metrics = LockMetrics()
        return _lock_metrics


# ============================================================================
# Distributed Lock Implementation
# ============================================================================


class DistributedLock:
    """
    Redis-based distributed lock with automatic expiration.

    Implements a distributed lock using Redis SET with NX (not exists) and EX
    (expiration) options. The lock automatically releases after timeout to
    prevent deadlocks from process crashes.

    Example:
        # Basic usage with context manager
        async with DistributedLock("my-resource", timeout=30) as lock:
            await perform_critical_operation()

        # Manual lock management
        lock = DistributedLock("my-resource")
        if await lock.acquire(timeout=10):
            try:
                await perform_critical_operation()
            finally:
                await lock.release()
    """

    def __init__(
        self,
        name: str,
        timeout: float = DEFAULT_LOCK_TIMEOUT,
        redis_client: redis.Redis | None = None,
    ):
        """
        Initialize distributed lock.

        Args:
            name: Unique name for the lock resource
            timeout: Lock timeout in seconds (auto-release after this time)
            redis_client: Optional Redis client (creates new one if not provided)
        """
        self.name = name
        self.timeout = timeout
        self._redis_client = redis_client
        self._redis: redis.Redis | None = None
        self._settings = get_settings()
        self._token: str | None = None
        self._acquired = False
        self._renewal_task: asyncio.Task | None = None

    @property
    def lock_key(self) -> str:
        """Get the Redis key for this lock."""
        return f"{LOCK_KEY_PREFIX}:{self.name}"

    @property
    def owner_key(self) -> str:
        """Get the Redis key for lock owner info."""
        return f"{LOCK_OWNER_PREFIX}:{self.name}"

    async def _get_redis(self) -> redis.Redis:
        """
        Get or create async Redis connection.

        Returns:
            Redis client instance

        Raises:
            ConnectionError: If Redis is unavailable
        """
        if self._redis_client is not None:
            return self._redis_client

        if self._redis is None:
            redis_url = self._settings.redis_url_with_password
            self._redis = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            await self._redis.ping()

        return self._redis

    async def acquire(
        self,
        blocking: bool = True,
        acquisition_timeout: float = DEFAULT_ACQUISITION_TIMEOUT,
    ) -> bool:
        """
        Acquire the distributed lock.

        Args:
            blocking: If True, wait for lock to become available
            acquisition_timeout: Maximum time to wait for lock (if blocking)

        Returns:
            True if lock was acquired, False otherwise

        Raises:
            LockTimeoutError: If blocking and timeout is exceeded
            LockAcquisitionError: If lock acquisition fails
        """
        start_time = time.time()
        metrics = get_lock_metrics()

        try:
            redis_conn = await self._get_redis()

            # Generate unique token for this lock acquisition
            self._token = str(uuid.uuid4())

            while True:
                # Try to acquire lock using SET NX EX
                # NX: Only set if not exists
                # EX: Set expiration time
                acquired = await redis_conn.set(
                    self.lock_key,
                    self._token,
                    nx=True,
                    ex=int(self.timeout),
                )

                if acquired:
                    self._acquired = True

                    # Store owner metadata
                    owner_info = {
                        "token": self._token,
                        "acquired_at": datetime.utcnow().isoformat(),
                        "timeout": self.timeout,
                    }
                    await redis_conn.hset(
                        self.owner_key,
                        mapping=owner_info,  # type: ignore
                    )
                    await redis_conn.expire(self.owner_key, int(self.timeout) + 10)

                    # Record metrics
                    duration = time.time() - start_time
                    metrics.record_acquisition(self.name, duration, self._token)

                    logger.debug(
                        f"Acquired lock '{self.name}' with token {self._token[:8]}... "
                        f"in {duration:.3f}s"
                    )

                    return True

                # Lock not acquired
                if not blocking:
                    metrics.record_acquisition_failure(self.name, timed_out=False)
                    return False

                # Check if we've exceeded acquisition timeout
                elapsed = time.time() - start_time
                if elapsed >= acquisition_timeout:
                    metrics.record_acquisition_failure(self.name, timed_out=True)
                    raise LockTimeoutError(self.name, acquisition_timeout)

                # Wait a bit before retrying (exponential backoff)
                wait_time = min(0.1 * (2 ** min(elapsed, 5)), 1.0)
                await asyncio.sleep(wait_time)

        except redis.ConnectionError as e:
            logger.error(f"Redis connection error while acquiring lock: {e}")
            metrics.record_acquisition_failure(self.name, timed_out=False)
            raise LockAcquisitionError("Failed to acquire lock: Redis unavailable")
        except LockTimeoutError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error acquiring lock '{self.name}': {e}")
            metrics.record_acquisition_failure(self.name, timed_out=False)
            raise LockAcquisitionError(f"Failed to acquire lock: {str(e)}")

    async def release(self) -> bool:
        """
        Release the distributed lock.

        Only releases the lock if this instance owns it (token matches).

        Returns:
            True if lock was released, False if not owned by this instance

        Raises:
            LockError: If lock release fails
        """
        if not self._acquired or self._token is None:
            return False

        try:
            redis_conn = await self._get_redis()

            # Stop renewal task if running
            if self._renewal_task:
                self._renewal_task.cancel()
                try:
                    await self._renewal_task
                except asyncio.CancelledError:
                    pass
                self._renewal_task = None

            # Use Lua script to atomically check token and delete
            # This ensures we only delete our own lock
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                redis.call("del", KEYS[1])
                redis.call("del", KEYS[2])
                return 1
            else
                return 0
            end
            """

            result = await redis_conn.eval(
                lua_script,
                2,
                self.lock_key,
                self.owner_key,
                self._token,
            )

            if result == 1:
                self._acquired = False
                metrics = get_lock_metrics()
                metrics.record_release(self.name)

                logger.debug(
                    f"Released lock '{self.name}' with token {self._token[:8]}..."
                )

                return True
            else:
                logger.warning(
                    f"Failed to release lock '{self.name}': token mismatch "
                    f"(lock may have expired)"
                )
                return False

        except redis.ConnectionError as e:
            logger.error(f"Redis connection error while releasing lock: {e}")
            raise LockError("Failed to release lock: Redis unavailable")
        except Exception as e:
            logger.error(f"Unexpected error releasing lock '{self.name}': {e}")
            raise LockError(f"Failed to release lock: {str(e)}")

    async def extend(self, additional_time: float) -> bool:
        """
        Extend the lock timeout by additional seconds.

        Args:
            additional_time: Additional seconds to extend the lock

        Returns:
            True if lock was extended, False if not owned

        Raises:
            LockRenewalError: If lock extension fails
        """
        if not self._acquired or self._token is None:
            return False

        try:
            redis_conn = await self._get_redis()

            # Use Lua script to atomically check token and extend expiration
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                redis.call("expire", KEYS[1], ARGV[2])
                redis.call("expire", KEYS[2], ARGV[2] + 10)
                return 1
            else
                return 0
            end
            """

            new_timeout = int(self.timeout + additional_time)

            result = await redis_conn.eval(
                lua_script,
                2,
                self.lock_key,
                self.owner_key,
                self._token,
                new_timeout,
            )

            if result == 1:
                self.timeout = new_timeout
                metrics = get_lock_metrics()
                metrics.record_renewal(success=True)

                logger.debug(
                    f"Extended lock '{self.name}' by {additional_time}s "
                    f"(new timeout: {new_timeout}s)"
                )

                return True
            else:
                metrics = get_lock_metrics()
                metrics.record_renewal(success=False)
                logger.warning(
                    f"Failed to extend lock '{self.name}': token mismatch "
                    f"(lock may have expired)"
                )
                return False

        except redis.ConnectionError as e:
            logger.error(f"Redis connection error while extending lock: {e}")
            metrics = get_lock_metrics()
            metrics.record_renewal(success=False)
            raise LockRenewalError("Failed to extend lock: Redis unavailable")
        except Exception as e:
            logger.error(f"Unexpected error extending lock '{self.name}': {e}")
            metrics = get_lock_metrics()
            metrics.record_renewal(success=False)
            raise LockRenewalError(f"Failed to extend lock: {str(e)}")

    async def renew(self) -> bool:
        """
        Renew the lock by resetting its timeout.

        Returns:
            True if lock was renewed, False if not owned

        Raises:
            LockRenewalError: If lock renewal fails
        """
        if not self._acquired or self._token is None:
            return False

        try:
            redis_conn = await self._get_redis()

            # Use Lua script to atomically check token and reset expiration
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                redis.call("expire", KEYS[1], ARGV[2])
                redis.call("expire", KEYS[2], ARGV[2] + 10)
                return 1
            else
                return 0
            end
            """

            result = await redis_conn.eval(
                lua_script,
                2,
                self.lock_key,
                self.owner_key,
                self._token,
                int(self.timeout),
            )

            if result == 1:
                metrics = get_lock_metrics()
                metrics.record_renewal(success=True)

                logger.debug(f"Renewed lock '{self.name}' for {self.timeout}s")

                return True
            else:
                metrics = get_lock_metrics()
                metrics.record_renewal(success=False)
                logger.warning(
                    f"Failed to renew lock '{self.name}': token mismatch "
                    f"(lock may have expired)"
                )
                return False

        except redis.ConnectionError as e:
            logger.error(f"Redis connection error while renewing lock: {e}")
            metrics = get_lock_metrics()
            metrics.record_renewal(success=False)
            raise LockRenewalError("Failed to renew lock: Redis unavailable")
        except Exception as e:
            logger.error(f"Unexpected error renewing lock '{self.name}': {e}")
            metrics = get_lock_metrics()
            metrics.record_renewal(success=False)
            raise LockRenewalError(f"Failed to renew lock: {str(e)}")

    async def _auto_renew_task(self, interval: float) -> None:
        """
        Background task to automatically renew the lock.

        Args:
            interval: Renewal interval in seconds
        """
        try:
            while self._acquired:
                await asyncio.sleep(interval)
                if self._acquired:
                    await self.renew()
        except asyncio.CancelledError:
            # Task was cancelled (lock released)
            pass
        except Exception as e:
            logger.error(f"Error in auto-renewal task for lock '{self.name}': {e}")

    def start_auto_renewal(self, interval: float = DEFAULT_RENEWAL_INTERVAL) -> None:
        """
        Start automatic lock renewal in the background.

        Args:
            interval: Renewal interval in seconds (should be less than timeout)

        Raises:
            ValueError: If interval is greater than or equal to timeout
        """
        if interval >= self.timeout:
            raise ValueError(
                f"Renewal interval ({interval}s) must be less than "
                f"lock timeout ({self.timeout}s)"
            )

        if self._renewal_task is None or self._renewal_task.done():
            self._renewal_task = asyncio.create_task(self._auto_renew_task(interval))

    async def __aenter__(self):
        """Async context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.release()
        return False

    async def close(self) -> None:
        """Close Redis connection if we created it."""
        if self._renewal_task:
            self._renewal_task.cancel()
            try:
                await self._renewal_task
            except asyncio.CancelledError:
                pass

        if self._redis is not None and self._redis_client is None:
            await self._redis.close()


# ============================================================================
# Reentrant Lock Implementation
# ============================================================================


class ReentrantLock(DistributedLock):
    """
    Reentrant distributed lock allowing the same owner to acquire multiple times.

    Tracks acquisition count and only releases when count reaches zero.
    Useful for nested operations that need the same lock.

    Example:
        lock = ReentrantLock("resource", owner_id="worker-1")

        async with lock:  # Acquisition count: 1
            await operation_1()

            async with lock:  # Acquisition count: 2 (no blocking)
                await nested_operation()
            # Acquisition count: 1

        # Lock released when count reaches 0
    """

    def __init__(
        self,
        name: str,
        owner_id: str,
        timeout: float = DEFAULT_LOCK_TIMEOUT,
        redis_client: redis.Redis | None = None,
    ):
        """
        Initialize reentrant lock.

        Args:
            name: Unique name for the lock resource
            owner_id: Unique identifier for the lock owner (e.g., worker ID)
            timeout: Lock timeout in seconds
            redis_client: Optional Redis client
        """
        super().__init__(name, timeout, redis_client)
        self.owner_id = owner_id
        self._acquisition_count = 0
        self._reentrant_key = f"{LOCK_KEY_PREFIX}:reentrant:{self.name}:{owner_id}"

    async def acquire(
        self,
        blocking: bool = True,
        acquisition_timeout: float = DEFAULT_ACQUISITION_TIMEOUT,
    ) -> bool:
        """
        Acquire the reentrant lock.

        If the same owner already holds the lock, increments the acquisition count.

        Args:
            blocking: If True, wait for lock to become available
            acquisition_timeout: Maximum time to wait for lock

        Returns:
            True if lock was acquired, False otherwise
        """
        redis_conn = await self._get_redis()

        # Check if we already own this lock
        current_count = await redis_conn.get(self._reentrant_key)

        if current_count is not None:
            # We already own the lock - increment count
            self._acquisition_count = int(current_count) + 1
            await redis_conn.set(
                self._reentrant_key,
                self._acquisition_count,
                ex=int(self.timeout),
            )

            logger.debug(
                f"Reentrant lock '{self.name}' count increased to "
                f"{self._acquisition_count} for owner {self.owner_id}"
            )

            return True

        # We don't own the lock - try to acquire normally
        acquired = await super().acquire(blocking, acquisition_timeout)

        if acquired:
            self._acquisition_count = 1
            await redis_conn.set(
                self._reentrant_key,
                self._acquisition_count,
                ex=int(self.timeout),
            )

        return acquired

    async def release(self) -> bool:
        """
        Release the reentrant lock.

        Decrements acquisition count and only releases the lock when count reaches zero.

        Returns:
            True if lock was released/decremented, False otherwise
        """
        if self._acquisition_count == 0:
            return False

        redis_conn = await self._get_redis()

        self._acquisition_count -= 1

        if self._acquisition_count > 0:
            # Still holding the lock - update count
            await redis_conn.set(
                self._reentrant_key,
                self._acquisition_count,
                ex=int(self.timeout),
            )

            logger.debug(
                f"Reentrant lock '{self.name}' count decreased to "
                f"{self._acquisition_count} for owner {self.owner_id}"
            )

            return True
        else:
            # Count reached zero - fully release the lock
            await redis_conn.delete(self._reentrant_key)
            return await super().release()


# ============================================================================
# Fair Lock Implementation (FIFO Queue)
# ============================================================================


class FairLock(DistributedLock):
    """
    Fair distributed lock using FIFO queue.

    Ensures locks are acquired in the order they were requested,
    preventing starvation of long-waiting clients.

    Uses Redis sorted set with timestamp scores for queue ordering.

    Example:
        async with FairLock("schedule-generation", timeout=60) as lock:
            # Acquired in FIFO order
            await generate_schedule()
    """

    def __init__(
        self,
        name: str,
        timeout: float = DEFAULT_LOCK_TIMEOUT,
        redis_client: redis.Redis | None = None,
    ):
        """
        Initialize fair lock.

        Args:
            name: Unique name for the lock resource
            timeout: Lock timeout in seconds
            redis_client: Optional Redis client
        """
        super().__init__(name, timeout, redis_client)
        self._queue_position: float | None = None

    @property
    def queue_key(self) -> str:
        """Get the Redis key for the lock queue."""
        return f"{FAIR_LOCK_QUEUE_PREFIX}:{self.name}"

    async def acquire(
        self,
        blocking: bool = True,
        acquisition_timeout: float = DEFAULT_ACQUISITION_TIMEOUT,
    ) -> bool:
        """
        Acquire the fair lock in FIFO order.

        Args:
            blocking: If True, wait for lock to become available
            acquisition_timeout: Maximum time to wait for lock

        Returns:
            True if lock was acquired, False otherwise

        Raises:
            LockTimeoutError: If blocking and timeout is exceeded
        """
        start_time = time.time()
        redis_conn = await self._get_redis()

        # Generate unique token and add to queue
        self._token = str(uuid.uuid4())
        self._queue_position = time.time()

        # Add to queue with timestamp as score
        await redis_conn.zadd(
            self.queue_key,
            {self._token: self._queue_position},
        )

        # Set queue expiration
        await redis_conn.expire(self.queue_key, int(self.timeout) + 60)

        try:
            while True:
                # Check if we're first in queue
                first_in_queue = await redis_conn.zrange(self.queue_key, 0, 0)

                if first_in_queue and first_in_queue[0] == self._token:
                    # We're first - try to acquire lock
                    acquired = await super().acquire(blocking=False)

                    if acquired:
                        # Remove ourselves from queue
                        await redis_conn.zrem(self.queue_key, self._token)

                        logger.debug(
                            f"Acquired fair lock '{self.name}' after "
                            f"{time.time() - start_time:.3f}s in queue"
                        )

                        return True

                # Not our turn yet or lock not available
                if not blocking:
                    await redis_conn.zrem(self.queue_key, self._token)
                    return False

                # Check timeout
                elapsed = time.time() - start_time
                if elapsed >= acquisition_timeout:
                    await redis_conn.zrem(self.queue_key, self._token)
                    metrics = get_lock_metrics()
                    metrics.record_acquisition_failure(self.name, timed_out=True)
                    raise LockTimeoutError(self.name, acquisition_timeout)

                # Wait before checking again
                await asyncio.sleep(0.1)

        except Exception:
            # Clean up queue entry on error
            await redis_conn.zrem(self.queue_key, self._token)
            raise


# ============================================================================
# Deadlock Detection
# ============================================================================


@dataclass
class LockInfo:
    """Information about an active lock."""

    name: str
    owner: str
    acquired_at: datetime
    timeout: float


class DeadlockDetector:
    """
    Utility for detecting potential deadlocks in distributed locks.

    Analyzes lock ownership and wait patterns to identify circular
    dependencies that could lead to deadlocks.

    Example:
        detector = DeadlockDetector()
        deadlocks = await detector.detect_deadlocks()

        if deadlocks:
            logger.warning(f"Detected {len(deadlocks)} potential deadlocks")
            for cycle in deadlocks:
                logger.warning(f"Deadlock cycle: {cycle}")
    """

    def __init__(self, redis_client: redis.Redis | None = None):
        """
        Initialize deadlock detector.

        Args:
            redis_client: Optional Redis client
        """
        self._redis_client = redis_client
        self._redis: redis.Redis | None = None
        self._settings = get_settings()

    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection."""
        if self._redis_client is not None:
            return self._redis_client

        if self._redis is None:
            redis_url = self._settings.redis_url_with_password
            self._redis = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            await self._redis.ping()

        return self._redis

    async def get_active_locks(self) -> list[LockInfo]:
        """
        Get all currently active locks.

        Returns:
            List of LockInfo objects for active locks
        """
        redis_conn = await self._get_redis()

        # Find all lock keys
        lock_pattern = f"{LOCK_KEY_PREFIX}:*"
        lock_keys = []

        async for key in redis_conn.scan_iter(match=lock_pattern):
            if not key.startswith(f"{LOCK_OWNER_PREFIX}:"):
                lock_keys.append(key)

        # Get lock info for each key
        active_locks = []

        for lock_key in lock_keys:
            # Extract lock name
            lock_name = lock_key.replace(f"{LOCK_KEY_PREFIX}:", "")

            # Get owner info
            owner_key = f"{LOCK_OWNER_PREFIX}:{lock_name}"
            owner_info = await redis_conn.hgetall(owner_key)

            if owner_info:
                try:
                    acquired_at = datetime.fromisoformat(
                        owner_info.get("acquired_at", "")
                    )
                    timeout = float(owner_info.get("timeout", 0))
                    owner = owner_info.get("token", "unknown")

                    active_locks.append(
                        LockInfo(
                            name=lock_name,
                            owner=owner,
                            acquired_at=acquired_at,
                            timeout=timeout,
                        )
                    )
                except (ValueError, KeyError) as e:
                    logger.warning(f"Failed to parse lock info for {lock_name}: {e}")

        return active_locks

    async def detect_deadlocks(self) -> list[list[str]]:
        """
        Detect potential deadlock cycles.

        Analyzes lock ownership patterns to find circular wait conditions.

        Returns:
            List of deadlock cycles (each cycle is a list of lock names)
        """
        active_locks = await self.get_active_locks()

        # Simple deadlock detection based on timeout expiration
        # More sophisticated detection would require tracking wait-for graphs
        deadlocks = []
        current_time = datetime.utcnow()

        for lock in active_locks:
            # Check if lock has been held past its timeout (potential deadlock)
            age = (current_time - lock.acquired_at).total_seconds()

            if age > lock.timeout:
                deadlocks.append([lock.name])
                logger.warning(
                    f"Potential deadlock detected: Lock '{lock.name}' held for "
                    f"{age:.1f}s (timeout: {lock.timeout}s)"
                )

                # Record metric
                metrics = get_lock_metrics()
                metrics.record_deadlock()

        return deadlocks

    async def force_release_expired_locks(self) -> int:
        """
        Force release locks that have exceeded their timeout.

        This is a recovery mechanism for stuck locks. Use with caution.

        Returns:
            Number of locks released
        """
        redis_conn = await self._get_redis()
        active_locks = await self.get_active_locks()
        current_time = datetime.utcnow()
        released_count = 0

        for lock in active_locks:
            age = (current_time - lock.acquired_at).total_seconds()

            if age > lock.timeout:
                # Force delete the lock
                lock_key = f"{LOCK_KEY_PREFIX}:{lock.name}"
                owner_key = f"{LOCK_OWNER_PREFIX}:{lock.name}"

                await redis_conn.delete(lock_key, owner_key)
                released_count += 1

                logger.warning(
                    f"Force-released expired lock '{lock.name}' "
                    f"(held for {age:.1f}s, timeout: {lock.timeout}s)"
                )

        return released_count

    async def close(self) -> None:
        """Close Redis connection if we created it."""
        if self._redis is not None and self._redis_client is None:
            await self._redis.close()
