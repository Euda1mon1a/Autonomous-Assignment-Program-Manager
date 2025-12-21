"""Tests for date validation in schemas."""
import pytest
from datetime import date
from pydantic import ValidationError

from app.schemas.block import BlockCreate
from app.schemas.schedule import ScheduleRequest, EmergencyRequest
from app.schemas.leave import LeaveCreateRequest
from app.schemas.absence import AbsenceCreate
from app.schemas.certification import PersonCertificationCreate
from app.schemas.procedure_credential import CredentialCreate
from app.schemas.swap import SwapExecuteRequest, SwapTypeSchema
from app.schemas.academic_blocks import AcademicBlock


class TestBlockDateValidation:
    """Test date validation for BlockCreate schema."""

    def test_valid_date(self):
        """Test that valid dates are accepted."""
        block = BlockCreate(
            date=date(2024, 7, 1),
            time_of_day="AM",
            block_number=1
        )
        assert block.date == date(2024, 7, 1)

    def test_date_too_early(self):
        """Test that dates before 2020 are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BlockCreate(
                date=date(1900, 1, 1),
                time_of_day="AM",
                block_number=1
            )
        assert "must be on or after" in str(exc_info.value)

    def test_date_too_late(self):
        """Test that dates after 2050 are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BlockCreate(
                date=date(2099, 12, 31),
                time_of_day="AM",
                block_number=1
            )
        assert "must be on or before" in str(exc_info.value)


class TestScheduleRequestDateValidation:
    """Test date validation for ScheduleRequest schema."""

    def test_valid_date_range(self):
        """Test that valid date ranges are accepted."""
        request = ScheduleRequest(
            start_date=date(2024, 7, 1),
            end_date=date(2024, 7, 31)
        )
        assert request.start_date == date(2024, 7, 1)
        assert request.end_date == date(2024, 7, 31)

    def test_start_date_too_early(self):
        """Test that start dates before 2020 are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ScheduleRequest(
                start_date=date(1900, 1, 1),
                end_date=date(2024, 7, 31)
            )
        assert "must be on or after" in str(exc_info.value)

    def test_end_date_too_late(self):
        """Test that end dates after 2050 are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ScheduleRequest(
                start_date=date(2024, 7, 1),
                end_date=date(2099, 12, 31)
            )
        assert "must be on or before" in str(exc_info.value)

    def test_start_after_end(self):
        """Test that start_date > end_date is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ScheduleRequest(
                start_date=date(2024, 8, 1),
                end_date=date(2024, 7, 1)
            )
        assert "must be before or equal to" in str(exc_info.value)


class TestLeaveCreateRequestDateValidation:
    """Test date validation for LeaveCreateRequest schema."""

    def test_valid_leave_dates(self):
        """Test that valid leave dates are accepted."""
        from uuid import uuid4
        request = LeaveCreateRequest(
            faculty_id=uuid4(),
            start_date=date(2024, 7, 1),
            end_date=date(2024, 7, 10),
            leave_type="vacation"
        )
        assert request.start_date == date(2024, 7, 1)

    def test_leave_date_too_early(self):
        """Test that leave dates before 2020 are rejected."""
        from uuid import uuid4
        with pytest.raises(ValidationError) as exc_info:
            LeaveCreateRequest(
                faculty_id=uuid4(),
                start_date=date(1900, 1, 1),
                end_date=date(2024, 7, 10),
                leave_type="vacation"
            )
        assert "must be on or after" in str(exc_info.value)


class TestAbsenceCreateDateValidation:
    """Test date validation for AbsenceCreate schema."""

    def test_valid_absence_dates(self):
        """Test that valid absence dates are accepted."""
        from uuid import uuid4
        absence = AbsenceCreate(
            person_id=uuid4(),
            start_date=date(2024, 7, 1),
            end_date=date(2024, 7, 10),
            absence_type="vacation"
        )
        assert absence.start_date == date(2024, 7, 1)

    def test_absence_date_too_late(self):
        """Test that absence dates after 2050 are rejected."""
        from uuid import uuid4
        with pytest.raises(ValidationError) as exc_info:
            AbsenceCreate(
                person_id=uuid4(),
                start_date=date(2024, 7, 1),
                end_date=date(2099, 12, 31),
                absence_type="vacation"
            )
        assert "must be on or before" in str(exc_info.value)


class TestCertificationDateValidation:
    """Test date validation for PersonCertificationCreate schema."""

    def test_valid_certification_dates(self):
        """Test that valid certification dates are accepted."""
        from uuid import uuid4
        cert = PersonCertificationCreate(
            person_id=uuid4(),
            certification_type_id=uuid4(),
            issued_date=date(2024, 1, 1),
            expiration_date=date(2026, 1, 1)
        )
        assert cert.issued_date == date(2024, 1, 1)
        assert cert.expiration_date == date(2026, 1, 1)

    def test_expiration_before_issue(self):
        """Test that expiration_date before issued_date is rejected."""
        from uuid import uuid4
        with pytest.raises(ValidationError) as exc_info:
            PersonCertificationCreate(
                person_id=uuid4(),
                certification_type_id=uuid4(),
                issued_date=date(2024, 1, 1),
                expiration_date=date(2023, 1, 1)
            )
        assert "must be after" in str(exc_info.value)

    def test_expiration_same_as_issue(self):
        """Test that expiration_date equal to issued_date is rejected."""
        from uuid import uuid4
        with pytest.raises(ValidationError) as exc_info:
            PersonCertificationCreate(
                person_id=uuid4(),
                certification_type_id=uuid4(),
                issued_date=date(2024, 1, 1),
                expiration_date=date(2024, 1, 1)
            )
        assert "must be after" in str(exc_info.value)


class TestCredentialDateValidation:
    """Test date validation for CredentialCreate schema."""

    def test_valid_credential_dates(self):
        """Test that valid credential dates are accepted."""
        from uuid import uuid4
        cred = CredentialCreate(
            person_id=uuid4(),
            procedure_id=uuid4(),
            issued_date=date(2024, 1, 1),
            expiration_date=date(2026, 1, 1)
        )
        assert cred.issued_date == date(2024, 1, 1)

    def test_credential_expiration_before_issue(self):
        """Test that expiration before issue is rejected."""
        from uuid import uuid4
        with pytest.raises(ValidationError) as exc_info:
            CredentialCreate(
                person_id=uuid4(),
                procedure_id=uuid4(),
                issued_date=date(2024, 1, 1),
                expiration_date=date(2023, 1, 1)
            )
        assert "must be after" in str(exc_info.value)


class TestSwapExecuteRequestDateValidation:
    """Test date validation for SwapExecuteRequest schema."""

    def test_valid_swap_dates(self):
        """Test that valid swap dates are accepted."""
        from uuid import uuid4
        swap = SwapExecuteRequest(
            source_faculty_id=uuid4(),
            source_week=date(2024, 7, 1),
            target_faculty_id=uuid4(),
            target_week=date(2024, 7, 8),
            swap_type=SwapTypeSchema.ONE_TO_ONE
        )
        assert swap.source_week == date(2024, 7, 1)

    def test_swap_date_too_early(self):
        """Test that swap dates before 2020 are rejected."""
        from uuid import uuid4
        with pytest.raises(ValidationError) as exc_info:
            SwapExecuteRequest(
                source_faculty_id=uuid4(),
                source_week=date(1900, 1, 1),
                target_faculty_id=uuid4(),
                target_week=date(2024, 7, 8),
                swap_type=SwapTypeSchema.ONE_TO_ONE
            )
        assert "must be on or after" in str(exc_info.value)


class TestAcademicBlockDateValidation:
    """Test date validation for AcademicBlock schema."""

    def test_valid_academic_block_dates(self):
        """Test that valid academic block dates are accepted."""
        block = AcademicBlock(
            block_number=1,
            start_date=date(2024, 7, 1),
            end_date=date(2024, 7, 28),
            name="Block 1"
        )
        assert block.start_date == date(2024, 7, 1)

    def test_academic_block_start_after_end(self):
        """Test that start_date > end_date is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            AcademicBlock(
                block_number=1,
                start_date=date(2024, 7, 28),
                end_date=date(2024, 7, 1),
                name="Block 1"
            )
        assert "must be before or equal to" in str(exc_info.value)

    def test_academic_block_date_too_late(self):
        """Test that dates after 2050 are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            AcademicBlock(
                block_number=1,
                start_date=date(2099, 1, 1),
                end_date=date(2099, 1, 28),
                name="Block 1"
            )
        assert "must be on or before" in str(exc_info.value)
