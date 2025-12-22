"""Database connection pool optimization package.

This package provides advanced connection pool management including:
- Dynamic pool sizing based on utilization
- Real-time monitoring and metrics
- Automatic health checks and recovery
- Query timeout handling
- Pool overflow protection
- Connection pre-warming
- Graceful shutdown

Usage:
    from app.db.pool import initialize_pool_manager, get_pool_manager
    from app.db.pool.config import PoolConfig

    # Initialize with custom configuration
    config = PoolConfig(
        pool_size=20,
        max_overflow=40,
        enable_monitoring=True,
        enable_dynamic_sizing=True
    )

    # Initialize pool manager
    pool_manager = initialize_pool_manager(database_url, config)

    # Get metrics
    metrics = pool_manager.get_metrics()

    # Get health status
    health = pool_manager.get_health_status()

    # Shutdown gracefully
    pool_manager.shutdown()
"""

from app.db.pool.config import PoolConfig, get_pool_config_from_settings
from app.db.pool.health import (
    AutoRecovery,
    ConnectionValidator,
    HealthCheckResult,
    PoolHealthChecker,
)
from app.db.pool.manager import (
    PoolManager,
    get_pool_manager,
    initialize_pool_manager,
    shutdown_pool_manager,
)
from app.db.pool.monitoring import PoolMonitor, PoolSnapshot, PoolStatistics

__all__ = [
    # Configuration
    "PoolConfig",
    "get_pool_config_from_settings",
    # Manager
    "PoolManager",
    "get_pool_manager",
    "initialize_pool_manager",
    "shutdown_pool_manager",
    # Monitoring
    "PoolMonitor",
    "PoolSnapshot",
    "PoolStatistics",
    # Health
    "PoolHealthChecker",
    "HealthCheckResult",
    "ConnectionValidator",
    "AutoRecovery",
]
