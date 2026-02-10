"""Tests for migration validators (pure logic, no DB)."""

import pytest

from app.migrations.validators import (
    MigrationValidator,
    ValidationIssue,
    ValidationResult,
)


# -- ValidationIssue ---------------------------------------------------------


class TestValidationIssue:
    def test_required_fields(self):
        issue = ValidationIssue(severity="error", message="bad data")
        assert issue.severity == "error"
        assert issue.message == "bad data"

    def test_optional_defaults(self):
        issue = ValidationIssue(severity="warning", message="check this")
        assert issue.details is None
        assert issue.record_id is None

    def test_optional_fields(self):
        issue = ValidationIssue(
            severity="error",
            message="missing field",
            details="name is required",
            record_id="abc-123",
        )
        assert issue.details == "name is required"
        assert issue.record_id == "abc-123"

    def test_repr(self):
        issue = ValidationIssue(severity="error", message="bad data")
        r = repr(issue)
        assert "error" in r
        assert "bad data" in r

    def test_severity_values(self):
        for sev in ["error", "warning", "info"]:
            issue = ValidationIssue(severity=sev, message="test")
            assert issue.severity == sev


# -- ValidationResult --------------------------------------------------------


class TestValidationResultInit:
    def test_empty_init(self):
        result = ValidationResult()
        assert result.issues == []
        assert result.checks_run == 0
        assert result.checks_passed == 0
        assert result.checks_failed == 0


class TestValidationResultAddIssue:
    def test_add_error(self):
        result = ValidationResult()
        result.add_issue("error", "bad data")
        assert len(result.issues) == 1
        assert result.issues[0].severity == "error"
        assert result.issues[0].message == "bad data"

    def test_add_warning(self):
        result = ValidationResult()
        result.add_issue("warning", "might be wrong")
        assert result.issues[0].severity == "warning"

    def test_add_with_details(self):
        result = ValidationResult()
        result.add_issue("error", "missing field", details="name is required")
        assert result.issues[0].details == "name is required"

    def test_add_with_record_id(self):
        result = ValidationResult()
        result.add_issue("error", "bad record", record_id="rec-1")
        assert result.issues[0].record_id == "rec-1"

    def test_add_multiple(self):
        result = ValidationResult()
        result.add_issue("error", "e1")
        result.add_issue("warning", "w1")
        result.add_issue("info", "i1")
        assert len(result.issues) == 3


class TestValidationResultIsValid:
    def test_empty_is_valid(self):
        result = ValidationResult()
        assert result.is_valid is True

    def test_warnings_only_is_valid(self):
        result = ValidationResult()
        result.add_issue("warning", "w1")
        result.add_issue("warning", "w2")
        assert result.is_valid is True

    def test_info_only_is_valid(self):
        result = ValidationResult()
        result.add_issue("info", "i1")
        assert result.is_valid is True

    def test_error_makes_invalid(self):
        result = ValidationResult()
        result.add_issue("error", "e1")
        assert result.is_valid is False

    def test_mixed_with_error_is_invalid(self):
        result = ValidationResult()
        result.add_issue("warning", "w1")
        result.add_issue("error", "e1")
        result.add_issue("info", "i1")
        assert result.is_valid is False


class TestValidationResultHasWarnings:
    def test_no_warnings(self):
        result = ValidationResult()
        assert result.has_warnings is False

    def test_with_warning(self):
        result = ValidationResult()
        result.add_issue("warning", "w1")
        assert result.has_warnings is True

    def test_errors_only_no_warnings(self):
        result = ValidationResult()
        result.add_issue("error", "e1")
        assert result.has_warnings is False


class TestValidationResultCounts:
    def test_error_count_empty(self):
        result = ValidationResult()
        assert result.error_count == 0

    def test_error_count(self):
        result = ValidationResult()
        result.add_issue("error", "e1")
        result.add_issue("error", "e2")
        result.add_issue("warning", "w1")
        assert result.error_count == 2

    def test_warning_count_empty(self):
        result = ValidationResult()
        assert result.warning_count == 0

    def test_warning_count(self):
        result = ValidationResult()
        result.add_issue("warning", "w1")
        result.add_issue("warning", "w2")
        result.add_issue("error", "e1")
        assert result.warning_count == 2


class TestValidationResultSummary:
    def test_passed_summary(self):
        result = ValidationResult()
        result.checks_run = 3
        result.checks_passed = 3
        summary = result.get_summary()
        assert "PASSED" in summary
        assert "3/3" in summary
        assert "0 errors" in summary
        assert "0 warnings" in summary

    def test_failed_summary(self):
        result = ValidationResult()
        result.checks_run = 2
        result.checks_passed = 1
        result.add_issue("error", "bad")
        summary = result.get_summary()
        assert "FAILED" in summary
        assert "1/2" in summary
        assert "1 errors" in summary

    def test_with_warnings_summary(self):
        result = ValidationResult()
        result.checks_run = 1
        result.checks_passed = 1
        result.add_issue("warning", "check this")
        summary = result.get_summary()
        assert "PASSED" in summary
        assert "1 warnings" in summary

    def test_repr(self):
        result = ValidationResult()
        r = repr(result)
        assert "ValidationResult" in r
        assert "PASSED" in r


# -- Check factory naming ----------------------------------------------------


class TestCheckFactoryNames:
    """Test that check factories produce functions with correct __name__."""

    def _fake_table(self, name):
        """Create a minimal fake table class with __tablename__."""

        class FakeTable:
            __tablename__ = name

        return FakeTable

    def test_check_no_null_values_name(self):
        table = self._fake_table("persons")
        check = MigrationValidator.check_no_null_values(table, "email")
        assert check.__name__ == "check_no_null_persons_email"
        assert callable(check)

    def test_check_unique_constraint_name(self):
        table = self._fake_table("users")
        check = MigrationValidator.check_unique_constraint(table, "username")
        assert check.__name__ == "check_unique_users_username"
        assert callable(check)

    def test_check_foreign_key_integrity_name(self):
        table = self._fake_table("assignments")
        ref_table = self._fake_table("persons")
        check = MigrationValidator.check_foreign_key_integrity(
            table, "person_id", ref_table
        )
        assert check.__name__ == "check_fk_assignments_person_id"
        assert callable(check)

    def test_check_value_in_range_name(self):
        table = self._fake_table("scores")
        check = MigrationValidator.check_value_in_range(
            table, "score", min_value=0, max_value=100
        )
        assert check.__name__ == "check_range_scores_score"
        assert callable(check)

    def test_check_email_format_name(self):
        table = self._fake_table("persons")
        check = MigrationValidator.check_email_format(table)
        assert check.__name__ == "check_email_persons_email"
        assert callable(check)

    def test_check_email_format_custom_field(self):
        table = self._fake_table("contacts")
        check = MigrationValidator.check_email_format(table, field="contact_email")
        assert check.__name__ == "check_email_contacts_contact_email"

    def test_check_record_count_unchanged_name(self):
        table = self._fake_table("events")
        check = MigrationValidator.check_record_count_unchanged(table, 100)
        assert check.__name__ == "check_count_events"
        assert callable(check)

    def test_check_custom_name(self):
        check = MigrationValidator.check_custom(
            lambda db: (True, "ok"), "my_custom_check"
        )
        assert check.__name__ == "my_custom_check"
        assert callable(check)
