"""
Performance Optimization Module for Scheduling System.

Provides:
- Query optimization utilities for database operations
- Algorithm performance improvements (memoization, early termination)
- Batch processing for bulk operations
- Performance profiling decorators
"""
import time
import logging
import functools
import hashlib
import json
from typing import Any, Callable, Optional, TypeVar, ParamSpec
from collections import defaultdict
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import select

from app.models.person import Person
from app.models.block import Block
from app.models.assignment import Assignment
from app.models.absence import Absence
from app.models.rotation_template import RotationTemplate

logger = logging.getLogger(__name__)

P = ParamSpec('P')
R = TypeVar('R')


# ==================================================
# PERFORMANCE PROFILING DECORATORS
# ==================================================

def profile_time(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator to profile execution time of a function.

    Logs the function name and execution time at INFO level.

    Example:
        @profile_time
        def expensive_operation():
            # ... computation
            pass
    """
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = time.perf_counter() - start_time
            logger.info(f"[PROFILE] {func.__name__} took {elapsed:.4f}s")
    return wrapper


def profile_memory(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator to profile memory usage of a function.

    Requires psutil to be installed. Logs memory delta.

    Example:
        @profile_memory
        def memory_intensive_operation():
            # ... large data processing
            pass
    """
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            mem_before = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            logger.warning("psutil not installed, skipping memory profiling")
            return func(*args, **kwargs)

        result = func(*args, **kwargs)

        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_delta = mem_after - mem_before
        logger.info(f"[PROFILE] {func.__name__} memory delta: {mem_delta:+.2f} MB")
        return result
    return wrapper


def profile_detailed(func: Callable[P, R]) -> Callable[P, R]:
    """
    Combined profiling decorator for time and memory.

    Example:
        @profile_detailed
        def complex_operation():
            # ... computation
            pass
    """
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        # Time profiling
        start_time = time.perf_counter()

        # Memory profiling (if available)
        mem_before = None
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            mem_before = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            pass

        # Execute function
        result = func(*args, **kwargs)

        # Log results
        elapsed = time.perf_counter() - start_time
        log_msg = f"[PROFILE] {func.__name__} - Time: {elapsed:.4f}s"

        if mem_before is not None:
            mem_after = process.memory_info().rss / 1024 / 1024  # MB
            mem_delta = mem_after - mem_before
            log_msg += f", Memory: {mem_delta:+.2f} MB"

        logger.info(log_msg)
        return result
    return wrapper


# ==================================================
# MEMOIZATION UTILITIES
# ==================================================

class MemoizedFunction:
    """
    Memoization decorator with configurable cache size and TTL.

    Features:
    - LRU-style cache with max size
    - Optional TTL-based expiration
    - Cache statistics tracking

    Example:
        @MemoizedFunction(max_size=100, ttl_seconds=300)
        def expensive_computation(x, y):
            return x * y
    """

    def __init__(self, max_size: int = 128, ttl_seconds: Optional[float] = None):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: dict = {}
        self.access_times: dict = {}
        self.hits = 0
        self.misses = 0

    def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Generate cache key
            cache_key = self._make_key(args, kwargs)
            current_time = time.time()

            # Check cache
            if cache_key in self.cache:
                # Check TTL if configured
                if self.ttl_seconds is not None:
                    cached_time = self.access_times.get(cache_key, 0)
                    if current_time - cached_time > self.ttl_seconds:
                        # Expired
                        del self.cache[cache_key]
                        del self.access_times[cache_key]
                    else:
                        # Valid cache hit
                        self.hits += 1
                        self.access_times[cache_key] = current_time
                        return self.cache[cache_key]
                else:
                    # No TTL, direct hit
                    self.hits += 1
                    self.access_times[cache_key] = current_time
                    return self.cache[cache_key]

            # Cache miss - compute result
            self.misses += 1
            result = func(*args, **kwargs)

            # Store in cache
            self.cache[cache_key] = result
            self.access_times[cache_key] = current_time

            # Enforce max size (LRU eviction)
            if len(self.cache) > self.max_size:
                # Remove oldest access
                oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
                del self.cache[oldest_key]
                del self.access_times[oldest_key]

            return result

        # Attach cache statistics
        wrapper.cache_info = lambda: {
            'hits': self.hits,
            'misses': self.misses,
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_rate': self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0.0
        }
        wrapper.cache_clear = lambda: self._clear_cache()

        return wrapper

    def _make_key(self, args: tuple, kwargs: dict) -> str:
        """Generate cache key from arguments."""
        # Convert UUIDs to strings for hashing
        args_serializable = []
        for arg in args:
            if isinstance(arg, UUID):
                args_serializable.append(str(arg))
            elif isinstance(arg, (list, tuple)):
                args_serializable.append(tuple(str(x) if isinstance(x, UUID) else x for x in arg))
            else:
                args_serializable.append(arg)

        kwargs_serializable = {
            k: str(v) if isinstance(v, UUID) else v
            for k, v in kwargs.items()
        }

        key_data = (tuple(args_serializable), tuple(sorted(kwargs_serializable.items())))
        return hashlib.md5(str(key_data).encode()).hexdigest()

    def _clear_cache(self):
        """Clear the cache."""
        self.cache.clear()
        self.access_times.clear()
        self.hits = 0
        self.misses = 0


def memoize(func: Callable[P, R]) -> Callable[P, R]:
    """
    Simple memoization decorator with default settings.

    Example:
        @memoize
        def fibonacci(n):
            if n < 2:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
    """
    return MemoizedFunction(max_size=128, ttl_seconds=None)(func)


# ==================================================
# QUERY OPTIMIZATION UTILITIES
# ==================================================

class QueryOptimizer:
    """
    Database query optimization utilities.

    Provides methods for:
    - Eager loading relationships
    - Batch loading entities
    - Optimized bulk operations
    """

    @staticmethod
    def load_residents_with_assignments(
        db: Session,
        start_date,
        end_date,
        pgy_levels: Optional[list[int]] = None
    ) -> list[Person]:
        """
        Load residents with their assignments eagerly loaded.

        Uses joinedload to avoid N+1 query problems.
        """
        query = db.query(Person).filter(Person.type == "resident")

        if pgy_levels:
            query = query.filter(Person.pgy_level.in_(pgy_levels))

        # Eager load assignments for the date range
        query = query.options(
            joinedload(Person.assignments)
        )

        return query.order_by(Person.pgy_level, Person.name).all()

    @staticmethod
    def load_blocks_with_assignments(
        db: Session,
        start_date,
        end_date
    ) -> list[Block]:
        """
        Load blocks with assignments eagerly loaded.
        """
        query = db.query(Block).filter(
            Block.date >= start_date,
            Block.date <= end_date
        )

        # Eager load assignments
        query = query.options(
            selectinload(Block.assignments)
        )

        return query.order_by(Block.date, Block.time_of_day).all()

    @staticmethod
    @profile_time
    def batch_load_availability(
        db: Session,
        person_ids: list[UUID],
        start_date,
        end_date
    ) -> dict:
        """
        Batch load availability data for multiple people.

        Returns availability matrix optimized for performance.
        """
        # Single query for all absences
        absences = db.query(Absence).filter(
            Absence.person_id.in_(person_ids),
            Absence.start_date <= end_date,
            Absence.end_date >= start_date
        ).all()

        # Single query for all blocks
        blocks = db.query(Block).filter(
            Block.date >= start_date,
            Block.date <= end_date
        ).all()

        # Build availability matrix
        availability_matrix = {}
        for person_id in person_ids:
            availability_matrix[person_id] = {}

            for block in blocks:
                is_available = True
                replacement_activity = None
                has_partial_absence = False

                for absence in absences:
                    if (absence.person_id == person_id and
                        absence.start_date <= block.date <= absence.end_date):

                        if absence.should_block_assignment:
                            is_available = False
                            replacement_activity = absence.replacement_activity
                            break
                        else:
                            has_partial_absence = True
                            replacement_activity = absence.replacement_activity

                availability_matrix[person_id][block.id] = {
                    "available": is_available,
                    "replacement": replacement_activity,
                    "partial_absence": has_partial_absence,
                }

        return availability_matrix


# ==================================================
# BATCH PROCESSING UTILITIES
# ==================================================

class BatchProcessor:
    """
    Utilities for batch processing database operations.

    Improves performance for bulk inserts and updates.
    """

    @staticmethod
    @profile_time
    def batch_create_assignments(
        db: Session,
        assignments_data: list[tuple[UUID, UUID, Optional[UUID]]],  # (person_id, block_id, template_id)
        role: str = "primary",
        batch_size: int = 500
    ) -> list[Assignment]:
        """
        Create assignments in batches for better performance.

        Args:
            db: Database session
            assignments_data: List of (person_id, block_id, template_id) tuples
            role: Assignment role
            batch_size: Number of assignments to insert per batch

        Returns:
            List of created Assignment objects
        """
        assignments = []
        total = len(assignments_data)

        for i in range(0, total, batch_size):
            batch = assignments_data[i:i + batch_size]

            for person_id, block_id, template_id in batch:
                assignment = Assignment(
                    block_id=block_id,
                    person_id=person_id,
                    rotation_template_id=template_id,
                    role=role,
                )
                assignments.append(assignment)
                db.add(assignment)

            # Flush each batch
            db.flush()
            logger.debug(f"Batch created {len(batch)} assignments ({i + len(batch)}/{total})")

        return assignments

    @staticmethod
    @profile_time
    def batch_delete_assignments(
        db: Session,
        block_ids: list[UUID],
        batch_size: int = 500
    ) -> int:
        """
        Delete assignments in batches.

        Args:
            db: Database session
            block_ids: List of block IDs to delete assignments for
            batch_size: Number of block IDs per batch

        Returns:
            Total number of deleted assignments
        """
        total_deleted = 0

        for i in range(0, len(block_ids), batch_size):
            batch = block_ids[i:i + batch_size]
            deleted = db.query(Assignment).filter(
                Assignment.block_id.in_(batch)
            ).delete(synchronize_session=False)
            total_deleted += deleted
            logger.debug(f"Batch deleted {deleted} assignments ({i + len(batch)}/{len(block_ids)} blocks)")

        return total_deleted


# ==================================================
# EARLY TERMINATION UTILITIES
# ==================================================

class TimeoutHandler:
    """
    Provides timeout and early termination utilities.

    Example:
        handler = TimeoutHandler(timeout_seconds=30)

        for item in large_dataset:
            if handler.should_terminate():
                break
            process(item)
    """

    def __init__(self, timeout_seconds: float):
        self.timeout_seconds = timeout_seconds
        self.start_time = time.time()

    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time

    def remaining(self) -> float:
        """Get remaining time in seconds."""
        return max(0, self.timeout_seconds - self.elapsed())

    def should_terminate(self) -> bool:
        """Check if timeout has been reached."""
        return self.elapsed() >= self.timeout_seconds

    def reset(self):
        """Reset the timer."""
        self.start_time = time.time()


class QualityChecker:
    """
    Early termination based on solution quality.

    Allows stopping computation when a "good enough" solution is found.

    Example:
        checker = QualityChecker(target_quality=0.95)

        while not checker.is_satisfied(current_quality):
            improve_solution()
    """

    def __init__(self, target_quality: float = 0.95, min_iterations: int = 10):
        self.target_quality = target_quality
        self.min_iterations = min_iterations
        self.iteration = 0
        self.best_quality = 0.0
        self.quality_history: list[float] = []

    def update(self, quality: float) -> bool:
        """
        Update with new quality metric.

        Returns True if target quality is reached and can terminate early.
        """
        self.iteration += 1
        self.quality_history.append(quality)
        self.best_quality = max(self.best_quality, quality)

        # Don't terminate before minimum iterations
        if self.iteration < self.min_iterations:
            return False

        # Check if target reached
        return quality >= self.target_quality

    def is_satisfied(self, quality: float) -> bool:
        """Check if quality is satisfactory."""
        return self.update(quality)

    def get_statistics(self) -> dict:
        """Get quality statistics."""
        return {
            'iterations': self.iteration,
            'best_quality': self.best_quality,
            'current_quality': self.quality_history[-1] if self.quality_history else 0.0,
            'improvement': self.best_quality - self.quality_history[0] if self.quality_history else 0.0,
        }


# ==================================================
# PERFORMANCE STATISTICS
# ==================================================

class PerformanceStats:
    """
    Track and report performance statistics.

    Example:
        stats = PerformanceStats()

        with stats.measure("phase_1"):
            # ... computation
            pass

        with stats.measure("phase_2"):
            # ... computation
            pass

        print(stats.report())
    """

    def __init__(self):
        self.timings: dict[str, list[float]] = defaultdict(list)
        self.counters: dict[str, int] = defaultdict(int)
        self.current_measurements: dict[str, float] = {}

    def measure(self, name: str):
        """Context manager for timing a block of code."""
        return self._MeasurementContext(self, name)

    class _MeasurementContext:
        def __init__(self, stats: 'PerformanceStats', name: str):
            self.stats = stats
            self.name = name
            self.start_time = None

        def __enter__(self):
            self.start_time = time.perf_counter()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            elapsed = time.perf_counter() - self.start_time
            self.stats.timings[self.name].append(elapsed)
            self.stats.current_measurements[self.name] = elapsed

    def increment(self, name: str, amount: int = 1):
        """Increment a counter."""
        self.counters[name] += amount

    def get_timing(self, name: str) -> dict:
        """Get timing statistics for a measurement."""
        if name not in self.timings or not self.timings[name]:
            return {'count': 0, 'total': 0, 'avg': 0, 'min': 0, 'max': 0}

        times = self.timings[name]
        return {
            'count': len(times),
            'total': sum(times),
            'avg': sum(times) / len(times),
            'min': min(times),
            'max': max(times),
        }

    def report(self) -> str:
        """Generate a performance report."""
        lines = ["=== Performance Statistics ==="]

        # Timings
        if self.timings:
            lines.append("\nTimings:")
            for name in sorted(self.timings.keys()):
                stats = self.get_timing(name)
                lines.append(
                    f"  {name}: {stats['total']:.4f}s total, "
                    f"{stats['avg']:.4f}s avg "
                    f"({stats['count']} calls)"
                )

        # Counters
        if self.counters:
            lines.append("\nCounters:")
            for name in sorted(self.counters.keys()):
                lines.append(f"  {name}: {self.counters[name]}")

        return "\n".join(lines)
