"""
Load balancer implementation for distributing traffic across service instances.

Provides:
- Unified load balancing interface
- Service instance selection
- Health check integration
- Failover handling
- Strategy switching
- Metrics and monitoring
"""

import logging
from typing import Any

from app.loadbalancer.health import HealthProbe, ServiceHealthChecker
from app.loadbalancer.registry import ServiceInstance, ServiceRegistry
from app.loadbalancer.strategies import (
    HealthBasedStrategy,
    LoadBalancingStrategy,
    RoundRobinStrategy,
)

logger = logging.getLogger(__name__)


class LoadBalancer:
    """
    Load balancer for distributing traffic across service instances.

    Coordinates service registry, health checking, and load balancing
    strategies to provide reliable traffic distribution.
    """

    def __init__(
        self,
        registry: ServiceRegistry | None = None,
        strategy: LoadBalancingStrategy | None = None,
        health_probe: HealthProbe | None = None,
        enable_health_checks: bool = True,
        health_check_interval: int = 30,
        enable_failover: bool = True,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize load balancer.

        Args:
            registry: Service registry (creates new if not provided)
            strategy: Load balancing strategy (defaults to HealthBasedStrategy)
            health_probe: Health probe for checking instances
            enable_health_checks: Whether to enable periodic health checks
            health_check_interval: Interval between health checks in seconds
            enable_failover: Whether to enable automatic failover
            max_retries: Maximum retry attempts for failover
        """
        self.registry = registry or ServiceRegistry()
        self.strategy = strategy or HealthBasedStrategy(RoundRobinStrategy())
        self.enable_failover = enable_failover
        self.max_retries = max_retries

        # Health checker
        self.health_checker: ServiceHealthChecker | None = None
        if enable_health_checks:
            self.health_checker = ServiceHealthChecker(
                registry=self.registry,
                probe=health_probe,
                check_interval=health_check_interval,
            )

            # Statistics
        self._total_requests = 0
        self._failed_requests = 0
        self._failover_count = 0

    async def start(self) -> None:
        """Start load balancer services."""
        # Start registry cleanup
        await self.registry.start_cleanup_task()

        # Start health checker
        if self.health_checker:
            await self.health_checker.start()

        logger.info("Load balancer started")

    async def stop(self) -> None:
        """Stop load balancer services."""
        # Stop health checker
        if self.health_checker:
            await self.health_checker.stop()

            # Stop registry cleanup
        await self.registry.stop_cleanup_task()

        logger.info("Load balancer stopped")

    async def register_instance(
        self,
        service_name: str,
        host: str,
        port: int,
        weight: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> ServiceInstance:
        """
        Register a service instance.

        Args:
            service_name: Name of the service
            host: Host address
            port: Port number
            weight: Weight for weighted load balancing
            metadata: Additional instance metadata

        Returns:
            Registered ServiceInstance
        """
        instance = await self.registry.register(
            service_name=service_name,
            host=host,
            port=port,
            weight=weight,
            metadata=metadata,
        )

        logger.info(f"Registered instance: {instance.endpoint} ({service_name})")

        return instance

    async def deregister_instance(self, instance_id: str) -> bool:
        """
        Deregister a service instance.

        Args:
            instance_id: Instance ID to deregister

        Returns:
            True if instance was found and removed, False otherwise
        """
        result = await self.registry.deregister(instance_id)

        if result:
            logger.info(f"Deregistered instance: {instance_id}")

        return result

    async def get_instance(
        self,
        service_name: str,
        healthy_only: bool = True,
    ) -> ServiceInstance | None:
        """
        Get a service instance for handling a request.

        Args:
            service_name: Name of the service
            healthy_only: Only consider healthy instances

        Returns:
            Selected ServiceInstance or None if no instances available
        """
        self._total_requests += 1

        try:
            # Get available instances
            instances = await self.registry.get_instances(
                service_name=service_name,
                healthy_only=healthy_only,
            )

            if not instances:
                logger.warning(f"No instances available for service: {service_name}")
                self._failed_requests += 1
                return None

                # Use strategy to select instance
            selected = await self.strategy.select_instance(instances)

            if selected:
                logger.debug(f"Selected instance: {selected.endpoint} ({service_name})")

            return selected

        except Exception as e:
            logger.error(f"Error selecting instance for {service_name}: {e}")
            self._failed_requests += 1
            return None

    async def get_instance_with_failover(
        self,
        service_name: str,
    ) -> ServiceInstance | None:
        """
        Get a service instance with automatic failover.

        If the selected instance is unavailable, tries alternative instances.

        Args:
            service_name: Name of the service

        Returns:
            Selected ServiceInstance or None if no instances available
        """
        if not self.enable_failover:
            return await self.get_instance(service_name)

        attempts = 0
        tried_instances: set[str] = set()

        while attempts < self.max_retries:
            # Get an instance
            instance = await self.get_instance(service_name)

            if not instance:
                break

                # Check if we've already tried this instance
            if instance.id in tried_instances:
                # No more unique instances to try
                break

            tried_instances.add(instance.id)

            # Try to use the instance (basic check)
            # In real usage, caller would attempt actual connection
            if instance.healthy:
                return instance

                # Instance is unhealthy, try another
            logger.debug(f"Instance {instance.endpoint} unhealthy, trying alternative")
            self._failover_count += 1
            attempts += 1

            # No healthy instance found
        self._failed_requests += 1
        logger.warning(
            f"Failed to find healthy instance for {service_name} "
            f"after {attempts} attempts"
        )
        return None

    async def execute_with_failover(
        self,
        service_name: str,
        func: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute a function with automatic failover.

        Automatically retries with different instances if execution fails.

        Args:
            service_name: Name of the service
            func: Async function to execute (should accept instance as first arg)
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Result from function execution

        Raises:
            Exception: If all retry attempts fail
        """
        if not self.enable_failover:
            instance = await self.get_instance(service_name)
            if not instance:
                raise RuntimeError(f"No instances available for {service_name}")
            return await func(instance, *args, **kwargs)

        attempts = 0
        tried_instances: set[str] = set()
        last_error = None

        while attempts < self.max_retries:
            # Get an instance
            instance = await self.get_instance(service_name)

            if not instance:
                break

                # Check if we've already tried this instance
            if instance.id in tried_instances:
                break

            tried_instances.add(instance.id)

            try:
                # Execute function with instance
                result = await func(instance, *args, **kwargs)
                return result

            except Exception as e:
                last_error = e
                logger.warning(f"Execution failed on instance {instance.endpoint}: {e}")

                # Mark instance as unhealthy
                await self.registry.update_health(instance.id, False)

                # Trigger immediate health check
                if self.health_checker:
                    await self.health_checker.check_instance(instance)

                self._failover_count += 1
                attempts += 1

                # All attempts failed
        self._failed_requests += 1
        error_msg = f"All retry attempts failed for {service_name}"
        if last_error:
            raise RuntimeError(error_msg) from last_error
        else:
            raise RuntimeError(error_msg)

    async def list_services(self) -> list[str]:
        """
        List all registered service names.

        Returns:
            List of service names
        """
        return await self.registry.list_services()

    async def get_service_instances(
        self,
        service_name: str,
        healthy_only: bool = False,
    ) -> list[ServiceInstance]:
        """
        Get all instances for a service.

        Args:
            service_name: Name of the service
            healthy_only: Only return healthy instances

        Returns:
            List of service instances
        """
        return await self.registry.get_instances(service_name, healthy_only)

    def set_strategy(self, strategy: LoadBalancingStrategy) -> None:
        """
        Change load balancing strategy.

        Args:
            strategy: New load balancing strategy
        """
        logger.info(
            f"Switching load balancing strategy from {self.strategy.__class__.__name__} "
            f"to {strategy.__class__.__name__}"
        )
        self.strategy = strategy

    def reset_strategy(self) -> None:
        """Reset current strategy state."""
        self.strategy.reset()
        logger.info("Reset load balancing strategy state")

    async def get_health_status(
        self,
        service_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Get health status for service(s).

        Args:
            service_name: Name of specific service (None for all services)

        Returns:
            Dictionary with health status
        """
        if service_name:
            instances = await self.registry.get_instances(
                service_name,
                healthy_only=False,
            )

            healthy = sum(1 for i in instances if i.healthy)

            return {
                "service": service_name,
                "total_instances": len(instances),
                "healthy_instances": healthy,
                "unhealthy_instances": len(instances) - healthy,
                "instances": [i.to_dict() for i in instances],
            }
        else:
            # Get status for all services
            services = await self.registry.list_services()
            status = {}

            for svc in services:
                instances = await self.registry.get_instances(svc, healthy_only=False)
                healthy = sum(1 for i in instances if i.healthy)

                status[svc] = {
                    "total": len(instances),
                    "healthy": healthy,
                    "unhealthy": len(instances) - healthy,
                }

            return status

    def get_stats(self) -> dict[str, Any]:
        """
        Get load balancer statistics.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_requests": self._total_requests,
            "failed_requests": self._failed_requests,
            "failover_count": self._failover_count,
            "success_rate": (
                (
                    (self._total_requests - self._failed_requests)
                    / self._total_requests
                    * 100
                )
                if self._total_requests > 0
                else 0.0
            ),
            "registry_stats": self.registry.get_stats(),
            "strategy_stats": self.strategy.get_stats(),
        }

        if self.health_checker:
            stats["health_checker_stats"] = self.health_checker.get_stats()

        return stats

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._total_requests = 0
        self._failed_requests = 0
        self._failover_count = 0
        logger.info("Reset load balancer statistics")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop()
