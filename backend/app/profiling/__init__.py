"""
Performance profiling utilities for the Residency Scheduler application.

This package provides comprehensive performance profiling capabilities including:
- CPU profiling
- Memory profiling
- SQL query profiling
- Request tracing
- Flame graph generation
- Bottleneck detection
- Performance reporting
"""

from app.profiling.profiler import (
    CPUProfiler,
    MemoryProfiler,
    ProfilerContext,
    profile_async,
    profile_sync,
)
from app.profiling.collectors import (
    MetricCollector,
    SQLQueryCollector,
    RequestCollector,
    TraceCollector,
)
from app.profiling.analyzers import (
    PerformanceAnalyzer,
    BottleneckDetector,
    QueryAnalyzer,
)
from app.profiling.reporters import (
    PerformanceReporter,
    FlameGraphGenerator,
    ProfileReport,
)

__all__ = [
    # Profilers
    "CPUProfiler",
    "MemoryProfiler",
    "ProfilerContext",
    "profile_async",
    "profile_sync",
    # Collectors
    "MetricCollector",
    "SQLQueryCollector",
    "RequestCollector",
    "TraceCollector",
    # Analyzers
    "PerformanceAnalyzer",
    "BottleneckDetector",
    "QueryAnalyzer",
    # Reporters
    "PerformanceReporter",
    "FlameGraphGenerator",
    "ProfileReport",
]
