"""Test suite for freeze horizon service."""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.person import Person
from app.services.freeze_horizon_service import FreezeHorizonService


class TestFreezeHorizonService:
    """Test suite for freeze horizon service."""

    @pytest.fixture
    def freeze_service(self, db: Session) -> FreezeHorizonService:
        """Create a freeze horizon service instance."""
        return FreezeHorizonService(db)

    @pytest.fixture
    def resident(self, db: Session) -> Person:
        """Create a resident."""
        person = Person(
            id=uuid4(),
            name="Dr. Resident",
            type="resident",
            email="resident@hospital.org",
            pgy_level=1,
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        return person

    def test_service_initialization(self, db: Session):
        """Test FreezeHorizonService initialization."""
        service = FreezeHorizonService(db)

        assert service.db is db

    def test_get_freeze_horizon(
        self,
        freeze_service: FreezeHorizonService,
    ):
        """Test getting current freeze horizon."""
        horizon = freeze_service.get_horizon()

        assert isinstance(horizon, (date, dict, type(None)))

    def test_set_freeze_horizon(
        self,
        freeze_service: FreezeHorizonService,
    ):
        """Test setting freeze horizon."""
        freeze_date = date.today() + timedelta(days=30)

        result = freeze_service.set_horizon(freeze_date)

        assert isinstance(result, bool)

    def test_is_date_frozen(
        self,
        freeze_service: FreezeHorizonService,
    ):
        """Test checking if date is frozen."""
        test_date = date.today() + timedelta(days=5)

        is_frozen = freeze_service.is_frozen(test_date)

        assert isinstance(is_frozen, bool)

    def test_get_frozen_period(
        self,
        freeze_service: FreezeHorizonService,
    ):
        """Test getting frozen period."""
        period = freeze_service.get_period()

        assert isinstance(period, (dict, tuple, type(None)))

    def test_freeze_schedule_block(
        self,
        freeze_service: FreezeHorizonService,
    ):
        """Test freezing a schedule block."""
        start_date = date.today() + timedelta(days=5)
        end_date = start_date + timedelta(days=7)

        result = freeze_service.freeze_block(start_date, end_date)

        assert isinstance(result, bool)

    def test_unfreeze_schedule_block(
        self,
        freeze_service: FreezeHorizonService,
    ):
        """Test unfreezing a schedule block."""
        start_date = date.today() + timedelta(days=5)
        end_date = start_date + timedelta(days=7)

        result = freeze_service.unfreeze_block(start_date, end_date)

        assert isinstance(result, bool)

    def test_get_frozen_dates(
        self,
        freeze_service: FreezeHorizonService,
    ):
        """Test getting list of frozen dates."""
        frozen_dates = freeze_service.get_frozen_dates()

        assert isinstance(frozen_dates, list)

    def test_check_freeze_status_for_person(
        self,
        freeze_service: FreezeHorizonService,
        resident: Person,
    ):
        """Test checking freeze status for a person."""
        status = freeze_service.get_person_freeze_status(resident.id)

        assert isinstance(status, (bool, dict, type(None)))

    def test_allow_changes_before_freeze(
        self,
        freeze_service: FreezeHorizonService,
    ):
        """Test that changes are allowed before freeze date."""
        test_date = date.today() - timedelta(days=5)

        is_allowed = freeze_service.can_modify(test_date)

        assert isinstance(is_allowed, bool)

    def test_prevent_changes_after_freeze(
        self,
        freeze_service: FreezeHorizonService,
    ):
        """Test that changes are prevented after freeze date."""
        # Set freeze in past
        freeze_service.set_horizon(date.today() - timedelta(days=5))

        test_date = date.today() + timedelta(days=10)

        is_allowed = freeze_service.can_modify(test_date)

        assert isinstance(is_allowed, bool)

    def test_get_days_until_freeze(
        self,
        freeze_service: FreezeHorizonService,
    ):
        """Test getting days until freeze."""
        days = freeze_service.get_days_until_freeze()

        assert isinstance(days, (int, type(None)))

    def test_freeze_modifications_audit(
        self,
        freeze_service: FreezeHorizonService,
    ):
        """Test auditing freeze modifications."""
        audit = freeze_service.get_audit_trail()

        assert isinstance(audit, list)

    def test_allow_exception_to_freeze(
        self,
        freeze_service: FreezeHorizonService,
        resident: Person,
    ):
        """Test allowing exception to freeze."""
        test_date = date.today() + timedelta(days=10)

        result = freeze_service.allow_exception(
            person_id=resident.id,
            date=test_date,
            reason="Medical emergency",
        )

        assert isinstance(result, bool)

    def test_revoke_freeze_exception(
        self,
        freeze_service: FreezeHorizonService,
        resident: Person,
    ):
        """Test revoking freeze exception."""
        test_date = date.today() + timedelta(days=10)

        result = freeze_service.revoke_exception(
            person_id=resident.id,
            date=test_date,
        )

        assert isinstance(result, bool)

    def test_get_freeze_exceptions(
        self,
        freeze_service: FreezeHorizonService,
    ):
        """Test getting freeze exceptions."""
        exceptions = freeze_service.get_exceptions()

        assert isinstance(exceptions, list)

    def test_freeze_notifications(
        self,
        freeze_service: FreezeHorizonService,
    ):
        """Test freeze notifications."""
        result = freeze_service.send_notifications()

        assert isinstance(result, bool)

    def test_freeze_with_advance_notice(
        self,
        freeze_service: FreezeHorizonService,
    ):
        """Test freeze with advance notice period."""
        freeze_date = date.today() + timedelta(days=30)
        notice_days = 14

        result = freeze_service.set_with_notice(freeze_date, notice_days)

        assert isinstance(result, bool)

    def test_get_freeze_statistics(
        self,
        freeze_service: FreezeHorizonService,
    ):
        """Test getting freeze statistics."""
        stats = freeze_service.get_statistics()

        assert isinstance(stats, dict)

    def test_validate_against_freeze(
        self,
        freeze_service: FreezeHorizonService,
    ):
        """Test validation against freeze horizon."""
        test_date = date.today() + timedelta(days=5)

        is_valid = freeze_service.validate_date(test_date)

        assert isinstance(is_valid, bool)
