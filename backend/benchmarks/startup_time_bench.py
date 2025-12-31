"""
Startup Time Benchmark

Measures application initialization and startup performance including:
- FastAPI app initialization
- Database connection establishment
- Module import time
- Configuration loading
- Middleware initialization

Metrics:
    - Cold start time (first run)
    - Warm start time (subsequent runs)
    - Import overhead
    - Database connection time
    - Total startup latency

Usage:
    python -m benchmarks.startup_time_bench
    python -m benchmarks.startup_time_bench --iterations 5
"""

import argparse
import importlib
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psutil

from benchmarks import (
    BenchmarkResult,
    calculate_stats,
    print_benchmark_header,
    print_benchmark_results,
)


def benchmark_import_time(verbose: bool = False) -> BenchmarkResult:
    """Benchmark module import time."""
    print_benchmark_header(
        "Module Import Time",
        "Measuring time to import core application modules",
    )

    modules_to_test = [
        "app.main",
        "app.models.person",
        "app.models.assignment",
        "app.scheduling.engine",
        "app.scheduling.validator",
        "app.resilience.contingency",
        "app.api.routes.auth",
        "sqlalchemy",
        "fastapi",
        "pydantic",
    ]

    import_times = {}
    total_import_time = 0

    for module_name in modules_to_test:
        # Clear module from cache if already imported
        if module_name in sys.modules:
            del sys.modules[module_name]

        start = time.perf_counter()
        try:
            importlib.import_module(module_name)
            duration = time.perf_counter() - start
            import_times[module_name] = duration
            total_import_time += duration

            if verbose:
                print(f"  {module_name}: {duration * 1000:.1f}ms")
        except Exception as e:
            if verbose:
                print(f"  {module_name}: FAILED ({str(e)})")
            import_times[module_name] = 0

    # Calculate statistics
    durations = list(import_times.values())
    stats = calculate_stats(durations)

    result = BenchmarkResult(
        benchmark_name="startup_import_time",
        category="startup",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        duration_seconds=total_import_time,
        iterations=len(modules_to_test),
        avg_duration=stats["avg"],
        min_duration=stats["min"],
        max_duration=stats["max"],
        std_deviation=stats["std_dev"],
        metadata={
            "total_modules": len(modules_to_test),
            "total_import_time_ms": total_import_time * 1000,
            "slowest_module": max(import_times, key=import_times.get),
            "slowest_time_ms": max(import_times.values()) * 1000,
        },
    )

    print_benchmark_results(result)
    return result


def benchmark_database_connection(
    iterations: int = 10, verbose: bool = False
) -> BenchmarkResult:
    """Benchmark database connection establishment time."""
    print_benchmark_header(
        "Database Connection Time",
        f"Measuring connection establishment time over {iterations} iterations",
    )

    from sqlalchemy import create_engine, text

    from app.core.config import settings

    durations = []
    memory_usage = []

    for i in range(iterations):
        process = psutil.Process()
        start_mem = process.memory_info().rss / 1024 / 1024

        start = time.perf_counter()

        # Create engine and establish connection
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            # Execute simple query to ensure connection is established
            conn.execute(text("SELECT 1"))

        duration = time.perf_counter() - start
        durations.append(duration)

        end_mem = process.memory_info().rss / 1024 / 1024
        memory_usage.append(end_mem - start_mem)

        engine.dispose()

        if verbose:
            print(f"  Iteration {i + 1}: {duration * 1000:.1f}ms")

    stats = calculate_stats(durations)

    result = BenchmarkResult(
        benchmark_name="startup_db_connection",
        category="startup",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        duration_seconds=sum(durations),
        iterations=iterations,
        avg_duration=stats["avg"],
        min_duration=stats["min"],
        max_duration=stats["max"],
        std_deviation=stats["std_dev"],
        memory_mb=sum(memory_usage) / len(memory_usage) if memory_usage else 0,
        metadata={
            "avg_connection_time_ms": stats["avg"] * 1000,
            "min_connection_time_ms": stats["min"] * 1000,
            "max_connection_time_ms": stats["max"] * 1000,
        },
    )

    print_benchmark_results(result)
    return result


def benchmark_app_initialization(
    iterations: int = 3, verbose: bool = False
) -> BenchmarkResult:
    """Benchmark full FastAPI application initialization."""
    print_benchmark_header(
        "FastAPI App Initialization",
        f"Measuring full application startup time over {iterations} iterations",
    )

    durations = []

    # Path to main application
    backend_dir = Path(__file__).parent.parent

    for i in range(iterations):
        if verbose:
            print(f"\n  Iteration {i + 1}/{iterations}...")

        start = time.perf_counter()

        # Run uvicorn in check mode (imports app but doesn't start server)
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from app.main import app; print('OK')",
            ],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        duration = time.perf_counter() - start
        durations.append(duration)

        if verbose:
            print(f"  Duration: {duration:.3f}s")
            if result.returncode != 0:
                print(f"  STDERR: {result.stderr[:200]}")

    stats = calculate_stats(durations)

    result = BenchmarkResult(
        benchmark_name="startup_app_init",
        category="startup",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        duration_seconds=sum(durations),
        iterations=iterations,
        avg_duration=stats["avg"],
        min_duration=stats["min"],
        max_duration=stats["max"],
        std_deviation=stats["std_dev"],
        metadata={
            "avg_init_time_s": stats["avg"],
            "cold_start_s": durations[0] if durations else 0,
            "warm_start_avg_s": sum(durations[1:]) / len(durations[1:])
            if len(durations) > 1
            else 0,
        },
    )

    print_benchmark_results(result)
    return result


def benchmark_config_loading(
    iterations: int = 100, verbose: bool = False
) -> BenchmarkResult:
    """Benchmark configuration loading time."""
    print_benchmark_header(
        "Configuration Loading",
        f"Measuring config loading time over {iterations} iterations",
    )

    durations = []

    for i in range(iterations):
        # Force reload of config module
        if "app.core.config" in sys.modules:
            del sys.modules["app.core.config"]

        start = time.perf_counter()

        from app.core.config import settings

        # Access a few settings to ensure full initialization
        _ = settings.DATABASE_URL
        _ = settings.SECRET_KEY
        _ = settings.DEBUG

        duration = time.perf_counter() - start
        durations.append(duration)

        if verbose and i % 20 == 0:
            print(f"  Iteration {i + 1}: {duration * 1000:.3f}ms")

    stats = calculate_stats(durations)

    result = BenchmarkResult(
        benchmark_name="startup_config_loading",
        category="startup",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        duration_seconds=sum(durations),
        iterations=iterations,
        avg_duration=stats["avg"],
        min_duration=stats["min"],
        max_duration=stats["max"],
        std_deviation=stats["std_dev"],
        metadata={
            "avg_config_load_ms": stats["avg"] * 1000,
            "min_config_load_ms": stats["min"] * 1000,
            "max_config_load_ms": stats["max"] * 1000,
        },
    )

    print_benchmark_results(result)
    return result


def run_suite(verbose: bool = False):
    """Run startup time benchmark suite."""
    print("=" * 80)
    print("STARTUP TIME BENCHMARK SUITE")
    print("=" * 80)
    print()

    results = []

    results.append(benchmark_config_loading(iterations=100, verbose=verbose))
    print()

    results.append(benchmark_import_time(verbose=verbose))
    print()

    results.append(benchmark_database_connection(iterations=10, verbose=verbose))
    print()

    results.append(benchmark_app_initialization(iterations=3, verbose=verbose))
    print()

    output_dir = Path(__file__).parent.parent.parent / "benchmark_results"
    for result in results:
        result.save(output_dir)

    print("\n" + "=" * 80)
    print("SUITE COMPLETE")
    print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Benchmark application startup time")
    parser.add_argument(
        "--benchmark",
        type=str,
        default="all",
        choices=["config", "import", "db", "app", "all"],
        help="Benchmark type",
    )
    parser.add_argument(
        "--iterations", type=int, default=10, help="Number of iterations"
    )
    parser.add_argument("--suite", action="store_true", help="Run full suite")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.suite:
        run_suite(verbose=args.verbose)
    else:
        if args.benchmark == "config" or args.benchmark == "all":
            result = benchmark_config_loading(
                iterations=args.iterations, verbose=args.verbose
            )

        if args.benchmark == "import" or args.benchmark == "all":
            result = benchmark_import_time(verbose=args.verbose)

        if args.benchmark == "db" or args.benchmark == "all":
            result = benchmark_database_connection(
                iterations=args.iterations, verbose=args.verbose
            )

        if args.benchmark == "app" or args.benchmark == "all":
            result = benchmark_app_initialization(
                iterations=min(args.iterations, 5), verbose=args.verbose
            )

        if args.benchmark != "all":
            output_dir = Path(__file__).parent.parent.parent / "benchmark_results"
            result.save(output_dir)


if __name__ == "__main__":
    main()
