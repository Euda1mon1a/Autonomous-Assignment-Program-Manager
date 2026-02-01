"""Route tests for call assignment API endpoints."""

from datetime import date
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.controllers.call_assignment_controller import CallAssignmentController


def _call_assignment_dict(call_id: UUID, person_id: UUID, call_date: date) -> dict:
    return {
        "id": call_id,
        "date": call_date,
        "person_id": person_id,
        "call_type": "weekday",
        "is_weekend": False,
        "is_holiday": False,
        "person": {
            "id": person_id,
            "name": "Dr. Test",
            "faculty_role": None,
        },
    }


class TestCallAssignmentRoutes:
    """Smoke tests for call assignment routes."""

    def test_list_call_assignments(self, client: TestClient, auth_headers, monkeypatch):
        call_id = uuid4()
        person_id = uuid4()
        call_date = date.today()

        async def fake_list_call_assignments(self, **_kwargs):
            return {
                "items": [_call_assignment_dict(call_id, person_id, call_date)],
                "total": 1,
                "skip": 0,
                "limit": 100,
            }

        monkeypatch.setattr(
            CallAssignmentController,
            "list_call_assignments",
            fake_list_call_assignments,
        )

        response = client.get("/api/v1/call-assignments", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == str(call_id)

    def test_get_call_assignment(self, client: TestClient, auth_headers, monkeypatch):
        call_id = uuid4()
        person_id = uuid4()
        call_date = date.today()

        async def fake_get_call_assignment(self, _call_id):
            return _call_assignment_dict(call_id, person_id, call_date)

        monkeypatch.setattr(
            CallAssignmentController, "get_call_assignment", fake_get_call_assignment
        )

        response = client.get(
            f"/api/v1/call-assignments/{call_id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(call_id)
        assert data["person_id"] == str(person_id)

    def test_create_call_assignment(
        self, client: TestClient, auth_headers, monkeypatch
    ):
        call_id = uuid4()
        person_id = uuid4()
        call_date = date.today()

        async def fake_create_call_assignment(self, _assignment):
            return _call_assignment_dict(call_id, person_id, call_date)

        monkeypatch.setattr(
            CallAssignmentController,
            "create_call_assignment",
            fake_create_call_assignment,
        )

        payload = {
            "call_date": call_date.isoformat(),
            "person_id": str(person_id),
            "call_type": "weekday",
            "is_weekend": False,
            "is_holiday": False,
        }
        response = client.post(
            "/api/v1/call-assignments",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(call_id)

    def test_get_coverage_report(self, client: TestClient, auth_headers, monkeypatch):
        start = date.today()
        end = start

        async def fake_get_coverage_report(self, _start, _end):
            return {
                "start_date": start,
                "end_date": end,
                "total_expected_nights": 1,
                "covered_nights": 1,
                "coverage_percentage": 100.0,
                "gaps": [],
            }

        monkeypatch.setattr(
            CallAssignmentController, "get_coverage_report", fake_get_coverage_report
        )

        response = client.get(
            "/api/v1/call-assignments/reports/coverage",
            params={"start_date": start.isoformat(), "end_date": end.isoformat()},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["coverage_percentage"] == 100.0

    def test_get_call_assignments_by_person(
        self, client: TestClient, auth_headers, monkeypatch
    ):
        call_id = uuid4()
        person_id = uuid4()
        call_date = date.today()

        async def fake_get_by_person(self, **_kwargs):
            return {
                "items": [_call_assignment_dict(call_id, person_id, call_date)],
                "total": 1,
                "skip": 0,
                "limit": 100,
            }

        monkeypatch.setattr(
            CallAssignmentController,
            "get_call_assignments_by_person",
            fake_get_by_person,
        )

        response = client.get(
            f"/api/v1/call-assignments/by-person/{person_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_equity_report(self, client: TestClient, auth_headers, monkeypatch):
        start = date.today()
        end = start

        async def fake_get_equity_report(self, _start, _end):
            return {
                "start_date": start,
                "end_date": end,
                "faculty_count": 1,
                "total_overnight_calls": 1,
                "sunday_call_stats": {"min": 0, "max": 0, "mean": 0, "stdev": 0},
                "weekday_call_stats": {"min": 1, "max": 1, "mean": 1, "stdev": 0},
                "distribution": [],
            }

        monkeypatch.setattr(
            CallAssignmentController, "get_equity_report", fake_get_equity_report
        )

        response = client.get(
            "/api/v1/call-assignments/reports/equity",
            params={"start_date": start.isoformat(), "end_date": end.isoformat()},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["faculty_count"] == 1

    def test_get_call_assignments_by_date(
        self, client: TestClient, auth_headers, monkeypatch
    ):
        call_id = uuid4()
        person_id = uuid4()
        call_date = date.today()

        async def fake_get_by_date(self, _on_date, **_kwargs):
            return {
                "items": [_call_assignment_dict(call_id, person_id, call_date)],
                "total": 1,
                "skip": 0,
                "limit": 100,
            }

        monkeypatch.setattr(
            CallAssignmentController, "get_call_assignments_by_date", fake_get_by_date
        )

        response = client.get(
            f"/api/v1/call-assignments/by-date/{call_date.isoformat()}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_bulk_create_call_assignments(
        self, client: TestClient, auth_headers, monkeypatch
    ):
        async def fake_bulk_create(self, _bulk_data):
            return {"created": 2, "errors": []}

        monkeypatch.setattr(
            CallAssignmentController, "bulk_create_call_assignments", fake_bulk_create
        )

        payload = {
            "assignments": [
                {
                    "call_date": date.today().isoformat(),
                    "person_id": str(uuid4()),
                    "call_type": "weekday",
                    "is_weekend": False,
                    "is_holiday": False,
                },
                {
                    "call_date": date.today().isoformat(),
                    "person_id": str(uuid4()),
                    "call_type": "sunday",
                    "is_weekend": True,
                    "is_holiday": False,
                },
            ],
            "replace_existing": False,
        }

        response = client.post(
            "/api/v1/call-assignments/bulk", json=payload, headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["created"] == 2

    def test_bulk_update_call_assignments(
        self, client: TestClient, auth_headers, monkeypatch
    ):
        call_id = uuid4()
        person_id = uuid4()
        call_date = date.today()

        async def fake_bulk_update(self, _request):
            return {
                "updated": 1,
                "errors": [],
                "assignments": [_call_assignment_dict(call_id, person_id, call_date)],
            }

        monkeypatch.setattr(
            CallAssignmentController, "bulk_update_call_assignments", fake_bulk_update
        )

        payload = {
            "assignment_ids": [str(call_id)],
            "updates": {"person_id": str(person_id)},
            "auto_generate_post_call": False,
        }

        response = client.post(
            "/api/v1/call-assignments/bulk-update", json=payload, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["updated"] == 1
        assert data["assignments"][0]["id"] == str(call_id)

    def test_generate_pcat_assignments(
        self, client: TestClient, auth_headers, monkeypatch
    ):
        call_id = uuid4()
        person_id = uuid4()
        call_date = date.today()

        async def fake_generate_pcat(self, _request):
            return {
                "processed": 1,
                "pcat_created": 1,
                "do_created": 1,
                "errors": [],
                "results": [
                    {
                        "call_assignment_id": call_id,
                        "call_date": call_date,
                        "person_id": person_id,
                        "person_name": "Dr. Test",
                        "pcat_created": True,
                        "do_created": True,
                        "pcat_assignment_id": uuid4(),
                        "do_assignment_id": uuid4(),
                        "error": None,
                    }
                ],
            }

        monkeypatch.setattr(
            CallAssignmentController, "generate_pcat", fake_generate_pcat
        )

        payload = {"assignment_ids": [str(call_id)]}
        response = client.post(
            "/api/v1/call-assignments/generate-pcat",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["processed"] == 1
        assert data["results"][0]["call_assignment_id"] == str(call_id)

    def test_get_equity_preview(self, client: TestClient, auth_headers, monkeypatch):
        start = date.today()
        end = start

        async def fake_get_equity_preview(self, **_kwargs):
            equity_report = {
                "start_date": start,
                "end_date": end,
                "faculty_count": 1,
                "total_overnight_calls": 1,
                "sunday_call_stats": {"min": 0, "max": 0, "mean": 0, "stdev": 0},
                "weekday_call_stats": {"min": 1, "max": 1, "mean": 1, "stdev": 0},
                "distribution": [],
            }
            return {
                "start_date": start,
                "end_date": end,
                "current_equity": equity_report,
                "projected_equity": equity_report,
                "faculty_details": [],
                "improvement_score": 0.5,
            }

        monkeypatch.setattr(
            CallAssignmentController, "get_equity_preview", fake_get_equity_preview
        )

        payload = {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "simulated_changes": [
                {
                    "assignment_id": str(uuid4()),
                    "new_person_id": str(uuid4()),
                    "call_type": "weekday",
                }
            ],
        }

        response = client.post(
            "/api/v1/call-assignments/equity-preview",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["improvement_score"] == 0.5
