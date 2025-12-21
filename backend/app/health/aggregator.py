"""
Health check aggregator for coordinating all service health checks.

Provides:
- Aggregated health status across all services
- Liveness probe (basic health)
- Readiness probe (full health)
- Detailed health reporting
- Health history tracking
- Alert integration
"""

import asyncio
import logging
from collections import deque
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel

from app.health.checks.celery import CeleryHealthCheck
from app.health.checks.database import DatabaseHealthCheck
from app.health.checks.redis import RedisHealthCheck

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheckResult(BaseModel):
    """
    Health check result model.

    Represents the result of a single health check.
    """

    service: str
    status: HealthStatus
    response_time_ms: float
    timestamp: datetime
    details: dict[str, Any] = {}
    error: str | None = None
    warning: str | None = None


class AggregatedHealthResult(BaseModel):
    """
    Aggregated health check result.

    Represents the overall health status across all services.
    """

    status: HealthStatus
    timestamp: datetime
    services: dict[str, HealthCheckResult]
    summary: dict[str, Any]


class HealthAggregator:
    """
    Health check aggregator.

    Coordinates health checks across all services and provides
    aggregated health status reporting.
    """

    def __init__(
        self,
        enable_history: bool = True,
        history_size: int = 100,
        timeout: float = 10.0
    ):
        """
        Initialize health aggregator.

        Args:
            enable_history: Whether to track health check history
            history_size: Maximum number of history entries to keep
            timeout: Default timeout for health checks
        """
        self.enable_history = enable_history
        self.history_size = history_size
        self.timeout = timeout

        # Health check history (circular buffer)
        self._history: deque[AggregatedHealthResult] = deque(maxlen=history_size)

        # Initialize health checkers
        self.database_check = DatabaseHealthCheck(timeout=timeout)
        self.redis_check = RedisHealthCheck(timeout=timeout)
        self.celery_check = CeleryHealthCheck(timeout=timeout)

    async def check_liveness(self) -> dict[str, Any]:
        """
        Perform liveness probe.

        Liveness checks verify that the application is running and responsive.
        This is a lightweight check suitable for Kubernetes liveness probes.

        Returns:
            Dictionary with liveness status
        """
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "residency-scheduler",
        }

    async def check_readiness(self) -> dict[str, Any]:
        """
        Perform readiness probe.

        Readiness checks verify that the application is ready to serve traffic.
        This includes checking critical dependencies like database and Redis.

        Returns:
            Dictionary with readiness status
        """
        try:
            # Check critical services in parallel
            db_task = asyncio.create_task(self.database_check.check())
            redis_task = asyncio.create_task(self.redis_check.check())

            db_result, redis_result = await asyncio.gather(
                db_task,
                redis_task,
                return_exceptions=True
            )

            # Determine overall readiness
            db_healthy = (
                not isinstance(db_result, Exception)
                and db_result.get("status") in ["healthy", "degraded"]
            )
            redis_healthy = (
                not isinstance(redis_result, Exception)
                and redis_result.get("status") in ["healthy", "degraded"]
            )

            if db_healthy and redis_healthy:
                status = "healthy"
            else:
                status = "unhealthy"

            return {
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "database": db_healthy,
                "redis": redis_healthy,
            }

        except Exception as e:
            logger.error(f"Readiness check failed: {e}", exc_info=True)
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }

    async def check_detailed(self) -> AggregatedHealthResult:
        """
        Perform detailed health check across all services.

        Returns:
            AggregatedHealthResult with detailed status for all services
        """
        timestamp = datetime.utcnow()

        # Run all health checks in parallel
        tasks = {
            "database": asyncio.create_task(self._check_with_timeout("database", self.database_check)),
            "redis": asyncio.create_task(self._check_with_timeout("redis", self.redis_check)),
            "celery": asyncio.create_task(self._check_with_timeout("celery", self.celery_check)),
        }

        # Wait for all checks to complete
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        # Build service results
        service_results = {}
        for (service_name, task), result in zip(tasks.items(), results):
            if isinstance(result, Exception):
                service_results[service_name] = HealthCheckResult(
                    service=service_name,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=0.0,
                    timestamp=timestamp,
                    error=str(result),
                )
            else:
                service_results[service_name] = result

        # Determine overall status
        overall_status = self._aggregate_status(service_results)

        # Build summary
        summary = self._build_summary(service_results)

        # Create aggregated result
        aggregated_result = AggregatedHealthResult(
            status=overall_status,
            timestamp=timestamp,
            services=service_results,
            summary=summary,
        )

        # Add to history
        if self.enable_history:
            self._history.append(aggregated_result)

        return aggregated_result

    async def _check_with_timeout(
        self,
        service_name: str,
        health_checker: Any
    ) -> HealthCheckResult:
        """
        Execute a health check with timeout handling.

        Args:
            service_name: Name of the service
            health_checker: Health checker instance

        Returns:
            HealthCheckResult for the service
        """
        try:
            result = await health_checker.check()

            # Convert result dict to HealthCheckResult
            status_str = result.get("status", "unhealthy")
            status = HealthStatus(status_str)

            return HealthCheckResult(
                service=service_name,
                status=status,
                response_time_ms=result.get("response_time_ms", 0.0),
                timestamp=datetime.utcnow(),
                details=result,
                error=result.get("error"),
                warning=result.get("warning"),
            )

        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}", exc_info=True)
            return HealthCheckResult(
                service=service_name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0.0,
                timestamp=datetime.utcnow(),
                error=str(e),
            )

    def _aggregate_status(
        self,
        service_results: dict[str, HealthCheckResult]
    ) -> HealthStatus:
        """
        Aggregate status from individual service results.

        Rules:
        - If any critical service is unhealthy -> overall unhealthy
        - If any service is degraded -> overall degraded
        - If all services are healthy -> overall healthy

        Args:
            service_results: Dictionary of service health results

        Returns:
            Aggregated health status
        """
        critical_services = ["database", "redis"]

        # Check critical services first
        for service_name in critical_services:
            if service_name in service_results:
                result = service_results[service_name]
                if result.status == HealthStatus.UNHEALTHY:
                    return HealthStatus.UNHEALTHY

        # Check for any degraded services
        for result in service_results.values():
            if result.status == HealthStatus.DEGRADED:
                return HealthStatus.DEGRADED

        # Check for any unhealthy non-critical services
        for result in service_results.values():
            if result.status == HealthStatus.UNHEALTHY:
                return HealthStatus.DEGRADED

        # All services healthy
        return HealthStatus.HEALTHY

    def _build_summary(
        self,
        service_results: dict[str, HealthCheckResult]
    ) -> dict[str, Any]:
        """
        Build summary statistics from service results.

        Args:
            service_results: Dictionary of service health results

        Returns:
            Summary statistics
        """
        total_services = len(service_results)
        healthy_count = sum(
            1 for r in service_results.values()
            if r.status == HealthStatus.HEALTHY
        )
        degraded_count = sum(
            1 for r in service_results.values()
            if r.status == HealthStatus.DEGRADED
        )
        unhealthy_count = sum(
            1 for r in service_results.values()
            if r.status == HealthStatus.UNHEALTHY
        )

        avg_response_time = sum(
            r.response_time_ms for r in service_results.values()
        ) / total_services if total_services > 0 else 0.0

        return {
            "total_services": total_services,
            "healthy_count": healthy_count,
            "degraded_count": degraded_count,
            "unhealthy_count": unhealthy_count,
            "avg_response_time_ms": round(avg_response_time, 2),
        }

    def get_history(self, limit: int | None = None) -> list[AggregatedHealthResult]:
        """
        Get health check history.

        Args:
            limit: Maximum number of history entries to return

        Returns:
            List of historical health check results
        """
        if not self.enable_history:
            return []

        history = list(self._history)

        if limit:
            history = history[-limit:]

        return history

    def clear_history(self) -> None:
        """Clear health check history."""
        self._history.clear()

    async def check_service(self, service_name: str) -> HealthCheckResult:
        """
        Check health of a specific service.

        Args:
            service_name: Name of service to check (database, redis, celery)

        Returns:
            HealthCheckResult for the requested service

        Raises:
            ValueError: If service name is not recognized
        """
        if service_name == "database":
            return await self._check_with_timeout(service_name, self.database_check)
        elif service_name == "redis":
            return await self._check_with_timeout(service_name, self.redis_check)
        elif service_name == "celery":
            return await self._check_with_timeout(service_name, self.celery_check)
        else:
            raise ValueError(f"Unknown service: {service_name}")

    def get_metrics(self) -> dict[str, Any]:
        """
        Get health check metrics.

        Returns:
            Dictionary with metrics about health checks
        """
        if not self.enable_history or not self._history:
            return {
                "history_enabled": self.enable_history,
                "history_size": 0,
                "metrics": "No history available",
            }

        recent_checks = list(self._history)[-10:]

        # Calculate uptime percentage
        healthy_checks = sum(
            1 for check in recent_checks
            if check.status == HealthStatus.HEALTHY
        )
        uptime_percentage = (healthy_checks / len(recent_checks)) * 100

        # Calculate average response times
        avg_response_times = {}
        for check in recent_checks:
            for service_name, service_result in check.services.items():
                if service_name not in avg_response_times:
                    avg_response_times[service_name] = []
                avg_response_times[service_name].append(service_result.response_time_ms)

        avg_times = {
            service: round(sum(times) / len(times), 2)
            for service, times in avg_response_times.items()
        }

        return {
            "history_enabled": self.enable_history,
            "history_size": len(self._history),
            "uptime_percentage": round(uptime_percentage, 2),
            "recent_checks": len(recent_checks),
            "avg_response_times_ms": avg_times,
        }
