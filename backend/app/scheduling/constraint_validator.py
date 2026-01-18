"""
Constraint Validator - Pre-solver validation system.

This module provides comprehensive validation of constraints before they are
applied to the solver, helping catch configuration errors early.

Features:
    - Syntax validation (constraint structure)
    - Feasibility checking (can constraints be satisfied together?)
    - Conflict detection (constraint interactions)
    - Completeness verification (coverage of requirements)
    - Coverage analysis (what requirements are covered?)
    - Dependency analysis (constraint dependencies)
    - Performance profiling (constraint computational cost)

Classes:
    - ConstraintValidator: Main validator orchestrator
    - ConstraintSyntaxValidator: Structure and syntax checking
    - ConstraintFeasibilityChecker: Feasibility analysis
    - ConstraintConflictDetector: Conflict detection
    - ConstraintCoverageAnalyzer: Coverage analysis
    - ConstraintDependencyAnalyzer: Dependency tracking
    - ConstraintPerformanceProfiler: Performance estimation

Example:
    >>> validator = ConstraintValidator(manager, context)
    >>> report = validator.validate_all()
    >>> if not report.is_valid:
    ...     for error in report.errors:
    ...         print(f"ERROR: {error}")
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from app.scheduling.constraints.base import (
    Constraint,
    ConstraintPriority,
    ConstraintType,
    HardConstraint,
    SchedulingContext,
    SoftConstraint,
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Represents a validation error or warning."""

    level: str  # 'ERROR', 'WARNING', 'INFO'
    category: str  # 'SYNTAX', 'FEASIBILITY', 'CONFLICT', 'COVERAGE', 'PERFORMANCE'
    message: str
    constraint_name: str | None = None
    details: dict = field(default_factory=dict)

    def __str__(self) -> str:
        """String representation."""
        return f"[{self.level}/{self.category}] {self.message}"


@dataclass
class ValidationReport:
    """Complete validation report."""

    valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    timestamp: str | None = None

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are warnings."""
        return len(self.warnings) > 0

    def add_error(
        self,
        category: str,
        message: str,
        constraint_name: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Add error to report."""
        self.errors.append(
            ValidationError(
                level="ERROR",
                category=category,
                message=message,
                constraint_name=constraint_name,
                details=details or {},
            )
        )
        self.valid = False

    def add_warning(
        self,
        category: str,
        message: str,
        constraint_name: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Add warning to report."""
        self.warnings.append(
            ValidationError(
                level="WARNING",
                category=category,
                message=message,
                constraint_name=constraint_name,
                details=details or {},
            )
        )


class ConstraintValidator:
    """
    Main constraint validation orchestrator.

    Coordinates all validation checks and produces a comprehensive report.

    Usage:
        >>> validator = ConstraintValidator(manager, context)
        >>> report = validator.validate_all()
        >>> print(f"Valid: {report.is_valid}")
        >>> for error in report.errors:
        ...     print(f"- {error}")
    """

    def __init__(
        self,
        manager: Any,
        context: SchedulingContext,
    ) -> None:
        """
        Initialize validator.

        Args:
            manager: ConstraintManager instance to validate
            context: SchedulingContext with domain data
        """
        self.manager = manager
        self.context = context

        # Sub-validators
        self.syntax_validator = ConstraintSyntaxValidator()
        self.feasibility_checker = ConstraintFeasibilityChecker()
        self.conflict_detector = ConstraintConflictDetector()
        self.coverage_analyzer = ConstraintCoverageAnalyzer()
        self.dependency_analyzer = ConstraintDependencyAnalyzer()
        self.performance_profiler = ConstraintPerformanceProfiler()

    def validate_all(self) -> ValidationReport:
        """
        Run all validation checks.

        Returns:
            ValidationReport with complete validation results
        """
        report = ValidationReport(valid=True)

        # Phase 1: Syntax validation
        logger.info("Phase 1: Validating constraint syntax...")
        self.syntax_validator.validate_all(self.manager.constraints, report)

        # Phase 2: Feasibility checking
        logger.info("Phase 2: Checking constraint feasibility...")
        self.feasibility_checker.check_feasibility(
            self.manager.get_enabled(), self.context, report
        )

        # Phase 3: Conflict detection
        logger.info("Phase 3: Detecting constraint conflicts...")
        self.conflict_detector.detect_conflicts(self.manager.get_enabled(), report)

        # Phase 4: Coverage analysis
        logger.info("Phase 4: Analyzing coverage...")
        self.coverage_analyzer.analyze_coverage(self.manager.get_enabled(), report)

        # Phase 5: Dependency analysis
        logger.info("Phase 5: Analyzing dependencies...")
        self.dependency_analyzer.analyze_dependencies(self.manager.constraints, report)

        # Phase 6: Performance profiling
        logger.info("Phase 6: Profiling performance...")
        self.performance_profiler.profile_performance(
            self.manager.get_enabled(), self.context, report
        )

        logger.info(f"Validation complete: {report.is_valid}")
        return report

    def validate_subset(
        self,
        constraints: list[Constraint],
    ) -> ValidationReport:
        """Validate a subset of constraints."""
        report = ValidationReport(valid=True)
        self.syntax_validator.validate_all(constraints, report)
        return report


class ConstraintSyntaxValidator:
    """Validates constraint syntax and structure."""

    def validate_all(
        self,
        constraints: list[Constraint],
        report: ValidationReport,
    ) -> None:
        """Validate all constraints."""
        for constraint in constraints:
            self.validate_constraint(constraint, report)

    def validate_constraint(
        self,
        constraint: Constraint,
        report: ValidationReport,
    ) -> None:
        """Validate single constraint."""
        # Check required attributes
        if not hasattr(constraint, "name") or not constraint.name:
            report.add_error(
                "SYNTAX",
                "Constraint missing required attribute: name",
                constraint.__class__.__name__,
            )

        if not hasattr(constraint, "constraint_type"):
            report.add_error(
                "SYNTAX",
                "Constraint missing required attribute: constraint_type",
                constraint.name,
            )

        if not hasattr(constraint, "priority"):
            report.add_error(
                "SYNTAX",
                "Constraint missing required attribute: priority",
                constraint.name,
            )

        # Check soft constraint weight
        if isinstance(constraint, SoftConstraint):
            if not hasattr(constraint, "weight") or constraint.weight < 0:
                report.add_warning(
                    "SYNTAX",
                    f"Soft constraint {constraint.name} has invalid weight",
                    constraint.name,
                    {"weight": getattr(constraint, "weight", None)},
                )

        # Check method implementation
        for method_name in ["add_to_cpsat", "add_to_pulp", "validate"]:
            if not hasattr(constraint, method_name):
                report.add_error(
                    "SYNTAX",
                    f"Constraint missing required method: {method_name}",
                    constraint.name,
                )


class ConstraintFeasibilityChecker:
    """Checks if constraints can be satisfied together."""

    def check_feasibility(
        self,
        constraints: list[Constraint],
        context: SchedulingContext,
        report: ValidationReport,
    ) -> None:
        """Check if constraints are feasible together."""
        # Get hard constraints
        hard_constraints = [c for c in constraints if isinstance(c, HardConstraint)]

        if len(hard_constraints) == 0:
            return

        # Warning: Too many hard constraints may reduce feasibility
        if len(hard_constraints) > 20:
            report.add_warning(
                "FEASIBILITY",
                f"System has {len(hard_constraints)} hard constraints - "
                "may reduce solution space",
                details={"hard_constraint_count": len(hard_constraints)},
            )

        # Check for obviously infeasible combinations
        self._check_infeasible_combinations(hard_constraints, report)

    def _check_infeasible_combinations(
        self,
        constraints: list[HardConstraint],
        report: ValidationReport,
    ) -> None:
        """
        Check for known infeasible constraint combinations.

        Detects combinations that can never be satisfied together, such as:
        - Contradictory availability requirements
        - Capacity constraints that exceed resource limits
        - Mutually exclusive assignments
        """
        constraint_names = {c.name for c in constraints}
        constraint_types = {c.constraint_type for c in constraints}

        # Known infeasible combinations
        infeasible_pairs = [
            # Strict no-overlap + mandatory double-booking = impossible
            ("NoDoubleBooking", "MandatoryDoubleBooking"),
            # Full coverage + no overtime = may be impossible with limited staff
            ("FullCoverageRequired", "ZeroOvertimeStrict"),
            # Block all leaves + mandatory leave compliance = impossible
            ("BlockAllLeaves", "MandatoryLeaveCompliance"),
        ]

        for c1_name, c2_name in infeasible_pairs:
            if c1_name in constraint_names and c2_name in constraint_names:
                report.add_error(
                    "FEASIBILITY",
                    f"Infeasible combination: {c1_name} and {c2_name} cannot both be satisfied",
                    details={"constraint1": c1_name, "constraint2": c2_name},
                )

        # Check for ACGME compliance + aggressive scheduling conflicts
        acgme_constraints = [
            c for c in constraints if "ACGME" in c.name.upper() or "80Hour" in c.name
        ]
        aggressive_work = [
            c
            for c in constraints
            if "MaximizeCoverage" in c.name or "FillAllSlots" in c.name
        ]

        if acgme_constraints and aggressive_work:
            report.add_warning(
                "FEASIBILITY",
                "ACGME compliance constraints may conflict with aggressive coverage constraints. "
                "Solver may not find a solution or may prioritize incorrectly.",
                details={
                    "acgme_constraints": [c.name for c in acgme_constraints],
                    "coverage_constraints": [c.name for c in aggressive_work],
                },
            )

        # Check capacity vs demand ratio
        capacity_constraints = [
            c for c in constraints if c.constraint_type == ConstraintType.CAPACITY
        ]
        coverage_constraints = [
            c for c in constraints if c.constraint_type == ConstraintType.COVERAGE
        ]

        if len(capacity_constraints) > 3 and len(coverage_constraints) > 3:
            report.add_warning(
                "FEASIBILITY",
                f"High number of capacity ({len(capacity_constraints)}) and coverage ({len(coverage_constraints)}) "
                "constraints may reduce solution feasibility",
                details={
                    "capacity_count": len(capacity_constraints),
                    "coverage_count": len(coverage_constraints),
                },
            )


class ConstraintConflictDetector:
    """Detects conflicts between constraints."""

    def detect_conflicts(
        self,
        constraints: list[Constraint],
        report: ValidationReport,
    ) -> None:
        """Detect constraint conflicts."""
        # Check for conflicting priorities
        for i, c1 in enumerate(constraints):
            for c2 in constraints[i + 1 :]:
                if self._conflicts(c1, c2):
                    report.add_warning(
                        "CONFLICT",
                        f"Potential conflict between {c1.name} and {c2.name}",
                        details={"constraint1": c1.name, "constraint2": c2.name},
                    )

    def _conflicts(self, c1: Constraint, c2: Constraint) -> bool:
        """Check if two constraints conflict."""
        # Known conflicts from CONSTRAINT_CATALOG.md
        conflict_pairs = [
            ("Equity", "Continuity"),
            ("HubProtection", "Fairness"),
            ("CallSpacing", "CallEquity"),
        ]

        for name1, name2 in conflict_pairs:
            if (c1.name == name1 and c2.name == name2) or (
                c1.name == name2 and c2.name == name1
            ):
                return True

        return False


class ConstraintCoverageAnalyzer:
    """Analyzes what requirements are covered by constraints."""

    def analyze_coverage(
        self,
        constraints: list[Constraint],
        report: ValidationReport,
    ) -> None:
        """Analyze constraint coverage."""
        # Check coverage of ACGME requirements
        acgme_constraints = self._find_acgme_constraints(constraints)

        required_acgme = {"Availability", "EightyHourRule", "OneInSevenRule"}
        covered_acgme = {c.name for c in acgme_constraints}

        missing = required_acgme - covered_acgme
        if missing:
            report.add_error(
                "COVERAGE",
                f"Missing ACGME compliance constraints: {missing}",
                details={"missing": list(missing)},
            )

        # Summary
        report.summary["acgme_coverage"] = len(covered_acgme)
        report.summary["total_constraints"] = len(constraints)
        report.summary["hard_constraints"] = len(
            [c for c in constraints if isinstance(c, HardConstraint)]
        )
        report.summary["soft_constraints"] = len(
            [c for c in constraints if isinstance(c, SoftConstraint)]
        )

    def _find_acgme_constraints(
        self,
        constraints: list[Constraint],
    ) -> list[Constraint]:
        """Find all ACGME-related constraints."""
        acgme_names = {
            "Availability",
            "EightyHourRule",
            "OneInSevenRule",
            "SupervisionRatio",
        }
        return [c for c in constraints if c.name in acgme_names]


class ConstraintDependencyAnalyzer:
    """Analyzes dependencies between constraints."""

    # Known constraint dependencies (dependent -> required constraints)
    KNOWN_DEPENDENCIES = {
        # Post-call assignments need call tracking
        "PostCallAutoAssignment": ["CallAvailability", "CallCoverageMandatory"],
        "PostFMITRecovery": ["FMITMandatoryCall"],
        "NightFloatPostCall": ["OvernightCallGeneration"],
        # ACGME validation needs work tracking
        "ACGME80HourRule": ["WorkHourTracking"],
        "ACGME24Plus4Rule": ["ShiftDurationTracking"],
        # Supervision needs faculty assignment
        "SupervisionRatioEnforcement": ["FacultyAvailability"],
        # Leave handling needs availability tracking
        "LeaveBlockEnforcement": ["AvailabilityTracking"],
        # Equity constraints need workload tracking
        "CallEquityDistribution": ["CallTracking", "WorkloadTracking"],
        # Night float scheduling chains
        "NightFloatRotation": ["NightFloatAvailability", "PostCallAutoAssignment"],
    }

    def analyze_dependencies(
        self,
        constraints: list[Constraint],
        report: ValidationReport,
    ) -> None:
        """
        Analyze constraint dependencies.

        Checks that when a constraint is enabled, all of its required
        dependencies are also enabled for proper functioning.
        """
        constraint_names = {c.name for c in constraints}

        for dependent, required_list in self.KNOWN_DEPENDENCIES.items():
            if dependent in constraint_names:
                missing = [req for req in required_list if req not in constraint_names]
                if missing:
                    report.add_warning(
                        "DEPENDENCY",
                        f"{dependent} requires {', '.join(missing)} to function correctly",
                        dependent,
                        {"depends_on": missing, "all_dependencies": required_list},
                    )

        # Check for circular dependencies (shouldn't happen but good to verify)
        self._check_circular_dependencies(constraints, report)

    def _check_circular_dependencies(
        self,
        constraints: list[Constraint],
        report: ValidationReport,
    ) -> None:
        """Check for circular dependency chains."""
        constraint_names = {c.name for c in constraints}

        # Build dependency graph for active constraints
        active_deps = {
            name: deps
            for name, deps in self.KNOWN_DEPENDENCIES.items()
            if name in constraint_names
        }

        # Simple cycle detection using visited tracking
        def has_cycle(node: str, visited: set, path: set) -> bool:
            if node in path:
                return True
            if node in visited:
                return False

            visited.add(node)
            path.add(node)

            for dep in active_deps.get(node, []):
                if dep in constraint_names and has_cycle(dep, visited, path):
                    return True

            path.remove(node)
            return False

        for name in active_deps:
            if has_cycle(name, set(), set()):
                report.add_error(
                    "DEPENDENCY",
                    f"Circular dependency detected involving {name}",
                    name,
                    {"constraint": name},
                )
                break  # Stop after first cycle found


class ConstraintPerformanceProfiler:
    """Estimates performance impact of constraints."""

    # Base complexity per constraint type (operations per unit)
    BASE_COMPLEXITY = {
        ConstraintType.AVAILABILITY: 1,  # O(n) - linear
        ConstraintType.CAPACITY: 10,  # O(n²) - quadratic
        ConstraintType.EQUITY: 5,  # O(n log n)
        ConstraintType.CALL: 8,  # O(n log n)
        ConstraintType.SUPERVISION: 3,  # O(n)
        ConstraintType.CONSECUTIVE_DAYS: 2,  # O(n)
        ConstraintType.DUTY_HOURS: 4,  # O(n)
        ConstraintType.ROTATION: 3,  # O(n)
        ConstraintType.CONTINUITY: 2,  # O(n)
        ConstraintType.RESILIENCE: 6,  # O(n log n)
    }

    def profile_performance(
        self,
        constraints: list[Constraint],
        context: SchedulingContext,
        report: ValidationReport,
    ) -> None:
        """
        Profile constraint performance with dynamic complexity estimation.

        Complexity is calculated as O(residents × blocks × constraint_factor).
        """
        # Get problem size from context - use actual list lengths, not arbitrary defaults
        # This ensures complexity warnings are accurate for real workloads
        num_residents = (
            len(context.residents)
            if hasattr(context, "residents") and context.residents
            else getattr(context, "num_residents", 20)
        )
        num_blocks = (
            len(context.blocks)
            if hasattr(context, "blocks") and context.blocks
            else getattr(context, "num_blocks", 100)
        )
        problem_size = num_residents * num_blocks

        # Calculate complexity per constraint
        total_complexity = 0
        constraint_complexities = []

        for constraint in constraints:
            base = self.BASE_COMPLEXITY.get(constraint.constraint_type, 5)

            # Hard constraints add more overhead (must be strictly enforced)
            multiplier = 2.0 if isinstance(constraint, HardConstraint) else 1.0

            # High priority constraints are checked more frequently
            priority_factor = {
                ConstraintPriority.MANDATORY: 1.5,
                ConstraintPriority.HIGH: 1.2,
                ConstraintPriority.MEDIUM: 1.0,
                ConstraintPriority.LOW: 0.8,
            }.get(constraint.priority, 1.0)

            complexity = int(base * multiplier * priority_factor * (problem_size / 100))
            total_complexity += complexity

            constraint_complexities.append(
                {
                    "name": constraint.name,
                    "type": constraint.constraint_type.value
                    if hasattr(constraint.constraint_type, "value")
                    else str(constraint.constraint_type),
                    "complexity": complexity,
                }
            )

        report.summary["estimated_complexity"] = total_complexity
        report.summary["problem_size"] = {
            "residents": num_residents,
            "blocks": num_blocks,
            "decision_variables": problem_size,
        }

        # Sort by complexity for reporting
        constraint_complexities.sort(key=lambda x: x["complexity"], reverse=True)
        report.summary["top_complexity_constraints"] = constraint_complexities[:5]

        # Warnings based on estimated solver time
        # Rough estimate: 1000 complexity units ≈ 1 second of solver time
        estimated_seconds = total_complexity / 1000

        if estimated_seconds > 60:
            report.add_warning(
                "PERFORMANCE",
                f"High complexity: estimated {estimated_seconds:.0f}s solver time "
                f"(complexity={total_complexity}, problem_size={problem_size})",
                details={
                    "complexity_score": total_complexity,
                    "estimated_seconds": estimated_seconds,
                    "problem_size": problem_size,
                },
            )
        elif estimated_seconds > 10:
            report.add_warning(
                "PERFORMANCE",
                f"Moderate complexity: estimated {estimated_seconds:.0f}s solver time",
                details={
                    "complexity_score": total_complexity,
                    "estimated_seconds": estimated_seconds,
                },
            )

        # Check for soft constraint weight distribution
        soft_constraints = [c for c in constraints if isinstance(c, SoftConstraint)]
        if soft_constraints:
            weights = [c.weight for c in soft_constraints]
            avg_weight = sum(weights) / len(weights)
            max_weight = max(weights)
            min_weight = min(weights)

            report.summary["soft_constraint_stats"] = {
                "count": len(soft_constraints),
                "avg_weight": avg_weight,
                "max_weight": max_weight,
                "min_weight": min_weight,
                "weight_ratio": max_weight / min_weight
                if min_weight > 0
                else float("inf"),
            }

            # Warn if weights are highly imbalanced
            if min_weight > 0 and max_weight / min_weight > 100:
                report.add_warning(
                    "PERFORMANCE",
                    f"Soft constraint weights highly imbalanced (ratio: {max_weight / min_weight:.0f}x). "
                    "Lower-weight constraints may be effectively ignored.",
                    details={
                        "max_weight": max_weight,
                        "min_weight": min_weight,
                    },
                )


# Convenience functions


def validate_constraint_manager(
    manager: Any,
    context: SchedulingContext,
) -> ValidationReport:
    """
    Validate constraint manager before solving.

    Usage:
        >>> report = validate_constraint_manager(manager, context)
        >>> if report.is_valid:
        ...     solve_schedule(manager, context)
        ... else:
        ...     print_errors(report)

    Args:
        manager: ConstraintManager instance
        context: SchedulingContext

    Returns:
        ValidationReport
    """
    validator = ConstraintValidator(manager, context)
    return validator.validate_all()


def quick_syntax_check(constraints: list[Constraint]) -> bool:
    """Quick syntax check for constraints."""
    report = ValidationReport(valid=True)
    validator = ConstraintSyntaxValidator()
    validator.validate_all(constraints, report)
    return report.is_valid
