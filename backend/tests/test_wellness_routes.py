"""Route tests for wellness API endpoints."""

from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes import wellness as wellness_routes
from app.services.wellness_service import WellnessService


def _fake_person():
    return SimpleNamespace(id=uuid4(), email="testuser@example.com")


def _fake_survey(survey_id):
    return SimpleNamespace(
        id=survey_id,
        name="burnout",
        display_name="Burnout Survey",
        survey_type="burnout",
        description=None,
        instructions=None,
        points_value=5,
        estimated_seconds=60,
        frequency="weekly",
        questions_json=[{"id": "q1", "text": "How are you?"}],
        is_active=True,
        created_at=datetime.utcnow(),
    )


def _fake_account(person_id):
    return SimpleNamespace(
        person_id=person_id,
        points_balance=10,
        points_lifetime=50,
        current_streak_weeks=2,
        longest_streak_weeks=4,
        last_activity_date=datetime.utcnow().date(),
        streak_start_date=datetime.utcnow().date(),
        leaderboard_opt_in=True,
        display_name="Anon",
        research_consent=True,
    )


class TestWellnessRoutes:
    """Smoke tests for wellness routes."""

    def test_list_surveys(self, client: TestClient, auth_headers, monkeypatch):
        async def fake_get_person(_db, _user):
            return _fake_person()

        async def fake_get_available_surveys(self, _person_id):
            return [
                {
                    "id": uuid4(),
                    "name": "burnout",
                    "display_name": "Burnout Survey",
                    "survey_type": "burnout",
                    "points_value": 5,
                    "estimated_seconds": 60,
                    "frequency": "weekly",
                    "is_available": True,
                    "next_available_at": None,
                    "completed_this_period": False,
                }
            ]

        monkeypatch.setattr(wellness_routes, "_get_person_for_user", fake_get_person)
        monkeypatch.setattr(
            WellnessService, "get_available_surveys", fake_get_available_surveys
        )

        response = client.get("/api/v1/wellness/surveys", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "burnout"

    def test_get_survey(self, client: TestClient, auth_headers, monkeypatch):
        survey_id = uuid4()

        async def fake_get_survey_by_id(self, _survey_id):
            return _fake_survey(survey_id)

        monkeypatch.setattr(WellnessService, "get_survey_by_id", fake_get_survey_by_id)

        response = client.get(
            f"/api/v1/wellness/surveys/{survey_id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(survey_id)
        assert data["survey_type"] == "burnout"

    def test_submit_survey_response(
        self, client: TestClient, auth_headers, monkeypatch
    ):
        survey_id = uuid4()
        person = _fake_person()

        async def fake_get_person(_db, _user):
            return person

        class DummyPoints:
            points_awarded = 10

        class DummyAchievements:
            newly_earned = []

        class DummyStreak:
            streak_updated = True
            current_streak = 3

        class DummyResult:
            success = True
            response_id = uuid4()
            score = 5
            score_interpretation = "ok"
            points_result = DummyPoints()
            achievement_result = DummyAchievements()
            streak_result = DummyStreak()
            message = "ok"

        async def fake_submit(self, **_kwargs):
            return DummyResult()

        monkeypatch.setattr(wellness_routes, "_get_person_for_user", fake_get_person)
        monkeypatch.setattr(WellnessService, "submit_survey_response", fake_submit)

        payload = {
            "responses": {"q1": 3},
            "block_number": 1,
            "academic_year": 2026,
        }

        response = client.post(
            f"/api/v1/wellness/surveys/{survey_id}/respond",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["points_earned"] == 10

    def test_get_survey_history(self, client: TestClient, auth_headers, monkeypatch):
        person = _fake_person()

        async def fake_get_person(_db, _user):
            return person

        async def fake_history(self, **_kwargs):
            return (
                [
                    {
                        "id": uuid4(),
                        "survey_id": uuid4(),
                        "survey_name": "burnout",
                        "survey_type": "burnout",
                        "score": 3,
                        "score_interpretation": "ok",
                        "submitted_at": datetime.utcnow(),
                        "block_number": 1,
                        "academic_year": 2026,
                    }
                ],
                1,
            )

        monkeypatch.setattr(wellness_routes, "_get_person_for_user", fake_get_person)
        monkeypatch.setattr(
            WellnessService, "get_survey_response_history", fake_history
        )

        response = client.get("/api/v1/wellness/surveys/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_wellness_account(self, client: TestClient, auth_headers, monkeypatch):
        person = _fake_person()

        async def fake_get_person(_db, _user):
            return person

        async def fake_get_account(self, _person_id):
            return _fake_account(person.id)

        def fake_achievements(self, _account):
            return [
                {
                    "code": "starter",
                    "name": "Starter",
                    "description": "First steps",
                    "icon": "star",
                    "earned": True,
                    "earned_at": datetime.utcnow(),
                    "criteria": {},
                }
            ]

        async def fake_available_surveys(self, _person_id):
            return [
                {
                    "completed_this_period": False,
                    "is_available": True,
                }
            ]

        monkeypatch.setattr(wellness_routes, "_get_person_for_user", fake_get_person)
        monkeypatch.setattr(WellnessService, "get_or_create_account", fake_get_account)
        monkeypatch.setattr(WellnessService, "get_achievement_info", fake_achievements)
        monkeypatch.setattr(
            WellnessService, "get_available_surveys", fake_available_surveys
        )

        response = client.get("/api/v1/wellness/account", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["person_id"] == str(person.id)
        assert data["points_balance"] == 10

    def test_get_leaderboard(self, client: TestClient, auth_headers, monkeypatch):
        person = _fake_person()

        async def fake_get_person(_db, _user):
            return person

        async def fake_leaderboard(self, **_kwargs):
            return {
                "entries": [
                    {
                        "rank": 1,
                        "display_name": "Anon",
                        "points": 100,
                        "streak": 3,
                        "is_you": True,
                    }
                ],
                "total_participants": 1,
                "your_rank": 1,
                "your_points": 100,
            }

        monkeypatch.setattr(wellness_routes, "_get_person_for_user", fake_get_person)
        monkeypatch.setattr(WellnessService, "get_leaderboard", fake_leaderboard)

        response = client.get("/api/v1/wellness/leaderboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_participants"] == 1

    def test_get_widget_data(self, client: TestClient, auth_headers, monkeypatch):
        person = _fake_person()

        async def fake_get_person(_db, _user):
            return person

        async def fake_get_account(self, _person_id):
            return _fake_account(person.id)

        def fake_achievements(self, _account):
            recent = datetime.utcnow().isoformat()
            return [
                {
                    "code": "starter",
                    "name": "Starter",
                    "description": "First steps",
                    "icon": "star",
                    "earned": True,
                    "earned_at": recent,
                    "criteria": {},
                }
            ]

        async def fake_available_surveys(self, _person_id):
            return [
                {
                    "id": uuid4(),
                    "name": "burnout",
                    "display_name": "Burnout Survey",
                    "survey_type": "burnout",
                    "points_value": 5,
                    "estimated_seconds": 60,
                    "frequency": "weekly",
                    "is_available": True,
                    "next_available_at": None,
                    "completed_this_period": False,
                }
            ]

        monkeypatch.setattr(wellness_routes, "_get_person_for_user", fake_get_person)
        monkeypatch.setattr(WellnessService, "get_or_create_account", fake_get_account)
        monkeypatch.setattr(WellnessService, "get_achievement_info", fake_achievements)
        monkeypatch.setattr(
            WellnessService, "get_available_surveys", fake_available_surveys
        )

        response = client.get("/api/v1/wellness/widget/data", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["current_streak"] == 2
        assert len(data["available_surveys"]) == 1
        assert len(data["recent_achievements"]) == 1

    def test_submit_quick_pulse(self, client: TestClient, auth_headers, monkeypatch):
        person = _fake_person()
        survey_id = uuid4()

        async def fake_get_person(_db, _user):
            return person

        async def fake_get_survey_by_name(self, _name):
            return SimpleNamespace(id=survey_id)

        class DummyPoints:
            points_awarded = 3

        class DummyStreak:
            current_streak = 4

        class DummyResult:
            success = True
            points_result = DummyPoints()
            streak_result = DummyStreak()
            message = "ok"

        async def fake_submit(self, **_kwargs):
            return DummyResult()

        monkeypatch.setattr(wellness_routes, "_get_person_for_user", fake_get_person)
        monkeypatch.setattr(
            WellnessService, "get_survey_by_name", fake_get_survey_by_name
        )
        monkeypatch.setattr(WellnessService, "submit_survey_response", fake_submit)

        payload = {"mood": 4, "energy": 3}
        response = client.post(
            "/api/v1/wellness/pulse", json=payload, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["points_earned"] == 3

    def test_get_admin_analytics(self, client: TestClient, auth_headers, monkeypatch):
        async def fake_get_analytics_summary(self, **_kwargs):
            return {
                "total_participants": 5,
                "active_this_week": 3,
                "active_this_block": 4,
                "participation_rate": 0.8,
                "total_responses_this_week": 7,
                "total_responses_this_block": 12,
                "average_responses_per_person": 2.4,
                "average_streak": 1.5,
                "longest_streak": 6,
                "total_points_earned_this_week": 42,
                "hopfield_positions_this_week": 15,
            }

        monkeypatch.setattr(
            WellnessService, "get_analytics_summary", fake_get_analytics_summary
        )

        response = client.get("/api/v1/wellness/admin/analytics", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_participants"] == 5
