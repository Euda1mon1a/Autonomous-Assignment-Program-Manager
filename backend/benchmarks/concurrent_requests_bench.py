"""
Concurrent Requests Benchmark

Measures API throughput and performance under concurrent load without
using external HTTP requests. Tests database connection pooling, async
operation handling, and concurrent transaction management.

Metrics:
    - Concurrent database operations throughput
    - Connection pool efficiency
    - Lock contention under concurrent writes
    - Async task queue processing rate

Usage:
    python -m benchmarks.concurrent_requests_bench
    python -m benchmarks.concurrent_requests_bench --workers 50 --duration 30
"""

import argparse
import asyncio
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from benchmarks import (
    BenchmarkResult,
    calculate_stats,
    print_benchmark_header,
    print_benchmark_results,
)


async def concurrent_read_operation(session: AsyncSession, person_id: str) -> bool:
    """Simulate a concurrent read operation."""
    try:
        result = await session.execute(select(Person).where(Person.id == person_id))
        person = result.scalar_one_or_none()
        return person is not None
    except Exception:
        return False


async def concurrent_write_operation(session: AsyncSession, person_id: str) -> bool:
    """Simulate a concurrent write operation."""
    try:
        result = await session.execute(select(Person).where(Person.id == person_id))
        person = result.scalar_one_or_none()

        if person:
            person.name = f"Updated {person.name}"
            await session.commit()
            return True
        return False
    except Exception:
        await session.rollback()
        return False


async def benchmark_concurrent_reads(
    num_workers: int = 20,
    duration_seconds: int = 10,
    verbose: bool = False,
) -> BenchmarkResult:
    """Benchmark concurrent read operations."""
    print_benchmark_header(
        f"Concurrent Reads ({num_workers} workers, {duration_seconds}s)",
        "Benchmarking concurrent database read operations",
    )

    # Setup async database
    async_engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        pool_size=num_workers,
        max_overflow=num_workers * 2,
    )
    AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    # Setup test data (using sync engine)
    sync_engine = create_engine(settings.DATABASE_URL)
    SyncSession = sessionmaker(bind=sync_engine)
    db = SyncSession()

    try:
        # Create test people
        people = []
        for i in range(100):
            person = Person(
                id=uuid4(),
                name=f"Concurrent Person {i + 1}",
                type="resident",
                email=f"concurrent{i + 1}@test.org",
                pgy_level=1,
            )
            db.add(person)
            people.append(person)
        db.commit()

        person_ids = [str(p.id) for p in people]

        # Run concurrent operations
        total_operations = 0
        successful_operations = 0
        start_time = time.perf_counter()
        operation_times = []

        async def worker(worker_id: int):
            nonlocal total_operations, successful_operations

            async with AsyncSessionLocal() as session:
                worker_start = time.perf_counter()
                worker_ops = 0

                while (time.perf_counter() - start_time) < duration_seconds:
                    person_id = person_ids[worker_ops % len(person_ids)]
                    op_start = time.perf_counter()

                    success = await concurrent_read_operation(session, person_id)

                    op_duration = time.perf_counter() - op_start
                    operation_times.append(op_duration)

                    total_operations += 1
                    if success:
                        successful_operations += 1
                    worker_ops += 1

                worker_duration = time.perf_counter() - worker_start
                if verbose:
                    print(
                        f"  Worker {worker_id}: {worker_ops} ops in {worker_duration:.3f}s "
                        f"({worker_ops / worker_duration:.1f} ops/sec)"
                    )

        # Run workers concurrently
        await asyncio.gather(*[worker(i) for i in range(num_workers)])

        total_duration = time.perf_counter() - start_time
        throughput = total_operations / total_duration

        stats = calculate_stats(operation_times)

        result = BenchmarkResult(
            benchmark_name=f"concurrent_reads_{num_workers}workers",
            category="concurrent",
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            duration_seconds=total_duration,
            iterations=total_operations,
            avg_duration=stats["avg"],
            min_duration=stats["min"],
            max_duration=stats["max"],
            std_deviation=stats["std_dev"],
            throughput=throughput,
            metadata={
                "num_workers": num_workers,
                "total_operations": total_operations,
                "successful_operations": successful_operations,
                "success_rate": f"{(successful_operations / total_operations * 100):.1f}%"
                if total_operations > 0
                else "N/A",
                "target_duration": duration_seconds,
            },
        )

        print_benchmark_results(result)
        return result

    finally:
        # Cleanup
        db.query(Person).delete()
        db.commit()
        db.close()
        await async_engine.dispose()


async def benchmark_concurrent_writes(
    num_workers: int = 10,
    duration_seconds: int = 10,
    verbose: bool = False,
) -> BenchmarkResult:
    """Benchmark concurrent write operations (with lock contention)."""
    print_benchmark_header(
        f"Concurrent Writes ({num_workers} workers, {duration_seconds}s)",
        "Benchmarking concurrent database write operations with lock contention",
    )

    # Setup async database
    async_engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        pool_size=num_workers,
        max_overflow=num_workers * 2,
    )
    AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    # Setup test data
    sync_engine = create_engine(settings.DATABASE_URL)
    SyncSession = sessionmaker(bind=sync_engine)
    db = SyncSession()

    try:
        # Create test people
        people = []
        for i in range(50):
            person = Person(
                id=uuid4(),
                name=f"Concurrent Write Person {i + 1}",
                type="faculty",
                email=f"conwrite{i + 1}@test.org",
            )
            db.add(person)
            people.append(person)
        db.commit()

        person_ids = [str(p.id) for p in people]

        # Run concurrent write operations
        total_operations = 0
        successful_operations = 0
        start_time = time.perf_counter()
        operation_times = []

        async def worker(worker_id: int):
            nonlocal total_operations, successful_operations

            worker_start = time.perf_counter()
            worker_ops = 0

            while (time.perf_counter() - start_time) < duration_seconds:
                person_id = person_ids[worker_ops % len(person_ids)]

                async with AsyncSessionLocal() as session:
                    op_start = time.perf_counter()
                    success = await concurrent_write_operation(session, person_id)
                    op_duration = time.perf_counter() - op_start

                    operation_times.append(op_duration)
                    total_operations += 1
                    if success:
                        successful_operations += 1
                    worker_ops += 1

            worker_duration = time.perf_counter() - worker_start
            if verbose:
                print(
                    f"  Worker {worker_id}: {worker_ops} ops in {worker_duration:.3f}s "
                    f"({worker_ops / worker_duration:.1f} ops/sec)"
                )

        # Run workers
        await asyncio.gather(*[worker(i) for i in range(num_workers)])

        total_duration = time.perf_counter() - start_time
        throughput = total_operations / total_duration

        stats = calculate_stats(operation_times)

        result = BenchmarkResult(
            benchmark_name=f"concurrent_writes_{num_workers}workers",
            category="concurrent",
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            duration_seconds=total_duration,
            iterations=total_operations,
            avg_duration=stats["avg"],
            min_duration=stats["min"],
            max_duration=stats["max"],
            std_deviation=stats["std_dev"],
            throughput=throughput,
            metadata={
                "num_workers": num_workers,
                "total_operations": total_operations,
                "successful_operations": successful_operations,
                "success_rate": f"{(successful_operations / total_operations * 100):.1f}%"
                if total_operations > 0
                else "N/A",
            },
        )

        print_benchmark_results(result)
        return result

    finally:
        # Cleanup
        db.query(Person).delete()
        db.commit()
        db.close()
        await async_engine.dispose()


def run_suite(verbose: bool = False):
    """Run concurrent requests benchmark suite."""
    print("=" * 80)
    print("CONCURRENT REQUESTS BENCHMARK SUITE")
    print("=" * 80)
    print()

    results = []

    async def run_async_suite():
        # Concurrent reads with varying worker counts
        for num_workers in [10, 20, 50]:
            result = await benchmark_concurrent_reads(
                num_workers=num_workers, duration_seconds=10, verbose=verbose
            )
            results.append(result)
            print()

        # Concurrent writes (lower worker count due to lock contention)
        for num_workers in [5, 10, 20]:
            result = await benchmark_concurrent_writes(
                num_workers=num_workers, duration_seconds=10, verbose=verbose
            )
            results.append(result)
            print()

    asyncio.run(run_async_suite())

    # Save results
    output_dir = Path(__file__).parent.parent.parent / "benchmark_results"
    for result in results:
        result.save(output_dir)

    print("\n" + "=" * 80)
    print("SUITE COMPLETE")
    print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Benchmark concurrent request performance")
    parser.add_argument("--workers", type=int, default=20, help="Number of concurrent workers")
    parser.add_argument("--duration", type=int, default=10, help="Test duration in seconds")
    parser.add_argument(
        "--operation",
        type=str,
        default="reads",
        choices=["reads", "writes"],
        help="Operation type",
    )
    parser.add_argument("--suite", action="store_true", help="Run full suite")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.suite:
        run_suite(verbose=args.verbose)
    else:

        async def run_single():
            if args.operation == "reads":
                result = await benchmark_concurrent_reads(
                    num_workers=args.workers,
                    duration_seconds=args.duration,
                    verbose=args.verbose,
                )
            else:
                result = await benchmark_concurrent_writes(
                    num_workers=args.workers,
                    duration_seconds=args.duration,
                    verbose=args.verbose,
                )

            output_dir = Path(__file__).parent.parent.parent / "benchmark_results"
            result.save(output_dir)

        asyncio.run(run_single())


if __name__ == "__main__":
    main()
