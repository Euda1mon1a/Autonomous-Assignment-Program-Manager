"""Tests for solver sandboxing — resource limits for CP-SAT solver."""

import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from app.scheduling.solver_sandbox import (
    MemoryWatchdog,
    SandboxMetrics,
    SolverResourceLimits,
    clamp_workers,
    create_sandboxed_callback,
)


class TestSolverResourceLimits:
    def test_defaults(self):
        limits = SolverResourceLimits()
        assert limits.max_memory_mb == 4096
        assert limits.max_workers == 8
        assert limits.max_wall_time_seconds == 300.0

    def test_from_settings(self):
        settings = MagicMock()
        settings.SOLVER_MAX_MEMORY_MB = 2048
        settings.SOLVER_MAX_WORKERS = 4
        settings.SOLVER_MAX_WALL_TIME_SECONDS = 120.0

        limits = SolverResourceLimits.from_settings(settings)
        assert limits.max_memory_mb == 2048
        assert limits.max_workers == 4
        assert limits.max_wall_time_seconds == 120.0

    def test_from_settings_missing_attrs(self):
        settings = MagicMock(spec=[])
        limits = SolverResourceLimits.from_settings(settings)
        assert limits.max_memory_mb == 4096
        assert limits.max_workers == 8

    def test_frozen(self):
        limits = SolverResourceLimits()
        with pytest.raises(AttributeError):
            limits.max_memory_mb = 999


class TestClampWorkers:
    def test_clamp_above_max(self):
        assert clamp_workers(16, 8) == 8

    def test_below_max_unchanged(self):
        assert clamp_workers(4, 8) == 4

    def test_at_max_unchanged(self):
        assert clamp_workers(8, 8) == 8

    def test_auto_detect_clamped(self):
        result = clamp_workers(0, 2)
        assert result <= 2

    def test_negative_treated_as_auto(self):
        result = clamp_workers(-1, 4)
        assert result <= 4


class TestMemoryWatchdog:
    def test_starts_and_stops(self):
        watchdog = MemoryWatchdog(max_memory_mb=999999)
        watchdog.start()
        time.sleep(0.1)
        assert watchdog.is_alive()
        assert not watchdog.exceeded
        assert watchdog.peak_mb > 0
        watchdog.stop()
        watchdog.join(timeout=2.0)
        assert not watchdog.is_alive()

    def test_detects_exceeded_with_low_limit(self):
        # Set limit to 1MB — process RSS will always exceed this
        watchdog = MemoryWatchdog(max_memory_mb=1, check_interval=0.05)
        watchdog.start()
        time.sleep(0.2)
        watchdog.stop()
        watchdog.join(timeout=2.0)
        assert watchdog.exceeded


class TestSandboxedCallback:
    def test_creates_callback(self):
        watchdog = MagicMock()
        watchdog.exceeded = False
        cb = create_sandboxed_callback(watchdog)
        assert hasattr(cb, "on_solution_callback")
        assert hasattr(cb, "solution_count")

    def test_counts_solutions(self):
        watchdog = MagicMock()
        watchdog.exceeded = False
        cb = create_sandboxed_callback(watchdog)
        cb.on_solution_callback()
        cb.on_solution_callback()
        assert cb.solution_count == 2

    def test_aborts_on_memory_exceeded(self):
        watchdog = MagicMock()
        watchdog.exceeded = True
        watchdog.peak_mb = 5000.0
        cb = create_sandboxed_callback(watchdog)
        cb.StopSearch = MagicMock()
        cb.on_solution_callback()
        assert cb.memory_aborted
        cb.StopSearch.assert_called_once()

    def test_delegates_to_inner(self):
        watchdog = MagicMock()
        watchdog.exceeded = False
        inner = MagicMock()
        cb = create_sandboxed_callback(watchdog, inner)
        cb.on_solution_callback()
        inner.on_solution_callback.assert_called_once()

    def test_inner_error_does_not_crash(self):
        watchdog = MagicMock()
        watchdog.exceeded = False
        inner = MagicMock()
        inner.on_solution_callback.side_effect = RuntimeError("boom")
        cb = create_sandboxed_callback(watchdog, inner)
        cb.on_solution_callback()  # Should not raise
        assert cb.solution_count == 1
