"""Optimized database connection pooling.

Provides advanced connection pool management with monitoring and automatic tuning.
"""
import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class PoolMetrics:
    """Connection pool performance metrics."""

    active_connections: int
    idle_connections: int
    total_connections: int
    checkout_count: int
    overflow_count: int
    avg_checkout_time: float
    max_checkout_time: float
    pool_size: int
    max_overflow: int
    timeout: int


class OptimizedConnectionPool:
    """Advanced connection pool with monitoring and auto-tuning."""

    def __init__(
        self,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True,
        enable_monitoring: bool = True,
    ):
        """Initialize optimized connection pool.

        Args:
            pool_size: Number of persistent connections
            max_overflow: Maximum overflow connections
            pool_timeout: Timeout for getting connection
            pool_recycle: Recycle connections after N seconds
            pool_pre_ping: Test connections before using
            enable_monitoring: Enable performance monitoring
        """
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.pool_pre_ping = pool_pre_ping
        self.enable_monitoring = enable_monitoring

        # Metrics tracking
        self.checkout_times: list[float] = []
        self.checkout_count = 0
        self.overflow_count = 0
        self.last_metrics_reset = datetime.utcnow()

        # Create engine with optimized pool
        self.engine = self._create_engine()
        self.async_session_maker = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    def _create_engine(self) -> AsyncEngine:
        """Create SQLAlchemy async engine with optimized pool.

        Returns:
            Configured async engine
        """
        engine = create_async_engine(
            settings.SQLALCHEMY_DATABASE_URI,
            poolclass=QueuePool,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=self.pool_pre_ping,
            echo=settings.DB_ECHO,
            # Additional performance optimizations
            execution_options={
                "isolation_level": "READ COMMITTED",
            },
        )

        # Add event listeners for monitoring
        if self.enable_monitoring:
            self._add_monitoring_hooks(engine)

        return engine

    def _add_monitoring_hooks(self, engine: AsyncEngine):
        """Add event listeners for connection monitoring.

        Args:
            engine: SQLAlchemy engine to monitor
        """
        from sqlalchemy import event

        @event.listens_for(engine.sync_engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Track connection checkout."""
            connection_record.info["checkout_time"] = time.time()

        @event.listens_for(engine.sync_engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Track connection checkin and calculate checkout time."""
            if "checkout_time" in connection_record.info:
                checkout_time = time.time() - connection_record.info["checkout_time"]
                self.checkout_times.append(checkout_time)
                self.checkout_count += 1

                # Keep only last 1000 measurements
                if len(self.checkout_times) > 1000:
                    self.checkout_times = self.checkout_times[-1000:]

    async def get_session(self) -> AsyncSession:
        """Get database session from pool.

        Returns:
            Async database session
        """
        return self.async_session_maker()

    async def get_metrics(self) -> PoolMetrics:
        """Get current pool metrics.

        Returns:
            PoolMetrics with current statistics
        """
        pool = self.engine.pool

        # Calculate checkout time statistics
        avg_checkout = (
            sum(self.checkout_times) / len(self.checkout_times)
            if self.checkout_times
            else 0.0
        )
        max_checkout = max(self.checkout_times) if self.checkout_times else 0.0

        return PoolMetrics(
            active_connections=pool.checkedout(),
            idle_connections=pool.size() - pool.checkedout(),
            total_connections=pool.size(),
            checkout_count=self.checkout_count,
            overflow_count=pool.overflow(),
            avg_checkout_time=round(avg_checkout, 4),
            max_checkout_time=round(max_checkout, 4),
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            timeout=self.pool_timeout,
        )

    async def health_check(self) -> dict:
        """Check pool health and return status.

        Returns:
            Health status dictionary
        """
        metrics = await self.get_metrics()

        # Determine health status
        utilization = metrics.active_connections / metrics.pool_size
        is_healthy = True
        warnings = []

        if utilization > 0.9:
            warnings.append("High pool utilization (>90%)")
            is_healthy = False

        if metrics.overflow_count > 0:
            warnings.append(f"Using overflow connections ({metrics.overflow_count})")

        if metrics.avg_checkout_time > 1.0:
            warnings.append(
                f"High avg checkout time ({metrics.avg_checkout_time}s)"
            )

        return {
            "healthy": is_healthy,
            "warnings": warnings,
            "metrics": {
                "utilization": round(utilization * 100, 2),
                "active": metrics.active_connections,
                "idle": metrics.idle_connections,
                "total": metrics.total_connections,
                "avg_checkout_time": metrics.avg_checkout_time,
            },
        }

    async def reset_metrics(self):
        """Reset metrics counters."""
        self.checkout_times.clear()
        self.checkout_count = 0
        self.overflow_count = 0
        self.last_metrics_reset = datetime.utcnow()
        logger.info("Connection pool metrics reset")

    async def dispose(self):
        """Dispose of the connection pool."""
        await self.engine.dispose()
        logger.info("Connection pool disposed")


# Global pool instance
_pool_instance: Optional[OptimizedConnectionPool] = None


def get_connection_pool() -> OptimizedConnectionPool:
    """Get global connection pool instance.

    Returns:
        OptimizedConnectionPool singleton
    """
    global _pool_instance
    if _pool_instance is None:
        _pool_instance = OptimizedConnectionPool(
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
        )
    return _pool_instance


async def get_optimized_session() -> AsyncSession:
    """Get optimized database session.

    Yields:
        Async database session from optimized pool
    """
    pool = get_connection_pool()
    async with pool.get_session() as session:
        yield session
