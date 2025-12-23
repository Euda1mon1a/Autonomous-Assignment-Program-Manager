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

from app.profiling.analyzers import (
    BottleneckDetector,
    PerformanceAnalyzer,
    QueryAnalyzer,
)
from app.profiling.collectors import (
    MetricCollector,
    RequestCollector,
    SQLQueryCollector,
    TraceCollector,
)
from app.profiling.profiler import (
    CPUProfiler,
    MemoryProfiler,
    ProfilerContext,
    profile_async,
    profile_sync,
)
from app.profiling.reporters import (
    FlameGraphGenerator,
    PerformanceReporter,
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
