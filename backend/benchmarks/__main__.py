"""
Benchmark Suite Runner

Main entry point for running all benchmarks or specific benchmark categories.

Usage:
    ***REMOVED*** Run all benchmarks
    python -m benchmarks

    ***REMOVED*** Run specific category
    python -m benchmarks --category schedule_generation

    ***REMOVED*** Run quick benchmarks (reduced iterations)
    python -m benchmarks --quick

    ***REMOVED*** Run with verbose output
    python -m benchmarks --verbose

    ***REMOVED*** Run and generate comparison report
    python -m benchmarks --compare-with previous_run.json
"""

import argparse
import sys
import time
from pathlib import Path

from benchmarks import print_benchmark_header

***REMOVED*** Import all benchmark modules
from benchmarks.acgme_validation_bench import (
    benchmark_acgme_validation,
    run_suite as acgme_suite,
)
from benchmarks.concurrent_requests_bench import run_suite as concurrent_suite
from benchmarks.database_query_bench import run_suite as database_suite
from benchmarks.memory_usage_bench import run_suite as memory_suite
from benchmarks.resilience_calculation_bench import run_suite as resilience_suite
from benchmarks.schedule_generation_bench import (
    benchmark_schedule_generation,
    run_suite as schedule_suite,
)
from benchmarks.startup_time_bench import run_suite as startup_suite
from benchmarks.swap_matching_bench import run_suite as swap_suite


def run_quick_benchmarks(verbose: bool = False):
    """Run a quick subset of benchmarks with reduced iterations."""
    print_benchmark_header(
        "QUICK BENCHMARK SUITE",
        "Running reduced benchmark suite for fast validation",
    )
    print()

    results = []

    ***REMOVED*** Quick schedule generation (1 size, 1 iteration)
    print("Running quick schedule generation benchmark...")
    results.append(
        benchmark_schedule_generation(
            num_residents=25,
            num_weeks=2,
            iterations=1,
            verbose=verbose,
        )
    )
    print()

    ***REMOVED*** Quick ACGME validation (1 size, 3 iterations)
    print("Running quick ACGME validation benchmark...")
    results.append(
        benchmark_acgme_validation(
            num_residents=25,
            num_weeks=2,
            validation_type="full",
            iterations=3,
            verbose=verbose,
        )
    )
    print()

    ***REMOVED*** Quick startup benchmark
    print("Running quick startup benchmark...")
    from benchmarks.startup_time_bench import benchmark_config_loading

    results.append(benchmark_config_loading(iterations=10, verbose=verbose))
    print()

    ***REMOVED*** Save results
    output_dir = Path(__file__).parent.parent.parent / "benchmark_results"
    for result in results:
        result.save(output_dir)

    print("\n" + "=" * 80)
    print("QUICK SUITE COMPLETE")
    print("=" * 80)


def run_all_suites(verbose: bool = False):
    """Run all benchmark suites."""
    print("=" * 80)
    print("FULL BENCHMARK SUITE")
    print("=" * 80)
    print("This will run all benchmarks and may take 15-30 minutes.")
    print("=" * 80)
    print()

    start_time = time.time()

    ***REMOVED*** Run each suite
    print("\n***REMOVED******REMOVED******REMOVED*** SCHEDULE GENERATION BENCHMARKS ***REMOVED******REMOVED******REMOVED***")
    schedule_suite(verbose=verbose)
    print()

    print("\n***REMOVED******REMOVED******REMOVED*** ACGME VALIDATION BENCHMARKS ***REMOVED******REMOVED******REMOVED***")
    acgme_suite(verbose=verbose)
    print()

    print("\n***REMOVED******REMOVED******REMOVED*** DATABASE QUERY BENCHMARKS ***REMOVED******REMOVED******REMOVED***")
    database_suite(verbose=verbose)
    print()

    print("\n***REMOVED******REMOVED******REMOVED*** RESILIENCE CALCULATION BENCHMARKS ***REMOVED******REMOVED******REMOVED***")
    resilience_suite(verbose=verbose)
    print()

    print("\n***REMOVED******REMOVED******REMOVED*** SWAP MATCHING BENCHMARKS ***REMOVED******REMOVED******REMOVED***")
    swap_suite(verbose=verbose)
    print()

    print("\n***REMOVED******REMOVED******REMOVED*** CONCURRENT REQUESTS BENCHMARKS ***REMOVED******REMOVED******REMOVED***")
    concurrent_suite(verbose=verbose)
    print()

    print("\n***REMOVED******REMOVED******REMOVED*** MEMORY USAGE BENCHMARKS ***REMOVED******REMOVED******REMOVED***")
    memory_suite(verbose=verbose)
    print()

    print("\n***REMOVED******REMOVED******REMOVED*** STARTUP TIME BENCHMARKS ***REMOVED******REMOVED******REMOVED***")
    startup_suite(verbose=verbose)
    print()

    total_time = time.time() - start_time

    print("\n" + "=" * 80)
    print(f"ALL BENCHMARKS COMPLETE (Total time: {total_time / 60:.1f} minutes)")
    print("=" * 80)
    print(f"Results saved to: {Path.cwd() / 'benchmark_results'}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run performance benchmarks for Residency Scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m benchmarks                              ***REMOVED*** Run quick benchmarks
  python -m benchmarks --all                        ***REMOVED*** Run all benchmarks
  python -m benchmarks --category schedule          ***REMOVED*** Run schedule benchmarks only
  python -m benchmarks --quick --verbose            ***REMOVED*** Quick run with verbose output
        """,
    )

    parser.add_argument(
        "--category",
        type=str,
        choices=[
            "schedule",
            "acgme",
            "database",
            "resilience",
            "swap",
            "concurrent",
            "memory",
            "startup",
        ],
        help="Run specific benchmark category",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all benchmark suites (may take 15-30 minutes)",
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick benchmark subset (faster, reduced iterations)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output with iteration details",
    )

    args = parser.parse_args()

    ***REMOVED*** Default to quick mode if no options specified
    if not args.category and not args.all and not args.quick:
        args.quick = True

    if args.quick:
        run_quick_benchmarks(verbose=args.verbose)
    elif args.all:
        run_all_suites(verbose=args.verbose)
    elif args.category:
        if args.category == "schedule":
            schedule_suite(verbose=args.verbose)
        elif args.category == "acgme":
            acgme_suite(verbose=args.verbose)
        elif args.category == "database":
            database_suite(verbose=args.verbose)
        elif args.category == "resilience":
            resilience_suite(verbose=args.verbose)
        elif args.category == "swap":
            swap_suite(verbose=args.verbose)
        elif args.category == "concurrent":
            concurrent_suite(verbose=args.verbose)
        elif args.category == "memory":
            memory_suite(verbose=args.verbose)
        elif args.category == "startup":
            startup_suite(verbose=args.verbose)


if __name__ == "__main__":
    main()
