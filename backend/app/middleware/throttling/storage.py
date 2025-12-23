"""
Storage layer for throttling state management.

Provides Redis-based storage for tracking concurrent requests,
queue state, and throttling metrics.
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass

import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class RequestSlot:
    """Represents an active request slot."""

    request_id: str  # Unique request identifier
    user_id: str | None  # User making the request
    endpoint: str  # Endpoint being accessed
    priority: str  # Request priority level
    started_at: float  # Timestamp when request started
    timeout_at: float  # Timestamp when request times out


@dataclass
class QueuedRequest:
    """Represents a queued request awaiting processing."""

    request_id: str  # Unique request identifier
    user_id: str | None  # User making the request
    endpoint: str  # Endpoint being accessed
    priority: str  # Request priority level
    queued_at: float  # Timestamp when request was queued
    timeout_at: float  # Timestamp when request times out


@dataclass
class ThrottleMetrics:
    """Metrics for throttling state."""

    active_requests: int  # Current active requests
    queued_requests: int  # Current queued requests
    total_capacity: int  # Total capacity
    utilization: float  # Current utilization (0.0 to 1.0)
    queue_utilization: float  # Queue utilization (0.0 to 1.0)


class ThrottleStorage:
    """
    Redis-based storage for throttling state.

    Manages concurrent request tracking, request queuing,
    and provides metrics for monitoring.
    """

    def __init__(self, redis_client: redis.Redis | None = None):
        """
        Initialize throttle storage.

        Args:
            redis_client: Optional Redis client (creates new if not provided)
        """
        self.redis = redis_client
        self._local_locks: dict[str, asyncio.Lock] = {}  # Fallback local locks

    async def _get_lock(self, key: str) -> asyncio.Lock:
        """Get or create a local lock for fallback."""
        if key not in self._local_locks:
            self._local_locks[key] = asyncio.Lock()
        return self._local_locks[key]

    async def acquire_slot(
        self,
        request_id: str,
        user_id: str | None,
        endpoint: str,
        priority: str,
        max_concurrent: int,
        timeout: float,
    ) -> tuple[bool, str | None]:
        """
        Try to acquire a request slot.

        Args:
            request_id: Unique request identifier
            user_id: User making the request
            endpoint: Endpoint being accessed
            priority: Request priority level
            max_concurrent: Maximum concurrent requests allowed
            timeout: Request timeout in seconds

        Returns:
            Tuple of (acquired, reason) where:
                - acquired: True if slot was acquired
                - reason: Reason if slot was not acquired
        """
        if not self.redis:
            # Fallback: always allow if Redis unavailable
            return True, None

        key = "throttle:active"
        now = time.time()
        timeout_at = now + timeout

        try:
            # Create request slot data
            slot = RequestSlot(
                request_id=request_id,
                user_id=user_id,
                endpoint=endpoint,
                priority=priority,
                started_at=now,
                timeout_at=timeout_at,
            )

            # Use Lua script for atomic check-and-set
            lua_script = """
            local key = KEYS[1]
            local max_concurrent = tonumber(ARGV[1])
            local request_id = ARGV[2]
            local slot_data = ARGV[3]
            local now = tonumber(ARGV[4])

            -- Clean up expired slots
            local expired = redis.call('ZREMRANGEBYSCORE', key, '-inf', now)

            -- Check current count
            local current = redis.call('ZCARD', key)

            if current >= max_concurrent then
                return 0  -- Slot not available
            end

            -- Add new slot with timeout as score
            redis.call('ZADD', key, ARGV[5], request_id .. ':' .. slot_data)

            return 1  -- Slot acquired
            """

            result = await self.redis.eval(
                lua_script,
                1,
                key,
                max_concurrent,
                request_id,
                json.dumps(asdict(slot)),
                now,
                timeout_at,
            )

            if result == 1:
                return True, None
            else:
                return False, "Maximum concurrent requests reached"

        except Exception as e:
            logger.error(f"Error acquiring throttle slot: {e}")
            # Fail open: allow request if Redis fails
            return True, None

    async def release_slot(self, request_id: str) -> bool:
        """
        Release a request slot.

        Args:
            request_id: Request identifier to release

        Returns:
            True if released successfully
        """
        if not self.redis:
            return True

        key = "throttle:active"

        try:
            # Remove all entries with this request_id prefix
            # (format is request_id:slot_data)
            pattern = f"{request_id}:*"

            # Get all members
            members = await self.redis.zrange(key, 0, -1)

            # Find and remove matching members
            for member in members:
                if isinstance(member, bytes):
                    member = member.decode("utf-8")
                if member.startswith(f"{request_id}:"):
                    await self.redis.zrem(key, member)
                    logger.debug(f"Released throttle slot for request {request_id}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error releasing throttle slot: {e}")
            return False

    async def enqueue_request(
        self,
        request_id: str,
        user_id: str | None,
        endpoint: str,
        priority: str,
        max_queue_size: int,
        timeout: float,
    ) -> tuple[bool, str | None]:
        """
        Add request to queue.

        Args:
            request_id: Unique request identifier
            user_id: User making the request
            endpoint: Endpoint being accessed
            priority: Request priority level
            max_queue_size: Maximum queue size
            timeout: Queue timeout in seconds

        Returns:
            Tuple of (enqueued, reason) where:
                - enqueued: True if request was queued
                - reason: Reason if request was not queued
        """
        if not self.redis:
            return False, "Queueing not available"

        key = "throttle:queue"
        now = time.time()
        timeout_at = now + timeout

        try:
            # Create queued request data
            queued = QueuedRequest(
                request_id=request_id,
                user_id=user_id,
                endpoint=endpoint,
                priority=priority,
                queued_at=now,
                timeout_at=timeout_at,
            )

            # Priority score: combine priority level with timestamp
            # Lower score = higher priority
            priority_scores = {
                "critical": 1000,
                "high": 2000,
                "normal": 3000,
                "low": 4000,
                "background": 5000,
            }
            priority_score = priority_scores.get(priority, 3000)
            score = priority_score + now  # Add timestamp for FIFO within priority

            # Check queue size and add
            lua_script = """
            local key = KEYS[1]
            local max_size = tonumber(ARGV[1])
            local request_id = ARGV[2]
            local data = ARGV[3]
            local score = tonumber(ARGV[4])
            local now = tonumber(ARGV[5])

            -- Clean up expired requests
            redis.call('ZREMRANGEBYSCORE', key, '-inf', now)

            -- Check current size
            local current = redis.call('ZCARD', key)

            if current >= max_size then
                return 0  -- Queue full
            end

            -- Add to queue
            redis.call('ZADD', key, score, request_id .. ':' .. data)

            return 1  -- Queued successfully
            """

            result = await self.redis.eval(
                lua_script,
                1,
                key,
                max_queue_size,
                request_id,
                json.dumps(asdict(queued)),
                score,
                now,
            )

            if result == 1:
                return True, None
            else:
                return False, "Queue is full"

        except Exception as e:
            logger.error(f"Error enqueueing request: {e}")
            return False, f"Queue error: {str(e)}"

    async def dequeue_request(self, request_id: str) -> bool:
        """
        Remove request from queue.

        Args:
            request_id: Request identifier to dequeue

        Returns:
            True if dequeued successfully
        """
        if not self.redis:
            return True

        key = "throttle:queue"

        try:
            # Find and remove the request
            members = await self.redis.zrange(key, 0, -1)

            for member in members:
                if isinstance(member, bytes):
                    member = member.decode("utf-8")
                if member.startswith(f"{request_id}:"):
                    await self.redis.zrem(key, member)
                    return True

            return False

        except Exception as e:
            logger.error(f"Error dequeuing request: {e}")
            return False

    async def get_metrics(
        self,
        max_concurrent: int,
        max_queue_size: int,
    ) -> ThrottleMetrics:
        """
        Get current throttling metrics.

        Args:
            max_concurrent: Maximum concurrent requests
            max_queue_size: Maximum queue size

        Returns:
            ThrottleMetrics with current state
        """
        if not self.redis:
            return ThrottleMetrics(
                active_requests=0,
                queued_requests=0,
                total_capacity=max_concurrent,
                utilization=0.0,
                queue_utilization=0.0,
            )

        try:
            now = time.time()

            # Clean up expired entries
            await self.redis.zremrangebyscore("throttle:active", "-inf", now)
            await self.redis.zremrangebyscore("throttle:queue", "-inf", now)

            # Get counts
            active = await self.redis.zcard("throttle:active")
            queued = await self.redis.zcard("throttle:queue")

            # Calculate utilization
            utilization = active / max_concurrent if max_concurrent > 0 else 0.0
            queue_util = queued / max_queue_size if max_queue_size > 0 else 0.0

            return ThrottleMetrics(
                active_requests=active,
                queued_requests=queued,
                total_capacity=max_concurrent,
                utilization=min(utilization, 1.0),
                queue_utilization=min(queue_util, 1.0),
            )

        except Exception as e:
            logger.error(f"Error getting throttle metrics: {e}")
            return ThrottleMetrics(
                active_requests=0,
                queued_requests=0,
                total_capacity=max_concurrent,
                utilization=0.0,
                queue_utilization=0.0,
            )

    async def cleanup_expired(self) -> tuple[int, int]:
        """
        Clean up expired requests from active and queue.

        Returns:
            Tuple of (active_cleaned, queue_cleaned)
        """
        if not self.redis:
            return 0, 0

        try:
            now = time.time()

            active_cleaned = await self.redis.zremrangebyscore(
                "throttle:active", "-inf", now
            )
            queue_cleaned = await self.redis.zremrangebyscore(
                "throttle:queue", "-inf", now
            )

            return active_cleaned, queue_cleaned

        except Exception as e:
            logger.error(f"Error cleaning up expired requests: {e}")
            return 0, 0
