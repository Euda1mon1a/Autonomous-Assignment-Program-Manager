"""
Performance analyzers for detecting bottlenecks and analyzing metrics.

Provides tools to analyze profiling data and identify performance issues.
"""

import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from app.profiling.collectors import RequestMetrics, SQLQuery, Trace
from app.profiling.profiler import ProfileResult


@dataclass
class Bottleneck:
    """Represents a detected performance bottleneck."""

    bottleneck_type: str  # "cpu", "memory", "sql", "request", "trace"
    severity: str  # "low", "medium", "high", "critical"
    description: str
    affected_items: list[str]
    metrics: dict[str, Any]
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "bottleneck_type": self.bottleneck_type,
            "severity": self.severity,
            "description": self.description,
            "affected_items": self.affected_items,
            "metrics": self.metrics,
            "recommendations": self.recommendations,
        }


@dataclass
class PerformanceInsight:
    """Represents a performance insight or recommendation."""

    category: str
    title: str
    description: str
    priority: int  # 1 (highest) to 5 (lowest)
    impact: str  # "low", "medium", "high"
    effort: str  # "low", "medium", "high"
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "impact": self.impact,
            "effort": self.effort,
            "details": self.details,
        }


class PerformanceAnalyzer:
    """
    Analyzes performance data to identify issues and opportunities.

    Examines profiling results, metrics, and traces to provide insights.
    """

    def __init__(
        self,
        cpu_threshold_percent: float = 80.0,
        memory_threshold_mb: float = 1000.0,
        duration_threshold_ms: float = 1000.0,
    ):
        """
        Initialize performance analyzer.

        Args:
            cpu_threshold_percent: CPU usage threshold for alerts
            memory_threshold_mb: Memory usage threshold for alerts
            duration_threshold_ms: Duration threshold for slow operations
        """
        self.cpu_threshold = cpu_threshold_percent
        self.memory_threshold = memory_threshold_mb
        self.duration_threshold = duration_threshold_ms

    def analyze_profile_results(
        self, results: list[ProfileResult]
    ) -> list[PerformanceInsight]:
        """
        Analyze profiling results for insights.

        Args:
            results: List of profile results

        Returns:
            List of performance insights
        """
        if not results:
            return []

        insights = []

        # Analyze CPU usage
        cpu_percentages = [r.cpu_percent for r in results]
        avg_cpu = statistics.mean(cpu_percentages)
        max_cpu = max(cpu_percentages)

        if max_cpu > self.cpu_threshold:
            insights.append(
                PerformanceInsight(
                    category="cpu",
                    title="High CPU Usage Detected",
                    description=f"Peak CPU usage of {max_cpu:.1f}% exceeds threshold",
                    priority=2,
                    impact="high",
                    effort="medium",
                    details={
                        "avg_cpu_percent": avg_cpu,
                        "max_cpu_percent": max_cpu,
                        "threshold": self.cpu_threshold,
                        "affected_functions": [
                            r.function_name
                            for r in results
                            if r.cpu_percent > self.cpu_threshold
                        ],
                    },
                )
            )

        # Analyze memory usage
        memory_usage = [r.memory_peak_mb for r in results]
        avg_memory = statistics.mean(memory_usage)
        max_memory = max(memory_usage)

        if max_memory > self.memory_threshold:
            insights.append(
                PerformanceInsight(
                    category="memory",
                    title="High Memory Usage Detected",
                    description=f"Peak memory usage of {max_memory:.1f}MB exceeds threshold",
                    priority=2,
                    impact="high",
                    effort="medium",
                    details={
                        "avg_memory_mb": avg_memory,
                        "max_memory_mb": max_memory,
                        "threshold": self.memory_threshold,
                        "affected_functions": [
                            r.function_name
                            for r in results
                            if r.memory_peak_mb > self.memory_threshold
                        ],
                    },
                )
            )

        # Analyze execution time
        durations = [r.duration_seconds * 1000 for r in results]
        avg_duration = statistics.mean(durations)
        max_duration = max(durations)

        if max_duration > self.duration_threshold:
            insights.append(
                PerformanceInsight(
                    category="performance",
                    title="Slow Function Execution",
                    description=f"Maximum execution time of {max_duration:.1f}ms exceeds threshold",
                    priority=3,
                    impact="medium",
                    effort="medium",
                    details={
                        "avg_duration_ms": avg_duration,
                        "max_duration_ms": max_duration,
                        "threshold": self.duration_threshold,
                        "slow_functions": [
                            {
                                "name": r.function_name,
                                "duration_ms": r.duration_seconds * 1000,
                            }
                            for r in results
                            if r.duration_seconds * 1000 > self.duration_threshold
                        ],
                    },
                )
            )

        return insights

    def compare_profiles(
        self, baseline: list[ProfileResult], current: list[ProfileResult]
    ) -> dict[str, Any]:
        """
        Compare two sets of profile results.

        Args:
            baseline: Baseline profiling results
            current: Current profiling results

        Returns:
            Comparison metrics
        """
        if not baseline or not current:
            return {}

        baseline_avg_cpu = statistics.mean([r.cpu_percent for r in baseline])
        current_avg_cpu = statistics.mean([r.cpu_percent for r in current])

        baseline_avg_memory = statistics.mean([r.memory_peak_mb for r in baseline])
        current_avg_memory = statistics.mean([r.memory_peak_mb for r in current])

        baseline_avg_duration = statistics.mean(
            [r.duration_seconds * 1000 for r in baseline]
        )
        current_avg_duration = statistics.mean(
            [r.duration_seconds * 1000 for r in current]
        )

        return {
            "cpu_change_percent": (
                ((current_avg_cpu - baseline_avg_cpu) / baseline_avg_cpu * 100)
                if baseline_avg_cpu > 0
                else 0
            ),
            "memory_change_percent": (
                ((current_avg_memory - baseline_avg_memory) / baseline_avg_memory * 100)
                if baseline_avg_memory > 0
                else 0
            ),
            "duration_change_percent": (
                (
                    (current_avg_duration - baseline_avg_duration)
                    / baseline_avg_duration
                    * 100
                )
                if baseline_avg_duration > 0
                else 0
            ),
            "baseline": {
                "avg_cpu_percent": baseline_avg_cpu,
                "avg_memory_mb": baseline_avg_memory,
                "avg_duration_ms": baseline_avg_duration,
            },
            "current": {
                "avg_cpu_percent": current_avg_cpu,
                "avg_memory_mb": current_avg_memory,
                "avg_duration_ms": current_avg_duration,
            },
        }


class BottleneckDetector:
    """
    Detects performance bottlenecks in various metrics.

    Analyzes SQL queries, requests, and traces to identify issues.
    """

    def __init__(
        self,
        sql_slow_threshold_ms: float = 100.0,
        request_slow_threshold_ms: float = 1000.0,
        n_plus_one_threshold: int = 10,
    ):
        """
        Initialize bottleneck detector.

        Args:
            sql_slow_threshold_ms: Threshold for slow SQL queries
            request_slow_threshold_ms: Threshold for slow requests
            n_plus_one_threshold: Threshold for detecting N+1 queries
        """
        self.sql_slow_threshold = sql_slow_threshold_ms
        self.request_slow_threshold = request_slow_threshold_ms
        self.n_plus_one_threshold = n_plus_one_threshold

    def detect_sql_bottlenecks(self, queries: list[SQLQuery]) -> list[Bottleneck]:
        """
        Detect SQL-related bottlenecks.

        Args:
            queries: List of SQL queries

        Returns:
            List of detected bottlenecks
        """
        bottlenecks = []

        if not queries:
            return bottlenecks

        # Detect slow queries
        slow_queries = [
            q
            for q in queries
            if q.duration_ms and q.duration_ms > self.sql_slow_threshold
        ]

        if slow_queries:
            avg_duration = statistics.mean([q.duration_ms for q in slow_queries])
            bottlenecks.append(
                Bottleneck(
                    bottleneck_type="sql",
                    severity="high" if avg_duration > 500 else "medium",
                    description=f"Found {len(slow_queries)} slow SQL queries",
                    affected_items=[q.query_id for q in slow_queries[:10]],
                    metrics={
                        "count": len(slow_queries),
                        "avg_duration_ms": avg_duration,
                        "max_duration_ms": max(q.duration_ms for q in slow_queries),
                    },
                    recommendations=[
                        "Add database indexes for frequently queried columns",
                        "Optimize query joins and conditions",
                        "Consider query result caching",
                        "Review query execution plans",
                    ],
                )
            )

        # Detect N+1 queries
        query_patterns = defaultdict(list)
        for query in queries:
            # Normalize SQL to detect patterns
            normalized = self._normalize_sql(query.sql)
            query_patterns[normalized].append(query)

        for pattern, pattern_queries in query_patterns.items():
            if len(pattern_queries) > self.n_plus_one_threshold:
                bottlenecks.append(
                    Bottleneck(
                        bottleneck_type="sql",
                        severity="critical",
                        description=f"Potential N+1 query detected: {len(pattern_queries)} similar queries",
                        affected_items=[q.query_id for q in pattern_queries[:10]],
                        metrics={
                            "count": len(pattern_queries),
                            "pattern": pattern[:100],
                        },
                        recommendations=[
                            "Use eager loading with joinedload or selectinload",
                            "Batch queries using in_ clauses",
                            "Consider using a single query with joins",
                        ],
                    )
                )

        # Detect missing indexes
        full_scan_keywords = ["FULL SCAN", "TABLE SCAN", "ALL ROWS"]
        potential_missing_indexes = [
            q
            for q in queries
            if any(keyword in q.sql.upper() for keyword in full_scan_keywords)
        ]

        if potential_missing_indexes:
            bottlenecks.append(
                Bottleneck(
                    bottleneck_type="sql",
                    severity="high",
                    description=f"Found {len(potential_missing_indexes)} queries with potential full table scans",
                    affected_items=[q.query_id for q in potential_missing_indexes[:10]],
                    metrics={"count": len(potential_missing_indexes)},
                    recommendations=[
                        "Add appropriate database indexes",
                        "Review query WHERE clauses",
                        "Consider composite indexes for multi-column filters",
                    ],
                )
            )

        return bottlenecks

    def detect_request_bottlenecks(
        self, requests: list[RequestMetrics]
    ) -> list[Bottleneck]:
        """
        Detect request-related bottlenecks.

        Args:
            requests: List of request metrics

        Returns:
            List of detected bottlenecks
        """
        bottlenecks = []

        if not requests:
            return bottlenecks

        # Detect slow requests
        slow_requests = [
            r
            for r in requests
            if r.duration_ms and r.duration_ms > self.request_slow_threshold
        ]

        if slow_requests:
            avg_duration = statistics.mean([r.duration_ms for r in slow_requests])
            bottlenecks.append(
                Bottleneck(
                    bottleneck_type="request",
                    severity="high" if avg_duration > 3000 else "medium",
                    description=f"Found {len(slow_requests)} slow HTTP requests",
                    affected_items=[f"{r.method} {r.path}" for r in slow_requests[:10]],
                    metrics={
                        "count": len(slow_requests),
                        "avg_duration_ms": avg_duration,
                        "max_duration_ms": max(r.duration_ms for r in slow_requests),
                    },
                    recommendations=[
                        "Implement caching for frequently accessed data",
                        "Optimize database queries",
                        "Consider async processing for long operations",
                        "Review third-party API calls",
                    ],
                )
            )

        # Detect high error rates
        failed_requests = [
            r for r in requests if r.status_code and r.status_code >= 500
        ]

        if failed_requests:
            error_rate = len(failed_requests) / len(requests) * 100
            severity = (
                "critical" if error_rate > 5 else "high" if error_rate > 1 else "medium"
            )

            bottlenecks.append(
                Bottleneck(
                    bottleneck_type="request",
                    severity=severity,
                    description=f"High error rate: {error_rate:.1f}% of requests failed",
                    affected_items=[
                        f"{r.method} {r.path}" for r in failed_requests[:10]
                    ],
                    metrics={
                        "error_count": len(failed_requests),
                        "error_rate_percent": error_rate,
                        "total_requests": len(requests),
                    },
                    recommendations=[
                        "Review server logs for error details",
                        "Improve error handling and recovery",
                        "Add monitoring and alerting",
                        "Consider circuit breakers for external dependencies",
                    ],
                )
            )

        return bottlenecks

    def detect_trace_bottlenecks(self, traces: list[Trace]) -> list[Bottleneck]:
        """
        Detect trace-related bottlenecks.

        Args:
            traces: List of traces

        Returns:
            List of detected bottlenecks
        """
        bottlenecks = []

        if not traces:
            return bottlenecks

        # Group traces by trace_id
        trace_groups = defaultdict(list)
        for trace in traces:
            trace_groups[trace.trace_id].append(trace)

        # Detect long trace chains
        for trace_id, spans in trace_groups.items():
            total_duration = sum(
                s.duration_ms for s in spans if s.duration_ms is not None
            )

            if total_duration > self.request_slow_threshold * 2:
                bottlenecks.append(
                    Bottleneck(
                        bottleneck_type="trace",
                        severity="high",
                        description=f"Long trace chain: {total_duration:.1f}ms total duration",
                        affected_items=[trace_id],
                        metrics={
                            "total_duration_ms": total_duration,
                            "span_count": len(spans),
                            "operations": [s.operation_name for s in spans],
                        },
                        recommendations=[
                            "Review operation dependencies",
                            "Consider parallel execution where possible",
                            "Optimize individual operations",
                        ],
                    )
                )

        return bottlenecks

    def _normalize_sql(self, sql: str) -> str:
        """
        Normalize SQL query for pattern detection.

        Args:
            sql: SQL query string

        Returns:
            Normalized SQL string
        """
        import re

        # Remove parameter values
        normalized = re.sub(r"'[^']*'", "?", sql)
        normalized = re.sub(r"\b\d+\b", "?", normalized)

        # Normalize whitespace
        normalized = " ".join(normalized.split())

        return normalized


class QueryAnalyzer:
    """
    Analyzes SQL queries for optimization opportunities.

    Provides detailed analysis of query patterns and performance.
    """

    def analyze_query_patterns(self, queries: list[SQLQuery]) -> dict[str, Any]:
        """
        Analyze query patterns and statistics.

        Args:
            queries: List of SQL queries

        Returns:
            Dictionary with query analysis
        """
        if not queries:
            return {}

        # Group by query pattern
        patterns = defaultdict(list)
        for query in queries:
            normalized = self._normalize_sql(query.sql)
            patterns[normalized].append(query)

        # Calculate statistics per pattern
        pattern_stats = []
        for pattern, pattern_queries in patterns.items():
            durations = [q.duration_ms for q in pattern_queries if q.duration_ms]

            pattern_stats.append(
                {
                    "pattern": pattern[:200],
                    "count": len(pattern_queries),
                    "avg_duration_ms": (statistics.mean(durations) if durations else 0),
                    "max_duration_ms": max(durations) if durations else 0,
                    "total_duration_ms": sum(durations) if durations else 0,
                }
            )

        # Sort by total duration
        pattern_stats.sort(key=lambda x: x["total_duration_ms"], reverse=True)

        return {
            "total_queries": len(queries),
            "unique_patterns": len(patterns),
            "top_patterns": pattern_stats[:10],
        }

    def _normalize_sql(self, sql: str) -> str:
        """
        Normalize SQL query for pattern detection.

        Args:
            sql: SQL query string

        Returns:
            Normalized SQL string
        """
        import re

        # Remove parameter values
        normalized = re.sub(r"'[^']*'", "?", sql)
        normalized = re.sub(r"\b\d+\b", "?", normalized)

        # Normalize whitespace
        normalized = " ".join(normalized.split())

        return normalized
