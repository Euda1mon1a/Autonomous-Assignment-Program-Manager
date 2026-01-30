"""
Metric collectors for profiling.

Provides collectors for SQL queries, HTTP requests, and distributed traces.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import event
from sqlalchemy.engine import Engine


@dataclass
class SQLQuery:
    """Represents a captured SQL query."""

    query_id: str
    sql: str
    parameters: dict[str, Any] | None
    start_time: datetime
    end_time: datetime | None
    duration_ms: float | None
    row_count: int | None
    error: str | None
    stack_trace: str | None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query_id": self.query_id,
            "sql": self.sql,
            "parameters": self.parameters,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "row_count": self.row_count,
            "error": self.error,
        }


@dataclass
class RequestMetrics:
    """Represents HTTP request metrics."""

    request_id: str
    method: str
    path: str
    status_code: int | None
    start_time: datetime
    end_time: datetime | None
    duration_ms: float | None
    request_size_bytes: int
    response_size_bytes: int | None
    user_id: str | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "request_id": self.request_id,
            "method": self.method,
            "path": self.path,
            "status_code": self.status_code,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "request_size_bytes": self.request_size_bytes,
            "response_size_bytes": self.response_size_bytes,
            "user_id": self.user_id,
            "metadata": self.metadata,
        }


@dataclass
class Trace:
    """Represents a distributed trace span."""

    trace_id: str
    span_id: str
    parent_span_id: str | None
    operation_name: str
    start_time: datetime
    end_time: datetime | None
    duration_ms: float | None
    tags: dict[str, Any] = field(default_factory=dict)
    logs: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "operation_name": self.operation_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "tags": self.tags,
            "logs": self.logs,
        }


class MetricCollector:
    """
    Base metric collector.

    Provides common functionality for all collectors.
    """

    def __init__(self, enabled: bool = True, max_items: int = 10000) -> None:
        """
        Initialize metric collector.

        Args:
            enabled: Whether collection is enabled
            max_items: Maximum number of items to store
        """
        self.enabled = enabled
        self.max_items = max_items
        self.items: list[Any] = []

    def add_item(self, item: Any) -> None:
        """
        Add an item to the collection.

        Args:
            item: Item to add
        """
        if not self.enabled:
            return

        self.items.append(item)

        # Trim if over max
        if len(self.items) > self.max_items:
            self.items = self.items[-self.max_items :]

    def get_items(self, limit: int | None = None) -> list[Any]:
        """
        Get collected items.

        Args:
            limit: Maximum number of items to return

        Returns:
            List of collected items
        """
        if limit:
            return self.items[-limit:]
        return self.items

    def clear(self) -> None:
        """Clear all collected items."""
        self.items.clear()

    def get_count(self) -> int:
        """Get number of collected items."""
        return len(self.items)


class SQLQueryCollector(MetricCollector):
    """
    SQL query collector.

    Captures all SQL queries executed through SQLAlchemy.
    """

    def __init__(self, enabled: bool = True, max_queries: int = 10000) -> None:
        """
        Initialize SQL query collector.

        Args:
            enabled: Whether collection is enabled
            max_queries: Maximum number of queries to store
        """
        super().__init__(enabled=enabled, max_items=max_queries)
        self.active_queries: dict[str, SQLQuery] = {}
        self._listeners_registered = False

    def register_listeners(self, engine: Engine) -> None:
        """
        Register SQLAlchemy event listeners.

        Args:
            engine: SQLAlchemy engine instance
        """
        if self._listeners_registered:
            return

        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ) -> None:
            if not self.enabled:
                return

            query_id = str(uuid4())
            context._query_id = query_id

            query = SQLQuery(
                query_id=query_id,
                sql=statement,
                parameters=parameters if not executemany else None,
                start_time=datetime.utcnow(),
                end_time=None,
                duration_ms=None,
                row_count=None,
                error=None,
                stack_trace=None,
            )
            self.active_queries[query_id] = query

        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ) -> None:
            if not self.enabled:
                return

            query_id = getattr(context, "_query_id", None)
            if not query_id or query_id not in self.active_queries:
                return

            query = self.active_queries[query_id]
            query.end_time = datetime.utcnow()
            query.duration_ms = (
                query.end_time - query.start_time
            ).total_seconds() * 1000
            query.row_count = cursor.rowcount if cursor.rowcount >= 0 else None

            self.add_item(query)
            del self.active_queries[query_id]

        @event.listens_for(engine, "handle_error")
        def handle_error(context) -> None:
            if not self.enabled:
                return

            query_id = getattr(context.execution_context, "_query_id", None)
            if not query_id or query_id not in self.active_queries:
                return

            query = self.active_queries[query_id]
            query.end_time = datetime.utcnow()
            query.duration_ms = (
                query.end_time - query.start_time
            ).total_seconds() * 1000
            query.error = str(context.original_exception)

            self.add_item(query)
            del self.active_queries[query_id]

        self._listeners_registered = True

    def get_slow_queries(self, threshold_ms: float = 100) -> list[SQLQuery]:
        """
        Get queries slower than threshold.

        Args:
            threshold_ms: Threshold in milliseconds

        Returns:
            List of slow queries
        """
        return [q for q in self.items if q.duration_ms and q.duration_ms > threshold_ms]

    def get_failed_queries(self) -> list[SQLQuery]:
        """
        Get failed queries.

        Returns:
            List of failed queries
        """
        return [q for q in self.items if q.error]

    def get_query_stats(self) -> dict[str, Any]:
        """
        Get query statistics.

        Returns:
            Dictionary with query statistics
        """
        if not self.items:
            return {
                "total_queries": 0,
                "avg_duration_ms": 0,
                "max_duration_ms": 0,
                "min_duration_ms": 0,
                "failed_queries": 0,
            }

        durations = [q.duration_ms for q in self.items if q.duration_ms]
        return {
            "total_queries": len(self.items),
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "failed_queries": len(self.get_failed_queries()),
        }


class RequestCollector(MetricCollector):
    """
    HTTP request collector.

    Captures metrics for all HTTP requests.
    """

    def __init__(self, enabled: bool = True, max_requests: int = 10000) -> None:
        """
        Initialize request collector.

        Args:
            enabled: Whether collection is enabled
            max_requests: Maximum number of requests to store
        """
        super().__init__(enabled=enabled, max_items=max_requests)
        self.active_requests: dict[str, RequestMetrics] = {}

    def start_request(
        self,
        request_id: str,
        method: str,
        path: str,
        request_size_bytes: int = 0,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Start tracking a request.

        Args:
            request_id: Unique request ID
            method: HTTP method
            path: Request path
            request_size_bytes: Size of request body
            user_id: User making the request
            metadata: Additional metadata

        Returns:
            Request ID
        """
        if not self.enabled:
            return request_id

        metrics = RequestMetrics(
            request_id=request_id,
            method=method,
            path=path,
            status_code=None,
            start_time=datetime.utcnow(),
            end_time=None,
            duration_ms=None,
            request_size_bytes=request_size_bytes,
            response_size_bytes=None,
            user_id=user_id,
            metadata=metadata or {},
        )
        self.active_requests[request_id] = metrics
        return request_id

    def end_request(
        self,
        request_id: str,
        status_code: int,
        response_size_bytes: int = 0,
    ) -> None:
        """
        Finish tracking a request.

        Args:
            request_id: Request ID
            status_code: HTTP status code
            response_size_bytes: Size of response body
        """
        if not self.enabled or request_id not in self.active_requests:
            return

        metrics = self.active_requests[request_id]
        metrics.end_time = datetime.utcnow()
        metrics.duration_ms = (
            metrics.end_time - metrics.start_time
        ).total_seconds() * 1000
        metrics.status_code = status_code
        metrics.response_size_bytes = response_size_bytes

        self.add_item(metrics)
        del self.active_requests[request_id]

    def get_slow_requests(self, threshold_ms: float = 1000) -> list[RequestMetrics]:
        """
        Get requests slower than threshold.

        Args:
            threshold_ms: Threshold in milliseconds

        Returns:
            List of slow requests
        """
        return [r for r in self.items if r.duration_ms and r.duration_ms > threshold_ms]

    def get_failed_requests(self) -> list[RequestMetrics]:
        """
        Get failed requests (4xx, 5xx status codes).

        Returns:
            List of failed requests
        """
        return [r for r in self.items if r.status_code and r.status_code >= 400]

    def get_request_stats(self) -> dict[str, Any]:
        """
        Get request statistics.

        Returns:
            Dictionary with request statistics
        """
        if not self.items:
            return {
                "total_requests": 0,
                "avg_duration_ms": 0,
                "max_duration_ms": 0,
                "min_duration_ms": 0,
                "failed_requests": 0,
                "status_codes": {},
            }

        durations = [r.duration_ms for r in self.items if r.duration_ms]
        status_codes = defaultdict(int)
        for r in self.items:
            if r.status_code:
                status_codes[r.status_code] += 1

        return {
            "total_requests": len(self.items),
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "failed_requests": len(self.get_failed_requests()),
            "status_codes": dict(status_codes),
        }


class TraceCollector(MetricCollector):
    """
    Distributed trace collector.

    Captures distributed traces for request flows.
    """

    def __init__(self, enabled: bool = True, max_traces: int = 10000) -> None:
        """
        Initialize trace collector.

        Args:
            enabled: Whether collection is enabled
            max_traces: Maximum number of traces to store
        """
        super().__init__(enabled=enabled, max_items=max_traces)
        self.active_traces: dict[str, Trace] = {}

    def start_span(
        self,
        operation_name: str,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        tags: dict[str, Any] | None = None,
    ) -> str:
        """
        Start a new trace span.

        Args:
            operation_name: Name of the operation
            trace_id: Trace ID (generated if not provided)
            parent_span_id: Parent span ID
            tags: Additional tags

        Returns:
            Span ID
        """
        if not self.enabled:
            return str(uuid4())

        span_id = str(uuid4())
        trace_id = trace_id or str(uuid4())

        trace = Trace(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=datetime.utcnow(),
            end_time=None,
            duration_ms=None,
            tags=tags or {},
            logs=[],
        )
        self.active_traces[span_id] = trace
        return span_id

    def end_span(self, span_id: str) -> None:
        """
        End a trace span.

        Args:
            span_id: Span ID
        """
        if not self.enabled or span_id not in self.active_traces:
            return

        trace = self.active_traces[span_id]
        trace.end_time = datetime.utcnow()
        trace.duration_ms = (trace.end_time - trace.start_time).total_seconds() * 1000

        self.add_item(trace)
        del self.active_traces[span_id]

    def add_log(
        self, span_id: str, message: str, fields: dict[str, Any] | None = None
    ) -> None:
        """
        Add a log entry to a span.

        Args:
            span_id: Span ID
            message: Log message
            fields: Additional fields
        """
        if not self.enabled or span_id not in self.active_traces:
            return

        trace = self.active_traces[span_id]
        trace.logs.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "message": message,
                "fields": fields or {},
            }
        )

    def get_trace_by_id(self, trace_id: str) -> list[Trace]:
        """
        Get all spans for a trace.

        Args:
            trace_id: Trace ID

        Returns:
            List of trace spans
        """
        return [t for t in self.items if t.trace_id == trace_id]

    def get_slow_traces(self, threshold_ms: float = 1000) -> list[Trace]:
        """
        Get traces slower than threshold.

        Args:
            threshold_ms: Threshold in milliseconds

        Returns:
            List of slow traces
        """
        return [t for t in self.items if t.duration_ms and t.duration_ms > threshold_ms]
