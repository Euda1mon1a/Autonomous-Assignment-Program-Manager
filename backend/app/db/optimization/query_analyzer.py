"""Query performance analyzer with N+1 detection and slow query logging.

Provides real-time query analysis, performance monitoring, and N+1 query detection
to help identify and fix performance bottlenecks.
"""

import logging
import re
import time
from collections import defaultdict
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Context variable to track queries within a request
_query_context: ContextVar[Optional["QueryContext"]] = ContextVar(
    "query_context", default=None
)


@dataclass
class QueryInfo:
    """Information about a single query execution."""

    sql: str
    params: dict[str, Any] | tuple | None
    duration_ms: float
    timestamp: datetime
    stack_trace: str
    explain_plan: str | None = None


@dataclass
class QueryContext:
    """Context for tracking queries during a request."""

    request_id: str
    queries: list[QueryInfo] = field(default_factory=list)
    n_plus_one_warnings: list[dict[str, Any]] = field(default_factory=list)
    slow_queries: list[QueryInfo] = field(default_factory=list)
    total_duration_ms: float = 0.0
    start_time: datetime = field(default_factory=datetime.utcnow)


class QueryAnalyzer:
    """
    Query performance analyzer with N+1 detection.

    Features:
    - Tracks all queries executed during a request
    - Detects N+1 query patterns
    - Logs slow queries
    - Generates EXPLAIN plans for analysis
    - Provides query statistics

    Usage:
        analyzer = QueryAnalyzer(slow_query_threshold_ms=100)
        analyzer.attach_to_engine(engine)

        # Within a request
        with analyzer.track_request("request-123"):
            # Execute queries
            db.query(Person).all()

        # Get stats
        stats = analyzer.get_request_stats("request-123")
    """

    def __init__(
        self,
        slow_query_threshold_ms: float = 100.0,
        n_plus_one_threshold: int = 10,
        enable_explain: bool = False,
    ):
        """
        Initialize query analyzer.

        Args:
            slow_query_threshold_ms: Queries slower than this are logged
            n_plus_one_threshold: Number of similar queries to trigger N+1 warning
            enable_explain: Whether to capture EXPLAIN plans (performance impact)
        """
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.n_plus_one_threshold = n_plus_one_threshold
        self.enable_explain = enable_explain
        self._attached_engines: set[Engine] = set()
        self._request_contexts: dict[str, QueryContext] = {}

    def attach_to_engine(self, engine: Engine) -> None:
        """
        Attach query tracking to a SQLAlchemy engine.

        Args:
            engine: SQLAlchemy engine instance
        """
        if engine in self._attached_engines:
            return

        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            """Track query start time."""
            context._query_start_time = time.perf_counter()

        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            """Track query completion and analyze."""
            query_context = _query_context.get()
            if not query_context:
                return

            # Calculate duration
            duration_ms = (
                time.perf_counter() - context._query_start_time
            ) * 1000

            # Get stack trace (limited depth to avoid noise)
            import traceback
            stack_trace = "".join(traceback.format_stack()[-8:-2])

            # Create query info
            query_info = QueryInfo(
                sql=statement,
                params=parameters,
                duration_ms=duration_ms,
                timestamp=datetime.utcnow(),
                stack_trace=stack_trace,
            )

            # Capture EXPLAIN plan if enabled and query is slow
            if (
                self.enable_explain
                and duration_ms > self.slow_query_threshold_ms
                and statement.strip().upper().startswith("SELECT")
            ):
                try:
                    explain_query = f"EXPLAIN ANALYZE {statement}"
                    result = conn.execute(text(explain_query), parameters)
                    query_info.explain_plan = "\n".join(
                        [row[0] for row in result]
                    )
                except Exception as e:
                    logger.debug(f"Failed to get EXPLAIN plan: {e}")

            # Add to context
            query_context.queries.append(query_info)
            query_context.total_duration_ms += duration_ms

            # Check for slow query
            if duration_ms > self.slow_query_threshold_ms:
                query_context.slow_queries.append(query_info)
                logger.warning(
                    f"Slow query detected ({duration_ms:.2f}ms): {self._sanitize_sql(statement)[:100]}"
                )

        self._attached_engines.add(engine)
        logger.info("Query analyzer attached to engine")

    def track_request(self, request_id: str) -> "RequestTracker":
        """
        Track queries for a specific request.

        Args:
            request_id: Unique identifier for the request

        Returns:
            RequestTracker: Context manager for tracking queries
        """
        return RequestTracker(self, request_id)

    def analyze_n_plus_one(self, context: QueryContext) -> list[dict[str, Any]]:
        """
        Detect N+1 query patterns in the context.

        Args:
            context: Query context to analyze

        Returns:
            List of N+1 warnings with details
        """
        warnings = []

        # Group queries by normalized SQL
        query_groups = defaultdict(list)
        for query in context.queries:
            normalized = self._normalize_sql(query.sql)
            query_groups[normalized].append(query)

        # Check for repeated queries (potential N+1)
        for normalized_sql, queries in query_groups.items():
            if len(queries) >= self.n_plus_one_threshold:
                # Check if queries are similar (same structure, different params)
                if self._are_queries_similar(queries):
                    total_duration = sum(q.duration_ms for q in queries)
                    warnings.append(
                        {
                            "type": "N+1_QUERY",
                            "query_count": len(queries),
                            "total_duration_ms": total_duration,
                            "avg_duration_ms": total_duration / len(queries),
                            "sql_pattern": self._sanitize_sql(normalized_sql)[:200],
                            "recommendation": "Consider using joinedload() or selectinload() for eager loading",
                            "example_stack": queries[0].stack_trace,
                        }
                    )

        return warnings

    def get_request_stats(self, request_id: str) -> dict[str, Any]:
        """
        Get statistics for a tracked request.

        Args:
            request_id: Request identifier

        Returns:
            Dictionary with query statistics
        """
        context = self._request_contexts.get(request_id)
        if not context:
            return {}

        # Analyze N+1 patterns
        n_plus_one_warnings = self.analyze_n_plus_one(context)

        # Calculate stats
        query_count = len(context.queries)
        slow_query_count = len(context.slow_queries)

        # Group by query type
        query_types = defaultdict(int)
        for query in context.queries:
            query_type = self._get_query_type(query.sql)
            query_types[query_type] += 1

        # Find slowest queries
        slowest_queries = sorted(
            context.queries, key=lambda q: q.duration_ms, reverse=True
        )[:5]

        return {
            "request_id": request_id,
            "total_queries": query_count,
            "total_duration_ms": context.total_duration_ms,
            "avg_duration_ms": (
                context.total_duration_ms / query_count if query_count > 0 else 0
            ),
            "slow_queries": slow_query_count,
            "n_plus_one_warnings": len(n_plus_one_warnings),
            "n_plus_one_details": n_plus_one_warnings,
            "query_types": dict(query_types),
            "slowest_queries": [
                {
                    "sql": self._sanitize_sql(q.sql)[:200],
                    "duration_ms": q.duration_ms,
                    "timestamp": q.timestamp.isoformat(),
                }
                for q in slowest_queries
            ],
            "recommendations": self._generate_recommendations(
                context, n_plus_one_warnings
            ),
        }

    def _normalize_sql(self, sql: str) -> str:
        """
        Normalize SQL by removing parameters to group similar queries.

        Args:
            sql: SQL statement

        Returns:
            Normalized SQL
        """
        # Remove values in WHERE clauses
        normalized = re.sub(r"= \?|\= '[^']*'|= \d+", "= ?", sql)
        # Remove IN clause values
        normalized = re.sub(r"IN \([^)]+\)", "IN (?)", normalized)
        # Normalize whitespace
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()

    def _sanitize_sql(self, sql: str) -> str:
        """
        Sanitize SQL for logging (remove sensitive data).

        Args:
            sql: SQL statement

        Returns:
            Sanitized SQL
        """
        # This is a simple sanitization - in production, you'd want more robust handling
        sanitized = re.sub(r"'[^']*'", "'***'", sql)
        return sanitized

    def _get_query_type(self, sql: str) -> str:
        """
        Determine query type (SELECT, INSERT, UPDATE, DELETE).

        Args:
            sql: SQL statement

        Returns:
            Query type
        """
        sql_upper = sql.strip().upper()
        for query_type in ["SELECT", "INSERT", "UPDATE", "DELETE"]:
            if sql_upper.startswith(query_type):
                return query_type
        return "OTHER"

    def _are_queries_similar(self, queries: list[QueryInfo]) -> bool:
        """
        Check if queries are similar (same structure, different params).

        Args:
            queries: List of query info objects

        Returns:
            True if queries are similar
        """
        if len(queries) < 2:
            return False

        # Check if all queries have the same normalized SQL
        first_normalized = self._normalize_sql(queries[0].sql)
        return all(
            self._normalize_sql(q.sql) == first_normalized for q in queries[1:]
        )

    def _generate_recommendations(
        self, context: QueryContext, n_plus_one_warnings: list[dict[str, Any]]
    ) -> list[str]:
        """
        Generate optimization recommendations based on query patterns.

        Args:
            context: Query context
            n_plus_one_warnings: Detected N+1 patterns

        Returns:
            List of recommendations
        """
        recommendations = []

        # N+1 recommendations
        if n_plus_one_warnings:
            recommendations.append(
                f"Found {len(n_plus_one_warnings)} N+1 query patterns - use eager loading (joinedload/selectinload)"
            )

        # Slow query recommendations
        if len(context.slow_queries) > 5:
            recommendations.append(
                f"{len(context.slow_queries)} slow queries detected - consider adding indexes or optimizing queries"
            )

        # High query count
        if len(context.queries) > 100:
            recommendations.append(
                f"High query count ({len(context.queries)}) - consider batching or reducing database calls"
            )

        # Total duration
        if context.total_duration_ms > 1000:
            recommendations.append(
                f"High total query time ({context.total_duration_ms:.0f}ms) - review query efficiency"
            )

        return recommendations


class RequestTracker:
    """Context manager for tracking queries during a request."""

    def __init__(self, analyzer: QueryAnalyzer, request_id: str):
        """
        Initialize request tracker.

        Args:
            analyzer: Query analyzer instance
            request_id: Unique request identifier
        """
        self.analyzer = analyzer
        self.request_id = request_id
        self.context = QueryContext(request_id=request_id)

    def __enter__(self) -> QueryContext:
        """Start tracking queries."""
        _query_context.set(self.context)
        self.analyzer._request_contexts[self.request_id] = self.context
        return self.context

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop tracking and analyze queries."""
        _query_context.set(None)

        # Log summary
        stats = self.analyzer.get_request_stats(self.request_id)
        if stats.get("n_plus_one_warnings", 0) > 0 or stats.get("slow_queries", 0) > 5:
            logger.warning(
                f"Request {self.request_id}: {stats['total_queries']} queries, "
                f"{stats['n_plus_one_warnings']} N+1 warnings, "
                f"{stats['slow_queries']} slow queries"
            )


def get_query_analyzer(
    slow_query_threshold_ms: float = 100.0,
    n_plus_one_threshold: int = 10,
) -> QueryAnalyzer:
    """
    Get a configured query analyzer instance.

    Args:
        slow_query_threshold_ms: Threshold for slow queries
        n_plus_one_threshold: Threshold for N+1 detection

    Returns:
        QueryAnalyzer instance
    """
    return QueryAnalyzer(
        slow_query_threshold_ms=slow_query_threshold_ms,
        n_plus_one_threshold=n_plus_one_threshold,
        enable_explain=False,  # Disable by default due to performance impact
    )
