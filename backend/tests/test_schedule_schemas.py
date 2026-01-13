"""Tests for schedule Pydantic schemas."""

from datetime import date, datetime
from uuid import uuid4

import pytest

from app.schemas.schedule import (
    ScheduleResponse,
    SchedulingAlgorithm,
    ValidationResult,
    Violation,
)


class TestScheduleResponse:
    """Tests for ScheduleResponse schema."""

    def test_total_assignments_field_name(self):
        """Test that total_assignments field is properly named.

        The field was renamed from total_blocks_assigned to total_assignments
        because it stores assignment count, not block count. This test verifies
        the field is correctly serialized as 'total_assignments' in JSON.
        """
        validation = ValidationResult(
            valid=True,
            total_violations=0,
            violations=[],
            coverage_rate=100.0,
        )

        response = ScheduleResponse(
            status="success",
            message="Schedule generated successfully",
            total_assignments=42,
            total_blocks=50,
            validation=validation,
        )

        # Verify internal field name
        assert response.total_assignments == 42

        # Verify JSON serialization uses correct field name
        json_data = response.model_dump(by_alias=True)
        assert "total_assignments" in json_data
        assert json_data["total_assignments"] == 42

        # Verify old name is NOT in serialized output
        assert "total_blocks_assigned" not in json_data

    def test_schedule_response_serialization(self):
        """Test full ScheduleResponse serialization."""
        validation = ValidationResult(
            valid=True,
            total_violations=0,
            violations=[],
            coverage_rate=95.5,
        )

        response = ScheduleResponse(
            status="partial",
            message="Schedule generated with some gaps",
            total_assignments=87,
            total_blocks=100,
            validation=validation,
            run_id=uuid4(),
            acgme_override_count=2,
        )

        json_data = response.model_dump(by_alias=True)

        assert json_data["status"] == "partial"
        assert json_data["total_assignments"] == 87
        assert json_data["total_blocks"] == 100
        assert json_data["acgme_override_count"] == 2
        assert json_data["validation"]["coverage_rate"] == 95.5

    def test_schedule_response_with_violations(self):
        """Test ScheduleResponse with ACGME violations."""
        violations = [
            Violation(
                type="SUPERVISION_RATIO",
                severity="HIGH",
                message="Insufficient supervision",
            ),
        ]
        validation = ValidationResult(
            valid=False,
            total_violations=1,
            violations=violations,
            coverage_rate=88.0,
        )

        response = ScheduleResponse(
            status="partial",
            message="Generated with violations",
            total_assignments=25,
            total_blocks=30,
            validation=validation,
        )

        assert response.validation.valid is False
        assert len(response.validation.violations) == 1


class TestSchedulingAlgorithm:
    """Tests for SchedulingAlgorithm enum."""

    def test_algorithm_values(self):
        """Test all algorithm values exist."""
        assert SchedulingAlgorithm.GREEDY == "greedy"
        assert SchedulingAlgorithm.CP_SAT == "cp_sat"
        assert SchedulingAlgorithm.PULP == "pulp"
        assert SchedulingAlgorithm.HYBRID == "hybrid"


class TestValidationResult:
    """Tests for ValidationResult schema."""

    def test_valid_schedule(self):
        """Test validation result for valid schedule."""
        result = ValidationResult(
            valid=True,
            total_violations=0,
            violations=[],
            coverage_rate=100.0,
        )
        assert result.valid is True
        assert result.total_violations == 0

    def test_schedule_with_violations(self):
        """Test validation result with violations."""
        violations = [
            Violation(
                type="80_HOUR",
                severity="CRITICAL",
                message="Exceeds 80-hour limit",
                person_id=uuid4(),
                person_name="Dr. Test",
            ),
        ]
        result = ValidationResult(
            valid=False,
            total_violations=1,
            violations=violations,
            coverage_rate=75.0,
        )
        assert result.valid is False
        assert result.total_violations == 1
        assert result.violations[0].type == "80_HOUR"
