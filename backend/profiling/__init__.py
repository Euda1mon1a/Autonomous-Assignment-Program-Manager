"""
Profiling Tools for Residency Scheduler

Provides utilities for profiling application performance using cProfile,
line_profiler, memory_profiler, and flame graph generation.

Usage:
    # Profile schedule generation
    python -m profiling.profile_scheduler

    # Profile database queries
    python -m profiling.profile_queries

    # Generate flame graph
    python -m profiling.flame_graph_generator --target schedule_generation

Profiling Methods:
    - cProfile: Function-level profiling
    - line_profiler: Line-by-line profiling
    - memory_profiler: Memory usage profiling
    - py-spy: Sampling profiler (requires separate installation)

Output Formats:
    - Text reports
    - pstats files (for analysis)
    - Flame graphs (SVG)
    - Call graphs
"""

import cProfile
import pstats
from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from typing import Any, Callable, Optional


class ProfilerContext:
    """Context manager for cProfile profiling."""

    def __init__(self, name: str = "profile"):
        self.name = name
        self.profiler = cProfile.Profile()
        self.stats: Optional[pstats.Stats] = None

    def __enter__(self):
        """Start profiling."""
        self.profiler.enable()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop profiling and save stats."""
        self.profiler.disable()
        self.stats = pstats.Stats(self.profiler)

    def print_stats(self, sort_by: str = "cumulative", limit: int = 30):
        """Print profiling statistics."""
        if self.stats:
            print(f"\n{'=' * 80}")
            print(f"PROFILE RESULTS: {self.name}")
            print(f"{'=' * 80}\n")

            self.stats.strip_dirs()
            self.stats.sort_stats(sort_by)
            self.stats.print_stats(limit)

    def save_stats(self, output_dir: Path):
        """Save profiling statistics to file."""
        if self.stats:
            output_dir.mkdir(parents=True, exist_ok=True)
            filepath = output_dir / f"{self.name}.pstats"
            self.stats.dump_stats(str(filepath))
            print(f"Saved profiling stats to {filepath}")

    def get_function_stats(self, func_name: str) -> dict[str, Any]:
        """Get statistics for a specific function."""
        if not self.stats:
            return {}

        # Create string buffer to capture output
        buffer = StringIO()
        self.stats.stream = buffer
        self.stats.print_stats(func_name)

        return {
            "output": buffer.getvalue(),
            "total_calls": self.stats.total_calls,
        }


@contextmanager
def profile_block(name: str = "code_block", save_dir: Optional[Path] = None):
    """
    Context manager for profiling a code block.

    Usage:
        with profile_block("my_operation") as prof:
            # Code to profile
            do_something()

        prof.print_stats()
    """
    profiler = ProfilerContext(name)
    try:
        yield profiler.profiler
    finally:
        profiler.profiler.disable()
        profiler.stats = pstats.Stats(profiler.profiler)

        if save_dir:
            profiler.save_stats(save_dir)


def profile_function(sort_by: str = "cumulative", limit: int = 30):
    """
    Decorator for profiling a function.

    Usage:
        @profile_function(sort_by="time")
        def my_function():
            # Function code
            pass
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            profiler = ProfilerContext(func.__name__)

            with profiler:
                result = func(*args, **kwargs)

            profiler.print_stats(sort_by=sort_by, limit=limit)

            # Save stats
            output_dir = Path(__file__).parent.parent.parent / "profiling_results"
            profiler.save_stats(output_dir)

            return result

        return wrapper

    return decorator


def analyze_pstats_file(filepath: Path, sort_by: str = "cumulative", limit: int = 50):
    """
    Analyze a saved .pstats file and print statistics.

    Args:
        filepath: Path to .pstats file
        sort_by: How to sort results (cumulative, time, calls, etc.)
        limit: Number of top results to show
    """
    stats = pstats.Stats(str(filepath))

    print(f"\n{'=' * 80}")
    print(f"PROFILE ANALYSIS: {filepath.name}")
    print(f"{'=' * 80}\n")

    stats.strip_dirs()
    stats.sort_stats(sort_by)
    stats.print_stats(limit)

    # Print callers for top functions
    print(f"\n{'=' * 80}")
    print("CALLERS (Top 10 functions)")
    print(f"{'=' * 80}\n")
    stats.print_callers(10)


def compare_profiles(baseline_file: Path, current_file: Path):
    """
    Compare two profiling runs to detect performance regressions.

    Args:
        baseline_file: Path to baseline .pstats file
        current_file: Path to current .pstats file
    """
    baseline_stats = pstats.Stats(str(baseline_file))
    current_stats = pstats.Stats(str(current_file))

    print(f"\n{'=' * 80}")
    print(f"PROFILE COMPARISON")
    print(f"Baseline: {baseline_file.name}")
    print(f"Current:  {current_file.name}")
    print(f"{'=' * 80}\n")

    # This is simplified - would need custom comparison logic
    # for detailed regression analysis
    print("Baseline stats:")
    baseline_stats.strip_dirs()
    baseline_stats.sort_stats("cumulative")
    baseline_stats.print_stats(20)

    print("\n\nCurrent stats:")
    current_stats.strip_dirs()
    current_stats.sort_stats("cumulative")
    current_stats.print_stats(20)


# Export public API
__all__ = [
    "ProfilerContext",
    "profile_block",
    "profile_function",
    "analyze_pstats_file",
    "compare_profiles",
]
