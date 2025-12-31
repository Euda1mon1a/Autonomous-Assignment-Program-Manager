"""
Tests for Constraint Validator

Tests for constraint validation system including syntax, feasibility,
conflict detection, and coverage analysis.
"""

import pytest

from app.scheduling.constraint_validator import (
    ConstraintValidator,
    ValidationReport,
    quick_syntax_check,
    validate_constraint_manager,
)
from app.scheduling.constraints.acgme import (
    AvailabilityConstraint,
    EightyHourRuleConstraint,
    OneInSevenRuleConstraint,
    SupervisionRatioConstraint,
)
from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    HardConstraint,
    SchedulingContext,
)
from app.scheduling.constraints.capacity import CoverageConstraint
from app.scheduling.constraints.manager import ConstraintManager


@pytest.fixture
def constraint_manager():
    """Create constraint manager with standard constraints."""
    manager = ConstraintManager()
    manager.add(AvailabilityConstraint())
    manager.add(EightyHourRuleConstraint())
    manager.add(OneInSevenRuleConstraint())
    manager.add(SupervisionRatioConstraint())
    return manager


@pytest.fixture
def context():
    """Create empty scheduling context."""
    return SchedulingContext(residents=[], faculty=[], blocks=[], templates=[])


class TestConstraintValidator:
    """Tests for main validator orchestrator."""

    def test_validator_initialization(self, constraint_manager, context):
        """Test validator initializes correctly."""
        validator = ConstraintValidator(constraint_manager, context)
        assert validator.manager is constraint_manager
        assert validator.context is context

    def test_validate_all_returns_report(self, constraint_manager, context):
        """Test validate_all returns ValidationReport."""
        validator = ConstraintValidator(constraint_manager, context)
        report = validator.validate_all()

        assert isinstance(report, ValidationReport)
        assert report.valid is not None
        assert isinstance(report.errors, list)
        assert isinstance(report.warnings, list)

    def test_report_summary_includes_stats(self, constraint_manager, context):
        """Test report includes summary statistics."""
        validator = ConstraintValidator(constraint_manager, context)
        report = validator.validate_all()

        assert "total_constraints" in report.summary
        assert "hard_constraints" in report.summary
        assert "soft_constraints" in report.summary
        assert report.summary["total_constraints"] == 4

    def test_validate_with_missing_name_error(self):
        """Test validation detects constraint with missing name."""
        manager = ConstraintManager()

        # Create constraint without name
        bad_constraint = HardConstraint(
            name="",
            constraint_type=ConstraintType.AVAILABILITY,
        )
        manager.add(bad_constraint)

        context = SchedulingContext(residents=[], faculty=[], blocks=[], templates=[])
        validator = ConstraintValidator(manager, context)
        report = validator.validate_all()

        # Should have errors
        assert not report.is_valid
        assert len(report.errors) > 0


class TestValidationReport:
    """Tests for ValidationReport."""

    def test_report_initialization(self):
        """Test report initializes correctly."""
        report = ValidationReport(valid=True)
        assert report.valid is True
        assert len(report.errors) == 0
        assert len(report.warnings) == 0

    def test_report_add_error(self):
        """Test adding error to report."""
        report = ValidationReport(valid=True)
        report.add_error("SYNTAX", "Test error")

        assert not report.valid
        assert len(report.errors) == 1
        assert report.errors[0].message == "Test error"

    def test_report_add_warning(self):
        """Test adding warning to report."""
        report = ValidationReport(valid=True)
        report.add_warning("FEASIBILITY", "Test warning")

        assert report.valid  # Warnings don't make report invalid
        assert len(report.warnings) == 1

    def test_report_is_valid(self):
        """Test is_valid property."""
        report = ValidationReport(valid=True)
        assert report.is_valid

        report.add_error("TEST", "Error")
        assert not report.is_valid

    def test_report_has_warnings(self):
        """Test has_warnings property."""
        report = ValidationReport(valid=True)
        assert not report.has_warnings

        report.add_warning("TEST", "Warning")
        assert report.has_warnings


class TestConstraintSyntaxValidator:
    """Tests for syntax validation."""

    def test_syntax_valid_hard_constraint(self):
        """Test valid hard constraint passes syntax check."""
        constraint = AvailabilityConstraint()
        assert quick_syntax_check([constraint])

    def test_syntax_valid_multiple_constraints(self):
        """Test multiple valid constraints pass syntax check."""
        constraints = [
            AvailabilityConstraint(),
            EightyHourRuleConstraint(),
            OneInSevenRuleConstraint(),
        ]
        assert quick_syntax_check(constraints)


class TestConstraintFeasibilityChecker:
    """Tests for feasibility checking."""

    def test_feasibility_with_few_constraints(self, constraint_manager, context):
        """Test feasibility check passes with reasonable constraints."""
        validator = ConstraintValidator(constraint_manager, context)
        report = validator.validate_all()

        # With standard constraints, feasibility should be OK
        assert report.is_valid or any(
            e.category != "FEASIBILITY" for e in report.errors
        )

    def test_feasibility_warning_with_many_constraints(self):
        """Test feasibility warning with many hard constraints."""
        manager = ConstraintManager()

        # Add 25 hard constraints
        for i in range(25):
            constraint = HardConstraint(
                name=f"Constraint{i}",
                constraint_type=ConstraintType.CAPACITY,
                priority=ConstraintPriority.HIGH,
            )
            manager.add(constraint)

        context = SchedulingContext(residents=[], faculty=[], blocks=[], templates=[])
        validator = ConstraintValidator(manager, context)
        report = validator.validate_all()

        # Should have feasibility warning
        feasibility_warnings = [
            w for w in report.warnings if w.category == "FEASIBILITY"
        ]
        assert len(feasibility_warnings) > 0


class TestConstraintCoverageAnalyzer:
    """Tests for coverage analysis."""

    def test_coverage_analysis_includes_acgme(self, constraint_manager, context):
        """Test coverage analysis checks ACGME compliance."""
        validator = ConstraintValidator(constraint_manager, context)
        report = validator.validate_all()

        assert "acgme_coverage" in report.summary

    def test_coverage_missing_acgme_constraint(self):
        """Test coverage detects missing ACGME constraint."""
        manager = ConstraintManager()
        manager.add(AvailabilityConstraint())
        # Missing EightyHourRule, OneInSevenRule, SupervisionRatio

        context = SchedulingContext(residents=[], faculty=[], blocks=[], templates=[])
        validator = ConstraintValidator(manager, context)
        report = validator.validate_all()

        # Should have coverage error
        coverage_errors = [
            e for e in report.errors if e.category == "COVERAGE"
        ]
        assert len(coverage_errors) > 0


class TestConstraintConflictDetector:
    """Tests for conflict detection."""

    def test_conflict_detection_runs(self, constraint_manager, context):
        """Test conflict detection completes without error."""
        validator = ConstraintValidator(constraint_manager, context)
        report = validator.validate_all()

        # Should complete without exception
        assert isinstance(report, ValidationReport)


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_quick_syntax_check(self):
        """Test quick_syntax_check function."""
        constraints = [AvailabilityConstraint(), EightyHourRuleConstraint()]
        assert quick_syntax_check(constraints)

    def test_validate_constraint_manager(self, constraint_manager, context):
        """Test validate_constraint_manager function."""
        report = validate_constraint_manager(constraint_manager, context)

        assert isinstance(report, ValidationReport)
        assert isinstance(report.summary, dict)
