"""Tests for faculty self-service portal schemas (enums, defaults, nested)."""

from datetime import date, datetime
from uuid import uuid4

import pytest
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
    def test_values(self):
        assert SwapRequestStatus.PENDING.value == "pending"
        assert SwapRequestStatus.APPROVED.value == "approved"
        assert SwapRequestStatus.REJECTED.value == "rejected"
        assert SwapRequestStatus.EXECUTED.value == "executed"
        assert SwapRequestStatus.CANCELLED.value == "cancelled"

    def test_count(self):
        assert len(SwapRequestStatus) == 5


class TestFMITWeekInfo:
    def test_valid_defaults(self):
        r = FMITWeekInfo(week_start=date(2026, 3, 2), week_end=date(2026, 3, 8))
        assert r.is_past is False
        assert r.has_conflict is False
        assert r.conflict_description is None
        assert r.can_request_swap is True
        assert r.pending_swap_request is False

    def test_with_conflict(self):
        r = FMITWeekInfo(
            week_start=date(2026, 3, 2),
            week_end=date(2026, 3, 8),
            has_conflict=True,
            conflict_description="Leave overlap",
            can_request_swap=False,
        )
        assert r.has_conflict is True
        assert r.can_request_swap is False


class TestMyScheduleResponse:
    def test_valid(self):
        r = MyScheduleResponse(
            faculty_id=uuid4(),
            faculty_name="Dr. Smith",
            fmit_weeks=[],
            total_weeks_assigned=10,
            target_weeks=12,
            weeks_remaining=2,
        )
        assert r.weeks_remaining == 2


class TestSwapRequestSummary:
    def test_valid(self):
        r = SwapRequestSummary(
            id=uuid4(),
            other_faculty_name="Dr. Jones",
            week_to_give=date(2026, 3, 2),
            week_to_receive=date(2026, 4, 6),
            status=SwapRequestStatus.PENDING,
            created_at=datetime(2026, 3, 1),
            is_incoming=True,
        )
        assert r.is_incoming is True

    def test_absorb_no_receive(self):
        r = SwapRequestSummary(
            id=uuid4(),
            other_faculty_name="Dr. Jones",
            week_to_give=date(2026, 3, 2),
            week_to_receive=None,
            status=SwapRequestStatus.PENDING,
            created_at=datetime(2026, 3, 1),
            is_incoming=False,
        )
        assert r.week_to_receive is None


class TestMySwapsResponse:
    def test_valid(self):
        r = MySwapsResponse(incoming_requests=[], outgoing_requests=[], recent_swaps=[])
        assert r.incoming_requests == []


class TestSwapRequestCreate:
    def test_valid_minimal(self):
        r = SwapRequestCreate(week_to_offload=date(2026, 3, 2))
        assert r.preferred_target_faculty_id is None
        assert r.reason is None
        assert r.auto_find_candidates is True

    # --- reason max_length=500 ---

    def test_reason_too_long(self):
        with pytest.raises(ValidationError):
            SwapRequestCreate(week_to_offload=date(2026, 3, 2), reason="x" * 501)


class TestSwapRequestResponse:
    def test_valid(self):
        r = SwapRequestResponse(success=True, request_id=uuid4(), message="Created")
        assert r.candidates_notified == 0


class TestSwapRespondRequest:
    def test_valid(self):
        r = SwapRespondRequest(accept=True)
        assert r.counter_offer_week is None
        assert r.notes is None

    # --- notes max_length=500 ---

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            SwapRespondRequest(accept=False, notes="x" * 501)


class TestPreferencesUpdate:
    def test_all_none(self):
        r = PreferencesUpdate()
        assert r.preferred_weeks is None
        assert r.blocked_weeks is None
        assert r.max_weeks_per_month is None
        assert r.max_consecutive_weeks is None
        assert r.min_gap_between_weeks is None
        assert r.notify_swap_requests is None
        assert r.notes is None

    # --- max_weeks_per_month ge=1, le=4 ---

    def test_max_weeks_per_month_below_min(self):
        with pytest.raises(ValidationError):
            PreferencesUpdate(max_weeks_per_month=0)

    def test_max_weeks_per_month_above_max(self):
        with pytest.raises(ValidationError):
            PreferencesUpdate(max_weeks_per_month=5)

    # --- max_consecutive_weeks ge=1, le=2 ---

    def test_max_consecutive_weeks_below_min(self):
        with pytest.raises(ValidationError):
            PreferencesUpdate(max_consecutive_weeks=0)

    def test_max_consecutive_weeks_above_max(self):
        with pytest.raises(ValidationError):
            PreferencesUpdate(max_consecutive_weeks=3)

    # --- min_gap_between_weeks ge=1, le=4 ---

    def test_min_gap_below_min(self):
        with pytest.raises(ValidationError):
            PreferencesUpdate(min_gap_between_weeks=0)

    def test_min_gap_above_max(self):
        with pytest.raises(ValidationError):
            PreferencesUpdate(min_gap_between_weeks=5)

    # --- notify_reminder_days ge=1, le=14 ---

    def test_notify_reminder_days_below_min(self):
        with pytest.raises(ValidationError):
            PreferencesUpdate(notify_reminder_days=0)

    def test_notify_reminder_days_above_max(self):
        with pytest.raises(ValidationError):
            PreferencesUpdate(notify_reminder_days=15)

    # --- notes max_length=1000 ---

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            PreferencesUpdate(notes="x" * 1001)


class TestPreferencesResponse:
    def test_valid(self):
        r = PreferencesResponse(
            faculty_id=uuid4(),
            preferred_weeks=[],
            blocked_weeks=[],
            max_weeks_per_month=2,
            max_consecutive_weeks=1,
            min_gap_between_weeks=2,
            target_weeks_per_year=12,
            notify_swap_requests=True,
            notify_schedule_changes=True,
            notify_conflict_alerts=True,
            notify_reminder_days=7,
            notes=None,
            updated_at=datetime(2026, 3, 1),
        )
        assert r.target_weeks_per_year == 12


class TestDashboardAlert:
    def test_valid(self):
        r = DashboardAlert(
            id=uuid4(),
            alert_type="conflict",
            severity="warning",
            message="Schedule conflict detected",
            created_at=datetime(2026, 3, 1),
        )
        assert r.action_url is None


class TestDashboardStats:
    def test_valid(self):
        r = DashboardStats(
            weeks_assigned=10,
            weeks_completed=6,
            weeks_remaining=4,
            target_weeks=12,
            pending_swap_requests=2,
            unread_alerts=1,
        )
        assert r.pending_swap_requests == 2


class TestDashboardResponse:
    def test_valid(self):
        stats = DashboardStats(
            weeks_assigned=10,
            weeks_completed=6,
            weeks_remaining=4,
            target_weeks=12,
            pending_swap_requests=0,
            unread_alerts=0,
        )
        r = DashboardResponse(
            faculty_id=uuid4(),
            faculty_name="Dr. Smith",
            stats=stats,
            upcoming_weeks=[],
            recent_alerts=[],
            pending_swap_decisions=[],
        )
        assert r.upcoming_weeks == []


class TestMarketplaceEntry:
    def test_valid(self):
        r = MarketplaceEntry(
            request_id=uuid4(),
            requesting_faculty_name="Dr. Jones",
            week_available=date(2026, 4, 6),
            reason=None,
            posted_at=datetime(2026, 3, 1),
            expires_at=None,
            is_compatible=True,
        )
        assert r.is_compatible is True


class TestMarketplaceResponse:
    def test_valid(self):
        r = MarketplaceResponse(entries=[], total=0, my_postings=0)
        assert r.entries == []
