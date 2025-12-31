"""
Schedule Generation Benchmark

Measures the performance of the schedule generation engine under various
dataset sizes and constraint configurations.

Metrics:
    - Generation time for different program sizes (10, 25, 50, 100 residents)
    - Solver convergence time
    - Constraint evaluation overhead
    - Memory usage during generation
    - Success rate across iterations

Usage:
    python -m benchmarks.schedule_generation_bench
    python -m benchmarks.schedule_generation_bench --residents 50 --iterations 5
    python -m benchmarks.schedule_generation_bench --verbose
"""

import argparse
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.scheduling.engine import ScheduleGenerator
from app.scheduling.optimizer import ScheduleOptimizer
from benchmarks import (
    BenchmarkResult,
    calculate_stats,
    measure_performance,
    print_benchmark_header,
    print_benchmark_results,
)


def create_test_data(db: Session, num_residents: int, num_weeks: int = 4):
    """Create test dataset for benchmarking."""
    # Create rotation template
    template = RotationTemplate(
        id=uuid4(),
        name="Primary Care",
        activity_type="clinic",
        abbreviation="PC",
        max_residents=10,
        supervision_required=True,
    )
    db.add(template)

    # Create residents
    residents = []
    for pgy in [1, 2, 3]:
        count = num_residents // 3
        for i in range(count):
            resident = Person(
                id=uuid4(),
                name=f"Benchmark Resident PGY{pgy}-{i + 1}",
                type="resident",
                email=f"bench.pgy{pgy}.r{i + 1}@test.org",
                pgy_level=pgy,
                target_clinical_blocks=48,
            )
            db.add(resident)
            residents.append(resident)

    # Create faculty
    faculty = []
    num_faculty = max(10, num_residents // 5)
    for i in range(num_faculty):
        fac = Person(
            id=uuid4(),
            name=f"Benchmark Faculty {i + 1}",
            type="faculty",
            email=f"bench.faculty{i + 1}@test.org",
        )
        db.add(fac)
        faculty.append(fac)

    # Create blocks
    blocks = []
    start_date = date.today()
    num_days = num_weeks * 7

    for day_offset in range(num_days):
        current_date = start_date + timedelta(days=day_offset)
        is_weekend = current_date.weekday() >= 5

        for time_of_day in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=time_of_day,
                block_number=1,
                is_weekend=is_weekend,
            )
            db.add(block)
            blocks.append(block)

    db.commit()

    return {
        "residents": residents,
        "faculty": faculty,
        "blocks": blocks,
        "template": template,
        "start_date": start_date,
        "end_date": start_date + timedelta(days=num_days - 1),
    }


def benchmark_schedule_generation(
    num_residents: int = 25,
    num_weeks: int = 4,
    iterations: int = 3,
    verbose: bool = False,
) -> BenchmarkResult:
    """
    Benchmark schedule generation for a given program size.

    Args:
        num_residents: Number of residents to schedule
        num_weeks: Number of weeks to schedule
        iterations: Number of iterations to average
        verbose: Print detailed output

    Returns:
        BenchmarkResult with timing and memory metrics
    """
    print_benchmark_header(
        f"Schedule Generation ({num_residents} residents, {num_weeks} weeks)",
        f"Benchmarking schedule generation with {iterations} iterations",
    )

    # Setup database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)

    durations = []
    memory_usage = []
    success_count = 0
    total_assignments = 0

    for i in range(iterations):
        if verbose:
            print(f"\nIteration {i + 1}/{iterations}...")

        db = SessionLocal()

        try:
            # Create test data
            test_data = create_test_data(db, num_residents, num_weeks)

            # Benchmark generation
            with measure_performance("schedule_generation") as metrics:
                generator = ScheduleGenerator(db)

                result = generator.generate_schedule(
                    start_date=test_data["start_date"],
                    end_date=test_data["end_date"],
                    residents=test_data["residents"],
                    blocks=test_data["blocks"],
                )

            durations.append(metrics["duration"])
            memory_usage.append(metrics["memory_delta_mb"])

            if result and result.get("success"):
                success_count += 1
                total_assignments += len(result.get("assignments", []))

            if verbose:
                print(f"  Duration: {metrics['duration']:.3f}s")
                print(f"  Memory: {metrics['memory_delta_mb']:.1f} MB")
                print(f"  Success: {result.get('success', False)}")

        finally:
            # Cleanup
            db.query(Assignment).delete()
            db.query(Block).delete()
            db.query(Person).delete()
            db.query(RotationTemplate).delete()
            db.commit()
            db.close()

    # Calculate statistics
    stats = calculate_stats(durations)

    result = BenchmarkResult(
        benchmark_name=f"schedule_generation_{num_residents}res_{num_weeks}wk",
        category="schedule_generation",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        duration_seconds=sum(durations),
        iterations=iterations,
        avg_duration=stats["avg"],
        min_duration=stats["min"],
        max_duration=stats["max"],
        std_deviation=stats["std_dev"],
        throughput=num_residents / stats["avg"] if stats["avg"] > 0 else 0,
        memory_mb=sum(memory_usage) / len(memory_usage) if memory_usage else 0,
        peak_memory_mb=max(memory_usage) if memory_usage else 0,
        metadata={
            "num_residents": num_residents,
            "num_weeks": num_weeks,
            "success_rate": f"{(success_count / iterations * 100):.1f}%",
            "avg_assignments": total_assignments // iterations if iterations > 0 else 0,
        },
    )

    print_benchmark_results(result)
    return result


def run_suite(verbose: bool = False):
    """Run full benchmark suite across multiple program sizes."""
    print("=" * 80)
    print("SCHEDULE GENERATION BENCHMARK SUITE")
    print("=" * 80)
    print()

    sizes = [
        (10, 2),  # Small: 10 residents, 2 weeks
        (25, 4),  # Medium: 25 residents, 4 weeks
        (50, 4),  # Large: 50 residents, 4 weeks
        (100, 4),  # Very large: 100 residents, 4 weeks
    ]

    results = []
    for num_residents, num_weeks in sizes:
        result = benchmark_schedule_generation(
            num_residents=num_residents,
            num_weeks=num_weeks,
            iterations=3,
            verbose=verbose,
        )
        results.append(result)
        print()

    # Save results
    output_dir = Path(__file__).parent.parent.parent / "benchmark_results"
    for result in results:
        result.save(output_dir)

    print("\n" + "=" * 80)
    print("SUITE COMPLETE")
    print("=" * 80)


def main():
    """Main entry point for benchmark."""
    parser = argparse.ArgumentParser(
        description="Benchmark schedule generation performance"
    )
    parser.add_argument(
        "--residents",
        type=int,
        default=25,
        help="Number of residents (default: 25)",
    )
    parser.add_argument(
        "--weeks",
        type=int,
        default=4,
        help="Number of weeks (default: 4)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Number of iterations (default: 3)",
    )
    parser.add_argument(
        "--suite",
        action="store_true",
        help="Run full benchmark suite",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    if args.suite:
        run_suite(verbose=args.verbose)
    else:
        result = benchmark_schedule_generation(
            num_residents=args.residents,
            num_weeks=args.weeks,
            iterations=args.iterations,
            verbose=args.verbose,
        )

        # Save result
        output_dir = Path(__file__).parent.parent.parent / "benchmark_results"
        result.save(output_dir)


if __name__ == "__main__":
    main()
