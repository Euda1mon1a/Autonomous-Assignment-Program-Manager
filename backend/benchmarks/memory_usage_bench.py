"""
Memory Usage Benchmark

Tracks memory consumption patterns for various operations to detect
memory leaks, inefficient object retention, and peak memory usage.

Metrics:
    - Baseline memory footprint
    - Memory growth during operations
    - Peak memory usage
    - Memory leaks detection
    - GC pressure and collection frequency

Usage:
    python -m benchmarks.memory_usage_bench
    python -m benchmarks.memory_usage_bench --operation schedule_generation
"""

import argparse
import gc
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

import psutil

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.scheduling.engine import ScheduleGenerator
from app.scheduling.validator import ACGMEValidator
from benchmarks import (
    BenchmarkResult,
    print_benchmark_header,
    print_benchmark_results,
)


def get_memory_info():
    """Get current process memory information in MB."""
    process = psutil.Process()
    mem_info = process.memory_info()
    return {
        "rss_mb": mem_info.rss / 1024 / 1024,  # Resident Set Size
        "vms_mb": mem_info.vms / 1024 / 1024,  # Virtual Memory Size
        "percent": process.memory_percent(),
    }


def force_gc():
    """Force garbage collection and return stats."""
    gc.collect()
    gc.collect()
    gc.collect()
    return {
        "objects": len(gc.get_objects()),
        "garbage": len(gc.garbage),
    }


def benchmark_schedule_generation_memory(
    iterations: int = 10, verbose: bool = False
) -> BenchmarkResult:
    """Benchmark memory usage during schedule generation."""
    print_benchmark_header(
        "Schedule Generation Memory Usage",
        f"Tracking memory consumption across {iterations} schedule generations",
    )

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)

    # Get baseline memory
    force_gc()
    baseline = get_memory_info()

    print(f"Baseline Memory: {baseline['rss_mb']:.1f} MB")

    memory_samples = []
    peak_memory = baseline["rss_mb"]

    for i in range(iterations):
        db = SessionLocal()

        try:
            # Create test data
            template = RotationTemplate(
                id=uuid4(),
                name="Memory Test",
                activity_type="clinic",
                abbreviation="MT",
            )
            db.add(template)

            residents = []
            for j in range(50):
                resident = Person(
                    id=uuid4(),
                    name=f"Mem Resident {j + 1}",
                    type="resident",
                    email=f"mem.res{j + 1}@test.org",
                    pgy_level=(j % 3) + 1,
                )
                db.add(resident)
                residents.append(resident)

            blocks = []
            start_date = date.today()
            for day in range(28):
                current_date = start_date + timedelta(days=day)
                for tod in ["AM", "PM"]:
                    block = Block(
                        id=uuid4(),
                        date=current_date,
                        time_of_day=tod,
                        block_number=1,
                        is_weekend=(current_date.weekday() >= 5),
                    )
                    db.add(block)
                    blocks.append(block)

            db.commit()

            # Generate schedule
            generator = ScheduleGenerator(db)
            result = generator.generate_schedule(
                start_date=start_date,
                end_date=start_date + timedelta(days=27),
                residents=residents,
                blocks=blocks,
            )

            # Sample memory
            current_mem = get_memory_info()
            memory_samples.append(current_mem["rss_mb"])
            peak_memory = max(peak_memory, current_mem["rss_mb"])

            if verbose:
                print(
                    f"  Iteration {i + 1}: {current_mem['rss_mb']:.1f} MB "
                    f"(+{current_mem['rss_mb'] - baseline['rss_mb']:.1f} MB)"
                )

        finally:
            # Cleanup
            db.query(Assignment).delete()
            db.query(Block).delete()
            db.query(Person).delete()
            db.query(RotationTemplate).delete()
            db.commit()
            db.close()

            # Force GC between iterations
            force_gc()

    # Final memory check
    final_mem = get_memory_info()
    memory_leak = final_mem["rss_mb"] - baseline["rss_mb"]

    print(f"\nFinal Memory: {final_mem['rss_mb']:.1f} MB")
    print(f"Peak Memory: {peak_memory:.1f} MB")
    print(f"Memory Growth: {memory_leak:.1f} MB")

    if memory_leak > 50:
        print(
            f"⚠️  WARNING: Possible memory leak detected ({memory_leak:.1f} MB growth)"
        )

    result = BenchmarkResult(
        benchmark_name="memory_schedule_generation",
        category="memory",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        duration_seconds=0,  # Not time-based
        iterations=iterations,
        avg_duration=0,
        min_duration=0,
        max_duration=0,
        std_deviation=0,
        memory_mb=final_mem["rss_mb"],
        peak_memory_mb=peak_memory,
        metadata={
            "baseline_mb": baseline["rss_mb"],
            "final_mb": final_mem["rss_mb"],
            "growth_mb": memory_leak,
            "peak_mb": peak_memory,
            "avg_per_iteration_mb": sum(memory_samples) / len(memory_samples)
            if memory_samples
            else 0,
            "leak_detected": memory_leak > 50,
        },
    )

    print_benchmark_results(result)
    return result


def benchmark_validation_memory(
    iterations: int = 20, verbose: bool = False
) -> BenchmarkResult:
    """Benchmark memory usage during ACGME validation."""
    print_benchmark_header(
        "ACGME Validation Memory Usage",
        f"Tracking memory consumption across {iterations} validations",
    )

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)

    force_gc()
    baseline = get_memory_info()

    print(f"Baseline Memory: {baseline['rss_mb']:.1f} MB")

    memory_samples = []
    peak_memory = baseline["rss_mb"]

    # Create persistent test data
    db = SessionLocal()
    try:
        template = RotationTemplate(
            id=uuid4(),
            name="Val Memory Test",
            activity_type="clinic",
            abbreviation="VMT",
        )
        db.add(template)

        residents = []
        for i in range(100):
            resident = Person(
                id=uuid4(),
                name=f"Val Mem Resident {i + 1}",
                type="resident",
                email=f"valmem.res{i + 1}@test.org",
                pgy_level=(i % 3) + 1,
            )
            db.add(resident)
            residents.append(resident)

        blocks = []
        start_date = date.today()
        for day in range(28):
            current_date = start_date + timedelta(days=day)
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current_date,
                    time_of_day=tod,
                    block_number=1,
                    is_weekend=(current_date.weekday() >= 5),
                )
                db.add(block)
                blocks.append(block)

        db.commit()

        # Create assignments
        for resident in residents:
            for block in blocks:
                if block.date.weekday() != 6:
                    assignment = Assignment(
                        id=uuid4(),
                        block_id=block.id,
                        person_id=resident.id,
                        rotation_template_id=template.id,
                        role="primary",
                    )
                    db.add(assignment)

        db.commit()

        # Run validations
        validator = ACGMEValidator(db)
        end_date = start_date + timedelta(days=27)

        for i in range(iterations):
            result = validator.validate_all(start_date, end_date)

            # Sample memory
            current_mem = get_memory_info()
            memory_samples.append(current_mem["rss_mb"])
            peak_memory = max(peak_memory, current_mem["rss_mb"])

            if verbose and i % 5 == 0:
                print(
                    f"  Iteration {i + 1}: {current_mem['rss_mb']:.1f} MB "
                    f"(+{current_mem['rss_mb'] - baseline['rss_mb']:.1f} MB)"
                )

            # Force GC periodically
            if i % 5 == 0:
                force_gc()

    finally:
        db.query(Assignment).delete()
        db.query(Block).delete()
        db.query(Person).delete()
        db.query(RotationTemplate).delete()
        db.commit()
        db.close()

    final_mem = get_memory_info()
    memory_leak = final_mem["rss_mb"] - baseline["rss_mb"]

    print(f"\nFinal Memory: {final_mem['rss_mb']:.1f} MB")
    print(f"Peak Memory: {peak_memory:.1f} MB")
    print(f"Memory Growth: {memory_leak:.1f} MB")

    result = BenchmarkResult(
        benchmark_name="memory_acgme_validation",
        category="memory",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        duration_seconds=0,
        iterations=iterations,
        avg_duration=0,
        min_duration=0,
        max_duration=0,
        std_deviation=0,
        memory_mb=final_mem["rss_mb"],
        peak_memory_mb=peak_memory,
        metadata={
            "baseline_mb": baseline["rss_mb"],
            "final_mb": final_mem["rss_mb"],
            "growth_mb": memory_leak,
            "peak_mb": peak_memory,
            "avg_per_iteration_mb": sum(memory_samples) / len(memory_samples)
            if memory_samples
            else 0,
        },
    )

    print_benchmark_results(result)
    return result


def run_suite(verbose: bool = False):
    """Run memory usage benchmark suite."""
    print("=" * 80)
    print("MEMORY USAGE BENCHMARK SUITE")
    print("=" * 80)
    print()

    results = []

    results.append(benchmark_schedule_generation_memory(iterations=10, verbose=verbose))
    print()

    results.append(benchmark_validation_memory(iterations=20, verbose=verbose))
    print()

    output_dir = Path(__file__).parent.parent.parent / "benchmark_results"
    for result in results:
        result.save(output_dir)

    print("\n" + "=" * 80)
    print("SUITE COMPLETE")
    print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Benchmark memory usage")
    parser.add_argument(
        "--operation",
        type=str,
        default="schedule",
        choices=["schedule", "validation"],
        help="Operation to benchmark",
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
        if args.operation == "schedule":
            result = benchmark_schedule_generation_memory(
                iterations=args.iterations, verbose=args.verbose
            )
        else:
            result = benchmark_validation_memory(
                iterations=args.iterations, verbose=args.verbose
            )

        output_dir = Path(__file__).parent.parent.parent / "benchmark_results"
        result.save(output_dir)


if __name__ == "__main__":
    main()
