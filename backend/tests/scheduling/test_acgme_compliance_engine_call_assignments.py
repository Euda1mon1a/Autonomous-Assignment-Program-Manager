from datetime import date
from uuid import uuid4

from app.scheduling.acgme_compliance_engine import ACGMEComplianceEngine


def test_call_assignment_triggers_rest_violation():
    engine = ACGMEComplianceEngine()
    resident_id = uuid4()
    block_id = uuid4()

    blocks = [
        {
            "id": block_id,
            "date": date(2025, 1, 2),
            "time_of_day": "AM",
            "start_time": "07:00",
            "end_time": "13:00",
            "duration_hours": 6.0,
        }
    ]
    assignments = [
        {
            "person_id": resident_id,
            "block_id": block_id,
            "rotation_name": "Clinic",
        }
    ]
    call_assignments = [
        {
            "date": date(2025, 1, 1),
            "start_time": "19:00",
            "end_time": "07:00",
            "duration_hours": 12.0,
            "call_type": "weekday",
        }
    ]

    result = engine.validate_resident_compliance(
        person_id=resident_id,
        pgy_level=2,
        period_start=date(2025, 1, 1),
        period_end=date(2025, 1, 2),
        assignments=assignments,
        blocks=blocks,
        call_assignments=call_assignments,
        leave_records=[],
    )

    work_hour_violations = result.violations_by_domain.get("work_hours", [])
    assert any(v.violation_type == "rest_period" for v in work_hour_violations), (
        "Overnight call should require rest before next shift"
    )


def test_call_assignment_triggers_24_plus_4_violation():
    engine = ACGMEComplianceEngine()
    resident_id = uuid4()

    call_assignments = [
        {
            "date": date(2025, 1, 1),
            "start_time": "06:00",
            "end_time": "12:00",
            "duration_hours": 30.0,
            "call_type": "weekday",
        }
    ]

    result = engine.validate_resident_compliance(
        person_id=resident_id,
        pgy_level=2,
        period_start=date(2025, 1, 1),
        period_end=date(2025, 1, 1),
        assignments=[],
        blocks=[],
        call_assignments=call_assignments,
        leave_records=[],
    )

    work_hour_violations = result.violations_by_domain.get("work_hours", [])
    assert any(v.violation_type == "24_plus_4" for v in work_hour_violations), (
        "Extended call duty should be evaluated under 24+4 rule"
    )
