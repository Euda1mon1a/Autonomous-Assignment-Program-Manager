"""Tests for FairnessAuditService helpers."""

from datetime import date

from app.services.fairness_audit_service import FairnessAuditService
from app.scheduling.constraints.integrated_workload import FacultyWorkload


def test_jains_fairness_index_handles_empty_and_uniform() -> None:
    service = FairnessAuditService(db=None)  # type: ignore[arg-type]

    assert service._jains_fairness_index([]) == 1.0
    assert service._jains_fairness_index([1.0, 1.0, 1.0]) == 1.0

    # Two values: 1 and 2 => 0.9
    assert service._jains_fairness_index([1.0, 2.0]) == 0.9


def test_build_report_flags_outliers() -> None:
    service = FairnessAuditService(db=None)  # type: ignore[arg-type]

    workloads = [
        FacultyWorkload(person_id="1", person_name="High", call_count=10),
        FacultyWorkload(person_id="2", person_name="Low", call_count=2),
    ]

    report = service._build_report(
        start_date=date(2026, 1, 1), end_date=date(2026, 1, 28), workloads=workloads
    )

    assert report.workload_stats.mean == 6.0
    assert report.workload_stats.spread == 8.0
    assert report.high_workload_faculty == ["High"]
    assert report.low_workload_faculty == ["Low"]
