"""Tests for personal dashboard schemas (defaults, nested models)."""

from datetime import date, datetime
from uuid import uuid4

from app.schemas.me_dashboard import (
    DashboardUserInfo,
    DashboardScheduleItem,
    DashboardSwapItem,
    DashboardAbsenceItem,
    DashboardSummary,
    MeDashboardResponse,
)


class TestDashboardUserInfo:
    def test_valid_minimal(self):
        r = DashboardUserInfo(id=uuid4(), name="Dr. Smith", role="resident")
        assert r.email is None
        assert r.pgy_level is None

    def test_full(self):
        r = DashboardUserInfo(
            id=uuid4(),
            name="Dr. Jones",
            role="faculty",
            email="jones@example.com",
            pgy_level=3,
        )
        assert r.email == "jones@example.com"
        assert r.pgy_level == 3


class TestDashboardScheduleItem:
    def test_valid_minimal(self):
        r = DashboardScheduleItem(
            date=date(2026, 3, 1),
            time_of_day="AM",
            activity="FM Clinic",
        )
        assert r.location is None
        assert r.can_trade is True
        assert r.role is None
        assert r.assignment_id is None

    def test_full(self):
        r = DashboardScheduleItem(
            date=date(2026, 3, 1),
            time_of_day="PM",
            activity="ICU",
            location="Building A",
            can_trade=False,
            role="primary",
            assignment_id=uuid4(),
        )
        assert r.can_trade is False
        assert r.role == "primary"


class TestDashboardSwapItem:
    def test_valid(self):
        r = DashboardSwapItem(
            swap_id=uuid4(),
            swap_type="one_to_one",
            status="pending",
            source_week=date(2026, 3, 1),
            target_week=date(2026, 3, 8),
            other_party_name="Dr. Brown",
            requested_at=datetime(2026, 2, 20),
        )
        assert r.swap_type == "one_to_one"

    def test_target_week_none(self):
        r = DashboardSwapItem(
            swap_id=uuid4(),
            swap_type="absorb",
            status="approved",
            source_week=date(2026, 3, 1),
            target_week=None,
            other_party_name="Dr. White",
            requested_at=datetime(2026, 2, 20),
        )
        assert r.target_week is None


class TestDashboardAbsenceItem:
    def test_valid(self):
        r = DashboardAbsenceItem(
            absence_id=uuid4(),
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 5),
            absence_type="vacation",
        )
        assert r.notes is None

    def test_with_notes(self):
        r = DashboardAbsenceItem(
            absence_id=uuid4(),
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 5),
            absence_type="conference",
            notes="AAFP conference",
        )
        assert r.notes == "AAFP conference"


class TestDashboardSummary:
    def test_defaults(self):
        r = DashboardSummary()
        assert r.next_assignment is None
        assert r.workload_next_4_weeks == 0
        assert r.pending_swap_count == 0
        assert r.upcoming_absences_count == 0

    def test_full(self):
        r = DashboardSummary(
            next_assignment=date(2026, 3, 1),
            workload_next_4_weeks=8,
            pending_swap_count=2,
            upcoming_absences_count=1,
        )
        assert r.workload_next_4_weeks == 8


class TestMeDashboardResponse:
    def test_valid_minimal(self):
        user = DashboardUserInfo(id=uuid4(), name="Dr. Smith", role="resident")
        summary = DashboardSummary()
        r = MeDashboardResponse(user=user, summary=summary)
        assert r.upcoming_schedule == []
        assert r.pending_swaps == []
        assert r.absences == []
        assert r.calendar_sync_url is None
