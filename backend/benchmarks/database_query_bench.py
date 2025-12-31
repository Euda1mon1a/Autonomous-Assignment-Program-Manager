"""
Database Query Benchmark

Measures database query performance, connection pooling efficiency,
and ORM overhead for common operations.

Metrics:
    - Single record query time
    - Bulk query performance
    - Join query optimization
    - Insert/update throughput
    - Connection pool efficiency
    - Query cache effectiveness

Usage:
    python -m benchmarks.database_query_bench
    python -m benchmarks.database_query_bench --query-type joins --iterations 100
    python -m benchmarks.database_query_bench --suite
"""

import argparse
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, joinedload, selectinload, sessionmaker

from app.core.config import settings
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from benchmarks import (
    BenchmarkResult,
    calculate_stats,
    measure_performance,
    print_benchmark_header,
    print_benchmark_results,
)


def setup_test_data(db: Session, num_records: int = 1000):
    """Setup test data for query benchmarks."""
    # Create templates
    templates = []
    for i in range(5):
        template = RotationTemplate(
            id=uuid4(),
            name=f"Template {i + 1}",
            activity_type="clinic",
            abbreviation=f"T{i + 1}",
        )
        db.add(template)
        templates.append(template)

    # Create people
    people = []
    for i in range(num_records // 10):
        person = Person(
            id=uuid4(),
            name=f"Person {i + 1}",
            type="resident" if i % 2 == 0 else "faculty",
            email=f"person{i + 1}@test.org",
            pgy_level=(i % 3) + 1 if i % 2 == 0 else None,
        )
        db.add(person)
        people.append(person)

    # Create blocks
    blocks = []
    start_date = date.today()
    for day_offset in range(num_records // 20):
        current_date = start_date + timedelta(days=day_offset)
        for time_of_day in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=time_of_day,
                block_number=1,
                is_weekend=(current_date.weekday() >= 5),
            )
            db.add(block)
            blocks.append(block)

    db.commit()

    # Create assignments
    assignments = []
    for i in range(num_records):
        assignment = Assignment(
            id=uuid4(),
            block_id=blocks[i % len(blocks)].id,
            person_id=people[i % len(people)].id,
            rotation_template_id=templates[i % len(templates)].id,
            role="primary" if i % 3 == 0 else "backup",
        )
        db.add(assignment)
        assignments.append(assignment)

    db.commit()

    return {
        "people": people,
        "blocks": blocks,
        "templates": templates,
        "assignments": assignments,
    }


def benchmark_simple_queries(
    iterations: int = 100, verbose: bool = False
) -> BenchmarkResult:
    """Benchmark simple SELECT queries."""
    print_benchmark_header(
        "Simple Query Performance",
        f"Benchmarking single-record and simple queries with {iterations} iterations",
    )

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)

    durations = []

    db = SessionLocal()
    try:
        # Setup test data
        test_data = setup_test_data(db, num_records=1000)
        person_ids = [p.id for p in test_data["people"][:100]]

        # Benchmark
        for i in range(iterations):
            person_id = person_ids[i % len(person_ids)]

            with measure_performance("simple_query") as metrics:
                result = db.execute(
                    select(Person).where(Person.id == person_id)
                ).scalar_one_or_none()

            durations.append(metrics["duration"])

            if verbose and i % 20 == 0:
                print(f"  Iteration {i + 1}: {metrics['duration']:.6f}s")

    finally:
        # Cleanup
        db.query(Assignment).delete()
        db.query(Block).delete()
        db.query(Person).delete()
        db.query(RotationTemplate).delete()
        db.commit()
        db.close()

    stats = calculate_stats(durations)

    result = BenchmarkResult(
        benchmark_name="database_simple_queries",
        category="database",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        duration_seconds=sum(durations),
        iterations=iterations,
        avg_duration=stats["avg"],
        min_duration=stats["min"],
        max_duration=stats["max"],
        std_deviation=stats["std_dev"],
        throughput=1 / stats["avg"] if stats["avg"] > 0 else 0,
        metadata={"query_type": "simple_select"},
    )

    print_benchmark_results(result)
    return result


def benchmark_join_queries(
    iterations: int = 50, verbose: bool = False
) -> BenchmarkResult:
    """Benchmark complex JOIN queries with relationships."""
    print_benchmark_header(
        "Join Query Performance",
        f"Benchmarking multi-table JOIN queries with {iterations} iterations",
    )

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)

    durations = []
    eager_durations = []
    lazy_durations = []

    db = SessionLocal()
    try:
        # Setup test data
        test_data = setup_test_data(db, num_records=1000)

        # Benchmark eager loading (joinedload)
        for i in range(iterations):
            with measure_performance("eager_join") as metrics:
                result = (
                    db.execute(
                        select(Assignment)
                        .options(
                            joinedload(Assignment.person),
                            joinedload(Assignment.block),
                            joinedload(Assignment.rotation_template),
                        )
                        .limit(50)
                    )
                    .scalars()
                    .all()
                )

            eager_durations.append(metrics["duration"])

            if verbose and i % 10 == 0:
                print(f"  Eager load {i + 1}: {metrics['duration']:.6f}s")

        # Benchmark lazy loading (selectinload)
        for i in range(iterations):
            with measure_performance("lazy_join") as metrics:
                result = (
                    db.execute(
                        select(Assignment)
                        .options(
                            selectinload(Assignment.person),
                            selectinload(Assignment.block),
                            selectinload(Assignment.rotation_template),
                        )
                        .limit(50)
                    )
                    .scalars()
                    .all()
                )

            lazy_durations.append(metrics["duration"])

    finally:
        # Cleanup
        db.query(Assignment).delete()
        db.query(Block).delete()
        db.query(Person).delete()
        db.query(RotationTemplate).delete()
        db.commit()
        db.close()

    eager_stats = calculate_stats(eager_durations)
    lazy_stats = calculate_stats(lazy_durations)

    result = BenchmarkResult(
        benchmark_name="database_join_queries",
        category="database",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        duration_seconds=sum(eager_durations) + sum(lazy_durations),
        iterations=iterations * 2,
        avg_duration=(eager_stats["avg"] + lazy_stats["avg"]) / 2,
        min_duration=min(eager_stats["min"], lazy_stats["min"]),
        max_duration=max(eager_stats["max"], lazy_stats["max"]),
        std_deviation=(eager_stats["std_dev"] + lazy_stats["std_dev"]) / 2,
        throughput=50 / eager_stats["avg"] if eager_stats["avg"] > 0 else 0,
        metadata={
            "query_type": "joins",
            "eager_avg": f"{eager_stats['avg']:.6f}s",
            "lazy_avg": f"{lazy_stats['avg']:.6f}s",
            "speedup": f"{(lazy_stats['avg'] / eager_stats['avg']):.2f}x"
            if eager_stats["avg"] > 0
            else "N/A",
        },
    )

    print_benchmark_results(result)
    return result


def benchmark_bulk_operations(
    batch_size: int = 100, iterations: int = 10, verbose: bool = False
) -> BenchmarkResult:
    """Benchmark bulk insert/update operations."""
    print_benchmark_header(
        f"Bulk Operations (batch size: {batch_size})",
        f"Benchmarking bulk inserts and updates with {iterations} iterations",
    )

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)

    insert_durations = []
    update_durations = []

    db = SessionLocal()
    try:
        # Create minimal dependencies
        template = RotationTemplate(
            id=uuid4(),
            name="Bulk Test",
            activity_type="clinic",
            abbreviation="BT",
        )
        db.add(template)
        db.commit()

        for i in range(iterations):
            # Benchmark bulk insert
            with measure_performance("bulk_insert") as metrics:
                people = []
                for j in range(batch_size):
                    person = Person(
                        id=uuid4(),
                        name=f"Bulk Person {i}-{j}",
                        type="resident",
                        email=f"bulk{i}_{j}@test.org",
                        pgy_level=1,
                    )
                    people.append(person)

                db.bulk_save_objects(people)
                db.commit()

            insert_durations.append(metrics["duration"])

            if verbose:
                print(
                    f"  Insert batch {i + 1}: {metrics['duration']:.6f}s ({batch_size / metrics['duration']:.0f} ops/sec)"
                )

            # Benchmark bulk update
            with measure_performance("bulk_update") as metrics:
                db.execute(
                    select(Person).where(Person.email.like(f"bulk{i}_%"))
                ).scalars().all()

                # Update all records
                for person in people:
                    person.name = f"Updated {person.name}"

                db.commit()

            update_durations.append(metrics["duration"])

            # Cleanup after each iteration
            db.query(Person).filter(Person.email.like(f"bulk{i}_%")).delete()
            db.commit()

    finally:
        # Final cleanup
        db.query(Person).delete()
        db.query(RotationTemplate).delete()
        db.commit()
        db.close()

    insert_stats = calculate_stats(insert_durations)
    update_stats = calculate_stats(update_durations)

    result = BenchmarkResult(
        benchmark_name=f"database_bulk_operations_batch{batch_size}",
        category="database",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        duration_seconds=sum(insert_durations) + sum(update_durations),
        iterations=iterations * 2,
        avg_duration=(insert_stats["avg"] + update_stats["avg"]) / 2,
        min_duration=min(insert_stats["min"], update_stats["min"]),
        max_duration=max(insert_stats["max"], update_stats["max"]),
        std_deviation=(insert_stats["std_dev"] + update_stats["std_dev"]) / 2,
        throughput=batch_size / insert_stats["avg"] if insert_stats["avg"] > 0 else 0,
        metadata={
            "batch_size": batch_size,
            "insert_avg": f"{insert_stats['avg']:.6f}s",
            "update_avg": f"{update_stats['avg']:.6f}s",
            "insert_throughput": f"{batch_size / insert_stats['avg']:.0f} ops/sec"
            if insert_stats["avg"] > 0
            else "N/A",
        },
    )

    print_benchmark_results(result)
    return result


def run_suite(verbose: bool = False):
    """Run full database benchmark suite."""
    print("=" * 80)
    print("DATABASE BENCHMARK SUITE")
    print("=" * 80)
    print()

    results = []

    # Simple queries
    results.append(benchmark_simple_queries(iterations=100, verbose=verbose))
    print()

    # Join queries
    results.append(benchmark_join_queries(iterations=50, verbose=verbose))
    print()

    # Bulk operations
    for batch_size in [50, 100, 500]:
        results.append(
            benchmark_bulk_operations(
                batch_size=batch_size, iterations=10, verbose=verbose
            )
        )
        print()

    # Save results
    output_dir = Path(__file__).parent.parent.parent / "benchmark_results"
    for result in results:
        result.save(output_dir)

    print("\n" + "=" * 80)
    print("SUITE COMPLETE")
    print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Benchmark database query performance")
    parser.add_argument(
        "--query-type",
        type=str,
        default="simple",
        choices=["simple", "joins", "bulk"],
        help="Query type to benchmark",
    )
    parser.add_argument(
        "--iterations", type=int, default=100, help="Number of iterations"
    )
    parser.add_argument(
        "--batch-size", type=int, default=100, help="Batch size for bulk operations"
    )
    parser.add_argument("--suite", action="store_true", help="Run full suite")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.suite:
        run_suite(verbose=args.verbose)
    else:
        if args.query_type == "simple":
            result = benchmark_simple_queries(
                iterations=args.iterations, verbose=args.verbose
            )
        elif args.query_type == "joins":
            result = benchmark_join_queries(
                iterations=args.iterations, verbose=args.verbose
            )
        elif args.query_type == "bulk":
            result = benchmark_bulk_operations(
                batch_size=args.batch_size,
                iterations=args.iterations,
                verbose=args.verbose,
            )

        output_dir = Path(__file__).parent.parent.parent / "benchmark_results"
        result.save(output_dir)


if __name__ == "__main__":
    main()
