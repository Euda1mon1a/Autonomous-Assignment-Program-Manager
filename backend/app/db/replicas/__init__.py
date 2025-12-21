"""Read replica routing package.

Provides database replication support with automatic query routing:
- Primary/replica separation
- Read/write query splitting
- Round-robin load balancing across replicas
- Health-based routing (skip unhealthy replicas)
- Replication lag detection
- Sticky session support

Usage:
    from app.db.replicas import ReplicaAwareSessionFactory
    from sqlalchemy import create_engine

    # Set up engines
    primary = create_engine("postgresql://primary:5432/db")
    replicas = {
        "replica1": create_engine("postgresql://replica1:5432/db"),
        "replica2": create_engine("postgresql://replica2:5432/db"),
    }

    # Create session factory
    factory = ReplicaAwareSessionFactory(
        primary_engine=primary,
        replica_engines=replicas,
        enable_sticky_sessions=True
    )

    # Use sessions
    with factory.session_scope() as session:
        # Reads automatically route to replicas
        users = session.query(User).all()

        # Writes automatically route to primary
        session.add(new_user)
        session.commit()

Features:
    - Automatic read/write splitting
    - Health monitoring and lag detection
    - Round-robin load balancing
    - Sticky sessions (optional)
    - Fallback to primary if no healthy replicas
    - Configurable routing policies
"""

from app.db.replicas.balancer import LoadBalancer, StickySessionBalancer
from app.db.replicas.health import HealthChecker, ReplicaHealth
from app.db.replicas.router import QueryRouter, QueryType, RoutingPolicy
from app.db.replicas.session import ReplicaAwareSession, ReplicaAwareSessionFactory

__all__ = [
    # Session management
    "ReplicaAwareSessionFactory",
    "ReplicaAwareSession",
    # Query routing
    "QueryRouter",
    "QueryType",
    "RoutingPolicy",
    # Load balancing
    "LoadBalancer",
    "StickySessionBalancer",
    # Health monitoring
    "HealthChecker",
    "ReplicaHealth",
]

__version__ = "1.0.0"
