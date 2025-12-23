"""
Health checking utilities for load-balanced services.

Provides:
- Service instance health checking
- HTTP health probe implementation
- TCP health probe implementation
- Custom health check support
- Health check scheduling and monitoring
- Automatic unhealthy instance detection
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

import aiohttp

from app.loadbalancer.registry import ServiceInstance, ServiceRegistry

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status enumeration."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheckResult:
    """
    Health check result.

    Attributes:
        status: Health status
        response_time_ms: Response time in milliseconds
        error: Error message if unhealthy
        details: Additional health check details
        timestamp: Check timestamp
    """

    def __init__(
        self,
        status: HealthStatus,
        response_time_ms: float = 0.0,
        error: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize health check result.

        Args:
            status: Health status
            response_time_ms: Response time in milliseconds
            error: Error message if unhealthy
            details: Additional details
        """
        self.status = status
        self.response_time_ms = response_time_ms
        self.error = error
        self.details = details or {}
        self.timestamp = time.time()

    @property
    def is_healthy(self) -> bool:
        """Check if status is healthy."""
        return self.status == HealthStatus.HEALTHY

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "response_time_ms": round(self.response_time_ms, 2),
            "error": self.error,
            "details": self.details,
            "timestamp": self.timestamp,
        }


class HealthProbe(ABC):
    """Abstract base class for health probes."""

    @abstractmethod
    async def check(self, instance: ServiceInstance) -> HealthCheckResult:
        """
        Perform health check on instance.

        Args:
            instance: Service instance to check

        Returns:
            HealthCheckResult
        """
        pass


class HTTPHealthProbe(HealthProbe):
    """
    HTTP-based health probe.

    Performs HTTP GET request to health check endpoint.
    """

    def __init__(
        self,
        path: str = "/health",
        timeout: float = 5.0,
        expected_status: int = 200,
        verify_ssl: bool = True,
    ):
        """
        Initialize HTTP health probe.

        Args:
            path: Health check endpoint path
            timeout: Request timeout in seconds
            expected_status: Expected HTTP status code
            verify_ssl: Whether to verify SSL certificates
        """
        self.path = path
        self.timeout = timeout
        self.expected_status = expected_status
        self.verify_ssl = verify_ssl

    async def check(self, instance: ServiceInstance) -> HealthCheckResult:
        """
        Perform HTTP health check.

        Args:
            instance: Service instance to check

        Returns:
            HealthCheckResult
        """
        url = f"{instance.endpoint}{self.path}"
        start_time = time.time()

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    ssl=self.verify_ssl,
                ) as response,
            ):
                response_time_ms = (time.time() - start_time) * 1000

                if response.status == self.expected_status:
                    return HealthCheckResult(
                        status=HealthStatus.HEALTHY,
                        response_time_ms=response_time_ms,
                        details={
                            "status_code": response.status,
                            "url": url,
                        },
                    )
                else:
                    return HealthCheckResult(
                        status=HealthStatus.UNHEALTHY,
                        response_time_ms=response_time_ms,
                        error=f"Unexpected status code: {response.status}",
                        details={
                            "status_code": response.status,
                            "expected": self.expected_status,
                            "url": url,
                        },
                    )

        except TimeoutError:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time_ms,
                error=f"Health check timed out after {self.timeout}s",
                details={"url": url},
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.debug(f"Health check failed for {url}: {e}")
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time_ms,
                error=str(e),
                details={"url": url},
            )


class TCPHealthProbe(HealthProbe):
    """
    TCP-based health probe.

    Checks if TCP port is open and accepting connections.
    """

    def __init__(self, timeout: float = 5.0):
        """
        Initialize TCP health probe.

        Args:
            timeout: Connection timeout in seconds
        """
        self.timeout = timeout

    async def check(self, instance: ServiceInstance) -> HealthCheckResult:
        """
        Perform TCP health check.

        Args:
            instance: Service instance to check

        Returns:
            HealthCheckResult
        """
        start_time = time.time()

        try:
            # Attempt to open TCP connection
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(instance.host, instance.port),
                timeout=self.timeout,
            )

            response_time_ms = (time.time() - start_time) * 1000

            # Close connection
            writer.close()
            await writer.wait_closed()

            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time_ms,
                details={
                    "host": instance.host,
                    "port": instance.port,
                },
            )

        except TimeoutError:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time_ms,
                error=f"Connection timed out after {self.timeout}s",
                details={
                    "host": instance.host,
                    "port": instance.port,
                },
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time_ms,
                error=str(e),
                details={
                    "host": instance.host,
                    "port": instance.port,
                },
            )


class ServiceHealthChecker:
    """
    Service health checker.

    Performs periodic health checks on registered service instances
    and updates registry with health status.
    """

    def __init__(
        self,
        registry: ServiceRegistry,
        probe: HealthProbe | None = None,
        check_interval: int = 30,
        initial_delay: int = 5,
    ):
        """
        Initialize service health checker.

        Args:
            registry: Service registry
            probe: Health probe to use (defaults to HTTPHealthProbe)
            check_interval: Interval between health checks in seconds
            initial_delay: Initial delay before first check in seconds
        """
        self.registry = registry
        self.probe = probe or HTTPHealthProbe()
        self.check_interval = check_interval
        self.initial_delay = initial_delay

        # Background task
        self._check_task: asyncio.Task | None = None
        self._running = False

        # Statistics
        self._total_checks = 0
        self._failed_checks = 0

    async def start(self) -> None:
        """Start periodic health checking."""
        if self._running:
            logger.warning("Health checker already running")
            return

        self._running = True
        self._check_task = asyncio.create_task(self._health_check_loop())
        logger.info(
            f"Started health checker (interval: {self.check_interval}s, "
            f"initial delay: {self.initial_delay}s)"
        )

    async def stop(self) -> None:
        """Stop periodic health checking."""
        if not self._running:
            return

        self._running = False

        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass

            self._check_task = None

        logger.info("Stopped health checker")

    async def check_instance(self, instance: ServiceInstance) -> HealthCheckResult:
        """
        Check health of a single instance.

        Args:
            instance: Service instance to check

        Returns:
            HealthCheckResult
        """
        self._total_checks += 1

        try:
            result = await self.probe.check(instance)

            # Update registry with health status
            await self.registry.update_health(instance.id, result.is_healthy)

            if not result.is_healthy:
                self._failed_checks += 1
                logger.debug(
                    f"Health check failed for {instance.service_name} "
                    f"({instance.endpoint}): {result.error}"
                )

            return result

        except Exception as e:
            self._failed_checks += 1
            logger.error(
                f"Error checking health for {instance.service_name} "
                f"({instance.endpoint}): {e}",
                exc_info=True,
            )

            # Mark as unhealthy on error
            await self.registry.update_health(instance.id, False)

            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                error=str(e),
            )

    async def check_all_services(self) -> dict[str, list[HealthCheckResult]]:
        """
        Check health of all registered service instances.

        Returns:
            Dictionary mapping service names to health check results
        """
        services = await self.registry.list_services()
        results: dict[str, list[HealthCheckResult]] = {}

        for service_name in services:
            instances = await self.registry.get_instances(
                service_name,
                healthy_only=False,
            )

            service_results = await asyncio.gather(
                *[self.check_instance(instance) for instance in instances],
                return_exceptions=True,
            )

            # Filter out exceptions
            results[service_name] = [
                r for r in service_results if isinstance(r, HealthCheckResult)
            ]

        return results

    async def _health_check_loop(self) -> None:
        """Background task for periodic health checking."""
        # Initial delay before first check
        await asyncio.sleep(self.initial_delay)

        while self._running:
            try:
                start_time = time.time()

                # Check all services
                results = await self.check_all_services()

                # Log summary
                total_instances = sum(len(r) for r in results.values())
                healthy_instances = sum(
                    sum(1 for check in r if check.is_healthy) for r in results.values()
                )

                check_duration = time.time() - start_time

                logger.debug(
                    f"Health check completed: {healthy_instances}/{total_instances} "
                    f"healthy (duration: {check_duration:.2f}s)"
                )

                # Wait for next check interval
                await asyncio.sleep(self.check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)

    def get_stats(self) -> dict[str, Any]:
        """
        Get health checker statistics.

        Returns:
            Dictionary with statistics
        """
        success_rate = (
            ((self._total_checks - self._failed_checks) / self._total_checks * 100)
            if self._total_checks > 0
            else 0.0
        )

        return {
            "running": self._running,
            "total_checks": self._total_checks,
            "failed_checks": self._failed_checks,
            "success_rate": round(success_rate, 2),
            "check_interval": self.check_interval,
        }
