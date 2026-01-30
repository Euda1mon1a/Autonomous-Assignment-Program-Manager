"""Health checks for system dependencies and services."""

import asyncio
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# ============================================================================
# HEALTH STATUS ENUMS
# ============================================================================


class HealthStatus(str, Enum):
    """Health check status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class DependencyType(str, Enum):
    """Type of dependency."""

    DATABASE = "database"
    CACHE = "cache"
    EXTERNAL_SERVICE = "external_service"
    MESSAGE_QUEUE = "message_queue"
    FILE_SYSTEM = "file_system"

    # ============================================================================
    # HEALTH CHECK RESULT
    # ============================================================================


class HealthCheckResult:
    """Result of a health check."""

    def __init__(
        self,
        name: str,
        status: HealthStatus,
        response_time_ms: float,
        details: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """
        Initialize health check result.

        Args:
            name: Name of check
            status: Health status
            response_time_ms: Time to execute check in milliseconds
            details: Additional details
            error: Error message if unhealthy
        """
        self.name = name
        self.status = status
        self.response_time_ms = response_time_ms
        self.details = details or {}
        self.error = error
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "response_time_ms": round(self.response_time_ms, 2),
            "details": self.details,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


class OverallHealthResult:
    """Overall health check result."""

    def __init__(self, results: list[HealthCheckResult]) -> None:
        """
        Initialize overall result.

        Args:
            results: List of individual check results
        """
        self.results = results
        self.timestamp = datetime.utcnow()

    @property
    def overall_status(self) -> HealthStatus:
        """Get overall health status."""
        statuses = [r.status for r in self.results]

        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    @property
    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        return self.overall_status == HealthStatus.HEALTHY

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "overall_status": self.overall_status.value,
            "timestamp": self.timestamp.isoformat(),
            "checks": [r.to_dict() for r in self.results],
            "summary": {
                "total": len(self.results),
                "healthy": sum(
                    1 for r in self.results if r.status == HealthStatus.HEALTHY
                ),
                "degraded": sum(
                    1 for r in self.results if r.status == HealthStatus.DEGRADED
                ),
                "unhealthy": sum(
                    1 for r in self.results if r.status == HealthStatus.UNHEALTHY
                ),
            },
        }

        # ============================================================================
        # DATABASE HEALTH CHECK (Task 44)
        # ============================================================================


async def check_database_health(db: AsyncSession) -> HealthCheckResult:
    """
    Check database health.

    Args:
        db: Database session

    Returns:
        Health check result
    """
    start_time = time.time()

    try:
        # Execute simple query
        result = await db.execute(text("SELECT 1"))
        result.scalar()

        response_time = (time.time() - start_time) * 1000

        # Check response time
        if response_time > 100:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY

        return HealthCheckResult(
            name="database",
            status=status,
            response_time_ms=response_time,
            details={"connection_ok": True},
        )

    except (ConnectionError, TimeoutError) as e:
        response_time = (time.time() - start_time) * 1000

        return HealthCheckResult(
            name="database",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=response_time,
            error=f"Connection error: {str(e)}",
        )
    except RuntimeError as e:
        response_time = (time.time() - start_time) * 1000

        return HealthCheckResult(
            name="database",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=response_time,
            error=f"Database error: {str(e)}",
        )

        # ============================================================================
        # REDIS/CACHE HEALTH CHECK (Task 45)
        # ============================================================================


async def check_redis_health(redis_client: redis.Redis) -> HealthCheckResult:
    """
    Check Redis health.

    Args:
        redis_client: Redis client instance

    Returns:
        Health check result
    """
    start_time = time.time()

    try:
        # Ping Redis
        pong = await redis_client.ping()

        response_time = (time.time() - start_time) * 1000

        if not pong:
            return HealthCheckResult(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error="No response from Redis",
            )

            # Check memory usage
        info = await redis_client.info("memory")
        memory_used_mb = info.get("used_memory", 0) / (1024 * 1024)
        memory_max_mb = (
            info.get("maxmemory", 0) / (1024 * 1024) if info.get("maxmemory") else None
        )

        details = {
            "ping": "ok",
            "memory_used_mb": round(memory_used_mb, 2),
            "memory_max_mb": round(memory_max_mb, 2) if memory_max_mb else None,
        }

        # Determine status
        if response_time > 50:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY

        return HealthCheckResult(
            name="redis", status=status, response_time_ms=response_time, details=details
        )

    except (redis.ConnectionError, redis.RedisError) as e:
        response_time = (time.time() - start_time) * 1000

        return HealthCheckResult(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=response_time,
            error=f"Redis error: {str(e)}",
        )
    except (ConnectionError, TimeoutError) as e:
        response_time = (time.time() - start_time) * 1000

        return HealthCheckResult(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=response_time,
            error=f"Connection error: {str(e)}",
        )

        # ============================================================================
        # EXTERNAL SERVICE HEALTH CHECKS (Task 46)
        # ============================================================================


async def check_external_service(
    service_name: str, url: str, timeout_seconds: float = 5.0
) -> HealthCheckResult:
    """
    Check external service health.

    Args:
        service_name: Name of service
        url: Service URL to check
        timeout_seconds: Timeout for check

    Returns:
        Health check result
    """
    import aiohttp

    start_time = time.time()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=timeout_seconds)
            ) as response:
                response_time = (time.time() - start_time) * 1000

                if response.status == 200:
                    status = HealthStatus.HEALTHY
                elif 400 <= response.status < 500:
                    status = HealthStatus.DEGRADED
                else:
                    status = HealthStatus.UNHEALTHY

                return HealthCheckResult(
                    name=f"external_service_{service_name}",
                    status=status,
                    response_time_ms=response_time,
                    details={"status_code": response.status},
                )

    except TimeoutError:
        response_time = (time.time() - start_time) * 1000

        return HealthCheckResult(
            name=f"external_service_{service_name}",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=response_time,
            error="Request timeout",
        )

    except (ConnectionError, OSError) as e:
        response_time = (time.time() - start_time) * 1000

        return HealthCheckResult(
            name=f"external_service_{service_name}",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=response_time,
            error=f"Network error: {str(e)}",
        )

        # ============================================================================
        # DEPENDENCY HEALTH CHECKS (Task 47)
        # ============================================================================


async def check_disk_space(
    path: str = "/", min_free_gb: float = 1.0
) -> HealthCheckResult:
    """
    Check disk space availability.

    Args:
        path: Path to check
        min_free_gb: Minimum free space in GB

    Returns:
        Health check result
    """
    import shutil

    start_time = time.time()

    try:
        stat = shutil.disk_usage(path)
        free_gb = stat.free / (1024**3)
        total_gb = stat.total / (1024**3)
        used_percent = (stat.used / stat.total) * 100

        response_time = (time.time() - start_time) * 1000

        # Determine status
        if free_gb < min_free_gb:
            status = HealthStatus.UNHEALTHY
        elif used_percent > 90:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY

        return HealthCheckResult(
            name="disk_space",
            status=status,
            response_time_ms=response_time,
            details={
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2),
                "used_percent": round(used_percent, 2),
            },
        )

    except OSError as e:
        response_time = (time.time() - start_time) * 1000

        return HealthCheckResult(
            name="disk_space",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=response_time,
            error=f"File system error: {str(e)}",
        )
    except ValueError as e:
        response_time = (time.time() - start_time) * 1000

        return HealthCheckResult(
            name="disk_space",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=response_time,
            error=f"Invalid path: {str(e)}",
        )


async def check_memory_usage(max_percent: float = 90.0) -> HealthCheckResult:
    """
    Check system memory usage.

    Args:
        max_percent: Maximum acceptable memory usage percentage

    Returns:
        Health check result
    """
    import psutil

    start_time = time.time()

    try:
        memory = psutil.virtual_memory()
        used_percent = memory.percent

        response_time = (time.time() - start_time) * 1000

        # Determine status
        if used_percent > max_percent:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY

        return HealthCheckResult(
            name="memory",
            status=status,
            response_time_ms=response_time,
            details={
                "used_percent": round(used_percent, 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2),
            },
        )

    except RuntimeError as e:
        response_time = (time.time() - start_time) * 1000

        return HealthCheckResult(
            name="memory",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=response_time,
            error=f"Memory check error: {str(e)}",
        )
    except (OSError, ValueError) as e:
        response_time = (time.time() - start_time) * 1000

        return HealthCheckResult(
            name="memory",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=response_time,
            error=f"System error: {str(e)}",
        )


async def check_cpu_usage(max_percent: float = 80.0) -> HealthCheckResult:
    """
    Check system CPU usage.

    Args:
        max_percent: Maximum acceptable CPU usage percentage

    Returns:
        Health check result
    """
    import psutil

    start_time = time.time()

    try:
        cpu_percent = psutil.cpu_percent(interval=1.0)

        response_time = (
            time.time() - start_time
        ) * 1000 + 1000  # Account for 1 second interval

        # Determine status
        if cpu_percent > max_percent:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY

        return HealthCheckResult(
            name="cpu",
            status=status,
            response_time_ms=response_time,
            details={
                "cpu_percent": round(cpu_percent, 2),
                "logical_cores": psutil.cpu_count(logical=True),
            },
        )

    except RuntimeError as e:
        response_time = (time.time() - start_time) * 1000

        return HealthCheckResult(
            name="cpu",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=response_time,
            error=f"CPU check error: {str(e)}",
        )
    except (OSError, ValueError) as e:
        response_time = (time.time() - start_time) * 1000

        return HealthCheckResult(
            name="cpu",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=response_time,
            error=f"System error: {str(e)}",
        )

        # ============================================================================
        # HEALTH CHECK COORDINATOR
        # ============================================================================


class HealthCheckCoordinator:
    """Coordinate health checks across system."""

    def __init__(self) -> None:
        """Initialize coordinator."""
        self.checks: dict[str, Callable] = {}
        self.logger = logging.getLogger("app.health")

    def register_check(self, name: str, check_func: Callable) -> None:
        """
        Register health check.

        Args:
            name: Check name
            check_func: Check function
        """
        self.checks[name] = check_func

    async def run_all_checks(self) -> OverallHealthResult:
        """
        Run all health checks.

        Returns:
            Overall health result
        """
        results = []

        # Run checks concurrently
        tasks = [
            asyncio.create_task(self._run_check(name, check_func))
            for name, check_func in self.checks.items()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to health check results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(
                    HealthCheckResult(
                        name="unknown",
                        status=HealthStatus.UNHEALTHY,
                        response_time_ms=0,
                        error=str(result),
                    )
                )
            else:
                processed_results.append(result)

        return OverallHealthResult(processed_results)

    async def _run_check(self, name: str, check_func: Callable) -> HealthCheckResult:
        """
        Run individual check.

        Args:
            name: Check name
            check_func: Check function

        Returns:
            Health check result
        """
        try:
            # Check if function is async or sync
            if asyncio.iscoroutinefunction(check_func):
                return await check_func()
            else:
                # Run sync function in executor
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, check_func)

        except (ValueError, TypeError, RuntimeError) as e:
            self.logger.error(f"Error running health check {name}: {e}", exc_info=True)

            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                error=str(e),
            )

    def get_status_summary(self, result: OverallHealthResult) -> dict[str, Any]:
        """
        Get health status summary for display.

        Args:
            result: Overall health result

        Returns:
            Summary dictionary
        """
        return {
            "status": result.overall_status.value,
            "healthy": result.overall_status == HealthStatus.HEALTHY,
            "checks": {
                check.name: {
                    "status": check.status.value,
                    "response_time_ms": check.response_time_ms,
                }
                for check in result.results
            },
        }

        # ============================================================================
        # GLOBAL HEALTH CHECK COORDINATOR
        # ============================================================================


health_check_coordinator = HealthCheckCoordinator()
