"""
Storage layer for request deduplication.

Provides Redis-based storage for tracking request state, caching responses,
and managing concurrent request processing.
"""

import asyncio
import logging
import pickle
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RequestStatus(str, Enum):
    """Status of a deduplicated request."""

    PROCESSING = "processing"  # Request currently being processed
    COMPLETED = "completed"  # Request completed successfully
    FAILED = "failed"  # Request failed with error


@dataclass
class RequestRecord:
    """
    Record of a deduplicated request.

    Tracks request state, timing, and cached response.
    """

    idempotency_key: str  # Unique idempotency key
    status: RequestStatus  # Current processing status
    created_at: float  # Timestamp when request started
    completed_at: float | None = None  # Timestamp when request completed
    ttl: int = 300  # Time-to-live in seconds
    response_status: int | None = None  # HTTP status code
    response_headers: dict[str, str] | None = None  # Response headers
    response_body: bytes | None = None  # Cached response body
    error_message: str | None = None  # Error message if failed

    def is_expired(self) -> bool:
        """
        Check if request record has expired.

        Returns:
            True if record has exceeded its TTL, False otherwise
        """
        age = time.time() - self.created_at
        return age > self.ttl

    def is_processing(self) -> bool:
        """Check if request is currently being processed."""
        return self.status == RequestStatus.PROCESSING

    def is_completed(self) -> bool:
        """Check if request has completed successfully."""
        return self.status == RequestStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if request has failed."""
        return self.status == RequestStatus.FAILED


class DeduplicationStorage:
    """
    Redis-based storage for request deduplication.

    Manages request records, response caching, and provides
    distributed locking for concurrent request handling.
    """

    # Redis key prefixes
    KEY_PREFIX = "dedup"
    RECORD_PREFIX = "dedup:record"
    LOCK_PREFIX = "dedup:lock"

    # Default timeouts
    DEFAULT_TTL = 300  # 5 minutes
    LOCK_TIMEOUT = 60  # 60 seconds for lock
    LOCK_POLLING_INTERVAL = 0.1  # 100ms between lock checks

    def __init__(
        self,
        redis_client: redis.Redis | None = None,
        default_ttl: int = DEFAULT_TTL,
    ):
        """
        Initialize deduplication storage.

        Args:
            redis_client: Optional Redis client (creates new if not provided)
            default_ttl: Default time-to-live for request records in seconds
        """
        self.redis = redis_client
        self.default_ttl = default_ttl
        self._local_locks: dict[str, asyncio.Lock] = {}  # Fallback local locks

    def _get_record_key(self, idempotency_key: str) -> str:
        """
        Generate Redis key for request record.

        Args:
            idempotency_key: Idempotency key

        Returns:
            Full Redis key
        """
        return f"{self.RECORD_PREFIX}:{idempotency_key}"

    def _get_lock_key(self, idempotency_key: str) -> str:
        """
        Generate Redis key for distributed lock.

        Args:
            idempotency_key: Idempotency key

        Returns:
            Full Redis key
        """
        return f"{self.LOCK_PREFIX}:{idempotency_key}"

    async def _get_local_lock(self, key: str) -> asyncio.Lock:
        """
        Get or create a local lock for fallback.

        Args:
            key: Lock key

        Returns:
            Asyncio lock
        """
        if key not in self._local_locks:
            self._local_locks[key] = asyncio.Lock()
        return self._local_locks[key]

    async def acquire_lock(
        self,
        idempotency_key: str,
        timeout: float = LOCK_TIMEOUT,
    ) -> tuple[bool, str | None]:
        """
        Acquire a distributed lock for request processing.

        Uses Redis SET with NX (set if not exists) for atomic locking.

        Args:
            idempotency_key: Idempotency key to lock
            timeout: Lock timeout in seconds

        Returns:
            Tuple of (acquired, lock_id) where:
                - acquired: True if lock was acquired
                - lock_id: Unique lock identifier for release
        """
        if not self.redis:
            # Fallback to local lock if Redis unavailable
            lock = await self._get_local_lock(idempotency_key)
            acquired = lock.locked()
            if not acquired:
                await lock.acquire()
            return True, idempotency_key

        lock_key = self._get_lock_key(idempotency_key)
        lock_id = f"{idempotency_key}:{time.time()}"

        try:
            # Try to acquire lock with expiry
            acquired = await self.redis.set(
                lock_key,
                lock_id,
                nx=True,
                ex=int(timeout),
            )

            if acquired:
                logger.debug(f"Acquired lock for idempotency key: {idempotency_key}")
                return True, lock_id
            else:
                logger.debug(
                    f"Lock already held for idempotency key: {idempotency_key}"
                )
                return False, None

        except Exception as e:
            logger.error(f"Error acquiring lock: {e}")
            # Fail open: allow request if Redis fails
            return True, None

    async def release_lock(self, idempotency_key: str, lock_id: str | None) -> bool:
        """
        Release a distributed lock.

        Args:
            idempotency_key: Idempotency key
            lock_id: Lock identifier from acquire_lock

        Returns:
            True if lock was released successfully
        """
        if not self.redis or not lock_id:
            # Release local lock if using fallback
            if idempotency_key in self._local_locks:
                lock = self._local_locks[idempotency_key]
                if lock.locked():
                    lock.release()
            return True

        lock_key = self._get_lock_key(idempotency_key)

        try:
            # Only release if we own the lock (atomic check-and-delete)
            lua_script = """
            local lock_key = KEYS[1]
            local lock_id = ARGV[1]

            local current_id = redis.call('GET', lock_key)

            if current_id == lock_id then
                redis.call('DEL', lock_key)
                return 1
            else
                return 0
            end
            """

            result = await self.redis.eval(lua_script, 1, lock_key, lock_id)

            if result == 1:
                logger.debug(f"Released lock for idempotency key: {idempotency_key}")
                return True
            else:
                logger.warning(f"Failed to release lock (not owner): {idempotency_key}")
                return False

        except Exception as e:
            logger.error(f"Error releasing lock: {e}")
            return False

    async def wait_for_completion(
        self,
        idempotency_key: str,
        timeout: float = 30.0,
    ) -> RequestRecord | None:
        """
        Wait for a request to complete processing.

        Polls Redis for request completion or timeout.

        Args:
            idempotency_key: Idempotency key to wait for
            timeout: Maximum time to wait in seconds

        Returns:
            Completed RequestRecord or None if timed out
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            record = await self.get_record(idempotency_key)

            if record and not record.is_processing():
                return record

            # Wait before polling again
            await asyncio.sleep(self.LOCK_POLLING_INTERVAL)

        logger.warning(f"Wait for completion timed out: {idempotency_key}")
        return None

    async def create_record(
        self,
        idempotency_key: str,
        ttl: int | None = None,
    ) -> RequestRecord:
        """
        Create a new request record in PROCESSING state.

        Args:
            idempotency_key: Idempotency key
            ttl: Time-to-live in seconds (uses default if None)

        Returns:
            Created RequestRecord
        """
        ttl = ttl or self.default_ttl

        record = RequestRecord(
            idempotency_key=idempotency_key,
            status=RequestStatus.PROCESSING,
            created_at=time.time(),
            ttl=ttl,
        )

        await self.save_record(record)
        return record

    async def save_record(self, record: RequestRecord) -> bool:
        """
        Save request record to Redis.

        Args:
            record: RequestRecord to save

        Returns:
            True if saved successfully
        """
        if not self.redis:
            return False

        key = self._get_record_key(record.idempotency_key)

        try:
            # Serialize record
            data = pickle.dumps(record)

            # Save with TTL
            await self.redis.setex(key, record.ttl, data)

            logger.debug(f"Saved request record: {record.idempotency_key}")
            return True

        except Exception as e:
            logger.error(f"Error saving request record: {e}")
            return False

    async def get_record(self, idempotency_key: str) -> RequestRecord | None:
        """
        Get request record from Redis.

        Args:
            idempotency_key: Idempotency key

        Returns:
            RequestRecord or None if not found
        """
        if not self.redis:
            return None

        key = self._get_record_key(idempotency_key)

        try:
            data = await self.redis.get(key)

            if data is None:
                return None

            # Deserialize record
            record = pickle.loads(data)

            # Check expiration
            if record.is_expired():
                await self.delete_record(idempotency_key)
                return None

            return record

        except Exception as e:
            logger.error(f"Error getting request record: {e}")
            return None

    async def update_record(
        self,
        idempotency_key: str,
        status: RequestStatus,
        response_status: int | None = None,
        response_headers: dict[str, str] | None = None,
        response_body: bytes | None = None,
        error_message: str | None = None,
    ) -> bool:
        """
        Update request record with completion data.

        Args:
            idempotency_key: Idempotency key
            status: New request status
            response_status: HTTP status code
            response_headers: Response headers to cache
            response_body: Response body to cache
            error_message: Error message if failed

        Returns:
            True if updated successfully
        """
        record = await self.get_record(idempotency_key)

        if not record:
            logger.warning(f"Cannot update non-existent record: {idempotency_key}")
            return False

        # Update record fields
        record.status = status
        record.completed_at = time.time()
        record.response_status = response_status
        record.response_headers = response_headers
        record.response_body = response_body
        record.error_message = error_message

        return await self.save_record(record)

    async def delete_record(self, idempotency_key: str) -> bool:
        """
        Delete request record from Redis.

        Args:
            idempotency_key: Idempotency key

        Returns:
            True if deleted successfully
        """
        if not self.redis:
            return False

        key = self._get_record_key(idempotency_key)

        try:
            deleted = await self.redis.delete(key)
            return deleted > 0

        except Exception as e:
            logger.error(f"Error deleting request record: {e}")
            return False

    async def cleanup_expired(self) -> int:
        """
        Clean up expired request records.

        Note: This is a best-effort cleanup. Redis automatically expires
        keys with TTL, but this can be used for manual cleanup.

        Returns:
            Number of records cleaned up
        """
        if not self.redis:
            return 0

        try:
            pattern = f"{self.RECORD_PREFIX}:*"
            cursor = 0
            cleaned = 0

            while True:
                cursor, keys = await self.redis.scan(
                    cursor,
                    match=pattern,
                    count=100,
                )

                for key in keys:
                    # Check if expired and delete
                    data = await self.redis.get(key)
                    if data:
                        record = pickle.loads(data)
                        if record.is_expired():
                            await self.redis.delete(key)
                            cleaned += 1

                if cursor == 0:
                    break

            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired request records")

            return cleaned

        except Exception as e:
            logger.error(f"Error cleaning up expired records: {e}")
            return 0

    async def get_stats(self) -> dict[str, Any]:
        """
        Get deduplication statistics.

        Returns:
            Dictionary with statistics
        """
        if not self.redis:
            return {
                "total_records": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0,
            }

        try:
            pattern = f"{self.RECORD_PREFIX}:*"
            cursor = 0
            stats = {
                "total_records": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0,
            }

            while True:
                cursor, keys = await self.redis.scan(
                    cursor,
                    match=pattern,
                    count=100,
                )

                for key in keys:
                    data = await self.redis.get(key)
                    if data:
                        record = pickle.loads(data)
                        stats["total_records"] += 1

                        if record.status == RequestStatus.PROCESSING:
                            stats["processing"] += 1
                        elif record.status == RequestStatus.COMPLETED:
                            stats["completed"] += 1
                        elif record.status == RequestStatus.FAILED:
                            stats["failed"] += 1

                if cursor == 0:
                    break

            return stats

        except Exception as e:
            logger.error(f"Error getting deduplication stats: {e}")
            return {
                "total_records": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0,
                "error": str(e),
            }
