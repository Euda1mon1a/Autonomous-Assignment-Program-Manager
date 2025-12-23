"""Basic API tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Residency Scheduler" in response.json()["name"]


# Note: Full tests would require database setup
# These are placeholder tests for the CI/CD pipeline
