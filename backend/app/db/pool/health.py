"""Database connection pool health checks.

This module provides health check functionality for the connection pool,
including connection validation, performance checks, and automatic recovery.
"""
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.pool.config import PoolConfig

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a pool health check.

    Attributes:
        timestamp: When check was performed
        is_healthy: Overall health status
        connection_count: Number of connections tested
        successful_pings: Number of successful pings
        failed_pings: Number of failed pings
        avg_ping_time: Average ping response time (ms)
        errors: List of error messages
        warnings: List of warning messages
    """

    timestamp: datetime
    is_healthy: bool
    connection_count: int
    successful_pings: int
    failed_pings: int
    avg_ping_time: float
    errors: List[str]
    warnings: List[str]


class PoolHealthChecker:
    """Perform health checks on database connection pool.

    This class validates pool connections, checks performance,
    and can trigger automatic recovery actions.
    """

    def __init__(self, session_factory, config: PoolConfig):
        """Initialize health checker.

        Args:
            session_factory: SQLAlchemy session factory
            config: Pool configuration
        """
        self._session_factory = session_factory
        self._config = config
        self._last_check: Optional[HealthCheckResult] = None

    def check_connection_health(
        self, connection, connection_record, connection_proxy
    ) -> bool:
        """Check if a connection is healthy.

        This is called by SQLAlchemy's pre_ping mechanism.

        Args:
            connection: Database connection
            connection_record: Connection record
            connection_proxy: Connection proxy

        Returns:
            bool: True if connection is healthy
        """
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception as e:
            logger.warning(f"Connection health check failed: {e}")
            return False

    def perform_health_check(self) -> HealthCheckResult:
        """Perform comprehensive health check on pool.

        Returns:
            HealthCheckResult: Health check results
        """
        timestamp = datetime.utcnow()
        errors = []
        warnings = []
        successful_pings = 0
        failed_pings = 0
        ping_times = []

        # Test a connection from the pool
        try:
            session = self._session_factory()
            try:
                # Ping database
                import time

                start = time.perf_counter()
                session.execute(text("SELECT 1"))
                ping_time = (time.perf_counter() - start) * 1000  # Convert to ms
                ping_times.append(ping_time)
                successful_pings += 1

                # Check for slow queries
                if ping_time > 100:  # 100ms threshold
                    warnings.append(
                        f"Slow ping detected: {ping_time:.2f}ms (threshold: 100ms)"
                    )

            except OperationalError as e:
                failed_pings += 1
                errors.append(f"Database operational error: {str(e)}")
                logger.error(f"Health check operational error: {e}", exc_info=True)
            except SQLAlchemyError as e:
                failed_pings += 1
                errors.append(f"Database error: {str(e)}")
                logger.error(f"Health check SQLAlchemy error: {e}", exc_info=True)
            finally:
                session.close()

        except Exception as e:
            failed_pings += 1
            errors.append(f"Failed to acquire connection: {str(e)}")
            logger.error(f"Health check connection error: {e}", exc_info=True)

        # Calculate metrics
        avg_ping_time = sum(ping_times) / len(ping_times) if ping_times else 0.0
        is_healthy = failed_pings == 0 and len(errors) == 0

        result = HealthCheckResult(
            timestamp=timestamp,
            is_healthy=is_healthy,
            connection_count=successful_pings + failed_pings,
            successful_pings=successful_pings,
            failed_pings=failed_pings,
            avg_ping_time=avg_ping_time,
            errors=errors,
            warnings=warnings,
        )

        self._last_check = result
        return result

    def get_last_check_result(self) -> Optional[HealthCheckResult]:
        """Get result of last health check.

        Returns:
            HealthCheckResult: Last check result, or None if no checks performed
        """
        return self._last_check

    def validate_pool_configuration(self) -> List[str]:
        """Validate pool configuration and return warnings.

        Returns:
            list: List of configuration warnings
        """
        warnings = []

        # Check pool size
        if self._config.pool_size < 5:
            warnings.append(
                f"Pool size ({self._config.pool_size}) is low. "
                "Consider increasing to at least 5 for production."
            )

        if self._config.pool_size > 50:
            warnings.append(
                f"Pool size ({self._config.pool_size}) is very high. "
                "This may consume excessive database resources."
            )

        # Check overflow
        if self._config.max_overflow > self._config.pool_size * 3:
            warnings.append(
                f"Max overflow ({self._config.max_overflow}) is very high "
                f"relative to pool size ({self._config.pool_size}). "
                "This may indicate pool size is too small."
            )

        # Check timeout
        if self._config.timeout < 10:
            warnings.append(
                f"Pool timeout ({self._config.timeout}s) is low. "
                "This may cause timeout errors under load."
            )

        # Check recycle time
        if self._config.recycle < 600:
            warnings.append(
                f"Connection recycle time ({self._config.recycle}s) is low. "
                "This may cause excessive connection churn."
            )

        if self._config.recycle > 7200:
            warnings.append(
                f"Connection recycle time ({self._config.recycle}s) is high. "
                "This may allow stale connections to persist."
            )

        return warnings


class ConnectionValidator:
    """Validate individual database connections.

    This class provides utilities for validating connection state,
    testing queries, and detecting connection issues.
    """

    @staticmethod
    def validate_connection(session: Session) -> bool:
        """Validate that a session has a working connection.

        Args:
            session: SQLAlchemy session to validate

        Returns:
            bool: True if connection is valid
        """
        try:
            session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.warning(f"Connection validation failed: {e}")
            return False

    @staticmethod
    def test_query_timeout(session: Session, timeout_seconds: int = 5) -> bool:
        """Test that query timeout is working.

        Args:
            session: SQLAlchemy session
            timeout_seconds: Timeout to test

        Returns:
            bool: True if timeout mechanism is working
        """
        try:
            # Set statement timeout
            session.execute(text(f"SET statement_timeout = {timeout_seconds * 1000}"))

            # Try a query that should timeout
            # pg_sleep is a PostgreSQL function that sleeps for N seconds
            session.execute(text(f"SELECT pg_sleep({timeout_seconds + 1})"))

            # If we get here, timeout didn't work
            return False
        except OperationalError:
            # Timeout worked correctly
            return True
        except Exception as e:
            logger.error(f"Query timeout test failed: {e}")
            return False
        finally:
            # Reset timeout
            try:
                session.rollback()
                session.execute(text("SET statement_timeout = 0"))
            except Exception:
                pass

    @staticmethod
    def check_connection_age(connection_record) -> Optional[float]:
        """Check how long a connection has been alive.

        Args:
            connection_record: SQLAlchemy connection record

        Returns:
            float: Connection age in seconds, or None if unavailable
        """
        if hasattr(connection_record, "info") and "connect_time" in connection_record.info:
            import time

            return time.time() - connection_record.info["connect_time"]
        return None


class AutoRecovery:
    """Automatic recovery for pool issues.

    This class handles automatic recovery actions when pool
    health checks detect problems.
    """

    def __init__(self, pool, config: PoolConfig):
        """Initialize auto recovery.

        Args:
            pool: SQLAlchemy connection pool
            config: Pool configuration
        """
        self._pool = pool
        self._config = config
        self._recovery_attempts = 0
        self._max_recovery_attempts = 3

    def attempt_recovery(self, health_result: HealthCheckResult) -> bool:
        """Attempt to recover from health check failures.

        Args:
            health_result: Failed health check result

        Returns:
            bool: True if recovery was successful
        """
        if self._recovery_attempts >= self._max_recovery_attempts:
            logger.error(
                f"Max recovery attempts ({self._max_recovery_attempts}) reached. "
                "Manual intervention required."
            )
            return False

        self._recovery_attempts += 1
        logger.warning(
            f"Attempting pool recovery (attempt {self._recovery_attempts}/"
            f"{self._max_recovery_attempts})"
        )

        try:
            # Dispose of current pool and recreate
            logger.info("Disposing current connection pool")
            self._pool.dispose()

            # Wait a bit before next attempt
            import time

            time.sleep(self._config.reconnect_delay)

            logger.info("Pool recovery attempt completed")
            return True

        except Exception as e:
            logger.error(f"Pool recovery failed: {e}", exc_info=True)
            return False

    def reset_recovery_counter(self):
        """Reset recovery attempt counter after successful health check."""
        self._recovery_attempts = 0
