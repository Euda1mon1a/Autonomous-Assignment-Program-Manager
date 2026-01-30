"""
Performance logging for monitoring application performance metrics.

Tracks:
- API endpoint latency
- Database query performance
- Cache hit/miss rates
- Background task execution times
- Resource utilization
- Slow operations
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from loguru import logger

from app.core.logging.context import bind_context_to_logger


@dataclass
class PerformanceMetric:
    """
    Performance metric data.

    Captures timing and resource utilization for an operation.
    """

    operation: str
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    success: bool = True
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # Resource metrics
    cpu_usage: float | None = None
    memory_usage: float | None = None
    db_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "operation": self.operation,
            "duration_ms": round(self.duration_ms, 2),
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "error": self.error,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "db_queries": self.db_queries,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            **self.metadata,
        }


class PerformanceLogger:
    """
    Performance logger for tracking operation metrics.

    Features:
    - Operation timing
    - Resource tracking
    - Slow operation detection
    - Performance metrics aggregation
    """

    def __init__(
        self,
        slow_threshold_ms: float = 1000.0,
        enable_resource_tracking: bool = False,
    ) -> None:
        """
        Initialize performance logger.

        Args:
            slow_threshold_ms: Threshold for slow operation warnings (milliseconds)
            enable_resource_tracking: Enable CPU/memory tracking
        """
        self.slow_threshold_ms = slow_threshold_ms
        self.enable_resource_tracking = enable_resource_tracking

    def log_operation(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        error: str | None = None,
        **metadata,
    ) -> None:
        """
        Log a performance metric.

        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            success: Whether operation succeeded
            error: Error message if failed
            **metadata: Additional metadata
        """
        metric = PerformanceMetric(
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            error=error,
            metadata=metadata,
        )

        # Log at appropriate level
        if not success:
            logger.bind(**bind_context_to_logger()).error(
                f"Operation failed: {operation}",
                **metric.to_dict(),
            )
        elif duration_ms > self.slow_threshold_ms:
            logger.bind(**bind_context_to_logger()).warning(
                f"Slow operation: {operation} ({duration_ms:.2f}ms)",
                **metric.to_dict(),
            )
        else:
            logger.bind(**bind_context_to_logger()).debug(
                f"Operation completed: {operation} ({duration_ms:.2f}ms)",
                **metric.to_dict(),
            )

    def time_operation(self, operation: str, **metadata):
        """
        Context manager for timing an operation.

        Args:
            operation: Operation name
            **metadata: Additional metadata

        Example:
            with perf_logger.time_operation("database_query", table="users"):
                results = db.query(User).all()
        """
        return PerformanceTimer(self, operation, metadata)

    def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        **metadata,
    ) -> None:
        """
        Log API request performance.

        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            duration_ms: Request duration
            **metadata: Additional metadata
        """
        operation = f"{method} {path}"
        success = 200 <= status_code < 400

        self.log_operation(
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            status_code=status_code,
            **metadata,
        )

    def log_database_query(
        self,
        query_type: str,
        table: str,
        duration_ms: float,
        rows_affected: int = 0,
        **metadata,
    ) -> None:
        """
        Log database query performance.

        Args:
            query_type: Query type (SELECT, INSERT, UPDATE, DELETE)
            table: Table name
            duration_ms: Query duration
            rows_affected: Number of rows affected
            **metadata: Additional metadata
        """
        operation = f"db_{query_type.lower()}_{table}"

        self.log_operation(
            operation=operation,
            duration_ms=duration_ms,
            query_type=query_type,
            table=table,
            rows_affected=rows_affected,
            **metadata,
        )

    def log_cache_access(
        self,
        cache_key: str,
        hit: bool,
        duration_ms: float | None = None,
        **metadata,
    ) -> None:
        """
        Log cache access.

        Args:
            cache_key: Cache key
            hit: Whether cache hit or miss
            duration_ms: Access duration
            **metadata: Additional metadata
        """
        operation = f"cache_{'hit' if hit else 'miss'}"

        logger.bind(**bind_context_to_logger()).debug(
            f"Cache {operation}: {cache_key}",
            operation=operation,
            cache_key=cache_key,
            duration_ms=duration_ms,
            **metadata,
        )

    def log_background_task(
        self,
        task_name: str,
        duration_ms: float,
        success: bool = True,
        error: str | None = None,
        **metadata,
    ) -> None:
        """
        Log background task performance.

        Args:
            task_name: Task name
            duration_ms: Task duration
            success: Whether task succeeded
            error: Error message if failed
            **metadata: Additional metadata
        """
        operation = f"task_{task_name}"

        self.log_operation(
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            error=error,
            task_type="background",
            **metadata,
        )

    def log_external_api_call(
        self,
        service: str,
        endpoint: str,
        duration_ms: float,
        status_code: int | None = None,
        success: bool = True,
        **metadata,
    ) -> None:
        """
        Log external API call performance.

        Args:
            service: External service name
            endpoint: API endpoint
            duration_ms: Call duration
            status_code: HTTP status code
            success: Whether call succeeded
            **metadata: Additional metadata
        """
        operation = f"external_{service}_{endpoint}"

        self.log_operation(
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            service=service,
            endpoint=endpoint,
            status_code=status_code,
            **metadata,
        )


class PerformanceTimer:
    """Context manager for timing operations."""

    def __init__(
        self,
        perf_logger: PerformanceLogger,
        operation: str,
        metadata: dict[str, Any],
    ) -> None:
        """
        Initialize performance timer.

        Args:
            perf_logger: Performance logger instance
            operation: Operation name
            metadata: Metadata to include
        """
        self.perf_logger = perf_logger
        self.operation = operation
        self.metadata = metadata
        self.start_time: float | None = None
        self.success = True
        self.error: str | None = None

    def __enter__(self):
        """Start timing."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and log."""
        if self.start_time is None:
            return False

        duration_ms = (time.perf_counter() - self.start_time) * 1000

        # Check if exception occurred
        if exc_type is not None:
            self.success = False
            self.error = str(exc_val) if exc_val else exc_type.__name__

            # Log the operation
        self.perf_logger.log_operation(
            operation=self.operation,
            duration_ms=duration_ms,
            success=self.success,
            error=self.error,
            **self.metadata,
        )

        return False  # Don't suppress exceptions


def time_function(operation: str | None = None, **metadata):
    """
    Decorator for timing function execution.

    Args:
        operation: Operation name (defaults to function name)
        **metadata: Additional metadata

    Example:
        @time_function(operation="schedule_generation")
        def generate_schedule():
            # ... implementation
            pass
    """

    def decorator(func: Callable) -> Callable:
        nonlocal operation
        if operation is None:
            operation = func.__name__

        def wrapper(*args, **kwargs):
            perf_logger = get_performance_logger()
            with perf_logger.time_operation(operation, **metadata):
                return func(*args, **kwargs)

        return wrapper

    return decorator


async def time_async_function(operation: str | None = None, **metadata):
    """
    Decorator for timing async function execution.

    Args:
        operation: Operation name (defaults to function name)
        **metadata: Additional metadata

    Example:
        @time_async_function(operation="async_schedule_generation")
        async def generate_schedule_async():
            # ... implementation
            pass
    """

    def decorator(func: Callable) -> Callable:
        nonlocal operation
        if operation is None:
            operation = func.__name__

        async def wrapper(*args, **kwargs):
            perf_logger = get_performance_logger()
            with perf_logger.time_operation(operation, **metadata):
                return await func(*args, **kwargs)

        return wrapper

    return decorator

    # Global performance logger instance


_global_perf_logger: PerformanceLogger | None = None


def get_performance_logger() -> PerformanceLogger:
    """Get or create global performance logger instance."""
    global _global_perf_logger
    if _global_perf_logger is None:
        _global_perf_logger = PerformanceLogger()
    return _global_perf_logger


def set_performance_logger(perf_logger: PerformanceLogger) -> None:
    """Set global performance logger instance."""
    global _global_perf_logger
    _global_perf_logger = perf_logger

    # Convenience functions for common operations


def log_api_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    **metadata,
) -> None:
    """Log API request performance (convenience function)."""
    get_performance_logger().log_api_request(
        method, path, status_code, duration_ms, **metadata
    )


def log_database_query(
    query_type: str,
    table: str,
    duration_ms: float,
    rows_affected: int = 0,
    **metadata,
) -> None:
    """Log database query performance (convenience function)."""
    get_performance_logger().log_database_query(
        query_type, table, duration_ms, rows_affected, **metadata
    )


def log_cache_access(
    cache_key: str,
    hit: bool,
    duration_ms: float | None = None,
    **metadata,
) -> None:
    """Log cache access (convenience function)."""
    get_performance_logger().log_cache_access(cache_key, hit, duration_ms, **metadata)


def time_operation(operation: str, **metadata):
    """Time an operation (convenience function)."""
    return get_performance_logger().time_operation(operation, **metadata)
