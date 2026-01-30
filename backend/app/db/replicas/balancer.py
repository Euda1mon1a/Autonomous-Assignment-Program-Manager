"""Load balancer for distributing queries across replicas.

Implements multiple load balancing strategies:
- Round-robin: Distributes queries evenly
- Health-aware: Skips unhealthy replicas
- Least-connections: Routes to least busy replica (future)
"""

import logging
import threading

from sqlalchemy.engine import Engine

from app.db.replicas.health import HealthChecker

logger = logging.getLogger(__name__)


class LoadBalancer:
    """Distributes read queries across multiple database replicas.

    Features:
    - Round-robin selection for even distribution
    - Health-based filtering (skips unhealthy replicas)
    - Thread-safe replica selection
    - Automatic fallback to primary if no replicas available
    """

    def __init__(
        self,
        replicas: dict[str, Engine],
        health_checker: HealthChecker | None = None,
        enable_health_checks: bool = True,
    ) -> None:
        """Initialize load balancer.

        Args:
            replicas: Dictionary of replica_name -> engine
            health_checker: Health checker instance (creates default if None)
            enable_health_checks: Whether to check replica health before routing
        """
        self.replicas = replicas
        self.health_checker = health_checker or HealthChecker()
        self.enable_health_checks = enable_health_checks

        # Round-robin state
        self._current_index = 0
        self._lock = threading.Lock()

        # Replica list for round-robin (maintains insertion order)
        self._replica_names = list(replicas.keys())

        logger.info(
            f"LoadBalancer initialized with {len(replicas)} replicas: "
            f"{', '.join(self._replica_names)}"
        )

    def select_replica(
        self, session_id: str | None = None
    ) -> tuple[str, Engine] | None:
        """Select a healthy replica using round-robin.

        Args:
            session_id: Optional session ID for sticky sessions (future use)

        Returns:
            Tuple of (replica_name, engine) or None if no healthy replicas
        """
        if not self.replicas:
            logger.debug("No replicas configured")
            return None

            # Try each replica in round-robin order
        num_replicas = len(self._replica_names)
        attempts = 0

        while attempts < num_replicas:
            replica_name, engine = self._get_next_replica()

            # Check health if enabled
            if self.enable_health_checks:
                if self.health_checker.is_replica_healthy(
                    engine, replica_name, use_cache=True, cache_max_age=10.0
                ):
                    logger.debug(f"Selected replica: {replica_name}")
                    return replica_name, engine
                else:
                    logger.debug(f"Skipping unhealthy replica: {replica_name}")
                    attempts += 1
                    continue
            else:
                # Health checks disabled, use replica anyway
                logger.debug(f"Selected replica (no health check): {replica_name}")
                return replica_name, engine

                # No healthy replicas available
        logger.warning("No healthy replicas available for read query")
        return None

    def _get_next_replica(self) -> tuple[str, Engine]:
        """Get next replica in round-robin order (thread-safe).

        Returns:
            Tuple of (replica_name, engine)
        """
        with self._lock:
            replica_name = self._replica_names[self._current_index]
            engine = self.replicas[replica_name]

            # Advance to next replica
            self._current_index = (self._current_index + 1) % len(self._replica_names)

            return replica_name, engine

    def add_replica(self, name: str, engine: Engine) -> None:
        """Add a new replica to the pool.

        Args:
            name: Identifier for the replica
            engine: SQLAlchemy engine for the replica
        """
        with self._lock:
            if name in self.replicas:
                logger.warning(f"Replica {name} already exists, replacing")

            self.replicas[name] = engine

            if name not in self._replica_names:
                self._replica_names.append(name)

            logger.info(f"Added replica: {name} (total: {len(self.replicas)})")

    def remove_replica(self, name: str) -> None:
        """Remove a replica from the pool.

        Args:
            name: Identifier for the replica
        """
        with self._lock:
            if name not in self.replicas:
                logger.warning(f"Replica {name} not found")
                return

            del self.replicas[name]
            self._replica_names.remove(name)

            # Reset index if it's now out of bounds
            if self._replica_names and self._current_index >= len(self._replica_names):
                self._current_index = 0

            logger.info(f"Removed replica: {name} (remaining: {len(self.replicas)})")

    def get_replica_count(self) -> int:
        """Get number of configured replicas.

        Returns:
            Number of replicas in the pool
        """
        return len(self.replicas)

    def get_healthy_replica_count(self) -> int:
        """Get number of currently healthy replicas.

        Returns:
            Number of healthy replicas
        """
        if not self.enable_health_checks:
            return len(self.replicas)

        healthy_count = 0

        for name, engine in self.replicas.items():
            if self.health_checker.is_replica_healthy(
                engine, name, use_cache=True, cache_max_age=30.0
            ):
                healthy_count += 1

        return healthy_count

    def get_replica_stats(self) -> dict[str, dict]:
        """Get statistics for all replicas.

        Returns:
            Dictionary of replica_name -> stats
        """
        stats = {}

        for name, engine in self.replicas.items():
            health = self.health_checker.get_cached_health(name, max_age_seconds=60.0)

            stats[name] = {
                "is_healthy": health.is_healthy if health else None,
                "lag_seconds": health.lag_seconds if health else None,
                "last_check": (
                    health.last_check.isoformat()
                    if health and health.last_check
                    else None
                ),
                "consecutive_failures": health.consecutive_failures if health else 0,
                "pool_size": engine.pool.size(),
                "checked_in_connections": engine.pool.checkedin(),
            }

        return stats


class StickySessionBalancer(LoadBalancer):
    """Load balancer with sticky session support.

    Maintains session affinity - routes all queries from the same session
    to the same replica for consistency.
    """

    def __init__(
        self,
        replicas: dict[str, Engine],
        health_checker: HealthChecker | None = None,
        enable_health_checks: bool = True,
        session_timeout_seconds: int = 300,
    ) -> None:
        """Initialize sticky session balancer.

        Args:
            replicas: Dictionary of replica_name -> engine
            health_checker: Health checker instance
            enable_health_checks: Whether to check replica health
            session_timeout_seconds: Time to maintain session affinity
        """
        super().__init__(replicas, health_checker, enable_health_checks)
        self._session_assignments: dict[str, str] = {}
        self._session_lock = threading.Lock()
        self.session_timeout_seconds = session_timeout_seconds

    def select_replica(
        self, session_id: str | None = None
    ) -> tuple[str, Engine] | None:
        """Select replica with session affinity.

        If session_id is provided, returns the same replica for that session
        (unless it becomes unhealthy).

        Args:
            session_id: Session identifier for sticky routing

        Returns:
            Tuple of (replica_name, engine) or None if no healthy replicas
        """
        if not session_id:
            # No session affinity requested, use normal round-robin
            return super().select_replica(session_id)

            # Check if session already has a replica assignment
        with self._session_lock:
            assigned_replica = self._session_assignments.get(session_id)

        if assigned_replica:
            # Verify assigned replica is still healthy
            if assigned_replica in self.replicas:
                engine = self.replicas[assigned_replica]

                if (
                    not self.enable_health_checks
                    or self.health_checker.is_replica_healthy(
                        engine, assigned_replica, use_cache=True, cache_max_age=10.0
                    )
                ):
                    logger.debug(
                        f"Using sticky session assignment: "
                        f"session={session_id} -> replica={assigned_replica}"
                    )
                    return assigned_replica, engine
                else:
                    logger.warning(
                        f"Assigned replica {assigned_replica} is unhealthy, "
                        f"reassigning session {session_id}"
                    )

                    # No assignment or assigned replica is unhealthy
                    # Select a new replica
        selection = super().select_replica(session_id)

        if selection:
            replica_name, engine = selection

            # Store assignment for future requests
            with self._session_lock:
                self._session_assignments[session_id] = replica_name

            logger.debug(
                f"New sticky session assignment: "
                f"session={session_id} -> replica={replica_name}"
            )

        return selection

    def clear_session(self, session_id: str) -> None:
        """Clear session affinity for a session.

        Args:
            session_id: Session identifier
        """
        with self._session_lock:
            if session_id in self._session_assignments:
                del self._session_assignments[session_id]
                logger.debug(f"Cleared sticky session: {session_id}")

    def get_session_count(self) -> int:
        """Get number of active session assignments.

        Returns:
            Number of sessions with sticky assignments
        """
        with self._session_lock:
            return len(self._session_assignments)
