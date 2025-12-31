"""
Benchmark suite for Residency Scheduler performance testing.

This package contains standalone benchmark scripts for measuring the performance
of critical system components. Unlike unit tests, these benchmarks are designed
to provide detailed timing metrics, memory profiles, and throughput measurements.

Usage:
    # Run all benchmarks
    python -m benchmarks

    # Run specific benchmark
    python -m benchmarks.schedule_generation_bench

    # Run with detailed output
    python -m benchmarks.schedule_generation_bench --verbose

    # Run with iterations
    python -m benchmarks.schedule_generation_bench --iterations 10

Benchmark Categories:
    - Schedule Generation: Measure solver performance and optimization time
    - ACGME Validation: Measure compliance checking speed
    - Database Queries: Measure query optimization and connection pooling
    - Resilience Calculations: Measure resilience framework metrics
    - Swap Matching: Measure swap matching algorithm performance
    - Concurrent Requests: Measure API throughput under load
    - Memory Usage: Track memory consumption patterns
    - Startup Time: Measure application initialization time

Output Format:
    All benchmarks output JSON-formatted results that can be:
    - Compared across runs to detect regressions
    - Visualized in dashboards
    - Stored in time-series databases for trending
    - Used for CI/CD performance gates
"""

import json
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import psutil


@dataclass
class BenchmarkResult:
    """Standard benchmark result format."""

    benchmark_name: str
    category: str
    timestamp: str
    duration_seconds: float
    iterations: int
    avg_duration: float
    min_duration: float
    max_duration: float
    std_deviation: float
    throughput: Optional[float] = None  # Operations per second
    memory_mb: Optional[float] = None
    peak_memory_mb: Optional[float] = None
    metadata: Optional[dict[str, Any]] = None

    def to_json(self) -> str:
        """Convert result to JSON string."""
        return json.dumps(asdict(self), indent=2)

    def save(self, output_dir: Path):
        """Save result to file."""
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{self.benchmark_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = output_dir / filename
        filepath.write_text(self.to_json())
        print(f"Saved benchmark result to {filepath}")


@contextmanager
def measure_performance(name: str = "operation"):
    """
    Context manager for measuring performance metrics.

    Yields:
        dict with metrics updated during execution

    Example:
        with measure_performance("my_operation") as metrics:
            do_work()
        print(f"Duration: {metrics['duration']:.3f}s")
        print(f"Memory: {metrics['memory_mb']:.1f} MB")
    """
    process = psutil.Process()
    start_memory = process.memory_info().rss / 1024 / 1024  # MB
    start_time = time.perf_counter()

    metrics = {
        "name": name,
        "start_time": start_time,
        "start_memory_mb": start_memory,
    }

    try:
        yield metrics
    finally:
        end_time = time.perf_counter()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB

        metrics.update(
            {
                "end_time": end_time,
                "duration": end_time - start_time,
                "end_memory_mb": end_memory,
                "memory_delta_mb": end_memory - start_memory,
                "peak_memory_mb": max(start_memory, end_memory),
            }
        )


def calculate_stats(durations: list[float]) -> dict[str, float]:
    """Calculate statistics from a list of durations."""
    if not durations:
        return {
            "avg": 0.0,
            "min": 0.0,
            "max": 0.0,
            "std_dev": 0.0,
        }

    avg = sum(durations) / len(durations)
    variance = sum((x - avg) ** 2 for x in durations) / len(durations)
    std_dev = variance**0.5

    return {
        "avg": avg,
        "min": min(durations),
        "max": max(durations),
        "std_dev": std_dev,
    }


def print_benchmark_header(name: str, description: str):
    """Print formatted benchmark header."""
    print("=" * 80)
    print(f"BENCHMARK: {name}")
    print("=" * 80)
    print(description)
    print("-" * 80)


def print_benchmark_results(result: BenchmarkResult):
    """Print formatted benchmark results."""
    print("\nResults:")
    print(f"  Total Duration: {result.duration_seconds:.3f}s")
    print(f"  Iterations: {result.iterations}")
    print(f"  Average: {result.avg_duration:.3f}s")
    print(f"  Min: {result.min_duration:.3f}s")
    print(f"  Max: {result.max_duration:.3f}s")
    print(f"  Std Dev: {result.std_deviation:.3f}s")

    if result.throughput:
        print(f"  Throughput: {result.throughput:.2f} ops/sec")

    if result.memory_mb:
        print(f"  Memory: {result.memory_mb:.1f} MB")

    if result.peak_memory_mb:
        print(f"  Peak Memory: {result.peak_memory_mb:.1f} MB")

    if result.metadata:
        print("\nMetadata:")
        for key, value in result.metadata.items():
            print(f"  {key}: {value}")

    print("=" * 80)
