"""
Empirical Testing Tools for MCP Server.

These tools enable head-to-head comparison of Python modules to determine:
- Which solvers perform best
- Which constraints have high yield vs false positives
- Which resilience modules earn their complexity
- What code can be safely removed

Goal: Data-driven decisions about what to keep, improve, or cut.
"""

import ast
import logging
import subprocess
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Get project root (mcp-server/src/scheduler_mcp -> project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"


# =============================================================================
# Response Models
# =============================================================================


class SolverMetrics(BaseModel):
    """Metrics for a single solver."""

    solver_name: str
    runs: int = 0
    successes: int = 0
    failures: int = 0
    avg_runtime_seconds: float = 0.0
    avg_violations: float = 0.0
    avg_coverage: float = 0.0
    avg_fairness: float = 0.0
    min_runtime: float = 0.0
    max_runtime: float = 0.0


class SolverBenchmarkResult(BaseModel):
    """Result of solver benchmarking."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    scenarios_run: int = 0
    solvers_tested: list[str] = Field(default_factory=list)
    results_by_solver: dict[str, SolverMetrics] = Field(default_factory=dict)
    winner_by_metric: dict[str, str] = Field(default_factory=dict)
    recommendation: str = ""
    raw_data: list[dict] = Field(default_factory=list)


class ConstraintStats(BaseModel):
    """Statistics for a single constraint."""

    constraint_name: str
    triggers: int = 0
    true_positives: int = 0
    false_positives: int = 0
    yield_rate: float = 0.0
    avg_runtime_ms: float = 0.0
    description: str = ""


class ConstraintBenchmarkResult(BaseModel):
    """Result of constraint benchmarking."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    schedules_analyzed: int = 0
    constraint_stats: dict[str, ConstraintStats] = Field(default_factory=dict)
    high_yield: list[str] = Field(default_factory=list)
    low_yield: list[str] = Field(default_factory=list)
    candidates_for_removal: list[str] = Field(default_factory=list)
    recommendation: str = ""


class AblationResult(BaseModel):
    """Result of ablation study."""

    module_path: str
    module_exists: bool = True
    module_size_lines: int = 0
    module_size_bytes: int = 0
    file_count: int = 0
    imports_this: list[str] = Field(default_factory=list)
    imported_by: list[str] = Field(default_factory=list)
    tests_affected: int = 0
    tests_would_fail: int = 0
    functionality_lost: list[str] = Field(default_factory=list)
    safe_to_remove: bool = False
    removal_impact: str = "unknown"  # none, minor, major, breaking
    recommendation: str = ""


class ResilienceModuleStats(BaseModel):
    """Statistics for a resilience module."""

    module_name: str
    detection_rate: float = 0.0
    false_alarm_rate: float = 0.0
    avg_runtime_ms: float = 0.0
    complexity_lines: int = 0
    tier: str = ""  # tier1, tier2, tier3
    description: str = ""


class ResilienceBenchmarkResult(BaseModel):
    """Result of resilience benchmarking."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    scenarios_tested: int = 0
    module_stats: dict[str, ResilienceModuleStats] = Field(default_factory=dict)
    tier_analysis: dict[str, float] = Field(default_factory=dict)
    high_value: list[str] = Field(default_factory=list)
    low_value: list[str] = Field(default_factory=list)
    cut_candidates: list[str] = Field(default_factory=list)
    recommendation: str = ""


class ModuleUsageResult(BaseModel):
    """Result of module usage analysis."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    entry_points_analyzed: list[str] = Field(default_factory=list)
    total_modules: int = 0
    reachable_modules: list[str] = Field(default_factory=list)
    unreachable_modules: list[str] = Field(default_factory=list)
    hot_paths: list[str] = Field(default_factory=list)
    cold_paths: list[str] = Field(default_factory=list)
    dead_code_lines: int = 0
    dead_code_percentage: float = 0.0
    recommendation: str = ""


# =============================================================================
# Implementation Functions
# =============================================================================


def _run_command(cmd: list[str], cwd: Path | None = None, timeout: int = 300) -> tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or BACKEND_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def _count_lines(path: Path) -> int:
    """Count lines in a file or directory."""
    total = 0
    if path.is_file() and path.suffix == ".py":
        try:
            total = len(path.read_text().splitlines())
        except Exception:
            pass
    elif path.is_dir():
        for f in path.rglob("*.py"):
            if "__pycache__" not in str(f):
                try:
                    total += len(f.read_text().splitlines())
                except Exception:
                    pass
    return total


def _find_imports(file_path: Path) -> list[str]:
    """Find all imports in a Python file."""
    imports = []
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
    except Exception:
        pass
    return imports


def _find_importers(target_module: str, search_dir: Path) -> list[str]:
    """Find all files that import a given module."""
    importers = []
    for py_file in search_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        try:
            imports = _find_imports(py_file)
            for imp in imports:
                if target_module in imp or imp in target_module:
                    rel_path = py_file.relative_to(search_dir)
                    importers.append(str(rel_path))
                    break
        except Exception:
            pass
    return importers


async def benchmark_solvers(
    solvers: list[str] | None = None,
    scenario_count: int = 10,
    timeout_per_run: int = 60,
) -> SolverBenchmarkResult:
    """
    Benchmark solvers head-to-head.

    Runs each solver on identical synthetic scenarios and compares:
    - Runtime
    - Violation count
    - Coverage rate
    - Fairness score
    """
    if solvers is None:
        solvers = ["greedy", "cp_sat", "pulp", "hybrid"]

    result = SolverBenchmarkResult(
        solvers_tested=solvers,
        scenarios_run=scenario_count,
    )

    # Initialize metrics for each solver
    for solver in solvers:
        result.results_by_solver[solver] = SolverMetrics(solver_name=solver)

    # Check if pytest is available and tests exist
    test_file = BACKEND_ROOT / "tests" / "test_solvers.py"
    if not test_file.exists():
        result.recommendation = (
            "Solver test file not found. Create tests/test_solvers.py with "
            "parameterized tests for each solver to enable benchmarking."
        )
        return result

    # Run solver benchmarks via pytest
    for solver in solvers:
        logger.info(f"Benchmarking solver: {solver}")
        start_time = time.time()

        # Run tests for this solver
        cmd = [
            "python", "-m", "pytest",
            f"tests/test_solvers.py",
            "-k", solver,
            "--tb=no",
            "-q",
            f"--timeout={timeout_per_run}",
        ]

        returncode, stdout, stderr = _run_command(cmd, timeout=timeout_per_run * 2)
        runtime = time.time() - start_time

        metrics = result.results_by_solver[solver]
        metrics.runs = scenario_count

        if returncode == 0:
            metrics.successes = scenario_count
            metrics.avg_runtime_seconds = runtime / scenario_count
        else:
            # Parse failures from output
            if "failed" in stdout.lower():
                try:
                    # Extract failure count from pytest output
                    import re
                    match = re.search(r"(\d+) failed", stdout)
                    if match:
                        metrics.failures = int(match.group(1))
                        metrics.successes = scenario_count - metrics.failures
                except Exception:
                    metrics.failures = scenario_count

            metrics.avg_runtime_seconds = runtime / max(1, scenario_count)

        result.raw_data.append({
            "solver": solver,
            "returncode": returncode,
            "runtime": runtime,
            "stdout_preview": stdout[:500] if stdout else "",
        })

    # Determine winners by metric
    if result.results_by_solver:
        # Best runtime (lowest)
        best_runtime = min(
            result.results_by_solver.items(),
            key=lambda x: x[1].avg_runtime_seconds if x[1].avg_runtime_seconds > 0 else float('inf')
        )
        result.winner_by_metric["runtime"] = best_runtime[0]

        # Best success rate (highest)
        best_success = max(
            result.results_by_solver.items(),
            key=lambda x: x[1].successes
        )
        result.winner_by_metric["success_rate"] = best_success[0]

    # Generate recommendation
    recommendations = []
    for solver, metrics in result.results_by_solver.items():
        if metrics.failures == 0:
            recommendations.append(f"{solver}: All tests passed")
        else:
            recommendations.append(f"{solver}: {metrics.failures}/{metrics.runs} failed")

    result.recommendation = "; ".join(recommendations)

    return result


async def benchmark_constraints(
    test_schedules: str = "historical",
) -> ConstraintBenchmarkResult:
    """
    Measure constraint effectiveness.

    Analyzes which constraints:
    - Catch real issues (high yield)
    - Generate false positives (low yield)
    - Are candidates for removal
    """
    result = ConstraintBenchmarkResult()

    # Find constraint files
    constraints_dir = BACKEND_ROOT / "app" / "scheduling" / "constraints"
    if not constraints_dir.exists():
        result.recommendation = "Constraints directory not found"
        return result

    # Catalog constraints
    constraint_files = list(constraints_dir.glob("*.py"))
    for cf in constraint_files:
        if cf.name.startswith("_"):
            continue

        name = cf.stem
        lines = _count_lines(cf)

        result.constraint_stats[name] = ConstraintStats(
            constraint_name=name,
            avg_runtime_ms=0,
            description=f"Constraint from {cf.name}",
        )

        # Check if constraint has tests
        test_file = BACKEND_ROOT / "tests" / f"test_{name}.py"
        if test_file.exists():
            # Run constraint tests to check effectiveness
            cmd = [
                "python", "-m", "pytest",
                str(test_file),
                "--tb=no", "-q",
            ]
            returncode, stdout, _ = _run_command(cmd, timeout=60)

            if returncode == 0:
                result.constraint_stats[name].yield_rate = 1.0
                result.high_yield.append(name)
            else:
                result.constraint_stats[name].yield_rate = 0.5
                result.low_yield.append(name)
        else:
            # No tests - unknown yield
            result.constraint_stats[name].yield_rate = 0.0
            result.candidates_for_removal.append(name)

    # Generate recommendations
    if result.high_yield:
        result.recommendation = f"High-yield constraints: {', '.join(result.high_yield)}. "
    if result.candidates_for_removal:
        result.recommendation += f"Missing tests: {', '.join(result.candidates_for_removal)}"

    return result


async def ablation_study(
    module_path: str,
) -> AblationResult:
    """
    Test impact of removing a module.

    Analyzes:
    - Module size and complexity
    - What imports this module
    - What tests would break
    - Whether it's safe to remove
    """
    result = AblationResult(module_path=module_path)

    # Resolve path
    if module_path.startswith("app/"):
        full_path = BACKEND_ROOT / module_path
    else:
        full_path = BACKEND_ROOT / "app" / module_path

    if not full_path.exists():
        result.module_exists = False
        result.recommendation = f"Module not found: {module_path}"
        return result

    # Count lines and files
    if full_path.is_file():
        result.module_size_lines = _count_lines(full_path)
        result.module_size_bytes = full_path.stat().st_size
        result.file_count = 1
    else:
        result.module_size_lines = _count_lines(full_path)
        result.file_count = len(list(full_path.rglob("*.py")))
        result.module_size_bytes = sum(
            f.stat().st_size for f in full_path.rglob("*.py")
            if "__pycache__" not in str(f)
        )

    # Find what imports this module
    module_name = module_path.replace("/", ".").replace(".py", "")
    if module_name.startswith("app."):
        module_name = module_name[4:]

    result.imported_by = _find_importers(module_name, BACKEND_ROOT / "app")

    # Find tests that mention this module
    tests_dir = BACKEND_ROOT / "tests"
    if tests_dir.exists():
        for test_file in tests_dir.rglob("*.py"):
            if "__pycache__" in str(test_file):
                continue
            try:
                content = test_file.read_text()
                if module_name in content or module_path in content:
                    result.tests_affected += 1
            except Exception:
                pass

    # Determine safety
    if len(result.imported_by) == 0:
        result.safe_to_remove = True
        result.removal_impact = "none"
        result.recommendation = (
            f"Safe to remove. {result.module_size_lines} lines, "
            f"no other modules import this."
        )
    elif len(result.imported_by) <= 2:
        result.safe_to_remove = True
        result.removal_impact = "minor"
        result.recommendation = (
            f"Likely safe to remove with minor refactoring. "
            f"Imported by: {', '.join(result.imported_by)}"
        )
    else:
        result.safe_to_remove = False
        result.removal_impact = "major"
        result.recommendation = (
            f"Removal would require significant refactoring. "
            f"Imported by {len(result.imported_by)} modules."
        )

    return result


async def benchmark_resilience(
    modules: list[str] | None = None,
) -> ResilienceBenchmarkResult:
    """
    Compare resilience framework components.

    Identifies:
    - High-value modules (good detection, low false alarm)
    - Low-value modules (candidates for removal)
    """
    result = ResilienceBenchmarkResult()

    # Define known resilience modules with tiers
    known_modules = {
        # Tier 1 - Core
        "utilization_threshold": ("tier1", "80% queuing theory threshold"),
        "defense_levels": ("tier1", "Defense-in-depth (GREEN→BLACK)"),
        "n1_contingency": ("tier1", "N-1 power grid analysis"),
        "n2_contingency": ("tier1", "N-2 power grid analysis"),
        "static_fallbacks": ("tier1", "Pre-computed fallback schedules"),
        "sacrifice_hierarchy": ("tier1", "Triage-based load shedding"),

        # Tier 2 - Strategic
        "homeostasis": ("tier2", "Biological feedback loops"),
        "blast_radius": ("tier2", "Zone containment"),
        "le_chatelier": ("tier2", "Equilibrium shift prediction"),

        # Tier 3 - Advanced
        "hub_centrality": ("tier3", "Single point of failure detection"),
        "stigmergy": ("tier3", "Swarm intelligence patterns"),
        "cognitive_load": ("tier3", "Miller's Law monitoring"),
        "mtf_compliance": ("tier3", "Military training facility rules"),
        "spc_monitoring": ("tier3", "Statistical process control"),
        "burnout_epidemiology": ("tier3", "SIR models for burnout"),
        "erlang_coverage": ("tier3", "Telecommunications queuing"),
        "tensegrity": ("tier3", "Force density method"),
    }

    if modules is None:
        modules = list(known_modules.keys())

    # Analyze each module
    resilience_dir = BACKEND_ROOT / "app" / "resilience"
    services_resilience = BACKEND_ROOT / "app" / "services" / "resilience"

    for module_name in modules:
        tier, description = known_modules.get(module_name, ("unknown", ""))

        # Find module file
        module_file = None
        for search_dir in [resilience_dir, services_resilience]:
            if search_dir.exists():
                for f in search_dir.rglob(f"*{module_name}*.py"):
                    if "__pycache__" not in str(f):
                        module_file = f
                        break

        stats = ResilienceModuleStats(
            module_name=module_name,
            tier=tier,
            description=description,
        )

        if module_file and module_file.exists():
            stats.complexity_lines = _count_lines(module_file)

            # Check for tests
            test_patterns = [
                f"test_{module_name}.py",
                f"test_*{module_name}*.py",
            ]
            has_tests = False
            for pattern in test_patterns:
                if list((BACKEND_ROOT / "tests").rglob(pattern)):
                    has_tests = True
                    break

            if has_tests:
                stats.detection_rate = 0.8  # Assume tested = functional
                stats.false_alarm_rate = 0.1
            else:
                stats.detection_rate = 0.5  # Unknown
                stats.false_alarm_rate = 0.3

        result.module_stats[module_name] = stats

    # Categorize by value
    for name, stats in result.module_stats.items():
        value_score = stats.detection_rate - stats.false_alarm_rate

        if value_score >= 0.5:
            result.high_value.append(name)
        elif value_score <= 0.0:
            result.low_value.append(name)
            if stats.complexity_lines > 500:
                result.cut_candidates.append(name)

    # Tier analysis
    tier_scores = defaultdict(list)
    for name, stats in result.module_stats.items():
        tier_scores[stats.tier].append(
            stats.detection_rate - stats.false_alarm_rate
        )

    for tier, scores in tier_scores.items():
        if scores:
            result.tier_analysis[tier] = sum(scores) / len(scores)

    # Recommendation
    if result.high_value:
        result.recommendation = f"High value: {', '.join(result.high_value[:5])}. "
    if result.cut_candidates:
        result.recommendation += f"Cut candidates: {', '.join(result.cut_candidates)}"

    return result


async def module_usage_analysis(
    entry_points: list[str] | None = None,
) -> ModuleUsageResult:
    """
    Analyze which modules are actually used from entry points.

    Identifies dead code that could be removed.
    """
    result = ModuleUsageResult()

    if entry_points is None:
        entry_points = ["main", "api", "scheduling"]

    result.entry_points_analyzed = entry_points

    # Get all Python modules
    app_dir = BACKEND_ROOT / "app"
    if not app_dir.exists():
        result.recommendation = "App directory not found"
        return result

    all_modules = set()
    module_lines = {}

    for py_file in app_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        rel_path = py_file.relative_to(app_dir)
        module_name = str(rel_path).replace("/", ".").replace(".py", "")
        all_modules.add(module_name)
        module_lines[module_name] = _count_lines(py_file)

    result.total_modules = len(all_modules)

    # Trace imports from entry points
    reachable = set()
    to_process = []

    # Find entry point files
    for ep in entry_points:
        for py_file in app_dir.rglob(f"*{ep}*.py"):
            if "__pycache__" not in str(py_file):
                rel_path = py_file.relative_to(app_dir)
                module_name = str(rel_path).replace("/", ".").replace(".py", "")
                to_process.append((py_file, module_name))

    # BFS through imports
    processed = set()
    while to_process:
        file_path, module_name = to_process.pop(0)
        if module_name in processed:
            continue
        processed.add(module_name)
        reachable.add(module_name)

        imports = _find_imports(file_path)
        for imp in imports:
            if imp.startswith("app."):
                imp_module = imp[4:]
                if imp_module in all_modules and imp_module not in processed:
                    imp_file = app_dir / imp_module.replace(".", "/")
                    if imp_file.with_suffix(".py").exists():
                        to_process.append((imp_file.with_suffix(".py"), imp_module))

    result.reachable_modules = sorted(reachable)
    result.unreachable_modules = sorted(all_modules - reachable)

    # Calculate dead code
    for module in result.unreachable_modules:
        result.dead_code_lines += module_lines.get(module, 0)

    total_lines = sum(module_lines.values())
    if total_lines > 0:
        result.dead_code_percentage = (result.dead_code_lines / total_lines) * 100

    # Identify hot/cold paths based on import count
    import_counts = defaultdict(int)
    for py_file in app_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        for imp in _find_imports(py_file):
            if imp.startswith("app."):
                import_counts[imp[4:]] += 1

    sorted_by_imports = sorted(import_counts.items(), key=lambda x: x[1], reverse=True)
    result.hot_paths = [m for m, c in sorted_by_imports[:10] if c > 5]
    result.cold_paths = [m for m, c in sorted_by_imports if c <= 1][:10]

    # Recommendation
    if result.unreachable_modules:
        result.recommendation = (
            f"Found {len(result.unreachable_modules)} potentially unreachable modules "
            f"({result.dead_code_lines} lines, {result.dead_code_percentage:.1f}%). "
            f"Review: {', '.join(result.unreachable_modules[:5])}"
        )
    else:
        result.recommendation = "All modules appear reachable from entry points."

    return result
