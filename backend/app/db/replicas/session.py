"""Replica-aware database session management.

Provides session factories and context managers that automatically route
queries to primary or replica databases based on operation type.
"""
import logging
import uuid
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.replicas.balancer import LoadBalancer, StickySessionBalancer
from app.db.replicas.health import HealthChecker
from app.db.replicas.router import QueryRouter, QueryType, RoutingPolicy

logger = logging.getLogger(__name__)


class ReplicaAwareSessionFactory:
    """Factory for creating replica-aware database sessions.

    Manages session creation with automatic query routing between
    primary and replica databases.
    """

    def __init__(
        self,
        primary_engine: Engine,
        replica_engines: Optional[dict[str, Engine]] = None,
        routing_policy: Optional[RoutingPolicy] = None,
        enable_sticky_sessions: bool = False,
        enable_health_checks: bool = True
    ):
        """Initialize session factory.

        Args:
            primary_engine: SQLAlchemy engine for primary database
            replica_engines: Dict of replica_name -> engine (optional)
            routing_policy: Custom routing policy (optional)
            enable_sticky_sessions: Use sticky session balancing
            enable_health_checks: Enable replica health monitoring
        """
        self.primary_engine = primary_engine
        self.replica_engines = replica_engines or {}
        self.routing_policy = routing_policy or RoutingPolicy()
        self.enable_sticky_sessions = enable_sticky_sessions

        # Initialize health checker and load balancer
        self.health_checker = HealthChecker() if enable_health_checks else None

        if self.replica_engines:
            if enable_sticky_sessions:
                self.balancer = StickySessionBalancer(
                    self.replica_engines,
                    health_checker=self.health_checker,
                    enable_health_checks=enable_health_checks
                )
            else:
                self.balancer = LoadBalancer(
                    self.replica_engines,
                    health_checker=self.health_checker,
                    enable_health_checks=enable_health_checks
                )
        else:
            self.balancer = None

        # Initialize router
        self.router = QueryRouter(
            primary_engine=primary_engine,
            balancer=self.balancer,
            fallback_to_primary=True
        )

        # Session makers for primary and replicas
        self.primary_session_maker = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=primary_engine
        )

        logger.info(
            f"ReplicaAwareSessionFactory initialized: "
            f"replicas={len(self.replica_engines)}, "
            f"sticky={enable_sticky_sessions}, "
            f"health_checks={enable_health_checks}"
        )

    def create_session(
        self,
        session_id: Optional[str] = None,
        force_primary: bool = False
    ) -> 'ReplicaAwareSession':
        """Create a new replica-aware session.

        Args:
            session_id: Session ID for sticky routing (auto-generated if None)
            force_primary: Force all queries to primary database

        Returns:
            ReplicaAwareSession instance
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        # Create base session bound to primary
        base_session = self.primary_session_maker()

        # Wrap in replica-aware session
        return ReplicaAwareSession(
            session=base_session,
            router=self.router,
            routing_policy=self.routing_policy,
            session_id=session_id,
            force_primary=force_primary
        )

    @contextmanager
    def session_scope(
        self,
        session_id: Optional[str] = None,
        force_primary: bool = False
    ) -> Generator['ReplicaAwareSession', None, None]:
        """Provide a transactional scope with replica routing.

        Usage:
            with session_factory.session_scope() as session:
                # Reads automatically route to replicas
                users = session.query(User).all()

                # Writes automatically route to primary
                session.add(new_user)
                session.commit()

        Args:
            session_id: Session ID for sticky routing
            force_primary: Force all queries to primary

        Yields:
            ReplicaAwareSession instance
        """
        session = self.create_session(session_id, force_primary)

        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_stats(self) -> dict:
        """Get statistics about session factory.

        Returns:
            Dictionary with factory statistics
        """
        return {
            "replica_count": len(self.replica_engines),
            "sticky_sessions": self.enable_sticky_sessions,
            "routing_stats": self.router.get_routing_stats()
        }


class ReplicaAwareSession:
    """Database session with automatic primary/replica routing.

    Wraps a SQLAlchemy session and routes queries based on operation type:
    - Read queries -> Replicas (when available)
    - Write queries -> Primary (always)
    - Transactions -> Primary (for consistency)
    """

    def __init__(
        self,
        session: Session,
        router: QueryRouter,
        routing_policy: RoutingPolicy,
        session_id: str,
        force_primary: bool = False
    ):
        """Initialize replica-aware session.

        Args:
            session: Base SQLAlchemy session (bound to primary)
            router: Query router instance
            routing_policy: Routing policy
            session_id: Session identifier
            force_primary: Force all queries to primary
        """
        self._session = session
        self._router = router
        self._routing_policy = routing_policy
        self._session_id = session_id
        self._force_primary = force_primary

        # Track session state for routing decisions
        self._in_transaction = False
        self._recent_write = False

        # Set up event listeners for transaction tracking
        self._setup_event_listeners()

    def _setup_event_listeners(self) -> None:
        """Set up SQLAlchemy event listeners for tracking state."""
        # Track transaction begin/end
        @event.listens_for(self._session, "after_transaction_create")
        def track_transaction_start(session, transaction):
            if transaction.parent is None:  # Only track top-level transactions
                self._in_transaction = True
                logger.debug(f"Transaction started: session={self._session_id}")

        @event.listens_for(self._session, "after_transaction_end")
        def track_transaction_end(session, transaction):
            if transaction.parent is None:
                self._in_transaction = False
                logger.debug(f"Transaction ended: session={self._session_id}")

        # Track writes
        @event.listens_for(self._session, "after_flush")
        def track_writes(session, flush_context):
            if session.new or session.dirty or session.deleted:
                self._recent_write = True
                logger.debug(f"Write detected: session={self._session_id}")

    def execute(self, statement, params=None, **kwargs):
        """Execute a statement with automatic routing.

        Args:
            statement: SQL statement to execute
            params: Query parameters
            **kwargs: Additional arguments

        Returns:
            Result of query execution
        """
        # Determine query type and routing
        query_str = str(statement.compile()) if hasattr(statement, 'compile') else str(statement)
        query_type = self._router.classify_query(query_str)

        # Check routing policy
        force_primary = (
            self._force_primary or
            self._routing_policy.should_force_primary(
                query_type=query_type,
                in_transaction=self._in_transaction,
                recent_write=self._recent_write
            )
        )

        # Route the query
        engine = self._router.route_query(
            query=query_str,
            query_type=query_type,
            session_id=self._session_id,
            force_primary=force_primary
        )

        # Execute on appropriate engine
        # Note: For proper replica routing, we'd need to switch session binding
        # For now, we'll use the session's existing connection
        # Full implementation would require more sophisticated connection management

        return self._session.execute(statement, params, **kwargs)

    def query(self, *entities, **kwargs):
        """Create a query (delegates to underlying session).

        Args:
            *entities: Entities to query
            **kwargs: Query options

        Returns:
            Query object
        """
        return self._session.query(*entities, **kwargs)

    def add(self, instance):
        """Add an instance to the session.

        Args:
            instance: Model instance to add
        """
        self._recent_write = True
        return self._session.add(instance)

    def delete(self, instance):
        """Mark an instance for deletion.

        Args:
            instance: Model instance to delete
        """
        self._recent_write = True
        return self._session.delete(instance)

    def commit(self):
        """Commit the current transaction."""
        return self._session.commit()

    def rollback(self):
        """Rollback the current transaction."""
        return self._session.rollback()

    def close(self):
        """Close the session."""
        return self._session.close()

    def flush(self):
        """Flush pending changes."""
        self._recent_write = True
        return self._session.flush()

    def refresh(self, instance, *args, **kwargs):
        """Refresh an instance from database.

        Args:
            instance: Instance to refresh
            *args: Additional arguments
            **kwargs: Additional keyword arguments
        """
        return self._session.refresh(instance, *args, **kwargs)

    def merge(self, instance, *args, **kwargs):
        """Merge an instance into the session.

        Args:
            instance: Instance to merge
            *args: Additional arguments
            **kwargs: Additional keyword arguments
        """
        self._recent_write = True
        return self._session.merge(instance, *args, **kwargs)

    def expunge(self, instance):
        """Expunge an instance from the session.

        Args:
            instance: Instance to expunge
        """
        return self._session.expunge(instance)

    def expunge_all(self):
        """Expunge all instances from the session."""
        return self._session.expunge_all()

    @property
    def dirty(self):
        """Get dirty instances in the session."""
        return self._session.dirty

    @property
    def new(self):
        """Get new instances in the session."""
        return self._session.new

    @property
    def deleted(self):
        """Get deleted instances in the session."""
        return self._session.deleted

    @property
    def is_active(self):
        """Check if session is active."""
        return self._session.is_active

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()
