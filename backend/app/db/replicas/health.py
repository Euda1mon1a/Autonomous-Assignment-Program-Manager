"""Replica health checking and lag detection.

This module provides health monitoring for database replicas, including:
- Connection health verification
- Replication lag detection
- Automatic marking of unhealthy replicas
"""
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, OperationalError

logger = logging.getLogger(__name__)


@dataclass
class ReplicaHealth:
    """Health status of a database replica.

    Attributes:
        is_healthy: Whether the replica is healthy and available
        lag_seconds: Replication lag in seconds (None if unavailable)
        last_check: Timestamp of last health check
        error_message: Error message if unhealthy
        consecutive_failures: Number of consecutive health check failures
    """

    is_healthy: bool
    lag_seconds: Optional[float] = None
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None
    consecutive_failures: int = 0


class HealthChecker:
    """Monitors health of database replicas.

    Performs periodic health checks including:
    - Connection verification (pre_ping)
    - Replication lag detection
    - Automatic replica circuit breaking
    """

    def __init__(
        self,
        max_lag_seconds: float = 30.0,
        max_consecutive_failures: int = 3,
        health_check_timeout: float = 5.0
    ):
        """Initialize health checker.

        Args:
            max_lag_seconds: Maximum acceptable replication lag in seconds
            max_consecutive_failures: Failures before marking replica unhealthy
            health_check_timeout: Timeout for health check queries in seconds
        """
        self.max_lag_seconds = max_lag_seconds
        self.max_consecutive_failures = max_consecutive_failures
        self.health_check_timeout = health_check_timeout
        self._health_cache: dict[str, ReplicaHealth] = {}

    def check_replica_health(self, engine: Engine, replica_name: str) -> ReplicaHealth:
        """Check health of a specific replica.

        Performs comprehensive health check including:
        1. Connection verification
        2. Replication lag measurement
        3. Query responsiveness

        Args:
            engine: SQLAlchemy engine for the replica
            replica_name: Identifier for the replica

        Returns:
            ReplicaHealth: Current health status
        """
        start_time = time.time()

        try:
            # Test connection with simple query
            with engine.connect() as conn:
                # Set statement timeout for this connection
                conn.execute(
                    text(f"SET statement_timeout = {int(self.health_check_timeout * 1000)}")
                )

                # Verify connection is alive
                conn.execute(text("SELECT 1"))

                # Measure replication lag
                lag_seconds = self._measure_replication_lag(conn)

                # Check if lag is acceptable
                is_healthy = lag_seconds is None or lag_seconds <= self.max_lag_seconds

                health = ReplicaHealth(
                    is_healthy=is_healthy,
                    lag_seconds=lag_seconds,
                    last_check=datetime.utcnow(),
                    error_message=None if is_healthy else f"Replication lag too high: {lag_seconds}s",
                    consecutive_failures=0 if is_healthy else 1
                )

                # Update cache
                self._health_cache[replica_name] = health

                elapsed = time.time() - start_time
                logger.debug(
                    f"Health check for {replica_name}: healthy={is_healthy}, "
                    f"lag={lag_seconds}s, elapsed={elapsed:.3f}s"
                )

                return health

        except (OperationalError, DBAPIError) as e:
            # Connection or query error
            previous_health = self._health_cache.get(replica_name)
            consecutive_failures = (
                previous_health.consecutive_failures + 1
                if previous_health
                else 1
            )

            is_healthy = consecutive_failures < self.max_consecutive_failures

            health = ReplicaHealth(
                is_healthy=is_healthy,
                lag_seconds=None,
                last_check=datetime.utcnow(),
                error_message=str(e),
                consecutive_failures=consecutive_failures
            )

            self._health_cache[replica_name] = health

            logger.warning(
                f"Health check failed for {replica_name}: {e} "
                f"(failures: {consecutive_failures}/{self.max_consecutive_failures})"
            )

            return health

        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error checking health of {replica_name}: {e}")

            health = ReplicaHealth(
                is_healthy=False,
                lag_seconds=None,
                last_check=datetime.utcnow(),
                error_message=f"Unexpected error: {e}",
                consecutive_failures=self.max_consecutive_failures
            )

            self._health_cache[replica_name] = health

            return health

    def _measure_replication_lag(self, connection) -> Optional[float]:
        """Measure replication lag using PostgreSQL system views.

        Args:
            connection: Active database connection

        Returns:
            Lag in seconds, or None if not available (e.g., on primary)
        """
        try:
            # Check if this is a standby (replica)
            result = connection.execute(
                text("SELECT pg_is_in_recovery()")
            ).scalar()

            if not result:
                # This is the primary, not a replica
                return None

            # Get replay lag (time between last WAL received and applied)
            lag_result = connection.execute(
                text("""
                    SELECT EXTRACT(EPOCH FROM (
                        pg_last_wal_receive_lsn() - pg_last_wal_replay_lsn()
                    )) /
                    NULLIF(
                        (SELECT setting::int FROM pg_settings WHERE name = 'wal_block_size'),
                        0
                    ) AS lag_bytes,
                    EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) AS lag_seconds
                """)
            ).first()

            if lag_result and lag_result[1] is not None:
                # Return time-based lag (more accurate)
                return float(lag_result[1])

            # Fallback: estimate lag from LSN difference
            # This is less accurate but better than nothing
            if lag_result and lag_result[0] is not None:
                # Rough estimate: assume 16MB/s replication speed
                estimated_lag = float(lag_result[0]) / (16 * 1024 * 1024)
                return estimated_lag

            return None

        except Exception as e:
            logger.warning(f"Could not measure replication lag: {e}")
            return None

    def get_cached_health(
        self,
        replica_name: str,
        max_age_seconds: float = 10.0
    ) -> Optional[ReplicaHealth]:
        """Get cached health status if recent enough.

        Args:
            replica_name: Identifier for the replica
            max_age_seconds: Maximum age of cached health check

        Returns:
            Cached health status, or None if not available or stale
        """
        health = self._health_cache.get(replica_name)

        if not health or not health.last_check:
            return None

        age = (datetime.utcnow() - health.last_check).total_seconds()

        if age > max_age_seconds:
            return None

        return health

    def is_replica_healthy(
        self,
        engine: Engine,
        replica_name: str,
        use_cache: bool = True,
        cache_max_age: float = 10.0
    ) -> bool:
        """Quick health check with optional caching.

        Args:
            engine: SQLAlchemy engine for the replica
            replica_name: Identifier for the replica
            use_cache: Whether to use cached health status
            cache_max_age: Maximum age of cached status in seconds

        Returns:
            True if replica is healthy, False otherwise
        """
        if use_cache:
            cached = self.get_cached_health(replica_name, cache_max_age)
            if cached:
                return cached.is_healthy

        health = self.check_replica_health(engine, replica_name)
        return health.is_healthy

    def reset_failures(self, replica_name: str) -> None:
        """Reset consecutive failure count for a replica.

        Useful when manually recovering a replica or after maintenance.

        Args:
            replica_name: Identifier for the replica
        """
        if replica_name in self._health_cache:
            health = self._health_cache[replica_name]
            health.consecutive_failures = 0
            logger.info(f"Reset failure count for replica {replica_name}")
