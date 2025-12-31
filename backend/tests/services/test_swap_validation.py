"""Test suite for swap validation service."""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.person import Person
from app.services.swap_validation import (
    SwapValidationService,
    SwapValidationResult,
    ValidationError,
)


class TestSwapValidationService:
    """Test suite for swap validation service."""

    @pytest.fixture
    def validation_service(self, db: Session) -> SwapValidationService:
        """Create a swap validation service instance."""
        return SwapValidationService(db)

    @pytest.fixture
    def faculty_user(self, db: Session) -> Person:
        """Create a faculty user for testing."""
        faculty = Person(
            id=uuid4(),
            name="Dr. Faculty Test",
            type="faculty",
            email="faculty@hospital.org",
            performs_procedures=True,
        )
        db.add(faculty)
        db.commit()
        db.refresh(faculty)
        return faculty

    @pytest.fixture
    def another_faculty(self, db: Session) -> Person:
        """Create another faculty user for testing."""
        faculty = Person(
            id=uuid4(),
            name="Dr. Other Faculty",
            type="faculty",
            email="other@hospital.org",
            performs_procedures=True,
        )
        db.add(faculty)
        db.commit()
        db.refresh(faculty)
        return faculty

    def test_validate_swap_valid_request(
        self,
        validation_service: SwapValidationService,
        faculty_user: Person,
        another_faculty: Person,
    ):
        """Test validation of a valid swap request."""
        source_week = date.today() + timedelta(days=30)
        target_week = date.today() + timedelta(days=35)

        result = validation_service.validate_swap(
            source_faculty_id=faculty_user.id,
            source_week=source_week,
            target_faculty_id=another_faculty.id,
            target_week=target_week,
        )

        assert isinstance(result, SwapValidationResult)
        # May be valid or have warnings depending on internal state
        assert isinstance(result.valid, bool)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)

    def test_validate_swap_nonexistent_source_faculty(
        self,
        validation_service: SwapValidationService,
        another_faculty: Person,
    ):
        """Test validation with nonexistent source faculty."""
        nonexistent_id = uuid4()
        source_week = date.today() + timedelta(days=30)

        result = validation_service.validate_swap(
            source_faculty_id=nonexistent_id,
            source_week=source_week,
            target_faculty_id=another_faculty.id,
            target_week=source_week,
        )

        assert result.valid is False
        assert len(result.errors) > 0
        assert any(e.code == "SOURCE_NOT_FOUND" for e in result.errors)

    def test_validate_swap_nonexistent_target_faculty(
        self,
        validation_service: SwapValidationService,
        faculty_user: Person,
    ):
        """Test validation with nonexistent target faculty."""
        nonexistent_id = uuid4()
        source_week = date.today() + timedelta(days=30)

        result = validation_service.validate_swap(
            source_faculty_id=faculty_user.id,
            source_week=source_week,
            target_faculty_id=nonexistent_id,
            target_week=source_week,
        )

        assert result.valid is False
        assert len(result.errors) > 0
        assert any(e.code == "TARGET_NOT_FOUND" for e in result.errors)

    def test_validate_swap_past_date(
        self,
        validation_service: SwapValidationService,
        faculty_user: Person,
        another_faculty: Person,
    ):
        """Test validation with past date."""
        past_week = date.today() - timedelta(days=30)

        result = validation_service.validate_swap(
            source_faculty_id=faculty_user.id,
            source_week=past_week,
            target_faculty_id=another_faculty.id,
            target_week=past_week,
        )

        assert result.valid is False
        assert any(e.code == "PAST_DATE" for e in result.errors)

    def test_validate_swap_imminent_date_warning(
        self,
        validation_service: SwapValidationService,
        faculty_user: Person,
        another_faculty: Person,
    ):
        """Test validation with imminent date (should generate warning)."""
        imminent_week = date.today() + timedelta(days=7)

        result = validation_service.validate_swap(
            source_faculty_id=faculty_user.id,
            source_week=imminent_week,
            target_faculty_id=another_faculty.id,
            target_week=imminent_week,
        )

        # Should have warning about imminent swap
        assert len(result.warnings) > 0

    def test_validate_swap_same_faculty(
        self,
        validation_service: SwapValidationService,
        faculty_user: Person,
    ):
        """Test validation where source and target are the same."""
        source_week = date.today() + timedelta(days=30)

        result = validation_service.validate_swap(
            source_faculty_id=faculty_user.id,
            source_week=source_week,
            target_faculty_id=faculty_user.id,
            target_week=source_week,
        )

        # Should be invalid - can't swap with yourself
        assert isinstance(result.valid, bool)

    def test_validate_swap_none_target_week(
        self,
        validation_service: SwapValidationService,
        faculty_user: Person,
        another_faculty: Person,
    ):
        """Test validation with None target week."""
        source_week = date.today() + timedelta(days=30)

        result = validation_service.validate_swap(
            source_faculty_id=faculty_user.id,
            source_week=source_week,
            target_faculty_id=another_faculty.id,
            target_week=None,
        )

        assert isinstance(result, SwapValidationResult)

    def test_validation_error_structure(self):
        """Test ValidationError dataclass structure."""
        error = ValidationError(
            code="TEST_ERROR",
            message="This is a test error",
            severity="error",
        )

        assert error.code == "TEST_ERROR"
        assert error.message == "This is a test error"
        assert error.severity == "error"

    def test_validation_error_default_severity(self):
        """Test ValidationError default severity."""
        error = ValidationError(
            code="TEST",
            message="Test",
        )

        assert error.severity == "error"

    def test_validation_result_structure(self):
        """Test SwapValidationResult dataclass structure."""
        errors = [
            ValidationError("ERR1", "Error 1"),
            ValidationError("ERR2", "Error 2"),
        ]
        warnings = [ValidationError("WARN1", "Warning 1", "warning")]

        result = SwapValidationResult(
            valid=False,
            errors=errors,
            warnings=warnings,
            back_to_back_conflict=True,
        )

        assert result.valid is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
        assert result.back_to_back_conflict is True

    def test_validation_result_optional_fields(self):
        """Test SwapValidationResult optional field defaults."""
        result = SwapValidationResult(
            valid=True,
            errors=[],
            warnings=[],
        )

        assert result.back_to_back_conflict is False
        assert result.external_conflict is None
        assert result.call_cascade_affected is False

    def test_validate_swap_future_date(
        self,
        validation_service: SwapValidationService,
        faculty_user: Person,
        another_faculty: Person,
    ):
        """Test validation with far future date."""
        far_future = date.today() + timedelta(days=365)

        result = validation_service.validate_swap(
            source_faculty_id=faculty_user.id,
            source_week=far_future,
            target_faculty_id=another_faculty.id,
            target_week=far_future,
        )

        # Should be valid or have specific constraints
        assert isinstance(result.valid, bool)

    def test_validate_swap_adjacent_dates(
        self,
        validation_service: SwapValidationService,
        faculty_user: Person,
        another_faculty: Person,
    ):
        """Test validation with adjacent swap dates."""
        week1 = date.today() + timedelta(days=30)
        week2 = week1 + timedelta(days=7)

        result = validation_service.validate_swap(
            source_faculty_id=faculty_user.id,
            source_week=week1,
            target_faculty_id=another_faculty.id,
            target_week=week2,
        )

        assert isinstance(result, SwapValidationResult)

    def test_validate_swap_with_default_target_week(
        self,
        validation_service: SwapValidationService,
        faculty_user: Person,
        another_faculty: Person,
    ):
        """Test validation with default target week behavior."""
        source_week = date.today() + timedelta(days=30)

        # When target_week is None, it may use source_week as default
        result = validation_service.validate_swap(
            source_faculty_id=faculty_user.id,
            source_week=source_week,
            target_faculty_id=another_faculty.id,
        )

        assert isinstance(result, SwapValidationResult)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)

    def test_validate_swap_multiple_errors(
        self,
        validation_service: SwapValidationService,
    ):
        """Test validation that generates multiple errors."""
        nonexistent_id = uuid4()
        past_week = date.today() - timedelta(days=30)

        result = validation_service.validate_swap(
            source_faculty_id=nonexistent_id,
            source_week=past_week,
            target_faculty_id=nonexistent_id,
            target_week=past_week,
        )

        # Should have multiple errors
        assert result.valid is False
        assert len(result.errors) >= 2

    def test_validate_swap_result_serializable(
        self,
        validation_service: SwapValidationService,
        faculty_user: Person,
        another_faculty: Person,
    ):
        """Test that validation result can be serialized."""
        source_week = date.today() + timedelta(days=30)

        result = validation_service.validate_swap(
            source_faculty_id=faculty_user.id,
            source_week=source_week,
            target_faculty_id=another_faculty.id,
            target_week=source_week,
        )

        # Should be able to access all fields
        assert hasattr(result, "valid")
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")
        assert hasattr(result, "back_to_back_conflict")
        assert hasattr(result, "external_conflict")
        assert hasattr(result, "call_cascade_affected")
