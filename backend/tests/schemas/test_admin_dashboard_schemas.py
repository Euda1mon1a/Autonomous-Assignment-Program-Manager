"""Tests for admin dashboard schemas (nested model composition)."""

from datetime import datetime

from app.schemas.admin_dashboard import (
    AdminUserCounts,
    AdminPeopleCounts,
    AdminAbsenceCounts,
    AdminSwapCounts,
    AdminConflictCounts,
    AdminBreakGlassUsage,
    AdminDashboardSummary,
)


class TestAdminUserCounts:
    def test_valid(self):
        r = AdminUserCounts(total=50, active=45)
        assert r.total == 50
        assert r.active == 45


class TestAdminPeopleCounts:
    def test_valid(self):
        r = AdminPeopleCounts(total=30, residents=20, faculty=10)
        assert r.residents == 20
        assert r.faculty == 10


class TestAdminAbsenceCounts:
    def test_valid(self):
        r = AdminAbsenceCounts(active=3, upcoming=5)
        assert r.active == 3
        assert r.upcoming == 5


class TestAdminSwapCounts:
    def test_valid(self):
        r = AdminSwapCounts(
            pending=2,
            approved=5,
            executed=3,
            rejected=1,
            cancelled=0,
            rolled_back=0,
        )
        assert r.pending == 2
        assert r.executed == 3


class TestAdminConflictCounts:
    def test_valid(self):
        r = AdminConflictCounts(new=3, acknowledged=2, resolved=10, ignored=1)
        assert r.new == 3
        assert r.resolved == 10


class TestAdminBreakGlassUsage:
    def test_valid(self):
        r = AdminBreakGlassUsage(
            window_start=datetime(2026, 1, 1),
            window_end=datetime(2026, 1, 31),
            count=2,
        )
        assert r.count == 2
        assert r.last_used_at is None

    def test_with_last_used(self):
        ts = datetime(2026, 1, 15, 10, 30)
        r = AdminBreakGlassUsage(
            window_start=datetime(2026, 1, 1),
            window_end=datetime(2026, 1, 31),
            count=1,
            last_used_at=ts,
        )
        assert r.last_used_at == ts


class TestAdminDashboardSummary:
    def test_valid(self):
        r = AdminDashboardSummary(
            timestamp=datetime.now(),
            users=AdminUserCounts(total=50, active=45),
            people=AdminPeopleCounts(total=30, residents=20, faculty=10),
            absences=AdminAbsenceCounts(active=3, upcoming=5),
            swaps=AdminSwapCounts(
                pending=2,
                approved=5,
                executed=3,
                rejected=1,
                cancelled=0,
                rolled_back=0,
            ),
            conflicts=AdminConflictCounts(
                new=3, acknowledged=2, resolved=10, ignored=1
            ),
        )
        assert r.users.total == 50
        assert r.people.residents == 20
        assert r.swaps.pending == 2
