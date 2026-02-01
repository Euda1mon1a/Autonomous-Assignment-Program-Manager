"""Route tests for fatigue risk API endpoints."""

from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes import fatigue_risk as fatigue_routes
from app.resilience.frms import CircadianPhase, HazardLevel, SamnPerelliLevel
from app.resilience.frms.frms_service import FatigueProfile


def _make_profile(resident_id, hazard_level=HazardLevel.GREEN, sleep_debt=2.0):
    """Create a minimal FatigueProfile for route testing."""
    return FatigueProfile(
        resident_id=resident_id,
        resident_name="Test Resident",
        pgy_level=2,
        generated_at=datetime.utcnow(),
        current_alertness=0.8,
        samn_perelli_level=SamnPerelliLevel.OKAY,
        sleep_debt_hours=sleep_debt,
        circadian_phase=CircadianPhase.MORNING_PEAK,
        hours_since_sleep=6.0,
        hazard_level=hazard_level,
        hazard_triggers=[],
        required_mitigations=[],
        hours_worked_week=40.0,
        hours_worked_day=8.0,
        consecutive_duty_days=2,
        consecutive_night_shifts=0,
        predicted_end_of_shift_alertness=0.7,
        next_rest_opportunity=datetime.utcnow(),
        recovery_sleep_needed=1.0,
        acgme_hours_remaining=40.0,
        acgme_violation_risk=False,
    )


class TestFatigueRiskRoutes:
    """Smoke tests for fatigue risk endpoints."""

    def test_get_samn_perelli_levels(self, client: TestClient):
        response = client.get("/api/v1/fatigue-risk/samn-perelli/levels")
        assert response.status_code == 200
        data = response.json()
        assert "levels" in data
        assert len(data["levels"]) == 7
        assert {"level", "name", "description"}.issubset(data["levels"][0].keys())

    def test_calculate_fatigue_score(self, client: TestClient):
        payload = {
            "hours_awake": 12.0,
            "hours_worked_24h": 10.0,
            "consecutive_night_shifts": 1,
            "time_of_day_hour": 9,
            "prior_sleep_hours": 6.5,
        }
        response = client.post("/api/v1/fatigue-risk/score", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "samn_perelli_level" in data
        assert "samn_perelli_name" in data
        assert "alertness_score" in data
        assert "circadian_phase" in data
        assert "factors" in data

    def test_get_resident_profile(self, client: TestClient, monkeypatch):
        resident_id = uuid4()

        async def fake_get_profile(self, resident_id, target_time=None):
            return _make_profile(resident_id)

        monkeypatch.setattr(
            fatigue_routes.FRMSService, "get_resident_profile", fake_get_profile
        )

        response = client.get(f"/api/v1/fatigue-risk/resident/{resident_id}/profile")
        assert response.status_code == 200
        data = response.json()
        assert data["resident_id"] == str(resident_id)
        assert data["resident_name"] == "Test Resident"
        assert "current_state" in data
        assert "hazard" in data
        assert "work_history" in data
        assert "predictions" in data
        assert "acgme" in data

    def test_get_alertness_prediction(self, client: TestClient, monkeypatch):
        resident_id = uuid4()

        async def fake_get_profile(self, resident_id, target_time=None):
            return _make_profile(resident_id)

        monkeypatch.setattr(
            fatigue_routes.FRMSService, "get_resident_profile", fake_get_profile
        )

        response = client.get(f"/api/v1/fatigue-risk/resident/{resident_id}/alertness")
        assert response.status_code == 200
        data = response.json()
        assert data["resident_id"] == str(resident_id)
        assert "alertness_score" in data
        assert "samn_perelli" in data
        assert "circadian_phase" in data
        assert "risk_level" in data

    def test_assess_schedule_fatigue_risk(self, client: TestClient, monkeypatch):
        resident_id = uuid4()

        async def fake_assess(self, **_kwargs):
            return {
                "resident_id": str(resident_id),
                "shifts_evaluated": 1,
                "overall_risk": "low",
                "metrics": {},
                "hazard_distribution": {},
                "high_risk_windows": [],
                "trajectory": [],
                "recommendations": [],
            }

        monkeypatch.setattr(
            fatigue_routes.FRMSService,
            "assess_schedule_fatigue_risk",
            fake_assess,
        )

        payload = {
            "proposed_shifts": [
                {
                    "type": "day",
                    "start": datetime.utcnow().isoformat(),
                    "end": datetime.utcnow().isoformat(),
                    "prior_sleep": 7.0,
                }
            ]
        }
        response = client.post(
            f"/api/v1/fatigue-risk/resident/{resident_id}/schedule-assessment",
            json=payload,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resident_id"] == str(resident_id)
        assert data["overall_risk"] == "low"

    def test_get_current_hazard(self, client: TestClient, monkeypatch):
        resident_id = uuid4()

        async def fake_get_profile(self, resident_id, target_time=None):
            return _make_profile(resident_id, hazard_level=HazardLevel.YELLOW)

        monkeypatch.setattr(
            fatigue_routes.FRMSService, "get_resident_profile", fake_get_profile
        )

        response = client.get(f"/api/v1/fatigue-risk/resident/{resident_id}/hazard")
        assert response.status_code == 200
        data = response.json()
        assert data["hazard_level"] == HazardLevel.YELLOW.value

    def test_scan_all_residents_for_hazards(self, client: TestClient, monkeypatch):
        profiles = [
            _make_profile(uuid4(), hazard_level=HazardLevel.RED),
            _make_profile(uuid4(), hazard_level=HazardLevel.GREEN),
        ]

        async def fake_scan(self, **_kwargs):
            return profiles

        monkeypatch.setattr(fatigue_routes.FRMSService, "scan_all_residents", fake_scan)

        response = client.get("/api/v1/fatigue-risk/hazards/scan")
        assert response.status_code == 200
        data = response.json()
        assert data["total_residents"] == 2
        assert data["critical_count"] == 1

    def test_get_sleep_debt_state(self, client: TestClient, monkeypatch):
        resident_id = uuid4()

        async def fake_get_profile(self, resident_id, target_time=None):
            return _make_profile(resident_id, sleep_debt=12.0)

        monkeypatch.setattr(
            fatigue_routes.FRMSService, "get_resident_profile", fake_get_profile
        )

        response = client.get(f"/api/v1/fatigue-risk/resident/{resident_id}/sleep-debt")
        assert response.status_code == 200
        data = response.json()
        assert data["resident_id"] == str(resident_id)
        assert data["current_debt_hours"] == 12.0
        assert data["debt_severity"] in {"moderate", "severe", "critical"}

    def test_predict_sleep_debt_trajectory(self, client: TestClient, monkeypatch):
        from app.resilience.frms import sleep_debt as sleep_debt_module

        resident_id = uuid4()

        def fake_predict(self, **_kwargs):
            return [
                {"day": 1, "cumulative_debt": 2.0},
                {"day": 2, "cumulative_debt": 1.0},
            ]

        def fake_estimate(self, _debt):
            return 1

        monkeypatch.setattr(
            sleep_debt_module.SleepDebtModel, "predict_debt_trajectory", fake_predict
        )
        monkeypatch.setattr(
            sleep_debt_module.SleepDebtModel, "estimate_recovery_time", fake_estimate
        )

        payload = {"planned_sleep_hours": [7.0, 8.0]}
        response = client.post(
            f"/api/v1/fatigue-risk/resident/{resident_id}/sleep-debt/trajectory",
            json=payload,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resident_id"] == str(resident_id)
        assert data["days_predicted"] == 2

    def test_team_heatmap(self, client: TestClient, monkeypatch):
        async def fake_heatmap(self, **_kwargs):
            return {
                "date": "2026-02-01",
                "generated_at": datetime.utcnow().isoformat(),
                "residents": [],
                "hours": list(range(24)),
            }

        monkeypatch.setattr(
            fatigue_routes.FRMSService, "get_team_heatmap", fake_heatmap
        )

        payload = {"target_date": "2026-02-01", "include_predictions": True}
        response = client.post("/api/v1/fatigue-risk/team/heatmap", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == "2026-02-01"

    def test_reference_endpoints(self, client: TestClient):
        response = client.get("/api/v1/fatigue-risk/reference/circadian-phases")
        assert response.status_code == 200
        assert "phases" in response.json()

        response = client.get("/api/v1/fatigue-risk/reference/hazard-levels")
        assert response.status_code == 200
        assert "levels" in response.json()

        response = client.get("/api/v1/fatigue-risk/reference/mitigation-types")
        assert response.status_code == 200
        assert "mitigations" in response.json()

    def test_export_temporal_constraints(self, client: TestClient, monkeypatch):
        def fake_export(self):
            return {
                "version": "1.0",
                "generated_at": datetime.utcnow(),
                "framework": "FRMS",
                "references": [],
                "circadian_rhythm": {},
                "sleep_homeostasis": {},
                "samn_perelli_scale": {},
                "hazard_thresholds": {},
                "acgme_integration": {},
                "scheduling_constraints": {},
            }

        monkeypatch.setattr(
            fatigue_routes.FRMSService, "export_temporal_constraints", fake_export
        )

        response = client.get("/api/v1/fatigue-risk/temporal-constraints")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "1.0"

    def test_validate_acgme_with_fatigue(self, client: TestClient, monkeypatch):
        resident_id = uuid4()

        async def fake_get_profile(self, resident_id, target_time=None):
            return _make_profile(resident_id, hazard_level=HazardLevel.GREEN)

        monkeypatch.setattr(
            fatigue_routes.FRMSService, "get_resident_profile", fake_get_profile
        )

        payload = {
            "resident_id": str(resident_id),
            "schedule_start": datetime.utcnow().date().isoformat(),
            "schedule_end": datetime.utcnow().date().isoformat(),
        }
        response = client.post(
            f"/api/v1/fatigue-risk/resident/{resident_id}/acgme-validation",
            json=payload,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resident_id"] == str(resident_id)
        assert data["acgme_compliant"] is True
