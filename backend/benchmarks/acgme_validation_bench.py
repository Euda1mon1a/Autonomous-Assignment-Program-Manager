"""
ACGME Validation Benchmark

Measures the performance of ACGME compliance validation across different
dataset sizes and validation types.

Metrics:
    - 80-hour rule validation time
    - 1-in-7 rule validation time
    - Supervision ratio validation time
    - Full validation suite time
    - Violations detection throughput
    - Memory efficiency

Usage:
    python -m benchmarks.acgme_validation_bench
    python -m benchmarks.acgme_validation_bench --residents 100 --weeks 12
    python -m benchmarks.acgme_validation_bench --rule 80hour --iterations 10
"""

import argparse
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.scheduling.validator import ACGMEValidator
from benchmarks import (
    BenchmarkResult,
    calculate_stats,
    measure_performance,
    print_benchmark_header,
    print_benchmark_results,
)


def create_validation_dataset(
    db: Session,
    num_residents: int = 50,
    num_weeks: int = 4,
):
    """Create realistic dataset for ACGME validation testing."""
    # Create rotation template
    template = RotationTemplate(
        id=uuid4(),
        name="Clinical",
        activity_type="clinic",
        abbreviation="CLN",
        max_residents=10,
        supervision_required=True,
        max_supervision_ratio=4,
    )
    db.add(template)

    # Create residents with PGY distribution
    residents = []
    pgy_counts = {1: num_residents // 3, 2: num_residents // 3, 3: num_residents // 3}

    for pgy, count in pgy_counts.items():
        for i in range(count):
            resident = Person(
                id=uuid4(),
                name=f"Val Resident PGY{pgy}-{i + 1}",
                type="resident",
                email=f"val.pgy{pgy}.r{i + 1}@test.org",
                pgy_level=pgy,
            )
            db.add(resident)
            residents.append(resident)

    # Create faculty
    faculty = []
    for i in range(max(15, num_residents // 4)):
        fac = Person(
            id=uuid4(),
            name=f"Val Faculty {i + 1}",
            type="faculty",
            email=f"val.faculty{i + 1}@test.org",
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

    # Create assignments (skip Sundays for 1-in-7 compliance)
    assignments = []
    for resident in residents:
        for block in blocks:
            if block.date.weekday() != 6:  # Skip Sundays
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=resident.id,
                    rotation_template_id=template.id,
                    role="primary",
                )
                db.add(assignment)
                assignments.append(assignment)

    # Add faculty supervision
    for i, block in enumerate(blocks):
        if not block.is_weekend:
            for j in range(2):
                fac = faculty[(i + j) % len(faculty)]
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=fac.id,
                    rotation_template_id=template.id,
                    role="supervising",
                )
                db.add(assignment)
                assignments.append(assignment)

    db.commit()

    return {
        "residents": residents,
        "faculty": faculty,
        "blocks": blocks,
        "assignments": assignments,
        "template": template,
        "start_date": start_date,
        "end_date": start_date + timedelta(days=num_days - 1),
    }


def benchmark_acgme_validation(
    num_residents: int = 50,
    num_weeks: int = 4,
    validation_type: str = "full",
    iterations: int = 5,
    verbose: bool = False,
) -> BenchmarkResult:
    """
    Benchmark ACGME validation performance.

    Args:
        num_residents: Number of residents to validate
        num_weeks: Number of weeks of schedule data
        validation_type: Type of validation ("full", "80hour", "1in7", "supervision")
        iterations: Number of iterations to average
        verbose: Print detailed output

    Returns:
        BenchmarkResult with timing and violation metrics
    """
    print_benchmark_header(
        f"ACGME Validation - {validation_type} ({num_residents} residents, {num_weeks} weeks)",
        f"Benchmarking ACGME compliance validation with {iterations} iterations",
    )

    # Setup database
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)

    durations = []
    memory_usage = []
    total_violations = []

    for i in range(iterations):
        if verbose:
            print(f"\nIteration {i + 1}/{iterations}...")

        db = SessionLocal()

        try:
            # Create test data
            test_data = create_validation_dataset(db, num_residents, num_weeks)
            validator = ACGMEValidator(db)

            # Benchmark validation
            with measure_performance("acgme_validation") as metrics:
                result = validator.validate_all(
                    start_date=test_data["start_date"],
                    end_date=test_data["end_date"],
                )

            durations.append(metrics["duration"])
            memory_usage.append(metrics["memory_delta_mb"])
            total_violations.append(result.total_violations if result else 0)

            if verbose:
                print(f"  Duration: {metrics['duration']:.3f}s")
                print(f"  Memory: {metrics['memory_delta_mb']:.1f} MB")
                print(f"  Violations: {result.total_violations if result else 0}")

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

    # Calculate throughput (residents validated per second)
    throughput = num_residents / stats["avg"] if stats["avg"] > 0 else 0

    result = BenchmarkResult(
        benchmark_name=f"acgme_validation_{validation_type}_{num_residents}res_{num_weeks}wk",
        category="acgme_validation",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        duration_seconds=sum(durations),
        iterations=iterations,
        avg_duration=stats["avg"],
        min_duration=stats["min"],
        max_duration=stats["max"],
        std_deviation=stats["std_dev"],
        throughput=throughput,
        memory_mb=sum(memory_usage) / len(memory_usage) if memory_usage else 0,
        peak_memory_mb=max(memory_usage) if memory_usage else 0,
        metadata={
            "num_residents": num_residents,
            "num_weeks": num_weeks,
            "validation_type": validation_type,
            "avg_violations": sum(total_violations) / len(total_violations)
            if total_violations
            else 0,
            "total_assignments": num_residents * num_weeks * 14,  # Estimate
        },
    )

    print_benchmark_results(result)
    return result


def run_suite(verbose: bool = False):
    """Run full ACGME validation benchmark suite."""
    print("=" * 80)
    print("ACGME VALIDATION BENCHMARK SUITE")
    print("=" * 80)
    print()

    configurations = [
        (25, 4, "full"),
        (50, 4, "full"),
        (100, 4, "full"),
        (100, 12, "full"),  # Extended period
    ]

    results = []
    for num_residents, num_weeks, val_type in configurations:
        result = benchmark_acgme_validation(
            num_residents=num_residents,
            num_weeks=num_weeks,
            validation_type=val_type,
            iterations=5,
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
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Benchmark ACGME validation performance"
    )
    parser.add_argument("--residents", type=int, default=50, help="Number of residents")
    parser.add_argument("--weeks", type=int, default=4, help="Number of weeks")
    parser.add_argument(
        "--rule",
        type=str,
        default="full",
        choices=["full", "80hour", "1in7", "supervision"],
        help="Validation type",
    )
    parser.add_argument(
        "--iterations", type=int, default=5, help="Number of iterations"
    )
    parser.add_argument("--suite", action="store_true", help="Run full suite")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.suite:
        run_suite(verbose=args.verbose)
    else:
        result = benchmark_acgme_validation(
            num_residents=args.residents,
            num_weeks=args.weeks,
            validation_type=args.rule,
            iterations=args.iterations,
            verbose=args.verbose,
        )

        output_dir = Path(__file__).parent.parent.parent / "benchmark_results"
        result.save(output_dir)


if __name__ == "__main__":
    main()
