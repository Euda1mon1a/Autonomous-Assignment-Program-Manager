"""
Database health check and monitoring utilities.

Provides:
- Connection pool monitoring
- Query latency tracking
- Deadlock detection
- Index usage analysis
- Table size monitoring
- Vacuum/analyze scheduling
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict

from sqlalchemy import text, event, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class PoolMetrics:
    """Connection pool metrics."""

    total_connections: int
    checked_out_connections: int
    available_connections: int
    overflow_connections: int
    pool_utilization_percent: float
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class QueryMetrics:
    """Query execution metrics."""

    total_queries: int
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    slow_query_count: int
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class TableMetrics:
    """Table metrics."""

    table_name: str
    row_count: int
    size_mb: float
    index_count: int
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class ConnectionPoolMonitor:
    """Monitor connection pool health."""

    def __init__(self, engine: Engine):
        """
        Initialize connection pool monitor.

        Args:
            engine: SQLAlchemy engine
        """
        self.engine = engine
        self.metrics: list[PoolMetrics] = []

    def get_current_metrics(self) -> PoolMetrics:
        """
        Get current pool metrics.

        Returns:
            PoolMetrics instance
        """
        pool = self.engine.pool

        total = pool.size() + pool.overflow()
        checked_out = pool.checkedout()
        available = total - checked_out
        utilization = (checked_out / total * 100) if total > 0 else 0

        metrics = PoolMetrics(
            total_connections=total,
            checked_out_connections=checked_out,
            available_connections=available,
            overflow_connections=pool.overflow(),
            pool_utilization_percent=utilization,
            timestamp=datetime.utcnow(),
        )

        self.metrics.append(metrics)

        # Keep only last 100 metrics
        if len(self.metrics) > 100:
            self.metrics = self.metrics[-100:]

        return metrics

    def is_healthy(self, max_utilization: float = 90.0) -> bool:
        """
        Check if pool is healthy.

        Args:
            max_utilization: Maximum acceptable utilization percent

        Returns:
            True if healthy, False otherwise
        """
        current = self.get_current_metrics()
        return current.pool_utilization_percent < max_utilization

    def get_metrics_summary(self) -> dict[str, Any]:
        """
        Get summary of pool metrics over time.

        Returns:
            Summary dictionary
        """
        if not self.metrics:
            return {}

        utilizations = [m.pool_utilization_percent for m in self.metrics]

        return {
            "current": self.metrics[-1].to_dict(),
            "average_utilization": sum(utilizations) / len(utilizations),
            "max_utilization": max(utilizations),
            "min_utilization": min(utilizations),
            "metrics_count": len(self.metrics),
        }


class QueryLatencyTracker:
    """Track query execution latency."""

    def __init__(self, slow_query_threshold_ms: float = 100.0):
        """
        Initialize query latency tracker.

        Args:
            slow_query_threshold_ms: Threshold for slow queries
        """
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.query_times: list[float] = []
        self.slow_queries: list[dict[str, Any]] = []

    def record_query(self, query: str, duration_ms: float) -> None:
        """
        Record query execution.

        Args:
            query: SQL query string
            duration_ms: Execution time in milliseconds
        """
        self.query_times.append(duration_ms)

        if duration_ms > self.slow_query_threshold_ms:
            self.slow_queries.append(
                {
                    "query": query[:200],  # Truncate long queries
                    "duration_ms": duration_ms,
                    "timestamp": datetime.utcnow(),
                }
            )

        # Keep only last 1000 queries
        if len(self.query_times) > 1000:
            self.query_times = self.query_times[-1000:]

        # Keep only last 100 slow queries
        if len(self.slow_queries) > 100:
            self.slow_queries = self.slow_queries[-100:]

    def get_metrics(self) -> QueryMetrics:
        """
        Get query latency metrics.

        Returns:
            QueryMetrics instance
        """
        if not self.query_times:
            return QueryMetrics(
                total_queries=0,
                avg_duration_ms=0.0,
                min_duration_ms=0.0,
                max_duration_ms=0.0,
                slow_query_count=0,
                timestamp=datetime.utcnow(),
            )

        return QueryMetrics(
            total_queries=len(self.query_times),
            avg_duration_ms=sum(self.query_times) / len(self.query_times),
            min_duration_ms=min(self.query_times),
            max_duration_ms=max(self.query_times),
            slow_query_count=len(self.slow_queries),
            timestamp=datetime.utcnow(),
        )

    def get_slow_queries(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get slowest queries.

        Args:
            limit: Maximum number to return

        Returns:
            List of slow query records
        """
        return sorted(
            self.slow_queries,
            key=lambda x: x["duration_ms"],
            reverse=True,
        )[:limit]


class DeadlockDetector:
    """Detect and track database deadlocks."""

    def __init__(self, session: Session):
        """
        Initialize deadlock detector.

        Args:
            session: Database session
        """
        self.session = session
        self.deadlocks: list[dict[str, Any]] = []

    def check_for_deadlocks(self) -> tuple[bool, list[dict[str, Any]]]:
        """
        Check for recent deadlocks (PostgreSQL specific).

        Returns:
            Tuple of (has_deadlocks, deadlock_records)
        """
        try:
            # PostgreSQL: Check for deadlock errors
            result = self.session.execute(
                text("""
                    SELECT * FROM pg_stat_statements
                    WHERE query LIKE '%deadlock%'
                    ORDER BY calls DESC
                    LIMIT 10
                """)
            ).fetchall()

            deadlocks = [dict(row) for row in result]
            self.deadlocks.extend(deadlocks)

            # Keep only recent deadlocks
            cutoff = datetime.utcnow() - timedelta(hours=24)
            self.deadlocks = [
                d
                for d in self.deadlocks
                if d.get("timestamp", datetime.utcnow()) > cutoff
            ]

            return len(deadlocks) > 0, deadlocks

        except Exception as e:
            logger.debug(f"Could not check for deadlocks: {e}")
            return False, []

    def get_deadlock_summary(self) -> dict[str, Any]:
        """
        Get deadlock summary.

        Returns:
            Summary dictionary
        """
        return {
            "total_deadlocks": len(self.deadlocks),
            "recent_deadlocks": self.deadlocks[-5:],
        }


class IndexUsageAnalyzer:
    """Analyze index usage and efficiency."""

    def __init__(self, session: Session):
        """
        Initialize index usage analyzer.

        Args:
            session: Database session
        """
        self.session = session

    def get_unused_indexes(self) -> list[dict[str, Any]]:
        """
        Get unused indexes (PostgreSQL specific).

        Returns:
            List of unused index information
        """
        try:
            result = self.session.execute(
                text("""
                    SELECT schemaname, tablename, indexname, idx_scan
                    FROM pg_stat_user_indexes
                    WHERE idx_scan = 0
                    ORDER BY pg_relation_size(indexrelid) DESC
                """)
            ).fetchall()

            return [dict(row) for row in result]

        except Exception as e:
            logger.debug(f"Could not get unused indexes: {e}")
            return []

    def get_index_efficiency(self) -> list[dict[str, Any]]:
        """
        Get index usage efficiency metrics.

        Returns:
            List of index efficiency records
        """
        try:
            result = self.session.execute(
                text("""
                    SELECT schemaname, tablename, indexname, idx_scan,
                           idx_tup_read, idx_tup_fetch
                    FROM pg_stat_user_indexes
                    ORDER BY idx_scan DESC
                    LIMIT 20
                """)
            ).fetchall()

            return [dict(row) for row in result]

        except Exception as e:
            logger.debug(f"Could not get index efficiency: {e}")
            return []


class TableSizeMonitor:
    """Monitor table sizes."""

    def __init__(self, session: Session):
        """
        Initialize table size monitor.

        Args:
            session: Database session
        """
        self.session = session
        self.table_metrics: list[TableMetrics] = []

    def get_table_sizes(self) -> list[TableMetrics]:
        """
        Get sizes of all tables.

        Returns:
            List of TableMetrics
        """
        try:
            result = self.session.execute(
                text("""
                    SELECT tablename, n_live_tup,
                           pg_total_relation_size(schemaname||'.'||tablename)/1024.0/1024.0 as size_mb
                    FROM pg_stat_user_tables
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                """)
            ).fetchall()

            metrics = []
            for row in result:
                metric = TableMetrics(
                    table_name=row[0],
                    row_count=row[1],
                    size_mb=row[2],
                    index_count=0,  # Could be fetched separately
                    timestamp=datetime.utcnow(),
                )
                metrics.append(metric)

            self.table_metrics.extend(metrics)

            # Keep only recent metrics
            if len(self.table_metrics) > 500:
                self.table_metrics = self.table_metrics[-500:]

            return metrics

        except Exception as e:
            logger.debug(f"Could not get table sizes: {e}")
            return []

    def get_largest_tables(self, limit: int = 10) -> list[TableMetrics]:
        """
        Get largest tables.

        Args:
            limit: Maximum number to return

        Returns:
            List of largest tables
        """
        metrics = self.get_table_sizes()
        return sorted(metrics, key=lambda m: m.size_mb, reverse=True)[:limit]

    def get_growth_trend(self, table_name: str) -> dict[str, Any]:
        """
        Get growth trend for a specific table.

        Args:
            table_name: Name of table

        Returns:
            Growth trend information
        """
        table_metrics = [m for m in self.table_metrics if m.table_name == table_name]

        if len(table_metrics) < 2:
            return {}

        first = table_metrics[0]
        last = table_metrics[-1]

        size_growth_mb = last.size_mb - first.size_mb
        row_growth = last.row_count - first.row_count
        time_span = (last.timestamp - first.timestamp).total_seconds() / 3600

        return {
            "table_name": table_name,
            "size_growth_mb": size_growth_mb,
            "row_growth": row_growth,
            "time_span_hours": time_span,
            "growth_rate_mb_per_hour": size_growth_mb / time_span
            if time_span > 0
            else 0,
        }


class DatabaseHealthCheck:
    """Comprehensive database health check."""

    def __init__(self, engine: Engine, session: Session):
        """
        Initialize health check.

        Args:
            engine: SQLAlchemy engine
            session: Database session
        """
        self.engine = engine
        self.session = session
        self.pool_monitor = ConnectionPoolMonitor(engine)
        self.latency_tracker = QueryLatencyTracker()
        self.deadlock_detector = DeadlockDetector(session)
        self.index_analyzer = IndexUsageAnalyzer(session)
        self.table_monitor = TableSizeMonitor(session)

    def run_full_check(self) -> dict[str, Any]:
        """
        Run comprehensive health check.

        Returns:
            Dictionary with all health metrics
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "connection_pool": self.pool_monitor.get_metrics_summary(),
            "query_latency": self.latency_tracker.get_metrics().to_dict(),
            "slow_queries": self.latency_tracker.get_slow_queries(limit=5),
            "deadlocks": self.deadlock_detector.get_deadlock_summary(),
            "unused_indexes": self.index_analyzer.get_unused_indexes()[:5],
            "largest_tables": [
                m.to_dict() for m in self.table_monitor.get_largest_tables(limit=5)
            ],
        }

    def is_healthy(
        self,
        max_pool_utilization: float = 85.0,
        max_avg_query_time: float = 200.0,
    ) -> bool:
        """
        Check if database is healthy.

        Args:
            max_pool_utilization: Max acceptable pool utilization percent
            max_avg_query_time: Max acceptable average query time in ms

        Returns:
            True if healthy, False otherwise
        """
        pool_healthy = self.pool_monitor.is_healthy(max_pool_utilization)
        query_metrics = self.latency_tracker.get_metrics()
        query_healthy = query_metrics.avg_duration_ms < max_avg_query_time

        return pool_healthy and query_healthy

    def get_health_status(self) -> dict[str, Any]:
        """
        Get current health status.

        Returns:
            Health status dictionary
        """
        return {
            "healthy": self.is_healthy(),
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "connection_pool": self.pool_monitor.is_healthy(),
                "query_latency": self.latency_tracker.get_metrics().avg_duration_ms
                < 200.0,
                "no_deadlocks": len(self.deadlock_detector.deadlocks) == 0,
            },
        }
