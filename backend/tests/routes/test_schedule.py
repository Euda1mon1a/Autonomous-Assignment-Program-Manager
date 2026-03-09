"""Tests for schedule routes."""

from datetime import date
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import Settings


def test_generate_schedule_rejects_non_cp_sat_in_production(
    client: TestClient, auth_headers: dict
) -> None:
    settings = Settings(
        DEBUG=False,
        DATABASE_URL="postgresql://user:supersecretpassword123@localhost:5432/db",
        REDIS_PASSWORD="supersecretredispassword123",
    )

    payload = {
        "start_date": date(2025, 1, 1).isoformat(),
        "end_date": date(2025, 1, 7).isoformat(),
        "algorithm": "greedy",
    }

    with patch("app.api.routes.schedule.get_settings", return_value=settings):
        response = client.post(
            "/api/v1/schedule/generate",
            headers=auth_headers,
            json=payload,
        )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Only CP-SAT is allowed in production. Use algorithm=cp_sat."
    )
