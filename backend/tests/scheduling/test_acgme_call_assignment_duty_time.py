"""Tests for call assignments counting as duty time in ACGME checks."""

from datetime import date, timedelta
from uuid import uuid4

from app.scheduling.acgme_compliance_engine import ACGMEComplianceEngine


def _make_block(block_date: date) -> dict:
    return {
        "id": uuid4(),
        "date": block_date,
        "time_of_day": "AM",
        "start_time": "07:00",
        "end_time": "13:00",
        "duration_hours": 6.0,
    }


def test_call_assignment_counts_for_rest_period_violation():
    engine = ACGMEComplianceEngine()
    resident_id = uuid4()

    call_date = date(2025, 1, 1)
    next_day = call_date + timedelta(days=1)

    block = _make_block(next_day)
    assignments = [
        {
            "person_id": resident_id,
            "block_id": block["id"],
            "rotation_name": "FMIT",
        }
    ]
    call_assignments = [{"date": call_date, "call_type": "weekday"}]

    result = engine.validate_resident_compliance(
        person_id=resident_id,
        pgy_level=2,
        period_start=call_date,
        period_end=next_day,
        assignments=assignments,
        blocks=[block],
        call_assignments=call_assignments,
        leave_records=[],
    )

    violations = result.violations_by_domain.get("work_hours", [])
    assert any(v.violation_type == "rest_period" for v in violations)


def test_call_assignment_counts_for_24_plus_4_violation():
    engine = ACGMEComplianceEngine()
    resident_id = uuid4()

    call_date = date(2025, 2, 1)
    call_assignments = [
        {
            "date": call_date,
            "call_type": "weekday",
            "start_time": "07:00",
            "end_time": "07:00",
            "duration_hours": 32.0,
        }
    ]

    result = engine.validate_resident_compliance(
        person_id=resident_id,
        pgy_level=2,
        period_start=call_date,
        period_end=call_date,
        assignments=[],
        blocks=[],
        call_assignments=call_assignments,
        leave_records=[],
    )

    violations = result.violations_by_domain.get("work_hours", [])
    assert any(v.violation_type == "24_plus_4" for v in violations)
