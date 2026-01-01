"""
Performance Profiler for Scheduling Engine.

Provides detailed timing and resource usage tracking:
- Phase-based timing (pre-processing, solving, post-processing)
- Custom metric recording
- Memory usage tracking
- Context manager support for automatic timing
"""

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PhaseMetrics:
    """Metrics for a single phase."""

    name: str
    start_time: float
    end_time: float | None = None
    duration: float | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    memory_start: float | None = None
    memory_end: float | None = None

    def finalize(self):
        """Calculate final metrics."""
        if self.end_time and self.start_time:
            self.duration = self.end_time - self.start_time
        if self.memory_end and self.memory_start:
            self.metrics["memory_delta_mb"] = round(
                (self.memory_end - self.memory_start) / (1024 * 1024),
                2,
            )


class SchedulingProfiler:
    """
    Performance profiler for scheduling operations.

    Features:
    - Hierarchical phase timing
    - Custom metric tracking
    - Memory usage monitoring
    - Context manager support
    - JSON export for analysis
    """

    def __init__(self, track_memory: bool = True) -> None:
        """
        Initialize profiler.

        Args:
            track_memory: Enable memory usage tracking (requires psutil)
        """
        self.track_memory = track_memory
        self._phases: dict[str, PhaseMetrics] = {}
        self._phase_stack: list[str] = []
        self._start_time = time.time()
        self._metrics: dict[str, Any] = {}

        # Try to import psutil for memory tracking
        self._psutil = None
        if track_memory:
            try:
                import psutil

                self._psutil = psutil
            except ImportError:
                logger.warning("psutil not installed, memory tracking disabled")
                self.track_memory = False

    def start_phase(self, name: str):
        """
        Start timing a phase.

        Args:
            name: Phase name (e.g., "context_building", "solving")
        """
        if name in self._phases:
            logger.warning(f"Phase '{name}' already started, resetting")

        memory_start = self._get_memory_usage() if self.track_memory else None

        self._phases[name] = PhaseMetrics(
            name=name,
            start_time=time.time(),
            memory_start=memory_start,
        )
        self._phase_stack.append(name)

        logger.debug(f"Started phase: {name}")

    def end_phase(self, name: str):
        """
        End timing a phase.

        Args:
            name: Phase name (must match start_phase call)
        """
        if name not in self._phases:
            logger.warning(f"Phase '{name}' not found in active phases")
            return

        phase = self._phases[name]
        phase.end_time = time.time()
        phase.memory_end = self._get_memory_usage() if self.track_memory else None
        phase.finalize()

        # Remove from stack
        if name in self._phase_stack:
            self._phase_stack.remove(name)

        logger.debug(f"Ended phase: {name} (duration: {phase.duration:.3f}s)")

    @contextmanager
    def phase(self, name: str):
        """
        Context manager for automatic phase timing.

        Usage:
            with profiler.phase("solving"):
                solve_problem()

        Args:
            name: Phase name
        """
        self.start_phase(name)
        try:
            yield
        finally:
            self.end_phase(name)

    def record_metric(self, name: str, value: Any) -> None:
        """
        Record a custom metric.

        Args:
            name: Metric name
            value: Metric value (numeric, string, dict, etc.)
        """
        self._metrics[name] = value
        logger.debug(f"Recorded metric: {name} = {value}")

    def get_report(self) -> dict[str, Any]:
        """
        Get complete profiling report.

        Returns:
            Dictionary with timing breakdown and metrics:
            - total_time: Total elapsed time
            - phases: Timing for each phase
            - metrics: Custom recorded metrics
            - memory: Memory usage summary (if enabled)
        """
        total_time = time.time() - self._start_time

        # Build phase report
        phases = {}
        for name, phase in self._phases.items():
            phases[name] = {
                "duration": round(phase.duration, 3) if phase.duration else None,
                "start": round(phase.start_time - self._start_time, 3),
                "metrics": phase.metrics,
            }

        # Memory summary
        memory_summary = None
        if self.track_memory:
            memory_summary = {
                "current_mb": round(self._get_memory_usage() / (1024 * 1024), 2),
            }

        return {
            "total_time": round(total_time, 3),
            "phases": phases,
            "metrics": self._metrics,
            "memory": memory_summary,
            "timestamp": datetime.now().isoformat(),
        }

    def print_report(self) -> None:
        """Print formatted profiling report to console."""
        report = self.get_report()

        print("\n" + "=" * 60)
        print("SCHEDULING PERFORMANCE REPORT")
        print("=" * 60)
        print(f"Total Time: {report['total_time']:.3f}s")
        print(f"Timestamp: {report['timestamp']}")

        if report["phases"]:
            print("\nPhase Breakdown:")
            print("-" * 60)
            for name, data in sorted(
                report["phases"].items(),
                key=lambda x: x[1].get("start", 0),
            ):
                duration = data.get("duration")
                if duration:
                    percent = (duration / report["total_time"]) * 100
                    print(f"  {name:30s} {duration:8.3f}s ({percent:5.1f}%)")

        if report["metrics"]:
            print("\nCustom Metrics:")
            print("-" * 60)
            for name, value in report["metrics"].items():
                print(f"  {name:30s} {value}")

        if report["memory"]:
            print("\nMemory Usage:")
            print("-" * 60)
            print(f"  Current: {report['memory']['current_mb']:.2f} MB")

        print("=" * 60 + "\n")

    def reset(self) -> None:
        """Reset profiler state for new run."""
        self._phases.clear()
        self._phase_stack.clear()
        self._metrics.clear()
        self._start_time = time.time()
        logger.debug("Profiler reset")

    def _get_memory_usage(self) -> float:
        """
        Get current process memory usage in bytes.

        Returns:
            Memory usage in bytes, or 0 if unavailable
        """
        if not self._psutil:
            return 0.0

        try:
            import os

            process = self._psutil.Process(os.getpid())
            return process.memory_info().rss
        except Exception as e:
            logger.warning(f"Failed to get memory usage: {e}")
            return 0.0
