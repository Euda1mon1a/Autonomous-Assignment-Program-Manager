"""
Experimental Test Harness - Main Entry Point.

Provides infrastructure to safely test experimental scheduling algorithms
against production baselines without code contamination.

Architecture:
    1. Checkout experimental branch to temp directory
    2. Import experimental solver via isolated subprocess
    3. Run same scenarios through production and experimental
    4. Compare results and generate reports

Usage:
    python -m experimental.harness --branch quantum-physics --scenario standard
    python -m experimental.harness --branch catalyst-concepts --scenario swap-heavy
    python -m experimental.harness --compare-all --output reports/comparison.json
"""

import argparse
import json
import logging
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class ExperimentResult:
    """Results from running an experimental solver."""

    branch: str
    scenario: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Quality metrics
    constraint_violations: int = 0
    acgme_compliance: float = 1.0  # 0.0-1.0
    coverage_score: float = 1.0  # 0.0-1.0
    equity_variance: float = 0.0  # Lower is better

    # Performance metrics
    solve_time_ms: int = 0
    memory_peak_mb: int = 0

    # Comparison to baseline
    baseline_solve_time_ms: int = 0
    quality_delta: float = 0.0  # Positive = better than baseline

    # Status
    success: bool = True
    error_message: str | None = None


@dataclass
class ComparisonReport:
    """Comparison report across all experimental branches."""

    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    scenarios_tested: list[str] = field(default_factory=list)
    results: dict[str, list[ExperimentResult]] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)


# =============================================================================
# BRANCH DEFINITIONS
# =============================================================================


EXPERIMENTAL_BRANCHES = {
    "quantum-physics": {
        "pattern": "claude/quantum-physics-scheduler-*",
        "solver_module": "app.scheduling.quantum.qubo_solver",
        "solver_class": "QUBOSolver",
        "success_criteria": {
            "quality_threshold": 0.95,  # Must be ≥95% of baseline quality
            "time_threshold": 0.50,  # Must be ≤50% of baseline time
        },
    },
    "catalyst-concepts": {
        "pattern": "claude/catalyst-concepts-research-*",
        "solver_module": "app.scheduling_catalyst.optimizer",
        "solver_class": "TransitionOptimizer",
        "success_criteria": {
            "swap_success_rate": 0.90,  # >90% valid transitions
        },
    },
    "transcription-factors": {
        "pattern": "claude/transcription-factors-scheduler-*",
        "solver_module": "app.resilience.transcription_factors",
        "solver_class": "TranscriptionFactorScheduler",
        "success_criteria": {
            "graceful_degradation": True,  # Must degrade gracefully at 120% load
        },
    },
}


SCENARIOS = {
    "standard": {
        "description": "Standard scheduling with typical constraints",
        "residents": 24,
        "blocks": 730,
        "constraints": "standard",
    },
    "swap-heavy": {
        "description": "High volume of swap requests",
        "residents": 24,
        "blocks": 730,
        "swap_rate": 0.15,  # 15% of assignments have swap requests
    },
    "crisis-mode": {
        "description": "Emergency staffing crisis simulation",
        "residents": 24,
        "blocks": 730,
        "unavailable_rate": 0.25,  # 25% unavailable
        "stress_level": "high",
    },
    "minimal": {
        "description": "Minimal test scenario for quick validation",
        "residents": 6,
        "blocks": 14,
        "constraints": "standard",
    },
}


# =============================================================================
# HARNESS IMPLEMENTATION
# =============================================================================


class ExperimentalHarness:
    """Main test harness for experimental algorithm comparison."""

    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root or Path(__file__).parent.parent.parent
        self.reports_dir = Path(__file__).parent / "reports"
        self.reports_dir.mkdir(exist_ok=True)

    def find_branch(self, branch_key: str) -> str | None:
        """Find the full branch name matching the pattern."""
        config = EXPERIMENTAL_BRANCHES.get(branch_key)
        if not config:
            logger.error(f"Unknown branch key: {branch_key}")
            return None

        pattern = config["pattern"]
        result = subprocess.run(
            ["git", "branch", "-r", "--list", f"origin/{pattern}"],
            capture_output=True,
            text=True,
            cwd=self.repo_root,
        )

        branches = [b.strip() for b in result.stdout.strip().split("\n") if b.strip()]
        if not branches:
            logger.warning(f"No branches found matching {pattern}")
            return None

        # Return most recent (assuming naming convention includes timestamp/id)
        return branches[-1].replace("origin/", "")

    def run_baseline(self, scenario_key: str) -> ExperimentResult:
        """Run the production baseline solver."""
        scenario = SCENARIOS.get(scenario_key)
        if not scenario:
            return ExperimentResult(
                branch="baseline",
                scenario=scenario_key,
                success=False,
                error_message=f"Unknown scenario: {scenario_key}",
            )

        logger.info(f"Running baseline for scenario: {scenario_key}")

        # TODO: Implement actual baseline solver invocation
        # For now, return placeholder demonstrating structure
        return ExperimentResult(
            branch="baseline",
            scenario=scenario_key,
            constraint_violations=0,
            acgme_compliance=1.0,
            coverage_score=0.98,
            equity_variance=0.05,
            solve_time_ms=1500,
            memory_peak_mb=256,
        )

    def run_experimental(self, branch_key: str, scenario_key: str) -> ExperimentResult:
        """Run an experimental solver in isolation."""
        branch_name = self.find_branch(branch_key)
        if not branch_name:
            return ExperimentResult(
                branch=branch_key,
                scenario=scenario_key,
                success=False,
                error_message=f"Branch not found for: {branch_key}",
            )

        logger.info(f"Running experimental branch {branch_name} for scenario: {scenario_key}")

        # TODO: Implement isolated subprocess execution
        # 1. Checkout branch to temp directory
        # 2. Run solver via subprocess with JSON input/output
        # 3. Parse results

        # For now, return placeholder demonstrating structure
        return ExperimentResult(
            branch=branch_key,
            scenario=scenario_key,
            constraint_violations=0,
            acgme_compliance=1.0,
            coverage_score=0.97,
            equity_variance=0.06,
            solve_time_ms=1200,
            memory_peak_mb=280,
            baseline_solve_time_ms=1500,
            quality_delta=0.02,  # Slightly better
        )

    def compare_all(self, scenarios: list[str] | None = None) -> ComparisonReport:
        """Run all experimental branches against baseline for given scenarios."""
        if scenarios is None:
            scenarios = list(SCENARIOS.keys())

        report = ComparisonReport(scenarios_tested=scenarios)

        for scenario_key in scenarios:
            logger.info(f"=== Scenario: {scenario_key} ===")

            # Run baseline
            baseline = self.run_baseline(scenario_key)

            for branch_key in EXPERIMENTAL_BRANCHES:
                result = self.run_experimental(branch_key, scenario_key)

                # Calculate delta vs baseline
                if baseline.success and result.success:
                    result.baseline_solve_time_ms = baseline.solve_time_ms
                    result.quality_delta = result.coverage_score - baseline.coverage_score

                if branch_key not in report.results:
                    report.results[branch_key] = []
                report.results[branch_key].append(result)

        # Generate recommendations
        report.recommendations = self._generate_recommendations(report)

        return report

    def _generate_recommendations(self, report: ComparisonReport) -> list[str]:
        """Generate recommendations based on comparison results."""
        recommendations = []

        for branch_key, results in report.results.items():
            config = EXPERIMENTAL_BRANCHES[branch_key]
            criteria = config.get("success_criteria", {})

            passing = all(r.success for r in results)
            if not passing:
                recommendations.append(
                    f"[{branch_key}] NOT READY: Some scenarios failed"
                )
                continue

            avg_quality_delta = sum(r.quality_delta for r in results) / len(results)
            if avg_quality_delta >= 0:
                recommendations.append(
                    f"[{branch_key}] PROMISING: Avg quality delta +{avg_quality_delta:.2%}"
                )
            else:
                recommendations.append(
                    f"[{branch_key}] NEEDS WORK: Avg quality delta {avg_quality_delta:.2%}"
                )

        return recommendations

    def save_report(self, report: ComparisonReport, output_path: Path) -> None:
        """Save comparison report to JSON file."""
        # Convert dataclasses to dicts
        data = {
            "generated_at": report.generated_at,
            "scenarios_tested": report.scenarios_tested,
            "results": {
                branch: [asdict(r) for r in results]
                for branch, results in report.results.items()
            },
            "recommendations": report.recommendations,
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Report saved to: {output_path}")


# =============================================================================
# CLI ENTRY POINT
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Experimental Test Harness for Novel Scheduling Algorithms"
    )
    parser.add_argument(
        "--branch",
        choices=list(EXPERIMENTAL_BRANCHES.keys()),
        help="Specific experimental branch to test",
    )
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()),
        default="minimal",
        help="Scenario to test (default: minimal)",
    )
    parser.add_argument(
        "--compare-all",
        action="store_true",
        help="Run all branches against all scenarios",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path for comparison report",
    )
    parser.add_argument(
        "--list-branches",
        action="store_true",
        help="List available experimental branches",
    )
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="List available test scenarios",
    )

    args = parser.parse_args()
    harness = ExperimentalHarness()

    if args.list_branches:
        print("\nExperimental Branches:")
        print("-" * 50)
        for key, config in EXPERIMENTAL_BRANCHES.items():
            branch = harness.find_branch(key)
            status = f"Found: {branch}" if branch else "Not found"
            print(f"  {key}: {status}")
        return

    if args.list_scenarios:
        print("\nTest Scenarios:")
        print("-" * 50)
        for key, config in SCENARIOS.items():
            print(f"  {key}: {config['description']}")
        return

    if args.compare_all:
        report = harness.compare_all()
        if args.output:
            harness.save_report(report, args.output)
        else:
            print("\nComparison Report:")
            print("-" * 50)
            for rec in report.recommendations:
                print(f"  {rec}")
        return

    if args.branch:
        baseline = harness.run_baseline(args.scenario)
        result = harness.run_experimental(args.branch, args.scenario)

        print(f"\n=== Results for {args.branch} on {args.scenario} ===")
        print(f"Baseline solve time: {baseline.solve_time_ms}ms")
        print(f"Experimental solve time: {result.solve_time_ms}ms")
        print(f"Quality delta: {result.quality_delta:+.2%}")
        print(f"Success: {result.success}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
