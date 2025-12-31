"""Distributed locking with Redis for concurrent operations.

Provides distributed locks to prevent race conditions in cache updates.
"""

import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from app.cache.cache_manager import get_cache_manager

logger = logging.getLogger(__name__)


class DistributedLock:
    """Redis-based distributed lock."""

    def __init__(
        self,
        name: str,
        timeout: int = 10,
        retry_interval: float = 0.1,
    ):
        """Initialize distributed lock.

        Args:
            name: Lock name (should be unique)
            timeout: Lock timeout in seconds
            retry_interval: Time to wait between acquire retries
        """
        self.name = f"lock:{name}"
        self.timeout = timeout
        self.retry_interval = retry_interval
        self.identifier = str(uuid.uuid4())
        self.cache = get_cache_manager()

    async def acquire(
        self, blocking: bool = True, timeout: float | None = None
    ) -> bool:
        """Acquire the lock.

        Args:
            blocking: If True, wait for lock to become available
            timeout: Maximum time to wait for lock (None = wait indefinitely)

        Returns:
            True if lock acquired
        """
        await self.cache.connect()

        end_time = time.time() + timeout if timeout else None

        while True:
            # Try to acquire lock
            result = await self.cache._redis.set(
                self.name,
                self.identifier,
                nx=True,  # Only set if not exists
                ex=self.timeout,  # Expire after timeout
            )

            if result:
                logger.debug(f"Lock acquired: {self.name} ({self.identifier})")
                return True

            if not blocking:
                return False

            if end_time and time.time() >= end_time:
                logger.warning(f"Lock acquisition timeout: {self.name}")
                return False

            # Wait before retrying
            await asyncio.sleep(self.retry_interval)

    async def release(self) -> bool:
        """Release the lock.

        Returns:
            True if lock was released by this instance
        """
        await self.cache.connect()

        # Lua script for atomic check-and-delete
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """

        result = await self.cache._redis.eval(
            lua_script,
            1,
            self.name,
            self.identifier,
        )

        if result:
            logger.debug(f"Lock released: {self.name} ({self.identifier})")
            return True
        else:
            logger.warning(
                f"Lock release failed - not owner: {self.name} ({self.identifier})"
            )
            return False

    async def extend(self, additional_time: int) -> bool:
        """Extend lock timeout.

        Args:
            additional_time: Additional seconds to extend

        Returns:
            True if extended successfully
        """
        await self.cache.connect()

        # Lua script for atomic check-and-extend
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("expire", KEYS[1], ARGV[2])
        else
            return 0
        end
        """

        result = await self.cache._redis.eval(
            lua_script,
            1,
            self.name,
            self.identifier,
            str(self.timeout + additional_time),
        )

        if result:
            logger.debug(f"Lock extended: {self.name} (+{additional_time}s)")
            return True
        return False

    async def is_locked(self) -> bool:
        """Check if lock is currently held.

        Returns:
            True if lock is held (by anyone)
        """
        await self.cache.connect()
        return await self.cache.exists(self.name)

    async def get_owner(self) -> str | None:
        """Get current lock owner identifier.

        Returns:
            Owner identifier or None if not locked
        """
        await self.cache.connect()
        return await self.cache.get(self.name)

    @asynccontextmanager
    async def __call__(self, blocking: bool = True, timeout: float | None = None):
        """Context manager for automatic lock acquire/release.

        Args:
            blocking: If True, wait for lock
            timeout: Maximum wait time

        Yields:
            True if lock acquired

        Example:
            async with DistributedLock("my_resource"):
                # Critical section - lock is held
                await do_work()
            # Lock is automatically released
        """
        acquired = await self.acquire(blocking=blocking, timeout=timeout)

        if not acquired:
            raise TimeoutError(f"Could not acquire lock: {self.name}")

        try:
            yield acquired
        finally:
            await self.release()


class LockManager:
    """Manager for multiple distributed locks."""

    def __init__(self):
        """Initialize lock manager."""
        self.locks: dict[str, DistributedLock] = {}

    def get_lock(
        self,
        name: str,
        timeout: int = 10,
        retry_interval: float = 0.1,
    ) -> DistributedLock:
        """Get or create a lock.

        Args:
            name: Lock name
            timeout: Lock timeout in seconds
            retry_interval: Retry interval

        Returns:
            DistributedLock instance
        """
        if name not in self.locks:
            self.locks[name] = DistributedLock(name, timeout, retry_interval)
        return self.locks[name]

    @asynccontextmanager
    async def lock(
        self,
        name: str,
        blocking: bool = True,
        timeout: float | None = None,
    ):
        """Context manager for lock acquisition.

        Args:
            name: Lock name
            blocking: If True, wait for lock
            timeout: Maximum wait time

        Yields:
            Lock instance

        Example:
            async with lock_manager.lock("resource"):
                await do_work()
        """
        lock = self.get_lock(name)
        async with lock(blocking=blocking, timeout=timeout):
            yield lock


# Global lock manager
_lock_manager: LockManager | None = None


def get_lock_manager() -> LockManager:
    """Get global lock manager instance.

    Returns:
        LockManager singleton
    """
    global _lock_manager
    if _lock_manager is None:
        _lock_manager = LockManager()
    return _lock_manager
