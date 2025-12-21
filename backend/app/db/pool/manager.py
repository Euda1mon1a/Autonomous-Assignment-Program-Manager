"""Database connection pool manager.

This module provides the main connection pool manager that coordinates
pool configuration, monitoring, health checks, and automatic recovery.
"""
import logging
import threading
import time
from typing import Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import Pool, QueuePool

from app.db.pool.config import PoolConfig
from app.db.pool.health import AutoRecovery, HealthCheckResult, PoolHealthChecker
from app.db.pool.monitoring import PoolMonitor

logger = logging.getLogger(__name__)


class PoolManager:
    """Manage database connection pool lifecycle and health.

    This class coordinates all aspects of connection pool management including:
    - Pool creation and configuration
    - Dynamic pool sizing
    - Health monitoring
    - Automatic recovery
    - Graceful shutdown
    """

    def __init__(self, database_url: str, config: Optional[PoolConfig] = None):
        """Initialize pool manager.

        Args:
            database_url: Database connection URL
            config: Pool configuration (uses defaults if not provided)
        """
        self._database_url = database_url
        self._config = config or PoolConfig()
        self._engine: Optional[Engine] = None
        self._session_factory = None
        self._pool: Optional[Pool] = None
        self._monitor: Optional[PoolMonitor] = None
        self._health_checker: Optional[PoolHealthChecker] = None
        self._auto_recovery: Optional[AutoRecovery] = None
        self._health_check_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        self._is_running = False

    def initialize(self) -> Engine:
        """Initialize the connection pool and engine.

        Returns:
            Engine: SQLAlchemy engine with configured pool

        Raises:
            RuntimeError: If already initialized
        """
        if self._engine is not None:
            raise RuntimeError("Pool manager already initialized")

        logger.info("Initializing database connection pool")

        # Create engine with pool configuration
        self._engine = create_engine(
            self._database_url,
            poolclass=QueuePool,
            pool_size=self._config.pool_size,
            max_overflow=self._config.max_overflow,
            pool_timeout=self._config.timeout,
            pool_recycle=self._config.recycle,
            pool_pre_ping=self._config.pre_ping,
            echo_pool=self._config.echo_pool,
            pool_reset_on_return=self._config.pool_reset_on_return,
            connect_args={"connect_timeout": self._config.connect_timeout},
        )

        # Get pool reference
        self._pool = self._engine.pool

        # Create session factory
        self._session_factory = sessionmaker(
            autocommit=False, autoflush=False, bind=self._engine
        )

        # Initialize monitoring
        if self._config.enable_monitoring:
            self._monitor = PoolMonitor(self._pool)
            self._setup_pool_events()

        # Initialize health checker
        self._health_checker = PoolHealthChecker(self._session_factory, self._config)

        # Initialize auto recovery
        self._auto_recovery = AutoRecovery(self._pool, self._config)

        # Pre-warm connections if configured
        if self._config.pool_size > 0:
            self._prewarm_connections()

        # Start health check thread
        if self._config.enable_monitoring:
            self._start_health_checks()

        self._is_running = True
        logger.info(
            f"Pool initialized: size={self._config.pool_size}, "
            f"max_overflow={self._config.max_overflow}"
        )

        return self._engine

    def _setup_pool_events(self):
        """Set up SQLAlchemy pool event listeners for monitoring."""
        if not self._monitor:
            return

        @event.listens_for(self._pool, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Track connection creation."""
            # Store connect time in connection record
            connection_record.info["connect_time"] = time.time()
            self._monitor.record_connect()
            logger.debug(f"New connection created: {id(dbapi_conn)}")

        @event.listens_for(self._pool, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Track connection checkout."""
            self._monitor.record_checkout(id(dbapi_conn))
            logger.debug(f"Connection checked out: {id(dbapi_conn)}")

        @event.listens_for(self._pool, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Track connection checkin."""
            self._monitor.record_checkin(id(dbapi_conn))
            logger.debug(f"Connection checked in: {id(dbapi_conn)}")

        @event.listens_for(self._pool, "reset")
        def receive_reset(dbapi_conn, connection_record):
            """Track connection reset."""
            logger.debug(f"Connection reset: {id(dbapi_conn)}")

        @event.listens_for(self._pool, "invalidate")
        def receive_invalidate(dbapi_conn, connection_record, exception):
            """Track connection invalidation."""
            self._monitor.record_disconnect()
            logger.warning(
                f"Connection invalidated: {id(dbapi_conn)}, reason: {exception}"
            )

    def _prewarm_connections(self):
        """Pre-warm the connection pool by creating initial connections.

        This reduces latency for the first few requests by establishing
        connections in advance.
        """
        logger.info(f"Pre-warming {self._config.pool_size} connections")
        connections = []

        try:
            # Check out connections to force creation
            for i in range(self._config.pool_size):
                try:
                    conn = self._engine.connect()
                    connections.append(conn)
                except Exception as e:
                    logger.error(f"Failed to pre-warm connection {i + 1}: {e}")
                    break

            logger.info(f"Pre-warmed {len(connections)} connections")

        finally:
            # Return all connections to pool
            for conn in connections:
                try:
                    conn.close()
                except Exception as e:
                    logger.error(f"Error closing pre-warmed connection: {e}")

    def _start_health_checks(self):
        """Start background health check thread."""
        if self._health_check_thread and self._health_check_thread.is_alive():
            return

        self._shutdown_event.clear()
        self._health_check_thread = threading.Thread(
            target=self._health_check_loop, daemon=True, name="PoolHealthChecker"
        )
        self._health_check_thread.start()
        logger.info("Health check thread started")

    def _health_check_loop(self):
        """Background loop for periodic health checks."""
        while not self._shutdown_event.is_set():
            try:
                # Perform health check
                result = self._health_checker.perform_health_check()

                if result.is_healthy:
                    logger.debug("Pool health check passed")
                    self._auto_recovery.reset_recovery_counter()
                else:
                    logger.warning(
                        f"Pool health check failed: {len(result.errors)} errors, "
                        f"{len(result.warnings)} warnings"
                    )
                    for error in result.errors:
                        logger.error(f"Health check error: {error}")

                    # Attempt recovery if configured
                    if self._auto_recovery:
                        recovery_success = self._auto_recovery.attempt_recovery(result)
                        if recovery_success:
                            logger.info("Pool recovery successful")
                        else:
                            logger.error("Pool recovery failed")

                # Check if dynamic sizing is needed
                if self._config.enable_dynamic_sizing:
                    self._adjust_pool_size()

            except Exception as e:
                logger.error(f"Error in health check loop: {e}", exc_info=True)

            # Wait for next check interval
            self._shutdown_event.wait(self._config.health_check_interval)

    def _adjust_pool_size(self):
        """Dynamically adjust pool size based on utilization.

        This implements automatic pool scaling based on current load.
        """
        if not self._monitor:
            return

        snapshot = self._monitor.get_current_snapshot()
        current_size = snapshot.size
        utilization = snapshot.utilization

        # Scale up if utilization is high
        if utilization >= self._config.scale_up_threshold:
            new_size = min(current_size + 5, self._config.max_pool_size)
            if new_size > current_size:
                logger.info(
                    f"Scaling pool up: {current_size} -> {new_size} "
                    f"(utilization: {utilization:.2%})"
                )
                self._update_pool_size(new_size)

        # Scale down if utilization is low
        elif utilization <= self._config.scale_down_threshold:
            new_size = max(current_size - 5, self._config.min_pool_size)
            if new_size < current_size:
                logger.info(
                    f"Scaling pool down: {current_size} -> {new_size} "
                    f"(utilization: {utilization:.2%})"
                )
                self._update_pool_size(new_size)

    def _update_pool_size(self, new_size: int):
        """Update the pool size dynamically.

        Note: SQLAlchemy's QueuePool doesn't support runtime size changes,
        so this implementation recreates the engine with the new pool size.

        Args:
            new_size: New pool size
        """
        if new_size == self._config.pool_size:
            logger.debug(f"Pool size unchanged at {new_size}")
            return

        logger.info(
            f"Resizing pool from {self._config.pool_size} to {new_size} connections"
        )

        try:
            # Update config
            old_size = self._config.pool_size
            self._config.pool_size = new_size

            # Dispose old engine and pool
            if self._engine:
                logger.debug("Disposing old engine and pool")
                self._engine.dispose()

            # Create new engine with updated pool size
            self._engine = create_engine(
                self._database_url,
                poolclass=QueuePool,
                pool_size=self._config.pool_size,
                max_overflow=self._config.max_overflow,
                pool_timeout=self._config.timeout,
                pool_recycle=self._config.recycle,
                pool_pre_ping=self._config.pre_ping,
                echo_pool=self._config.echo_pool,
                pool_reset_on_return=self._config.pool_reset_on_return,
                connect_args={"connect_timeout": self._config.connect_timeout},
            )

            # Get new pool reference
            self._pool = self._engine.pool

            # Update session factory
            self._session_factory = sessionmaker(
                autocommit=False, autoflush=False, bind=self._engine
            )

            # Re-setup pool events for monitoring
            if self._config.enable_monitoring and self._monitor:
                self._setup_pool_events()

            # Update monitor reference
            if self._monitor:
                self._monitor._pool = self._pool

            # Update auto-recovery reference
            if self._auto_recovery:
                self._auto_recovery._pool = self._pool

            logger.info(
                f"Pool successfully resized from {old_size} to {new_size} connections"
            )

        except Exception as e:
            logger.error(f"Failed to resize pool: {e}", exc_info=True)
            # Attempt to restore old size
            self._config.pool_size = old_size
            raise

    def get_session_factory(self):
        """Get the session factory for creating database sessions.

        Returns:
            sessionmaker: Session factory

        Raises:
            RuntimeError: If pool not initialized
        """
        if not self._session_factory:
            raise RuntimeError("Pool manager not initialized")
        return self._session_factory

    def get_engine(self) -> Engine:
        """Get the SQLAlchemy engine.

        Returns:
            Engine: SQLAlchemy engine

        Raises:
            RuntimeError: If pool not initialized
        """
        if not self._engine:
            raise RuntimeError("Pool manager not initialized")
        return self._engine

    def get_monitor(self) -> Optional[PoolMonitor]:
        """Get the pool monitor.

        Returns:
            PoolMonitor: Pool monitor, or None if monitoring disabled
        """
        return self._monitor

    def get_health_checker(self) -> Optional[PoolHealthChecker]:
        """Get the health checker.

        Returns:
            PoolHealthChecker: Health checker
        """
        return self._health_checker

    def get_metrics(self) -> dict:
        """Get current pool metrics.

        Returns:
            dict: Pool metrics summary
        """
        if not self._monitor:
            return {"monitoring_enabled": False}

        return self._monitor.get_metrics_summary()

    def get_health_status(self) -> dict:
        """Get current pool health status.

        Returns:
            dict: Health status information
        """
        if not self._health_checker:
            return {"health_checks_enabled": False}

        last_result = self._health_checker.get_last_check_result()
        if not last_result:
            return {"status": "unknown", "message": "No health checks performed yet"}

        return {
            "is_healthy": last_result.is_healthy,
            "timestamp": last_result.timestamp.isoformat(),
            "successful_pings": last_result.successful_pings,
            "failed_pings": last_result.failed_pings,
            "avg_ping_time": last_result.avg_ping_time,
            "errors": last_result.errors,
            "warnings": last_result.warnings,
        }

    def shutdown(self, timeout: int = 30):
        """Gracefully shutdown the pool manager.

        Args:
            timeout: Maximum seconds to wait for shutdown
        """
        if not self._is_running:
            return

        logger.info("Shutting down pool manager")
        self._is_running = False

        # Stop health check thread
        if self._health_check_thread:
            self._shutdown_event.set()
            self._health_check_thread.join(timeout=timeout)
            if self._health_check_thread.is_alive():
                logger.warning("Health check thread did not stop within timeout")

        # Dispose of pool
        if self._engine:
            logger.info("Disposing database engine and connection pool")
            self._engine.dispose()

        logger.info("Pool manager shutdown complete")

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


# Global pool manager instance
_pool_manager: Optional[PoolManager] = None


def get_pool_manager() -> PoolManager:
    """Get the global pool manager instance.

    Returns:
        PoolManager: Global pool manager

    Raises:
        RuntimeError: If pool manager not initialized
    """
    global _pool_manager
    if _pool_manager is None:
        raise RuntimeError(
            "Pool manager not initialized. Call initialize_pool_manager() first."
        )
    return _pool_manager


def initialize_pool_manager(
    database_url: str, config: Optional[PoolConfig] = None
) -> PoolManager:
    """Initialize the global pool manager.

    Args:
        database_url: Database connection URL
        config: Pool configuration

    Returns:
        PoolManager: Initialized pool manager
    """
    global _pool_manager
    if _pool_manager is not None:
        logger.warning("Pool manager already initialized, disposing old instance")
        _pool_manager.shutdown()

    _pool_manager = PoolManager(database_url, config)
    _pool_manager.initialize()
    return _pool_manager


def shutdown_pool_manager():
    """Shutdown the global pool manager."""
    global _pool_manager
    if _pool_manager:
        _pool_manager.shutdown()
        _pool_manager = None
