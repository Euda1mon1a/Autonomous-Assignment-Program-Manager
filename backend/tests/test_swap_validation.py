"""Tests for swap validation service."""
from datetime import date, timedelta
from uuid import uuid4

from app.models.absence import Absence
from app.services.swap_validation import (
    SwapValidationResult,
    SwapValidationService,
    ValidationError,
)


class TestSwapValidationService:
    """Tests for SwapValidationService."""

    def test_init(self, db):
        """Test service initialization."""
        service = SwapValidationService(db)
        assert service.db == db

    def test_validate_swap_faculty_not_found(self, db):
        """Test validation fails when faculty not found."""
        service = SwapValidationService(db)

        result = service.validate_swap(
            source_faculty_id=uuid4(),  # Non-existent
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=uuid4(),  # Non-existent
        )

        assert not result.valid
        assert len(result.errors) >= 1
        error_codes = [e.code for e in result.errors]
        assert "SOURCE_NOT_FOUND" in error_codes or "TARGET_NOT_FOUND" in error_codes

    def test_validate_swap_past_date(self, db, sample_faculty_members):
        """Test validation fails for past dates."""
        service = SwapValidationService(db)
        source = sample_faculty_members[0]
        target = sample_faculty_members[1]

        result = service.validate_swap(
            source_faculty_id=source.id,
            source_week=date.today() - timedelta(days=7),  # Past
            target_faculty_id=target.id,
        )

        assert not result.valid
        error_codes = [e.code for e in result.errors]
        assert "PAST_DATE" in error_codes

    def test_validate_swap_imminent_warning(self, db, sample_faculty_members):
        """Test warning for swaps within 2 weeks."""
        service = SwapValidationService(db)
        source = sample_faculty_members[0]
        target = sample_faculty_members[1]

        result = service.validate_swap(
            source_faculty_id=source.id,
            source_week=date.today() + timedelta(days=7),  # Within 2 weeks
            target_faculty_id=target.id,
        )

        warning_codes = [w.code for w in result.warnings]
        assert "IMMINENT_SWAP" in warning_codes

    def test_validate_swap_external_conflict(self, db, sample_faculty_members):
        """Test detection of external conflicts."""
        service = SwapValidationService(db)
        source = sample_faculty_members[0]
        target = sample_faculty_members[1]

        # Create blocking absence for target
        swap_week = date.today() + timedelta(days=21)
        absence = Absence(
            id=uuid4(),
            person_id=target.id,
            start_date=swap_week,
            end_date=swap_week + timedelta(days=4),
            absence_type="tdy",
            is_blocking=True,
        )
        db.add(absence)
        db.commit()

        result = service.validate_swap(
            source_faculty_id=source.id,
            source_week=swap_week,
            target_faculty_id=target.id,
        )

        assert not result.valid
        assert result.external_conflict == "tdy"
        error_codes = [e.code for e in result.errors]
        assert "EXTERNAL_CONFLICT" in error_codes

    def test_validate_swap_valid(self, db, sample_faculty_members):
        """Test successful validation."""
        service = SwapValidationService(db)
        source = sample_faculty_members[0]
        target = sample_faculty_members[1]

        result = service.validate_swap(
            source_faculty_id=source.id,
            source_week=date.today() + timedelta(days=30),  # Future, not imminent
            target_faculty_id=target.id,
        )

        assert result.valid
        assert len(result.errors) == 0


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_valid_result(self):
        """Test creating a valid result."""
        result = SwapValidationResult(
            valid=True,
            errors=[],
            warnings=[],
        )
        assert result.valid
        assert not result.back_to_back_conflict
        assert result.external_conflict is None

    def test_invalid_result_with_errors(self):
        """Test creating an invalid result with errors."""
        errors = [
            ValidationError("TEST_ERROR", "Test error message"),
            ValidationError("ANOTHER_ERROR", "Another message"),
        ]
        result = SwapValidationResult(
            valid=False,
            errors=errors,
            warnings=[],
            back_to_back_conflict=True,
        )
        assert not result.valid
        assert len(result.errors) == 2
        assert result.back_to_back_conflict


class TestValidationError:
    """Tests for ValidationError dataclass."""

    def test_error_defaults(self):
        """Test error default severity."""
        error = ValidationError("CODE", "Message")
        assert error.code == "CODE"
        assert error.message == "Message"
        assert error.severity == "error"

    def test_warning_severity(self):
        """Test warning severity."""
        warning = ValidationError("CODE", "Message", severity="warning")
        assert warning.severity == "warning"
