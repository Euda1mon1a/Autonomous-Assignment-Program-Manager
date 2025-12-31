#!/usr/bin/env python3
"""
Benchmark Comparison Tool

Compares benchmark results across multiple runs to identify performance changes.

Usage:
    python compare_benchmarks.py --baseline results/baseline.json --current results/current.json
    python compare_benchmarks.py --dir benchmark_results/ --last 7  # Compare last 7 runs
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def load_benchmark_results(filepath: Path) -> dict[str, Any]:
    """Load benchmark results from JSON file."""
    with open(filepath) as f:
        return json.load(f)


def compare_two_benchmarks(baseline: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    """Compare two benchmark runs."""
    baseline_name = baseline.get("benchmark_name", "unknown")
    current_name = current.get("benchmark_name", "unknown")

    if baseline_name != current_name:
        return {"error": "Benchmark names do not match"}

    baseline_duration = baseline.get("avg_duration", 0)
    current_duration = current.get("avg_duration", 0)

    if baseline_duration == 0:
        percent_change = 0
    else:
        percent_change = ((current_duration - baseline_duration) / baseline_duration) * 100

    comparison = {
        "benchmark_name": baseline_name,
        "baseline_duration": baseline_duration,
        "current_duration": current_duration,
        "absolute_change": current_duration - baseline_duration,
        "percent_change": percent_change,
        "regression": percent_change > 10,  # >10% slower is a regression
        "improvement": percent_change < -10,  # >10% faster is an improvement
    }

    # Compare throughput if available
    if baseline.get("throughput") and current.get("throughput"):
        baseline_throughput = baseline["throughput"]
        current_throughput = current["throughput"]
        throughput_change = ((current_throughput - baseline_throughput) / baseline_throughput) * 100

        comparison["baseline_throughput"] = baseline_throughput
        comparison["current_throughput"] = current_throughput
        comparison["throughput_change_percent"] = throughput_change

    # Compare memory if available
    if baseline.get("memory_mb") and current.get("memory_mb"):
        baseline_memory = baseline["memory_mb"]
        current_memory = current["memory_mb"]
        memory_change = ((current_memory - baseline_memory) / baseline_memory) * 100

        comparison["baseline_memory_mb"] = baseline_memory
        comparison["current_memory_mb"] = current_memory
        comparison["memory_change_percent"] = memory_change

    return comparison


def print_comparison(comparison: dict[str, Any]):
    """Print formatted comparison results."""
    if "error" in comparison:
        print(f"ERROR: {comparison['error']}")
        return

    print(f"\n{'=' * 80}")
    print(f"BENCHMARK: {comparison['benchmark_name']}")
    print(f"{'=' * 80}")

    # Duration
    print(f"\nDuration:")
    print(f"  Baseline:       {comparison['baseline_duration']:.3f}s")
    print(f"  Current:        {comparison['current_duration']:.3f}s")
    print(f"  Change:         {comparison['absolute_change']:+.3f}s ({comparison['percent_change']:+.1f}%)")

    if comparison.get("regression"):
        print(f"  ⚠️  REGRESSION DETECTED (>{comparison['percent_change']:.1f}% slower)")
    elif comparison.get("improvement"):
        print(f"  ✓ IMPROVEMENT (>{abs(comparison['percent_change']):.1f}% faster)")

    # Throughput
    if "throughput_change_percent" in comparison:
        print(f"\nThroughput:")
        print(f"  Baseline:       {comparison['baseline_throughput']:.2f} ops/sec")
        print(f"  Current:        {comparison['current_throughput']:.2f} ops/sec")
        print(f"  Change:         {comparison['throughput_change_percent']:+.1f}%")

    # Memory
    if "memory_change_percent" in comparison:
        print(f"\nMemory:")
        print(f"  Baseline:       {comparison['baseline_memory_mb']:.1f} MB")
        print(f"  Current:        {comparison['current_memory_mb']:.1f} MB")
        print(f"  Change:         {comparison['memory_change_percent']:+.1f}%")


def compare_benchmark_files(baseline_file: Path, current_file: Path):
    """Compare two benchmark result files."""
    print(f"Comparing benchmarks:")
    print(f"  Baseline: {baseline_file}")
    print(f"  Current:  {current_file}")

    baseline = load_benchmark_results(baseline_file)
    current = load_benchmark_results(current_file)

    comparison = compare_two_benchmarks(baseline, current)
    print_comparison(comparison)


def compare_multiple_runs(directory: Path, last_n: int = 7):
    """Compare multiple benchmark runs in a directory."""
    print(f"Comparing last {last_n} runs in {directory}")
    print()

    # Find all JSON files
    json_files = sorted(directory.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)

    if len(json_files) < 2:
        print("ERROR: Need at least 2 benchmark files to compare")
        return

    # Group by benchmark name
    by_benchmark = {}
    for filepath in json_files[:last_n * 10]:  # Check more files to find matches
        try:
            with open(filepath) as f:
                data = json.load(f)
                name = data.get("benchmark_name", "unknown")

                if name not in by_benchmark:
                    by_benchmark[name] = []

                by_benchmark[name].append((filepath, data))
        except Exception:
            continue

    # Compare each benchmark's runs
    for benchmark_name, runs in by_benchmark.items():
        if len(runs) < 2:
            continue

        # Sort by modification time (newest first)
        runs = sorted(runs, key=lambda x: x[0].stat().st_mtime, reverse=True)[:last_n]

        if len(runs) >= 2:
            print(f"\n{'=' * 80}")
            print(f"BENCHMARK: {benchmark_name}")
            print(f"{'=' * 80}")

            # Compare latest with oldest in the set
            latest = runs[0][1]
            oldest = runs[-1][1]

            comparison = compare_two_benchmarks(oldest, latest)

            print(f"\nComparing {len(runs)} runs:")
            print(f"  Oldest:  {runs[-1][0].name}")
            print(f"  Latest:  {runs[0][0].name}")

            # Show trend
            durations = [r[1].get("avg_duration", 0) for r in reversed(runs)]
            print(f"\nDuration trend (oldest → latest):")
            print(f"  {' → '.join([f'{d:.3f}s' for d in durations])}")

            if comparison.get("regression"):
                print(f"\n  ⚠️  REGRESSION: {comparison['percent_change']:+.1f}% slower")
            elif comparison.get("improvement"):
                print(f"\n  ✓ IMPROVEMENT: {abs(comparison['percent_change']):.1f}% faster")
            else:
                print(f"\n  Stable: {comparison['percent_change']:+.1f}% change")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Compare benchmark results")

    parser.add_argument(
        "--baseline",
        type=Path,
        help="Baseline benchmark JSON file",
    )

    parser.add_argument(
        "--current",
        type=Path,
        help="Current benchmark JSON file",
    )

    parser.add_argument(
        "--dir",
        type=Path,
        default=Path("benchmark_results"),
        help="Directory containing benchmark results",
    )

    parser.add_argument(
        "--last",
        type=int,
        default=7,
        help="Number of recent runs to compare (default: 7)",
    )

    args = parser.parse_args()

    if args.baseline and args.current:
        # Compare two specific files
        compare_benchmark_files(args.baseline, args.current)
    else:
        # Compare multiple runs in directory
        if not args.dir.exists():
            print(f"ERROR: Directory not found: {args.dir}")
            return

        compare_multiple_runs(args.dir, args.last)


if __name__ == "__main__":
    main()
