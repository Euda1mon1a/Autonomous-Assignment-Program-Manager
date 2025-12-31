"""
Query optimization utilities and helpers.

Provides:
- Query analysis
- N+1 detection
- Slow query logging
- Query caching patterns
- Bulk operations
- Pagination helpers
- Filtering helpers
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, List
from datetime import datetime

from sqlalchemy import inspect, event
from sqlalchemy.orm import Session, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select

logger = logging.getLogger(__name__)


class QueryMetrics:
    """Metrics for query execution."""

    def __init__(self):
        """Initialize query metrics."""
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.query_count = 0
        self.total_duration = 0.0
        self.slow_queries: List[Dict[str, Any]] = []

    @property
    def duration(self) -> float:
        """Get query duration in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0

    def add_slow_query(self, query: str, duration: float) -> None:
        """Add slow query to tracking."""
        self.slow_queries.append({
            "query": query,
            "duration_ms": duration,
            "timestamp": datetime.utcnow(),
        })

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"QueryMetrics(count={self.query_count}, "
            f"duration={self.duration:.2f}ms, "
            f"slow_queries={len(self.slow_queries)})"
        )


class QueryAnalyzer:
    """Analyze and optimize queries."""

    SLOW_QUERY_THRESHOLD_MS = 100.0

    @staticmethod
    def enable_query_logging(engine: Any, verbose: bool = False) -> None:
        """
        Enable SQL query logging.

        Args:
            engine: SQLAlchemy engine
            verbose: Print to console if True
        """
        @event.listens_for(engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Log before query execution."""
            conn.info.setdefault("query_start_time", []).append(time.time())
            if verbose:
                logger.debug(f"Query: {statement}")

        @event.listens_for(engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Log after query execution."""
            total = time.time() - conn.info["query_start_time"].pop(-1)
            duration_ms = total * 1000

            if duration_ms > QueryAnalyzer.SLOW_QUERY_THRESHOLD_MS:
                logger.warning(f"SLOW QUERY ({duration_ms:.2f}ms): {statement}")

    @staticmethod
    def detect_n_plus_one(session: Session) -> List[str]:
        """
        Detect potential N+1 query patterns.

        Args:
            session: Database session

        Returns:
            List of issue descriptions
        """
        issues = []
        queries = []

        # Track all queries executed in session
        @event.listens_for(session, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            queries.append(statement)

        # Analyze query patterns
        select_count = sum(1 for q in queries if q.strip().upper().startswith("SELECT"))
        if select_count > 5:
            issues.append(f"Possible N+1 pattern: {select_count} SELECT queries")

        return issues

    @staticmethod
    def analyze_query_plan(session: Session, query: Query) -> Dict[str, Any]:
        """
        Analyze query execution plan.

        Args:
            session: Database session
            query: SQLAlchemy query

        Returns:
            Dictionary with query plan analysis
        """
        # Note: EXPLAIN only works with certain databases
        try:
            statement = str(query.statement.compile(compile_kwargs={"literal_binds": True}))
            plan = session.execute(f"EXPLAIN {statement}").fetchall()

            return {
                "query": statement,
                "plan": [row for row in plan],
                "estimated_rows": None,
            }

        except Exception as e:
            logger.warning(f"Could not analyze query plan: {e}")
            return {
                "query": str(query),
                "plan": None,
                "error": str(e),
            }

    @staticmethod
    def get_table_stats(session: Session, model: Any) -> Dict[str, Any]:
        """
        Get statistics for a model's table.

        Args:
            session: Database session
            model: SQLAlchemy model class

        Returns:
            Dictionary with table statistics
        """
        table_name = model.__tablename__

        try:
            # Get row count
            row_count = session.query(model).count()

            # Get columns
            mapper = inspect(model)
            columns = [c.key for c in mapper.columns]

            return {
                "table": table_name,
                "row_count": row_count,
                "columns": columns,
                "column_count": len(columns),
            }

        except Exception as e:
            logger.error(f"Error getting table stats for {table_name}: {e}")
            return {
                "table": table_name,
                "error": str(e),
            }


class QueryDecorator:
    """Decorators for query optimization."""

    @staticmethod
    def track_performance(threshold_ms: float = 100.0) -> Callable:
        """
        Decorator to track query performance.

        Args:
            threshold_ms: Log if execution time exceeds this

        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    if duration_ms > threshold_ms:
                        logger.warning(
                            f"SLOW OPERATION: {func.__name__} took {duration_ms:.2f}ms"
                        )
            return wrapper
        return decorator

    @staticmethod
    def cache_result(ttl_seconds: int = 300) -> Callable:
        """
        Decorator to cache query results.

        Args:
            ttl_seconds: Cache time-to-live in seconds

        Returns:
            Decorator function
        """
        cache: Dict[str, tuple] = {}

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                cache_key = f"{func.__name__}:{args}:{kwargs}"

                if cache_key in cache:
                    result, cache_time = cache[cache_key]
                    if time.time() - cache_time < ttl_seconds:
                        return result

                result = func(*args, **kwargs)
                cache[cache_key] = (result, time.time())
                return result

            return wrapper
        return decorator


class BulkOperations:
    """Utilities for efficient bulk operations."""

    @staticmethod
    def bulk_insert(session: Session, model: Any, data_list: List[Dict]) -> int:
        """
        Efficiently insert multiple records.

        Args:
            session: Database session
            model: SQLAlchemy model class
            data_list: List of dictionaries with data

        Returns:
            Number of inserted records
        """
        if not data_list:
            return 0

        try:
            session.bulk_insert_mappings(model, data_list)
            session.commit()
            return len(data_list)
        except Exception as e:
            session.rollback()
            logger.error(f"Bulk insert error: {e}")
            return 0

    @staticmethod
    def bulk_update(session: Session, model: Any, data_list: List[Dict]) -> int:
        """
        Efficiently update multiple records.

        Args:
            session: Database session
            model: SQLAlchemy model class
            data_list: List of dictionaries with updated data

        Returns:
            Number of updated records
        """
        if not data_list:
            return 0

        try:
            session.bulk_update_mappings(model, data_list)
            session.commit()
            return len(data_list)
        except Exception as e:
            session.rollback()
            logger.error(f"Bulk update error: {e}")
            return 0

    @staticmethod
    def bulk_delete(session: Session, model: Any, ids: List[Any]) -> int:
        """
        Efficiently delete multiple records by ID.

        Args:
            session: Database session
            model: SQLAlchemy model class
            ids: List of IDs to delete

        Returns:
            Number of deleted records
        """
        if not ids:
            return 0

        try:
            session.query(model).filter(model.id.in_(ids)).delete()
            session.commit()
            return len(ids)
        except Exception as e:
            session.rollback()
            logger.error(f"Bulk delete error: {e}")
            return 0


class FilterHelper:
    """Helpers for building and applying filters."""

    @staticmethod
    def apply_filters(query: Query, filters: Dict[str, Any]) -> Query:
        """
        Apply filter dictionary to query.

        Args:
            query: SQLAlchemy query
            filters: Dictionary of {field: value} pairs

        Returns:
            Filtered query
        """
        for field, value in filters.items():
            if value is not None:
                if hasattr(query.column_descriptions[0]["entity"], field):
                    column = getattr(query.column_descriptions[0]["entity"], field)
                    query = query.filter(column == value)

        return query

    @staticmethod
    def apply_range_filter(
        query: Query,
        field: str,
        model: Any,
        min_val: Optional[Any] = None,
        max_val: Optional[Any] = None,
    ) -> Query:
        """
        Apply range filter to query.

        Args:
            query: SQLAlchemy query
            field: Field name to filter
            model: Model class
            min_val: Minimum value
            max_val: Maximum value

        Returns:
            Filtered query
        """
        if hasattr(model, field):
            column = getattr(model, field)

            if min_val is not None:
                query = query.filter(column >= min_val)

            if max_val is not None:
                query = query.filter(column <= max_val)

        return query

    @staticmethod
    def apply_search(
        query: Query,
        model: Any,
        search_text: str,
        fields: List[str],
    ) -> Query:
        """
        Apply text search across multiple fields.

        Args:
            query: SQLAlchemy query
            model: Model class
            search_text: Text to search for
            fields: List of field names to search

        Returns:
            Filtered query
        """
        if not search_text:
            return query

        conditions = []
        for field in fields:
            if hasattr(model, field):
                column = getattr(model, field)
                conditions.append(column.ilike(f"%{search_text}%"))

        if conditions:
            from sqlalchemy import or_
            query = query.filter(or_(*conditions))

        return query


class SortHelper:
    """Helpers for sorting queries."""

    @staticmethod
    def apply_sort(query: Query, model: Any, sort_by: str) -> Query:
        """
        Apply sorting to query.

        Args:
            query: SQLAlchemy query
            model: Model class
            sort_by: Field to sort by (prefix with '-' for descending)

        Returns:
            Sorted query
        """
        if sort_by.startswith("-"):
            field_name = sort_by[1:]
            if hasattr(model, field_name):
                from sqlalchemy import desc
                column = getattr(model, field_name)
                query = query.order_by(desc(column))
        else:
            if hasattr(model, sort_by):
                column = getattr(model, sort_by)
                query = query.order_by(column)

        return query

    @staticmethod
    def apply_multi_sort(query: Query, model: Any, sort_fields: List[str]) -> Query:
        """
        Apply multiple sort fields to query.

        Args:
            query: SQLAlchemy query
            model: Model class
            sort_fields: List of fields to sort by

        Returns:
            Sorted query
        """
        for sort_by in sort_fields:
            query = SortHelper.apply_sort(query, model, sort_by)

        return query


class PaginationHelper:
    """Helpers for pagination."""

    @staticmethod
    def paginate(
        query: Query,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[Query, int]:
        """
        Apply pagination to query.

        Args:
            query: SQLAlchemy query
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            Tuple of (paginated_query, total_count)
        """
        # Get total count before pagination
        total = query.count()

        # Apply pagination
        query = query.offset(skip).limit(limit)

        return query, total

    @staticmethod
    def get_pagination_info(
        total: int,
        skip: int = 0,
        limit: int = 100,
    ) -> Dict[str, int]:
        """
        Get pagination information.

        Args:
            total: Total record count
            skip: Records skipped
            limit: Limit per page

        Returns:
            Dictionary with pagination info
        """
        pages = (total + limit - 1) // limit
        current_page = (skip // limit) + 1

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "pages": pages,
            "current_page": current_page,
            "has_next": current_page < pages,
            "has_previous": current_page > 1,
        }
