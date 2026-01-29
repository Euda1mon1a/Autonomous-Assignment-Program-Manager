"""Tests for schedule override admin routes and overlay reads."""

from datetime import date, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.activity import Activity, ActivityCategory
from app.models.call_assignment import CallAssignment
from app.models.half_day_assignment import HalfDayAssignment
from app.models.person import Person


class TestScheduleOverrides:
    """Schedule override API tests."""

    def test_overrides_require_auth(self, client: TestClient):
        response = client.get("/api/v1/admin/schedule-overrides")
        assert response.status_code == 401

    def test_create_list_deactivate_and_overlay(
        self,
        client: TestClient,
        db: Session,
        auth_headers: dict,
    ):
        activity = Activity(
            id=uuid4(),
            name="Clinic",
            code="fm_clinic_test",
            display_abbreviation="C",
            activity_category=ActivityCategory.CLINICAL.value,
            is_protected=False,
        )
        db.add(activity)

        faculty_a = Person(
            id=uuid4(),
            name="Dr. Alpha",
            type="faculty",
            email="alpha@example.com",
        )
        faculty_b = Person(
            id=uuid4(),
            name="Dr. Beta",
            type="faculty",
            email="beta@example.com",
        )
        db.add(faculty_a)
        db.add(faculty_b)
        db.commit()

        slot_date = date(2026, 3, 12)
        assignment = HalfDayAssignment(
            id=uuid4(),
            person_id=faculty_a.id,
            date=slot_date,
            time_of_day="AM",
            activity_id=activity.id,
            source="solver",
        )
        db.add(assignment)
        db.commit()

        create_resp = client.post(
            "/api/v1/admin/schedule-overrides",
            headers=auth_headers,
            json={
                "half_day_assignment_id": str(assignment.id),
                "override_type": "coverage",
                "replacement_person_id": str(faculty_b.id),
                "reason": "deployment",
            },
        )
        assert create_resp.status_code == 201
        override_id = create_resp.json()["id"]

        list_resp = client.request(
            "GET",
            "/api/v1/admin/schedule-overrides",
            headers=auth_headers,
            params={
                "start_date": slot_date.isoformat(),
                "end_date": slot_date.isoformat(),
                "active_only": "true",
            },
        )
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] == 1

        with_overrides = client.get(
            "/api/v1/half-day-assignments",
            params={
                "start_date": slot_date.isoformat(),
                "end_date": slot_date.isoformat(),
                "include_overrides": "true",
            },
        ).json()
        without_overrides = client.get(
            "/api/v1/half-day-assignments",
            params={
                "start_date": slot_date.isoformat(),
                "end_date": slot_date.isoformat(),
                "include_overrides": "false",
            },
        ).json()

        def find_assignment(payload):
            for item in payload.get("assignments", []):
                if item.get("id") == str(assignment.id):
                    return item
            return None

        with_entry = find_assignment(with_overrides)
        without_entry = find_assignment(without_overrides)
        assert with_entry is not None
        assert without_entry is not None
        assert with_entry["person_id"] == str(faculty_b.id)
        assert without_entry["person_id"] == str(faculty_a.id)

        delete_resp = client.delete(
            f"/api/v1/admin/schedule-overrides/{override_id}",
            headers=auth_headers,
        )
        assert delete_resp.status_code == 200

        list_after = client.get(
            "/api/v1/admin/schedule-overrides",
            headers=auth_headers,
            params={
                "start_date": slot_date.isoformat(),
                "end_date": slot_date.isoformat(),
                "active_only": "true",
            },
        )
        assert list_after.status_code == 200
        assert list_after.json()["total"] == 0

    def test_gap_override_renders_gap(
        self,
        client: TestClient,
        db: Session,
        auth_headers: dict,
    ):
        activity = Activity(
            id=uuid4(),
            name="Clinic",
            code="fm_clinic_test_gap",
            display_abbreviation="C",
            activity_category=ActivityCategory.CLINICAL.value,
            is_protected=False,
        )
        db.add(activity)

        faculty = Person(
            id=uuid4(),
            name="Dr. Gamma",
            type="faculty",
            email="gamma@example.com",
        )
        db.add(faculty)
        db.commit()

        slot_date = date(2026, 3, 13)
        assignment = HalfDayAssignment(
            id=uuid4(),
            person_id=faculty.id,
            date=slot_date,
            time_of_day="PM",
            activity_id=activity.id,
            source="solver",
        )
        db.add(assignment)
        db.commit()

        create_resp = client.post(
            "/api/v1/admin/schedule-overrides",
            headers=auth_headers,
            json={
                "half_day_assignment_id": str(assignment.id),
                "override_type": "gap",
                "reason": "deployment",
            },
        )
        assert create_resp.status_code == 201

        with_overrides = client.get(
            "/api/v1/half-day-assignments",
            params={
                "start_date": slot_date.isoformat(),
                "end_date": slot_date.isoformat(),
                "include_overrides": "true",
            },
        ).json()

        def find_assignment(payload):
            for item in payload.get("assignments", []):
                if item.get("id") == str(assignment.id):
                    return item
            return None

        entry = find_assignment(with_overrides)
        assert entry is not None
        assert entry["display_abbreviation"] == "GAP"
        assert entry["is_gap"] is True

    def test_cascade_creates_gap_for_post_call_pcat_do(
        self,
        client: TestClient,
        db: Session,
        auth_headers: dict,
    ):
        pcat_activity = Activity(
            id=uuid4(),
            name="PCAT",
            code="PCAT",
            display_abbreviation="PCAT",
            activity_category=ActivityCategory.ADMINISTRATIVE.value,
            is_protected=True,
        )
        do_activity = Activity(
            id=uuid4(),
            name="DO",
            code="DO",
            display_abbreviation="DO",
            activity_category=ActivityCategory.ADMINISTRATIVE.value,
            is_protected=True,
        )
        db.add(pcat_activity)
        db.add(do_activity)

        faculty_a = Person(
            id=uuid4(),
            name="Dr. Caller",
            type="faculty",
            email="caller@example.com",
        )
        faculty_b = Person(
            id=uuid4(),
            name="Dr. Backup",
            type="faculty",
            email="backup@example.com",
        )
        db.add(faculty_a)
        db.add(faculty_b)
        db.commit()

        call_date = date(2026, 3, 14)
        call_assignment = CallAssignment(
            id=uuid4(),
            date=call_date,
            person_id=faculty_a.id,
            call_type="weekday",
            is_weekend=False,
            is_holiday=False,
        )
        db.add(call_assignment)

        next_day = call_date + timedelta(days=1)
        pcat_assignment = HalfDayAssignment(
            id=uuid4(),
            person_id=faculty_a.id,
            date=next_day,
            time_of_day="AM",
            activity_id=pcat_activity.id,
            source="solver",
        )
        do_assignment = HalfDayAssignment(
            id=uuid4(),
            person_id=faculty_a.id,
            date=next_day,
            time_of_day="PM",
            activity_id=do_activity.id,
            source="solver",
        )
        db.add(pcat_assignment)
        db.add(do_assignment)
        db.commit()

        resp = client.post(
            "/api/v1/admin/schedule-overrides/cascade",
            headers=auth_headers,
            json={
                "person_id": str(faculty_a.id),
                "start_date": call_date.isoformat(),
                "end_date": call_date.isoformat(),
                "reason": "deployment",
                "apply": False,
                "max_depth": 2,
            },
        )
        assert resp.status_code == 200
        payload = resp.json()

        gap_steps = [
            step
            for step in payload.get("steps", [])
            if step.get("override_type") == "gap"
        ]
        gap_assignment_ids = {step.get("assignment_id") for step in gap_steps}
        assert str(pcat_assignment.id) in gap_assignment_ids
        assert str(do_assignment.id) in gap_assignment_ids
