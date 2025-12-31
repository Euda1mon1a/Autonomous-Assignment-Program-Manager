"""Semaphore-based rate limiting and resource pooling.

Provides advanced semaphore utilities for controlling concurrent access
to resources and rate limiting.
"""
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

logger = logging.getLogger(__name__)


class SemaphorePool:
    """Semaphore pool for managing concurrent resource access."""

    def __init__(
        self,
        max_concurrent: int = 10,
        timeout: Optional[float] = None,
    ):
        """Initialize semaphore pool.

        Args:
            max_concurrent: Maximum concurrent acquisitions
            timeout: Optional timeout for acquisitions
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.stats = {
            "total_acquisitions": 0,
            "current_active": 0,
            "max_active": 0,
            "total_wait_time": 0.0,
            "timeouts": 0,
        }

    @asynccontextmanager
    async def acquire(self, timeout: Optional[float] = None):
        """Acquire semaphore with optional timeout.

        Args:
            timeout: Override default timeout

        Yields:
            None when acquired

        Raises:
            asyncio.TimeoutError: If timeout occurs
        """
        start_time = time.time()
        timeout_val = timeout if timeout is not None else self.timeout

        try:
            if timeout_val:
                async with asyncio.timeout(timeout_val):
                    async with self.semaphore:
                        self._track_acquisition(start_time)
                        yield
                        self._track_release()
            else:
                async with self.semaphore:
                    self._track_acquisition(start_time)
                    yield
                    self._track_release()

        except asyncio.TimeoutError:
            self.stats["timeouts"] += 1
            logger.warning(f"Semaphore acquisition timeout after {timeout_val}s")
            raise

    def _track_acquisition(self, start_time: float):
        """Track semaphore acquisition.

        Args:
            start_time: Acquisition start time
        """
        wait_time = time.time() - start_time

        self.stats["total_acquisitions"] += 1
        self.stats["current_active"] += 1
        self.stats["total_wait_time"] += wait_time

        if self.stats["current_active"] > self.stats["max_active"]:
            self.stats["max_active"] = self.stats["current_active"]

    def _track_release(self):
        """Track semaphore release."""
        self.stats["current_active"] -= 1

    async def get_stats(self) -> dict:
        """Get semaphore pool statistics.

        Returns:
            Statistics dictionary
        """
        avg_wait = (
            self.stats["total_wait_time"] / self.stats["total_acquisitions"]
            if self.stats["total_acquisitions"] > 0
            else 0.0
        )

        return {
            **self.stats,
            "max_concurrent": self.max_concurrent,
            "available": self.max_concurrent - self.stats["current_active"],
            "utilization": (
                self.stats["current_active"] / self.max_concurrent * 100
            ),
            "average_wait_time": round(avg_wait, 4),
        }


class RateLimiter:
    """Token bucket rate limiter for async operations."""

    def __init__(
        self,
        rate: int,
        per: float = 1.0,
        burst: Optional[int] = None,
    ):
        """Initialize rate limiter.

        Args:
            rate: Number of operations allowed
            per: Time period in seconds
            burst: Maximum burst size (defaults to rate)
        """
        self.rate = rate
        self.per = per
        self.burst = burst or rate
        self.tokens = float(self.burst)
        self.last_update = time.time()
        self.lock = asyncio.Lock()
        self.stats = {
            "total_requests": 0,
            "allowed": 0,
            "throttled": 0,
        }

    async def acquire(self, tokens: int = 1, wait: bool = True) -> bool:
        """Acquire tokens from rate limiter.

        Args:
            tokens: Number of tokens to acquire
            wait: If True, wait for tokens to become available

        Returns:
            True if tokens acquired, False if throttled (when wait=False)
        """
        async with self.lock:
            self._update_tokens()

            self.stats["total_requests"] += 1

            if self.tokens >= tokens:
                self.tokens -= tokens
                self.stats["allowed"] += 1
                return True

            if not wait:
                self.stats["throttled"] += 1
                return False

            # Wait for tokens to become available
            wait_time = (tokens - self.tokens) * (self.per / self.rate)
            await asyncio.sleep(wait_time)

            self._update_tokens()
            self.tokens -= tokens
            self.stats["allowed"] += 1
            return True

    def _update_tokens(self):
        """Update token bucket based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update

        # Add tokens based on rate
        tokens_to_add = elapsed * (self.rate / self.per)
        self.tokens = min(self.burst, self.tokens + tokens_to_add)
        self.last_update = now

    @asynccontextmanager
    async def __call__(self, tokens: int = 1):
        """Context manager for rate limiting.

        Args:
            tokens: Number of tokens to acquire

        Yields:
            None when tokens acquired

        Example:
            async with rate_limiter(tokens=5):
                await expensive_operation()
        """
        await self.acquire(tokens)
        yield

    async def get_stats(self) -> dict:
        """Get rate limiter statistics.

        Returns:
            Statistics dictionary
        """
        async with self.lock:
            self._update_tokens()

            throttle_rate = (
                self.stats["throttled"] / self.stats["total_requests"] * 100
                if self.stats["total_requests"] > 0
                else 0.0
            )

            return {
                **self.stats,
                "rate": self.rate,
                "per": self.per,
                "burst": self.burst,
                "available_tokens": round(self.tokens, 2),
                "throttle_rate": round(throttle_rate, 2),
            }


class AdaptiveRateLimiter(RateLimiter):
    """Rate limiter that adapts based on error rates."""

    def __init__(
        self,
        initial_rate: int,
        per: float = 1.0,
        min_rate: int = 1,
        max_rate: int = 1000,
        error_threshold: float = 0.05,  # 5% error rate
        adjustment_factor: float = 0.5,
    ):
        """Initialize adaptive rate limiter.

        Args:
            initial_rate: Starting rate
            per: Time period in seconds
            min_rate: Minimum allowed rate
            max_rate: Maximum allowed rate
            error_threshold: Error rate threshold for adjustment
            adjustment_factor: Rate adjustment factor (0.5 = halve on errors)
        """
        super().__init__(initial_rate, per)
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.error_threshold = error_threshold
        self.adjustment_factor = adjustment_factor
        self.errors = 0
        self.successes = 0

    async def report_success(self):
        """Report successful operation."""
        async with self.lock:
            self.successes += 1
            await self._adjust_rate()

    async def report_error(self):
        """Report failed operation."""
        async with self.lock:
            self.errors += 1
            await self._adjust_rate()

    async def _adjust_rate(self):
        """Adjust rate based on error rate."""
        total = self.errors + self.successes

        if total >= 100:  # Adjust every 100 operations
            error_rate = self.errors / total

            if error_rate > self.error_threshold:
                # Decrease rate
                new_rate = int(self.rate * self.adjustment_factor)
                self.rate = max(self.min_rate, new_rate)
                logger.info(f"Rate decreased to {self.rate} due to errors")
            else:
                # Increase rate
                new_rate = int(self.rate / self.adjustment_factor)
                self.rate = min(self.max_rate, new_rate)
                logger.info(f"Rate increased to {self.rate}")

            # Reset counters
            self.errors = 0
            self.successes = 0


# Global instances
_semaphore_pools: dict[str, SemaphorePool] = {}
_rate_limiters: dict[str, RateLimiter] = {}


def get_semaphore_pool(
    name: str,
    max_concurrent: int = 10,
) -> SemaphorePool:
    """Get or create named semaphore pool.

    Args:
        name: Pool name
        max_concurrent: Maximum concurrent operations

    Returns:
        SemaphorePool instance
    """
    if name not in _semaphore_pools:
        _semaphore_pools[name] = SemaphorePool(max_concurrent=max_concurrent)
    return _semaphore_pools[name]


def get_rate_limiter(
    name: str,
    rate: int,
    per: float = 1.0,
) -> RateLimiter:
    """Get or create named rate limiter.

    Args:
        name: Limiter name
        rate: Operations per period
        per: Time period in seconds

    Returns:
        RateLimiter instance
    """
    if name not in _rate_limiters:
        _rate_limiters[name] = RateLimiter(rate=rate, per=per)
    return _rate_limiters[name]
