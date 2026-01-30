"""
Performance profiler for CPU and memory profiling.

Provides decorators and context managers for profiling code execution,
including CPU time, memory usage, and function call statistics.
"""

import cProfile
import functools
import io
import pstats
import time
import tracemalloc
from collections.abc import Callable
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TypeVar
from uuid import uuid4

import psutil

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class ProfileResult:
    """Result of a profiling operation."""

    profile_id: str
    function_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    cpu_percent: float
    memory_mb: float
    memory_peak_mb: float
    call_count: int
    stats: pstats.Stats | None = None
    traceback: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "profile_id": self.profile_id,
            "function_name": self.function_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": self.duration_seconds,
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "memory_peak_mb": self.memory_peak_mb,
            "call_count": self.call_count,
            "metadata": self.metadata,
        }


class CPUProfiler:
    """
    CPU profiler using cProfile.

    Provides detailed statistics about function calls and CPU time.
    """

    def __init__(self, enabled: bool = True) -> None:
        """
        Initialize CPU profiler.

        Args:
            enabled: Whether profiling is enabled
        """
        self.enabled = enabled
        self.profiler: cProfile.Profile | None = None
        self.results: list[ProfileResult] = []

    @contextmanager
    def profile(self, function_name: str = "unknown"):
        """
        Profile a block of code.

        Args:
            function_name: Name to identify the profiled code

        Yields:
            ProfileResult: Result object that will be populated
        """
        profile_id = str(uuid4())
        start_time = datetime.utcnow()

        if not self.enabled:
            result = ProfileResult(
                profile_id=profile_id,
                function_name=function_name,
                start_time=start_time,
                end_time=start_time,
                duration_seconds=0.0,
                cpu_percent=0.0,
                memory_mb=0.0,
                memory_peak_mb=0.0,
                call_count=0,
            )
            yield result
            return

            # Start profiling
        profiler = cProfile.Profile()
        process = psutil.Process()
        cpu_start = process.cpu_percent()

        profiler.enable()
        start = time.perf_counter()

        try:
            yield None
        finally:
            # Stop profiling
            end = time.perf_counter()
            profiler.disable()
            cpu_end = process.cpu_percent()

            # Collect statistics
            stats = pstats.Stats(profiler)
            end_time = datetime.utcnow()

            result = ProfileResult(
                profile_id=profile_id,
                function_name=function_name,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=end - start,
                cpu_percent=(cpu_start + cpu_end) / 2,
                memory_mb=process.memory_info().rss / 1024 / 1024,
                memory_peak_mb=process.memory_info().rss / 1024 / 1024,
                call_count=stats.total_calls,
                stats=stats,
            )
            self.results.append(result)

    def get_stats_string(self, sort_by: str = "cumulative") -> str:
        """
        Get formatted statistics string.

        Args:
            sort_by: How to sort stats (cumulative, time, calls)

        Returns:
            Formatted statistics string
        """
        if not self.results or not self.results[-1].stats:
            return "No profiling data available"

        stream = io.StringIO()
        stats = self.results[-1].stats
        stats.sort_stats(sort_by)
        stats.print_stats(stream=stream)
        return stream.getvalue()

    def clear(self) -> None:
        """Clear all profiling results."""
        self.results.clear()


class MemoryProfiler:
    """
    Memory profiler using tracemalloc.

    Tracks memory allocation and peak usage during code execution.
    """

    def __init__(self, enabled: bool = True) -> None:
        """
        Initialize memory profiler.

        Args:
            enabled: Whether profiling is enabled
        """
        self.enabled = enabled
        self.results: list[ProfileResult] = []
        self._tracking = False

    @contextmanager
    def profile(self, function_name: str = "unknown"):
        """
        Profile memory usage of a block of code.

        Args:
            function_name: Name to identify the profiled code

        Yields:
            ProfileResult: Result object that will be populated
        """
        profile_id = str(uuid4())
        start_time = datetime.utcnow()

        if not self.enabled:
            result = ProfileResult(
                profile_id=profile_id,
                function_name=function_name,
                start_time=start_time,
                end_time=start_time,
                duration_seconds=0.0,
                cpu_percent=0.0,
                memory_mb=0.0,
                memory_peak_mb=0.0,
                call_count=0,
            )
            yield result
            return

            # Start memory tracking
        if not self._tracking:
            tracemalloc.start()
            self._tracking = True

        tracemalloc.reset_peak()
        start = time.perf_counter()
        snapshot_start = tracemalloc.take_snapshot()

        try:
            yield None
        finally:
            # Stop tracking
            end = time.perf_counter()
            snapshot_end = tracemalloc.take_snapshot()
            current, peak = tracemalloc.get_traced_memory()

            # Calculate memory difference
            top_stats = snapshot_end.compare_to(snapshot_start, "lineno")
            total_diff = sum(stat.size_diff for stat in top_stats)

            end_time = datetime.utcnow()

            result = ProfileResult(
                profile_id=profile_id,
                function_name=function_name,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=end - start,
                cpu_percent=0.0,
                memory_mb=total_diff / 1024 / 1024,
                memory_peak_mb=peak / 1024 / 1024,
                call_count=len(top_stats),
                metadata={
                    "current_mb": current / 1024 / 1024,
                    "peak_mb": peak / 1024 / 1024,
                    "diff_mb": total_diff / 1024 / 1024,
                },
            )
            self.results.append(result)

    def get_top_allocations(self, limit: int = 10) -> list[str]:
        """
        Get top memory allocations.

        Args:
            limit: Number of top allocations to return

        Returns:
            List of formatted allocation strings
        """
        if not self._tracking:
            return []

        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")

        return [str(stat) for stat in top_stats[:limit]]

    def clear(self) -> None:
        """Clear all profiling results."""
        self.results.clear()

    def stop(self) -> None:
        """Stop memory tracking."""
        if self._tracking:
            tracemalloc.stop()
            self._tracking = False


class ProfilerContext:
    """
    Combined profiler context for CPU and memory profiling.

    Provides a unified interface for profiling both CPU and memory.
    """

    def __init__(self, cpu_enabled: bool = True, memory_enabled: bool = True) -> None:
        """
        Initialize profiler context.

        Args:
            cpu_enabled: Enable CPU profiling
            memory_enabled: Enable memory profiling
        """
        self.cpu_profiler = CPUProfiler(enabled=cpu_enabled)
        self.memory_profiler = MemoryProfiler(enabled=memory_enabled)

    @contextmanager
    def profile(self, function_name: str = "unknown"):
        """
        Profile both CPU and memory for a block of code.

        Args:
            function_name: Name to identify the profiled code

        Yields:
            Dict with cpu and memory ProfileResults
        """
        with self.cpu_profiler.profile(function_name) as cpu_result:
            with self.memory_profiler.profile(function_name) as mem_result:
                yield {"cpu": cpu_result, "memory": mem_result}

    @asynccontextmanager
    async def profile_async(self, function_name: str = "unknown"):
        """
        Profile async code for both CPU and memory.

        Args:
            function_name: Name to identify the profiled code

        Yields:
            Dict with cpu and memory ProfileResults
        """
        with self.cpu_profiler.profile(function_name) as cpu_result:
            with self.memory_profiler.profile(function_name) as mem_result:
                yield {"cpu": cpu_result, "memory": mem_result}

    def get_combined_report(self) -> dict[str, Any]:
        """
        Get combined profiling report.

        Returns:
            Dictionary containing CPU and memory profiling results
        """
        return {
            "cpu_results": [r.to_dict() for r in self.cpu_profiler.results],
            "memory_results": [r.to_dict() for r in self.memory_profiler.results],
        }

    def clear(self) -> None:
        """Clear all profiling results."""
        self.cpu_profiler.clear()
        self.memory_profiler.clear()


def profile_sync(
    enabled: bool = True,
    cpu: bool = True,
    memory: bool = True,
) -> Callable[[F], F]:
    """
    Decorator to profile synchronous functions.

    Args:
        enabled: Whether profiling is enabled
        cpu: Enable CPU profiling
        memory: Enable memory profiling

    Returns:
        Decorated function

    Example:
        @profile_sync()
        def compute_schedule():
            # Your code here
            pass
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not enabled:
                return func(*args, **kwargs)

            profiler = ProfilerContext(cpu_enabled=cpu, memory_enabled=memory)
            with profiler.profile(func.__name__):
                result = func(*args, **kwargs)

                # Store profiler in function metadata
            if not hasattr(wrapper, "_profilers"):
                wrapper._profilers = []
            wrapper._profilers.append(profiler)

            return result

        return wrapper  # type: ignore

    return decorator


def profile_async(
    enabled: bool = True,
    cpu: bool = True,
    memory: bool = True,
) -> Callable[[F], F]:
    """
    Decorator to profile async functions.

    Args:
        enabled: Whether profiling is enabled
        cpu: Enable CPU profiling
        memory: Enable memory profiling

    Returns:
        Decorated function

    Example:
        @profile_async()
        async def generate_schedule():
            # Your code here
            pass
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not enabled:
                return await func(*args, **kwargs)

            profiler = ProfilerContext(cpu_enabled=cpu, memory_enabled=memory)
            async with profiler.profile_async(func.__name__):
                result = await func(*args, **kwargs)

                # Store profiler in function metadata
            if not hasattr(wrapper, "_profilers"):
                wrapper._profilers = []
            wrapper._profilers.append(profiler)

            return result

        return wrapper  # type: ignore

    return decorator
