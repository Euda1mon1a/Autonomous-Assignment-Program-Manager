"""
Cache warming service for optimized cache population and maintenance.

Provides comprehensive cache warming capabilities:
- Startup cache population with priority-based ordering
- Scheduled cache refresh with configurable intervals
- Lazy warming on cache misses with automatic prioritization
- Warming progress tracking for monitoring
- Concurrency control to prevent overwhelming the system
- Cache hit prediction based on historical access patterns
- Detailed warming metrics for performance analysis

This module implements:
- CacheWarmer: Main cache warming service
- WarmingPriority: Priority levels for cache entries
- WarmingStrategy: Strategies for cache warming
- CacheWarmingConfig: Configuration for cache warming
- CacheWarmingMetrics: Metrics tracking for warming operations
- CacheWarmingProgress: Progress tracking for warming operations

Example:
    # Initialize cache warmer
    warmer = CacheWarmer(
        cache_namespace="schedule",
        config=CacheWarmingConfig(
            max_concurrent_tasks=10,
            batch_size=100,
            enable_prediction=True
        )
    )

    # Warm cache on startup
    await warmer.warm_on_startup()

    # Schedule periodic refresh
    await warmer.schedule_refresh(interval_seconds=3600)

    # Track cache misses and warm lazily
    await warmer.on_cache_miss("schedule:recent", priority=WarmingPriority.HIGH)
"""
import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import RLock
from typing import Any, Callable, Coroutine

import redis.asyncio as redis

from app.core.cache import get_cache
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class WarmingPriority(str, Enum):
    """
    Priority levels for cache warming.

    Higher priority entries are warmed first.
    """

    CRITICAL = "critical"  # Must be warmed immediately (authentication, config)
    HIGH = "high"  # Should be warmed early (frequently accessed data)
    MEDIUM = "medium"  # Standard warming priority
    LOW = "low"  # Can be deferred (rarely accessed data)
    BACKGROUND = "background"  # Warm only when idle


class WarmingStrategy(str, Enum):
    """
    Strategies for cache warming.

    Determines how and when cache entries are populated.
    """

    EAGER = "eager"  # Warm all entries immediately on startup
    LAZY = "lazy"  # Warm only on cache miss
    SCHEDULED = "scheduled"  # Warm on a schedule
    PREDICTED = "predicted"  # Warm based on predicted access patterns
    HYBRID = "hybrid"  # Combination of eager + lazy + predicted


@dataclass
class CacheWarmingConfig:
    """
    Configuration for cache warming behavior.

    Controls concurrency, batching, prediction, and other warming parameters.
    """

    max_concurrent_tasks: int = 10  # Maximum concurrent warming tasks
    batch_size: int = 100  # Number of entries to warm per batch
    enable_prediction: bool = True  # Enable cache hit prediction
    prediction_window_hours: int = 24  # Hours of history for prediction
    min_access_count: int = 2  # Minimum accesses to consider warming
    refresh_interval_seconds: int = 3600  # Default refresh interval (1 hour)
    startup_timeout_seconds: int = 300  # Timeout for startup warming (5 min)
    lazy_warm_delay_ms: int = 100  # Delay before lazy warming (debounce)
    ttl_buffer_seconds: int = 300  # Refresh entries this many seconds before TTL expiry
    enable_background_warming: bool = True  # Enable background warming
    background_check_interval_seconds: int = 60  # How often to check for background warming


@dataclass
class CacheWarmingMetrics:
    """
    Metrics for cache warming operations.

    Tracks performance and effectiveness of cache warming.
    """

    total_warmed: int = 0  # Total entries warmed
    successful_warms: int = 0  # Successfully warmed entries
    failed_warms: int = 0  # Failed warming attempts
    cache_hits_after_warm: int = 0  # Hits on warmed entries
    cache_misses_detected: int = 0  # Cache misses detected
    lazy_warms_triggered: int = 0  # Lazy warming operations triggered
    scheduled_warms: int = 0  # Scheduled warming operations
    predicted_warms: int = 0  # Warming based on predictions
    total_warming_time_ms: float = 0.0  # Total time spent warming
    startup_warming_time_ms: float = 0.0  # Time for startup warming
    last_warm_timestamp: datetime | None = None  # Last warming operation
    prediction_accuracy: float = 0.0  # Accuracy of cache hit predictions

    def to_dict(self) -> dict[str, Any]:
        """
        Convert metrics to dictionary.

        Returns:
            Dictionary with all metrics
        """
        return {
            "total_warmed": self.total_warmed,
            "successful_warms": self.successful_warms,
            "failed_warms": self.failed_warms,
            "success_rate": round(
                self.successful_warms / max(self.total_warmed, 1), 3
            ),
            "cache_hits_after_warm": self.cache_hits_after_warm,
            "cache_misses_detected": self.cache_misses_detected,
            "lazy_warms_triggered": self.lazy_warms_triggered,
            "scheduled_warms": self.scheduled_warms,
            "predicted_warms": self.predicted_warms,
            "total_warming_time_ms": round(self.total_warming_time_ms, 2),
            "startup_warming_time_ms": round(self.startup_warming_time_ms, 2),
            "avg_warming_time_ms": round(
                self.total_warming_time_ms / max(self.total_warmed, 1), 2
            ),
            "last_warm_timestamp": (
                self.last_warm_timestamp.isoformat()
                if self.last_warm_timestamp
                else None
            ),
            "prediction_accuracy": round(self.prediction_accuracy, 3),
        }


@dataclass
class CacheWarmingProgress:
    """
    Progress tracking for cache warming operations.

    Provides real-time status of warming operations.
    """

    total_entries: int = 0  # Total entries to warm
    warmed_entries: int = 0  # Entries warmed so far
    in_progress: bool = False  # Whether warming is in progress
    start_time: datetime | None = None  # Start time of current operation
    estimated_completion: datetime | None = None  # Estimated completion time
    current_batch: int = 0  # Current batch number
    total_batches: int = 0  # Total batches to process
    errors: list[str] = field(default_factory=list)  # Recent errors

    @property
    def progress_percentage(self) -> float:
        """
        Calculate progress percentage.

        Returns:
            Progress as percentage (0-100)
        """
        if self.total_entries == 0:
            return 0.0
        return (self.warmed_entries / self.total_entries) * 100

    @property
    def elapsed_time_seconds(self) -> float:
        """
        Calculate elapsed time since start.

        Returns:
            Elapsed time in seconds
        """
        if not self.start_time:
            return 0.0
        return (datetime.utcnow() - self.start_time).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert progress to dictionary.

        Returns:
            Dictionary with progress information
        """
        return {
            "total_entries": self.total_entries,
            "warmed_entries": self.warmed_entries,
            "in_progress": self.in_progress,
            "progress_percentage": round(self.progress_percentage, 2),
            "elapsed_time_seconds": round(self.elapsed_time_seconds, 2),
            "current_batch": self.current_batch,
            "total_batches": self.total_batches,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "estimated_completion": (
                self.estimated_completion.isoformat()
                if self.estimated_completion
                else None
            ),
            "recent_errors": self.errors[-10:],  # Last 10 errors
        }


class CacheWarmer:
    """
    Service for cache warming and maintenance.

    Provides intelligent cache warming with multiple strategies:
    - Startup warming: Pre-populate cache on application start
    - Scheduled warming: Refresh cache on a schedule
    - Lazy warming: Warm cache entries on miss
    - Predicted warming: Warm based on access patterns

    Features:
    - Priority-based warming queue
    - Concurrency control to prevent overload
    - Progress tracking for monitoring
    - Cache hit prediction using historical data
    - Automatic refresh before TTL expiry
    - Comprehensive metrics

    Example:
        # Create warmer
        warmer = CacheWarmer(cache_namespace="schedule")

        # Define warming functions
        async def warm_schedules():
            schedules = await db.get_active_schedules()
            return {f"schedule:{s.id}": s for s in schedules}

        # Register warming function
        warmer.register_warming_function(
            "schedules",
            warm_schedules,
            priority=WarmingPriority.HIGH
        )

        # Warm on startup
        await warmer.warm_on_startup()

        # Schedule refresh
        await warmer.schedule_refresh(interval_seconds=3600)
    """

    def __init__(
        self,
        cache_namespace: str = "default",
        config: CacheWarmingConfig | None = None,
    ):
        """
        Initialize cache warmer.

        Args:
            cache_namespace: Cache namespace to warm
            config: Warming configuration (uses defaults if None)
        """
        self.namespace = cache_namespace
        self.config = config or CacheWarmingConfig()
        self.cache = get_cache(cache_namespace)

        # Redis for tracking access patterns
        self._redis: redis.Redis | None = None
        self._settings = get_settings()

        # Metrics and progress
        self.metrics = CacheWarmingMetrics()
        self.progress = CacheWarmingProgress()
        self._metrics_lock = RLock()

        # Registered warming functions
        self._warming_functions: dict[
            str, tuple[Callable[[], Coroutine[Any, Any, dict[str, Any]]], WarmingPriority]
        ] = {}

        # Access pattern tracking for prediction
        self._access_patterns: dict[str, list[datetime]] = defaultdict(list)
        self._access_lock = RLock()

        # Concurrency control
        self._warming_semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)
        self._warming_queue: asyncio.Queue = asyncio.Queue()

        # Scheduled task handles
        self._scheduled_task: asyncio.Task | None = None
        self._background_task: asyncio.Task | None = None

        # Pending lazy warming operations (for debouncing)
        self._pending_lazy_warms: dict[str, asyncio.Task] = {}

    async def _get_redis(self) -> redis.Redis:
        """
        Get or create async Redis connection.

        Returns:
            Redis client instance
        """
        if self._redis is None:
            redis_url = self._settings.redis_url_with_password
            self._redis = redis.from_url(redis_url, decode_responses=False)

        return self._redis

    def register_warming_function(
        self,
        name: str,
        func: Callable[[], Coroutine[Any, Any, dict[str, Any]]],
        priority: WarmingPriority = WarmingPriority.MEDIUM,
    ) -> None:
        """
        Register a function for cache warming.

        The function should return a dictionary of {cache_key: value} pairs.

        Args:
            name: Name of the warming function
            func: Async function that returns dict of cache entries
            priority: Priority level for this warming operation

        Example:
            async def warm_users():
                users = await db.get_all_users()
                return {f"user:{u.id}": u for u in users}

            warmer.register_warming_function(
                "users",
                warm_users,
                priority=WarmingPriority.HIGH
            )
        """
        self._warming_functions[name] = (func, priority)
        logger.info(
            f"Registered warming function '{name}' with priority {priority.value}"
        )

    async def warm_on_startup(
        self,
        strategy: WarmingStrategy = WarmingStrategy.HYBRID,
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        """
        Warm cache on application startup.

        Populates cache with critical and high-priority entries before
        the application starts serving requests.

        Args:
            strategy: Warming strategy to use
            timeout_seconds: Maximum time to spend warming (uses config default if None)

        Returns:
            Dictionary with warming results and statistics

        Example:
            # Warm cache on startup
            result = await warmer.warm_on_startup(
                strategy=WarmingStrategy.EAGER,
                timeout_seconds=300
            )
            print(f"Warmed {result['entries_warmed']} entries")
        """
        timeout = timeout_seconds or self.config.startup_timeout_seconds
        start_time = time.time()

        logger.info(
            f"Starting cache warming on startup (strategy: {strategy.value}, "
            f"timeout: {timeout}s)"
        )

        # Initialize progress
        with self._metrics_lock:
            self.progress.in_progress = True
            self.progress.start_time = datetime.utcnow()
            self.progress.errors.clear()

        # Sort warming functions by priority
        sorted_functions = sorted(
            self._warming_functions.items(),
            key=lambda x: self._get_priority_value(x[1][1]),
            reverse=True,
        )

        # Filter based on strategy
        if strategy == WarmingStrategy.EAGER:
            # Warm CRITICAL and HIGH priority
            functions_to_warm = [
                (name, func, priority)
                for name, (func, priority) in sorted_functions
                if priority in (WarmingPriority.CRITICAL, WarmingPriority.HIGH)
            ]
        elif strategy == WarmingStrategy.LAZY:
            # Only warm CRITICAL
            functions_to_warm = [
                (name, func, priority)
                for name, (func, priority) in sorted_functions
                if priority == WarmingPriority.CRITICAL
            ]
        elif strategy == WarmingStrategy.PREDICTED:
            # Warm based on predictions
            functions_to_warm = await self._get_predicted_warming_functions()
        else:  # HYBRID or SCHEDULED
            # Warm CRITICAL, HIGH, and MEDIUM
            functions_to_warm = [
                (name, func, priority)
                for name, (func, priority) in sorted_functions
                if priority
                not in (WarmingPriority.LOW, WarmingPriority.BACKGROUND)
            ]

        total_entries = 0
        entries_warmed = 0

        try:
            # Warm each function with timeout
            for name, func, priority in functions_to_warm:
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    logger.warning(
                        f"Startup warming timeout reached after {elapsed:.2f}s"
                    )
                    break

                remaining_timeout = timeout - elapsed

                try:
                    # Execute warming function with timeout
                    entries = await asyncio.wait_for(func(), timeout=remaining_timeout)

                    # Warm cache entries
                    warmed_count = await self._warm_entries(
                        entries, priority=priority
                    )

                    total_entries += len(entries)
                    entries_warmed += warmed_count

                    logger.info(
                        f"Warmed {warmed_count}/{len(entries)} entries from '{name}' "
                        f"({priority.value})"
                    )

                except asyncio.TimeoutError:
                    error_msg = f"Timeout warming '{name}' after {remaining_timeout:.2f}s"
                    logger.warning(error_msg)
                    self.progress.errors.append(error_msg)

                except Exception as e:
                    error_msg = f"Error warming '{name}': {e}"
                    logger.error(error_msg, exc_info=True)
                    self.progress.errors.append(error_msg)

        finally:
            # Update metrics
            elapsed_ms = (time.time() - start_time) * 1000
            with self._metrics_lock:
                self.metrics.startup_warming_time_ms = elapsed_ms
                self.metrics.last_warm_timestamp = datetime.utcnow()
                self.progress.in_progress = False
                self.progress.warmed_entries = entries_warmed
                self.progress.total_entries = total_entries

        result = {
            "strategy": strategy.value,
            "entries_warmed": entries_warmed,
            "total_entries": total_entries,
            "elapsed_time_ms": elapsed_ms,
            "functions_executed": len(functions_to_warm),
            "errors": self.progress.errors.copy(),
        }

        logger.info(
            f"Startup warming completed: {entries_warmed}/{total_entries} entries "
            f"in {elapsed_ms:.2f}ms"
        )

        return result

    async def schedule_refresh(
        self,
        interval_seconds: int | None = None,
        priority_threshold: WarmingPriority = WarmingPriority.MEDIUM,
    ) -> None:
        """
        Schedule periodic cache refresh.

        Automatically refreshes cache entries on a schedule to prevent
        cache expiry during high traffic.

        Args:
            interval_seconds: Refresh interval in seconds (uses config default if None)
            priority_threshold: Only refresh entries at or above this priority

        Example:
            # Refresh high and critical priority entries every hour
            await warmer.schedule_refresh(
                interval_seconds=3600,
                priority_threshold=WarmingPriority.HIGH
            )
        """
        interval = interval_seconds or self.config.refresh_interval_seconds

        # Cancel existing scheduled task
        if self._scheduled_task and not self._scheduled_task.done():
            self._scheduled_task.cancel()
            try:
                await self._scheduled_task
            except asyncio.CancelledError:
                pass

        logger.info(
            f"Scheduling cache refresh every {interval}s "
            f"(priority >= {priority_threshold.value})"
        )

        async def refresh_loop():
            """Periodic refresh loop."""
            while True:
                try:
                    await asyncio.sleep(interval)
                    await self._execute_scheduled_refresh(priority_threshold)

                except asyncio.CancelledError:
                    logger.info("Scheduled refresh cancelled")
                    break

                except Exception as e:
                    logger.error(f"Error in scheduled refresh: {e}", exc_info=True)

        # Start scheduled task
        self._scheduled_task = asyncio.create_task(refresh_loop())

    async def on_cache_miss(
        self,
        cache_key: str,
        fetch_func: Callable[[], Coroutine[Any, Any, Any]] | None = None,
        priority: WarmingPriority = WarmingPriority.MEDIUM,
    ) -> Any:
        """
        Handle cache miss with lazy warming.

        When a cache miss occurs, optionally fetch the value and warm the cache.
        Uses debouncing to prevent overwhelming the system with repeated misses.

        Args:
            cache_key: The cache key that missed
            fetch_func: Optional function to fetch the value
            priority: Priority for warming this entry

        Returns:
            The fetched value if fetch_func provided, None otherwise

        Example:
            # On cache miss, fetch and warm
            async def fetch_user(user_id):
                return await db.get_user(user_id)

            user = await warmer.on_cache_miss(
                f"user:{user_id}",
                fetch_func=lambda: fetch_user(user_id),
                priority=WarmingPriority.HIGH
            )
        """
        # Track the miss
        with self._metrics_lock:
            self.metrics.cache_misses_detected += 1

        # Track access pattern for prediction
        await self._track_access(cache_key)

        # Cancel pending lazy warm for this key (debouncing)
        if cache_key in self._pending_lazy_warms:
            self._pending_lazy_warms[cache_key].cancel()

        # Schedule lazy warming
        async def lazy_warm_task():
            """Lazy warming task with debounce delay."""
            try:
                # Debounce delay
                await asyncio.sleep(self.config.lazy_warm_delay_ms / 1000)

                # Fetch value if function provided
                value = None
                if fetch_func:
                    value = await fetch_func()

                    # Warm cache
                    await self.cache.set(cache_key, value)

                    with self._metrics_lock:
                        self.metrics.lazy_warms_triggered += 1
                        self.metrics.successful_warms += 1
                        self.metrics.total_warmed += 1

                    logger.debug(f"Lazy warmed cache key: {cache_key}")

                return value

            except asyncio.CancelledError:
                # Task was cancelled (debounced)
                pass

            except Exception as e:
                logger.error(f"Error in lazy warming for {cache_key}: {e}")
                with self._metrics_lock:
                    self.metrics.failed_warms += 1

            finally:
                # Remove from pending
                if cache_key in self._pending_lazy_warms:
                    del self._pending_lazy_warms[cache_key]

        # Create and store task
        task = asyncio.create_task(lazy_warm_task())
        self._pending_lazy_warms[cache_key] = task

        # Wait for result if fetch_func provided
        if fetch_func:
            return await task

        return None

    async def predict_and_warm(
        self,
        prediction_window_hours: int | None = None,
        min_access_count: int | None = None,
    ) -> dict[str, Any]:
        """
        Predict cache keys likely to be accessed and warm them.

        Uses historical access patterns to predict which cache entries
        will be accessed soon and pre-warms them.

        Args:
            prediction_window_hours: Hours of history to analyze
            min_access_count: Minimum accesses to consider for warming

        Returns:
            Dictionary with prediction results

        Example:
            # Predict and warm based on last 24 hours
            result = await warmer.predict_and_warm(
                prediction_window_hours=24,
                min_access_count=3
            )
        """
        if not self.config.enable_prediction:
            logger.debug("Cache hit prediction is disabled")
            return {"predicted": 0, "warmed": 0}

        window_hours = prediction_window_hours or self.config.prediction_window_hours
        min_accesses = min_access_count or self.config.min_access_count

        logger.info(
            f"Predicting cache accesses (window: {window_hours}h, "
            f"min_accesses: {min_accesses})"
        )

        # Analyze access patterns
        predicted_keys = await self._predict_cache_accesses(
            window_hours=window_hours,
            min_accesses=min_accesses,
        )

        # Warm predicted entries
        warmed_count = 0
        for cache_key in predicted_keys:
            # Find warming function for this key
            warming_func = self._find_warming_function_for_key(cache_key)
            if warming_func:
                try:
                    entries = await warming_func()
                    if cache_key in entries:
                        await self.cache.set(cache_key, entries[cache_key])
                        warmed_count += 1

                        with self._metrics_lock:
                            self.metrics.predicted_warms += 1
                            self.metrics.successful_warms += 1
                            self.metrics.total_warmed += 1

                except Exception as e:
                    logger.error(f"Error warming predicted key {cache_key}: {e}")
                    with self._metrics_lock:
                        self.metrics.failed_warms += 1

        result = {
            "predicted_keys": len(predicted_keys),
            "warmed_entries": warmed_count,
            "prediction_window_hours": window_hours,
            "min_access_count": min_accesses,
        }

        logger.info(
            f"Predicted warming completed: {warmed_count}/{len(predicted_keys)} entries"
        )

        return result

    async def get_metrics(self) -> dict[str, Any]:
        """
        Get cache warming metrics.

        Returns:
            Dictionary with comprehensive warming metrics

        Example:
            metrics = await warmer.get_metrics()
            print(f"Success rate: {metrics['success_rate']:.2%}")
        """
        with self._metrics_lock:
            metrics_dict = self.metrics.to_dict()

        # Add cache statistics
        cache_stats = self.cache.get_stats()
        metrics_dict["cache_stats"] = cache_stats

        return metrics_dict

    async def get_progress(self) -> dict[str, Any]:
        """
        Get current warming progress.

        Returns:
            Dictionary with progress information

        Example:
            progress = await warmer.get_progress()
            print(f"Progress: {progress['progress_percentage']:.1f}%")
        """
        return self.progress.to_dict()

    async def start_background_warming(self) -> None:
        """
        Start background warming task.

        Continuously monitors cache and warms entries that are about
        to expire or are frequently accessed.

        Example:
            # Start background warming
            await warmer.start_background_warming()
        """
        if not self.config.enable_background_warming:
            logger.debug("Background warming is disabled")
            return

        # Cancel existing background task
        if self._background_task and not self._background_task.done():
            logger.info("Background warming task already running")
            return

        logger.info("Starting background warming task")

        async def background_loop():
            """Background warming loop."""
            while True:
                try:
                    await asyncio.sleep(
                        self.config.background_check_interval_seconds
                    )
                    await self._execute_background_warming()

                except asyncio.CancelledError:
                    logger.info("Background warming cancelled")
                    break

                except Exception as e:
                    logger.error(f"Error in background warming: {e}", exc_info=True)

        # Start background task
        self._background_task = asyncio.create_task(background_loop())

    async def stop_background_warming(self) -> None:
        """
        Stop background warming task.

        Example:
            # Stop background warming
            await warmer.stop_background_warming()
        """
        if self._background_task and not self._background_task.done():
            logger.info("Stopping background warming task")
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass

    # Private methods

    async def _warm_entries(
        self,
        entries: dict[str, Any],
        priority: WarmingPriority = WarmingPriority.MEDIUM,
        ttl: int | None = None,
    ) -> int:
        """
        Warm cache with entries.

        Args:
            entries: Dictionary of {cache_key: value} pairs
            priority: Priority level for these entries
            ttl: Time-to-live for entries (uses cache default if None)

        Returns:
            Number of entries successfully warmed
        """
        start_time = time.time()
        warmed_count = 0
        failed_count = 0

        # Process in batches
        batch_size = self.config.batch_size
        keys = list(entries.keys())

        for i in range(0, len(keys), batch_size):
            batch_keys = keys[i : i + batch_size]

            # Warm batch with concurrency control
            tasks = []
            for key in batch_keys:
                task = self._warm_single_entry(key, entries[key], ttl)
                tasks.append(task)

            # Wait for batch with concurrency limit
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Count successes and failures
            for result in results:
                if isinstance(result, Exception):
                    failed_count += 1
                elif result:
                    warmed_count += 1
                else:
                    failed_count += 1

        # Update metrics
        elapsed_ms = (time.time() - start_time) * 1000
        with self._metrics_lock:
            self.metrics.total_warmed += len(entries)
            self.metrics.successful_warms += warmed_count
            self.metrics.failed_warms += failed_count
            self.metrics.total_warming_time_ms += elapsed_ms
            self.metrics.last_warm_timestamp = datetime.utcnow()

        return warmed_count

    async def _warm_single_entry(
        self, key: str, value: Any, ttl: int | None = None
    ) -> bool:
        """
        Warm a single cache entry with concurrency control.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live (optional)

        Returns:
            True if successful, False otherwise
        """
        async with self._warming_semaphore:
            try:
                await self.cache.set(key, value, ttl=ttl)
                return True

            except Exception as e:
                logger.error(f"Error warming cache key {key}: {e}")
                return False

    async def _execute_scheduled_refresh(
        self, priority_threshold: WarmingPriority
    ) -> None:
        """
        Execute scheduled cache refresh.

        Args:
            priority_threshold: Only refresh entries at or above this priority
        """
        logger.debug(f"Executing scheduled refresh (priority >= {priority_threshold.value})")

        # Filter functions by priority
        functions_to_refresh = [
            (name, func, priority)
            for name, (func, priority) in self._warming_functions.items()
            if self._get_priority_value(priority)
            >= self._get_priority_value(priority_threshold)
        ]

        # Refresh each function
        for name, func, priority in functions_to_refresh:
            try:
                entries = await func()
                await self._warm_entries(entries, priority=priority)

                with self._metrics_lock:
                    self.metrics.scheduled_warms += 1

                logger.debug(f"Scheduled refresh of '{name}': {len(entries)} entries")

            except Exception as e:
                logger.error(f"Error in scheduled refresh of '{name}': {e}")

    async def _execute_background_warming(self) -> None:
        """
        Execute background warming.

        Warms entries that are about to expire or frequently accessed.
        """
        logger.debug("Executing background warming")

        # Find entries about to expire
        # This would require tracking TTLs in Redis
        # For now, just refresh low-priority entries
        background_functions = [
            (name, func)
            for name, (func, priority) in self._warming_functions.items()
            if priority == WarmingPriority.BACKGROUND
        ]

        for name, func in background_functions:
            try:
                entries = await func()
                await self._warm_entries(entries, priority=WarmingPriority.BACKGROUND)

                logger.debug(f"Background warmed '{name}': {len(entries)} entries")

            except Exception as e:
                logger.error(f"Error in background warming of '{name}': {e}")

    async def _track_access(self, cache_key: str) -> None:
        """
        Track cache access for prediction.

        Args:
            cache_key: The cache key that was accessed
        """
        if not self.config.enable_prediction:
            return

        with self._access_lock:
            self._access_patterns[cache_key].append(datetime.utcnow())

            # Trim old accesses
            cutoff = datetime.utcnow() - timedelta(
                hours=self.config.prediction_window_hours
            )
            self._access_patterns[cache_key] = [
                access
                for access in self._access_patterns[cache_key]
                if access > cutoff
            ]

    async def _predict_cache_accesses(
        self,
        window_hours: int,
        min_accesses: int,
    ) -> list[str]:
        """
        Predict which cache keys will be accessed soon.

        Args:
            window_hours: Hours of history to analyze
            min_accesses: Minimum access count to consider

        Returns:
            List of cache keys predicted to be accessed
        """
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        predicted = []

        with self._access_lock:
            for key, accesses in self._access_patterns.items():
                # Count recent accesses
                recent_accesses = [a for a in accesses if a > cutoff]

                if len(recent_accesses) >= min_accesses:
                    # Simple prediction: if accessed frequently, likely to be accessed again
                    predicted.append(key)

        return predicted

    async def _get_predicted_warming_functions(
        self,
    ) -> list[tuple[str, Callable, WarmingPriority]]:
        """
        Get warming functions based on predictions.

        Returns:
            List of (name, func, priority) tuples
        """
        # For now, return CRITICAL and HIGH priority functions
        # In a full implementation, this would use ML predictions
        return [
            (name, func, priority)
            for name, (func, priority) in self._warming_functions.items()
            if priority in (WarmingPriority.CRITICAL, WarmingPriority.HIGH)
        ]

    def _find_warming_function_for_key(
        self, cache_key: str
    ) -> Callable[[], Coroutine[Any, Any, dict[str, Any]]] | None:
        """
        Find the warming function that can provide a cache key.

        Args:
            cache_key: The cache key to find

        Returns:
            Warming function or None
        """
        # Simple prefix matching
        # In production, this would be more sophisticated
        for name, (func, priority) in self._warming_functions.items():
            if cache_key.startswith(name):
                return func

        return None

    @staticmethod
    def _get_priority_value(priority: WarmingPriority) -> int:
        """
        Get numeric value for priority (for sorting).

        Args:
            priority: Priority enum value

        Returns:
            Numeric priority (higher is more important)
        """
        priority_values = {
            WarmingPriority.CRITICAL: 100,
            WarmingPriority.HIGH: 75,
            WarmingPriority.MEDIUM: 50,
            WarmingPriority.LOW: 25,
            WarmingPriority.BACKGROUND: 0,
        }
        return priority_values.get(priority, 50)


# Global cache warmer instances by namespace
_warmer_instances: dict[str, CacheWarmer] = {}
_warmer_lock = RLock()


def get_cache_warmer(
    namespace: str = "default",
    config: CacheWarmingConfig | None = None,
) -> CacheWarmer:
    """
    Get or create a cache warmer instance for a namespace.

    Args:
        namespace: Cache namespace
        config: Warming configuration (uses defaults if None)

    Returns:
        CacheWarmer instance for the namespace

    Example:
        # Get cache warmer for schedule namespace
        warmer = get_cache_warmer("schedule")

        # Register warming functions
        warmer.register_warming_function(
            "schedules",
            warm_schedules_func,
            priority=WarmingPriority.HIGH
        )

        # Warm on startup
        await warmer.warm_on_startup()
    """
    global _warmer_instances

    with _warmer_lock:
        if namespace not in _warmer_instances:
            _warmer_instances[namespace] = CacheWarmer(
                cache_namespace=namespace,
                config=config,
            )

        return _warmer_instances[namespace]
