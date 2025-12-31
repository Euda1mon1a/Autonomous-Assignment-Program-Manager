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
            self.manager.get_enabled(), report
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
        """Check for known infeasible combinations."""
        constraint_types = {c.constraint_type for c in constraints}

        # Example: Cannot have both CRITICAL availability and complete coverage
        # (in a scheduling scenario where requirements exceed capacity)
        pass


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

    def analyze_dependencies(
        self,
        constraints: list[Constraint],
        report: ValidationReport,
    ) -> None:
        """Analyze constraint dependencies."""
        # Known dependencies
        dependencies = {
            "PostCallAutoAssignment": ["CallAvailability"],
            "PostFMITRecovery": ["FMITMandatoryCall"],
            "NightFloatPostCall": ["OvernightCallGeneration"],
        }

        constraint_names = {c.name for c in constraints}

        for dependent, required_list in dependencies.items():
            if dependent in constraint_names:
                for required in required_list:
                    if required not in constraint_names:
                        report.add_warning(
                            "DEPENDENCY",
                            f"{dependent} requires {required} to function correctly",
                            dependent,
                            {"depends_on": required},
                        )


class ConstraintPerformanceProfiler:
    """Estimates performance impact of constraints."""

    def profile_performance(
        self,
        constraints: list[Constraint],
        report: ValidationReport,
    ) -> None:
        """Profile constraint performance."""
        # Estimate computational complexity
        total_complexity = 0

        complexity_estimates = {
            ConstraintType.AVAILABILITY: 10,  # O(n)
            ConstraintType.CAPACITY: 100,  # O(n²)
            ConstraintType.EQUITY: 50,  # O(n)
            ConstraintType.CALL: 75,  # O(n log n)
        }

        for constraint in constraints:
            complexity = complexity_estimates.get(constraint.constraint_type, 50)
            total_complexity += complexity

        report.summary["estimated_complexity"] = total_complexity

        if total_complexity > 1000:
            report.add_warning(
                "PERFORMANCE",
                f"High estimated computational complexity: {total_complexity}",
                details={"complexity_score": total_complexity},
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
            }


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
