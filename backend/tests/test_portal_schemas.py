"""Tests for portal Pydantic schemas."""
import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4
from pydantic import ValidationError

from app.schemas.portal import (
    SwapRequestStatus,
    FMITWeekInfo,
    MyScheduleResponse,
    SwapRequestSummary,
    MySwapsResponse,
    SwapRequestCreate,
    SwapRequestResponse,
    SwapRespondRequest,
    PreferencesUpdate,
    PreferencesResponse,
    DashboardAlert,
    DashboardStats,
    DashboardResponse,
    MarketplaceEntry,
    MarketplaceResponse,
)


class TestSwapRequestStatus:
    """Tests for SwapRequestStatus enum."""

    def test_status_values(self):
        """Test all status values."""
        assert SwapRequestStatus.PENDING == "pending"
        assert SwapRequestStatus.APPROVED == "approved"
        assert SwapRequestStatus.REJECTED == "rejected"
        assert SwapRequestStatus.EXECUTED == "executed"
        assert SwapRequestStatus.CANCELLED == "cancelled"


class TestFMITWeekInfo:
    """Tests for FMITWeekInfo schema."""

    def test_create_week_info(self):
        """Test creating week info."""
        info = FMITWeekInfo(
            week_start=date.today(),
            week_end=date.today() + timedelta(days=6),
        )
        assert info.is_past is False
        assert info.has_conflict is False
        assert info.can_request_swap is True

    def test_week_with_conflict(self):
        """Test week info with conflict."""
        info = FMITWeekInfo(
            week_start=date.today(),
            week_end=date.today() + timedelta(days=6),
            has_conflict=True,
            conflict_description="TDY conflict",
            can_request_swap=False,
        )
        assert info.has_conflict is True
        assert info.conflict_description == "TDY conflict"


class TestMyScheduleResponse:
    """Tests for MyScheduleResponse schema."""

    def test_create_schedule(self):
        """Test creating schedule response."""
        response = MyScheduleResponse(
            faculty_id=uuid4(),
            faculty_name="Dr. Smith",
            fmit_weeks=[],
            total_weeks_assigned=0,
            target_weeks=6,
            weeks_remaining=6,
        )
        assert response.faculty_name == "Dr. Smith"
        assert response.total_weeks_assigned == 0

    def test_schedule_with_weeks(self):
        """Test schedule with FMIT weeks."""
        weeks = [
            FMITWeekInfo(
                week_start=date.today() + timedelta(days=14),
                week_end=date.today() + timedelta(days=20),
            ),
            FMITWeekInfo(
                week_start=date.today() + timedelta(days=42),
                week_end=date.today() + timedelta(days=48),
            ),
        ]
        response = MyScheduleResponse(
            faculty_id=uuid4(),
            faculty_name="Dr. Smith",
            fmit_weeks=weeks,
            total_weeks_assigned=2,
            target_weeks=6,
            weeks_remaining=4,
        )
        assert len(response.fmit_weeks) == 2


class TestSwapRequestCreate:
    """Tests for SwapRequestCreate schema."""

    def test_create_request(self):
        """Test creating swap request."""
        request = SwapRequestCreate(
            week_to_offload=date.today() + timedelta(days=14),
        )
        assert request.preferred_target_faculty_id is None
        assert request.auto_find_candidates is True

    def test_request_with_target(self):
        """Test request with specific target."""
        target_id = uuid4()
        request = SwapRequestCreate(
            week_to_offload=date.today() + timedelta(days=14),
            preferred_target_faculty_id=target_id,
            reason="Vacation planned",
            auto_find_candidates=False,
        )
        assert request.preferred_target_faculty_id == target_id
        assert request.reason == "Vacation planned"

    def test_reason_max_length(self):
        """Test reason field max length."""
        with pytest.raises(ValidationError):
            SwapRequestCreate(
                week_to_offload=date.today() + timedelta(days=14),
                reason="x" * 501,  # Over 500 char limit
            )


class TestPreferencesUpdate:
    """Tests for PreferencesUpdate schema."""

    def test_partial_update(self):
        """Test partial preference update."""
        update = PreferencesUpdate(
            notify_swap_requests=False,
        )
        assert update.notify_swap_requests is False
        assert update.preferred_weeks is None

    def test_week_preferences(self):
        """Test updating week preferences."""
        update = PreferencesUpdate(
            preferred_weeks=[date.today() + timedelta(days=30)],
            blocked_weeks=[date.today() + timedelta(days=60)],
        )
        assert len(update.preferred_weeks) == 1
        assert len(update.blocked_weeks) == 1

    def test_max_weeks_validation(self):
        """Test max_weeks_per_month validation."""
        update = PreferencesUpdate(
            max_weeks_per_month=3,
        )
        assert update.max_weeks_per_month == 3

        with pytest.raises(ValidationError):
            PreferencesUpdate(max_weeks_per_month=5)  # Over limit


class TestDashboardStats:
    """Tests for DashboardStats schema."""

    def test_create_stats(self):
        """Test creating dashboard stats."""
        stats = DashboardStats(
            weeks_assigned=3,
            weeks_completed=1,
            weeks_remaining=2,
            target_weeks=6,
            pending_swap_requests=1,
            unread_alerts=2,
        )
        assert stats.weeks_assigned == 3
        assert stats.unread_alerts == 2


class TestDashboardAlert:
    """Tests for DashboardAlert schema."""

    def test_create_alert(self):
        """Test creating dashboard alert."""
        alert = DashboardAlert(
            id=uuid4(),
            alert_type="conflict",
            severity="critical",
            message="FMIT conflict with vacation",
            created_at=datetime.utcnow(),
        )
        assert alert.alert_type == "conflict"
        assert alert.action_url is None

    def test_alert_with_action(self):
        """Test alert with action URL."""
        alert = DashboardAlert(
            id=uuid4(),
            alert_type="swap_request",
            severity="info",
            message="New swap request from Dr. Jones",
            created_at=datetime.utcnow(),
            action_url="/portal/my/swaps/123",
        )
        assert alert.action_url is not None


class TestMarketplaceEntry:
    """Tests for MarketplaceEntry schema."""

    def test_create_entry(self):
        """Test creating marketplace entry."""
        entry = MarketplaceEntry(
            request_id=uuid4(),
            requesting_faculty_name="Dr. Smith",
            week_available=date.today() + timedelta(days=21),
            reason="Family commitment",
            posted_at=datetime.utcnow(),
            expires_at=None,
            is_compatible=True,
        )
        assert entry.requesting_faculty_name == "Dr. Smith"
        assert entry.is_compatible is True


class TestMarketplaceResponse:
    """Tests for MarketplaceResponse schema."""

    def test_empty_marketplace(self):
        """Test empty marketplace."""
        response = MarketplaceResponse(
            entries=[],
            total=0,
            my_postings=0,
        )
        assert len(response.entries) == 0

    def test_marketplace_with_entries(self):
        """Test marketplace with entries."""
        entries = [
            MarketplaceEntry(
                request_id=uuid4(),
                requesting_faculty_name="Dr. Smith",
                week_available=date.today() + timedelta(days=21),
                reason=None,
                posted_at=datetime.utcnow(),
                expires_at=None,
                is_compatible=True,
            ),
        ]
        response = MarketplaceResponse(
            entries=entries,
            total=1,
            my_postings=0,
        )
        assert response.total == 1
