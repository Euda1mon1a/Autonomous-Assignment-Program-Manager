"""Query router for primary/replica database routing.

Routes database queries to appropriate database instances:
- Write operations (INSERT, UPDATE, DELETE) -> Primary
- Read operations (SELECT) -> Replicas (with fallback to primary)
"""

import logging
import re
from enum import Enum

from sqlalchemy.engine import Engine

from app.db.replicas.balancer import LoadBalancer

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Type of database query for routing decisions."""

    READ = "read"
    WRITE = "write"
    DDL = "ddl"  # Data Definition Language (CREATE, ALTER, DROP)
    TRANSACTION = "transaction"  # BEGIN, COMMIT, ROLLBACK
    UNKNOWN = "unknown"


class QueryRouter:
    """Routes queries to primary or replica databases.

    Routing logic:
    - SELECT queries -> Replicas (round-robin load balanced)
    - INSERT/UPDATE/DELETE/DDL -> Primary (only)
    - Transactions -> Primary (for consistency)
    - Unknown queries -> Primary (safe default)

    Fallback behavior:
    - If no healthy replicas available, reads go to primary
    - Ensures high availability at cost of primary load
    """

    # SQL statement patterns for query classification
    READ_PATTERNS = [
        re.compile(r"^\s*SELECT\s+", re.IGNORECASE),
        re.compile(r"^\s*WITH\s+.*\s+SELECT\s+", re.IGNORECASE),  # CTE with SELECT
        re.compile(r"^\s*SHOW\s+", re.IGNORECASE),
        re.compile(r"^\s*DESCRIBE\s+", re.IGNORECASE),
        re.compile(r"^\s*EXPLAIN\s+", re.IGNORECASE),
    ]

    WRITE_PATTERNS = [
        re.compile(r"^\s*INSERT\s+", re.IGNORECASE),
        re.compile(r"^\s*UPDATE\s+", re.IGNORECASE),
        re.compile(r"^\s*DELETE\s+", re.IGNORECASE),
        re.compile(r"^\s*MERGE\s+", re.IGNORECASE),
    ]

    DDL_PATTERNS = [
        re.compile(r"^\s*CREATE\s+", re.IGNORECASE),
        re.compile(r"^\s*ALTER\s+", re.IGNORECASE),
        re.compile(r"^\s*DROP\s+", re.IGNORECASE),
        re.compile(r"^\s*TRUNCATE\s+", re.IGNORECASE),
        re.compile(r"^\s*RENAME\s+", re.IGNORECASE),
    ]

    TRANSACTION_PATTERNS = [
        re.compile(r"^\s*BEGIN\s*", re.IGNORECASE),
        re.compile(r"^\s*COMMIT\s*", re.IGNORECASE),
        re.compile(r"^\s*ROLLBACK\s*", re.IGNORECASE),
        re.compile(r"^\s*START\s+TRANSACTION\s*", re.IGNORECASE),
        re.compile(r"^\s*SAVEPOINT\s+", re.IGNORECASE),
    ]

    def __init__(
        self,
        primary_engine: Engine,
        balancer: LoadBalancer | None = None,
        fallback_to_primary: bool = True,
    ) -> None:
        """Initialize query router.

        Args:
            primary_engine: SQLAlchemy engine for primary database
            balancer: Load balancer for replicas (optional)
            fallback_to_primary: Whether to use primary if no replicas available
        """
        self.primary_engine = primary_engine
        self.balancer = balancer
        self.fallback_to_primary = fallback_to_primary

        logger.info(
            f"QueryRouter initialized: replicas={balancer.get_replica_count() if balancer else 0}, "
            f"fallback={fallback_to_primary}"
        )

    def route_query(
        self,
        query: str | None = None,
        query_type: QueryType | None = None,
        session_id: str | None = None,
        force_primary: bool = False,
    ) -> Engine:
        """Route a query to appropriate database engine.

        Args:
            query: SQL query string (for automatic type detection)
            query_type: Explicit query type (overrides detection)
            session_id: Session ID for sticky routing (optional)
            force_primary: Force routing to primary regardless of query type

        Returns:
            Engine to use for the query
        """
        # Force primary if requested
        if force_primary:
            logger.debug("Routing to primary (forced)")
            return self.primary_engine

            # Determine query type
        if query_type is None and query is not None:
            query_type = self.classify_query(query)

            # Route based on query type
        if query_type == QueryType.READ:
            return self._route_read_query(session_id)
        else:
            # All non-read queries go to primary
            logger.debug(f"Routing to primary (query_type={query_type})")
            return self.primary_engine

    def _route_read_query(self, session_id: str | None = None) -> Engine:
        """Route a read query to a replica or primary.

        Args:
            session_id: Session ID for sticky routing

        Returns:
            Engine to use for the read query
        """
        if not self.balancer:
            logger.debug("No balancer configured, routing read to primary")
            return self.primary_engine

            # Try to select a healthy replica
        selection = self.balancer.select_replica(session_id)

        if selection:
            replica_name, engine = selection
            logger.debug(f"Routing read to replica: {replica_name}")
            return engine

            # No healthy replicas available
        if self.fallback_to_primary:
            logger.debug("No healthy replicas, falling back to primary")
            return self.primary_engine
        else:
            logger.warning("No healthy replicas and fallback disabled")
            # Return primary anyway to avoid application errors
            # Alternative: could raise an exception here
            return self.primary_engine

    @classmethod
    def classify_query(cls, query: str) -> QueryType:
        """Classify a SQL query by type.

        Args:
            query: SQL query string

        Returns:
            QueryType classification
        """
        if not query or not isinstance(query, str):
            return QueryType.UNKNOWN

            # Normalize whitespace
        normalized_query = " ".join(query.split())

        # Check patterns in order of specificity
        for pattern in cls.TRANSACTION_PATTERNS:
            if pattern.match(normalized_query):
                return QueryType.TRANSACTION

        for pattern in cls.DDL_PATTERNS:
            if pattern.match(normalized_query):
                return QueryType.DDL

        for pattern in cls.WRITE_PATTERNS:
            if pattern.match(normalized_query):
                return QueryType.WRITE

        for pattern in cls.READ_PATTERNS:
            if pattern.match(normalized_query):
                return QueryType.READ

                # Default to unknown (will route to primary)
        logger.debug(f"Could not classify query: {query[:100]}")
        return QueryType.UNKNOWN

    def get_routing_stats(self) -> dict:
        """Get statistics about query routing.

        Returns:
            Dictionary with routing statistics
        """
        stats = {
            "has_replicas": self.balancer is not None,
            "replica_count": self.balancer.get_replica_count() if self.balancer else 0,
            "healthy_replicas": (
                self.balancer.get_healthy_replica_count() if self.balancer else 0
            ),
            "fallback_enabled": self.fallback_to_primary,
            "primary_pool_size": self.primary_engine.pool.size(),
            "primary_checked_in": self.primary_engine.pool.checkedin(),
        }

        if self.balancer:
            stats["replica_stats"] = self.balancer.get_replica_stats()

        return stats

    def is_replica_routing_available(self) -> bool:
        """Check if replica routing is available.

        Returns:
            True if at least one healthy replica is available
        """
        if not self.balancer:
            return False

        return self.balancer.get_healthy_replica_count() > 0


class RoutingPolicy:
    """Policy for query routing decisions.

    Allows customization of routing behavior beyond simple read/write split.
    """

    def __init__(
        self,
        force_primary_for_user_writes: bool = True,
        force_primary_in_transaction: bool = True,
        allow_stale_reads: bool = False,
        max_acceptable_lag_seconds: float = 30.0,
    ) -> None:
        """Initialize routing policy.

        Args:
            force_primary_for_user_writes: Route to primary after writes in session
            force_primary_in_transaction: Route all queries in transaction to primary
            allow_stale_reads: Allow reads from lagging replicas
            max_acceptable_lag_seconds: Maximum acceptable replication lag
        """
        self.force_primary_for_user_writes = force_primary_for_user_writes
        self.force_primary_in_transaction = force_primary_in_transaction
        self.allow_stale_reads = allow_stale_reads
        self.max_acceptable_lag_seconds = max_acceptable_lag_seconds

    def should_force_primary(
        self,
        query_type: QueryType,
        in_transaction: bool = False,
        recent_write: bool = False,
    ) -> bool:
        """Determine if query should be forced to primary.

        Args:
            query_type: Type of query
            in_transaction: Whether currently in a transaction
            recent_write: Whether session recently executed a write

        Returns:
            True if query should go to primary
        """
        # Always route writes to primary
        if query_type in (QueryType.WRITE, QueryType.DDL, QueryType.TRANSACTION):
            return True

            # Force primary in transactions for consistency
        if in_transaction and self.force_primary_in_transaction:
            return True

            # Force primary after recent write for read-your-writes consistency
        if recent_write and self.force_primary_for_user_writes:
            return True

        return False
