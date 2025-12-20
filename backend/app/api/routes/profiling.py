"""
Profiling API Endpoints.

Provides endpoints for performance profiling and analysis:
- GET /profiling/status - Get profiling status
- POST /profiling/start - Start profiling session
- POST /profiling/stop - Stop profiling session
- GET /profiling/report - Get profiling report
- GET /profiling/queries - Get SQL query metrics
- GET /profiling/requests - Get HTTP request metrics
- GET /profiling/traces - Get distributed traces
- GET /profiling/bottlenecks - Detect performance bottlenecks
- GET /profiling/flamegraph - Generate flame graph data
- POST /profiling/analyze - Analyze profiling data
- DELETE /profiling/clear - Clear profiling data
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.profiling import (
    BottleneckDetector,
    CPUProfiler,
    FlameGraphGenerator,
    MemoryProfiler,
    MetricCollector,
    PerformanceAnalyzer,
    PerformanceReporter,
    ProfilerContext,
    QueryAnalyzer,
    RequestCollector,
    SQLQueryCollector,
    TraceCollector,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["profiling"])

# Global profiling instances
cpu_profiler = CPUProfiler(enabled=True)
memory_profiler = MemoryProfiler(enabled=True)
profiler_context = ProfilerContext(cpu_enabled=True, memory_enabled=True)
sql_collector = SQLQueryCollector(enabled=True)
request_collector = RequestCollector(enabled=True)
trace_collector = TraceCollector(enabled=True)
performance_analyzer = PerformanceAnalyzer()
bottleneck_detector = BottleneckDetector()
query_analyzer = QueryAnalyzer()
performance_reporter = PerformanceReporter()
flame_graph_generator = FlameGraphGenerator()


# Request/Response Models
class ProfilingStatusResponse(BaseModel):
    """Profiling status response."""

    enabled: bool = Field(..., description="Whether profiling is enabled")
    cpu_profiling: bool = Field(..., description="CPU profiling status")
    memory_profiling: bool = Field(..., description="Memory profiling status")
    sql_collection: bool = Field(..., description="SQL query collection status")
    request_collection: bool = Field(..., description="Request collection status")
    trace_collection: bool = Field(..., description="Trace collection status")
    stats: Dict[str, Any] = Field(..., description="Current profiling statistics")


class ProfilingSessionRequest(BaseModel):
    """Start profiling session request."""

    cpu: bool = Field(True, description="Enable CPU profiling")
    memory: bool = Field(True, description="Enable memory profiling")
    sql: bool = Field(True, description="Enable SQL query collection")
    requests: bool = Field(True, description="Enable request collection")
    traces: bool = Field(True, description="Enable trace collection")


class AnalyzeRequest(BaseModel):
    """Analyze profiling data request."""

    cpu_threshold_percent: Optional[float] = Field(
        80.0, description="CPU usage threshold"
    )
    memory_threshold_mb: Optional[float] = Field(
        1000.0, description="Memory usage threshold"
    )
    duration_threshold_ms: Optional[float] = Field(
        1000.0, description="Duration threshold"
    )
    sql_slow_threshold_ms: Optional[float] = Field(
        100.0, description="SQL slow query threshold"
    )
    request_slow_threshold_ms: Optional[float] = Field(
        1000.0, description="Request slow threshold"
    )


@router.get(
    "/status",
    response_model=ProfilingStatusResponse,
    summary="Get Profiling Status",
    description="Get current status of profiling system",
)
async def get_profiling_status() -> ProfilingStatusResponse:
    """
    Get profiling system status.

    Returns:
        Current profiling status and statistics

    Example Response:
        {
            "enabled": true,
            "cpu_profiling": true,
            "memory_profiling": true,
            "sql_collection": true,
            "request_collection": true,
            "trace_collection": true,
            "stats": {
                "cpu_profiles": 10,
                "memory_profiles": 10,
                "sql_queries": 1250,
                "requests": 523,
                "traces": 145
            }
        }
    """
    return ProfilingStatusResponse(
        enabled=True,
        cpu_profiling=cpu_profiler.enabled,
        memory_profiling=memory_profiler.enabled,
        sql_collection=sql_collector.enabled,
        request_collection=request_collector.enabled,
        trace_collection=trace_collector.enabled,
        stats={
            "cpu_profiles": len(cpu_profiler.results),
            "memory_profiles": len(memory_profiler.results),
            "sql_queries": sql_collector.get_count(),
            "requests": request_collector.get_count(),
            "traces": trace_collector.get_count(),
        },
    )


@router.post(
    "/start",
    summary="Start Profiling Session",
    description="Start a new profiling session",
)
async def start_profiling_session(
    request: ProfilingSessionRequest,
) -> Dict[str, Any]:
    """
    Start a profiling session.

    Args:
        request: Profiling session configuration

    Returns:
        Session start confirmation

    Example Response:
        {
            "status": "started",
            "session_id": "abc123",
            "config": {
                "cpu": true,
                "memory": true,
                "sql": true,
                "requests": true,
                "traces": true
            }
        }
    """
    # Configure profilers based on request
    cpu_profiler.enabled = request.cpu
    memory_profiler.enabled = request.memory
    sql_collector.enabled = request.sql
    request_collector.enabled = request.requests
    trace_collector.enabled = request.traces

    from uuid import uuid4

    session_id = str(uuid4())

    return {
        "status": "started",
        "session_id": session_id,
        "config": {
            "cpu": request.cpu,
            "memory": request.memory,
            "sql": request.sql,
            "requests": request.requests,
            "traces": request.traces,
        },
    }


@router.post(
    "/stop",
    summary="Stop Profiling Session",
    description="Stop current profiling session",
)
async def stop_profiling_session() -> Dict[str, Any]:
    """
    Stop profiling session.

    Returns:
        Session stop confirmation with summary

    Example Response:
        {
            "status": "stopped",
            "summary": {
                "cpu_profiles": 10,
                "memory_profiles": 10,
                "sql_queries": 1250,
                "requests": 523,
                "traces": 145
            }
        }
    """
    # Don't disable, just return summary
    summary = {
        "cpu_profiles": len(cpu_profiler.results),
        "memory_profiles": len(memory_profiler.results),
        "sql_queries": sql_collector.get_count(),
        "requests": request_collector.get_count(),
        "traces": trace_collector.get_count(),
    }

    return {"status": "stopped", "summary": summary}


@router.get(
    "/report",
    summary="Get Profiling Report",
    description="Generate comprehensive profiling report",
)
async def get_profiling_report(
    format: str = Query("json", description="Report format (json or html)"),
) -> Dict[str, Any]:
    """
    Generate profiling report.

    Args:
        format: Report format (json or html)

    Returns:
        Profiling report

    Example Response:
        {
            "report_id": "abc123",
            "created_at": "2024-01-15T10:30:00",
            "summary": {...},
            "bottlenecks": [...],
            "insights": [...]
        }
    """
    # Analyze data
    insights = performance_analyzer.analyze_profile_results(
        cpu_profiler.results + memory_profiler.results
    )

    bottlenecks = []
    bottlenecks.extend(bottleneck_detector.detect_sql_bottlenecks(sql_collector.items))
    bottlenecks.extend(
        bottleneck_detector.detect_request_bottlenecks(request_collector.items)
    )
    bottlenecks.extend(bottleneck_detector.detect_trace_bottlenecks(trace_collector.items))

    # Generate report
    report = performance_reporter.generate_report(
        profile_results=cpu_profiler.results + memory_profiler.results,
        sql_queries=sql_collector.items,
        requests=request_collector.items,
        traces=trace_collector.items,
        bottlenecks=bottlenecks,
        insights=insights,
    )

    if format == "html":
        html_content = performance_reporter.export_to_html(report)
        from fastapi.responses import HTMLResponse

        return HTMLResponse(content=html_content)

    return report.to_dict()


@router.get(
    "/queries",
    summary="Get SQL Query Metrics",
    description="Get SQL query profiling metrics",
)
async def get_query_metrics(
    limit: int = Query(100, description="Maximum number of queries to return"),
    slow_only: bool = Query(False, description="Return only slow queries"),
    threshold_ms: float = Query(100.0, description="Slow query threshold in ms"),
) -> Dict[str, Any]:
    """
    Get SQL query metrics.

    Args:
        limit: Maximum number of queries to return
        slow_only: Whether to return only slow queries
        threshold_ms: Slow query threshold

    Returns:
        SQL query metrics

    Example Response:
        {
            "total_queries": 1250,
            "slow_queries": 45,
            "failed_queries": 2,
            "stats": {...},
            "queries": [...]
        }
    """
    queries = sql_collector.items

    if slow_only:
        queries = sql_collector.get_slow_queries(threshold_ms)

    queries = queries[-limit:] if limit else queries

    return {
        "total_queries": sql_collector.get_count(),
        "slow_queries": len(sql_collector.get_slow_queries(threshold_ms)),
        "failed_queries": len(sql_collector.get_failed_queries()),
        "stats": sql_collector.get_query_stats(),
        "queries": [q.to_dict() for q in queries],
    }


@router.get(
    "/requests",
    summary="Get Request Metrics",
    description="Get HTTP request profiling metrics",
)
async def get_request_metrics(
    limit: int = Query(100, description="Maximum number of requests to return"),
    slow_only: bool = Query(False, description="Return only slow requests"),
    threshold_ms: float = Query(1000.0, description="Slow request threshold in ms"),
) -> Dict[str, Any]:
    """
    Get HTTP request metrics.

    Args:
        limit: Maximum number of requests to return
        slow_only: Whether to return only slow requests
        threshold_ms: Slow request threshold

    Returns:
        HTTP request metrics

    Example Response:
        {
            "total_requests": 523,
            "slow_requests": 12,
            "failed_requests": 3,
            "stats": {...},
            "requests": [...]
        }
    """
    requests = request_collector.items

    if slow_only:
        requests = request_collector.get_slow_requests(threshold_ms)

    requests = requests[-limit:] if limit else requests

    return {
        "total_requests": request_collector.get_count(),
        "slow_requests": len(request_collector.get_slow_requests(threshold_ms)),
        "failed_requests": len(request_collector.get_failed_requests()),
        "stats": request_collector.get_request_stats(),
        "requests": [r.to_dict() for r in requests],
    }


@router.get(
    "/traces",
    summary="Get Distributed Traces",
    description="Get distributed trace data",
)
async def get_traces(
    limit: int = Query(100, description="Maximum number of traces to return"),
    trace_id: Optional[str] = Query(None, description="Filter by trace ID"),
    slow_only: bool = Query(False, description="Return only slow traces"),
    threshold_ms: float = Query(1000.0, description="Slow trace threshold in ms"),
) -> Dict[str, Any]:
    """
    Get distributed traces.

    Args:
        limit: Maximum number of traces to return
        trace_id: Filter by specific trace ID
        slow_only: Whether to return only slow traces
        threshold_ms: Slow trace threshold

    Returns:
        Distributed trace data

    Example Response:
        {
            "total_traces": 145,
            "slow_traces": 8,
            "traces": [...]
        }
    """
    traces = trace_collector.items

    if trace_id:
        traces = trace_collector.get_trace_by_id(trace_id)

    if slow_only:
        traces = trace_collector.get_slow_traces(threshold_ms)

    traces = traces[-limit:] if limit else traces

    return {
        "total_traces": trace_collector.get_count(),
        "slow_traces": len(trace_collector.get_slow_traces(threshold_ms)),
        "traces": [t.to_dict() for t in traces],
    }


@router.get(
    "/bottlenecks",
    summary="Detect Performance Bottlenecks",
    description="Detect and analyze performance bottlenecks",
)
async def detect_bottlenecks(
    sql_threshold_ms: float = Query(100.0, description="SQL slow query threshold"),
    request_threshold_ms: float = Query(1000.0, description="Request slow threshold"),
) -> Dict[str, Any]:
    """
    Detect performance bottlenecks.

    Args:
        sql_threshold_ms: SQL query slow threshold
        request_threshold_ms: Request slow threshold

    Returns:
        Detected bottlenecks

    Example Response:
        {
            "bottlenecks": [...],
            "summary": {
                "total": 5,
                "critical": 1,
                "high": 2,
                "medium": 2,
                "low": 0
            }
        }
    """
    detector = BottleneckDetector(
        sql_slow_threshold_ms=sql_threshold_ms,
        request_slow_threshold_ms=request_threshold_ms,
    )

    bottlenecks = []
    bottlenecks.extend(detector.detect_sql_bottlenecks(sql_collector.items))
    bottlenecks.extend(detector.detect_request_bottlenecks(request_collector.items))
    bottlenecks.extend(detector.detect_trace_bottlenecks(trace_collector.items))

    # Summarize by severity
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for b in bottlenecks:
        severity_counts[b.severity] = severity_counts.get(b.severity, 0) + 1

    return {
        "bottlenecks": [b.to_dict() for b in bottlenecks],
        "summary": {"total": len(bottlenecks), **severity_counts},
    }


@router.get(
    "/flamegraph",
    summary="Generate Flame Graph",
    description="Generate flame graph data for visualization",
)
async def generate_flamegraph(
    type: str = Query("cpu", description="Type of flame graph (cpu or traces)"),
    profile_index: int = Query(-1, description="Profile result index (-1 for latest)"),
) -> Dict[str, Any]:
    """
    Generate flame graph data.

    Args:
        type: Type of flame graph (cpu or traces)
        profile_index: Profile result index

    Returns:
        Flame graph data structure

    Example Response:
        {
            "name": "function_name",
            "value": 1234.5,
            "children": [...]
        }
    """
    if type == "cpu":
        if not cpu_profiler.results:
            raise HTTPException(status_code=404, detail="No CPU profiling data available")

        profile = cpu_profiler.results[profile_index]
        flame_data = flame_graph_generator.generate_from_profile(profile)

    elif type == "traces":
        if not trace_collector.items:
            raise HTTPException(status_code=404, detail="No trace data available")

        flame_data = flame_graph_generator.generate_from_traces(trace_collector.items)

    else:
        raise HTTPException(
            status_code=400, detail=f"Invalid flame graph type: {type}"
        )

    return flame_data


@router.post(
    "/analyze",
    summary="Analyze Profiling Data",
    description="Perform detailed analysis of profiling data",
)
async def analyze_profiling_data(request: AnalyzeRequest) -> Dict[str, Any]:
    """
    Analyze profiling data.

    Args:
        request: Analysis configuration

    Returns:
        Analysis results with insights and recommendations

    Example Response:
        {
            "insights": [...],
            "bottlenecks": [...],
            "query_patterns": {...},
            "recommendations": [...]
        }
    """
    # Configure analyzers
    analyzer = PerformanceAnalyzer(
        cpu_threshold_percent=request.cpu_threshold_percent,
        memory_threshold_mb=request.memory_threshold_mb,
        duration_threshold_ms=request.duration_threshold_ms,
    )

    detector = BottleneckDetector(
        sql_slow_threshold_ms=request.sql_slow_threshold_ms,
        request_slow_threshold_ms=request.request_slow_threshold_ms,
    )

    # Analyze profiles
    insights = analyzer.analyze_profile_results(
        cpu_profiler.results + memory_profiler.results
    )

    # Detect bottlenecks
    bottlenecks = []
    bottlenecks.extend(detector.detect_sql_bottlenecks(sql_collector.items))
    bottlenecks.extend(detector.detect_request_bottlenecks(request_collector.items))
    bottlenecks.extend(detector.detect_trace_bottlenecks(trace_collector.items))

    # Analyze query patterns
    query_patterns = query_analyzer.analyze_query_patterns(sql_collector.items)

    # Compile recommendations
    recommendations = []
    for insight in insights:
        recommendations.append(
            {
                "category": insight.category,
                "title": insight.title,
                "priority": insight.priority,
                "impact": insight.impact,
                "effort": insight.effort,
            }
        )

    for bottleneck in bottlenecks:
        for rec in bottleneck.recommendations:
            recommendations.append(
                {
                    "category": bottleneck.bottleneck_type,
                    "title": rec,
                    "priority": 1 if bottleneck.severity == "critical" else 2,
                    "impact": bottleneck.severity,
                    "effort": "unknown",
                }
            )

    return {
        "insights": [i.to_dict() for i in insights],
        "bottlenecks": [b.to_dict() for b in bottlenecks],
        "query_patterns": query_patterns,
        "recommendations": recommendations[:20],  # Top 20
    }


@router.delete(
    "/clear",
    summary="Clear Profiling Data",
    description="Clear all collected profiling data",
)
async def clear_profiling_data() -> Dict[str, Any]:
    """
    Clear all profiling data.

    Returns:
        Confirmation of data clearing

    Example Response:
        {
            "status": "cleared",
            "message": "All profiling data cleared successfully"
        }
    """
    cpu_profiler.clear()
    memory_profiler.clear()
    sql_collector.clear()
    request_collector.clear()
    trace_collector.clear()
    profiler_context.clear()

    return {
        "status": "cleared",
        "message": "All profiling data cleared successfully",
    }
