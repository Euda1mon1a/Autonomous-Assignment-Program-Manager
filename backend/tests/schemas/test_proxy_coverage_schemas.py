"""Tests for proxy coverage schemas (enums, defaults, nested models)."""

from datetime import date
from uuid import uuid4

from app.schemas.proxy_coverage import (
    CoverageType,
    CoverageStatus,
    PersonRef,
    CoverageRelationship,
    PersonCoverageSummary,
    CoverageCountByType,
    TopCoverer,
    CoverageStats,
    ProxyCoverageResponse,
    ProxyCoverageFilter,
)


class TestCoverageType:
    def test_values(self):
        assert CoverageType.REMOTE_SURROGATE.value == "remote_surrogate"
        assert CoverageType.SWAP_ABSORB.value == "swap_absorb"
        assert CoverageType.SWAP_EXCHANGE.value == "swap_exchange"
        assert CoverageType.BACKUP_CALL.value == "backup_call"
        assert CoverageType.ABSENCE_COVERAGE.value == "absence_coverage"
        assert CoverageType.TEMPORARY_PROXY.value == "temporary_proxy"

    def test_count(self):
        assert len(CoverageType) == 6

    def test_is_str(self):
        assert isinstance(CoverageType.REMOTE_SURROGATE, str)


class TestCoverageStatus:
    def test_values(self):
        assert CoverageStatus.ACTIVE.value == "active"
        assert CoverageStatus.SCHEDULED.value == "scheduled"
        assert CoverageStatus.COMPLETED.value == "completed"
        assert CoverageStatus.CANCELLED.value == "cancelled"

    def test_count(self):
        assert len(CoverageStatus) == 4


class TestPersonRef:
    def test_valid_minimal(self):
        r = PersonRef(id=uuid4(), name="Dr. Smith")
        assert r.pgy_level is None
        assert r.role_type is None

    def test_full(self):
        r = PersonRef(id=uuid4(), name="Dr. Jones", pgy_level=2, role_type="resident")
        assert r.pgy_level == 2
        assert r.role_type == "resident"


class TestCoverageRelationship:
    def _make_ref(self, name="Dr. Smith"):
        return PersonRef(id=uuid4(), name=name)

    def test_valid_minimal(self):
        r = CoverageRelationship(
            id="cov-001",
            covering_person=self._make_ref("Dr. Smith"),
            covered_person=self._make_ref("Dr. Jones"),
            coverage_type=CoverageType.REMOTE_SURROGATE,
            status=CoverageStatus.ACTIVE,
            start_date=date(2026, 3, 1),
        )
        assert r.end_date is None
        assert r.location is None
        assert r.reason is None
        assert r.swap_id is None

    def test_full(self):
        r = CoverageRelationship(
            id="cov-002",
            covering_person=self._make_ref(),
            covered_person=self._make_ref(),
            coverage_type=CoverageType.SWAP_ABSORB,
            status=CoverageStatus.SCHEDULED,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 14),
            location="Remote Clinic",
            reason="TDY",
            swap_id=uuid4(),
        )
        assert r.location == "Remote Clinic"
        assert r.swap_id is not None


class TestPersonCoverageSummary:
    def test_valid(self):
        person = PersonRef(id=uuid4(), name="Dr. Smith")
        r = PersonCoverageSummary(person=person)
        assert r.providing == []
        assert r.receiving == []


class TestCoverageCountByType:
    def test_defaults(self):
        r = CoverageCountByType()
        assert r.remote_surrogate == 0
        assert r.swap_absorb == 0
        assert r.swap_exchange == 0
        assert r.backup_call == 0
        assert r.absence_coverage == 0
        assert r.temporary_proxy == 0


class TestCoverageStats:
    def test_defaults(self):
        r = CoverageStats()
        assert r.total_active == 0
        assert r.total_scheduled == 0
        assert r.top_coverers == []
        assert r.most_covered == []


class TestProxyCoverageResponse:
    def test_valid_minimal(self):
        r = ProxyCoverageResponse(coverage_date=date(2026, 3, 1))
        assert r.active_coverage == []
        assert r.upcoming_coverage == []
        assert r.by_coverer == []


class TestProxyCoverageFilter:
    def test_all_none(self):
        r = ProxyCoverageFilter()
        assert r.coverage_type is None
        assert r.status is None
        assert r.person_id is None
        assert r.start_date is None
        assert r.end_date is None

    def test_with_filter(self):
        r = ProxyCoverageFilter(
            coverage_type=CoverageType.BACKUP_CALL,
            status=CoverageStatus.ACTIVE,
        )
        assert r.coverage_type == CoverageType.BACKUP_CALL
