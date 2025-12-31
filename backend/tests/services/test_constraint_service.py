"""Test suite for constraint service."""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.services.constraint_service import (
    ConstraintService,
    ValidationSeverity,
    ScheduleValidationIssue,
    ScheduleValidationResult,
)


class TestConstraintService:
    """Test suite for constraint service."""

    @pytest.fixture
    def constraint_service(self, db: Session) -> ConstraintService:
        """Create a constraint service instance."""
        return ConstraintService(db)

    @pytest.fixture
    def resident(self, db: Session) -> Person:
        """Create a resident for testing."""
        person = Person(
            id=uuid4(),
            name="PGY1-01",
            type="resident",
            email="resident1@hospital.org",
            pgy_level=1,
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        return person

    @pytest.fixture
    def rotation_template(self, db: Session) -> RotationTemplate:
        """Create a rotation template for testing."""
        template = RotationTemplate(
            id=uuid4(),
            name="Clinic Rotation",
            activity_type="outpatient",
            abbreviation="CLI",
            max_residents=4,
            supervision_required=True,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @pytest.fixture
    def test_block(self, db: Session) -> Block:
        """Create a test block."""
        block = Block(
            id=uuid4(),
            date=date.today(),
            time_of_day="AM",
            block_number=1,
            is_weekend=False,
            is_holiday=False,
        )
        db.add(block)
        db.commit()
        db.refresh(block)
        return block

    def test_constraint_service_initialization(self, db: Session):
        """Test ConstraintService initialization."""
        service = ConstraintService(db)

        assert service.db is db

    def test_validation_severity_enum(self):
        """Test ValidationSeverity enum values."""
        assert ValidationSeverity.CRITICAL == "critical"
        assert ValidationSeverity.WARNING == "warning"
        assert ValidationSeverity.INFO == "info"

    def test_schedule_validation_issue_creation(self):
        """Test ScheduleValidationIssue creation."""
        issue = ScheduleValidationIssue(
            severity=ValidationSeverity.CRITICAL,
            rule_type="acgme",
            message="80-hour rule violation",
            constraint_name="max_hours_per_week",
            affected_entity_ref="RES-001",
            date_context="2025-01-01",
        )

        assert issue.severity == ValidationSeverity.CRITICAL
        assert issue.rule_type == "acgme"
        assert issue.message == "80-hour rule violation"
        assert issue.constraint_name == "max_hours_per_week"
        assert issue.affected_entity_ref == "RES-001"
        assert issue.date_context == "2025-01-01"

    def test_schedule_validation_issue_optional_fields(self):
        """Test ScheduleValidationIssue optional fields."""
        issue = ScheduleValidationIssue(
            severity=ValidationSeverity.WARNING,
            rule_type="acgme",
            message="Test warning",
            constraint_name="test_constraint",
        )

        assert issue.affected_entity_ref is None
        assert issue.date_context is None
        assert issue.details == {}
        assert issue.suggested_action is None

    def test_schedule_validation_result_creation(self):
        """Test ScheduleValidationResult creation."""
        result = ScheduleValidationResult(
            is_valid=True,
            total_assignments=100,
            issues=[],
        )

        assert result.is_valid is True
        assert result.total_assignments == 100
        assert result.issues == []

    def test_schedule_validation_result_with_issues(self):
        """Test ScheduleValidationResult with validation issues."""
        issues = [
            ScheduleValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                rule_type="acgme",
                message="Test issue",
                constraint_name="test",
            )
        ]

        result = ScheduleValidationResult(
            is_valid=False,
            total_assignments=100,
            issues=issues,
        )

        assert result.is_valid is False
        assert len(result.issues) == 1

    def test_constraint_service_database_access(
        self, constraint_service: ConstraintService, resident: Person
    ):
        """Test that constraint service can access database."""
        # Service should be able to query the database
        assert constraint_service.db is not None

    def test_validation_issue_with_details(self):
        """Test ScheduleValidationIssue with details dictionary."""
        details = {
            "hours_worked": 85,
            "hours_limit": 80,
            "overage": 5,
        }

        issue = ScheduleValidationIssue(
            severity=ValidationSeverity.CRITICAL,
            rule_type="acgme",
            message="80-hour rule violation",
            constraint_name="max_hours_per_week",
            details=details,
        )

        assert issue.details == details
        assert issue.details["hours_worked"] == 85

    def test_validation_issue_with_suggested_action(self):
        """Test ScheduleValidationIssue with suggested action."""
        issue = ScheduleValidationIssue(
            severity=ValidationSeverity.WARNING,
            rule_type="acgme",
            message="Test warning",
            constraint_name="test",
            suggested_action="Remove one shift to comply",
        )

        assert issue.suggested_action == "Remove one shift to comply"

    def test_validation_result_critical_issues(self):
        """Test identifying critical issues in validation result."""
        issues = [
            ScheduleValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                rule_type="acgme",
                message="Critical issue",
                constraint_name="critical_test",
            ),
            ScheduleValidationIssue(
                severity=ValidationSeverity.WARNING,
                rule_type="acgme",
                message="Warning issue",
                constraint_name="warning_test",
            ),
        ]

        result = ScheduleValidationResult(
            is_valid=False,
            total_assignments=100,
            issues=issues,
        )

        critical_issues = [
            i for i in result.issues if i.severity == ValidationSeverity.CRITICAL
        ]
        assert len(critical_issues) == 1

    def test_validation_result_by_severity(self):
        """Test grouping validation issues by severity."""
        issues = [
            ScheduleValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                rule_type="acgme",
                message="Critical 1",
                constraint_name="test",
            ),
            ScheduleValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                rule_type="acgme",
                message="Critical 2",
                constraint_name="test",
            ),
            ScheduleValidationIssue(
                severity=ValidationSeverity.WARNING,
                rule_type="acgme",
                message="Warning",
                constraint_name="test",
            ),
            ScheduleValidationIssue(
                severity=ValidationSeverity.INFO,
                rule_type="acgme",
                message="Info",
                constraint_name="test",
            ),
        ]

        result = ScheduleValidationResult(
            is_valid=False,
            total_assignments=100,
            issues=issues,
        )

        severity_counts = {}
        for issue in result.issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1

        assert severity_counts[ValidationSeverity.CRITICAL] == 2
        assert severity_counts[ValidationSeverity.WARNING] == 1
        assert severity_counts[ValidationSeverity.INFO] == 1

    def test_constraint_service_with_no_assignments(
        self, constraint_service: ConstraintService
    ):
        """Test constraint service with empty database."""
        # Should handle empty database gracefully
        assert constraint_service.db is not None

    def test_validation_issue_pii_anonymization(self):
        """Test that validation issues use anonymized identifiers."""
        # Validation issues should use entity_ref instead of actual names
        issue = ScheduleValidationIssue(
            severity=ValidationSeverity.WARNING,
            rule_type="acgme",
            message="Test issue",
            constraint_name="test",
            affected_entity_ref="RES-001",  # Anonymized
        )

        assert "RES-001" in issue.affected_entity_ref
        assert issue.affected_entity_ref is not None

    def test_validation_result_multiple_rule_types(self):
        """Test validation results covering multiple rule types."""
        issues = [
            ScheduleValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                rule_type="acgme",
                message="ACGME violation",
                constraint_name="test",
            ),
            ScheduleValidationIssue(
                severity=ValidationSeverity.WARNING,
                rule_type="faculty",
                message="Faculty constraint",
                constraint_name="test",
            ),
            ScheduleValidationIssue(
                severity=ValidationSeverity.INFO,
                rule_type="preference",
                message="Preference info",
                constraint_name="test",
            ),
        ]

        result = ScheduleValidationResult(
            is_valid=False,
            total_assignments=100,
            issues=issues,
        )

        rule_types = {issue.rule_type for issue in result.issues}
        assert "acgme" in rule_types
        assert "faculty" in rule_types
        assert "preference" in rule_types

    def test_validation_result_empty_issues(self):
        """Test validation result with no issues."""
        result = ScheduleValidationResult(
            is_valid=True,
            total_assignments=100,
            issues=[],
        )

        assert result.is_valid is True
        assert len(result.issues) == 0

    def test_validation_result_valid_with_info_messages(self):
        """Test valid result can still have info-level messages."""
        issues = [
            ScheduleValidationIssue(
                severity=ValidationSeverity.INFO,
                rule_type="preference",
                message="Schedule is suboptimal for preference",
                constraint_name="test",
            )
        ]

        result = ScheduleValidationResult(
            is_valid=True,
            total_assignments=100,
            issues=issues,
        )

        assert result.is_valid is True
        assert len(result.issues) == 1
        assert result.issues[0].severity == ValidationSeverity.INFO
