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


def test_dev_cleanup_endpoint_forbidden():
    client = TestClient(app)
    os.environ["ENV"] = "production"
    os.environ["ALLOW_DEV_SEED"] = "false"

    response = client.post("/api/v1/dev/cleanup")
    assert response.status_code == 403


def test_dev_cleanup_endpoint_success():
    client = TestClient(app)
    os.environ["ENV"] = "test"
    os.environ["ALLOW_DEV_SEED"] = "true"

    seed_response = client.post("/api/v1/dev/seed?scenario=e2e_baseline")
    assert seed_response.status_code == 200

    response = client.post("/api/v1/dev/cleanup")
    if response.status_code != 200:
        print(response.json())
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["faculty_deleted"] == 13
    assert data["residents_deleted"] == 17
    assert data["hdas_deleted"] >= 1
