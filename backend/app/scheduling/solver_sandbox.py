"""
Solver sandboxing — resource ceilings for pathological inputs.

Enforces memory and CPU limits around CP-SAT solver execution to prevent
runaway resource consumption from adversarial or malformed scheduling inputs.
"""

import logging
import os
import threading
import time
from dataclasses import dataclass

import psutil

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SolverResourceLimits:
    """Resource ceilings for solver execution."""

    max_memory_mb: int = 4096
    max_workers: int = 8
    max_wall_time_seconds: float = 300.0

    @classmethod
    def from_settings(cls, settings) -> "SolverResourceLimits":
        return cls(
            max_memory_mb=getattr(settings, "SOLVER_MAX_MEMORY_MB", 4096),
            max_workers=getattr(settings, "SOLVER_MAX_WORKERS", 8),
            max_wall_time_seconds=getattr(
                settings, "SOLVER_MAX_WALL_TIME_SECONDS", 300.0
            ),
        )


@dataclass
class SandboxMetrics:
    """Metrics collected during sandboxed solver execution."""

    peak_memory_mb: float = 0.0
    wall_time_seconds: float = 0.0
    aborted: bool = False
    abort_reason: str = ""


class MemoryWatchdog(threading.Thread):
    """Background thread that monitors process memory during solver execution.

    Sets a flag when memory exceeds the limit. The solver callback reads
    this flag and calls StopSearch().
    """

    def __init__(self, max_memory_mb: int, check_interval: float = 0.5):
        super().__init__(daemon=True, name="solver-memory-watchdog")
        self.max_memory_mb = max_memory_mb
        self.check_interval = check_interval
        self._stop_event = threading.Event()
        self._exceeded = threading.Event()
        self._peak_mb: float = 0.0
        self._process = psutil.Process(os.getpid())

    def run(self) -> None:
        while not self._stop_event.is_set():
            try:
                rss_mb = self._process.memory_info().rss / (1024 * 1024)
                self._peak_mb = max(self._peak_mb, rss_mb)
                if rss_mb > self.max_memory_mb:
                    logger.warning(
                        f"Solver memory watchdog: {rss_mb:.0f}MB exceeds "
                        f"{self.max_memory_mb}MB limit"
                    )
                    self._exceeded.set()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
            self._stop_event.wait(self.check_interval)

    def stop(self) -> None:
        self._stop_event.set()

    @property
    def exceeded(self) -> bool:
        return self._exceeded.is_set()

    @property
    def peak_mb(self) -> float:
        return self._peak_mb


def clamp_workers(requested: int, max_workers: int) -> int:
    """Clamp solver worker count to configured maximum."""
    if requested <= 0:
        auto = os.cpu_count() or 4
        clamped = min(auto, max_workers)
    else:
        clamped = min(requested, max_workers)
    if clamped != requested:
        logger.info(
            f"Solver sandbox: clamped workers {requested} -> {clamped} "
            f"(max: {max_workers})"
        )
    return clamped


def create_sandboxed_callback(watchdog, inner_callback=None):
    """Create a CP-SAT callback that monitors memory and delegates to inner.

    Args:
        watchdog: MemoryWatchdog instance
        inner_callback: Optional existing CpSolverSolutionCallback

    Returns:
        CpSolverSolutionCallback subclass instance
    """
    from ortools.sat.python import cp_model

    class SandboxedCallback(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            super().__init__()
            self.solution_count = 0
            self.memory_aborted = False

        def on_solution_callback(self):
            self.solution_count += 1

            if watchdog.exceeded:
                self.memory_aborted = True
                self.StopSearch()
                return

            if inner_callback is not None:
                try:
                    inner_callback.on_solution_callback()
                except Exception as e:
                    logger.warning(f"Inner solver callback error: {e}")

    return SandboxedCallback()
