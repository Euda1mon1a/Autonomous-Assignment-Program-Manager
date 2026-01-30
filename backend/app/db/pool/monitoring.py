"""Database connection pool monitoring and statistics.

This module provides real-time monitoring of connection pool metrics,
including active connections, idle connections, waiting requests, and
performance statistics.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock

from sqlalchemy.pool import Pool


@dataclass
class PoolSnapshot:
    """Snapshot of pool state at a point in time.

    Attributes:
        timestamp: When snapshot was taken
        size: Current pool size
        checked_in: Number of connections checked in (idle)
        checked_out: Number of connections checked out (active)
        overflow: Number of overflow connections
        total_connections: Total connections (pool + overflow)
        waiting: Number of requests waiting for connection
        utilization: Pool utilization ratio (0.0 to 1.0)
    """

    timestamp: datetime
    size: int
    checked_in: int
    checked_out: int
    overflow: int
    total_connections: int
    waiting: int = 0
    utilization: float = 0.0

    def __post_init__(self) -> None:
        """Calculate derived metrics."""
        if self.total_connections > 0:
            self.utilization = self.checked_out / self.total_connections


@dataclass
class PoolStatistics:
    """Aggregated statistics for connection pool.

    Attributes:
        total_checkouts: Total number of connection checkouts
        total_checkins: Total number of connection checkins
        total_connects: Total number of new connections created
        total_disconnects: Total number of connections closed
        total_timeouts: Number of timeout errors
        total_overflows: Number of overflow connections used
        avg_checkout_duration: Average time connections are checked out (seconds)
        peak_connections: Maximum connections reached
        peak_utilization: Maximum utilization reached
        checkout_durations: List of recent checkout durations
    """

    total_checkouts: int = 0
    total_checkins: int = 0
    total_connects: int = 0
    total_disconnects: int = 0
    total_timeouts: int = 0
    total_overflows: int = 0
    avg_checkout_duration: float = 0.0
    peak_connections: int = 0
    peak_utilization: float = 0.0
    checkout_durations: list[float] = field(default_factory=list)

    def update_avg_checkout_duration(self, duration: float) -> None:
        """Update average checkout duration with new sample.

        Args:
            duration: Checkout duration in seconds
        """
        self.checkout_durations.append(duration)
        # Keep only last 100 samples
        if len(self.checkout_durations) > 100:
            self.checkout_durations.pop(0)
        if self.checkout_durations:
            self.avg_checkout_duration = sum(self.checkout_durations) / len(
                self.checkout_durations
            )


class PoolMonitor:
    """Monitor and track database connection pool metrics.

    This class provides real-time monitoring of pool state and aggregated
    statistics over time. Thread-safe for concurrent access.
    """

    def __init__(self, pool: Pool) -> None:
        """Initialize pool monitor.

        Args:
            pool: SQLAlchemy connection pool to monitor
        """
        self._pool = pool
        self._stats = PoolStatistics()
        self._snapshots: list[PoolSnapshot] = []
        self._max_snapshots = 100
        self._lock = Lock()
        self._checkout_times: dict[int, float] = {}

    def capture_snapshot(self) -> PoolSnapshot:
        """Capture current pool state.

        Returns:
            PoolSnapshot: Current pool state snapshot
        """
        pool_status = self._pool.status()

        # Parse pool status string
        # Example: "Pool size: 10  Connections in pool: 7 Current Overflow: 2 Current Checked out connections: 5"
        size = self._extract_metric(pool_status, "Pool size:")
        checked_in = self._extract_metric(pool_status, "Connections in pool:")
        overflow = self._extract_metric(pool_status, "Current Overflow:")
        checked_out = self._extract_metric(
            pool_status, "Current Checked out connections:"
        )

        total_connections = size + overflow

        snapshot = PoolSnapshot(
            timestamp=datetime.utcnow(),
            size=size,
            checked_in=checked_in,
            checked_out=checked_out,
            overflow=overflow,
            total_connections=total_connections,
        )

        with self._lock:
            self._snapshots.append(snapshot)
            if len(self._snapshots) > self._max_snapshots:
                self._snapshots.pop(0)

                # Update peak metrics
            if total_connections > self._stats.peak_connections:
                self._stats.peak_connections = total_connections
            if snapshot.utilization > self._stats.peak_utilization:
                self._stats.peak_utilization = snapshot.utilization

        return snapshot

    def _extract_metric(self, status: str, key: str) -> int:
        """Extract numeric metric from pool status string.

        Args:
            status: Pool status string
            key: Metric key to search for

        Returns:
            int: Extracted metric value, or 0 if not found
        """
        try:
            if key in status:
                start = status.index(key) + len(key)
                # Find the next space or end of string
                end = status.find(" ", start)
                if end == -1:
                    end = len(status)
                value_str = status[start:end].strip()
                return int(value_str)
        except (ValueError, IndexError):
            pass
        return 0

    def record_checkout(self, connection_id: int) -> None:
        """Record connection checkout event.

        Args:
            connection_id: Unique identifier for the connection
        """
        with self._lock:
            self._checkout_times[connection_id] = time.time()
            self._stats.total_checkouts += 1

    def record_checkin(self, connection_id: int) -> None:
        """Record connection checkin event.

        Args:
            connection_id: Unique identifier for the connection
        """
        with self._lock:
            self._stats.total_checkins += 1
            if connection_id in self._checkout_times:
                duration = time.time() - self._checkout_times[connection_id]
                self._stats.update_avg_checkout_duration(duration)
                del self._checkout_times[connection_id]

    def record_connect(self) -> None:
        """Record new connection creation."""
        with self._lock:
            self._stats.total_connects += 1

    def record_disconnect(self) -> None:
        """Record connection closure."""
        with self._lock:
            self._stats.total_disconnects += 1

    def record_timeout(self) -> None:
        """Record connection timeout error."""
        with self._lock:
            self._stats.total_timeouts += 1

    def record_overflow(self) -> None:
        """Record overflow connection usage."""
        with self._lock:
            self._stats.total_overflows += 1

    def get_current_snapshot(self) -> PoolSnapshot:
        """Get the most recent pool snapshot.

        Returns:
            PoolSnapshot: Most recent snapshot, or new snapshot if none exist
        """
        with self._lock:
            if self._snapshots:
                return self._snapshots[-1]
        return self.capture_snapshot()

    def get_statistics(self) -> PoolStatistics:
        """Get aggregated pool statistics.

        Returns:
            PoolStatistics: Copy of current statistics
        """
        with self._lock:
            # Return a copy to prevent external modification
            return PoolStatistics(
                total_checkouts=self._stats.total_checkouts,
                total_checkins=self._stats.total_checkins,
                total_connects=self._stats.total_connects,
                total_disconnects=self._stats.total_disconnects,
                total_timeouts=self._stats.total_timeouts,
                total_overflows=self._stats.total_overflows,
                avg_checkout_duration=self._stats.avg_checkout_duration,
                peak_connections=self._stats.peak_connections,
                peak_utilization=self._stats.peak_utilization,
                checkout_durations=self._stats.checkout_durations.copy(),
            )

    def get_metrics_summary(self) -> dict[str, any]:
        """Get summary of pool metrics for reporting.

        Returns:
            dict: Dictionary of current metrics
        """
        snapshot = self.get_current_snapshot()
        stats = self.get_statistics()

        return {
            "current": {
                "size": snapshot.size,
                "checked_in": snapshot.checked_in,
                "checked_out": snapshot.checked_out,
                "overflow": snapshot.overflow,
                "total_connections": snapshot.total_connections,
                "utilization": snapshot.utilization,
                "waiting": snapshot.waiting,
            },
            "lifetime": {
                "total_checkouts": stats.total_checkouts,
                "total_checkins": stats.total_checkins,
                "total_connects": stats.total_connects,
                "total_disconnects": stats.total_disconnects,
                "total_timeouts": stats.total_timeouts,
                "total_overflows": stats.total_overflows,
                "avg_checkout_duration": stats.avg_checkout_duration,
                "peak_connections": stats.peak_connections,
                "peak_utilization": stats.peak_utilization,
            },
        }

    def reset_statistics(self) -> None:
        """Reset all statistics counters."""
        with self._lock:
            self._stats = PoolStatistics()
            self._snapshots.clear()
            self._checkout_times.clear()

    def get_health_metrics(self) -> dict[str, any]:
        """Get health-related metrics for monitoring.

        Returns:
            dict: Health metrics including utilization and error rates
        """
        snapshot = self.get_current_snapshot()
        stats = self.get_statistics()

        # Calculate error rate
        total_operations = stats.total_checkouts + stats.total_connects
        error_rate = (
            stats.total_timeouts / total_operations if total_operations > 0 else 0.0
        )

        # Calculate overflow rate
        overflow_rate = (
            stats.total_overflows / stats.total_checkouts
            if stats.total_checkouts > 0
            else 0.0
        )

        return {
            "utilization": snapshot.utilization,
            "error_rate": error_rate,
            "overflow_rate": overflow_rate,
            "avg_checkout_duration": stats.avg_checkout_duration,
            "is_healthy": (
                snapshot.utilization < 0.9
                and error_rate < 0.01
                and stats.total_timeouts == 0
            ),
        }
