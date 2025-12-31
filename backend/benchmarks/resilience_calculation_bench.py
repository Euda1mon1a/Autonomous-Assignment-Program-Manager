"""
Resilience Calculation Benchmark

Measures the performance of resilience framework calculations including:
- N-1/N-2 contingency analysis
- Utilization metrics
- Burnout epidemiology (SIR model, Rt calculation)
- SPC monitoring (Western Electric rules)
- Erlang C coverage analysis

Metrics:
    - Contingency analysis time
    - Burnout model computation time
    - SPC chart generation time
    - Unified critical index calculation
    - Memory efficiency for graph operations

Usage:
    python -m benchmarks.resilience_calculation_bench
    python -m benchmarks.resilience_calculation_bench --metric n1 --iterations 20
    python -m benchmarks.resilience_calculation_bench --suite
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
from app.resilience.contingency import N1ContingencyAnalyzer, N2ContingencyAnalyzer
from app.resilience.burnout_epidemiology import BurnoutEpidemiologyModel
from app.resilience.spc_monitoring import SPCMonitor
from app.resilience.utilization import UtilizationTracker
from app.resilience.unified_critical_index import UnifiedCriticalIndex
from benchmarks import (
    BenchmarkResult,
    calculate_stats,
    measure_performance,
    print_benchmark_header,
    print_benchmark_results,
)


def setup_resilience_data(db: Session, num_people: int = 50, num_weeks: int = 4):
    """Setup test data for resilience calculations."""
    # Create rotation template
    template = RotationTemplate(
        id=uuid4(),
        name="Clinical",
        activity_type="clinic",
        abbreviation="CLN",
    )
    db.add(template)

    # Create people
    people = []
    for i in range(num_people):
        person = Person(
            id=uuid4(),
            name=f"Resilience Person {i + 1}",
            type="resident" if i % 3 != 0 else "faculty",
            email=f"res.person{i + 1}@test.org",
            pgy_level=(i % 3) + 1 if i % 3 != 0 else None,
        )
        db.add(person)
        people.append(person)

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

    # Create assignments with realistic distribution
    assignments = []
    for block in blocks:
        # Assign 60-80% of people to each block
        assigned_count = int(num_people * (0.6 + (hash(str(block.id)) % 20) / 100))

        for i in range(assigned_count):
            person = people[i % len(people)]
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=person.id,
                rotation_template_id=template.id,
                role="primary",
            )
            db.add(assignment)
            assignments.append(assignment)

    db.commit()

    return {
        "people": people,
        "blocks": blocks,
        "assignments": assignments,
        "template": template,
        "start_date": start_date,
        "end_date": start_date + timedelta(days=num_weeks * 7 - 1),
    }


def benchmark_n1_contingency(
    num_people: int = 50,
    num_weeks: int = 4,
    iterations: int = 10,
    verbose: bool = False,
) -> BenchmarkResult:
    """Benchmark N-1 contingency analysis performance."""
    print_benchmark_header(
        f"N-1 Contingency Analysis ({num_people} people, {num_weeks} weeks)",
        f"Benchmarking power grid-style N-1 analysis with {iterations} iterations",
    )

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)

    durations = []
    memory_usage = []
    vulnerabilities_found = []

    for i in range(iterations):
        db = SessionLocal()

        try:
            test_data = setup_resilience_data(db, num_people, num_weeks)

            with measure_performance("n1_contingency") as metrics:
                analyzer = N1ContingencyAnalyzer(db)
                result = analyzer.analyze(
                    start_date=test_data["start_date"],
                    end_date=test_data["end_date"],
                )

            durations.append(metrics["duration"])
            memory_usage.append(metrics["memory_delta_mb"])
            vulnerabilities_found.append(len(result.get("vulnerabilities", [])))

            if verbose:
                print(f"  Iteration {i + 1}: {metrics['duration']:.3f}s, "
                      f"{len(result.get('vulnerabilities', []))} vulnerabilities")

        finally:
            db.query(Assignment).delete()
            db.query(Block).delete()
            db.query(Person).delete()
            db.query(RotationTemplate).delete()
            db.commit()
            db.close()

    stats = calculate_stats(durations)

    result = BenchmarkResult(
        benchmark_name=f"resilience_n1_contingency_{num_people}people_{num_weeks}wk",
        category="resilience",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        duration_seconds=sum(durations),
        iterations=iterations,
        avg_duration=stats["avg"],
        min_duration=stats["min"],
        max_duration=stats["max"],
        std_deviation=stats["std_dev"],
        throughput=num_people / stats["avg"] if stats["avg"] > 0 else 0,
        memory_mb=sum(memory_usage) / len(memory_usage) if memory_usage else 0,
        peak_memory_mb=max(memory_usage) if memory_usage else 0,
        metadata={
            "num_people": num_people,
            "num_weeks": num_weeks,
            "avg_vulnerabilities": sum(vulnerabilities_found) / len(vulnerabilities_found)
            if vulnerabilities_found
            else 0,
        },
    )

    print_benchmark_results(result)
    return result


def benchmark_burnout_epidemiology(
    num_residents: int = 50,
    num_weeks: int = 12,
    iterations: int = 10,
    verbose: bool = False,
) -> BenchmarkResult:
    """Benchmark burnout epidemiology model (SIR model + Rt calculation)."""
    print_benchmark_header(
        f"Burnout Epidemiology Model ({num_residents} residents, {num_weeks} weeks)",
        f"Benchmarking SIR model and reproduction number with {iterations} iterations",
    )

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)

    durations = []
    memory_usage = []
    rt_values = []

    for i in range(iterations):
        db = SessionLocal()

        try:
            test_data = setup_resilience_data(db, num_residents, num_weeks)

            with measure_performance("burnout_epidemiology") as metrics:
                model = BurnoutEpidemiologyModel(db)
                result = model.calculate_reproduction_number(
                    start_date=test_data["start_date"],
                    end_date=test_data["end_date"],
                )

            durations.append(metrics["duration"])
            memory_usage.append(metrics["memory_delta_mb"])
            rt_values.append(result.get("Rt", 0))

            if verbose:
                print(f"  Iteration {i + 1}: {metrics['duration']:.3f}s, Rt={result.get('Rt', 0):.2f}")

        finally:
            db.query(Assignment).delete()
            db.query(Block).delete()
            db.query(Person).delete()
            db.query(RotationTemplate).delete()
            db.commit()
            db.close()

    stats = calculate_stats(durations)

    result = BenchmarkResult(
        benchmark_name=f"resilience_burnout_epi_{num_residents}res_{num_weeks}wk",
        category="resilience",
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
            "avg_rt": sum(rt_values) / len(rt_values) if rt_values else 0,
        },
    )

    print_benchmark_results(result)
    return result


def benchmark_spc_monitoring(
    num_weeks: int = 12,
    iterations: int = 10,
    verbose: bool = False,
) -> BenchmarkResult:
    """Benchmark SPC monitoring and Western Electric rules detection."""
    print_benchmark_header(
        f"SPC Monitoring ({num_weeks} weeks)",
        f"Benchmarking statistical process control charts with {iterations} iterations",
    )

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)

    durations = []
    memory_usage = []
    violations_found = []

    for i in range(iterations):
        db = SessionLocal()

        try:
            test_data = setup_resilience_data(db, num_people=50, num_weeks=num_weeks)

            with measure_performance("spc_monitoring") as metrics:
                monitor = SPCMonitor(db)
                result = monitor.analyze_control_chart(
                    start_date=test_data["start_date"],
                    end_date=test_data["end_date"],
                    metric="utilization",
                )

            durations.append(metrics["duration"])
            memory_usage.append(metrics["memory_delta_mb"])
            violations_found.append(len(result.get("violations", [])))

            if verbose:
                print(f"  Iteration {i + 1}: {metrics['duration']:.3f}s, "
                      f"{len(result.get('violations', []))} violations")

        finally:
            db.query(Assignment).delete()
            db.query(Block).delete()
            db.query(Person).delete()
            db.query(RotationTemplate).delete()
            db.commit()
            db.close()

    stats = calculate_stats(durations)

    result = BenchmarkResult(
        benchmark_name=f"resilience_spc_monitoring_{num_weeks}wk",
        category="resilience",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        duration_seconds=sum(durations),
        iterations=iterations,
        avg_duration=stats["avg"],
        min_duration=stats["min"],
        max_duration=stats["max"],
        std_deviation=stats["std_dev"],
        throughput=num_weeks / stats["avg"] if stats["avg"] > 0 else 0,
        memory_mb=sum(memory_usage) / len(memory_usage) if memory_usage else 0,
        peak_memory_mb=max(memory_usage) if memory_usage else 0,
        metadata={
            "num_weeks": num_weeks,
            "avg_violations": sum(violations_found) / len(violations_found)
            if violations_found
            else 0,
        },
    )

    print_benchmark_results(result)
    return result


def run_suite(verbose: bool = False):
    """Run full resilience calculation benchmark suite."""
    print("=" * 80)
    print("RESILIENCE CALCULATION BENCHMARK SUITE")
    print("=" * 80)
    print()

    results = []

    # N-1 contingency
    for num_people in [25, 50, 100]:
        results.append(
            benchmark_n1_contingency(
                num_people=num_people,
                num_weeks=4,
                iterations=10,
                verbose=verbose,
            )
        )
        print()

    # Burnout epidemiology
    results.append(
        benchmark_burnout_epidemiology(
            num_residents=50,
            num_weeks=12,
            iterations=10,
            verbose=verbose,
        )
    )
    print()

    # SPC monitoring
    results.append(
        benchmark_spc_monitoring(
            num_weeks=12,
            iterations=10,
            verbose=verbose,
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
    parser = argparse.ArgumentParser(description="Benchmark resilience calculation performance")
    parser.add_argument(
        "--metric",
        type=str,
        default="n1",
        choices=["n1", "n2", "burnout", "spc"],
        help="Resilience metric to benchmark",
    )
    parser.add_argument("--people", type=int, default=50, help="Number of people")
    parser.add_argument("--weeks", type=int, default=4, help="Number of weeks")
    parser.add_argument("--iterations", type=int, default=10, help="Number of iterations")
    parser.add_argument("--suite", action="store_true", help="Run full suite")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.suite:
        run_suite(verbose=args.verbose)
    else:
        if args.metric == "n1":
            result = benchmark_n1_contingency(
                num_people=args.people,
                num_weeks=args.weeks,
                iterations=args.iterations,
                verbose=args.verbose,
            )
        elif args.metric == "burnout":
            result = benchmark_burnout_epidemiology(
                num_residents=args.people,
                num_weeks=args.weeks,
                iterations=args.iterations,
                verbose=args.verbose,
            )
        elif args.metric == "spc":
            result = benchmark_spc_monitoring(
                num_weeks=args.weeks,
                iterations=args.iterations,
                verbose=args.verbose,
            )

        output_dir = Path(__file__).parent.parent.parent / "benchmark_results"
        result.save(output_dir)


if __name__ == "__main__":
    main()
