"""
Solver Comparison Benchmark.

Compares solution quality and performance between production and experimental solvers.
"""

import time
import tracemalloc
from dataclasses import dataclass
from typing import Any, Protocol


class Solver(Protocol):
    """Protocol for solver implementations."""

    def solve(self, context: Any) -> Any:
        """Solve the scheduling problem."""
        ...


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""

    solver_name: str
    scenario: str
    solve_time_ms: float
    constraint_violations: int
    coverage_score: float
    memory_mb: float


class SolverBenchmark:
    """Benchmark runner for solver comparison."""

    def __init__(self):
        self.results: list[BenchmarkResult] = []

    def run(
        self,
        solver: Solver,
        solver_name: str,
        context: Any,
        scenario: str,
    ) -> BenchmarkResult:
        """Run a single benchmark."""
        # Start memory tracking
        tracemalloc.start()

        start = time.perf_counter()
        result = solver.solve(context)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Get peak memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        memory_mb = peak / 1024 / 1024

        benchmark_result = BenchmarkResult(
            solver_name=solver_name,
            scenario=scenario,
            solve_time_ms=elapsed_ms,
            constraint_violations=self._count_violations(result),
            coverage_score=self._calculate_coverage(result),
            memory_mb=memory_mb,
        )

        self.results.append(benchmark_result)
        return benchmark_result

    def _count_violations(self, result: Any) -> int:
        """Count constraint violations in result."""
        # Try multiple attributes that might contain violation data
        if hasattr(result, "violations"):
            # If result has a violations list/count attribute
            violations = getattr(result, "violations")
            if isinstance(violations, list):
                return len(violations)
            elif isinstance(violations, int):
                return violations

        if hasattr(result, "constraint_violations"):
            # Direct constraint_violations attribute
            return getattr(result, "constraint_violations")

        if hasattr(result, "statistics") and isinstance(result.statistics, dict):
            # Check in statistics dict
            stats = result.statistics
            if "constraint_violations" in stats:
                return stats["constraint_violations"]
            if "violations" in stats:
                violations = stats["violations"]
                if isinstance(violations, list):
                    return len(violations)
                return violations

        # Default: 0 violations if not found or result is successful
        if hasattr(result, "success") and result.success:
            return 0

        return 0

    def _calculate_coverage(self, result: Any) -> float:
        """Calculate coverage score (0.0-1.0)."""
        # Try multiple attributes that might contain coverage data
        if hasattr(result, "coverage_score"):
            score = getattr(result, "coverage_score")
            if isinstance(score, (int, float)):
                return float(score)

        if hasattr(result, "coverage"):
            coverage = getattr(result, "coverage")
            if isinstance(coverage, (int, float)):
                return float(coverage)

        if hasattr(result, "statistics") and isinstance(result.statistics, dict):
            # Check in statistics dict
            stats = result.statistics
            if "coverage_score" in stats:
                return float(stats["coverage_score"])
            if "coverage_rate" in stats:
                return float(stats["coverage_rate"])
            if "coverage" in stats:
                return float(stats["coverage"])

        # Calculate from assignments if available
        if hasattr(result, "assignments") and hasattr(result, "statistics"):
            if isinstance(result.statistics, dict):
                total_blocks = result.statistics.get("total_blocks", 0)
                if total_blocks > 0 and hasattr(result, "assignments"):
                    assignments = getattr(result, "assignments")
                    if isinstance(assignments, list):
                        return len(assignments) / total_blocks

        # Default: 1.0 if successful, 0.0 otherwise
        if hasattr(result, "success"):
            return 1.0 if result.success else 0.0

        return 1.0

    def compare(self, baseline_name: str, experimental_name: str) -> dict:
        """Compare two solvers' results."""
        baseline = [r for r in self.results if r.solver_name == baseline_name]
        experimental = [r for r in self.results if r.solver_name == experimental_name]

        if not baseline or not experimental:
            return {"error": "Missing results for comparison"}

        avg_baseline_time = sum(r.solve_time_ms for r in baseline) / len(baseline)
        avg_exp_time = sum(r.solve_time_ms for r in experimental) / len(experimental)

        avg_baseline_coverage = sum(r.coverage_score for r in baseline) / len(baseline)
        avg_exp_coverage = sum(r.coverage_score for r in experimental) / len(
            experimental
        )

        return {
            "baseline_avg_time_ms": avg_baseline_time,
            "experimental_avg_time_ms": avg_exp_time,
            "time_improvement": (avg_baseline_time - avg_exp_time) / avg_baseline_time,
            "baseline_avg_coverage": avg_baseline_coverage,
            "experimental_avg_coverage": avg_exp_coverage,
            "coverage_delta": avg_exp_coverage - avg_baseline_coverage,
        }
