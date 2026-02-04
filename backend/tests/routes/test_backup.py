"""Tests for backup snapshot endpoint validation."""

from fastapi.testclient import TestClient


def test_backup_snapshot_rejects_unknown_table(client: TestClient, auth_headers):
    response = client.post(
        "/api/v1/backup/snapshot",
        json={"table": "not_allowed", "reason": "test"},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"].lower()
