"""
Tests for Freeze Horizon enforcement.

Tests the FreezeHorizonService and its integration with AssignmentService.
"""

from datetime import date, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.settings import (
    ApplicationSettings,
    FreezeScope,
    OverrideReasonCode,
)
from app.services.freeze_horizon_service import (
    FreezeCheckResult,
    FreezeHorizonService,
    FreezeHorizonViolation,
    FreezeOverrideRequest,
)


class TestFreezeCheckResult:
    """Test FreezeCheckResult data structure."""

    def test_to_dict(self):
        """Test serialization to dictionary."""
        result = FreezeCheckResult(
            is_frozen=True,
            assignment_date=date(2025, 12, 20),
            days_until_assignment=2,
            freeze_horizon_days=7,
            freeze_scope=FreezeScope.NON_EMERGENCY_ONLY,
            requires_override=True,
            can_use_emergency_bypass=True,
            message="Test message",
        )

        d = result.to_dict()
        assert d["is_frozen"] is True
        assert d["assignment_date"] == "2025-12-20"
        assert d["days_until_assignment"] == 2
        assert d["freeze_horizon_days"] == 7
        assert d["freeze_scope"] == "non_emergency_only"
        assert d["requires_override"] is True
        assert d["can_use_emergency_bypass"] is True
        assert d["message"] == "Test message"


class TestFreezeHorizonService:
    """Test FreezeHorizonService core functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        return db

    @pytest.fixture
    def mock_settings(self):
        """Create mock ApplicationSettings."""
        settings = MagicMock(spec=ApplicationSettings)
        settings.freeze_horizon_days = 7
        settings.freeze_scope = FreezeScope.NON_EMERGENCY_ONLY.value
        return settings

    @pytest.fixture
    def service(self, mock_db, mock_settings):
        """Create FreezeHorizonService with mocked dependencies."""
        mock_db.query.return_value.first.return_value = mock_settings
        return FreezeHorizonService(mock_db)

    # =========================================================================
    # Test check_freeze_status
    # =========================================================================

    def test_check_freeze_status_not_frozen(self, service):
        """Test that assignment outside freeze horizon is not frozen."""
        # Assignment 14 days out (beyond 7-day horizon)
        future_date = date.today() + timedelta(days=14)
        result = service.check_freeze_status(future_date)

        assert result.is_frozen is False
        assert result.requires_override is False
        assert result.days_until_assignment == 14

    def test_check_freeze_status_frozen(self, service):
        """Test that assignment within freeze horizon is frozen."""
        # Assignment 3 days out (within 7-day horizon)
        future_date = date.today() + timedelta(days=3)
        result = service.check_freeze_status(future_date)

        assert result.is_frozen is True
        assert result.requires_override is True
        assert result.days_until_assignment == 3
        assert result.can_use_emergency_bypass is True  # NON_EMERGENCY_ONLY scope

    def test_check_freeze_status_today(self, service):
        """Test that assignment today is frozen."""
        result = service.check_freeze_status(date.today())

        assert result.is_frozen is True
        assert result.days_until_assignment == 0
        assert "TODAY" in result.message

    def test_check_freeze_status_past(self, service):
        """Test that past assignment is frozen."""
        past_date = date.today() - timedelta(days=2)
        result = service.check_freeze_status(past_date)

        assert result.is_frozen is True
        assert result.days_until_assignment == -2
        assert "passed" in result.message.lower()

    def test_check_freeze_status_disabled_by_scope(self, mock_db, mock_settings):
        """Test that freeze is disabled when scope is NONE."""
        mock_settings.freeze_scope = FreezeScope.NONE.value
        mock_db.query.return_value.first.return_value = mock_settings
        service = FreezeHorizonService(mock_db)

        future_date = date.today() + timedelta(days=3)
        result = service.check_freeze_status(future_date)

        assert result.is_frozen is False
        assert "disabled" in result.message.lower()

    def test_check_freeze_status_disabled_by_zero_days(self, mock_db, mock_settings):
        """Test that freeze is disabled when horizon is 0 days."""
        mock_settings.freeze_horizon_days = 0
        mock_db.query.return_value.first.return_value = mock_settings
        service = FreezeHorizonService(mock_db)

        future_date = date.today() + timedelta(days=1)
        result = service.check_freeze_status(future_date)

        assert result.is_frozen is False

    # =========================================================================
    # Test validate_override
    # =========================================================================

    def test_validate_override_emergency_accepted(self, service):
        """Test that emergency overrides are accepted with NON_EMERGENCY_ONLY scope."""
        freeze_result = FreezeCheckResult(
            is_frozen=True,
            assignment_date=date.today() + timedelta(days=3),
            days_until_assignment=3,
            freeze_horizon_days=7,
            freeze_scope=FreezeScope.NON_EMERGENCY_ONLY,
            requires_override=True,
            can_use_emergency_bypass=True,
            message="Frozen",
        )

        override = FreezeOverrideRequest(
            reason_code=OverrideReasonCode.SICK_CALL,
            reason_text="Dr. Smith called in sick",
            initiated_by="user123",
            initiating_module="manual",
        )

        is_valid, message = service.validate_override(freeze_result, override)
        assert is_valid is True
        assert "accepted" in message.lower()

    def test_validate_override_non_emergency_rejected(self, service):
        """Test that non-emergency overrides are rejected with NON_EMERGENCY_ONLY scope."""
        freeze_result = FreezeCheckResult(
            is_frozen=True,
            assignment_date=date.today() + timedelta(days=3),
            days_until_assignment=3,
            freeze_horizon_days=7,
            freeze_scope=FreezeScope.NON_EMERGENCY_ONLY,
            requires_override=True,
            can_use_emergency_bypass=True,
            message="Frozen",
        )

        override = FreezeOverrideRequest(
            reason_code=OverrideReasonCode.OTHER,  # Not classified as emergency
            reason_text="Just want to change it",
            initiated_by="user123",
            initiating_module="manual",
        )

        is_valid, message = service.validate_override(freeze_result, override)
        assert is_valid is False
        assert "not classified as emergency" in message.lower()

    def test_validate_override_all_changes_requires_text(self, service):
        """Test that ALL_CHANGES_REQUIRE_OVERRIDE needs sufficient reason text."""
        freeze_result = FreezeCheckResult(
            is_frozen=True,
            assignment_date=date.today() + timedelta(days=3),
            days_until_assignment=3,
            freeze_horizon_days=7,
            freeze_scope=FreezeScope.ALL_CHANGES_REQUIRE_OVERRIDE,
            requires_override=True,
            can_use_emergency_bypass=False,
            message="Frozen",
        )

        # Short reason text should be rejected
        override = FreezeOverrideRequest(
            reason_code=OverrideReasonCode.OTHER,
            reason_text="short",  # Less than 10 characters
            initiated_by="user123",
            initiating_module="manual",
        )

        is_valid, message = service.validate_override(freeze_result, override)
        assert is_valid is False

        # Long reason text should be accepted
        override.reason_text = "This is a sufficiently long reason text"
        is_valid, message = service.validate_override(freeze_result, override)
        assert is_valid is True

    # =========================================================================
    # Test enforce_freeze_or_override
    # =========================================================================

    def test_enforce_not_frozen_passes(self, service):
        """Test that non-frozen assignments pass without override."""
        future_date = date.today() + timedelta(days=14)
        result = service.enforce_freeze_or_override(block_date=future_date)
        assert result.is_frozen is False

    def test_enforce_frozen_without_override_raises(self, service):
        """Test that frozen assignments without override raise exception."""
        future_date = date.today() + timedelta(days=3)

        with pytest.raises(FreezeHorizonViolation) as exc_info:
            service.enforce_freeze_or_override(block_date=future_date)

        assert exc_info.value.check_result.is_frozen is True

    def test_enforce_frozen_with_valid_override_passes(self, service):
        """Test that frozen assignments with valid override pass."""
        future_date = date.today() + timedelta(days=3)
        override = FreezeOverrideRequest(
            reason_code=OverrideReasonCode.SICK_CALL,
            reason_text="Emergency sick call coverage needed",
            initiated_by="user123",
            initiating_module="resiliency",
        )

        result = service.enforce_freeze_or_override(
            block_date=future_date,
            override_request=override,
            assignment_id=uuid4(),
            block_id=uuid4(),
        )

        assert result.is_frozen is True  # Still frozen, but override accepted
        assert "overridden" in result.message.lower()

    def test_enforce_frozen_with_invalid_override_raises(self, service):
        """Test that frozen assignments with invalid override raise exception."""
        future_date = date.today() + timedelta(days=3)
        override = FreezeOverrideRequest(
            reason_code=OverrideReasonCode.OTHER,  # Not emergency
            reason_text="Non-emergency reason",
            initiated_by="user123",
            initiating_module="manual",
        )

        with pytest.raises(FreezeHorizonViolation):
            service.enforce_freeze_or_override(
                block_date=future_date,
                override_request=override,
            )

    # =========================================================================
    # Test audit records
    # =========================================================================

    def test_audit_record_created_on_override(self, service):
        """Test that audit record is created when freeze is overridden."""
        future_date = date.today() + timedelta(days=3)
        assignment_id = uuid4()
        block_id = uuid4()

        override = FreezeOverrideRequest(
            reason_code=OverrideReasonCode.COVERAGE_GAP,
            reason_text="Critical coverage gap discovered",
            initiated_by="scheduler_system",
            initiating_module="resiliency",
        )

        service.enforce_freeze_or_override(
            block_date=future_date,
            override_request=override,
            assignment_id=assignment_id,
            block_id=block_id,
        )

        # Check audit records
        records = service.get_override_audit_records()
        assert len(records) >= 1

        record = records[0]
        assert record.assignment_id == assignment_id
        assert record.block_id == block_id
        assert record.reason_code == OverrideReasonCode.COVERAGE_GAP
        assert record.initiated_by == "scheduler_system"
        assert record.initiating_module == "resiliency"
        assert record.is_emergency is True  # COVERAGE_GAP is emergency

    def test_get_freeze_statistics(self, service):
        """Test freeze statistics calculation."""
        # Create some override records
        future_date = date.today() + timedelta(days=3)

        for reason_code in [
            OverrideReasonCode.SICK_CALL,
            OverrideReasonCode.SICK_CALL,
            OverrideReasonCode.COVERAGE_GAP,
        ]:
            override = FreezeOverrideRequest(
                reason_code=reason_code,
                reason_text=f"Test override for {reason_code.value}",
                initiated_by="test_user",
                initiating_module="test_module",
            )
            service.enforce_freeze_or_override(
                block_date=future_date,
                override_request=override,
                assignment_id=uuid4(),
                block_id=uuid4(),
            )

        stats = service.get_freeze_statistics()
        assert stats["total_overrides"] >= 3
        assert stats["by_reason_code"].get("sick_call", 0) >= 2
        assert stats["by_reason_code"].get("coverage_gap", 0) >= 1
        assert stats["emergency_count"] >= 3


class TestEmergencyReasonCodes:
    """Test emergency reason code classification."""

    def test_emergency_codes_are_correct(self):
        """Verify emergency codes match expected set."""
        expected_emergency = {
            OverrideReasonCode.SICK_CALL,
            OverrideReasonCode.DEPLOYMENT,
            OverrideReasonCode.SAFETY,
            OverrideReasonCode.COVERAGE_GAP,
            OverrideReasonCode.EMERGENCY_LEAVE,
            OverrideReasonCode.CRISIS_MODE,
        }

        assert expected_emergency == FreezeHorizonService.EMERGENCY_REASON_CODES

    def test_non_emergency_codes(self):
        """Verify non-emergency codes are not in emergency set."""
        non_emergency = {
            OverrideReasonCode.ADMINISTRATIVE,
            OverrideReasonCode.OTHER,
        }

        for code in non_emergency:
            assert code not in FreezeHorizonService.EMERGENCY_REASON_CODES


class TestFreezeScopeEnum:
    """Test FreezeScope enum values."""

    def test_freeze_scope_values(self):
        """Test FreezeScope enum has expected values."""
        assert FreezeScope.NONE.value == "none"
        assert FreezeScope.NON_EMERGENCY_ONLY.value == "non_emergency_only"
        assert (
            FreezeScope.ALL_CHANGES_REQUIRE_OVERRIDE.value
            == "all_changes_require_override"
        )

    def test_freeze_scope_from_string(self):
        """Test creating FreezeScope from string value."""
        assert FreezeScope("none") == FreezeScope.NONE
        assert FreezeScope("non_emergency_only") == FreezeScope.NON_EMERGENCY_ONLY
        assert (
            FreezeScope("all_changes_require_override")
            == FreezeScope.ALL_CHANGES_REQUIRE_OVERRIDE
        )


class TestOverrideReasonCodeEnum:
    """Test OverrideReasonCode enum values."""

    def test_all_reason_codes_defined(self):
        """Test all expected reason codes are defined."""
        expected_codes = [
            "sick_call",
            "deployment",
            "safety",
            "coverage_gap",
            "emergency_leave",
            "administrative",
            "crisis_mode",
            "other",
        ]

        actual_codes = [code.value for code in OverrideReasonCode]
        assert sorted(actual_codes) == sorted(expected_codes)
