#!/usr/bin/env python3
"""
Headless CLI Entrypoint for Autonomous Scheduling.

Make one Python entrypoint that can run headless. Given inputs, it can:
    - Load data
    - Generate candidate schedule(s)
    - Evaluate constraints
    - Output artifacts (JSON/CSV) plus a machine-readable scorecard

This is the "robot can run without you" prerequisite.

Usage:
    python -m app.autonomous.cli --scenario baseline --max-iters 200
    python -m app.autonomous.cli --resume RUN_ID
    python -m app.autonomous.cli --harness --threshold 0.8

What you get as output each run:
    - schedule.json (assignments)
    - report.json (violations, metrics, score)
    - run.log (trace)
"""

import argparse
import json
import sys
from datetime import date, timedelta

from app.core.logging import get_logger
from app.db.session import SessionLocal

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Autonomous Schedule Generator - Headless CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run baseline scenario for 200 iterations
  python -m app.autonomous.cli --scenario baseline --max-iters 200

  # Resume a previous run
  python -m app.autonomous.cli --resume baseline_20250122_143052_abc12345

  # Run resilience test harness
  python -m app.autonomous.cli --harness --threshold 0.8

  # Generate for specific date range
  python -m app.autonomous.cli --start 2025-01-01 --end 2025-03-31

  # Use specific algorithm
  python -m app.autonomous.cli --algorithm cp_sat --timeout 120

Output files are saved to runs/{run_id}/:
  - state.json: Current loop state
  - history.ndjson: Iteration history
  - schedule.json: Best schedule assignments
  - report.json: Best evaluation report
  - run.log: Execution trace
""",
    )

    # Mode selection
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--scenario",
        type=str,
        default="baseline",
        help="Scenario name for new run (default: baseline)",
    )
    mode.add_argument(
        "--resume",
        type=str,
        metavar="RUN_ID",
        help="Resume an existing run by ID",
    )
    mode.add_argument(
        "--harness",
        action="store_true",
        help="Run resilience test harness instead of loop",
    )

    # Date range
    parser.add_argument(
        "--start",
        type=str,
        help="Start date (YYYY-MM-DD), default: today",
    )
    parser.add_argument(
        "--end",
        type=str,
        help="End date (YYYY-MM-DD), default: start + 90 days",
    )

    # Loop configuration
    parser.add_argument(
        "--max-iters",
        type=int,
        default=200,
        help="Maximum iterations (default: 200)",
    )
    parser.add_argument(
        "--target-score",
        type=float,
        default=0.95,
        help="Target score to stop at (default: 0.95)",
    )
    parser.add_argument(
        "--stagnation",
        type=int,
        default=20,
        help="Iterations without improvement before stopping (default: 20)",
    )
    parser.add_argument(
        "--time-limit",
        type=float,
        help="Maximum time in seconds (default: unlimited)",
    )

    # Generator configuration
    parser.add_argument(
        "--algorithm",
        type=str,
        choices=["greedy", "cp_sat", "pulp", "hybrid"],
        default="greedy",
        help="Initial algorithm (default: greedy)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Solver timeout in seconds (default: 60)",
    )
    parser.add_argument(
        "--candidates",
        type=int,
        default=1,
        help="Candidates per iteration (default: 1)",
    )

    # Harness configuration
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.8,
        help="Pass rate threshold for harness (default: 0.8)",
    )

    # Output configuration
    parser.add_argument(
        "--runs-path",
        type=str,
        default="runs",
        help="Directory for run outputs (default: runs)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output",
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Output final result as JSON",
    )

    return parser.parse_args()


def run_loop(args: argparse.Namespace) -> int:
    """
    Run the autonomous scheduling loop.

    Returns exit code: 0 for success, 1 for failure/exhausted.
    """
    from app.autonomous.generator import GeneratorConfig
    from app.autonomous.loop import AutonomousLoop, LoopConfig
    from app.autonomous.state import GeneratorParams

    # Parse dates
    start_date = date.fromisoformat(args.start) if args.start else date.today()
    end_date = (
        date.fromisoformat(args.end) if args.end else start_date + timedelta(days=90)
    )

    # Create database session
    db = SessionLocal()

    try:
        # Create loop configuration
        loop_config = LoopConfig(
            max_iterations=args.max_iters,
            target_score=args.target_score,
            stagnation_limit=args.stagnation,
            time_limit_seconds=args.time_limit,
            candidates_per_iteration=args.candidates,
            log_interval=10 if not args.quiet else 50,
        )

        # Create generator configuration
        generator_config = GeneratorConfig(
            algorithms=[args.algorithm, "greedy", "cp_sat", "pulp", "hybrid"],
            default_timeout=args.timeout,
        )

        # Create or resume loop
        loop = AutonomousLoop.from_config(
            db=db,
            scenario=args.scenario,
            start_date=start_date,
            end_date=end_date,
            config=loop_config,
            generator_config=generator_config,
            runs_path=args.runs_path,
            resume_run_id=args.resume,
        )

        # Set initial parameters
        if not args.resume:
            loop.state.current_params = GeneratorParams(
                algorithm=args.algorithm,
                timeout_seconds=args.timeout,
            )

        if not args.quiet:
            print(f"Run ID: {loop.state.run_id}")
            print(f"Scenario: {loop.state.scenario}")
            print(f"Date range: {start_date} to {end_date}")
            print(f"Target score: {args.target_score}")
            print(f"Max iterations: {args.max_iters}")
            print()

        # Run the loop
        result = loop.run()

        # Output result
        if args.json_output:
            output = {
                "run_id": result.run_id,
                "success": result.success,
                "stop_reason": result.stop_reason.value,
                "final_score": result.final_score,
                "final_iteration": result.final_iteration,
                "total_time": result.total_time,
            }
            print(json.dumps(output, indent=2))
        else:
            print()
            print("=" * 60)
            print(f"Run completed: {result.run_id}")
            print(f"  Status: {'SUCCESS' if result.success else 'EXHAUSTED'}")
            print(f"  Stop reason: {result.stop_reason.value}")
            print(f"  Final score: {result.final_score:.4f}")
            print(f"  Iterations: {result.final_iteration}")
            print(f"  Total time: {result.total_time:.1f}s")
            print()
            print(f"Outputs saved to: {args.runs_path}/{result.run_id}/")
            print("  - schedule.json")
            print("  - report.json")
            print("  - history.ndjson")
            print("  - run.log")
            print("=" * 60)

        return 0 if result.success else 1

    finally:
        db.close()


def run_harness(args: argparse.Namespace) -> int:
    """
    Run the resilience test harness.

    Returns exit code: 0 for pass, 1 for fail.
    """
    from app.autonomous.harness import run_resilience_regression

    # Parse dates
    start_date = date.fromisoformat(args.start) if args.start else date.today()
    end_date = (
        date.fromisoformat(args.end) if args.end else start_date + timedelta(days=90)
    )

    # Create database session
    db = SessionLocal()

    try:
        if not args.quiet:
            print("Running resilience test harness")
            print(f"Date range: {start_date} to {end_date}")
            print(f"Pass threshold: {args.threshold:.0%}")
            print()

        passed, result = run_resilience_regression(
            db=db,
            start_date=start_date,
            end_date=end_date,
            threshold_pass_rate=args.threshold,
        )

        # Output result
        if args.json_output:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print()
            print("=" * 60)
            print(f"Resilience Harness: {'PASS' if passed else 'FAIL'}")
            print(f"  Total scenarios: {result.total_scenarios}")
            print(f"  Passed: {result.passed_scenarios}")
            print(f"  Failed: {result.failed_scenarios}")
            print(f"  Pass rate: {result.pass_rate():.1%}")
            print(f"  Avg degradation: {result.avg_score_degradation:.4f}")
            print(f"  Total time: {result.total_time:.1f}s")
            if result.worst_scenario:
                print(f"  Worst scenario: {result.worst_scenario.name}")
            print("=" * 60)

            if not passed:
                print()
                print("Failed scenarios:")
                for sr in result.scenario_results:
                    if not sr.feasible:
                        print(f"  - {sr.scenario.name}: score={sr.scenario_score:.4f}")

        return 0 if passed else 1

    finally:
        db.close()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Configure logging
    import logging

    log_level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        if args.harness:
            return run_harness(args)
        else:
            return run_loop(args)

    except KeyboardInterrupt:
        print("\nAborted by user")
        return 130

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if not args.quiet:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
