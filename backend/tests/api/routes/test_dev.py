import os
from fastapi.testclient import TestClient

from app.main import app


def test_dev_seed_endpoint_forbidden():
    client = TestClient(app)
    # Ensure ENV is not test and ALLOW_DEV_SEED is false
    os.environ["ENV"] = "production"
    os.environ["ALLOW_DEV_SEED"] = "false"

    response = client.post("/api/v1/dev/seed?scenario=e2e_baseline")
    assert response.status_code == 403


def test_dev_seed_endpoint_success():
    client = TestClient(app)
    # Allow seed
    os.environ["ENV"] = "test"
    os.environ["ALLOW_DEV_SEED"] = "true"

    response = client.post("/api/v1/dev/seed?scenario=e2e_baseline")
    if response.status_code != 200:
        print(response.json())
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["residents_created"] == 17
    assert data["faculty_created"] == 13
    assert data["activities_created"] == 5
    assert (
        data["assignments_created"] == 28 * 30 * 2
    )  # 28 days, 30 people, 2 half-days = 1680
