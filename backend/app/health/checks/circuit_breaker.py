"""
Circuit breaker health check implementation.

Provides comprehensive circuit breaker health monitoring including:
- Total breaker count
- Open/Half-Open/Closed breaker counts
- Overall failure rate
- Individual breaker status
- Rejection statistics
"""

import asyncio
import logging
import time
from typing import Any

from app.resilience.circuit_breaker.registry import get_registry
from app.resilience.circuit_breaker.states import CircuitState

logger = logging.getLogger(__name__)


class CircuitBreakerHealthCheck:
    """
    Circuit breaker health check implementation.

    Performs health checks on all registered circuit breakers including:
    - Breaker state monitoring (open/half-open/closed)
    - Failure rate tracking
    - Request rejection statistics
    - Individual breaker status
    """

    def __init__(self, timeout: float = 5.0) -> None:
        """
        Initialize circuit breaker health check.

        Args:
            timeout: Maximum time in seconds to wait for health check
        """
        self.timeout = timeout
        self.name = "circuit_breakers"

    async def check(self) -> dict[str, Any]:
        """
        Perform circuit breaker health check.

        Returns:
            Dictionary with health status:
            - status: "healthy", "degraded", or "unhealthy"
            - response_time_ms: Check execution time
            - total_breakers: Total number of registered breakers
            - open_breakers: Number of open breakers
            - half_open_breakers: Number of half-open breakers
            - closed_breakers: Number of closed breakers
            - overall_failure_rate: Overall failure rate across all breakers
            - breaker_details: Individual breaker statuses
            - error: Error message if unhealthy

        Raises:
            TimeoutError: If check exceeds timeout
        """
        start_time = time.time()

        try:
            # Run check with timeout
            result = await asyncio.wait_for(self._perform_check(), timeout=self.timeout)

            response_time_ms = (time.time() - start_time) * 1000
            result["response_time_ms"] = round(response_time_ms, 2)

            return result

        except TimeoutError:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Circuit breaker health check timed out after {self.timeout}s"
            )
            return {
                "status": "unhealthy",
                "error": f"Health check timed out after {self.timeout}s",
                "response_time_ms": round(response_time_ms, 2),
            }

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Circuit breaker health check failed: {e}", exc_info=True)
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": round(response_time_ms, 2),
            }

    async def _perform_check(self) -> dict[str, Any]:
        """
        Perform the actual circuit breaker health check.

        Returns:
            Dictionary with detailed health information
        """
        try:
            # Get the global circuit breaker registry
            registry = get_registry()

            # Get health check data from registry
            health_data = registry.health_check()

            # Determine overall health status
            status = self._determine_status(health_data)

            # Build detailed breaker information
            breaker_details = self._get_breaker_details(registry)

            # Build result
            result = {
                "status": status,
                "total_breakers": health_data["total_breakers"],
                "open_breakers": health_data["open_breakers"],
                "half_open_breakers": health_data["half_open_breakers"],
                "closed_breakers": health_data["closed_breakers"],
                "overall_failure_rate": round(health_data["overall_failure_rate"], 4),
                "total_requests": health_data["total_requests"],
                "total_failures": health_data["total_failures"],
                "total_rejections": health_data["total_rejections"],
                "open_breaker_names": health_data["open_breaker_names"],
                "half_open_breaker_names": health_data["half_open_breaker_names"],
                "breaker_details": breaker_details,
            }

            # Add warning if applicable
            if status == "degraded":
                result["warning"] = self._get_degraded_warning(health_data)

            return result

        except Exception as e:
            logger.error(f"Circuit breaker health check failed: {e}", exc_info=True)
            return {
                "status": "unhealthy",
                "error": f"Failed to check circuit breakers: {str(e)}",
            }

    def _determine_status(self, health_data: dict[str, Any]) -> str:
        """
        Determine overall health status based on circuit breaker states.

        Rules:
        - HEALTHY: No breakers are open
        - DEGRADED: Some breakers are open or half-open
        - UNHEALTHY: All breakers are open, or critical breakers are open

        Args:
            health_data: Health check data from registry

        Returns:
            Health status: "healthy", "degraded", or "unhealthy"
        """
        total_breakers = health_data["total_breakers"]
        open_breakers = health_data["open_breakers"]
        half_open_breakers = health_data["half_open_breakers"]
        open_breaker_names = health_data["open_breaker_names"]

        # If no breakers registered, that's healthy (no problems)
        if total_breakers == 0:
            return "healthy"

            # Check for critical breakers being open
        critical_breakers = {"database", "redis", "external_api"}
        open_critical = set(open_breaker_names) & critical_breakers

        # If all breakers are open, system is unhealthy
        if open_breakers == total_breakers:
            return "unhealthy"

            # If any critical breaker is open, system is unhealthy
        if open_critical:
            return "unhealthy"

            # If some breakers are open or half-open, system is degraded
        if open_breakers > 0 or half_open_breakers > 0:
            return "degraded"

            # All breakers are closed
        return "healthy"

    def _get_degraded_warning(self, health_data: dict[str, Any]) -> str:
        """
        Generate warning message for degraded status.

        Args:
            health_data: Health check data from registry

        Returns:
            Warning message describing the degraded state
        """
        open_breakers = health_data["open_breakers"]
        half_open_breakers = health_data["half_open_breakers"]
        open_names = health_data["open_breaker_names"]
        half_open_names = health_data["half_open_breaker_names"]

        warnings = []

        if open_breakers > 0:
            warnings.append(
                f"{open_breakers} circuit breaker(s) open: {', '.join(open_names)}"
            )

        if half_open_breakers > 0:
            warnings.append(
                f"{half_open_breakers} circuit breaker(s) half-open: "
                f"{', '.join(half_open_names)}"
            )

        return "; ".join(warnings)

    def _get_breaker_details(self, registry) -> dict[str, Any]:
        """
        Get detailed information for each circuit breaker.

        Args:
            registry: Circuit breaker registry

        Returns:
            Dictionary mapping breaker names to their detailed status
        """
        all_statuses = registry.get_all_statuses()

        # Simplify the breaker details for health check response
        breaker_details = {}
        for name, status in all_statuses.items():
            breaker_details[name] = {
                "state": status["state"],
                "failure_count": status["failure_count"],
                "success_count": status["success_count"],
                "total_requests": status["total_requests"],
                "failed_requests": status["failed_requests"],
                "rejected_requests": status["rejected_requests"],
                "last_failure_time": status.get("last_failure_time"),
                "last_state_change": status.get("last_state_change"),
            }

        return breaker_details

    async def check_critical_breakers(self) -> dict[str, Any]:
        """
        Check only critical circuit breakers.

        This is a faster check that only monitors business-critical breakers.

        Returns:
            Dictionary with critical breaker status
        """
        try:
            registry = get_registry()
            critical_names = {"database", "redis", "external_api"}

            critical_statuses = {}
            for name in critical_names:
                if registry.exists(name):
                    breaker = registry.get(name)
                    critical_statuses[name] = {
                        "state": str(breaker.state),
                        "is_open": breaker.state == CircuitState.OPEN,
                    }

            any_open = any(s["is_open"] for s in critical_statuses.values())

            return {
                "status": "unhealthy" if any_open else "healthy",
                "critical_breakers": critical_statuses,
                "any_critical_open": any_open,
            }

        except Exception as e:
            logger.error(f"Critical breaker check failed: {e}", exc_info=True)
            return {
                "status": "unhealthy",
                "error": str(e),
            }
