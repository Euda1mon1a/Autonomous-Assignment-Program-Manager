"""
Service registry for service discovery and instance management.

Provides:
- Service instance registration and deregistration
- Service discovery by name
- Instance metadata management
- Health status tracking
- Automatic cleanup of unhealthy instances
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class ServiceInstance:
    """
    Represents a single service instance.

    Attributes:
        id: Unique instance identifier
        service_name: Name of the service
        host: Host address (IP or hostname)
        port: Port number
        metadata: Additional instance metadata
        weight: Weight for weighted load balancing (default: 1)
        healthy: Current health status
        registered_at: Registration timestamp
        last_health_check: Last health check timestamp
        consecutive_failures: Number of consecutive health check failures
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    service_name: str = ""
    host: str = ""
    port: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    weight: int = 1
    healthy: bool = True
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_health_check: datetime | None = None
    consecutive_failures: int = 0

    @property
    def endpoint(self) -> str:
        """Get full endpoint URL."""
        return f"http://{self.host}:{self.port}"

    @property
    def address(self) -> tuple[str, int]:
        """Get address tuple (host, port)."""
        return (self.host, self.port)

    def mark_healthy(self) -> None:
        """Mark instance as healthy."""
        self.healthy = True
        self.consecutive_failures = 0
        self.last_health_check = datetime.utcnow()

    def mark_unhealthy(self) -> None:
        """Mark instance as unhealthy."""
        self.healthy = False
        self.consecutive_failures += 1
        self.last_health_check = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert instance to dictionary."""
        return {
            "id": self.id,
            "service_name": self.service_name,
            "host": self.host,
            "port": self.port,
            "endpoint": self.endpoint,
            "metadata": self.metadata,
            "weight": self.weight,
            "healthy": self.healthy,
            "registered_at": self.registered_at.isoformat(),
            "last_health_check": (
                self.last_health_check.isoformat() if self.last_health_check else None
            ),
            "consecutive_failures": self.consecutive_failures,
        }


class ServiceRegistry:
    """
    Service registry for managing service instances.

    Provides service discovery, registration, and health tracking
    for distributed service instances.
    """

    def __init__(
        self,
        cleanup_interval: int = 60,
        failure_threshold: int = 3,
        stale_threshold_seconds: int = 300,
    ) -> None:
        """
        Initialize service registry.

        Args:
            cleanup_interval: Interval in seconds for cleanup task
            failure_threshold: Number of failures before removing instance
            stale_threshold_seconds: Seconds before instance is considered stale
        """
        self.cleanup_interval = cleanup_interval
        self.failure_threshold = failure_threshold
        self.stale_threshold = timedelta(seconds=stale_threshold_seconds)

        # Service instances organized by service name
        self._instances: dict[str, dict[str, ServiceInstance]] = {}

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

        # Cleanup task
        self._cleanup_task: asyncio.Task | None = None

    async def register(
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
        async with self._lock:
            instance = ServiceInstance(
                service_name=service_name,
                host=host,
                port=port,
                weight=weight,
                metadata=metadata or {},
            )

            if service_name not in self._instances:
                self._instances[service_name] = {}

            self._instances[service_name][instance.id] = instance

            logger.info(
                f"Registered service instance: {service_name} at {host}:{port} "
                f"(id: {instance.id})"
            )

            return instance

    async def deregister(self, instance_id: str) -> bool:
        """
        Deregister a service instance.

        Args:
            instance_id: Instance ID to deregister

        Returns:
            True if instance was found and removed, False otherwise
        """
        async with self._lock:
            for service_name, instances in self._instances.items():
                if instance_id in instances:
                    instance = instances.pop(instance_id)
                    logger.info(
                        f"Deregistered service instance: {service_name} "
                        f"(id: {instance_id})"
                    )

                    # Clean up empty service entries
                    if not instances:
                        del self._instances[service_name]

                    return True

            return False

    async def deregister_service(self, service_name: str) -> int:
        """
        Deregister all instances of a service.

        Args:
            service_name: Name of service to deregister

        Returns:
            Number of instances deregistered
        """
        async with self._lock:
            if service_name in self._instances:
                count = len(self._instances[service_name])
                del self._instances[service_name]
                logger.info(
                    f"Deregistered all instances of service: {service_name} "
                    f"({count} instances)"
                )
                return count

            return 0

    async def get_instances(
        self,
        service_name: str,
        healthy_only: bool = True,
    ) -> list[ServiceInstance]:
        """
        Get all instances of a service.

        Args:
            service_name: Name of the service
            healthy_only: Only return healthy instances

        Returns:
            List of service instances
        """
        async with self._lock:
            if service_name not in self._instances:
                return []

            instances = list(self._instances[service_name].values())

            if healthy_only:
                instances = [i for i in instances if i.healthy]

            return instances

    async def get_instance(self, instance_id: str) -> ServiceInstance | None:
        """
        Get a specific service instance by ID.

        Args:
            instance_id: Instance ID

        Returns:
            ServiceInstance if found, None otherwise
        """
        async with self._lock:
            for instances in self._instances.values():
                if instance_id in instances:
                    return instances[instance_id]

            return None

    async def update_health(
        self,
        instance_id: str,
        healthy: bool,
    ) -> bool:
        """
        Update health status of an instance.

        Args:
            instance_id: Instance ID
            healthy: New health status

        Returns:
            True if instance was found and updated, False otherwise
        """
        async with self._lock:
            for instances in self._instances.values():
                if instance_id in instances:
                    instance = instances[instance_id]

                    if healthy:
                        instance.mark_healthy()
                    else:
                        instance.mark_unhealthy()

                        # Remove instance if it exceeds failure threshold
                        if instance.consecutive_failures >= self.failure_threshold:
                            logger.warning(
                                f"Removing unhealthy instance {instance_id} "
                                f"after {instance.consecutive_failures} failures"
                            )
                            instances.pop(instance_id)

                    return True

            return False

    async def list_services(self) -> list[str]:
        """
        List all registered service names.

        Returns:
            List of service names
        """
        async with self._lock:
            return list(self._instances.keys())

    async def get_service_count(self, service_name: str) -> dict[str, int]:
        """
        Get count of instances for a service.

        Args:
            service_name: Name of the service

        Returns:
            Dictionary with total and healthy instance counts
        """
        async with self._lock:
            if service_name not in self._instances:
                return {"total": 0, "healthy": 0}

            instances = list(self._instances[service_name].values())
            healthy_count = sum(1 for i in instances if i.healthy)

            return {
                "total": len(instances),
                "healthy": healthy_count,
            }

    async def clear(self) -> None:
        """Clear all registered instances."""
        async with self._lock:
            count = sum(len(instances) for instances in self._instances.values())
            self._instances.clear()
            logger.info(f"Cleared registry: {count} instances removed")

    async def cleanup_stale_instances(self) -> int:
        """
        Clean up stale instances.

        Removes instances that haven't been health checked recently
        and are marked unhealthy.

        Returns:
            Number of instances removed
        """
        async with self._lock:
            now = datetime.utcnow()
            removed_count = 0

            for service_name, instances in list(self._instances.items()):
                to_remove = []

                for instance_id, instance in instances.items():
                    # Check if instance is stale
                    if (
                        not instance.healthy
                        and instance.last_health_check
                        and (now - instance.last_health_check) > self.stale_threshold
                    ):
                        to_remove.append(instance_id)

                        # Remove stale instances
                for instance_id in to_remove:
                    instances.pop(instance_id)
                    removed_count += 1
                    logger.info(f"Removed stale instance: {instance_id}")

                    # Clean up empty service entries
                if not instances:
                    del self._instances[service_name]

            return removed_count

    async def start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        if self._cleanup_task is not None:
            logger.warning("Cleanup task already running")
            return

        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Started registry cleanup task")

    async def stop_cleanup_task(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task is None:
            return

        self._cleanup_task.cancel()
        try:
            await self._cleanup_task
        except asyncio.CancelledError:
            pass

        self._cleanup_task = None
        logger.info("Stopped registry cleanup task")

    async def _cleanup_loop(self) -> None:
        """Background task for cleaning up stale instances."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                removed = await self.cleanup_stale_instances()

                if removed > 0:
                    logger.info(f"Cleaned up {removed} stale instances")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}", exc_info=True)

    def get_stats(self) -> dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with registry statistics
        """
        total_instances = sum(len(instances) for instances in self._instances.values())
        healthy_instances = sum(
            sum(1 for i in instances.values() if i.healthy)
            for instances in self._instances.values()
        )

        service_stats = {}
        for service_name, instances in self._instances.items():
            healthy = sum(1 for i in instances.values() if i.healthy)
            service_stats[service_name] = {
                "total": len(instances),
                "healthy": healthy,
                "unhealthy": len(instances) - healthy,
            }

        return {
            "total_services": len(self._instances),
            "total_instances": total_instances,
            "healthy_instances": healthy_instances,
            "unhealthy_instances": total_instances - healthy_instances,
            "services": service_stats,
        }
