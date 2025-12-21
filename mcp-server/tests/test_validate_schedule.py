"""
Tests for validate_schedule MCP tool.

Tests cover:
- Input validation (schedule_id sanitization)
- Output structure verification
- PII sanitization in responses
- Different constraint configurations
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from tools.validate_schedule import (
    ScheduleValidationRequest,
    ScheduleValidationResponse,
    ValidationIssue,
    ValidationSeverity,
    ConstraintConfig,
    validate_schedule,
    _sanitize_message,
    _sanitize_details,
    _anonymize_entity_ref,
)


class TestScheduleIdValidation:
    """Test suite for schedule_id input validation."""

    def test_valid_uuid_accepted(self):
        """Test that valid UUID schedule_id is accepted."""
        request = ScheduleValidationRequest(
            schedule_id="12345678-1234-1234-1234-123456789abc"
        )
        assert request.schedule_id == "12345678-1234-1234-1234-123456789abc"

    def test_valid_alphanumeric_accepted(self):
        """Test that valid alphanumeric schedule_id is accepted."""
        request = ScheduleValidationRequest(schedule_id="schedule_2025_winter")
        assert request.schedule_id == "schedule_2025_winter"

    def test_valid_hyphenated_accepted(self):
        """Test that hyphenated schedule_id is accepted."""
        request = ScheduleValidationRequest(schedule_id="schedule-2025-01")
        assert request.schedule_id == "schedule-2025-01"

    def test_empty_schedule_id_rejected(self):
        """Test that empty schedule_id is rejected."""
        with pytest.raises(ValidationError):
            ScheduleValidationRequest(schedule_id="")

    def test_whitespace_schedule_id_rejected(self):
        """Test that whitespace-only schedule_id is rejected."""
        with pytest.raises(ValidationError):
            ScheduleValidationRequest(schedule_id="   ")

    def test_too_long_schedule_id_rejected(self):
        """Test that overly long schedule_id is rejected."""
        with pytest.raises(ValidationError):
            ScheduleValidationRequest(schedule_id="a" * 100)

    def test_path_traversal_rejected(self):
        """Test that path traversal attempts are rejected."""
        with pytest.raises(ValidationError):
            ScheduleValidationRequest(schedule_id="../etc/passwd")

    def test_sql_injection_rejected(self):
        """Test that SQL injection attempts are rejected."""
        with pytest.raises(ValidationError):
            ScheduleValidationRequest(schedule_id="'; DROP TABLE--")

    def test_command_injection_rejected(self):
        """Test that command injection attempts are rejected."""
        with pytest.raises(ValidationError):
            ScheduleValidationRequest(schedule_id="schedule; rm -rf /")

    def test_html_injection_rejected(self):
        """Test that HTML injection attempts are rejected."""
        with pytest.raises(ValidationError):
            ScheduleValidationRequest(schedule_id="<script>alert(1)</script>")

    def test_null_byte_rejected(self):
        """Test that null byte injection is rejected."""
        with pytest.raises(ValidationError):
            ScheduleValidationRequest(schedule_id="schedule\x00.txt")

    def test_newline_rejected(self):
        """Test that newline injection is rejected."""
        with pytest.raises(ValidationError):
            ScheduleValidationRequest(schedule_id="schedule\nid")

    def test_shell_expansion_rejected(self):
        """Test that shell expansion attempts are rejected."""
        with pytest.raises(ValidationError):
            ScheduleValidationRequest(schedule_id="$(whoami)")

    def test_special_chars_rejected(self):
        """Test that special characters are rejected."""
        invalid_ids = [
            "schedule@test",
            "schedule#test",
            "schedule!test",
            "schedule%test",
            "schedule`test",
        ]
        for invalid_id in invalid_ids:
            with pytest.raises(ValidationError):
                ScheduleValidationRequest(schedule_id=invalid_id)


class TestConstraintConfigValidation:
    """Test suite for constraint_config validation."""

    def test_default_config(self):
        """Test default constraint configuration."""
        request = ScheduleValidationRequest(schedule_id="test123")
        assert request.constraint_config == ConstraintConfig.DEFAULT

    def test_minimal_config(self):
        """Test minimal constraint configuration."""
        request = ScheduleValidationRequest(
            schedule_id="test123", constraint_config=ConstraintConfig.MINIMAL
        )
        assert request.constraint_config == ConstraintConfig.MINIMAL

    def test_strict_config(self):
        """Test strict constraint configuration."""
        request = ScheduleValidationRequest(
            schedule_id="test123", constraint_config=ConstraintConfig.STRICT
        )
        assert request.constraint_config == ConstraintConfig.STRICT

    def test_resilience_config(self):
        """Test resilience constraint configuration."""
        request = ScheduleValidationRequest(
            schedule_id="test123", constraint_config=ConstraintConfig.RESILIENCE
        )
        assert request.constraint_config == ConstraintConfig.RESILIENCE


class TestPIISanitization:
    """Test suite for PII sanitization functions."""

    def test_email_sanitization(self):
        """Test that email addresses are sanitized."""
        message = "Contact dr.smith@hospital.org for details"
        sanitized = _sanitize_message(message)

        assert "dr.smith@hospital.org" not in sanitized
        assert "[EMAIL REDACTED]" in sanitized

    def test_phone_sanitization(self):
        """Test that phone numbers are sanitized."""
        message = "Call 555-123-4567 for coverage"
        sanitized = _sanitize_message(message)

        assert "555-123-4567" not in sanitized
        assert "[PHONE REDACTED]" in sanitized

    def test_ssn_sanitization(self):
        """Test that SSN patterns are sanitized."""
        message = "SSN 123-45-6789 on file"
        sanitized = _sanitize_message(message)

        assert "123-45-6789" not in sanitized
        assert "[SSN REDACTED]" in sanitized

    def test_doctor_name_sanitization(self):
        """Test that doctor names are sanitized."""
        message = "Dr. Johnson exceeded hours"
        sanitized = _sanitize_message(message)

        assert "Dr. Johnson" not in sanitized
        assert "[PERSON]" in sanitized

    def test_sensitive_fields_removed(self):
        """Test that sensitive fields are removed from details."""
        details = {
            "email": "test@example.com",
            "ssn": "123-45-6789",
            "password": "secret",
            "hours": 85,
            "blocks": 15,
        }

        sanitized = _sanitize_details(details)

        assert "email" not in sanitized
        assert "ssn" not in sanitized
        assert "password" not in sanitized
        assert sanitized["hours"] == 85
        assert sanitized["blocks"] == 15

    def test_entity_anonymization(self):
        """Test that entity references are anonymized."""
        entity_id = "12345678-1234-1234-1234-123456789abc"
        anonymized = _anonymize_entity_ref(entity_id)

        assert anonymized.startswith("entity-")
        assert entity_id not in anonymized

    def test_none_entity_returns_none(self):
        """Test that None entity_id returns None."""
        assert _anonymize_entity_ref(None) is None


class TestValidateScheduleTool:
    """Test suite for the validate_schedule tool function."""

    @pytest.mark.asyncio
    async def test_validate_schedule_returns_response(self):
        """Test that validate_schedule returns proper response."""
        request = ScheduleValidationRequest(schedule_id="test-schedule-123")
        response = await validate_schedule(request)

        assert isinstance(response, ScheduleValidationResponse)
        assert response.schedule_id == "test-schedule-123"
        assert isinstance(response.is_valid, bool)
        assert 0.0 <= response.compliance_rate <= 1.0
        assert response.validated_at is not None

    @pytest.mark.asyncio
    async def test_validate_schedule_default_config(self):
        """Test validation with default configuration."""
        request = ScheduleValidationRequest(
            schedule_id="test123",
            constraint_config=ConstraintConfig.DEFAULT,
        )
        response = await validate_schedule(request)

        assert response.constraint_config == "default"
        # Default config should have fewer/milder issues
        assert response.critical_count == 0

    @pytest.mark.asyncio
    async def test_validate_schedule_strict_config(self):
        """Test validation with strict configuration."""
        request = ScheduleValidationRequest(
            schedule_id="test123",
            constraint_config=ConstraintConfig.STRICT,
        )
        response = await validate_schedule(request)

        assert response.constraint_config == "strict"
        # Strict config should find more issues
        assert len(response.issues) > 0

    @pytest.mark.asyncio
    async def test_validate_schedule_resilience_config(self):
        """Test validation with resilience configuration."""
        request = ScheduleValidationRequest(
            schedule_id="test123",
            constraint_config=ConstraintConfig.RESILIENCE,
        )
        response = await validate_schedule(request)

        assert response.constraint_config == "resilience"
        # Should include resilience-specific issues
        resilience_rules = ["hub_protection", "utilization_buffer"]
        issue_rules = [issue.rule_type for issue in response.issues]
        assert any(rule in issue_rules for rule in resilience_rules)

    @pytest.mark.asyncio
    async def test_validate_schedule_includes_suggestions(self):
        """Test that suggestions are included when requested."""
        request = ScheduleValidationRequest(
            schedule_id="test123",
            constraint_config=ConstraintConfig.STRICT,
            include_suggestions=True,
        )
        response = await validate_schedule(request)

        # At least some issues should have suggestions
        has_suggestions = any(
            issue.suggested_action is not None for issue in response.issues
        )
        assert has_suggestions

    @pytest.mark.asyncio
    async def test_validate_schedule_no_suggestions(self):
        """Test that suggestions are excluded when not requested."""
        request = ScheduleValidationRequest(
            schedule_id="test123",
            constraint_config=ConstraintConfig.STRICT,
            include_suggestions=False,
        )
        response = await validate_schedule(request)

        # No issues should have suggestions
        all_no_suggestions = all(
            issue.suggested_action is None for issue in response.issues
        )
        assert all_no_suggestions

    @pytest.mark.asyncio
    async def test_response_has_correct_structure(self):
        """Test that response has all required fields."""
        request = ScheduleValidationRequest(schedule_id="test123")
        response = await validate_schedule(request)

        # Check all required fields exist
        assert hasattr(response, "schedule_id")
        assert hasattr(response, "is_valid")
        assert hasattr(response, "compliance_rate")
        assert hasattr(response, "total_issues")
        assert hasattr(response, "critical_count")
        assert hasattr(response, "warning_count")
        assert hasattr(response, "info_count")
        assert hasattr(response, "issues")
        assert hasattr(response, "validated_at")
        assert hasattr(response, "constraint_config")
        assert hasattr(response, "metadata")

    @pytest.mark.asyncio
    async def test_issue_counts_match(self):
        """Test that issue counts match actual issues."""
        request = ScheduleValidationRequest(
            schedule_id="test123",
            constraint_config=ConstraintConfig.STRICT,
        )
        response = await validate_schedule(request)

        # Count issues by severity
        actual_critical = sum(
            1 for i in response.issues if i.severity == ValidationSeverity.CRITICAL
        )
        actual_warning = sum(
            1 for i in response.issues if i.severity == ValidationSeverity.WARNING
        )
        actual_info = sum(
            1 for i in response.issues if i.severity == ValidationSeverity.INFO
        )

        assert response.critical_count == actual_critical
        assert response.warning_count == actual_warning
        assert response.info_count == actual_info
        assert response.total_issues == len(response.issues)

    @pytest.mark.asyncio
    async def test_compliance_rate_bounds(self):
        """Test that compliance rate is within valid bounds."""
        for config in ConstraintConfig:
            request = ScheduleValidationRequest(
                schedule_id="test123",
                constraint_config=config,
            )
            response = await validate_schedule(request)

            assert 0.0 <= response.compliance_rate <= 1.0

    @pytest.mark.asyncio
    async def test_is_valid_reflects_critical_issues(self):
        """Test that is_valid is False when critical issues exist."""
        request = ScheduleValidationRequest(
            schedule_id="test123",
            constraint_config=ConstraintConfig.STRICT,
        )
        response = await validate_schedule(request)

        if response.critical_count > 0:
            assert response.is_valid is False
        else:
            assert response.is_valid is True


class TestValidationIssueStructure:
    """Test suite for ValidationIssue structure."""

    def test_issue_has_required_fields(self):
        """Test that ValidationIssue has all required fields."""
        issue = ValidationIssue(
            severity=ValidationSeverity.CRITICAL,
            rule_type="duty_hours",
            message="Test message",
            constraint_name="80HourRule",
        )

        assert issue.severity == ValidationSeverity.CRITICAL
        assert issue.rule_type == "duty_hours"
        assert issue.message == "Test message"
        assert issue.constraint_name == "80HourRule"

    def test_issue_optional_fields(self):
        """Test that optional fields have proper defaults."""
        issue = ValidationIssue(
            severity=ValidationSeverity.WARNING,
            rule_type="supervision",
            message="Test",
            constraint_name="SupervisionRatio",
        )

        assert issue.affected_entity_ref is None
        assert issue.date_context is None
        assert issue.details == {}
        assert issue.suggested_action is None

    def test_issue_with_all_fields(self):
        """Test issue with all fields populated."""
        issue = ValidationIssue(
            severity=ValidationSeverity.INFO,
            rule_type="equity",
            message="Workload imbalance",
            constraint_name="Equity",
            affected_entity_ref="entity-12345678",
            date_context="2025-01-15",
            details={"variance": 0.12},
            suggested_action="Redistribute workload",
        )

        assert issue.affected_entity_ref == "entity-12345678"
        assert issue.date_context == "2025-01-15"
        assert issue.details["variance"] == 0.12
        assert issue.suggested_action == "Redistribute workload"
