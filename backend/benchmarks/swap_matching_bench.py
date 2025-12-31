"""
Swap Matching Benchmark

Measures the performance of the swap matching algorithm that finds
compatible swap candidates for faculty schedule exchange requests.

Metrics:
    - Match finding time for different program sizes
    - Algorithm scalability (O(n) vs O(n²) behavior)
    - Constraint validation overhead
    - Match quality scoring time

Usage:
    python -m benchmarks.swap_matching_bench
    python -m benchmarks.swap_matching_bench --faculty 100 --iterations 20
"""

import argparse
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.swap import SwapRequest
from app.services.swap_matcher import SwapMatcher
from benchmarks import (
    BenchmarkResult,
    calculate_stats,
    measure_performance,
    print_benchmark_header,
    print_benchmark_results,
)


def setup_swap_data(db, num_faculty: int = 30, num_weeks: int = 4):
    """Setup test data for swap matching benchmarks."""
    # Create template
    template = RotationTemplate(
        id=uuid4(),
        name="Clinical",
        activity_type="clinic",
        abbreviation="CLN",
    )
    db.add(template)

    # Create faculty
    faculty = []
    for i in range(num_faculty):
        fac = Person(
            id=uuid4(),
            name=f"Swap Faculty {i + 1}",
            type="faculty",
            email=f"swap.fac{i + 1}@test.org",
        )
        db.add(fac)
        faculty.append(fac)

    # Create blocks
    blocks = []
    start_date = date.today()
    for day_offset in range(num_weeks * 7):
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
    for fac in faculty:
        # Assign each faculty member to random blocks
        assigned_blocks = blocks[::3]  # Every 3rd block
        for block in assigned_blocks[:20]:  # Limit to 20 per faculty
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=fac.id,
                rotation_template_id=template.id,
                role="primary",
            )
            db.add(assignment)
            assignments.append(assignment)

    db.commit()

    return {
        "faculty": faculty,
        "blocks": blocks,
        "assignments": assignments,
        "template": template,
    }


def benchmark_swap_matching(
    num_faculty: int = 30,
    num_weeks: int = 4,
    iterations: int = 20,
    verbose: bool = False,
) -> BenchmarkResult:
    """Benchmark swap matching algorithm performance."""
    print_benchmark_header(
        f"Swap Matching ({num_faculty} faculty, {num_weeks} weeks)",
        f"Benchmarking swap match finding with {iterations} iterations",
    )

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)

    durations = []
    memory_usage = []
    matches_found = []

    for i in range(iterations):
        db = SessionLocal()

        try:
            test_data = setup_swap_data(db, num_faculty, num_weeks)
            faculty = test_data["faculty"]
            blocks = test_data["blocks"]

            # Create a swap request
            requester = faculty[i % len(faculty)]
            target_block = blocks[i % len(blocks)]

            swap_request = SwapRequest(
                id=uuid4(),
                requester_id=requester.id,
                original_block_id=target_block.id,
                desired_block_id=blocks[(i + 1) % len(blocks)].id,
                swap_type="one_to_one",
                status="pending",
            )
            db.add(swap_request)
            db.commit()

            # Benchmark matching
            with measure_performance("swap_matching") as metrics:
                matcher = SwapMatcher(db)
                candidates = matcher.find_swap_candidates(swap_request.id)

            durations.append(metrics["duration"])
            memory_usage.append(metrics["memory_delta_mb"])
            matches_found.append(len(candidates))

            if verbose:
                print(
                    f"  Iteration {i + 1}: {metrics['duration']:.3f}s, "
                    f"{len(candidates)} candidates"
                )

        finally:
            db.query(SwapRequest).delete()
            db.query(Assignment).delete()
            db.query(Block).delete()
            db.query(Person).delete()
            db.query(RotationTemplate).delete()
            db.commit()
            db.close()

    stats = calculate_stats(durations)

    result = BenchmarkResult(
        benchmark_name=f"swap_matching_{num_faculty}faculty_{num_weeks}wk",
        category="swap_matching",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        duration_seconds=sum(durations),
        iterations=iterations,
        avg_duration=stats["avg"],
        min_duration=stats["min"],
        max_duration=stats["max"],
        std_deviation=stats["std_dev"],
        throughput=num_faculty / stats["avg"] if stats["avg"] > 0 else 0,
        memory_mb=sum(memory_usage) / len(memory_usage) if memory_usage else 0,
        peak_memory_mb=max(memory_usage) if memory_usage else 0,
        metadata={
            "num_faculty": num_faculty,
            "num_weeks": num_weeks,
            "avg_matches": sum(matches_found) / len(matches_found)
            if matches_found
            else 0,
        },
    )

    print_benchmark_results(result)
    return result


def run_suite(verbose: bool = False):
    """Run swap matching benchmark suite."""
    print("=" * 80)
    print("SWAP MATCHING BENCHMARK SUITE")
    print("=" * 80)
    print()

    results = []

    for num_faculty in [10, 30, 50, 100]:
        results.append(
            benchmark_swap_matching(
                num_faculty=num_faculty,
                num_weeks=4,
                iterations=20,
                verbose=verbose,
            )
        )
        print()

    output_dir = Path(__file__).parent.parent.parent / "benchmark_results"
    for result in results:
        result.save(output_dir)

    print("\n" + "=" * 80)
    print("SUITE COMPLETE")
    print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Benchmark swap matching performance")
    parser.add_argument("--faculty", type=int, default=30, help="Number of faculty")
    parser.add_argument("--weeks", type=int, default=4, help="Number of weeks")
    parser.add_argument("--iterations", type=int, default=20, help="Number of iterations")
    parser.add_argument("--suite", action="store_true", help="Run full suite")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.suite:
        run_suite(verbose=args.verbose)
    else:
        result = benchmark_swap_matching(
            num_faculty=args.faculty,
            num_weeks=args.weeks,
            iterations=args.iterations,
            verbose=args.verbose,
        )

        output_dir = Path(__file__).parent.parent.parent / "benchmark_results"
        result.save(output_dir)


if __name__ == "__main__":
    main()
